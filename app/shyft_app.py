# app/shyft_app.py — Lane: Ana. Stages 1 and 2 of the Windows app plan: Shyft's screens, with real answers.
#
#   python3 app/shyft_app.py
#
# Opens Shyft's screens (ui/) in your browser, and answers them with what is true on this computer
# (app/checks.py). Stage 2 adds jobs (app/jobs.py), one at a time: downloading missing model files through
# Ollama, and starting the team's run.py on the made-up test set. Still nothing is moved or deleted:
# run.py only proposes.
# Close this window, or press Ctrl+C, to stop it.
#
# Safety rules (plan, section 6; D38):
# - Listens on 127.0.0.1 only, never on the network, on a port picked at random each time.
# - A secret key, made at start, is in the address the browser opens. Every /api/ request must carry it
#   (header X-Shyft-Key), so no other website or program can ask this server anything.
# - The Host header must be this exact address, so a website can't reach it by renaming itself (DNS rebinding).
# - Requests from other websites are refused, files included: browsers label every request with
#   Sec-Fetch-Site, and anything but "same-origin" (our own page) or "none" (typed into the address bar)
#   is turned away. A POST must also carry our own Origin.
# - Serves only Shyft's screens from ui/, read-only, never review_data.js (a review's real words come
#   only through the keyed /api/review). Never takes a file path from the browser.
# - A strict Content-Security-Policy: only our own script files run, nothing loads from elsewhere.
# - Builds no path to a person's files or the home: Shyft's records are found by harness/records.py.
# - Sends nothing anywhere: the only other address it talks to is Ollama, on this computer.
# Python standard library only.

import hmac
import json
import mimetypes
import secrets
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # the project folder, so "app" can be found
from app import checks, jobs   # noqa: E402 (after the path line on purpose)

UI = checks.ROOT / "ui"
SHOWN = {".html", ".js", ".css", ".png", ".jpg", ".jpeg", ".svg", ".ico", ".webp", ".gif"}
# In ui/ but not part of the app: the made-up demo review (real reviews come through /api/review),
# the public landing page, and the tester kit's own opener. None of them is ever served.
NOT_SERVED = {"review_data.js", "start.html", "start.css", "start_buddies.js", "open_results.html"}
CSP = ("default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
       "connect-src 'self'; object-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'")
# style-src allows inline styles (progress bars and buddy sizes are set in style="..."): styles can't run code.


def review_answer():
    """The newest review.json, as harness/records.py finds it (stage 0.3), or None. This file never
    builds that path itself (D38)."""
    try:
        from harness import records
    except ImportError:   # code from before stage 0.3: no records yet
        return None
    where = records.review_to_read()
    if where is None:
        return None
    return json.loads(Path(where).read_text(encoding="utf-8"))


def make_handler(key, host):
    origin = "http://" + host

    class Handler(BaseHTTPRequestHandler):
        server_version = "Shyft"
        sys_version = ""

        def log_message(self, *args):   # quiet: no file names or addresses in the window
            pass

        def _send(self, code, body, kind="application/json; charset=utf-8"):
            data = body if isinstance(body, bytes) else json.dumps(body).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")   # the key never leaves in a Referer header
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Content-Security-Policy", CSP)
            self.end_headers()
            self.wfile.write(data)

        def _ours(self, post=False):
            if self.headers.get("Host") != host:
                return False
            site = self.headers.get("Sec-Fetch-Site")
            if site is not None and site not in ("same-origin", "none"):   # another website asked
                return False
            if post and self.headers.get("Origin") != origin:
                return False
            if urlsplit(self.path).path.startswith("/api/"):
                return hmac.compare_digest(self.headers.get("X-Shyft-Key", ""), key)
            return True

        def do_GET(self):
            if not self._ours():
                return self._send(403, {"error": "Not allowed."})
            path = urlsplit(self.path).path
            if path == "/api/status":
                return self._send(200, checks.status())
            if path == "/api/job":
                return self._send(200, jobs.snapshot())
            if path == "/api/review":
                review = review_answer()
                return self._send(200, review) if review is not None else self._send(404, {"error": "No review yet."})
            if path.startswith("/api/"):
                return self._send(404, {"error": "Unknown."})
            return self._file(path)

        def do_POST(self):
            if not self._ours(post=True):
                return self._send(403, {"error": "Not allowed."})
            path = urlsplit(self.path).path
            if path == "/api/quit":   # stops any job first, so nothing keeps running unseen
                jobs.stop()
                self._send(200, {"bye": True})
                threading.Thread(target=self.server.shutdown, daemon=True).start()
                return None
            if path in ("/api/get-ready", "/api/run"):
                started, answer = (jobs.get_ready if path == "/api/get-ready" else jobs.sort)()
                return self._send(200, answer) if started else self._send(409, {"error": answer})
            if path == "/api/stop":
                jobs.stop()
                return self._send(200, jobs.snapshot())
            return self._send(404, {"error": "Unknown."})

        def _file(self, path):   # only Shyft's screens in ui/, only the kinds a page needs
            name = "index.html" if path in ("", "/") else path.lstrip("/")
            target = (UI / name).resolve()
            if (UI.resolve() not in target.parents or target.suffix.lower() not in SHOWN
                    or target.name in NOT_SERVED or not target.is_file()):
                return self._send(404, b"Not found", "text/plain; charset=utf-8")
            kind = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
            if kind.startswith("text/") or kind.endswith("javascript"):
                kind += "; charset=utf-8"
            return self._send(200, target.read_bytes(), kind)

    return Handler


def serve(open_browser=True, port=0):
    """Start the server. Returns (server, address the browser should open, key)."""
    key = secrets.token_urlsafe(24)
    server = ThreadingHTTPServer(("127.0.0.1", port), None)
    host = "127.0.0.1:" + str(server.server_address[1])
    server.RequestHandlerClass = make_handler(key, host)
    address = "http://" + host + "/index.html?k=" + key
    if open_browser:
        webbrowser.open(address)
    return server, address, key


def main():
    server, address, _ = serve()
    print("Shyft is open in your browser.")
    print("If it didn't open, copy this address into your browser (it only works on this computer):")
    print("  " + address)
    print("Leave this window open while you use Shyft. Close it (or press Ctrl+C) to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        jobs.stop()   # closing the window stops a download or a run too
        server.server_close()
    print("Shyft stopped.")


if __name__ == "__main__":
    main()
