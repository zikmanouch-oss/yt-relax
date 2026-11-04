"""Titres, descriptions et tags (en anglais : audience mondiale)."""
from __future__ import annotations

import random

TITLES = {
    "window": [
        "Rain on Window Sounds for Sleeping – {h} Hours of Relaxing Night Rain",
        "Gentle Rain on the Window – {h} Hours to Fall Asleep Fast",
        "Cozy Rainy Night by the Window – {h} Hours of Rain Sounds for Sleep",
    ],
    "forest": [
        "Rain in the Forest – {h} Hours of Nature Rain Sounds for Deep Sleep",
        "Relaxing Forest Rain Sounds – {h} Hours for Sleep, Study & Calm",
        "Soft Rain on Leaves – {h} Hours of Peaceful Forest Rain",
    ],
    "lake": [
        "Rain on a Calm Lake – {h} Hours of Soothing Rain Sounds for Sleep",
        "Gentle Rain on Water – {h} Hours to Relax and Fall Asleep",
        "Peaceful Rain Over a Pond – {h} Hours of Nature Rain Ambience",
    ],
    "roof": [
        "Rain on Roof Sounds for Sleeping – {h} Hours of Cozy Rain",
        "Heavy Rain on a Roof – {h} Hours for Deep Sleep & Insomnia",
        "Rain Sounds on a Cabin Roof – {h} Hours of Relaxing Rain",
    ],
}
THUNDER_SUFFIX = " & Distant Thunder"

THUMB = {"window": "RAIN ON WINDOW", "forest": "FOREST RAIN", "lake": "RAIN ON THE LAKE", "roof": "RAIN ON ROOF"}

DESCRIPTION = """{title}

Close your eyes and let the rain carry you to sleep. {h} hours of real rain \
ambience{thunder} to help you fall asleep, relax, study, meditate or block out \
background noise.

🌧️ No music, no talking — just rain.
🎧 Best with headphones or a speaker at low volume.
😴 For sleep, babies, studying, reading, focus and calm.

— Credits —
Footage: {video_source} — {video_credits}
Sounds: Freesound (freesound.org, CC0) — {sound_credits}

#rainsounds #sleep #relaxing #rain #sleepsounds
"""

TAGS = [
    "rain sounds", "rain sounds for sleeping", "sleep sounds", "relaxing rain",
    "rain ambience", "white noise", "deep sleep", "rain for sleep", "nature sounds",
    "study sounds", "focus", "insomnia", "relaxation", "sleep aid", "rainy night",
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


def build(theme: str, thunder: bool, hours: float, seed: int,
          clips: list[dict], sounds: list[dict], video_source: str = "Pixabay (pixabay.com)") -> dict:
    rnd = random.Random(seed)
    h = f"{hours:g}"
    title = rnd.choice(TITLES[theme]).format(h=h)
    if thunder and len(title) + len(THUNDER_SUFFIX) <= 100:
        title += THUNDER_SUFFIX
    tags = TAGS + THEME_TAGS[theme] + (["thunder sounds", "thunderstorm"] if thunder else [])
    return {
        "title": title[:100],
        "description": DESCRIPTION.format(
            title=title, h=h, thunder=" with distant thunder" if thunder else "",
            video_source=video_source, video_credits=_names(clips), sound_credits=_names(sounds)),
        "tags": tags,
        "thumb_line1": THUMB[theme],
        "thumb_line2": f"{'& THUNDER • ' if thunder else 'DEEP SLEEP • '}{h} HOURS",
    }
