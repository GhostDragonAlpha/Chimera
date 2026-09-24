# M04 PREREGISTRATION — Rigid-transform covariance of exported mass properties

Campaign: 24h material-volume campaign, worktree `E:/ChimeraWork/mvc-20260924`
(branch `material-volume-campaign-20260924`, base `3db8bc4e`).
Frozen: `prereg_expectations.json` sha256 `9c857835a7294fd3454c21fc2c6a930c88e818719cb8455daa2c2b52a90919ce`.
This document is written BEFORE the first exporter invocation. After the freeze:
no expectation edits, no tolerance changes, no new runs.

## Rule-0 theory

- **STATEMENT** (disagreeable): the material-volume exporter's exported mass
  properties are rigid-motion covariant — under any proper rigid motion of the
  partition geometry the domain-frame export satisfies `COM → R·COM + t` and
  `I → R·I·Rᵀ`, and when the co-moving frame is authored the body-frame export
  is invariant (`COM` and `I` unchanged).
- **PREDICTION** (unmeasured until the runs below): all 7 preregistered runs ×
  all quantities (COM 3 components, inertia 9 entries, mass, volume) match the
  frozen hand-derived expectations within relative tolerance 1e-9.
- **FALSIFIER** (named before the run): ANY quantity in ANY run outside the
  frozen tolerance; or exporter refusal / `export_status ≠ complete` /
  non-exported group on schema-valid fixtures. A single red entry refutes.
- **Stop rule**: stop when every run (7) is verdicted for every quantity
  (12 mass-property quantities + mass + volume). No additional runs, no
  re-rolling, no tuning. Instrument failures before any verdict (exporter crash
  or refusal traced to a fixture defect) are logged in
  `receipts/iterations.log`, the fixture alone is repaired (expectations
  untouched), and the affected runs are re-executed.

## Tested input path (task 1)

The exporter (`tools/material_volume_body_export.py`, copied byte-identical to
`work/`) integrates cells in **domain coordinates** (`_integrate_cells`) and
takes transforms ONLY through the authored
`body_frame.domain_from_body {rotation, origin_m}` per
`chimera.rigid_body_cell_groups.v1`: it writes
`center_body = Rᵀ(COM_domain − origin)` and
`inertia_body = Rᵀ·I_domain·R` (`_body_mass_properties`); it never transforms
input geometry itself (`x_domain = R·x_body + origin_m` is the documented
authored-transform contract, doc `Chimera/docs/matter/material_volume_body_export.md`).

Both legal injection points are exercised, as two legs on the same frozen
fixture:

- **Leg A (geometry-side motion, identity authored frame)** — the motion is
  applied to the partition vertices by the fixture generator; the exporter
  exports in the domain basis. Tests integrator covariance: COM → R·COM + t,
  I → R·I·Rᵀ in the FIXED basis.
- **Leg B (co-moving authored frame — the exporter's own transform path)** —
  the same moved geometry, with `domain_from_body = {rotation R, origin t}`
  authored. Tests the exporter's frame re-expression: body-frame COM and
  inertia come back UNCHANGED (rotated-basis invariance). B-runs are the only
  runs that exercise `_body_mass_properties` with non-identity R and non-zero
  origin (the path the schemas/examples support for transforms).

## Derivation (task 2) — hand algebra, two independent exact paths

**Cell closed form (path 1).** Right tetrahedron, apex p, orthogonal legs
a = (a₁,a₂,a₃) (signed octant legs), density ρ, mass m = ρ|a₁a₂a₃|/6.
Unit right tetra T = {x,y,z ≥ 0, x+y+z ≤ 1}, V = 1/6, centroid (¼,¼,¼):

- ∫ x² dV = ∫₀¹ x²(1−x)²/2 dx = 1/60; ∫ xy dV = ∫₀¹ x(1−x)³/6 dx = 1/120
- C_xx = ρ(1/60) − m·(1/16) = (per unit mass) 3m/80; C_xy = ρ(1/120) − m/16·… = −m/80

Anisotropic scaling D = diag(|a|) maps T to the cell, C → D·C·Dᵀ, giving the
closed form used (i,j ∈ {1,2,3}):

    C_ij = (m/80) · a_i a_j · (4δ_ij − 1)      [centroid = p + a/4]

**Raw-monomial simplex path (path 2, independent algebraic route).** With
vertices p0..p3, edge matrix E = [p1−p0 | p2−p0 | p3−p0], V = |det E|/6, and
reference-simplex integrals ∫_{T0} q dV = (1,1,1)/24,
∫_{T0} q qᵀ dV = (I₃+J₃)/120, the Jacobian 6V gives

    ∫ x xᵀ dV = V·p0p0ᵀ + p0·(V·r/4)ᵀ + (V·r/4)·p0ᵀ + (V/20)(EEᵀ + r·rᵀ),
      r = E·(1,1,1)ᵀ;   C = ρ·∫x xᵀ dV − m·c·cᵀ.

Both paths are evaluated in exact rational arithmetic (`fractions.Fraction`)
and asserted EQUAL for every cell — they agreed on all three cells (after two
implementation bugs in path 2 were caught BY this assertion during derivation:
a dropped Jacobian factor and a missing density factor; the closed form was
never modified).

**Body assembly.** COM = Σ m_k c_k / M;
I = Σ_k [ tr(C_k)·Id − C_k + m_k(‖d_k‖²·Id − d_k d_kᵀ) ], d_k = c_k − COM
(textbook parallel-axis theorem — shared physics, different computational path
from the exporter's per-cell `(m/20)Σ(v_k−c)(v_k−c)ᵀ` code).

**Covariance laws under x → R x + t (R proper, det +1).**

- Volumes/masses invariant (det R = +1). Legs a → R a ⇒ C_k → R C_k Rᵀ
  (closed form: `(Ra)_i(Ra)_j(4δ−1)` = R[(m/80)a_i a_j(4δ−1)]Rᵀ).
- COM → Σ m_k(R c_k + t)/M = R·COM + t.
- d_k → R d_k ⇒ parallel-axis term → R(·)Rᵀ ⇒ **I → R·I·Rᵀ in the fixed
  (domain) basis**; translation alone (R = Id) leaves I invariant.
- Authored co-moving frame {R, t}: center_body = Rᵀ(R·COM + t − t) = COM;
  inertia_body = Rᵀ(R I Rᵀ)R = I — **in the rotated basis, I is unchanged**.

**Off-diagonal mixing.** R is a rotation by 37° about the non-axis-aligned
direction (1,1,2)/√6; all 9 entries of R are nonzero (frozen below), so any
nonzero diagonal input maps to a fully populated tensor. The fixture base
tensor is already fully populated (all three off-diagonals ≠ 0, exact), which
makes the fixed-basis mixing test strictly stronger: every one of the 9 entries
must move to the analytic value of R·I·Rᵀ.

## Fixture (task 3, frozen)

Three right tetrahedra sharing one apex vertex v_apex = (0,0,0), interiors
disjoint (distinct octants), conforming at the shared vertex; positive
orientation asserted per cell in the file order (cell-y's frozen order is
`(apex, −x-leg, +z-leg, +y-leg)`; det = +24 > 0):

| cell | apex | legs (signed, m) | file vertex order | density (kg/m³) | mass (kg) | V (m³) | centroid (m) |
|---|---|---|---|---|---|---|---|
| cell-x | (0,0,0) | (+2, +3, +5) | (apex, +x, +y, +z) | 1000 | 5000 | 5 | (1/2, 3/4, 5/4) |
| cell-y | (0,0,0) | (−4, +2, +3) | (apex, −x, +z, +y) | 800 | 3200 | 4 | (−1, 1/2, 3/4) |
| cell-z | (0,0,0) | (−3, −2, +4) | (apex, −x, −y, +z) | 1200 | 4800 | 4 | (−3/4, −1/2, 1) |

Materials `mat-x/mat-y/mat-z` (sources "M04 analytic rigid-covariance fixture",
uniform); regions `region-x/y/z` with distinct owners `owner-x/y/z`; one body
group `m04-rigid-body` owning all three cells (multi-cell body).
`mass_authority = reconstructed_tissue_mass` everywhere. All fixtures
schema-validated against the EXISTING `tools/material_volume_body_export_schema.json`
(groups) and `tools/material_volume_admission_schema.json` (manifest,
partition) with jsonschema 4.25.1. Hashes: `fixtures/fixture_sha256.json`.

**Exact base mass properties (the frozen ground truth, exact rationals):**

- M = 13000 kg, V = 13 m³
- COM = (−43/130, 59/260, 269/260) m
  = (−0.33076923076923076, 0.22692307692307692, 1.0346153846153847)
- I about COM (kg·m²), exact / float64:

| | col 1 | col 2 | col 3 |
|---|---|---|---|
| row 1 | 16175 | 171460/13 | 177790/13 |
| row 2 | 171460/13 | 498215/26 | 418265/26 |
| row 3 | 177790/13 | 418265/26 | 443255/26 |

  float64: (0,0) 16175.0 · (0,1) 13189.23076923077 · (0,2) 13676.153846153846 ·
  (1,1) 19162.115384615383 · (1,2) 16087.115384615385 · (2,2) 17048.26923076923
  (symmetric; exact fractions in `prereg_expectations.json`).
- All base off-diagonals ≠ 0 and all COM components ≠ 0 (asserted at freeze).

**Frozen motion.** R = Rodrigues(axis (1,1,2)/√6, θ = 37°), float64-frozen:

```
[[ 0.832196258372744, -0.45781916042913656,  0.3128114510281963],
 [ 0.524940657080039,  0.832196258372744, -0.17856845772639146],
 [-0.17856845772639146, 0.3128114510281963,  0.9328785033490976]]
```

max|RᵀR − I| = 2.776e-17, |det R − 1| = 0.0 — passes the exporter's own
orthonormality/determinant gate (1e-10) with ~7 orders of margin.
t = (13.0, −7.0, 4.5) m (dyadic — exact in float64).
R·I·Rᵀ (float64, frozen):

```
[[ 9349.133258146107, 10493.969541725297,  8895.610974579162],
 [10493.969541725299, 22449.93567592251,  19561.754032032724],
 [ 8895.610974579162, 19561.754032032728, 20586.315681316002]]
```

## Runs + frozen expectations (task 3)

7 runs (identity motion needs no separate B run: B0 ≡ A0 by construction).
"want" values are frozen in `prereg_expectations.json` (`expectations.runs`);
floating expectations are exact to the last bit of the repr below.

| run | motion (geometry) | authored frame | COM want | inertia want |
|---|---|---|---|---|
| run_A0_identity | v | {I, 0} | COM₀ | I₀ |
| run_A1_translation | v + t | {I, 0} | COM₀ + t = (12.669230769230768, −6.773076923076923, 5.534615384615385) | I₀ |
| run_A2_rotation | R·v | {I, 0} | R·COM₀ = (−0.05551510907227014, −0.16953935535881062, 1.0952195399078481) | R·I₀·Rᵀ |
| run_A3_rot_then_trans | R·v + t | {I, 0} | R·COM₀ + t = (12.944484890927729, −7.16953935535881, 5.595219539907848) | R·I₀·Rᵀ |
| run_B1_translation_comoving | v + t | {I, t} | COM₀ | I₀ |
| run_B2_rotation_comoving | R·v | {R, 0} | COM₀ | I₀ |
| run_B3_rot_then_trans_comoving | R·v + t | {R, t} | COM₀ | I₀ |

Every run additionally must export `mass = 13000.0 kg` and `volume = 13.0 m³`
(frame-invariant). B-run outputs must name their authored `frame_id` and
`basis: authored_body_frame`; A-runs export in `m04-coupon-domain`.

## Frozen tolerances (≤1e-9 relative, exact text from expectations JSON)

A quantity PASSES iff BOTH:
1. `dev_max = max|got − want| ≤ 1e-9 · max|want|` (entry-wise deviation bounded
   by 1e-9 × the largest-magnitude expectation entry of that quantity — handles
   exact-zero entries without relativizing against zero), AND
2. `frobenius_ratio = ‖got − want‖_F / ‖want‖_F ≤ 1e-9`.

Applied to COM (3), inertia (9), mass, volume, in every run. Falsifier: any
single violation anywhere ⇒ REFUTED; the numbers are reported as measured and
preserved. Verdict is COVARIANT only if all 7 runs pass everything.

## Execution plan (after freeze)

`python work/material_volume_body_export.py` (work/ copy, byte-identical,
sha256 `04be88a7c62dc358c06aff29d3ac70244ae575298603712d2352d44853e018e7`;
admission `d6d4b0e010c0982f5c94dc880a2fec4ac50ea69af605ce80b7186745a5f7750d`;
compiler `6d2817b7b4ea59213f90134b343a06579d92db998c1db7f27b0e89aff71799cf`)
is invoked once per run with `PYTHONDONTWRITEBYTECODE=1`, CPU-only (numpy
float64), stdout captured to `receipts/<run>.json` with exit code and command
logged. `work/compare_runs.py` (written before the first run) then compares
receipts against `prereg_expectations.json` only.

Module copies verified byte-identical to `tools/` originals at freeze time
(sha256 above, recorded in `receipts/module_hashes.json` at run time).
`tools/` and `Chimera/docs/matter/` remain READ-ONLY (integrity check pasted in
report.md).

---

## AMENDMENT 1 (append-only; repair recorded in receipts/iterations.log, iterations 1 and 1b)

The first execution of the 7 preregistered runs was blocked at admission
(`compiler_refusal:non_manifold_vertex_link`; the three cells shared one apex
vertex). A first repair attempt with coincident (unmerged) apexes was refused
as `duplicate_vertex_position`. Both refusals are fixture defects, not
covariance results: they were diagnosed via `work/material_volume_admission.py`
and the blocked receipts are preserved in `receipts/iteration1_blocked/`.

Per the frozen stop rule, the FIXTURE alone was repaired: the three right
tetrahedra keep their legs, signs, densities, orientations, and frozen order,
but each apex is placed on its own disjoint copy of the domain:

| cell | apex (m) | legs (signed) | density (kg/m³) |
|---|---|---|---|
| cell-x | (0, 0, 0) | (+2, +3, +5) | 1000 |
| cell-y | (−20, 0, 0) | (−4, +2, +3) | 800 |
| cell-z | (0, −20, 0) | (−3, −2, +4) | 1200 |

Vertex positions are pairwise distinct and cells share no vertices (manifold
links; 3 connected components — the shipped coupon's pattern). The exact
expectations were RE-DERIVED by the identical frozen method (both independent
exact paths, asserted equal per cell; design assertions extended with
distinct-position and no-shared-vertex guards) and RE-FROZEN BEFORE any
re-run. Motion, tolerance (1e-9 relative, both criteria), falsifier, stop
rule, and run matrix are unchanged from the original freeze.

**Amended exact base (frozen):** M = 13000 kg, V = 13 m³,
COM = (−683/130, −1861/260, 269/260) m =
(−5.253846153846154, −7.157692307692308, 1.0346153846153847);

| I₀ (kg·m²) | col 1 | col 2 | col 3 |
|---|---|---|---|
| row 1 | 17768675/13 | 6019460/13 | −59010/13 |
| row 2 | 6019460/13 | 27813415/26 | 331865/26 |
| row 3 | −59010/13 | 331865/26 | 62875255/26 |

float64: (0,0) 1366821.1538461538 · (0,1) 463035.3846153846 ·
(0,2) −4539.2307692307695 · (1,1) 1069746.7307692308 ·
(1,2) 12764.038461538461 · (2,2) 2418279.0384615385 (symmetric).
All base off-diagonals ≠ 0; R and t unchanged from the original freeze;
R·I₀·Rᵀ frozen in `prereg_expectations.json` (fully populated).

**Amended run expectations** (same structure as the original freeze; values in
`prereg_expectations.json`, sha256
`8100ca5981abf29bdc6c0c2a33a5cddf3889050d6b0ad3f8a02b5fdfed1e4570`):
A-runs (identity frame): COM → COM₀ + t / R·COM₀ / R·COM₀ + t, I → I₀ / R·I₀·Rᵀ;
B-runs (co-moving frames {I,t}, {R,0}, {R,t}): COM and I identical to A0's
body-frame values (COM₀, I₀). Amended want-COM values:
- run_A1: (7.746153846153846, −14.157692307692308, 5.534615384615385)
- run_A2: (−3.6439035325322282, −8.45642179624337, 5.54262075679479)
- run_A3: (9.35609646746777, −15.45642179624337, 10.04262075679479)

Admission dry-check of the repaired fixtures (diagnosis tool, work/ copy):
`validation_only_admissible`, zero reason codes, for every run's manifest +
partition.

### AMENDMENT 1 CORRECTION (append-only)

The prose values above for run_A2 and run_A3 want-COM were transcribed
INCORRECTLY (hand-recopied, not read from the frozen JSON; run_A1's z component
was 1 ulp off in repr). The authoritative want values were always those in
`prereg_expectations.json`, which was never modified after the Amendment-1
freeze and is what `work/compare_runs.py` reads. Corrected want-COM:

- run_A1: (7.746153846153846, −14.157692307692308, 5.5346153846153845)
- run_A2: (−0.7716628886613861, −8.899311882813114, −0.3356664604165974)
- run_A3: (12.228337111338615, −15.899311882813114, 4.164333539583403)

---

## AMENDMENT 2 (append-only; repair recorded in receipts/iterations.log, iteration 2)

The first verdict attempt (all 7 runs complete, exit 0) FAILED the falsifier on
every run's inertia tensor — with a surgically specific signature: diagonals
matched to machine precision, every off-diagonal off by exactly −15825, and
COM/mass/volume matching at ~1e-15. The decisive whole-body Monte Carlo
integration of the true fixture geometry (`receipts/mc_crosscheck.txt`) agreed
with the EXPORTER to sampling noise (~1e-5 relative) and against the frozen
want. Diagnosis: the expectation assembly
(`work/compute_expectations.py::inertia_from_cov`) added tr(C) to EVERY entry
instead of tr(C)·δ_ij; the sum of per-cell traces is 7125 + 3480 + 5220 =
15825 kg·m² — exactly the observed constant. The exporter's integrator is
independently validated against ground truth by the Monte Carlo; the red
comparison and receipts are preserved in `receipts/iteration2_wrong_expectation/`.

Per the frozen stop rule, the EXPECTATION code alone was repaired (one line);
the fixture, motion, tolerances, run matrix, falsifier, and stop rule are
unchanged, and the fixtures' sha256 are verified unchanged. Corrected exact
base (RE-FROZEN before the verdicted re-run; prereg_expectations.json sha256
`90102ec7919438f11733423cf053189fa0a355f91afc31bced2f82037e30bfeb`):

| I₀ (kg·m²) | col 1 | col 2 | col 3 |
|---|---|---|---|
| row 1 | 17768675/13 | 5813735/13 | −264735/13 |
| row 2 | 5813735/13 | 27813415/26 | −79585/26 |
| row 3 | −264735/13 | −79585/26 | 62875255/26 |

float64: (0,0) 1366821.1538461538 · (0,1) 447210.3846153846 ·
(0,2) −20364.23076923077 · (1,1) 1069746.7307692308 ·
(1,2) −3060.9615384615386 · (2,2) 2418279.0384615385 (symmetric).
All base off-diagonals ≠ 0 (asserted). COM, mass, volume, R, t unchanged from
Amendment 1. R·I₀·Rᵀ recomputed from the corrected I₀ (frozen in the JSON,
fully populated, all 9 entries ≠ 0 — asserted).

The 7 runs were re-executed AFTER this re-freeze; their receipts are the
verdicted ones at `receipts/`.
