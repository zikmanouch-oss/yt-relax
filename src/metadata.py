"""Titres, descriptions et tags (en anglais : audience mondiale).

Règles SEO appliquées (voir claude/plan-yt-relax.md, section « Directives SEO ») :
- titre : mot-clé principal au début, durée, ambiance, année de publication à la fin ;
- description : mot-clé + bénéfice dans les 150 premiers caractères, minuteur de
  sommeil en chapitres, appel à l'abonnement, crédits, 3 hashtags maximum ;
- tags : pertinents uniquement, avec une variante datée.
L'année est celle de la publication : elle ne doit jamais annoncer une
nouveauté qui n'en est pas une.
"""
from __future__ import annotations

import datetime as _dt
import random

# {h} = durée en heures, {t} = « & Distant Thunder » si orage, {y} = année.
TITLES = {
    "window": [
        "Rain on Window Sounds for Sleeping – {h} Hours of Gentle Night Rain{t} ({y})",
        "Rain Sounds for Sleeping – {h} Hours of Rain on a Window{t} ({y})",
        "Fall Asleep Fast with Rain on the Window – {h} Hours{t} ({y})",
    ],
    "forest": [
        "Rain Sounds for Sleeping – {h} Hours of Forest Rain{t} ({y})",
        "Forest Rain Sounds for Deep Sleep – {h} Hours of Rain on Leaves{t} ({y})",
        "Relaxing Rain in the Forest – {h} Hours for Sleep, Study & Calm{t} ({y})",
    ],
    "lake": [
        "Rain Sounds for Sleeping – {h} Hours of Rain on a Calm Lake{t} ({y})",
        "Gentle Rain on Water for Deep Sleep – {h} Hours{t} ({y})",
        "Peaceful Lake Rain Sounds – {h} Hours to Relax & Fall Asleep{t} ({y})",
    ],
    "roof": [
        "Rain on Roof Sounds for Sleeping – {h} Hours of Cozy Cabin Rain{t} ({y})",
        "Heavy Rain on a Tin Roof for Deep Sleep – {h} Hours{t} ({y})",
        "Rain Sounds for Sleeping – {h} Hours of Rain on a Cabin Roof{t} ({y})",
    ],
}
THUNDER = " & Distant Thunder"

# Ambiances hors pluie : titres, description, tags et hashtags propres.
OTHER_TITLES = {
    "fireplace": [
        "Fireplace Sounds for Sleeping – {h} Hours of Crackling Fire ({y})",
        "Crackling Fireplace for Deep Sleep & Relaxation – {h} Hours ({y})",
        "Cozy Fireplace Ambience – {h} Hours of Crackling Fire for Sleep ({y})",
    ],
}
OTHER_TITLES["ocean"] = [
    "Ocean Waves Sounds for Sleeping – {h} Hours of Gentle Sea Waves ({y})",
    "Ocean Sounds for Deep Sleep – {h} Hours of Calm Waves on the Shore ({y})",
    "Relaxing Ocean Waves for Sleep, Study & Calm – {h} Hours ({y})",
]
OTHER_TITLES["waterfall"] = [
    "Waterfall Sounds for Sleeping – {h} Hours of Relaxing Waterfall ({y})",
    "Waterfall White Noise for Deep Sleep – {h} Hours ({y})",
    "Relaxing Waterfall in Nature – {h} Hours for Sleep, Study & Calm ({y})",
]
OTHER_DESCRIPTION = {
    "waterfall": """Waterfall sounds for sleeping: {h} hours of a steady, relaxing waterfall to help you \
fall asleep fast, sleep deeply through the night and quiet a busy mind.

Let the constant rush of falling water wash the noise of the day away. This is real nature sound, \
with no music and no talking, so it works as calm background for sleep, insomnia, \
studying, focus, reading, meditation or soothing a baby.

💧 Real waterfall recordings
🌙 {h} hours, uninterrupted: play it all night
🎧 Best with headphones or a speaker at low volume
🚫 No mid-roll ads: nothing will interrupt your sleep
📵 Tip: lower your screen brightness and let the water flow

⏱️ Sleep timer
{chapters}

🔔 Subscribe to Calm Haven Sounds for new rain, fireplace, ocean and nature soundscapes every week.

— Credits —
Footage: {video_source} — {video_credits}
Sounds: Freesound (freesound.org, CC0) — {sound_credits}

#waterfallsounds #sleepsounds #whitenoise
""",
    "ocean": """Ocean waves sounds for sleeping: {h} hours of gentle sea waves rolling onto the shore to help you \
fall asleep fast, sleep deeply through the night and quiet a busy mind.

Let the slow rhythm of the waves on the beach carry you away. This is real ocean sound, \
with no music and no talking, so it works as calm background for sleep, insomnia, \
studying, focus, reading, meditation or soothing a baby.

🌊 Real ocean wave recordings
🌙 {h} hours, uninterrupted: play it all night
🎧 Best with headphones or a speaker at low volume
🚫 No mid-roll ads: nothing will interrupt your sleep
📵 Tip: lower your screen brightness and let the waves play

⏱️ Sleep timer
{chapters}

🔔 Subscribe to Calm Haven Sounds for new rain, fireplace, ocean and nature soundscapes every week.

— Credits —
Footage: {video_source} — {video_credits}
Sounds: Freesound (freesound.org, CC0) — {sound_credits}

#oceanwaves #sleepsounds #relaxing
""",
    "fireplace": """Fireplace sounds for sleeping: {h} hours of a warm, crackling fire to help you \
fall asleep fast, relax deeply and feel cozy through the night.

Let the soft crackle and pop of burning logs slow everything down. This is real fire sound, \
with no music and no talking, so it works as calm background for sleep, insomnia, \
studying, focus, reading, meditation or a cozy evening.

🔥 Real crackling fireplace recordings
🌙 {h} hours, uninterrupted: play it all night
🎧 Best with headphones or a speaker at low volume
🚫 No mid-roll ads: nothing will interrupt your sleep
📵 Tip: lower your screen brightness and let the fire play

⏱️ Sleep timer
{chapters}

🔔 Subscribe to Calm Haven Sounds for new rain, fireplace, ocean and nature soundscapes every week.

— Credits —
Footage: {video_source} — {video_credits}
Sounds: Freesound (freesound.org, CC0) — {sound_credits}

#fireplace #sleepsounds #relaxing
""",
}
OTHER_TAGS = {
    "waterfall": [
        "waterfall sounds", "waterfall sounds for sleeping", "waterfall white noise", "water sounds",
        "nature sounds", "relaxing waterfall", "sleep sounds", "relaxing sounds", "deep sleep",
        "white noise", "insomnia", "study sounds", "relaxation", "calm haven sounds",
    ],
    "ocean": [
        "ocean waves", "ocean waves sounds for sleeping", "ocean sounds", "sea waves", "waves sounds",
        "beach waves", "ocean waves for sleep", "sleep sounds", "relaxing sounds", "deep sleep",
        "white noise", "insomnia", "study sounds", "relaxation", "calm haven sounds",
    ],
    "fireplace": [
        "fireplace sounds", "fireplace sounds for sleeping", "crackling fire", "fireplace ambience",
        "cozy fireplace", "fire sounds", "crackling fireplace", "sleep sounds", "relaxing sounds",
        "deep sleep", "white noise", "insomnia", "study sounds", "relaxation", "calm haven sounds",
    ],
}

SCENE = {
    "window": "gentle rain on a window",
    "forest": "gentle forest rain",
    "lake": "soft rain falling on a calm lake",
    "roof": "cozy rain on a cabin roof",
}
SCENE_LINE = {
    "window": "Let raindrops tapping on the glass carry you away",
    "forest": "Let steady rain on the leaves surround you",
    "lake": "Let soft rain on still water slow everything down",
    "roof": "Let the steady patter of rain on the roof wrap around you",
}

THUMB = {"window": "RAIN ON WINDOW", "forest": "FOREST RAIN", "lake": "RAIN ON THE LAKE", "roof": "RAIN ON ROOF",
         "fireplace": "COZY FIREPLACE", "ocean": "OCEAN WAVES",
         "waterfall": "WATERFALL"}

HASHTAGS = {False: "#rainsounds #sleepsounds #relaxing", True: "#rainsounds #sleepsounds #thunderstorm"}

DESCRIPTION = """Rain sounds for sleeping: {h} hours of {scene}{thunder_txt} to help you \
fall asleep fast, sleep deeply through the night and quiet a busy mind.

{scene_line}{thunder_line}. This is real nature sound, with no music and no talking, \
so it works as calm background for sleep, insomnia, studying, focus, reading, \
meditation or soothing a baby.

🌧️ Real rain recordings{thunder_bullet}
🌙 {h} hours, uninterrupted: play it all night
🎧 Best with headphones or a speaker at low volume
🚫 No mid-roll ads: nothing will interrupt your sleep
📵 Tip: lower your screen brightness and let the sound play

⏱️ Sleep timer
{chapters}

🔔 Subscribe to Calm Haven Sounds for new rain, fireplace, ocean and nature soundscapes every week.

— Credits —
Footage: {video_source} — {video_credits}
Sounds: Freesound (freesound.org, CC0) — {sound_credits}

{hashtags}
"""

TAGS = [
    "rain sounds", "rain sounds for sleeping", "sleep sounds", "relaxing rain",
    "rain ambience", "white noise", "deep sleep", "rain for sleep", "nature sounds",
    "study sounds", "insomnia", "relaxation", "sleep aid", "rainy night", "calm haven sounds",
]
THEME_TAGS = {
    "window": ["rain on window", "rain on glass"],
    "forest": ["forest rain", "rain in the forest", "rain on leaves"],
    "lake": ["rain on water", "rain on lake", "pond rain"],
    "roof": ["rain on roof", "rain on tin roof", "cabin rain"],
}


def _names(items: list[dict]) -> str:
    names = list(dict.fromkeys(i["author"] for i in items))
    return ", ".join(names) if names else "—"


def _ts(seconds: int) -> str:
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def chapters(hours: float) -> str:
    """Minuteur de sommeil : 0:00, 30 min, puis chaque heure (dernier repère
    au moins 10 min avant la fin, au moins 3 repères sinon rien)."""
    total = int(hours * 3600)
    marks = [(0, "Start")]
    if total >= 45 * 60:
        marks.append((30 * 60, "30 minutes"))
    for k in range(1, int(hours) + 1):
        if k * 3600 <= total - 600:
            marks.append((k * 3600, f"{k} hour" + ("s" if k > 1 else "")))
    if len(marks) < 3:
        return "Press play and let it run."
    return "\n".join(f"{_ts(t)} {label}" for t, label in marks)


BLACK_TITLES = {
    "window": "Rain on Window Sounds for Sleeping – Black Screen, {h} Hours{t} ({y})",
    "forest": "Forest Rain Sounds for Sleeping – Black Screen, {h} Hours{t} ({y})",
    "lake": "Rain on a Lake Sounds for Sleeping – Black Screen, {h} Hours{t} ({y})",
    "roof": "Rain on Roof Sounds for Sleeping – Black Screen, {h} Hours{t} ({y})",
    "fireplace": "Fireplace Sounds for Sleeping – Black Screen, {h} Hours{t} ({y})",
    "ocean": "Ocean Waves Sounds for Sleeping – Black Screen, {h} Hours{t} ({y})",
    "waterfall": "Waterfall Sounds for Sleeping – Black Screen, {h} Hours{t} ({y})",
}


def _blackify(d: dict, theme: str, thunder: bool, hours: float, y: int) -> dict:
    """Variante « écran noir » : titre, 1re phrase, puce et tags adaptés (promesse tenue : image noire)."""
    h = f"{hours:g}"
    title = BLACK_TITLES[theme].format(h=h, t=THUNDER if thunder else "", y=y)
    if len(title) > 100:
        title = BLACK_TITLES[theme].format(h=h, t="", y=y)
    desc = d["description"]
    desc = desc.replace("Rain sounds for sleeping: ", "Rain sounds for sleeping with a black screen: ", 1)
    desc = desc.replace("Fireplace sounds for sleeping: ", "Fireplace sounds for sleeping with a black screen: ", 1)
    desc = desc.replace("Ocean waves sounds for sleeping: ", "Ocean waves sounds for sleeping with a black screen: ", 1)
    desc = desc.replace("Waterfall sounds for sleeping: ", "Waterfall sounds for sleeping with a black screen: ", 1)
    for tip in ("📵 Tip: lower your screen brightness and let the sound play",
                "📵 Tip: lower your screen brightness and let the fire play",
                "📵 Tip: lower your screen brightness and let the waves play",
                "📵 Tip: lower your screen brightness and let the water flow"):
        desc = desc.replace(tip, "⬛ Black screen: no light to keep you awake, just the sound")
    desc = desc.replace("Footage: ", "Thumbnail image: ", 1)
    kind = {"fireplace": "fireplace", "ocean": "ocean", "waterfall": "waterfall"}.get(theme, "rain")
    tags = [t for t in d["tags"] if "hours" not in t][:16] + [
        "black screen", f"{kind} sounds black screen", f"{kind} sounds for sleeping black screen",
        "dark screen sleep sounds"]
    return {**d, "title": title[:100], "description": desc, "tags": tags,
            "thumb_line2": f"BLACK SCREEN • {h} HOURS" if hours >= 1 else "BLACK SCREEN"}


# ------------------------------------------------------------ binaural beats
# Fréquences « binaural beats » : formulation prudente, AUCUNE allégation médicale
# (pas de « soigne », pas de « recommandé par les psychologues »).
BANDS = {  # battement (Hz) → (nom de l'onde, usage, mot-clé)
    10: ("Alpha", "Anxiety & Stress Relief", "calm"),
    6: ("Theta", "Deep Relaxation & Calm Mind", "relax"),
    2.5: ("Delta", "Deep Sleep & Letting Go", "sleep"),
}


def _band(beat: float) -> tuple[str, str, str]:
    return BANDS[min(BANDS, key=lambda b: abs(b - beat))]


BINAURAL_TITLES = [
    "{w} Waves Binaural Beats for {use} – {h} Hours ({hz} Hz) ({y})",
    "{use}: {w} Waves {hz} Hz Binaural Beats – {h} Hours ({y})",
    "Calming {w} Waves for {use} – {h} Hours of Binaural Beats ({y})",
]
BINAURAL_DESCRIPTION = """{w} waves binaural beats ({hz} Hz) for {use_l}: {h} hours of a soft, steady tone \
blended with gentle real nature sound, to help you slow down, breathe deeper and let tension go.

How it works: each ear hears a slightly different tone ({c} Hz and {c2} Hz). Your brain perceives \
the {hz} Hz difference as a slow pulse, the "binaural beat". {w} waves are usually associated with \
{assoc}. Many people use them to unwind before sleep, during meditation or on stressful days.

🎧 Headphones required: binaural beats only work when each ear hears its own tone
🔈 Keep the volume low and comfortable
🌙 {h} hours, uninterrupted: play it all night
🚫 No mid-roll ads: nothing will interrupt your session
⚠️ A relaxation aid, not a medical treatment. If anxiety or sleep problems affect your daily life, \
please talk to a health professional. Do not listen while driving.

⏱️ Session timer
{chapters}

🔔 Subscribe to Calm Haven Sounds for new rain, fireplace, ocean and nature soundscapes every week.

— Credits —
Binaural tones: generated by Calm Haven Sounds
Footage: {video_source} — {video_credits}
Nature sounds: Freesound (freesound.org, CC0) — {sound_credits}

#binauralbeats #{wl}waves #anxietyrelief
"""
ASSOC = {"Alpha": "calm, relaxed wakefulness", "Theta": "deep relaxation, meditation and drowsiness",
         "Delta": "deep, dreamless sleep"}
BINAURAL_TAGS = [
    "binaural beats", "binaural beats for anxiety", "anxiety relief", "stress relief", "calming frequencies",
    "relaxing frequency", "healing frequency", "meditation music", "sleep frequency", "brainwave",
    "headphones", "relaxation", "deep sleep", "calm haven sounds",
]


def _build_binaural(beat: float, hours: float, seed: int, clips: list[dict], sounds: list[dict],
                    video_source: str, y: int) -> dict:
    rnd = random.Random(seed)
    w, use, _ = _band(beat)
    h, hz = f"{hours:g}", f"{beat:g}"
    title = rnd.choice(BINAURAL_TITLES).format(w=w, use=use, h=h, hz=hz, y=y)
    c = 200
    return {
        "title": title[:100],
        "description": BINAURAL_DESCRIPTION.format(
            w=w, wl=w.lower(), hz=hz, use_l=use.lower(), h=h, c=c, c2=f"{c + beat:g}", assoc=ASSOC[w],
            chapters=chapters(hours), video_source=video_source,
            video_credits=_names(clips), sound_credits=_names(sounds)),
        "tags": BINAURAL_TAGS + [f"{w.lower()} waves", f"{hz} hz binaural beats", f"{w.lower()} waves {hz} hz",
                                 f"binaural beats {y}", f"binaural beats {h} hours"],
        "thumb_line1": f"{w.upper()} WAVES {hz} HZ",
        "thumb_line2": ("CALM ANXIETY" if w == "Alpha" else "DEEP RELAX" if w == "Theta" else "DEEP SLEEP")
                       + (f" • {h} HOURS" if hours >= 1 else ""),
    }


def build(theme: str, thunder: bool, hours: float, seed: int,
          clips: list[dict], sounds: list[dict], video_source: str = "Pixabay (pixabay.com)",
          year: int | None = None, black: bool = False, beat: float | None = None) -> dict:
    if theme == "binaural":
        y = year or _dt.datetime.now(_dt.timezone.utc).year
        return _build_binaural(beat or 10, hours, seed, clips, sounds, video_source, y)
    d = _build(theme, thunder, hours, seed, clips, sounds, video_source, year)
    if black:
        y = year or _dt.datetime.now(_dt.timezone.utc).year
        d = _blackify(d, theme, thunder, hours, y)
    return d


def _build(theme: str, thunder: bool, hours: float, seed: int,
           clips: list[dict], sounds: list[dict], video_source: str = "Pixabay (pixabay.com)",
           year: int | None = None) -> dict:
    rnd = random.Random(seed)
    h = f"{hours:g}"
    y = year or _dt.datetime.now(_dt.timezone.utc).year
    if theme in OTHER_TITLES:
        title = rnd.choice(OTHER_TITLES[theme]).format(h=h, y=y)
        return {
            "title": title[:100],
            "description": OTHER_DESCRIPTION[theme].format(
                h=h, chapters=chapters(hours), video_source=video_source,
                video_credits=_names(clips), sound_credits=_names(sounds)),
            "tags": OTHER_TAGS[theme] + [f"{theme} sounds for sleeping {y}", f"{theme} {h} hours"],
            "thumb_line1": THUMB[theme],
            "thumb_line2": f"DEEP SLEEP • {h} HOURS" if hours >= 1 else "DEEP SLEEP",
        }
    title = rnd.choice(TITLES[theme]).format(h=h, t=THUNDER if thunder else "", y=y)
    if len(title) > 100:  # sans l'orage si trop long, jamais sans l'année
        title = rnd.choice(TITLES[theme]).format(h=h, t="", y=y)
    tags = (TAGS + THEME_TAGS[theme]
            + (["thunder sounds", "thunderstorm sounds for sleeping", "rain and thunder sounds"] if thunder else [])
            + [f"rain sounds for sleeping {y}", f"rain sounds {h} hours"])
    return {
        "title": title[:100],
        "description": DESCRIPTION.format(
            h=h, scene=SCENE[theme],
            thunder_txt=" with soft, distant thunder" if thunder else "",
            scene_line=SCENE_LINE[theme],
            thunder_line=", with a low, far-off rumble of thunder now and then" if thunder else "",
            thunder_bullet=" + distant thunder" if thunder else "",
            chapters=chapters(hours),
            video_source=video_source, video_credits=_names(clips), sound_credits=_names(sounds),
            hashtags=HASHTAGS[thunder]),
        "tags": tags,
        "thumb_line1": THUMB[theme],
        "thumb_line2": (f"{'& THUNDER • ' if thunder else 'DEEP SLEEP • '}{h} HOURS" if hours >= 1
                        else ("& THUNDER" if thunder else "DEEP SLEEP")),
    }


CHANNEL_URL = "https://www.youtube.com/@CalmHavenSounds-z4p"
SUBSCRIBE_ANCHOR = "🔔 Subscribe to Calm Haven Sounds for new rain, fireplace, ocean and nature soundscapes every week."
PLAYLIST_LABEL = {"fireplace": "More fireplace sounds", "ocean": "More ocean sounds",
                  "waterfall": "More waterfall sounds", "binaural": "More binaural beats sessions"}


CALM_PLAYLIST = "PLEChJox9ZBJU"  # « Calming Sounds for Anxiety & Stress Relief »


def link_lines(theme: str, playlist_id: str | None) -> list[str]:
    lines = [f"👉 Subscribe: {CHANNEL_URL}?sub_confirmation=1"]
    if playlist_id:
        label = PLAYLIST_LABEL.get(theme, "More rain sounds")
        lines.append(f"📂 {label}: https://www.youtube.com/playlist?list={playlist_id}")
    lines.append(f"😌 Calming sounds for anxiety & stress: https://www.youtube.com/playlist?list={CALM_PLAYLIST}")
    return lines


def add_links(description: str, theme: str, playlist_id: str | None) -> str:
    """Ajoute le lien d'abonnement et celui de la playlist sous l'appel à l'abonnement."""
    new = [l for l in link_lines(theme, playlist_id) if l not in description]
    if not new or SUBSCRIBE_ANCHOR not in description:
        return description
    return description.replace(SUBSCRIBE_ANCHOR, SUBSCRIBE_ANCHOR + "\n" + "\n".join(new), 1)


# ---------------------------------------------------------------- arabe
# Traductions affichées aux spectateurs arabophones (localizations YouTube « ar »).
AR_TITLES = {
    "window": "صوت المطر على النافذة للنوم{b} – {h}{t} ({y})",
    "forest": "صوت المطر في الغابة للنوم العميق{b} – {h}{t} ({y})",
    "lake": "صوت المطر على البحيرة للنوم{b} – {h}{t} ({y})",
    "roof": "صوت المطر على السقف للنوم{b} – {h}{t} ({y})",
    "fireplace": "صوت المدفأة وطقطقة الحطب للنوم{b} – {h}{t} ({y})",
    "ocean": "صوت أمواج البحر للنوم العميق{b} – {h}{t} ({y})",
    "waterfall": "صوت الشلال للنوم العميق{b} – {h}{t} ({y})",
}
AR_LEAD = {"fireplace": "صوت المدفأة للنوم", "ocean": "صوت أمواج البحر للنوم", "waterfall": "صوت الشلال للنوم"}
AR_SCENE = {
    "window": "المطر الهادئ على زجاج النافذة",
    "forest": "المطر الهادئ في الغابة",
    "lake": "المطر الخفيف على بحيرة هادئة",
    "roof": "المطر على سقف كوخ دافئ",
    "fireplace": "نار دافئة وطقطقة الحطب",
    "ocean": "أمواج البحر الهادئة على الشاطئ",
    "waterfall": "شلال هادئ وسط الطبيعة",
}
AR_HASHTAGS = {
    "rain": "#أصوات_المطر #صوت_المطر_للنوم #نوم_عميق",
    "fireplace": "#صوت_المدفأة #أصوات_للنوم #استرخاء",
    "ocean": "#صوت_البحر #أصوات_للنوم #استرخاء",
    "waterfall": "#صوت_الشلال #أصوات_للنوم #استرخاء",
}
AR_DESCRIPTION = """{lead}: {hh} من {scene}{thunder} لتساعدك على النوم بسرعة، والنوم بعمق طوال الليل، وتهدئة أفكارك.

أصوات حقيقية من الطبيعة، بدون موسيقى وبدون كلام، مناسبة للنوم والأرق والدراسة والتركيز والقراءة والتأمل.

🌙 {hh} متواصلة: شغّله طوال الليل
🎧 يُفضّل استخدام سماعات أو مكبر صوت بصوت منخفض
🚫 بدون إعلانات في منتصف الفيديو: لا شيء يقطع نومك
{black_line}
⏱️ مؤقت النوم
{chapters}

🔔 اشترك في Calm Haven Sounds لمزيد من أصوات المطر والمدفأة والبحر والطبيعة كل أسبوع.
{links}

المصادر: Pixabay (فيديو) — Freesound (أصوات CC0)

{hashtags}
"""


def _ar_hours(hours: float) -> str:
    h = f"{hours:g}"
    if hours == 1:
        return "ساعة واحدة"
    if hours == 2:
        return "ساعتان"
    if 3 <= hours <= 10 and float(hours).is_integer():
        return f"{h} ساعات"
    return f"{h} ساعة"


def _ar_chapters(hours: float) -> str:
    total = int(hours * 3600)
    marks = [(0, "البداية")]
    if total >= 45 * 60:
        marks.append((30 * 60, "30 دقيقة"))
    for k in range(1, int(hours) + 1):
        if k * 3600 <= total - 600:
            marks.append((k * 3600, f"الساعة {k}"))
    if len(marks) < 3:
        return "شغّل الفيديو واتركه يعمل."
    return "\n".join(f"{_ts(t)} {label}" for t, label in marks)


AR_WAVES = {"Alpha": ("موجات ألفا", "للتخلص من القلق والتوتر"),
            "Theta": ("موجات ثيتا", "للاسترخاء العميق وتهدئة العقل"),
            "Delta": ("موجات دلتا", "للنوم العميق")}
AR_BINAURAL = """{wave} بتردد {hz} هرتز (نبضات بينورال) {use}: {hh} من نغمة هادئة وثابتة مع أصوات طبيعية حقيقية خفيفة، لتساعدك على الاسترخاء والتنفس بعمق.

🎧 السماعات ضرورية: كل أذن تسمع نغمة مختلفة قليلاً
🔈 اجعل الصوت منخفضاً ومريحاً
🌙 {hh} متواصلة
🚫 بدون إعلانات في منتصف الفيديو
⚠️ وسيلة للاسترخاء وليست علاجاً طبياً. إذا كان القلق أو الأرق يؤثر على حياتك اليومية، استشر مختصاً. لا تستمع أثناء القيادة.

⏱️ مؤقت الجلسة
{chapters}

🔔 اشترك في Calm Haven Sounds لمزيد من الأصوات الهادئة كل أسبوع.
{links}

المصادر: Pixabay (فيديو) — Freesound (أصوات CC0) — النغمات من إنتاج Calm Haven Sounds

#نبضات_بينورال #التخلص_من_القلق #استرخاء
"""


def arabic(theme: str, thunder: bool, hours: float, black: bool, playlist_id: str | None,
           year: int | None = None, beat: float | None = None) -> dict:
    y = year or _dt.datetime.now(_dt.timezone.utc).year
    hh = _ar_hours(hours)
    if theme == "binaural":
        w, _, _ = _band(beat or 10)
        wave, use = AR_WAVES[w]
        hz = f"{(beat or 10):g}"
        links = [f"👉 اشترك: {CHANNEL_URL}?sub_confirmation=1"]
        if playlist_id:
            links.append(f"📂 المزيد: https://www.youtube.com/playlist?list={playlist_id}")
        title = f"{wave} {hz} هرتز {use} – {hh} من نبضات بينورال ({y})"
        desc = AR_BINAURAL.format(wave=wave, hz=hz, use=use, hh=hh, chapters=_ar_chapters(hours),
                                  links="\n".join(links))
        return {"title": title[:100], "description": desc}
    title = AR_TITLES[theme].format(b="، شاشة سوداء" if black else "", h=hh,
                                    t=" مع رعد بعيد" if thunder else "", y=y)
    kind = {"fireplace": "fireplace", "ocean": "ocean", "waterfall": "waterfall"}.get(theme, "rain")
    links = [f"👉 اشترك: {CHANNEL_URL}?sub_confirmation=1"]
    if playlist_id:
        links.append(f"📂 المزيد: https://www.youtube.com/playlist?list={playlist_id}")
    links.append(f"😌 أصوات هادئة للتخلص من القلق والتوتر: https://www.youtube.com/playlist?list={CALM_PLAYLIST}")
    desc = AR_DESCRIPTION.format(
        lead=AR_LEAD.get(theme, "أصوات المطر للنوم"), hh=hh, scene=AR_SCENE[theme],
        thunder=" مع رعد خفيف بعيد" if thunder else "",
        black_line="⬛ شاشة سوداء: لا ضوء يوقظك، فقط الصوت\n" if black else "",
        chapters=_ar_chapters(hours), links="\n".join(links), hashtags=AR_HASHTAGS[kind])
    return {"title": title[:100], "description": desc}
