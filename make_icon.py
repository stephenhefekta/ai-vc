#!/usr/bin/env python3
"""Generate AI VC.icns — bold $ sign on dark rounded background."""

import subprocess
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


BG    = "#0f172a"   # dark slate
GREEN = "#10b981"   # emerald-500

FONT_PATH = "/System/Library/Fonts/Supplemental/Arial Black.ttf"


def make_frame(size: int) -> Image.Image:
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Rounded background
    radius = size // 5
    draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=BG)

    # Draw $ using Arial Black, sized to fill ~70% of the icon
    font_size = int(size * 0.72)
    font = ImageFont.truetype(FONT_PATH, font_size)

    cx, cy = size / 2, size / 2

    # Measure text
    bbox = font.getbbox("$")
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = cx - tw / 2 - bbox[0]
    y = cy - th / 2 - bbox[1]

    # Subtle shadow for depth
    shadow_offset = max(1, size // 64)
    draw.text((x + shadow_offset, y + shadow_offset), "$", font=font, fill="#065f46")

    # Main $ in emerald
    draw.text((x, y), "$", font=font, fill=GREEN)

    return img


def main():
    iconset = Path("AI VC.iconset")
    iconset.mkdir(exist_ok=True)

    for base, scale in [
        (16, 1), (16, 2),
        (32, 1), (32, 2),
        (128, 1), (128, 2),
        (256, 1), (256, 2),
        (512, 1), (512, 2),
    ]:
        img = make_frame(base * scale)
        suffix = f"@{scale}x" if scale > 1 else ""
        img.save(iconset / f"icon_{base}x{base}{suffix}.png")

    subprocess.run(["iconutil", "-c", "icns", str(iconset)], check=True)
    shutil.rmtree(iconset)
    print("✓ Created AI VC.icns")


if __name__ == "__main__":
    main()
