# harness/receipt.py — Lane: Sphinx. Bloop's receipt (idea: Sabrina, 'Spire).
# Three jobs: RECORD what changed, let the person UNDO the last run, and PROVE
# where it ran. Two files per run, in the folder's "Shyft receipts" subfolder:
#   receipt_<time>.json  every step, for undo (our code reads it)
#   receipt_<time>.txt   the same in plain words, for the person
# Locked files are SEALED in the .txt: kind and month only, never a name.

import json
from datetime import datetime

FOLDER_NAME = "Shyft receipts"
WORDS = {"renamed": "Renamed", "moved": "Moved to To Be Deleted", "kept": "Kept as they were",
         "skipped": "Not now", "not_done": "Not done"}
ONE = {"moved": "moved to To Be Deleted", "kept": "kept as it was", "skipped": "not now",
       "not_done": "not done"}                     # one locked file, in a sentence


def folder_for(target):
    return target / FOLDER_NAME


def now():
    return datetime.now().isoformat(timespec="seconds")


def save(target, record):
    """Write both files. Returns the .txt path."""
    where = folder_for(target)
    where.mkdir(exist_ok=True)
    stamp = record["made"].replace(":", "").replace("-", "")
    (where / ("receipt_" + stamp + ".json")).write_text(json.dumps(record, indent=1), encoding="utf-8")
    text = where / ("receipt_" + stamp + ".txt")
    text.write_text(plain(record), encoding="utf-8")
    return text


def all_records(target):
    """(path, record) for every receipt, oldest first."""
    where = folder_for(target)
    if not where.exists():
        return []
    paths = sorted(where.glob("receipt_*.json"))
    return [(p, json.loads(p.read_text(encoding="utf-8"))) for p in paths]


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
