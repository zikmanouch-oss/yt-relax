"""Ajoute toutes les vidéos 8 h déjà publiées (historique) aux playlists supplémentaires de config.yaml."""
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.upload import _client  # noqa: E402

cfg = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
history = json.loads((ROOT / "history.json").read_text(encoding="utf-8"))
videos = [h["video_id"] for h in history if float(h.get("hours", 0)) >= 1]
yt = _client()
for pl in cfg.get("extra_playlists") or []:
    have = {i["contentDetails"]["videoId"] for i in
            yt.playlistItems().list(part="contentDetails", playlistId=pl, maxResults=50).execute().get("items", [])}
    for v in videos:
        if v in have:
            continue
        yt.playlistItems().insert(part="snippet", body={"snippet": {
            "playlistId": pl, "resourceId": {"kind": "youtube#video", "videoId": v}}}).execute()
        print("ajoutée :", v, "→", pl)
