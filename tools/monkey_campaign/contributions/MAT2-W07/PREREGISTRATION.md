# PREREGISTRATION — MAT2-W07 load the accepted walking policy in the native runtime

Frozen BEFORE any load/run receipt exists. This file is committed ALONE
(separate-first; the M03/P04 law). Every emitted receipt refuses any document
whose `preregistration_sha256` does not match these live bytes.

- Card MAT2-W07 (planning id W07, wave 8), agent `wk-w07-native`, attempt
  `bf3fd3e8c78145f6964a661e78d56ea9`, attempt workspace
  `E:\ChimeraWork\monkey-coordination\kanban-attempts\MAT2-W07\bf3fd3e8c78145f6964a661e78d56ea9`,
  publication branch `review/MAT2-W07`, PR base `astra/gait-capture`.
- Criteria sha256 `2c942079f1c8bb88a7ac41908c9b46d659e05ff0f2b6d79fb14eb8a6e1e98fd0`
  (startup join == registry `kanban.cards[MAT2-W07].criteria_sha256`, re-read
  READ-ONLY (`file:...?mode=ro`) from
  `E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3` at run time;
  mismatch = refusal `criteria_pin_mismatch`).
- done_when (verbatim, registry): "Runtime consumes the certified
  observation/action contract and drives physical actuators. Material-first
  addition: The controller supplies bounded activation/pressure/effort to the
  accepted material system; native solved matter is the only physical pose
  authority."
- Observation (verbatim, registry): "No pose-writing locomotion substitute".
- Card task falsifier (verbatim): "Sliding/penetration, unsupported
  propulsion, hidden reset, wrong command response or diagnostic/clean state
  divergence fails."
- Profile: `walking`/`motion`; numerical_evidence_required true;
  clean_view_required true; the capture is delivered per the sealed W06
  motion-replay precedent (section 7) with the absent inventory named.
- Base: `fa02f075` = `origin/astra/gait-capture` tip at join (the MAT2-G05
  merge, PR #300; it contains the MAT2-W06 merge, PR #299, correction r1).
  Candidate branch: `codex/monkey-mat2-w07-bf3fd3e8` (the join's nominal
  `branch-3` is the lead-serialized publication slot, never pushed by a
  worker; the recorded W05/W06 deviation applies unchanged).
- Composed against CARD_STARTER v3 and the house standards:
  `IMPLEMENTER_CHECKLIST.md` (G1-G9) + `TOOLKIT.md` (P1-P9), cited at the
  candidate commit. Dispatch brief:
  `E:/ChimeraWork/monkey-coordination/gap-analysis/wave-8.md` (MAT2-W07
  section).
- Calculations: C10 (held-out train/evaluation separation, already sealed by
  W06 — consumed read-only, never recomputed) and C11 (the runtime
  consumption of the certified contract — this card's execution arm).

## 0. The governing frame (what "load" and "native" mean on this card)

THE ACCEPTED POLICY IS THE FROZEN CERTIFIED LINE — nothing else. W04 froze
the runtime/training contract and re-issued the compatibility certificate
(cert_hash `4b306f4f66f100335276fdc79f1e201aaccacc65ce7303f65183ea46d283f76b`,
compat_key `dbda388b4797cfaaac3995d044cbca9da408e5eba450466d11b98cdbe15cd244`,
store-pinned). W05 produced trained thetas that all FAILED the frozen
training-signal criterion; W06 sealed their deploy treatment:
ALLOW(frozen)/BLOCK(trained). This card LOADS THE FROZEN LINE and never loads
the trained bundles; the deploy gate is the executed instrument of that
distinction, run in BOTH directions at load time.

"THE NATIVE RUNTIME" is the certified runtime side of the W04 contract: the
sealed `tools/policy_compat` machinery (validator, deploy gate, frozen P3
loader, frozen inference recipe, declared deterministic CPU walk scene
`cpu-walk-scene/1.0.0`, build `cpu-walk-scene-build-N`), consumed UNMODIFIED
through a sha-pinned extraction exactly as W04/W06 consumed it. The
machinery's own honesty label is carried unchanged: the certified execution
vehicle is the DECLARED SURROGATE scene; the adopted assembly
(`chimera.b07.adoption.240b457bc9612111173314b49f453b80`, the TC-7 BINDING
TARGET) is NOT a runtime-qualified body, because its two reissue
prerequisites are structurally missing (section 6).

- BQ-1 (CPU-first): the certified backend is the CPU scene; this card is
  CPU-only (the capture's FFV1 encode/decode ffmpeg calls are the declared
  capture-tool exceptions, W06 addendum precedent). No GPU work exists in
  this lane. No engine binary is built or run (the W2 engine-up lane proved
  the engine accepts `/skin_bin` uploads; an upload is not this card's load,
  and the product engine has no live control path for the certified policy —
  named-missing, section 6).
- TC-6 (the gate): deployment requests are checked against the certificate
  by the machinery's own `check_deploy`; the validator is the only
  authority. The load on this card happens ONLY AFTER an ALLOW.
- Claim class (verbatim from the certificate, COST-GAP): offline/trace
  qualification at the 300 Hz tick is the ONLY satisfied execution class;
  interactive real-time 300 Hz is NOT a satisfied line and is not claimed.
- The no-reissue law: this card deploys the EXISTING certificate; it does
  not re-issue, re-certify or amend anything. A policy binds only by
  reissuance through the gate, and nothing on this card changes the
  certificate's bytes.

OUTCOME-INDEPENDENCE DISCLOSURE: the sealed W06 replay already reproduced
the certified trajectory anchors. This card's execution arm re-executes the
line THROUGH THE LOAD PATH (gate -> frozen loader -> runtime), which is the
seam W06 did not consume; the anchors are re-checked because a load that
reproduces them is the definition of "the accepted policy, bit-for-bit", not
a new claim.

## 1. Input pins (verified byte-exact at attempt start; drift = refusal `input_pin_mismatch`)

All upstream artifacts are pinned at their durable paths — the W04 freeze
records in the evidence store, the W05/W06 published bytes at their merged
in-tree paths (base `fa02f075`), the sealed lane machinery at
`E:/ChimeraWork/pass3-integ/repo`, and the ingestion-spike evidence in the
coordination store. Computed live at attempt start (sha256):

W04 freeze records (evidence-store/MAT2-W04/):
- `numerical/w04_certificate.json` `07f05bfa982e066ae67413b04e3367c5ad7570830e99fc32edcb86cbe8d87598`
- `numerical/w04_freeze_manifest.json` `be632ffc85865515285f3d622a09882a3180a43101027914f1ed3408496f5d29`
- `numerical/c09_anchor_reseal.json` `2311c10c05f0846989909090966285f59b84dd4d6b4d6b46c464a6efa7e647f4`
- `numerical/checks_receipt.json` `05e28bbaffcf9d65db174ec9b83708d33705922ac506b1cee852a2f9790744c9`
- `numerical/w04_gate_receipt.json` `d8cd056ffb245a910f08bdf15ab1dd068291110badcbf8a3946795b5ebd5d78b`
- `logs/gates12_w04.json` `1c5d74d9d44c18142f9016bfbc5cd7a9ca85a7673688437955a98c2eef21ef6b`

W06 published bytes (merged in-tree, contributions/MAT2-W06/):
- `PREREGISTRATION.md` `31d43b67132b2a4fe0167be0297193734e0a8d2bca929ac8607157b72d53a87e`
- `PREREGISTRATION-ADDENDUM-1.md` `dea6b825774b0770100a81c482fb08082397ae740f23034954454c2a6df9caba`
- `REPORT.md` `978aff5eb57416a4ff984c989865381e7bc3c3d54753c6929df4abbd700be61b`
- `verify_inputs.py` `f02085eae26cd5d3cff1f90c05409a2c797b56c07b552294731465fa2d33a067`
- `run_replay_capture.py` `fececfbe25dcda4b6ffb37613f51306a8b531603fb38a56bb69ece2e846d75af`
- `run_checks.py` `f4926e3e89f44af661b5e41a9538aa1151eb082d47bd0174ad92adc22add2235`
- `checks_receipt.json` `7e4891be165ce9113c3bf7b319e2ab5bb0ac34ec76994264e5339c172c1439b2`
- `receipts/evaluation_summary.json` `a1af58baf15edd7ac595b5bb4571e13ed44780f77faf5a761355140f456b075a`
- `receipts/input_pins.json` `6740532e6159ebe6493527ed8908f5041841510e29fb344c14a05467382902c1`
- `capture/replay_receipt.json` `c8ba8705560a148c82922efd2f194d29378c672a065eea97692900c42d32cd8d`
- `capture/trace.json` `15bf0b4c47ba208366b4bf7cd77775d434c836b70c992e198c51aa9012e1d535`
- `capture/capture_manifest.json` `6b696efa76b1e9e0a8d3a5ff4f7cbd0a248e65f843d1f8f1ded4d7d29516f181`
- `capture/capture_context.json` `7cbc302efe15fad78e1fae557fbfd610c1a77756b697437bcc75567cc4afe390`
- `capture/capture_validation_receipt.json` `335a9091071eea6e4881b797094890d792192edc4f0febd6ba6ea0b9d41c003e`
- `capture/frame_hashes.json` `be88b5381ab0c814845fcbc7ea99219f704db9695b3ad937856cd965f017f443`

W05 published bytes (merged in-tree, contributions/MAT2-W05/):
- `receipts/deploy_check_receipt.json` `766a7cbe6a2ccd67c739d82af5b32e859ee4bc3f3a558715fafc63dbab0ae635`
- `PREREGISTRATION.md` `260c6d53e66c79689e95b5f880c1f6828f5316d4d7d6e172132296137d3f1c2a`

Sealed lane machinery (pass3-integ/repo; consumed read-only, pinned bytes;
values verified identical to W06's addendum-A1 pin table — no drift):
- `tools/policy_compat/__init__.py` `11d523c8c0ee363e09c4e57afa564f3e38b178e274d7ee3ef335f5a0c44e9f4e`
- `tools/policy_compat/__main__.py` `74d592d0551e226289f944e8182a19a3b574d7d2ee331e157e17ac55ea969528`
- `tools/policy_compat/certificate.py` `2b6a75ba79c367a646d89fdc8cbe2243239dbc5e336f1eba1deb33aa30e295ac`
- `tools/policy_compat/engine_cert.py` `c1aa05362e20a3e0c8967634af2d97fadd11d62daf412e07917824f16c1e5152`
- `tools/policy_compat/injections.py` `1b5b978bf5feafb93801066486a5656caaba7cf3a618949036c13d0ceae28f1e`
- `tools/policy_compat/runner.py` `1fa8d8b70836d6e3355e3e2630f83e0a6a31a9658104e9f928d7ef52cfef5160`
- `tools/policy_compat/scene_cpu.py` `ab4257024df63d9755e9c1ae524ee631339ce24a2fd36615d40575335f835af2`
- `tools/policy_compat/snapshot_api.py` `c47a09596dd36692aa28f8f10b2967d9276b78082a96d0bba27bf632b8f0e493`
- `tools/science_funnel/typeb_export/infer_numpy.py` `8030b609c7ecbfcc368addee2c140b830450fff48ecb62e02683d62062bfbfc4`
- `tools/science_funnel/typeb_export/observation_schema.py` `8876e1a64d68e93b003c6daba8cacb34bff02c11133eb098bf1ef85bf8a39894`
- `tools/science_funnel/typeb_export/policy_manifest.py` `a65cf8757c9d4d4d6a8d5fce30be6aaebb016c98d7dc69f972b0b7781e2961d7`
- `tools/science_funnel/validation/typeb_p3_20260921/policy_manifest.json` `aa5334f797b50c2ac3950cec5b82b439f982c1090dd66827754a1acbb8a26b6f`
- `tools/science_funnel/validation/typeb_p3_20260921/dummy_actor.npz` `5fb2b7857d872fccc0bb89d6733582647da04d11d636e84c266912ce9c027f0f`
- `tools/science_funnel/validation/typeb_p3_20260921/trace_slice_wave38.json` `69babe846e2447333b527c7fd8c190499e5ac1d55733dbd043edd0422245daa2`
- `tools/science_funnel/validation/upgrade_gate_20260920/receipt.json` `2c7794e6ff0c5c2d81c39536076ce1d6a0900333f4738549079afbe21012685a`

Ingestion-spike evidence (named-missing inputs, coordination store):
- `ingestion-spike/INGESTION_SPIKE.md` `218b34614d8917eceb3f4ea2a6404c5715f8e25f71e57989c53213d7498e512b`
- `ingestion-spike/tile_ingest_receipt.json` `bc252e448805bf082198ec5802ff82662fa52a39673236eb001929d86494e97f`
- `ingestion-spike/w2-engine-up/ENGINE_UP_RECEIPT.md` `364ae9453bdba88f636980a971263847823a14d8f7c2e957719a87421b7bb73c`
- `ingestion-spike/w2-engine-up/w2_post.py` `dd1fa9118f73a505bf1c8153f5de2853cf307ba86754e150c562904bc39cf325`

## 2. The frozen load protocol (order is law)

1. Verify every section-1 pin; re-read the registry READ-ONLY and require
   the criteria hash. Any drift is a named refusal BEFORE anything runs.
2. Pin-extract the machinery tree under scratch and import ONLY the pinned
   bytes (W06 addendum-A1 pattern; zero machinery files modified).
3. Re-validate the pinned W04 certificate with the machinery's own
   validator (the only authority): zero violations, else refusal
   `certificate_validator_violation`.
4. Build the deployment request tuple from the certificate's OWN relation
   components (the certified 5-tuple: policy_bundle, physics_build,
   runtime_profile, body_domain, test_suite) and run `check_deploy`:
   ALLOW is required BEFORE any load. Non-ALLOW is refusal
   `deploy_gate_sanity`.
5. ONLY THEN load the bundle through the FROZEN loader
   (`typeb_export.policy_manifest.load_manifest` via `runner.load_bundle`)
   and require bit-for-bit identity against the certificate's policy_bundle
   component: manifest_hash, weights sha, manifest file sha, architecture,
   activation, normalization clip. Any mismatch is refusal
   `load_identity_mismatch` (the W04 seam, executed).
6. Verify the physics build identity: build N params sha ==
   certificate.physics_build.params_sha256; the pinned scene module sha ==
   certificate.physics_build.scene_module_sha256; timestep == 1/300 s.
7. Execute the loaded runtime: `run_closed_loop(bundle, build N, params,
   seed 20260920, 900 ticks, collect_records=True)` — the certified
   corpus/horizon of the certificate's test_suite. THEN check the three
   baseline anchors (section 3 P3) BEFORE any receipt is emitted.

## 3. Frozen predictions (registered BEFORE the load; disclosed either way)

- P1_gate_load_allow: the certified 5-tuple ALLOWs against the re-validated
  W04 certificate and the load proceeds through the frozen loader with
  bit-for-bit bundle identity (manifest_hash `9ca7e976dfb0dedd...`, weights
  `5fb2b7857d872fccc...`).
- P2_gate_discrimination: the trained-theta bundle tuple BLOCKs at the same
  gate (compatibility-key mismatch); a foreign build_id BLOCKs; a missing
  certificate BLOCKs.
- P3_anchors_exact: the loaded runtime's run reproduces the certified line
  EXACTLY: trajectory_sha256 `cd4944d99be1270951926be53859828a6b0aef21d32d6551f68e78d504ef6c7a`,
  initial_snapshot_sha256 `11ac68cfb2c237445902b65bd1ee3bd228d915e1009d01d1cd16a3e5aab13346`,
  final_state_sha256 `b9a7fb99c32013e2e993c8c81a88b0abea2d5e0ce19e010e344b5d4e8cb27d72`.
  Any drift is the named refusal `baseline_drift:<key>` and NO receipt is
  emitted.
- P4_contract_consumption_bit_exact: the runtime consumes the certified
  observation/action contract bit-for-bit — at EVERY decision tick the
  independently recomputed applied vector (pinned `project_trace` through
  the declared field table -> the manifest's declared consumer width ->
  `clip((x-mean)/std, -8, +8)` -> tanh MLP -> `clip(center+scale*a, lo, hi)`)
  equals the runtime's own applied commands exactly (float32 array
  equality); every hold tick reproduces the previous applied vector exactly;
  decision iff tick % 15 == 0 (60 decisions over 900 ticks; the clock closes:
  20 Hz x 15 = 300 Hz).
- P5_caps_and_gates: every applied command lies within the manifest limiter
  bounds at every tick; no NaN/Inf in any recorded state quantity;
  intervention_reason == "none" at every tick; contact_count >= 2 at every
  tick; available_groups exactly the declared set; |v| <= the derived
  envelope at every tick.
- P6_pose_authority: the runtime has NO pose-writing channel —
  (i) structurally, the scene's public stepping API accepts only the bounded
  8-command vector plus the limiter saturation vector (introspected on the
  pinned bytes: no method writes body pose outside the declared
  restart-snapshot path, which is a restart instrument, not a per-tick pose
  authority); (ii) dynamically, the machinery's action-replay refusal FIRES:
  `requalify(..., precomputed_actions=...)` raises ACTION_REPLAY_REFUSED
  (observations and actions are recomputed from the solved trajectory every
  tick); (iii) the observed motion is produced solely by the scene's solved
  drive law from the bounded commands.
- P7_named_missing_stands: the two B07 reissue prerequisites remain open at
  this tip exactly as the pinned W04 certificate declares; the
  adopted-assembly native load is NOT attempted and NOT fabricated; the
  product-engine live-control path for the certified policy stays absent
  (pinned spike evidence); the certified claim class stays offline/trace at
  the 300 Hz tick.

## 4. The certified contract clause set (what "consumes" is measured against)

From the pinned W04 certificate (quoted identities, never re-derived):
tick 300 Hz physics / 20 Hz policy / 15-tick hold; the observation interface
= the pinned v2 field table (OBS_SCHEMA_VERSION 2, 80 declared fields, legacy
width 64, the manifest's declared consumer width, no privileged field,
unavailable channels mean-filled and masked — never invented); the frozen
inference recipe (the certificate's runtime_profile.inference_recipe,
verbatim); the actuation caps = the manifest limiter bounds with the
saturation indicator; the pose-authority law = native solved matter only;
the C09 anchors = the pinned W04 re-seal (9/9 EXACT on the native coupled
line: ticks 302, refusal_tick 302, base_dx/base_dy, dump/stdout/stderr,
worst ledger); the qualification bars (bounds_honored, no_nan_inf,
no_intervention, contact_floor, availability_exact, velocity_envelope).

## 5. Falsifier mapping (card falsifier -> executed detector)

| falsifier class | executed detector on this card |
|---|---|
| sliding/penetration | contact_floor bar checked per tick on the loaded runtime's records (>= 2 contacts; a breach is a named refusal, never a pass-through) |
| unsupported propulsion | velocity_envelope bar per tick against the derived envelope V |
| hidden reset | no_intervention bar per tick PLUS the continuous hash-chain event sequence reproducing the sealed chain (any reset/restart inside the run would move the chain and break P3) |
| wrong command response | bounds_honored bar per tick PLUS the bit-exact recipe recomputation (P4): the applied bytes are a pure function of the certified contract, so any un-contracted command path breaks equality |
| diagnostic/clean state divergence | the capture renders diagnostic and clean bands from the SAME recorded per-tick state (one state hash per frame row-pair; section 7) |

The falsifier must be able to FAIL: FB bite arms (section 8) prove each
detector fires on a tampered input and stays green on the clean run.

## 6. The named-missing recording protocol (never fabricate a load)

The card's gated parts are RECORDED, not executed:

- N1 adopted-assembly runtime scene module: the pinned W04 certificate
  declares "a runtime scene module executing the adopted assembly (none
  exists; named-missing; gates RUNTIME USE, not this freeze)". This card
  re-checks the presence claim honestly (the pinned machinery's scene-module
  inventory is exactly the certificate's declared surrogate scene module;
  the in-tree base carries no runtime scene module at all) and records
  outcome NAMED_MISSING for the adopted-assembly native load. Nothing is
  loaded on the adopted assembly; no pose, mass or drive constant is
  invented for it.
- N2 TC-3 drive-table re-declaration: the adopted assembly's drive table is
  NOT re-declared from its own sealed sources (the certified scene's caps
  never transfer silently). Recorded NAMED_MISSING; the certified scene's
  drive table is used ONLY inside the declared surrogate scene, never
  presented as the assembly's.
- N3 product-engine live control path: the pinned ingestion-spike evidence
  establishes the native windowed engine accepts `/skin_bin` uploads but has
  NO live input path for the certified policy (`/gait_bin` is a different
  CPG gait; "NO LIVE PATH" for the W03/W04 line; a `/skin_bin` load is an
  upload, not a simulation). Recorded NAMED_MISSING for the windowed-engine
  visual walk claim; the certified execution class stays offline/trace at
  the 300 Hz tick (COST-GAP, quoted from the certificate).
- N4 C09 anchors on the adopted assembly: the pinned re-seal is the native
  coupled line's own evidence; its adopted-assembly re-run remains
  structurally missing (the pinned receipt's own status line, carried
  verbatim). The C09 anchor receipt is verified byte-exact and carried; it
  is never re-issued by this card.

## 7. Capture protocol (profile walking/motion; the W06 sealed precedent)

The one declared capture arm: 60 frames at the loaded runtime's decision
boundaries (EVENT_STRIDE 15, ticks 14..899), each frame a sheet of the three
profile views (full-body ground overview | side view of stance/swing |
close-up of foot-ground contact) with the five declared diagnostic layers in
the diagnostic band and the clean band below rendered from the SAME recorded
state; encoded FFV1 (`-c:v ffv1 -level 3 -g 1 -fflags +bitexact`); G4
pixel-exactness decode check; camera record fields complete per row; the
validator `visual_capture.validate_manifest` (CAMERA_METADATA_STRUCTURE_ONLY;
visual_acceptance stays False — independent visual review remains the
Sergeant's). The subject receipt binds THIS card's load receipt (gate
decision, anchors, contract consumption), and the honesty label names the
record-space delivery: the frames are record-space panels of the loaded
runtime's own per-tick telemetry — NOT engine frames; the native windowed
engine cannot host this load (N3) and the absent inventory says so. The
diagnostic/clean bands are rendered from one recorded state per frame, so a
view toggle cannot move the state identity (the falsifier's instrument).

## 8. Named checks and gates

- Suite `test_w07_native_load.py` (unittest discover -p test_*.py), G12
  accounting executed/skipped claimed in the report. FB arms, each with a
  clean control AND a bite: FB1 pin-verifier bite (tampered pin table ->
  `input_pin_mismatch`); FB2 load-gate bites (foreign bundle tuple BLOCK,
  foreign build BLOCK, missing certificate BLOCK); FB3 anchor-drift bite
  (a tampered frozen anchor value -> `baseline_drift`); FB4 bounds bite
  (an out-of-bounds applied vector -> detector fires); FB5 recipe bite
  (a swapped normalization vector -> the bit-exact recomputation detects
  the mismatch); FB6 named-missing presence bite (a receipt draft without
  the N1/N2 records -> detector fires); FB7 structural scan (the
  contribution launches no engine/simulation/training process; the only
  subprocess calls in the whole contribution are the declared ffmpeg
  capture-tool calls in make_capture.py).
- The 12 campaign gates run over the card dir via the card-kit
  `batch_gates.py`; results written to scratch (never the card dir).
- Report GENERATED from the receipts by make_report.py; every numeric
  literal proven traceable by lint_report_numbers.py (adapted from the
  sealed W06 lint, upstream artifact table pointed at this card's pins).

## 9. Deviations (recorded, none silent)

- Candidate branch is `codex/monkey-mat2-w07-bf3fd3e8`, not the nominal
  `branch-3` (the lead-serialized publication slot; worktrees cannot share a
  branch; the recorded W05/W06 deviation applies).
- C10 (held-out evaluation) is NOT recomputed: W06 sealed it; this card
  consumes the sealed receipt read-only and claims nothing about it.
- The capture arm re-renders the certified line's motion as W07's own
  record-space delivery with W07's subject receipt; frame CONTENT is
  generated by this attempt from its own run (not copied from the W06
  capture), and the W06 capture remains the sealed upstream evidence it is.
