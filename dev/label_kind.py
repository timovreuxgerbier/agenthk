# dev/label_kind.py — the second question, asked by you, blind. DEV ONLY.
#
#   python3 dev/label_kind.py
#
# Shows EVERY loaded screenshot that has no sensitive_kind yet and asks the D19
# question: does it show private information about a specific person (you included),
# or does the screenshot itself say it is confidential? Answer with the kind:
#   0 none   then the ladder (D23), most harmful first:  1 nudity_or_children
#   2 government_id   3 credentials   4 health_record   5 bank_or_payment
#   6 official_document   7 private_message   8 contact_details   9 marked_confidential
# If more than one fits, choose the LOWEST number (highest on the ladder).
# For any kind but none it then asks what should happen to it:  k keep (locked, as an
# image)   d delete.  If you answer none for a row that had no keep/delete label yet,
# it asks for one:  1 keep_image   2 keep_text   3 to_be_deleted.
# It never shows your earlier label, your note, or anything the agent said.
# Saved after every answer. Type q to stop; run it again to carry on.
#
#   python3 dev/label_kind.py redo "Screen Shot 2024-01-01 at 10.00.00 AM.png"
# Got one wrong? Stop the labeller first (q), then this clears that one row and asks
# it again, on its own. The name is the one printed before your answer.

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from harness import schema               # noqa: E402
from eval import golden                  # noqa: E402

KINDS = {str(i): kind for i, kind in enumerate([schema.GATE_CLEAR] + [k for k in schema.GATE_KINDS
                                                                       if k != schema.GATE_CLEAR])}
FATE = {"k": "keep_image", "d": "to_be_deleted"}
DISPOSITION = {"1": "keep_image", "2": "keep_text", "3": "to_be_deleted"}
QUESTION = ("Private information about a specific person (you included), or marked confidential?\n"
            + "   ".join(n + " " + k for n, k in KINDS.items()) + "   q quit\n"
            + "More than one fits? Choose the lowest number. An ID number anywhere = 2 government_id.")


def show(path):
    if hasattr(os, "startfile"):          # Windows: opens the Photos app
        os.startfile(path)
    else:
        print("  (open it yourself: " + str(path) + ")")


def ask(prompt, choices):
    while True:
        answer = input(prompt).strip().lower()
        if answer == "q":
            return None
        if answer in choices:
            return choices[answer]
        print("  Type one of " + ", ".join(choices) + " (or q to stop).")


def redo(rows, name):
    if name not in rows:
        sys.exit("No row called '" + name + "' in golden/golden.csv. Copy the name exactly, in quotes.")
    rows[name]["sensitive_kind"], rows[name]["expected_action"] = "", ""
    golden.write(rows)
    print("Cleared " + name + ". Asking it again now.\n")


def main():
    rows = golden.read_rows()
    if len(sys.argv) > 2 and sys.argv[1] == "redo":
        redo(rows, sys.argv[2])
    images = sorted(p for p in schema.SCREENSHOTS.iterdir()
                    if p.is_file() and p.suffix.lower() in schema.IMAGE_TYPES)
    todo = [p for p in images if not (rows.get(p.name, {}).get("sensitive_kind") or "").strip()]
    if not todo:
        print("Every screenshot here has a sensitive_kind. Next:  python3 run.py score")
        return
    print(str(len(todo)) + " to label. Decide from the picture alone.\n" + QUESTION + "\n")
    for n, path in enumerate(todo, start=1):
        show(path)
        row = rows.setdefault(path.name, {"file": path.name})
        tag = "[" + str(n) + "/" + str(len(todo)) + "] " + path.name
        kind = ask(tag + "  kind > ", KINDS)
        if kind is None:
            break
        row["sensitive_kind"] = kind
        if kind != schema.GATE_CLEAR:
            fate = ask("      keep or delete?  k / d > ", FATE)
            if fate is None:
                break
            row["expected_action"] = fate
        elif (row.get("expected_action") or "").strip().lower() not in golden.DISPOSITIONS:
            fate = ask("      1 keep_image   2 keep_text   3 to_be_deleted > ", DISPOSITION)
            if fate is None:
                break
            row["expected_action"] = fate
        print("  -> " + kind + (", " + row["expected_action"] if kind != schema.GATE_CLEAR else ""))
        golden.write(rows)                # saved after every answer: nothing is lost
    else:
        golden.write(rows)
        print("\nAll labelled. Saved to golden/golden.csv. Next:  python3 run.py score")
        return
    golden.write(rows)
    print("Saved. Run this again to carry on.")


if __name__ == "__main__":
    main()
