# harness/execute.py — Lane: Sphinx. The step after review: a person's decisions
# become real changes, one file at a time, each checked and recorded.
#
# Rules (contract v0.2, D18, "nothing deletes"):
# - Only what a person decided happens. No entry or "skip" = nothing.
# - The id is the safety check: if the file's bytes or place changed since review,
#   its id no longer matches and the step is refused.
# - Locked files are never renamed and never get keep_text. They may only be kept
#   as they are or moved to "To Be Deleted".
# - Nothing is overwritten and nothing is deleted. "To Be Deleted" is a folder.
# - Every change is checked afterwards (result check) and goes in the receipt.

import os

from harness import ids, naming, receipt

BIN = "To Be Deleted"
KEEP = ("keep_image", "keep_text")


class Refused(Exception):
    """The whole decisions file is refused; nothing was changed."""


def free_path(folder, stem, suffix):
    """A path in folder that does not exist yet: stem.png, stem-2.png, stem-3.png ..."""
    candidate = folder / (stem + suffix)
    number = 2
    while candidate.exists():
        candidate = folder / (stem + "-" + str(number) + suffix)
        number += 1
    return candidate


def check_files(review, decisions):
    if review.get("contract") != "0.2" or decisions.get("contract") != "0.2":
        raise Refused("This needs review contract 0.2 on both sides.")
    if review.get("run_id") != decisions.get("run_id"):
        raise Refused("These decisions are for run " + str(decisions.get("run_id"))
                      + ", but the review on disk is for run " + str(review.get("run_id")) + ".")


def plan(item, decision):
    """What should happen: ('skip'|'keep'|'rename'|'move'|'refuse', new stem, note)."""
    action = decision.get("action")
    if decision.get("decision") == "skip" or not action:
        return "skip", None, ""
    if action == "to_be_deleted":
        return "move", None, ""
    if action not in KEEP:
        return "refuse", None, "unknown action " + str(action)
    if item["state"] == "locked":
        if action == "keep_text":
            return "refuse", None, "a locked file is never read for its text"
        return "keep", None, "locked, left untouched"
    note = "text not saved yet (later version)" if action == "keep_text" else ""
    if item["state"] != "open":
        return "keep", None, note
    stem = naming.clean_name(decision.get("new_name"))
    if not stem:
        return "keep", None, note
    return "rename", stem, note


def do_one(folder, root, item, decision):
    """Carry out one decision. Returns one receipt step."""
    source = folder / item["file"]
    step = {"id": item["id"], "state": item["state"], "kind": item.get("kind"),
            "file_date": item.get("file_date"), "decision": decision.get("decision"),
            "action": decision.get("action"), "from_name": item["file"], "to_name": None,
            "from_path": str(source), "to_path": None, "hash": None, "note": "",
            "reason": item.get("reason") if item["state"] == "open" else None}   # Pip's words
    what, stem, note = plan(item, decision)
    step["note"] = note
    if what == "skip":
        step["outcome"] = "skipped"
        return step
    if what == "refuse":
        step["outcome"] = "not_done"
        return step
    if not source.exists() or ids.stable_id(source, root) != item["id"]:
        step.update(outcome="not_done", note="the file is missing or changed since review")
        return step
    if what == "keep":
        step["outcome"] = "kept"
        return step
    before = ids.file_hash(source)
    if what == "move":
        (folder / BIN).mkdir(exist_ok=True)
        target = free_path(folder / BIN, source.stem, source.suffix)
    else:
        target = free_path(folder, stem, source.suffix)
    os.rename(source, target)
    ok = target.exists() and not source.exists() and ids.file_hash(target) == before
    step.update(to_name=target.name, to_path=str(target), hash=before,
                outcome=("moved" if what == "move" else "renamed") if ok else "not_done")
    if not ok:
        step["note"] = "the result check failed after the change; see the file by hand"
    return step


def apply(folder, root, review, decisions, models=None):
    """Apply a decisions file to folder. Returns (receipt .txt path, steps)."""
    check_files(review, decisions)
    items = {item["id"]: item for item in review["items"]}
    unknown = [d.get("id") for d in decisions["decisions"] if d.get("id") not in items]
    if unknown:
        raise Refused(str(len(unknown)) + " decision(s) are for items not in this review.")
    steps, seen = [], set()
    for decision in decisions["decisions"]:
        if decision["id"] in seen:
            continue
        seen.add(decision["id"])
        steps.append(do_one(folder, root, items[decision["id"]], decision))
    record = {"receipt": "1", "made": receipt.now(), "run_id": review["run_id"],
              "folder": str(folder), "models": models or review.get("models"),
              "steps": steps, "undone": None}
    return receipt.save(folder, record), steps
