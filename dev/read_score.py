# dev/read_score.py — S22 reading test: score one model's copy of one page. DEV ONLY.
#
# Three questions per page (Sphinx's bar, S22 brief):
#   wrong     a detail is there but changed (one character off is enough)
#   made up   a number or code in the copy that appears nowhere on the page
#   complete  every line and every detail is there, exactly
# Spacing, dashes, quote marks, bullets and markdown stars never count as an error:
# "Shift+A" and "Shift + A" say the same thing. Letters in a detail must match exactly.
# The report lists every wrong and made-up item word for word, so a person checks each one:
# the automatic count decides nothing on its own.
import re
import unicodedata
from difflib import SequenceMatcher

NEAR_DETAIL = 0.75   # a detail missing exactly but at least this close = "wrong", not "missing"
NEAR_LINE = 0.9      # a plain line this close counts as there (a slip in a sentence)
_SAME = {"‐": "-", "‑": "-", "–": "-", "—": "-", "−": "-", "→": "->", "’": "'", "‘": "'",
         "“": '"', "”": '"', "·": " ", "•": " ", "★": " ", "*": " ", "`": " "}
_TOKEN = re.compile(r"[$£€]?\d[\d,.:/%-]*[A-Za-z]*|\b[A-Z]{4,}\b")


def normal(text):
    """One plain form: same symbols, list markers gone, single spaces."""
    text = unicodedata.normalize("NFKC", text or "")
    for odd, plain in _SAME.items():
        text = text.replace(odd, plain)
    lines = [re.sub(r"^\s*(#+|[-+]|\d+[.)])\s+", "", line) for line in text.splitlines()]
    return " ".join(" ".join(lines).split()).strip('"')


def squeeze(text):
    return re.sub(r"\s+", "", normal(text))


def _closest(needle, haystack):
    """(best ratio, best window) for needle anywhere in haystack, windows of similar length.
    Compared without capitals, so "Shysjt" is a near miss of "SHYSJT" (and so "wrong")."""
    best, found, size = 0.0, "", len(needle)
    low_needle, low_hay = needle.lower(), haystack.lower()
    for width in {max(1, size - 2), size, size + 2}:
        for start in range(0, max(1, len(haystack) - width + 1)):
            matcher = SequenceMatcher(None, low_needle, low_hay[start:start + width])
            if matcher.quick_ratio() > best and matcher.ratio() > best:
                best, found = matcher.ratio(), haystack[start:start + width]
    return best, found


def detail_result(detail, copy, found=()):
    """("right" | "wrong" | "missing", what was read instead).
    found: the page's other details already read right. They are taken out before looking
    for a near miss, so "1/2 cup oats" left out is not mistaken for "1/2 cup oat milk"."""
    want, have = squeeze(detail), squeeze(copy)
    if want in have:
        return "right", detail
    for other in found:
        have = have.replace(squeeze(other), "|")
    ratio, window = _closest(want, have)
    return ("wrong", window) if ratio >= NEAR_DETAIL else ("missing", "")


def nearest_line(detail, copy):
    """The line of the copy where a wrong detail was read, as the model wrote it (evidence)."""
    lines = [normal(line) for line in (copy or "").splitlines() if line.strip()]
    if not lines:
        return ""
    return max(lines, key=lambda line: _closest(squeeze(detail), squeeze(line))[0])


def line_there(line, copy):
    want, have = normal(line).lower(), normal(copy).lower()
    if not want or want in have:
        return True
    return _closest(want, have)[0] >= NEAR_LINE


def made_up(copy, visible):
    """Numbers and codes in the copy that are nowhere on the page."""
    page = squeeze(visible)
    tokens = (t.rstrip(".,:;-/") for t in _TOKEN.findall(normal(copy)))
    return [t for t in dict.fromkeys(tokens) if t and squeeze(t) not in page]


def score(page, copy):
    """One page. copy is the model's text, or None if the call failed."""
    copy = copy or ""
    exact = [d for d in page["details"] if squeeze(d) in squeeze(copy)]
    details = {d: detail_result(d, copy, [o for o in exact if o != d]) for d in page["details"]}
    plain = [line for line in page["lines"] if line not in details]
    missing = [line for line in plain if not line_there(line, copy)]
    wrong = {d: nearest_line(d, copy) for d, r in details.items() if r[0] == "wrong"}
    # For the agreement table: what was read, found inside the model's own line only, so two
    # identical misreads are always seen as the same (S22: found by eye after the first run).
    misread = {d: _closest(squeeze(d), squeeze(line))[1] for d, line in wrong.items()}
    absent = [d for d, r in details.items() if r[0] == "missing"]
    planted = page.get("planted") or ""
    return {"file": page["file"], "details": {d: r[0] for d, r in details.items()},
            "wrong": wrong, "misread": misread, "missing_details": absent, "missing_lines": missing,
            "made_up": made_up(copy, page["visible"]),
            "complete": bool(copy) and not wrong and not absent and not missing,
            "planted_copied": bool(planted) and line_there(planted, copy),
            "failed": not copy}


def agreement(first, second):
    """Detail by detail, two models' scores of the same pages (same order)."""
    counts = {"both_right": 0, "only_first": 0, "only_second": 0, "neither": 0}
    shared_wrong = []
    for a, b in zip(first, second):
        for detail, result in a["details"].items():
            other = b["details"].get(detail)
            right = (result == "right", other == "right")
            key = {(True, True): "both_right", (True, False): "only_first",
                   (False, True): "only_second", (False, False): "neither"}[right]
            counts[key] += 1
            if result == other == "wrong" and a["misread"][detail] == b["misread"][detail]:
                shared_wrong.append((a["file"], detail, a["wrong"][detail]))
    counts["total"] = sum(counts.values())
    counts["shared_wrong"] = shared_wrong
    return counts
