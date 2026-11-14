# eval/gate_report.py — Lane: Sphinx. Zippy's own numbers, apart from Pip's (S8).
#   recall:       of the screenshots that ARE sensitive, how many Zippy locked
#   false alarms: of the ordinary ones, how many Zippy locked anyway
#   by kind:      which menu choice it made, so we see WHAT it misses
# The bar was set before the first gated run (Nov 14): >= 80% recall, <= 10% false alarms.

import csv
from collections import Counter

from harness import schema, gate

RECALL_BAR = 80
FALSE_ALARM_BAR = 10


def _notes():
    with schema.GOLDEN.open(newline="", encoding="utf-8-sig") as sheet:
        return {row["file"].strip(): (row.get("note") or "").strip()
                for row in csv.DictReader(sheet) if row.get("file")}


def _pct(part, whole):
    return round(100 * part / whole) if whole else 0


def _avg(values):
    values = [v for v in values if isinstance(v, (int, float))]
    return str(round(sum(values) / len(values), 2)) if values else "n/a"


def build(results, answers):
    gated = {n: r for n, r in results.items() if n in answers and r.get("gate") is not None}
    if not gated:
        return []                                  # a run from before Zippy existed
    sensitive = [n for n in gated if answers[n] == "sensitive"]
    ordinary = [n for n in gated if answers[n] != "sensitive"]
    caught = [n for n in sensitive if gate.is_locked(gated[n]["gate"])]
    alarms = [n for n in ordinary if gate.is_locked(gated[n]["gate"])]
    recall, alarm_rate = _pct(len(caught), len(sensitive)), _pct(len(alarms), len(ordinary))

    lines = ["ZIPPY (the sensitivity gate: looks first, answers by kind)"]
    if sensitive:
        lines.append("  Sensitive recall:  " + str(len(caught)) + "/" + str(len(sensitive))
                     + " = " + str(recall) + "%   (bar: " + str(RECALL_BAR) + "% or more)")
    lines.append("  False alarms:      " + str(len(alarms)) + "/" + str(len(ordinary))
                 + " = " + str(alarm_rate) + "%   ordinary screenshots locked (bar: "
                 + str(FALSE_ALARM_BAR) + "% or less)")
    meets = (not sensitive or recall >= RECALL_BAR) and alarm_rate <= FALSE_ALARM_BAR
    lines.append("  Verdict: " + ("MEETS the bar on this set." if meets else "BELOW the bar on this set."))

    errors = [n for n in gated if gated[n]["gate"].get("kind") == gate.GATE_ERROR]
    if errors:
        lines.append("  Locked because Zippy's answer was broken (fail closed): " + str(len(errors)))
    right = [gated[n]["gate"].get("confidence") for n in caught]
    right += [gated[n]["gate"].get("confidence") for n in ordinary if n not in alarms]
    wrong = [gated[n]["gate"].get("confidence") for n in gated if n not in caught
             and (n in sensitive or n in alarms)]
    lines.append("  Zippy's confidence when right " + _avg(right) + ", when wrong " + _avg(wrong))
    lines.append("")

    missed = [n for n in sensitive if n not in caught]
    if missed:
        backed = [n for n in missed if results[n].get("pip_action") == "sensitive"]
        lines.append("  Zippy MISSED " + str(len(missed)) + ". Pip caught " + str(len(backed))
                     + " of those (the second net). Still missed by both:")
        notes = _notes()
        lines += ["    " + n + "   (" + notes.get(n, "") + ")" for n in missed if n not in backed]
        lines.append("")

    lines.append("  Kinds Zippy chose for the screenshots that ARE sensitive:")
    lines.append("    " + ", ".join(k + " " + str(c) for k, c in
                                    Counter(gated[n]["gate"]["kind"] for n in sensitive).most_common()))
    if alarms:
        notes = _notes()
        lines.append("  False alarms (your label -> Zippy's kind):")
        lines += ["    " + answers[n] + " -> " + gated[n]["gate"]["kind"] + "   " + n
                  + "   (" + notes.get(n, "") + ")" for n in alarms]
    return lines + [""]
