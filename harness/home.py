# harness/home.py — Lane: Sphinx. S20, stage 0.2 of the home base (D34, D36).
# Shyft's home for a person's files ("The Waystation", working title). Today it is created
# with one note in it; Shyft's own records move in at 0.3, a person's files only with approval.
#
# where() is the ONE answer to "where is the home". Nothing else builds that path
# (Ana's app included: D38).
#
# Rules (S20, Sphinx):
# 1. Shyft proposes a visible folder in the person's user folder.
# 2. The person may choose another place at any time. The same checks apply.
# 3. Inside OneDrive: only on an explicit request, said plainly, repeated before every run.
# 4. Couldn't check: only on an explicit yes.
# 5. Never inside Shyft's own folders: its code folder, or the "Shyft" folder in the user
#    folder (the tester kit's Remove deletes that one).
# 6. Nothing is deleted or overwritten. A folder of that name Shyft didn't make is left alone.
# 7. Changing place covers an empty home only. The old folder stays where it is.
# Shyft's note of the address lives in the hidden area where programs keep their settings,
# outside the home, so the home can be found. The tester kit's Remove should delete the note
# and nothing else (S20 item 4).
#
# The person's commands are in harness/home_cli.py.

import json
import os
import sys
from pathlib import Path

from harness import home_words as words, schema, sync_check


def note_path():
    """Shyft's own note of where the home is: hidden, outside the home and the code folder."""
    base = os.environ.get("LOCALAPPDATA") if sys.platform == "win32" else None
    return (Path(base) / "Shyft" if base else Path.home() / ".shyft") / "home.json"


def proposed(user=None):
    return Path(user or Path.home()) / words.NAME


def read_note(note=None):
    """The note as a dict, None if there is none. Raises ValueError if it can't be read."""
    note = Path(note or note_path())
    if not note.exists():
        return None
    try:
        data = json.loads(note.read_text(encoding="utf-8"))
        Path(data["place"])
        return data
    except (OSError, ValueError, KeyError, TypeError) as problem:
        raise ValueError("unreadable note") from problem


def where(note=None):
    """Where the home is (a Path), or None if it hasn't been made or the note can't be read."""
    try:
        data = read_note(note)
    except ValueError:
        return None
    return Path(data["place"]) if data else None


def state(note=None, check=sync_check.check):
    """For the run notice: (state, sync result or None). Never raises."""
    try:
        data = read_note(note)
    except ValueError:
        return "unreadable", None
    if not data:
        return "none", None
    place = Path(data["place"])
    if not place.is_dir():
        return "missing", None
    return ("by_request" if data.get("synced_by_request") else "made"), check(place)


def _ours(place):
    """An empty folder, or one with only Shyft's note in it."""
    return all(item.name == words.ABOUT_FILE for item in place.iterdir())


def _problem(holder, place, user, old=None):
    """Why this place can't hold the home at all, or None. `old`: the home as it is now."""
    if not holder.is_dir():
        return words.NO_FOLDER
    if holder.parent == holder:
        return words.WHOLE_FOLDER
    for own in (schema.ROOT, Path(user) / "Shyft"):
        if sync_check.inside(place, own, os.path):
            return words.SHYFT_OWN
    if place.exists() and not place.is_dir():
        return words.NOT_A_FOLDER
    if place.is_dir() and place != old and not _ours(place):
        return words.NOT_OURS
    return None


def make(holder=None, yes_onedrive=False, yes_unchecked=False, user=None, note=None,
         check=sync_check.check):
    """Make the home inside `holder` (default: the user folder). Returns (made_or_kept, lines)."""
    user = Path(user or Path.home())
    note = Path(note or note_path())
    holder = Path(os.path.abspath(os.path.expanduser(str(holder)))) if holder else user
    place = holder / words.NAME
    try:
        before = read_note(note)
    except ValueError:
        return False, words.refused("Shyft's note of where its home is can't be read.")
    old = Path(before["place"]) if before else None
    why = _problem(holder, place, user, old)
    answer, reason = check(holder) if why is None else (None, None)
    if answer == sync_check.INSIDE and not yes_onedrive:
        why = words.INSIDE_ONEDRIVE
    elif answer == sync_check.UNKNOWN and not yes_unchecked:
        why = words.UNCHECKED.format(reason)
    if why:
        return False, words.refused(why)
    if old and old != place and old.is_dir() and not _ours(old):
        return False, words.refused(words.HAS_FILES)
    existed = place.is_dir()
    fresh = not (place / words.ABOUT_FILE).exists()
    place.mkdir(exist_ok=True)
    if fresh:
        with open(place / words.ABOUT_FILE, "x", encoding="utf-8") as about:   # never overwrites
            about.write(words.ABOUT_TEXT)
    data = {"place": str(place), "synced_by_request": answer == sync_check.INSIDE,
            "unchecked_by_request": answer == sync_check.UNKNOWN}
    if old == place and before == data:        # S20 fix: "nothing changed" only when true
        if existed and not fresh:
            return True, words.already(place)
        return True, words.remade(place, existed)
    note.parent.mkdir(parents=True, exist_ok=True)
    temp = note.with_name(note.name + ".new")
    temp.write_text(json.dumps(data, indent=1), encoding="utf-8")
    os.replace(temp, note)
    lines = words.made(place, data["synced_by_request"])
    if old and old != place:
        lines += words.moved_from(old)
    return True, lines
