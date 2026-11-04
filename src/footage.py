"""Montage vidéo à partir de vrais clips de pluie.

1. Chaque clip est mis au format 1920×1080, 30 i/s, sans son.
2. On compose un segment long (≈ 15 min) : extraits tirés au hasard,
   enchaînés par fondus lents. Le segment se termine sur l'image exacte
   par laquelle il commence → la boucle est invisible.
3. Le segment est répété (copie directe, sans réencodage) sur toute la durée.
"""
from __future__ import annotations

import json
import random
import subprocess
from pathlib import Path

FPS = 30
XFADE = 2.5  # durée des fondus entre extraits (s)


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def probe_duration(path: str) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", path],
                         check=True, capture_output=True, text=True).stdout
    return float(json.loads(out)["format"]["duration"])


def normalize(src: str, dest: str) -> str:
    _run(["ffmpeg", "-y", "-v", "error", "-i", src, "-an",
          "-vf", f"scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps={FPS},format=yuv420p",
          "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", dest])
    return dest


def build_segment(clips: list[str], target_s: int, dest: str, rng: random.Random,
                  maxrate: str = "3M") -> float:
    durs = [probe_duration(c) for c in clips]
    occ, total, last = [], 0.0, -1
    while total < target_s:
        i = rng.choice([k for k in range(len(clips)) if k != last] or [0])
        d = durs[i]
        length = min(d - 0.2, rng.uniform(15, 35))
        if length < XFADE * 2 + 1:
            last = i
            continue
        start = rng.uniform(0, max(0.0, d - length - 0.1))
        occ.append((i, start, length))
        total += length - XFADE
        last = i
    # retour sur le premier extrait, même point de départ → raccord parfait
    i0, s0, _ = occ[0]
    occ.append((i0, s0, XFADE + 1.0))

    inputs, filters = [], []
    for k, (i, s, l) in enumerate(occ):
        inputs += ["-ss", f"{s:.3f}", "-t", f"{l:.3f}", "-i", clips[i]]
        filters.append(f"[{k}:v]settb=AVTB,setpts=PTS-STARTPTS,fps={FPS}[s{k}]")
    prev, offset = "s0", 0.0
    for k in range(1, len(occ)):
        offset += occ[k - 1][2] - XFADE
        filters.append(f"[{prev}][s{k}]xfade=transition=fade:duration={XFADE}:offset={offset:.3f}[x{k}]")
        prev = f"x{k}"
    loop_len = offset  # début du dernier fondu
    filters.append(f"[{prev}]trim=start={XFADE}:duration={loop_len:.3f},setpts=PTS-STARTPTS[out]")

    script = Path(dest).with_suffix(".filter")
    script.write_text(";\n".join(filters), encoding="utf-8")
    _run(["ffmpeg", "-y", "-v", "error", "-stats", "-stats_period", "60", *inputs,
          "-filter_complex_script", str(script), "-map", "[out]",
          "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
          "-maxrate", maxrate, "-bufsize", "6M", "-g", str(FPS * 2), "-pix_fmt", "yuv420p", dest])
    return loop_len


def frame(video: str, at_s: float, dest: str) -> str:
    _run(["ffmpeg", "-y", "-v", "error", "-ss", f"{at_s:.2f}", "-i", video, "-frames:v", "1", dest])
    return dest


def final_mux(segment: str, audio: str, seconds: int, dest: str) -> None:
    _run(["ffmpeg", "-y", "-v", "error", "-stats", "-stats_period", "60",
          "-stream_loop", "-1", "-i", segment, "-i", audio,
          "-map", "0:v", "-map", "1:a", "-c", "copy", "-t", str(seconds), dest])
