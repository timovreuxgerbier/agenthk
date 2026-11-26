# app/shyft_app.py — Lane: Ana. Stage 1 of the Windows app plan: Shyft's screens, with real answers.
#
#   python app/shyft_app.py          (Mac: python3 app/shyft_app.py)
#
# Opens Shyft's screens (ui/) in your browser, and answers them with what is true on this computer
# (app/checks.py). Stage 1 only LOOKS: it installs, downloads, runs, moves and deletes nothing.
# Close this window, or press Ctrl+C, to stop it.
#
# Safety rules (plan, section 6):
# - Listens on 127.0.0.1 only, never on the network, on a port picked at random each time.
# - A secret key, made at start, is in the address the browser opens. Every /api/ request must carry it
#   (header X-Shyft-Key), so no other website or program can ask this server anything.
# - The Host header must be this exact address, so a website can't reach it by renaming itself (DNS rebinding).
# - Serves only files inside ui/, read-only. Never takes a file path from the browser.
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
from app import checks   # noqa: E402 (after the path line on purpose)

UI = checks.ROOT / "ui"
SHOWN = {".html", ".js", ".css", ".png", ".jpg", ".jpeg", ".svg", ".ico", ".webp", ".gif"}


def make_handler(key, host):
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
            self.end_headers()
            self.wfile.write(data)

        def _ours(self):   # the right Host, and for /api/ the right key
            if self.headers.get("Host") != host:
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
            if path.startswith("/api/"):
                return self._send(404, {"error": "Unknown."})
            return self._file(path)

        def do_POST(self):
            if not self._ours():
                return self._send(403, {"error": "Not allowed."})
            if urlsplit(self.path).path == "/api/quit":
                self._send(200, {"bye": True})
                threading.Thread(target=self.server.shutdown, daemon=True).start()
                return None
            return self._send(404, {"error": "Unknown."})

        def _file(self, path):   # only files inside ui/, only the kinds a page needs
            name = "index.html" if path in ("", "/") else path.lstrip("/")
            target = (UI / name).resolve()
            if UI.resolve() not in target.parents or target.suffix.lower() not in SHOWN or not target.is_file():
                return self._send(404, b"Not found", "text/plain; charset=utf-8")
            kind = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
            if kind.startswith("text/") or kind.endswith("javascript"):
                kind += "; charset=utf-8"
            return self._send(200, target.read_bytes(), kind)

    return Handler


def serve(open_browser=True, port=0):
    """Start the server. Returns (server, address the browser should open)."""
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
        server.server_close()
    print("Shyft stopped.")


if __name__ == "__main__":
    main()
