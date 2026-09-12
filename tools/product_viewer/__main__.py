"""python -m tools.product_viewer — run the viewer service (repo root cwd)."""
from __future__ import annotations

import argparse

from .server import serve_forever


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--engine-url", default="http://127.0.0.1:8105",
                    help="the private engine instance to observe")
    ap.add_argument("--port", type=int, default=8205,
                    help="the viewer's own port (availability checked by bind failure)")
    ap.add_argument("--history", type=int, default=240,
                    help="ring buffer capacity (frames)")
    args = ap.parse_args()
    serve_forever(args.engine_url, args.port, args.history)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
