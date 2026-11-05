"""Ajoute une vidéo à une playlist si elle n'y est pas déjà. Usage : playlist_add.py VIDEO_ID PLAYLIST_ID"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.upload import _client  # noqa: E402

video, playlist = sys.argv[1], sys.argv[2]
yt = _client()
items = yt.playlistItems().list(part="contentDetails", playlistId=playlist, maxResults=50).execute().get("items", [])
if any(i["contentDetails"]["videoId"] == video for i in items):
    print("Déjà dans la playlist")
else:
    yt.playlistItems().insert(part="snippet", body={"snippet": {
        "playlistId": playlist, "resourceId": {"kind": "youtube#video", "videoId": video}}}).execute()
    print("Ajoutée :", video, "→", playlist)
