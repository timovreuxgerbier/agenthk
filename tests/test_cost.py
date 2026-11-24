# tests/test_cost.py — Lane: Sphinx. S11: token and time counts, and the cost report.
#   python3 -m unittest tests.test_cost
# No model needed: Ollama's replies and both buddies are stand-ins.
# 1. Ollama's nanoseconds become seconds; a missing count stays None (never guessed).
# 2. A failed call leaves no numbers behind, so one call's cost can't land on another.
# 3. The trace line ON DISK keeps each buddy's counts (S10 lesson: the trace only keeps
#    the fields in schema.TRACE_FIELDS, so checking before the write would prove nothing).
# 4. The report: old runs say "not recorded"; the cloud sum is right for a known number.

import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

from harness import caps, pipeline, router, schema
from eval import cost

PIP_ANSWER = json.dumps({"reason": "A pasta recipe.", "new_name": "pasta-recipe",
                         "why_saved_guess": "To cook it later.", "action": "keep_text",
                         "confidence": 0.9})


class TestRouterCounts(unittest.TestCase):
    def test_nanoseconds_become_seconds_and_missing_stays_none(self):
        usage = router.usage_from({"prompt_eval_count": 812, "eval_count": 40,
                                   "load_duration": 2500000000, "total_duration": 3000000000})
        self.assertEqual((usage["tokens_in"], usage["tokens_out"]), (812, 40))
        self.assertEqual((usage["load_seconds"], usage["ollama_seconds"]), (2.5, 3.0))
        self.assertIsNone(usage["write_seconds"])

    def test_a_failed_call_leaves_no_numbers(self):
        router._last_usage = {"tokens_in": 999}
        with mock.patch.object(router.urllib.request, "urlopen",
                               side_effect=urllib.error.URLError("down")):
            with self.assertRaises(urllib.error.URLError):
                router.ask("any-model", [])
        self.assertIsNone(router.take_usage())


class TestTraceKeepsCounts(unittest.TestCase):
    def test_each_buddy_has_its_own_counts_on_disk(self):
        def zippy(model, instructions, image):
            router._last_usage = {"tokens_in": 100, "tokens_out": 10}
            return {"kind": "none", "confidence": 0.9}

        def pip(model, messages, shape=None):
            router._last_usage = {"tokens_in": 200, "tokens_out": 50}
            return PIP_ANSWER

        with tempfile.TemporaryDirectory() as folder:
            trace_file = Path(folder) / "trace.jsonl"
            with mock.patch.object(pipeline.gate, "ask", zippy), \
                    mock.patch.object(pipeline.router, "ask", pip), \
                    mock.patch.object(pipeline.context, "build_messages", lambda *a: []), \
                    mock.patch.object(schema, "TRACE", trace_file), \
                    mock.patch("builtins.print"):
                pipeline.handle("[1/1]", Path("IMG_0001.png"), "pip-model",
                                {"pip": "", "zippy": ""}, {}, caps.RunCaps(), "test-run")
            line = json.loads(trace_file.read_text(encoding="utf-8"))
        self.assertEqual(line["zippy_usage"]["tokens_in"], 100)
        self.assertEqual(line["pip_usage"]["tokens_in"], 200)


class TestReport(unittest.TestCase):
    def test_old_runs_say_tokens_were_not_recorded(self):
        old = [{"run_id": "old", "model": "gemma4:e2b", "seconds": 5.0, "zippy_seconds": 2.0,
                "gate": {"kind": "none", "confidence": 0.9}}]
        report = cost.build("old", old)
        self.assertIn("TOKENS: not recorded", report)
        self.assertIn("5.0 s average", report)

    def test_cloud_sum_for_a_known_number(self):
        expected = cost.CLOUD["in_per_million"] + cost.CLOUD["out_per_million"]
        self.assertAlmostEqual(cost.cloud_dollars(1000000, 1000000), expected)


if __name__ == "__main__":
    unittest.main()
