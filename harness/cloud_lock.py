# harness/cloud_lock.py — Lane: Sphinx. S18: no model call Shyft makes leaves this computer.
# It sits at the one door every model call goes through (harness/router.py: Zippy, Rick and
# the dev tools all use router.ask). Nothing can go around it.
#
# Before the first call to each model in a run:
#   1. Ollama itself says its cloud is OFF (/api/status). A setting in a file is a promise;
#      the running server's answer is the fact. Not in Ollama's docs; there since 0.40.17.
#   2. The model's name is not a cloud name (":cloud" or a tag ending "-cloud").
#   3. Ollama's own model list gives it no remote host. A cloud model can be copied under
#      any name (lesson 18: a name is not the file), so the list decides, not the name.
# After every call:
#   4. Ollama's reply names no remote host: the answer came from this computer.
# Any failed check REFUSES. Before a call, nothing is sent. The run stops with plain words.
# It blocks cloud models only: any model that runs here (Qwen included) passes.
# Checking that it is the MEASURED file (the D27 id) is a different job, kept apart.

import json
import urllib.error
import urllib.request

from harness import schema

TURN_IT_OFF = ("To turn Ollama's cloud off: in your home folder, open the folder .ollama and "
               "put this line in a file called server.json (make the file if it isn't there): "
               "{\"disable_ollama_cloud\": true}  Then quit Ollama completely and open it again.")

_cloud_off = False    # Ollama said its cloud is off (asked once per run)
_cleared = set()      # models checked against Ollama's list in this run


class Refused(Exception):
    """A check failed. The message says, in plain words, what happened and what to do."""


def forget():
    """Start fresh: the next call asks Ollama again. Every run is a new program, so it
    starts fresh anyway; this is for the tests."""
    global _cloud_off
    _cloud_off = False
    _cleared.clear()


def _get(url):
    with urllib.request.urlopen(url, timeout=schema.SERVER_TIMEOUT_SECONDS) as response:
        return json.loads(response.read().decode("utf-8"))


def looks_like_cloud(name):
    """True for Ollama's cloud names: "gemma4:cloud", "gpt-oss:120b-cloud" (any case)."""
    last = str(name).strip().lower().rsplit("/", 1)[-1]   # a registry's ":5000" is not a tag
    tag = last.rsplit(":", 1)[-1] if ":" in last else ""
    return tag == "cloud" or tag.endswith("-cloud") or last.endswith("-cloud")


def status_problem(status):
    """None if Ollama's /api/status answer says its cloud is off, else what is wrong."""
    cloud = status.get("cloud") if isinstance(status, dict) else None
    if not isinstance(cloud, dict) or "disabled" not in cloud:
        return "Ollama didn't say whether its cloud is off, so Shyft can't promise local-only."
    if cloud["disabled"] is not True:
        return "Ollama's cloud is ON, so a model call could leave this computer. " + TURN_IT_OFF
    return None


def model_problem(model, listing):
    """None if Ollama's list gives `model` no remote host. Not listed = not ours to judge:
    the call then fails with "not downloaded", which already stops the run."""
    for item in (listing or {}).get("models") or []:
        names = (item.get("name"), item.get("model"))
        if model in names or model + ":latest" in names:
            if item.get("remote_host") or item.get("remote_model"):
                return ("'" + model + "' runs on another computer (" + str(item.get("remote_host"))
                        + "), whatever it is called. Use a model downloaded to this computer.")
    return None


def before(model):
    """Run checks 1-3 for `model`, once per run. Raises Refused; nothing has been sent."""
    global _cloud_off
    if looks_like_cloud(model):
        raise Refused("'" + model + "' is a cloud model: it would send screenshots to Ollama's "
                      "servers. Shyft only uses models that run on this computer.")
    if not _cloud_off:
        try:
            problem = status_problem(_get(schema.OLLAMA_STATUS_URL))
        except urllib.error.HTTPError as error:
            error.close()   # an unclosed error object prints a warning on newer Pythons
            problem =("This Ollama can't tell Shyft whether its cloud is off (answer "
                       + str(error.code) + "). Update Ollama from ollama.com/download.")
        if problem:
            raise Refused(problem)
        _cloud_off = True
    if model not in _cleared:
        problem = model_problem(model, _get(schema.OLLAMA_TAGS_URL))
        if problem:
            raise Refused(problem)
        _cleared.add(model)


def after(model, reply):
    """Check 4, after every call: the answer came from this computer, not a remote host."""
    if isinstance(reply, dict) and (reply.get("remote_host") or reply.get("remote_model")):
        raise Refused("Ollama answered '" + model + "' from another computer ("
                      + str(reply.get("remote_host")) + "), so this screenshot may have left "
                      "this computer. The run stopped and nothing was saved for it. " + TURN_IT_OFF)
