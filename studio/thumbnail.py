"""Render a YouTube thumbnail overlay with Devanagari text."""

from __future__ import annotations

import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

WIDTH = 1280
HEIGHT = 720
AMBER = (232, 180, 91)
CREAM = (255, 246, 229)
DARK = (8, 12, 20)

DEVANAGARI_FONTS = [
    os.environ.get("THUMBNAIL_FONT", ""),
    r"C:\Windows\Fonts\Nirmala.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
    "/System/Library/Fonts/Supplemental/Devanagari Sangam MN.ttc",
]
LATIN_FONTS = [
    os.environ.get("THUMBNAIL_LATIN_FONT", ""),
    r"C:\Windows\Fonts\segoeuib.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
]


def _pick_font(candidates: list[str]) -> str:
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    raise RuntimeError(
        "No Devanagari font found for the thumbnail. Install Nirmala UI, "
        "Noto Sans Devanagari, or set THUMBNAIL_FONT to a TTF/TTC file."
    )


def _font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size=size)


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words = text.split()
    if not words:
        return ["एक कहानी"]
    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if draw.textlength(trial, font=font) <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _green_anchor(img: Image.Image) -> tuple[int, int] | None:
    """Find the protagonist's green polo shirt and return a point near the face above it."""
    try:
        import numpy as np
    except Exception:
        return None
    arr = np.asarray(img.convert("RGB"), dtype=np.int16)
    height, width, _ = arr.shape
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    mask = (g > 55) & (g > r + 12) & (g > b + 4) & (r < 130)
    if not mask.any():
        return None
    grid = 16
    cell_area = (height * width) / (grid * grid)
    best = None
    for gy in range(grid // 4, grid):
        y0, y1 = gy * height // grid, (gy + 1) * height // grid
        for gx in range(grid):
            x0, x1 = gx * width // grid, (gx + 1) * width // grid
            count = int(mask[y0:y1, x0:x1].sum())
            if count < cell_area * 0.2:
                continue
            if best is None or count > best[0]:
                best = (count, x0, x1)
    if best is None:
        return None
    _, x0, x1 = best
    cx = (x0 + x1) // 2
    window = mask[:, max(0, cx - 170) : min(width, cx + 170)]
    ys, _ = np.nonzero(window)
    if not len(ys):
        return None
    top = int(np.percentile(ys, 8))
    return (cx, max(0, top - 55))


def _skin_anchor(img: Image.Image) -> tuple[int, int] | None:
    """Find the densest skin-tone region (the face) for the POV 'YOU' arrow."""
    try:
        import numpy as np
    except Exception:
        return None
    arr = np.asarray(img.convert("RGB"), dtype=np.int16)
    height, width, _ = arr.shape
    top = arr[: int(height * 0.72)]
    r, g, b = top[:, :, 0], top[:, :, 1], top[:, :, 2]
    mask = (
        (r > 105)
        & (g > 50)
        & (b > 25)
        & (r - g > 15)
        & (r - b > 25)
        & (g - b > -20)
    )
    if not mask.any():
        return None
    grid_h, grid_w = 16, 16
    cell_area = (height * width) / (grid_h * grid_w)
    best = None
    for gy in range(grid_h):
        y0, y1 = gy * top.shape[0] // grid_h, (gy + 1) * top.shape[0] // grid_h
        for gx in range(grid_w):
            x0, x1 = gx * width // grid_w, (gx + 1) * width // grid_w
            count = int(mask[y0:y1, x0:x1].sum())
            if count < cell_area * 0.12:
                continue
            if best is None or count > best[0]:
                best = (count, x0, x1, y0, y1)
    if best is None:
        return None
    _, x0, x1, y0, y1 = best
    ys, xs = np.nonzero(mask[y0:y1, x0:x1])
    return (x0 + int(xs.mean()), y0 + int(ys.mean()))


def render_thumbnail(
    base_path: Path,
    out_path: Path,
    text: str,
    channel_name: str,
    tagline: str = "",
    pov: bool = False,
) -> tuple[int, int]:
    """Crop the base render to 16:9 and add the title/thumbnail text."""
    if not base_path.exists():
        raise RuntimeError("Thumbnail base image is missing")

    with Image.open(base_path) as source:
        source = source.convert("RGB")
        scale = max(WIDTH / source.width, HEIGHT / source.height)
        scaled = source.resize(
            (round(source.width * scale), round(source.height * scale)),
            Image.LANCZOS,
        )
        left = max(0, (scaled.width - WIDTH) // 2)
        top = max(0, (scaled.height - HEIGHT) // 2)
        img = scaled.crop((left, top, left + WIDTH, top + HEIGHT))

    # Dark gradient at the bottom so the title always stays legible.
    alpha = Image.new("L", (1, HEIGHT))
    for y in range(HEIGHT):
        start = int(HEIGHT * 0.28)
        a = 0 if y < start else int(225 * (y - start) / (HEIGHT - start))
        alpha.putpixel((0, y), min(225, a))
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (5, 8, 15, 255))
    overlay.putalpha(alpha.resize((WIDTH, HEIGHT)))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    draw = ImageDraw.Draw(img)
    hindi_path = _pick_font(DEVANAGARI_FONTS)
    latin_path = _pick_font(LATIN_FONTS)

    # Small channel label.
    label = (channel_name or "STORY STUDIO").upper()
    label_font = _font(latin_path, 23)
    draw.rectangle((52, 46, 110, 50), fill=AMBER)
    draw.text((52, 58), label, font=label_font, fill=AMBER)

    # Main thumbnail text. Try large sizes and fall back until it fits in 3 lines.
    title = " ".join((text or "एक कहानी").split())
    max_width = 1010
    chosen_size = 54
    chosen_font = _font(hindi_path, chosen_size)
    chosen_lines = _wrap(draw, title, chosen_font, max_width)
    for size in (104, 96, 88, 80, 72, 64, 56, 48):
        font = _font(hindi_path, size)
        lines = _wrap(draw, title, font, max_width)
        if len(lines) <= 3:
            chosen_size, chosen_font, chosen_lines = size, font, lines
            break

    line_height = int(chosen_size * 1.18)
    block_height = line_height * len(chosen_lines)
    y = HEIGHT - 64 - block_height
    draw.rectangle((52, y - 22, 132, y - 16), fill=AMBER)
    stroke = max(2, chosen_size // 30)
    draw.multiline_text(
        (52, y),
        "\n".join(chosen_lines),
        font=chosen_font,
        fill=CREAM,
        stroke_width=stroke,
        stroke_fill=DARK,
        spacing=8,
    )

    if tagline and not pov:
        tag_font = _font(hindi_path, 21)
        tag_width = draw.textlength(tagline, font=tag_font)
        draw.text(
            (WIDTH - 52 - tag_width, 52),
            tagline,
            font=tag_font,
            fill=(210, 190, 150),
            stroke_width=1,
            stroke_fill=DARK,
        )

    if pov:
        red = (219, 45, 45)
        label_font = _font(latin_path, 29)
        label = "YOU"
        label_w = int(draw.textlength(label, font=label_font))
        box_w = label_w + 28
        box_h = 44
        anchor = _green_anchor(img) or _skin_anchor(img)
        if anchor:
            ax, ay = anchor
            box_x = ax + 78
            if box_x + box_w > WIDTH - 28:
                box_x = ax - 78 - box_w
            box_x = max(28, min(WIDTH - 28 - box_w, box_x))
            box_y = max(28, min(HEIGHT - box_h - 28, ay - 150))
            end = (ax, max(20, ay - 26))
            start = (
                box_x + (box_w if box_x + box_w // 2 < ax else 0),
                box_y + box_h // 2,
            )
        else:
            box_x = WIDTH - 56 - box_w
            box_y = 106
            start = (box_x + box_w // 2, box_y + box_h)
            end = (start[0] - 52, start[1] + 58)
        draw.rounded_rectangle(
            (box_x, box_y, box_x + box_w, box_y + box_h),
            radius=8,
            fill=red,
            outline=(120, 18, 18),
            width=2,
        )
        draw.text(
            (box_x + 14, box_y + 4),
            label,
            font=label_font,
            fill=(255, 255, 255),
        )
        dx, dy = end[0] - start[0], end[1] - start[1]
        length = max(1.0, (dx * dx + dy * dy) ** 0.5)
        ux, uy = dx / length, dy / length
        base = (end[0] - ux * 18, end[1] - uy * 18)
        draw.line([start, base], fill=red, width=7)
        px, py = -uy, ux
        draw.polygon(
            [
                (end[0], end[1]),
                (base[0] + px * 9, base[1] + py * 9),
                (base[0] - px * 9, base[1] - py * 9),
            ],
            fill=red,
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "PNG", optimize=True)
    return img.width, img.height
