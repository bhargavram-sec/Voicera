
"""
Audio Extractor Module.
Handles extraction of audio from video files using FFmpeg.
"""

import os
import subprocess
import logging
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_audio(video_path: str, output_path: str) -> str:
    """
    Extract audio from video using FFmpeg.
    Converts to WAV format, 16kHz, mono channel for best compatibility with Whisper.

    Args:
        video_path: Absolute path to the input video file.
        output_path: Absolute path where the output WAV file should be saved.

    Returns:
        str: Path to the extracted audio file.

    Raises:
        RuntimeError: If FFmpeg execution fails or input file is invalid.
        FileNotFoundError: If video_path does not exist.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # FFmpeg command:
    # -i input
    # -vn (disable video)
    # -acodec pcm_s16le (WAV codec)
    # -ar 16000 (16kHz sample rate)
    # -ac 1 (mono channel)
    # -y (overwrite output)
    command = [
        "ffmpeg",
        "-i", video_path,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        "-y",
        output_path
    ]

    try:
        logger.info(f"Extracting audio from {video_path} to {output_path}")
        result = subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Validation
        if not os.path.exists(output_path) or os.path.getsize(output_path) < 1024:
             raise RuntimeError("Extracted audio file is empty or too small. The input video might not have an audio track.")
             
        logger.info("Audio extraction successful")
        return output_path
    except subprocess.CalledProcessError as e:
        error_msg = f"FFmpeg extraction failed: {e.stderr}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error during audio extraction: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

def get_media_duration(file_path: str) -> float:
    """
    Get duration of a media file in seconds using ffprobe.
    """
    if not os.path.exists(file_path):
        return 0.0
    try:
        command = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file_path
        ]
        result = subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return float(result.stdout.strip())
    except Exception as e:
        logger.warning(f"Failed to get duration for {file_path}: {e}")
        return 0.0

if __name__ == "__main__":
    pass
