# D-FOREST-RUNTIME-20260924-FOLLOWUP — correction 2: gap/row/projection convention consistency

**Verdict: the lead's correctness finding (msg-0cca72cf79d34124bcc7f60e5e76a730,
PR #155 @ be058d58) is corrected and regressively pinned. The defect: the
patched `gap_of` uses the VERTICAL gap (`y + radius - h(x,z)`, exact q-derivative
`(-hx,1,-hz)·J`) while the patched `contact_row` returns the NORMALIZED
`(-hx,1,-hz)/||·||·J`, and the pinned positional-correction block consumes
`arows=contact_row, rhs=-gaps` under the pinned invariant "the contact rows ARE
d gap/d q". On h=x+z, J=I, unit mass, gap=-0.01 the projection overshoots to
gap=+0.007320508... (the lead's reproducer, re-derived and confirmed), inside
the pinned 0.05 correction budget. The consumer audit (PREREGISTRATION.md)
found no pinned consumer requires a UNIT row, but the unit surface frame IS
what the velocity/force consumers (friction_solve's mu cone, project_rows'
velocity floors) now see on slopes — so the shared rows are NOT unnormalized
(that would silently rescale the slope friction cone by 1/||·||). Instead the
projection-local rows are rescaled to the exact gap Jacobian
(`row /= contact_normal(...).y`), the pinned `rhs=-gaps` line untouched, the
flat/inactive path bitwise identical (IEEE x/1.0==x). A second, audit-missed
inconsistency of the same class was found by the new compiled regression and
fixed in the same stroke: `sole_local` (the rows' anchor-point selector) kept a
stale PLANE gap law in the terrain arm. All prior evidence (compile placement,
public ctor, oracle parity 0.0 m / 3.469e-18) preserved bit-exactly. No engine
run, no `step()` call, no trunk contact; runtime/visual gates remain PENDING.**

- card: `D-FOREST-RUNTIME-20260924-FOLLOWUP`; correction attempt
  `9b1d9ec7c1ae4c969db51c317b99f44f`, arrival
  `arrival-93d3ca26b5b640a6983176e771421e30`; criteria
  `be7394fa3f7f02f43e67a271926342fb994c1a2042d58791c8cac75fe505a7c3`
- corrects the reviewed candidate at attempt
  `0f29ec07434840939d0b53c4bc5a30b4` (PR #155 head `be058d58`), which itself
  corrected the verified ill-formed-insertion finding on `95df22c9...` — both
  prior attempts and artifacts untouched.
- PREREGISTRATION frozen BEFORE candidate code changes, with the convention
  derivation + full consumer audit; Amendments A1–A5 (disclosed, dated, before
  the first full-suite run, citing the temp smoke-run measurements that
  motivated them) in PREREGISTRATION.md.

## The convention derivation (audit outcome)

Every `contact_row`/`tangent_row`/`gap_of` call site in the pinned tree (blob
`5863348f...` @ `33e7a444`) was read: touch gates (sign tests), friction_solve
(force rows: mu cone couples row_n to the unit tangent rows), project_rows
velocity floors, the positional correction (`rhs=-gaps` — THE pinned contract
"the contact rows ARE d gap/d q"), the energy ledger (scale-cancelling), and
gap-scalar-only consumers (convention-free). Conclusion: no pinned consumer
needs a unit row, but the candidate's terrain arm established the unit
surface-frame FORCE convention; blindly unnormalizing the shared row would
rescale the physical friction cone on slopes by 1/||n||. CHOSEN (the lead's
"row must match the gap derivative" branch, applied at the projection
consumer): keep `contact_row`/`tangent_row` exactly as reviewed; in the
positional-correction block only, rescale each projection-local row by
`1/n_y` (`n_y = contact_normal(...).y = 1/||(-hx,1,-hz)||`), making
`row = (-hx,1,-hz)·J = d gap/dq` exactly; `rhs[a2]=-gaps[a2];` byte-identical
to pinned. The rejected alternative (`rhs *= n_y` with unit rows) is
algebraically equivalent and recorded in the prereg for the reviewer.

## What changed vs the reviewed PR #155 bytes (all inside gait_controller.hpp)

1. **Projection-local row rescale (THE fix).** In `impact()`'s positional
   correction: `arows` are built as `contact_row(es,k)` rescaled by
   `1/contact_normal(es,points_[k]).y`, guarded by a named refusal
   `gait_gap_row_normal_y_invalid`. The pinned comment at the site ("the
   contact rows ARE d gap/d q") is TRUE again on terrain. Flat/inactive:
   n_y=1 → `x/1.0 == x` bitwise.
2. **`sole_local` anchor consistency (found by the new regression, A1).** Its
   stale plane-law comparison (`gh/gm/dy` vs `plane_model_y_`,
   `dy=pm[1]-ph[1]`) could anchor the rows at a pair point that is NOT the
   active terrain gap branch (measured worst mismatch 8.886e-2 before this
   edit). Its selection now consumes the terrain gap law in the active arm;
   original plane expressions verbatim behind; `dy` uses `gm-gh` only on
   terrain (identical values on flat/inactive: pair radii are equal).
3. **Read-only probe seam (regression enabler).** Four one-line forwarders
   (`probe_gap_of`, `probe_contact_row`, `probe_tangent_row`,
   `probe_contact_normal`) inside the patch's existing public seam. No law
   change; exercised by the compiled regression only.
4. **Unchanged:** the gap/contact/tangent ternary edits, member seam, loader
   seam (original plane expressions verbatim in inactive arms), the recipe-
   gated `terrain_grid` activation, the tangent degenerate-axis named refusal,
   the public `TerrainSurface` default ctor, and the whole of
   `terrain_surface.hpp` (bytes identical to the reviewed candidate).

## NEW compiled regression (exercises the patched C++ path; no step() call)

`contact_consistency.cpp` compiles against the PATCHED `gait_controller.hpp`
(pinned subtree @ 33e7a444 + proposed.patch, engine-dir include path, g++
`-std=c++17 -O0`, g++ 15.2.0) and drives construction + public
`model().evaluate()` + the probe forwarders over a real compiled 18-coordinate
walker scene (fixture `inputs/gait_scene.json`, sha256
`f6844eea...`, deterministic product of the pinned-tree scene compiler
`tools/science_funnel/gait_scene.py` @ 33e7a444 — provenance + measured sole
geometry in the prereg). Laws (all in evidence/checks.json):

- **R1 flat-path identity (bitwise):** constant-grid terrain-active walker vs
  no-terrain walker — gaps, contact rows, tangent rows (axes 0/2) bitwise
  equal over all 8 contact points; axis-1 tangent refuses by name
  (`gait_tangent_degenerate`). Also green on the pre-fix law (bitwise_equal
  true) — the regression detects only the reviewed defect class.
- **R2 sloped-plane finite-difference gap/Jacobian:** central FD (h=1e-6) of
  the COMPILED `gap_of` vs the COMPILED projection row over all 18
  coordinates, 16 (state, sole-representative) probes (pair-branch margin
  > 1e-4): worst |row − FD| = **1.038e-10** (bar 1e-7). Pre-fix law: worst
  **1.271e-1** — the predicted `1 − n_y = 0.1271` to four digits.
- **R3 penetration-correction exactness:** the pinned projection algorithm
  (arrows / rhs=-gaps / mass-metric gram / Cholesky / least-norm, budget 0.05)
  on the compiled values. Single row (fore-left pair at −0.003 m): residual
  **8.298e-6 m** (0.28% of |gap|, second-order — the mass metric legitimately
  couples rotations), dq_max 0.0184. Two rows (both fore pairs at −0.0005 m,
  roll-equalized): residuals **1.573e-7 / 1.571e-7 m**, dq_max 0.0031.
  Unilateral law: previously-positive pairs stay positive.
- **R4 BITE (negative control):** the reviewed projection law (raw rows) on
  the same compiled values over-shoots exactly as predicted — single row:
  gap_after **+4.478e-4 m** (predicted +4.369e-4, the lead's reproducer at
  scene scale; band [3e-4, 6e-4]), and R2 mismatch 0.1271 >= 0.05. The
  reviewed BYTES' identity is hash-proven: reverting the three correction
  edits from this correction's modified header reproduces git blob
  `15ea952820d8a84440a2da2831988efbbd08a8c7` / sha256 `476b5905...` — the
  prior attempt's pinned reference materialization of PR #155's header.
- **Prior evidence preserved, this run:** header `-fsyntax-only` exit 0;
  ill-formed stub control exit 1 ("not allowed here"); oracle parity 2081
  points worst height 0.0 m EXACT / worst gradient 0.0 / nodes exact / worst
  normal 3.469446951953614e-18; plane degeneracy exact; gap-law
  constant-grid delta 0.0; extent law exact; physics-symbol guard green;
  patch applies to the pinned blob, scope exactly the two engine files.
- `python -B implementation.py all` → exit 0, `all_ok: true`;
  `python -B -m unittest test_implementation` → **Ran 25 tests, OK**;
  fresh-directory re-run: exit 0, OK, `proposed.patch` byte-identical
  (sha256 `b02fc9e65da5459120249d8fd2ec3068818dcd0c43385ffe4331815ac431acb8`).

## Predictions lost / refined (honest)

- **R3 "|gap_after| <= 1e-8" REFINED-LOST (A3):** the frozen exactness bar
  assumed a pure-translation correction; the pinned mass-metric least-norm
  legitimately couples rotations, so the residual is second-order (measured
  8.298e-6 at 3 mm). The shipped law is the second-order bar
  (<= 2% of |gap_before|) + pinned budget + unilateral preservation, frozen in
  Amendment A3 BEFORE the first full-suite run.
- **Two-row scenario re-authored (A4):** the frozen pure-vertical drop to
  −0.003/−0.001 measures dq_max 7.94e-2 — beyond the engine's own 0.05 budget;
  translations cannot change the pairs' relative height on a constant-gradient
  plane (probe-verified), so the scenario roll-equalizes then drops both pairs
  to −0.0005.
- All other prereg predictions measured as predicted (R1 bitwise; R2 bar and
  bite within their bands; R4 overshoot +4.478e-4 vs predicted +4.369e-4; the
  lead's reproducer algebra confirmed; prior frozen numbers bit-reproduced).

## Honest boundary (preserved gates)

The regression exercises the COMPILED patched gap/row members and the pinned
projection algorithm on those compiled values, plus TU well-formedness of the
in-class edit (`-fsyntax-only` exit 0). The in-class positional-correction
statement itself runs inside `impact()` during engine walks and is NOT
executed headless: no `step()` call exists anywhere in this attempt —
construction (`reset()` state seeding), public `evaluate()`, and probe
forwarders only. NOT done, all still PENDING: full engine build, the recipe
integration carrying `terrain_grid`, the collision query route (S1-3), render
binding + normal hygiene (S1-4), any engine walk replay (A1 byte-identity),
W10 readiness, all runtime and visual gates. Trunk contact remains Stage 2.

Environment: Windows x64, CPython 3.14.3, g++ 15.2.0 (MinGW), numpy 2.2.6 (only
for the one-off scene-fixture provenance run). Read-only against
E:/ChimeraWork/monkey-play-20260924 and E:/PythonChimera; all scratch trees in
temp dirs; prior attempt workspaces untouched; zero writes in E:/PythonChimera
and E:/Chimera.
