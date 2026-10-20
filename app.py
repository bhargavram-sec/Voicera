
"""
Main Flask Application for Voicera.
Handles API routes and orchestrates the processing pipeline.
"""

import os
# Fix for PyTorch MPS float64 error
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

import uuid
import threading
import logging
import json
from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename
import shutil
from utils.config import (
    UPLOAD_FOLDER, OUTPUT_FOLDER, TEMP_FOLDER, LANGUAGES
)
from processors.audio_extractor import extract_audio
from processors.transcriber import transcribe_audio
from processors.translator import TranslationEngine
from processors.tts_generator import TTSGenerator
from processors.audio_sync import AudioSynchronizer
from processors.video_assembler import assemble_video
import yt_dlp

# Setup Flask
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB limit

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Job storage (in-memory for simplicity, use Redis/DB for production)
jobs = {}

# Allowed extensions
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mp3', 'wav', 'm4a', 'flac', 'aac'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def download_video(url, output_path):
    """Download video from URL using yt-dlp."""
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def process_video_task(job_id, video_path, target_lang, voice_gender, sync_mode=False, source_lang=None, audio_only=False, model_size="medium"):
    """
    Background task to process the video.
    """
    try:
        job_dir = os.path.join(TEMP_FOLDER, job_id)
        os.makedirs(job_dir, exist_ok=True)
        
        # 1. Audio Extraction
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["current_step"] = "Extracting audio"
        jobs[job_id]["progress"] = 10
        
        audio_path = os.path.join(job_dir, "original.wav")
        extract_audio(video_path, audio_path)
        
        # 2. Transcription
        jobs[job_id]["current_step"] = "Transcribing"
        jobs[job_id]["progress"] = 25
        
        transcription_result = transcribe_audio(audio_path, source_lang=source_lang, model_size=model_size)
        source_lang = transcription_result["language"]
        segments = transcription_result["segments"]
        
        # Save SRT
        srt_path = os.path.join(job_dir, "subtitles.srt")
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(transcription_result.get("srt", ""))
        jobs[job_id]["srt_path"] = f"{job_id}/subtitles.srt"  # Store relative path for potential download
        
        # 3. Translation
        jobs[job_id]["current_step"] = "Translating"
        jobs[job_id]["progress"] = 40
        
        # --- SMART MERGE SEGMENTS START ---
        # Merge short segments to improve translation context
        merged_segments = []
        if segments:
            current_group = segments[0]
            for next_seg in segments[1:]:
                # Logic: Merge if current is short (< 2.5s) AND total duration < 15s
                # Or if current text does not end in sentence-ending punctuation
                duration = current_group['end'] - current_group['start']
                total_duration = next_seg['end'] - current_group['start']
                
                text = current_group['text'].strip()
                ends_with_punctuation = text.endswith(('.', '?', '!'))
                
                should_merge = (
                    (duration < 5.0 or not ends_with_punctuation) and 
                    total_duration < 7.0
                )
                
                if should_merge:
                    # Merge
                    current_group['text'] += " " + next_seg['text']
                    current_group['end'] = next_seg['end']
                    # We lose individual word timestamps for the second part, but that's acceptable for translation context
                    if 'words' in next_seg:
                         current_group['words'].extend(next_seg.get('words', []))
                else:
                    merged_segments.append(current_group)
                    current_group = next_seg
            merged_segments.append(current_group)
            
        segments = merged_segments
        # Update SRT with merged segments (optional, but good for consistency)
        # We won't update the saved SRT file to keep original timestamps, 
        # but translation will use merged chunks.
        # --- SMART MERGE SEGMENTS END ---
        
        translator = TranslationEngine(source_lang, target_lang)
        translated_segments = []
        
        for seg in segments:
            translated = translator.translate_segment(seg)
            translated_segments.append(translated)
            
        # 4. TTS Generation + Sync (Integrated)
        jobs[job_id]["current_step"] = "Generating & Syncing Speech"
        jobs[job_id]["progress"] = 60
        
        tts = TTSGenerator(target_lang, voice_gender)
        
        for i, seg in enumerate(translated_segments):
            seg_audio_path = os.path.join(job_dir, f"seg_{i}.mp3")
            
            # Pass target_duration to let TTS engine handle natural speed adjustment
            # Use original duration (from Whisper) as target
            target_dur = seg["duration"]
            
            # Generate natively pacing audio
            result = tts.generate_speech(seg["translated_text"], seg_audio_path, target_duration=target_dur)
            
            seg["audio_path"] = result["audio_path"] # Path to file
            seg["generated_duration"] = result["duration"]
            seg["audio_path_final"] = result["audio_path"] # No extra tempo step needed

        # 5. Merging (No post-process tempo needed now)
        jobs[job_id]["current_step"] = "Merging audio"
        jobs[job_id]["progress"] = 80
        
        synchronizer = AudioSynchronizer(strict_mode=sync_mode)
        
        total_duration = segments[-1]["end"] if segments else 0
        merged_audio_path = os.path.join(job_dir, "merged_dubbed.mp3")
        synchronizer.merge_segments(translated_segments, total_duration + 5, merged_audio_path)
        
        # 6. Assembly (or Audio Output)
        jobs[job_id]["current_step"] = "Finalizing"
        jobs[job_id]["progress"] = 95
        
        is_audio_input = video_path.lower().endswith(('.mp3', '.wav', '.m4a', '.flac', '.aac'))
        
        if is_audio_input or audio_only:
             final_output_filename = f"{job_id}_dubbed.mp3"
             final_output_path = os.path.join(OUTPUT_FOLDER, final_output_filename)
             shutil.copy(merged_audio_path, final_output_path)
        else:
            final_output_filename = f"{job_id}_dubbed.mp4"
            final_output_path = os.path.join(OUTPUT_FOLDER, final_output_filename)
            try:
                assemble_video(video_path, merged_audio_path, final_output_path)
            except Exception as e:
                logger.warning(f"Video assembly failed (likely audio-only input): {e}. Falling back to audio output.")
                # Fallback to audio
                final_output_filename = f"{job_id}_dubbed.mp3"
                final_output_path = os.path.join(OUTPUT_FOLDER, final_output_filename)
                shutil.copy(merged_audio_path, final_output_path)
        
        # Move SRT to output folder
        final_srt_filename = f"{job_id}_subtitles.srt"
        final_srt_path = os.path.join(OUTPUT_FOLDER, final_srt_filename)
        if os.path.exists(srt_path):
             os.rename(srt_path, final_srt_path)
             jobs[job_id]["srt_path"] = final_srt_filename

        # Complete
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["progress"] = 100
        jobs[job_id]["output_path"] = final_output_filename # relative for download
        jobs[job_id]["current_step"] = "Complete"
        
    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}", exc_info=True)
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
    finally:
        # After job completes or fails, schedule cleanup after 1 hour
        threading.Timer(3600.0, lambda: jobs.pop(job_id, None)).start()

@app.route('/')
def index():
    return render_template('index.html', languages=LANGUAGES)

@app.route('/api/upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({"success": False, "error": "No file part"}), 400
        
    file = request.files['video']
    target_lang = request.form.get('language', 'hi')
    voice_gender = request.form.get('gender', 'female')
    # Capture options
    sync_mode = request.form.get('sync_mode') == 'true'
    source_lang = request.form.get('source_lang')
    audio_only = request.form.get('audio_only') == 'true'
    model_size = request.form.get('model_size', 'medium')
    if source_lang == 'auto':
        source_lang = None
    
    if file.filename == '':
        return jsonify({"success": False, "error": "No selected file"}), 400
        
    if file and allowed_file(file.filename):
        job_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        save_path = os.path.join(UPLOAD_FOLDER, f"{job_id}_{filename}")
        file.save(save_path)
        
        # Init job
        jobs[job_id] = {
            "status": "queued",
            "progress": 0,
            "current_step": "Queued",
            "video_path": save_path,
            "target_lang": target_lang
        }
        
        # Start processing in thread with sync_mode
        thread = threading.Thread(target=process_video_task, args=(job_id, save_path, target_lang, voice_gender, sync_mode, source_lang, audio_only, model_size))
        thread.start()
        
        return jsonify({"success": True, "job_id": job_id})
    else:
        return jsonify({"success": False, "error": "Invalid file type"}), 400

@app.route('/api/upload-url', methods=['POST'])
def upload_url():
    data = request.json
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400
        
    url = data.get('url')
    target_lang = data.get('language', 'hi')
    voice_gender = data.get('gender', 'female')
    # Capture sync_mode
    sync_mode = data.get('sync_mode', False)
    source_lang = data.get('source_lang')
    audio_only = data.get('audio_only', False)
    model_size = data.get('model_size', 'medium')
    if source_lang == 'auto':
        source_lang = None

    if not url:
        return jsonify({"success": False, "error": "No URL provided"}), 400

    job_id = str(uuid.uuid4())
    save_path = os.path.join(UPLOAD_FOLDER, f"{job_id}_download.mp4")
    
    try:
        # Init job
        jobs[job_id] = {
            "status": "processing",
            "progress": 5,
            "current_step": "Downloading video...",
            "target_lang": target_lang,
            "created_at": str(uuid.uuid1())
        }
        
        def download_and_process():
            try:
                download_video(url, save_path)
                
                if not os.path.exists(save_path):
                     pass
                
                jobs[job_id]["video_path"] = save_path
                # Pass sync_mode
                process_video_task(job_id, save_path, target_lang, voice_gender, sync_mode, source_lang, audio_only, model_size)
            except Exception as e:
                logger.error(f"Download/Process failed: {e}")
                jobs[job_id]["status"] = "failed"
                jobs[job_id]["error"] = str(e)
        
        thread = threading.Thread(target=download_and_process)
        thread.start()
        
        return jsonify({"success": True, "job_id": job_id})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/status/<job_id>', methods=['GET'])
def get_status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"success": False, "error": "Job not found"}), 404
        
    return jsonify(job)

@app.route('/api/download/<filename>')
def download_file(filename):
    return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=9090, debug=True)