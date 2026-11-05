"""Ajoute la ligne « No mid-roll ads » aux descriptions des vidéos déjà en ligne.

Insertion juste après la ligne « 🎧 Best with headphones… » ; une vidéo sans cette ligne
(description rédigée à la main) n'est pas modifiée et est signalée. Rien d'autre n'est changé.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.upload import _client  # noqa: E402

LINE = "🚫 No mid-roll ads: nothing will interrupt your sleep"
ANCHOR = "🎧 Best with headphones or a speaker at low volume"

yt = _client()
ch = yt.channels().list(part="contentDetails", mine=True).execute()["items"][0]
uploads = ch["contentDetails"]["relatedPlaylists"]["uploads"]
ids = [i["contentDetails"]["videoId"] for i in
       yt.playlistItems().list(part="contentDetails", playlistId=uploads, maxResults=50).execute().get("items", [])]
for v in yt.videos().list(part="snippet", id=",".join(ids)).execute().get("items", []):
    sn = v["snippet"]
    desc = sn.get("description", "")
    if LINE in desc:
        print("déjà présent :", v["id"])
        continue
    if ANCHOR not in desc:
        print("ignorée (description manuelle) :", v["id"], sn["title"])
        continue
    sn["description"] = desc.replace(ANCHOR, ANCHOR + "\n" + LINE, 1)
    body = {"id": v["id"], "snippet": {k: sn[k] for k in ("title", "description", "categoryId", "tags",
                                                         "defaultLanguage") if k in sn}}
    yt.videos().update(part="snippet", body=body).execute()
    print("mise à jour :", v["id"], sn["title"])
