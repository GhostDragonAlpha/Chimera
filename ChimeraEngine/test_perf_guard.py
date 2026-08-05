"""test_perf_guard.py -- do the three guards actually FIRE?

A guard that never fires reads exactly like one that was never wired up, and every falsifier in
the expansion-budget batch is some form of that question. Each check here INJECTS the condition
the guard exists to catch and asserts the guard notices, then injects a near-miss and asserts it
stays quiet -- a check that only ever tests the firing direction cannot tell a guard from an alarm
that is stuck on.

IT HAS ALREADY EARNED ITS KEEP. Its first run failed two checks and both were real: `perf_guard`
carried TWO definitions of `check_frame_budget` -- the new expansion one and the old grain one,
the later shadowing the earlier -- so every call was still comparing expansions against a
250,000-GRAIN cap. Reading the file did not show it; running it did.

    python ChimeraEngine/test_perf_guard.py
"""
import warnings; warnings.filterwarnings('ignore')
import sys, io, math, json, contextlib
from pathlib import Path
import numpy as np

ROOT = Path('E:/PythonChimera')
sys.path.insert(0, str(ROOT / 'ChimeraEngine')); sys.path.insert(0, str(ROOT))

import perf_guard as pg
import splat_appearance as sa
import lod as LOD

OK, BAD = [], []
def check(name, cond, detail=""):
    (OK if cond else BAD).append(name)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f"  -- {detail}" if detail else ""))

print("=" * 100)
print("TASK 1 falsifier -- 'theMining at 0.25x zoom passes the budget check'")
print("=" * 100)
MIN_EXP = 804_771         # measured, docs/pipeline_benchmark.csv (was 1,307,982 before the LOD
                          # size fix -- theMining's grains had been inflated 1.77x by the uniform
                          # law, so a third of that "cost" was the renderer, not the membrane)
try:
    pg.check_frame_budget(MIN_EXP)
    passed = True
except pg.PerfBudgetError:
    passed = False
print(f"  theMining@0.25x = {MIN_EXP:,} expansions vs cap {pg.MAX_EXPANSIONS_PER_FRAME:,}")
print(f"  -> the FALSIFIER {'FIRES: it passes the check' if passed else 'does not fire'}")
print(f"  measured frame time there is 57.1 ms; the declared wall MAX_RENDER_MS is "
      f"{pg.MAX_RENDER_MS} ms, so a 57.1 ms frame is INSIDE budget and a correctly derived cap")
print(f"  must let it through. At a 33 ms wall the cap would be "
      f"{pg.expansions_for_ms(33.3):,} and theMining WOULD be caught.")
try:
    pg.check_frame_budget(2 * pg.MAX_EXPANSIONS_PER_FRAME)
    check("2x the cap raises PerfBudgetError", False, "it did NOT raise")
except pg.PerfBudgetError as e:
    check("2x the cap raises PerfBudgetError", True, str(e)[:70] + "...")
try:
    pg.check_frame_budget(pg.MAX_EXPANSIONS_PER_FRAME - 1)
    check("one under the cap does NOT raise", True)
except pg.PerfBudgetError:
    check("one under the cap does NOT raise", False, "it raised -- off-by-one")

print()
print("=" * 100)
print("TASK 3 falsifier -- 'a frame with 2x the max expansions passes without warning'")
print("=" * 100)
import demo
from ParticleEngine.gpu_pipeline import FullGPUPipeline
from ParticleEngine.camera import FirstPersonCamera

pipe = FullGPUPipeline(bg=(0.015, 0.015, 0.04))
cam = FirstPersonCamera((0.0, -3.0, 0.0))
buf = sa.scene_buffer('theMining')
R = LOD.body_radius(buf); dist = 2.8 * R * 0.25
pos = (0.0, -dist, 0.0)
cam.position = np.array(pos, dtype=np.float32)
demo._aim_at_origin(cam, pos)

# MEASURE THE FRAME FIRST, THEN SET THE WALL UNDER IT. Hardcoding "600,000 because theMining makes
# 1.31M" was wrong by 3.4x: that figure is from the 1920x1080 benchmark and the demo renders at
# 1280x720, which is 2.9x fewer tiles and therefore 385k expansions. A threshold test whose
# threshold is copied from a different resolution tests the copy, not the guard.
with contextlib.redirect_stdout(io.StringIO()):
    demo._render_frame(pipe, cam, buf, "probe", 0, term="theMining")
_frame_exp = pipe.expansion_count()
real_cap = pg.MAX_EXPANSIONS_PER_FRAME
pg.MAX_EXPANSIONS_PER_FRAME = _frame_exp // 2      # this frame is exactly 2x the wall
print(f"  this frame makes {_frame_exp:,} expansions at {demo._W}x{demo._H}; "
      f"wall moved to {pg.MAX_EXPANSIONS_PER_FRAME:,} (frame is 2.0x over)")
cap_out = io.StringIO()
with contextlib.redirect_stdout(cap_out):
    demo._render_frame(pipe, cam, buf, "falsifier", 4242, term="theMining")
pg.MAX_EXPANSIONS_PER_FRAME = real_cap
txt = cap_out.getvalue()
check("demo._render_frame prints [PERF] on an over-budget frame",
      "[PERF]" in txt and "4242" in txt, txt.strip().splitlines()[0][:88] if txt.strip() else "no output")

cap_out = io.StringIO()
with contextlib.redirect_stdout(cap_out):
    demo._render_frame(pipe, cam, buf, "falsifier", 4243, term="theMining")
check("and stays SILENT when the same frame is inside budget",
      "[PERF]" not in cap_out.getvalue())

print()
print("=" * 100)
print("TASK 9 falsifier -- 'the baseline is identical to the current run, so it always passes'")
print("=" * 100)
import test_render_pipeline as T
base = T._load_baseline()
check("baseline file exists and has terms", len(base) > 40, f"{len(base)} terms")

# INJECT each regression the baseline claims to catch, against the REAL recorded values.
b_mining = base['theMining']
r = T._check_regression('theMining', base, b_mining['n_grains'], b_mining['n_lod'],
                        b_mining['max_pixel'], True)
check("an UNCHANGED term reports no regression", r == [], str(r))

r = T._check_regression('theMining', base, b_mining['n_grains'], b_mining['n_lod'],
                        b_mining['max_pixel'] * 0.08, True)
check("max_pixel 255 -> 20 (the task's named case) IS caught", len(r) == 1, r[0] if r else "MISSED")

r = T._check_regression('theMining', base, int(b_mining['n_grains'] * 0.5),
                        b_mining['n_lod'], b_mining['max_pixel'], True)
check("a 50% grain-count drop IS caught", len(r) == 1, r[0] if r else "MISSED")

r = T._check_regression('theMining', base, b_mining['n_grains'], b_mining['n_lod'],
                        0.0, False)
check("a term that rendered and now renders NOTHING is caught", len(r) >= 1,
      r[0] if r else "MISSED")

r = T._check_regression('theMining', base, int(b_mining['n_grains'] * 0.95),
                        b_mining['n_lod'], b_mining['max_pixel'] * 0.9, True)
check("a 5% grain / 10% brightness wobble does NOT fire (band is above the noise)", r == [], str(r))

r = T._check_regression('aBrandNewMembrane', base, 100, 100, 5.0, False)
check("an UNBASELINED term is not a failure", r == [], str(r))

print()
print("=" * 100)
print(f"  {len(OK)} passed, {len(BAD)} failed")
for b in BAD:
    print(f"    FAILED: {b}")
print("=" * 100)
sys.exit(1 if BAD else 0)
