# tests/test_check_misses.py — Lane: Sphinx. S17: the look-at-the-misses check (dev only).
#   python3 -m unittest tests.test_check_misses
# No model and no real picture needed: the person and the picture viewer are stand-ins.
# 1. A miss is a screenshot labelled sensitive that Zippy cleared; rows count from 1 in run order.
# 2. Zippy's sentence for a kind is read from zippy.md, whole, on one line.
# 3. The reading rule (written before any answer) gives the causes it says it gives.
# 4. The set is found whether it is loaded or put away, and nothing is moved.
# 5. A whole check: the first four questions come before anything a model wrote, and what
#    is saved or left on screen holds no file name, no description and no proposed name.
# 6. Opening a picture never prints where it is, even when the viewer fails; a character the
#    window can't show never stops the check.

import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from harness import schema
from eval import golden
from dev import check_misses

CLEAR = {"kind": "none", "confidence": 0.9}
LOCK = {"kind": "credentials", "confidence": 0.9}


def _result(gate, action="keep_text", reason="", new_name="", model="pip-model"):
    locked = gate["kind"] != "none"
    return {"action": "sensitive" if locked else action, "pip_action": None if locked else action,
            "gate": gate, "reason": reason, "new_name": new_name, "model": model,
            "zippy_model": "zippy-model"}


def _label(kind, disposition="keep_image"):
    return {"expected": "sensitive" if kind != "none" else disposition, "kind": kind,
            "disposition": disposition, "note": "", "secret": ""}


class TestMisses(unittest.TestCase):
    def test_only_sensitive_labels_that_zippy_cleared_and_rows_follow_the_run(self):
        results = {"a.png": _result(CLEAR), "b.png": _result(LOCK), "c.png": _result(CLEAR),
                   "d.png": _result(CLEAR)}
        labels = {"a.png": _label("none"), "b.png": _label("credentials"),
                  "c.png": _label("credentials"), "d.png": _label("official_document")}
        self.assertEqual(check_misses.misses(results, labels),
                         [(3, "c.png", "credentials"), (4, "d.png", "official_document")])

    def test_a_run_from_before_zippy_has_no_misses(self):
        results = {"a.png": dict(_result(CLEAR), gate=None)}
        self.assertEqual(check_misses.misses(results, {"a.png": _label("credentials")}), [])


class TestKindSentence(unittest.TestCase):
    def test_a_sentence_over_several_lines_comes_back_whole(self):
        sentence = check_misses.kind_sentence("credentials")
        self.assertTrue(sentence.startswith("a login screen"))
        self.assertTrue(sentence.endswith("secrets."))
        self.assertNotIn("\n", sentence)
        self.assertNotIn("health_record", sentence)

    def test_a_one_line_sentence_and_a_kind_with_none(self):
        self.assertEqual(check_misses.kind_sentence("nudity_or_children"), "nudity, or a child.")
        self.assertEqual(check_misses.kind_sentence("unknown"), "")

    def test_it_stops_at_the_next_kind(self):
        text = "- a: first\n  more of a\n- b: second\n"
        self.assertEqual(check_misses.kind_sentence("a", text), "first more of a")
        self.assertEqual(check_misses.kind_sentence("b", text), "second")


class TestReadingRule(unittest.TestCase):
    def _read(self, small, plain, fits, label="y", seen="n", name="n"):
        return check_misses.reading({"small": small, "plain": plain, "fits": fits, "label": label,
                                     "seen": seen, "name": name})

    def test_only_the_person_knows(self):
        self.assertEqual(self._read("y", "n", "y"), ["not in the picture"])

    def test_visible_but_not_what_the_sentence_says(self):
        self.assertEqual(self._read("n", "y", "n"), ["definition"])

    def test_small_and_the_model_did_not_describe_it(self):
        self.assertEqual(self._read("y", "y", "y", seen="n"), ["reading"])
        self.assertEqual(self._read("y", "y", "y", seen="-"), ["reading"])

    def test_small_but_the_model_described_it_is_the_model(self):
        self.assertEqual(self._read("y", "y", "y", seen="y"), ["the model"])

    def test_plain_fits_and_still_cleared_is_the_model(self):
        self.assertEqual(self._read("n", "y", "y"), ["the model"])

    def test_label_and_name_are_noted_beside_the_cause(self):
        self.assertEqual(self._read("n", "y", "y", label="n", name="y"),
                         ["the model", "label in doubt", "the name leaks"])

    def test_two_causes_can_hold_at_once(self):
        self.assertEqual(self._read("y", "y", "n"), ["definition", "reading"])


class TestFindSet(unittest.TestCase):
    def test_finds_a_set_that_is_put_away_and_moves_nothing(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            home = root / "sets" / "mac"
            (home / "screenshots").mkdir(parents=True)
            golden.write({"x.png": {"file": "x.png", "expected_action": "keep_image",
                                    "sensitive_kind": "credentials"}}, home / "golden.csv")
            with mock.patch.object(schema, "GOLDEN", root / "golden.csv"), \
                    mock.patch.object(schema, "SCREENSHOTS", root / "screenshots"), \
                    mock.patch.object(check_misses, "SETS", root / "sets"):
                labels, pictures = check_misses.find_set(["x.png"])
                nothing, _ = check_misses.find_set(["x.png", "not-in-any-set.png"])
            self.assertEqual(labels["x.png"]["kind"], "credentials")
            self.assertEqual(pictures, home / "screenshots")
            self.assertIsNone(nothing)
            self.assertTrue((home / "golden.csv").exists())
            self.assertFalse((root / "golden.csv").exists())


class TestShowAndSay(unittest.TestCase):
    def test_windows_viewer_opens_the_picture_and_a_failure_is_quiet(self):
        opened = []
        with mock.patch.object(check_misses.os, "startfile", opened.append, create=True), \
                mock.patch("builtins.print") as printed:
            self.assertTrue(check_misses.show(Path("private name.png")))
        self.assertEqual(opened, [Path("private name.png")])
        printed.assert_not_called()

        def broken(path):
            raise OSError("cannot open " + str(path))

        with mock.patch.object(check_misses.os, "startfile", broken, create=True), \
                mock.patch("builtins.print") as printed:
            self.assertFalse(check_misses.show(Path("private name.png")))
        printed.assert_not_called()

    @unittest.skipIf(hasattr(os, "startfile"), "this branch is for Mac and Linux")
    def test_other_viewers_are_silenced_and_a_failure_is_reported(self):
        calls = []

        def fake_run(command, **options):
            calls.append(options)
            return mock.Mock(returncode=4)

        with mock.patch.object(check_misses.subprocess, "run", fake_run):
            self.assertFalse(check_misses.show(Path("private name.png")))
        self.assertEqual(calls[0]["stderr"], subprocess.DEVNULL)
        self.assertEqual(calls[0]["stdout"], subprocess.DEVNULL)

    def test_a_character_the_window_cannot_show_does_not_stop_the_check(self):
        shown = []

        def picky_print(words, *rest, **more):
            words.encode("ascii")           # raises UnicodeEncodeError on anything else
            shown.append(words)

        with mock.patch("builtins.print", picky_print):
            check_misses.say("caf\u00e9 \u2014 menu")
        self.assertEqual(shown, ["caf? ? menu"])


class TestWholeCheck(unittest.TestCase):
    FILE = "Screen Shot 2099-01-01 at 1.00.00 PM.png"
    REASON = "A settings page that shows the secret recovery phrase."
    NAME = "secret-recovery-phrase-settings"

    def _run(self, typed):
        events, shown = [], []
        results = {"first.png": _result(LOCK),
                   self.FILE: _result(CLEAR, "keep_text", "what the small model said", self.NAME, "small-model")}
        second = {self.FILE: _result(CLEAR, "keep_text", self.REASON, "other-name", "big-model")}
        labels = {"first.png": _label("credentials"), self.FILE: _label("credentials")}
        answers = iter(typed)

        def fake_input(prompt=""):
            events.append(("ask", prompt))
            return next(answers)

        def fake_print(*parts, **_):
            events.append(("print", " ".join(str(p) for p in parts)))

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with mock.patch.object(schema, "GOLDEN", root / "golden.csv"), \
                    mock.patch.object(check_misses.score, "results_for",
                                      lambda run_id=None: (run_id, results if run_id == "RUN" else second)), \
                    mock.patch.object(check_misses, "find_set", lambda names: (labels, root / "pictures")), \
                    mock.patch.object(check_misses, "show", lambda path: shown.append(path) or True), \
                    mock.patch.object(check_misses, "clear", lambda: events.append(("clear", ""))), \
                    mock.patch.object(check_misses.sys, "argv", ["check_misses.py", "RUN", "SECOND"]), \
                    mock.patch("builtins.input", fake_input), mock.patch("builtins.print", fake_print):
                check_misses.main()
            saved = sorted(root.glob("misses_check_*.txt"))
            text = saved[0].read_text(encoding="utf-8") if saved else ""
        return events, shown, text

    def test_answers_are_saved_without_any_name_or_description(self):
        events, shown, text = self._run(["", "y", "y", "n", "y", "y", "y", "y", ""])
        self.assertEqual([p.name for p in shown], [self.FILE])
        self.assertIn("row 2 | credentials | small y | plain y | fits n | label y | seen y | name y", text)
        self.assertIn("reads as: definition + the name leaks", text)
        for private in (self.FILE, self.REASON, self.NAME, "what the small model said", "other-name"):
            self.assertNotIn(private, text)
        after = [words for kind, words in events[[k for k, _ in events].index("clear"):] if kind == "print"]
        for private in (self.FILE, self.REASON, self.NAME):
            self.assertFalse(any(private in words for words in after))

    def test_the_file_name_is_never_printed_at_all(self):
        events, _, _ = self._run(["", "y", "y", "n", "y", "y", "y", "y", ""])
        self.assertFalse(any(self.FILE in words for _, words in events))

    def test_four_questions_come_before_anything_a_model_wrote(self):
        events, _, _ = self._run(["", "y", "y", "n", "y", "y", "y", "y", ""])
        asked = [i for i, (kind, words) in enumerate(events) if kind == "ask" and " of 6 " in words]
        first_model_words = min(i for i, (kind, words) in enumerate(events)
                                if kind == "print" and (self.REASON in words or self.NAME in words))
        self.assertGreater(first_model_words, asked[3])
        self.assertLess(first_model_words, asked[4])

    def test_the_description_comes_from_the_second_run_and_the_name_from_the_first(self):
        events, _, _ = self._run(["", "y", "y", "n", "y", "y", "y", "y", ""])
        printed = "\n".join(words for kind, words in events if kind == "print")
        self.assertIn("big-model described it as", printed)
        self.assertIn(self.REASON, printed)
        self.assertIn("written by small-model", printed)
        self.assertIn(self.NAME, printed)
        self.assertNotIn("what the small model said", printed)

    def test_saying_no_to_keep_asks_the_same_screenshot_again(self):
        typed = ["", "y", "y", "y", "y", "y", "y", "n", "n", "y", "y", "y", "n", "n", "y", ""]
        _, shown, text = self._run(typed)
        self.assertEqual(len(shown), 2)
        self.assertIn("small n | plain y | fits y | label y | seen n | name n | reads as: the model", text)

    def test_stopping_early_saves_nothing_for_that_screenshot(self):
        events, _, text = self._run(["", "y", "q", ""])
        self.assertEqual(text, "")
        self.assertTrue(any("Stopped early" in words for kind, words in events if kind == "print"))


if __name__ == "__main__":
    unittest.main()
