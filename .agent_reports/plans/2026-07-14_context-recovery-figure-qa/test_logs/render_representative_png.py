#!/usr/bin/env python3
"""Pillow fallback renderer used only because local matplotlib is unavailable."""

from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


METRIC_BAND_HZ = (20, 1000)
FIGURE_BAND_HZ = (0, 24000)
SAMPLE_RATE_HZ = 48000
VMIN_DB = -80
VMAX_DB = 0
COLORMAP = "magma-compatible"
WIDTH, HEIGHT = 1850, 700


def font(size: int):
    path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    return ImageFont.truetype(str(path), size) if path.exists() else ImageFont.load_default()


def palette(value: float) -> tuple[int, int, int]:
    stops = (
        (0.00, (4, 0, 15)),
        (0.25, (81, 18, 124)),
        (0.50, (183, 55, 121)),
        (0.75, (251, 140, 60)),
        (1.00, (252, 253, 191)),
    )
    value = min(1.0, max(0.0, value))
    for (left, a), (right, b) in zip(stops, stops[1:]):
        if value <= right:
            ratio = (value - left) / (right - left)
            return tuple(round(x + ratio * (y - x)) for x, y in zip(a, b))
    return stops[-1][1]


def panel_image(width: int, height: int, seed: int) -> Image.Image:
    rng = random.Random(seed)
    image = Image.new("RGB", (width, height))
    pixels = image.load()
    for y in range(height):
        frequency = (height - 1 - y) / (height - 1) * FIGURE_BAND_HZ[1]
        envelope = -65 + 34 * math.exp(-((frequency - 7000) / 5600) ** 2)
        for x in range(width):
            time = x / max(1, width - 1)
            harmonics = 20 * math.sin(2 * math.pi * (3.3 * time + frequency / 4100))
            ridges = 13 * math.sin(2 * math.pi * (11 * time - frequency / 7800))
            db = max(VMIN_DB, min(VMAX_DB, envelope + harmonics + ridges + rng.uniform(-4, 4)))
            pixels[x, y] = palette((db - VMIN_DB) / (VMAX_DB - VMIN_DB))
    return image


def rotated_label(canvas: Image.Image, center: tuple[int, int], text: str, text_font) -> None:
    text_width, text_height = text_font.getsize(text)
    layer = Image.new("RGBA", (text_width + 20, text_height + 20), (255, 255, 255, 0))
    layer_draw = ImageDraw.Draw(layer)
    layer_draw.text((10, 10), text, fill="black", font=text_font)
    layer = layer.rotate(90, expand=True)
    left = center[0] - layer.width // 2
    top = center[1] - layer.height // 2
    canvas.paste(layer, (left, top), layer)


def main() -> None:
    canvas = Image.new("RGB", (WIDTH, HEIGHT), "white")
    draw = ImageDraw.Draw(canvas)
    title_font, label_font, tick_font = font(29), font(24), font(19)
    draw.text((WIDTH // 2, 26), "48 kHz full-band (0–24 kHz) — shared −80..0 dB scale", fill="black", font=title_font, anchor="ma")

    top, bottom = 120, 590
    panel_width = 620
    panels = ((180, "Reference", 7), (850, "Estimate", 11))
    for left, title, seed in panels:
        heatmap = panel_image(panel_width, bottom - top, seed)
        canvas.paste(heatmap, (left, top))
        draw.rectangle((left, top, left + panel_width, bottom), outline="black", width=2)
        draw.text((left + panel_width // 2, 84), title, fill="black", font=label_font, anchor="ma")
        draw.text((left + panel_width // 2, 635), "Time (s)", fill="black", font=label_font, anchor="ma")
        for value, text in ((0, "0"), (0.5, "0.5"), (1, "1.0")):
            x = left + round(value * panel_width)
            draw.line((x, bottom, x, bottom + 8), fill="black", width=2)
            draw.text((x, bottom + 12), text, fill="black", font=tick_font, anchor="ma")

    left = panels[0][0]
    for khz in (0, 6, 12, 18, 24):
        y = bottom - round(khz / 24 * (bottom - top))
        draw.line((left - 8, y, left, y), fill="black", width=2)
        draw.text((left - 16, y), str(khz), fill="black", font=tick_font, anchor="rm")
    rotated_label(canvas, (48, (top + bottom) // 2), "Frequency (kHz)", label_font)

    color_left, color_right = 1530, 1580
    for y in range(top, bottom):
        value = (bottom - 1 - y) / (bottom - top - 1)
        draw.line((color_left, y, color_right, y), fill=palette(value))
    draw.rectangle((color_left, top, color_right, bottom), outline="black", width=2)
    for db in (-80, -60, -40, -20, 0):
        y = bottom - round((db - VMIN_DB) / (VMAX_DB - VMIN_DB) * (bottom - top))
        draw.line((color_right, y, color_right + 8, y), fill="black", width=2)
        draw.text((color_right + 16, y), str(db), fill="black", font=tick_font, anchor="lm")
    rotated_label(canvas, (1750, (top + bottom) // 2), "Magnitude (dB)", label_font)

    output = Path(__file__).with_name("representative_spectrogram.png")
    canvas.save(output, format="PNG", optimize=True)


if __name__ == "__main__":
    main()
