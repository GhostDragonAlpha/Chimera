"""B1 verification probe: planted soles must land ON the ground plane, never through it.

Emits aHuman across the gait cycle against synthetic sloped terrains (in emit's own local
frame) and measures, per PLANTED leg per phase, the lowest boot grain's height above the
terrain. Compares the old flat-floor pose (ground=None) with the B1 terrain conform.

Run:  C:/Python314/python.exe tools/probe_foot_ik.py
"""
import importlib.util
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
STORY = ROOT / "story"
TERR = (STORY / "theZero/theHorizon/theEmptying/theCooling/theCloud/theGalaxy/theSolarSystem"
        "/thePlanets/theRockyPlanet/aRockyPlanet/aBlueWorld/theTerrain/aTerrain")
sys.path.insert(0, str(STORY))

spec = importlib.util.spec_from_file_location(
    "aHuman_phys", TERR / "theGround/theHuman/aHuman/physics.py")
law = importlib.util.module_from_spec(spec)
spec.loader.exec_module(law)
hn = json.loads((TERR / "theGround/theHuman/aHuman/numbers.json").read_text())

H = float(hn["height_m"])
com_h = float(hn["com_height_m"]) / H
GT = hn["gait_cycle"]
N = int(hn["gait_samples"])

# the flat sole plane in emit's pre-CoM frame (the walker's own definition of `lift`)
lows = [law.emit(hn, k / 12.0)[:, 2].min() for k in range(12)]
lift = -float(sum(lows) / len(lows))
base = com_h - lift


def sole_errors(emit_fn, slope_tan):
    """worst float (sole ABOVE terrain) and worst plough (sole THROUGH it) over the cycle,
    per planted leg, in LOCAL units. The spec is asymmetric: soles land ON the terrain
    (float is a landing shortfall, capped by the leg's reach) and NEVER through it."""
    up, down = 0.0, 0.0
    for k in range(N):
        t = k / N
        row = GT[k]
        b = emit_fn(t)
        for i in (0, 1):
            planted = row[5 + 5 * i] > 0.5
            if not planted:
                continue
            side = -1.0 if i == 0 else 1.0
            # boot grains: MAT == 2, on this side, below the hip (excludes gloves + pack)
            m = (b[:, law_blank_mat_col()] == 2.0) & (np.sign(b[:, 1]) == np.sign(side)) & (b[:, 2] < 0.1)
            if not m.any():
                continue
            g = b[m]
            # the contact is the min over grains of (grain z - terrain under THAT grain):
            # >0 the boot floats by that much, <0 it ploughs. (The lowest-ALTITUDE grain is
            # the wrong read wherever the ground tilts away under a rigid toe.)
            errs = g[:, 2] - ((base - com_h) + slope_tan * g[:, 0])
            err = float(errs.min())
            up = max(up, err)
            down = min(down, err)
    return up, -down


def law_blank_mat_col():
    from matter import MAT
    return MAT


print(f"leg reach check: thigh+shank = 0.491 of stature = {0.491 * H:.3f} m")
print(f"{'slope':>6} | {'old: float/plough':>22} | {'B1: float/plough':>22}")
for deg in (0, 10, 20, 30):
    s = math.tan(math.radians(deg))                # slope in local units per local x (unitless)
    of, op = sole_errors(lambda t: law.emit(hn, t), s)
    nf, np_ = sole_errors(lambda t: law.emit(hn, t, ground=lambda lx, ly: base + math.tan(math.radians(deg)) * lx), s)
    print(f"{deg:>5}° | {of*H*1000:>9.1f}/{op*H*1000:>9.1f} mm | {nf*H*1000:>9.1f}/{np_*H*1000:>9.1f} mm")

# perf: emit with terrain must be per-frame affordable
t0 = time.perf_counter()
for k in range(48):
    law.emit(hn, k / 48.0, ground=lambda lx, ly: base + 0.2 * lx)
dt = (time.perf_counter() - t0) / 48
print(f"emit with ground: {dt * 1000:.1f} ms/pose ({1.0 / dt:.0f} poses/s)")

# sanity: the upper body must be IDENTICAL with and without terrain (hip bob untouched)
a = law.emit(hn, 0.3)
b = law.emit(hn, 0.3, ground=lambda lx, ly: base + 0.2 * lx)
upper = a[:, 2] > 0.2
same = np.allclose(a[upper], b[upper])
print(f"upper body untouched by the conform: {same}")
