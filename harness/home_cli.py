# harness/home_cli.py — Lane: Sphinx. S20. The person's commands for the home (harness/home.py).
#
#   python3 -m harness.home_cli                     where it is, or where Shyft proposes. Changes nothing.
#   python3 -m harness.home_cli make                make it in the proposed place (your user folder)
#   python3 -m harness.home_cli make "D:\Folder"    make it inside a folder you choose
#   add --yes-onedrive   to make it inside OneDrive anyway (Shyft says what that means)
#   add --yes-unchecked  to make it where Shyft couldn't check

import sys
from pathlib import Path

from harness import home, home_words as words, sync_check


def show(user=None, note=None, check=sync_check.check):
    """What `python3 -m harness.home_cli` prints. Changes nothing."""
    try:
        current = home.read_note(note)
    except ValueError:
        return ["Shyft's note of where its home is can't be read."]
    if current:
        place = Path(current["place"])
        return [words.NAME + " is in " + words.shown(place.parent) + ".",
                words.notice_line(*home.state(note, check))]
    holder = Path(user or Path.home())
    answer, reason = check(holder)
    if answer == sync_check.INSIDE:        # rule 1: never propose a place that fails the check
        return ["Your user folder is inside OneDrive, so Shyft doesn't propose it.",
                "To choose a place: python3 -m harness.home_cli make \"<a folder you choose>\""]
    if answer == sync_check.UNKNOWN:
        return ["Shyft couldn't check your user folder (" + str(reason) + "), so it proposes "
                "nothing. To choose a place: python3 -m harness.home_cli make \"<a folder>\""]
    return ["Shyft proposes making " + words.NAME + " in " + words.shown(holder) + ".",
            words.SENTENCE,
            "To make it there: python3 -m harness.home_cli make",
            "To choose another place: python3 -m harness.home_cli make \"<a folder you choose>\""]


def main(args):
    if not args:
        print("\n".join(show()))
        return 0
    if args[0] != "make":
        print("Use: python3 -m harness.home_cli  |  make [folder] [--yes-onedrive] [--yes-unchecked]")
        return 2
    rest = [a for a in args[1:] if not a.startswith("--")]
    ok, lines = home.make(rest[0] if rest else None, "--yes-onedrive" in args, "--yes-unchecked" in args)
    print("\n".join(lines))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
