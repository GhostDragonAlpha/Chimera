"""boot_slice.py -- boot the declared playable slice WITHOUT the desktop
browser pop (webbrowser.open stubbed: the pilot drives its own private
headless Chrome; the shared desktop is never touched).

Usage: python tools/thin_client_pilot/boot_slice.py --port N [--engine-exe P]
"""
from __future__ import annotations

import argparse
import sys
import webbrowser
from pathlib import Path

HERE = Path(__file__).resolve().parent
SLICE_DIR = HERE.parent / "playable_slice"
sys.path.insert(0, str(SLICE_DIR))

import slice_server  # noqa: E402

# slice_server imports webbrowser INSIDE main(); stubbing the shared singleton
# module covers that import too.
webbrowser.open = lambda *a, **k: None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, required=True,
                    help="bind-tested free port (8127 refused upstream by code)")
    ap.add_argument("--engine-exe", type=Path, default=None)
    ns, rest = ap.parse_known_args()
    argv = ["slice_server.py", "--port", str(ns.port)]
    if ns.engine_exe is not None:
        argv += ["--engine-exe", str(ns.engine_exe)]
    argv += rest
    sys.argv = argv
    return slice_server.main()


if __name__ == "__main__":
    sys.exit(main())
