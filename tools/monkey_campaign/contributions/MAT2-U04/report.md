# MAT2-U04 — candidate report: input settings, motion qualification

Card `MAT2-U04` (planning U04, profile `controls`, kind **motion**), attempt
`d9ce4334674e435d95b9cb95373327e5`, agent `arrival-1390bce44d204c709636097a9613e84f`,
criteria `192ca43f061c4b6b2763d11213e0246ea075c3f62e6948948ba8c64213bf5180`.

Done-when (verbatim): "Sensitivity, inversion and bindings needed for the
selected controls work and persist."

## What this candidate is

The **motion complement** the lead's ONT-U04 correction demanded
(msg-b5edae96, ONT-X02 precedent), delivered over the ALREADY-IMPLEMENTED
pinned product modules — plus the preserved records leg reused exactly as the
lead directed:

1. **Subject, pinned and cited.** `input_settings.py`
   (`8d1a49d6…`) at the monkey-play lineage integration tip: byte-identical at
   integration commit `4699b37d`, at the old pin `9afbddcd`, and at the pinned
   head `f30f2224663324e9374b076938c56672febf4082` (branch
   `monkey-play-20260924` tip) — re-verified this attempt by read-only
   `git show` from `E:/ChimeraWork/monkey-play-20260924`, together with
   `input_mapper.py` (`7a36a45e…`), `command_record.py` (`67711759…`) and the
   pinned battery `input_settings_tests.py` (`5845178a…`). All recovered
   byte-exact into `reference/`; hashes asserted at probe import.

2. **Records leg, reused + freshly re-run.** The reviewed PR #182 head
   (`939e8e6f…`, fetched from the origin remote) is snapshotted verbatim under
   `records_leg/ONT-U04/` (14 files); its unmodified `run_falsifiers.py` was
   re-run at this scope: **GREEN, 33 PASS / 0 FAIL**, internal hash proof
   `candidate == reference == ledger`, 3.5 s of the 120 s bound
   (`evidence/records_leg_rerun.{txt,json}`).

3. **Motion leg, new work (the actual through-the-interface runs).**
   `input_settings_probe.py` drives the frozen timeline through the subject's
   OWN public surface (`load_settings`, `save_settings`, `apply_settings`,
   `configured_mapper`, `InputSettings`) with injected milliseconds, and a
   REAL separate OS process (`child_load_probe.py`, spawned `python -B`)
   re-loads the saved settings and replays the frozen sequence:

   - **Sensitivity works** — 265 mouse boundaries bit-exact vs the mapper's
     own law; 4x setting => exactly 4x yaw (ratio 4.0); the derived ceiling
     0.08 (= OMEGA*INTERVAL_MS/1000) saturates at EXACTLY `OMEGA_MAX_RAD_S`
     (the seam's clamp, never bypassed). N2.
   - **Inversion works** — 100 inverted boundaries bit-exact vs the signed
     law; the same +5 counts flip from exactly `+OMEGA` to exactly `-OMEGA`;
     the turn-key path is UNAFFECTED (A gives +OMEGA even inverted; the
     cancel window sums to exactly 0.0). N3/N4.
   - **Bindings work** — the A/D remap flips the emitted key signs exactly
     (A: +OMEGA -> -OMEGA; D: -OMEGA -> +OMEGA); `E->sprint` binds legally and
     refuses BY NAME at runtime; a coverage-negative file refuses
     `action_unbound`. N5.
   - **Everything PERSISTS** — save is canonical and atomic (file bytes ==
     `canonical_bytes`, resave byte-identical, no temp residue); the parent
     reload is status `loaded` with structural equality; the CHILD PROCESS
     (fresh interpreter, pid recorded) loads the same file and its replay
     records are FIELD-EXACT vs the parent's reloaded mapper (10/10);
     in-session behavior continues unchanged across the save/reload boundary.
     N6.
   - Plus: first-run defaults with nothing created (N1), nine poison classes
     refusing BY NAME with defaults and load never writing (N7), seam
     constants/bytes unchanged (N8), 368 records conforming to
     provenance/band/timing laws (N9). **All ten frozen checks GREEN**;
     trace `9aea974e…` (391 rows) byte-identical across runs
     (`evidence/numerical_receipt.json`, `evidence/trace.jsonl`).

4. **Camera manifest + runtime evidence.** `evidence/capture.mp4`
   (640x360, 2346 frames @20 fps, 117.3 s): three profile views x
   diagnostic+clean segments; built twice, byte-identical (bitexact ffmpeg
   flags). `evidence/capture_manifest.json` is `chimera.visual_capture_manifest.v1`
   with the identity envelope **task_id `U04` (the contract task id — not the
   card id)**, subject `8d1a49d6…`, capture sha bound to the committed video
   bytes, tick_interval [0,390], three diagnostic+clean pairs, trace-bound
   (`state_binding` = trace sha), all 16 profile camera fields. Validated
   in-process with the campaign's own `visual_capture.validate_manifest` AND
   `visual_gate.verify` against `card_task.json` — structurally_valid true
   (`evidence/capture_receipt.json`). `evidence/runtime_receipt.json` records
   the run identity, the child-process spawn, and the injected-timing chain.

5. **Failing-first falsifiers — all six FIRED** (`evidence/falsifier_demos.log`,
   `evidence/selftest_receipt.json`): PIN-DRIFT aborts at import;
   SENS-LAW-BREAK fires N2; INVERT-BREAK fires N3; PERSIST-BREAK fires N6;
   GATE-NEGATIVE (tampered manifest sample) refused
   `camera_target_distance_mismatch`; BATTERY-NEGATIVE (corrupted scratch
   copy) aborts the battery hash proof.

6. **Unit tests: 17/17 OK** (`python -B -m unittest test_input_settings_probe`).
   The commit-local `.gitattributes` (`* -text`) keeps every byte LF-stable
   (the ONT-U04 review's CRLF-drift finding cannot recur here).

## Reconciliation summary

- Done-when and profile are byte-identical to the archived ONT-U04 card
  definition (`57ded6eb…`); only the scope digest differs. Dependency
  MAT2-U01 is DONE with a merged qualified winner (PR #197); its frozen seam
  is consumed, never amended (N8 proves the seam untouched).
- The pinned modules are NOT yet on `astra/gait-capture`; this candidate is
  qualification evidence over the pinned lineage — the same delivery shape as
  the merged MAT2-U02 candidate (no `proposed.patch`). Integration and
  publication remain lead-serialized.

## Honest limits and disclosures

- The capture pixels are a deterministic CPU visualization of the recorded
  headless trace; the body is the harness's declared integration of the real
  emitted CommandRecords — NOT native engine frames, no native-render or W10
  claim. The persistence leg is a REAL separate OS process; the battery leg
  runs the pinned test module unmodified.
- Two prereg wording miscounts are disclosed in
  `numerical_receipt.prediction_deviations` (replay records: prereg said 11,
  the pinned mapper's frozen law yields 10 — boundary 500 is the
  grid-dissolve tick; N6's "original-phase records" comparison is implemented
  as replay-law conformance + parent/child field-exactness because no
  main-trace window pairs 1:1 with the replay's key+mouse combination).
  Nothing was silently corrected.
- NOT claimed: camera obstruction avoidance (U02's subject), focus loss
  (U03), climb intent (U05), native checkpoints (V03/V04), trained gait,
  new model, full-game completion.

## Remaining gates

Independent worker review of this candidate; lead-serialized publication to
`review/MAT2-U04`. At acceptance the lead sets `head_sha` and
`independent_review` on `qualification_receipt.json`
(in-tree `head_sha` is null by design).

## CORRECTION (independent-review findings applied; this attempt)

Attempt `c6818f39ff824b8bb612d3d1ba4204f3` (branch-1), worked per the P01
reviewer-executed-correction precedent. Applies the two exact defects of the
independent review of this candidate (review
`f926df0ce66c4dcabd51338940510c0b`, verdict CHANGES_REQUIRED, PR #204 head
`504a7fa0a90b163743eadadacbd6173325211a48`). Everything else in the report
above is the original candidate text, unchanged; all verification was re-run
GREEN in the review and the candidate bytes are otherwise untouched.

1. **qualification_receipt.json evidence bindings now bind the DELIVERED
   bytes.** The original receipt carried stale hashes for two entries (the
   probe rewrites `numerical_receipt.json`/`runtime_receipt.json` on every
   run — wall clock, child pid — and the receipt generator ran before the
   final probe run): `evidence.numerical.raw_sha256` `a4ae2518…` ->
   `578fae40c41f147ba8f6d191595b5d8867820708bd76d4186571076a40932c78`;
   `evidence.runtime.raw_sha256` `68bc21bb…` ->
   `ca1dae90a7381784f42ba456cbd13606c0c6c450c68e221e80519de8ca8a77d9`.
   Recomputed from the committed files; no probe re-run; every other binding
   (source, visual, camera, candidate_suite) already matched and is unchanged.
   Regenerated receipt sha256
   `4af13d1299a5b6fccb8e95a18ecfb6189f29820e0a85ec85bccc98fccdaaff7f`.
2. **Third prereg-vs-measured miscount now disclosed.** The frozen prereg
   labels the decay tail's second record "boundary 19000: v == 0.0 exactly;
   then inert", but the pinned mapper's frozen second-boundary deadline law
   emits the exact zero at boundary **18550** (18500 -> V_MAX, 18550 -> 0.0,
   then inert; 19000 emits nothing). The 368-record count held exactly and no
   N-check enforced the label, so no GREEN check is falsified. The entry is
   recorded in the qualification receipt's `prediction_deviations`
   (check `N9-decay-label`, trace-bound), NOT corrected in the frozen
   prereg — PREREGISTRATION.md is byte-identical to freeze commit `9b93a848`
   (sha256 `a4e31f052b228f67c414492da68aef97906264c4622d7d417f02a385f91646a0`).
   The two miscounts recorded in `evidence/numerical_receipt.json`
   `prediction_deviations` are unchanged (that file was not rewritten).

Diff vs the reviewed head touches ONLY `qualification_receipt.json` and this
`report.md`. Both campaign validators re-verified on the committed envelope
(task_id `U04`): `visual_capture.validate_manifest` and `visual_gate.verify`
-> structurally_valid true. Unit tests 17/17 re-run OK. All other candidate
bytes (probe, battery, records-leg snapshot, trace, capture, manifests,
receipts, reference pins) are byte-identical to the reviewed head.
