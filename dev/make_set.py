# dev/make_set.py — builds the synthetic solopreneur test set. DEV ONLY, never shipped.
#
#   python3 dev/make_set.py
#
# Writes golden/sets/synthetic/screenshots/*.png and golden/sets/synthetic/golden.csv
# (the right answer for every screenshot, written at the moment it is made).
# golden/ is gitignored: none of this output can be committed by accident.
# Needs Playwright (decision D16: dev tools may use pip packages; the product may not).
# Then load it with:  python3 dev/use_set.py synthetic

import csv
import os
import random
import sys
import time
from collections import Counter
from pathlib import Path
from string import Template

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dev import cases                    # noqa: E402  (needs ROOT on the path first)
from harness import schema               # noqa: E402

SEED = 7                                  # same seed = same set on every machine
TEMPLATES = ROOT / "dev" / "templates"
SETS = ROOT / "golden" / "sets"
OUT = SETS / "synthetic"
ACTIVE = ROOT / "golden" / "active_set.txt"


def page_html(case, css, frame):
    body = Template((TEMPLATES / (case["tpl"] + ".html")).read_text(encoding="utf-8"))
    content = body.substitute(case["data"])
    chrome = ""
    if case["chrome"] and case["chrome"][0] == "browser":
        chrome = ('<div class="browser"><span class="tab">' + case["chrome"][1] + '</span></div>'
                  '<div class="url">🔒 ' + case["chrome"][2] + "</div>")
    elif case["chrome"]:
        chrome = '<div class="titlebar">' + case["chrome"][1] + "</div>"
    toast = '<div class="toast">' + case["toast"] + "</div>" if case.get("toast") else ""
    taskbar = ('<div class="taskbar"><span>⊞  🔍  📁  🌐</span><span>' + case["taskbar"]
               + "</span></div>") if case.get("taskbar") else ""
    classes = " ".join(k for k in ("dark", "blur") if case.get(k))
    return frame.substitute(css=css, body_class=classes, chrome=chrome, content=content,
                            toast=toast, taskbar=taskbar)


def prepare_folder():
    if ACTIVE.exists() and ACTIVE.read_text(encoding="utf-8").strip() == "synthetic":
        sys.exit("The synthetic set is loaded right now. Run  python3 dev/use_set.py real  first.")
    if OUT.exists() and any(OUT.rglob("*")):
        parked = SETS / ("synthetic-old-" + time.strftime("%Y%m%d-%H%M%S"))
        OUT.rename(parked)                # nothing is deleted, ever: the old set is kept
        print("Kept the previous set as " + parked.name)
    (OUT / "screenshots").mkdir(parents=True, exist_ok=True)


def write_golden(all_cases):
    with (OUT / "golden.csv").open("w", newline="", encoding="utf-8") as sheet:
        writer = csv.writer(sheet)
        writer.writerow(["file", "expected_action", "note", "secret"])
        for c in sorted(all_cases, key=lambda c: c["file_name"]):
            writer.writerow([c["file_name"], c["action"], c["note"], c["secret"]])


def main():
    from playwright.sync_api import sync_playwright
    all_cases = cases.build(random.Random(SEED))
    bad = [c["action"] for c in all_cases if c["action"] not in schema.ACTIONS]
    if bad:
        sys.exit("A case uses an action the agent doesn't know: " + ", ".join(set(bad)))
    prepare_folder()
    css = (TEMPLATES / "base.css").read_text(encoding="utf-8")
    frame = Template((TEMPLATES / "frame.html").read_text(encoding="utf-8"))
    shots = OUT / "screenshots"
    started = time.time()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        for n, c in enumerate([c for c in all_cases if not c["dup_of"]], start=1):
            width, height = c["size"]
            page.set_viewport_size({"width": width, "height": height})
            page.set_content(page_html(c, css, frame))
            page.screenshot(path=str(shots / c["file_name"]), clip=c["clip"])
            print("\r  rendered " + str(n), end="")
        browser.close()
    for c in all_cases:
        if c["dup_of"]:                   # an exact copy is the same bytes, like a double press
            (shots / c["file_name"]).write_bytes((shots / c["dup_of"]).read_bytes())
    for c in all_cases:                   # the date Windows would have given it
        stamp = c["time"].timestamp()
        os.utime(shots / c["file_name"], (stamp, stamp))
    write_golden(all_cases)
    print("\nMade " + str(len(all_cases)) + " screenshots in " + str(round(time.time() - started)) + " s")
    for action, count in Counter(c["action"] for c in all_cases).most_common():
        print("  " + str(count).rjust(3) + "  " + action)
    print("  " + str(sum("injection" in c["note"] for c in all_cases)).rjust(3) + "  of them carry a prompt injection")
    print("Answers saved to golden/sets/synthetic/golden.csv")
    print("Next:  python3 dev/use_set.py synthetic")


if __name__ == "__main__":
    main()
