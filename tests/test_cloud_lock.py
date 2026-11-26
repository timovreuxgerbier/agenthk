# tests/test_cloud_lock.py — Lane: Sphinx. S18: the cloud lock.
#   python3 -m unittest tests.test_cloud_lock
# No model needed: Ollama's answers are stand-ins.
# 1. Cloud names are refused; local names pass (a registry's ":5000" is not a tag).
# 2. Ollama must SAY its cloud is off; on, unclear or too old all refuse.
# 3. A cloud model under a local-looking name is caught by Ollama's own list.
# 4. With cloud on, the chat call is never sent; with cloud off, Ollama is asked once per run.
# 5. A reply from a remote host stops the run; in the pipeline every refusal becomes a stop.

import json
import unittest
import urllib.error
from unittest import mock

from harness import cloud_lock, pipeline, router, schema

OFF = {"cloud": {"disabled": True, "source": "config"}}
ON = {"cloud": {"disabled": False, "source": "none"}}
CHAT = {"message": {"content": "{}"}, "prompt_eval_count": 1, "eval_count": 1}
ALIAS = {"models": [{"name": "my-local:latest", "model": "my-local:latest",
                     "remote_host": "https://ollama.com:443", "remote_model": "gpt-oss:120b"}]}


class Reply:
    def __init__(self, data):
        self.data = json.dumps(data).encode("utf-8")

    def read(self):
        return self.data

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def fake(status=OFF, tags=None, chat=CHAT, asked=None):
    """A stand-in Ollama. `asked` collects every address our code called."""
    def urlopen(request, timeout=None):
        url = request if isinstance(request, str) else request.full_url
        if asked is not None:
            asked.append(url)
        if url == schema.OLLAMA_STATUS_URL:
            if status == 404:
                raise urllib.error.HTTPError(url, 404, "not found", None, None)
            return Reply(status)
        if url == schema.OLLAMA_TAGS_URL:
            return Reply(tags or {"models": []})
        if url in (schema.OLLAMA_PS_URL, schema.OLLAMA_VERSION_URL):
            return Reply({})
        return Reply(chat)
    return urlopen


class TestNames(unittest.TestCase):
    def test_cloud_names_are_caught(self):
        for name in ("gemma4:cloud", "GEMMA4:Cloud", "gpt-oss:120b-cloud", "qwen3-coder-cloud"):
            self.assertTrue(cloud_lock.looks_like_cloud(name), name)

    def test_local_names_pass(self):
        for name in ("gemma4:e4b", "gemma4:e2b-it-q4_K_M", "qwen3.8", "qwen-zippy:latest",
                     "registry.example.com:5000/gemma4"):
            self.assertFalse(cloud_lock.looks_like_cloud(name), name)


class TestOllamaMustSaySo(unittest.TestCase):
    def test_only_a_clear_off_passes(self):
        self.assertIsNone(cloud_lock.status_problem(OFF))
        self.assertIn("ON", cloud_lock.status_problem(ON))
        self.assertIn("didn't say", cloud_lock.status_problem({"version": "0.40.17"}))
        self.assertIn("didn't say", cloud_lock.status_problem(None))

    def test_an_ollama_without_the_answer_is_told_to_update(self):
        cloud_lock.forget()
        with mock.patch.object(router.urllib.request, "urlopen", fake(status=404)):
            with self.assertRaisesRegex(cloud_lock.Refused, "Update Ollama"):
                cloud_lock.before("gemma4:e4b")


class TestTheListDecides(unittest.TestCase):
    def test_a_cloud_model_under_a_local_name_is_refused(self):
        self.assertIn("another computer", cloud_lock.model_problem("my-local", ALIAS))
        self.assertIsNone(cloud_lock.model_problem("gemma4:e4b", ALIAS))   # not listed: not ours


class TestTheDoor(unittest.TestCase):
    def setUp(self):
        cloud_lock.forget()

    def test_with_cloud_on_nothing_is_sent(self):
        asked = []
        with mock.patch.object(router.urllib.request, "urlopen", fake(status=ON, asked=asked)):
            with self.assertRaises(cloud_lock.Refused):
                router.ask("gemma4:e4b", [])
        self.assertNotIn(schema.OLLAMA_URL, asked)

    def test_with_cloud_off_ollama_is_asked_once(self):
        asked = []
        with mock.patch.object(router.urllib.request, "urlopen", fake(asked=asked)):
            self.assertEqual(router.ask("gemma4:e4b", []), "{}")
            router.ask("gemma4:e4b", [])
        self.assertEqual(asked.count(schema.OLLAMA_STATUS_URL), 1)
        self.assertEqual(asked.count(schema.OLLAMA_URL), 2)

    def test_a_reply_from_a_remote_host_stops(self):
        remote = dict(CHAT, remote_host="https://ollama.com:443")
        with mock.patch.object(router.urllib.request, "urlopen", fake(chat=remote)):
            with self.assertRaisesRegex(cloud_lock.Refused, "may have left"):
                router.ask("gemma4:e4b", [])

    def test_in_the_pipeline_a_refusal_ends_the_run(self):
        def refuses(*args):
            raise cloud_lock.Refused("cloud is on")
        with self.assertRaisesRegex(pipeline.Stopped, "CLOUD LOCK: cloud is on"):
            pipeline._call("gemma4:e4b", refuses)


if __name__ == "__main__":
    unittest.main()
