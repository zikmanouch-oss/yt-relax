"""Synthèse de sons de pluie, 100 % générés (aucun droit d'auteur).

Tout est construit dans le domaine fréquentiel : le signal obtenu par
transformée inverse est parfaitement périodique, donc la boucle se répète
sans aucune coupure audible.
"""
from __future__ import annotations

import wave
from dataclasses import dataclass

import numpy as np

SR = 44100


@dataclass
class RainParams:
    loop_seconds: int = 600          # durée de la boucle (10 min)
    intensity: str = "medium"        # light | medium | heavy
    thunder: bool = False
    seed: int = 0


INTENSITY = {
    #          gouttes/s, niveau gouttes, centre du souffle (Hz)
    "light":  (35,  0.55, 3500),
    "medium": (90,  0.45, 2800),
    "heavy":  (220, 0.35, 2200),
}


def _band(freqs: np.ndarray, lo: float, hi: float, slope: float = 1.0) -> np.ndarray:
    """Filtre passe-bande doux (gain en amplitude) défini sur l'axe fréquentiel."""
    f = np.maximum(freqs, 1.0)
    hp = 1.0 / np.sqrt(1.0 + (lo / f) ** (2 * slope))
    lp = 1.0 / np.sqrt(1.0 + (f / hi) ** (2 * slope))
    return hp * lp


def _periodic_noise(n: int, shape: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    spec = (rng.standard_normal(shape.size) + 1j * rng.standard_normal(shape.size)) * shape
    spec[0] = 0
    return np.fft.irfft(spec, n=n).astype(np.float32)


def _circular_place(n: int, times: np.ndarray, amps: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    """Place un motif court à des instants donnés, avec bouclage circulaire."""
    out = np.zeros(n, dtype=np.float32)
    k = kernel.size
    idx = (times[:, None] + np.arange(k)[None, :]) % n
    np.add.at(out, idx.ravel(), (amps[:, None] * kernel[None, :]).ravel())
    return out


def _drop_kernels(rng: np.random.Generator, count: int = 24) -> list[np.ndarray]:
    """Petits impacts de gouttes : bruit filtré à décroissance rapide."""
    kernels = []
    for _ in range(count):
        length = int(SR * rng.uniform(0.008, 0.03))
        t = np.arange(length) / SR
        env = np.exp(-t / rng.uniform(0.002, 0.008))
        noise = rng.standard_normal(length)
        # filtre passe-haut simple (différence) pour un « tic » clair
        noise = np.diff(noise, prepend=0.0)
        kernels.append((noise * env).astype(np.float32))
    return kernels


def _slow_lfo(n: int, rng: np.random.Generator, cycles: tuple[int, int] = (3, 9), depth: float = 0.15) -> np.ndarray:
    """Modulation lente d'intensité, périodique (nombre entier de cycles par boucle)."""
    t = np.arange(n, dtype=np.float32) / n
    lfo = np.zeros(n, dtype=np.float32)
    for _ in range(3):
        c = rng.integers(*cycles)
        lfo += np.sin(2 * np.pi * (c * t + rng.random())).astype(np.float32)
    return 1.0 + depth * lfo / 3.0


def synth_rain(p: RainParams) -> np.ndarray:
    """Retourne un tableau stéréo (n, 2) float32 dans [-1, 1]."""
    rng = np.random.default_rng(p.seed)
    n = SR * p.loop_seconds
    freqs = np.fft.rfftfreq(n, 1 / SR)
    rate, drop_level, centre = INTENSITY[p.intensity]

    channels = []
    kernels = _drop_kernels(rng)
    for _ch in range(2):
        # 1) souffle continu de la pluie (bruit rose filtré)
        pink = 1.0 / np.sqrt(np.maximum(freqs, 20.0))
        hiss = _periodic_noise(n, pink * _band(freqs, 300, centre * 2.2), rng)
        hiss /= np.std(hiss) + 1e-9
        hiss *= _slow_lfo(n, rng)

        # 2) grondement sourd (pluie lointaine, bruit brun)
        brown = 1.0 / np.maximum(freqs, 20.0)
        rumble = _periodic_noise(n, brown * _band(freqs, 30, 250), rng)
        rumble /= np.std(rumble) + 1e-9

        # 3) gouttes individuelles
        count = int(rate * p.loop_seconds)
        times = rng.integers(0, n, count)
        amps = (rng.lognormal(0, 0.6, count) * rng.choice([-1, 1], count)).astype(np.float32)
        drops = np.zeros(n, dtype=np.float32)
        groups = np.array_split(np.arange(count), len(kernels))
        for kern, g in zip(kernels, groups):
            if g.size:
                drops += _circular_place(n, times[g], amps[g], kern)
        drops /= np.std(drops) + 1e-9

        mix = 1.0 * hiss + 0.35 * rumble + drop_level * drops
        channels.append(mix)

    stereo = np.stack(channels, axis=1)
    # léger mélange des canaux pour un champ stéréo naturel
    stereo = 0.8 * stereo + 0.2 * stereo[:, ::-1]

    if p.thunder:
        stereo += _thunder(n, freqs, rng)

    # normalisation : RMS ≈ -20 dBFS, crêtes limitées en douceur
    rms = np.sqrt(np.mean(stereo ** 2))
    stereo *= 0.1 / (rms + 1e-9)
    stereo = np.tanh(stereo * 1.2) / 1.2
    return stereo.astype(np.float32)


def _thunder(n: int, freqs: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Quelques grondements de tonnerre lointains, placés en boucle circulaire."""
    out = np.zeros((n, 2), dtype=np.float32)
    events = max(1, n // (SR * 90))  # environ un toutes les 90 s
    for _ in range(events):
        length = int(SR * rng.uniform(5, 11))
        f = np.fft.rfftfreq(length, 1 / SR)
        spec = (rng.standard_normal(f.size) + 1j * rng.standard_normal(f.size)) / np.maximum(f, 15.0) * _band(f, 25, 180)
        burst = np.fft.irfft(spec, n=length)
        t = np.linspace(0, 1, length)
        env = (1 - np.exp(-t * 8)) * np.exp(-t * rng.uniform(2.5, 4.5))
        burst = burst * env
        burst /= np.max(np.abs(burst)) + 1e-9
        burst *= rng.uniform(0.6, 1.4)
        start = rng.integers(0, n)
        pan = rng.uniform(0.3, 0.7)
        idx = (start + np.arange(length)) % n
        out[idx, 0] += (burst * (1 - pan)).astype(np.float32)
        out[idx, 1] += (burst * pan).astype(np.float32)
    return out * 0.9


def write_wav(path: str, stereo: np.ndarray) -> None:
    pcm = np.clip(stereo * 32767, -32768, 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
