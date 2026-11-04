"""Récupère des photos CC0 (domaine public, via Openverse) pour l'identité de la chaîne.

Les images sont enregistrées dans branding/candidates/ avec leurs sources.
CC0 : aucune restriction, y compris pour un avatar ou une bannière.
"""
import io
import json
import sys
from pathlib import Path

import requests
from PIL import Image

QUERIES = sys.argv[1:] or ["moon over ocean night", "calm lake night", "misty forest dawn",
                           "rain drops window", "starry sky lake", "ocean waves sunset"]
OUT = Path("branding/candidates")
OUT.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "yt-relax/1.0 (branding script)"}
index = []
for q in QUERIES:
    r = requests.get("https://api.openverse.org/v1/images/", headers=UA, timeout=60, params={
        "q": q, "license": "cc0", "page_size": 20, "mature": "false", "aspect_ratio": "wide,square"})
    r.raise_for_status()
    n = 0
    for it in r.json().get("results", []):
        if n >= 5 or (it.get("width") or 0) < 1200:
            continue
        try:
            img = Image.open(io.BytesIO(requests.get(it["url"], headers=UA, timeout=60).content)).convert("RGB")
        except Exception:
            continue
        img.thumbnail((1600, 1600))
        name = f"{q.replace(' ', '-')}_{n}.jpg"
        img.save(OUT / name, quality=88)
        index.append({"file": name, "query": q, "title": it.get("title"), "creator": it.get("creator"),
                      "license": it.get("license"), "source": it.get("foreign_landing_url")})
        n += 1
    print(q, n)
(OUT / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
