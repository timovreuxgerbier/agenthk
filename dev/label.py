# dev/label.py — label the loaded screenshots yourself, one at a time. DEV ONLY.
#
#   python3 dev/label.py
#
# Opens each screenshot in your photo viewer and asks for ONE answer:
#   1 keep_image   2 keep_text   3 to_be_deleted   4 sensitive
# After the number you may type a short note:  "2 recipe from a blog"
# Type q to stop; your answers so far are saved and it picks up where you left off.
# It never shows what the agent said, so your answers stay your own.
# Writes golden/golden.csv, the file  python3 run.py score  grades against.

import csv
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from harness import schema               # noqa: E402

CHOICES = {"1": "keep_image", "2": "keep_text", "3": "to_be_deleted", "4": "sensitive"}


def read_existing():
    rows = {}
    if schema.GOLDEN.exists():
        with schema.GOLDEN.open(newline="", encoding="utf-8-sig") as sheet:
            for row in csv.DictReader(sheet):
                if row.get("file"):
                    rows[row["file"].strip()] = row
    return rows


def save(rows):
    schema.GOLDEN.parent.mkdir(exist_ok=True)
    fields = ["file", "expected_action", "sensitive_kind", "note", "secret"]   # S9: keep the kind column
    with schema.GOLDEN.open("w", newline="", encoding="utf-8") as sheet:
        writer = csv.DictWriter(sheet, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for name in sorted(rows):
            writer.writerow({k: rows[name].get(k, "") for k in fields})


def show(path):
    if hasattr(os, "startfile"):          # Windows: opens the Photos app
        os.startfile(path)
    else:
        print("  (open it yourself: " + str(path) + ")")


def main():
    rows = read_existing()
    images = sorted(p for p in schema.SCREENSHOTS.iterdir()
                    if p.is_file() and p.suffix.lower() in schema.IMAGE_TYPES)
    todo = [p for p in images if rows.get(p.name, {}).get("expected_action", "").strip() not in schema.ACTIONS]
    if not todo:
        print("Every screenshot here already has an answer. Next:  python3 run.py score")
        return
    print(str(len(todo)) + " to label.  1 keep_image   2 keep_text   3 to_be_deleted   4 sensitive   q quit")
    print("Decide from the picture alone.\n")
    for n, path in enumerate(todo, start=1):
        show(path)
        while True:
            answer = input("[" + str(n) + "/" + str(len(todo)) + "] " + path.name + "  > ").strip()
            if answer.lower() == "q":
                save(rows)
                print("Saved. Run this again to carry on.")
                return
            if answer[:1] in CHOICES:
                rows[path.name] = {"file": path.name, "expected_action": CHOICES[answer[:1]],
                                   "sensitive_kind": rows.get(path.name, {}).get("sensitive_kind", ""),
                                   "note": answer[1:].strip(), "secret": ""}
                print("  -> " + CHOICES[answer[:1]])
                break
            print("  Type 1, 2, 3 or 4 (or q to stop).")
        save(rows)                        # saved after every answer: nothing is lost
    print("\nAll labelled. Saved to golden/golden.csv. Next:  python3 run.py gemma4:e2b 10")


if __name__ == "__main__":
    main()
