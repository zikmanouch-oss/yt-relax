"""Montage ffmpeg : image fixe + boucle audio sur la durée voulue."""
from __future__ import annotations

import subprocess


def render(image: str, audio_loop: str, seconds: int, out: str, fps: int = 2) -> None:
    fade_out = max(1, seconds - 10)
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-stats", "-stats_period", "60",
        "-loop", "1", "-framerate", str(fps), "-i", image,
        "-stream_loop", "-1", "-i", audio_loop,
        "-t", str(seconds),
        "-af", f"afade=t=in:d=5,afade=t=out:st={fade_out}:d=10",
        "-c:v", "libx264", "-preset", "veryfast", "-tune", "stillimage",
        "-crf", "26", "-pix_fmt", "yuv420p", "-r", str(fps), "-g", str(fps * 10),
        "-c:a", "aac", "-b:a", "160k", "-ar", "44100",
        "-movflags", "+faststart",
        out,
    ]
    subprocess.run(cmd, check=True)
