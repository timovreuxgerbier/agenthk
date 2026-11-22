# tests/test_two_models.py — Lane: Sphinx. S10: Zippy and Pip on different models.
#   python3 -m unittest tests.test_two_models
# No model needed: both buddies are stand-ins that only note which model they were given.
# 1. Without --zippy, both buddies use the same model (behaviour before S10 is unchanged).
# 2. With --zippy, Zippy's question goes to Zippy's model and Pip's to Pip's.
# 3. The trace line ON DISK keeps both models and Zippy's seconds. (The trace only keeps
#    the fields listed in schema.TRACE_FIELDS, so checking the line before it is written
#    would pass even if the field were silently dropped.)

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import run
from harness import caps, pipeline, schema

PIP_ANSWER = json.dumps({"reason": "A pasta recipe.", "new_name": "pasta-recipe",
                         "why_saved_guess": "To cook it later.", "action": "keep_text",
                         "confidence": 0.9})


class TestCommandLine(unittest.TestCase):
    def test_without_zippy_both_use_one_model(self):
        model, zippy_model, _, batch_mode = run.read_args(["gemma4:e2b", "all"])
        self.assertEqual((model, zippy_model, batch_mode), ("gemma4:e2b", "gemma4:e2b", True))

    def test_zippy_gets_its_own_model_wherever_it_is_written(self):
        for args in (["gemma4:e2b", "all", "--zippy", "gemma4:e4b"],
                     ["--zippy", "gemma4:e4b", "gemma4:e2b", "all"]):
            model, zippy_model, _, batch_mode = run.read_args(args)
            self.assertEqual((model, zippy_model, batch_mode),
                             ("gemma4:e2b", "gemma4:e4b", True), args)

    def test_zippy_without_a_name_is_refused(self):
        with self.assertRaises(ValueError):
            run.read_args(["gemma4:e2b", "all", "--zippy"])


class TestPipeline(unittest.TestCase):
    def one_screenshot(self, zippy_model=None):
        """Send one made-up screenshot through the real pipeline with stand-in buddies."""
        asked = {}

        def zippy(model, instructions, image):
            asked["zippy"] = model
            return {"kind": "none", "confidence": 0.9}

        def pip(model, messages, shape=None):
            asked["pip"] = model
            return PIP_ANSWER

        with tempfile.TemporaryDirectory() as folder:
            trace_file = Path(folder) / "trace.jsonl"
            with mock.patch.object(pipeline.gate, "ask", zippy), \
                    mock.patch.object(pipeline.router, "ask", pip), \
                    mock.patch.object(pipeline.context, "build_messages", lambda *a: []), \
                    mock.patch.object(schema, "TRACE", trace_file), \
                    mock.patch("builtins.print"):
                pipeline.handle("[1/1]", Path("IMG_0001.png"), "pip-model",
                                {"pip": "", "zippy": ""}, {}, caps.RunCaps(), "test-run",
                                zippy_model)
            line = json.loads(trace_file.read_text(encoding="utf-8"))
        return asked, line

    def test_each_buddy_gets_its_model_and_the_trace_keeps_both(self):
        asked, line = self.one_screenshot("zippy-model")
        self.assertEqual(asked, {"zippy": "zippy-model", "pip": "pip-model"})
        self.assertEqual((line["model"], line["zippy_model"]), ("pip-model", "zippy-model"))
        self.assertIsInstance(line["zippy_seconds"], (int, float))

    def test_default_is_one_model_for_both(self):
        asked, line = self.one_screenshot()
        self.assertEqual(asked, {"zippy": "pip-model", "pip": "pip-model"})
        self.assertEqual(line["zippy_model"], "pip-model")


if __name__ == "__main__":
    unittest.main()
