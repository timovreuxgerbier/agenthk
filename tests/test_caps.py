# tests/test_caps.py — Lane: Timo. No model needed:  python3 -m unittest tests.test_caps

import unittest

from harness.caps import RunCaps


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


class TestRunCaps(unittest.TestCase):
    def test_file_limit(self):
        self.assertEqual(len(RunCaps(max_files=10).limit_files(range(25))), 10)

    def test_call_limit(self):
        caps = RunCaps(max_calls=15)
        for _ in range(15):
            self.assertIsNone(caps.check())
            caps.record_call()
        self.assertIn("call limit", caps.check())

    def test_time_limit(self):
        clock = FakeClock()
        caps = RunCaps(max_seconds=300, clock=clock)
        clock.now = 299
        self.assertIsNone(caps.check())
        clock.now = 300
        self.assertIn("time limit", caps.check())

    def test_defaults_come_from_schema(self):
        caps = RunCaps()
        self.assertEqual((caps.max_files, caps.max_calls, caps.max_seconds), (10, 15, 300))

    def test_run_asking_for_14_screenshots_gets_10(self):
        # Same path as run.py: prefilter picks, then caps limits. 14 fake files, no model.
        import tempfile
        from pathlib import Path
        from harness import prefilter, schema

        with tempfile.TemporaryDirectory() as folder:
            original = schema.SCREENSHOTS
            schema.SCREENSHOTS = Path(folder)
            try:
                import os
                for n in range(14):
                    shot = Path(folder) / ("shot" + str(n).zfill(2) + ".png")
                    shot.write_bytes(b"")
                    os.utime(shot, (1000 + n, 1000 + n))   # shot13 is the newest
                batch = RunCaps().limit_files(prefilter.pick_screenshots(14))
            finally:
                schema.SCREENSHOTS = original
        self.assertEqual(len(batch), 10)
        # The 4 oldest are the ones left out, never the newest.
        self.assertEqual(batch[0].name, "shot13.png")
        self.assertNotIn("shot00.png", [p.name for p in batch])


if __name__ == "__main__":
    unittest.main()
