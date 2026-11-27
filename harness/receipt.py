# harness/receipt.py — Lane: Sphinx. Bloop's receipt (idea: Sabrina, 'Spire).
# Three jobs: RECORD what changed, let the person UNDO the last run, and PROVE
# where it ran. Two files per run:
#   receipt_<time>.json  every step, for undo (our code reads it)
#   receipt_<time>.txt   the same in plain words, for the person
# Locked files are SEALED in the .txt: kind and month only, never a name.
# S21 (stage 0.3): new receipts go into the home ("Shyft's records/receipts", via
# harness/records.py), one folder for every screenshot folder, so each receipt says which
# folder it is about and undo only uses that folder's receipts. Receipts from before 0.3
# stay in the folder's "Shyft receipts" subfolder and are still read, so those runs can
# still be undone. With no home, receipts go to that subfolder, as before.

import json
from datetime import datetime
from pathlib import Path

from harness import records

FOLDER_NAME = records.OLD_RECEIPTS
WORDS = {"renamed": "Renamed", "moved": "Moved to To Be Deleted", "kept": "Kept as they were",
         "skipped": "Not now", "not_done": "Not done"}
ONE = {"moved": "moved to To Be Deleted", "kept": "kept as it was", "skipped": "not now",
       "not_done": "not done"}                     # one locked file, in a sentence


def folder_for(target):
    """Where a new receipt about `target` goes (the home, or the old subfolder)."""
    return records.receipts_folder(target)


def now():
    return datetime.now().isoformat(timespec="seconds")


def _free_stem(where, stamp):
    """receipt_<stamp>, or receipt_<stamp>_2... if that name is taken: never overwrites."""
    stem, n = "receipt_" + stamp, 2
    while (where / (stem + ".json")).exists() or (where / (stem + ".txt")).exists():
        stem, n = "receipt_" + stamp + "_" + str(n), n + 1
    return stem


def save(target, record):
    """Write both files. Returns the .txt path."""
    where = folder_for(target)
    where.mkdir(exist_ok=True)
    record = dict(record, folder=str(record.get("folder") or target))   # which folder it is about
    stem = _free_stem(where, record["made"].replace(":", "").replace("-", ""))
    with open(where / (stem + ".json"), "x", encoding="utf-8") as out:
        out.write(json.dumps(record, indent=1))
    text = where / (stem + ".txt")
    with open(text, "x", encoding="utf-8") as out:
        out.write(plain(record))
    return text


def _belongs(place, record, target):
    """Old subfolder: every receipt in it is about that folder. The home: only if it says so."""
    if place.name == records.OLD_RECEIPTS and place.parent == Path(target):
        return True
    return records.same_folder(record.get("folder"), target)


def all_records(target):
    """(path, record) for every receipt about `target`, old place and home, oldest first."""
    found = []
    for place in records.receipt_places(target):
        for path in sorted(place.glob("receipt_*.json")):
            record = json.loads(path.read_text(encoding="utf-8"))
            if _belongs(place, record, target):
                found.append((path, record))
    return sorted(found, key=lambda pair: str(pair[1].get("made") or ""))


def latest_open(target):
    """The newest receipt that has not been undone, or (None, None)."""
    for path, record in reversed(all_records(target)):
        if not record.get("undone"):
            return path, record
    return None, None


def mark_undone(path, record, steps):
    record["undone"] = {"time": now(), "steps": steps}
    path.write_text(json.dumps(record, indent=1), encoding="utf-8")
    text = path.with_suffix(".txt")
    if text.exists():
        with text.open("a", encoding="utf-8") as out:
            out.write("\nUNDONE " + record["undone"]["time"].replace("T", " ")
                      + ": every change above that could be put back was put back.\n")


def _month(day):
    try:
        return datetime.strptime(day, "%Y-%m-%d").strftime("%b %Y")
    except (TypeError, ValueError):
        return "date unknown"


def plain(record):
    models = record.get("models") or {}
    lines = ["Shyft receipt · " + record["made"].replace("T", " "),
             "Run " + str(record["run_id"]) + ". Zippy: " + str(models.get("zippy", "unknown"))
             + " · Pip: " + str(models.get("pip", "unknown")) + ".",
             "Every model call in that run went to " + str(models.get("address", "this computer")) + ".",
             "This step made no network calls. Nothing was deleted.", ""]
    steps = record["steps"]
    open_steps = [s for s in steps if s["state"] != "locked"]
    for outcome in ("renamed", "moved", "kept", "skipped", "not_done"):
        group = [s for s in open_steps if s["outcome"] == outcome]
        if not group:
            continue
        lines.append(WORDS[outcome] + " (" + str(len(group)) + "):")
        for s in group:
            if outcome == "renamed":
                lines.append("  " + s["from_name"] + "  ->  " + s["to_name"])
                if s.get("reason"):
                    lines.append("      " + s["reason"])
            elif outcome == "not_done":
                lines.append("  " + s["from_name"] + ": " + s["note"])
            else:
                lines.append("  " + s["from_name"] + (" (" + s["note"] + ")" if s.get("note") else ""))
        lines.append("")
    locked = [s for s in steps if s["state"] == "locked"]
    if locked:
        lines.append("Locked by Zippy (" + str(len(locked)) + "), sealed: kind and month only:")
        for s in locked:
            kind = (s.get("kind") or "locked").replace("_", " ")
            lines.append("  " + kind + ", " + _month(s.get("file_date")) + ": "
                         + ONE.get(s["outcome"], s["outcome"]))
        lines.append("")
    lines.append("To undo this run:  python3 apply.py undo")
    return "\n".join(lines) + "\n"
