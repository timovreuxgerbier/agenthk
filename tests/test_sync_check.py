# tests/test_sync_check.py — S19: is a folder inside OneDrive? (harness/sync_check.py)
# Uses Windows path rules (ntpath) on any computer, so it runs the same on Windows and Linux.
# No real OneDrive, registry or folder is touched.

import ntpath
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from harness import sync_check  # noqa: E402

ROOT = r"C:\Users\jordan\OneDrive"


class Inside(unittest.TestCase):
    def test_folder_inside_onedrive(self):
        self.assertEqual(sync_check.answer(ROOT + r"\Pictures\Screenshots", [ROOT]),
                         sync_check.INSIDE)

    def test_the_onedrive_folder_itself(self):
        self.assertEqual(sync_check.answer(ROOT, [ROOT]), sync_check.INSIDE)

    def test_case_and_slashes_do_not_matter(self):
        self.assertEqual(sync_check.answer("c:/users/JORDAN/onedrive/pictures", [ROOT]),
                         sync_check.INSIDE)

    def test_business_account_counts(self):
        work = r"C:\Users\jordan\OneDrive - Studio Ltd"
        self.assertEqual(sync_check.answer(work + r"\Desktop", [ROOT, work]), sync_check.INSIDE)


class NoSign(unittest.TestCase):
    def test_folder_outside_onedrive(self):
        self.assertEqual(sync_check.answer(r"C:\Users\jordan\shift-test\screenshots", [ROOT]),
                         sync_check.NO_SIGN)

    def test_a_name_that_only_starts_the_same_is_not_inside(self):
        self.assertEqual(sync_check.answer(r"C:\Users\jordan\OneDriveBackupOld", [ROOT]),
                         sync_check.NO_SIGN)

    def test_other_drive(self):
        self.assertEqual(sync_check.answer(r"D:\shots", [ROOT]), sync_check.NO_SIGN)

    def test_no_onedrive_at_all(self):
        self.assertEqual(sync_check.answer(r"C:\Users\jordan\Pictures", []), sync_check.NO_SIGN)

    def test_never_answers_not_synced(self):
        self.assertEqual(set(vars(sync_check)) & {"NOT_SYNCED", "SAFE"}, set())


class Roots(unittest.TestCase):
    def test_environment_names(self):
        env = {"OneDrive": ROOT, "OneDriveCommercial": r"C:\W", "PATH": r"C:\x"}
        self.assertEqual(sync_check.roots_from_env(env), [ROOT, r"C:\W"])

    def test_empty_values_ignored(self):
        self.assertEqual(sync_check.roots_from_env({"OneDrive": ""}), [])

    @unittest.skipIf(sys.platform == "win32", "on Windows the real registry is read")
    def test_registry_is_empty_off_windows(self):
        self.assertEqual(sync_check.roots_from_registry(), [])

    @unittest.skipIf(sys.platform == "win32", "the Windows answer depends on this computer")
    def test_check_off_windows_is_unknown(self):
        answer, reason = sync_check.check(Path.cwd())
        self.assertEqual(answer, sync_check.UNKNOWN)
        self.assertIn("Windows only", reason)

    @unittest.skipUnless(sys.platform == "win32", "Windows only")
    def test_check_on_windows_gives_one_of_three(self):
        answer, _ = sync_check.check(Path.cwd())
        self.assertIn(answer, (sync_check.INSIDE, sync_check.NO_SIGN, sync_check.UNKNOWN))


if __name__ == "__main__":
    unittest.main()
