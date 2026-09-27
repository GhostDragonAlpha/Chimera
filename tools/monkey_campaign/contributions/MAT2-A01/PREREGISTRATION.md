# MAT2-A01 PREREGISTRATION — reconciliation of the merged ulna volar-side orientation evidence

Frozen BEFORE any verification probe ran. Attempt `f59c82c7dba94fb5abb210fe818ef537`,
arrival `arrival-f0a6fc05faa548169c5afdd9fe332de4`, card MAT2-A01 (planning id A01),
criteria sha256 `3ffafb225eb06eb7dc958676d48c17bfcfd7f9d266c68b6e3a32d8b97920ff56`.
This file is committed alone, before the probe script or any receipt exists.

## Statement (what is claimed)

MAT2-A01 carries planning task **A01** — "Independent anatomical evidence determines
roll sign or records ambiguity" (`kind=measurement`, profile `anatomy`, `visible_static`,
`numerical_evidence_required`, `clean_view_required`). This attempt claims **no new
measurement**. It claims that the already-merged, lead-accepted ONT-A01 evidence record
satisfies the unchanged A01 clauses after scoped verification, per
`MATERIAL_PLAN_ADOPTION.md`: "Old evidence may satisfy unchanged clauses after checking
exact inputs, dependencies and validity; submit that reconciliation as the new card's
contribution instead of reimplementing known-good code."

## Clause-identity anchor (established from the registry, read-only, before this freeze)

- MAT2-A01 `ontology_qualification.definition_raw_sha256` = `57ded6eb2f2cc6aa914d6f68c8efb55b215790fc7a9d0baa5dfd2c49fd1465c1`
  == archived ONT-A01 `definition_raw_sha256` (scope archive `01ea5cdd…`, registry read-only).
- Canonical digest of the whole projected `ontology_qualification.task` object
  (done_when, observation, verification_profile with all 16 camera_required_fields,
  views, diagnostic_layers, falsifier, calculation contract list) is
  `5f121837b1c6a9a6b2405ba9320191810ca590b47118e4fbf1880b11f678dd83` for BOTH cards —
  a zero-line unified diff. Only the envelope changed: card id (ONT-A01 → MAT2-A01),
  scope sha (`01ea5cdd…` → `cb5475f8…`), depends_on (`ONT-P02` → `MAT2-P02`).

## Evidence under reconciliation (all on the merged line `origin/astra/gait-capture`)

1. `tools/monkey_campaign/contributions/ONT-A01/` — merged via PR #176
   (head `6f90c288ce93f236c820a2d665b0418c11d7024a`), present at merge-era tip
   `4aecbc9e` (PR #187) and at current merged tip `8ec90f13` (PR #196, MAT2-P02).
   Lead-accepted twice (#164 then #176); two independent worker PASS reviews at the
   exact head; outcome **AMBIGUITY_RECORDED** (done_when satisfied via its
   records-ambiguity arm) with the roll-sign values reproducing the pinned O1 record.
2. Forearm-package O1 ruling — integrated at `c3255f74`: ulna roll SIGN resolved
   (source volar +x ↔ target volar +z, azimuth law +90°, 180° flip refuted unanimously
   by ECU-P2/ANC-P2/TRIlat-P5).
3. A03 correspondence record — merged PR #187 @ `4aecbc9e`
   (`contributions/ONT-A03/`): staged radius supersession adopting the
   source-kinematic basis with O1's resolved roll (residual 0.1535°, selection-not-
   validation) and R1's refutation carried verbatim. (Planning-id A03 record; the
   dispatch context's "MAT2-A03" directory name does not exist in any merged tree —
   the merged record lives at `contributions/ONT-A03/`. Recorded, not silently renamed.)

## Frozen predictions, probes and falsifiers (executed in this order, nothing tuned)

Probe = `verify_reconciliation.py`, `python -B`, CPU-only, run inside this attempt
checkout against a TEMP replica extracted from THIS checkout's git objects; the play
checkout `E:/PythonChimera` is read-only and is not touched.

- **PR-1 byte-stability**: every file under `contributions/ONT-A01/` has an identical
  git blob sha256 at `4aecbc9e` and at `8ec90f13`.
  **F1** (any blob differs): the evidence changed since its merge → reconciliation
  claim dies; stop and report.
- **PR-2 suite re-execution**: `test_ota01_roll_sign.py` passes 26/26 in the fresh
  temp replica (`python -B`, CPU-only).
  **F2** (any test fails or count regresses): archived evidence no longer verifies →
  stop and report.
- **PR-3 numerical identity**: `evidence/numerical_receipt.json` at `8ec90f13` carries
  outcome `AMBIGUITY_RECORDED`; falsifiers F2 and F4 fired; P1 olecranon extreme
  x = -28.320999816060066 mm; P2 best station t=+6 mm with D = +3.2891597453041737 mm;
  P3 TRIlat-P5 no-flip error 0.15353092426937565 deg (all exactly as pinned in the
  merged REPORT/receipts).
  **F3** (any pinned value or outcome differs): done_when satisfaction reading was
  wrong → stop and report.
- **PR-4 manifest class**: `evidence/capture_manifest.json` envelope carries
  `task_id == "A01"`, `profile_id == "anatomy"`, schema
  `chimera.visual_capture_manifest.v1`; exactly 6 views = 3 declared view_ids x
  {diagnostic, clean} pairs; all 16 contract camera fields are locatable on every row
  in the canonical schema layout (camera block + samples for frame/position/
  orientation/target/distance/projection/span/planes/aspect/resolution/bookmarks;
  visibility block for layers/labels/occlusion; manifest tick_interval +
  samples[].tick for state/tick) — checked by structure walk, plus canonical
  `visual_capture.validate_manifest` and `visual_gate.verify` if importable in this
  checkout.
  **F4** (wrong task_id, missing field, or broken pair): the visible_static class is
  not delivered → stop and report.
- **PR-5 dependency**: MAT2-P02 (this card's only dependency) is DONE — registry
  winner merge commit `8ec90f13e76954596af3711c241c08b843ff78bf` == this candidate's
  base revision.
  **F5** (dependency not merged at this base): card is blocked → stop and report.
- **PR-6 probe has teeth (failing-first)**: flipping one byte of the replica's
  `numerical_receipt.json` (AMBIGUITY_RECORDED → TAMPERED) makes the PR-3 check FAIL
  on the tampered replica while the pristine replica passes.
  **F6** (tampered replica still passes): the probe is not a real comparison →
  discard the probe, do not substitute conclusions.

## Applicability boundary (recorded, never claimed past)

- This is records/bytes + CPU re-execution evidence for an anatomy evidence subject.
  No new visual capture is produced (the merged, review-accepted capture IS the
  visual evidence; PR-4 binds it to committed bytes). No runtime/native/GPU claim.
  No production mapping (ONT-A01 kept all touched membranes `binding: unresolved`,
  `physics: not_qualified`; A03 staged a mapping awaiting lead-merge approval
  semantics; nothing here executes or approves either).
- The merged record's own honesty items stay open exactly where they were: target
  palm sign UNRESOLVED pending the human A/B labeling verdict (A04 scope); 14
  phalanges not covered; ONT-A01's F2/F4 firing stands as recorded (frozen
  zone-shape over-strictness, both readings preserved). Reconciliation adds nothing
  to and subtracts nothing from those records.
- If any falsifier fires, this attempt stops and reports instead of repairing the
  evidence (repair belongs to a correction lane, not to a reconciliation card).
