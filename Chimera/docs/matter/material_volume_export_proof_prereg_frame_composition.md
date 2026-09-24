# Preregistration 2/2 — frame-composition coupon (FC)

**Status: preregistration artifact. Frozen and committed before the proof suite
executes.** Bounded export proof only: it establishes nothing about anatomical
correctness, mechanical qualification, or dynamics readiness. It proves, for
one authored two-body coupon, that exported mass properties expressed in
authored frames (including frames composed through a shared parent frame with
nonzero translations and nontrivial proper rotations) equal independently
derived analytic expectations with off-diagonal inertia terms intact.

Fixture source of truth: `tools/material_volume_export_proof_prereg_derivation.py`
(cross-checked hand rationals H, Hammer–Stroud quadrature Q, congruence route
R2; agreement within 1e-12 required or the script fails). Fixture documents,
validated byte-deep against those builders before freezing:

- `tools/material_volume_frame_composition_manifest_example.json`
- `tools/material_volume_frame_composition_partition_example.json`
- `tools/material_volume_frame_composition_groups_shared_example.json`
- `tools/material_volume_frame_composition_groups_composed_example.json`

## Fixture definition

Domain frame `fc-domain`, right-handed, coordinates in m (`scale_to_m` 1.0).

| vertex | position (m) |
|---|---|
| a0 | (0, 0, 0) |
| a1 | (1, 0, 0) |
| a2 | (0, 1, 0) |
| a3 | (0, 0, 1) |
| b0 | (2, −1, 0.5) |
| b1 | (2, 0, 0.5) |
| b2 | (2, −1, 1.5) |
| b3 | (3, −1, 0.5) |

| cell | vertex ids (ordered) | region | owner | material | density |
|---|---|---|---|---|---|
| fc-cell-A | a0, a1, a2, a3 | fc-region-A | fc-owner-A | fc-tissue-A | 12 kg/m³ |
| fc-cell-B | b0, b1, b2, b3 | fc-region-B | fc-owner-B | fc-tissue-B | 6 kg/m³ |

Body groups: `fc-body-A` owns `fc-cell-A`; `fc-body-B` owns `fc-cell-B`.
Grouping is an explicitly authored rigid-body modeling choice.

### Authored-frame chain (contract: `x_domain = R · x_body + origin_m`)

Parent frame `fc-parent-P` (nonzero translation, nontrivial proper rotation):

```
R_DP = [[ √3/2, -1/2, 0 ], [ 1/2, √3/2, 0 ], [ 0, 0, 1 ]]   (Rz +30 deg)
t_DP = (1, -2, 0.5)
```

Body-local frames composed through P (also nonzero translations and nontrivial
proper rotations):

```
R_PA = [[ 0, -1, 0 ], [ 1, 0, 0 ], [ 0, 0, 1 ]]   (Rz +90 deg)   t_PA = (0.5, 0, 0.25)
R_PB = [[ 0, 0, 1 ], [ 0, 1, 0 ], [ -1, 0, 0 ]]   (Ry +90 deg)   t_PB = (0, 0.75, -0.5)
```

Two runs of the same geometry and partition:

- **RUN-SHARED** (`..._groups_shared_example.json`): both bodies authored in
  the single shared parent frame `fc-parent-P`, i.e. `domain_from_body =
  (R_DP, t_DP)`. Results of both bodies are expressed in `fc-parent-P`.
- **RUN-COMPOSED** (`..._groups_composed_example.json`): each body authored in
  its own local frame, reached by composition through P. The schema v1 carries
  only the pre-composed single transform per body (see the architectural
  blocker below): `domain_from_body = (R_DP·R_PA, R_DP·t_PA + t_DP)` for A and
  `(R_DP·R_PB, R_DP·t_PB + t_DP)` for B. Frozen composed matrices:

```
R_DA = [[ -0.5, -0.8660254037844386, 0 ], [ 0.8660254037844386, -0.5, 0 ], [ 0, 0, 1 ]]
t_DA = [ 1.4330127018922192, -1.75, 0.75 ]
R_DB = [[ 0, -0.5, 0.8660254037844386 ], [ 0, 0.8660254037844386, 0.5 ], [ -1, 0, 0 ]]
t_DB = [ 0.625, -1.350480947161671, 0.0 ]
```

## Analytic expectations (frozen)

Domain-frame values (exact rationals; from the same uniform-right-tet raw
moment integrals as preregistration 1/2):

| quantity | fc-cell-A | fc-cell-B | combined |
|---|---|---|---|
| mass (kg) | 2 | 1 | 3 |
| COM (m) | (1/4, 1/4, 1/4) | (9/4, −3/4, 3/4) | (11/12, −1/12, 5/12) |
| I_xx, I_yy, I_zz | 3/20 | 3/40 | 127/120, 367/120, 427/120 |
| I_xy | 1/40 | 1/80 | 329/240 |
| I_xz | 1/40 | 1/80 | −151/240 |
| I_yz | 1/40 | 1/80 | 89/240 |

(Transparency note: a draft of the combined row double-counted the per-cell
tensors in 8 of 9 entries; the preregistration cross-check gate caught the
disagreement with the exact parallel-axis recombination **before** freezing,
and the table above is the corrected, cross-checked derivation.)

Frozen run expectations (decimals; route 1 = vertices transformed into the
target frame, then quadrature — never a tensor congruence):

```
RUN-SHARED  fc-body-A:  mass 2.0
            com  [0.4754809471616711, 2.323557158514987, -0.25]
            I    [[0.17165063509461018, 0.012500000000000178, 0.03415063509461097],
                  [0.012500000000000178, 0.12834936490538898, 0.009150635094610893],
                  [0.03415063509461097, 0.009150635094610893, 0.14999999999999908]]
RUN-SHARED  fc-body-B:  mass 1.0
            com  [1.7075317547305482, 0.45753175473054825, 0.25]
            I    [[0.0858253175473055, 0.006249999999999978, 0.017075317547305402],
                  [0.006249999999999978, 0.06417468245269468, 0.004575317547305488],
                  [0.017075317547305402, 0.004575317547305488, 0.07500000000000015]]
RUN-COMPOSED fc-body-A: mass 2.0
            com  [2.323557158514987, 0.02451905283832875, -0.5]
            I    [[0.128349364905389, -0.012499999999999997, 0.00915063509461067],
                  [-0.012499999999999997, 0.1716506350946101, -0.03415063509461097],
                  [0.00915063509461067, -0.03415063509461097, 0.1499999999999992]]
RUN-COMPOSED fc-body-B: mass 1.0
            com  [-0.75, -0.29246824526945175, 1.7075317547305482]
            I    [[0.07500000000000019, -0.004575317547305502, -0.017075317547305513],
                  [-0.004575317547305502, 0.06417468245269464, 0.006250000000000033],
                  [-0.017075317547305513, 0.006250000000000033, 0.0858253175473055]]
```

Cross-run consistency expectation: mapping both runs' outputs back to
`fc-domain` must recover the domain rows above (masses 2 and 1 exactly;
COM and tensors within TOL).

## Independent oracle methods (for this coupon)

1. **H — hand rationals** (exact `fractions.Fraction`), as above.
2. **Q — Hammer–Stroud 4-point degree-3 quadrature** over fixture vertices
   transformed into the target frame (`x_body = Rᵀ(x_domain − t)`),
   implemented independently in the proof file in pure Python.
3. **R2 — congruence route** (`c_body = Rᵀ(c − t)`, `I_body = Rᵀ I R`) applied
   to H. Direct-versus-composed comparison: route Q on the pre-composed
   matrices (direct) must equal route Q on the two-step chain
   domain → parent → body-local (composed).

The exporter's frame path (`RᵀIR`) and integration path are what these oracles
pin down. Because Q transforms **vertices** and never a tensor, agreement of Q
with the exporter's `RᵀIR` output is not shared algebra.

## Architectural blocker (frozen finding, no extension invented)

Schema `chimera.rigid_body_cell_groups.v1`
(`tools/material_volume_body_export_schema.json`) admits exactly one flat
`domain_from_body = {rotation, origin_m}` per body. It has **no** `parent_frame`
field, no frame-pose graph, and no deferred composition. Therefore:

- Two bodies under one authored parent frame **are** expressible when both are
  authored in that frame directly (RUN-SHARED) or when each body's frame is
  **pre-composed** at authoring time into one flat transform (RUN-COMPOSED).
- Declared, verifiable parent-frame **lineage** (e.g. `frame_id` plus
  `parent_frame_id` plus per-link poses, composed at load time) is **not**
  expressible in v1 and would require a schema change. That is the
  architectural blocker. Per instruction, the extension is **not invented**
  here; it is escalated to contract owners. The proof suite asserts the
  current schema's flatness so that any silent schema evolution re-fires F7.

## Numerical tolerances (frozen)

- `TOL = 1e-12` absolute (rtol 0) on every mass, COM, and inertia comparison
  (rationale as in preregistration 1/2: expected round-off ≲ 1e-15 for these
  magnitudes; effects under test are ≥ 4.5e-3).
- `T_PROTECTED = 0.002`: protected off-diagonal threshold. The smallest
  protected off-diagonal across this coupon's frozen tensors is
  0.004575317547305488 (design gate verified > T_PROTECTED before freezing).
- Status strings, frame ids, and report flags: exact equality.

## Falsifiers (frozen)

| id | trigger | consequence |
|---|---|---|
| F1 | Any exported mass deviating from frozen expectation by more than TOL (either run) | proof FAILS; observed values preserved |
| F3 | Incorrect COM/inertia transformation: any exported COM or inertia entry deviating from the frozen run expectations by more than TOL; or direct-versus-composed oracle disagreement above TOL; or cross-run domain recovery failing above TOL | proof FAILS |
| F4 | Lost off-diagonal term: any protected off-diagonal exported with wrong sign, magnitude ≤ 1e-9, or deviation > TOL; or report flags `off_diagonal_terms_preserved` not true / `principal_axis_transform_applied` not false / tensor asymmetry above TOL | proof FAILS |
| F5 | Oracle divergence: Q and H disagree by more than TOL anywhere in this coupon | proof FAILS; independence claim void |
| F7 | Silent schema extension: the groups schema advertises parent/composition fields while this preregistration's blocker note stands, without an escalated contract change | proof FAILS; escalation required |

Integration-level falsifier F6 (CLI determinism and reader refusal) belongs to
the integrated verification plan.

## Execution protocol (frozen)

1. This document and the four fixture documents are committed in the landing
   revision **before** any proof suite runs; the proof suite file
   `tools/material_volume_frame_composition_proof.py` (package 2, sole owner)
   executes afterwards and may not edit fixtures, expectations, or tolerances.
2. Falsifiers fire on observed data and failures are **preserved**: results
   record observed values verbatim. Fixtures, expectations, and tolerances are
   never altered to obtain a pass. Implementation defects in the proof or
   export code may be corrected only with a logged diff and a re-run receipt;
   contract or architecture changes are escalated, never invented here.
3. Package 2 imports only the Python standard library and
   `material_volume_body_export`. It must not import the compiler, admission
   checks, export checks, or the other proof packages' code.
