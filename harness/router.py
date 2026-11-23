# harness/router.py — Lane: Raaghavi (before the model)
# Sends one set of messages to one local model and returns its raw answer.
# The answer shape decides who is speaking: Pip's proposal (default) or Zippy's verdict.

import json
import urllib.request

from harness import schema


def ask(model, messages, shape=None):
    """Return the model's raw text answer. Raises urllib errors or TimeoutError on failure."""
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
    return reply["message"]["content"]
