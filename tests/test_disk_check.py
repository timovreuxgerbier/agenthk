# tests/test_disk_check.py — S19: does Windows say the disk is encrypted? (harness/disk_check.py)
# PowerShell is never started here: a stand-in "asker" plays Windows' answer.

import ntpath
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from harness import disk_check  # noqa: E402


def answers(text):
    return lambda drive: text


def raises(error):
    def asker(drive):
        raise error
    return asker


class Read(unittest.TestCase):
    def test_one_is_encrypted(self):
        self.assertEqual(disk_check.read("1\r\n"), (disk_check.ENCRYPTED, None))

    def test_two_is_not_encrypted(self):
        self.assertEqual(disk_check.read("2"), (disk_check.NOT_ENCRYPTED, None))

    def test_other_numbers_are_unknown_never_encrypted(self):
        for text in ("0", "3", "4", "5", "6", "9"):
            answer, reason = disk_check.read(text)
            self.assertEqual(answer, disk_check.UNKNOWN, text)
            self.assertIn(text, reason)

    def test_nothing_is_unknown(self):
        self.assertEqual(disk_check.read("")[0], disk_check.UNKNOWN)
        self.assertEqual(disk_check.read(None)[0], disk_check.UNKNOWN)

    def test_words_are_unknown(self):
        self.assertEqual(disk_check.read("Exception calling ...")[0], disk_check.UNKNOWN)


class Drive(unittest.TestCase):
    def test_drive_letter(self):
        self.assertEqual(disk_check.drive_of(r"c:\Users\jordan\shift-test", ntpath), "C:")

    def test_network_share_has_no_letter(self):
        self.assertIsNone(disk_check.drive_of(r"\\server\share\shots", ntpath))

    def test_only_a_checked_letter_reaches_the_question(self):
        seen = []
        disk_check.check(r"C:\x", asker=lambda drive: seen.append(drive) or "1")
        if sys.platform == "win32":
            self.assertEqual(seen, ["C:"])
        for drive in seen:
            self.assertRegex(drive, r"^[A-Z]:$")


@unittest.skipUnless(sys.platform == "win32", "drive letters exist only on Windows")
class CheckOnWindows(unittest.TestCase):
    def test_encrypted(self):
        self.assertEqual(disk_check.check(r"C:\x", answers("1"))[0], disk_check.ENCRYPTED)

    def test_timeout_is_unknown(self):
        answer, reason = disk_check.check(r"C:\x", raises(subprocess.TimeoutExpired("ps", 6)))
        self.assertEqual(answer, disk_check.UNKNOWN)
        self.assertIn("in time", reason)

    def test_no_powershell_is_unknown(self):
        self.assertEqual(disk_check.check(r"C:\x", raises(FileNotFoundError()))[0],
                         disk_check.UNKNOWN)


class Question(unittest.TestCase):
    def test_question_is_fixed(self):
        self.assertEqual(disk_check.QUESTION.format(drive="C:").count("C:"), 1)
        self.assertIn("System.Volume.BitLockerProtection", disk_check.QUESTION)

    @unittest.skipIf(sys.platform == "win32", "the Windows answer depends on this computer")
    def test_off_windows_is_unknown_and_starts_nothing(self):
        answer, reason = disk_check.check(Path.cwd())
        self.assertEqual(answer, disk_check.UNKNOWN)
        self.assertIn("Windows only", reason)


if __name__ == "__main__":
    unittest.main()
