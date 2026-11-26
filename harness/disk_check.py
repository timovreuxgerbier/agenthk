# harness/disk_check.py — Lane: Sphinx. S19, stage 0.1 of the home base (D34).
# Is the disk Shyft works on encrypted? Whole-disk encryption is the system's job
# (BitLocker, or Device Encryption on Windows Home); Shyft's job is only to ask and say.
#
# Three answers, never a fourth:
#   ENCRYPTED      Windows says the disk is encrypted
#   NOT_ENCRYPTED  Windows says it is not
#   UNKNOWN        couldn't tell (not Windows, no answer in time, or an answer we don't know)
# Shyft says "encrypted" ONLY when Windows says so. Shyft itself encrypts nothing.
#
# How: one FIXED question to PowerShell (it ships with Windows; no administrator rights):
# the drive's "BitLocker protection" property, the one File Explorer shows as a padlock.
# The property is not in Microsoft's documentation. Its numbers, by report (checked by
# Sphinx's own eyes in S19): 1 = on, 2 = off; 3 encrypting, 4 decrypting, 5 suspended,
# 6 locked. Only 1 and 2 are trusted here; anything else is UNKNOWN, with the number.
# Nothing but a checked drive letter ever goes into the command.

import os
import re
import subprocess
import sys

ENCRYPTED, NOT_ENCRYPTED, UNKNOWN = "encrypted", "not_encrypted", "unknown"

TIMEOUT_SECONDS = 6          # a check must never hold a run up for long
QUESTION = ("(New-Object -ComObject Shell.Application).NameSpace('{drive}\\')"
            ".Self.ExtendedProperty('System.Volume.BitLockerProtection')")
NO_WINDOW = 0x08000000       # CREATE_NO_WINDOW: no black window flashes up


def drive_of(folder, pathmod=os.path):
    """'C:' for a folder on C, or None if it isn't a plain drive letter (a network share)."""
    drive = pathmod.splitdrive(pathmod.abspath(str(folder)))[0]
    return drive.upper() if re.fullmatch(r"[A-Za-z]:", drive) else None


def read(text):
    """Turn PowerShell's printed answer into (answer, reason for UNKNOWN or None)."""
    text = (text or "").strip()
    if text == "1":
        return ENCRYPTED, None
    if text == "2":
        return NOT_ENCRYPTED, None
    if not text:
        return UNKNOWN, "Windows didn't say"
    if text.isdigit():
        return UNKNOWN, "Windows gave an answer Shyft doesn't know yet (" + text + ")"
    return UNKNOWN, "Windows gave an answer Shyft couldn't read"


def ask_windows(drive):
    """Run the fixed question for one drive. Returns PowerShell's printed text."""
    done = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
         QUESTION.format(drive=drive)],
        capture_output=True, text=True, timeout=TIMEOUT_SECONDS, creationflags=NO_WINDOW)
    return done.stdout


def check(folder, asker=ask_windows):
    """(answer, reason for UNKNOWN or None) for the disk that holds folder."""
    if sys.platform != "win32" and asker is ask_windows:
        return UNKNOWN, "this check is written for Windows only so far"
    drive = drive_of(folder)
    if drive is None:
        return UNKNOWN, "the folder isn't on a lettered drive"
    try:
        return read(asker(drive))
    except subprocess.TimeoutExpired:
        return UNKNOWN, "Windows didn't answer in time"
    except (OSError, subprocess.SubprocessError):
        return UNKNOWN, "Windows wouldn't say"
