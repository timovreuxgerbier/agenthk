# tests/test_records.py — S21, stage 0.3: Shyft's records go into the home (Nook).
#   python3 -m unittest tests.test_records
# Works in temporary folders only: a made-up home, a made-up trace, made-up screenshot folders.
# Never touches the real home, trace.jsonl, screenshots/ or demo/.

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from harness import (execute, home, home_words as words, ids, receipt, records, schema, trace,
                     undo, where_check)


def item(root, folder, name):
    return {"id": ids.stable_id(folder / name, root), "file": name, "state": "open",
            "kind": "none", "file_date": "2026-11-01"}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.note = self.root / "hidden" / "home.json"
        self.old_trace = self.root / "code" / "trace.jsonl"
        self.old_trace.parent.mkdir()
        patches = [mock.patch.dict(os.environ, {"SHYFT_HOME_NOTE": str(self.note)}),
                   mock.patch.object(schema, "TRACE", self.old_trace),
                   mock.patch.object(records, "OLD_REVIEW", self.root / "code" / "demo" / "review.json")]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        self.addCleanup(self.tmp.cleanup)

    def make_home(self):
        user = self.root / "user"
        user.mkdir(exist_ok=True)
        ok, _ = home.make(user=user, note=self.note, check=lambda p: ("no_sign", None))
        self.assertTrue(ok)
        return user / words.NAME

    def shots(self, name, files=("Screenshot (1).png", "Screenshot (2).png")):
        folder = self.root / name
        folder.mkdir()
        for n, f in enumerate(files):
            (folder / f).write_bytes(name.encode() + bytes([n]))
        return folder

    def apply(self, folder, new_name, run_id="R1", file="Screenshot (1).png"):
        it = item(self.root, folder, file)
        review = {"contract": "0.2", "run_id": run_id, "items": [it]}
        decisions = {"contract": "0.2", "run_id": run_id,
                     "decisions": [{"id": it["id"], "decision": "approve", "action": "keep_image",
                                    "new_name": new_name}]}
        return execute.apply(folder, self.root, review, decisions)


class NoHome(Base):
    def test_records_stay_where_they_were(self):
        self.assertIsNone(records.folder())
        self.assertEqual(records.trace_file(), self.old_trace)
        folder = self.shots("shots")
        self.assertEqual(records.receipts_folder(folder), folder / records.OLD_RECEIPTS)
        self.assertEqual(records.review_file(), records.OLD_REVIEW)

    def test_nothing_is_made_when_the_home_is_missing(self):
        place = self.make_home()
        (place / words.ABOUT_FILE).unlink()
        place.rmdir()                                 # the person deleted the home
        self.assertIsNone(records.folder())
        self.assertEqual(records.trace_file(), self.old_trace)
        self.assertFalse(place.exists())              # Shyft did not make it again

    def test_says_where_without_a_home(self):
        self.assertEqual(records.where_words("Shyft's code folder"), "Shyft's code folder (no Nook to use)")

    def test_the_tests_never_see_a_real_home(self):   # tests/__init__.py
        self.assertIn("SHYFT_HOME_NOTE", os.environ)


class WithHome(Base):
    def test_new_records_go_into_the_home(self):
        place = self.make_home()
        base = place / words.RECORDS_FOLDER
        self.assertEqual(records.trace_file(), base / "trace.jsonl")
        self.assertEqual(records.review_file(), base / "review.json")
        self.assertEqual(records.receipts_folder(self.shots("shots")), base / "receipts")
        self.assertEqual(records.where_words("Shyft's code folder"), "Nook")

    def test_trace_written_in_home_and_read_from_both(self):
        self.old_trace.write_text(json.dumps({"run_id": "20261127-111154", "file": "old.png"}) + "\n",
                                  encoding="utf-8")
        place = self.make_home()
        trace.write({"run_id": "20261128-090000", "file": "new.png"})
        self.assertEqual(self.old_trace.read_text(encoding="utf-8").count("\n"), 1)   # untouched
        self.assertTrue((place / words.RECORDS_FOLDER / "trace.jsonl").exists())
        self.assertEqual([e["file"] for e in trace.read_all()], ["old.png", "new.png"])
        self.assertEqual(trace.latest_run()[0], "20261128-090000")
        self.assertEqual(len(trace.run("20261127-111154")[1]), 1)                     # baseline found

    def test_receipt_in_home_says_its_folder_and_undo_works(self):
        place = self.make_home()
        folder = self.shots("shots")
        text, _ = self.apply(folder, "Lisbon Flight")
        self.assertEqual(text.parent, place / words.RECORDS_FOLDER / "receipts")
        self.assertFalse((folder / records.OLD_RECEIPTS).exists())    # nothing next to the files
        saved = json.loads(text.with_suffix(".json").read_text(encoding="utf-8"))
        self.assertTrue(records.same_folder(saved["folder"], folder))
        lines, _ = undo.undo_last(folder)
        self.assertTrue((folder / "Screenshot (1).png").exists())
        self.assertEqual(lines, ["Put back: Screenshot (1).png"])

    def test_undo_only_uses_that_folders_receipts(self):
        self.make_home()
        a, b = self.shots("a"), self.shots("b")
        self.apply(a, "From A")
        self.apply(b, "From B")                       # newest receipt in the home is B's
        undo.undo_last(a)
        self.assertTrue((a / "Screenshot (1).png").exists())
        self.assertTrue((b / "from-b.png").exists())  # B untouched
        self.assertIsNone(receipt.latest_open(a)[1])
        self.assertIsNotNone(receipt.latest_open(b)[1])

    def test_runs_from_before_the_home_can_still_be_undone(self):
        folder = self.shots("shots")
        self.apply(folder, "Before Home")             # no home yet: old subfolder
        old = folder / records.OLD_RECEIPTS
        self.assertTrue(old.is_dir())
        self.make_home()
        it2 = item(self.root, folder, "Screenshot (2).png")
        execute.apply(folder, self.root, {"contract": "0.2", "run_id": "R2", "items": [it2]},
                      {"contract": "0.2", "run_id": "R2", "decisions": [
                          {"id": it2["id"], "decision": "approve", "action": "keep_image",
                           "new_name": "After Home"}]})
        undo.undo_last(folder)                        # the newer run (in the home) first
        self.assertTrue((folder / "Screenshot (2).png").exists())
        self.assertTrue((folder / "before-home.png").exists())
        undo.undo_last(folder)                        # then the one from before the home
        self.assertTrue((folder / "Screenshot (1).png").exists())
        self.assertEqual(len(list(old.glob("receipt_*.json"))), 1)   # old receipt stayed put
        self.assertEqual(undo.undo_last(folder), (None, None))

    def test_receipts_never_overwrite_each_other(self):
        self.make_home()
        folder = self.shots("shots")
        with mock.patch.object(receipt, "now", return_value="2026-11-28T09:00:00"):
            first, _ = self.apply(folder, "One")
            second, _ = self.apply(folder, "Two", file="Screenshot (2).png")
        self.assertNotEqual(first, second)
        self.assertTrue(first.exists() and second.exists())

    def test_review_newest_is_read(self):
        place = self.make_home()
        self.assertIsNone(records.review_to_read())
        records.review_file().write_text("{}", encoding="utf-8")
        self.assertEqual(records.review_to_read(), place / words.RECORDS_FOLDER / "review.json")


class TheHomeStaysShyfts(Base):
    def test_shyft_still_knows_its_home_after_remove(self):     # D42: Remove deletes the note only
        place = self.make_home()
        trace.write({"run_id": "R", "file": "x.png"})
        self.note.unlink()
        ok, lines = home.make(user=place.parent, note=self.note, check=lambda p: ("no_sign", None))
        self.assertTrue(ok, lines)
        self.assertEqual(home.where(self.note), place)

    def test_a_home_with_records_does_not_move(self):            # rule 7: empty homes only
        place = self.make_home()
        trace.write({"run_id": "R", "file": "x.png"})
        other = self.root / "elsewhere"
        other.mkdir()
        ok, _ = home.make(other, user=place.parent, note=self.note, check=lambda p: ("no_sign", None))
        self.assertFalse(ok)
        self.assertEqual(home.where(self.note), place)


class Renamed(Base):
    def test_after_a_rename_the_old_folder_is_named_truly(self):   # S21: Waystation -> Nook
        user = self.root / "user"
        old = user / "The Waystation"
        old.mkdir(parents=True)
        self.note.parent.mkdir()
        self.note.write_text(json.dumps({"place": str(old), "synced_by_request": False,
                                         "unchecked_by_request": False}), encoding="utf-8")
        ok, lines = home.make(user=user, note=self.note, check=lambda p: ("no_sign", None))
        self.assertTrue(ok)
        self.assertIn("The Waystation", lines[-1])
        self.assertTrue(old.is_dir())                              # left where it is
        old.rmdir()                                                # the person deleted it
        self.note.write_text(json.dumps({"place": str(old), "synced_by_request": False,
                                         "unchecked_by_request": False}), encoding="utf-8")
        (user / words.NAME / words.ABOUT_FILE).unlink()
        (user / words.NAME).rmdir()
        ok, lines = home.make(user=user, note=self.note, check=lambda p: ("no_sign", None))
        self.assertTrue(ok)
        self.assertFalse(any("left where it is" in line for line in lines))   # nothing false said
        self.assertEqual(home.where(self.note), user / words.NAME)


class Words(unittest.TestCase):
    def test_the_name_is_nook(self):
        self.assertEqual(words.NAME, "Nook")

    def test_notice_says_where_records_go_without_paths(self):
        made = where_check.lines([], ("unknown", "x"), ("made", ("no_sign", None)))
        self.assertIn("  Shyft's records (what it proposed, receipts for undo): kept in Nook.", made)
        none = "\n".join(where_check.lines([], ("unknown", "x"), ("none", None)))
        self.assertIn("Nook isn't made yet, so this run's records go to", none)
        self.assertNotIn(str(Path.home()), none)


if __name__ == "__main__":
    unittest.main()
