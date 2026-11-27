# app/test_shyft_app.py — Lane: Ana. Stage 1: the server's safety rules and its status answer.
# Run:  python3 -m unittest app.test_shyft_app
# Uses a stand-in Ollama on this computer, so no models or internet are needed.

import ast
import json
import sys
import tempfile
import threading
import types
import unittest
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from app import checks, shyft_app

ZIPPY_ID, RICK_ID = "dc35e8d9c606", "b37049369adf"
APP = Path(__file__).resolve().parent


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

    def get(self, path, key=None, host=None, method="GET", headers=None):
        req = urllib.request.Request(self.base + path, method=method, data=b"" if method == "POST" else None)
        if key:
            req.add_header("X-Shyft-Key", key)
        if host:
            req.add_header("Host", host)
        for k, v in (headers or {}).items():
            req.add_header(k, v)
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status, r.read(), r.headers
        except urllib.error.HTTPError as e:
            body = e.read()
            e.close()
            return e.code, body, e.headers


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

    def test_other_websites_get_nothing(self):   # Sphinx's test: a page elsewhere loading our files as <script>
        for site in ("cross-site", "same-site"):
            for path in ("/index.html", "/live.js", "/sample_review.js", "/review_data.js"):
                self.assertEqual(self.get(path, headers={"Sec-Fetch-Site": site})[0], 403, (site, path))
        self.assertEqual(self.get("/api/status", key=self.key, headers={"Sec-Fetch-Site": "cross-site"})[0], 403)
        self.assertEqual(self.get("/index.html", headers={"Sec-Fetch-Site": "none"})[0], 200)          # typed in the address bar
        self.assertEqual(self.get("/live.js", headers={"Sec-Fetch-Site": "same-origin"})[0], 200)      # our own page

    def test_real_review_data_is_never_a_file(self):
        for name in ("review_data.js", "start.html", "start_buddies.js", "open_results.html"):
            self.assertEqual(self.get("/" + name)[0], 404, name)

    def test_strict_content_security_policy(self):
        csp = self.get("/index.html")[2]["Content-Security-Policy"]
        self.assertIn("default-src 'self'", csp)
        self.assertIn("script-src 'self'", csp)
        self.assertNotIn("unsafe-inline'; img", csp.split("script-src")[1].split(";")[0] + "; img")   # no inline script
        self.assertIn("frame-ancestors 'none'", csp)

    def test_no_inline_script_in_the_app_page(self):   # the policy would block it: keep it in files
        page = (checks.ROOT / "ui" / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("<script>", page)
        self.assertNotRegex(page, r"\son[a-z]+=\"")

    def test_serves_ui_files_only(self):
        self.assertEqual(self.get("/index.html")[0], 200)
        for path in ("/../shyft_requirements.json", "/%2e%2e/run.py", "/../app/shyft_app.py", "/ui", "/README.md"):
            self.assertEqual(self.get(path)[0], 404, path)

    def test_the_address_carries_the_key(self):
        self.assertIn("?k=" + self.key, self.address)
        self.assertTrue(self.address.startswith("http://127.0.0.1:"))

    def test_quit_needs_the_key_and_our_origin(self):
        self.assertEqual(self.get("/api/quit", method="POST")[0], 403)
        self.assertEqual(self.get("/api/quit", key=self.key, method="POST")[0], 403)   # no Origin
        self.assertEqual(self.get("/api/quit", key=self.key, method="POST", headers={"Origin": "http://evil.example"})[0], 403)
        self.assertEqual(self.get("/api/quit", key=self.key, method="POST", headers={"Origin": self.base})[0], 200)


class Status(Base):
    def status(self):
        code, body, _ = self.get("/api/status", key=self.key)
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

    def test_cloud_setting_and_the_locks_own_words(self):
        self.assertEqual(self.status()["ollama"]["cloud"], "off")
        self.ollama.cloud = False
        s = self.status()["ollama"]
        self.assertEqual(s["cloud"], "on")
        try:
            from harness.cloud_lock import TURN_IT_OFF
            self.assertEqual(s["cloud_fix"], TURN_IT_OFF)   # never retyped
        except ImportError:
            self.assertTrue(s["cloud_fix"])
        self.ollama.cloud = None
        self.assertEqual(self.status()["ollama"]["cloud"], "too_old")

    def test_the_screens_never_call_cloud_on_ready(self):   # Sphinx's must-fix 1
        js = (checks.ROOT / "ui" / "setup.js").read_text(encoding="utf-8")
        self.assertIn('o.cloud === "on" ? "cloudon"', js)
        self.assertNotIn("will run it with the cloud off", js)

    def test_ollama_not_running(self):
        self.ollama.stop()
        s = self.status()
        self.assertFalse(s["ollama"]["running"])
        self.assertFalse(any(m["found"] for m in s["models"]))
        self.ollama = FakeOllama([])   # so tearDown has something to stop

    def test_space_needed_counts_a_different_build_as_missing(self):
        s = self.status()   # Zippy right; Rick a different build, so Rick's 4.6 GB must still come, plus 2 spare
        req = json.loads(checks.REQUIREMENTS.read_text(encoding="utf-8"))
        self.assertEqual(s["requirements"]["need_now_gb"], round(req["floor"]["free_disk_parts_gb"]["spare"] + req["shape"]["namer"]["download_gb"], 1))
        self.assertEqual(s["meets"]["disk"], s["computer"]["free_disk_gb"] >= s["requirements"]["need_now_gb"])


class Review(Base):
    def test_no_records_module_means_no_review(self):
        code, body, _ = self.get("/api/review", key=self.key)
        if "harness.records" not in sys.modules and code == 404:
            self.assertEqual(json.loads(body)["error"], "No review yet.")

    def test_review_comes_from_records_only(self):   # stage 0.3: harness/records.py finds the file
        with tempfile.TemporaryDirectory() as tmp:
            review = Path(tmp) / "review.json"
            review.write_text(json.dumps({"contract_version": "0.2", "items": [{"id": "a"}]}), encoding="utf-8")
            fake = types.ModuleType("harness.records")
            fake.review_to_read = lambda: review
            import harness
            saved = sys.modules.get("harness.records"), getattr(harness, "records", None)
            sys.modules["harness.records"] = fake
            harness.records = fake
            try:
                code, body, _ = self.get("/api/review", key=self.key)
                self.assertEqual(code, 200)
                self.assertEqual(json.loads(body)["items"], [{"id": "a"}])
                self.assertEqual(self.get("/api/review")[0], 403)        # the key, as everywhere
                fake.review_to_read = lambda: None
                self.assertEqual(self.get("/api/review", key=self.key)[0], 404)
            finally:
                if saved[0] is None:
                    sys.modules.pop("harness.records", None)
                else:
                    sys.modules["harness.records"] = saved[0]
                if saved[1] is None:
                    if hasattr(harness, "records"):
                        delattr(harness, "records")
                else:
                    harness.records = saved[1]


class D38(unittest.TestCase):
    """app/ writes, moves, renames and deletes nothing, and builds no path to a person's files or to
    Shyft's home. Read every app/ file (not this test) and look at what it calls."""
    CHANGES_FILES = {"write_text", "write_bytes", "mkdir", "makedirs", "rename", "renames", "unlink", "rmdir",
                     "remove", "removedirs", "rmtree", "move", "copy", "copy2", "copyfile", "copytree", "chmod",
                     "touch", "symlink_to", "hardlink_to", "truncate"}
    PERSONAL = {"home", "expanduser", "USERPROFILE", "HOMEDRIVE", "HOMEPATH", "LOCALAPPDATA", "APPDATA", "HOME"}

    def files(self):
        return [p for p in APP.glob("*.py") if p.name != Path(__file__).name]

    def test_changes_no_files(self):
        for path in self.files():
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if isinstance(node, ast.Call):
                    f = node.func
                    name = f.attr if isinstance(f, ast.Attribute) else f.id if isinstance(f, ast.Name) else ""
                    self.assertNotIn(name, self.CHANGES_FILES, f"{path.name}:{node.lineno} calls {name}")
                    if isinstance(f, ast.Attribute) and f.attr == "replace" and isinstance(f.value, ast.Name) and f.value.id in ("os", "shutil"):
                        self.fail(f"{path.name}:{node.lineno} calls {f.value.id}.replace")
                    if name == "open":   # reading only
                        modes = [a.value for a in node.args[1:2] if isinstance(a, ast.Constant)] + \
                                [k.value.value for k in node.keywords if k.arg == "mode" and isinstance(k.value, ast.Constant)]
                        for mode in modes:
                            self.assertFalse(set(str(mode)) & set("wax+"), f"{path.name}:{node.lineno} opens to write")

    def test_builds_no_personal_or_home_path(self):
        for path in self.files():
            text = path.read_text(encoding="utf-8")
            for node in ast.walk(ast.parse(text)):
                name = node.attr if isinstance(node, ast.Attribute) else node.id if isinstance(node, ast.Name) else None
                if name:
                    self.assertNotIn(name, self.PERSONAL, f"{path.name}:{node.lineno} uses {name}")
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    for word in ("Nook", "Shyft's records", "%USERPROFILE%", "~/"):
                        self.assertNotIn(word, node.value, f"{path.name}:{node.lineno} names {word!r}")


if __name__ == "__main__":
    unittest.main()
