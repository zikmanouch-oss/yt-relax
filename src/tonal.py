"""Musique de fréquences synthétisée (style « 432 Hz meditation music »), douce et mélodique.

Aucun enregistrement : tout est calculé à partir de la fréquence de référence f0
(432, 528, 396 Hz…), qui joue le rôle du « la » : toute la gamme en découle (intonation juste).

Écriture musicale :
- tempo lent (≈ 52 bpm), mesures de 4 temps ; chaque accord dure 2 mesures ;
  progressions de 4 accords (I, vi, IV, V…) tirées au hasard ;
- nappe très douce (3 voix ouvertes) + basse ronde ;
- arpèges de harpe/piano au début de chaque mesure ;
- mélodie pentatonique construite sur un motif répété puis varié (c'est la répétition qui
  rend l'écoute « musicale »), avec des sections sans mélodie pour respirer ;
- réverbération à convolution (salle douce de ~3 s) : de l'espace sans saturation ;
- bourdon très discret sur f0/4 avec un léger battement binaural.
Aucune saturation : le niveau est fixé avec de la marge (crête < -6 dB).
Calcul à partir du temps absolu, par blocs, avec la queue de réverbération reportée
d'un bloc au suivant : aucune coupure sur 8 h.
"""
from __future__ import annotations

import bisect
import random
import subprocess
from dataclasses import dataclass

import numpy as np

SR = 44100
CHUNK_S = 20
BEAT = 60 / 52           # durée d'un temps (s)
BAR = 4 * BEAT

# Gamme majeure en intonation juste, rapports au « la » de référence (f0 = degré I).
I, II, III, IV, V, VI, VII = 1, 9 / 8, 5 / 4, 4 / 3, 3 / 2, 5 / 3, 15 / 8
CHORDS = {  # (basse, nappe, notes d'arpège) en rapports de f0
    "I": (I / 4, [I / 2, V / 2, III], [I / 2, V / 2, I, III]),
    "vi": (VI / 4, [VI / 2, III / 2, I], [VI / 2, I, III, VI]),
    "IV": (IV / 4, [IV / 2, I, VI / 2], [IV / 2, VI / 2, I, IV]),
    "V": (V / 4, [V / 2, II, VII / 2], [V / 2, VII / 2, II, V]),
    "ii": (II / 4, [II / 2, VI / 2, IV / 2], [II / 2, IV / 2, VI / 2, II]),
}
PROGRESSIONS = [
    ["I", "vi", "IV", "V"], ["I", "IV", "vi", "V"], ["vi", "IV", "I", "V"],
    ["I", "V", "vi", "IV"], ["IV", "I", "ii", "V"], ["I", "vi", "ii", "V"],
]
CHORD_TONES = {"I": [I, III, V], "vi": [VI, I, III], "IV": [IV, VI, I], "V": [V, VII, II], "ii": [II, IV, VI]}
MELODY = [V / 2, VI / 2, I, II, III, V, VI, 2 * I, 2 * II]   # pentatonique, de 0,75 f0 à 2,25 f0
RHYTHMS = [  # rythmes d'un motif de 2 mesures (en temps, total 8)
    [1, 1, 2, 2, 2], [2, 1, 1, 4], [1.5, 0.5, 2, 4], [1, 1, 1, 1, 4], [2, 2, 1, 1, 2], [3, 1, 4],
]


def _deg(r: float) -> float:
    while r < 1:
        r *= 2
    while r >= 2:
        r /= 2
    return r


@dataclass
class Chord:
    start: float
    name: str
    length: float = 2 * BAR


@dataclass
class Note:
    start: float
    freq: float          # multiple de f0
    gain: float
    pan: float
    decay: float         # constante de déclin (s)


def _snap(idx: int, prefer: list[float]) -> int:
    cands = [j for j, m in enumerate(MELODY) if _deg(m) in prefer]
    return min(cands, key=lambda j: abs(j - idx))


def _plan(seconds: float, rng: random.Random) -> tuple[list[Chord], list[Note]]:
    chords: list[Chord] = []
    notes: list[Note] = []
    t, section = 2.0, 0
    while t < seconds:
        prog = rng.choice(PROGRESSIONS)
        melody_on = section % 3 != 2          # 2 progressions avec mélodie, 1 sans
        rhythm = rng.choice(RHYTHMS)
        steps = [rng.choice([-1, 1, 1, -2, 2, 0]) for _ in rhythm]
        start_idx = rng.randrange(2, len(MELODY) - 2)
        for k, name in enumerate(prog):
            c = Chord(t, name)
            chords.append(c)
            tones = CHORD_TONES[name]
            # arpège doux au début de chaque mesure
            _, _, arp = CHORDS[name]
            for bar in range(2):
                b0 = t + bar * BAR
                order = arp if (k + bar) % 2 == 0 else arp[::-1]
                for j, r in enumerate(order):
                    notes.append(Note(b0 + j * BEAT / 2, r, 0.45 * rng.uniform(0.85, 1), 0.3 + 0.13 * j, 3.0))
            if melody_on:
                # motif répété (accords 1-2-3), varié sur le dernier accord
                idx = _snap(start_idx, tones)
                tt = t
                vary = k == len(prog) - 1
                for d, s in zip(rhythm, steps):
                    if vary and rng.random() < 0.5:
                        s = -s
                    idx = min(len(MELODY) - 1, max(0, idx + s))
                    if _deg(MELODY[idx]) not in tones and d >= 2:   # notes longues = notes de l'accord
                        idx = _snap(idx, tones)
                    notes.append(Note(tt, MELODY[idx], rng.uniform(0.75, 1.0), rng.uniform(0.4, 0.6),
                                      2.0 + 0.6 * d))
                    tt += d * BEAT
            t += c.length
        section += 1
    return chords, notes


def _sin(f: float, t: np.ndarray, phase: float = 0.0) -> np.ndarray:
    return np.sin(2 * np.pi * f * t + phase)


def _impulse(rng: np.random.Generator, seconds: float = 3.2) -> np.ndarray:
    """Réponse d'une salle douce : bruit qui décroît, de plus en plus sombre, décorrélé G/D."""
    n = int(seconds * SR)
    t = np.arange(n) / SR
    ir = np.zeros((n, 2))
    for ch in range(2):
        noise = rng.standard_normal(n)
        k = 12
        dark = np.convolve(noise, np.ones(k) / k, mode="same")          # adoucit les aigus
        ir[:, ch] = (0.5 * noise * np.exp(-t / 0.18) + dark * np.exp(-t / 0.55))
    pre = int(0.025 * SR)
    ir = np.vstack([np.zeros((pre, 2)), ir])
    ir /= np.sqrt((ir ** 2).sum(axis=0))
    return ir


class Reverb:
    def __init__(self, ir: np.ndarray, block: int):
        self.L = len(ir)
        self.n = 1 << int(np.ceil(np.log2(block + self.L)))
        self.H = np.fft.rfft(ir, self.n, axis=0)
        self.tail = np.zeros((self.L - 1, 2))

    def __call__(self, x: np.ndarray) -> np.ndarray:
        m = len(x)
        y = np.fft.irfft(np.fft.rfft(x, self.n, axis=0) * self.H, self.n, axis=0)[:m + self.L - 1]
        y[:self.L - 1] += self.tail
        self.tail = y[m:].copy()
        return y[:m]


def _render(t: np.ndarray, f0: float, beat: float, chords: list[Chord], cstarts: list[float],
            notes: list[Note], nstarts: list[float], seconds: float) -> tuple[np.ndarray, np.ndarray]:
    """Renvoie (son direct, envoi vers la réverbération)."""
    n = len(t)
    dry = np.zeros((n, 2))
    send = np.zeros((n, 2))
    t0, t1 = t[0], t[-1]

    # bourdon très discret, battement binaural
    swell = 0.8 + 0.2 * np.sin(2 * np.pi * t / 83.0)
    dry[:, 0] += 0.035 * swell * _sin(f0 / 4, t)
    dry[:, 1] += 0.035 * swell * _sin(f0 / 4 + beat, t)

    # nappe + basse, fondus de 3 s qui se chevauchent d'un accord à l'autre
    fade = 3.0
    k0 = max(0, bisect.bisect_right(cstarts, t0 - 30) - 1)
    for c in chords[k0:]:
        if c.start - fade > t1:
            break
        if c.start + c.length + fade < t0:
            continue
        local = t - (c.start - fade / 2)
        span = c.length + fade
        fin = np.clip(local / fade, 0, 1)
        fout = np.clip((span - local) / fade, 0, 1)
        env = np.sin(fin * np.pi / 2) * np.sin(fout * np.pi / 2)
        bass, pad, _ = CHORDS[c.name]
        for j, r in enumerate(pad):
            f = f0 * r
            a = 0.022 * env
            pad_l = a * (_sin(f, t, j) + 0.25 * _sin(f * 1.002, t, j + 1))
            pad_r = a * (_sin(f, t, j + 0.7) + 0.25 * _sin(f * 0.998, t, j + 2))
            dry[:, 0] += pad_l
            dry[:, 1] += pad_r
            send[:, 0] += 0.6 * pad_l
            send[:, 1] += 0.6 * pad_r
        fb = f0 * bass
        b = 0.05 * env * (_sin(fb, t) + 0.2 * _sin(2 * fb, t))
        dry += b[:, None]

    # notes (arpèges et mélodie) : piano feutré
    i0 = max(0, bisect.bisect_left(nstarts, t0 - 14))
    for nt in notes[i0:]:
        if nt.start > t1:
            break
        if nt.start + 7 * nt.decay < t0:
            continue
        f = f0 * nt.freq
        local = t - nt.start
        pos = np.maximum(local, 0)
        env = np.where(local >= 0, (1 - np.exp(-pos / 0.012)) * np.exp(-pos / nt.decay), 0.0)
        tone = (_sin(f, pos) + 0.30 * _sin(2 * f, pos) * np.exp(-pos / 0.9)
                + 0.10 * _sin(3 * f, pos) * np.exp(-pos / 0.45)
                + 0.04 * _sin(4 * f, pos) * np.exp(-pos / 0.25)) * env
        level = 0.07 if f < 500 else 0.06 if f < 800 else 0.045
        tone *= level * nt.gain
        l, r = tone * (1 - nt.pan) * 1.4, tone * nt.pan * 1.4
        dry[:, 0] += l
        dry[:, 1] += r
        send[:, 0] += l
        send[:, 1] += r

    return dry, send


def render(seconds: int, out_path: str, seed: int, f0: float = 432.0, beat: float = 6.0) -> None:
    rng = random.Random(seed)
    chords, notes = _plan(seconds, rng)
    cstarts = [c.start for c in chords]
    nstarts = [n.start for n in notes]
    chunk = CHUNK_S * SR
    reverb = Reverb(_impulse(np.random.default_rng(seed)), chunk)
    enc = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "s16le", "-ar", str(SR), "-ac", "2", "-i", "-",
         "-c:a", "aac", "-b:a", "192k", out_path], stdin=subprocess.PIPE)
    total = int(seconds * SR)
    for s0 in range(0, total, chunk):
        s1 = min(total, s0 + chunk)
        t = np.arange(s0, s1, dtype=np.float64) / SR
        dry, send = _render(t, f0, beat, chords, cstarts, notes, nstarts, seconds)
        out = 0.75 * dry + 0.55 * reverb(send)
        out *= (np.clip(t / 8, 0, 1) * np.clip((seconds - t) / 15, 0, 1))[:, None]
        out *= 1.6   # niveau final (crête visée ≈ 0,5, sans écrêtage)
        enc.stdin.write(np.clip(out * 32767, -32768, 32767).astype("<i2").tobytes())
    enc.stdin.close()
    if enc.wait() != 0:
        raise RuntimeError("Encodage audio échoué")
