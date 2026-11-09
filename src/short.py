"""Short YouTube (40 s, vertical) qui renvoie vers une vidéo de 8 h.

Usage :
    python -m src.short                 # prend la dernière vidéo 8 h sans Short
    python -m src.short --video ID      # Short pour cette vidéo
    python -m src.short --dry-run       # génère sans publier

Le Short reprend l'ambiance de la vidéo (vrais clips Pixabay recadrés en 1080×1920,
vrais sons Freesound CC0, ou la musique de fréquences pour « frequency »), avec un texte
discret « 8 hours on my channel ». Après publication, relier le Short à la vidéo longue
dans YouTube Studio (Short → « Vidéo associée ») : l'API ne le permet pas.
"""
from __future__ import annotations

import argparse
import json
import random
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml
from PIL import Image, ImageDraw

from . import footage, soundscape, sources, tonal
from .visual import _font

ROOT = Path(__file__).resolve().parent.parent
SHORTS = ROOT / "shorts.json"
SECONDS = 40
W, H = 1080, 1920

TITLES = {
    "window": "Rain on the Window to Fall Asleep Fast 🌧️ #shorts",
    "forest": "Forest Rain Sounds for Deep Sleep 🌧️ #shorts",
    "lake": "Gentle Rain on a Calm Lake for Sleep 🌧️ #shorts",
    "roof": "Rain on a Cabin Roof for Deep Sleep 🌧️ #shorts",
    "fireplace": "Crackling Fireplace to Fall Asleep 🔥 #shorts",
    "ocean": "Ocean Waves Sounds for Deep Sleep 🌊 #shorts",
    "waterfall": "Waterfall Sounds to Calm Your Mind 💧 #shorts",
    "binaural": "Alpha Waves 10 Hz to Ease Stress 🎧 #shorts",
    "frequency": "{hz} Hz Calming Piano for Anxiety & Sleep 🎹 #shorts",
}
AR_TITLES = {
    "window": "صوت المطر على النافذة للنوم بسرعة 🌧️ #shorts",
    "forest": "صوت المطر في الغابة للنوم العميق 🌧️ #shorts",
    "lake": "صوت المطر على البحيرة للنوم 🌧️ #shorts",
    "roof": "صوت المطر على السقف للنوم العميق 🌧️ #shorts",
    "fireplace": "صوت المدفأة وطقطقة الحطب للنوم 🔥 #shorts",
    "ocean": "صوت أمواج البحر للنوم العميق 🌊 #shorts",
    "waterfall": "صوت الشلال لتهدئة الأعصاب 💧 #shorts",
    "binaural": "موجات ألفا 10 هرتز لتخفيف التوتر 🎧 #shorts",
    "frequency": "موسيقى هادئة {hz} هرتز للتخلص من القلق والنوم 🎹 #shorts",
}
LINE1 = {"window": "RAIN ON THE WINDOW", "forest": "FOREST RAIN", "lake": "RAIN ON THE LAKE",
         "roof": "RAIN ON THE ROOF", "fireplace": "COZY FIREPLACE", "ocean": "OCEAN WAVES",
         "waterfall": "WATERFALL", "binaural": "ALPHA WAVES 10 HZ", "frequency": "{hz} HZ CALM MUSIC"}
HASHTAGS = {"fireplace": "#fireplace #sleepsounds", "ocean": "#oceanwaves #sleepsounds",
            "waterfall": "#waterfallsounds #sleepsounds", "binaural": "#binauralbeats #stressrelief",
            "frequency": "#{hz}hz #relaxingmusic"}


def _overlay(theme: str, hz: str, path: str) -> None:
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # bandeau sombre très doux en haut et en bas pour la lisibilité
    for y in range(420):
        a = int(150 * (1 - y / 420))
        d.line([(0, y), (W, y)], fill=(0, 0, 0, a))
    for y in range(H - 760, H):
        a = int(140 * min(1, (y - (H - 760)) / 260))
        d.line([(0, y), (W, y)], fill=(0, 0, 0, a))
    sub = "FOR ANXIETY & DEEP SLEEP" if theme in ("frequency", "binaural") else "FOR DEEP SLEEP & CALM"
    # le bas de l'écran (~25 %) est masqué par l'interface des Shorts : textes placés plus haut
    lines = [(LINE1[theme].format(hz=hz), 84, 190), (sub, 52, 300),
             ("Full 8-hour version on my channel", 46, H - 640), ("Calm Haven Sounds", 46, H - 570)]
    for text, size, y in lines:
        f = _font(size)
        while d.textlength(text, font=f) > W - 80:
            size -= 4
            f = _font(size)
        x = (W - d.textlength(text, font=f)) / 2
        d.text((x + 3, y + 4), text, font=f, fill=(0, 0, 0, 170))
        d.text((x, y), text, font=f, fill=(255, 255, 255, 240))
    img.save(path)


def _video(clips: list[str], overlay: str, audio: str, dest: str, rng: random.Random) -> None:
    n = len(clips)
    xf = 1.5
    seg = (SECONDS + xf * (n - 1)) / n
    inputs, filters = [], []
    for k, c in enumerate(clips):
        d = footage.probe_duration(c)
        start = rng.uniform(0, max(0.0, d - seg - 0.2))
        inputs += ["-ss", f"{start:.2f}", "-t", f"{seg:.2f}", "-i", c]
        filters.append(f"[{k}:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
                       f"fps=30,format=yuv420p,settb=AVTB,setpts=PTS-STARTPTS[s{k}]")
    prev, offset = "s0", 0.0
    for k in range(1, n):
        offset += seg - xf
        filters.append(f"[{prev}][s{k}]xfade=transition=fade:duration={xf}:offset={offset:.2f}[x{k}]")
        prev = f"x{k}"
    filters.append(f"[{prev}][{n}:v]overlay=0:0,format=yuv420p[v]")
    cmd = (["ffmpeg", "-y", "-v", "error"] + inputs + ["-i", overlay, "-i", audio,
           "-filter_complex", ";".join(filters), "-map", "[v]", "-map", f"{n + 1}:a",
           "-t", str(SECONDS), "-c:v", "libx264", "-preset", "medium", "-crf", "20",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", dest])
    subprocess.run(cmd, check=True)


def _today_count(entries: list, tz: str = "America/Los_Angeles") -> int:
    from zoneinfo import ZoneInfo
    pt = ZoneInfo(tz)
    today = datetime.now(pt).date()
    return sum(1 for e in entries if datetime.fromisoformat(e["date"]).astimezone(pt).date() == today)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--out", default="out")
    args = ap.parse_args()

    cfg = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    history = json.loads((ROOT / "history.json").read_text(encoding="utf-8"))
    shorts = json.loads(SHORTS.read_text(encoding="utf-8")) if SHORTS.exists() else []
    if not args.dry_run and _today_count(history + shorts) >= int(cfg.get("max_per_day", 3)):
        print("::notice::Plafond quotidien de mises en ligne atteint : pas de Short aujourd'hui.")
        return
    per_video: dict[str, int] = {}
    for sh in shorts:
        per_video[sh["for_video"]] = per_video.get(sh["for_video"], 0) + 1
    longs = [h for h in history if h.get("hours", 0) >= 1 and not h.get("black")]
    freq = ("frequency", "binaural")
    if args.video:
        target = next(h for h in history if h["video_id"] == args.video)
    else:
        # 09/11 : les Shorts de fréquences marchent le mieux → 2 Shorts sur 3 sont des fréquences,
        # jusqu'à 3 Shorts différents par vidéo de fréquences (1 seul pour les autres ambiances)
        def todo(themes_freq: bool) -> list:
            limit = 3 if themes_freq else 1
            c = [h for h in longs if (h["theme"] in freq) == themes_freq and per_video.get(h["video_id"], 0) < limit]
            return sorted(c, key=lambda h: (per_video.get(h["video_id"], 0), h["date"]), reverse=False)
        want_freq = len(shorts) % 3 != 2
        cands = todo(want_freq) or todo(not want_freq)
        if not cands:
            print("::notice::Toutes les vidéos 8 h ont déjà leurs Shorts.")
            return
        # le moins de Shorts d'abord, puis la plus récente
        best = min(per_video.get(h["video_id"], 0) for h in cands)
        target = [h for h in cands if per_video.get(h["video_id"], 0) == best][-1]
    theme, hz = target["theme"], target.get("hz")
    hz_s = f"{hz:g}" if hz else ""
    tcfg = cfg["themes"][theme]
    seed = int(time.time()) % 1_000_000
    rng = random.Random(seed)
    out = Path(args.out)
    assets = out / "short_assets"
    assets.mkdir(parents=True, exist_ok=True)
    print(f"Short pour {target['video_id']} ({theme} {hz_s}) — graine {seed}", flush=True)

    clips = []
    for q in rng.sample(tcfg["video"], len(tcfg["video"])):
        clips += sources.video_clips(q, 3 - len(clips), assets, rng, {c["id"] for c in clips},
                                     {int(i) for i in cfg.get("blocked_clips") or []})
        if len(clips) >= 3:
            break
    if not clips:
        raise SystemExit("Aucun clip exploitable.")

    audio = str(out / "short_audio.m4a")
    if tcfg.get("mode") == "tonal":
        tonal.render(SECONDS, audio, seed, f0=float(hz or 432), beat=float(tcfg.get("binaural_beat", 6)))
    else:
        sounds = sources.freesound_sounds(rng.choice(tcfg["sound"]), 4, assets, rng)
        soundscape.mix([s["path"] for s in sounds], [], SECONDS, audio, seed,
                       beat=target.get("beat"), carrier=float(tcfg.get("carrier_hz", 200)),
                       bed_gain=float(tcfg.get("bed_gain", 1.0)))

    overlay = str(out / "short_overlay.png")
    _overlay(theme, hz_s, overlay)
    video = str(out / "short.mp4")
    _video([c["path"] for c in clips], overlay, audio, video, rng)
    print(f"Short prêt : {Path(video).stat().st_size / 1e6:.1f} Mo", flush=True)

    long_url = f"https://youtu.be/{target['video_id']}"
    title = TITLES[theme].format(hz=hz_s)
    desc = (f"Full 8-hour version, no mid-roll ads: {long_url}\n\n"
            f"{target['title']}\n\n"
            "Real footage and sounds, no talking. Subscribe to Calm Haven Sounds for more: "
            "https://www.youtube.com/@CalmHavenSounds-z4p?sub_confirmation=1\n\n"
            + HASHTAGS.get(theme, "#rainsounds #sleepsounds").format(hz=hz_s) + " #shorts")
    if theme in ("frequency", "binaural"):
        desc = desc.replace("Real footage and sounds, no talking.", "Real footage, original calm music, no talking.")
    meta = {
        "title": title[:100], "description": desc,
        "tags": ["shorts", "sleep sounds", "relaxing", "calm haven sounds", theme],
        "localizations": {"ar": {"title": AR_TITLES[theme].format(hz=hz_s)[:100],
                                 "description": f"النسخة الكاملة 8 ساعات بدون إعلانات في المنتصف: {long_url}\n\n#shorts"}},
    }
    (out / "short_metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.dry_run:
        print("Mode test : pas de publication.")
        return

    from . import upload
    up_cfg = dict(cfg, playlist_id=None, extra_playlists=[])
    thumb = str(out / "short_thumb.jpg")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", "5", "-i", video, "-frames:v", "1", thumb], check=True)
    vid = upload.upload(video, thumb, meta, up_cfg)
    entry = {"date": datetime.now(timezone.utc).isoformat(timespec="seconds"), "video_id": vid,
             "for_video": target["video_id"], "theme": theme, "title": meta["title"],
             "clip_ids": [c["id"] for c in clips]}
    (out / "short_entry.json").write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Short publié : https://youtube.com/shorts/{vid} → relier à {long_url} dans Studio")


if __name__ == "__main__":
    main()
