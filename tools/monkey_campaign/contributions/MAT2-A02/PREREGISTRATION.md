# MAT2-A02 PREREGISTRATION — reconciliation of the merged U-STR / radius-consequence validation

Frozen BEFORE any verification probe ran. Attempt `ce71ec9ca3d74978bd62f99a5c0fcdfe`,
arrival `arrival-138570e4c25445f88c57b28d25e29d7a`, card MAT2-A02 (planning id A02),
criteria sha256 `c5d0e02ef376f01afcab78ee81e087f3b28dd9c7f29aef1bd0375c9ac2dd7bdf`,
scope sha256 `cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097`.
This file is committed alone, before the probe script or any receipt exists.

## Statement (what is claimed)

MAT2-A02 carries planning task **A02** — "Validate U-STR and proposed radius
consequence" (`kind=measurement`, profile `anatomy`, `visible_static`,
`numerical_evidence_required`, `clean_view_required`; calculation contracts C01/C16).
This attempt claims **no new measurement**. It claims that the already-merged,
lead-accepted ONT-A02 evidence record satisfies the unchanged A02 clauses after
scoped verification, per `MATERIAL_PLAN_ADOPTION.md`: "Old evidence may satisfy
unchanged clauses after checking exact inputs, dependencies and validity; submit
that reconciliation as the new card's contribution instead of reimplementing
known-good code."

**done_when (exact card clause)**

> Radioulnar definition, independent evidence, B4 result and before/after radius
> mapping are presented

## Clause-identity anchor (established from the registry, read-only, before this freeze)

- MAT2-A02 `ontology_qualification.definition_raw_sha256` = `57ded6eb2f2cc6aa914d6f68c8efb55b215790fc7a9d0baa5dfd2c49fd1465c1`
  == archived ONT-A02 `definition_raw_sha256` (scope archive `01ea5cdd…`, registry read-only).
- Canonical digest of the whole projected `ontology_qualification.task` object
  (done_when, observation "U-ANA rejected; U-STR provisional; radius supersession not
  authorized", kind, verification_profile with all 16 camera_required_fields, views,
  diagnostic_layers, falsifier, numerical_evidence_required, clean_view_required,
  calculation_ids C01/C16, catalog_refs CTRL-01/BIO-02/MAT-03/PROC-02) is
  `f804c9151fda7d3c47e3ac662bdeb8cf5b5f754f188c18b1d2df93be2a2f61eb` for BOTH cards —
  a zero-line task diff. Only the envelope changed: card id (ONT-A02 → MAT2-A02),
  scope sha (`01ea5cdd…` → `cb5475f8…`), depends_on (`ONT-A01` → `MAT2-A01`).
- Criteria pin honored: canonical `digest(spec)` of the live MAT2-A02 card recomputes
  to `c5d0e02e…` == registry `criteria_sha256` == this attempt's `criteria_sha256`.
- Convention cross-check: the same digest computation reproduces MAT2-A01's recorded
  projected-task digest `5f121837…` exactly for both A01 cards.

## Evidence under reconciliation (all on the merged line `origin/astra/gait-capture`)

1. `tools/monkey_campaign/contributions/ONT-A02/` — merged via PR #181
   (head `dadfda280d7c4abcc403b78f5c5b6ecd8332a402`, merge `970ffe1a34eb8a895956c6cb92ce66d01dc74961`),
   present at merge-era tip `4aecbc9ee98cb115ec9a690f5c0df173d9f3efbf` (PR #187,
   ONT-A03) and at current merged tip `6af853ad3be90e2f9564cb7f908fd4a202f9241c`
   (PR #211, MAT2-A01) == this candidate's base revision. Its own receipts:
   re-measurement **57/57 PASS** (`outcome = PRESENTED_AND_VERIFIED`), regression
   suite **106/106** (`test_ota02_radioulnar.py`), visual capture 6 rows
   (3 views × diagnostic/clean), canonical validator structurally valid.
2. ONT-A03 staged supersession — merged PR #187 @ `4aecbc9e`
   (`contributions/ONT-A03/`): adopts the section-4 radius consequence on the
   source-kinematic basis with O1's resolved roll, R1's refutation carried verbatim.
   Its approval act is a lead review/merge decision on that exact head — never
   executed here. The card observation "radius supersession not authorized" stands.
3. MAT2-A01 — merged PR #211 @ `6af853ad`: the ulna records-ambiguity arm
   (AMBIGUITY_RECORDED) intact, with the TRIlat-P5 no-flip residual
   `0.15353092426937565` deg appearing consistently in both the A01 and A02 records.

## Frozen predictions, probes and falsifiers (executed in this order, nothing tuned)

Probe = `verify_reconciliation.py`, `python -B`, CPU-only, offline, run inside this
attempt checkout against a TEMP replica extracted from THIS checkout's git objects;
the play checkout `E:/PythonChimera` is read-only and is not touched.

- **PR-1 byte-stability**: every file under `contributions/ONT-A02/` (35 files) has
  an identical git blob sha256 at `dadfda28` (PR #181 head), `970ffe1a` (PR #181
  merge), `4aecbc9e` (PR #187 merge era) and `6af853ad` (this base).
  **F1** (any blob differs): the evidence changed since its merge → reconciliation
  claim dies; stop and report.
- **PR-2 suite re-execution**: `test_ota02_radioulnar.py` exits 0 with final line
  `106/106 tests PASS` in a fresh temp replica extracted from `6af853ad`
  (`python -B`, CPU-only).
  **F2** (nonzero exit or count regression): archived evidence no longer verifies →
  stop and report.
- **PR-3 numerical identity**: `evidence/numerical_receipt.json` at `6af853ad`:
  `outcome == "PRESENTED_AND_VERIFIED"`; `task_id == "A02"`, `card_id == "ONT-A02"`,
  `schema == "chimera.ont_a02_numerical_receipt.v1"`; `summary == {pass 57, total 57,
  fail 0}`; all 57 check verdicts PASS; `preregistration_sha256 == c624401da34c14ed0b71bae33ec85825187d4a6d8e93cbb1acba78faacf4150b`;
  `state_snapshot_sha256 == 9e770ea52f8172e3b004df58ac2feb534a0cedfb106d82d775c008931eedcb58`;
  falsifier bookkeeping F1_identity `no identity mismatch`, F2_value `none`; and these
  exact `measured` values: N1.u2r_mm `23.07463997552291` mm; N1.r2h_mm
  `292.0293820833787`; N1.e2h_mm `305.79223569279844`; N1.axial_mm `14.323729312735956`;
  N1.lateral_mm `18.088103293382634`; N1.posterior_mm `0.3005126010484894`;
  N1.angle_deg `51.62861170617259`; N1.source_fraction_pct `7.545855414950395`;
  N2.radius.s_old `0.22170679566544982`; N2.radius.s_new `0.20418868001006546`;
  N2.radius.span_old_m `0.06474489854186721`; N2.radius.span_new_m `0.05962909405176015`;
  N2.radius.gap_m `0.005115804490107064`; N2.radius.det_new `0.008513242115903161`;
  N2.radius.G_unchanged `2.220446049250313e-16`; N2.radius.max_delta_m
  `0.004950983466166482` (worst site `BICshort-P6`, 16 sites/side);
  N2.radius_l.max_delta_m `0.004948423135921825` (worst site `BIClong_l-P9`);
  N2.scale_change_pct `-7.901478889180636`; N4.o1_ECU-P2 `63.61229795664599` deg;
  N4.o1_ANC-P2 `17.552772577400333` deg; N4.o1_TRIlat-P5 `0.15353092426937565` deg;
  N4.o1_unanimous true; N4.c1_10of10 true; N4.band_margin `3.0`;
  N3.gate_cells `10 PASS`; N3.t6 `{verdict PASS, banned_evidence_occurrences 0}`;
  N3.receipt_08_ok true; N3.coverage_ok true.
  **F3** (any pinned value or outcome differs): the done_when satisfaction reading
  was wrong → stop and report.
- **PR-4 manifest class (the `visible_static` class delivered, bound to committed
  bytes)**: `evidence/capture_manifest.json` envelope `task_id == "A02"`,
  `profile_id == "anatomy"`, `schema == "chimera.visual_capture_manifest.v1"`,
  `capture_sha256 == a728b16a6c0fb87170c3ce2dd6c1824bf7a9a353e4c304a5cf41966b5d4462fa`;
  exactly 6 rows = V1/V2/V3 × {diagnostic, clean}; diagnostic rows
  `occlusion_mode: mixed`, clean rows `depth_tested` with empty layers/label_ids;
  all 16 contract camera fields locatable on every row in the canonical schema
  layout; `capture_context.json` `task_id == "A02"`, `tick_interval == [0, 3]`;
  the committed `capture_sheet.png` bytes hash to `a728b16a…` == manifest ==
  context == the merged qualification receipt's `evidence.visual.raw_sha256`; the
  merged qualification receipt (`chimera.ont_a02_qualification.v1`, task_id A02,
  archived-era scope `01ea5cdd…` and criteria `ab47206c…`, `done_when_verified`,
  `profile_verified`) binds numerical `2aa382a15c0f005ef421fb0fa967b912486e03bdac2f75b9a50529d3ab90cce1`,
  source `60241502ebe8f7679f4dd42f69a498a547417aa0c2342cf7571940e53f121089`, camera
  `6a7957d3d4c9aa4d0493f2ad984768bce182232f77a7909067926f7a0e8c0f6d` — each equal to
  the actual replica file bytes. Canonical `visual_capture.validate_manifest` runs
  from the base revision's own bytes (blob `210a6ecc…`, byte-identical to the play
  checkout copy the lead pipeline imports): `structurally_valid: true`, 6 views;
  `visual_gate.verify` (play checkout module, read-only import) against
  replica-resolved absolute paths with THIS card's contract (task_id A02): returns
  `structurally_valid: true`, view_count 6.
  **F4** (wrong task_id, missing field, broken byte binding, or invalid manifest):
  the visible_static class is not delivered → stop and report.
- **PR-5 dependency + freeze chronology**: registry read-only: MAT2-A01 (this card's
  only dependency) `state == "DONE"`, winner `merge_commit_sha == 6af853ad3be90e2f9564cb7f908fd4a202f9241c`
  (PR #211) == this candidate's base, and the winner carries an
  `ontology_qualification` block (dependency admission requires it). The freeze
  commit is located by its frozen message, its parent == `6af853ad…`, it is an
  ancestor of HEAD, it touched ONLY this `PREREGISTRATION.md`, and HEAD carries the
  candidate contribution dir.
  **F5** (dependency not merged at this base, or chronology broken): card is
  blocked → stop and report.
- **PR-6 probe has teeth (failing-first)**: flipping one token of the replica's
  `numerical_receipt.json` (`PRESENTED_AND_VERIFIED` → `TAMPERED_RECORD`) makes the
  PR-3 check FAIL on the tampered replica while the pristine replica passes.
  **F6** (tampered replica still passes): the probe is not a real comparison →
  discard the probe, do not substitute conclusions.

## Applicability boundary (recorded, never claimed past)

- This is records/bytes + CPU re-execution evidence for an anatomy evidence subject.
  No new visual capture is produced (the merged, review-accepted capture IS the
  visual evidence; PR-4 binds it to committed bytes). No runtime/native/GPU claim,
  no network.
- Nothing is executed toward production: no radius supersession, no hand fit, no
  training-body change, no fit search, no moment-arm/utility computation. The
  ONT-A03 staged record stays exactly as staged (its approval act remains a lead
  decision); the old radius record and every failed alternative remain preserved.
- The merged record's own honesty items stay open exactly where they were: R1's
  refutation is retained and not relabeled (the B4 PASS is source-kinematic
  fidelity only); the A03 anatomical decision remains where I7's DR-B left it;
  the target palm sign question belongs to the A01/A04 lane. Reconciliation adds
  nothing to and subtracts nothing from those records.
- The replica suite reads two pinned external inputs from the read-only play
  checkout (`E:/PythonChimera/Saved/meshes/monkey_birth.bin`, 661076 bytes and
  `monkey_joints.bin`, 296589 bytes; hash-pinned `550a5b3e…` / `74b3ab04…` inside
  the receipt under test) and imports `visual_capture`/`visual_gate` support
  modules from the play checkout (read-only imports; `python -B` writes no
  bytecode). Disclosed here before the freeze.
- If any falsifier fires, this attempt stops and reports instead of repairing the
  evidence (repair belongs to a correction lane, not to a reconciliation card).
  Any probe-implementation defect is disclosed in the receipt's probe_corrections
  with the frozen expectations unchanged.
