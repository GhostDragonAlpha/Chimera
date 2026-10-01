"""render_truth_server_launcher.py -- start the slice server for THIS lane's
movie capture WITHOUT its desktop side effect (lane render-truth-20260920).

Same shape the realbody-movie lane shipped: slice_server.main() ends its
boot with webbrowser.open(url); the operator plays on this machine, so the
capture must never touch the shared desktop. This launcher stubs
webbrowser.open BEFORE the server runs, then execs the unchanged slice
server through runpy. No slice file is edited for this.

Usage:
  python render_truth_server_launcher.py --port N --engine-exe P --log PATH
"""
from __future__ import annotations

import argparse
import runpy
import sys
import webbrowser
from pathlib import Path

HERE = Path(__file__).resolve().parent
SLICE = HERE.parents[3] / "tools" / "playable_slice"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--engine-exe", required=True)
    ap.add_argument("--log", required=True)
    a = ap.parse_args()
    webbrowser.open = lambda *args, **kwargs: None   # the desktop stays dark
    sys.argv = [str(SLICE / "slice_server.py"),
                "--port", str(a.port), "--engine-exe", a.engine_exe]
    sys.path.insert(0, str(SLICE))
    print("render_truth launcher: port %d engine %s" % (a.port, a.engine_exe),
          flush=True)
    runpy.run_path(str(SLICE / "slice_server.py"), run_name="__main__")
    return 0


if __name__ == "__main__":
    sys.exit(main())
