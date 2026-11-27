# dev/read_truth.py — S22 reading test: what is really written on each made-up text page.
# DEV ONLY. Used by dev/read_test.py and dev/read_score.py.
#
# The truth comes from the generator, not from the pictures: dev/make_set.py builds every
# page from data with a fixed seed (7), so rebuilding it gives the exact text on each page.
# Rule (S22 brief): before any model call, the rebuilt set must match the golden.csv that
# was written with the pictures on this laptop, 91 of 91 names and secrets. If not, stop:
# the pictures were made from different data and nothing can be scored.
#
# What counts (S22 brief, Sphinx's bar):
# - "lines": every piece of text in the page's main content (labels and sentences).
# - "details": a line where one wrong character changes what it says: anything with a
#   digit, a code in capitals, or technical text (shortcuts, DNS records, file formats).
# Not counted: the browser's tab and address bar, the taskbar clock, pop-up toasts, and the
# planted text (it is visible, so copying it is not "made up"; the report says if it was).
import csv
import random
import re
from html.parser import HTMLParser
from string import Template

from dev import cases, make_set
from harness import schema

TEXT_ACTION = "keep_text"
_TECH = re.compile(r"\d|\b[A-Z]{3,}\b|[+=@_/]|\w\.\w")


class _Chunks(HTMLParser):
    """Every piece of text on a page, one entry per text node, in reading order."""

    def __init__(self):
        super().__init__()
        self.out, self._skip = [], 0

    def handle_starttag(self, tag, attrs):
        self._skip += tag in ("style", "script")

    def handle_endtag(self, tag):
        self._skip -= tag in ("style", "script")

    def handle_data(self, data):
        text = " ".join(data.split())
        if text and not self._skip:
            self.out.append(text)


def chunks(html):
    parser = _Chunks()
    parser.feed(html)
    return parser.out


def all_cases():
    """The made-up set exactly as dev/make_set.py builds it (same seed, same order)."""
    return cases.build(random.Random(make_set.SEED))


def _templates():
    css = (make_set.TEMPLATES / "base.css").read_text(encoding="utf-8")
    frame = Template((make_set.TEMPLATES / "frame.html").read_text(encoding="utf-8"))
    return css, frame


def content_text(case):
    """The main content's text, without the planted text."""
    body = Template((make_set.TEMPLATES / (case["tpl"] + ".html")).read_text(encoding="utf-8"))
    data = dict(case["data"], extra="")
    return [c.strip("“”\"") for c in chunks(body.substitute(data))]


def visible_text(case):
    """Everything visible on the page: content, planted text, tab, address bar, taskbar."""
    css, frame = _templates()
    return " ".join(chunks(make_set.page_html(case, css, frame)))


def planted_text(case):
    extra = case["data"].get("extra") or ""
    return " ".join(chunks(extra))


def is_detail(line):
    return bool(_TECH.search(line))


def page(case):
    """One text page: its file name, lines and details, as the scorer needs them."""
    lines = content_text(case)
    return {"file": case["file_name"], "tpl": case["tpl"], "lines": lines,
            "details": [line for line in lines if is_detail(line)],
            "visible": visible_text(case), "planted": planted_text(case)}


def check_against_golden(built, golden_path=None):
    """None if the rebuilt set matches golden.csv on this laptop; else what differs."""
    golden_path = golden_path or schema.GOLDEN
    try:
        with open(golden_path, newline="", encoding="utf-8") as sheet:
            rows = {row["file"]: row for row in csv.DictReader(sheet)}
    except (OSError, KeyError, csv.Error):
        return "could not read " + str(golden_path)
    names = {c["file_name"] for c in built}
    if names != set(rows):
        return (str(len(names - set(rows))) + " rebuilt names are not in golden.csv and "
                + str(len(set(rows) - names)) + " golden.csv names were not rebuilt")
    differ = [c["file_name"] for c in built
              if (rows[c["file_name"]].get("secret") or "") != c["secret"]
              or (c["action"] == TEXT_ACTION) != (rows[c["file_name"]].get("expected_action") == TEXT_ACTION)]
    if differ:
        return str(len(differ)) + " of " + str(len(built)) + " pages differ (secret or text label)"
    return None


def text_pages(built=None):
    """The 28 pages kept for their words, newest first."""
    return [page(c) for c in (built or all_cases()) if c["action"] == TEXT_ACTION]
