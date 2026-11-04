"""Génère une vidéo de pluie et la publie sur YouTube.

Usage :
    python -m src.main                 # vidéo complète + publication
    python -m src.main --hours 0.05 --dry-run   # test de 3 min, sans publication
"""
from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml

from . import audio, metadata, render, visual

ROOT = Path(__file__).resolve().parent.parent
HISTORY = ROOT / "history.json"


def load_history() -> list:
    if HISTORY.exists():
        return json.loads(HISTORY.read_text(encoding="utf-8"))
    return []


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=float, default=None)
    ap.add_argument("--dry-run", action="store_true", help="génère sans publier")
    ap.add_argument("--out", default="out")
    args = ap.parse_args()

    cfg = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    hours = args.hours if args.hours is not None else float(cfg["hours"])
    history = load_history()
    variant = cfg["variants"][len(history) % len(cfg["variants"])]
    seed = int(time.time()) % 1_000_000

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    wav, img, thumb, mp4 = (out / n for n in ("loop.wav", "scene.png", "thumb.jpg", "video.mp4"))

    loop_s = min(int(cfg.get("loop_minutes", 10) * 60), max(60, int(hours * 3600)))
    print(f"Variante {variant} — graine {seed} — {hours:g} h", flush=True)

    t0 = time.time()
    audio.write_wav(str(wav), audio.synth_rain(audio.RainParams(
        loop_seconds=loop_s, intensity=variant["intensity"], thunder=variant["thunder"], seed=seed)))
    print(f"Son généré en {time.time() - t0:.0f} s", flush=True)

    visual.rain_scene(seed, str(img))
    meta = metadata.build(variant["intensity"], variant["thunder"], hours, seed)
    visual.thumbnail(str(img), meta["thumb_line1"], meta["thumb_line2"], str(thumb))
    (out / "metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    t0 = time.time()
    render.render(str(img), str(wav), int(hours * 3600), str(mp4), fps=int(cfg.get("fps", 2)))
    print(f"Montage terminé en {time.time() - t0:.0f} s — {mp4.stat().st_size / 1e6:.0f} Mo", flush=True)

    if args.dry_run:
        print("Mode test : pas de publication.")
        return

    from . import upload
    if not upload.credentials_available():
        raise SystemExit("Identifiants YouTube absents (secrets YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN).")

    video_id = upload.upload(str(mp4), str(thumb), meta, cfg)
    history.append({
        "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "video_id": video_id,
        "title": meta["title"],
        "hours": hours,
        "seed": seed,
        **variant,
    })
    HISTORY.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    os.environ.setdefault("PYTHONUNBUFFERED", "1")
    main()
