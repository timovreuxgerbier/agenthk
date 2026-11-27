# harness/where_check.py — Lane: Sphinx. S19, stage 0.1 of the home base (D34).
# Before each run, Shyft says in plain words where the files it works on sit:
# inside OneDrive or not (harness/sync_check.py), and whether Windows says the disk is
# encrypted (harness/disk_check.py). It is a notice, not a gate: the run always goes on,
# and a check that fails says "couldn't check" instead of stopping anything.
#
# Rules for the words (S19 brief):
# - No folder paths and no user names: testers send their run output back.
# - Say exactly what was checked, so "no sign" is never read as "safe".
# - "Encrypted" only when Windows says so. Shyft encrypts nothing.

from harness import disk_check, schema, sync_check

PLACES = [
    ("Screenshots folder", schema.SCREENSHOTS),
    ("Shyft's own folder (where it keeps its notes)", schema.ROOT),
]
SCOPE = "Only OneDrive was checked. iCloud, Dropbox and Google Drive are not checked yet."


def sync_line(label, result):
    answer, reason = result
    if answer == sync_check.INSIDE:
        return (label + ": inside your OneDrive folder. While OneDrive is on, these files are "
                "copied to Microsoft's cloud.")
    if answer == sync_check.NO_SIGN:
        return label + ": no sign of a OneDrive copy."
    return label + ": couldn't check (" + str(reason) + ")."


def disk_line(result):
    answer, reason = result
    if answer == disk_check.ENCRYPTED:
        return "This computer's disk: encrypted, Windows says."
    if answer == disk_check.NOT_ENCRYPTED:
        return ("This computer's disk: not encrypted, Windows says. Someone holding this laptop "
                "could read these files.")
    return "This computer's disk: couldn't tell (" + str(reason) + ")."


def lines(sync_results, disk_result):
    """The notice, as a list of lines. sync_results: [(label, (answer, reason)), ...]."""
    out = ["WHERE YOUR FILES ARE (checked before this run; Shyft only looked, nothing changed)"]
    out += ["  " + sync_line(label, result) for label, result in sync_results]
    if any(result[0] == sync_check.NO_SIGN for _, result in sync_results):
        out.append("  " + SCOPE)
    out.append("  " + disk_line(disk_result))
    out.append("  The run goes on either way.")
    return out


def report(places=PLACES):
    """Print the notice. Never raises: a broken check must not stop a run."""
    try:
        sync_results = [(label, sync_check.check(folder)) for label, folder in places]
        disk_result = disk_check.check(places[0][1])
        text = lines(sync_results, disk_result)
    except Exception as problem:            # noqa: BLE001 (on purpose: notice, not gate)
        text = ["WHERE YOUR FILES ARE: couldn't check (" + type(problem).__name__
                + "). The run goes on."]
    print("\n".join(text) + "\n")
