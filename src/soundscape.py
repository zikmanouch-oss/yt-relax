"""Mixage d'un paysage sonore de pluie à partir de vrais enregistrements.

Deux « voix » jouent chacune une suite de morceaux tirés au hasard dans les
enregistrements, avec des fondus longs. Leurs volumes varient lentement et en
sens opposé : la pluie se renforce, se calme, change de caractère, sans jamais
se répéter à l'identique. Du tonnerre lointain peut s'ajouter de temps en temps.
Le rendu est diffusé par blocs vers ffmpeg : la mémoire reste faible même sur 8 h.
"""
from __future__ import annotations

import random
import subprocess
from dataclasses import dataclass

import numpy as np

SR = 44100
MAX_SOURCE_S = 900       # on garde au plus 15 min de chaque enregistrement
FADE_S = 30              # fondu entre deux morceaux d'une même voix
CHUNK_S = 30             # taille des blocs de rendu


def decode(path: str, max_s: int = MAX_SOURCE_S) -> np.ndarray:
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path, "-t", str(max_s), "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
        check=True, capture_output=True).stdout
    a = np.frombuffer(raw, dtype=np.float32).reshape(-1, 2).copy()
    return a


def _normalize(a: np.ndarray, rms_target: float) -> np.ndarray:
    # RMS mesuré sur le cœur du fichier (ignore fondus d'entrée/sortie)
    core = a[len(a) // 10: -len(a) // 10 or None]
    rms = float(np.sqrt(np.mean(core ** 2))) + 1e-9
    return a * (rms_target / rms)


@dataclass
class Event:
    start: int     # échantillon de début dans la timeline
    length: int    # durée en échantillons (fondus compris)
    src: int       # index de l'enregistrement
    offset: int    # position de départ dans l'enregistrement
    fade: int      # durée des fondus
    gain: float = 1.0
    pan: float = 0.5   # utilisé pour le tonnerre


def _bed_events(total: int, sources: list[np.ndarray], rng: random.Random, phase: float) -> list[Event]:
    fade = FADE_S * SR
    events, t, last = [], -int(phase * 120 * SR), -1
    while t < total:
        choices = [i for i in range(len(sources)) if i != last] or [0]
        src = rng.choice(choices)
        n = len(sources[src])
        length = min(int(rng.uniform(150, 420) * SR), n - 2 * SR)
        length = max(length, 2 * fade + SR)
        offset = rng.randint(SR, max(SR, n - length - SR))
        events.append(Event(t, length, src, offset, fade))
        t += length - fade
        last = src
    return events


def _thunder_events(total: int, sources: list[np.ndarray], rng: random.Random) -> list[Event]:
    events, t = [], int(rng.uniform(60, 240) * SR)
    while t < total and sources:
        src = rng.randrange(len(sources))
        n = len(sources[src])
        length = min(n, int(rng.uniform(15, 40) * SR))
        offset = rng.randint(0, max(0, n - length))
        events.append(Event(t, length, src, offset, int(3 * SR),
                            gain=rng.uniform(0.35, 0.9), pan=rng.uniform(0.25, 0.75)))
        t += int(rng.uniform(180, 720) * SR)
    return events


def _envelope(total: int, rng: random.Random, lo: float, hi: float, step_s: tuple[int, int] = (120, 360)):
    """Courbe lente et lisse (points aléatoires toutes les 2 à 6 min, interpolation cosinus)."""
    xs, ys, t = [0], [rng.uniform(lo, hi)], 0
    while t < total:
        t += int(rng.uniform(*step_s) * SR)
        xs.append(t)
        ys.append(rng.uniform(lo, hi))
    xs, ys = np.array(xs, dtype=np.float64), np.array(ys)

    def at(idx: np.ndarray) -> np.ndarray:
        k = np.clip(np.searchsorted(xs, idx, side="right") - 1, 0, len(xs) - 2)
        u = (idx - xs[k]) / (xs[k + 1] - xs[k])
        u = (1 - np.cos(np.pi * np.clip(u, 0, 1))) / 2
        return (ys[k] * (1 - u) + ys[k + 1] * u).astype(np.float32)
    return at


def _render_event(ev: Event, src: np.ndarray, t0: int, t1: int, out: np.ndarray, thunder: bool) -> None:
    a, b = max(t0, ev.start), min(t1, ev.start + ev.length)
    if a >= b:
        return
    local = np.arange(a - ev.start, b - ev.start)
    seg = src[ev.offset + local]
    # fondus à puissance constante
    fin = np.clip(local / ev.fade, 0, 1)
    fout = np.clip((ev.length - local) / ev.fade, 0, 1)
    w = (np.sin(fin * np.pi / 2) * np.sin(fout * np.pi / 2)).astype(np.float32)[:, None]
    seg = seg * w * ev.gain
    if thunder:
        mono = seg.mean(axis=1)
        seg = np.stack([mono * (1 - ev.pan) * 2 ** 0.5, mono * ev.pan * 2 ** 0.5], axis=1)
    out[a - t0:b - t0] += seg


def _tones(idx: np.ndarray, total: int, beat: float, carrier: float, breathe) -> np.ndarray:
    """Battement binaural : porteuse « carrier » à gauche, « carrier + beat » à droite,
    plus une quinte douce une octave plus bas (même battement) pour un son moins sec.
    La phase est calculée à partir du temps absolu : aucune coupure entre deux blocs."""
    t = idx.astype(np.float64) / SR
    left = 0.75 * np.sin(2 * np.pi * carrier * t) + 0.25 * np.sin(2 * np.pi * carrier * 0.75 * t)
    right = (0.75 * np.sin(2 * np.pi * (carrier + beat) * t)
             + 0.25 * np.sin(2 * np.pi * (carrier * 0.75 + beat) * t))
    amp = TONE_LEVEL * breathe(idx) * np.clip(idx / (20 * SR), 0, 1)   # entrée en douceur (20 s)
    return np.stack([left * amp, right * amp], axis=1).astype(np.float32)


TONE_LEVEL = 0.07        # niveau des battements binauraux (le fond nature passe dessous)


def mix(bed_paths: list[str], thunder_paths: list[str], seconds: int, out_path: str, seed: int,
        beat: float | None = None, carrier: float = 200.0, bed_gain: float = 1.0) -> None:
    """Si « beat » est donné : ajoute un battement binaural (Hz) sur le fond sonore réel."""
    rng = random.Random(seed)
    beds = [_normalize(decode(p), 0.1) for p in bed_paths]
    beds = [b for b in beds if len(b) > 100 * SR]
    if not beds:
        raise RuntimeError("Aucun enregistrement de pluie exploitable.")
    thunders = []
    for p in thunder_paths:
        t = decode(p, 120)
        thunders.append(t / (np.max(np.abs(t)) + 1e-9) * 0.5)

    total = seconds * SR
    voices = [_bed_events(total, beds, rng, phase=0.0), _bed_events(total, beds, rng, phase=1.0)]
    thunder_ev = _thunder_events(total, thunders, rng)
    env_a = _envelope(total, rng, 0.45, 1.0)
    env_b = _envelope(total, rng, 0.45, 1.0)
    breathe = _envelope(total, rng, 0.8, 1.0, (240, 600))

    enc = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "s16le", "-ar", str(SR), "-ac", "2", "-i", "-",
         "-c:a", "aac", "-b:a", "192k", out_path], stdin=subprocess.PIPE)
    chunk = CHUNK_S * SR
    for t0 in range(0, total, chunk):
        t1 = min(total, t0 + chunk)
        idx = np.arange(t0, t1)
        buf_a = np.zeros((t1 - t0, 2), np.float32)
        buf_b = np.zeros((t1 - t0, 2), np.float32)
        for ev in voices[0]:
            _render_event(ev, beds[ev.src], t0, t1, buf_a, False)
        for ev in voices[1]:
            _render_event(ev, beds[ev.src], t0, t1, buf_b, False)
        out = (buf_a * env_a(idx)[:, None] + buf_b * env_b(idx)[:, None]) * bed_gain
        if beat:
            out += _tones(idx, total, beat, carrier, breathe)
        for ev in thunder_ev:
            _render_event(ev, thunders[ev.src], t0, t1, out, True)
        # fondu d'ouverture (5 s) et de fin (10 s)
        out *= np.clip(idx / (5 * SR), 0, 1)[:, None]
        out *= np.clip((total - idx) / (10 * SR), 0, 1)[:, None]
        out = np.tanh(out * 1.1) / 1.1
        enc.stdin.write(np.clip(out * 32767, -32768, 32767).astype("<i2").tobytes())
    enc.stdin.close()
    if enc.wait() != 0:
        raise RuntimeError("Encodage audio échoué")
