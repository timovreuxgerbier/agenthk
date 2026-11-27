# app/jobs.py — Lane: Ana. Stage 2 of the Windows app plan: Shyft gets itself ready, and sorts.
# One job at a time:
#   get_ready()  downloads the model files that are missing, through Ollama's own API, with progress.
#   sort()       starts the team's run.py on the made-up test set, and follows its progress.
#   stop()       stops the job. Nothing is half-moved: Stage 2 never moves anything (run.py only proposes).
# The screens only ever see numbers and the team's own plain words: no file names, no paths.
# This file writes, moves and deletes nothing itself, and builds no path to a person's files (D38).
# Python standard library only.

import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.request

from app import checks

LABEL = re.compile(r"^\[(\d+)/(\d+)\] .+? \.\.\. (Zippy is looking|locked, Pip skips it|Pip's turn)\s*$")
TOOK = re.compile(r"^\s+Took [\d.]+ seconds")
RUN = "run.py"            # the team's script, in the project folder (tests point this at a stand-in)
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)   # Windows: run.py works without a window of its own

_lock = threading.Lock()
_job = {"kind": None, "state": "idle"}
_process = None
_stop = threading.Event()


def snapshot():
    """What the screens may see: numbers, states and the team's own words. Never file names."""
    with _lock:
        return json.loads(json.dumps(_job))


def _set(**changes):
    with _lock:
        _job.update(changes)


def _start(kind, work, **fields):
    """Start a job unless one is running. Returns (True, snapshot) or (False, why)."""
    global _job
    with _lock:
        if _job.get("state") == "running":
            return False, "Shyft is already busy. Wait for it, or press Stop."
        _stop.clear()
        _job = dict({"kind": kind, "state": "running", "message": "", "started": time.time()}, **fields)
    threading.Thread(target=work, daemon=True).start()
    return True, snapshot()


def stop():
    """Stop whatever is running. Safe to call when nothing runs."""
    _stop.set()
    process = _process
    if process is not None and process.poll() is None:
        process.terminate()
    with _lock:
        if _job.get("state") == "running":
            _job.update(state="stopped", message="Stopped. Nothing was moved.")


# ---- Getting ready: the missing model files ----
def get_ready():
    """Download the model files that aren't here. A different build is NOT replaced: that is someone's
    own model, and the person decides (the screen says so)."""
    status = checks.status()
    if not status["ollama"]["running"]:
        return False, "Ollama isn't running. Open it (the llama icon), then try again."
    missing = [m for m in status["models"] if not m["found"]]
    if not missing:
        return False, "Nothing to download."
    return _start("get-ready", lambda: _download(missing), buddy=None, gb_done=0.0,
                  gb_total=round(sum(m["gb"] for m in missing), 1))


def _download(models):
    done_before = 0.0
    try:
        for m in models:
            _set(buddy=m["buddy"])
            layers = {}
            request = urllib.request.Request(checks.OLLAMA + "/api/pull", method="POST",
                                             data=json.dumps({"model": m["pull"]}).encode("utf-8"),
                                             headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(request, timeout=60) as response:
                for raw in response:
                    if _stop.is_set():
                        return
                    line = json.loads(raw.decode("utf-8") or "{}")
                    if line.get("error"):
                        return _set(state="failed", message="The download stopped: " + str(line["error"])
                                    + ". Try again: it carries on where it stopped.")
                    if line.get("total"):
                        layers[line.get("digest", "")] = (line.get("completed", 0), line["total"])
                        got = sum(c for c, _ in layers.values()) / checks.DISK_GB
                        _set(gb_done=round(done_before + got, 2))
            done_before += m["gb"]
        after = checks.status()
        wrong = [m["buddy"] for m in after["models"] if m["found"] and not m["matches"]]
        if wrong:
            return _set(state="failed", message=" and ".join(wrong) + " downloaded, but it isn't the build Shyft "
                        "was measured with. Please tell the Shyft team.")
        _set(state="done", gb_done=round(done_before, 1), message="Both models are here, the exact builds Shyft was measured with.")
    except Exception as problem:   # noqa: BLE001 (a cut connection must end in plain words, not a crash)
        if not _stop.is_set():
            _set(state="failed", message="The download stopped (" + type(problem).__name__ + "). Check the "
                 "internet connection and try again: it carries on where it stopped.")


# ---- Sorting: the team's run.py, on the made-up test set only ----
def loaded_set():
    """The team's own answer to "which test set is in screenshots/?" ("real" when nobody chose one)."""
    sys.path.insert(0, str(checks.ROOT))
    from dev import use_set
    return use_set.active()


def sort():
    """Start run.py with the two measured builds, by the names they are under (found by id, D27) on the made-up test set. Refuses, in plain
    words, when a run couldn't work: the wrong set loaded, models missing, the cloud on."""
    if loaded_set() != "synthetic":
        return False, ("Stage 2 only sorts the made-up test screenshots, and they aren't loaded. "
                       "Load them with: python3 dev/use_set.py synthetic")
    status = checks.status()
    o = status["ollama"]
    if not o["running"]:
        return False, "Ollama isn't running. Open it (the llama icon), then try again."
    if o["cloud"] == "too_old":
        return False, "This Ollama can't say whether its cloud is off. Update it from ollama.com/download."
    if o["cloud"] == "on":
        return False, "Ollama's cloud is on, so Shyft would refuse to run. " + o["cloud_fix"]
    if not all(m["matches"] for m in status["models"]):
        return False, "A model is missing or isn't the build Shyft was measured with. Go back to Get Shyft ready."
    zippy, rick = (m["name"] for m in status["models"])   # the name each measured build is under (found by id)
    command = [sys.executable, "-u", RUN, rick, "all", "--zippy", zippy]
    return _start("sort", lambda: _follow(command), total=0, zippy_done=0, done=0, phase="starting",
                  notice=[], seconds=0)


def _follow(command):
    """Run run.py and turn its own lines into numbers for the screens."""
    global _process
    env = dict(os.environ, PYTHONUNBUFFERED="1", PYTHONIOENCODING="utf-8")
    try:
        _process = subprocess.Popen(command, cwd=str(checks.ROOT), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    text=True, encoding="utf-8", errors="replace", env=env, creationflags=NO_WINDOW)
    except OSError as problem:
        return _set(state="failed", message="Couldn't start Shyft's run (" + type(problem).__name__ + ").")
    notice, in_notice, last_words, finished = [], False, "", False
    zippy_seen, done = set(), 0
    for line in _process.stdout:
        line = line.rstrip("\n")
        if line.startswith("WHERE YOUR FILES ARE"):
            in_notice = True
        if in_notice:
            if line.strip():
                notice.append(line.strip())
                continue
            in_notice = False
            _set(notice=notice)
        hit = LABEL.match(line)
        if hit:
            number, total, what = int(hit.group(1)), int(hit.group(2)), hit.group(3)
            if what == "Zippy is looking":
                zippy_seen.add(number)
                _set(total=total, zippy_done=len(zippy_seen), phase="zippy")
            elif what.startswith("locked"):
                done += 1
                _set(total=total, done=done, phase="rick")
            else:
                _set(total=total, phase="rick")
        elif TOOK.match(line):
            done += 1
            _set(done=done)
        elif line.startswith("Done. Total "):
            finished = True
        elif line.strip():
            last_words = line.strip()
            if last_words.startswith("Stopped before ") and ": " in last_words:   # keep the reason, not the file name
                last_words = last_words.split(": ", 1)[1]
        _set(seconds=round(time.time() - snapshot().get("started", time.time())))
    _process.wait()
    _process.stdout.close()
    _process_end(finished, last_words)


def _process_end(finished, last_words):
    global _process
    _process = None
    if _stop.is_set():
        return
    if finished:
        _set(state="done", phase="done", message="Rick and Zippy looked at every made-up screenshot. Nothing was moved.")
    else:   # the team's own words for why it stopped (a cap, the cloud lock, Ollama gone)
        _set(state="failed", message="The run stopped: " + (last_words or "no reason given") + " Nothing was moved.")
