# B3 PREREGISTRATION — reader/exporter round-trip (frozen BEFORE execution)

Frozen: 2026-09-24, before any B3 fixture generation, run, or measurement.
File-timeline proof: receipts/00_prereg_freeze.txt records this file's sha256 and
mtime; every fixtures/, work/, and run artifact is created AFTER that receipt.
No B3 measurement or exploration of exporter/reader behavior was performed before
this freeze; the predictions below come from READING the frozen tools/ sources
(revision cbe611aa worktree) and the contract v0.9 — that reading is declared, and
if the reading is wrong the falsifiers catch it.

## THEORY (Rule 0 membrane)

STATEMENT: A genuine exporter report survives the reader's parse layer with every
field bit-exact (the writer and parser share one canonical serializer), but the
reader's SUMMARY layer is a projection that drops part of the contract §1
authoritative content on complete/exported reports — the same drop mechanism M09
banked for CON-4/6/7 diagnostics on blocked/refused reports, here hitting the
exported-body path.

PREDICTIONS (made before the run; each is falsifiable by the matrix):

- P1 (parse layer, both fixtures): `canonical_json(read_json_file(report_file))`
  equals the exporter's canonical output string exactly (same floats, same key
  order, LF); every invariant field present with exact-equal values. Parsed float64
  values compare equal with `==` because JSON repr round-trips float64 losslessly.
- P2 (summary layer): SURVIVE — the 9 tensor entries (exact), tensor/COM frame
  identifiers + unit + the three contract flags, COM value/unit/coordinate_frame,
  admission_status (top + per body), per-body admission_report_sha256,
  owned_cell_ids, top unassigned_cell_ids, and `dynamics_readiness_claimed: false`
  (pinned). DROP — `body_frame` (whole), `cell_provenance` (whole),
  `material_mass_source_provenance` (whole), `volume`, mass unit + frame_invariant
  (reduced to scalar `mass_kg`), top-level `admission_report_sha256`,
  `admission_reason_codes`, `all_supplied_cells_assigned`, `reason_codes`,
  `unassigned_cells` rows (this last one is M09's CON-7 banked finding — recorded
  as recurring, NOT claimed as new).
- P3 (fixture F1, body-R): the authored-frame tensor has ALL 9 entries nonzero —
  the generic rotation mixes the asymmetric tet's already-off-diagonal domain
  tensor; body-S (identity frame) keeps diagonal structure where the domain tensor
  has it. Off-diagonal summary values equal parsed values exactly.
- P4 (byte layer): piped subprocess stdout on Windows is CRLF (the B4 smudge
  layer); newline-normalized, it is byte-identical to the exporter's canonical
  string; the report file as written parses identically through read_json_file.
  Per B4's law, byte-layer verdicts use canonical_json — raw-byte EOL is recorded,
  never scored.
- P5 (reader output round-trip): the reader's own summary output re-parsed through
  `read_json_file` re-serializes to the identical canonical string.

## FALSIFIERS (named before the run; a fired falsifier is a preserved verdict)

- F-B3-1 (parse): any invariant field absent or value-differing between the
  exporter's canonical output and the parsed report, either fixture.
- F-B3-2 (summary): any invariant field absent (DROP) or differing (DIFF) in
  `summarize_export_report` output vs the parsed report, either fixture. P2
  predicts F-B3-2 FIRES on `cell_provenance` (contract line 28: "travels with the
  body; never summarized away"; CON-12: "stripping provenance voids the
  contract") and on `body_frame` (line 27). Prediction and falsifier are both
  frozen; if the run shows NO drop where P2 predicted one, that refutes P2 and is
  recorded. Firing is classified, never tuned away, and NOT fixed by B3 (tools/
  read-only; reader-improvement candidates go to the defect/change queue per the
  M09 U7 disposition precedent).
- F-B3-3 (readiness): any produced document (exporter report or reader summary,
  either fixture) carrying `dynamics_readiness_claimed != false`.
- F-B3-4 (canonical bytes): canonical_json of parsed output differing from the
  producing process's canonical string (parse instability), either stage.

## FIXTURES (>= 2; designs frozen now, realized by work/make_fixtures.py)

- F1 `rotcoupon` (authored by B3, inside agents/B3_roundtrip/fixtures/rotcoupon/):
  two single-tet bodies in one domain ("rotcoupon-domain", scale_to_m 1.0).
  tet-P vertices (0,0,0),(2,0,0),(0,1,0),(0,0,1) density 7.5, region-P/owner-P/
  tissue-P; tet-Q vertices (10,0,0),(12,0,0),(10,1,0),(10,0,1) density 3.25,
  region-Q/owner-Q/tissue-Q; uniform conditions, density_source
  "b3 rotated-frame coupon fixture". body-R owns cell-P with a GENERIC proper
  rotation R = Rz(37 deg) * Rx(23 deg) (trig-generated floats, orthonormal within
  the exporter's 1e-10 check) and origin (0.1,-0.2,0.3), frame "rotR-authored";
  body-S owns cell-Q, identity rotation, origin (10,0,0), frame "identS-authored".
  This is the required "nonzero off-diagonals via rotated authored frame" fixture.
- F2 `shipped_example`: byte-for-byte copies of the shipped
  tools/material_volume_body_export_{manifest,partition,groups}_example.json into
  fixtures/shipped_example/ (reuse law; copies live inside the B3 dir; source
  sha256 recorded for identity). Two bodies: coupon-A identity frame,
  coupon-B 90-degree z rotation, domain origin (3,-2,1) — exercises a second
  rotated frame class and the shipped off-diagonal entries (0.025).

## INVARIANT LIST x LAYERS (exact-equality tolerance on parsed values)

Sub-field rows (each scored PASS_EXACT / DROP / DIFF / N_A per fixture per layer):

- I1 tensor: value[3][3] all 9 entries (off-diagonals named individually), unit,
  full_symmetric_tensor, off_diagonal_terms_preserved,
  principal_axis_transform_applied.
- I2 COM: value[3], unit, coordinate_frame.
- I3 frames: body_frame.frame_id, .handedness, .coordinate_unit,
  .domain_from_body.rotation, .domain_from_body.origin_m; tensor .coordinate_frame,
  .frame_id, .basis; COM .coordinate_frame; mass/volume .coordinate_frame.
- I4 per-cell provenance: per row cell_id, mass_owner_id, region_id, material_id,
  density_kg_m3, density_source, density_conditions.
- I5 admission: top admission_status, top admission_report_sha256, per-body
  admission_status, per-body admission_report_sha256.
- I6 readiness: `dynamics_readiness_claimed` false in exporter report AND reader
  summary (and nothing in the summary reconstructs a claim).

Layers: L-WRITE (in-memory build_export_report vs exporter canonical string),
L-PARSE (read_json_file of the report file vs canonical string + invariant fields),
L-SUMMARY (summarize_export_report vs parsed report, invariant fields),
L-REREAD (reader summary re-parsed, canonical equality).

TOLERANCE: exact equality (==) on every parsed value, elementwise for arrays;
mismatches recorded with float.hex. No np.allclose anywhere in the verdict.

## SCOPE DECISIONS (declared, so the report cannot drift)

- B3 does NOT re-derive physics values (M02/M04/B6 lane); the preservation
  reference is the exporter's own emitted object/report — B3 tests transport
  fidelity, not integration correctness.
- B3 does NOT touch partial/blocked/refused reports (M09/B7/M06 lanes); fixtures
  are genuine exporter output, export_status "complete".
- B3 does NOT fix anything in tools/ even where a falsifier fires (exclusive
  ownership; reader-improvement candidates are queued findings).

## STOP RULE

Run once (deterministic, CPU-only); complete the full invariant x fixture x layer
matrix + byte-layer receipts + integrity paste; classify every non-PASS; write
report.md with the verdict; STOP. A second execution is allowed only as a
reproduction receipt and must not change any verdict.
