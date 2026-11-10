# tests/test_naming.py — Lane: Sphinx. No model needed:  python3 -m unittest tests.test_naming

import unittest

from harness import naming


class TestIsMeaningless(unittest.TestCase):
    def test_default_names_say_nothing(self):
        for name in [
            "Screenshot 2026-11-10 085400.png",          # Windows Snipping Tool
            "Screenshot 2026-11-03 at 2.10.00 PM.png",   # macOS
            "Screen Shot 2024-01-01 at 10.00.00 AM.png", # older macOS
            "Screenshot_20231105-120000.png",            # Android
            "IMG_4821.PNG",                              # iPhone
            "image (3).png", "Untitled.png", "Capture.PNG", "20261110_091158.jpg",
        ]:
            self.assertTrue(naming.is_meaningless(name), name)

    def test_real_names_are_kept(self):
        for name in ["pasta-recipe.png", "Lisbon flight.png", "sofa inspo.jpg",
                     "Screenshot of tax form.png"]:
            self.assertFalse(naming.is_meaningless(name), name)


class TestCleanName(unittest.TestCase):
    def test_tidies_a_good_suggestion(self):
        self.assertEqual(naming.clean_name("Pasta Recipe, Lemon & Garlic!"),
                         "pasta-recipe-lemon-garlic")

    def test_drops_extension_dates_and_extra_words(self):
        self.assertEqual(naming.clean_name("flight 2026 JFK Lisbon confirm code seat window.png"),
                         "flight-jfk-lisbon-confirm-code-seat")

    def test_rejects_names_that_still_say_nothing(self):
        for bad in ["", "screenshot", "image 2026-11-10", "IMG_1234", None, 42]:
            self.assertEqual(naming.clean_name(bad), "", bad)


class TestRenameFor(unittest.TestCase):
    def test_kept_screenshot_with_meaningless_name_is_renamed(self):
        proposal = {"action": "keep_text", "new_name": "pasta recipe"}
        self.assertEqual(naming.rename_for(proposal, "IMG_1.png"), "pasta-recipe")

    def test_good_name_is_left_alone(self):
        proposal = {"action": "keep_text", "new_name": "pasta recipe"}
        self.assertEqual(naming.rename_for(proposal, "grandma-pasta.png"), "")

    def test_sensitive_and_deleted_are_never_renamed(self):
        for action in ["sensitive", "to_be_deleted"]:
            proposal = {"action": action, "new_name": "chase bank statement"}
            self.assertEqual(naming.rename_for(proposal, "IMG_1.png"), "", action)

    def test_missing_name_is_a_code_check_problem(self):
        proposal = {"action": "keep_image", "new_name": ""}
        self.assertIsNotNone(naming.rename_problem(proposal, "IMG_1.png"))
        self.assertIsNone(naming.rename_problem(proposal, "sofa-inspo.png"))


if __name__ == "__main__":
    unittest.main()
