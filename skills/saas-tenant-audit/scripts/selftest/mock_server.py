#!/usr/bin/env python3
"""Tiny mock API for testing tenant_probe.py itself. `secure` or `vuln` mode.

Tokens: tokA (scheme Bearer), tokB (scheme Token). Items: 101 belongs to A, 202 to B.
vuln mode reproduces three classic bugs: 403-vs-404 existence oracle, cross-tenant write,
and (via /old) a redirect that must NOT be followed by the probe.
"""
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

DATA = {"101": {"owner": "A", "name": "a1"}, "202": {"owner": "B", "name": "b1"}}
TOKENS = {"Bearer tokA": "A", "Token tokB": "B"}
VULN = sys.argv[1] == "vuln"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send_json(self, code, obj, extra=None):
        payload = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(payload)

    def item(self):
        who = TOKENS.get(self.headers.get("Authorization") or "")
        if not who:
            self.send_json(401, {"error": "unauthenticated"})
            return None
        item = DATA.get(self.path.rsplit("/", 1)[-1])
        if item is None:
            self.send_json(404, {"error": "not found"})
            return None
        if item["owner"] != who:
            if VULN and self.command == "GET":
                self.send_json(403, {"error": "forbidden"})   # existence oracle
                return None
            if not (VULN and self.command == "PATCH"):        # vuln: cross-tenant write allowed
                self.send_json(404, {"error": "not found"})
                return None
        return item

    def do_GET(self):
        if self.path == "/old":
            self.send_json(301, {"moved": True}, {"Location": "/things/101"})
            return
        item = self.item()
        if item is not None:
            self.send_json(200, {"name": item["name"]})

    def do_PATCH(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or "{}")
        item = self.item()
        if item is not None:
            item.update(body)
            self.send_json(200, {"ok": True})


if __name__ == "__main__":
    HTTPServer(("127.0.0.1", int(sys.argv[2])), Handler).serve_forever()
