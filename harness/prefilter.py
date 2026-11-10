# harness/prefilter.py — Lane: Raaghavi (before the model)
# Decides WHICH screenshots go to the model this run.
# Later: skip files listed in seen.json.

from harness import schema


def pick_screenshots(max_files):
    """Return up to max_files image paths from the screenshots folder, newest first
    (by date modified), so a full folder never hides the latest screenshots."""
    schema.SCREENSHOTS.mkdir(exist_ok=True)
    images = sorted(
        (p for p in schema.SCREENSHOTS.iterdir()
         if p.is_file() and p.suffix.lower() in schema.IMAGE_TYPES),
        key=lambda p: (p.stat().st_mtime, p.name),
        reverse=True,
    )
    return images[:max_files]


def find_copies(batch):
    """Return {path: original file name} for screenshots in the batch that are exact
    byte-for-byte copies of an older screenshot. Copies need no model call: the model
    sees one image at a time, so it can never notice a duplicate (Nov 10 runs)."""
    import hashlib
    images = sorted(
        (p for p in schema.SCREENSHOTS.iterdir()
         if p.is_file() and p.suffix.lower() in schema.IMAGE_TYPES),
        key=lambda p: (p.stat().st_mtime, len(p.name), p.name),
    )
    first_seen, copies = {}, {}
    for path in images:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest in first_seen:
            copies[path] = first_seen[digest]
        else:
            first_seen[digest] = path.name
    return {p: copies[p] for p in batch if p in copies}
