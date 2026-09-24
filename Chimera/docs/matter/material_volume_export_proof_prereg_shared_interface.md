# Preregistration 1/2 — shared-interface coupon (SI)

**Status: preregistration artifact. Frozen and committed before the proof suite
executes.** Bounded export proof only: it establishes nothing about anatomical
correctness, mechanical qualification, or dynamics readiness. It proves, for
one authored two-body coupon with a shared internal interface, that exported
body mass properties equal independently derived analytic expectations and
that the internal face contributes no material.

Fixture source of truth: `tools/material_volume_export_proof_prereg_derivation.py`
(cross-checked hand rationals H, Hammer–Stroud quadrature Q, congruence route
R2; agreement within 1e-12 required or the script fails). Fixture documents,
validated byte-deep against those builders before freezing:

- `tools/material_volume_shared_interface_manifest_example.json`
- `tools/material_volume_shared_interface_partition_example.json`
- `tools/material_volume_shared_interface_groups_example.json`

## Fixture definition

Domain frame `si-domain`, right-handed, coordinates in m (`scale_to_m` 1.0).

| vertex | position (m) |
|---|---|
| v0 | (0, 0, 0) |
| v1 | (1, 0, 0) |
| v2 | (0, 1, 0) |
| v3 | (0, 0, 1) |
| v4 | (0, 0, −1) |

| cell | vertex ids (ordered) | region | owner | material | density | component |
|---|---|---|---|---|---|---|
| cell-upper | v0, v1, v2, v3 | si-region-A | si-owner-A | si-tissue-A | 12 kg/m³ | si-component-0 |
| cell-lower | v0, v2, v1, v4 | si-region-B | si-owner-B | si-tissue-B | 6 kg/m³ | si-component-0 |

Body groups (explicit authored grouping): `si-body-A` owns `cell-upper`,
`si-body-B` owns `cell-lower`. Both bodies are authored in frame `si-domain`
(identity transform), so exported values are domain-frame values and
recombination is frame-trivial. The two cells share exactly one triangular
face, {v0, v1, v2} in the plane z = 0: the **internal interface**. Mass
authority is `reconstructed_tissue_mass`; matter is owned only by
`tetrahedral_volume` representation; no surface overlay exists.

## Analytic expectations (frozen)

Exact rationals (decimals are the same values in binary floating point).
Uniform right tetrahedron raw moments used: with signed leg vector from the
right-angle corner, `COM = (Σ vertices)/4`,
`∫x_a x_b dm = (m/20)[Σ_i p_ia p_ib + S_a S_b]` with `S = Σ vertices`, and
about COM `I = tr(C)·E − C`, `C = raw_second − m·c·cᵀ`.

| quantity | si-body-A | si-body-B | combined (recombination target) |
|---|---|---|---|
| mass (kg) | 2 | 1 | 3 |
| volume (m³) | 1/6 | 1/6 | 1/3 |
| COM (m) | (1/4, 1/4, 1/4) | (1/4, 1/4, −1/4) | (1/4, 1/4, 1/12) |
| I_xx, I_yy, I_zz | 3/20 | 3/40 | 47/120, 47/120, 9/40 |
| I_xy | 1/40 | 1/80 | 3/80 |
| I_xz | 1/40 | −1/80 | 1/80 |
| I_yz | 1/40 | −1/80 | 1/80 |

(all inertia entries in kg·m² about each object's own COM; combined row =
parallel-axis recombination of the two body tensors about the combined COM.)

Frozen decimal literals (the comparison targets):

```
si-body-A:  mass 2.0
            com  [0.25, 0.25, 0.25]
            I    [[0.15, 0.025, 0.025], [0.025, 0.15, 0.025], [0.025, 0.025, 0.15]]
si-body-B:  mass 1.0
            com  [0.25, 0.25, -0.25]
            I    [[0.075, 0.0125, -0.0125], [0.0125, 0.075, -0.0125], [-0.0125, -0.0125, 0.075]]
combined:   mass 3.0
            com  [0.25, 0.25, 0.08333333333333333]
            I    [[0.39166666666666666, 0.0375, 0.0125],
                  [0.0375, 0.39166666666666666, 0.0125],
                  [0.0125, 0.0125, 0.225]]
interface:  exactly 1 internal face, face {v0, v1, v2}, area 0.5 m^2
```

## Independent oracle methods (for this coupon)

1. **H — hand rationals** above (exact `fractions.Fraction` derivation,
   independent of any shipped moment code).
2. **Q — Hammer–Stroud 4-point degree-3 tetrahedron quadrature** (barycentric
   points `(5±√5·3)/20`-family, irrational), integrated over the fixture
   vertices. Exact for all integrands here (degree ≤ 2).
3. **R2 — congruence transform** of H through authored frames (cross-check
   only; for this coupon the frames are identity).

The proof suite must implement Q in its own file in pure Python and compare
exporter output **and** Q against the frozen H values. The exporter's own
integration path (centroid-relative vertex moments) and the pre-existing
checks' raw-origin formula are deliberately *not* reused as oracles.

## Numerical tolerances (frozen)

- `TOL = 1e-12` absolute (relative tolerance 0) on every mass, COM, and
  inertia comparison. Rationale: expected round-off for these magnitudes
  (≤ 4) through the tested pipelines is ≲ 1e-15; the smallest falsifier-target
  effect is 1/80 = 0.0125, so TOL is ≥ 3 orders of magnitude below any
  effect under test and ≈ 3 orders above expected round-off.
- Interface area: absolute 1e-12 against 0.5 m².
- `T_PROTECTED = 0.002`: an off-diagonal inertia term counts as "protected"
  when `|expected| > T_PROTECTED`. The smallest protected term in this
  coupon's frozen tensors is 0.0125 (> 6× the threshold).
- Status strings, ownership lists, counts, and report flags: exact equality.

## Falsifiers (frozen)

| id | trigger | consequence |
|---|---|---|
| F1 | Any exported mass, COM, or inertia entry deviating from the frozen expectation by more than TOL; or the parallel-axis recombination of the two exported bodies deviating from the combined row by more than TOL | proof FAILS; observed values preserved in results |
| F2 | Duplicate interface contribution: face-adjacency oracles do not find exactly one shared face of area 0.5 ± 1e-12; or Σ body masses deviates from Σ ρᵢVᵢ = 3 kg by more than TOL (interface adds or removes mass); or the export report claims any surface-mass overlay or source payload consumption | proof FAILS |
| F4 | Lost off-diagonal term: any protected off-diagonal exported with wrong sign, magnitude ≤ 1e-9, or deviation > TOL; or report flags `off_diagonal_terms_preserved` not true / `principal_axis_transform_applied` not false / tensor not symmetric within TOL | proof FAILS |
| F5 | Oracle divergence: Q and H disagree by more than TOL anywhere in this coupon | proof FAILS; independence claim void |

Integration-level falsifiers F3 (frame transformation), F6 (determinism and
reader), F7 (silent schema extension) are preregistered in
`material_volume_export_proof_prereg_frame_composition.md` and the integrated
verification plan.

## Execution protocol (frozen)

1. This document and the fixture documents are committed in the landing
   revision **before** any proof suite runs; the proof suite file
   `tools/material_volume_shared_interface_proof.py` (package 1, sole owner)
   executes afterwards and may not edit fixtures, expectations, or tolerances.
2. Falsifiers fire on observed data. Fired falsifiers are **preserved**:
   results record observed values verbatim. Fixtures, expectations, and
   tolerances are never altered to obtain a pass. Implementation defects in
   the proof or export code may be corrected only with a logged diff and a
   re-run receipt; contract or architecture changes are escalated, never
   invented here.
3. Package 1 imports only the Python standard library and
   `material_volume_body_export`. It must not import the compiler, admission
   checks, export checks, or the other proof packages' code.
