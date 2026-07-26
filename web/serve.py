"""serve.py — the renderer's static server, with caching turned OFF.

The stdlib's bare static-file module sends no Cache-Control at all, so browsers fall back to
HEURISTIC caching and quietly serve a stale page. That is not a nuisance here, it is the single
most expensive bug class this renderer has had:

  * a cached splat.wgsl once reported "entry point doesn't exist" and ran at 240 fps rendering
    NOTHING, while every measurement looked plausible
  * a cached main.js later hid a whole group of new controls, and the honest reading of the screen
    was "you forgot to wire the sliders"

Both times the code on disk was correct and the browser was showing something else. A stale asset
is worse than a broken one, because a broken one announces itself.

So: no-store on everything. This is a development viewer on loopback -- there is no traffic to save
and nothing to gain by caching.

    python web/serve.py [port]         (default 8017)
"""
from __future__ import annotations

import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class NoCache(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def log_message(self, fmt, *args):            # one line per request, without the date noise
        sys.stderr.write("  %s\n" % (fmt % args))


def main() -> int:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8017
    root = Path(__file__).resolve().parent
    handler = partial(NoCache, directory=str(root))
    # 127.0.0.1 only. Reaches the agent and the browser and nobody else -- see docs/LOCAL_SERVERS.md.
    srv = ThreadingHTTPServer(('127.0.0.1', port), handler)
    print(f"serving {root} on http://127.0.0.1:{port}/  (no-store: every reload is fresh)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
