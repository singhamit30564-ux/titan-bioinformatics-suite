"""Rasterize static/icons/icon.svg into the PNG sizes the PWA manifest needs.

This is a one-off build script (not imported at runtime). It redraws the same
simple navy/gold double-helix mark with Pillow rather than depending on an SVG
rasterizer library, so no new runtime dependency is introduced. Re-run this
script by hand whenever ``icon.svg`` changes:

    python scripts/build_pwa_icons.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

NAVY = (10, 14, 23, 255)
GOLD = (212, 175, 55, 255)
CYAN = (102, 252, 241, 230)
MUTED = (139, 155, 180, 255)

ICON_DIR = Path(__file__).resolve().parent.parent / "static" / "icons"


def _rounded_square(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    radius = int(size * 0.1875)
    draw.rounded_rectangle([(0, 0), (size - 1, size - 1)], radius=radius, fill=NAVY)
    return img


def _draw_helix(draw: ImageDraw.ImageDraw, size: int) -> None:
    cx = size / 2
    top, bottom = size * 0.23, size * 0.86
    amplitude = size * 0.16
    width = max(2, int(size * 0.027))
    steps = 160
    strand_a = []
    strand_b = []
    for i in range(steps + 1):
        frac = i / steps
        y = top + (bottom - top) * frac
        offset = amplitude * __import__("math").sin(frac * 3.14159 * 2)
        strand_a.append((cx + offset, y))
        strand_b.append((cx - offset, y))
    draw.line(strand_a, fill=GOLD, width=width, joint="curve")
    draw.line(strand_b, fill=CYAN, width=width, joint="curve")
    # Base-pair rungs every ~1/6th of the strand.
    for i in range(0, steps + 1, steps // 6):
        draw.line([strand_a[i], strand_b[i]], fill=MUTED, width=max(1, width // 2))


def build_icon(size: int) -> Image.Image:
    img = _rounded_square(size)
    draw = ImageDraw.Draw(img)
    ring_bbox = [size * 0.08, size * 0.08, size * 0.92, size * 0.92]
    draw.ellipse(ring_bbox, outline=(*GOLD[:3], 90), width=max(1, int(size * 0.02)))
    _draw_helix(draw, size)
    return img


def main() -> None:
    ICON_DIR.mkdir(parents=True, exist_ok=True)
    for size in (192, 512):
        icon = build_icon(size)
        icon.save(ICON_DIR / f"icon-{size}.png")
        print(f"wrote {ICON_DIR / f'icon-{size}.png'}")

    # Maskable variant (512) with extra safe-area padding, per PWA guidance.
    maskable = Image.new("RGBA", (512, 512), NAVY)
    inner = build_icon(360)
    maskable.paste(inner, (76, 76), inner)
    maskable.save(ICON_DIR / "icon-512-maskable.png")
    print(f"wrote {ICON_DIR / 'icon-512-maskable.png'}")


if __name__ == "__main__":
    main()
