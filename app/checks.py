# app/checks.py — Lane: Ana. Stage 1 of the Windows app plan: what is true on THIS computer.
# Only looks. It never installs, downloads, starts, changes or deletes anything, and it builds no path
# to a person's files or to Shyft's home (D38: only harness/home.py and harness/records.py do that).
# Numbers come from shyft_requirements.json (D27): never retyped here.
# Python standard library only, so it runs before anything else is installed.
#
# Units: disk sizes in the requirements file come from Ollama's own sizes, which count a GB as
# 1,000,000,000 bytes, so free disk is measured the same way (DISK_GB). Memory is sold and reported
# in 1024s, so memory uses GiB (MEMORY_GB). A "16 GB" laptop then reads 16.0, not 17.2.

import ctypes
import json
import os
import platform
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQUIREMENTS = ROOT / "shyft_requirements.json"
# 127.0.0.1, never localhost (shyft_requirements.json: on Windows localhost adds 2 s to every call).
OLLAMA = os.environ.get("SHYFT_OLLAMA_URL", "http://127.0.0.1:11434")
DISK_GB = 1000 ** 3
MEMORY_GB = 1024 ** 3

try:   # the cloud lock's own words for turning the cloud off (harness/cloud_lock.py), never retyped
    sys.path.insert(0, str(ROOT))
    from harness.cloud_lock import TURN_IT_OFF
except Exception:   # noqa: BLE001 (older code without the lock: the screen points to Ollama's settings)
    TURN_IT_OFF = "Turn Ollama's cloud off in Ollama's settings, then quit Ollama completely and open it again."


def requirements():
    """What Shyft needs and which model files, from shyft_requirements.json. In the UI's words:
    the "namer" is Rick (the file still says Pip, his old name)."""
    req = json.loads(REQUIREMENTS.read_text(encoding="utf-8"))
    shape = req["shape"]
    models = []
    for role, buddy in (("gate", "Zippy"), ("namer", "Rick")):
        m = shape[role]
        models.append({"role": role, "buddy": buddy, "job": m["job"].replace("Pip", "Rick"),
                       "pull": m["pull"], "short": m.get("short_name"), "id": m["id"], "gb": m["download_gb"]})
    return {"memory_gb": req["floor"]["memory_gb"], "free_disk_gb": req["floor"]["free_disk_gb"],
            "disk_parts": req["floor"]["free_disk_parts_gb"], "download_gb": shape["download_gb_total"],
            "models": models, "pace": req["pace"]["plain_words"], "below_floor": req["floor"]["below_the_floor"]}


# ---- This computer ----
def memory_gb():
    """Installed memory in GB (GiB), one decimal, or None if this computer won't say.
    Windows: the memory that is installed, not what Windows has left after the graphics took
    their share (a 16 GB laptop with built-in graphics can otherwise report about 15.3)."""
    try:
        if sys.platform == "win32":
            kb = ctypes.c_ulonglong(0)
            if ctypes.windll.kernel32.GetPhysicallyInstalledSystemMemory(ctypes.byref(kb)):
                return round(kb.value * 1024 / MEMORY_GB, 1)

            class MEMORYSTATUSEX(ctypes.Structure):   # fallback: total usable memory
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
            status = MEMORYSTATUSEX()
            status.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
            total = status.ullTotalPhys
        elif sys.platform == "darwin":
            total = int(subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True, timeout=5).stdout)
        else:
            with open("/proc/meminfo") as f:
                total = int(f.readline().split()[1]) * 1024
        return round(total / MEMORY_GB, 1)
    except Exception:   # noqa: BLE001 (a check that fails says "couldn't check", it never stops the app)
        return None


def free_disk_gb():
    """Free space on the disk Shyft runs from, in GB (as Ollama counts them), one decimal.
    Later: where the models and the home are (home.where()); stage 1 measures Shyft's own disk."""
    try:
        return round(shutil.disk_usage(ROOT).free / DISK_GB, 1)
    except OSError:
        return None


def graphics():
    """Graphics card names, "Apple chip", or None if this computer won't say. On Windows this asks
    Windows itself, with no window shown."""
    try:
        if sys.platform == "win32":
            out = subprocess.run(["powershell", "-NoProfile", "-Command",
                                  "(Get-CimInstance Win32_VideoController).Name"],
                                 capture_output=True, text=True, timeout=10,
                                 creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)).stdout
            names = [line.strip() for line in out.splitlines() if line.strip()]
            return names or None
        if sys.platform == "darwin" and platform.machine() == "arm64":
            return ["Apple chip"]
    except Exception:   # noqa: BLE001
        pass
    return None


# ---- Ollama ----
def _get(path):
    with urllib.request.urlopen(OLLAMA + path, timeout=3) as response:
        return json.loads(response.read().decode("utf-8"))


def ollama():
    """Is Ollama running, its version, its cloud setting, and which models it has (name -> id)."""
    try:
        version = _get("/api/version").get("version")
    except Exception:   # noqa: BLE001 (not running, or not installed: the screen says so)
        return {"running": False, "version": None, "cloud": "unknown", "models": {}}
    try:   # the same question Shyft's cloud lock asks before every run (harness/cloud_lock.py)
        cloud = _get("/api/status").get("cloud")
        report = ("off" if cloud.get("disabled") is True else "on") if isinstance(cloud, dict) and "disabled" in cloud else "too_old"
    except Exception:   # noqa: BLE001 (older than 0.40.17: can't say, so every run would stop)
        report = "too_old"
    models = {}
    try:
        for item in _get("/api/tags").get("models") or []:
            name = item.get("name") or item.get("model") or ""   # as Ollama has it: run.py gets this exact name
            models[name] = (item.get("digest") or "")[:12]   # "ollama list" shows these 12 characters as ID
    except Exception:   # noqa: BLE001
        pass
    return {"running": True, "version": version, "cloud": report, "models": models}


def match(m, here):
    """D27 / files_rule: names can be re-pointed, ids can't. So a model is FOUND by its id, under any
    name (a laptop may hold the measured build as gemma4:e4b). A DIFFERENT BUILD is only a tag with the
    model's long or short name whose id differs. Neither: not downloaded.
      matches: the measured build is here.  found: something is here (the right build, or a different one).
      name: the name to run it by (the long name if it has it, else any name it's under)."""
    own = {m["pull"].lower(), (m.get("short") or "").lower()} - {""}      # names compared without case
    under = sorted((n for n, i in here.items() if i == m["id"]), key=lambda n: n.lower() != m["pull"].lower())
    if under:
        return {"found": True, "matches": True, "found_id": m["id"], "name": under[0]}
    named = [i for n, i in here.items() if n.lower() in own]
    return {"found": bool(named), "matches": False, "found_id": named[0] if named else None, "name": m["pull"]}


def status():
    """Everything the Spec and Setup screens show, in one answer. The screens only display it:
    every judgement (ready, enough space) is made here, once, so the two screens can't disagree."""
    req = requirements()
    oll = ollama()
    models = [dict(m, **match(m, oll["models"])) for m in req["models"]]
    memory, disk = memory_gb(), free_disk_gb()
    # Free space needed NOW: what is still to download (a different build too: the right one must come),
    # plus Ollama if it isn't there, plus spare. The parts come from shyft_requirements.json.
    parts = req["disk_parts"]
    need_now = round(parts["spare"] + sum(m["gb"] for m in models if not m["matches"])
                     + (0 if oll["running"] else parts["ollama_itself"]), 1)
    return {
        "requirements": dict(req, need_now_gb=need_now),
        "computer": {"memory_gb": memory, "free_disk_gb": disk, "graphics": graphics(),
                     "system": platform.system()},
        "meets": {"memory": None if memory is None else memory >= req["memory_gb"],
                  "disk": None if disk is None else disk >= need_now},
        "ollama": {"running": oll["running"], "version": oll["version"], "cloud": oll["cloud"],
                   "cloud_fix": TURN_IT_OFF},
        "models": models,
    }
