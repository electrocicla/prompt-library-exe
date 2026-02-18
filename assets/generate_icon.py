"""
generate_icon.py – create assets/icon.ico from Not-Meta SVG design.

Run once before building the exe:
    python assets/generate_icon.py

Requires: Pillow
"""

from __future__ import annotations

import math
import pathlib
import struct
import zlib

try:
    from PIL import Image, ImageDraw
except ImportError:
    raise SystemExit("Pillow is required: pip install Pillow")


HERE = pathlib.Path(__file__).parent
OUTPUT_ICO = HERE / "icon.ico"


def _hex_to_rgb(hex_color: str) -> tuple:
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def draw_not_meta_logo(size: int) -> "Image.Image":
    """
    Render the Not-Meta logo at the given pixel size.

    Design (mirrors public/favicon.svg):
      - Dark background (#0a0a0f)
      - Green circle (#00ff88) with thin black stroke
      - Black diamond/rhombus (top-half) in the centre
      - Small white dot in the centre of the diamond
    """
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx = cy = size / 2
    r = size * 0.46  # main circle radius

    # Background dark circle (slightly inset to give some padding)
    draw.ellipse(
        [cx - r - 1, cy - r - 1, cx + r + 1, cy + r + 1],
        fill=(10, 10, 15, 255),
    )

    # Green circle
    draw.ellipse(
        [cx - r, cy - r, cx + r, cy + r],
        fill=(0, 255, 136, 255),
        outline=(0, 0, 0, 255),
        width=max(1, size // 32),
    )

    # Diamond: M8 12 L16 8 L24 12 L16 16 Z  (original 32×32 SVG coords)
    # Scale to current size
    scale = size / 32.0
    diamond = [
        (8 * scale, 12 * scale),
        (16 * scale, 8 * scale),
        (24 * scale, 12 * scale),
        (16 * scale, 16 * scale),
    ]
    draw.polygon(diamond, fill=(0, 0, 0, 255))

    # White dot at (16, 12) in SVG coords, radius 2
    dot_cx = 16 * scale
    dot_cy = 12 * scale
    dot_r = max(1, 2 * scale)
    draw.ellipse(
        [dot_cx - dot_r, dot_cy - dot_r, dot_cx + dot_r, dot_cy + dot_r],
        fill=(255, 255, 255, 255),
    )

    return img


def build_ico(output: pathlib.Path) -> None:
    sizes = [16, 24, 32, 48, 64, 128, 256]
    frames = [draw_not_meta_logo(s) for s in sizes]

    # Save as ICO using Pillow's built-in ICO support
    frames[0].save(
        str(output),
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=frames[1:],
    )
    print(f"Icon written → {output}")


if __name__ == "__main__":
    build_ico(OUTPUT_ICO)
