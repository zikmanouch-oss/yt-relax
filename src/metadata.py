"""Titres, descriptions et tags (en anglais : audience mondiale)."""
from __future__ import annotations

import random

TITLES = {
    "light": [
        "Gentle Rain Sounds for Sleeping – {h} Hours of Soft Rain at Night",
        "Soft Rain on the Window – {h} Hours for Deep Sleep & Relaxation",
        "Light Rain Sounds for Sleep, Study & Calm – {h} Hours",
    ],
    "medium": [
        "Rain Sounds for Sleeping – {h} Hours of Relaxing Rain at Night",
        "Calming Rain on a Window – {h} Hours to Fall Asleep Fast",
        "Steady Rain Sounds for Deep Sleep – {h} Hours, No Music",
    ],
    "heavy": [
        "Heavy Rain Sounds for Sleeping – {h} Hours of Rainstorm at Night",
        "Heavy Rain on the Window – {h} Hours for Insomnia & Deep Sleep",
        "Strong Rain Sounds to Block Noise – {h} Hours for Sleep & Focus",
    ],
}

THUNDER_SUFFIX = " (with Distant Thunder)"

DESCRIPTION = """{title}

Close your eyes and let the sound of the rain carry you to sleep. \
This {h}-hour recording of {kind} rain is made to help you fall asleep, \
relax, study, meditate or simply block out background noise.

🌧️ No music, no talking — just rain.
🎧 Best with headphones or a speaker at low volume.
🔁 Perfect for sleep, babies, studying, reading, focus and calm.

The sounds and visuals of this video were created by our own sound engine.

#rainsounds #sleep #relaxing #whitenoise #rain
"""

TAGS = [
    "rain sounds", "rain sounds for sleeping", "sleep sounds", "relaxing rain",
    "rain on window", "white noise", "deep sleep", "rain for sleep", "ambient rain",
    "study sounds", "focus", "insomnia", "relaxation", "nature sounds", "sleep aid",
]


def build(intensity: str, thunder: bool, hours: float, seed: int) -> dict:
    rnd = random.Random(seed)
    h = f"{hours:g}"
    title = rnd.choice(TITLES[intensity]).format(h=h)
    if thunder and len(title) + len(THUNDER_SUFFIX) <= 100:
        title += THUNDER_SUFFIX
    kind = {"light": "gentle", "medium": "calming", "heavy": "heavy"}[intensity]
    tags = TAGS + (["thunder sounds", "thunderstorm"] if thunder else [])
    return {
        "title": title[:100],
        "description": DESCRIPTION.format(title=title, h=h, kind=kind),
        "tags": tags,
        "thumb_line1": "RAIN SOUNDS",
        "thumb_line2": f"{'Heavy Rain' if intensity == 'heavy' else 'Deep Sleep'} • {h} HOURS",
    }
