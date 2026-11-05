"""Récupération de médias réels et gratuits.

- Vidéos : API Pixabay (ou Pexels), licences gratuites avec usage commercial autorisé.
- Sons   : API Freesound, uniquement licence CC0 (domaine public).
"""
from __future__ import annotations

import os
import random
import time
from pathlib import Path

import requests

UA = {"User-Agent": "yt-relax/1.0"}

# Mots-clés qui signalent souvent des logos, enseignes, textes ou personnes à l'image.
BANNED_TAGS = {
    "city", "cityscape", "building", "buildings", "skyscraper", "skyline", "urban", "downtown",
    "neon", "sign", "signs", "advertising", "advertisement", "billboard", "logo", "brand", "text",
    "shop", "store", "restaurant", "cafe", "street", "traffic", "car", "cars", "taxi", "bus",
    "people", "person", "man", "woman", "girl", "boy", "child", "crowd", "umbrella", "face",
    "cat", "cats", "kitten", "dog", "dogs", "puppy", "pet", "pets", "animal", "animals",
    "christmas", "santa", "gift", "gifts", "stocking", "candle", "candles", "tv", "television",
}


def _get(url: str, **kw) -> requests.Response:
    for attempt in range(4):
        try:
            r = requests.get(url, timeout=60, headers={**UA, **kw.pop("headers", {})}, **kw)
            if r.status_code == 429:
                time.sleep(10 * (attempt + 1))
                continue
            r.raise_for_status()
            return r
        except requests.RequestException:
            if attempt == 3:
                raise
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(url)


def _download(url: str, dest: Path, headers: dict | None = None) -> Path:
    with requests.get(url, stream=True, timeout=120, headers={**UA, **(headers or {})}) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
    return dest


# --------------------------------------------------------------- Pixabay

def pixabay_clips(query: str, count: int, dest: Path, rng: random.Random,
                  avoid: set[int] = frozenset(), blocked: set[int] = frozenset()) -> list[dict]:
    key = os.environ["PIXABAY_API_KEY"]
    r = _get("https://pixabay.com/api/videos/", params={
        "key": key, "q": query, "per_page": 200, "safesearch": "true", "order": "popular"})
    found = []
    for v in r.json().get("hits", []):
        if v.get("duration", 0) < 8 or v["id"] in blocked:
            continue
        tags = {t.strip().lower() for t in v.get("tags", "").split(",")}
        words = {w for t in tags for w in t.split()}
        if (tags | words) & BANNED_TAGS:
            continue
        vids = v.get("videos", {})
        # « medium » = 1920×1080 en général ; sinon « large » (souvent 4K)
        cand = [vids.get(k) for k in ("medium", "large", "small")]
        cand = [c for c in cand if c and c.get("url") and c.get("width", 0) >= 1280]
        if not cand:
            continue
        best = min(cand, key=lambda c: abs(c["width"] - 1920))
        found.append({"id": v["id"], "url": best["url"], "duration": v["duration"],
                      "author": v.get("user", "Pixabay"), "page": v.get("pageURL", "")})
    fresh = [c for c in found if c["id"] not in avoid] or found
    top = fresh[:max(count * 4, 20)]
    rng.shuffle(top)
    chosen = top[:count]
    dest.mkdir(parents=True, exist_ok=True)
    for c in chosen:
        c["path"] = str(_download(c["url"], dest / f"pixabay_{c['id']}.mp4"))
    print(f"Pixabay « {query} » : {len(chosen)} clips — IDs {[c['id'] for c in chosen]}", flush=True)
    return chosen


def video_clips(query: str, count: int, dest: Path, rng: random.Random,
                avoid: set[int] = frozenset(), blocked: set[int] = frozenset()) -> list[dict]:
    """Utilise Pixabay si la clé existe, sinon Pexels."""
    if os.environ.get("PIXABAY_API_KEY"):
        return pixabay_clips(query, count, dest, rng, avoid, blocked)
    return [c for c in pexels_clips(query, count, dest, rng, avoid | blocked)]


# ---------------------------------------------------------------- Pexels

def pexels_clips(query: str, count: int, dest: Path, rng: random.Random,
                 avoid: set[int] = frozenset()) -> list[dict]:
    key = os.environ["PEXELS_API_KEY"]
    found: list[dict] = []
    for page in (1, 2, 3):
        r = _get("https://api.pexels.com/videos/search",
                 headers={"Authorization": key},
                 params={"query": query, "orientation": "landscape", "per_page": 80, "page": page})
        for v in r.json().get("videos", []):
            if v["duration"] < 8 or v["width"] < 1280:
                continue
            files = [f for f in v["video_files"]
                     if f.get("width") and 1280 <= f["width"] <= 2560 and f.get("file_type") == "video/mp4"]
            if not files:
                continue
            best = min(files, key=lambda f: abs(f["width"] - 1920))
            found.append({"id": v["id"], "url": best["link"], "duration": v["duration"],
                          "author": v.get("user", {}).get("name", "Pexels"), "page": v["url"]})
        if len(found) >= count * 4:
            break

    fresh = [c for c in found if c["id"] not in avoid] or found
    rng.shuffle(fresh)
    chosen = fresh[:count]
    dest.mkdir(parents=True, exist_ok=True)
    for c in chosen:
        c["path"] = str(_download(c["url"], dest / f"pexels_{c['id']}.mp4"))
    print(f"Pexels « {query} » : {len(chosen)} clips", flush=True)
    return chosen


# ------------------------------------------------------------- Freesound

def freesound_sounds(query: str, count: int, dest: Path, rng: random.Random,
                     min_dur: int = 90, avoid: set[int] = frozenset()) -> list[dict]:
    key = os.environ["FREESOUND_API_KEY"]
    exclude = " ".join(f"-tag:{t}" for t in
                       ("voice", "speech", "talking", "music", "melody", "synth", "people", "birds", "bird"))
    r = _get("https://freesound.org/apiv2/search/text/", params={
        "query": query,
        "filter": f'license:"Creative Commons 0" duration:[{min_dur} TO 3600] {exclude}',
        "sort": "rating_desc",
        "page_size": 60,
        "fields": "id,name,duration,previews,username,url,avg_rating,num_ratings",
        "token": key,
    })
    results = [s for s in r.json().get("results", []) if s.get("previews")]
    fresh = [s for s in results if s["id"] not in avoid] or results
    top = fresh[:max(count * 3, 12)]
    rng.shuffle(top)
    chosen = top[:count]
    dest.mkdir(parents=True, exist_ok=True)
    out = []
    for s in chosen:
        url = s["previews"].get("preview-hq-ogg") or s["previews"]["preview-hq-mp3"]
        ext = ".ogg" if url.endswith(".ogg") else ".mp3"
        path = _download(url, dest / f"fs_{s['id']}{ext}")
        out.append({"id": s["id"], "path": str(path), "name": s["name"],
                    "author": s["username"], "page": s["url"], "duration": s["duration"]})
    print(f"Freesound « {query} » : {len(out)} sons", flush=True)
    return out
