"""B1 walker-level verification, PER LEG: through the SHIPPING path (Walker + body_buffer +
the terrain closure), each PLANTED boot's lowest grain must sit ON the carved terrain, never
through it. Swing boots and airborne frames are reported separately -- a foot in the air is
not on any terrain (the spec is about LANDING).

Run:  C:/Python314/python.exe tools/probe_walker_ik.py
"""
import json
import math
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "ChimeraEngine"))
sys.path.insert(0, str(REPO / "story"))

import controller as C          # noqa: E402
import walker as W              # noqa: E402
from matter import MAT          # noqa: E402

DT = 1.0 / 60.0
HN = json.loads((REPO / "story/theZero/theHorizon/theEmptying/theCooling/theCloud/theGalaxy"
                 "/theSolarSystem/thePlanets/theRockyPlanet/aRockyPlanet/aBlueWorld/theTerrain"
                 "/aTerrain/theGround/theHuman/aHuman/numbers.json").read_text())
GT = HN["gait_cycle"]
N = int(HN["gait_samples"])
STRIDE = float(HN["stride_m"])


def boots(w):
    """world-frame body grains, split per leg side. emit local +Y maps to LEFT of the facing
    (world lateral = -H*y along the facing's right vector)."""
    b = W.body_buffer(w)
    right = (math.cos(w.body_yaw), math.sin(w.body_yaw))
    lat = (b[:, 0] - w.x) * right[0] + (b[:, 1] - w.y) * right[1]
    low = (b[:, MAT] == 2.0) & (b[:, 2] < w.z + 0.55)          # boots, not gloves/pack
    return b, low, lat


def main() -> int:
    w = W.Walker()
    ctl = C.Controller()
    res = {"planted": [0.0, 0.0], "swing": [0.0, 0.0]}
    reads = {"planted": 0, "swing": 0}
    worst = {}
    script = [(8.0, {"fwd": True}), (1.0, {"turn_r": True}), (8.0, {"fwd": True}),
              (1.0, {"turn_l": True, "turn_r": False}), (8.0, {"fwd": True, "sprint": True})]
    hist = []                                            # (err_mm, grade_deg, kind)
    for secs, keys in script:
        for _ in range(int(secs / DT)):
            C.drive_walker(w, ctl, keys, DT)
            if not w.on_ground:
                continue
            b, low, lat = boots(w)
            grade = math.degrees(math.atan(math.hypot(*W.slope_at(w.x, w.y))))
            row = GT[int((w.dist / (2.0 * STRIDE)) * N) % N]
            for i in (0, 1):
                # table leg i is emit side -1/+1; emit +Y is LEFT, so leg i sits at lateral
                side_lat = -1.0 if i == 0 else 1.0
                m = low & (np.sign(lat) == np.sign(-side_lat))
                if not m.any():
                    continue
                g = b[m]
                # PER-BOOT CONTACT ERROR = min over the boot's grains of (grain z - terrain
                # under THAT grain). The lowest-ALTITUDE grain is the wrong read on real
                # terrain: a rigid toe hanging over ground that falls away downhill is not a
                # misplaced contact. The min-err grain IS the contact: >0 the whole boot
                # floats by that much (the leg's reach gave out), <0 it ploughs (forbidden).
                errs = g[:, 2] - np.array([W.height_at(gj[0], gj[1]) for gj in g])
                j = int(np.argmin(errs))
                err = float(errs[j])
                kind = "planted" if row[5 + 5 * i] > 0.5 else "swing"
                reads[kind] += 1
                hist.append((err * 1000, grade, kind))
                r = res[kind]
                if err > r[0]:
                    r[0] = err
                    worst[(kind, "float")] = (err, w.x, w.y, i, g[j, 0], g[j, 1])
                if err < r[1]:
                    r[1] = err
                    worst[(kind, "plough")] = (err, w.x, w.y, i, g[j, 0], g[j, 1])
    for kind in ("planted", "swing"):
        up, down = res[kind]
        print(f"{kind:>8}: reads={reads[kind]:>5}  worst float {up*1000:+8.1f} mm   "
              f"worst plough {down*1000:+8.1f} mm")
    # the honest picture is the DISTRIBUTION, not the worst sample: how often is the sole
    # within a grain (~24 mm) of the carved field, by terrain grade band
    for lo, hi in ((0, 8), (8, 16), (16, 90)):
        band = [e for e, gd, k in hist if k == "planted" and lo <= gd < hi]
        if not band:
            continue
        a = np.array(band)
        within = float(np.mean(np.abs(a) <= 24.0)) * 100.0
        print(f"  planted on {lo:>2}-{hi:<2} deg: n={len(a):>4}  p50={np.percentile(a, 50):+6.1f}  "
              f"p90={np.percentile(a, 90):+6.1f}  min={a.min():+6.1f}  max={a.max():+6.1f} mm   "
              f"within a grain: {within:.0f}%")
    for k, (err, wx, wy, i, gx, gy) in worst.items():
        grade = math.degrees(math.atan(math.hypot(*W.slope_at(wx, wy))))
        print(f"  {k}: {err*1000:+.1f} mm at walker ({wx:.1f},{wy:.1f}) grade {grade:.1f} deg, "
              f"leg {i}, grain ({gx:.2f},{gy:.2f})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
