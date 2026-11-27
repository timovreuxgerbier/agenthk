# tests/test_where_check.py — S19: the notice Shyft prints before a run (harness/where_check.py)

import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from harness import disk_check as d, sync_check as s, where_check  # noqa: E402

SHOTS, OWN = "Screenshots folder", "Shyft's own folder"


def notice(shots, own, disk):
    return "\n".join(where_check.lines([(SHOTS, shots), (OWN, own)], disk))


class Words(unittest.TestCase):
    def test_inside_onedrive_says_cloud(self):
        text = notice((s.INSIDE, None), (s.NO_SIGN, None), (d.ENCRYPTED, None))
        self.assertIn("Screenshots folder: inside your OneDrive folder", text)
        self.assertIn("Microsoft's cloud", text)

    def test_no_sign_says_what_was_checked(self):
        text = notice((s.NO_SIGN, None), (s.NO_SIGN, None), (d.NOT_ENCRYPTED, None))
        self.assertIn("no sign of a OneDrive copy", text)
        self.assertIn(where_check.SCOPE, text)
        self.assertNotIn("not synced", text.lower())
        self.assertNotIn("safe", text.lower())

    def test_unknown_gives_the_reason(self):
        text = notice((s.UNKNOWN, "x reason"), (s.UNKNOWN, "x reason"), (d.UNKNOWN, "y reason"))
        self.assertIn("couldn't check (x reason)", text)
        self.assertIn("couldn't tell (y reason)", text)
        self.assertNotIn(where_check.SCOPE, text)     # nothing was checked, so no scope line

    def test_encrypted_only_when_windows_says(self):
        for disk in ((d.NOT_ENCRYPTED, None), (d.UNKNOWN, "r")):
            text = notice((s.NO_SIGN, None), (s.NO_SIGN, None), disk)
            self.assertNotIn("disk: encrypted", text)
        self.assertIn("disk: encrypted, Windows says",
                      notice((s.NO_SIGN, None), (s.NO_SIGN, None), (d.ENCRYPTED, None)))

    def test_always_says_the_run_goes_on(self):
        self.assertIn("The run goes on", notice((s.INSIDE, None), (s.INSIDE, None),
                                                (d.UNKNOWN, "r")))


class Report(unittest.TestCase):
    def printed(self, places):
        out = io.StringIO()
        with redirect_stdout(out):
            where_check.report(places)
        return out.getvalue()

    def test_no_paths_or_user_names_printed(self):
        secret = Path.cwd() / "jordan-private-folder"
        text = self.printed([(SHOTS, secret), (OWN, secret)])
        self.assertNotIn("jordan-private-folder", text)
        self.assertNotIn(str(Path.home()), text)

    def test_a_broken_check_never_stops_the_run(self):
        with mock.patch.object(s, "check", side_effect=RuntimeError("boom")):
            text = self.printed([(SHOTS, Path.cwd())])
        self.assertIn("couldn't check (RuntimeError)", text)
        self.assertIn("The run goes on", text)

    def test_disk_is_asked_about_the_screenshots_folder(self):
        with mock.patch.object(d, "check", return_value=(d.ENCRYPTED, None)) as asked:
            self.printed([(SHOTS, Path("shots-here")), (OWN, Path("own-here"))])
        asked.assert_called_once_with(Path("shots-here"))


if __name__ == "__main__":
    unittest.main()
