# E2 SEAM BBW — agent A3 "bbw-binding", fleet (2026-09-14)

Route 3 of the E2 seam fix: BOUNDED BIHARMONIC WEIGHTS on the welded monkey
mesh, truncated to the engine's 3-pin payload format
(`tools/bbw_binding.py`, new script; `tools/classify_run.py` untouched; NO
engine edits).

**VERDICT: the law is REFUTED by its prereg'd falsifier — do NOT post the
payload to the live world.** But the mission's own diagnostic decides the
real finding AGAINST the obvious next move: the top-3 payload FORMAT is NOT
the limit (measured — dense 28-pin blending creases identically), so a
dense-weight format extension would buy nothing. The residual crease is
carried by the engine's linear travel-blend shear on this coarse
tessellation, exactly the boundary-value-problem character Astra's answer
predicted. All numbers below are real measurements; reproduce with
`python tools/bbw_binding.py --report` then `--ab`.

SOURCE (cited, per mission): Astra's answer to fleet Q2 (skin-binding
question, 2026-09-13) — no universal distance-to-pin weighting law is
implied by a thin elastic shell (kernel search retired); the derived object
is a boundary-value problem, geometry-dependent and matrix-valued; the
defensible smoothness surrogate is bounded biharmonic weights; point
attachments need finite patches; curvature metrics must be
resolution-normalized.

## RULE 0 ledger

- Prereg (frozen in the script header BEFORE any run): BBW weights decay
  smoothly, so top-3 truncation swaps happen where the leaving weight is
  tiny; knee-region >10-deg introduced crease edges drop >=50% vs W8 on
  both poses (180 -> <=90, 212 -> <=106), zero pose-introduced
  inverted-winding faces, >=95% of swap edges benign
  (step_e < h_e*tan 10 deg). **LOST** — creases dropped only 29.4% / 27.8%
  (127 / 153); winding flips 2 / 4 (W8 itself has 2 / 2, pre-W8 8 / 14);
  benign 97.1% knee45 but 93.1% compound (< 95%).

## What was built

- Cotangent Laplacian (half-sum cotans; E2's 206 area<1e-8 slivers excluded
  from L and mass — they span the body and would wire the solve with
  near-singular weights), lumped barycentric mass, energy Q = L^T M^-1 L.
- Handles = FINITE vertex patches per Astra: the nearest QUARTILE of each
  pin's W8-classified cell (28 patches, 43-380 verts, 15.4% of the mesh).
  Derivation: a cell covers a fixed surface area, so its nearest quarter is
  resolution-independent in METRIC. The alternative reading — a metric ball
  around the pin — was measured DEAD pre-build: the spine pins are INTERIOR
  (zero surface verts within 0.5x cell radius for spine_upper/mid/lower);
  the quartile attaches at the surface's nearest patch to the joint.
- Same-limb law retained (W8): shipped top-3 = own-limb pins by BBW weight
  first; out-of-limb fill (5880-6571 chain-end verts) with W8's 0.25
  combined cap (0 hits); rows renormalized to sum 1 in float32
  (max |sum-1| 4.5e-8; deg-0 rest return 4.1e-7 — W8-class bounds, PASS).
- Solver: box-constrained active set with clamp-in AND the KKT RELEASE
  phase (SciPy splu; 950 factorizations, 3-87 rounds/handle, 21,830 clamp
  events, 13,595 releases).

Two invalid early runs are on the record and were NOT allowed to speak:
(a) clamp-in without release over-constrained the overshoot regions, broke
partition of unity by 1.555 and NaN-poisoned every metric — the release
phase is load-bearing, not cosmetics; (b) with release, 178 verts (all
lid_L/lid_R) still come out all-zero: the bounded QP optimum itself
violates partition of unity there (bounds [0,1] vs PoU are structurally
inconsistent in the far field — KKT-confirmed, not a solver artifact).
PoU wins where the engine needs sum-1 rows: those 178 verts (0.96%) fall
back to the shipped W8 row, located and counted. An unbounded solve
diagnostic showed 8,903 rows leave [0,1] and 992 shipped rows would carry
NEGATIVE weights — Astra's bounds are necessary for shipping.

## Numbers (E2 knee-region metric, >10 deg introduced vertex-normal delta;
resolution-normalized curvature = deg per METRE of edge length, per Astra)

| binding            | knee45 creases (max deg) | compound creases (max deg) | pose-introduced inverted-winding faces | knee45 norm-max (deg/m) |
|--------------------|--------------------------|----------------------------|----------------------------------------|-------------------------|
| pre-W8 (reference) | 193 (161.9)              | 237 (161.4)                | 8 / 14                                 | 4778 |
| W8 (shipped OLD)   | 180 (165.7)              | 212 (164.6)                | 2 / 2                                  | 4927 |
| BBW (NEW)          | **127 (165.5)**          | **153 (165.8)**            | **2 / 4**                              | 4956 |

Drop vs W8: 29.4% (knee45), 27.8% (compound) — REAL but half the prereg'd
50% bar. The worst crease DEGREE does not drop (165+) — the residual is the
same knife the shipped binding carries.

## Swap-impact distribution (the theory test)

| binding | swap edges | leave-w p50 | leave-w p95 | leave-w max | < bar 0.045 | knee-region swaps | region leave-w p95 | region benign |
|---------|-----------|-------------|-------------|-------------|-------------|-------------------|--------------------|---------------|
| W8      | 4485 | 0.0505 | 0.2868 | 0.7621 | 48.0% | 261 | 0.3350 | 52.9% |
| BBW     | 4100 | 0.0086 | 0.8669 | 1.0000 | 65.9% | 221 | 0.1058 | 51.1% |

The mechanism HALF-confirmed: BBW's typical swap is 6x lighter (p50 0.0086
vs 0.0505) and knee-region swap mass is 3x lighter (p95 0.106 vs 0.335) —
the smooth decay is real. The tail (p95 0.87, max 1.0) comes from the
clamp/renormalize path far from the knee. But the decisive part: knee-region
benign fraction barely moved (51.1% vs 52.9%) while creases dropped 29% —
the crease edges are NOT the swap edges. This converges with E2's prereg-1
LOSS (flip-edge concentration 0.20-0.34, predicted >=0.80) and with the
softmax refutation (identical pin sets, creases ROSE): the residual crease
is the band-wide shear of the engine's per-vertex linear blend of rotated
pin frames on a 0.133 m-median-edge tessellation, re-created by ANY weight
field that must interpolate a 45-deg pivot.

## The diagnostic that decides the routing (format limit or field limit?)

| variant | knee45 | compound |
|---------|--------|----------|
| BBW bounded, top-3 shipped (the payload) | 127 | 153 |
| BBW bounded, DENSE 28-pin blend (what the format cannot ship) | 127 | 153 |
| BBW UNBOUNDED, top-3 (no clamp/renorm path) | 128 | 153 |

Truncation to the 3-slot format adds ZERO creases (dense top-3 mass: median
1.000, p5 0.917, min 0.723 — the 4th+ pins carry nothing in the knee
region). The clamp/renorm path adds at most 1. **The 15-byte format is not
the bottleneck for a smoothness surrogate — do not extend it for this
purpose.** The limit is the FIELD: even the fully smooth 28-pin biharmonic
blend carries 127/153 creases, because the crease is the linear-blend shear
itself (the engine's travel law), not a property of any weight encoding.

## Engine A/B (scratch 127.0.0.1:8157, isolated cwd, born-empty, killed by
PID; live world 8107 untouched, GET-only — never)

Both payloads load (`/tick_vertbind` ok; the engine snapshotted
tick_vertbind.blob, 276889 B) and pose identically well: EVERY frame gated
on /verts matching the offline prediction (2 mm) before capture — old
knee45 pred 0.2602 / obs 0.2602; new 0.2613 / 0.2613; compound old
0.2606/0.2606, new 0.2614/0.2614; rest return 0.000000 in all four.
Captures (identical camera bookmarked at the knee pin, portrait crops):

- `knee45_old_crop.png` — W8: the angular kink mid-leg (the sharp corner).
- `knee45_new_crop.png` — BBW: a visibly rounder, continuous S-bend. The
  29% metric drop is real and visible — but the kink's worst angle does not
  improve, matching the metric's max_deg.

## Derived-from-Astra note (why it half-worked, and why that was expected)

Astra's answer predicted BOTH halves of this outcome. The half that worked:
suppressing distant pins (softmax) narrows transitions and RAISES curvature
(|u''| ~ |du|/l^2), so a smoothness MAXIMIZER (BBW) instead of a
bounded-falloff TRUNCATION must beat the shipped IDW^2 — it did, 29% vs the
softmax's -30.6%, with the same pin-selection law. The half that was always
coming: "no universal distance-to-pin weighting law is implied by a thin
elastic shell — the derived object is a boundary-value problem,
geometry-dependent, matrix-valued." A weight field is a SCALAR surrogate of
that matrix-valued object; the residual shear (127/153 creases, max 165
deg) is what the surrogate cannot represent. No better weight law will
close the gap; the remaining routes attack the LAW OF MOTION (the travel
blend) or the tessellation, not the weights.

## Duplicate-position splits — an independent ship-blocker on this route

E2's hard requirement: float32-exact duplicate verts must carry IDENTICAL
bindings (they must move together — measured 1235 duplicate groups). W8
(distance-only) has 0 splits. BBW, being connectivity-based, gives
coincident verts at cell seams different patches and different weights:
**278 duplicate groups split**. Any future prereg of this route must add
the E2-compliance pass (duplicate-group weight averaging before selection,
then re-prove 0 splits) — that is a NEW membrane, not a patch to this one.

## For the LEAD (routing)

1. **Do not post `vertbind_bbw_payload.bin` to the live world** (prereg
   discipline: the falsifier fired; the 29% is visible but the prereg'd
   bar was 50%, and compound winding flips doubled vs W8, 4 vs 2).
   Independent of the bar: **278 duplicate-position groups split** (E2's
   "duplicates move together" requirement, W8 = 0) — the payload as-is
   would crack at sculpt seams under pose.
2. **Do not extend the payload format to dense weights for this purpose** —
   measured zero benefit (dense == top-3 creases).
3. If the 29% + visibly rounder bend is judged worth having anyway, that is
   a NEW membrane needing a NEW prereg (bar ~30%, flips <= W8's, AND the
   duplicate-split fix as a stated requirement) — the script and machinery
   are ready; the same-limb law and hard constraints all pass. Default
   recommendation: NOT worth it for a seam the judges will still see.
4. The crease's true owner is the linear travel-blend law
   (MembraneTick::apply_travel) at h_med = 0.133 m — a geometry/DOF
   problem (per E2's original band analysis; per Astra's BVP answer), not a
   weight-law problem. Route accordingly.

## Files

- `tools/bbw_binding.py` — generator + solver + metrics + gated A/B (repo)
- `vertbind_bbw_payload.bin` — the exact /tick_vertbind body
  (4 + 18459*15 = 276889 bytes); loads ok; DO NOT POST LIVE
- `metrics.json` — every number above, machine-readable (incl. diagnostics)
- `knee45_{old,new}.png` + `_crop.png`, `compound_{old,new}.png` +
  `_crop.png` — the gated pose-test captures (portrait crops)
- `tick_state_after.json`, `engine_8157_log.txt` — scratch engine state/log
- Console transcripts: `.tmp/bbw_report_console.txt`, `.tmp/bbw_ab_console.txt`
