"""Build the animated binary-portrait / Earth-search README hero."""

from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "binary-portrait.png"
OUTPUT = ROOT / "assets" / "binary-earth-radar.gif"
W, H = 1200, 360
FRAMES = 32


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    names = [
        Path("C:/Windows/Fonts/consolab.ttf" if bold else "C:/Windows/Fonts/consola.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
    ]
    for name in names:
        if name.exists():
            return ImageFont.truetype(str(name), size)
    return ImageFont.load_default()


LABEL = font(14, True)
SMALL = font(11)
MEDIUM = font(18, True)
random.seed(19)
stars = [(random.randrange(400, W), random.randrange(20, H - 20), random.choice((1, 1, 1, 2)), random.random()) for _ in range(80)]
bits = [(random.randrange(15, 420), random.randrange(-H, H), random.choice("01"), random.random()) for _ in range(95)]


def fit_portrait() -> Image.Image:
    im = Image.open(SOURCE).convert("RGB")
    # The generated artwork is square; retain the face and shoulders.
    im = im.resize((410, 410), Image.Resampling.LANCZOS).crop((0, 18, 410, 378))
    im = ImageEnhance.Contrast(im).enhance(1.08)
    mask = Image.new("L", (410, H), 255)
    md = ImageDraw.Draw(mask)
    for x in range(330, 410):
        md.rectangle((x, 0, x, H), fill=max(0, 255 - (x - 330) * 4))
    rgba = im.convert("RGBA")
    rgba.putalpha(mask)
    return rgba


PORTRAIT = fit_portrait()


def glow_dot(layer: Image.Image, xy: tuple[int, int], radius: int, color: tuple[int, int, int], strength: int = 180) -> None:
    glow = Image.new("RGBA", layer.size)
    gd = ImageDraw.Draw(glow)
    x, y = xy
    gd.ellipse((x - radius * 3, y - radius * 3, x + radius * 3, y + radius * 3), fill=(*color, strength))
    glow = glow.filter(ImageFilter.GaussianBlur(radius * 2))
    layer.alpha_composite(glow)


def frame(index: int) -> Image.Image:
    phase = index / FRAMES
    canvas = Image.new("RGBA", (W, H), (3, 8, 24, 255))
    bg = Image.new("RGBA", (W, H))
    bd = ImageDraw.Draw(bg)
    for y in range(H):
        t = y / H
        bd.line((0, y, W, y), fill=(4 + int(7 * t), 10, 30 + int(16 * t), 255))
    canvas.alpha_composite(bg)

    d = ImageDraw.Draw(canvas)
    for sx, sy, sr, tw in stars:
        alpha = int(80 + 150 * (0.5 + 0.5 * math.sin((phase + tw) * math.tau)))
        d.ellipse((sx - sr, sy - sr, sx + sr, sy + sr), fill=(120, 225, 255, alpha))

    canvas.alpha_composite(PORTRAIT, (0, 0))
    # Moving binary rain adds actual animation to the portrait treatment.
    for bx, by, value, speed in bits:
        yy = int((by + phase * (120 + speed * 150)) % (H + 30) - 15)
        alpha = int(45 + speed * 125)
        d.text((bx, yy), value, font=SMALL, fill=(20, 225, 255, alpha))

    # Separator and compact header line.
    d.line((420, 26, 420, H - 26), fill=(42, 92, 140, 180), width=1)
    d.text((455, 28), "DEEP SPACE SEARCH ARRAY", font=LABEL, fill=(120, 220, 255, 255))
    d.text((1160, 30), "ONLINE", anchor="ra", font=SMALL, fill=(58, 255, 186, 255))
    d.ellipse((1103, 29, 1111, 37), fill=(58, 255, 186, 255))

    # Radar grid.
    cx, cy, max_r = 800, 192, 132
    for r in (33, 66, 99, 132):
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(32, 116, 144, 130), width=1)
    for angle in range(0, 360, 45):
        rad = math.radians(angle)
        d.line((cx, cy, cx + math.cos(rad) * max_r, cy + math.sin(rad) * max_r), fill=(25, 84, 111, 105), width=1)

    angle = phase * math.tau - math.pi / 2
    sweep = Image.new("RGBA", (W, H))
    sd = ImageDraw.Draw(sweep)
    points = [(cx, cy)]
    for offset in range(0, 27, 3):
        a = angle - math.radians(offset)
        points.append((cx + math.cos(a) * max_r, cy + math.sin(a) * max_r))
    sd.polygon(points, fill=(25, 235, 220, 28))
    ex, ey = cx + math.cos(angle) * max_r, cy + math.sin(angle) * max_r
    sd.line((cx, cy, ex, ey), fill=(80, 255, 229, 235), width=3)
    sweep = sweep.filter(ImageFilter.GaussianBlur(1.2))
    canvas.alpha_composite(sweep)

    # Earth-analogue target at bearing 320 degrees.
    tx, ty = 918, 93
    target_angle = math.atan2(ty - cy, tx - cx)
    delta = abs((angle - target_angle + math.pi) % math.tau - math.pi)
    acquired = delta < 0.36
    glow_dot(canvas, (tx, ty), 10 if acquired else 7, (60, 220, 255), 230 if acquired else 100)
    d = ImageDraw.Draw(canvas)
    d.ellipse((tx - 10, ty - 10, tx + 10, ty + 10), fill=(45, 143, 237, 255), outline=(145, 245, 255, 255), width=1)
    d.arc((tx - 8, ty - 7, tx + 8, ty + 7), 195, 350, fill=(75, 235, 155, 255), width=4)
    if acquired:
        pulse = 18 + int(7 * math.sin(phase * math.tau * 4) ** 2)
        d.ellipse((tx - pulse, ty - pulse, tx + pulse, ty + pulse), outline=(78, 255, 216, 230), width=2)
        d.line((tx + 20, ty, 1084, ty), fill=(78, 255, 216, 180), width=1)
        d.text((1090, ty - 8), "TARGET ACQUIRED", font=SMALL, fill=(78, 255, 216, 255))

    d.text((455, 325), "EARTH ANALOGUE SEARCH", font=SMALL, fill=(107, 139, 181, 255))
    d.text((1160, 325), f"SCAN {index + 1:02d}/{FRAMES:02d}", anchor="ra", font=SMALL, fill=(107, 139, 181, 255))
    d.rectangle((20, 18, W - 20, H - 18), outline=(37, 72, 118, 220), width=1)
    return canvas.convert("RGB")


def main() -> None:
    frames = [frame(i) for i in range(FRAMES)]
    frames[0].save(
        OUTPUT,
        save_all=True,
        append_images=frames[1:],
        duration=90,
        loop=0,
        optimize=True,
        disposal=2,
    )
    print(f"Wrote {OUTPUT} ({OUTPUT.stat().st_size / 1024 / 1024:.2f} MiB)")


if __name__ == "__main__":
    main()
