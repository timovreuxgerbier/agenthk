# eval/server.py — Lane: Sphinx. Lesson 13: under which server settings did a run happen?
# Reads the settings router.py stores inside each buddy's usage (context window, GPU share,
# Ollama version). Used by the cost report and by dev/compare_runs.py.
# D28: compare a run only against a baseline with the same server settings. This file is
# how the code checks that, instead of a person remembering which window had which setting.
# Prints numbers only, never file names: safe on the Mac (referee) set.

KEYS = ("context", "gpu_share", "ollama_version")
BUDDIES = (("Zippy", "zippy_usage"), ("Pip", "pip_usage"))


def settings(entries):
    """{"Zippy": {key: set of values seen}, "Pip": {...}}. An empty set = not recorded."""
    out = {}
    for who, field in BUDDIES:
        seen = {key: set() for key in KEYS}
        for entry in entries:
            usage = entry.get(field)
            if isinstance(usage, dict):
                for key in KEYS:
                    if usage.get(key) is not None:
                        seen[key].add(usage[key])
        out[who] = seen
    return out


def _where(share):
    if share >= 1:
        return "GPU (all of the model)"
    if share <= 0:
        return "CPU (none of the model on the GPU)"
    return "split: " + str(round(share * 100)) + "% on the GPU, the rest on the CPU"


def _show(key, values):
    if not values:
        return "not recorded"
    ordered = sorted(values, key=str)
    if key == "gpu_share" and len(ordered) == 1:
        return _where(ordered[0])
    text = ", ".join(str(v) for v in ordered)
    return text if len(ordered) == 1 else "MIXED within this run: " + text


def lines(entries):
    """The SERVER section of the cost report."""
    found = settings(entries)
    if not any(found[who][key] for who, _ in BUDDIES for key in KEYS):
        return ["SERVER: not recorded for this run.",
                "  Runs before lesson 13 (Nov 22) kept the models, not the server's settings.", ""]
    out = ["SERVER (asked from Ollama after each call)"]
    labels = {"context": "context window", "gpu_share": "where it ran", "ollama_version": "Ollama"}
    for who, _ in BUDDIES:
        for key in KEYS:
            out.append("  " + who.ljust(6) + labels[key].ljust(16) + _show(key, found[who][key]))
    out += ["  Compare this run only with a baseline whose SERVER lines match (D28).", ""]
    return out


def differences(old_entries, new_entries):
    """Why two runs may not be comparable. [] = same settings, both recorded."""
    old, new = settings(old_entries), settings(new_entries)
    problems = []
    for who, _ in BUDDIES:
        for key in KEYS:
            before, after = old[who][key], new[who][key]
            if not before and not after:
                continue
            if not before or not after:
                problems.append(who + " " + key + ": not recorded in the "
                                + ("old" if not before else "new") + " run")
            elif before != after:
                problems.append(who + " " + key + ": " + _show(key, before) + " -> " + _show(key, after))
    if not any(old[w][k] or new[w][k] for w, _ in BUDDIES for k in KEYS):
        problems.append("neither run recorded its server settings (both before lesson 13)")
    return problems
