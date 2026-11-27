"""Repère les Shorts publiés avec l'ancien code (avant le 28/11) dont l'image s'arrête avant le son.

Un Short assemble n clips Pixabay de seg = (40 + 1,5 × (n − 1)) / n secondes.
Avant le correctif 60c6127, un clip plus court que seg n'était pas bouclé : l'image finissait trop tôt.
Méthode déterministe : durée de chaque clip via l'API Pixabay (sans télécharger les vidéos).
Écrit un rapport Markdown sur la sortie standard.
"""
import json
import os
import sys
import time

import requests

SECONDS, XF, MARGIN = 40, 1.5, 0.2
FIX_DATE = "2026-11-28"  # Shorts fabriqués à partir de cette date : code corrigé
KEY = os.environ["PIXABAY_API_KEY"]


def clip_duration(cid):
    for i in range(3):
        r = requests.get("https://pixabay.com/api/videos/", params={"id": cid, "key": KEY}, timeout=30)
        if r.status_code == 429:
            time.sleep(5 * (i + 1))
            continue
        r.raise_for_status()
        hits = r.json().get("hits") or []
        return hits[0].get("duration") if hits else None
    return None


def main():
    shorts = json.load(open("shorts.json", encoding="utf-8"))
    views = {}
    try:
        daily = json.load(open("stats/daily.json", encoding="utf-8"))
        last = daily[max(daily)]
        views = {k: v.get("views", 0) for k, v in (last.get("videos") or {}).items()}
    except Exception:
        pass

    rows, touched, seg = [], 0, (SECONDS + XF * 2) / 3
    for s in shorts:
        if s["date"][:10] >= FIX_DATE:
            continue
        ids = s.get("clip_ids") or []
        n = len(ids) or 1
        seg = (SECONDS + XF * (n - 1)) / n
        durs = [clip_duration(c) for c in ids]
        short = [d for d in durs if d is not None and d < seg + MARGIN]
        unknown = any(d is None for d in durs)
        # image visible ≈ somme des segments réels moins les fondus
        real = [min(d, seg) if d is not None else seg for d in durs]
        visible = sum(real) - XF * (n - 1)
        if short:
            touched += 1
            etat = f"⚠️ touché (~{visible:.0f} s d'image / 40 s)"
        elif unknown:
            etat = "❓ clip introuvable sur Pixabay"
        else:
            etat = "✅ OK"
        v = views.get(s["video_id"], "?")
        rows.append(f"| {s['date'][:10]} | [{s['video_id']}](https://youtube.com/shorts/{s['video_id']}) | {s.get('theme','')} "
                    f"| {v} | {', '.join(f'{c}:{d}s' for c, d in zip(ids, durs))} | {etat} |")
        time.sleep(0.5)

    print(f"## Shorts publiés avant le correctif du {FIX_DATE}\n")
    print(f"**{touched} Short(s) touché(s)** sur {len(rows)} vérifiés (clip < {seg + MARGIN:.1f} s pour 3 clips).\n")
    print("| Date | Short | Ambiance | Vues | Clips (durée Pixabay) | État |\n|---|---|---|---|---|---|")
    print("\n".join(rows))
    print("\nRappel : rien n'est supprimé automatiquement. Décision du propriétaire : garder les Shorts touchés "
          "avec beaucoup de vues, remplacer ceux à faible audience (< ~20 vues).")


if __name__ == "__main__":
    sys.exit(main())
