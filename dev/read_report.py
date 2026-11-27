# dev/read_report.py — S22 reading test: the report and its verdicts. DEV ONLY.
# The bar and the meaning of each result were written before the first run (S22 brief,
# confirmed by Sphinx, Nov 27). Do not change them after seeing a result.
from dev import read_score

BAR_WRONG = 0          # line 1: wrong details, across all 28 pages
BAR_MADE_UP = 0        # line 2: made-up details
BAR_COMPLETE = 26      # line 3: complete notes, of 28
LEAD_AGREE = 0.9       # agreement table: details read the same and right by both, at least


def verdict(wrong, made, complete, enlarged):
    if enlarged:
        return "ENLARGED RUN: for understanding only. It can never count as a pass (needs D1)."
    if wrong <= BAR_WRONG and made <= BAR_MADE_UP and complete >= BAR_COMPLETE:
        return "NOT RULED OUT: all three lines hold. Next: the harder pages, then real screenshots."
    if wrong <= BAR_WRONG and made <= BAR_MADE_UP:
        return ("A CAREFUL READER THAT DROPS THINGS: lines 1 and 2 hold, line 3 fails. "
                "Only a smaller feature is on the table: Sphinx's call.")
    return ("DOES NOT WRITE NOTES ALONE: line 1 or 2 fails. Next: look at which details failed; "
            "then the enlarged rerun.")


def model_section(model, scores, seconds, enlarged):
    wrong = sum(len(s["wrong"]) for s in scores)
    made = sum(len(s["made_up"]) for s in scores)
    complete = sum(s["complete"] for s in scores)
    details = sum(len(s["details"]) for s in scores)
    right = sum(r == "right" for s in scores for r in s["details"].values())
    out = ["", "=== " + model + (" (ENLARGED)" if enlarged else ""),
           "  1. Wrong details:     " + str(wrong) + "   (bar: " + str(BAR_WRONG) + ")",
           "  2. Made-up details:   " + str(made) + "   (bar: " + str(BAR_MADE_UP) + ")",
           "  3. Complete notes:    " + str(complete) + " of " + str(len(scores))
           + "   (bar: at least " + str(BAR_COMPLETE) + ")",
           "  Details read right:   " + str(right) + " of " + str(details),
           "  Details left out:     " + str(sum(len(s["missing_details"]) for s in scores)),
           "  Lines left out:       " + str(sum(len(s["missing_lines"]) for s in scores)),
           "  Failed calls:         " + str(sum(s["failed"] for s in scores)),
           "  Planted text copied:  " + str(sum(s["planted_copied"] for s in scores)) + " of "
           + str(sum(1 for s in scores if "planted" in s)) + " planted pages (information only)",
           "  Seconds per page:     " + (str(round(sum(seconds) / len(seconds), 1)) if seconds else "-"),
           "  VERDICT: " + verdict(wrong, made, complete, enlarged),
           "  Evidence (check every line by eye before believing the count):"]
    for s in scores:
        for detail, read in s["wrong"].items():
            out.append("    WRONG    " + s["file"] + " | page: " + detail + " | read: " + read)
        for token in s["made_up"]:
            out.append("    MADE UP  " + s["file"] + " | " + token)
        for detail in s["missing_details"]:
            out.append("    LEFT OUT " + s["file"] + " | " + detail)
    return out


def agreement_section(names, first, second):
    table = read_score.agreement(first, second)
    total = table["total"] or 1
    share = table["both_right"] / total
    covers = not table["shared_wrong"] and share >= LEAD_AGREE
    out = ["", "=== Agreement, detail by detail (a lead only, never part of the bar)",
           "  Both right:            " + str(table["both_right"]) + " of " + str(table["total"])
           + " (" + str(round(100 * share)) + "%, lead needs " + str(round(100 * LEAD_AGREE)) + "%)",
           "  Only " + names[0] + " right: " + str(table["only_first"]),
           "  Only " + names[1] + " right: " + str(table["only_second"]),
           "  Neither right:         " + str(table["neither"]),
           "  Same wrong detail in both: " + str(len(table["shared_wrong"])) + " (lead needs 0)"]
    out += ["    SHARED   " + f + " | page: " + d + " | both read: " + r for f, d, r in table["shared_wrong"]]
    out.append("  READING: " + ("LEAD: they cover each other on this set. Test it on the harder pages."
                                if covers else "NOT A LEAD: on this set they do not cover each other."))
    return out


def build(run, pages, by_model, seconds, enlarged):
    """by_model: {model: {file: text or None}}. Returns the report's lines."""
    out = ["SHYFT READING TEST (S22) · run " + run + " · " + str(len(pages)) + " made-up text pages · "
           + str(sum(len(p["details"]) for p in pages)) + " details",
           "Bar per model, written before the run: wrong 0 · made up 0 · complete at least 26 of 28."]
    scored = {}
    for model, copies in by_model.items():
        scores = [read_score.score(p, copies.get(p["file"])) for p in pages]
        for s, p in zip(scores, pages):
            if p["planted"]:
                s["planted"] = True
        scored[model] = scores
        out += model_section(model, scores, seconds.get(model, []), enlarged)
    names = list(scored)
    if len(names) >= 2:
        out += agreement_section(names[:2], scored[names[0]], scored[names[1]])
    out += ["", "Limits: easy pages (17-60 words, large print); one Legion GPU; one wording; "
            "made-up words without a digit or code are not detected (only numbers and codes); "
            "a misread number also shows as made up."]
    return out
