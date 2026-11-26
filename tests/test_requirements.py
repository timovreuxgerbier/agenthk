# tests/test_requirements.py — Lane: Sphinx. D27: one file holds what a laptop needs.
#   python3 -m unittest tests.test_requirements
# The download and the screens read shyft_requirements.json, so it must always open and add up.
# 1. It is valid JSON with the four rulings in it (shape, floor, files rule, bar).
# 2. The sizes add up: the two downloads make the total, and the parts make the free disk.
# 3. Each model has a long name to pull, a short name and a 12-character id.

import json
import unittest

from harness import schema

PATH = schema.ROOT / "shyft_requirements.json"


class TestRequirementsFile(unittest.TestCase):
    def setUp(self):
        self.needs = json.loads(PATH.read_text(encoding="utf-8"))

    def test_the_four_rulings_are_there(self):
        for part in ("shape", "floor", "files_rule", "bar", "unverified"):
            self.assertIn(part, self.needs)
        self.assertFalse(self.needs["bar"]["real_set"]["meets_bar"])

    def test_the_sizes_add_up(self):
        shape, floor = self.needs["shape"], self.needs["floor"]
        both = shape["gate"]["download_gb"] + shape["namer"]["download_gb"]
        self.assertAlmostEqual(both, shape["download_gb_total"], places=1)
        self.assertEqual(floor["free_disk_parts_gb"]["model_files"], shape["download_gb_total"])
        parts = sum(floor["free_disk_parts_gb"].values())
        self.assertTrue(parts <= floor["free_disk_gb"] < parts + 1)

    def test_each_model_has_names_and_an_id(self):
        for job in ("gate", "namer"):
            model = self.needs["shape"][job]
            self.assertTrue(model["pull"].startswith(model["short_name"]))
            self.assertRegex(model["id"], r"^[0-9a-f]{12}$")

    def test_the_gate_is_the_default_model_family(self):
        self.assertEqual(self.needs["shape"]["gate"]["short_name"], schema.DEFAULT_MODEL)


if __name__ == "__main__":
    unittest.main()
