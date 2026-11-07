"""Musique de fréquences synthétisée (style « 432 Hz meditation music »).

Aucun enregistrement : tout est calculé.
- Bourdon grave (fondamentale / 4 et / 2), avec un léger battement binaural.
- Nappe d'accords consonants (intonation juste) construite sur la fréquence choisie
  (432, 528, 396 Hz…) : chaque accord dure 40 à 90 s et se fond dans le suivant
  (fondus de 15 à 25 s) ; chaque note est doublée de copies très légèrement désaccordées
  à gauche et à droite (mouvement lent, effet « chorus »).
- Quelques notes de cloche douces, espacées et rares, avec un écho stéréo.
Le calcul se fait à partir du temps absolu : aucune coupure entre deux blocs,
et la suite d'accords tirée au hasard ne se répète pas sur 8 h.
"""
from __future__ import annotations

import math
import random
import subprocess
from dataclasses import dataclass

import numpy as np

SR = 44100
CHUNK_S = 20

# Accords (rapports à la fondamentale grave root = f0 / 2), tous consonants.
# Chaque accord contient le rapport 2 (= f0 elle-même) ou son octave : la fréquence annoncée
# est toujours présente.
CHORDS = [
    [1, 3 / 2, 2, 5 / 2],
    [1, 5 / 4, 3 / 2, 2],
    [1, 3 / 2, 2, 3],
    [3 / 4, 1, 3 / 2, 2],
    [1, 4 / 3, 5 / 3, 2],
    [1, 9 / 8, 3 / 2, 2],
    [5 / 6, 5 / 4, 5 / 3, 2],
    [1, 3 / 2, 15 / 8, 2],
]
BELL_RATIOS = [2, 9 / 4, 5 / 2, 3, 10 / 3, 4]   # gamme pentatonique au-dessus de f0


@dataclass
class Chord:
    start: float
    length: float
    fade: float
    ratios: list
    lfo: list          # (période, phase) d'ondulation de volume par note


@dataclass
class Bell:
    start: float
    freq: float
    gain: float
    pan: float


def _plan(seconds: float, rng: random.Random) -> tuple[list[Chord], list[Bell]]:
    chords, t, last = [], -5.0, None
    while t < seconds:
        options = [c for c in CHORDS if c is not last]
        ratios = rng.choice(options)
        length = rng.uniform(40, 90)
        fade = rng.uniform(15, 25)
        lfo = [(rng.uniform(18, 60), rng.uniform(0, 2 * math.pi)) for _ in ratios]
        chords.append(Chord(t, length + 2 * fade, fade, ratios, lfo))
        t += length + fade
        last = ratios
    bells, t = [], rng.uniform(20, 40)
    while t < seconds:
        bells.append(Bell(t, rng.choice(BELL_RATIOS), rng.uniform(0.25, 0.6), rng.uniform(0.25, 0.75)))
        t += rng.uniform(9, 30)
    return chords, bells


def _sin(f: float, t: np.ndarray, phase: float = 0.0) -> np.ndarray:
    return np.sin(2 * np.pi * f * t + phase)


def _render(t: np.ndarray, f0: float, beat: float, chords: list[Chord], bells: list[Bell],
            seconds: float) -> np.ndarray:
    n = len(t)
    left = np.zeros(n)
    right = np.zeros(n)
    root = f0 / 2
    t0, t1 = t[0], t[-1]

    # bourdon : f0/4 et f0/2, battement binaural (droite = gauche + beat)
    swell = 0.85 + 0.15 * np.sin(2 * np.pi * t / 97.0)
    for f, a in ((f0 / 4, 0.30), (f0 / 2, 0.22)):
        left += a * swell * _sin(f, t)
        right += a * swell * _sin(f + beat, t)

    # nappe d'accords
    for c in chords:
        if c.start > t1 or c.start + c.length < t0:
            continue
        local = t - c.start
        fin = np.clip(local / c.fade, 0, 1)
        fout = np.clip((c.length - local) / c.fade, 0, 1)
        env = np.sin(fin * np.pi / 2) * np.sin(fout * np.pi / 2)
        if not env.any():
            continue
        for r, (per, ph) in zip(c.ratios, c.lfo):
            f = root * r
            a = 0.13 * env * (0.7 + 0.3 * np.sin(2 * np.pi * t / per + ph))
            a = a * (1.0 if f < 900 else 0.6)
            body_l = _sin(f, t) + 0.35 * _sin(f - 0.12, t, 1.0) + 0.12 * _sin(2 * f, t)
            body_r = _sin(f, t, 0.5) + 0.35 * _sin(f + 0.09, t, 2.0) + 0.12 * _sin(2 * f + 0.1, t)
            left += a * body_l
            right += a * body_r

    # cloches douces avec écho
    for b in bells:
        for delay, g, side in ((0.0, 1.0, None), (0.42, 0.45, "l"), (0.63, 0.35, "r"), (1.1, 0.18, None)):
            st = b.start + delay
            if st > t1 or st + 9 < t0:
                continue
            local = t - st
            mask = local >= 0
            if not mask.any():
                continue
            env = np.where(mask, (1 - np.exp(-np.maximum(local, 0) / 0.04)) * np.exp(-np.maximum(local, 0) / 2.8), 0)
            f = f0 * b.freq / 2
            tone = (_sin(f, local) + 0.25 * _sin(2.01 * f, local)) * env * b.gain * g * 0.08
            pan = b.pan if side is None else (0.2 if side == "l" else 0.8)
            left += tone * (1 - pan) * 1.4
            right += tone * pan * 1.4

    out = np.stack([left, right], axis=1)
    # entrée (10 s) et sortie (15 s) en douceur
    out *= np.clip(t / 10, 0, 1)[:, None] * np.clip((seconds - t) / 15, 0, 1)[:, None]
    return out


def render(seconds: int, out_path: str, seed: int, f0: float = 432.0, beat: float = 6.0) -> None:
    rng = random.Random(seed)
    chords, bells = _plan(seconds, rng)
    enc = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "s16le", "-ar", str(SR), "-ac", "2", "-i", "-",
         "-c:a", "aac", "-b:a", "192k", out_path], stdin=subprocess.PIPE)
    total = int(seconds * SR)
    chunk = CHUNK_S * SR
    for s0 in range(0, total, chunk):
        s1 = min(total, s0 + chunk)
        t = np.arange(s0, s1, dtype=np.float64) / SR
        out = _render(t, f0, beat, chords, bells, seconds)
        out = np.tanh(out * 1.2) / 1.2 * 0.55
        enc.stdin.write(np.clip(out * 32767, -32768, 32767).astype("<i2").tobytes())
    enc.stdin.close()
    if enc.wait() != 0:
        raise RuntimeError("Encodage audio échoué")
