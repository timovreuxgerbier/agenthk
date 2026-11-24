# tests/test_execute.py — Lane: Sphinx. No model needed:
#   python3 -m unittest tests.test_execute
# Works in a temporary folder; never touches screenshots/ or demo/.

import tempfile
import unittest
from pathlib import Path

from harness import execute, ids, receipt, undo


def item(root, folder, name, state="open", kind="none"):
    return {"id": ids.stable_id(folder / name, root), "file": name, "state": state,
            "kind": kind, "file_date": "2016-03-04"}


def decision(it, action, new_name=None, what="approve"):
    return {"id": it["id"], "decision": what, "action": action, "new_name": new_name}


class TestExecute(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.folder = self.root / "demo"
        self.folder.mkdir()
        for name, data in (("Screenshot (1).png", b"one"), ("Screenshot (2).png", b"two"),
                           ("Screenshot (3).png", b"three")):
            (self.folder / name).write_bytes(data)
        self.open1 = item(self.root, self.folder, "Screenshot (1).png")
        self.open1["reason"] = "A flight confirmation."
        self.open2 = item(self.root, self.folder, "Screenshot (2).png")
        self.locked = item(self.root, self.folder, "Screenshot (3).png", "locked", "bank_or_payment")
        self.review = {"contract": "0.2", "run_id": "R1",
                       "items": [self.open1, self.open2, self.locked]}

    def tearDown(self):
        self.tmp.cleanup()

    def apply(self, decisions):
        return execute.apply(self.folder, self.root, self.review,
                             {"contract": "0.2", "run_id": "R1", "decisions": decisions})

    def test_rename_move_and_sealed_receipt(self):
        text, steps = self.apply([decision(self.open1, "keep_image", "Lisbon Flight"),
                                  decision(self.locked, "to_be_deleted"),
                                  decision(self.open2, None, what="skip")])
        self.assertTrue((self.folder / "lisbon-flight.png").exists())
        self.assertTrue((self.folder / execute.BIN / "Screenshot (3).png").exists())
        self.assertEqual([s["outcome"] for s in steps], ["renamed", "moved", "skipped"])
        words = text.read_text(encoding="utf-8")
        self.assertIn("lisbon-flight.png", words)
        self.assertIn("A flight confirmation.", words)
        self.assertIn("bank or payment, Mar 2016: moved to To Be Deleted", words)
        self.assertNotIn("Screenshot (3)", words)        # locked file is sealed

    def test_locked_is_never_renamed_or_read(self):
        _, steps = self.apply([decision(self.locked, "keep_text", "bank statement")])
        self.assertEqual(steps[0]["outcome"], "not_done")
        _, steps = self.apply([decision(self.locked, "keep_image", "bank statement")])
        self.assertEqual(steps[0]["outcome"], "kept")
        self.assertTrue((self.folder / "Screenshot (3).png").exists())

    def test_changed_file_is_refused(self):
        (self.folder / "Screenshot (1).png").write_bytes(b"edited after review")
        _, steps = self.apply([decision(self.open1, "keep_image", "lisbon flight")])
        self.assertEqual(steps[0]["outcome"], "not_done")
        self.assertFalse((self.folder / "lisbon-flight.png").exists())

    def test_never_overwrites(self):
        (self.folder / "lisbon-flight.png").write_bytes(b"already here")
        self.apply([decision(self.open1, "keep_image", "lisbon flight")])
        self.assertEqual((self.folder / "lisbon-flight.png").read_bytes(), b"already here")
        self.assertTrue((self.folder / "lisbon-flight-2.png").exists())

    def test_wrong_run_changes_nothing(self):
        with self.assertRaises(execute.Refused):
            execute.apply(self.folder, self.root, self.review,
                          {"contract": "0.2", "run_id": "OTHER",
                           "decisions": [decision(self.open1, "keep_image", "x name")]})
        self.assertTrue((self.folder / "Screenshot (1).png").exists())

    def test_undo_puts_everything_back(self):
        self.apply([decision(self.open1, "keep_image", "lisbon flight"),
                    decision(self.locked, "to_be_deleted")])
        lines, _ = undo.undo_last(self.folder)
        self.assertEqual(len(lines), 2)
        for name in ("Screenshot (1).png", "Screenshot (3).png"):
            self.assertTrue((self.folder / name).exists(), name)
        self.assertFalse((self.folder / "lisbon-flight.png").exists())
        self.assertEqual(undo.undo_last(self.folder), (None, None))   # nothing left to undo
        self.assertEqual(receipt.latest_open(self.folder), (None, None))


if __name__ == "__main__":
    unittest.main()
