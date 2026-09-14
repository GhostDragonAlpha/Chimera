# E2 SEAM NOTE — agent E2, fleet 2 (2026-09-13)

Mission: the blind judges saw "visible joint seams — prototype look". Diagnose
and fix, touching only the travel/normals/tint regions of
`ChimeraEngine/engine/membrane_tick.cpp` (marked // E2).

Files: this note + `.tmp/e2_seam_analysis.py` (pass 1, raw) /
`e2_seam_analysis2.py` (sign-aware) / `e2_seam_analysis3.py` (region-scoped) /
`e2_seam_analysis4.py` (THE decision record — lambda derivation + tint
verification; re-run reproduces every number below). No build, no commit.

## RULE 0 ledger

- Prereg 1 (mechanism): seams = C1 discontinuities at binding pin-set flips,
  reproduced by per-tick normals. **LOST** — flip-edge concentration of the
  introduced crease measured 0.20–0.34, prediction was >= 0.80.
- Prereg 2 (normal relax): a lambda <= 0.5 collapses the region's >10 deg
  introduced-delta population by >= 90% with normal-deviation p99 < 12 deg.
  **LOST** — best 72% at any lambda; deviation p99 9.1–14.1 deg and the
  collapse saturates. lambda DERIVED from the sweep = none. Edit A NOT SHIPPED.
- Prereg 3 (tint): per-vertex-averaged + saturating ramp collapses the
  group-boundary ring. Current ring measured 0.4675 channel units (full
  contrast, saturates at any press >= ~30%); proposed boundary max 0.1457,
  one-ring transition max 0.2004 — the hard ring becomes a soft gradient.
  **HELD** — Edit B SHIPPED.

## Measured facts (monkey_full.bin: 18459 verts, 36630 tris; pins joints28.json)

Binding (tools/classify_run.py, verbatim): 3 nearest pins, inverse-distance^2
weights. Rest blend == authored rest (max pos err 4e-7). Authored normals ==
area-weighted accumulation of the raw faces (max angle 0.0 deg).

Static pathology (both poses and rest — not the seam): the sculpt has 206
sliver faces (area <= 1e-8) and knife-fold geometry — face-normal deltas of
180 deg across shared edges AT REST (p99 146 deg). Winding is perfectly
consistent (flood fill: 0 flipped faces), so these are real geometric folds,
static, identical at rest and posed. All decision metrics therefore use the
pose-INTRODUCED change (posed - rest, per edge) scoped to the knee region
(sane edges within 1.5 m of the knee_L pin; 2468 edges).

POSED knee_L=45 deg, introduced vertex-normal delta (knee region):
  max 161.9 deg, p99 31.1 deg, mean 2.7 deg
  >10 deg: 193 edges (7.8% of region) | >20 deg: 61 | >60 deg: 4
  rest baseline in region: max 151.3 (static folds), p99 26.4, mean 10.4
Compound hip20+knee45: max 161.4, p99 35.0, >10 deg: 237 edges.

Mechanism — NOT pin-set flips (flip-frac of introduced >5 deg edges: 0.22 in
the 0.5–1.0 m band; 0.07 near the pin; ~0 far): pivot-heterogeneous linear
blend shear. Thigh vertices at y ~ 2.5–2.9 bind [spine_lower, hip_L, hip_R]
(all idle at a knee pose -> stay at rest) while one ring away vertices bind
[spine_lower, hip_L, knee_L] with knee weight 0.17–0.26 (rotate). Result: a
shear band 0.5–1.0 m above the knee pin (29.2% of band edges introduce >5 deg)
plus spikes: 204 crease-carrying vertices, 97 grow >2 cm ring-deviation
(max 16.7 cm, median 1.8 cm).

Lambda sweep (knee45, knee region; target: >10 deg count -90%, intro max
<= 45 deg, deviation p99 < 12 deg):
  lam 0.25: 151 (78%) | 0.30: 147 (76%) | 0.35: 139 (72%, dev p99 11.4)
  lam 0.40: 137 (71%, dev p99 12.4) | 0.45: 130 (67%) | 0.50: 131 (68%)
  -> no lambda meets the prereg; the crease is a ~band-wide field the posed
  surface re-creates every tick; one bounded iteration cannot flatten it and
  the crispness cost on well-defined normals is real. The engine normals are
  NOT the culprit — they faithfully report a geometric blend defect.

Duplicates: 1235 float32-exact duplicate-position groups (2490 verts, 1277
pairs checked) — 100% have IDENTICAL bindings (same pin set, same weights).
They move together; no crack mechanism. Recorded so nobody chases it.

Tint (knee_L group pressed; cell loads F/cnt with capacity = 15e6*area, floor
0.1 N; knee group 503 sane cells, 59 group-boundary edges): the per-cell
linear write saturates the whole patch (cells' capacity spread is narrow vs
the group force), so ANY meaningful press paints a FULL-contrast ring at the
group boundary: max per-edge color jump 0.4675 channel units (57 region edges
> 0.05). Per-vertex-averaged t + saturating t/(1+t): boundary max 0.1457,
one-ring transition max 0.2004 — soft gradient, no ring, no last-writer-wins
speckle (per-vertex color is now single-valued).

## Engine change (// E2, membrane_tick.cpp)

Edit B only: the tint loop now accumulates the clipped per-cell t over the
cells touching each vertex, then writes ONCE per vertex through the
saturating ramp t/(1+t) with the existing red-ramp formulas; any failed cell
touching a vertex marks it dark (0.08) deterministically (was
last-writer-wins). Unpressed rest look is unchanged (t=0 -> authored base).
Cost: two nv-sized temporaries + one extra vertex pass per tick (same class
as the existing per-tick normals buffer).

Edit A (bounded 1-iteration Laplacian relax of the POSED NORMALS accumulation)
was implemented in simulation, REFUTED by its falsifier, and deliberately NOT
applied. Do not add it "to see" — the sweep above is the reason.

## For the LEAD (routing)

1. THE actual seam fix is in the BINDING, not the engine: regenerate
   `tools/classify_run.py`'s vertbind with (a) same-limb pin restriction
   (no hip_R in left-thigh sets), (b) bounded weight falloff (softmax
   temperature or blend radius instead of raw 1/d^2) so the effective-angle
   gradient across one ring is bounded. Owner needed — outside E2 regions
   (weight clamping in the engine was forbidden by the mission). After that
   lands, re-run e2_seam_analysis4.py: the introduced-crease block should
   collapse at source; only then reconsider a residual normal relax.
2. Press-rim normals (press code owner — NOT touched by E2): the
   displaced-normal recompute in step() (~line 400 post-edit) skips faces
   with all-zero press offsets, so dimple-rim vertices accumulate a BIASED
   subset of their faces -> shading bias ring around touch dimples while a
   press is active. Suggested: drop the all-zero-offsets skip (full
   accumulation; the posed pass already pays it every tick) or reuse the E2
   relax there once justified.
3. Capture at the build window (before = current binary stash, after = with
   Edit B; identical camera and pose both times):
   - Pose: POST /tick_pose {"idx":13,"deg":20} then {"idx":15,"deg":45}
     (hip_L 20, knee_L 45).
   - Tint ring: POST /tick_intent with the knee joint index and a force
     (any force reaching ~30% median-cell t saturates the patch — measured).
   - Camera: v[8] bookmark aimed at the knee_L pin, world (0.4833, 1.9033,
     -0.0155) — the pin itself does not move under pose; ~0.6 m out,
     framing the thigh band y ~ 2.5–2.9 so the seam ring crosses the
     silhouette. Save/recall via POST /cameras {"op":"save"/"recall"}.
   - EXPECT: the red press ring at the knee-group boundary is gone (soft
     gradient instead). EXPECT UNCHANGED: the shading crease band above the
     knee (that is the binding defect, item 1 — do not judge Edit B on it).
   - FPS: re-run the bench probe (.tmp/bench_report.md procedure); Edit B
     adds one vertex pass + two nv buffers per tick.
