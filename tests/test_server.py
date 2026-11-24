# tests/test_server.py — Lane: Sphinx. Lesson 13: server settings in each call's usage.
#   python3 -m unittest tests.test_server
# No model needed: Ollama's answers are stand-ins.
# 1. The settings come from the model that answered, not another loaded model.
# 2. If Ollama can't say, the run goes on and the settings stay None (never guessed).
# 3. ask() puts the settings into the usage the trace keeps.
# 4. The report says CPU when nothing is on the GPU; old runs say "not recorded".
# 5. compare_runs' check flags different or unrecorded settings, and passes equal ones.

import json
import unittest
import urllib.error
from unittest import mock

from harness import router, schema
from eval import server

PS = {"models": [
    {"name": "qwen-zippy:latest", "model": "qwen-zippy:latest", "size": 8000, "size_vram": 0,
     "context_length": 4096},
    {"name": "gemma4:e2b", "model": "gemma4:e2b", "size": 4000, "size_vram": 4000,
     "context_length": 16384},
]}
CHAT = {"message": {"content": "{}"}, "prompt_eval_count": 10, "eval_count": 2}


class Reply:
    def __init__(self, data):
        self.data = json.dumps(data).encode("utf-8")

    def read(self):
        return self.data

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def fake_ollama(ps=PS, version="0.30.1"):
    def urlopen(request, timeout=None):
        url = request if isinstance(request, str) else request.full_url
        if url == schema.OLLAMA_PS_URL:
            return Reply(ps)
        if url == schema.OLLAMA_VERSION_URL:
            return Reply({"version": version})
        return Reply(CHAT)
    return urlopen


def run_with(zippy, pip):
    """Two trace lines' worth of entries with the given usage settings."""
    return [{"zippy_usage": zippy, "pip_usage": pip}, {"zippy_usage": zippy, "pip_usage": pip}]


class TestServerFrom(unittest.TestCase):
    def setUp(self):
        router._ollama_version = None

    def test_settings_of_the_model_that_answered(self):
        with mock.patch.object(router.urllib.request, "urlopen", fake_ollama()):
            found = router.server_from("gemma4:e2b")
            other = router.server_from("qwen-zippy")      # ":latest" is Ollama's own default tag
        self.assertEqual(found, {"context": 16384, "gpu_share": 1.0, "ollama_version": "0.30.1"})
        self.assertEqual((other["context"], other["gpu_share"]), (4096, 0.0))

    def test_ollama_cannot_say_so_nothing_is_guessed(self):
        with mock.patch.object(router.urllib.request, "urlopen",
                               side_effect=urllib.error.URLError("down")):
            found = router.server_from("gemma4:e2b")
        self.assertEqual(found, {"context": None, "gpu_share": None, "ollama_version": None})

    def test_a_model_not_loaded_has_no_settings(self):
        with mock.patch.object(router.urllib.request, "urlopen", fake_ollama()):
            found = router.server_from("gemma4:e4b")
        self.assertEqual((found["context"], found["gpu_share"]), (None, None))

    def test_ask_puts_the_settings_in_the_usage(self):
        with mock.patch.object(router.urllib.request, "urlopen", fake_ollama()):
            router.ask("gemma4:e2b", [])
        usage = router.take_usage()
        self.assertEqual((usage["tokens_in"], usage["context"], usage["gpu_share"]), (10, 16384, 1.0))


class TestReportAndCompare(unittest.TestCase):
    GPU = {"context": 16384, "gpu_share": 1.0, "ollama_version": "0.30.1"}
    CPU = {"context": 16384, "gpu_share": 0.0, "ollama_version": "0.30.1"}
    SMALL = {"context": 4096, "gpu_share": 1.0, "ollama_version": "0.30.1"}

    def test_report_says_cpu_and_old_runs_say_not_recorded(self):
        report = "\n".join(server.lines(run_with(self.CPU, self.GPU)))
        self.assertIn("CPU (none of the model on the GPU)", report)
        self.assertIn("GPU (all of the model)", report)
        old = "\n".join(server.lines(run_with({"tokens_in": 5}, None)))
        self.assertIn("SERVER: not recorded", old)

    def test_same_settings_pass(self):
        self.assertEqual(server.differences(run_with(self.GPU, self.GPU), run_with(self.GPU, self.GPU)), [])

    def test_a_different_context_window_is_flagged(self):
        problems = server.differences(run_with(self.SMALL, self.GPU), run_with(self.GPU, self.GPU))
        self.assertEqual(len(problems), 1)
        self.assertIn("Zippy context: 4096 -> 16384", problems[0])

    def test_an_unrecorded_baseline_is_flagged(self):
        old = run_with({"tokens_in": 5}, {"tokens_in": 5})
        problems = server.differences(old, run_with(self.GPU, self.GPU))
        self.assertTrue(problems)
        self.assertTrue(all("not recorded in the old run" in p for p in problems))


if __name__ == "__main__":
    unittest.main()
