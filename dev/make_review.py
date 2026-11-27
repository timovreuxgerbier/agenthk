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
# S13: the run's screenshots are COPIED into demo/ and the page points at the copies.
# review.json is written too: apply.py acts on demo/ only, never on a test set.
# S21 (0.3): the trace is read from every place it is kept, and review.json goes into the
# home (Nook), via harness/records.py. The copies stay in demo/ (D41).
import json
import shutil
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from harness import ids, naming, records, schema, trace  # noqa: E402

ACTIVE = ROOT / "golden" / "active_set.txt"
OUT = ROOT / "ui" / "review_data.js"
DEMO = ROOT / "demo"
DEFAULT_COUNT = 12


def stop(message):
    sys.exit("Stopped, nothing written: " + message)


def loaded_set():
    return ACTIVE.read_text(encoding="utf-8").strip() if ACTIVE.exists() else "real"


def run_rows(run_id):
    rows = trace.read_all()
    if not rows:
        stop("there is no trace yet.")
    run_id = run_id or rows[-1].get("run_id")
    picked = [r for r in rows if r.get("run_id") == run_id]
    if not picked:
        stop("no run called " + run_id + " in the trace.")
    return run_id, picked


def demo_copy(file):
    """Copy one screenshot into demo/ (keeping its date). Never overwrites a different file."""
    source, copy = schema.SCREENSHOTS / file, DEMO / file
    if not source.exists():
        stop(file + " is not in screenshots/. Load the set this run used.")
    if copy.exists() and ids.file_hash(copy) != ids.file_hash(source):
        stop("demo/" + file + " exists and is different. Move demo/ to _to_delete/ to start fresh.")
    if not copy.exists():
        shutil.copy2(source, copy)
    return copy


def pip_answer(row):
    try:
        answer = json.loads(row.get("raw_output") or "")
        return answer if isinstance(answer, dict) else {}
    except ValueError:
        return {}


def item(row):
    file = row["file"]
    path = demo_copy(file)
    gate = row.get("gate") or {}
    kind = gate.get("kind")
    answer = pip_answer(row)
    base = {"id": ids.stable_id(path, ROOT), "file": file,
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
    DEMO.mkdir(exist_ok=True)
    items = [item(r) for r in rows[:count]]
    states = [i["state"] for i in items]
    review = {"contract": "0.2", "run_id": run_id, "made": rows[0].get("time"),
              "counts": {"total": len(items), "open": states.count("open"),
                         "locked": states.count("locked"), "copies": states.count("copy")},
              "items": items,
              "models": {"zippy": rows[0].get("zippy_model") or rows[0].get("model"),
                         "pip": rows[0].get("model"), "address": schema.OLLAMA_URL}}
    # The page shows the image only for open items, and for locked ones only after "Show me".
    previews = {i["id"]: {"img": "../demo/" + i["file"], "label": i["file"]} for i in items}
    models = review["models"]["zippy"] + " / " + review["models"]["pip"]
    records.review_file().write_text(json.dumps(review, indent=1, ensure_ascii=False), encoding="utf-8")
    OUT.write_text(
        "// review_data.js — WRITTEN BY dev/make_review.py. Do not edit by hand.\n"
        "// Real answers from run " + run_id + " (Zippy / Pip: " + models + "), synthetic screenshots.\n"
        "var REVIEW_SOURCE = \"Real run · synthetic screenshots\";\n"
        "var SAMPLE_REVIEW = " + json.dumps(review, indent=1, ensure_ascii=False) + ";\n"
        "var SAMPLE_PREVIEWS = " + json.dumps(previews, indent=1, ensure_ascii=False) + ";\n",
        encoding="utf-8")
    print("Wrote ui/review_data.js from run", run_id + ":", len(items), "items,",
          states.count("open"), "open,", states.count("locked"), "locked,", states.count("copy"), "copies.")
    print("Copies in demo/. review.json for apply.py is in " + records.where_words("demo/") + ".")
    print("Open ui/index.html in your browser (double-click it).")


if __name__ == "__main__":
    main()
