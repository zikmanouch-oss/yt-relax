"""Traduction arabe de l'aperçu 3 min (31l7VUFKg9Q), dont la description a été écrite à la main."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.upload import _client  # noqa: E402

AR = {
    "title": "Calm Haven Sounds – صوت المطر على النافذة للنوم (معاينة 3 دقائق)",
    "description": """معاينة لمدة 3 دقائق من Calm Haven Sounds: مطر هادئ على النافذة في الليل، تسجيلات حقيقية لصوت المطر بدون موسيقى وبدون كلام.

لليلة كاملة، استمع إلى 8 ساعات متواصلة من أصوات المطر للنوم:
▶️ https://youtu.be/plrj5Nfoki0
🌧️ كل فيديوهات المطر: https://www.youtube.com/playlist?list=PLbbqInyCAtYM

تقدّم Calm Haven Sounds أصواتًا طويلة وهادئة للنوم العميق والدراسة والاسترخاء: المطر، المدفأة، البحر والطبيعة.
🔔 اشترك ليصلك جديدنا كل أسبوع: https://www.youtube.com/@CalmHavenSounds-z4p?sub_confirmation=1

المصادر: Pixabay (فيديو) — Freesound (أصوات CC0)

#أصوات_المطر #صوت_المطر_للنوم #استرخاء
""",
}
yt = _client()
v = yt.videos().list(part="localizations", id="31l7VUFKg9Q").execute()["items"][0]
loc = dict(v.get("localizations") or {})
loc["ar"] = AR
yt.videos().update(part="localizations", body={"id": "31l7VUFKg9Q", "localizations": loc}).execute()
print("arabe ajouté : 31l7VUFKg9Q →", AR["title"])
