"""Ajoute (ou met à jour) la traduction arabe du titre et de la description des vidéos existantes.

Utilise videos.update avec la seule partie « localizations » : le titre, la description,
la langue et les autres réglages d'origine ne sont pas modifiés. Les vidéos absentes de
history.json ou à description manuelle (aperçu 3 min) sont ignorées.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src import metadata  # noqa: E402
from src.upload import _client  # noqa: E402

cfg = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
history = {e["video_id"]: e for e in json.loads((ROOT / "history.json").read_text(encoding="utf-8"))}

yt = _client()
ch = yt.channels().list(part="contentDetails", mine=True).execute()["items"][0]
uploads = ch["contentDetails"]["relatedPlaylists"]["uploads"]
ids = [i["contentDetails"]["videoId"] for i in
       yt.playlistItems().list(part="contentDetails", playlistId=uploads, maxResults=50).execute().get("items", [])]
for v in yt.videos().list(part="snippet,localizations", id=",".join(ids)).execute().get("items", []):
    sn, e = v["snippet"], history.get(v["id"])
    if not e or metadata.SUBSCRIBE_ANCHOR not in sn.get("description", ""):
        print("ignorée :", v["id"], sn["title"])
        continue
    theme = e["theme"]
    tcfg = cfg["themes"].get(theme, {})
    pl = tcfg["playlist"] if "playlist" in tcfg else cfg.get("playlist_id")
    black = bool(e.get("black")) or "Black Screen" in sn["title"]
    year = datetime.fromisoformat(e["date"]).year
    loc = dict(v.get("localizations") or {})
    loc["ar"] = metadata.arabic(theme, bool(e.get("thunder")), float(e.get("hours", 8)), black, pl, year, beat=e.get("beat"))
    if not sn.get("defaultLanguage"):
        print("ignorée (pas de langue par défaut) :", v["id"], sn["title"])
        continue
    yt.videos().update(part="localizations", body={"id": v["id"], "localizations": loc}).execute()
    print("arabe ajouté :", v["id"], "→", loc["ar"]["title"])
