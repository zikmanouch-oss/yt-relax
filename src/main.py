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
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml

from . import footage, metadata, noise, soundscape, sources, tonal, visual

ROOT = Path(__file__).resolve().parent.parent
HISTORY = ROOT / "history.json"


def load_history() -> list:
    if HISTORY.exists():
        return json.loads(HISTORY.read_text(encoding="utf-8"))
    return []


FAMILY = {"fireplace": "fireplace", "ocean": "ocean", "waterfall": "waterfall", "binaural": "binaural",
          "frequency": "binaural", "brown_noise": "noise", "pink_noise": "noise", "green_noise": "noise",
          "white_noise": "noise"}  # toutes les autres ambiances = « rain »
FAMILIES = ("binaural", "noise", "ocean", "fireplace", "waterfall", "rain")
STATS = ROOT / "stats" / "daily.json"


def family_of(theme: str | None) -> str:
    return FAMILY.get(theme, "rain")


def performance_weights(cfg: dict, history: list, shorts: list, stats: dict | None = None,
                        now: datetime | None = None) -> dict:
    """Poids automatique par famille d'après les vues réelles (stats/daily.json, relevé chaque jour).

    - Vidéos 8 h : vues par semaine d'ancienneté (une vidéo ancienne n'est pas avantagée).
    - Shorts : vues totales (ils font l'essentiel de leurs vues en 48 h), comptées à 15 %
      (beaucoup de vues courtes ; ce sont les vidéos longues qui rapportent des heures de visionnage).
    - Peu de données = prudence : chaque moyenne est tirée vers la moyenne de la chaîne (2 vidéos
      « fictives »), si bien qu'une famille sans chiffres vaut la moyenne et qu'un seul bon Short ne suffit pas.
    Poids auto de 1 à 3, multiplié par le choix manuel de config.yaml (family_weight)."""
    manual = {f: 1.0 for f in FAMILIES}
    manual.update({k: float(v) for k, v in (cfg.get("family_weight") or {}).items() if k in manual})
    if stats is None:
        stats = json.loads(STATS.read_text(encoding="utf-8")) if STATS.exists() else {}
    days = sorted(stats)
    if not days:
        return manual
    views = {vid: int(v.get("views", 0)) for vid, v in stats[days[-1]].get("videos", {}).items()}
    now = now or datetime.now(timezone.utc)

    def age(entry: dict) -> float:
        return (now - datetime.fromisoformat(entry["date"])).total_seconds() / 86400

    longs = {f: [views[h["video_id"]] / max(3.0, age(h)) * 7 for h in history
                 if family_of(h.get("theme")) == f and h.get("hours", 0) >= 1 and h["video_id"] in views]
             for f in FAMILIES}
    shs = {f: [views[sh["video_id"]] for sh in shorts
               if family_of(sh.get("theme")) == f and sh["video_id"] in views and age(sh) >= 2]
           for f in FAMILIES}

    def shrunk(groups: dict) -> dict:
        allv = [x for g in groups.values() for x in g]
        g = sum(allv) / len(allv) if allv else 0.0
        return {f: (sum(v) + 2 * g) / (len(v) + 2) for f, v in groups.items()}

    lg, sg = shrunk(longs), shrunk(shs)
    score = {f: lg[f] + 0.15 * sg[f] for f in FAMILIES}
    top = max(score.values())
    if top <= 0:
        return manual
    return {f: round((1 + 2 * score[f] / top) * manual[f], 2) for f in FAMILIES}


def _variant_count(v: dict, history: list) -> int:
    """Nombre de vidéos déjà publiées pour cette variante précise."""
    def same(h: dict) -> bool:
        return (h.get("theme") == v["theme"] and bool(h.get("black")) == bool(v.get("black"))
                and bool(h.get("thunder")) == bool(v.get("thunder"))
                and (h.get("hz") or None) == (float(v["hz"]) if v.get("hz") else None)
                and (h.get("bed") or None) == (v.get("bed") or None)
                and bool(h.get("theta")) == bool(v.get("theta")))
    return sum(1 for h in history if same(h))


def pick_variant(cfg: dict, history: list, shorts: list | None = None) -> dict:
    """Choix de la prochaine vidéo 8 h.

    - Équilibrage (06/11) : famille qui a le moins de vidéos par rapport à son poids.
    - Poids automatique (14/11) : les familles les plus regardées reçoivent plus de vidéos.
    - Variété (14/11) : jamais deux jours de suite la même famille (important pour l'audience et
      pour l'examen « contenu répétitif » du Programme Partenaire).
    Dans une famille : la variante de config.yaml la moins publiée (dans l'ordre du fichier)."""
    counts = {f: 0 for f in FAMILIES}
    for h in history:
        counts[family_of(h.get("theme"))] += 1
    weight = performance_weights(cfg, history, shorts or [])
    have = {family_of(v["theme"]) for v in cfg["variants"]}
    longs = [h for h in history if h.get("hours", 0) >= 1]
    last = family_of(longs[-1].get("theme")) if longs else None
    pool = [f for f in FAMILIES if f in have and f != last] or [f for f in FAMILIES if f in have]
    family = min(pool, key=lambda f: (counts[f] / weight[f], FAMILIES.index(f)))
    options = [v for v in cfg["variants"] if family_of(v["theme"]) == family]
    # un seul écran noir par ambiance : on retire les variantes « black » déjà faites
    options = [v for v in options if not (v.get("black") and any(
        h.get("black") and h.get("theme") == v["theme"] for h in history))] or options
    print(f"Vidéos par famille : {counts} — poids : {weight} — hier : {last} → {family}", flush=True)
    return min(options, key=lambda v: _variant_count(v, history))


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
    ap.add_argument("--hz", type=float, default=None, help="frequency : fréquence de référence (432, 528, 396)")
    ap.add_argument("--beat", type=float, default=None, help="binaural : battement en Hz (10 alpha, 6 thêta, 2.5 delta)")
    ap.add_argument("--bed", choices=["rain", "ocean"], default=None, help="frequency : fond nature discret")
    ap.add_argument("--theta", action="store_true", help="frequency : annoncer le battement thêta (titre)")
    ap.add_argument("--force", action="store_true", help="ignore le plafond quotidien (exceptionnel)")
    args = ap.parse_args()

    cfg = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    hours = args.hours if args.hours is not None else float(cfg["hours"])
    seconds = int(hours * 3600)
    history = load_history()
    shorts_file = ROOT / "shorts.json"
    all_shorts = json.loads(shorts_file.read_text(encoding="utf-8")) if shorts_file.exists() else []
    if not args.dry_run and not args.force:
        # plafond déclaré à Google : 3 publications par « jour de quota » (minuit heure du Pacifique)
        from zoneinfo import ZoneInfo
        pt = ZoneInfo("America/Los_Angeles")
        today = datetime.now(pt).date()
        shorts_file = ROOT / "shorts.json"   # les Shorts comptent aussi dans le plafond déclaré à Google
        shorts = json.loads(shorts_file.read_text(encoding="utf-8")) if shorts_file.exists() else []
        done = [h for h in history + shorts if datetime.fromisoformat(h["date"]).astimezone(pt).date() == today]
        if len(done) >= int(cfg.get("max_per_day", 3)):
            print(f"::notice::Déjà {len(done)} publications aujourd'hui (plafond {cfg.get('max_per_day', 3)}) : rien de publié.")
            return
    variant = pick_variant(cfg, history, all_shorts)
    if args.theme:
        if args.theme not in cfg["themes"] or args.theme == "thunder_sound":
            raise SystemExit(f"Ambiance inconnue : {args.theme}")
        variant = {"theme": args.theme, "thunder": args.thunder}
        if args.theme == "binaural":
            variant["beat"] = args.beat or 10
        if args.theme == "frequency":
            variant["hz"] = args.hz or 432
            variant["bed"] = args.bed
            variant["theta"] = args.theta
    black = args.black or bool(variant.get("black"))
    if black and any(h.get("black") and h.get("theme") == variant["theme"] for h in history):
        # règle du propriétaire (06/11) : un seul écran noir par ambiance
        raise SystemExit(f"Un écran noir existe déjà pour l'ambiance « {variant['theme']} » : publication annulée.")
    theme, thunder = variant["theme"], bool(variant["thunder"])
    beat = float(variant.get("beat", 10)) if theme == "binaural" else None
    hz = float(variant.get("hz", 432)) if theme == "frequency" else None
    bed = variant.get("bed") if theme == "frequency" else None
    theta = bool(variant.get("theta")) if theme == "frequency" else False
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
        theme + (f" {beat:g} Hz" if beat else "") + (f" {hz:g} Hz" if hz else "") + (f" + {bed}" if bed else "") + (" + orage" if thunder else "") + (" écran noir" if black else ""),
        encoding="utf-8")
    step(f"Ambiance « {theme} », battement={beat}, tonnerre={thunder}, écran noir={black}, {hours:g} h, graine {seed}", t0)

    # 1. Médias réels
    tcfg = cfg["themes"][theme]
    if bed:   # musique de fréquences + fond nature : images et sons de ce fond
        tcfg = {**tcfg, **tcfg["beds"][bed]}
    n_clips = 2 if black else int(cfg.get("clips_per_video", 8))  # écran noir : clips pour la miniature seulement
    clips = sources.video_clips(rng.choice(tcfg["video"]), n_clips, assets, rng, avoid_clips, blocked)
    for q in tcfg["video"]:
        if len(clips) >= 4:
            break
        clips += sources.video_clips(q, n_clips - len(clips), assets, rng,
                                     avoid_clips | {c["id"] for c in clips}, blocked)
    if len(clips) < (1 if black else 3):
        raise SystemExit("Pas assez de clips vidéo exploitables.")
    tonal_mode = tcfg.get("mode") == "tonal"
    noise_mode = tcfg.get("mode") == "noise"       # bruit coloré synthétisé : aucun enregistrement
    sounds = [] if noise_mode or (tonal_mode and not bed) else sources.freesound_sounds(
        rng.choice(tcfg["sound"]), int(cfg.get("sounds_per_video", 5)), assets, rng, avoid=avoid_sounds)
    if not noise_mode and (not tonal_mode or bed) and len(sounds) < 3:
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
    if tonal_mode and bed:
        music, nature = str(out / "music.m4a"), str(out / "nature.m4a")
        tonal.render(seconds, music, seed, f0=hz, beat=float(tcfg.get("binaural_beat", 6)))
        soundscape.mix([s["path"] for s in sounds], [], seconds, nature, seed)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", music, "-i", nature, "-filter_complex",
                        f"[1:a]volume={float(tcfg.get('level', 0.4))}[n];[0:a][n]amix=inputs=2:normalize=0[a]",
                        "-map", "[a]", "-c:a", "aac", "-b:a", "192k", audio], check=True)
        Path(music).unlink(missing_ok=True)
        Path(nature).unlink(missing_ok=True)
    elif tonal_mode:
        tonal.render(seconds, audio, seed, f0=hz, beat=float(tcfg.get("binaural_beat", 6)))
    elif noise_mode:
        noise.render(seconds, audio, seed, color=tcfg["color"])
    else:
        soundscape.mix([s["path"] for s in sounds], [s["path"] for s in thunders], seconds, audio, seed,
                       beat=beat, carrier=float(tcfg.get("carrier_hz", 200)),
                       bed_gain=float(tcfg.get("bed_gain", 1.0)))
    step("Paysage sonore mixé", t0)

    # 4. Miniature + textes
    if not black:
        frame = footage.frame(segment, rng.uniform(5, max(6, loop_len - 5)), str(out / "frame.png"))
    meta = metadata.build(theme, thunder, hours, seed, clips, sounds + thunders, black=black, beat=beat, hz=hz,
                          bed=bed, theta=theta)
    playlist_for_theme = tcfg["playlist"] if "playlist" in tcfg else cfg.get("playlist_id")
    meta["description"] = metadata.add_links(meta["description"], theme, playlist_for_theme)
    meta["localizations"] = {"ar": metadata.arabic(theme, thunder, hours, black, playlist_for_theme, beat=beat, hz=hz,
                                                     bed=bed, theta=theta)}
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
        "hz": hz,
        "bed": bed,
        "theta": theta,
        "clip_ids": [c["id"] for c in clips],
        "sound_ids": [s["id"] for s in sounds],
    }
    (out / "history_entry.json").write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
    history.append(entry)
    HISTORY.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
    step("Terminé", t0)


if __name__ == "__main__":
    main()
