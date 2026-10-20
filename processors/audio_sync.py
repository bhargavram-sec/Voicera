
"""
Audio Synchronizer Module.
Adjusts audio tempo to match original video timing and merges segments.
"""

import os
import subprocess
import logging
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AudioSynchronizer:
    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode

    def merge_segments(self, segments: List[Dict[str, Any]], total_duration: float, output_path: str) -> str:
        """
        Merge all timed segments into single audio track using FFmpeg complex filter.
        Places each segment at its specific timestamp using 'adelay' and mixes them.
        This handles overlaps naturally without drift.
        """
        try:
            if not segments:
                logger.warning("No segments to merge. Generating silent audio.")
                # Generate silent audio of total_duration
                if total_duration <= 0: total_duration = 5.0 # Fallback
                
                cmd = [
                    "ffmpeg", "-f", "lavfi", "-i", f"anullsrc=r=24000:cl=mono", 
                    "-t", str(total_duration), "-c:a", "libmp3lame", "-y", output_path
                ]
                subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                return output_path

            # Inputs
            valid_segments = [s for s in segments if s.get('audio_path_final')]
            
            # PRE-PROCESSING: ADJUST TIMING TO PREVENT OVERLAP
            # cascading delay: if previous segment pushes past current segment's start, we push current segment back.
            time_cursor = 0.0
            
            for seg in valid_segments:
                # Get actual duration of the generated audio
                # Fallback to metadata duration if file check is expensive, but app.py sets 'generated_duration'
                dur = seg.get('generated_duration', 0)
                
                original_start = seg.get('start', 0)
                
                # New start is at least the original start, but pushed if cursor is ahead
                new_start = max(original_start, time_cursor)
                 
                # Update segment with new start
                seg['adjusted_start'] = new_start
                
                # Update cursor
                time_cursor = new_start + dur
            
            # CHUNK PROCESSING
            # ffmpeg command line limit is real. We process in chunks of 50 segments.
            chunk_size = 50
            chunks = [valid_segments[i:i + chunk_size] for i in range(0, len(valid_segments), chunk_size)]
            
            chunk_files = []
            
            for idx, chunk in enumerate(chunks):
                inputs = []
                filter_complex_parts = []
                
                for i, seg in enumerate(chunk):
                    path = seg['audio_path_final']
                    # Use adjusted_start
                    start_ms = int(seg['adjusted_start'] * 1000)
                    
                    inputs.extend(["-i", path])
                    # Add fade in/out (10ms) to avoid clicks
                    # [idx]adeclick,afade=...[s_idx] - adeclick might be too heavy/require dependencies, just afade
                    out_st = max(0, seg.get('generated_duration', 0)-0.01)
                    filter_complex_parts.append(f"[{i}]afade=t=in:st=0:d=0.01,afade=t=out:st={out_st}:d=0.01,adelay={start_ms}|{start_ms}[s{i}]")
                
                sources = "".join([f"[s{i}]" for i in range(len(chunk))])
                # amix: normalize=0 prevents volume drop
                filter_complex_parts.append(f"{sources}amix=inputs={len(chunk)}:dropout_transition=0:normalize=0[out]")
                
                filter_complex = ";".join(filter_complex_parts)
                
                chunk_out = output_path + f".chunk{idx}.mp3"
                chunk_files.append(chunk_out)
                
                cmd = [
                    "ffmpeg",
                    *inputs,
                    "-filter_complex", filter_complex,
                    "-map", "[out]",
                    "-c:a", "libmp3lame", "-q:a", "2",
                    "-y", chunk_out
                ]
                subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Merge chunks
            if len(chunk_files) == 1:
                os.rename(chunk_files[0], output_path)
            else:
                inputs = []
                filter_complex_parts = []
                for i, f in enumerate(chunk_files):
                    inputs.extend(["-i", f])
                    filter_complex_parts.append(f"[{i}]aformat=sample_fmts=fltp:channel_layouts=stereo[s{i}]")

                sources = "".join([f"[s{i}]" for i in range(len(chunk_files))])
                filter_complex_parts.append(f"{sources}amix=inputs={len(chunk_files)}:dropout_transition=0:normalize=0[out]")
                
                cmd = [
                    "ffmpeg",
                    *inputs,
                    "-filter_complex", ";".join(filter_complex_parts),
                    "-map", "[out]",
                    "-c:a", "libmp3lame",
                    "-y", output_path
                ]
                subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                # Cleanup chunks
                for f in chunk_files:
                    if os.path.exists(f): os.remove(f)

            return output_path
            
        except Exception as e:
            logger.error(f"Merge failed: {e}")
            raise RuntimeError(f"Merge failed: {e}")
