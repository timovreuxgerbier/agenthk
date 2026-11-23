# dev/make_review.py — turn one real run into the review page's data. DEV ONLY.
#
#   python3 dev/make_review.py                   latest run, first 12 screenshots
#   python3 dev/make_review.py 20261116-182753   that run, first 12
#   python3 dev/make_review.py 20261116-182753 20
#
# Reads trace.jsonl (what Zippy and Pip actually answered) and writes ui/review_data.js
# in the shape of docs/review_contract.md v0.2, so Ana's page shows a REAL run.
# It is a .js file (not .json) so the page works when opened by double-click.
# SAFETY: refuses unless the synthetic set is loaded. Real screenshots never go on a page.
import hashlib
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from harness import naming, schema       # noqa: E402

ACTIVE = ROOT / "golden" / "active_set.txt"
OUT = ROOT / "ui" / "review_data.js"
DEFAULT_COUNT = 12


def stop(message):
    sys.exit("Stopped, nothing written: " + message)


def loaded_set():
    return ACTIVE.read_text(encoding="utf-8").strip() if ACTIVE.exists() else "real"


def run_rows(run_id):
    rows = [json.loads(line) for line in schema.TRACE.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        stop("trace.jsonl is empty.")
    run_id = run_id or rows[-1].get("run_id")
    picked = [r for r in rows if r.get("run_id") == run_id]
    if not picked:
        stop("no run called " + run_id + " in trace.jsonl.")
    return run_id, picked


def stable_id(path):
    """Same file in the same place = same id in every run (contract v0.2)."""
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashlib.sha256((str(path.relative_to(ROOT)) + digest).encode()).hexdigest()[:12]


def pip_answer(row):
    try:
        answer = json.loads(row.get("raw_output") or "")
        return answer if isinstance(answer, dict) else {}
    except ValueError:
        return {}


def item(row):
    file = row["file"]
    path = schema.SCREENSHOTS / file
    if not path.exists():
        stop(file + " is not in screenshots/. Load the set this run used.")
    gate = row.get("gate") or {}
    kind = gate.get("kind")
    answer = pip_answer(row)
    base = {"id": stable_id(path), "file": file,
            "file_date": date.fromtimestamp(path.stat().st_mtime).isoformat(),
            "kind": "none", "action": None, "new_name": None, "reason": None,
            "why_saved": None, "confidence": None, "needs_ok": False, "copy_of": None}
    if kind not in schema.GATE_KINDS and kind != schema.GATE_CLEAR:
        base.update(state="locked", kind="gate_error", needs_ok=True)          # broken answer: locked
    elif kind != schema.GATE_CLEAR:
        base.update(state="locked", kind=kind, confidence=gate.get("confidence"), needs_ok=True)
    elif not row.get("pip_usage") and str(answer.get("reason", "")).startswith("Exact copy of"):
        original = answer["reason"][len("Exact copy of"):].strip().rstrip(".")
        base.update(state="copy", action="to_be_deleted", confidence=1.0, copy_of=original)
    else:
        action = answer.get("action")
        confidence = answer.get("confidence")
        unsure = (row.get("flagged") or row.get("check_problems")
                  or not isinstance(confidence, (int, float)) or confidence < schema.CONFIDENCE_FLOOR)
        if action not in ("keep_image", "keep_text", "to_be_deleted"):
            action, unsure = "keep_image", True                                  # odd answer: ask
        base.update(state="open", action=action, reason=answer.get("reason"),
                    why_saved=answer.get("why_saved_guess"), confidence=confidence,
                    needs_ok=bool(unsure),
                    new_name=naming.gated_rename(answer, file, gate) or None)    # D18: what code applies
    return base


def main():
    if loaded_set() != "synthetic":
        stop("the loaded set is '" + loaded_set() + "'. Run: python3 dev/use_set.py synthetic")
    run_id = sys.argv[1] if len(sys.argv) > 1 else None
    count = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_COUNT
    run_id, rows = run_rows(run_id)
    items = [item(r) for r in rows[:count]]
    states = [i["state"] for i in items]
    review = {"contract": "0.2", "run_id": run_id, "made": rows[0].get("time"),
              "counts": {"total": len(items), "open": states.count("open"),
                         "locked": states.count("locked"), "copies": states.count("copy")},
              "items": items}
    # The page shows the image only for open items, and for locked ones only after "Show me".
    previews = {i["id"]: {"img": "../screenshots/" + i["file"], "label": i["file"]} for i in items}
    models = (rows[0].get("zippy_model") or rows[0].get("model")) + " / " + rows[0].get("model", "")
    OUT.write_text(
        "// review_data.js — WRITTEN BY dev/make_review.py. Do not edit by hand.\n"
        "// Real answers from run " + run_id + " (Zippy / Pip: " + models + "), synthetic screenshots.\n"
        "var REVIEW_SOURCE = \"Real run · synthetic screenshots\";\n"
        "var SAMPLE_REVIEW = " + json.dumps(review, indent=1, ensure_ascii=False) + ";\n"
        "var SAMPLE_PREVIEWS = " + json.dumps(previews, indent=1, ensure_ascii=False) + ";\n",
        encoding="utf-8")
    print("Wrote ui/review_data.js from run", run_id + ":", len(items), "items,",
          states.count("open"), "open,", states.count("locked"), "locked,", states.count("copy"), "copies.")
    print("Open ui/index.html in your browser (double-click it).")


if __name__ == "__main__":
    main()
