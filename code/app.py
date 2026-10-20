"""Local demo with a live lower-level solve by the same Python code: python app.py, then open the printed URL."""
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import numpy as np

from dcn import config as C
from dcn import demand, evaluate, routing
from dcn.world import make_world

ROOT = Path(__file__).resolve().parent
PAGE = ROOT.parent / "demo.html"

# Same world as the run the page shows, so the live solve uses the engine's cached road distances
_P = C.FULL if C.DEMO_PROFILE == "full" else C.REDUCED
_W = make_world(_P["fraction"], C.SEED)
_M = demand.fit(_W, demand.make_history(_W, np.random.default_rng(C.SEED + 1)))
CTX = evaluate.context(_W, _M)


class Handler(SimpleHTTPRequestHandler):
    def _send(self, code, body, kind="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path in ("/", "/demo.html"):
            return self._send(200, PAGE.read_bytes(), "text/html; charset=utf-8")
        if self.path == "/api/health":
            return self._send(200, {"ok": True, "engine": "python routing.solve"})
        self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/api/solve":
            return self._send(404, {"error": "not found"})
        req = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        st = np.asarray(req["stores"], float)
        p = routing.Params(**req["params"])
        if "ids" in req:
            D = routing.territory_matrix(CTX, int(req["site"]), np.asarray(req["ids"], int))
        else:
            D = routing.dist_matrix(req["dc"][0], req["dc"][1], st[:, 0], st[:, 1], st[:, 2] > 0)
        r = routing.solve(D, st[:, 3], p)
        self._send(200, r)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    for port in range(8437, 8448):
        try:
            server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
            break
        except OSError:
            continue
    print(f"Dasol network lab: http://localhost:{port}  (Ctrl+C to stop)", flush=True)
    server.serve_forever()
