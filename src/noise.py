"""Bruits colorés synthétisés (brun, rose, vert, blanc) pour le sommeil et la concentration.

Aucun enregistrement : bruit blanc gaussien filtré, calculé par blocs avec l'état des
filtres reporté d'un bloc au suivant (aucune coupure sur 8 h), niveau constant.
- brun  : grave et enveloppant (−6 dB/octave), sans infra-basses ;
- rose  : équilibré (−3 dB/octave), proche d'une pluie régulière ;
- vert  : centré sur les médiums (≈ 500 Hz), « bruit de fond de la nature » ;
- blanc : toutes les fréquences, légèrement adouci dans l'extrême aigu.
Les deux canaux sont en partie indépendants : son large mais stable au casque.
"""
from __future__ import annotations

import subprocess

import numpy as np
from scipy import signal

SR = 44100
CHUNK_S = 30
TARGET_RMS = 0.085      # ≈ −21 dBFS : confortable, large marge avant saturation

# filtre « rose » de Paul Kellet (approximation −3 dB/octave)
PINK_B = [0.049922035, -0.095993537, 0.050612699, -0.004408786]
PINK_A = [1.0, -2.494956002, 2.017265875, -0.522189400]


def _chain(color: str) -> list[tuple[np.ndarray, np.ndarray]]:
    """Suite de filtres (b, a) appliqués au bruit blanc."""
    hp = signal.butter(2, 28, "highpass", fs=SR)            # pas d'infra-basses (inutile et fatigant)
    if color == "brown":
        return [(np.array([1.0]), np.array([1.0, -0.9975])), hp, signal.butter(1, 9000, "lowpass", fs=SR)]
    if color == "pink":
        return [(np.array(PINK_B), np.array(PINK_A)), hp]
    if color == "green":
        return [(np.array(PINK_B), np.array(PINK_A)), signal.butter(1, [180, 1400], "bandpass", fs=SR), hp]
    if color == "white":
        return [hp, signal.butter(1, 11000, "lowpass", fs=SR)]
    raise ValueError(f"Couleur de bruit inconnue : {color}")


class _Voice:
    def __init__(self, color: str, rng: np.random.Generator):
        self.rng = rng
        self.filters = _chain(color)
        self.state = [signal.lfilter_zi(b, a) * 0.0 for b, a in self.filters]

    def render(self, n: int) -> np.ndarray:
        x = self.rng.standard_normal(n)
        for k, (b, a) in enumerate(self.filters):
            x, self.state[k] = signal.lfilter(b, a, x, zi=self.state[k])
        return x


def render(seconds: int, out_path: str, seed: int, color: str = "brown") -> None:
    rng = np.random.default_rng(seed)
    left, right = _Voice(color, rng), _Voice(color, rng)
    for v in (left, right):          # mise en régime des filtres (jetée)
        v.render(3 * SR)
    probe = np.stack([left.render(10 * SR), right.render(10 * SR)], axis=1)
    probe = probe + 0.35 * probe[:, ::-1]
    gain = TARGET_RMS / (float(np.sqrt(np.mean(probe ** 2))) + 1e-12)

    enc = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "s16le", "-ar", str(SR), "-ac", "2", "-i", "-",
         "-c:a", "aac", "-b:a", "192k", out_path], stdin=subprocess.PIPE)
    total = int(seconds * SR)
    chunk = CHUNK_S * SR
    for s0 in range(0, total, chunk):
        n = min(chunk, total - s0)
        a = np.stack([left.render(n), right.render(n)], axis=1)
        a = (a + 0.35 * a[:, ::-1]) * gain
        t = (np.arange(s0, s0 + n) / SR)
        a *= (np.clip(t / 6, 0, 1) * np.clip((seconds - t) / 10, 0, 1))[:, None]   # entrée 6 s, sortie 10 s
        enc.stdin.write(np.clip(a * 32767, -32768, 32767).astype("<i2").tobytes())
    enc.stdin.close()
    if enc.wait() != 0:
        raise RuntimeError("Encodage audio échoué")
