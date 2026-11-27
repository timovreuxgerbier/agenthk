# harness/trace.py — Lane: Sphinx (traces + guardrails)
# Writes and reads the run record. One JSON line per screenshot per run.
# S8: anything judged sensitive, by Zippy OR Pip, is redacted before it is written:
# only the action and confidence survive. No description, no name, no why-saved.
# S21 (stage 0.3): new lines go into the home (harness/records.py). Old lines are read
# where they are, in the code folder's trace.jsonl. Nothing is moved or copied.

import json
from datetime import datetime

from harness import schema, gate, records


def new_run_id():
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _answer(entry):
    try:
        answer = json.loads(entry.get("raw_output") or "")
    except (json.JSONDecodeError, TypeError):
        return {}
    return answer if isinstance(answer, dict) else {}


def is_sensitive(entry):
    """True if Zippy locked it or Pip called it sensitive."""
    return gate.is_locked(entry.get("gate")) or _answer(entry).get("action") == "sensitive"


def redact(entry):
    """Return the entry as it may be stored. Sensitive items keep action + confidence only."""
    if not is_sensitive(entry):
        return entry
    kept = dict(entry)
    kept["raw_output"] = json.dumps({"action": "sensitive",
                                     "confidence": _answer(entry).get("confidence")})
    kept["check_problems"] = []
    return kept


def write(entry):
    """Append one trace line, redacted. Only the keys in schema.TRACE_FIELDS are kept."""
    safe = redact(entry)
    line = {key: safe.get(key) for key in schema.TRACE_FIELDS}
    with records.trace_file().open("a", encoding="utf-8") as log:
        log.write(json.dumps(line, ensure_ascii=False) + "\n")


def read_all():
    """Every trace line, old place and home together, as a list of dicts, oldest run first
    (empty list if no trace yet). Run ids are times, so sorting by them keeps runs in order;
    the sort is stable, so each run's own lines keep their order."""
    entries = []
    for path in records.trace_files():
        lines = path.read_text(encoding="utf-8").splitlines()
        entries += [json.loads(line) for line in lines if line.strip()]
    return sorted(entries, key=lambda e: str(e.get("run_id") or ""))


def latest_run():
    """Return (run_id, entries) for the most recent run, or (None, [])."""
    entries = read_all()
    if not entries:
        return None, []
    run_id = entries[-1]["run_id"]
    return run_id, [e for e in entries if e["run_id"] == run_id]


def run(run_id):
    """Return (run_id, entries) for one run by id, or (run_id, []) if there is no such run."""
    return run_id, [e for e in read_all() if e["run_id"] == run_id]
