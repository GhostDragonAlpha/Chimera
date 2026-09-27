# PREREGISTRATION — MAT2-P02 prototype recovery + lineage reconciliation

Card: MAT2-P02 (planning id P02), attempt b6607daeeed549aeb865302efd24eb9a,
agent arrival-fb675f3fd2934822acfe7190d04bc790.
criteria_sha256 28148c96061a42ae49753b622876f9ed1337aadb8f814b34204fb13fc7023c0d
active scope cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097
(astra-0031), task definition raw sha 57ded6eb2f2cc6aa914d6f68c8efb55b215790fc7a9d0baa5dfd2c49fd1465c1.

FROZEN before any build, run or evidence consumption for this attempt.
Date frozen: 2026-09-26 (local). All runs CPU-only, `python -B`, no GPU, no
training, no engine source edits, no process kills.

## 1. Statement (someone could disagree)

The operator-observed prototype — "the real CT body WALKING ON ALL FOURS"
(deliverable `real_body_walk.mp4` sha256 `2e2982f1e98204a3682b71f70bb6be542ae6b3edeceec9f2ad09f96dcd84699a`,
pinned at lane commit `17ba94b948ca217c1bbf8f7dee5b51b995b387bb`,
lane `lane/visible-walk-20260923`, receipt
`tools/science_funnel/validation/visible_walk_20260923/receipt.json`) — is
recoverable and reproducible from pinned, re-verifiable records: its executable,
build recipe, source, body, scene, motion driver and captured behavior are all
byte-pinned in the git object store reachable from the attempt checkout, and the
motion leg regenerates byte-exactly on this machine today. The MAT2-P02
five-item lineage clause is carried by the merged, lead-approved ONT-P02 map
(merge `51eaa010177b71d7728234c8b2883ef6547fa3a4`, PR #157, head `010ccd2d3d8b2e37842dcab00dfe31bfc7fa6c8a`)
and is re-verified, not re-implemented. Every missing piece is named as an
explicit unresolved gap and nothing is invented.

## 2. Frozen predictions (all evaluated only after this freeze)

- **P1 SCENE REGENERATION.** Extracting, byte-identically by blob sha, the
  pinned generator files from the `17ba94b9` tree (`tools/science_funnel/gait_scene.py`,
  `tools/science_funnel/common.py`, the `tools/creature_graph` package files it
  imports, `tools/science_funnel/validation/gait_controller_20260918/derived_numbers.json`)
  and running `python -B gait_scene.py --output <scratch>` reproduces the scene
  file with sha256 `f6844eeae3dc87170a572ccdeedf326a6cac4f73d1448941808bd8b25a8db342`
  EXACT (the certified scene anchor).
- **P2 MOTION REPRODUCTION.** Extracting the pinned statedump variant
  (`tools/science_funnel/validation/visible_walk_20260923/native/gait_unit_viswalk_dump.cpp`)
  into the extracted tree at `ChimeraEngine/engine/tests_coupled_arm/` together
  with its include closure (`engine/gait_controller.hpp`,
  `engine/coupled_articulation.hpp`, `engine/earth_environment.hpp`,
  `engine/force_models.hpp`, `native/viewer3rd/json.hpp`) and building with the
  pinned recipe (`vcvarsall.bat x64 && cl /nologo /std:c++17 /O2 /W4 /fp:precise
  /EHsc /DGAIT_EVENT_TRACE ...`) yields a binary that, run on the P1 scene with
  `GAIT_STATE_DUMP`/`GAIT_STATE_DUMP2` set, produces stdout sha256
  `8c537cdb7cb8c43cf9423cb50056787bcc31ee487d70d3c2a1e73ed5d60b06cc` EXACT,
  GAIT_EVENT_TRACE stderr sha256
  `c6f9b6c00a1d549a4bc709724d2f62f8f28b37823696de4689e1950651c37481` EXACT, two
  internal q dumps bit-identical to each other and to the pinned value
  `b47b709c43a021d24bfee13bb2fe4592167cf205ee0abf9971de462319389c93`, 302 dump
  ticks spanning 0..301, refusal at tick 302, and base dx `0.9131056683968011` m.
- **P3 WALK NUMBERS.** Recomputing the walk's numbers from the P2 dump
  reproduces the pinned receipt values: `ticks_covered` 302, `refusal_tick` 302,
  `engine_base_dx_m` 0.9131 (rounded), `worst_ledger_J` 30.970714.
- **P4 BEHAVIOR BYTES.** The pinned movie blob `real_body_walk.mp4` at
  `17ba94b9` hashes to `2e2982f1e98204a3682b71f70bb6be542ae6b3edeceec9f2ad09f96dcd84699a`
  (1,570,836 bytes); its receipt declares 340 frames / 20.04 s and the frame
  plan (24 lead-in + 302 walk + 14 end-hold = 340) is arithmetically consistent;
  the in-tree `states_run1.jsonl` dump blob hashes to the pinned
  `b47b709c43a021d24bfee13bb2fe4592167cf205ee0abf9971de462319389c93`.
- **P5 LINEAGE CARRY.** The merged ONT-P02 records leg re-verifies at this
  candidate from its extracted merged bytes: `verify_monkey_lineage.py --expected-criteria 5c0720b4451b8b9ea22360575461968667496000220c8cba645e1d3e28f252ef`
  exits PASS (152 checks / 23 pins) and `python -B -m unittest test_verify_monkey_lineage`
  reports 23/23 OK; the five card items (CT monkey, source MSK model,
  forearm/paddle assets, training body, runtime body) remain related exactly as
  merged, and the six mass lineages stay distinct.

## 3. Frozen falsifiers

- **F1 PIN-RESOLUTION.** Any pinned commit or blob above that fails to resolve
  in the attempt checkout's object store, or any byte-identity prediction
  (P1–P4) that misses its exact sha, REFUTES the recovery claim. No
  substitution, re-roll or tolerance is permitted; the failure is recorded and
  the affected clause reported as unresolved.
- **F2 LINEAGE-REGRESSION.** If the merged records leg fails any of its own
  frozen checks at this candidate (P5), or any five-item relation or mass
  lineage differs from the merged state, the reconciliation claim is REFUTED.
- **F3 GAP-INVENTION.** Claiming a trained walking policy, an interactive
  playable walking build, a landed stride-phase judge verdict, or ship-cleared
  CT assets where the pinned records show none REFUTES the recovery claim.
  Named standing gaps frozen at freeze time (to be re-stated, never silently
  resolved): (a) no trained policy exists — the prototype's motion driver is the
  engine's own certified gait harness (`gait_unit.cpp` @ engine base `f89cab4e`)
  with its own refusal death at tick 302; (b) the walking prototype is a
  captured movie, not an interactive playable scene; the playable slice boots a
  STANDING body; (c) the blind-judge AMENDMENT 1 stride-phase sample
  (`judgement_stride.json`) is PENDING — never landed in any ref; (d) CT
  distribution is BLOCKED FOR SHIP (MorphoSource 000875604, operator decision
  request `066485ae`); (e) the CoT denominator 13824.5 kg vs training body
  10.038 kg mismatch stays RESOLVED-AS-WRONG, correction needs a lead-authorized
  new registration (D-W04 §7).

## 4. Frozen probes (exact commands)

1. Extraction: `git show <rev>:<path>` for every pinned file into the attempt
   scratch; each extracted file's sha256 recorded against the pinned blob id.
2. P1: `python -B gait_scene.py --output <scratch>\scene` from the extracted
   generator tree; `sha256sum scene.json`.
3. P2: build per the pinned `build_dump.ps1` flag pattern into attempt scratch;
   run via the `run_dump_walk.py` contract (env `GAIT_STATE_DUMP`,
   `GAIT_STATE_DUMP2`, raw-byte stdout/stderr capture); hash all four outputs.
4. P3: per-tick q[3]/q[4] base trace from the reproduced dump → tick count,
   span, base dx/dy; ledger value taken from the reproduced stdout's own
   anchor line set (parsed, not copied).
5. P4: `git cat-file` blob bytes hashed; receipt/frame-plan arithmetic checked.
6. P5: merged ONT-P02 contribution dir extracted byte-identically from merge
   `51eaa010`; verifier + falsifier suite run with cwd = the attempt checkout
   (its object store), CPU-only.

## 5. Deviation rule

Any probe change after this freeze is recorded in the report's deviations
section together with its reason BEFORE the affected evidence is consumed; no
evidence from an amended probe is declared under the original prediction
number. Infrastructure failures are preserved verbatim as attempts.

## 6. Honest boundary

This is a records/anatomy recovery card (verification_profile `anatomy`,
kind `reconcile`). The visible_static capture leg is the merged ONT-P02
winner's capture (6-panel contact sheet, capture `ont-p02-visible-static-20260926-b248ac96`),
carried by reference with its merged evidence hashes and re-verified structurally;
this attempt does not re-record it. Nothing here implements new physics,
replaces any subsystem, or claims playable completion; MAT2-P01's frozen
contract remains the finish line.
