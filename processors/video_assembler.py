
"""
Video Assembler Module.
Combines the dubbed audio with the original video.
"""

import os
import subprocess
import logging
from processors.audio_extractor import get_media_duration

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def assemble_video(original_video: str, dubbed_audio: str, output_path: str) -> str:
    """
    Replace video audio with dubbed version.
    If the dubbed audio is slightly longer, gently hold the final video frame so no words are cut off.
    
    Args:
        original_video: Path to input video.
        dubbed_audio: Path to the new audio (translated).
        output_path: Path for final video.
        
    Returns:
        Path to final dubbed video.
    """
    try:
        # Check inputs
        if not os.path.exists(original_video):
            raise FileNotFoundError(f"Video not found: {original_video}")
        if not os.path.exists(dubbed_audio):
            raise FileNotFoundError(f"Audio not found: {dubbed_audio}")
            
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
        vid_dur = get_media_duration(original_video)
        aud_dur = get_media_duration(dubbed_audio)
        
        # If dubbed audio is longer than original video, pad final video frame
        if aud_dur > vid_dur + 0.15:
            diff = aud_dur - vid_dur
            logger.info(f"Dubbed audio ({aud_dur:.2f}s) is longer than video ({vid_dur:.2f}s). Extending final frame by {diff:.2f}s.")
            command = [
                "ffmpeg",
                "-i", original_video,
                "-i", dubbed_audio,
                "-filter_complex", f"[0:v]tpad=stop_mode=clone:stop_duration={diff:.2f}[v]",
                "-map", "[v]",
                "-map", "1:a:0",
                "-c:a", "aac",
                "-shortest",
                "-y",
                output_path
            ]
        else:
            command = [
                "ffmpeg",
                "-i", original_video,
                "-i", dubbed_audio,
                "-c:v", "copy",
                "-c:a", "aac",
                "-af", "apad",
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-shortest",
                "-y",
                output_path
            ]
        
        logger.info(f"Assembling video (dubbed audio only): {original_video} + {dubbed_audio} -> {output_path}")
        
        subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        logger.info("Video assembly complete.")
        return output_path
        
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg assembly failed: {e}")
        raise RuntimeError(f"Video assembly failed: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in assembly: {e}")
        raise RuntimeError(f"Assembly error: {e}")
