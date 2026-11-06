"""Ajoute le lien d'abonnement et le lien de la playlist de l'ambiance aux descriptions existantes.

Ne modifie que les vidéos dont la description contient l'appel à l'abonnement généré par le moteur.
Ambiance déduite de history.json ; playlist déduite de config.yaml.
"""
import json
import sys
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
for v in yt.videos().list(part="snippet", id=",".join(ids)).execute().get("items", []):
    sn = v["snippet"]
    theme = history.get(v["id"], {}).get("theme")
    if not theme:
        print("ignorée (hors historique) :", v["id"], sn["title"])
        continue
    tcfg = cfg["themes"].get(theme, {})
    pl = tcfg["playlist"] if "playlist" in tcfg else cfg.get("playlist_id")
    new_desc = metadata.add_links(sn.get("description", ""), theme, pl)
    if new_desc == sn.get("description", ""):
        print("inchangée :", v["id"], sn["title"])
        continue
    sn["description"] = new_desc
    body = {"id": v["id"], "snippet": {k: sn[k] for k in ("title", "description", "categoryId", "tags",
                                                         "defaultLanguage", "defaultAudioLanguage") if k in sn}}
    try:
        yt.videos().update(part="snippet", body=body).execute()
        print("liens ajoutés :", v["id"], sn["title"])
    except Exception as e:  # ex. langue audio « zxx » refusée par l'API : on n'écrase rien
        print("ÉCHEC :", v["id"], sn.get("defaultAudioLanguage"), len(new_desc), str(e)[:200])
