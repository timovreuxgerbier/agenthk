# harness/home_words.py — Lane: Sphinx; the copy is Raaghavi's to rewrite. S20, stage 0.2.
# Every sentence Shyft says about its home, in one place, so the words can change without
# touching the logic in harness/home.py.
#
# Rules for the words (S19 and S20 briefs):
# - The run notice (notice_line) never shows a folder path or a user name: testers send their
#   run output back. When a person makes or moves the home, Shyft does show the place, with
#   their user folder written as "your user folder".
# - Inside OneDrive: say it is at the person's request, and what "local" means then.
# - "No sign" is never "not synced", and never "safe".

from pathlib import Path

NAME = "The Waystation"          # working title (Sphinx, Nov 27). Renaming it is this one line.
ABOUT_FILE = "About this folder.txt"
SENTENCE = (NAME + " is your folder. Shyft sorts your screenshots here, and everything in it "
            "stays yours and stays put if you remove Shyft.")
ABOUT_TEXT = (SENTENCE + "\n\n"
              "What is in it today: only this note. Later, Shyft keeps its receipts and its notes "
              "about the screenshots it sorts here. Your own files come in only when you say so.\n\n"
              "If you remove Shyft, this folder and everything in it stay where they are. You can "
              "delete it yourself, like any other folder.\n\n"
              "If this folder is inside OneDrive, OneDrive copies it to Microsoft's cloud.\n")
LOCAL_NOW = ("What \"local\" means now: Shyft's AI still runs only on this computer, but the files "
             "in " + NAME + " are also copied to Microsoft's cloud while OneDrive is on.")


def shown(place):
    """A place as a person reads it: their user folder written as "your user folder"."""
    place, user = Path(place), Path.home()
    try:
        rest = place.relative_to(user)
    except ValueError:
        return str(place)
    return str(Path("your user folder") / rest) if rest.parts else "your user folder"


def notice_line(state, result=None):
    """The home's line in the WHERE YOUR FILES ARE notice. No paths, no user names.
    state: "none" | "unreadable" | "missing" | "by_request" | "made"."""
    label = NAME + " (Shyft's home for your files)"
    if state == "none":
        return label + ": not made yet."
    if state == "unreadable":
        return label + ": couldn't read Shyft's note of where it is."
    if state == "missing":
        return label + ": not found where Shyft made it. It may have been moved or deleted."
    answer, reason = result
    if answer == "inside":
        if state == "by_request":
            return label + ": inside your OneDrive folder, at your request. " + LOCAL_NOW
        return (label + ": inside your OneDrive folder, which you did not ask for. While OneDrive "
                "is on, the files in it are copied to Microsoft's cloud.")
    if answer == "no_sign":
        return label + ": no sign of a OneDrive copy."
    return label + ": couldn't check (" + str(reason) + ")."


# ---- What Shyft says when a person makes or moves the home -------------------------------
def made(place, by_request):
    out = ["Made " + NAME + " in " + shown(place.parent) + ".", SENTENCE]
    if by_request:
        out += ["It is inside your OneDrive folder because you asked for it there.", LOCAL_NOW,
                "Shyft will say this before every run."]
    return out


def already(place):
    return [NAME + " is already in " + shown(place.parent) + ". Nothing changed."]


def remade(place, folder_was_there):
    if folder_was_there:
        return ["Put Shyft's note back into " + NAME + " in " + shown(place.parent) + ". "
                "Nothing else changed."]
    return [NAME + " was missing from " + shown(place.parent) + ", so Shyft made it again, "
            "as you asked.", SENTENCE]


def moved_from(old):
    return ["The old " + NAME + " folder in " + shown(old.parent) + " is left where it is. "
            "You can delete it yourself."]


def refused(why):
    return ["Shyft didn't make " + NAME + ". " + why, "Nothing was changed."]


INSIDE_ONEDRIVE = ("That place is inside your OneDrive folder. While OneDrive is on, everything in "
                   + NAME + " would also be copied to Microsoft's cloud. Shyft's AI would still "
                   "run only on this computer, but your files would not stay only here. If you "
                   "want it there anyway, run the same command again and add --yes-onedrive")
UNCHECKED = ("Shyft couldn't check whether that place is inside OneDrive ({}). If you want it "
             "there anyway, run the same command again and add --yes-unchecked")
NO_FOLDER = "That folder isn't there. Pick a folder that exists."
SHYFT_OWN = ("That place is inside Shyft's own folders, which go when Shyft is removed. Your "
             "home has to outlive Shyft.")
WHOLE_FOLDER = "Pick a folder to hold " + NAME + ", not the top of a drive."
NOT_OURS = ("There is already a folder called " + NAME + " there that Shyft didn't make, with "
            "things in it. Shyft leaves it alone. Rename or move it, or pick another place.")
NOT_A_FOLDER = "There is a file called " + NAME + " there. Shyft leaves it alone."
HAS_FILES = ("The current " + NAME + " already has things in it. Moving a home with files in it "
             "is a later step, so it stays where it is for now.")
