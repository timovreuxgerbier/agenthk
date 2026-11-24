# tests/test_batch.py — Lane: Sphinx. S14: batching (Zippy over a chunk, then Pip).
#   python3 -m unittest tests.test_batch
# No model needed: both buddies are stand-ins that write down who they were asked about.
# 1. Chunks keep the files' order and are at most CHUNK_SIZE long.
# 2. Batched: Zippy looks at the whole chunk before Pip starts, chunk by chunk.
# 3. Pip is NEVER asked about a file Zippy locked (the wall, D20).
# 4. The trace lines ON DISK are the same as the old one-by-one order writes: same
#    files, same order, same fields, same answers (only the clock fields may differ).
# 5. dev/compare_runs.py: identical runs pass; one changed kind is caught.

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import run
from dev import compare_runs
from harness import batch, caps, pipeline, schema

FILES = [Path("IMG_0001.png"), Path("IMG_0002_secret.png"), Path("IMG_0003.png")]
CLOCK_FIELDS = {"time", "seconds", "zippy_seconds"}


def pip_answer(name):
    return json.dumps({"reason": "A recipe card.", "new_name": "recipe-" + name[4:8],
                       "why_saved_guess": "To cook it later.", "action": "keep_text",
                       "confidence": 0.9})


def run_with_stand_ins(chunked, chunk_size=batch.CHUNK_SIZE):
    """Run FILES through the real loop with stand-in buddies. Returns (calls, trace lines)."""
    calls = []

    def zippy(model, instructions, image):
        calls.append(("zippy", image.name))
        kind = "bank_or_payment" if "secret" in image.name else "none"
        return {"kind": kind, "confidence": 0.9}

    def pip(model, messages, shape=None):
        calls.append(("pip", messages[0]))
        return pip_answer(messages[0])

    step = batch.run if chunked else run._one_by_one
    with tempfile.TemporaryDirectory() as folder:
        trace_file = Path(folder) / "trace.jsonl"
        with mock.patch.object(pipeline.gate, "ask", zippy), \
                mock.patch.object(pipeline.router, "ask", pip), \
                mock.patch.object(pipeline.context, "build_messages", lambda spec, image: [image.name]), \
                mock.patch.object(schema, "TRACE", trace_file), \
                mock.patch.object(batch, "CHUNK_SIZE", chunk_size), \
                mock.patch("builtins.print"):
            limits = caps.RunCaps(max_files=10, max_calls=100, max_seconds=60)
            step(FILES, "pip-model", "zippy-model", {"pip": "", "zippy": ""}, {}, limits, "test-run")
        lines = [json.loads(line) for line in trace_file.read_text(encoding="utf-8").splitlines()]
    return calls, lines


class TestChunks(unittest.TestCase):
    def test_chunks_keep_order_and_size(self):
        parts = batch.chunks(range(91))
        self.assertEqual([len(p) for p in parts], [50, 41])
        self.assertEqual([n for p in parts for n in p], list(range(91)))

    def test_default_chunk_is_fifty(self):
        self.assertEqual(batch.CHUNK_SIZE, 50)


class TestBatchedOrder(unittest.TestCase):
    def test_zippy_sees_the_whole_chunk_before_pip(self):
        calls, _ = run_with_stand_ins(chunked=True)
        self.assertEqual(calls, [("zippy", "IMG_0001.png"), ("zippy", "IMG_0002_secret.png"),
                                 ("zippy", "IMG_0003.png"),
                                 ("pip", "IMG_0001.png"), ("pip", "IMG_0003.png")])

    def test_chunks_of_two_alternate_by_chunk(self):
        calls, _ = run_with_stand_ins(chunked=True, chunk_size=2)
        self.assertEqual([who for who, _ in calls], ["zippy", "zippy", "pip", "zippy", "pip"])

    def test_pip_never_sees_a_locked_file(self):
        for chunked in (True, False):
            calls, _ = run_with_stand_ins(chunked)
            self.assertNotIn(("pip", "IMG_0002_secret.png"), calls, chunked)

    def test_trace_on_disk_is_the_same_as_one_by_one(self):
        _, old = run_with_stand_ins(chunked=False)
        _, new = run_with_stand_ins(chunked=True)
        self.assertEqual([line["file"] for line in new], [f.name for f in FILES])
        self.assertEqual([list(line) for line in new], [schema.TRACE_FIELDS] * 3)
        strip = lambda lines: [{k: v for k, v in l.items() if k not in CLOCK_FIELDS} for l in lines]
        self.assertEqual(strip(new), strip(old))
        locked = new[1]
        self.assertEqual(json.loads(locked["raw_output"])["action"], "sensitive")
        self.assertIsNone(locked["pip_usage"])


class TestCompareRuns(unittest.TestCase):
    def runs(self):
        _, lines = run_with_stand_ins(chunked=True)
        old = {l["file"]: compare_runs.answers(l) for l in lines}
        return old, {f: dict(a) for f, a in old.items()}

    def test_identical_runs_pass(self):
        old, new = self.runs()
        rule, info, only_old, only_new = compare_runs.compare(old, new)
        self.assertEqual((rule, only_old, only_new), ([], 0, 0))
        self.assertEqual(sum(info.values()), 0)

    def test_a_changed_kind_is_caught(self):
        old, new = self.runs()
        new["IMG_0001.png"]["kind"] = "contact_details"
        rule, _, _, _ = compare_runs.compare(old, new)
        self.assertEqual([(row, field) for row, field, _, _ in rule], [(1, "kind")])


if __name__ == "__main__":
    unittest.main()
