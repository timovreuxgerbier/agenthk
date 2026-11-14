# dev/use_set.py — swap which test set the agent sees. DEV ONLY.
#
#   python3 dev/use_set.py              show which set is loaded and which exist
#   python3 dev/use_set.py synthetic    load the synthetic set
#   python3 dev/use_set.py real         put your real screenshots back
#
# Sets live in golden/sets/<name>/ (screenshots/ + golden.csv). Loading one MOVES its
# files into screenshots/ and golden/; the set that was there goes back to its own folder.
# Moving (not copying) keeps every file's date, which decides which screenshots run first.
# Nothing is deleted, and two sets are never mixed.

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from harness import schema               # noqa: E402

SETS = ROOT / "golden" / "sets"
ACTIVE = ROOT / "golden" / "active_set.txt"
FIRST_SET = "real"                        # what screenshots/ holds before this tool is ever used


def active():
    return ACTIVE.read_text(encoding="utf-8").strip() if ACTIVE.exists() else FIRST_SET


def images(folder):
    if not folder.exists():
        return []
    return [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in schema.IMAGE_TYPES]


def move_all(files, folder):
    folder.mkdir(parents=True, exist_ok=True)
    clashes = [p.name for p in files if (folder / p.name).exists()]
    if clashes:
        sys.exit("Stopped, nothing moved: " + str(folder) + " already has " + clashes[0]
                 + (" and " + str(len(clashes) - 1) + " more" if len(clashes) > 1 else ""))
    for p in files:
        os.replace(p, folder / p.name)


def park(name):
    """Send what's loaded now back to golden/sets/<name>/."""
    home = SETS / name
    move_all(images(schema.SCREENSHOTS), home / "screenshots")
    if schema.GOLDEN.exists():
        if (home / "golden.csv").exists():
            sys.exit("Stopped: " + name + " already has a golden.csv; not overwriting it.")
        os.replace(schema.GOLDEN, home / "golden.csv")


def load(name):
    home = SETS / name
    move_all(images(home / "screenshots"), schema.SCREENSHOTS)
    if (home / "golden.csv").exists():
        os.replace(home / "golden.csv", schema.GOLDEN)


def show():
    print("Loaded now: " + active() + " (" + str(len(images(schema.SCREENSHOTS))) + " screenshots)")
    others = sorted(p.name for p in SETS.iterdir() if p.is_dir()) if SETS.exists() else []
    for name in [n for n in others if n != active()]:
        print("  available: " + name + " (" + str(len(images(SETS / name / "screenshots"))) + ")")


def main():
    if len(sys.argv) < 2:
        show()
        return
    target, current = sys.argv[1], active()
    if target == current:
        print(target + " is already loaded.")
        return
    if target != FIRST_SET and not images(SETS / target / "screenshots"):
        sys.exit("No set called '" + target + "' in golden/sets/. Make it first: python3 dev/make_set.py")
    park(current)
    load(target)
    ACTIVE.parent.mkdir(exist_ok=True)
    ACTIVE.write_text(target + "\n", encoding="utf-8")
    print("Put away '" + current + "', loaded '" + target + "'.")
    show()
    if not schema.GOLDEN.exists():
        print("This set has no answers yet. Run  python3 run.py score  to make the sheet to fill in.")


if __name__ == "__main__":
    main()
