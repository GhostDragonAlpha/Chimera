# PREREGISTRATION ADDENDUM 1 — MAT2-W06 the profile-conformant motion-replay capture arm

Committed ALONE, BEFORE the replay capture executes (the M03/P04 law:
amendments land before experiments). Amends PREREGISTRATION.md (sha
recorded at commit time; every receipt refuses a mismatch). Motivation: the
acceptance packet's structural gate `motion_capture_interval_empty` — the
sealed verification profile is kind `motion`, so the delivered capture must
be a motion replay over a real tick interval, not a static record-space
sheet. The evaluation substance of this card (the per-seed frozen-metric
verdicts) is UNCHANGED by this addendum.

## A1. The replay-capture arm (what runs, and what it is)

- WHAT RUNS: the SEALED CERTIFIED BASELINE LINE re-executed through the
  UNMODIFIED pinned machinery — `gate_runner.run_closed_loop(bundle,
  build_n(), seed=20260920, horizon=900, collect_records=True)` — exactly
  the W05 retained-baseline arm (frozen P3 policy closed loop, build
  `cpu-walk-scene-build-N`, params sha `3e770bef8b8707c99cdae2f2b2f4a8afb8d12430d987217016e6720a6d232036`).
  This is the deploy gate's ALLOW(frozen) relation: the FROZEN P3 bundle is
  the actor. The BLOCKED trained thetas are NEVER loaded; nothing is tuned;
  nothing is trained; no seed of the walk1m-r1 training runbook is re-run.
- VALIDITY INSTRUMENT (the replay is a capture OF the sealed artifacts, not
  a new measurement): the three W05 baseline anchors must reproduce EXACTLY
  — trajectory sha `cd4944d99be1270951926be53859828a6b0aef21d32d6551f68e78d504ef6c7a`,
  initial snapshot sha `11ac68cfb2c237445902b65bd1ee3bd228d915e1009d01d1cd16a3e5aab13346`,
  final state sha `b9a7fb99c32013e2e993c8c81a88b0abea2d5e0ce19e010e344b5d4e8cb27d72`.
  Any drift = named refusal `baseline_drift:<key>` and NO capture is
  emitted. When the anchors are EXACT, every rendered frame is by
  construction a view of the sealed line's own trajectory.
- PREREG SECTION 3 AMENDMENT (the no-runs law): the law's object is
  unchanged — ZERO training runs, ZERO tuned runs, ZERO evaluation rollouts
  of the trained candidates, ZERO retries. The replay above is a NAMED,
  DECLARED exception class: a deterministic re-execution of the certified
  frozen reference line whose only outputs are the anchor proof and the
  capture bytes. It introduces no outcome number that any verdict of this
  card reads.
- PINNED INPUTS ADDED (the machinery of the arm; each sha-verified, drift =
  refusal `input_pin_mismatch`), all in the pinned lane repo
  `E:/ChimeraWork/pass3-integ/repo` — identical to the W05 prereg section 1
  machinery pins. Written as assembled parts (dir · file) so this document
  carries no repo-root-looking pointer; the machine-checkable table is the
  parts-tuple list in `verify_inputs.py`:
  - group `policy_compat` (under the lane `tools` root): `__init__.py`
    `11d523c8c0ee363e09c4e57afa564f3e38b178e274d7ee3ef335f5a0c44e9f4e`;
    `__main__.py`
    `74d592d0551e226289f944e8182a19a3b574d7d2ee331e157e17ac55ea969528`;
    `certificate.py`
    `2b6a75ba79c367a646d89fdc8cbe2243239dbc5e336f1eba1deb33aa30e295ac`;
    `engine_cert.py`
    `c1aa05362e20a3e0c8967634af2d97fadd11d62daf412e07917824f16c1e5152`;
    `injections.py`
    `1b5b978bf5feafb93801066486a5656caaba7cf3a618949036c13d0ceae28f1e`;
    `runner.py`
    `1fa8d8b70836d6e3355e3e2630f83e0a6a31a9658104e9f928d7ef52cfef5160`;
    `scene_cpu.py`
    `ab4257024df63d9755e9c1ae524ee631339ce24a2fd36615d40575335f835af2`;
    `snapshot_api.py`
    `c47a09596dd36692aa28f8f10b2967d9276b78082a96d0bba27bf632b8f0e493`.
  - group `science_funnel · typeb_export`: `infer_numpy.py`
    `8030b609c7ecbfcc368addee2c140b830450fff48ecb62e02683d62062bfbfc4`;
    `observation_schema.py`
    `8876e1a64d68e93b003c6daba8cacb34bff02c11133eb098bf1ef85bf8a39894`;
    `policy_manifest.py`
    `a65cf8757c9d4d4d6a8d5fce30be6aaebb016c98d7dc69f972b0b7781e2961d7`.
  - group `science_funnel · validation · typeb_p3_20260921`:
    `policy_manifest.json`
    `aa5334f797b50c2ac3950cec5b82b439f982c1090dd66827754a1acbb8a26b6f`;
    `dummy_actor.npz`
    `5fb2b7857d872fccc0bb89d6733582647da04d11d636e84c266912ce9c027f0f`;
    `trace_slice_wave38.json`
    `69babe846e2447333b527c7fd8c190499e5ac1d55733dbd043edd0422245daa2`.
  - group `science_funnel · validation · upgrade_gate_20260920`:
    `receipt.json`
    `2c7794e6ff0c5c2d81c39536076ce1d6a0900333f4738549079afbe21012685a`.
  Execution happens ONLY from a byte-verified extraction of these pins
  (scratch/pinned_root), never from a live-tree import.

## A2. The motion capture (declared before rendering)

- Profile: `walking` (kind `motion`), loaded READ-ONLY from the registry;
  manifest validated with the campaign validator
  `tools/monkey_campaign/visual_capture.py::validate_manifest`
  (`chimera.visual_capture_manifest.v1`, mode CAMERA_METADATA_STRUCTURE_ONLY).
- tick_interval: `[0, 899]` (the full declared 900-tick sealed interval;
  t0 < t1). 1 tick = 1/300 s.
- FRAMES: 60 stills, one at each decision boundary of the sealed events
  (ticks 14, 29, ..., 899 — the pinned EVENT_STRIDE 15), each a sheet of
  three viewports (the three profile views side by side), diagnostic row on
  top, clean row below (M08 sheet pattern). Frames render from the replay
  telemetry only; every viewport is labeled with view id, mode and tick, and
  the clean row carries no diagnostic overlay. Frame PNGs live in the
  attempt workspace `capture/frames/` and are bound by
  `capture/frame_hashes.json` (tick -> sha256); the FFV1 video is the
  in-contribution evidence.
- VIDEO: `capture/capture_replay.mkv`, FFV1 per CODEC_STANDARD
  (`ffmpeg -framerate 10 -i frame_%03d.png -c:v ffv1 -level 3 -g 1 -fflags
  +bitexact`), ffmpeg version recorded in the replay receipt.
  `capture_sha256` = the mkv sha256.
- TRACE (motion `state_binding.kind == 'trace'`): `capture/trace.json` —
  the per-tick sealed telemetry of the replay (tick, com speed, com x,
  phases, foot contacts, foot forces, pad gaps, applied command,
  contact_count, plus the pinned runner's state-chain events with their
  state shas). Its canonical sha256 is the `state_binding.sha256` of every
  view row.
- SUBJECT: `capture/replay_receipt.json` (schema
  `chimera.w06_replay_capture.v1`) — anchors EXACT triple, frame count and
  stride, ffmpeg version, capture/trace/frame-hash identities;
  `subject_sha256` binds it.
- CAMERA RECORDS per profile view id (diagnostic+clean pairs share the
  camera object, as the validator requires):
  - `full-body ground overview`: orthographic fixed bookmark, 2 samples at
    the interval endpoints, span covering the walked lane.
  - `side view of stance/swing`: orthographic `sampled_trajectory`,
    interpolation `recorded_each_tick` (900 samples; the camera x follows
    the RECORDED com x each tick).
  - `close-up of foot-ground contact`: orthographic `sampled_trajectory`,
    interpolation `recorded_each_tick`, tight span on the recorded pad-gap
    geometry at the com station.
  World frame declaration: +X = walk direction, +Y = up, +Z = lateral;
  `coordinate_unit` m; `handedness` right; orientation quaternions are unit
  camera-to-frame; `distance_to_target` computed as the exact
  `math.dist(position, target)` per sample.
- FALSIFIER OVERLAY (diagnostic rows only; the five profile diagnostic
  layers, mapped honestly): `command and tick overlay` = the recorded
  applied 8-channel command stream + tick; `foot contacts and normals` =
  the recorded 6-pad contact state and forces; `support/COM markers` = com
  speed/position markers and the contact-threshold line; `skeleton` /
  `stable 3D labels` = the surrogate's recorded phase state (the scene has
  no rigid skeleton: NAMED ABSENT, never imputed).
- G4 instruments: decode the mkv and pixel-compare the declared indices
  {0, 29, 59} against the rendered PNGs (lossless FFV1: zero delta), plus a
  frame-order sensitivity check (permuting the frame order must change the
  bound frame-hash sequence).

## A3. Predictions (registered BEFORE the capture; disclosed either way)

- R1 anchors: the three baseline anchors reproduce EXACTLY (else refusal,
  no capture).
- R2 trace integrity: at every one of the 900 ticks, contact_count >= 2,
  |v| <= 2.977443609022557 m/s, `intervention_reason == "none"`, every
  applied command within the manifest limiter bounds, and the state-chain
  events are continuous (no hidden reset); the replay shows stance/swing
  alternation of the recorded pads.
- R3 media integrity: the FFV1 mkv decodes pixel-exact against the rendered
  stills at the declared indices.

## A4. Vocabulary amendments

- FB5 (the no-runs structural scan) splits into three declared classes:
  (i) TRAINING/RUN-LAUNCH paths (`run_training`, `socket`, `urllib`,
  `spsa_iterate`, `TrainablePolicy`, `fitness` calls) remain forbidden in
  EVERY contribution file; (ii) the PINNED REPLAY import
  (`tools.policy_compat.runner.run_closed_loop` and its loader) is allowed
  ONLY inside `run_replay_capture.py`, the file this addendum declares;
  (iii) the CAPTURE-TOOL calls — the ffmpeg FFV1 encode and the G4 decode
  check — are allowed ONLY inside `run_replay_capture.py`, with the exact
  argv declared in A2 (encode:
  `ffmpeg -y -loglevel error -framerate 10 -i <frames>/frame_%03d.png -c:v
  ffv1 -level 3 -g 1 -fflags +bitexact <out>.mkv`; decode:
  `ffmpeg -loglevel error -i <mkv> -map 0:v:0 -f rawvideo -pix_fmt rgb24 -`
  piped and compared against the rendered PNG bytes). `subprocess` appears
  in `run_replay_capture.py` ONLY for these two declared media operations —
  it launches no simulation, no training and no evaluation. The bite arms
  for all three classes stay in the named checks.
- The static record-space rasters of the first capture are RETIRED from the
  profile-conformant capture manifest (the format validator forbids image
  rows under a motion profile: every row must be video-located). They
  remain in the attempt workspace and the evidence store as ADDITIONAL
  evidence and remain rendered as receipt tables in REPORT.md; the report
  discloses the retirement.

## A5. Honesty note

The scene of record is the DECLARED SURROGATE CPU walk scene (its own
module docstring and the W04 certificate say so): the replay shows the
sealed line's real physics — com advance, pad stance/swing, contacts,
commands, reflex trips — at the 300 Hz tick. No claim about the C++ engine
or the adopted assembly is made or implied; the native visual walk claim
belongs to the W07 runtime-consumption card.
