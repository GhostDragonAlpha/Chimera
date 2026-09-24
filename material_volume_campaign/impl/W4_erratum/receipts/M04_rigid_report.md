# M04 REPORT — Rigid-transform covariance of exported mass properties

Agent: M04 · Campaign: 24h material-volume campaign · Worktree:
`E:/ChimeraWork/mvc-20260924` (branch `material-volume-campaign-20260924`,
base `3db8bc4e` — the "3db4bc4e" in the brief context line is a typo for this).
Preregistration: `prereg.md` (with append-only Amendments 1-2) + frozen
`prereg_expectations.json`. CPU-only; `PYTHONDONTWRITEBYTECODE=1` everywhere;
`tools/` and `Chimera/docs/matter/` untouched (integrity paste at the end).

## VERDICT: COVARIANT (green)

All 7 preregistered runs x all quantities (COM 3, inertia 9, mass, volume)
PASS the frozen tolerance (<=1e-9 relative, both criteria) with ~6 orders of
margin. The falsifier was named before execution, fired exactly once — against
my own expectation code, not the exporter (iteration 2, below) — and the
corrected re-freeze preceded the verdicted re-run. Stop rule satisfied: every
run verdicted; stopping now.

## Rule-0 theory (from the prereg)

- STATEMENT: exported mass properties are rigid-motion covariant — under
  x -> Rx + t (det R = +1) on the partition geometry, domain-frame exports obey
  COM -> R*COM + t and I -> R*I*R^T, and under the co-moving authored frame the
  body-frame exports are invariant.
- PREDICTION: 7 runs x 12 quantities + mass + volume within 1e-9 relative of
  hand-derived exact expectations. CONFIRMED (numbers below).
- FALSIFIER: any quantity of any run outside tolerance, or refusal/non-complete
  status on schema-valid fixtures. Status: did not fire against the exporter;
  it fired once against my expectation code and was resolved by ground-truth
  Monte Carlo (see "Falsifier fired", below).
- Stop rule: all runs verdicted -> stop. SATISFIED.

## Tested input path (task 1)

The exporter transforms NOTHING itself. It integrates cells in domain
coordinates (`_integrate_cells`) and re-expresses the result through the
authored `body_frame.domain_from_body {rotation R, origin_m}` — the only
transform path the schemas/examples support
(`chimera.rigid_body_cell_groups.v1`; doc `material_volume_body_export.md`:
`x_domain = R*x_body + origin_m`, output `R^T(COM-origin)`, `R^T*I*R`).
Both injection points were exercised on one frozen fixture:

- Leg A (runs A0-A3): geometry moved by the motion, authored frame identity ->
  exports the domain basis; tests integrator covariance (fixed basis).
- Leg B (runs B1-B3): same moved geometries, authored CO-MOVING frames
  {I,t}, {R,0}, {R,t} -> tests the exporter's own frame re-expression
  (rotated basis: outputs must come back unchanged). Only B-runs exercise
  `_body_mass_properties` with non-identity R and non-zero origin.

## Derivation (task 2, summary — full algebra in prereg.md)

Per cell (right tetrahedron, apex p, signed octant legs a, mass m):
centroid c = p + a/4, centroidal covariance
C_ij = (m/80)*a_i*a_j*(4*delta_ij - 1) — derived by direct integration of the
unit right tetra (int x^2 dV = 1/60, int xy dV = 1/120) plus anisotropic
scaling, and independently re-derived via reference-simplex raw monomial
moments: int xx^T dV = V*p0*p0^T + p0*(V*r/4)^T + (V*r/4)*p0^T + (V/20)*(E*E^T
+ r*r^T). Both paths computed in exact rational arithmetic and ASSERTED equal
per cell. Body: COM = sum m c / M; I = sum[ tr(C)*delta - C + m(d^2*delta -
d d^T) ]. Covariance laws: C_k -> R C_k R^T (legs a -> R a, quadratic form),
COM -> R*COM + t, d_k -> R d_k, hence I -> R I R^T in the fixed basis; the
co-moving frame {R, t} pulls back to exactly COM and I (rotated-basis
invariance). R = Rodrigues((1,1,2)/sqrt(6), 37 deg) is fully populated (all 9
entries != 0), so diagonal-only inputs must mix into fully populated tensors;
the fixture base tensor is already fully populated (off-diagonals 447210.38,
-20364.23, -3060.96 — nonzero, asserted at freeze), making the fixed-basis
test strictly stronger: all 9 entries move.

## Fixture (task 3)

Three right tetrahedra (apexes (0,0,0), (-20,0,0), (0,-20,0); signed legs
(+2,+3,+5), (-4,+2,+3), (-3,-2,+4); densities 1000/800/1200 kg/m^3), disjoint
components, conforming, positive orientation per cell; ONE body group
`m04-rigid-body` owns all 3 cells (multi-cell body). Mass 13000 kg, volume
13 m^3. All 21 fixture documents validated against the EXISTING
`tools/material_volume_body_export_schema.json` (groups) and
`tools/material_volume_admission_schema.json` (manifest, partition) with
jsonschema 4.25.1. Motion: R = Rodrigues((1,1,2)/sqrt(6), 37 deg)
(max|R^T R - I| = 2.8e-17, |det R - 1| = 0 — inside the exporter's own 1e-10
gate), t = (13, -7, 4.5) m.

## Preregistration trail (3 freezes, all append-only, hashes recorded)

1. Original freeze `prereg_expectations.json` sha256 9c857835...0919ce —
   fixture with a single shared apex vertex.
2. Amendment 1 (fixture repair; entries in receipts/iterations.log): the
   compiler refused the shared-apex complex (`non_manifold_vertex_link`) and
   also coincident unmerged vertices (`duplicate_vertex_position`); cells were
   separated in space, exact expectations re-derived by the identical frozen
   method, re-frozen sha256 8100ca59...d1e4570 before any re-run.
3. Amendment 2 (expectation-code repair): see "Falsifier fired" below;
   re-frozen sha256 90102ec7...e30bfeb before the verdicted re-run. Fixture
   bytes verified unchanged across Amendment 2 (receipts/
   fixture_hash_check_iteration3.txt).

## Execution (task 4)

`python work/material_volume_body_export.py --manifest ... --partition ...
--groups ...` per run — work/ copies sha256-verified byte-identical to the
read-only `tools/` originals (receipts/module_hashes.json). 7 runs, exit 0,
`export_status: complete`, `admission_status: validation_only_admissible`,
`unassigned_cell_ids: []` on every run (receipts/run_*.json, run_*.log,
execution_log.json).

## Comparison (task 5) — got vs want per run

Tolerance (frozen): PASS iff max|got-want| <= 1e-9*max|want| AND
||got-want||_F / ||want||_F <= 1e-9. Worst case across all runs/quantities:

| quantity | worst dev_max (any run) | worst Frobenius ratio | margin vs 1e-9 |
|---|---|---|---|
| center_of_mass | 5.33e-15 | 7.44e-16 | ~6 orders |
| inertia_tensor | 9.31e-10 abs (tensor scale 2.21e6) | 5.21e-16 | ~6 orders |
| mass_kg | 5.46e-12 | 4.20e-16 | machine precision |
| volume_m3 | 5.33e-15 | 4.10e-16 | machine precision |

COM per run (got vs want, m):

| run | motion | com_x got | com_x want | com_y got | com_y want | com_z got | com_z want | dev_max | verdict |
|---|---|---|---|---|---|---|---|---|---|
| run_A0_identity | identity | -5.25384615384616 | -5.25384615384615 | -7.15769230769231 | -7.15769230769231 | 1.03461538461538 | 1.03461538461538 | 2.66e-15 | pass |
| run_A1_translation | v + t | 7.74615384615384 | 7.74615384615385 | -14.1576923076923 | -14.1576923076923 | 5.53461538461538 | 5.53461538461538 | 3.55e-15 | pass |
| run_A2_rotation | R v | -0.771662888661389 | -0.771662888661386 | -8.89931188281311 | -8.89931188281311 | -0.335666460416595 | -0.335666460416597 | 5.33e-15 | pass |
| run_A3_rot_then_trans | R v + t | 12.2283371113386 | 12.2283371113386 | -15.8993118828131 | -15.8993118828131 | 4.1643335395834 | 4.1643335395834 | 3.55e-15 | pass |
| run_B1_translation_comoving | v + t | -5.25384615384616 | -5.25384615384615 | -7.1576923076923 | -7.15769230769231 | 1.03461538461538 | 1.03461538461538 | 3.55e-15 | pass |
| run_B2_rotation_comoving | R v | -5.25384615384616 | -5.25384615384615 | -7.1576923076923 | -7.15769230769231 | 1.03461538461538 | 1.03461538461538 | 4.44e-15 | pass |
| run_B3_rot_then_trans_comoving | R v + t | -5.25384615384615 | -5.25384615384615 | -7.15769230769231 | -7.15769230769231 | 1.03461538461538 | 1.03461538461538 | 4.44e-16 | pass |

All 9 tensor entries per run (got vs want, kg*m^2; dev = |got-want|):


### run_A0_identity — motion identity, authored frame R diag 1…, origin [0.0, 0.0, 0.0]

| entry | got (kg·m²) | want (kg·m²) | dev | pass |
|---|---|---|---|---|
| Ixx | 1366821.15385 | 1366821.15385 | 2.33e-10 | pass |
| Ixy | 447210.384615 | 447210.384615 | 1.16e-10 | pass |
| Ixz | -20364.2307692 | -20364.2307692 | 3.64e-12 | pass |
| Iyx | 447210.384615 | 447210.384615 | 1.16e-10 | pass |
| Iyy | 1069746.73077 | 1069746.73077 | 2.33e-10 | pass |
| Iyz | -3060.96153846 | -3060.96153846 | 6.82e-12 | pass |
| Izx | -20364.2307692 | -20364.2307692 | 3.64e-12 | pass |
| Izy | -3060.96153846 | -3060.96153846 | 6.82e-12 | pass |
| Izz | 2418279.03846 | 2418279.03846 | 0.00e+00 | pass |

mass: got 13000 want 13000 (dev 1.82e-12, pass) · volume: got 13 want 13 (dev 1.78e-15, pass)

### run_A1_translation — motion v + t, authored frame R diag 1…, origin [0.0, 0.0, 0.0]

| entry | got (kg·m²) | want (kg·m²) | dev | pass |
|---|---|---|---|---|
| Ixx | 1366821.15385 | 1366821.15385 | 2.33e-10 | pass |
| Ixy | 447210.384615 | 447210.384615 | 1.16e-10 | pass |
| Ixz | -20364.2307692 | -20364.2307692 | 3.64e-12 | pass |
| Iyx | 447210.384615 | 447210.384615 | 1.16e-10 | pass |
| Iyy | 1069746.73077 | 1069746.73077 | 2.33e-10 | pass |
| Iyz | -3060.96153846 | -3060.96153846 | 6.37e-12 | pass |
| Izx | -20364.2307692 | -20364.2307692 | 3.64e-12 | pass |
| Izy | -3060.96153846 | -3060.96153846 | 6.37e-12 | pass |
| Izz | 2418279.03846 | 2418279.03846 | 0.00e+00 | pass |

mass: got 13000 want 13000 (dev 1.82e-12, pass) · volume: got 13 want 13 (dev 1.78e-15, pass)

### run_A2_rotation — motion R v, authored frame R diag 1…, origin [0.0, 0.0, 0.0]

| entry | got (kg·m²) | want (kg·m²) | dev | pass |
|---|---|---|---|---|
| Ixx | 1056945.12557 | 1056945.12557 | 2.33e-10 | pass |
| Ixy | 255325.254229 | 255325.254229 | 4.66e-10 | pass |
| Ixz | 488689.794057 | 488689.794057 | 2.33e-10 | pass |
| Iyx | 255325.254229 | 255325.254229 | 5.24e-10 | pass |
| Iyy | 1590068.11484 | 1590068.11484 | 9.31e-10 | pass |
| Iyz | -258338.404324 | -258338.404324 | 8.73e-11 | pass |
| Izx | 488689.794057 | 488689.794057 | 4.07e-10 | pass |
| Izy | -258338.404324 | -258338.404324 | 5.82e-11 | pass |
| Izz | 2207833.68266 | 2207833.68266 | 9.31e-10 | pass |

mass: got 13000 want 13000 (dev 5.46e-12, pass) · volume: got 13 want 13 (dev 5.33e-15, pass)

### run_A3_rot_then_trans — motion R v + t, authored frame R diag 1…, origin [0.0, 0.0, 0.0]

| entry | got (kg·m²) | want (kg·m²) | dev | pass |
|---|---|---|---|---|
| Ixx | 1056945.12557 | 1056945.12557 | 2.33e-10 | pass |
| Ixy | 255325.254229 | 255325.254229 | 1.16e-10 | pass |
| Ixz | 488689.794057 | 488689.794057 | 2.33e-10 | pass |
| Iyx | 255325.254229 | 255325.254229 | 1.75e-10 | pass |
| Iyy | 1590068.11484 | 1590068.11484 | 9.31e-10 | pass |
| Iyz | -258338.404324 | -258338.404324 | 8.73e-11 | pass |
| Izx | 488689.794057 | 488689.794057 | 4.07e-10 | pass |
| Izy | -258338.404324 | -258338.404324 | 1.16e-10 | pass |
| Izz | 2207833.68266 | 2207833.68266 | 4.66e-10 | pass |

mass: got 13000 want 13000 (dev 1.82e-12, pass) · volume: got 13 want 13 (dev 1.78e-15, pass)

### run_B1_translation_comoving — motion v + t, authored frame R diag 1…, origin [13.0, -7.0, 4.5]

| entry | got (kg·m²) | want (kg·m²) | dev | pass |
|---|---|---|---|---|
| Ixx | 1366821.15385 | 1366821.15385 | 2.33e-10 | pass |
| Ixy | 447210.384615 | 447210.384615 | 1.16e-10 | pass |
| Ixz | -20364.2307692 | -20364.2307692 | 3.64e-12 | pass |
| Iyx | 447210.384615 | 447210.384615 | 1.16e-10 | pass |
| Iyy | 1069746.73077 | 1069746.73077 | 2.33e-10 | pass |
| Iyz | -3060.96153846 | -3060.96153846 | 6.37e-12 | pass |
| Izx | -20364.2307692 | -20364.2307692 | 3.64e-12 | pass |
| Izy | -3060.96153846 | -3060.96153846 | 6.37e-12 | pass |
| Izz | 2418279.03846 | 2418279.03846 | 0.00e+00 | pass |

mass: got 13000 want 13000 (dev 1.82e-12, pass) · volume: got 13 want 13 (dev 1.78e-15, pass)

### run_B2_rotation_comoving — motion R v, authored frame R diag 0.832196…, origin [0.0, 0.0, 0.0]

| entry | got (kg·m²) | want (kg·m²) | dev | pass |
|---|---|---|---|---|
| Ixx | 1366821.15385 | 1366821.15385 | 6.98e-10 | pass |
| Ixy | 447210.384615 | 447210.384615 | 5.82e-10 | pass |
| Ixz | -20364.2307692 | -20364.2307692 | 2.55e-11 | pass |
| Iyx | 447210.384615 | 447210.384615 | 5.82e-10 | pass |
| Iyy | 1069746.73077 | 1069746.73077 | 2.33e-10 | pass |
| Iyz | -3060.96153846 | -3060.96153846 | 7.96e-11 | pass |
| Izx | -20364.2307692 | -20364.2307692 | 2.55e-11 | pass |
| Izy | -3060.96153846 | -3060.96153846 | 7.96e-11 | pass |
| Izz | 2418279.03846 | 2418279.03846 | 9.31e-10 | pass |

mass: got 13000 want 13000 (dev 5.46e-12, pass) · volume: got 13 want 13 (dev 5.33e-15, pass)

### run_B3_rot_then_trans_comoving — motion R v + t, authored frame R diag 0.832196…, origin [13.0, -7.0, 4.5]

| entry | got (kg·m²) | want (kg·m²) | dev | pass |
|---|---|---|---|---|
| Ixx | 1366821.15385 | 1366821.15385 | 2.33e-10 | pass |
| Ixy | 447210.384615 | 447210.384615 | 5.82e-10 | pass |
| Ixz | -20364.2307692 | -20364.2307692 | 6.18e-11 | pass |
| Iyx | 447210.384615 | 447210.384615 | 5.82e-10 | pass |
| Iyy | 1069746.73077 | 1069746.73077 | 6.98e-10 | pass |
| Iyz | -3060.96153846 | -3060.96153846 | 1.38e-10 | pass |
| Izx | -20364.2307692 | -20364.2307692 | 6.18e-11 | pass |
| Izy | -3060.96153846 | -3060.96153846 | 1.38e-10 | pass |
| Izz | 2418279.03846 | 2418279.03846 | 4.66e-10 | pass |

mass: got 13000 want 13000 (dev 1.82e-12, pass) · volume: got 13 want 13 (dev 1.78e-15, pass)
## R*I*R^T verified exactly (task 5)

- run_A2/run_A3 inertia matches the frozen R*I0*R^T (fixed-basis law) to
  dev_max 9.31e-10 on a tensor of scale 2.21e6 -> relative 4.2e-16.
- run_B1/B2/B3 match run_A0's body-frame values (rotated-basis invariance) to
  dev_max 6.99e-10 — the co-moving authored frame pulls the moved body back to
  COM0 = (-5.253846153846154, -7.157692307692308, 1.0346153846153847) and I0
  unchanged.
- Exporter-internal float cross-check (independent of my expectations):
  com_A2 vs R@com_A0 dev 3.55e-15; I_A2 vs R@I0@R^T dev 1.16e-9 abs /
  5.55e-16 Frobenius (receipts/comparison.json `float_crosscheck`).
- Off-diagonal mixing confirmed: base off-diagonals (447210.38, -20364.23,
  -3060.96) map under R to (255325.25, 488689.79, -258338.40) — every one of
  the 9 entries moves to its analytic value; none is dropped or diagonalized
  (contract flags full_symmetric_tensor=true, off_diagonal_terms_preserved=
  true, principal_axis_transform_applied=false on every exported group;
  existing reader exits 0 on the receipts).
- Independent ground-truth check: whole-body Monte Carlo integration of the
  fixture (N=4e7/cell, seed 20040924; receipts/mc_crosscheck.txt) matches the
  exporter's A0 tensor to ~1e-5 relative (sampling noise) — the exported
  inertia is not merely self-consistent, it is physically correct.

## Falsifier fired (preserved reds)

The falsifier fired ONCE, in iteration 2, against MY expectation code — not
the exporter. First verdict attempt: diagonals matched to machine precision,
every off-diagonal off by exactly -15825 in every run. A whole-body Monte
Carlo (assumption-free) sided with the exporter; the defect was
work/compute_expectations.py::inertia_from_cov adding tr(C) to every entry
instead of tr(C)*delta_ij (sum of per-cell traces 7125 + 3480 + 5220 = 15825 —
exactly the constant). One-line fix, re-derivation, re-freeze (Amendment 2),
then the verdicted re-run. Reds preserved: receipts/iteration2_wrong_expectation/
(comparison_red.json + all run receipts) and receipts/mc_crosscheck.txt.
Iteration 1 (fixture-side compiler refusals non_manifold_vertex_link,
duplicate_vertex_position) preserved in receipts/iteration1_blocked/.
Full log: receipts/iterations.log.

## Receipts

- receipts/run_{A0_identity,A1_translation,A2_rotation,A3_rot_then_trans,
  B1_translation_comoving,B2_rotation_comoving,B3_rot_then_trans_comoving}.json
  (+ .log each): exporter stdout, exit code, command, input hashes
- receipts/execution_log.json, receipts/module_hashes.json (work/ copies
  byte-identical to tools/ originals)
- receipts/comparison.json (full verdict data incl. float_crosscheck)
- receipts/reader_summary_run_A3.json, receipts/reader_summary_run_B2.json
  (existing reader, exit 0; contract flags verified)
- receipts/iterations.log, receipts/mc_crosscheck.txt,
  receipts/iteration1_blocked/, receipts/iteration2_wrong_expectation/,
  receipts/fixture_hash_check_iteration3.txt, receipts/tables_fragment.md
- fixtures/ (21 documents + fixture_sha256.json), all schema-validated
- Frozen expectations: prereg_expectations.json sha256
  90102ec7919438f11733423cf053189fa0a355f91afc31bced2f82037e30bfeb

## Integrity check

```
$ git -C E:/ChimeraWork/mvc-20260924 status --porcelain -- tools Chimera/docs/matter
(empty — no output)
```

No file outside agents/M04_rigid/ was written. tools/ and Chimera/docs/matter/
remain READ-ONLY. Module copies in work/ verified byte-identical (sha256) to
their tools/ originals at run time.

## Stop

Stop rule satisfied: all 7 runs verdicted on all quantities -> STOP. Nothing
was tuned: tolerances, run matrix, motion, and fixture geometry are byte-fixed
since their respective freezes; the only post-freeze changes were the two
logged instrument repairs (fixture topology in Amendment 1, expectation
assembly in Amendment 2), each re-frozen before execution and each preserved
with its red state.
