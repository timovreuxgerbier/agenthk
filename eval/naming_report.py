# eval/naming_report.py — Lane: Sphinx (rename measurement), Build Arc step 1.4
# Measures the non-negotiable feature: does every kept screenshot with a
# meaningless name get a usable new name? No extra labelling needed: your
# expected_action in golden.csv plus the file name are enough.

from harness import schema, naming

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
        suggestion = naming.clean_name(results[name].get("new_name"))
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
        lines.append("    (no usable name)   <-  " + name)

    leaks = [name for name, expected in answers.items()
             if expected == "sensitive" and name in results
             and naming.clean_name(results[name].get("new_name"))]
    if leaks:
        lines.append("")
        lines.append("  WARNING: the model named " + str(len(leaks)) + " sensitive screenshot(s).")
        lines.append("  Our code never applies those names, but the model ignored the rule:")
        lines += ["    " + name for name in leaks]
    return lines + [""]
