# harness/prefilter.py — Lane: Raaghavi (before the model)
# Decides WHICH screenshots go to the model this run.
# Later: skip files listed in seen.json.

from harness import schema


def pick_screenshots(max_files):
    """Return up to max_files image paths from the screenshots folder, sorted by name."""
    schema.SCREENSHOTS.mkdir(exist_ok=True)
    images = sorted(
        p for p in schema.SCREENSHOTS.iterdir()
        if p.is_file() and p.suffix.lower() in schema.IMAGE_TYPES
    )
    return images[:max_files]
