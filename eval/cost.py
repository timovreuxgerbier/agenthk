# eval/cost.py — Lane: Sphinx. S11: what one run cost, in time and tokens.
#   python3 run.py cost                  the latest run
#   python3 run.py cost 20261115-141247  an older run (its id is in trace.jsonl)
# Runs before S11 have time but no tokens: Ollama sent the counts, the harness dropped them.
# The cloud line is an ESTIMATE and says so. A cloud model counts an image in its own
# tokens, not Gemma's, so it gives the right size of the number, not an exact bill.
# Reads no labels and prints no file names, so it is safe on the Mac (referee) set.
# Saves golden/cost_<set>_<run>.txt, like score does.

from collections import Counter

from harness import schema, trace, gate

# What we compare against. Change the numbers AND the date together, from the price page.
CLOUD = {"name": "Gemini 3.5 Flash-Lite (standard paid tier)", "checked": "Nov 16, 2026",
         "in_per_million": 0.30, "out_per_million": 2.50}


def counts(entries, key, field):
    """Every number `field` found in entries[key], e.g. ("zippy_usage", "tokens_in")."""
    found = []
    for entry in entries:
        usage = entry.get(key)
        if isinstance(usage, dict) and isinstance(usage.get(field), (int, float)):
            found.append(usage[field])
    return found


def cloud_dollars(tokens_in, tokens_out):
    return (tokens_in * CLOUD["in_per_million"] + tokens_out * CLOUD["out_per_million"]) / 1e6


def _avg(values):
    return round(sum(values) / len(values), 1) if values else 0


def _clock(seconds):
    minutes, secs = divmod(int(round(seconds)), 60)
    return str(minutes) + ":" + str(secs).zfill(2)


def set_name(run_id):
    """The set this run was scored on, read from its saved score report. None if unscored."""
    tail = "_" + str(run_id) + ".txt"
    for path in sorted(schema.SCORE_REPORT.parent.glob("score_*" + tail)):
        return path.name[len("score_"):-len(tail)]
    return None


def _most_common(values, fallback="?"):
    values = [v for v in values if v and not str(v).startswith("code:")]
    return Counter(values).most_common(1)[0][0] if values else fallback


def _time_lines(entries):
    secs = [e["seconds"] for e in entries if isinstance(e.get("seconds"), (int, float))]
    if not secs:
        return ["TIME: not recorded for this run.", ""]
    out = ["TIME (our code's clock)",
           "  Whole run:       " + _clock(sum(secs)) + " for " + str(len(secs)) + " screenshots",
           "  Per screenshot:  " + str(_avg(secs)) + " s average, " + str(max(secs)) + " s longest"]
    zips = [e["zippy_seconds"] for e in entries if isinstance(e.get("zippy_seconds"), (int, float))]
    pips = [e["seconds"] - e["zippy_seconds"] for e in entries
            if isinstance(e.get("zippy_seconds"), (int, float)) and not gate.is_locked(e.get("gate"))
            and not str(e.get("model", "")).startswith("code:")]
    if zips:
        out.append("  Zippy:           " + str(_avg(zips)) + " s average per screenshot")
    if pips:
        out.append("  Pip:             " + str(_avg(pips)) + " s average, when Pip ran")
    loads = counts(entries, "zippy_usage", "load_seconds") + counts(entries, "pip_usage", "load_seconds")
    if loads:
        slow = sum(1 for s in loads if s > 1)
        out.append("  Model loading:   " + str(round(sum(loads), 1)) + " s in all; " + str(slow)
                   + " call(s) waited over 1 s for a model to load")
        out.append("                   (more than 1 or 2 = the models are swapping in and out of memory)")
    hours = _avg(secs) * 10000 / 3600
    out += ["  At this pace, 10,000 screenshots take about " + str(round(hours, 1)) + " hours on this laptop.", ""]
    return out


def _token_lines(entries):
    z_in, z_out = counts(entries, "zippy_usage", "tokens_in"), counts(entries, "zippy_usage", "tokens_out")
    p_in, p_out = counts(entries, "pip_usage", "tokens_in"), counts(entries, "pip_usage", "tokens_out")
    if not (z_in or z_out or p_in or p_out):
        return ["TOKENS: not recorded for this run.",
                "  Runs before S11 kept the time but dropped Ollama's token counts.",
                "  Run the set once more to get them.", ""]
    out = ["TOKENS (counted by Ollama)"]
    for who, t_in, t_out in (("Zippy", z_in, z_out), ("Pip", p_in, p_out)):
        if t_in or t_out:
            out.append("  " + who.ljust(6) + " " + str(len(t_in)) + " calls: read " + format(sum(t_in), ",")
                       + " (" + str(_avg(t_in)) + " avg, " + str(max(t_in) if t_in else 0) + " max)"
                       + ", wrote " + format(sum(t_out), ",") + " (" + str(_avg(t_out)) + " avg)")
    total_in, total_out = sum(z_in) + sum(p_in), sum(z_out) + sum(p_out)
    n = len(entries)
    out += ["  Total:  read " + format(total_in, ",") + ", wrote " + format(total_out, ",")
            + " = " + format(round((total_in + total_out) / n), ",") + " tokens per screenshot",
            "  If a max is far above its average, Ollama reused the start of the prompt from the",
            "  call before and did not count it again. A cloud bill would count it.", ""]
    dollars = cloud_dollars(total_in, total_out)
    per_thousand = dollars / n * 1000
    out += ["CLOUD EQUIVALENT (an estimate, not a bill)",
            "  " + CLOUD["name"] + ": $" + format(CLOUD["in_per_million"], ".2f") + " read / $"
            + format(CLOUD["out_per_million"], ".2f") + " written per million tokens (checked "
            + CLOUD["checked"] + ")",
            "  This run: $" + format(dollars, ".4f") + "   1,000 screenshots: $" + format(per_thousand, ".2f")
            + "   10,000: $" + format(per_thousand * 10, ".2f"),
            "  A cloud model counts an image in its own tokens: right size, not exact price.", ""]
    return out


def build(run_id, entries):
    n = len(entries)
    locked = sum(1 for e in entries if gate.is_locked(e.get("gate")))
    copies = sum(1 for e in entries if str(e.get("model", "")).startswith("code:"))
    name = set_name(run_id)
    out = ["COST  run " + str(run_id) + ("  set: " + name if name else ""),
           "Zippy " + _most_common([e.get("zippy_model") for e in entries]) + ", Pip "
           + _most_common([e.get("model") for e in entries]),
           str(n) + " screenshots: Zippy locked " + str(locked) + ", " + str(copies)
           + " exact copies (no Pip call), Pip answered " + str(n - locked - copies), ""]
    out += _time_lines(entries) + _token_lines(entries)
    local = schema.OLLAMA_URL.startswith(("http://localhost", "http://127.0.0.1"))
    out += ["STAYED ON THIS COMPUTER",
            ("  Every model call went to " + schema.OLLAMA_URL + " (this laptop)." if local
             else "  WARNING: OLLAMA_URL is not this computer: " + schema.OLLAMA_URL),
            "  " + str(n) + " screenshots read, " + str(locked) + " locked as sensitive, 0 uploaded."]
    return "\n".join(out)


def main(run_id=None):
    run_id, entries = trace.run(run_id) if run_id else trace.latest_run()
    if not entries:
        print("No run found" + (" with id " + str(run_id) if run_id else "") + ".")
        return
    report = build(run_id, entries)
    print(report)
    keep = schema.SCORE_REPORT.with_name("cost_" + (set_name(run_id) or "run") + "_" + str(run_id) + ".txt")
    keep.write_text(report + "\n", encoding="utf-8")
    print("\nSaved to golden/" + keep.name)
