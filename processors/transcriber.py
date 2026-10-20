
import os
# Fix for PyTorch MPS float64 error
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

import whisper
import logging
from typing import Dict, List, Any
import torch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set optimal CPU thread count for Whisper transcription
if hasattr(os, "cpu_count") and os.cpu_count():
    torch.set_num_threads(os.cpu_count())

# Load models lazily
MODELS = {}
DEVICE = "cpu" # Force CPU for Mac stability

def get_model(size="small"):
    global MODELS
    if size not in MODELS:
        logger.info(f"Loading Whisper model '{size}' on {DEVICE}...")
        try:
            model_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".models")
            os.makedirs(model_dir, exist_ok=True)
            MODELS[size] = whisper.load_model(size, device=DEVICE, download_root=model_dir)
            logger.info(f"Whisper model '{size}' loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load Whisper model '{size}': {e}")
            raise RuntimeError(f"Failed to load model {size}")
    return MODELS[size]

# Pre-load small model (for fast startup)
try:
    get_model("small")
except:
    pass

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


def transcribe_audio(audio_path: str, source_lang: str = None, model_size: str = "small") -> Dict[str, Any]:
    """
    Transcribe audio file using Whisper to get text and word-level timestamps.

    Args:
        audio_path: Path to the audio file (WAV).
        source_lang: Optional ISO language code (e.g. 'hi', 'en').
        model_size: 'small' or 'medium'.

    Returns:
        Dict containing language and segments with word timestamps.
    """
    model = get_model(model_size)
    if model is None:
        raise RuntimeError("Whisper model not initialized.")

    try:
        logger.info(f"Starting transcription for {audio_path} (lang={source_lang}, model={model_size})")
        
        # word_timestamps=True is CRITICAL for sync
        transcribe_opts = {
            "word_timestamps": True,
            "fp16": False,
            "condition_on_previous_text": False,
            "temperature": (0.0, 0.2),
            "beam_size": 1,
            "best_of": 1
        }
        if source_lang:
            transcribe_opts["language"] = source_lang

        try:
             result = model.transcribe(
                audio_path,
                **transcribe_opts
            )
        except RuntimeError as re:
            if "0 elements" in str(re):
                 logger.warning(f"Whisper failed to process audio (likely empty/silent): {re}")
                 # Return empty result
                 return {
                     "language": source_lang if source_lang else "en",
                     "segments": [],
                     "srt": ""
                 }
            raise re

        # Structure the output strictly
        
        # Structure the output strictly
        output = {
            "language": result.get("language", "en"),
            "segments": []
        }

        for segment in result.get("segments", []):
            seg_data = {
                "id": segment.get("id"),
                "start": segment.get("start"),
                "end": segment.get("end"),
                "text": segment.get("text", "").strip(),
                "words": []
            }
            
            # Extract word level info if available
            words = segment.get("words", [])
            for word in words:
                seg_data["words"].append({
                    "word": word.get("word", "").strip(),
                    "start": word.get("start"),
                    "end": word.get("end")
                })
            
            output["segments"].append(seg_data)

        # Generate SRT content
        srt_content = generate_srt(output["segments"])
        output["srt"] = srt_content

        logger.info(f"Transcription complete. Detected language: {output['language']}")
        return output

    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise RuntimeError(f"Transcription failed: {e}")

if __name__ == "__main__":
    # basic test if needed
    pass
