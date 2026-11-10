# harness/naming.py — Lane: Sphinx (rename measurement), Build Arc step 1.4
# Renaming is not an action. It happens IN ADDITION to keeping a screenshot.
# The model always suggests a name; OUR CODE decides whether the file needs one.

import re

from harness import schema

# Words that camera, phone and OS tools put in default file names.
# Once these, numbers and punctuation are removed, nothing meaningful is left.
DEFAULT_NAME_WORDS = {
    "screenshot", "screenshots", "screen", "shot", "capture", "snip", "snapshot",
    "img", "image", "photo", "pic", "picture", "scan", "untitled", "unnamed",
    "download", "file", "copy", "at", "am", "pm",
}

MAX_NAME_WORDS = 6
MAX_NAME_CHARS = 60


def is_meaningless(file_name):
    """True if a file name says nothing about what the screenshot shows.
    'Screenshot 2026-11-10 085400.png' -> True. 'pasta-recipe.png' -> False."""
    stem = file_name.rsplit(".", 1)[0].lower()
    words = re.findall(r"[a-z]+", stem)
    meaningful = [w for w in words if w not in DEFAULT_NAME_WORDS and len(w) >= 3]
    return not meaningful


def clean_name(suggested):
    """Turn the model's suggestion into a safe file name stem, or "" if unusable.
    Lowercase, words joined by hyphens, no long numbers (dates), at most 6 words."""
    if not isinstance(suggested, str):
        return ""
    stem = suggested.rsplit(".", 1)[0] if suggested.lower().endswith(tuple(schema.IMAGE_TYPES)) else suggested
    words = re.findall(r"[a-z0-9]+", stem.lower())
    words = [w for w in words if not (w.isdigit() and len(w) >= 4)]
    name = "-".join(words[:MAX_NAME_WORDS])[:MAX_NAME_CHARS].strip("-")
    if is_meaningless(name):
        return ""
    return name


def needs_rename(proposal, file_name):
    """True if this screenshot is being kept and its current name says nothing."""
    if not proposal or proposal.get("action") not in schema.ACTIONS_THAT_KEEP:
        return False
    return is_meaningless(file_name)


def rename_for(proposal, file_name):
    """Return the cleaned new name to show the person, or "" if no rename applies.
    Sensitive screenshots are never renamed: a name could reveal what they contain."""
    if not needs_rename(proposal, file_name):
        return ""
    return clean_name(proposal.get("new_name"))


def rename_problem(proposal, file_name):
    """Return a code-check problem string, or None."""
    if needs_rename(proposal, file_name) and not rename_for(proposal, file_name):
        return "kept screenshot has a meaningless name but no usable new name"
    return None
