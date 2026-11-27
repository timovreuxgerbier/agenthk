# harness/records.py — Lane: Sphinx. S21, stage 0.3 of the home base (D41).
# Where Shyft keeps its RECORDS: the trace (what Zippy and Rick answered), the receipts
# (what was changed, for undo) and review.json (what was proposed).
#
# Rules (S21 brief, Sphinx):
# 1. New records are written inside the home (Nook), in its "Shyft's records" folder.
#    The home's place comes from home.where() only (D38: nothing else builds that path).
# 2. No home (not made, its note unreadable, or the folder isn't where Shyft made it):
#    records are written where they were before 0.3, and the run notice says so.
#    Shyft never makes the home here: only the person does (python3 -m harness.home_cli make).
# 3. Old records are read where they are. Nothing is moved, copied or deleted.
# 4. Demo copies of screenshots stay in demo/: they are copies of a person's pictures,
#    and a person's files come into the home only with approval (D41).
# Not yet: re-finding a folder that was moved or renamed (receipts keep each file's
# fingerprint, so that stays possible later).

import os
from pathlib import Path

from harness import home, home_words as words, schema

OLD_RECEIPTS = "Shyft receipts"            # before 0.3: a subfolder next to the files
OLD_REVIEW = schema.ROOT / "demo" / "review.json"
TRACE_NAME, REVIEW_NAME, RECEIPTS = "trace.jsonl", "review.json", "receipts"


def folder():
    """The records folder inside the home, or None when there is no home to use.
    Does not create anything."""
    place = home.where()
    if place is None or not place.is_dir():
        return None
    return place / words.RECORDS_FOLDER


def _ready(sub=None):
    """The records folder (or a subfolder), created inside an existing home. None: no home."""
    base = folder()
    if base is None:
        return None
    target = base / sub if sub else base
    target.mkdir(parents=True, exist_ok=True)      # the home itself already exists
    return target


# ---- The trace ----
def trace_file():
    """Where NEW trace lines go."""
    base = _ready()
    return base / TRACE_NAME if base else schema.TRACE


def trace_files():
    """Every trace file to READ: the old one in the code folder, then the home's."""
    files = [schema.TRACE]
    base = folder()
    if base is not None:
        files.append(base / TRACE_NAME)
    return [f for f in files if f.is_file()]


# ---- Receipts ----
def receipts_folder(target):
    """Where a NEW receipt about `target` (the folder whose files were changed) goes."""
    base = _ready(RECEIPTS)
    return base if base else Path(target) / OLD_RECEIPTS


def receipt_places(target):
    """Folders that may hold receipts about `target`: the old subfolder, then the home's.
    In the home, every folder's receipts sit together; receipt.py keeps only target's."""
    places = [Path(target) / OLD_RECEIPTS]
    base = folder()
    if base is not None:
        places.append(base / RECEIPTS)
    return [p for p in places if p.is_dir()]


def same_folder(a, b):
    """True if two folder addresses name the same folder (Windows ignores letter case)."""
    if not a or not b:
        return False
    return os.path.normcase(os.path.abspath(str(a))) == os.path.normcase(os.path.abspath(str(b)))


# ---- review.json ----
def review_file():
    """Where a NEW review.json goes."""
    base = _ready()
    return base / REVIEW_NAME if base else OLD_REVIEW


def review_to_read():
    """The newest review.json, in the home or (from before 0.3) in demo/. None if none."""
    base = folder()
    found = [p for p in ([base / REVIEW_NAME] if base else []) + [OLD_REVIEW] if p.is_file()]
    return max(found, key=lambda p: p.stat().st_mtime) if found else None


def where_words(old_place):
    """One short phrase for a person: where a record goes now. No paths.
    old_place: how to say where it goes when there is no home, e.g. "Shyft's code folder"."""
    return words.NAME if folder() is not None else old_place + " (no " + words.NAME + " to use)"
