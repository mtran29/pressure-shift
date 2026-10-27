"""Dependency-free server for the fictional live overlay demo."""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from foundry import configured, edit, fallback
from insights import CANDIDATES
from simulation import public_scene

ROOT = Path(__file__).resolve().parent
CANDIDATE_BY_ID = {item["id"]: item for item in CANDIDATES}
EDITORIAL_CACHE: dict[str, dict] = {}


class Handler(BaseHTTPRequestHandler):
    def json(self, code: int, value: dict) -> None:
        body = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/api/scene":
            self.json(200, {**public_scene(), "candidates": CANDIDATES,
                            "preview": {c["id"]: fallback(c) for c in CANDIDATES},
                            "foundry_configured": configured()})
        elif self.path == "/api/health":
            self.json(200, {"ok": True, "foundry_configured": configured()})
        elif self.path in ("/", "/index.html"):
            data = (ROOT / "static" / "index.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)
        else:
            self.json(404, {"error": "Not found"})

    def do_POST(self) -> None:
        if self.path != "/api/editorial":
            self.json(404, {"error": "Not found"})
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size < 1 or size > 1024:
                raise ValueError("Invalid payload length")
            payload = json.loads(self.rfile.read(size))
            candidate_id = payload.get("candidate_id")
            candidate = CANDIDATE_BY_ID[candidate_id]
        except (ValueError, TypeError, KeyError, json.JSONDecodeError):
            self.json(400, {"error": "Unknown candidate"})
            return
        if candidate_id not in EDITORIAL_CACHE:
            EDITORIAL_CACHE[candidate_id] = edit(candidate)
        self.json(200, EDITORIAL_CACHE[candidate_id])


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"Pressure Shift live demo: http://localhost:{port}")
    print("Foundry configured:", configured())
    server.serve_forever()
