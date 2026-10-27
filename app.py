"""Standard-library HTTP server for the Pressure Shift demo."""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from engine import EVENTS, INSIGHTS
from foundry import configured, narrate, recap


ROOT = Path(__file__).resolve().parent
INSIGHT_BY_ID = {insight.id: insight for insight in INSIGHTS}
_cache: dict[str, dict] = {}


class Handler(BaseHTTPRequestHandler):
    def _json(self, status: int, value: dict) -> None:
        body = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/api/match":
            self._json(200, {"events": [e.public() for e in EVENTS],
                             "insights": [i.public() for i in INSIGHTS],
                             "foundry_configured": configured()})
        elif self.path == "/api/health":
            self._json(200, {"ok": True, "foundry_configured": configured()})
        elif self.path in ("/", "/index.html"):
            data = (ROOT / "static" / "index.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        else:
            self._json(404, {"error": "Not found"})

    def do_POST(self) -> None:
        size = int(self.headers.get("Content-Length", "0"))
        if size > 4096:
            self._json(413, {"error": "Payload too large"})
            return
        try:
            payload = json.loads(self.rfile.read(size) or b"{}")
        except json.JSONDecodeError:
            self._json(400, {"error": "Invalid JSON"})
            return
        if self.path == "/api/narrate":
            insight_id = payload.get("insight_id")
            insight = INSIGHT_BY_ID.get(insight_id)
            if insight is None:
                self._json(404, {"error": "Unknown insight"})
                return
            if insight_id not in _cache:
                _cache[insight_id] = narrate(insight)
            self._json(200, _cache[insight_id])
        elif self.path == "/api/recap":
            if "recap" not in _cache:
                _cache["recap"] = recap(INSIGHTS)
            self._json(200, _cache["recap"])
        else:
            self._json(404, {"error": "Not found"})


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"Pressure Shift running at http://localhost:{port}")
    print("Foundry configured:", configured())
    server.serve_forever()

