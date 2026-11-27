# apply.py — Shyft's second half: a person's decisions become real changes.
#
#   python3 apply.py              use the newest decisions*.json in your Downloads folder
#   python3 apply.py PATH         use that decisions file
#   python3 apply.py undo         put back everything the last apply changed
#
# It works ONLY on the demo folder (demo/), which dev/make_review.py fills with copies
# of a synthetic run's screenshots. The test sets are never touched.
# Renames and moves only. Nothing is ever deleted or overwritten. Every change is
# checked and written to a receipt. S21 (0.3): review.json and the receipts are kept in the
# home (Nook), via harness/records.py; with no home, where they were (demo/).

import json
import sys
from pathlib import Path

from harness import execute, records, schema, undo

sys.stdout.reconfigure(encoding="utf-8")
DEMO = schema.ROOT / "demo"


def newest_download():
    downloads = Path.home() / "Downloads"
    found = sorted(downloads.glob("decisions*.json"), key=lambda p: p.stat().st_mtime)
    return found[-1] if found else None


def load(path, what):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        sys.exit("Stopped, nothing changed: could not read the " + what + " at " + str(path))


def run_apply(args):
    review = records.review_to_read()
    if review is None:
        sys.exit("Stopped, nothing changed: no review.json. Run dev/make_review.py first.")
    source = Path(args[0]) if args else newest_download()
    if source is None:
        sys.exit("Stopped, nothing changed: no decisions*.json in your Downloads folder.\n"
                 "On the review page's last screen, click 'Download decisions.json'.")
    print("Decisions: " + str(source))
    try:
        text, steps = execute.apply(DEMO, schema.ROOT, load(review, "review"),
                                    load(source, "decisions file"))
    except execute.Refused as problem:
        sys.exit("Stopped, nothing changed: " + str(problem))
    counts = {}
    for step in steps:
        counts[step["outcome"]] = counts.get(step["outcome"], 0) + 1
    print("Renamed " + str(counts.get("renamed", 0)) + " · moved to To Be Deleted "
          + str(counts.get("moved", 0)) + " · kept " + str(counts.get("kept", 0))
          + " · not now " + str(counts.get("skipped", 0)) + " · not done "
          + str(counts.get("not_done", 0)))
    print("Receipt: " + str(text))
    print("To put everything back:  python3 apply.py undo")


def run_undo():
    lines, path = undo.undo_last(DEMO)
    if lines is None:
        print("Nothing to undo: every applied run has already been undone.")
        return
    for line in lines:
        print("  " + line)
    print("Undone. Receipt updated: " + str(path.with_suffix(".txt")))


def main():
    args = sys.argv[1:]
    if args and args[0] == "undo":
        run_undo()
    else:
        run_apply(args)


if __name__ == "__main__":
    main()
