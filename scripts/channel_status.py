"""État de la chaîne en lecture seule (aucune modification) : vidéos, playlists, accueil, branding."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.upload import _client  # noqa: E402

yt = _client()
ch = yt.channels().list(part="snippet,statistics,brandingSettings,contentDetails,status", mine=True).execute()["items"][0]
out = {
    "channel": ch["snippet"]["title"],
    "stats": ch["statistics"],
    "banner": bool(ch.get("brandingSettings", {}).get("image", {}).get("bannerExternalUrl")),
    "featured_for_new_visitors": ch.get("brandingSettings", {}).get("channel", {}).get("unsubscribedTrailer"),
    "country": ch.get("brandingSettings", {}).get("channel", {}).get("country"),
}
uploads = ch["contentDetails"]["relatedPlaylists"]["uploads"]
ids = [i["contentDetails"]["videoId"] for i in
       yt.playlistItems().list(part="contentDetails", playlistId=uploads, maxResults=50).execute().get("items", [])]
vids = yt.videos().list(part="snippet,status,statistics,contentDetails,processingDetails,localizations", id=",".join(ids)).execute().get("items", []) if ids else []
out["videos"] = [{"id": v["id"], "title": v["snippet"]["title"], "privacy": v["status"]["privacyStatus"],
                  "upload": v["status"].get("uploadStatus"), "duration": v["contentDetails"]["duration"],
                  "views": v["statistics"].get("viewCount"), "thumbnail_custom": "maxres" in v["snippet"]["thumbnails"],
                  "synthetic": v["status"].get("containsSyntheticMedia"),
                  "default_lang": v["snippet"].get("defaultLanguage"),
                  "audio_lang": v["snippet"].get("defaultAudioLanguage"),
                  "translations": sorted((v.get("localizations") or {}).keys()),
                  "ar_title": (v.get("localizations") or {}).get("ar", {}).get("title")} for v in vids]
pls = yt.playlists().list(part="snippet,contentDetails,status", mine=True, maxResults=50).execute().get("items", [])
out["playlists"] = [{"id": p["id"], "title": p["snippet"]["title"], "count": p["contentDetails"]["itemCount"],
                     "privacy": p["status"]["privacyStatus"]} for p in pls]
secs = yt.channelSections().list(part="snippet,contentDetails", mine=True).execute().get("items", [])
out["home_sections"] = [{"type": s["snippet"]["type"], "title": s["snippet"].get("title"),
                         "playlists": s.get("contentDetails", {}).get("playlists")} for s in secs]
print(json.dumps(out, ensure_ascii=False, indent=2))
