# eval/score.py — Lane: Sphinx (golden set)
# Compares one run against YOUR answers in golden/golden.csv (read by eval/golden.py).
#   python3 run.py score                 grade the latest run
#   python3 run.py score 20261114-132418 grade that run (re-score an old run after relabelling)
# First run: creates golden.csv listing every screenshot, for you to fill in.
# S8: in a gated run, "action" is the PIPELINE's answer (Zippy's lock wins, else Pip);
# "pip_action" is Pip's own answer, None when Zippy locked the screenshot first.
# S9: every report is also saved as golden/score_<set>_<run>.txt, so no number is lost
# to the next run overwriting score_report.txt.
# S10: the header names both models when Zippy runs on its own; TIME = seconds per screenshot.

import json
from collections import Counter

from harness import schema, trace, gate
from eval import gate_report, golden, naming_report, recall

ACTIVE_SET = schema.ROOT / "golden" / "active_set.txt"


def make_template():
    schema.GOLDEN.parent.mkdir(exist_ok=True)
    schema.SCREENSHOTS.mkdir(exist_ok=True)
    files = sorted(p.name for p in schema.SCREENSHOTS.iterdir()
                   if p.suffix.lower() in schema.IMAGE_TYPES)
    golden.write({name: {"file": name} for name in files})
    print("Created golden/golden.csv with " + str(len(files)) + " screenshots.")
    print("Easiest: python3 dev/label.py (disposition), then python3 dev/label_kind.py (sensitive kind).")
    print("Or fill it in by hand: expected_action = " + ", ".join(golden.DISPOSITIONS)
          + "; sensitive_kind = " + ", ".join(schema.GATE_KINDS))
    print("Decide BEFORE you look at what the agent said. Then save and run the score again.")


def results_for(run_id=None):
    run_id, entries = trace.run(run_id) if run_id else trace.latest_run()
    results = {}
    for entry in entries:
        try:
            answer = json.loads(entry["raw_output"])
        except (json.JSONDecodeError, TypeError):
            answer = {}
        verdict = entry.get("gate")
        locked = gate.is_locked(verdict)
        results[entry["file"]] = {
            "action": "sensitive" if locked else answer.get("action", "INVALID"),
            "pip_action": None if locked else answer.get("action", "INVALID"),
            "gate": verdict,
            "confidence": answer.get("confidence"),
            "reason": answer.get("reason", ""),
            "new_name": answer.get("new_name", ""),
            "model": entry.get("model", "?"),
            "zippy_model": entry.get("zippy_model") or entry.get("model", "?"),
            "seconds": entry.get("seconds"),
            "zippy_seconds": entry.get("zippy_seconds"),
        }
    return run_id, results


def build_report(run_id, results, labels):
    answers = golden.answers(labels)
    lines, passed, scored, not_run = [], 0, 0, 0
    misses = Counter()
    right_conf, wrong_conf = [], []
    for name, expected in answers.items():
        if name not in results:
            not_run += 1
            continue
        got = results[name]
        scored += 1
        conf = got["confidence"] if isinstance(got["confidence"], (int, float)) else None
        if got["action"] == expected:
            passed += 1
            if conf is not None:
                right_conf.append(conf)
            continue
        misses[expected + " -> " + got["action"]] += 1
        if conf is not None:
            wrong_conf.append(conf)
        lines.append("MISS      " + name + "\n          you: " + expected
                     + " | agent: " + got["action"] + " (" + str(conf) + ")"
                     + "\n          reason: " + got["reason"])
    if scored == 0:
        return None

    models = [r["model"] for r in results.values() if not r["model"].startswith("code:")]
    model = Counter(models).most_common(1)[0][0] if models else "code only"
    gated = any(r.get("gate") is not None for r in results.values())
    zippies = [r["zippy_model"] for r in results.values()
               if r.get("gate") is not None and not str(r["zippy_model"]).startswith("code:")]
    zippy = Counter(zippies).most_common(1)[0][0] if zippies else model
    who = "model " + model if zippy == model else "Zippy " + zippy + ", Pip " + model
    out = ["Run " + str(run_id) + "  " + who
           + ("  (Zippy gate, then Pip: scores are the whole pipeline)" if gated else "  (Pip alone)"),
           "PASS RATE: " + str(passed) + "/" + str(scored) + " = "
           + str(round(100 * passed / scored)) + "%"]
    secs = [r["seconds"] for r in results.values() if isinstance(r.get("seconds"), (int, float))]
    zips = [r["zippy_seconds"] for r in results.values() if isinstance(r.get("zippy_seconds"), (int, float))]
    if secs:
        out.append("TIME: " + str(round(sum(secs) / len(secs), 1)) + " s per screenshot"
                   + (" (Zippy " + str(round(sum(zips) / len(zips), 1)) + " s of it)" if zips else ""))
    out.append("")
    if misses:
        out.append("Most common mistakes (you -> agent):")
        out += ["  " + str(c) + "x  " + p for p, c in misses.most_common()]
        out.append("")
    if right_conf:
        out.append("Average confidence when RIGHT: " + str(round(sum(right_conf) / len(right_conf), 2)))
    if wrong_conf:
        out.append("Average confidence when WRONG: " + str(round(sum(wrong_conf) / len(wrong_conf), 2)))
    out.append("(If those two numbers are close, the confidence score is not telling you anything.)")
    out.append("")
    if not_run:
        out += [str(not_run) + " labelled screenshot(s) were not in this run (cap or newest-first).", ""]
    out += gate_report.build(results, labels)
    out += recall.build(results, answers)
    out += naming_report.build(results, answers)
    return "\n".join(out + lines)


def save(report, run_id):
    schema.SCORE_REPORT.write_text(report + "\n", encoding="utf-8")
    set_name = ACTIVE_SET.read_text(encoding="utf-8").strip() if ACTIVE_SET.exists() else "real"
    keep = schema.SCORE_REPORT.with_name("score_" + set_name + "_" + str(run_id) + ".txt")
    keep.write_text(report + "\n", encoding="utf-8")
    print("\nSaved to golden/score_report.txt and golden/" + keep.name)


def main(run_id=None):
    if not schema.GOLDEN.exists():
        make_template()
        return
    labels, problems = golden.read()
    for problem in problems:
        print("Skipped  " + problem)
    run_id, results = results_for(run_id)
    if not results:
        print("No agent run found" + (" with id " + str(run_id) if run_id else "")
              + ". Run  python3 run.py  first.")
        return
    report = build_report(run_id, results, labels)
    if report is None:
        print("None of the labelled files were in this run. Is the right set loaded? (python3 dev/use_set.py)")
        return
    print(report)
    save(report, run_id)
