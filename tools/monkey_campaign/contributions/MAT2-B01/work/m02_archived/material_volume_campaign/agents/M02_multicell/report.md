# M02 — multi-cell mixed-density coupon: report

**Agent:** M02 (`M02_multicell`) · **Date:** 2026-09-24 · **Worktree:** `E:/ChimeraWork/mvc-20260924` @ `0c5cbbf0` (branch `material-volume-campaign-20260924`)
**Verdict: PASS — the exporter's body-grouping math survives the outstanding multi-cell, mixed-density, nontrivial-offset case. 142/142 checks PASS, 0 falsifier fired. All deviations ≤ 5.68e-14 against frozen tolerance ≥ 1e-9·max(1,|exp|).**

---

## 1. What was tested (the outstanding case)

The frozen proofs at `1af0bbde` (SI, FC coupons) exercised only bodies that own
exactly ONE cell. This coupon is the case they did not cover:

- **3 non-overlapping cells** (pairwise strictly disjoint AABBs — gated, not asserted),
  **3 different tetrahedron shapes** (the v1 contract admits tetrahedral cells only):
  right tet `cell-R` (V = 1/6 m³), regular tet `cell-D` (V = 8/3 m³, six equal edges 2√2),
  scalene tet `cell-S` (V = 17/6 m³, six distinct edge lengths √2·{√5,√11,√13,√17,√6,√10}/… — all distinct).
- **Nontrivial relative offsets, not axis-stacked**: `cell-D` at the (+x,+y,+z) diagonal
  (AABB [3,5]×[2,4]×[2,4]), `cell-S` at (−x,+y,+z) (AABB [−2,1]×[2,4]×[1,4]).
- **3 distinct densities**: 12, 6, 9 kg/m³ (separate regions/owners/materials).
- **2 authored bodies**: `mc-body-1` groups `cell-R` + `cell-S` (**one body, two cells,
  mixed densities, mixed shapes** — the grouping-math case), `mc-body-2` owns `cell-D`.
- **Authored frames with nontrivial proper rotations and nonzero diagonal origins**:
  `mc-frame-1` = Ry(90°)·Rz(30°), origin (2,−1,3); `mc-frame-2` = Ry(60°)·Rz(90°), origin (−1,4,−2).
- Regular tet `cell-D` has an exactly isotropic COM tensor (off-diagonals exactly 0):
  the rotation must NOT invent cross terms — a directional test the prior coupons' frames could not make.

Fixture files: `fixtures/mc_manifest.json`, `fixtures/mc_partition.json`, `fixtures/mc_groups.json`.
All three **validate against the EXISTING shipped schemas** (5/5 PASS, jsonschema 4.25.1,
`receipts/validate_fixture.txt`; no schema edits).

## 2. Preregistration — frozen BEFORE the run (acceptance 1)

Frozen artifacts and sha256 (also embedded in `PREREG.md`):

| artifact | mtime | sha256 |
|---|---|---|
| fixtures/mc_manifest.json | 13:38:14 | `0d23af2c…58188b` |
| fixtures/mc_partition.json | 13:38:14 | `da942332…383faa` |
| fixtures/mc_groups.json | 13:38:14 | `5dd87a5a…1bce7be9` |
| derivation/derived_expectations.json | 13:38:14 | `d8ed7a82…978feec0` |
| PREREG.md (freeze) | **13:43:11** | — |
| receipts/run1_report.json (first exporter contact with fixture) | **13:45:31** | — |

File-order timeline proves freeze-before-run: oracle gates green 13:38 → schema validation 13:40
→ **prereg frozen 13:43** → **first exporter run 13:45:31**. The exporter never saw the fixture
before the freeze.

**Independent expectations** (acceptance: derived, not exported): `derivation/derive_oracle.py`
is pure-stdlib, imports nothing from `tools/`, no numpy:
- **H (primary)** — exact `fractions.Fraction` simplex moments; authored-frame values carried
  EXACTLY through Q(√3) pair algebra (`a + b√3`, rational a,b); frozen decimals are
  `float(a)+float(b)·√3`. Documents mass per cell, total mass, COM, FULL inertia about COM
  incl. all off-diagonals.
- **Q (cross-check)** — 4-point Hammer–Stroud degree-3 quadrature (irrational barycentric
  points `(5±3√5)/20`-family), vertices mapped into the authored frame first; never transforms
  a tensor ⇒ no shared algebra with the exporter's `RᵀIR`.
- **R2 (cross-check only)** — float congruence of H domain tensors.
- **Anchor** — H reproduces the PUBLISHED literals of
  `tools/material_volume_body_export_example_report.json` to 2.78e-17.
- Pre-freeze gate results (log: `derivation/derivation_log.txt`): H vs Q/R2 max relative
  deviation **2.84e-14** (gate 1e-12); all design gates green (disjoint AABBs, positive exact
  dets +1/+16/+17, 12 distinct vertices, exact frame orthonormality + det +1, protected
  off-diagonal margin: min |off-diag| of mc-body-1 = **2.3099** ≫ T_PROTECTED = 0.002,
  mc-body-2 off-diagonals exactly 0).

**Frozen tolerances** (tight, derivation-based): `TOL(exp) = 1e-9·max(1,|exp|)` on every mass,
volume, COM entry and every one of the 9 tensor entries; `T_ZERO = 1e-9` absolute on the three
must-stay-zero off-diagonals; statuses/flags/provenance exact. Error budget: float64 round-off
≤ ~1e-14 relative (observed oracle agreement 2.84e-14), so TOL sits ≥ 4 orders above round-off
and ≥ 6 orders below the smallest protected effect. Full falsifiers F1–F7 and stop rule:
`PREREG.md`.

## 3. Run receipts (acceptance 3)

```
PYTHONDONTWRITEBYTECODE=1 python work/material_volume_body_export.py \
  --manifest fixtures/mc_manifest.json --partition fixtures/mc_partition.json \
  --groups fixtures/mc_groups.json
```

- RUN 1: exit **0**, 5955 bytes canonical JSON → `receipts/run1_report.json` (stderr empty)
- RUN 2 (determinism): exit **0**, `cmp` → **byte-identical** (`receipts/run_export.log`)
- Modules copied to `work/` byte-identical (sha256 verified against `tools/` originals);
  `tools/` and `docs/` untouched; no `__pycache__`/`.pyc` litter (checked).
- Shipped reader: `PYTHONDONTWRITEBYTECODE=1 python work/material_volume_body_export_reader.py
  receipts/run1_report.json` → exit **0**, parses cleanly, values identical
  (`receipts/reader_receipt.log`).
- Report headline: `export_status: complete`, `admission_status: validation_only_admissible`,
  `all_supplied_cells_assigned: true`, `unassigned_cell_ids: []`, `reason_codes: []`,
  `dynamics_readiness_claimed: false`.

## 4. Comparison — per-quantity verdicts (acceptance 4)

Headline numbers (full 142-row table appended below; machine-rendered from
`receipts/comparison.txt`):

| quantity | body | observed | expected (frozen H) | abs dev | verdict |
|---|---|---|---|---|---|
| mass (kg) | mc-body-1 | 27.5 | 27.5 | 0 | PASS |
| volume (m³) | mc-body-1 | 3.0 | 3.0 | 0 | PASS |
| COM x/y/z (m) | mc-body-1 | 2.7913954752069743 / 3.043929696167259 / −2.909090909090909 | 2.7913954752069747 / 3.0439296961672597 / −2.909090909090909 | 4.4e-16 / 8.9e-16 / 0 | PASS×3 |
| inertia I[0][0] (kg·m²) | mc-body-1 | 36.98214438990925 | 36.982144389909266 | 1.42e-14 | PASS |
| I[0][1], I[0][2], I[1][2] | mc-body-1 | 2.309917453013379, −3.3929513777455074, 8.545963098861229 | 2.309917453013376, −3.3929513777455083, 8.545963098861229 | 3.0e-15, 8.9e-16, 0 | PASS×3 |
| remaining 4 tensor entries | mc-body-1 | see table | see table | ≤ 8.9e-16 | PASS |
| mass (kg) | mc-body-2 | 16.0 | 16.0 | 0 | PASS |
| volume (m³) | mc-body-2 | 2.6666666666666665 | 2.6666666666666665 | 0 | PASS |
| COM x/y/z (m) | mc-body-2 | −1.0 / 1.8301270189221928 / 6.830127018922193 | identical | 0, 0, 0 | PASS×3 |
| all 9 tensor entries | mc-body-2 | diag 6.400000000000001, off-diag **0.0** | diag 6.4, off-diag 0.0 | ≤ 8.9e-16; off-diag 0 | PASS×9 |
| Σ body masses (F6) | both | 43.5 | 87/2 = 43.5 | 0 | PASS |
| recombined whole COM (F6) | both | (0.8965517241379307, 3.0201149425287355, 2.4339080459770113) | (26/29, 1051/348, 847/348) | ≤ 4.4e-16 | PASS×3 |
| recombined whole inertia 9 entries (F6) | both | see table | frozen exact rationals (e.g. I_xx = 354211/6960) | ≤ 5.68e-14 | PASS×9 |
| tensor flags | both | full_symmetric_tensor=true, off_diagonal_terms_preserved=true, principal_axis_transform_applied=false | exact | — | PASS×6 |
| statuses, provenance, hashes | root+bodies | — | exact | — | PASS (47) |

**All 9 tensor entries of both bodies verdicted; off-diagonals preserved with correct signs
(mc-body-1: 2.31, −3.39, 8.55 kg·m²) and nothing invented (mc-body-2: exactly 0.0).**
Worst deviation of the whole campaign check: **5.68e-14** (whole-partition recombination path),
4+ orders of magnitude inside tolerance.

## 5. Falsifier status (frozen in PREREG.md)

| id | trigger | status | evidence |
|---|---|---|---|
| F1 | mass/volume outside TOL | NOT FIRED | Δ = 0 on all four body quantities |
| F2 | COM entry outside TOL | NOT FIRED | max Δ = 8.9e-16 |
| F3 | tensor entry outside TOL / asymmetry / flags | NOT FIRED | max entry Δ = 1.42e-14; asymmetry 0; flags exact |
| F4 | lost/invented off-diagonals | NOT FIRED | protected off-diagonals correct sign+value (min 2.31, Δ ≤ 3.0e-15); mc-body-2 off-diagonals exactly 0.0 |
| F5 | oracle divergence | NOT FIRED (pre-freeze gate) | H==Q==R2 ≤ 2.84e-14 rel; anchor 2.78e-17 |
| F6 | grouping loses/duplicates mass or cells | NOT FIRED (after comparator corrections, §6) | Σ masses 43.5 exact; recombined whole row ≤ 5.68e-14; unassigned []; status complete |
| F7 | schema drift / contract blocks fixture | NOT FIRED | 5/5 schema validations PASS on shipped schemas |

## 6. Failures preserved and corrective actions (transparency)

**No exporter/compiler/admission defect was found.** Two comparator (my own test-harness)
defects fired F6 spuriously during comparison; both were preserved before correction, per the
frozen protocol. The exporter output was never edited; frozen expectations, fixtures, and
tolerances were never altered after the freeze.

- **C-M02-1** (13:48:28, `receipts/comparison_FAIL_C-M02-1_preserved.txt`): my recombination
  combined inertia tensors with the second-moment-matrix formula (`(tr−m|d|²)E + m·ddᵀ`).
  Diff: replaced with the inertia-tensor parallel-axis law `I + m((d·d)E − ddᵀ)` in
  `compare.py`. Classification: comparator defect — 9/9 mismatches isolated to the
  whole-row recombination while all 133 per-body checks passed.
- **C-M02-2** (13:50:36, `receipts/comparison_FAIL_C-M02-2_preserved.txt`): my domain
  back-transform computed `Rᵀ·I_body·R` (re-applying the forward transform) instead of the
  inverse `R·I_body·Rᵀ`. Diff: fixed indices in `compare.py`. Algebra verified standalone
  first: the corrected recombination applied to the FROZEN per-body values reproduces the
  frozen whole row to 5.68e-14 (pure round-off) before the observed report was re-compared.
- **Pre-freeze oracle corrections** (before any run, recorded in PREREG.md): (a) AABB gate
  demanded separation on every axis instead of some; (b) `√3/2` mis-authored as `1/2+√3/2` —
  caught by the EXACT orthonormality/determinant gate; both fixed and gates re-run green.

## 7. Integrity (acceptance 5)

```
$ git -C E:/ChimeraWork/mvc-20260924 status --porcelain -- tools Chimera/docs/matter
(empty — no output lines)
```

Worktree-wide `git status` shows only untracked campaign agent directories (all agents'
output areas; `material_volume_campaign/agents/M02_multicell/` is mine). No
`__pycache__`/`*.pyc` anywhere under `tools/` or the campaign dir.

## 8. Scope limits

Bounded export proof over one synthetic three-cell coupon. Establishes nothing about
anatomical correctness, mechanical qualification, assembly integration, dynamics readiness,
constitutive laws, or production wiring. All reports retain `dynamics_readiness_claimed:
false`, `physical_state_mutated: false`, `production_wired: false`,
`anatomical_completeness_certified: false`. Environment: CPU-only; Python 3.14.3;
numpy 2.2.6 (imported by the exporter itself); jsonschema 4.25.1.

## Appendix — full 142-check comparison table

Machine-rendered from `receipts/comparison.txt` (post-correction run, exit 0).
| check | verdict | observed | expected | abs dev | tol |
|---|---|---|---|---|---|
| root.schema_version | PASS | `'chimera.rigid_body_mass_export.v1'` | `'chimera.rigid_body_mass_export.v1'` | — | exact |
| root.export_status | PASS | `'complete'` | `'complete'` | — | exact |
| root.admission_status | PASS | `'validation_only_admissible'` | `'validation_only_admissible'` | — | exact |
| root.mass_authority | PASS | `'reconstructed_tissue_mass'` | `'reconstructed_tissue_mass'` | — | exact |
| root.validation_only | PASS | `True` | `True` | — | exact |
| root.dynamics_readiness_claimed | PASS | `False` | `False` | — | exact |
| root.physical_state_mutated | PASS | `False` | `False` | — | exact |
| root.production_wired | PASS | `False` | `False` | — | exact |
| root.anatomical_completeness_certified | PASS | `False` | `False` | — | exact |
| root.admission_anatomical_completeness_certified | PASS | `False` | `False` | — | exact |
| root.all_supplied_cells_assigned | PASS | `True` | `True` | — | exact |
| root.unassigned_cell_ids | PASS | `[]` | `[]` | — | exact |
| root.unassigned_cells | PASS | `[]` | `[]` | — | exact |
| root.surface_mass_overlay_generated | PASS | `False` | `False` | — | exact |
| root.source_effective_segment_payloads_consumed | PASS | `False` | `False` | — | exact |
| root.reason_codes | PASS | `[]` | `[]` | — | exact |
| root.input_hashes.algorithm | PASS | `'sha256'` | `'sha256'` | — | exact |
| root.input_hashes.manifest_sha256 | PASS | `'c6b0ab297f7feef98149066e399dd57a13b10727e0126cc36d46e3fdddafb65c'` | `'c6b0ab297f7feef98149066e399dd57a13b10727e0126cc36d46e3fdddafb65c'` | — | exact |
| root.input_hashes.partition_sha256 | PASS | `'a402b1f43738f4f2d47a8b4bb49a594fcdeb7546ce59d66beccf6985e83c758b'` | `'a402b1f43738f4f2d47a8b4bb49a594fcdeb7546ce59d66beccf6985e83c758b'` | — | exact |
| root.input_hashes.body_groups_sha256 | PASS | `'2d8158fcbeadc55c1a261ecd35bb063e82c132af728a5953f88a20d0c795e43f'` | `'2d8158fcbeadc55c1a261ecd35bb063e82c132af728a5953f88a20d0c795e43f'` | — | exact |
| mc-body-1.export_status | PASS | `'exported'` | `'exported'` | — | exact |
| mc-body-1.admission_status | PASS | `'validation_only_admissible'` | `'validation_only_admissible'` | — | exact |
| mc-body-1.owned_cell_ids | PASS | `['cell-R', 'cell-S']` | `['cell-R', 'cell-S']` | — | exact |
| mc-body-1.body_frame.frame_id | PASS | `'mc-frame-1'` | `'mc-frame-1'` | — | exact |
| mc-body-1.body_frame.rotation | PASS | `[[0.0, 0.0, 1.0], [0.5, 0.8660254037844386, 0.0], [-0.8660254037844386, 0.5, 0.0]]` | `[[0.0, 0.0, 1.0], [0.5, 0.8660254037844386, 0.0], [-0.8660254037844386, 0.5, 0.0]]` | — | exact |
| mc-body-1.body_frame.origin_m | PASS | `[2.0, -1.0, 3.0]` | `[2.0, -1.0, 3.0]` | — | exact |
| mc-body-1.mass.unit | PASS | `'kg'` | `'kg'` | — | exact |
| mc-body-1.mass.coordinate_frame | PASS | `'frame_invariant'` | `'frame_invariant'` | — | exact |
| mc-body-1.mass.frame_invariant | PASS | `True` | `True` | — | exact |
| mc-body-1.volume.unit | PASS | `'m^3'` | `'m^3'` | — | exact |
| mc-body-1.volume.frame_invariant | PASS | `True` | `True` | — | exact |
| mc-body-1.com.unit | PASS | `'m'` | `'m'` | — | exact |
| mc-body-1.com.coordinate_frame | PASS | `'mc-frame-1'` | `'mc-frame-1'` | — | exact |
| mc-body-1.inertia.unit | PASS | `'kg*m^2'` | `'kg*m^2'` | — | exact |
| mc-body-1.inertia.coordinate_frame | PASS | `'mc-frame-1'` | `'mc-frame-1'` | — | exact |
| mc-body-1.inertia.frame_id | PASS | `'mc-frame-1'` | `'mc-frame-1'` | — | exact |
| mc-body-1.inertia.basis | PASS | `'authored_body_frame'` | `'authored_body_frame'` | — | exact |
| mc-body-1.inertia.full_symmetric_tensor | PASS | `True` | `True` | — | exact |
| mc-body-1.inertia.off_diagonal_terms_preserved | PASS | `True` | `True` | — | exact |
| mc-body-1.inertia.principal_axis_transform_applied | PASS | `False` | `False` | — | exact |
| mc-body-1.mass | PASS | `27.5` | `27.5` | 0.000e+00 | 2.750e-08 |
| mc-body-1.volume | PASS | `3.0` | `3.0` | 0.000e+00 | 3.000e-09 |
| mc-body-1.com.x | PASS | `2.7913954752069743` | `2.7913954752069747` | 4.441e-16 | 2.791e-09 |
| mc-body-1.com.y | PASS | `3.043929696167259` | `3.0439296961672597` | 8.882e-16 | 3.044e-09 |
| mc-body-1.com.z | PASS | `-2.909090909090909` | `-2.909090909090909` | 0.000e+00 | 2.909e-09 |
| mc-body-1.inertia[0][0] | PASS | `36.98214438990925` | `36.982144389909266` | 1.421e-14 | 3.698e-08 |
| mc-body-1.inertia[0][1] | PASS | `2.309917453013379` | `2.309917453013376` | 2.665e-15 | 2.310e-09 |
| mc-body-1.inertia[0][2] | PASS | `-3.3929513777455074` | `-3.3929513777455083` | 8.882e-16 | 3.393e-09 |
| mc-body-1.inertia[1][0] | PASS | `2.309917453013379` | `2.309917453013376` | 2.665e-15 | 2.310e-09 |
| mc-body-1.inertia[1][1] | PASS | `20.63490106463619` | `20.634901064636193` | 3.553e-15 | 2.063e-08 |
| mc-body-1.inertia[1][2] | PASS | `8.545963098861229` | `8.545963098861229` | 0.000e+00 | 8.546e-09 |
| mc-body-1.inertia[2][0] | PASS | `-3.3929513777455074` | `-3.3929513777455083` | 8.882e-16 | 3.393e-09 |
| mc-body-1.inertia[2][1] | PASS | `8.545963098861229` | `8.545963098861229` | 0.000e+00 | 8.546e-09 |
| mc-body-1.inertia[2][2] | PASS | `36.37159090909091` | `36.37159090909091` | 0.000e+00 | 3.637e-08 |
| mc-body-1.symmetry[0][1] | PASS | `0.0` | `0.0` | 0.000e+00 | 1.000e-09 |
| mc-body-1.symmetry[0][2] | PASS | `0.0` | `0.0` | 0.000e+00 | 1.000e-09 |
| mc-body-1.symmetry[1][2] | PASS | `0.0` | `0.0` | 0.000e+00 | 1.000e-09 |
| mc-body-1.prov.mass_authority | PASS | `'reconstructed_tissue_mass'` | `'reconstructed_tissue_mass'` | — | exact |
| mc-body-1.prov.mass_source_kind | PASS | `'reconstructed_material_volume'` | `'reconstructed_material_volume'` | — | exact |
| mc-body-1.prov.integration_model | PASS | `'piecewise_constant_density_over_owned_tetrahedral_cells'` | `'piecewise_constant_density_over_owned_tetrahedral_cells'` | — | exact |
| mc-body-1.prov.mass_owner_ids | PASS | `['mc-owner-R', 'mc-owner-S']` | `['mc-owner-R', 'mc-owner-S']` | — | exact |
| mc-body-1.prov.overlay_consumed | PASS | `False` | `False` | — | exact |
| mc-body-1.prov.overlay_generated | PASS | `False` | `False` | — | exact |
| mc-body-1.prov.segments_consumed | PASS | `False` | `False` | — | exact |
| mc-body-1.cell_provenance.cell_ids | PASS | `['cell-R', 'cell-S']` | `['cell-R', 'cell-S']` | — | exact |
| mc-body-1.prov.cell-R.density | PASS | `12.0` | `12.0` | — | exact |
| mc-body-1.prov.cell-R.owner | PASS | `'mc-owner-R'` | `'mc-owner-R'` | — | exact |
| mc-body-1.prov.cell-R.region | PASS | `'mc-region-R'` | `'mc-region-R'` | — | exact |
| mc-body-1.prov.cell-R.material | PASS | `'mc-tissue-R'` | `'mc-tissue-R'` | — | exact |
| mc-body-1.prov.cell-R.density_source | PASS | `'mc analytic coupon fixture'` | `'mc analytic coupon fixture'` | — | exact |
| mc-body-1.prov.cell-R.conditions | PASS | `'uniform'` | `'uniform'` | — | exact |
| mc-body-1.prov.cell-S.density | PASS | `9.0` | `9.0` | — | exact |
| mc-body-1.prov.cell-S.owner | PASS | `'mc-owner-S'` | `'mc-owner-S'` | — | exact |
| mc-body-1.prov.cell-S.region | PASS | `'mc-region-S'` | `'mc-region-S'` | — | exact |
| mc-body-1.prov.cell-S.material | PASS | `'mc-tissue-S'` | `'mc-tissue-S'` | — | exact |
| mc-body-1.prov.cell-S.density_source | PASS | `'mc analytic coupon fixture'` | `'mc analytic coupon fixture'` | — | exact |
| mc-body-1.prov.cell-S.conditions | PASS | `'uniform'` | `'uniform'` | — | exact |
| mc-body-2.export_status | PASS | `'exported'` | `'exported'` | — | exact |
| mc-body-2.admission_status | PASS | `'validation_only_admissible'` | `'validation_only_admissible'` | — | exact |
| mc-body-2.owned_cell_ids | PASS | `['cell-D']` | `['cell-D']` | — | exact |
| mc-body-2.body_frame.frame_id | PASS | `'mc-frame-2'` | `'mc-frame-2'` | — | exact |
| mc-body-2.body_frame.rotation | PASS | `[[0.0, -0.5, 0.8660254037844386], [1.0, 0.0, 0.0], [0.0, 0.8660254037844386, 0.5]]` | `[[0.0, -0.5, 0.8660254037844386], [1.0, 0.0, 0.0], [0.0, 0.8660254037844386, 0.5]]` | — | exact |
| mc-body-2.body_frame.origin_m | PASS | `[-1.0, 4.0, -2.0]` | `[-1.0, 4.0, -2.0]` | — | exact |
| mc-body-2.mass.unit | PASS | `'kg'` | `'kg'` | — | exact |
| mc-body-2.mass.coordinate_frame | PASS | `'frame_invariant'` | `'frame_invariant'` | — | exact |
| mc-body-2.mass.frame_invariant | PASS | `True` | `True` | — | exact |
| mc-body-2.volume.unit | PASS | `'m^3'` | `'m^3'` | — | exact |
| mc-body-2.volume.frame_invariant | PASS | `True` | `True` | — | exact |
| mc-body-2.com.unit | PASS | `'m'` | `'m'` | — | exact |
| mc-body-2.com.coordinate_frame | PASS | `'mc-frame-2'` | `'mc-frame-2'` | — | exact |
| mc-body-2.inertia.unit | PASS | `'kg*m^2'` | `'kg*m^2'` | — | exact |
| mc-body-2.inertia.coordinate_frame | PASS | `'mc-frame-2'` | `'mc-frame-2'` | — | exact |
| mc-body-2.inertia.frame_id | PASS | `'mc-frame-2'` | `'mc-frame-2'` | — | exact |
| mc-body-2.inertia.basis | PASS | `'authored_body_frame'` | `'authored_body_frame'` | — | exact |
| mc-body-2.inertia.full_symmetric_tensor | PASS | `True` | `True` | — | exact |
| mc-body-2.inertia.off_diagonal_terms_preserved | PASS | `True` | `True` | — | exact |
| mc-body-2.inertia.principal_axis_transform_applied | PASS | `False` | `False` | — | exact |
| mc-body-2.mass | PASS | `16.0` | `16.0` | 0.000e+00 | 1.600e-08 |
| mc-body-2.volume | PASS | `2.6666666666666665` | `2.6666666666666665` | 0.000e+00 | 2.667e-09 |
| mc-body-2.com.x | PASS | `-1.0` | `-1.0` | 0.000e+00 | 1.000e-09 |
| mc-body-2.com.y | PASS | `1.8301270189221928` | `1.8301270189221928` | 0.000e+00 | 1.830e-09 |
| mc-body-2.com.z | PASS | `6.830127018922193` | `6.830127018922193` | 0.000e+00 | 6.830e-09 |
| mc-body-2.inertia[0][0] | PASS | `6.400000000000001` | `6.4` | 8.882e-16 | 6.400e-09 |
| mc-body-2.inertia[0][1] | PASS | `0.0` | `0.0` | 0.000e+00 | 1.000e-09 |
| mc-body-2.inertia[0][2] | PASS | `0.0` | `0.0` | 0.000e+00 | 1.000e-09 |
| mc-body-2.inertia[1][0] | PASS | `0.0` | `0.0` | 0.000e+00 | 1.000e-09 |
| mc-body-2.inertia[1][1] | PASS | `6.400000000000001` | `6.4` | 8.882e-16 | 6.400e-09 |
| mc-body-2.inertia[1][2] | PASS | `0.0` | `0.0` | 0.000e+00 | 1.000e-09 |
| mc-body-2.inertia[2][0] | PASS | `0.0` | `0.0` | 0.000e+00 | 1.000e-09 |
| mc-body-2.inertia[2][1] | PASS | `0.0` | `0.0` | 0.000e+00 | 1.000e-09 |
| mc-body-2.inertia[2][2] | PASS | `6.400000000000001` | `6.4` | 8.882e-16 | 6.400e-09 |
| mc-body-2.symmetry[0][1] | PASS | `0.0` | `0.0` | 0.000e+00 | 1.000e-09 |
| mc-body-2.symmetry[0][2] | PASS | `0.0` | `0.0` | 0.000e+00 | 1.000e-09 |
| mc-body-2.symmetry[1][2] | PASS | `0.0` | `0.0` | 0.000e+00 | 1.000e-09 |
| mc-body-2.prov.mass_authority | PASS | `'reconstructed_tissue_mass'` | `'reconstructed_tissue_mass'` | — | exact |
| mc-body-2.prov.mass_source_kind | PASS | `'reconstructed_material_volume'` | `'reconstructed_material_volume'` | — | exact |
| mc-body-2.prov.integration_model | PASS | `'piecewise_constant_density_over_owned_tetrahedral_cells'` | `'piecewise_constant_density_over_owned_tetrahedral_cells'` | — | exact |
| mc-body-2.prov.mass_owner_ids | PASS | `['mc-owner-D']` | `['mc-owner-D']` | — | exact |
| mc-body-2.prov.overlay_consumed | PASS | `False` | `False` | — | exact |
| mc-body-2.prov.overlay_generated | PASS | `False` | `False` | — | exact |
| mc-body-2.prov.segments_consumed | PASS | `False` | `False` | — | exact |
| mc-body-2.cell_provenance.cell_ids | PASS | `['cell-D']` | `['cell-D']` | — | exact |
| mc-body-2.prov.cell-D.density | PASS | `6.0` | `6.0` | — | exact |
| mc-body-2.prov.cell-D.owner | PASS | `'mc-owner-D'` | `'mc-owner-D'` | — | exact |
| mc-body-2.prov.cell-D.region | PASS | `'mc-region-D'` | `'mc-region-D'` | — | exact |
| mc-body-2.prov.cell-D.material | PASS | `'mc-tissue-D'` | `'mc-tissue-D'` | — | exact |
| mc-body-2.prov.cell-D.density_source | PASS | `'mc analytic coupon fixture'` | `'mc analytic coupon fixture'` | — | exact |
| mc-body-2.prov.cell-D.conditions | PASS | `'uniform'` | `'uniform'` | — | exact |
| whole.mass_from_bodies | PASS | `43.5` | `43.5` | 0.000e+00 | 4.350e-08 |
| whole.volume_from_bodies | PASS | `5.666666666666666` | `5.666666666666667` | 8.882e-16 | 5.667e-09 |
| whole.com.x_recombined | PASS | `0.8965517241379307` | `0.896551724137931` | 3.331e-16 | 1.000e-09 |
| whole.com.y_recombined | PASS | `3.0201149425287355` | `3.0201149425287355` | 0.000e+00 | 3.020e-09 |
| whole.com.z_recombined | PASS | `2.4339080459770113` | `2.4339080459770117` | 4.441e-16 | 2.434e-09 |
| whole.inertia[0][0]_recombined | PASS | `50.892385057471245` | `50.892385057471266` | 2.132e-14 | 5.089e-08 |
| whole.inertia[0][1]_recombined | PASS | `7.284482758620663` | `7.2844827586206895` | 2.665e-14 | 7.284e-09 |
| whole.inertia[0][2]_recombined | PASS | `-37.2525862068965` | `-37.25258620689655` | 4.974e-14 | 3.725e-08 |
| whole.inertia[1][0]_recombined | PASS | `7.284482758620663` | `7.2844827586206895` | 2.665e-14 | 7.284e-09 |
| whole.inertia[1][1]_recombined | PASS | `284.9944683908045` | `284.99446839080457` | 5.684e-14 | 2.850e-07 |
| whole.inertia[1][2]_recombined | PASS | `-7.945330459770121` | `-7.945330459770115` | 6.217e-15 | 7.945e-09 |
| whole.inertia[2][0]_recombined | PASS | `-37.2525862068965` | `-37.25258620689655` | 4.974e-14 | 3.725e-08 |
| whole.inertia[2][1]_recombined | PASS | `-7.945330459770117` | `-7.945330459770115` | 2.665e-15 | 7.945e-09 |
| whole.inertia[2][2]_recombined | PASS | `281.066882183908` | `281.06688218390804` | 5.684e-14 | 2.811e-07 |

---
End of report. Files: brief.md, PREREG.md (frozen prereg), report.md, fixtures/ (3 docs), derivation/ (oracle + expectations + log), work/ (module copies), receipts/ (all raw receipts), validate_fixture.py, compare.py.
