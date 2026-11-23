# tests/test_zoom.py — Lane: Sphinx. S15: Zippy looks at an enlarged copy (dev only).
#   python3 -m unittest tests.test_zoom
# No model needed: Ollama is a stand-in. Skipped if Pillow isn't installed (dev tool).
# 1. The factor: 1.5 for small screenshots, less near Gemma's cap, 1.0 at the cap.
# 2. An enlarged look sends ONE image, bigger, with the same instruction, and records "zoom".
# 3. A file at the cap is sent as its own bytes, through the shipping Zippy.
# 4. A file that can't be opened is locked (fail closed).

import base64
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from harness import context, gate, router

try:
    from PIL import Image
    from dev import zoom_run
except ImportError:
    Image = None

CLEAR = json.dumps({"kind": "none", "confidence": 0.9})


def _png(folder, name, size):
    path = Path(folder) / name
    Image.new("RGB", size, "white").save(path)
    return path


@unittest.skipIf(Image is None, "Pillow is not installed (dev tool)")
class TestFactor(unittest.TestCase):
    def test_small_screenshots_get_the_full_zoom(self):
        self.assertEqual(zoom_run.factor(1000, 600), 1.5)

    def test_near_the_cap_it_enlarges_less(self):
        scale = zoom_run.factor(1600, 1000)
        self.assertTrue(1.0 < scale < 1.5)
        tokens = round(1600 * scale / 48) * round(1000 * scale / 48)
        self.assertLessEqual(tokens, 1120)

    def test_at_the_cap_it_stays_the_same(self):
        self.assertEqual(zoom_run.factor(2560, 1600), 1.0)


@unittest.skipIf(Image is None, "Pillow is not installed (dev tool)")
class TestZoomedLook(unittest.TestCase):
    def test_one_bigger_image_same_instruction_zoom_recorded(self):
        sent = {}

        def fake_ask(model, messages, shape=None):
            sent["messages"] = messages
            router._last_usage = {"tokens_in": 5}
            return CLEAR

        with tempfile.TemporaryDirectory() as folder:
            path = _png(folder, "a.png", (400, 200))
            with mock.patch.object(router, "ask", fake_ask):
                verdict = zoom_run.zoomed_ask("m", "rules", path)
        user = sent["messages"][1]
        self.assertEqual(user["content"], context.ZIPPY_INSTRUCTION)
        self.assertEqual(len(user["images"]), 1)
        picture = Image.open(io.BytesIO(base64.b64decode(user["images"][0])))
        self.assertEqual(picture.size, (600, 300))
        self.assertEqual(verdict["kind"], "none")
        self.assertEqual(router.take_usage()["zoom"], 1.5)

    def test_at_the_cap_the_original_bytes_go_through_shipping_zippy(self):
        sent = {}

        def fake_ask(model, messages, shape=None):
            sent["image"] = messages[1]["images"][0]
            router._last_usage = {"tokens_in": 5}
            return CLEAR

        with tempfile.TemporaryDirectory() as folder:
            path = _png(folder, "big.png", (2560, 1600))
            with mock.patch.object(router, "ask", fake_ask):
                zoom_run.zoomed_ask("m", "rules", path)
            original = base64.b64encode(path.read_bytes()).decode("ascii")
        self.assertEqual(sent["image"], original)
        self.assertEqual(router.take_usage()["zoom"], 1.0)

    def test_a_broken_file_is_locked(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "broken.png"
            path.write_bytes(b"not an image")
            with mock.patch("builtins.print"):
                verdict = zoom_run.zoomed_ask("m", "rules", path)
        self.assertEqual(verdict["kind"], gate.GATE_ERROR)


if __name__ == "__main__":
    unittest.main()
