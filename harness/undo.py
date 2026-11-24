# harness/undo.py — Lane: Sphinx. Undo the LAST applied run, from its receipt.
# Puts every renamed or moved file back where it was, newest step first.
# Never overwrites: if something else now has a file's old name, that file is
# left where it is and the undo receipt says so.

import os
from pathlib import Path

from harness import ids, receipt


def undo_last(folder):
    """Returns (list of plain-language lines, receipt path) or (None, None) if nothing to undo."""
    path, record = receipt.latest_open(folder)
    if record is None:
        return None, None
    lines, steps = [], []
    for step in reversed(record["steps"]):
        if step["outcome"] not in ("renamed", "moved"):
            continue
        now_at, back_to = Path(step["to_path"]), Path(step["from_path"])
        shown = step["from_name"] if step["state"] != "locked" else "a locked file"
        if not now_at.exists() or ids.file_hash(now_at) != step["hash"]:
            lines.append("Left alone: " + shown + " (it was moved or changed after the run).")
            steps.append({"id": step["id"], "result": "left_alone"})
            continue
        if back_to.exists():
            lines.append("Left alone: " + shown + " (another file now has its old name).")
            steps.append({"id": step["id"], "result": "left_alone"})
            continue
        os.rename(now_at, back_to)
        ok = back_to.exists() and not now_at.exists()
        lines.append(("Put back: " if ok else "Check by hand: ") + shown)
        steps.append({"id": step["id"], "result": "restored" if ok else "check"})
    receipt.mark_undone(path, record, steps)
    if not lines:
        lines.append("That run changed no files, so there was nothing to put back.")
    return lines, path
