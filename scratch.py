import os
import subprocess

chunk_files = ["temp/66cf32eb-bf18-4fdd-a827-9d582d9e9b3e/seg_0.mp3", "temp/66cf32eb-bf18-4fdd-a827-9d582d9e9b3e/seg_1.mp3", "temp/66cf32eb-bf18-4fdd-a827-9d582d9e9b3e/seg_2.mp3"]
output_path = "temp_scratch_merged.mp3"

filter_complex_parts = [
    "[0]afade=t=in:st=0:d=0.01,afade=t=out:st=10:d=0.01,adelay=0|0[s0]",
    "[1]afade=t=in:st=0:d=0.01,afade=t=out:st=10:d=0.01,adelay=6000|6000[s1]",
    "[2]afade=t=in:st=0:d=0.01,afade=t=out:st=10:d=0.01,adelay=12000|12000[s2]",
    "[s0][s1][s2]amix=inputs=3:dropout_transition=0:normalize=0[out]"
]

cmd = [
    "./venv/bin/ffmpeg",
    "-i", chunk_files[0],
    "-i", chunk_files[1],
    "-i", chunk_files[2],
    "-filter_complex", ";".join(filter_complex_parts),
    "-map", "[out]",
    "-c:a", "libmp3lame", "-q:a", "2",
    "-y", output_path
]
subprocess.run(cmd, check=True)
