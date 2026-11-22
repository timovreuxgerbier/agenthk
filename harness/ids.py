# harness/ids.py — Lane: Sphinx. The item id from review contract v0.2.
# Same file (same bytes) in the same place = same id in every run.
# A renamed, moved or edited file gets a NEW id, so a decision made about the old file
# can never be applied to something else. Execute uses this as its safety check.

import hashlib


def file_hash(path):
    """sha256 of the file's bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_id(path, root):
    """12-character id from the file's place (relative to root) and its bytes."""
    place = str(path.relative_to(root))
    return hashlib.sha256((place + file_hash(path)).encode()).hexdigest()[:12]
