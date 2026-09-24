"""C2 paddle controls — is the 84 mm dip and the 55-111 mm cross-section splits
real structure or surface-sampling artifacts?

Controls:
  (a) run the SAME 6 mm-gap split test on the PROXIMAL half (15-50 mm), which is
      certainly single-bodied (wrist/forearm continuation) — if it also splits,
      the test is sampling-limited, not anatomy.
  (b) split test at gap thresholds 6 / 10 / 14 mm on the distal half.
  (c) fine 2 mm slabs around 74-96 mm to characterise the 84 mm dip.
  (d) vertex spacing inside slabs (median nearest-neighbour gap) vs split threshold.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "work"))
from mesh_target import MonkeyTarget  # noqa: E402

BIRTH = r"E:\PythonChimera\forearm_package\baseline_snapshot\inputs\monkey_birth.bin"
PACK = r"E:\PythonChimera\forearm_package\baseline_snapshot\inputs\monkey_joints.bin"
OUT = Path(r"E:\PythonChimera\forearm_package\audits\C2_hand_evidence\receipts\target_paddle_controls.txt")

L: list[str] = []


def say(s: str = "") -> None:
    L.append(s)
    print(s)


def n_components_2d(pp2: np.ndarray, gap: float) -> int:
    g = np.floor(pp2 / gap).astype(int)
    cells = {tuple(row) for row in g}
    seen = set()
    ncomp = 0
    for v in cells:
        if v in seen:
            continue
        ncomp += 1
        stack = [v]
        seen.add(v)
        while stack:
            cur = stack.pop()
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    nb = (cur[0] + dx, cur[1] + dy)
                    if nb in cells and nb not in seen:
                        seen.add(nb)
                        stack.append(nb)
    return ncomp


mt = MonkeyTarget(birth_path=BIRTH, pack_path=PACK)
P = mt.joint_pos("elbow_R")
W = mt.joint_pos("wrist_R")
a = (W - P) / np.linalg.norm(W - P)
rel = mt.V - W
axial = rel @ a
perp = rel - np.outer(axial, a)
r = np.linalg.norm(perp, axis=1)
tmp = np.array([1.0, 0, 0])
b1 = np.cross(a, tmp); b1 /= np.linalg.norm(b1)
c1 = np.cross(a, b1)

reg = (axial > -0.005) & (axial < 0.120) & (r < 0.045)
idx = np.where(reg)[0]
axr = axial[idx]

say("=== C2 PADDLE CONTROLS (side R; same loader/axes as c2_target_paddle.py) ===")


def slab_loop(lo, hi, step, gap, label):
    nsplit = 0
    ntot = 0
    ranges = []
    for e in np.arange(lo, hi, step):
        s = idx[(axr >= e) & (axr < e + step)]
        if len(s) < 10:
            continue
        ntot += 1
        pp2 = perp[s] @ np.vstack([b1, c1]).T
        nc = n_components_2d(pp2, gap)
        if nc > 1:
            nsplit += 1
            ranges.append((e, nc))
    say(f"  {label}: {nsplit}/{ntot} slabs split" + (f"; first [{ranges[0][0]*1000:.0f}mm ncomp={ranges[0][1]}]" if ranges else ""))


say("")
say("--- (a) CONTROL: proximal half 15-50 mm (certainly single-bodied), 6 mm gap, 4 mm slabs ---")
slab_loop(0.015, 0.050, 0.004, 0.006, "proximal 15-50 mm @6mm gap")

say("")
say("--- (b) distal half 55-111 mm at gap thresholds 6 / 10 / 14 mm ---")
for gap in (0.006, 0.010, 0.014):
    slab_loop(0.055, 0.111, 0.004, gap, f"distal 55-111 mm @{gap*1000:.0f}mm gap")

say("")
say("--- (c) fine 2 mm slabs, 74-96 mm: width/thickness/n per slab ---")
say("  slab(mm)   n   width_mm  thick_mm")
for e in np.arange(0.074, 0.096, 0.002):
    s = idx[(axr >= e) & (axr < e + 0.002)]
    if len(s) < 3:
        say(f"  {e*1000:6.0f}  {len(s):4d}   (sparse)")
        continue
    pp = perp[s]
    wb = (pp @ b1).max() - (pp @ b1).min()
    wc = (pp @ c1).max() - (pp @ c1).min()
    say(f"  {e*1000:6.0f}  {len(s):4d}   {wb*1000:7.1f}  {wc*1000:8.1f}")

say("")
say("--- (d) median nearest-neighbour vertex spacing inside 4 mm slabs (sampling density) ---")
for e in (0.040, 0.060, 0.084, 0.100):
    s = idx[(axr >= e) & (axr < e + 0.004)]
    pts = perp[s] @ np.vstack([b1, c1]).T
    if len(pts) < 2:
        continue
    from itertools import combinations
    ds = [np.linalg.norm(x - y) for x, y in combinations(pts, 2)]
    say(f"  slab @{e*1000:.0f}mm: n={len(s)}, median nn gap = {np.median(ds)*1000:.1f} mm, p90 = {np.percentile(ds,90)*1000:.1f} mm (pairwise sample)")

OUT.write_text("\n".join(L), encoding="utf-8")
print(f"\n[receipt written: {OUT}]")
