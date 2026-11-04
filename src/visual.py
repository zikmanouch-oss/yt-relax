"""Miniature YouTube à partir d'une image de la vidéo."""
from __future__ import annotations

import os

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]


def _font(size: int) -> ImageFont.ImageFont:
    for f in FONT_CANDIDATES:
        if os.path.exists(f):
            return ImageFont.truetype(f, size)
    return ImageFont.load_default(size)


def thumbnail(frame_path: str, line1: str, line2: str, path: str) -> None:
    img = Image.open(frame_path).convert("RGB").resize((1280, 720), Image.LANCZOS)
    img = ImageEnhance.Contrast(ImageEnhance.Color(img).enhance(1.15)).enhance(1.08)

    # assombrissement doux au centre pour la lisibilité du texte
    yy = np.linspace(-1, 1, 720)[:, None]
    shade = 1 - 0.45 * np.exp(-(yy / 0.45) ** 2)
    arr = (np.asarray(img, np.float32) * shade[..., None]).clip(0, 255).astype(np.uint8)
    img = Image.fromarray(arr).convert("RGBA")

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    size1 = 130
    while d.textlength(line1, font=_font(size1)) > 1180:
        size1 -= 6
    f1, f2 = _font(size1), _font(60)
    for text, font, y in ((line1, f1, 360 - size1 + 10), (line2, f2, 400)):
        w = d.textlength(text, font=font)
        x = (1280 - w) / 2
        d.text((x + 4, y + 5), text, font=font, fill=(0, 0, 0, 180))
        d.text((x, y), text, font=font, fill=(255, 255, 255, 255))
    Image.alpha_composite(img, overlay).convert("RGB").save(path, "JPEG", quality=90)
