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

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_STT_URL = "https://api.groq.com/openai/v1/audio/transcriptions"

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

def transcribe_audio_sarvam(audio_path: str, source_lang: str = None) -> Dict[str, Any]:
    """
    Transcribe audio file using Sarvam AI Saaras STT API with word/chunk timestamps.
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
        "srt": srt_content,
        "engine": "sarvam"
    }

def transcribe_audio_groq(audio_path: str, source_lang: str = None) -> Dict[str, Any]:
    """
    Transcribe audio file using Groq Cloud Whisper API (whisper-large-v3).
    Runs 100% in the cloud on Groq LPUs (ultra-fast ~0.5s, 0 local compute/RAM).
    """
    api_key = os.getenv("GROQ_API_KEY", GROQ_API_KEY)
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not configured in .env or environment")

    logger.info(f"Starting Groq Cloud Whisper STT for {audio_path} (source_lang={source_lang})")

    data = {
        "model": "whisper-large-v3",
        "response_format": "verbose_json"
    }
    if source_lang:
        code = source_lang.split('-')[0].lower()
        data["language"] = code

    with open(audio_path, "rb") as f:
        files = {
            "file": (os.path.basename(audio_path), f, "audio/wav")
        }
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        response = requests.post(
            GROQ_STT_URL,
            headers=headers,
            files=files,
            data=data,
            timeout=60
        )

    if response.status_code != 200:
        logger.error(f"Groq STT failed with code {response.status_code}: {response.text}")
        raise RuntimeError(f"Groq STT API error: {response.text}")

    res_json = response.json()
    transcript = res_json.get("text", "").strip()
    detected_lang = res_json.get("language", "en")
    raw_segments = res_json.get("segments", [])

    segments = []
    if raw_segments:
        for idx, seg in enumerate(raw_segments):
            start = round(float(seg.get("start", 0.0)), 2)
            end = round(float(seg.get("end", 0.0)), 2)
            text = seg.get("text", "").strip()
            if not text:
                continue
            segments.append({
                "id": idx,
                "start": start,
                "end": end,
                "text": text,
                "words": text.split()
            })

    if not segments and transcript:
        from processors.audio_extractor import get_media_duration
        dur = get_media_duration(audio_path)
        segments.append({
            "id": 0,
            "start": 0.0,
            "end": round(dur if dur > 0 else 5.0, 2),
            "text": transcript,
            "words": transcript.split()
        })

    srt_content = generate_srt(segments)
    logger.info(f"Groq Cloud STT complete. Transcribed {len(segments)} segments. Detected language: {detected_lang}")
    return {
        "language": detected_lang,
        "segments": segments,
        "srt": srt_content,
        "engine": "groq"
    }

def transcribe_audio_dummy(audio_path: str, source_lang: str = None) -> Dict[str, Any]:
    """
    Zero-credit dummy transcription engine for development and testing.
    Analyzes actual audio timing and provides synchronized dialogue segments without burning Sarvam credits.
    """
    logger.info(f"Using Dummy/Free STT engine for {audio_path}")
    from processors.audio_extractor import get_media_duration
    
    duration = get_media_duration(audio_path)
    if duration <= 0:
        duration = 8.0
        
    detected_lang = source_lang.split('-')[0].lower() if source_lang else "en"
    
    # Natural conversational phrases for testing
    sample_phrases = [
        "Welcome to this video tutorial and presentation.",
        "In this section we explore the key ideas step by step.",
        "Notice how each concept connects smoothly to the next point.",
        "This helps make learning simple and completely clear.",
        "Thank you for watching and following along with our lesson today."
    ]
    
    # Determine segment windows based on actual media duration
    target_seg_len = 3.2
    num_segs = max(1, int(round(duration / target_seg_len)))
    seg_duration = duration / num_segs
    
    segments = []
    for i in range(num_segs):
        start_t = round(i * seg_duration, 2)
        end_t = round(duration if i == num_segs - 1 else (i + 1) * seg_duration, 2)
        phrase = sample_phrases[i % len(sample_phrases)]
        segments.append({
            "id": i,
            "start": start_t,
            "end": end_t,
            "text": phrase,
            "words": phrase.split()
        })
        
    srt_content = generate_srt(segments)
    logger.info(f"Dummy STT complete: generated {len(segments)} timed segments spanning {duration:.2f}s.")
    return {
        "language": detected_lang,
        "segments": segments,
        "srt": srt_content,
        "engine": "dummy"
    }

def transcribe_audio(audio_path: str, source_lang: str = None, model_size: str = "small") -> Dict[str, Any]:
    """
    Unified transcription entrypoint.
    Checks DUBBING_ENGINE ('sarvam', 'groq', or 'dummy').
    """
    engine = os.getenv("DUBBING_ENGINE", "groq").strip().lower()
    sarvam_key = os.getenv("SARVAM_API_KEY", SARVAM_API_KEY)
    groq_key = os.getenv("GROQ_API_KEY", GROQ_API_KEY)
    
    # Tier 1: Production Sarvam AI pipeline
    if engine == "sarvam" and sarvam_key:
        try:
            return transcribe_audio_sarvam(audio_path, source_lang=source_lang)
        except Exception as e:
            logger.warning(f"Sarvam STT failed: {e}. Falling back to Groq/Dummy STT.")
            
    # Tier 2: Groq Cloud API (Free, fast cloud Whisper large-v3)
    if (engine == "groq" or not sarvam_key) and groq_key:
        try:
            return transcribe_audio_groq(audio_path, source_lang=source_lang)
        except Exception as e:
            logger.warning(f"Groq STT failed: {e}. Falling back to Dummy STT.")
            return transcribe_audio_dummy(audio_path, source_lang=source_lang)
            
    # Tier 3: Zero-credit dummy STT fallback
    return transcribe_audio_dummy(audio_path, source_lang=source_lang)
