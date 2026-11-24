# dev/add_kinds.py — give the LOADED golden.csv its sensitive_kind column. DEV ONLY.
#
#   python3 dev/add_kinds.py
#
# Rows already labelled keep_image / keep_text / to_be_deleted get "none": they were
# never sensitive. Rows labelled "sensitive" get a kind from their note when the note
# says which (the synthetic set writes such notes); otherwise the kind is left blank
# and  python3 dev/label_kind.py  will ask you. Nothing you wrote is changed.

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from eval import golden                  # noqa: E402

KIND_BY_NOTE = [                         # how the synthetic set describes its sensitive cases
    ("invoice", "bank_or_payment"), ("bank account", "bank_or_payment"),
    ("private chat", "private_message"), ("email inbox", "private_message"),
    ("legal contract", "official_document"), ("password manager", "credentials"),
    ("client contact card", "contact_details"),
]


def kind_for(row):
    action = (row.get("expected_action") or "").strip().lower()
    if action in golden.DISPOSITIONS:
        return "none"
    note = (row.get("note") or "").lower()
    for phrase, kind in KIND_BY_NOTE:
        if phrase in note:
            return kind
    return ""


def main():
    rows = golden.read_rows()
    if not rows:
        sys.exit("No golden/golden.csv here. Load a set first: python3 dev/use_set.py <name>")
    filled, blank, kept = 0, 0, 0
    for name, row in rows.items():
        if (row.get("sensitive_kind") or "").strip():
            kept += 1
            continue
        row["sensitive_kind"] = kind_for(row)
        if row["sensitive_kind"]:
            filled += 1
        else:
            blank += 1
    golden.write(rows)
    print("sensitive_kind: filled " + str(filled) + ", already there " + str(kept)
          + ", left blank " + str(blank) + ". Saved golden/golden.csv.")
    if blank:
        print("Blank ones are sensitive rows whose kind only you know: python3 dev/label_kind.py")


if __name__ == "__main__":
    main()
