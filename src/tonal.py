"""Musique de fréquences synthétisée (style « 432 Hz meditation music »), douce et mélodique.

Aucun enregistrement : tout est calculé, à partir de la fréquence de référence f0
(432, 528, 396 Hz…), qui joue le rôle du « la » : toute la gamme en découle (intonation juste).
- Progression d'accords lente (I, vi, IV, V…), chaque accord 14 à 24 s, fondus de 5 à 8 s,
  avec une basse douce ; notes doublées de copies très légèrement désaccordées (largeur stéréo).
- Mélodie pentatonique au timbre de piano feutré : courtes phrases de 3 à 6 notes, puis silences ;
  notes choisies de préférence dans l'accord en cours ; échos stéréo pour l'espace.
- Bourdon grave très discret sur f0/4 avec un léger battement binaural.
Le calcul se fait à partir du temps absolu (aucune coupure entre blocs) ; la suite d'accords et
de phrases est tirée au hasard et ne se répète pas sur 8 h.
"""
from __future__ import annotations

import bisect
import math
import random
import subprocess
from dataclasses import dataclass

import numpy as np

SR = 44100
CHUNK_S = 20

# Gamme majeure en intonation juste, rapports au « la » de référence (f0 = degré I).
I, II, III, IV, V, VI, VII = 1, 9 / 8, 5 / 4, 4 / 3, 3 / 2, 5 / 3, 15 / 8
# Accords : (fondamentale, notes) en rapports de f0, voix entre ~0,4 f0 et ~1,3 f0.
CHORDS = {
    "I": (I / 4, [I / 2, III / 2, V / 2, I]),
    "vi": (VI / 4, [VI / 2, I, III]),
    "IV": (IV / 4, [IV / 2, VI / 2, I, IV]),
    "V": (V / 4, [V / 2, VII / 2, II, V]),
    "ii": (II / 4, [II / 2, IV / 2, VI / 2, II]),
}
PROGRESSIONS = [
    ["I", "vi", "IV", "I"], ["I", "IV", "vi", "V"], ["vi", "IV", "I", "V"],
    ["I", "V", "vi", "IV"], ["IV", "I", "ii", "V"], ["I", "IV", "I", "V"],
]
CHORD_TONES = {  # degrés de la mélodie préférés pour chaque accord
    "I": [I, III, V], "vi": [VI, I, III], "IV": [IV, VI, I], "V": [V, VII, II], "ii": [II, IV, VI],
}
PENTA = [I, II, III, V, VI]          # pentatonique majeure
MELODY = [V / 2, VI / 2, I, II, III, V, VI, 2 * I]   # de 0,75 f0 à 2 f0


def _deg(r: float) -> float:
    """Ramène un rapport dans l'octave [1, 2) pour le comparer aux degrés de l'accord."""
    while r < 1:
        r *= 2
    while r >= 2:
        r /= 2
    return r


@dataclass
class Chord:
    start: float
    length: float
    fade: float
    name: str


@dataclass
class Note:
    start: float
    freq: float      # en multiples de f0
    gain: float
    pan: float


def _plan(seconds: float, rng: random.Random) -> tuple[list[Chord], list[Note]]:
    chords, t = [], -3.0
    while t < seconds:
        for name in rng.choice(PROGRESSIONS):
            length, fade = rng.uniform(14, 24), rng.uniform(5, 8)
            chords.append(Chord(t, length + 2 * fade, fade, name))
            t += length + fade
    notes, t, idx = [], rng.uniform(6, 12), len(MELODY) // 2
    starts = [c.start for c in chords]
    while t < seconds:
        if rng.random() < 0.35:                 # silence entre deux phrases
            t += rng.uniform(6, 16)
            continue
        for _ in range(rng.randint(3, 6)):      # une phrase
            k = max(0, bisect.bisect_right(starts, t) - 1)
            prefer = CHORD_TONES[chords[k].name]
            step = rng.choice([-2, -1, -1, 0, 1, 1, 2])
            idx = min(len(MELODY) - 1, max(0, idx + step))
            r = MELODY[idx]
            if _deg(r) not in prefer and rng.random() < 0.6:
                cands = [j for j, m in enumerate(MELODY) if _deg(m) in prefer]
                idx = min(cands, key=lambda j: abs(j - idx))
                r = MELODY[idx]
            notes.append(Note(t, r, rng.uniform(0.6, 1.0), rng.uniform(0.3, 0.7)))
            t += rng.choice([1.6, 2.0, 2.4, 3.2])
        t += rng.uniform(3, 8)
    return chords, notes


def _sin(f: float, t: np.ndarray, phase: float = 0.0) -> np.ndarray:
    return np.sin(2 * np.pi * f * t + phase)


ECHOES = ((0.0, 1.0, None), (0.48, 0.38, 0.2), (0.96, 0.22, 0.8), (1.44, 0.12, 0.35), (1.92, 0.07, 0.65))


def _render(t: np.ndarray, f0: float, beat: float, chords: list[Chord], cstarts: list[float],
            notes: list[Note], nstarts: list[float], seconds: float) -> np.ndarray:
    left = np.zeros(len(t))
    right = np.zeros(len(t))
    t0, t1 = t[0], t[-1]

    # bourdon très discret, battement binaural
    swell = 0.8 + 0.2 * np.sin(2 * np.pi * t / 83.0)
    left += 0.10 * swell * _sin(f0 / 4, t)
    right += 0.10 * swell * _sin(f0 / 4 + beat, t)

    # accords (nappe + basse)
    k0 = max(0, bisect.bisect_right(cstarts, t0 - 60) - 1)
    for c in chords[k0:]:
        if c.start > t1:
            break
        if c.start + c.length < t0:
            continue
        local = t - c.start
        fin = np.clip(local / c.fade, 0, 1)
        fout = np.clip((c.length - local) / c.fade, 0, 1)
        env = np.sin(fin * np.pi / 2) * np.sin(fout * np.pi / 2)
        root, voices = CHORDS[c.name]
        for j, r in enumerate(voices):
            f = f0 * r
            a = 0.075 * env * (1.0 if f < 600 else 0.7)
            ph = j * 1.3
            left += a * (_sin(f, t, ph) + 0.3 * _sin(f - 0.11, t, ph + 1) + 0.05 * _sin(2 * f, t))
            right += a * (_sin(f, t, ph + 0.4) + 0.3 * _sin(f + 0.09, t, ph + 2) + 0.05 * _sin(2 * f, t))
        fb = f0 * root
        bass = 0.11 * env * (_sin(fb, t) + 0.15 * _sin(2 * fb, t))
        left += bass
        right += bass

    # mélodie : piano feutré (attaque douce, déclin lent) + échos
    n0 = max(0, bisect.bisect_left(nstarts, t0 - 12))
    for n in notes[n0:]:
        if n.start > t1:
            break
        f = f0 * n.freq
        for delay, g, pan in ECHOES:
            st = n.start + delay
            if st > t1 or st + 10 < t0:
                continue
            local = t - st
            pos = np.maximum(local, 0)
            env = np.where(local >= 0, (1 - np.exp(-pos / 0.06)) * np.exp(-pos / 2.2), 0.0)
            tone = (_sin(f, pos) + 0.22 * _sin(2 * f, pos) * np.exp(-pos / 0.8)
                    + 0.06 * _sin(3 * f, pos) * np.exp(-pos / 0.4)) * env
            tone *= 0.085 * n.gain * g
            p = n.pan if pan is None else pan
            left += tone * (1 - p) * 1.4
            right += tone * p * 1.4

    out = np.stack([left, right], axis=1)
    out *= np.clip(t / 10, 0, 1)[:, None] * np.clip((seconds - t) / 15, 0, 1)[:, None]
    return out


def render(seconds: int, out_path: str, seed: int, f0: float = 432.0, beat: float = 6.0) -> None:
    rng = random.Random(seed)
    chords, notes = _plan(seconds, rng)
    cstarts = [c.start for c in chords]
    nstarts = [n.start for n in notes]
    enc = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "s16le", "-ar", str(SR), "-ac", "2", "-i", "-",
         "-c:a", "aac", "-b:a", "192k", out_path], stdin=subprocess.PIPE)
    total = int(seconds * SR)
    chunk = CHUNK_S * SR
    for s0 in range(0, total, chunk):
        s1 = min(total, s0 + chunk)
        t = np.arange(s0, s1, dtype=np.float64) / SR
        out = _render(t, f0, beat, chords, cstarts, notes, nstarts, seconds)
        out = np.tanh(out * 1.3) / 1.3 * 0.8
        enc.stdin.write(np.clip(out * 32767, -32768, 32767).astype("<i2").tobytes())
    enc.stdin.close()
    if enc.wait() != 0:
        raise RuntimeError("Encodage audio échoué")
