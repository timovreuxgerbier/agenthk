# dev/check_misses.py — why did Zippy miss these? You look, and answer y or n. DEV ONLY. S17.
#
#   python3 dev/check_misses.py RUN_ID                  a run on a labelled set
#   python3 dev/check_misses.py RUN_ID SECOND_RUN_ID    read the description from a second run
#
# A MISS is a screenshot you labelled sensitive that Zippy cleared in RUN_ID. For each one
# the picture opens (for you only) and you answer six questions with y or n:
#   small   Is the private part small on the screen?
#   plain   Using only what is in the picture, could a stranger work out that it is private?
#   fits    Does it fit the sentence Zippy was given for that kind, as written?
#   label   Is your label still the right one?
#   seen    Does the model's own description mention the private thing?
#   name    Does the name that would be applied give the private thing away?
# The first four are asked BEFORE anything a model wrote is shown, so its words can't steer
# you. "seen" reads the description from SECOND_RUN_ID when you give one (for example a run
# where Zippy's model also did Pip's job). "name" always reads RUN_ID, the run being checked.
#
# How the answers are read (rule written before any answer, S17, Nov 24):
#   not in the picture   plain = n. Only you know it is private; no model can see that.
#   definition           plain = y, fits = n. Visible, but not what Zippy's sentence describes.
#   reading              plain = y, small = y, seen is not y. It is there but small, and the
#                        model's own description misses it too.
#   the model            plain = y, fits = y, and it is not "reading". Plain to see, fits the
#                        sentence, still cleared.
# Beside those: "label in doubt" (label = n) and "the name leaks" (name = y).
# This tool never changes a label or a score.
#
# PRIVATE BY DESIGN. It finds the set by itself (loaded or put away) and moves nothing.
# What it saves (golden/misses_check_<RUN_ID>.txt) holds row numbers, your label's kind and
# y / n: never a file name, a description or a proposed name. The window is cleared at the
# end, because it showed what the models wrote. It never asks a model anything.

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from harness import gate, naming, schema   # noqa: E402
from eval import golden, score             # noqa: E402

SETS = ROOT / "golden" / "sets"            # where dev/use_set.py keeps the sets that are put away
YES_NO = {"y": "y", "yes": "y", "n": "n", "no": "n"}
QUESTIONS = ["small", "plain", "fits", "label", "seen", "name"]
SKIPPED = "-"                              # this question could not be asked
MEANINGS = ("small = the private part is small on the screen | plain = a stranger could work out "
            "from the picture alone that it is private | fits = it fits Zippy's sentence for that "
            "kind as written | label = the label is still right | seen = the model's own "
            "description mentions the private thing | name = the name that would be applied "
            "gives the private thing away | - = could not be asked")


def find_set(names):
    """(labels, folder of pictures) for the set that holds every one of these files, else (None, None)."""
    places = [(schema.GOLDEN, schema.SCREENSHOTS)]
    if SETS.exists():
        places += [(home / "golden.csv", home / "screenshots")
                   for home in sorted(SETS.iterdir()) if home.is_dir()]
    for sheet, folder in places:
        if not sheet.exists():
            continue
        labels, _ = golden.read(sheet)
        if names and all(name in labels for name in names):
            return labels, folder
    return None, None


def misses(results, labels):
    """[(row, file name, kind)]: labelled sensitive, cleared by Zippy. row = place in the run, from 1."""
    found = []
    for row, name in enumerate(results, start=1):
        label = labels.get(name)
        if label and label["kind"] != schema.GATE_CLEAR and gate.is_cleared(results[name].get("gate")):
            found.append((row, name, label["kind"]))
    return found


def kind_sentence(kind, instructions=None):
    """The sentence zippy.md gives Zippy for this kind, on one line. "" if there is none."""
    text = instructions if instructions is not None else (gate.read_instructions() or "")
    start, picked = "- " + kind + ":", []
    for line in text.splitlines():
        if picked:
            if line.startswith("  ") and line.strip():
                picked.append(line.strip())
                continue
            break
        if line.startswith(start):
            picked.append(line[len(start):].strip())
    return " ".join(picked).strip()


def reading(answers):
    """The rule at the top of this file: what the six answers point to."""
    causes = []
    if answers.get("plain") == "n":
        causes.append("not in the picture")
    elif answers.get("plain") == "y":
        if answers.get("fits") == "n":
            causes.append("definition")
        if answers.get("small") == "y" and answers.get("seen") != "y":
            causes.append("reading")
        elif answers.get("fits") == "y":
            causes.append("the model")
    if answers.get("label") == "n":
        causes.append("label in doubt")
    if answers.get("name") == "y":
        causes.append("the name leaks")
    return causes or ["unclear"]


def saved_text(header, items):
    """What is kept and what stays on screen: rows, kinds, y / n. items: [(row, kind, answers)]."""
    lines = [header,
             "A person looked at each screenshot and answered y or n. No file name, description or "
             "proposed name is kept here.",
             MEANINGS, ""]
    for row, kind, answers in items:
        lines.append("row " + str(row) + " | " + kind + " | "
                     + " | ".join(q + " " + answers.get(q, SKIPPED) for q in QUESTIONS)
                     + " | reads as: " + " + ".join(reading(answers)))
    if not items:
        lines.append("Nothing answered yet.")
    lines += ["", "Reading rule: the top of dev/check_misses.py, written before any answer. "
              "This check changes no label and no score."]
    return "\n".join(lines) + "\n"


def show(path):
    """Open the picture for the person. Never prints where it is, even when it fails."""
    try:
        if hasattr(os, "startfile"):
            os.startfile(path)                       # Windows: opens the Photos app
            return True
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        done = subprocess.run([opener, str(path)], check=False,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return done.returncode == 0
    except OSError:
        return False


def say(words):
    """Print what a model wrote. A character this window can't show becomes "?", never a crash."""
    try:
        print(words)
    except UnicodeEncodeError:
        print(words.encode("ascii", "replace").decode("ascii"))


def clear():
    """Wipe the window: it showed what the models wrote."""
    os.system("cls" if os.name == "nt" else "clear")
    if os.name != "nt":
        print("\033[3J\033[2J\033[H", end="")


def ask(prompt):
    """y or n. None when the person types q."""
    while True:
        typed = input(prompt).strip().lower()
        if typed == "q":
            return None
        if typed in YES_NO:
            return YES_NO[typed]
        print("  Type y or n, then Enter (q stops).")


def ask_about(kind, described, described_by, name, named_by):
    """The six questions for one screenshot. Returns the answers, or None if the person stopped."""
    answers = {}

    def put(key, prompt):
        answers[key] = ask(prompt)
        return answers[key] is not None

    if not put("small", "1 of 6  Is the private part SMALL on the screen: small print, a corner, a thumbnail,\n"
                        "        or one line in a long page?  y / n > "):
        return None
    if not put("plain", "2 of 6  Using ONLY what is in the picture, could a stranger work out that it is private?\n"
                        "        (n = you know only because you know what it is)  y / n > "):
        return None
    sentence = kind_sentence(kind)
    if sentence:
        print("\n  Zippy was told, for " + kind + ":\n    \"" + sentence + "\"")
        if not put("fits", "3 of 6  Does this screenshot fit that sentence as it is written?  y / n > "):
            return None
    else:
        answers["fits"] = SKIPPED
    if not put("label", "4 of 6  Looking at it today, is \"" + kind + "\" still the right label?  y / n > "):
        return None
    print("\n  Now what the models wrote about it. Never copy this part anywhere.")
    if described:
        say("  " + described_by + " described it as:\n    " + described)
        if not put("seen", "5 of 6  Does that description mention the private thing?  y / n > "):
            return None
    else:
        print("  No description was written for it in that run.")
        answers["seen"] = SKIPPED
    if name:
        say("\n  The name that would be applied (written by " + named_by + "):\n    " + name)
        if not put("name", "6 of 6  Does that name give the private thing away?  y / n > "):
            return None
    else:
        print("\n  No name would be applied to it in this run.")
        answers["name"] = SKIPPED
    return answers


def written(results, name):
    """(description, model) Pip wrote for this file in a run. ("", model) if it was locked there."""
    got = results.get(name) or {}
    if got.get("pip_action") in (None, "sensitive"):
        return "", got.get("model", "?")
    return (got.get("reason") or "").strip(), got.get("model", "?")


def main():
    if len(sys.argv) < 2:
        sys.exit("Say which run:  python3 dev/check_misses.py RUN_ID [SECOND_RUN_ID]")
    run_id, results = score.results_for(sys.argv[1])
    if not results:
        sys.exit("No run called " + sys.argv[1] + " in trace.jsonl.")
    second_id, second = score.results_for(sys.argv[2]) if len(sys.argv) > 2 else (None, {})
    if len(sys.argv) > 2 and not second:
        sys.exit("No run called " + sys.argv[2] + " in trace.jsonl.")
    labels, folder = find_set(list(results))
    if labels is None:
        sys.exit("No labelled set, loaded or put away, holds every screenshot of run " + run_id + ".")
    todo = misses(results, labels)
    one = next(iter(results.values()))
    header = ("MISSES CHECK | run " + run_id + " | Zippy " + str(one.get("zippy_model")) + " | "
              + str(len(todo)) + " miss(es)"
              + (" | descriptions read from run " + second_id if second_id else ""))
    out = schema.GOLDEN.parent / ("misses_check_" + run_id + ".txt")
    if not todo:
        print("No misses: in run " + run_id + " Zippy cleared nothing you labelled sensitive.")
        return
    kinds = sorted(kind for _, _, kind in todo)
    print(str(len(todo)) + " screenshot(s) you labelled sensitive that Zippy cleared in run " + run_id + ":")
    print("  " + ", ".join(kinds))
    print("One at a time: the picture opens, then six questions. Type y or n, then Enter. q stops.")
    print("These are private pictures. Do this where only you can see the screen.")
    if input("Press Enter when you are ready (q stops) > ").strip().lower() == "q":
        return
    done, stopped = [], False
    for n, (row, name, kind) in enumerate(todo, start=1):
        described, described_by = written(second if second_id else results, name)
        applied = naming.gated_rename(results[name], name, results[name].get("gate"))
        answers = None
        while answers is None and not stopped:
            print("\n[" + str(n) + " of " + str(len(todo)) + "]  You labelled this one: " + kind
                  + ". Opening the picture now.")
            if not show(folder / name):
                print("  The picture did not open by itself. It is row " + str(row) + " of the run.")
            answers = ask_about(kind, described, described_by, applied, results[name].get("model", "?"))
            if answers is None:
                stopped = True
                break
            print("\n  Your answers: " + "  ".join(q + " " + answers[q] for q in QUESTIONS))
            keep = ask("  Keep them?  y keeps them, n asks this screenshot again > ")
            if keep is None:
                stopped = True
            elif keep == "n":
                answers = None
        if stopped:
            break
        done.append((row, kind, answers))
        out.write_text(saved_text(header, done), encoding="utf-8")   # saved after every screenshot
    if done:
        out.write_text(saved_text(header, done), encoding="utf-8")
    input("\nLast step: close the picture windows, then press Enter. This window will be cleared > ")
    clear()
    print(saved_text(header, done))
    if stopped:
        print("Stopped early. Run the same line again to answer them all.")
    if done:
        print("Saved: golden/" + out.name + " (answers only). Nothing to paste: tell Claude it is done.")


if __name__ == "__main__":
    main()
