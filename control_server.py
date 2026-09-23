"""Servidor web e endpoint local para controlar o threshold em tempo real."""

import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PORT = 8766
threshold = 0.08


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/api/threshold"):
            self.send_json({"threshold": threshold})
            return
        super().do_GET()

    def do_POST(self):
        global threshold
        if self.path != "/api/threshold":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length))
            threshold = min(max(float(payload["threshold"]), 0.0), 1.0)
            self.send_json({"threshold": threshold})
        except (ValueError, KeyError, json.JSONDecodeError):
            self.send_error(400, "threshold invalido")

    def send_json(self, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format_string, *args):
        if self.path.startswith("/api/"):
            super().log_message(format_string, *args)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    server.serve_forever()
