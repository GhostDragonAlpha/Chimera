"""wired_main.py -- MAT2-X02: run the PINNED slice_server with the session
wiring applied, by lazy substitution of the Handler global only.

Nothing in the extracted pinned tree is modified: the pinned main() boots
WORLD itself (engine + settle) and then serves with `Handler`; the wiring is
introduced as a subclass built by session_app.make_wired_handler whose routes
are constructed on the first request (at which point WORLD exists). Every
legacy route remains the pinned code path.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--play-root", type=Path, required=True)
    ap.add_argument("--port", type=int, default=0)
    ap.add_argument("--engine-exe", type=Path, required=True)
    a = ap.parse_args()

    slice_dir = a.play_root / "tools" / "playable_slice"
    if str(slice_dir) not in sys.path:
        sys.path.insert(0, str(slice_dir))

    import slice_server                    # the PINNED module (byte-exact)
    import session_app                     # the wiring layer (this card)

    def build_routes():
        world = slice_server.WORLD
        assert world is not None, "routes requested before the pinned main() booted WORLD"
        return session_app.SessionRoutes(
            session_app.SliceSession(world),
            page_loader=lambda: (slice_dir / "index.html").read_bytes())

    slice_server.Handler = session_app.make_wired_handler(
        slice_server.Handler, build_routes)

    sys.argv = ["slice_server", "--no-browser",
                "--port", str(a.port),
                "--engine-exe", str(a.engine_exe)]
    return slice_server.main()             # the shipped boot path, untouched


if __name__ == "__main__":
    raise SystemExit(main())
