"""Génère la bannière (2560x1440) et le filigrane (150x150) de la chaîne.

Source : branding/candidates/starry-sky-lake_4.jpg (CC0, rawpixel) — la même
image que la photo de profil, pour une identité cohérente.

Mise en page pensée pour tous les écrans :
- téléviseur : l'image entière (2560x1440) est remplie par la photo ;
- ordinateur : bande centrale 2560x423 ;
- mobile / tous appareils : zone centrale 1546x423, qui contient l'arbre
  au centre, le nom de la chaîne à gauche et l'accroche à droite.
Sortie : branding/final/
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "branding/candidates/starry-sky-lake_4.jpg"
OUT = ROOT / "branding/final"
OUT.mkdir(parents=True, exist_ok=True)
FONT_DIR = Path("/usr/share/fonts/opentype/inter")

W, H = 2560, 1440
SAFE_W, SAFE_H = 1546, 423
SX0, SY0 = (W - SAFE_W) // 2, (H - SAFE_H) // 2

src = Image.open(SRC).convert("RGB")
sw, sh = src.size
# La photo a un vignettage sombre sur les côtés : on le retire avant de prolonger.
cut = round(sw * 0.08)
body = src.crop((cut, 0, sw - cut, sh))

# Photo agrandie à la hauteur de la bannière, centrée.
s = H / sh
ph = body.resize((round(body.width * s), H), Image.LANCZOS)
ph = ph.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=3))
px = (W - ph.width) // 2

# Bords gauche/droit : on prolonge la photo avec la couleur moyenne de sa
# colonne de bord (ciel et eau sont presque uniformes sur les côtés).
def edge_band(x0, x1, width):
    col = ph.crop((x0, 0, x1, H)).resize((1, H), Image.BOX)
    return col.resize((width, H), Image.BILINEAR)

# Fond : bandes de couleur prolongées sur chaque moitié, sous la photo aussi
# (le fondu de la photo laisse apparaître ce fond, jamais du noir).
banner = Image.new("RGB", (W, H))
banner.paste(edge_band(20, 80, W // 2), (0, 0))
banner.paste(edge_band(ph.width - 80, ph.width - 20, W - W // 2), (W // 2, 0))
banner = banner.filter(ImageFilter.GaussianBlur(4))
# fondu doux entre la photo et les bords prolongés
mask = Image.new("L", ph.size, 255)
md = ImageDraw.Draw(mask)
fade = 260
for x in range(fade):
    a = round(255 * (x / fade))
    md.line([(x, 0), (x, H)], fill=a)
    md.line([(ph.width - 1 - x, 0), (ph.width - 1 - x, H)], fill=a)
banner.paste(ph, (px, 0), mask)

# Léger voile sombre derrière le texte pour la lisibilité.
veil = Image.new("L", (W, H), 0)
vd = ImageDraw.Draw(veil)
vd.rectangle((SX0 - 40, SY0 - 10, SX0 + 640, SY0 + SAFE_H + 10), fill=90)
vd.rectangle((W - SX0 - 640, SY0 - 10, W - SX0 + 40, SY0 + SAFE_H + 10), fill=90)
veil = veil.filter(ImageFilter.GaussianBlur(70))
banner = Image.composite(Image.new("RGB", (W, H), (5, 10, 25)), banner, veil)

d = ImageDraw.Draw(banner)
title_font = ImageFont.truetype(str(FONT_DIR / "InterDisplay-Light.otf"), 100)
sub_font = ImageFont.truetype(str(FONT_DIR / "Inter-Light.otf"), 40)
tag_font = ImageFont.truetype(str(FONT_DIR / "Inter-Medium.otf"), 30)

# Gauche : nom de la chaîne sur deux lignes.
lx = SX0 + 30
d.text((lx, SY0 + 70), "Calm Haven", font=title_font, fill=(240, 244, 255))
d.text((lx, SY0 + 185), "Sounds", font=title_font, fill=(240, 244, 255))

# Droite : accroche, alignée à droite.
def rtext(y, text, font, fill):
    w = d.textlength(text, font=font)
    d.text((W - SX0 - 30 - w, y), text, font=font, fill=fill)

rtext(SY0 + 110, "Long, calm soundscapes", sub_font, (210, 220, 240))
rtext(SY0 + 162, "for deep sleep", sub_font, (210, 220, 240))
rtext(SY0 + 250, "RAIN · FIREPLACE · OCEAN · NATURE", tag_font, (160, 185, 225))

banner.save(OUT / "banner.jpg", quality=92, optimize=True)

# Filigrane 150x150 : l'arbre en médaillon rond, fond transparent.
side = min(sw, sh)
crop = src.crop(((sw - side) // 2, (sh - side) // 2, (sw + side) // 2, (sh + side) // 2))
crop = crop.resize((600, 600), Image.LANCZOS)
circle = Image.new("L", (600, 600), 0)
ImageDraw.Draw(circle).ellipse((0, 0, 599, 599), fill=255)
wm = Image.new("RGBA", (600, 600), (0, 0, 0, 0))
wm.paste(crop, (0, 0), circle)
ImageDraw.Draw(wm).ellipse((4, 4, 595, 595), outline=(255, 255, 255, 230), width=10)
wm.resize((150, 150), Image.LANCZOS).save(OUT / "watermark.png")

print("OK", OUT)
