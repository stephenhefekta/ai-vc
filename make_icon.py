#!/usr/bin/env python3
"""Generate AI VC.icns — 5 VC dots on a dark rounded background."""

import subprocess
import shutil
from pathlib import Path
from PIL import Image, ImageDraw


# One dot per VC: Vinod, Doug, Ben, Peter, Pat
COLORS = ["#D97706", "#DC2626", "#475569", "#4F46E5", "#059669"]
BG = "#0f172a"  # dark slate


def make_frame(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Rounded background
    radius = size // 5
    draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=BG)

    # 3-2 arrangement of circles
    pad = size * 0.12
    dot_d = (size - 2 * pad) / 3.2
    cr = dot_d * 0.40

    # Row 1: 3 dots
    row1_y = size * 0.28
    for i in range(3):
        cx = pad + dot_d * 0.5 + i * ((size - 2 * pad) / 2.5)
        draw.ellipse([cx - cr, row1_y - cr, cx + cr, row1_y + cr], fill=COLORS[i])

    # Row 2: 2 dots centred
    row2_y = size * 0.70
    for i in range(2):
        cx = size * 0.28 + i * size * 0.44
        draw.ellipse([cx - cr, row2_y - cr, cx + cr, row2_y + cr], fill=COLORS[3 + i])

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
