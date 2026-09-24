# Body-export proof results — shared-interface and frame-composition coupons

**Status: bounded export proofs.** These results establish, for two explicitly
authored synthetic coupons, that body grouping and authored-frame composition
preserve exported mass properties (mass, COM, full symmetric inertia about
COM). They do **not** establish anatomical correctness, mechanical
qualification, or dynamics readiness. `validation_only_admissible` remains an
input gate, not dynamics readiness.

## Execution record

| stage | artifact | result |
|---|---|---|
| Preregistration freeze (before any proof execution) | landing commit `d2c23741` | 2 preregistrations + 7 fixture documents + derivation script, cross-checked H == Q == R2 within 1e-12 |
| Package 1 — shared-interface coupon | `tools/material_volume_shared_interface_proof.py` | 5/5 OK |
| Package 2 — frame-composition coupon | `tools/material_volume_frame_composition_proof.py` | 8/8 OK |
| Package 3 — integrated verification | `tools/material_volume_export_proof_verify.py` | 7/7 OK (66 leaf tests) |
| Reproduction of reported suites from clean-room extraction of `d2c23741` | receipt R1 | 17 compiler + 21 admission + 8 export = all OK |
| Single full battery against the integrated revision | clean-room extraction of the integrated commit | recorded at handoff (composition: 17+21+8+5+8+7) |

Preregistration documents (frozen before execution):
`material_volume_export_proof_prereg_shared_interface.md`,
`material_volume_export_proof_prereg_frame_composition.md`. Derivation with
the three-way cross-check: `tools/material_volume_export_proof_prereg_derivation.py`.

**Subagent disclosure.** The three packages were specified for concurrent
subagent execution; this session exposes no subagent-deployment tool. They
were executed as three isolated work packages by one session instead, with
strict file ownership (exactly one suite file per package, no cross-imports)
and independent oracle implementations per package. The shared-assumption
audit below compensates partially; the residual single-author assumption is
disclosed there.

## Independent expected-versus-observed results

Expectations were frozen before execution (exact rationals / prereg decimals).
Observed values are exporter outputs; deltas are max absolute deviations.

| case | body | mass kg (observed) | Δmass | ΔCOM | Δinertia (max entry) |
|---|---|---|---|---|---|
| SI shared interface | si-body-A | 2.0000 | 0 | 0 | 2.78e-17 |
| SI shared interface | si-body-B | 1.0000 | 0 | 0 | 1.39e-17 |
| SI recombined | combined | 3.0000 | 0 | 0 | 5.55e-17 |
| FC shared parent frame | fc-body-A | 2.0000 | 0 | 1.11e-16 | 9.44e-16 |
| FC shared parent frame | fc-body-B | 1.0000 | 0 | 5.55e-17 | 1.67e-16 |
| FC composed body frames | fc-body-A | 2.0000 | 0 | 3.12e-17 | 8.88e-16 |
| FC composed body frames | fc-body-B | 1.0000 | 0 | 5.55e-17 | 1.80e-16 |

All deviations ≤ 9.44e-16, three orders of magnitude inside the frozen
tolerance TOL = 1e-12. Frozen expectations (rational/decimal tables) are in
the two preregistrations; recomputation by Hammer–Stroud quadrature agrees
with every frozen entry (F5 quiet).

SI recombination: the two exported body tensors, recombined by parallel axis
about the combined COM in the shared domain frame, equal the combined row
(m = 3 kg, COM = (1/4, 1/4, 1/12) m, I = [[47/120, 3/80, 1/80], [3/80,
47/120, 1/80], [1/80, 1/80, 9/40]] kg·m²) within TOL. FC cross-run recovery:
mapping both runs' outputs back to `fc-domain` recovers the frozen domain rows
for both bodies within TOL.

## Falsifier status (preregistered; none fired)

| id | trigger class | status | evidence |
|---|---|---|---|
| F1 | mass / recombination discrepancy | NOT FIRED | Δmass 0 everywhere; recombination within TOL |
| F2 | duplicate interface contribution | NOT FIRED | face-adjacency oracle finds exactly 1 shared face {v0,v1,v2}, area 0.5 m²; body masses are ρ·V each and sum to 3 kg exactly; no overlay/source flags set |
| F3 | incorrect COM/inertia transformation | NOT FIRED | direct == composed-chain == congruence within 9.44e-16; cross-run domain recovery within TOL |
| F4 | lost off-diagonal term | NOT FIRED | all protected off-diagonals (|·| > 0.002; smallest frozen 0.0045753) present with correct sign; symmetry, `off_diagonal_terms_preserved: true`, `principal_axis_transform_applied: false` |
| F5 | oracle divergence (Q vs H) | NOT FIRED | quadrature vs hand rationals agree ≤ 1e-12 everywhere (observed ≤ 9.44e-16) |
| F6 | CLI nondeterminism / reader refusal | NOT FIRED (after C-1) | two CLI runs byte-identical for all four fixture sets; saved example == canonical CLI bytes; reader accepts all reports |
| F7 | silent schema extension for parent composition | NOT FIRED | schema `bodyFrame`/`domain_from_body` flat (exact key sets asserted); smuggled `parent_frame` field refused with `bad_schema` and empty groups |

One derivational defect fired the **preregistration cross-check gate before
freezing** (FC combined inertia draft double-counted per-cell tensors in 8/9
entries); it was corrected and re-cross-checked before any fixture or
expectation was frozen. Recorded in preregistration 2/2.

## Corrective actions (logged; no fixture/expectation/tolerance changes)

| id | classification | defect | correction | re-run receipt |
|---|---|---|---|---|
| C-0 | pre-freeze derivation defect | FC combined inertia hand table double-count | corrected table, three-way cross-check green before freeze | preregistration script exit 0 |
| C-1 | lane artifact defect (found by R1 reproduction) | saved example report was pretty-printed, not canonical CLI bytes (content identical, verified json-equal) | regenerated artifact with canonical CLI serialization; JSON content unchanged | runs byte-identical AND equal to saved bytes; reader OK |
| C-2 | proof-code defect | SI comparator label mismatch (`KeyError: 'mass_kg'`) | aligned oracle output labels | 5/5 OK |
| C-3 | audit-code defect | audit allowlist omitted `__future__` import | allowlisted (compile directive, not shared code) | 7/7 OK |

Fixtures, frozen expectations, and tolerances were **not** altered after
freezing. Failures above were preserved as observed until classified.

## Receipts

- **R1 reproduction (clean-room `git archive d2c23741`)**: `Ran 17 tests OK`,
  `Ran 21 tests OK`, `Ran 8 tests OK`; CLI two runs byte-identical; saved
  artifact byte-compare failed → C-1 → content-equal confirmed → corrected →
  byte-equal; reader: `complete`, `dynamics_readiness_claimed: false`.
- **R2 package 1**: `Ran 5 tests OK` (after C-2).
- **R3 package 2**: `Ran 8 tests OK`.
- **R4 package 3 (pre-integration)**: `Ran 7 tests OK` (after C-3); leaf
  suites 17+21+8+5+8 = 59 plus 7 verification tests.
- **R5 integrated full battery**: `python tools/material_volume_export_proof_verify.py`
  once, from a clean-room extraction of the integrated revision; output
  recorded at handoff.

## Shared-assumption audit (could exporter and oracle agree incorrectly?)

Executable audit (in `material_volume_export_proof_verify.py`):

1. **Import graph**: each proof file imports only the standard library and
   `material_volume_body_export` (the component under test). Oracle blocks
   contain no `exporter.`, `numpy`, or legacy oracle references
   (`tet_integrals`, `combine_oracle`, `oracle_simplex_moments`); neither
   proof imports the other, the compiler, admission, or the existing checks.
2. **File-local quadrature**: both proofs carry their own Hammer–Stroud
   point construction (asserted textually); no oracle module is shared.
3. **Perturbation tracking**: perturbing a fixture density in memory moves
   exporter output to the independently recomputed quadrature value (13/6 kg),
   so agreement with frozen literals is not coincidental constants.

Formula-family analysis (documented finding):

- The exporter's integration (`_integrate_cells`, centroid-relative vertex
  moments `(m/20)·Σ local`) and the existing export checks' raw-origin formula
  (`(V/20)[xᵀx + SSᵀ]`) are algebraically the same moment family. Agreement
  between them is therefore **not** independent evidence, and the coupons do
  not rely on it.
- The coupons instead anchor on: (i) exact hand rationals frozen before
  execution; (ii) Hammer–Stroud degree-3 quadrature with irrational barycentric
  points (different mathematics, exact for the degree-≤2 integrands); (iii) a
  congruence cross-check. Oracle Q transforms **vertices**, never a tensor, so
  its agreement with the exporter's `RᵀIR` transform is not shared algebra.

Residual shared assumptions (disclosed, not eliminated):

- All code and both oracles were authored by one session (no independent
  agent was available; see disclosure above).
- All arithmetic is IEEE-754 binary64; tolerances are sized accordingly.
- Fixture transcription risk was eliminated at freeze time by byte-deep
  validation of the seven fixture documents against the derivation builders.

## Architectural blocker: declared parent-frame composition

Schema `chimera.rigid_body_cell_groups.v1` carries exactly one flat
`domain_from_body = {rotation, origin_m}` per body. Numeric composition
through a parent frame is expressible only as an authoring-time **pre-composed**
transform (demonstrated: RUN-COMPOSED equals the two-step chain to within
9.44e-16), and two bodies under one parent frame are expressible when both
are authored in that frame (demonstrated: RUN-SHARED). **Declared, verifiable
frame lineage** (`parent_frame` references with per-link poses composed at
load time) is not expressible in v1 and would require a schema change. That
extension was **not invented** here; it is escalated to the contract owners.
F7 asserts the current flatness so any silent schema evolution re-fires.

## Scope limits

Grouping is an explicitly authored rigid-body modeling choice, never inferred
from stiffness, materials, or anatomy. These are bounded export proofs over
synthetic two-cell coupons: no anatomical correctness, mechanical
qualification, assembly integration, dynamics readiness, constitutive law, or
production wiring is established or claimed. All reports retain
`dynamics_readiness_claimed: false`, `physical_state_mutated: false`,
`production_wired: false`, `anatomical_completeness_certified: false`.
