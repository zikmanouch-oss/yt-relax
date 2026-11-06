"""Génère une vidéo de pluie réaliste et la publie sur YouTube.

Usage :
    python -m src.main                          # vidéo complète + publication
    python -m src.main --hours 0.05 --dry-run   # test de 3 min, sans publication
"""
from __future__ import annotations

import argparse
import json
import random
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml

from . import footage, metadata, soundscape, sources, visual

ROOT = Path(__file__).resolve().parent.parent
HISTORY = ROOT / "history.json"


def load_history() -> list:
    if HISTORY.exists():
        return json.loads(HISTORY.read_text(encoding="utf-8"))
    return []


FAMILY = {"fireplace": "fireplace", "ocean": "ocean", "waterfall": "waterfall", "binaural": "binaural"}  # toutes les autres ambiances = « rain »


def pick_variant(cfg: dict, history: list) -> dict:
    """Équilibrage automatique (demande du propriétaire, 06/11) : on publie la famille
    d'ambiances (pluie / feu / océan) qui a le moins de vidéos sur la chaîne, écrans noirs
    compris. En cas d'égalité : océan, puis feu, puis pluie. Dans une famille, les
    variantes de config.yaml tournent dans l'ordre."""
    counts = {"ocean": 0, "fireplace": 0, "waterfall": 0, "binaural": 0, "rain": 0}
    for h in history:
        counts[FAMILY.get(h.get("theme"), "rain")] += 1
    family = min(("ocean", "fireplace", "waterfall", "binaural", "rain"), key=lambda f: counts[f])
    options = [v for v in cfg["variants"] if FAMILY.get(v["theme"], "rain") == family]
    if not options:
        options = [{"theme": family, "thunder": False}]
    done = [h for h in history if FAMILY.get(h.get("theme"), "rain") == family and not h.get("black")]
    print(f"Équilibre des ambiances : {counts} → {family}", flush=True)
    return options[len(done) % len(options)]


def step(msg: str, t0: list) -> None:
    now = time.time()
    print(f"[{now - t0[0]:6.0f} s] {msg}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=float, default=None)
    ap.add_argument("--dry-run", action="store_true", help="génère sans publier")
    ap.add_argument("--out", default="out")
    ap.add_argument("--theme", default=None, help="force une ambiance (ex. fireplace)")
    ap.add_argument("--thunder", action="store_true", help="avec --theme : ajoute du tonnerre lointain")
    ap.add_argument("--black", action="store_true", help="version écran noir (son seul, image noire)")
    ap.add_argument("--beat", type=float, default=None, help="binaural : battement en Hz (10 alpha, 6 thêta, 2.5 delta)")
    ap.add_argument("--force", action="store_true", help="ignore le plafond quotidien (exceptionnel)")
    args = ap.parse_args()

    cfg = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    hours = args.hours if args.hours is not None else float(cfg["hours"])
    seconds = int(hours * 3600)
    history = load_history()
    if not args.dry_run and not args.force:
        # plafond déclaré à Google : 3 publications par « jour de quota » (minuit heure du Pacifique)
        from zoneinfo import ZoneInfo
        pt = ZoneInfo("America/Los_Angeles")
        today = datetime.now(pt).date()
        done = [h for h in history if datetime.fromisoformat(h["date"]).astimezone(pt).date() == today]
        if len(done) >= int(cfg.get("max_per_day", 3)):
            print(f"::notice::Déjà {len(done)} publications aujourd'hui (plafond {cfg.get('max_per_day', 3)}) : rien de publié.")
            return
    variant = pick_variant(cfg, history)
    if args.theme:
        if args.theme not in cfg["themes"] or args.theme == "thunder_sound":
            raise SystemExit(f"Ambiance inconnue : {args.theme}")
        variant = {"theme": args.theme, "thunder": args.thunder}
        if args.theme == "binaural":
            variant["beat"] = args.beat or 10
    black = args.black
    if black and any(h.get("black") and h.get("theme") == variant["theme"] for h in history):
        # règle du propriétaire (06/11) : un seul écran noir par ambiance
        raise SystemExit(f"Un écran noir existe déjà pour l'ambiance « {variant['theme']} » : publication annulée.")
    theme, thunder = variant["theme"], bool(variant["thunder"])
    beat = float(variant.get("beat", 10)) if theme == "binaural" else None
    seed = int(time.time()) % 1_000_000
    rng = random.Random(seed)
    t0 = [time.time()]

    recent = history[-6:]
    avoid_clips = {i for h in recent for i in h.get("clip_ids", [])}
    avoid_sounds = {i for h in recent for i in h.get("sound_ids", [])}
    blocked = {int(i) for i in cfg.get("blocked_clips") or []}

    out = Path(args.out)
    assets = out / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    # pour l'alerte d'échec : ambiance choisie, lisible par le workflow
    (out / "choice.txt").write_text(
        theme + (f" {beat:g} Hz" if beat else "") + (" + orage" if thunder else "") + (" écran noir" if black else ""),
        encoding="utf-8")
    step(f"Ambiance « {theme} », battement={beat}, tonnerre={thunder}, écran noir={black}, {hours:g} h, graine {seed}", t0)

    # 1. Médias réels
    tcfg = cfg["themes"][theme]
    n_clips = 2 if black else int(cfg.get("clips_per_video", 8))  # écran noir : clips pour la miniature seulement
    clips = sources.video_clips(rng.choice(tcfg["video"]), n_clips, assets, rng, avoid_clips, blocked)
    for q in tcfg["video"]:
        if len(clips) >= 4:
            break
        clips += sources.video_clips(q, n_clips - len(clips), assets, rng,
                                     avoid_clips | {c["id"] for c in clips}, blocked)
    if len(clips) < (1 if black else 3):
        raise SystemExit("Pas assez de clips vidéo exploitables.")
    sounds = sources.freesound_sounds(rng.choice(tcfg["sound"]), int(cfg.get("sounds_per_video", 5)),
                                      assets, rng, avoid=avoid_sounds)
    if len(sounds) < 3:
        sounds += sources.freesound_sounds(tcfg.get("fallback_sound", "rain"), 5 - len(sounds), assets, rng,
                                           avoid=avoid_sounds | {s["id"] for s in sounds})
    thunders = []
    if thunder:
        thunders = sources.freesound_sounds(rng.choice(cfg["themes"]["thunder_sound"]), 3, assets, rng, min_dur=8)
    step("Médias téléchargés", t0)

    # 2. Vidéo : clips normalisés → segment bouclable (sauf écran noir)
    segment = str(out / "segment.mp4")
    if black:
        frame = footage.frame(clips[0]["path"], 3.0, str(out / "frame.png"))
    else:
        norm = [footage.normalize(c["path"], str(assets / f"n{i}.mp4")) for i, c in enumerate(clips)]
        seg_target = min(int(cfg.get("segment_minutes", 15) * 60), max(60, seconds))
        loop_len = footage.build_segment(norm, seg_target, segment, rng, cfg.get("video_maxrate", "3M"))
        step(f"Segment vidéo de {loop_len / 60:.1f} min prêt", t0)

    # 3. Son : mixage des enregistrements réels
    audio = str(out / "audio.m4a")
    soundscape.mix([s["path"] for s in sounds], [s["path"] for s in thunders], seconds, audio, seed,
                   beat=beat, carrier=float(tcfg.get("carrier_hz", 200)), bed_gain=float(tcfg.get("bed_gain", 1.0)))
    step("Paysage sonore mixé", t0)

    # 4. Miniature + textes
    if not black:
        frame = footage.frame(segment, rng.uniform(5, max(6, loop_len - 5)), str(out / "frame.png"))
    meta = metadata.build(theme, thunder, hours, seed, clips, sounds + thunders, black=black, beat=beat)
    playlist_for_theme = tcfg["playlist"] if "playlist" in tcfg else cfg.get("playlist_id")
    meta["description"] = metadata.add_links(meta["description"], theme, playlist_for_theme)
    meta["localizations"] = {"ar": metadata.arabic(theme, thunder, hours, black, playlist_for_theme, beat=beat)}
    meta["clips"] = [{"id": c["id"], "page": c.get("page", "")} for c in clips]
    thumb = str(out / "thumb.jpg")
    visual.thumbnail(frame, meta["thumb_line1"], meta["thumb_line2"], thumb)
    (out / "metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    shutil.rmtree(assets, ignore_errors=True)  # libère le disque avant l'assemblage final

    # 5. Assemblage final (copie directe, sans réencodage)
    video = str(out / "video.mp4")
    if black:
        footage.black_mux(audio, seconds, video)
    else:
        footage.final_mux(segment, audio, seconds, video)
    step(f"Vidéo finale : {Path(video).stat().st_size / 1e9:.2f} Go", t0)

    if args.dry_run:
        print("Mode test : pas de publication.")
        return

    from . import upload
    if not upload.credentials_available():
        raise SystemExit("Identifiants YouTube absents (secrets YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN).")
    Path(segment).unlink(missing_ok=True)
    up_cfg = dict(cfg)
    if "playlist" in tcfg:
        up_cfg["playlist_id"] = tcfg["playlist"]
    video_id = upload.upload(video, thumb, meta, up_cfg)
    entry = {
        "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "video_id": video_id,
        "title": meta["title"],
        "hours": hours,
        "seed": seed,
        "theme": theme,
        "thunder": thunder,
        "black": black,
        "beat": beat,
        "clip_ids": [c["id"] for c in clips],
        "sound_ids": [s["id"] for s in sounds],
    }
    (out / "history_entry.json").write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
    history.append(entry)
    HISTORY.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
    step("Terminé", t0)


if __name__ == "__main__":
    main()
