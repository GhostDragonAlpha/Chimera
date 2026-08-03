"""stone_legibility.py -- M5's MEASURING INSTRUMENT: how does the stone read at 3.2 m?

The blind read (docs/THE_SLICE.md, rung 3) found "the 0.35 m stone and the 0.84 m pile are
faint patches at 3.2 m camera distance". F2's own rule: the fix is the presentation physics
-- exposure, object scale, reading -- never the tolerance. But a fix without a BEFORE frame
is a guess. This probe stands the walker 3.2 m from the stone, facing it, in the SAME view
the recorded session used (third person, the measured +0.55 high camera), and captures the
frame. Run it before and after any legibility change; the two frames are the evidence.

    python tools/stone_legibility.py before     # -> ChimeraEngine/output/stone_before.jpg
    python tools/stone_legibility.py after      # -> ChimeraEngine/output/stone_after.jpg
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "ChimeraEngine"))

STONE = (3.0, 5.0)          # touchables.spawn()'s own waypoints -- not chosen here
TUFT = (-3.5, 8.0)
TARGETS = {"stone": STONE, "tuft": TUFT}
CAM_DIST = 3.2              # m -- the blind read's measured camera distance
DOWN_LOOK = -0.55           # slice_record.py's measured value: the high camera over the fence


def main() -> int:
    tag = sys.argv[1] if len(sys.argv) > 1 else "before"
    what = sys.argv[2] if len(sys.argv) > 2 else "stone"
    tx, ty = TARGETS[what]
    import live_viewer
    v = live_viewer.get_viewer()
    with v._lock:
        v._clients += 1                             # wake the render thread (rung-1 trap)
    try:
        print("[legibility] standing up (the carve is ~13 s, once)...")
        v.stand()
        v.set_view("third")
        v.walk_input(my=DOWN_LOOK)
        w = v._walk
        # TELEPORT, facing the target from exactly the blind read's distance. A probe rig,
        # not gameplay -- the same move touch_tests.py's place() makes.
        w.x, w.y = tx, ty - CAM_DIST
        import walker as WK
        w.z = WK.height_at(w.x, w.y)
        w.vx = w.vy = w.vz = 0.0
        w.yaw = 0.0                                  # facing +y: straight at the target
        time.sleep(3.0)                              # let the view settle to full-res LOD
        jpg = v.frame()
        out = REPO / "ChimeraEngine" / "output" / f"{what}_{tag}.jpg"
        out.write_bytes(jpg)
        print(f"[legibility] {out}  ({len(jpg)} bytes)")
        return 0
    finally:
        with v._lock:
            v._clients -= 1


if __name__ == "__main__":
    sys.exit(main())
