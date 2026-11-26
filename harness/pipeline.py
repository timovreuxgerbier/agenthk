# harness/pipeline.py — what happens to ONE screenshot, in order (D20: order A).
#   1. look():   Zippy (gate.py) looks first. Any kind but "none" LOCKS it.
#   2. finish(): a locked file gets its trace line and nothing else. Otherwise: exact copy
#                of an older screenshot (code, no Pip call), or Pip (spec.md) describes,
#                names and proposes; then the code check, the gated rename (D18) and one
#                redacted trace line (trace.py).
# handle() = look() then finish() for one file: the order before S14 (--one-by-one).
# S14: harness/batch.py calls look() on a chunk of files, then finish() on the same chunk,
# so each model loads once per chunk. Same steps, same answers, same trace lines.
# S10: Zippy may run on its own model. S11: router.take_usage() after each model call.

import json
import time
import urllib.error

from harness import check, cloud_lock, context, gate, naming, router, trace

STOP = "stop"   # a run cap was reached; the loop ends cleanly


class Stopped(Exception):
    """Ollama can't be reached or the model is missing: the whole run ends."""


def _call(model, ask, *args):
    try:
        return ask(*args)
    except cloud_lock.Refused as problem:      # S18: the whole run ends, in plain words
        raise Stopped("CLOUD LOCK: " + str(problem))
    except urllib.error.HTTPError as error:
        if error.code == 404:
            raise Stopped("The model isn't downloaded. In a terminal run: ollama pull " + model)
        raise Stopped("Ollama returned an error: " + str(error.code) + " "
                      + error.read().decode("utf-8", "replace"))
    except urllib.error.URLError:
        raise Stopped("Can't reach Ollama. Start it (ollama serve), then run this again.")


def _zippy(model, instructions, image, limits):
    limits.record_call()
    try:
        return _call(model, gate.ask, model, instructions, image)
    except TimeoutError:
        return {"kind": gate.GATE_ERROR, "confidence": None}   # fail closed


def show(proposal, problems, flagged, file_name, verdict):
    if proposal is None:
        print("  REJECTED by code check: " + ", ".join(problems))
        return
    print("  Action:      " + str(proposal.get("action")))
    new_name = naming.gated_rename(proposal, file_name, verdict)
    if new_name:
        print("  Rename to:   " + new_name + "  (name had no meaning)")
    if proposal.get("action") == "sensitive":
        print("  (Pip called it sensitive: its description is not shown or stored.)")
    else:
        print("  Reason:      " + str(proposal.get("reason")))
        print("  Why saved:   " + str(proposal.get("why_saved_guess")) + "  (a guess)")
    print("  Confidence:  " + str(proposal.get("confidence")))
    if problems:
        print("  CODE CHECK:  " + ", ".join(problems))
    if flagged:
        print("  FLAGGED for review: the agent is unsure.")


def _finish(entry, started):
    """Seconds = Zippy's seconds + this step's, so batching doesn't change the measure."""
    entry["seconds"] = round(entry["zippy_seconds"] + time.time() - started, 1)
    entry["time"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    trace.write(entry)
    print("  Took " + str(entry["seconds"]) + " seconds\n")


def look(label, image, model, zippy_model, texts, limits, run_id):
    """Zippy's step for one screenshot. Returns the trace entry so far, or STOP."""
    stop = limits.check()
    if stop:
        print("Stopped before " + image.name + ": " + stop + "\n")
        return STOP
    print(label + " ... Zippy is looking")
    started = time.time()
    verdict = _zippy(zippy_model, texts["zippy"], image, limits)
    entry = {"run_id": run_id, "file": image.name, "model": model, "zippy_model": zippy_model,
             "zippy_seconds": round(time.time() - started, 1), "gate": verdict,
             "zippy_usage": router.take_usage(), "pip_usage": None,
             "check_problems": [], "flagged": False, "user_decision": None}
    if gate.is_locked(verdict):
        print("  Zippy:       LOCKED (" + verdict["kind"] + ", " + str(verdict["confidence"])
              + "). Pip never saw it. No rename.")
    else:
        print("  Zippy:       clear (" + str(verdict["confidence"]) + ")")
    return entry


def finish(label, image, entry, model, texts, copies, limits, announce=False):
    """Everything after Zippy for one screenshot. Returns STOP when a cap is reached.
    announce=True prints the file's label again (batch.py: Zippy's line was a while ago)."""
    started = time.time()
    verdict = entry["gate"]
    if announce:
        print(label + " ... " + ("locked, Pip skips it" if gate.is_locked(verdict) else "Pip's turn"))
    if gate.is_locked(verdict):
        entry["raw_output"] = json.dumps({"action": "sensitive",
                                          "confidence": verdict["confidence"]})
        return _finish(entry, started)

    if image in copies:
        print("  Exact copy of " + copies[image] + ", no Pip call")
        entry["model"] = "code: exact copy"
        entry["raw_output"] = json.dumps({"reason": "Exact copy of " + copies[image] + ".",
                                          "why_saved_guess": "Probably taken twice by accident (a guess).",
                                          "action": "to_be_deleted", "confidence": 1.0})
        proposal, entry["check_problems"] = check.check_proposal(entry["raw_output"])
        show(proposal, entry["check_problems"], False, image.name, verdict)
        return _finish(entry, started)

    stop = limits.check()
    if stop:
        print("  Stopped before Pip: " + stop + "\n")
        return STOP
    print("  Pip is thinking")
    limits.record_call()
    try:
        raw = _call(model, router.ask, model, context.build_messages(texts["pip"], image))
        entry["pip_usage"] = router.take_usage()
    except TimeoutError:
        print("  Pip took over 5 minutes and was stopped. Skipping this one.\n")
        return None
    proposal, problems = check.check_proposal(raw)
    rename_problem = naming.rename_problem(proposal, image.name)
    if rename_problem:
        problems.append(rename_problem)
    flagged = check.is_flagged(proposal, problems)
    show(proposal, problems, flagged, image.name, verdict)
    entry.update({"raw_output": raw, "check_problems": problems, "flagged": flagged})
    return _finish(entry, started)


def handle(label, image, model, texts, copies, limits, run_id, zippy_model=None):
    """Zippy then Pip for one screenshot (the order before S14). Returns STOP at a cap.
    model is Pip's model; zippy_model is Zippy's (S10). None means the same as Pip's."""
    entry = look(label, image, model, zippy_model or model, texts, limits, run_id)
    if entry == STOP:
        return STOP
    return finish(label, image, entry, model, texts, copies, limits)
