"""Remet la langue audio des vidéos générées à « Non applicable » (zxx), comme décidé pour la chaîne.

Ne touche qu'à defaultAudioLanguage (titre, description, tags renvoyés à l'identique).
Affiche aussi la description de l'aperçu 3 min (31l7VUFKg9Q) pour préparer sa traduction.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.upload import _client  # noqa: E402

yt = _client()
ch = yt.channels().list(part="contentDetails", mine=True).execute()["items"][0]
uploads = ch["contentDetails"]["relatedPlaylists"]["uploads"]
ids = [i["contentDetails"]["videoId"] for i in
       yt.playlistItems().list(part="contentDetails", playlistId=uploads, maxResults=50).execute().get("items", [])]
for v in yt.videos().list(part="snippet", id=",".join(ids)).execute().get("items", []):
    sn = v["snippet"]
    if v["id"] == "31l7VUFKg9Q":
        print("=== APERÇU ===\n" + sn["title"] + "\n---\n" + sn.get("description", "") + "\n=== FIN ===")
        continue
    if sn.get("defaultAudioLanguage") == "zxx":
        print("déjà zxx :", v["id"])
        continue
    body = {"id": v["id"], "snippet": {k: sn[k] for k in ("title", "description", "categoryId", "tags",
                                                         "defaultLanguage") if k in sn}}
    body["snippet"]["defaultAudioLanguage"] = "zxx"
    try:
        yt.videos().update(part="snippet", body=body).execute()
        print("langue audio → zxx :", v["id"])
    except Exception as e:  # noqa: BLE001
        print("échec :", v["id"], str(e)[:200])
