import http.client
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import adapter
from adapter import AdapterServer


class Upstream(BaseHTTPRequestHandler):
    last = None

    def do_GET(self):
        type(self).last = (self.path, dict(self.headers))
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"ok":true}')

    def log_message(self, *_):
        pass


class AdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.upstream = ThreadingHTTPServer(("127.0.0.1", 0), Upstream)
        adapter.UPSTREAM_PORT = cls.upstream.server_address[1]
        cls.upstream_thread = threading.Thread(target=cls.upstream.serve_forever, daemon=True)
        cls.upstream_thread.start()
        cls.adapter = AdapterServer(("127.0.0.1", 0), root=Path(__file__).parent / "static")
        cls.adapter_thread = threading.Thread(target=cls.adapter.serve_forever, daemon=True)
        cls.adapter_thread.start()
        cls.host, cls.port = cls.adapter.server_address

    @classmethod
    def tearDownClass(cls):
        cls.adapter.shutdown(); cls.adapter.server_close()
        cls.upstream.shutdown(); cls.upstream.server_close()

    def request(self, path, headers=None):
        conn = http.client.HTTPConnection(self.host, self.port)
        conn.request("GET", path, headers=headers or {})
        response = conn.getresponse()
        body = response.read()
        conn.close()
        return response, body

    def test_image_and_song_viewers_are_same_origin_assets(self):
        for path in ("/image/", "/song/"):
            response, body = self.request(path)
            self.assertEqual(response.status, 200)
            self.assertIn(b"DanBot Studio", body)
            self.assertEqual(response.getheader("Cache-Control"), "private, no-store")
            self.assertEqual(response.getheader("X-Robots-Tag"), "noindex")

    def test_api_proxy_is_fixed_and_preserves_access_headers_cookie_and_origin(self):
        headers = {
            "CF-Access-JWT-Assertion": "jwt-fixture",
            "Cookie": "CF_Authorization=fixture",
            "Origin": "https://studio.example.invalid",
        }
        response, body = self.request("/v1/results/abc/metadata", headers)
        self.assertEqual(response.status, 200)
        self.assertEqual(body, b'{"ok":true}')
        path, received = Upstream.last
        self.assertEqual(path, "/v1/results/abc/metadata")
        for name, value in headers.items():
            self.assertEqual(received.get(name), value)
        self.assertEqual(response.getheader("Cache-Control"), "private, no-store")
        self.assertEqual(response.getheader("X-Robots-Tag"), "noindex")

    def test_unknown_paths_are_denied(self):
        response, _ = self.request("/admin")
        self.assertEqual(response.status, 404)
        self.assertIsNone(Upstream.last if Upstream.last and Upstream.last[0] == "/admin" else None)

    def test_arbitrary_upstream_target_is_not_possible(self):
        response, _ = self.request("http://127.0.0.1:9999/v1/nope")
        self.assertEqual(response.status, 404)
        self.assertNotEqual(response.status, 502)

    def test_invalid_result_paths_are_denied_without_upstream_request(self):
        for path in ("/v1/results/../metadata", "/v1/results/a%2Fb/media", "/v1/admin", "/v1/results/a/secret"):
            response, _ = self.request(path)
            self.assertEqual(response.status, 404)

    def test_service_token_headers_are_not_forwarded(self):
        self.request("/v1/results/abc/media", {"CF-Access-Client-Id": "secret", "CF-Access-Client-Secret": "secret"})
        _, received = Upstream.last
        self.assertNotIn("CF-Access-Client-Id", received)
        self.assertNotIn("CF-Access-Client-Secret", received)


if __name__ == "__main__":
    unittest.main()
