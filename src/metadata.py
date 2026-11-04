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

THUMB = {"window": "RAIN ON WINDOW", "forest": "FOREST RAIN", "lake": "RAIN ON THE LAKE", "roof": "RAIN ON ROOF"}

HASHTAGS = {False: "#rainsounds #sleepsounds #relaxing", True: "#rainsounds #sleepsounds #thunderstorm"}

DESCRIPTION = """Rain sounds for sleeping: {h} hours of {scene}{thunder_txt} to help you \
fall asleep fast, sleep deeply through the night and quiet a busy mind.

{scene_line}{thunder_line}. This is real nature sound, with no music and no talking, \
so it works as calm background for sleep, insomnia, studying, focus, reading, \
meditation or soothing a baby.

🌧️ Real rain recordings{thunder_bullet}
🌙 {h} hours, uninterrupted: play it all night
🎧 Best with headphones or a speaker at low volume
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


def build(theme: str, thunder: bool, hours: float, seed: int,
          clips: list[dict], sounds: list[dict], video_source: str = "Pixabay (pixabay.com)",
          year: int | None = None) -> dict:
    rnd = random.Random(seed)
    h = f"{hours:g}"
    y = year or _dt.datetime.now(_dt.timezone.utc).year
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
        "thumb_line2": f"{'& THUNDER • ' if thunder else 'DEEP SLEEP • '}{h} HOURS",
    }
