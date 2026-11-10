# eval/score.py — Lane: Sphinx (golden set)
# Compares the agent's latest run against YOUR answers in golden/golden.csv.
# First run: creates golden.csv listing every screenshot, for you to fill in.
# Run it with:  python3 run.py score

import csv
import json
from collections import Counter

from harness import schema, trace


def make_template():
    schema.GOLDEN.parent.mkdir(exist_ok=True)
    schema.SCREENSHOTS.mkdir(exist_ok=True)
    files = sorted(p.name for p in schema.SCREENSHOTS.iterdir()
                   if p.suffix.lower() in schema.IMAGE_TYPES)
    with schema.GOLDEN.open("w", newline="", encoding="utf-8") as sheet:
        writer = csv.writer(sheet)
        writer.writerow(["file", "expected_action", "note"])
        for name in files:
            writer.writerow([name, "", ""])
    print("Created golden/golden.csv with " + str(len(files)) + " screenshots.")
    print("Open it, and in expected_action write ONE of:")
    print("  " + ", ".join(schema.ACTIONS))
    print("Decide BEFORE you look at what the agent said. Then save and run the score again.")


def read_golden():
    answers, problems = {}, []
    with schema.GOLDEN.open(newline="", encoding="utf-8-sig") as sheet:
        for row in csv.DictReader(sheet):
            name = (row.get("file") or "").strip()
            expected = (row.get("expected_action") or "").strip().lower()
            if not name:
                continue
            if expected not in schema.ACTIONS:
                problems.append(name + ": '" + expected + "' is blank or not an allowed action")
                continue
            answers[name] = expected
    return answers, problems


def latest_results():
    run_id, entries = trace.latest_run()
    results = {}
    for entry in entries:
        try:
            answer = json.loads(entry["raw_output"])
        except (json.JSONDecodeError, TypeError):
            answer = {}
        results[entry["file"]] = {
            "action": answer.get("action", "INVALID"),
            "confidence": answer.get("confidence"),
            "reason": answer.get("reason", ""),
            "model": entry.get("model", "?"),
        }
    return run_id, results


def build_report(run_id, results, answers):
    lines, passed, scored = [], 0, 0
    misses = Counter()
    right_conf, wrong_conf = [], []
    for name, expected in answers.items():
        if name not in results:
            lines.append("NOT RUN   " + name)
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

    model = next(iter(results.values()))["model"]
    out = ["Run " + str(run_id) + "  model " + model,
           "PASS RATE: " + str(passed) + "/" + str(scored) + " = "
           + str(round(100 * passed / scored)) + "%", ""]
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
    return "\n".join(out + lines)


def main():
    if not schema.GOLDEN.exists():
        make_template()
        return
    answers, problems = read_golden()
    for problem in problems:
        print("Skipped  " + problem)
    run_id, results = latest_results()
    if not results:
        print("No agent run found. Run  python3 run.py  first.")
        return
    report = build_report(run_id, results, answers)
    if report is None:
        print("None of the labelled files were in the latest run.")
        return
    print(report)
    schema.SCORE_REPORT.write_text(report + "\n", encoding="utf-8")
    print("\nSaved to golden/score_report.txt")
