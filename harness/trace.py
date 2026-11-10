# harness/trace.py — Lane: Sphinx (traces + guardrails)
# Writes and reads the run record. One JSON line per screenshot per run.
# Later: redact reason / why_saved_guess for sensitive items (Arc Step 1.8).

import json
from datetime import datetime

from harness import schema


def new_run_id():
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def write(entry):
    """Append one trace line. Only the keys in schema.TRACE_FIELDS are kept."""
    line = {key: entry.get(key) for key in schema.TRACE_FIELDS}
    with schema.TRACE.open("a", encoding="utf-8") as log:
        log.write(json.dumps(line, ensure_ascii=False) + "\n")


def read_all():
    """Return every trace line as a list of dicts (empty list if no trace yet)."""
    if not schema.TRACE.exists():
        return []
    lines = schema.TRACE.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def latest_run():
    """Return (run_id, entries) for the most recent run, or (None, [])."""
    entries = read_all()
    if not entries:
        return None, []
    run_id = entries[-1]["run_id"]
    return run_id, [e for e in entries if e["run_id"] == run_id]
