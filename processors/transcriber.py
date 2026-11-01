import os
import re
import logging
from typing import Dict, List, Any
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
SARVAM_STT_URL = "https://api.sarvam.ai/speech-to-text"

def format_timestamp(seconds: float) -> str:
    """Convert seconds to SRT timestamp format (HH:MM:SS,mmm)"""
    milliseconds = int((seconds % 1) * 1000)
    minutes = int(seconds // 60)
    hours = int(minutes // 60)
    minutes = minutes % 60
    seconds = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

def generate_srt(segments: List[Dict[str, Any]]) -> str:
    """Generate SRT formatted string from segments."""
    srt_content = []
    for i, seg in enumerate(segments, 1):
        start = format_timestamp(seg['start'])
        end = format_timestamp(seg['end'])
        text = seg['text'].strip()
        srt_content.append(f"{i}\n{start} --> {end}\n{text}\n")
    return "\n".join(srt_content)

def _split_chunk_into_sentences(text: str, start: float, end: float, base_id: int) -> List[Dict[str, Any]]:
    """
    Split a long chunk into sentence-level segments with proportionally distributed timestamps.
    """
    total_duration = max(0.1, end - start)
    # Split by sentence-ending punctuation while preserving them
    raw_sentences = re.split(r'(?<=[.?!])\s+', text.strip())
    sentences = [s.strip() for s in raw_sentences if s.strip()]
    
    if len(sentences) <= 1:
        return [{
            "id": base_id,
            "start": round(start, 2),
            "end": round(end, 2),
            "text": text.strip(),
            "words": []
        }]
    
    total_words = sum(max(1, len(s.split())) for s in sentences)
    segments = []
    cur_start = start
    
    for idx, sentence in enumerate(sentences):
        word_count = max(1, len(sentence.split()))
        seg_duration = (word_count / total_words) * total_duration
        cur_end = min(end, cur_start + seg_duration)
        if idx == len(sentences) - 1:
            cur_end = end
            
        segments.append({
            "id": base_id + idx,
            "start": round(cur_start, 2),
            "end": round(cur_end, 2),
            "text": sentence,
            "words": []
        })
        cur_start = cur_end
        
    return segments

def transcribe_audio(audio_path: str, source_lang: str = None, model_size: str = "small") -> Dict[str, Any]:
    """
    Transcribe audio file using Sarvam AI Saaras STT API with word/chunk timestamps.
    Eliminates local CPU/GPU load and overheating completely.
    """
    api_key = os.getenv("SARVAM_API_KEY", SARVAM_API_KEY)
    if not api_key:
        raise RuntimeError("SARVAM_API_KEY is not configured in .env or environment")

    logger.info(f"Starting Sarvam Saaras STT for {audio_path} (source_lang={source_lang})")
    
    # Map short language codes if needed (e.g., 'hi' -> 'hi-IN')
    lang_code = None
    if source_lang:
        code = source_lang.split('-')[0].lower()
        if code in ['hi', 'en', 'ta', 'te', 'kn', 'ml', 'bn', 'mr', 'gu', 'pa', 'od']:
            lang_code = f"{code}-IN"

    data = {
        "model": "saaras:v3",
        "with_timestamps": "true"
    }
    if lang_code:
        data["language_code"] = lang_code

    with open(audio_path, "rb") as f:
        files = {
            "file": (os.path.basename(audio_path), f, "audio/wav")
        }
        headers = {
            "api-subscription-key": api_key
        }
        
        response = requests.post(SARVAM_STT_URL, headers=headers, files=files, data=data, timeout=60)

    if response.status_code != 200:
        logger.error(f"Sarvam STT failed with code {response.status_code}: {response.text}")
        raise RuntimeError(f"Sarvam STT API error: {response.text}")

    res_json = response.json()
    transcript = res_json.get("transcript", "").strip()
    detected_lang = res_json.get("language_code", "en-IN").split("-")[0]
    timestamps = res_json.get("timestamps", {})
    
    words_or_chunks = timestamps.get("words", [])
    starts = timestamps.get("start_time_seconds", [])
    ends = timestamps.get("end_time_seconds", [])
    
    segments = []
    seg_counter = 0

    if words_or_chunks and starts and ends:
        for chunk_text, chunk_start, chunk_end in zip(words_or_chunks, starts, ends):
            sub_segs = _split_chunk_into_sentences(chunk_text, float(chunk_start), float(chunk_end), seg_counter)
            segments.extend(sub_segs)
            seg_counter += len(sub_segs)
    else:
        # Fallback if no timestamps provided
        segments.append({
            "id": 0,
            "start": 0.0,
            "end": 5.0,
            "text": transcript,
            "words": []
        })

    srt_content = generate_srt(segments)
    
    logger.info(f"Sarvam STT complete. Transcribed {len(segments)} segments. Detected language: {detected_lang}")
    return {
        "language": detected_lang,
        "segments": segments,
        "srt": srt_content
    }
