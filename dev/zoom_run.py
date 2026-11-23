# dev/zoom_run.py — S15 TEST ONLY. Zippy looks at an ENLARGED copy of each screenshot.
#
#   python3 -u dev/zoom_run.py gemma4:e2b all --zippy gemma4:e4b
#   (the same words as run.py. Only Zippy's look changes; Pip and everything after it don't)
#
# Why (S15, measured Nov 22): Ollama reads a Gemma 4 image at one token per 48x48 pixels,
# up to 1,120 tokens; Qwen reads one per 32x32. Enlarging 1.5x gives e4b Qwen's grain
# without a bigger model. Question: is it the reading, or the model?
# Decisions (Sphinx, S15 brief, option A; rule written before any run in build-log-4.md):
# - ONE enlarged image, ONE call, the same prompt and menu. Pip gets the original bytes.
# - Factor: 1.5x, or less when 1.5x would push the image past ~1,100 tokens (Gemma would
#   shrink it back). Files already at the cap are sent as their own bytes, unchanged.
# - Dev only (D16: Pillow allowed in dev/). Shipping code is unchanged: this file swaps in
#   an enlarged Zippy for this run only. Shipping it is a D1 question, and only if it wins.
# - The trace says so: every Zippy call in this run records "zoom" in its usage (lesson 13).
# A screenshot Pillow can't open is LOCKED (gate_error), as any broken look is (D18).
# Prints nothing about files beyond what run.py prints: safe on the Mac set.

import base64
import io
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from harness import context, gate, router, schema  # noqa: E402

try:
    from PIL import Image
except ImportError:   # Pillow is a dev tool; main() says how to get it
    Image = None

ZOOM = 1.5           # Qwen's grain: (48 / 32) = 1.5
PIXELS_PER_TOKEN = 48 * 48
TOKEN_ROOM = 1100    # a margin under Gemma's 1,120-token image cap
_plain_ask = gate.ask   # the shipping Zippy, used for files that stay unchanged


def factor(width, height):
    """How much to enlarge: 1.5, or less near the cap, or 1.0 (send as it is)."""
    room = math.sqrt(TOKEN_ROOM * PIXELS_PER_TOKEN / (width * height))
    scale = min(ZOOM, room)
    return 1.0 if scale < 1.02 else round(scale, 3)


def _record(scale):
    if isinstance(router._last_usage, dict):
        router._last_usage["zoom"] = scale


def enlarged(image_path, scale):
    """The screenshot enlarged by `scale` (Lanczos), as base64 PNG."""
    with Image.open(image_path) as picture:
        picture.load()
        if picture.mode not in ("RGB", "RGBA", "L"):
            picture = picture.convert("RGB")
        size = (round(picture.width * scale), round(picture.height * scale))
        bigger = picture.resize(size, Image.LANCZOS)
    buffer = io.BytesIO()
    bigger.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def zoomed_ask(model, instructions, image_path):
    """Takes gate.ask's place for this run. Same answer shape, same check, same lock rule."""
    try:
        with Image.open(image_path) as picture:
            scale = factor(*picture.size)
        picture_b64 = enlarged(image_path, scale) if scale > 1.0 else None
    except Exception:   # unreadable image: fail closed, like any broken look
        print("  (S15: could not enlarge this screenshot: locked)")
        return {"kind": gate.GATE_ERROR, "confidence": None}
    if picture_b64 is None:
        verdict = _plain_ask(model, instructions, image_path)   # its own bytes, unchanged
        _record(1.0)
        return verdict
    messages = [{"role": "system", "content": instructions},
                {"role": "user", "content": context.ZIPPY_INSTRUCTION, "images": [picture_b64]}]
    raw = router.ask(model, messages, schema.GATE_SHAPE)
    _record(scale)
    return gate.check_verdict(raw)


def main():
    if Image is None:
        sys.exit("S15 needs Pillow (dev only). In a terminal: python3 -m pip install pillow")
    import run   # here, not at the top, so the tests can import this file without run.py
    print("S15 TEST: Zippy looks at an enlarged copy (up to " + str(ZOOM) + "x). Pip unchanged.\n")
    gate.ask = zoomed_ask
    run.main()


if __name__ == "__main__":
    main()
