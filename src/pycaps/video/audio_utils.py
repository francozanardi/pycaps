import subprocess
from typing import Optional
from pycaps.logger import logger

def extract_audio_for_whisper(video: str, output: str, start: Optional[float] = None, end: Optional[float] = None) -> None:
    try:
        cmd = ["ffmpeg", "-y"]

        if start is not None:
            cmd += ["-ss", str(start)]

        cmd += ["-i", video]

        if end is not None:
            cmd += ["-to", str(end)]

        cmd += [
            "-vn",
            "-ac", "1",
            "-ar", "16000",
            "-c:a", "pcm_s16le",
            output,
            "-loglevel", "error",
            "-hide_banner",
        ]

        subprocess.run(cmd, check=True)
    except Exception as e:
        logger().error("Unable to extract audio from video. Are you sure your video has audio?. Ffmpeg error: " + e)
