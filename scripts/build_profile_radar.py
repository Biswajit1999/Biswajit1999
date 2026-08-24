"""Build a faithful photo + binary portrait + Earth-radar README animation."""

from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "profile-source.jpg"
OUTPUT = ROOT / "assets" / "binary-earth-radar.gif"
W, H, FRAME_COUNT = 1200, 360, 32


def load_font(size: int, bold: bool = False):
    candidates = [Path("C:/Windows/Fonts/consolab.ttf" if bold else "C:/Windows/Fonts/consola.ttf"), Path("C:/Windows/Fonts/arial.ttf")]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


TINY, SMALL, LABEL = load_font(9), load_font(11), load_font(13, True)
random.seed(73)
stars = [(random.randrange(690, W - 18), random.randrange(55, H - 22), random.choice((1, 1, 1, 2)), random.random()) for _ in range(52)]


def prepare_photo() -> Image.Image:
    image = Image.open(SOURCE).convert("RGB")
    image = ImageOps.fit(image, (285, 285), method=Image.Resampling.LANCZOS, centering=(0.5, 0.43))
    image = ImageEnhance.Contrast(image).enhance(1.04)
    mask = Image.new("L", image.size)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, 284, 284), radius=12, fill=255)
    result = image.convert("RGBA")
    result.putalpha(mask)
    return result


PHOTO = prepare_photo()
GRAY = ImageOps.grayscale(Image.open(SOURCE).convert("RGB"))
GRAY = ImageOps.fit(GRAY, (240, 280), method=Image.Resampling.LANCZOS, centering=(0.5, 0.43))


def binary_portrait(frame_index: int) -> Image.Image:
    """Render the actual source pixels as 0/1 glyphs—no generative face changes."""
    panel = Image.new("RGBA", (270, 285), (4, 11, 27, 255))
    draw = ImageDraw.Draw(panel)
    cols, rows, cell_w, cell_h = 48, 35, 5, 8
    sampled = GRAY.resize((cols, rows), Image.Resampling.BILINEAR)
    scan_row = (frame_index * 2) % rows
    for row in range(rows):
        for col in range(cols):
            lum = sampled.getpixel((col, row)) / 255
            if lum < 0.11:
                continue
            bit = "1" if (col * 7 + row * 11 + frame_index // 4) % 2 else "0"
            boost = 1.35 if abs(row - scan_row) <= 1 else 1.0
            alpha = int(min(255, (35 + lum * 220) * boost))
            color = (38, int(155 + lum * 95), 255, alpha) if lum < 0.62 else (120, 255, 225, alpha)
            draw.text((14 + col * cell_w, 2 + row * cell_h), bit, font=TINY, fill=color)
    scan_y = 2 + scan_row * cell_h
    draw.line((8, scan_y, 262, scan_y), fill=(75, 255, 218, 150), width=1)
    return panel


def add_glow(canvas: Image.Image, center: tuple[int, int], radius: int, color: tuple[int, int, int], alpha: int):
    layer = Image.new("RGBA", canvas.size)
    draw = ImageDraw.Draw(layer)
    x, y = center
    draw.ellipse((x - radius * 3, y - radius * 3, x + radius * 3, y + radius * 3), fill=(*color, alpha))
    canvas.alpha_composite(layer.filter(ImageFilter.GaussianBlur(radius * 2)))


def build_frame(index: int) -> Image.Image:
    phase = index / FRAME_COUNT
    canvas = Image.new("RGBA", (W, H), (3, 8, 23, 255))
    draw = ImageDraw.Draw(canvas)
    for y in range(H):
        draw.line((0, y, W, y), fill=(3 + y // 90, 8 + y // 120, 23 + y // 30, 255))

    # Two faithful versions side by side: original source and exact pixel-derived binary map.
    canvas.alpha_composite(PHOTO, (24, 50))
    canvas.alpha_composite(binary_portrait(index), (325, 50))
    draw = ImageDraw.Draw(canvas)
    draw.text((24, 25), "SOURCE / BISWAJIT JANA", font=LABEL, fill=(126, 213, 255, 255))
    draw.text((325, 25), "BINARY SIGNAL MAP", font=LABEL, fill=(126, 213, 255, 255))
    draw.rounded_rectangle((24, 50, 309, 335), radius=12, outline=(36, 88, 133, 255), width=1)
    draw.rounded_rectangle((325, 50, 595, 335), radius=12, outline=(36, 88, 133, 255), width=1)
    draw.line((620, 25, 620, 335), fill=(36, 88, 133, 210), width=1)

    for sx, sy, radius, offset in stars:
        alpha = int(65 + 170 * (0.5 + 0.5 * math.sin((phase + offset) * math.tau)))
        draw.ellipse((sx - radius, sy - radius, sx + radius, sy + radius), fill=(120, 226, 255, alpha))

    draw.text((650, 25), "DEEP SPACE / EARTH ANALOGUE SEARCH", font=LABEL, fill=(126, 213, 255, 255))
    draw.text((1168, 27), "● ONLINE", anchor="ra", font=SMALL, fill=(57, 255, 186, 255))
    cx, cy, max_radius = 900, 195, 128
    for radius in (32, 64, 96, 128):
        draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), outline=(32, 123, 150, 145), width=1)
    for degrees in range(0, 360, 45):
        radians = math.radians(degrees)
        draw.line((cx, cy, cx + math.cos(radians) * max_radius, cy + math.sin(radians) * max_radius), fill=(27, 82, 111, 120), width=1)

    angle = phase * math.tau - math.pi / 2
    sweep = Image.new("RGBA", canvas.size)
    sweep_draw = ImageDraw.Draw(sweep)
    sweep_points = [(cx, cy)]
    for offset in range(0, 31, 3):
        radians = angle - math.radians(offset)
        sweep_points.append((cx + math.cos(radians) * max_radius, cy + math.sin(radians) * max_radius))
    sweep_draw.polygon(sweep_points, fill=(24, 238, 219, 32))
    endpoint = (cx + math.cos(angle) * max_radius, cy + math.sin(angle) * max_radius)
    sweep_draw.line((cx, cy, *endpoint), fill=(78, 255, 226, 235), width=3)
    canvas.alpha_composite(sweep.filter(ImageFilter.GaussianBlur(1.1)))

    target = (1015, 91)
    target_angle = math.atan2(target[1] - cy, target[0] - cx)
    delta = abs((angle - target_angle + math.pi) % math.tau - math.pi)
    acquired = delta < 0.37
    add_glow(canvas, target, 10 if acquired else 7, (60, 220, 255), 225 if acquired else 90)
    draw = ImageDraw.Draw(canvas)
    tx, ty = target
    draw.ellipse((tx - 10, ty - 10, tx + 10, ty + 10), fill=(42, 139, 235, 255), outline=(145, 246, 255, 255), width=1)
    draw.arc((tx - 8, ty - 7, tx + 8, ty + 7), 195, 350, fill=(72, 235, 152, 255), width=4)
    if acquired:
        pulse = 18 + int(8 * math.sin(phase * math.tau * 4) ** 2)
        draw.ellipse((tx - pulse, ty - pulse, tx + pulse, ty + pulse), outline=(78, 255, 216, 230), width=2)
        draw.line((tx + 22, ty, 1164, ty), fill=(78, 255, 216, 170), width=1)
        draw.text((1168, ty - 7), "EARTH?", anchor="ra", font=SMALL, fill=(78, 255, 216, 255))

    draw.text((650, 326), "SCANNING HABITABLE ZONE", font=SMALL, fill=(101, 139, 180, 255))
    draw.text((1168, 326), f"BEARING {int((math.degrees(angle) + 360) % 360):03d}°", anchor="ra", font=SMALL, fill=(101, 139, 180, 255))
    draw.rounded_rectangle((10, 10, W - 10, H - 10), radius=14, outline=(35, 72, 118, 230), width=1)
    return canvas.convert("RGB")


def main():
    frames = [build_frame(i) for i in range(FRAME_COUNT)]
    frames[0].save(OUTPUT, save_all=True, append_images=frames[1:], duration=95, loop=0, optimize=True, disposal=2)
    print(f"Wrote {OUTPUT} ({OUTPUT.stat().st_size / 1024 / 1024:.2f} MiB)")


if __name__ == "__main__":
    main()
