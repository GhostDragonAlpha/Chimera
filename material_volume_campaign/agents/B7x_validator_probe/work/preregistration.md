# B7x PREREGISTRATION — M10 static validator vs B7's nine MISSED mutations

Agent: B7x_validator_probe · 2026-09-24 · frozen BEFORE any validator run against any
mutant. Sources read first: `agents/B7_faultinjection/report.md` +
`work/mutation_matrix_frozen.json`; `agents/M10_validator/report.md` +
`PREREGISTRATION.md` (rules R0–R16, limits L1/L2) +
`rigid_body_mass_consumption_validator.py` (read, never modified).

## Rule-0 membrane

- **STATEMENT.** M10's static consumption validator closes a measurable, nameable
  subset of B7's consumption-time gaps: the structural/tamper classes (missing
  provenance object, `partial` status, readiness claim, inconsistent hash tamper)
  are REJECTED by rules R11/R2/R12/R4, while the wrong-but-well-formed value
  classes (symmetric tensor edit, positive mass, COM shift, density inconsistency,
  self-consistent impostor owner) remain ACCEPT — statically indistinguishable
  without reference documents — and are therefore the honest residual for the
  decision queue.
- **PREDICTION (not yet measured).** The per-row predictions below hold on B7's
  frozen corpus; the validator ACCEPTs B7's clean baseline; and the L2 probe
  (silently diagonalized tensor, flags intact) ACCEPTs exactly as M10 declared.
- **FALSIFIER (named before the run).**
  (a) any row predicted REJECT (M08, M10, M11, M12) that the validator ACCEPTs;
  (b) any row predicted ACCEPT/residual (M02, M04, M06, M07, M09, L2-probe) that
  the validator REJECTs — recorded as SURPRISE-DETECTED (honest reclassification,
  never tuned away);
  (c) an L2-probe REJECT falsifies M10's declared static-limit claim;
  (d) a baseline REJECT means my staging is broken — fix staging, never verdicts
  (logged, rerun only for infrastructure).

## Per-row predictions (derived from M10's frozen rule set, written before any run)

| ID | Mutation (B7 frozen matrix) | Predicted verdict | Predicted detector / rule | Closes B7 gap? |
|---|---|---|---|---|
| M02 | body-B inertia [0][0] 0.075…→0.076 (symmetric, flags intact) | ACCEPT (residual = L2 class) | none: R9 checks 9-entries/finite/exact-symmetry/flags/unit/frame/basis only; R0 reader symmetry-only; R4 hashes untouched and still root↔body consistent | N |
| M04 | body-A mass 2.0→2.5 | ACCEPT (residual) | none: R6 enforces finite, >0, kg, frame_invariant — no value oracle in R1–R16 | N |
| M06 | body-A COM x 0.25→0.75 | ACCEPT (residual) | none: R8 enforces 3 finite numbers, unit m, coordinate_frame==frame_id (frame unchanged) | N |
| M07 | density 12→13 in provenance rows, mass left 2.0 (inconsistent) | ACCEPT (residual) | none: R11 requires density_kg_m3 finite >0 only; no density·volume==mass cross-rule exists in R1–R16 | N |
| M08 | delete `material_mass_source_provenance` from exported body-A | REJECT | R11 `source_provenance_missing` (CON-12: stripping provenance voids the contract) | Y |
| M09 | mass_owner_id 'owner-A'→'owner-IMPOSTOR' in cell_provenance AND material_mass_source_provenance.mass_owner_ids (both, consistently) | ACCEPT (residual) | none: R11 enforces non-empty owner strings, cell↔provenance bijection, no conflicting duplicates, and set(mass_owner_ids)==set(provenance owners) — a consistent wholesale rename satisfies every one; no external ownership reference exists statically | N |
| M10 | root export_status complete→partial (unassigned_cell_ids empty) | REJECT | R2 `partial_rejected` (strictest D2: silent partial assembly FORBIDDEN). NB: closed by the strict status gate, NOT by B7's imagined consistency cross-check — R14's unassigned-consistency fires only on root-complete reports | Y |
| M11 | root dynamics_readiness_claimed false→true | REJECT | R12 `root_readiness_flag_not_false` (+ recursive claim scan); the validator reads the RAW report, so unlike the reader it cannot silently neutralize | Y |
| M12 | body-A admission_report_sha256 → 64 zeros (root and body-B unchanged) | REJECT | R4 `hash_binding_mismatch` (root↔body equality on complete reports = CON-13 tamper signal). Residual sub-case declared: a UNIFORM tamper (root+all bodies) or input_hashes tamper passes static form/consistency checks; needs the R4(d) supplied-document recomputation path = M10 LIMIT 1 | Y (as-frozen) |

## L2-limit cross-check probe

Fixture: body-B tensor off-diagonals zeroed, symmetry and all three flags kept
(M10's adversarial A5 shape). Predicted: **ACCEPT**, exactly as M10 declared
(PREREGISTRATION §A5, LIMIT 2). A REJECT here falsifies M10's declared limit.

## Verdict semantics for the deliverable

`closes-gap Y` iff the validator REJECTs a mutation B7's consumption-time reader
passed (exit 0). `N` iff the validator also ACCEPTs it — the gap remains open and
is carried to the residual list for the decision queue.

## Stop rule

All nine B7 missed mutations verdicted (exit code + full verdict JSON captured per
row) + baseline sanity ACCEPT + L2 probe run. One pass; reruns only for
infrastructure failure (logged in receipts/run_log.txt with cause). STOP when nine
verdicted — no extra mutations, no parameter exploration.
