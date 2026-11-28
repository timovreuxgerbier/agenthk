# dev/attack_band.py — S23 TEST ONLY: the band dev/attack_real.py adds to a picture, in memory.
# A white band at the bottom, the same height for the twin (empty) and for each planted copy
# (one line of text), so the only difference Zippy can see is the line. Nothing is saved.
import base64
import io
import textwrap

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:   # Pillow is a dev tool (D16)
    Image = None

BAND_LINES = 4        # room for the longest planted line, wrapped, on a narrow picture


def font(size):
    for name in ("arial.ttf", "segoeui.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def banded(picture, text):
    """The picture with a white band at the bottom; the band holds text, or nothing (the twin)."""
    width, height = picture.size
    size = max(16, round(width / 55))
    per_line = max(24, int(width * 0.92 / (0.6 * size)))
    band = round(size * 1.45 * BAND_LINES + size)
    canvas = Image.new("RGB", (width, height + band), "white")
    canvas.paste(picture.convert("RGB"), (0, 0))
    if text:
        lines = textwrap.wrap(text, per_line)[:BAND_LINES]
        draw, face = ImageDraw.Draw(canvas), font(size)
        for n, line in enumerate(lines):
            draw.text((round(width * 0.04), height + round(size * 0.5 + n * size * 1.45)), line,
                      fill=(40, 40, 40), font=face)
    buffer = io.BytesIO()
    canvas.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")
