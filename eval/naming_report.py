# eval/naming_report.py — Lane: Sphinx (rename measurement), Build Arc step 1.4
# Measures the non-negotiable feature: does every kept screenshot with a
# meaningless name get a usable new name? No extra labelling needed: your
# expected_action in golden.csv plus the file name are enough.
# S8: in a gated run a name only counts if our code would APPLY it (D18: Zippy said
# "none"). Runs from before Zippy are scored the old way, so old reports still read.

from harness import schema, naming


def _applied(result, file_name):
    if result.get("gate") is None:                 # run from before Zippy existed
        return naming.rename_for(result, file_name)
    return naming.gated_rename(result, file_name, result["gate"])


TARGET = 80   # Build Arc step 1.4: done when coverage is at least 80%


def build(results, answers):
    """Return the naming section of the score report as a list of lines."""
    should_rename = [name for name, expected in answers.items()
                     if name in results
                     and expected in schema.ACTIONS_THAT_KEEP
                     and naming.is_meaningless(name)]
    lines = ["RENAME (the feature we will not ship without)"]
    if not should_rename:
        lines.append("  No kept screenshots with meaningless names in this set. Add some.")
        return lines + [""]

    named, missing = [], []
    for name in should_rename:
        suggestion = _applied(results[name], name)
        (named if suggestion else missing).append((name, suggestion))

    rate = round(100 * len(named) / len(should_rename))
    verdict = "meets" if rate >= TARGET else "below"
    lines.append("  Coverage: " + str(len(named)) + "/" + str(len(should_rename))
                 + " = " + str(rate) + "%  (" + verdict + " the " + str(TARGET) + "% target)")
    lines.append("  Of the screenshots you'd keep that have meaningless names, how many got a usable name.")
    lines.append("")
    lines.append("  Read these. Would you keep each name? (Quality is judged by a person for now.)")
    for name, suggestion in named:
        lines.append("    " + suggestion + "   <-  " + name)
    for name, _ in missing:
        reason = "locked by Zippy" if results[name].get("pip_action") is None else "no usable name"
        lines.append("    (" + reason + ")   <-  " + name)

    leaks = [n for n, expected in answers.items()
             if expected == "sensitive" and n in results and _applied(results[n], n)]
    if leaks:
        lines.append("")
        lines.append("  PRIVACY: our code WOULD rename " + str(len(leaks)) + " sensitive screenshot(s).")
        lines.append("  " + ("Zippy cleared them, so the gated rename let the name through:"
                             if results[leaks[0]].get("gate") is not None else
                             "The never-rename rule trusted Pip's action (before Zippy):"))
        lines += ["    " + _applied(results[n], n) + "   <-  " + n for n in leaks]
    return lines + [""]
