# tests/test_home.py — S20, stage 0.2: the home (harness/home.py, home_cli.py, home_words.py).
# Everything happens in throwaway folders; the OneDrive check is a stand-in.

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from harness import home, home_cli, home_words as words, sync_check as s  # noqa: E402

NO_SIGN = lambda folder: (s.NO_SIGN, None)          # noqa: E731
INSIDE = lambda folder: (s.INSIDE, None)            # noqa: E731
UNKNOWN = lambda folder: (s.UNKNOWN, "x reason")    # noqa: E731


class Home(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.user = self.tmp / "user"
        self.user.mkdir()
        self.note = self.tmp / "hidden" / "home.json"

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def make(self, holder=None, check=NO_SIGN, **flags):
        return home.make(holder, user=self.user, note=self.note, check=check, **flags)

    def test_proposes_a_visible_folder_in_the_user_folder(self):
        self.assertEqual(home.proposed(self.user), self.user / words.NAME)

    def test_makes_the_home_with_its_note_and_remembers_it(self):
        ok, lines = self.make()
        place = self.user / words.NAME
        self.assertTrue(ok)
        self.assertEqual(sorted(p.name for p in place.iterdir()), [words.ABOUT_FILE])
        self.assertIn(words.SENTENCE, (place / words.ABOUT_FILE).read_text(encoding="utf-8"))
        self.assertEqual(home.where(self.note), place)
        self.assertIn(words.SENTENCE, lines)

    def test_second_run_changes_nothing(self):
        self.make()
        place = self.user / words.NAME
        stamps = [(p, p.stat().st_mtime_ns) for p in (place / words.ABOUT_FILE, self.note)]
        ok, lines = self.make()
        self.assertTrue(ok)
        self.assertIn("Nothing changed", lines[0])
        self.assertEqual([(p, p.stat().st_mtime_ns) for p, _ in stamps], stamps)

    def test_a_deleted_home_is_made_again_and_says_so(self):
        # S20, found on the Legion: Sphinx deleted the folder; make re-made it and said
        # "Nothing changed". Never claim nothing changed when something did.
        self.make()
        place = self.user / words.NAME
        shutil.rmtree(place)
        ok, lines = self.make()
        self.assertTrue(ok)
        self.assertTrue((place / words.ABOUT_FILE).exists())
        self.assertNotIn("Nothing changed", " ".join(lines))
        self.assertIn("made it again", " ".join(lines))
        (place / words.ABOUT_FILE).unlink()
        ok, lines = self.make()
        self.assertIn("Put Shyft's note back", lines[0])
        self.assertIn("Nothing changed", self.make()[1][0])

    def test_inside_onedrive_needs_an_explicit_yes(self):
        ok, lines = self.make(check=INSIDE)
        self.assertFalse(ok)
        self.assertFalse((self.user / words.NAME).exists())
        self.assertFalse(self.note.exists())
        self.assertIn("--yes-onedrive", " ".join(lines))
        ok, lines = self.make(check=INSIDE, yes_onedrive=True)
        self.assertTrue(ok)
        self.assertIn("because you asked for it there", " ".join(lines))
        self.assertIn(words.LOCAL_NOW, lines)
        self.assertEqual(home.state(self.note, INSIDE)[0], "by_request")

    def test_couldnt_check_needs_an_explicit_yes(self):
        self.assertFalse(self.make(check=UNKNOWN)[0])
        self.assertFalse(self.note.exists())
        self.assertTrue(self.make(check=UNKNOWN, yes_unchecked=True)[0])

    def test_a_folder_of_that_name_shyft_didnt_make_is_left_alone(self):
        place = self.user / words.NAME
        place.mkdir()
        (place / "mine.txt").write_text("keep me", encoding="utf-8")
        ok, _ = self.make()
        self.assertFalse(ok)
        self.assertEqual([p.name for p in place.iterdir()], ["mine.txt"])
        self.assertFalse(self.note.exists())

    def test_an_empty_folder_of_that_name_is_used(self):
        (self.user / words.NAME).mkdir()
        self.assertTrue(self.make()[0])

    def test_never_inside_shyfts_own_folders(self):
        kit = self.user / "Shyft"
        kit.mkdir()
        self.assertFalse(self.make(kit)[0])
        self.assertFalse(self.make(home.schema.ROOT)[0])
        self.assertFalse(self.note.exists())

    def test_a_folder_that_isnt_there(self):
        self.assertFalse(self.make(self.tmp / "nowhere")[0])

    def test_changing_place_while_empty_leaves_the_old_folder(self):
        self.make()
        other = self.tmp / "elsewhere"
        other.mkdir()
        ok, lines = self.make(other)
        self.assertTrue(ok)
        self.assertEqual(home.where(self.note), other / words.NAME)
        self.assertTrue((self.user / words.NAME / words.ABOUT_FILE).exists())   # nothing deleted
        self.assertIn("left where it is", " ".join(lines))

    def test_changing_place_with_files_inside_is_refused(self):
        self.make()
        (self.user / words.NAME / "receipt.txt").write_text("x", encoding="utf-8")
        other = self.tmp / "elsewhere"
        other.mkdir()
        self.assertFalse(self.make(other)[0])
        self.assertEqual(home.where(self.note), self.user / words.NAME)
        self.assertTrue(self.make()[0])        # the same place still works with files in it

    def test_a_broken_note_stops_and_is_left_as_it_is(self):
        self.note.parent.mkdir()
        self.note.write_text("{not json", encoding="utf-8")
        self.assertFalse(self.make()[0])
        self.assertEqual(self.note.read_text(encoding="utf-8"), "{not json")
        self.assertIsNone(home.where(self.note))
        self.assertEqual(home.state(self.note)[0], "unreadable")


class Words(unittest.TestCase):
    def test_states_in_the_notice(self):
        self.assertIn("not made yet", words.notice_line("none"))
        self.assertIn("not found", words.notice_line("missing"))
        self.assertIn("at your request", words.notice_line("by_request", (s.INSIDE, None)))
        self.assertIn("did not ask for", words.notice_line("made", (s.INSIDE, None)))
        self.assertIn("no sign of a OneDrive copy", words.notice_line("made", (s.NO_SIGN, None)))
        self.assertNotIn("safe", words.notice_line("made", (s.NO_SIGN, None)).lower())

    def test_the_user_folder_is_never_named(self):
        self.assertEqual(words.shown(Path.home() / "Music"), str(Path("your user folder") / "Music"))
        self.assertNotIn(Path.home().name, words.shown(Path.home() / "Music"))

    def test_the_proposal_skips_a_user_folder_inside_onedrive(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            lines = home_cli.show(user=tmp, note=tmp / "none.json", check=INSIDE)
            self.assertIn("doesn't propose", lines[0])
            lines = home_cli.show(user=tmp, note=tmp / "none.json", check=NO_SIGN)
            self.assertIn("proposes making", lines[0])
        finally:
            shutil.rmtree(tmp)


if __name__ == "__main__":
    unittest.main()
