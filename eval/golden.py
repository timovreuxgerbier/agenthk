# eval/golden.py — Lane: Sphinx. ONE reader for golden/golden.csv, so every report
# grades the same truth. Since S9 a label has two axes:
#   sensitive_kind   HANDLING: "none", or which kind of private thing it shows. Zippy's
#                    axis (D19: private information about a person, you included).
#   expected_action  DISPOSITION: keep_image / keep_text / to_be_deleted. Pip's axis,
#                    and later the age rule's. Blank is allowed when the kind is not
#                    "none" (a locked file's fate was not labelled).
# The pipeline's expected answer follows from both: any kind but "none" means "sensitive"
# (locked), otherwise the disposition. Sheets from before S9 still read: an old
# expected_action of "sensitive" becomes kind "unknown" (sensitive, kind not labelled).

import csv

from harness import schema

FIELDS = ["file", "expected_action", "sensitive_kind", "note", "secret"]
DISPOSITIONS = ["keep_image", "keep_text", "to_be_deleted"]
UNKNOWN_KIND = "unknown"          # labelled sensitive before kinds existed
KNOWN_KINDS = schema.GATE_KINDS + [UNKNOWN_KIND]


def read(path=None):
    """Return (labels, problems). labels: file name -> label dict (see one_label)."""
    path = path or schema.GOLDEN
    labels, problems = {}, []
    with path.open(newline="", encoding="utf-8-sig") as sheet:
        for row in csv.DictReader(sheet):
            name = (row.get("file") or "").strip()
            if not name:
                continue
            label, problem = one_label(row)
            if problem:
                problems.append(name + ": " + problem)
            else:
                labels[name] = label
    return labels, problems


def one_label(row):
    """Turn one sheet row into {"expected", "kind", "disposition", "note", "secret"}."""
    action = (row.get("expected_action") or "").strip().lower()
    kind = (row.get("sensitive_kind") or "").strip().lower()
    if not kind:                                   # sheet from before S9
        if action == "sensitive":
            kind = UNKNOWN_KIND
        elif action in DISPOSITIONS:
            kind = schema.GATE_CLEAR
    if kind not in KNOWN_KINDS:
        return None, "sensitive_kind '" + kind + "' is blank or not one of " + ", ".join(KNOWN_KINDS)
    disposition = "" if action == "sensitive" else action
    if disposition and disposition not in DISPOSITIONS:
        return None, "expected_action '" + action + "' is not one of " + ", ".join(DISPOSITIONS)
    if kind == schema.GATE_CLEAR and not disposition:
        return None, "sensitive_kind is none, so expected_action must say keep_image, keep_text or to_be_deleted"
    expected = "sensitive" if kind != schema.GATE_CLEAR else disposition
    return {"expected": expected, "kind": kind, "disposition": disposition,
            "note": (row.get("note") or "").strip(),
            "secret": (row.get("secret") or "").strip()}, None


def answers(labels):
    """file name -> the action the whole pipeline should produce."""
    return {name: label["expected"] for name, label in labels.items()}


def write(rows, path=None):
    """Write the sheet with every column in FIELDS. rows: file name -> dict of columns."""
    path = path or schema.GOLDEN
    path.parent.mkdir(exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as sheet:
        writer = csv.DictWriter(sheet, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        for name in sorted(rows):
            writer.writerow({k: rows[name].get(k, "") for k in FIELDS})


def read_rows(path=None):
    """The sheet as written, file name -> row dict, no interpretation (for the dev tools)."""
    path = path or schema.GOLDEN
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8-sig") as sheet:
        return {row["file"].strip(): dict(row) for row in csv.DictReader(sheet) if row.get("file")}
