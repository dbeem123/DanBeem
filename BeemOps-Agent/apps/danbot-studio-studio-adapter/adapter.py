"""Local-only DanBot Studio static viewer and fixed /v1 proxy."""
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit
import re

UPSTREAM_HOST = "127.0.0.1"
RESULT_PATH = re.compile(r"^/v1/results/([A-Za-z0-9][A-Za-z0-9._~-]{0,127})/(metadata|media|download)$")
UPSTREAM_PORT = 8765
ACCESS_HEADERS = {
    "cf-access-jwt-assertion",
    "cookie",
    "origin",
}
HOP_BY_HOP = {"connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailer", "transfer-encoding", "upgrade"}


class Handler(BaseHTTPRequestHandler):
    server_version = "DanBotStudioAdapter/0.1"

    def _headers(self, content_type=None):
        self.send_header("Cache-Control", "private, no-store")
        self.send_header("Pragma", "no-cache")
        self.send_header("X-Robots-Tag", "noindex")
        if content_type:
            self.send_header("Content-Type", content_type)

    def _deny(self):
        self.send_response(404)
        self._headers("text/plain; charset=utf-8")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        parsed = urlsplit(self.path)
        if parsed.netloc:
            self._deny()
            return
        if parsed.path.startswith("/v1/"):
            if not RESULT_PATH.fullmatch(unquote(parsed.path)):
                self._deny()
                return
            self._proxy(parsed.path + (("?" + parsed.query) if parsed.query else ""))
            return
        files = {"/image/": "image/index.html", "/song/": "song/index.html", "/result.js": "result.js", "/result.css": "result.css"}
        relative = files.get(parsed.path)
        if relative:
            data = (self.server.root / relative).read_bytes()
            self.send_response(200)
            self._headers("text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        self._deny()

    def do_POST(self):
        self._deny()

    def _proxy(self, path):
        # The destination is constants, never derived from request input.
        headers = {}
        for name, value in self.headers.items():
            if name.lower() in ACCESS_HEADERS and name.lower() not in HOP_BY_HOP:
                headers[name] = value
        connection = HTTPConnection(UPSTREAM_HOST, UPSTREAM_PORT, timeout=10)
        try:
            connection.request("GET", path, headers=headers)
            upstream = connection.getresponse()
            body = upstream.read()
        except OSError:
            self.send_response(502)
            self._headers("text/plain; charset=utf-8")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        finally:
            connection.close()
        self.send_response(upstream.status)
        content_type = upstream.getheader("Content-Type") or "application/octet-stream"
        self._headers(content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class AdapterServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address, root):
        self.root = Path(root).resolve()
        super().__init__(address, Handler)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Local-only DanBot Studio adapter")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()
    if args.host != "127.0.0.1":
        raise SystemExit("refusing non-loopback host")
    server = AdapterServer((args.host, args.port), Path(__file__).parent / "static")
    print(f"DanBot Studio adapter listening on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
