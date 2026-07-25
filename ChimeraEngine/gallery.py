"""A local HTTP gallery for the dyadAnalysis renders -- so the PHYSICS side (the agent, who authors
the render) and the HUMAN side (the operator + the LM Studio vision model) SEE the same picture
during development. You cannot tune a render you cannot see; this is the shared view.

127.0.0.1 ONLY -- never public (the studio's bind rule; reaches the agent + the browser, nobody else).
Run:  python ChimeraEngine/gallery.py [port]        (default 8765)
"""
from __future__ import annotations

import functools
import http.server
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
OUT = _HERE / "output"
sys.path.insert(0, str(_HERE))
try:
    from human_messenger import PHYSICS_READING
except Exception:
    PHYSICS_READING = {}


def _index() -> bytes:
    figs = []
    for p in sorted(OUT.glob("appear_*.png")):
        term = p.stem.replace("appear_", "")
        phys = PHYSICS_READING.get(term, "")
        figs.append(
            f'<figure><img src="/{p.name}?v={p.stat().st_mtime_ns}" alt="{term}">'
            f'<figcaption><b>{term}</b>'
            + (f'<br><span>physics expects: {phys}</span>' if phys else '')
            + '</figcaption></figure>')
    body = "".join(figs) or "<p style='color:#8892b0'>no renders in output/ yet</p>"
    return (
        "<!doctype html><meta charset=utf-8><title>Chimera renders</title>"
        "<meta http-equiv=refresh content=5>"                      # auto-refresh: re-rendered images update live
        "<style>body{background:#0b0d12;color:#cfe0ff;font-family:system-ui,-apple-system,sans-serif;margin:24px}"
        "h1{font-weight:600;font-size:20px} figure{display:inline-block;vertical-align:top;margin:14px;width:440px;text-align:center}"
        "img{width:440px;background:#04050b;border:1px solid #2a3350;border-radius:10px}"
        "figcaption{margin-top:8px} figcaption b{color:#ffe9a8;font-size:15px}"
        "figcaption span{color:#8892b0;font-size:12px;display:block;margin-top:3px}</style>"
        f"<h1>Chimera dyadAnalysis renders &mdash; the shared view (physics &harr; human)</h1>{body}"
    ).encode("utf-8")


class _Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.split("?")[0] in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(_index())
            return
        return super().do_GET()

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    OUT.mkdir(parents=True, exist_ok=True)
    handler = functools.partial(_Handler, directory=str(OUT))
    with http.server.ThreadingHTTPServer(("127.0.0.1", port), handler) as srv:  # 127.0.0.1 only -- reaches the agent + browser, nobody else
        print(f"gallery at http://127.0.0.1:{port}   (serving {OUT})")
        srv.serve_forever()
