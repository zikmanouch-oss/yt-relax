"""Ajoute une entrée à history.json si sa vidéo n'y est pas déjà (fusion sans conflit)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
entry = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
path = ROOT / "history.json"
history = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
if not any(e.get("video_id") == entry["video_id"] for e in history):
    history.append(entry)
    history.sort(key=lambda e: e.get("date", ""))
    path.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Ajouté :", entry["video_id"])
else:
    print("Déjà présent :", entry["video_id"])
