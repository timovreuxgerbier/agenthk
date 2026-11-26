# harness/sync_check.py — Lane: Sphinx. S19, stage 0.1 of the home base (D34).
# Is a folder inside OneDrive? Before each run Shyft asks this about the folders it uses,
# because a screenshot that sits in a synced folder is already in the cloud, however
# local the models are (the S18 Aristotelian check).
#
# Three answers, never a fourth:
#   INSIDE   the folder is inside a OneDrive folder on this computer
#   NO_SIGN  no sign of a OneDrive copy. Only OneDrive is checked. This is NOT "not synced".
#   UNKNOWN  couldn't check (not Windows, or Windows wouldn't say)
#
# How: where OneDrive keeps its folders, from Windows itself (the OneDrive environment
# variables and OneDrive's own entries in the registry). A folder counts as inside when its
# real path starts inside one of those. It only reads: nothing is opened, moved or written.
# Windows only for now (Mac: iCloud Drive and ~/Library/CloudStorage, unverified).

import ntpath
import os
import sys

INSIDE, NO_SIGN, UNKNOWN = "inside", "no_sign", "unknown"

ENV_NAMES = ("OneDrive", "OneDriveConsumer", "OneDriveCommercial")
ACCOUNTS_KEY = r"Software\Microsoft\OneDrive\Accounts"


def roots_from_env(env):
    """OneDrive folders named in the environment (Windows sets these while OneDrive is set up)."""
    return [env[name] for name in ENV_NAMES if env.get(name)]


def roots_from_registry():
    """OneDrive folders from OneDrive's own registry entries, one per signed-in account.
    Empty on anything but Windows, or if the entries aren't there."""
    try:
        import winreg
    except ImportError:
        return []
    found = []
    try:
        accounts = winreg.OpenKey(winreg.HKEY_CURRENT_USER, ACCOUNTS_KEY)
    except OSError:
        return []
    with accounts:
        index = 0
        while True:
            try:
                name = winreg.EnumKey(accounts, index)
            except OSError:
                break
            index += 1
            try:
                with winreg.OpenKey(accounts, name) as account:
                    folder, _ = winreg.QueryValueEx(account, "UserFolder")
                    if folder:
                        found.append(str(folder))
            except OSError:
                continue
    return found


def inside(folder, root, pathmod=ntpath):
    """True if folder is root or lies under it. Windows rules: case and slashes don't matter."""
    folder = pathmod.normcase(pathmod.normpath(str(folder)))
    root = pathmod.normcase(pathmod.normpath(str(root)))
    if not folder or not root:
        return False
    try:
        return pathmod.commonpath([folder, root]) == root
    except ValueError:                       # different drives
        return False


def answer(folder, roots, pathmod=ntpath):
    """INSIDE or NO_SIGN for one folder against a list of OneDrive folders."""
    for root in roots:
        if inside(folder, root, pathmod):
            return INSIDE
    return NO_SIGN


def check(folder):
    """The answer for a real folder on this computer: (answer, reason for UNKNOWN or None)."""
    if sys.platform != "win32":
        return UNKNOWN, "this check is written for Windows only so far"
    try:
        real = os.path.realpath(str(folder))   # follows shortcuts such as junctions
        roots = [os.path.realpath(r) for r in roots_from_env(os.environ) + roots_from_registry()]
    except OSError:
        return UNKNOWN, "Windows wouldn't say where its folders are"
    return answer(real, [r for r in roots if os.path.isdir(r)]), None
