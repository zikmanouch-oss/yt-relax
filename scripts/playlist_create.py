"""Crée une playlist publique si aucune playlist de même titre n'existe. Usage : playlist_create.py "TITRE|DESCRIPTION" """
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.upload import _client  # noqa: E402

title, _, desc = " ".join(sys.argv[1:]).partition("|")
title, desc = title.strip(), desc.strip()
yt = _client()
existing = yt.playlists().list(part="snippet", mine=True, maxResults=50).execute().get("items", [])
for p in existing:
    if p["snippet"]["title"].strip().lower() == title.lower():
        print("PLAYLIST_ID existante :", p["id"], title)
        sys.exit(0)
p = yt.playlists().insert(part="snippet,status", body={
    "snippet": {"title": title, "description": desc, "defaultLanguage": "en"},
    "status": {"privacyStatus": "public"}}).execute()
print("PLAYLIST_ID créée :", p["id"], title)
