# app/checks.py — Lane: Ana. Stage 1 of the Windows app plan: what is true on THIS computer.
# Only looks. It never installs, downloads, starts, changes or deletes anything.
# Numbers come from shyft_requirements.json (D27): never retyped here.
# Python standard library only, so it runs before anything else is installed.

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
GB = 1024 ** 3


def requirements():
    """What Shyft needs and which model files, from shyft_requirements.json. In the UI's words:
    the "namer" is Rick (the file still says Pip, his old name)."""
    req = json.loads(REQUIREMENTS.read_text(encoding="utf-8"))
    shape = req["shape"]
    models = []
    for role, buddy in (("gate", "Zippy"), ("namer", "Rick")):
        m = shape[role]
        models.append({"role": role, "buddy": buddy, "job": m["job"].replace("Pip", "Rick"),
                       "pull": m["pull"], "id": m["id"], "gb": m["download_gb"]})
    return {"memory_gb": req["floor"]["memory_gb"], "free_disk_gb": req["floor"]["free_disk_gb"],
            "download_gb": shape["download_gb_total"], "models": models,
            "pace": req["pace"]["plain_words"], "below_floor": req["floor"]["below_the_floor"]}


# ---- This computer ----
def memory_gb():
    """Total memory in GB, one decimal, or None if this computer won't say."""
    try:
        if sys.platform == "win32":
            class MEMORYSTATUSEX(ctypes.Structure):
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
        return round(total / GB, 1)
    except Exception:   # noqa: BLE001 (a check that fails says "couldn't check", it never stops the app)
        return None


def free_disk_gb(where=None):
    """Free space where Shyft keeps its files, in GB, one decimal."""
    try:
        return round(shutil.disk_usage(where or Path.home()).free / GB, 1)
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
            name = (item.get("name") or item.get("model") or "").lower()
            models[name] = (item.get("digest") or "")[:12]   # "ollama list" shows these 12 characters as ID
    except Exception:   # noqa: BLE001
        pass
    return {"running": True, "version": version, "cloud": report, "models": models}


def status():
    """Everything the Spec and Setup screens show, in one answer."""
    req = requirements()
    oll = ollama()
    models = []
    for m in req["models"]:
        found_id = oll["models"].get(m["pull"].lower())
        models.append(dict(m, found=found_id is not None, found_id=found_id, matches=found_id == m["id"]))
    memory, disk = memory_gb(), free_disk_gb()
    # Free space needed NOW: only what is still missing, plus spare (the parts listed in shyft_requirements.json).
    parts = json.loads(REQUIREMENTS.read_text(encoding="utf-8"))["floor"]["free_disk_parts_gb"]
    need_now = parts["spare"] + sum(m["gb"] for m in models if not m["found"]) + (0 if oll["running"] else parts["ollama_itself"])
    req["need_now_gb"] = round(need_now, 1)
    return {
        "requirements": req,
        "computer": {"memory_gb": memory, "free_disk_gb": disk, "graphics": graphics(),
                     "system": platform.system()},
        "meets": {"memory": None if memory is None else memory >= req["memory_gb"] - 0.5,   # 16 GB laptops report about 15.7
                  "disk": None if disk is None else disk >= need_now},
        "ollama": {k: oll[k] for k in ("running", "version", "cloud")},
        "models": models,
    }
