
"""
Video Assembler Module.
Combines the dubbed audio with the original video.
"""

import os
import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def assemble_video(original_video: str, dubbed_audio: str, output_path: str) -> str:
    """
    Replace video audio with dubbed version.
    
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
            
        # FFmpeg command
        # -i video
        # -i audio
        # -c:v copy (copy video stream, no re-encode)
        # -c:a aac (encode audio to AAC)
        # -map 0:v:0 (take video from first input)
        # -map 1:a:0 (take audio from second input)
        # -shortest (finish when shorter stream ends)
        # -y (overwrite)
        
        # FFmpeg command
        # Replace audio track with dubbed version
        
        command = [
            "ffmpeg",
            "-i", original_video,
            "-i", dubbed_audio,
            "-c:v", "copy",
            "-c:a", "aac",
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
