"""Visuels générés : scène de pluie nocturne derrière une vitre, et miniature."""
from __future__ import annotations

import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1920, 1080

PALETTES = [
    # (haut, bas, lumières)
    ((8, 14, 30), (20, 42, 64), [(255, 190, 110), (255, 150, 90), (120, 170, 255)]),
    ((10, 12, 24), (34, 30, 58), [(255, 120, 160), (140, 120, 255), (255, 200, 140)]),
    ((6, 18, 22), (18, 52, 58), [(120, 230, 210), (255, 210, 130), (90, 160, 255)]),
    ((14, 14, 18), (44, 40, 40), [(255, 170, 80), (255, 230, 170), (255, 120, 70)]),
]

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]


def _gradient(top, bottom) -> Image.Image:
    t = np.linspace(0, 1, H)[:, None, None]
    arr = (1 - t) * np.array(top) + t * np.array(bottom)
    arr = np.broadcast_to(arr, (H, W, 3))
    return Image.fromarray(arr.astype(np.uint8), "RGB")


def rain_scene(seed: int, path: str) -> None:
    rng = np.random.default_rng(seed)
    top, bottom, lights = PALETTES[seed % len(PALETTES)]
    img = _gradient(top, bottom)

    # lumières de ville floues (bokeh)
    bokeh = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(bokeh)
    for _ in range(rng.integers(45, 80)):
        x = rng.uniform(0, W)
        y = rng.uniform(H * 0.35, H * 1.05)
        r = rng.uniform(18, 75)
        c = lights[rng.integers(len(lights))]
        k = rng.uniform(0.25, 0.8)
        d.ellipse([x - r, y - r, x + r, y + r], fill=tuple(int(v * k) for v in c))
    bokeh = bokeh.filter(ImageFilter.GaussianBlur(28))
    img = Image.fromarray(np.clip(np.asarray(img, np.int16) + np.asarray(bokeh, np.int16), 0, 255).astype(np.uint8))

    # traînées de pluie
    streaks = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(streaks)
    angle = rng.uniform(-0.12, 0.05)
    for _ in range(1400):
        x = rng.uniform(-100, W + 100)
        y = rng.uniform(-50, H)
        length = rng.uniform(25, 90)
        d.line([x, y, x + angle * length, y + length], fill=int(rng.uniform(25, 85)), width=1)
    streaks = streaks.filter(ImageFilter.GaussianBlur(0.6))

    # gouttes sur la vitre
    drops = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(drops)
    for _ in range(260):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        r = rng.uniform(2, 7)
        d.ellipse([x - r, y - r * 1.2, x + r, y + r * 1.2], fill=int(rng.uniform(40, 110)))
    drops = drops.filter(ImageFilter.GaussianBlur(1.2))

    base = np.asarray(img, np.float32)
    light = (np.asarray(streaks, np.float32) + np.asarray(drops, np.float32))[..., None] / 255.0
    base = base + light * np.array([170, 190, 215], np.float32)

    # vignette
    yy, xx = np.mgrid[0:H, 0:W]
    dist = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    vignette = np.clip(1.15 - 0.45 * dist ** 1.6, 0.35, 1.0)[..., None]
    base = np.clip(base * vignette, 0, 255).astype(np.uint8)
    Image.fromarray(base).save(path, optimize=True)


def _font(size: int) -> ImageFont.ImageFont:
    for f in FONT_CANDIDATES:
        if os.path.exists(f):
            return ImageFont.truetype(f, size)
    return ImageFont.load_default(size)


def thumbnail(scene_path: str, line1: str, line2: str, path: str) -> None:
    img = Image.open(scene_path).convert("RGB").resize((1280, 720), Image.LANCZOS)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    f1, f2 = _font(130), _font(62)
    for text, font, y in ((line1, f1, 230), (line2, f2, 400)):
        w = d.textlength(text, font=font)
        x = (1280 - w) / 2
        d.text((x + 4, y + 5), text, font=font, fill=(0, 0, 0, 170))
        d.text((x, y), text, font=font, fill=(255, 255, 255, 255))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    img.save(path, "JPEG", quality=90)
