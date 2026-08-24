"""Build the animated digital-observer / Earth-search profile hero."""

from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "binary-avatar.png"
OUTPUT = ROOT / "assets" / "binary-earth-radar.gif"
W, H, FRAME_COUNT = 1200, 360, 36


def font(size: int, bold: bool = False):
    paths = [Path("C:/Windows/Fonts/consolab.ttf" if bold else "C:/Windows/Fonts/consola.ttf"), Path("C:/Windows/Fonts/arial.ttf")]
    for path in paths:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


TINY, SMALL, LABEL, TITLE = font(9), font(11), font(13, True), font(18, True)
random.seed(3199)
stars = [(random.randrange(18, W - 18), random.randrange(18, H - 18), random.choice((1, 1, 1, 2)), random.random()) for _ in range(120)]
data_bits = [(random.randrange(770, 1190), random.randrange(-H, H), random.choice("01"), random.random()) for _ in range(100)]
constellation = [(435, 82), (520, 53), (594, 104), (665, 68), (738, 98), (820, 61)]


def prepare_avatar() -> Image.Image:
    avatar = Image.open(SOURCE).convert("RGB")
    avatar = ImageOps.fit(avatar, (430, 430), method=Image.Resampling.LANCZOS, centering=(0.52, 0.48)).crop((0, 30, 430, 390))
    avatar = ImageEnhance.Contrast(avatar).enhance(1.12)
    # The avatar is deliberately only a ghost in the system, never a dominant portrait.
    mask = Image.new("L", (430, H), 24)
    md = ImageDraw.Draw(mask)
    for x in range(0, 150):
        md.line((x, 0, x, H), fill=int(24 * x / 150))
    for y in range(285, H):
        md.line((0, y, 430, y), fill=max(0, 24 - (y - 285)))
    result = avatar.convert("RGBA")
    result.putalpha(mask)
    return result


AVATAR = prepare_avatar()


def glow(canvas: Image.Image, xy: tuple[int, int], radius: int, color: tuple[int, int, int], alpha: int = 180):
    layer = Image.new("RGBA", canvas.size)
    draw = ImageDraw.Draw(layer)
    x, y = xy
    draw.ellipse((x - radius * 3, y - radius * 3, x + radius * 3, y + radius * 3), fill=(*color, alpha))
    canvas.alpha_composite(layer.filter(ImageFilter.GaussianBlur(radius * 2)))


def frame(index: int) -> Image.Image:
    phase = index / FRAME_COUNT
    canvas = Image.new("RGBA", (W, H), (2, 6, 20, 255))
    draw = ImageDraw.Draw(canvas)
    for y in range(H):
        draw.line((0, y, W, y), fill=(2 + y // 120, 6 + y // 90, 20 + y // 22, 255))

    # Faint futuristic hex lattice.
    for gx in range(0, W, 62):
        for gy in range(-20, H, 54):
            points = [(gx + math.cos(math.radians(a)) * 31, gy + math.sin(math.radians(a)) * 31) for a in range(0, 360, 60)]
            draw.line(points + [points[0]], fill=(20, 78, 112, 30), width=1)

    for sx, sy, radius, offset in stars:
        alpha = int(55 + 175 * (0.5 + 0.5 * math.sin((phase + offset) * math.tau)))
        draw.ellipse((sx - radius, sy - radius, sx + radius, sy + radius), fill=(120, 229, 255, alpha))

    # The faint digital observer lives at the far right, behind the interface.
    canvas.alpha_composite(AVATAR, (770, 0))
    draw = ImageDraw.Draw(canvas)
    for bx, by, bit, speed in data_bits:
        yy = int((by + phase * (100 + speed * 190)) % (H + 30) - 15)
        flicker = 0.45 + 0.55 * math.sin((phase * 3 + speed) * math.tau) ** 2
        draw.text((bx, yy), bit, font=TINY, fill=(42, 224, 255, int((55 + speed * 145) * flicker)))

    # Constellation pathway carries the scan from radar toward the observer field.
    for a, b in zip(constellation, constellation[1:]):
        draw.line((*a, *b), fill=(89, 129, 205, 80), width=1)
    for point in constellation:
        glow(canvas, point, 2, (89, 222, 255), 110)
        draw.ellipse((point[0] - 2, point[1] - 2, point[0] + 2, point[1] + 2), fill=(169, 244, 255, 230))

    draw.text((35, 28), "EXO-RADAR // DEEP FIELD", font=LABEL, fill=(105, 228, 255, 255))
    draw.text((420, 28), "SEARCHING FOR ANOTHER EARTH", font=TITLE, fill=(224, 245, 255, 255))
    draw.text((1164, 31), "● DEEP SPACE LINK", anchor="ra", font=SMALL, fill=(55, 255, 187, 255))

    # Radar and orbital search field.
    cx, cy, radius = 225, 198, 126
    for ring in (31, 62, 94, 126):
        draw.ellipse((cx - ring, cy - ring, cx + ring, cy + ring), outline=(32, 129, 158, 150), width=1)
    for degrees in range(0, 360, 30):
        radians = math.radians(degrees)
        draw.line((cx, cy, cx + math.cos(radians) * radius, cy + math.sin(radians) * radius), fill=(25, 78, 112, 100), width=1)
    draw.ellipse((cx - 145, cy - 88, cx + 145, cy + 88), outline=(89, 81, 209, 95), width=1)

    # Counter-rotating orbital objects add depth beyond a flat radar sweep.
    for orbit_index, (orbit_radius, speed, color) in enumerate(((148, 1.35, (103, 112, 255)), (104, -1.8, (44, 238, 213)))):
        orbit_angle = phase * math.tau * speed + orbit_index * 1.7
        ox = cx + math.cos(orbit_angle) * orbit_radius
        oy = cy + math.sin(orbit_angle) * orbit_radius * 0.58
        draw.ellipse((cx - orbit_radius, cy - orbit_radius * 0.58, cx + orbit_radius, cy + orbit_radius * 0.58), outline=(*color, 62), width=1)
        glow(canvas, (int(ox), int(oy)), 3, color, 130)
        draw.ellipse((ox - 3, oy - 3, ox + 3, oy + 3), fill=(*color, 245))

    angle = phase * math.tau - math.pi / 2
    sweep = Image.new("RGBA", canvas.size)
    sd = ImageDraw.Draw(sweep)
    wedge = [(cx, cy)]
    for offset in range(0, 38, 3):
        radians = angle - math.radians(offset)
        wedge.append((cx + math.cos(radians) * radius, cy + math.sin(radians) * radius))
    sd.polygon(wedge, fill=(35, 244, 215, 36))
    endpoint = (cx + math.cos(angle) * radius, cy + math.sin(angle) * radius)
    sd.line((cx, cy, *endpoint), fill=(89, 255, 225, 245), width=3)
    canvas.alpha_composite(sweep.filter(ImageFilter.GaussianBlur(1.1)))

    # Earth analogue: a small living world with target acquisition pulse.
    tx, ty = 405, 105
    bearing = math.atan2(ty - cy, tx - cx)
    delta = abs((angle - bearing + math.pi) % math.tau - math.pi)
    locked = delta < 0.36
    glow(canvas, (tx, ty), 11 if locked else 8, (45, 220, 255), 230 if locked else 105)
    draw = ImageDraw.Draw(canvas)
    draw.ellipse((tx - 12, ty - 12, tx + 12, ty + 12), fill=(37, 137, 235, 255), outline=(177, 248, 255, 255), width=1)
    draw.arc((tx - 9, ty - 8, tx + 9, ty + 8), 190, 350, fill=(67, 238, 150, 255), width=5)
    if locked:
        pulse = 20 + int(10 * math.sin(phase * math.tau * 5) ** 2)
        draw.ellipse((tx - pulse, ty - pulse, tx + pulse, ty + pulse), outline=(67, 255, 211, 235), width=2)
        draw.line((tx + 25, ty, 555, ty), fill=(67, 255, 211, 180), width=1)
        draw.text((560, ty - 8), "POSSIBLE HOME", font=SMALL, fill=(67, 255, 211, 255))

    # Animated data rails and a living signal waveform occupy the central bridge.
    for lane, lane_y in enumerate((154, 190, 226)):
        draw.line((430, lane_y, 748, lane_y), fill=(43, 108, 147, 105), width=1)
        packet_x = 430 + int(((phase + lane * 0.21) % 1) * 318)
        draw.rectangle((packet_x - 7, lane_y - 2, packet_x + 7, lane_y + 2), fill=(78, 242, 220, 205))
    wave_points = []
    for x in range(430, 750, 4):
        envelope = 0.35 + 0.65 * math.sin((x - 430) / 320 * math.pi) ** 2
        y = 278 + math.sin(x * 0.105 + phase * math.tau * 3) * 16 * envelope
        wave_points.append((x, y))
    draw.line(wave_points, fill=(119, 101, 255, 220), width=2)
    draw.text((430, 304), "CANDIDATE SIGNAL / PHASE COHERENT", font=TINY, fill=(104, 144, 186, 230))

    # Targeting brackets and interference lines keep the portrait subliminal.
    bracket = (836, 58, 1164, 318)
    bx1, by1, bx2, by2 = bracket
    length = 24
    bracket_color = (59, 191, 214, 70)
    for segment in ((bx1, by1, bx1 + length, by1), (bx1, by1, bx1, by1 + length), (bx2, by1, bx2 - length, by1), (bx2, by1, bx2, by1 + length), (bx1, by2, bx1 + length, by2), (bx1, by2, bx1, by2 - length), (bx2, by2, bx2 - length, by2), (bx2, by2, bx2, by2 - length)):
        draw.line(segment, fill=bracket_color, width=1)
    for scan_y in range(64 + index % 5, 318, 9):
        draw.line((822, scan_y, 1172, scan_y), fill=(58, 201, 223, 18), width=1)

    # Single global scan line makes the whole scene feel like one hologram.
    scan_x = int(18 + phase * 1164)
    scan = Image.new("RGBA", canvas.size)
    scan_draw = ImageDraw.Draw(scan)
    scan_draw.rectangle((scan_x - 1, 52, scan_x + 1, 326), fill=(110, 255, 241, 155))
    canvas.alpha_composite(scan.filter(ImageFilter.GaussianBlur(4)))

    draw = ImageDraw.Draw(canvas)
    draw.text((430, 326), "NEURAL GHOST / IDENTITY MASKED", font=SMALL, fill=(100, 143, 183, 255))
    draw.text((1164, 326), f"SWEEP {index + 1:02d}/{FRAME_COUNT:02d}", anchor="ra", font=SMALL, fill=(100, 143, 183, 255))
    draw.rounded_rectangle((10, 10, W - 10, H - 10), radius=15, outline=(35, 77, 126, 230), width=1)
    return canvas.convert("RGB")


def main():
    frames = [frame(i) for i in range(FRAME_COUNT)]
    frames[0].save(OUTPUT, save_all=True, append_images=frames[1:], duration=85, loop=0, optimize=True, disposal=2)
    print(f"Wrote {OUTPUT} ({OUTPUT.stat().st_size / 1024 / 1024:.2f} MiB)")


if __name__ == "__main__":
    main()
