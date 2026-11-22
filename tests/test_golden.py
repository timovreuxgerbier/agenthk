# tests/test_golden.py — Lane: Sphinx. The label sheet's two axes read the same way everywhere.
#   python3 -m unittest tests.test_golden
# 1. A kind other than "none" means the pipeline should lock, whatever the disposition says.
# 2. Sheets from before S9 (no sensitive_kind column) still read.
# 3. A "none" row must carry a disposition; a bad kind or action is reported, not guessed.

import unittest

from eval import golden


class TestTwoAxes(unittest.TestCase):
    def test_kind_wins_over_disposition(self):
        label, problem = golden.one_label({"file": "a.png", "expected_action": "to_be_deleted",
                                           "sensitive_kind": "bank_or_payment"})
        self.assertIsNone(problem)
        self.assertEqual(label["expected"], "sensitive")
        self.assertEqual(label["disposition"], "to_be_deleted")

    def test_none_means_disposition(self):
        label, problem = golden.one_label({"file": "a.png", "expected_action": "keep_text",
                                           "sensitive_kind": "none"})
        self.assertIsNone(problem)
        self.assertEqual(label["expected"], "keep_text")

    def test_locked_file_may_have_no_disposition(self):
        label, problem = golden.one_label({"file": "a.png", "expected_action": "",
                                           "sensitive_kind": "credentials"})
        self.assertIsNone(problem)
        self.assertEqual((label["expected"], label["disposition"]), ("sensitive", ""))


class TestOldSheets(unittest.TestCase):
    def test_old_sensitive_becomes_unknown_kind(self):
        label, problem = golden.one_label({"file": "a.png", "expected_action": "sensitive"})
        self.assertIsNone(problem)
        self.assertEqual((label["expected"], label["kind"]), ("sensitive", golden.UNKNOWN_KIND))

    def test_old_keep_becomes_none(self):
        label, problem = golden.one_label({"file": "a.png", "expected_action": "keep_image", "note": "x"})
        self.assertIsNone(problem)
        self.assertEqual((label["expected"], label["kind"]), ("keep_image", "none"))


class TestProblems(unittest.TestCase):
    def test_none_without_disposition_is_a_problem(self):
        label, problem = golden.one_label({"file": "a.png", "expected_action": "", "sensitive_kind": "none"})
        self.assertIsNone(label)
        self.assertIn("expected_action", problem)

    def test_unknown_words_are_problems(self):
        for row in [{"expected_action": "keep", "sensitive_kind": "none"},
                    {"expected_action": "keep_image", "sensitive_kind": "sofa"},
                    {"expected_action": "", "sensitive_kind": ""}]:
            label, problem = golden.one_label(dict(row, file="a.png"))
            self.assertIsNone(label, row)
            self.assertTrue(problem, row)


if __name__ == "__main__":
    unittest.main()
