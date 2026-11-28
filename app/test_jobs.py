# app/test_jobs.py — Lane: Ana. Stage 2: the jobs (downloading, sorting, stopping) and their endpoints.
# Run:  python3 -m unittest app.test_jobs
# Uses a stand-in Ollama (it "downloads" in a moment) and a stand-in run.py that prints what the real one
# prints, so no models, internet or screenshots are needed.

import json
import sys
import tempfile
import textwrap
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from app import checks, jobs, shyft_app
from app.test_shyft_app import ZIPPY_ID, RICK_ID, model

ZIPPY, RICK = "gemma4:e4b-it-q4_K_M", "gemma4:e2b-it-q4_K_M"

# What the real run.py prints (its own lines), with file names that must never reach the screens.
STAND_IN = textwrap.dedent('''
    import sys, time
    if sys.argv[1:] != ["gemma4:e2b-it-q4_K_M", "all", "--zippy", "gemma4:e4b-it-q4_K_M"]:
        print("Stopped before x.png: wrong model names " + repr(sys.argv[1:])); sys.exit(0)
    print("Run r1: 2 screenshot(s), " + sys.argv[1])
    print("Nothing will be moved, renamed or deleted.\\n")
    print("WHERE YOUR FILES ARE")
    print("  Screenshots folder: not synced")
    print("")
    for n, name in ((1, "secret_bank.png"), (2, "cat.png")):
        print("[%d/2] %s ... Zippy is looking" % (n, name)); time.sleep(PAUSE)
    print("[1/2] secret_bank.png ... locked, Pip skips it")
    print("[2/2] cat.png ... Pip's turn")
    print("  Took 1.0 seconds\\n")
    if ENDING == "done":
        print("Done. Total 2.0 seconds. Trace saved to trace.jsonl")
    else:
        print("Stopped before cat.png: Ollama's cloud is on.")
''')


class Ollama:
    """Ollama with a pull that streams progress and then has the model."""
    def __init__(self, tags, cloud=True, pull_error=None):
        outer = self
        self.tags, self.cloud, self.pull_error, self.pulled = tags, cloud, pull_error, []

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_GET(self):
                body = {"/api/version": {"version": "0.40.17"}, "/api/status": {"cloud": {"disabled": outer.cloud}},
                        "/api/tags": {"models": outer.tags}}.get(self.path)
                self.send_response(200 if body is not None else 404); self.end_headers()
                self.wfile.write(json.dumps(body).encode())

            def do_POST(self):
                asked = json.loads(self.rfile.read(int(self.headers["Content-Length"])))["model"]
                outer.pulled.append(asked)
                self.send_response(200); self.end_headers()
                if outer.pull_error:
                    self.wfile.write(json.dumps({"error": outer.pull_error}).encode() + b"\n"); return
                for done in (0, 50, 100):
                    self.wfile.write(json.dumps({"status": "pulling", "digest": "sha256:a", "total": 100,
                                                 "completed": done}).encode() + b"\n")
                outer.tags.append(model(asked, ZIPPY_ID if asked == ZIPPY else RICK_ID))
                self.wfile.write(b'{"status":"success"}\n')
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.url = "http://127.0.0.1:" + str(self.server.server_address[1])

    def stop(self):
        self.server.shutdown(); self.server.server_close()


def wait_until_idle(seconds=10):
    end = time.time() + seconds
    while time.time() < end and jobs.snapshot().get("state") == "running":
        time.sleep(0.05)
    return jobs.snapshot()


class Base(unittest.TestCase):
    tags = [model(ZIPPY, ZIPPY_ID), model(RICK, RICK_ID)]
    cloud = True

    def setUp(self):
        self.ollama = Ollama(list(self.tags), self.cloud)
        self.saved = checks.OLLAMA, jobs.RUN, jobs.loaded_set
        checks.OLLAMA = self.ollama.url
        jobs.loaded_set = lambda: "synthetic"
        self.folder = tempfile.TemporaryDirectory()
        self.stand_in("done", 0)

    def tearDown(self):
        jobs.stop(); wait_until_idle()
        self.ollama.stop(); self.folder.cleanup()
        checks.OLLAMA, jobs.RUN, jobs.loaded_set = self.saved

    def stand_in(self, ending, pause):
        script = Path(self.folder.name) / ("run_%s_%s.py" % (ending, str(pause).replace(".", "")))
        script.write_text("ENDING, PAUSE = %r, %r\n" % (ending, pause) + STAND_IN, encoding="utf-8")
        jobs.RUN = str(script)


class Sorting(Base):
    def test_follows_run_py_to_the_end(self):
        started, _ = jobs.sort()
        self.assertTrue(started)
        job = wait_until_idle()
        self.assertEqual(job["state"], "done")
        self.assertEqual((job["total"], job["zippy_done"], job["done"]), (2, 2, 2))
        self.assertEqual(job["notice"][0], "WHERE YOUR FILES ARE")

    def test_uses_the_two_long_names(self):   # the stand-in stops unless it gets exactly these words (D27)
        jobs.sort(); job = wait_until_idle()
        self.assertEqual(job["state"], "done", job["message"])
        self.assertIn("Nothing was moved", job["message"])

    def test_no_file_names_reach_the_screen(self):
        for ending in ("done", "stopped"):
            self.stand_in(ending, 0)
            jobs.sort(); text = json.dumps(wait_until_idle())
            for name in ("secret_bank", "cat.png"):
                self.assertNotIn(name, text)

    def test_early_stop_uses_the_teams_words(self):
        self.stand_in("stopped", 0)
        jobs.sort(); job = wait_until_idle()
        self.assertEqual(job["state"], "failed")
        self.assertIn("Ollama's cloud is on.", job["message"])

    def test_one_job_at_a_time_and_stop(self):
        self.stand_in("done", 2)
        self.assertTrue(jobs.sort()[0])
        started, why = jobs.sort()
        self.assertFalse(started); self.assertIn("already busy", why)
        jobs.stop(); job = wait_until_idle()
        self.assertEqual(job["state"], "stopped")
        self.assertIn("Nothing was moved", job["message"])

    def test_refuses_the_real_set(self):
        jobs.loaded_set = lambda: "real"
        started, why = jobs.sort()
        self.assertFalse(started); self.assertIn("made-up test screenshots", why)


class ShortNames(Base):   # the Legion: the measured builds pulled under the short names
    tags = [model("gemma4:e4b", ZIPPY_ID), model("gemma4:e2b", RICK_ID)]

    def test_nothing_to_download(self):
        started, why = jobs.get_ready()
        self.assertFalse(started); self.assertEqual(why, "Nothing to download."); self.assertEqual(self.ollama.pulled, [])

    def test_run_py_gets_the_names_they_are_under(self):
        script = Path(self.folder.name) / "names.py"
        script.write_text('import sys\nprint("Stopped before x: " + " ".join(sys.argv[1:]))\n', encoding="utf-8")
        jobs.RUN = str(script)
        jobs.sort(); job = wait_until_idle()
        self.assertIn("gemma4:e2b all --zippy gemma4:e4b", job["message"])


class CloudOn(Base):
    cloud = False

    def test_refuses_before_starting(self):
        started, why = jobs.sort()
        self.assertFalse(started); self.assertIn("cloud is on", why)


class Downloading(Base):
    tags = [model(ZIPPY, ZIPPY_ID)]

    def test_downloads_only_whats_missing(self):
        started, job = jobs.get_ready()
        self.assertTrue(started); self.assertEqual(job["gb_total"], 4.6)
        job = wait_until_idle()
        self.assertEqual(job["state"], "done", job)
        self.assertEqual(self.ollama.pulled, [RICK])

    def test_refuses_to_sort_while_a_model_is_missing(self):
        started, why = jobs.sort()
        self.assertFalse(started); self.assertIn("Get Shyft ready", why)

    def test_a_download_error_is_plain_words(self):
        self.ollama.pull_error = "connection reset"
        jobs.get_ready(); job = wait_until_idle()
        self.assertEqual(job["state"], "failed"); self.assertIn("carries on where it stopped", job["message"])


class WrongBuild(Base):
    tags = [model(ZIPPY, ZIPPY_ID), model(RICK, "000000000000")]

    def test_never_replaces_someones_model(self):
        started, why = jobs.get_ready()
        self.assertFalse(started); self.assertEqual(self.ollama.pulled, [])


class Endpoints(Base):
    """The new POST endpoints keep Stage 1's rules: the key and our own Origin."""
    def setUp(self):
        super().setUp()
        self.server, address, self.key = shyft_app.serve(open_browser=False)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.base = "http://127.0.0.1:" + str(self.server.server_address[1])

    def tearDown(self):
        self.server.shutdown(); self.server.server_close()
        super().tearDown()

    def post(self, path, key=True, origin=True):
        import urllib.request, urllib.error
        req = urllib.request.Request(self.base + path, method="POST", data=b"")
        if key:
            req.add_header("X-Shyft-Key", self.key)
        if origin:
            req.add_header("Origin", self.base)
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status
        except urllib.error.HTTPError as e:
            e.close(); return e.code

    def test_need_the_key_and_our_origin(self):
        for path in ("/api/run", "/api/get-ready", "/api/stop"):
            self.assertEqual(self.post(path, key=False), 403, path)
            self.assertEqual(self.post(path, origin=False), 403, path)
        self.assertNotEqual(jobs.snapshot().get("state"), "running")

    def test_run_then_busy_then_quit_stops_it(self):
        self.stand_in("done", 2)
        self.assertEqual(self.post("/api/run"), 200)
        self.assertEqual(self.post("/api/run"), 409)
        self.assertEqual(self.post("/api/quit"), 200)
        self.assertEqual(wait_until_idle()["state"], "stopped")


if __name__ == "__main__":
    unittest.main()
