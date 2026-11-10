# harness/router.py — Lane: Raaghavi (before the model)
# Sends one set of messages to one local model and returns its raw answer.
# Today the router is 1:1 (one model). Later it can choose light / heavy models.

import json
import urllib.request

from harness import schema


def ask(model, messages):
    """Return the model's raw text answer. Raises urllib errors or TimeoutError on failure."""
    body = {
        "model": model,
        "stream": False,
        "think": False,
        "format": schema.PROPOSAL_SHAPE,
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
