"""Publication sur YouTube via l'API Data v3 (gratuite)."""
from __future__ import annotations

import os
import time

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube"]


def credentials_available() -> bool:
    return all(os.environ.get(k) for k in ("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN"))


def _client():
    creds = Credentials(
        token=None,
        refresh_token=os.environ["YT_REFRESH_TOKEN"],
        client_id=os.environ["YT_CLIENT_ID"],
        client_secret=os.environ["YT_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
        scopes=SCOPES,
    )
    return build("youtube", "v3", credentials=creds, cache_discovery=False)


def _fit_tags(tags: list[str], limit: int = 450) -> list[str]:
    """YouTube limite les tags à 500 caractères (guillemets comptés pour les tags à espaces)."""
    out, total = [], 0
    for t in dict.fromkeys(t.strip() for t in tags if t.strip()):
        cost = len(t) + (2 if " " in t else 0) + 1
        if total + cost > limit:
            break
        out.append(t)
        total += cost
    return out


def upload(video: str, thumb: str, meta: dict, cfg: dict) -> str:
    yt = _client()
    body = {
        "snippet": {
            "title": meta["title"],
            "description": meta["description"],
            "tags": _fit_tags(meta["tags"]),
            "categoryId": str(cfg.get("category_id", 22)),
            "defaultLanguage": "en",
        },
        "status": {
            "privacyStatus": os.environ.get("PRIVACY_OVERRIDE") or cfg.get("privacy", "public"),
            "selfDeclaredMadeForKids": False,
        },
    }
    media = MediaFileUpload(video, mimetype="video/mp4", chunksize=64 * 1024 * 1024, resumable=True)
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)

    response, retries = None, 0
    while response is None:
        try:
            status, response = req.next_chunk()
            if status:
                print(f"Upload {int(status.progress() * 100)} %", flush=True)
        except HttpError as e:
            if e.resp.status in (500, 502, 503, 504) and retries < 8:
                retries += 1
                time.sleep(2 ** retries)
                continue
            raise
    video_id = response["id"]
    print(f"Vidéo publiée : https://youtu.be/{video_id}")

    try:
        yt.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(thumb, mimetype="image/jpeg")).execute()
    except HttpError as e:
        print(f"Miniature non appliquée (chaîne non vérifiée ?) : {e}")

    playlist = cfg.get("playlist_id")
    if playlist:
        try:
            yt.playlistItems().insert(part="snippet", body={"snippet": {
                "playlistId": playlist,
                "resourceId": {"kind": "youtube#video", "videoId": video_id}}}).execute()
        except HttpError as e:
            print(f"Ajout à la playlist impossible : {e}")
    return video_id
