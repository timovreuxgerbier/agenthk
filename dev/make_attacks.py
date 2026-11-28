# dev/make_attacks.py — S23 TEST ONLY: renders the attack set. DEV ONLY, never shipped.
#
#   python3 dev/make_attacks.py
#
# Writes golden/sets/attacks/ (gitignored, like every set):
#   screenshots/*.png   56 pages: 28 pairs, each a PLANTED page and its TWIN
#   golden.csv          what each page is (make_set's columns), so use_set and run.py score read it
#   attacks.csv         which pages pair up, what each planted line asks, and the line itself
# Then:  python3 dev/use_set.py attacks     ...and back:  python3 dev/use_set.py synthetic
# Needs Playwright (D16: dev tools may use pip packages; the product may not).
# For S23 it was rendered in Claude's workspace (Linux fonts, a stated limit) and copied to the
# Legion, each file checked by sha. Both pages of a pair are rendered the same way.
# Nothing is deleted: an older attack set is kept beside the new one.

import csv
import os
import sys
import time
from collections import Counter
from pathlib import Path
from string import Template

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dev import attack_cases                       # noqa: E402  (needs ROOT on the path first)
from dev.make_set import TEMPLATES, page_html      # noqa: E402

SETS = ROOT / "golden" / "sets"
OUT = SETS / "attacks"
ACTIVE = ROOT / "golden" / "active_set.txt"


def prepare_folder():
    if ACTIVE.exists() and ACTIVE.read_text(encoding="utf-8").strip() == "attacks":
        sys.exit("The attack set is loaded right now. Run  python3 dev/use_set.py synthetic  first.")
    if OUT.exists() and any(OUT.rglob("*")):
        parked = SETS / ("attacks-old-" + time.strftime("%Y%m%d-%H%M%S"))
        OUT.rename(parked)
        print("Kept the previous attack set as " + parked.name)
    (OUT / "screenshots").mkdir(parents=True, exist_ok=True)


def write_sheets(pairs):
    with (OUT / "golden.csv").open("w", newline="", encoding="utf-8") as sheet:
        writer = csv.writer(sheet)
        writer.writerow(["file", "expected_action", "sensitive_kind", "note", "secret"])
        writer.writerows(attack_cases.golden_rows(pairs))
    with (OUT / "attacks.csv").open("w", newline="", encoding="utf-8") as sheet:
        writer = csv.DictWriter(sheet, fieldnames=attack_cases.FIELDS)
        writer.writeheader()
        writer.writerows(attack_cases.manifest(pairs))


def main():
    from playwright.sync_api import sync_playwright
    pairs = attack_cases.build()
    prepare_folder()
    css = (TEMPLATES / "base.css").read_text(encoding="utf-8")
    frame = Template((TEMPLATES / "frame.html").read_text(encoding="utf-8"))
    shots = OUT / "screenshots"
    pages = [p[role] for p in pairs for role in attack_cases.ROLES]
    with sync_playwright() as p:
        browser = p.chromium.launch()
        tab = browser.new_page()
        for n, page in enumerate(pages, start=1):
            tab.set_viewport_size({"width": page["size"][0], "height": page["size"][1]})
            tab.set_content(page_html(page, css, frame))
            tab.screenshot(path=str(shots / page["file_name"]))
            print("\r  rendered " + str(n) + " of " + str(len(pages)), end="")
        browser.close()
    for page in pages:                      # the date Windows would have given it
        stamp = page["time"].timestamp()
        os.utime(shots / page["file_name"], (stamp, stamp))
    write_sheets(pairs)
    print("\nMade " + str(len(pages)) + " pages, " + str(len(pairs)) + " pairs:")
    for target, count in Counter(p["target"] for p in pairs).most_common():
        print("  " + str(count).rjust(3) + "  " + target)
    print("Saved in golden/sets/attacks/. Next:  python3 dev/use_set.py attacks")


if __name__ == "__main__":
    main()
