# Preregistration — M02 multi-cell mixed-density coupon (M02-MC)

**Status: preregistration artifact. Frozen before the exporter runs on this
fixture.** Bounded export proof only: it establishes nothing about anatomical
correctness, mechanical qualification, or dynamics readiness. It proves, or
refutes, for one authored two-body coupon in which ONE body groups MULTIPLE
cells with DIFFERENT densities and DIFFERENT tetrahedron shapes at nontrivial
relative offsets, that the exporter's body-grouping math (per-cell integration,
cross-cell mass/COM/parallel-axis combination, full symmetric COM tensor,
authored-frame transform) equals independently derived exact expectations.

This is the case the frozen proofs at `1af0bbde` did NOT cover: in both prior
coupons (SI, FC) every body owned exactly one cell.

## Frozen artifacts (written before this run; sha256)

| artifact | sha256 |
|---|---|
| `fixtures/mc_manifest.json` | `0d23af2c524186bd044eb2d07e157076849f1acd8c7803857ba5ad156b58188b` |
| `fixtures/mc_partition.json` | `da942332f67791fb47ffe4b43c66c4d50380109d3cef9e153aab4eeaed383faa` |
| `fixtures/mc_groups.json` | `5dd87a5a8c5397b6caf8288d6652c6a2d7e59ec5059240ad943dec5c1bce7be9` |
| `derivation/derived_expectations.json` | `d8ed7a82b13c168b3bb1e58ba99688455754daf6acbf544125d3f305978feec0` |
| `derivation/derive_oracle.py` (fixture builder + oracle) | `633ac55c8a717b074e013d6be643801c6f456264ba697f10b77797c610947c6c` |
| `derivation/derivation_log.txt` (gate transcript) | `103aa53be3387626a122d83e526300512eb30fcc068700b1364ee59f6df1604d` |

Fixtures validated against the EXISTING shipped schemas (no schema edits):
`tools/material_volume_admission_schema.json` and
`tools/material_volume_body_export_schema.json` — 5/5 PASS (jsonschema 4.25.1,
receipt `receipts/validate_fixture.txt`).

## Fixture definition (source of truth: `derivation/derive_oracle.py`)

Domain frame `mc-domain`, right-handed, m, `scale_to_m` 1.0. The v1 contract
admits tetrahedral cells only, so "different shapes" = three geometrically
distinct tetrahedra: a right (tri-rectangular) tet, a regular tet, and a
scalene tet with six distinct edge lengths. Pairwise AABBs are strictly
disjoint (gated) — non-overlapping, not touching, offsets diagonal (no axis
stacking: cell-D sits at (+x,+y,+z) diagonal from cell-R; cell-S at (−x,+y,+z)).

| vertex | position (m) | | vertex | position (m) |
|---|---|---|---|---|
| r0 | (0, 0, 0) | | d2 | (3, 2, 4) |
| r1 | (1, 0, 0) | | d3 | (3, 4, 2) |
| r2 | (0, 1, 0) | | s0 | (−2, 3, 1) |
| r3 | (0, 0, 1) | | s1 | (1, 4, 1) |
| d0 | (5, 4, 4) | | s2 | (−2, 4, 3) |
| d1 | (5, 2, 2) | | s3 | (−1, 2, 4) |

| cell | ordered vertex ids | exact det | V (m³) | region | owner | material | rho (kg/m³) |
|---|---|---|---|---|---|---|---|
| cell-R | r0,r1,r2,r3 | +1 | 1/6 | mc-region-R | mc-owner-R | mc-tissue-R | 12 |
| cell-D | d0,d1,d2,d3 | +16 | 8/3 | mc-region-D | mc-owner-D | mc-tissue-D | 6 |
| cell-S | s0,s1,s2,s3 | +17 | 17/6 | mc-region-S | mc-owner-S | mc-tissue-S | 9 |

Mass authority `reconstructed_tissue_mass`; three `tetrahedral_volume` matter
claims (one per owner); three manifest components (`mc-component-R/D/S`,
one per cell — components are a manifest inventory concept, deliberately not
conflated with bodies).

Bodies (explicit authored grouping — the outstanding case: one body owns two
cells of different densities and shapes):

- `mc-body-1` owns `cell-R` + `cell-S` (mixed densities 12 and 9; right tet +
  scalene tet; separated by a diagonal offset of several metres).
- `mc-body-2` owns `cell-D` (regular tet, density 6). All cells assigned ⇒
  expected `export_status: complete`, `unassigned_cell_ids: []`.

Authored frames (both nontrivial: nonzero diagonal origins, proper rotations
with irrational entries that genuinely mix tensor components; contract
`x_domain = R·x_body + origin_m`):

```
mc-frame-1: R1 = Ry(90°)·Rz(30°) = [[0, 0, 1], [1/2, √3/2, 0], [−√3/2, 1/2, 0]],  t1 = (2, −1, 3)
mc-frame-2: R2 = Ry(60°)·Rz(90°) = [[0, −1/2, √3/2], [1, 0, 0], [0, √3/2, 1/2]],  t2 = (−1, 4, −2)
```

Fixture JSON carries `float(√3/2) = 0.8660254037844386`; exact orthonormality
and det = +1 were verified in exact Q(√3) arithmetic by the oracle (gates).

## Independent derivation method (H — the frozen expectation source)

`derivation/derive_oracle.py` uses ONLY the Python standard library
(`fractions`, `math`, `json`) and imports nothing from `tools/`:

- Exact `fractions.Fraction` arithmetic throughout the domain frame:
  per cell `V = det/6`, `m = ρV`, `c = Σx_i/4`,
  `Q_c = (m/20)·Σ_i (x_i−c)(x_i−c)ᵀ`, `I_c = tr(Q_c)·E − Q_c`
  (uniform-simplex barycentric moments `E[λ_i]=1/4`, `E[λ_iλ_j]=(1+δ_ij)/20`);
  bodies combined by `M = Σm`, `C = Σmc/M`,
  `I_C = Σ[I_c + m((d·d)E − ddᵀ)]`, `d = c − C`.
- Authored-frame expectations carried EXACTLY through Q(√3) pair algebra
  (every value is `a + b·√3` with rational a, b): `c_body = Rᵀ(C − t)`,
  `I_body = Rᵀ I R`; frozen decimals are `float(a) + float(b)·√3`.

## Cross-check oracles and pre-freeze gates (all passed; `derivation_log.txt`)

1. **Q — Hammer–Stroud 4-point degree-3 tetrahedron quadrature** (barycentric
   points `(5±3√5)/20`-family, irrational; weight 1/4 each), implemented in
   pure Python float64, applied to fixture **vertices mapped into the authored
   frame** — it never transforms a tensor, so its agreement with H is not
   shared algebra with the exporter's `RᵀIR` path.
2. **R2 — float congruence** of the H domain tensors (cross-check only; same
   algebra family as the exporter's transform, never primary evidence).
3. **Anchor** — H applied to the PUBLISHED two-body example coupon must
   reproduce the published literals in
   `tools/material_volume_body_export_example_report.json` (transcribed as
   frozen constants).

Observed pre-freeze: H vs Q/R2 max relative deviation 2.84e-14 (gate 1e-12);
anchor max abs deviation 2.78e-17 (gate 1e-12). Design gates passed: pairwise
AABB disjointness, positive exact dets, 12 distinct vertices, exact frame
orthonormality + det, `T_PROTECTED` margin (min |off-diagonal| of mc-body-1
authored tensor = 2.309917453013376 ≫ 0.002), mc-body-2 authored
off-diagonals exactly 0.0 (isotropic regular tet — tests that the exporter
does NOT invent cross terms).

**Pre-freeze corrections preserved (fired by the gates, fixed before any
exporter run; no exporter code involved):** (a) the AABB-disjointness gate
initially demanded separation on every axis instead of some axis — gate-code
logic fixed; (b) the `√3/2` constant was mis-authored as `1/2 + √3/2`; the
EXACT orthonormality/determinant gate fired, the constant was corrected to
`(0, 1/2)` in Q(√3) algebra, and all gates re-run green. These are
derivational defects of this agent's oracle, preserved here per the
preregistration protocol.

## Frozen expectations (H route; kg, m, kg·m²)

Per cell (domain frame, about each cell's own COM):

| quantity | cell-R | cell-D | cell-S |
|---|---|---|---|
| V (m³) | 1/6 = 0.16666666666666666 | 8/3 = 2.6666666666666665 | 17/6 = 2.8333333333333335 |
| mass (kg) | 2.0 | 16.0 | 25.5 |
| COM (m) | (0.25, 0.25, 0.25) | (4, 3, 3) | (−1, 3.25, 2.25) |
| I_xx | 0.15 | 6.4 | 12.1125 |
| I_yy | 0.15 | 6.4 | 16.25625 |
| I_zz | 0.15 | 6.4 | 11.15625 |
| I_xy | 0.025 | 0 | −1.275 |
| I_xz | 0.025 | 0 | 2.55 |
| I_yz | 0.025 | 0 | 2.86875 |

Bodies (the frozen comparison targets; full decimals in
`derivation/derived_expectations.json`, which is hash-frozen above):

```
mc-body-1 (cells R+S, frame mc-frame-1):
  mass = 27.5   volume = 3.0
  com_domain = (−0.9090909090909091, 3.0318181818181817, 2.1045454545454545)
  I_domain = [[36.37159090909091, 5.704545454545454, 7.211363636363636],
              [5.704545454545454, 26.72215909090909, −8.233522727272728],
              [7.211363636363636, −8.233522727272728, 30.894886363636363]]
  com_body   = (2.7913954752069747, 3.0439296961672597, −2.909090909090909)
  I_body     = [[36.982144389909266, 2.309917453013376, −3.3929513777455083],
                [2.309917453013376, 20.634901064636193, 8.545963098861229],
                [−3.3929513777455083, 8.545963098861229, 36.37159090909091]]
mc-body-2 (cell D, frame mc-frame-2):
  mass = 16.0   volume = 2.6666666666666665
  com_domain = (4, 3, 3)
  I_domain = 6.4·I₃ (off-diagonals exactly 0)
  com_body   = (−1.0, 1.8301270189221928, 6.830127018922193)
  I_body     = 6.4·I₃ (off-diagonals exactly 0 — rotation must NOT invent terms)
whole partition (independent target for the F6 recombination check):
  mass = 43.5   volume = 17/3 = 5.666666666666667
  COM = (0.896551724137931, 3.0201149425287355, 2.4339080459770117)
  I_about_COM = [[50.892385057471266, 7.2844827586206895, −37.25258620689655],
                 [7.2844827586206895, 284.99446839080457, −7.945330459770115],
                 [−37.25258620689655, −7.945330459770115, 281.06688218390804]]
```

Exact rational spot-anchors (hand-verifiable; verified in exact arithmetic):
body-1 `M = 55/2`, `C = (−10/11, 667/220, 463/220)`, `I_zz(domain) =
10875/352`, `C_z(body) = −32/11`, `I_body = [[52539/1760 + 14491/3520·√3,
14491/3520·√3 − 459/440, 251/88 − 3173/880·√3], …, …, [251/88 − 3173/880·√3,
3173/880·√3 + 251/88, 32007/880]]`; body-2 `I = (32/5)·I₃`; whole `M = 87/2`,
`C = (26/29, 1051/348, 847/348)`, `I_xx = 354211/6960`. Full exact values are
reproducible from `derive_oracle.py`.

## Tolerances (frozen before the run)

- `TOL(exp) = 1e-9 · max(1, |exp|)` on every mass, volume, COM entry, and
  every one of the 9 inertia entries (i.e. ≤ 1e-9 relative, 1e-9 absolute
  floor). Rationale (derived, not tasted): exported magnitudes ≤ ~37 per body;
  the float64 pipeline's expected round-off is ≤ ~1e-14 relative (observed
  oracle agreement 2.84e-14; prior frozen proofs observed ≤ 9.44e-16), and the
  frozen H decimals carry ≤ ~2 ulp conversion error. TOL is therefore ≥ 4
  orders of magnitude ABOVE the round-off budget and ≥ 6 orders BELOW the
  smallest protected effect (min protected off-diagonal 2.31; smallest
  structural scale = body-1 tensor diagonal spread ~16 kg·m²).
- `T_ZERO = 1e-9` absolute on mc-body-2's three must-stay-zero off-diagonals
  (an invented cross term must exceed it to escape F4).
- `T_PROTECTED = 0.002` (prior-prereg convention): an off-diagonal counts as
  protected when |expected| > T_PROTECTED — satisfied by ALL THREE mc-body-1
  authored off-diagonals (min 2.31), verified before freezing.
- Status strings, flags, frame ids, provenance rows, ownership lists, hashes:
  exact equality.
- Recombination check (F6) uses the same `TOL(exp)` rule against the frozen
  whole-partition row.

## Falsifiers (frozen)

| id | trigger | consequence |
|---|---|---|
| F1 | Any exported body mass or volume outside TOL vs frozen | defect finding; observed values preserved; proof FAILS |
| F2 | Any exported COM entry (3 per body) outside TOL | defect finding; proof FAILS |
| F3 | Any of the 9 inertia entries per body outside TOL; or tensor asymmetry > TOL; or flags `full_symmetric_tensor` / `off_diagonal_terms_preserved` / `principal_axis_transform_applied` not exactly true/true/false | defect finding; proof FAILS |
| F4 | Any protected off-diagonal with wrong sign or outside TOL; or any mc-body-2 off-diagonal with |value| > T_ZERO (invented cross term) | defect finding; proof FAILS |
| F5 | Oracle divergence (H vs Q/R2 > 1e-12, or anchor failure) | pre-freeze gate; run not started while red; independence claim void |
| F6 | Σ body masses ≠ 43.5 within TOL; or exported bodies mapped back to domain and parallel-axis recombined ≠ frozen whole-partition row within TOL; or `unassigned_cell_ids` ≠ []; or `export_status` ≠ `complete`; or `admission_status` ≠ `validation_only_admissible` | grouping loses/duplicates mass or cells; proof FAILS |
| F7 | Fixture fails validation against the EXISTING shipped schemas, or shipped schema/contract blocks construction of this fixture | decision request recorded; no fixture reinterpretation to force a pass |

## Stop rule (frozen)

Every quantity in the comparison scope receives a verdict (PASS/FAIL with
observed numbers). Any FAIL is PRESERVED with its numbers in `report.md`;
`tools/` and `docs/` are never modified by this agent. When all quantities are
verdicted (or F7 forces a decision request), the agent STOPS and reports. No
tolerance, expectation, or fixture is altered after this freeze.

## Run protocol (frozen)

1. Copy `tools/material_volume.py`, `tools/material_volume_admission.py`,
   `tools/material_volume_body_export.py` into `work/` (READ-ONLY originals
   untouched; `PYTHONDONTWRITEBYTECODE=1`).
2. Run the exporter CLI on the fixture; capture command, exit code, stdout
   bytes to `receipts/`. Run twice; bytes must be identical (determinism).
3. Run the shipped reader on the saved report as an additional receipt.
4. `compare.py` reads the frozen `derived_expectations.json` (hash-verified)
   and the observed report; emits the full verdict table into `report.md`.
