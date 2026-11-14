"""Bilan hebdomadaire en Markdown (lu depuis stats/daily.json, history.json, shorts.json)."""
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src import main  # noqa: E402

stats = json.loads((ROOT / "stats" / "daily.json").read_text(encoding="utf-8"))
history = json.loads((ROOT / "history.json").read_text(encoding="utf-8"))
shorts = json.loads((ROOT / "shorts.json").read_text(encoding="utf-8"))
cfg = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
days = sorted(stats)
now, before = stats[days[-1]], stats[days[max(0, len(days) - 8)]]
span = len(days) - 1 - max(0, len(days) - 8)
title = {e["video_id"]: e["title"] for e in history + shorts}
kind = {**{e["video_id"]: "8 h" for e in history}, **{e["video_id"]: "Short" for e in shorts}}


def gain(vid: str) -> int:
    return now["videos"][vid]["views"] - before["videos"].get(vid, {}).get("views", 0)


lines = [f"**Période : {days[max(0, len(days) - 8)]} → {days[-1]}** ({span} jour(s) de relevés)", "",
         "| | Maintenant | Évolution |", "|---|---|---|",
         f"| Abonnés | {now['subs']} | {now['subs'] - before['subs']:+d} |",
         f"| Vues | {now['views']} | {now['views'] - before['views']:+d} |",
         f"| Vidéos en ligne | {now['count']} | {now['count'] - before['count']:+d} |", ""]
for label in ("8 h", "Short"):
    top = sorted((v for v in now["videos"] if kind.get(v) == label), key=lambda v: (gain(v), now["videos"][v]["views"]), reverse=True)[:5]
    lines += [f"**Top {label} de la période (vues gagnées)**", ""]
    lines += [f"- {gain(v):+d} (total {now['videos'][v]['views']}) — [{title.get(v, v)}](https://youtu.be/{v})" for v in top]
    lines.append("")
w = main.performance_weights(cfg, history, shorts)
counts = {f: sum(1 for h in history if main.family_of(h.get("theme")) == f) for f in main.FAMILIES}
names = {"binaural": "Fréquences", "noise": "Bruits colorés", "ocean": "Océan", "fireplace": "Feu",
         "waterfall": "Chute d'eau", "rain": "Pluie"}
low = min(w.values())
lines += ["**Ambiances (rythme = combien de fois plus souvent qu'une ambiance au rythme de base ; calculé d'après les vues)**",
          "", "| Ambiance | Vidéos 8 h | Vues (8 h + Shorts) | Rythme |", "|---|---|---|---|"]
for f in main.FAMILIES:
    vids = [e["video_id"] for e in history + shorts if main.family_of(e.get("theme")) == f]
    total = sum(now["videos"].get(v, {}).get("views", 0) for v in vids)
    lines.append(f"| {names[f]} | {counts[f]} | {total} | ×{w[f] / low:.1f} |")
lines += ["", "Seuils du Programme Partenaire : 1 000 abonnés et 4 000 h de visionnage sur 12 mois "
          "(les heures ne sont visibles que dans YouTube Studio → Statistiques)."]
print("\n".join(lines))
