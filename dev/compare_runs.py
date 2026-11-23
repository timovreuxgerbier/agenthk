# dev/compare_runs.py — did two runs give the SAME answers, file by file? DEV ONLY. S14.
#
#   python3 dev/compare_runs.py OLD_RUN_ID NEW_RUN_ID
#   python3 dev/compare_runs.py OLD_RUN_ID latest     the newest run in trace.jsonl
#
# The S14 regression check (rule agreed before any run): batching must not change what
# the buddies decide. For every screenshot in both runs it compares three things:
#   1. Zippy's kind   2. Pip's action   3. Pip's proposed name
# 0 differences = PASS. Any difference = not yet a pass: rerun that set --one-by-one; if
# the old order shows the same difference, it is the machine, not batching.
# It also counts, for information only (not part of the rule), files whose confidence
# numbers or full answer text changed.
# SAFE ON THE MAC SET: prints row numbers and field names, never file names or names.
# Lesson 13 (Nov 22): warns first when the two runs' server settings differ or were not
# recorded (D28), so a difference caused by the server is not blamed on the change.

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from harness import trace  # noqa: E402
from eval import server  # noqa: E402

RULE_FIELDS = ("kind", "action", "name")


def answers(entry):
    """The three decisions, plus the information-only extras, from one trace line."""
    try:
        said = json.loads(entry.get("raw_output") or "")
    except (json.JSONDecodeError, TypeError):
        said = {}
    said = said if isinstance(said, dict) else {}
    verdict = entry.get("gate") or {}
    return {"kind": verdict.get("kind"), "action": said.get("action"),
            "name": said.get("new_name"),
            "zippy_confidence": verdict.get("confidence"),
            "pip_confidence": said.get("confidence"),
            "text": entry.get("raw_output")}


def by_file(run_id):
    _, entries = trace.run(run_id)
    return {e["file"]: answers(e) for e in entries}


def compare(old, new):
    """Return (rule_differences, info_counts, only_old, only_new). Rows are numbered by
    the old run's alphabetical file order, so the same row is the same file every time."""
    files = sorted(set(old) & set(new))
    rule, info = [], {"zippy_confidence": 0, "pip_confidence": 0, "text": 0}
    for row, file in enumerate(files, start=1):
        for field in RULE_FIELDS:
            if old[file][field] != new[file][field]:
                rule.append((row, field, old[file], new[file]))
        for field in info:
            if old[file][field] != new[file][field]:
                info[field] += 1
    return rule, info, len(set(old) - set(new)), len(set(new) - set(old))


def describe(row, field, before, after):
    if field == "name":
        return "  row " + str(row) + ": Pip's proposed name changed (not shown)"
    return ("  row " + str(row) + ": " + field + " " + str(before[field]) + " -> "
            + str(after[field]))


def main():
    if len(sys.argv) != 3:
        sys.exit("Write two run ids: python3 dev/compare_runs.py OLD_RUN_ID NEW_RUN_ID")
    old_id, new_id = sys.argv[1], sys.argv[2]
    if new_id == "latest":
        new_id = trace.latest_run()[0]
    old, new = by_file(old_id), by_file(new_id)
    for run_id, found in ((old_id, old), (new_id, new)):
        if not found:
            sys.exit("No run with id " + run_id + " in trace.jsonl.")
    rule, info, only_old, only_new = compare(old, new)
    shared = len(set(old) & set(new))
    print("COMPARE  old " + old_id + "  ->  new " + new_id)
    unlike = server.differences(trace.run(old_id)[1], trace.run(new_id)[1])
    if unlike:
        print("WARNING: the server settings are not shown to be the same (D28). A difference")
        print("below may come from the server, not from what you changed:")
        for problem in unlike:
            print("  " + problem)
    print("Screenshots in both runs: " + str(shared)
          + "   only in old: " + str(only_old) + "   only in new: " + str(only_new))
    if only_old or only_new:
        print("WARNING: the runs did not cover the same files (another set loaded, or a stop).")
    print("\nTHE RULE (kind, action, proposed name):")
    if rule:
        print("  " + str(len(rule)) + " difference(s): NOT a pass yet.")
        for difference in rule:
            print(describe(*difference))
    else:
        print("  0 differences: PASS" + ("" if not (only_old or only_new) else
                                         " on the shared files only"))
    print("\nFor information (not part of the rule): files whose")
    print("  Zippy confidence changed: " + str(info["zippy_confidence"]))
    print("  Pip confidence changed:   " + str(info["pip_confidence"]))
    print("  full answer text changed: " + str(info["text"]))


if __name__ == "__main__":
    main()
