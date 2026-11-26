# app/test_shyft_app.py — Lane: Ana. Stage 1: the server's safety rules and its status answer.
# Run:  python -m unittest app.test_shyft_app      (Mac: python3 ...)
# Uses a stand-in Ollama on this computer, so no models or internet are needed.

import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from app import checks, shyft_app

ZIPPY_ID, RICK_ID = "dc35e8d9c606", "b37049369adf"


class FakeOllama:
    """Answers like Ollama: /api/version, /api/status (cloud), /api/tags (models with digests)."""
    def __init__(self, tags, cloud=True):
        outer = self
        self.tags, self.cloud = tags, cloud

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_GET(self):
                if self.path == "/api/status" and outer.cloud is None:   # an Ollama older than 0.40.17
                    self.send_response(404); self.end_headers(); return
                body = {"/api/version": {"version": "0.40.17"},
                        "/api/status": {"cloud": {"disabled": outer.cloud}},
                        "/api/tags": {"models": outer.tags}}.get(self.path)
                data = json.dumps(body).encode()
                self.send_response(200 if body is not None else 404); self.end_headers(); self.wfile.write(data)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.url = "http://127.0.0.1:" + str(self.server.server_address[1])

    def stop(self):
        self.server.shutdown(); self.server.server_close()


def model(name, id12):
    return {"name": name, "digest": id12 + "0" * 52}


class Base(unittest.TestCase):
    def setUp(self):
        self.ollama = FakeOllama([model("gemma4:e4b-it-q4_K_M", ZIPPY_ID), model("gemma4:e2b-it-q4_k_m", "000000000000")])
        self.old = checks.OLLAMA
        checks.OLLAMA = self.ollama.url
        self.server, self.address, self.key = shyft_app.serve(open_browser=False)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.base = "http://127.0.0.1:" + str(self.server.server_address[1])

    def tearDown(self):
        self.server.shutdown(); self.server.server_close(); self.ollama.stop()
        checks.OLLAMA = self.old

    def get(self, path, key=None, host=None, method="GET"):
        req = urllib.request.Request(self.base + path, method=method, data=b"" if method == "POST" else None)
        if key:
            req.add_header("X-Shyft-Key", key)
        if host:
            req.add_header("Host", host)
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()


class Safety(Base):
    def test_listens_on_this_computer_only(self):
        self.assertEqual(self.server.server_address[0], "127.0.0.1")

    def test_api_needs_the_key(self):
        self.assertEqual(self.get("/api/status")[0], 403)
        self.assertEqual(self.get("/api/status", key="wrong")[0], 403)
        self.assertEqual(self.get("/api/status", key=self.key)[0], 200)

    def test_other_host_names_are_refused(self):   # DNS rebinding: a website renamed to point here
        self.assertEqual(self.get("/api/status", key=self.key, host="evil.example:80")[0], 403)
        self.assertEqual(self.get("/index.html", host="localhost")[0], 403)

    def test_serves_ui_files_only(self):
        self.assertEqual(self.get("/index.html")[0], 200)
        for path in ("/../shyft_requirements.json", "/%2e%2e/run.py", "/../app/shyft_app.py", "/ui", "/README.md"):
            self.assertEqual(self.get(path)[0], 404, path)

    def test_the_address_carries_the_key(self):
        self.assertIn("?k=" + self.key, self.address)
        self.assertTrue(self.address.startswith("http://127.0.0.1:"))

    def test_quit_needs_the_key(self):
        self.assertEqual(self.get("/api/quit", method="POST")[0], 403)


class Status(Base):
    def status(self):
        code, body = self.get("/api/status", key=self.key)
        self.assertEqual(code, 200)
        return json.loads(body)

    def test_numbers_come_from_the_requirements_file(self):
        req = json.loads(checks.REQUIREMENTS.read_text(encoding="utf-8"))
        s = self.status()["requirements"]
        self.assertEqual(s["memory_gb"], req["floor"]["memory_gb"])
        self.assertEqual(s["download_gb"], req["shape"]["download_gb_total"])
        self.assertEqual([m["pull"] for m in s["models"]], [req["shape"]["gate"]["pull"], req["shape"]["namer"]["pull"]])

    def test_ids_are_checked_not_just_names(self):   # D27: a name can be re-pointed, an id can't
        zippy, rick = self.status()["models"]
        self.assertTrue(zippy["found"] and zippy["matches"])
        self.assertTrue(rick["found"])                # found despite other upper/lower case...
        self.assertFalse(rick["matches"])             # ...but a different build

    def test_rick_not_pip_on_screen(self):
        names = [m["buddy"] for m in self.status()["requirements"]["models"]]
        self.assertEqual(names, ["Zippy", "Rick"])

    def test_cloud_setting(self):
        self.assertEqual(self.status()["ollama"]["cloud"], "off")
        self.ollama.cloud = False
        self.assertEqual(self.status()["ollama"]["cloud"], "on")
        self.ollama.cloud = None
        self.assertEqual(self.status()["ollama"]["cloud"], "too_old")

    def test_ollama_not_running(self):
        self.ollama.stop()
        s = self.status()
        self.assertFalse(s["ollama"]["running"])
        self.assertFalse(any(m["found"] for m in s["models"]))
        self.ollama = FakeOllama([])   # so tearDown has something to stop

    def test_space_needed_counts_only_whats_missing(self):
        s = self.status()   # Zippy found (6.6), Rick "found" too (wrong build, but on disk): only spare left
        self.assertEqual(s["requirements"]["need_now_gb"], 2)


if __name__ == "__main__":
    unittest.main()
