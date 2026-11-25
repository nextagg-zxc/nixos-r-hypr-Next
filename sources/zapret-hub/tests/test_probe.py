import http.server
import os
import socket
import sys
import threading
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from zaprethub import probe  # noqa: E402


class Quiet(http.server.BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.send_response(204)
        self.end_headers()

    def log_message(self, *a):
        pass


class QuietServer(http.server.HTTPServer):
    def handle_error(self, request, client_address):
        pass


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class Probe(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = QuietServer(("127.0.0.1", 0), Quiet)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.port = cls.srv.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def test_http_ok(self):
        self.assertEqual(probe.check_site(f"http://127.0.0.1:{self.port}/", 3), {"HTTP": "OK"})

    def test_closed_port_is_error(self):
        self.assertEqual(probe.check_site(f"http://127.0.0.1:{free_port()}/", 2), {"HTTP": "ERROR"})

    def test_https_without_tls_server_is_error(self):
        # a plain HTTP server on the port: TLS handshake fails -> ERROR, not OK
        res = probe.check_site(f"https://127.0.0.1:{self.port}/", 2)
        self.assertEqual(set(res), {"HTTP", "TLS1.2", "TLS1.3"})
        self.assertNotIn("OK", res.values())

    def test_dns_failure(self):
        self.assertEqual(probe.check_site("http://nonexistent.invalid/", 2), {"HTTP": "DNS"})

    def test_tcp_ping(self):
        ms = probe.tcp_ping("127.0.0.1", self.port, 2)
        self.assertIsInstance(ms, float)
        self.assertGreaterEqual(ms, 0)
        self.assertIsNone(probe.tcp_ping("127.0.0.1", free_port(), 1))

    def test_check_target(self):
        res = probe.check_target({"name": "loc", "url": f"http://127.0.0.1:{self.port}/", "ping": "127.0.0.1"},
                                 2, ping_port=self.port)
        self.assertEqual(res["name"], "loc")
        self.assertEqual(res["HTTP"], "OK")
        self.assertIsNotNone(res["ping"])

    def test_score(self):
        self.assertEqual(probe.score({"name": "x", "HTTP": "OK", "TLS1.2": "ERROR", "TLS1.3": "OK", "ping": 5}), (2, 3))
        self.assertEqual(probe.score({"name": "x", "ping": 5}), (0, 0))


if __name__ == "__main__":
    unittest.main()
