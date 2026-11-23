# harness/router.py — Lane: Raaghavi (before the model)
# Sends one set of messages to one local model and returns its raw answer.
# The answer shape decides who is speaking: Pip's proposal (default) or Zippy's verdict.
# S11: every Ollama reply also says how many tokens the model read and wrote and how long
# each part took. We used to throw that away. Now the last call's numbers are kept until
# the pipeline collects them with take_usage(). ask() still returns only the text, so
# nothing that calls it (gate.py, pipeline.py, the tests) had to change.

import json
import urllib.request

from harness import schema

_last_usage = None   # the most recent call's numbers, until take_usage() collects them


def _seconds(reply, key):
    """Ollama reports durations in nanoseconds. Return seconds, or None if it left it out."""
    value = reply.get(key)
    return round(value / 1e9, 2) if isinstance(value, (int, float)) else None


def usage_from(reply):
    """Ollama's own counters from one reply. Anything missing stays None: never guessed."""
    return {
        "tokens_in": reply.get("prompt_eval_count"),               # tokens the model read
        "tokens_out": reply.get("eval_count"),                     # tokens it wrote
        "load_seconds": _seconds(reply, "load_duration"),          # loading the model
        "read_seconds": _seconds(reply, "prompt_eval_duration"),   # reading prompt + image
        "write_seconds": _seconds(reply, "eval_duration"),         # writing the answer
        "ollama_seconds": _seconds(reply, "total_duration"),       # all of it, inside Ollama
    }


def take_usage():
    """Return the last call's numbers once, then forget them. None if no call finished."""
    global _last_usage
    usage, _last_usage = _last_usage, None
    return usage


def ask(model, messages, shape=None):
    """Return the model's raw text answer. Raises urllib errors or TimeoutError on failure."""
    global _last_usage
    _last_usage = None        # a failed call must never leave the previous call's numbers
    body = {
        "model": model,
        "stream": False,
        "think": False,
        "format": shape or schema.PROPOSAL_SHAPE,
        "options": {"temperature": 0},
        "messages": messages,
    }
    request = urllib.request.Request(
        schema.OLLAMA_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=schema.CALL_TIMEOUT_SECONDS) as response:
        reply = json.loads(response.read().decode("utf-8"))
    _last_usage = usage_from(reply)
    return reply["message"]["content"]
