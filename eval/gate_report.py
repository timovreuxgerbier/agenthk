# eval/gate_report.py — Lane: Sphinx. Zippy's own numbers, apart from Pip's (S8).
#   recall:       of the screenshots that ARE sensitive (sensitive_kind not "none"),
#                 how many Zippy locked
#   false alarms: of the ordinary ones, how many Zippy locked anyway
#   right kind:   of the ones it caught, how often it chose the kind you labelled (S9)
# The bar was set before the first gated run (Nov 14): >= 80% recall, <= 10% false alarms.

from collections import Counter

from harness import schema, gate
from eval import golden

RECALL_BAR = 80
FALSE_ALARM_BAR = 10


def _pct(part, whole):
    return round(100 * part / whole) if whole else 0


def _avg(values):
    values = [v for v in values if isinstance(v, (int, float))]
    return str(round(sum(values) / len(values), 2)) if values else "n/a"


def build(results, labels):
    gated = {n: r for n, r in results.items() if n in labels and r.get("gate") is not None}
    if not gated:
        return []                                  # a run from before Zippy existed
    sensitive = [n for n in gated if labels[n]["kind"] != schema.GATE_CLEAR]
    ordinary = [n for n in gated if labels[n]["kind"] == schema.GATE_CLEAR]
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

    known = [n for n in caught if labels[n]["kind"] != golden.UNKNOWN_KIND]
    if known:
        same = [n for n in known if gated[n]["gate"]["kind"] == labels[n]["kind"]]
        lines.append("  Right kind on the ones it caught: " + str(len(same)) + "/" + str(len(known)))
        mixed = Counter(labels[n]["kind"] + " -> " + gated[n]["gate"]["kind"] for n in known if n not in same)
        lines += ["    " + str(c) + "x  " + pair for pair, c in mixed.most_common()]
    lines.append("")

    missed = [n for n in sensitive if n not in caught]
    if missed:
        backed = [n for n in missed if results[n].get("pip_action") == "sensitive"]
        lines.append("  Zippy MISSED " + str(len(missed)) + ". Pip caught " + str(len(backed))
                     + " of those (the second net). Still missed by both:")
        lines += ["    " + labels[n]["kind"] + "   " + n + "   (" + labels[n]["note"] + ")"
                  for n in missed if n not in backed]
        lines.append("")

    lines.append("  Kinds Zippy chose for the screenshots that ARE sensitive:")
    lines.append("    " + ", ".join(k + " " + str(c) for k, c in
                                    Counter(gated[n]["gate"]["kind"] for n in sensitive).most_common()))
    if alarms:
        lines.append("  False alarms (your disposition -> Zippy's kind):")
        lines += ["    " + labels[n]["disposition"] + " -> " + gated[n]["gate"]["kind"] + "   " + n
                  + "   (" + labels[n]["note"] + ")" for n in alarms]
    return lines + [""]
