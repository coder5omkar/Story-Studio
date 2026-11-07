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


def render_thumbnail(
    base_path: Path,
    out_path: Path,
    text: str,
    channel_name: str,
    tagline: str = "",
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

    if tagline:
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

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "PNG", optimize=True)
    return img.width, img.height
