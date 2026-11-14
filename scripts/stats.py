"""Relevé quotidien des chiffres de la chaîne (lecture seule) → stats/daily.json.

Sert au poids automatique des ambiances (src/main.py) et au bilan hebdomadaire (scripts/report.py).
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.upload import _client  # noqa: E402

OUT = ROOT / "stats" / "daily.json"
yt = _client()
ch = yt.channels().list(part="statistics,contentDetails", mine=True).execute()["items"][0]
uploads = ch["contentDetails"]["relatedPlaylists"]["uploads"]
ids, token = [], None
while True:
    r = yt.playlistItems().list(part="contentDetails", playlistId=uploads, maxResults=50, pageToken=token).execute()
    ids += [i["contentDetails"]["videoId"] for i in r.get("items", [])]
    token = r.get("nextPageToken")
    if not token:
        break
videos = {}
for k in range(0, len(ids), 50):
    for v in yt.videos().list(part="statistics", id=",".join(ids[k:k + 50])).execute().get("items", []):
        st = v["statistics"]
        videos[v["id"]] = {"views": int(st.get("viewCount", 0)), "likes": int(st.get("likeCount", 0)),
                           "comments": int(st.get("commentCount", 0))}
data = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
today = datetime.now(timezone.utc).date().isoformat()
data[today] = {"subs": int(ch["statistics"].get("subscriberCount", 0)),
               "views": int(ch["statistics"].get("viewCount", 0)),
               "count": int(ch["statistics"].get("videoCount", 0)), "videos": videos}
for d in sorted(data)[:-180]:      # on garde 6 mois
    del data[d]
OUT.parent.mkdir(exist_ok=True)
OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
print(f"{today} : {data[today]['subs']} abonnés, {data[today]['views']} vues, {len(videos)} vidéos")
