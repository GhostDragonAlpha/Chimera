# PREREGISTRATION — MAT2-U04 input-settings motion qualification

Card `MAT2-U04` (planning U04, verification profile `controls`, kind
**motion**), attempt `d9ce4334674e435d95b9cb95373327e5`, agent
`arrival-1390bce44d204c709636097a9613e84f`, criteria
`192ca43f061c4b6b2763d11213e0246ea075c3f62e6948948ba8c64213bf5180`, scope
`cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097`,
definition raw sha `57ded6eb2f2cc6aa914d6f68c8efb55b215790fc7a9d0baa5dfd2c49fd1465c1`
(byte-identical to the archived ONT-U04 card definition; only the scope digest
differs). **Written BEFORE the probe, the capture builder or the records-leg
battery first ran in this attempt.** The freeze commit lands first (this file,
`card_task.json`, the pinned `reference/` bytes, the preserved `records_leg/`
snapshot and the contribution-local `.gitattributes` `* -text`); the probe and
builder are committed in a later commit of this same attempt.

Done-when (verbatim): "Sensitivity, inversion and bindings needed for the
selected controls work and persist." Observation (verbatim): "Keyboard/mouse
baseline; controller support is an explicit product decision." The profile is
kind **motion**, so this attempt delivers the motion complement over the
ALREADY-IMPLEMENTED pinned product modules: actual through-the-interface runs
demonstrating sensitivity, inversion and rebinding working AND persisting
through save / restore-in-a-fresh-process / reload, plus a
`chimera.visual_capture_manifest.v1` camera manifest whose identity envelope
carries the CONTRACT's task_id `U04`, bound to this attempt's committed bytes.

## RECONCILIATION FIRST (what already exists — reused, not re-implemented)

1. **The subject is implemented and pinned.** `input_settings.py` is the U04
   integration of the monkey-play lineage: integration commit `4699b37d`
   ("monkey-play: U04 integrated — input settings ..."), byte-identical at the
   pinned play head `f30f2224663324e9374b076938c56672febf4082` (branch
   `monkey-play-20260924` tip). Before this file was written, this attempt
   re-verified via read-only `git show f30f2224:<path>` from
   `E:/ChimeraWork/monkey-play-20260924` (and at `9afbddcd` and `4699b37d`,
   all three identical):

   | pinned module | sha256 | role |
   |---|---|---|
   | `tools/monkey_campaign/product/input_settings.py` | `8d1a49d63f85164f3b9ac27f3387237d0a0790f68075e2455a74e2caa485a2f1` | **THE QUALIFIED SUBJECT** (capture_context.subject_sha256) |
   | `tools/monkey_campaign/product/input_mapper.py` | `7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d02720ac970b42cfe6b44` | exercised (the U01 seam consumer) |
   | `tools/monkey_campaign/product/input_settings_tests.py` | `5845178ab12a69773e6b4bcdf2e8aa0b9fd144cddff7ee1e89204e0c5dd3720f` | the pinned falsifier battery (records leg) |
   | `tools/science_funnel/typeb_export/command_record.py` | `6771175933ad20ac6d20c360df96f6a9729a56deb31c58a13be5e76e1cc4355e` | command record v1 seam |
   | `tools/science_funnel/__init__.py` | `c5a9f9b162177ec18d127edb799bbfe1ba08442ed95c72f8f0947f9d64618b19` | package marker |
   | `tools/science_funnel/typeb_export/__init__.py` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | package marker (0 bytes) |

   All six are recovered byte-exact into `reference/` (hashes asserted at probe
   import; drift aborts before any check runs). No pinned byte is edited.

2. **The records leg is preserved and REUSED.** The archived ONT-U04 candidate
   (PR #182, head `939e8e6f725d162b18e8998aa725ad24f53fdb36`) carries the
   records/proof qualification: 13 COMPLETE PASS worker reviews reproduced its
   pins, battery, lineage receipts and 14-file diff scope; lead
   CHANGES_REQUIRED `msg-b5edae96` refused it SOLELY for missing motion-profile
   evidence and said the records leg "is verified and PRESERVED ... nothing
   needs re-running" and "Reuse the current PR as the records leg." This
   attempt fetched the reviewed head from the origin remote
   (`git fetch origin pull/182/head` == `939e8e6f...`) and snapshots its
   14 files verbatim into `records_leg/ONT-U04/` (frozen pre-run:
   `run_falsifiers.py` = `3a6784952b92455857eea6b50e8e293182e95f954e9964380aecd7b487eef996`,
   archived prereg = `26ba5c04f52ff2d67a6b20fd48b2b32231e5ababb50d0eb8833cad204673bb5d`;
   its `reference/` copies are byte-identical to this attempt's `reference/`
   — cross-checked at freeze time). This attempt RE-RUNS the unmodified
   pinned battery at this scope for a fresh hash-proofed receipt.

   **PREDICTION R (records leg):** `python -B
   tools/monkey_campaign/contributions/MAT2-U04/records_leg/ONT-U04/run_falsifiers.py`
   exits 0 with its internal hash proof passing and `VERDICT: GREEN`,
   33 PASS / 0 FAIL, within its 120 s / 16 MiB bounds (the battery is the
   pinned 5845178a file, unmodified).

3. **The motion complement is THIS attempt's new work** (the archived
   candidates carried none — that is exactly why the lead refused PR #182).
   Dependency MAT2-U01 is DONE with a qualified merged winner (PR #197,
   merged `ebdfda61`); its frozen seam (20 Hz boundary, DEFAULT_BINDINGS,
   `sensitivity` delta-scale, CommandRecord v1) is consumed here, never
   amended. The modules are NOT yet on `astra/gait-capture`; integration and
   publication remain lead-serialized — this candidate is qualification
   evidence over the pinned lineage (same delivery shape as the merged
   MAT2-U02 candidate: no `proposed.patch`).

## FROZEN SUBJECT INTERFACE (the pinned module's own surface, consumed only)

`load_settings(path) -> LoadResult(settings, status, refusals, path)`;
`save_settings(settings, path) -> SaveResult`; `canonical_bytes(settings)`;
`default_settings()`; `apply_settings(settings, mapper)` (writes ONLY
`mapper.bindings` and `mapper.sensitivity = settings.signed_sensitivity()`);
`configured_mapper(sink, settings)`; `InputSettings.signed_sensitivity()`,
`.to_document()`. The mapper's own numbers are imported, never redeclared:
`INTERVAL_MS=50`, `OMEGA_MAX_RAD_S=1.6`, `SENS_RAD_PER_COUNT=0.002`,
`V_MAX_IN_BAND_M_S=0.763625`, `RELEASE_DECAY_MS=100`, `PHYSICS_HZ=300`,
`SOURCE_ID="u01_input_mapper"`, `DEFAULT_BINDINGS`, `ACTIONS`, `REFUSALS`.
Derived ceiling: `SENS_YAW_MAX_RAD_PER_COUNT == OMEGA_MAX_RAD_S * INTERVAL_MS / 1000`
(== 0.08 up to float identity of that expression). Mouse counts injected as
integers; every boundary consumes them via the mapper's own clamp.

## FROZEN TIMELINE (injected milliseconds; nothing else is injected)

One parent run, tick grid every 50 ms from 0 to 19500 (ticks 0..390,
`tick_interval [0, 390]`). All events at tick multiples. Settings events use
`apply_settings` (the module's declared surface) on the LIVE mapper.

| t (ms) | event | frozen prediction for subsequent boundaries |
|---|---|---|
| 0 | `load_settings` on a DECLARED ABSENT path | status `first_run`, settings structurally == `default_settings()`, NOTHING created on disk |
| 200 | press `W` | every boundary 200..18450 emits one record, `v_forward == V_MAX_IN_BAND_M_S`, `issued_tick == t*300//1000` |
| 250..2450 (45 boundaries) | inject +5 mouse counts each | `yaw_rate == clamp(5*0.002/0.05)` == 0.2 (bit-exact vs the same expression), unclamped |
| 2500 | **S1** sensitivity 0.002 -> 0.008 (4x) | boundaries 2500..5450: `yaw == clamp(5*0.008/0.05)` == 0.8, unclamped; ratio to baseline == 4 within 1e-12 |
| 5500 | **S2** sensitivity -> `SENS_YAW_MAX` (derived ceiling) | boundaries 5500..8450: raw 5*s/0.05 = 8 -> clamp -> `yaw == OMEGA_MAX_RAD_S` EXACTLY (seam bound, no bypass) |
| 8500 | **S3** `invert_yaw = True` (same s) | boundaries 8500..8950: `yaw == -OMEGA_MAX_RAD_S` exactly (sign flip at the clamp) |
| 9000 | press `A` (still `turn_left`) | boundaries 9000..9450: `yaw == 0.0` exactly (+OMEGA key + -OMEGA inverted mouse) — the key path is UNAFFECTED by inversion |
| 9500 | release `A` | boundaries 9500..11450: `yaw == -OMEGA_MAX_RAD_S` |
| 11500 | **S4 REBIND**: `A->turn_right`, `D->turn_left`, add `E->sprint` (coverage of all four selected actions intact) | boundaries 11500..11950 (mouse +5): `yaw == -OMEGA_MAX_RAD_S` |
| 12000 | press `A` (now `turn_right`), mouse paused | boundaries 12000..12450: `yaw == -OMEGA_MAX_RAD_S` — the KEY SIGN FLIPPED with the remap (pre-remap `A` gave +OMEGA) |
| 12500 | release `A`, press `D` (now `turn_left`) | boundaries 12500..12950: `yaw == +OMEGA_MAX_RAD_S` |
| 13000 | press `E` (`sprint`) | `last_trace["refused"]` gains `("sprint", <named reason>)`; boundaries 13000..13450: `yaw == 0.0` (no seam channel) |
| 13500 | **SAVE** `S4` via `save_settings` to the declared path | file bytes == `canonical_bytes(S4)`; two saves byte-identical; directory contains ONLY the settings file (atomic temp+replace leaves no temp) |
| 14000 | **RELOAD (parent)**: `load_settings` -> fresh mapper `M2` | status `loaded`, zero refusals, settings structurally == `S4` (exact equality) |
| 14000 | **RELOAD (child process)**: `python -B child_load_probe.py` — a SEPARATE OS process | child `status == "loaded"`, child settings document == `S4.to_document()`, child replays the FROZEN REPLAY SEQUENCE below and its records are FIELD-EXACT (v_forward, yaw_rate, issued_tick, source, record_version) == the parent `M2` replay records |
| 14000..15950 (40 boundaries) | original mapper, mouse +5 | `yaw == -OMEGA_MAX_RAD_S` — settings persist IN SESSION across the save/reload boundary |
| 16000..18450 | no mouse, W held | `yaw == 0.0` |
| 18500 | release `W` | boundary 18500: decay sample `v == V_MAX` (elapsed 0); boundary 19000: `v == 0.0` exactly; then inert |

FROZEN REPLAY SEQUENCE (parent `M2` and child, identical injected clock):
press `W`@0; press `A`@50; inject +2 counts before each boundary
100,150,200,250,300 (A held: key `-OMEGA` [A=turn_right in S4] + mouse
`clamp(2*(-s)/0.05)` -> `-OMEGA`; total `-OMEGA`); release `A`@350 (boundary
350: mouse only, `-OMEGA`); release `W`@400 (boundary 400: tail v == `V_MAX`;
boundary 450: `v == 0.0` exact; inert after).

FROZEN SETTINGS EVENTS (exact vectors): S1 = (DEFAULT_BINDINGS, 0.008, False);
S2 = (DEFAULT_BINDINGS, `SENS_YAW_MAX_RAD_PER_COUNT`, False);
S3 = (DEFAULT_BINDINGS, `SENS_YAW_MAX_RAD_PER_COUNT`, True);
S4 = (DEFAULT_BINDINGS with `A:turn_right`, `D:turn_left`, `E:sprint`,
`SENS_YAW_MAX_RAD_PER_COUNT`, True). The declared settings path is
`<run_scratch>/monkey_input_settings.json` (a fresh per-run scratch directory;
never a repo path; never the play repo's data directory).

## FROZEN CHECKS N0-N9 (numerical evidence; all must be green; any mismatch is a FAIL and exits nonzero)

- **N0 identity** — reference hashes == the six pinned sha256 at import;
  lineage: play head `f30f2224...`, integration commit `4699b37d` (U04), card
  criteria `192ca43f...`, scope `cb5475f8...`; records-leg snapshot hashes ==
  the frozen values above. Prediction: all equal.
- **N1 first_run** — absent path: status `first_run`, defaults structural,
  scratch listing unchanged (load never writes). Prediction: equal.
- **N2 sensitivity law** — every mouse-carried record's `yaw_rate` is BIT-EXACT
  vs `max(-O, min(O, counts*sensitivity/0.05))` recomputed with the pinned
  constants for that boundary's settings; S1 ratio vs baseline == 4 within
  1e-12; S2 saturates at exactly `OMEGA_MAX_RAD_S`. Prediction: all exact.
- **N3 inversion** — S3 boundaries bit-exact vs recomputed with the SIGNED
  scale; the same +5 counts yields exactly `-OMEGA_MAX_RAD_S` where S2 yielded
  exactly `+OMEGA_MAX_RAD_S`. Prediction: exact.
- **N4 keys unaffected by inversion** — boundaries 9000..9450 yaw == 0.0
  exactly. Prediction: exact.
- **N5 rebinding** — 12000..12450 == `-OMEGA` (A flipped), 12500..12950 ==
  `+OMEGA` (D flipped), `E` refusal named in `last_trace["refused"]`, and a
  coverage-negative file (bindings without any `forward`) refuses with code
  `action_unbound` through `load_settings`. Prediction: all hold.
- **N6 persistence** — file bytes == `canonical_bytes(S4)`; resave
  byte-identical; parent reload `status=="loaded"`, settings == `S4` exactly;
  parent `M2` replay records field-exact == original-phase records for the
  same (settings, physical-input) pairs where the phase used S4; CHILD process
  records field-exact == parent `M2` replay records; child document ==
  `S4.to_document()`. Prediction: all exact (zero mismatches).
- **N7 refusals** — poison documents through `load_settings`: corrupt JSON ->
  `json_corrupt`; wrong schema -> `schema_unknown`; unknown key
  (`"interval_ms"`) -> `key_unknown`; sensitivity 0.16 -> `value_out_of_range`;
  sensitivity 0 -> `value_out_of_range`; sensitivity `true` -> `sensitivity_type`;
  duplicate JSON key -> `key_duplicate`; `NaN` literal -> `not_finite_json`;
  unknown action -> `action_unknown`; each returns defaults + `status
  == "refused"`, and the declared scratch listing is unchanged by every
  refused load. Prediction: code sets match exactly.
- **N8 seam protection** — before/after every `apply_settings`:
  `IM.OMEGA_MAX_RAD_S`, `IM.V_MAX_IN_BAND_M_S`, `IM.INTERVAL_MS`,
  `IM.SENS_RAD_PER_COUNT`, deep copy of `IM.DEFAULT_BINDINGS`,
  `CR.COMMAND_RECORD_VERSION` all bit-identical; `input_settings` ceiling ==
  the derived expression; the mapper's and command_record's module files'
  sha256 unchanged at exit. Prediction: unchanged.
- **N9 trace integrity** — every record: `source == SOURCE_ID`,
  `record_version == CR.COMMAND_RECORD_VERSION`, `0 <= v_forward <= V_MAX`,
  `|yaw_rate| <= OMEGA_MAX`, `issued_tick == t*300//1000`; counts fully
  consumed per boundary (no `steer_without_speed` rows while W is held).
  Prediction: 368 main-trace records (200..18450 = 366, + tail 18500, 19000),
  11 replay records per replay runner (boundaries 0..500), all conforming.

## FROZEN BODY INTEGRATION + CAMERA LAWS (harness-owned, declared here)

Body: X-forward heading zero, Y-up right-handed world, metre units; per tick,
for each record emitted at that boundary: `heading += yaw_rate*0.05`;
`x += v*cos(heading)*0.05`; `z += v*sin(heading)*0.05`. Start (0, 0, 0),
heading 0. This body is the HARNESS INTEGRATION of the real emitted
CommandRecords — it is not a native engine body (see honest boundary).

Declared static scene (rendered, depth-tested): trunk cylinder center
(3.4, -5.0) r=0.5 top=8.0; pole (2.0, 0.2) r=0.3 top=6.0; curb (3.0, 0.1)
r=0.12 top=0.15 — the same declared obstacle set the merged MAT2-U02 capture
used, frozen here as scene dressing only (NO camera-avoidance behavior is
claimed; obstruction avoidance is U02's subject, focus loss is U03's).

Views (the profile's three, content owned by THIS task = settings/input
state):
1. `normal follow-camera distance` — eye = body + (-cos h, 0, -sin h)*3.0 +
   (0, 1.4, 0); target = body + (0, 0.5, 0). Sampled trajectory,
   `recorded_each_tick`, 391 samples.
2. `obstructed and close-target views` — eye = body + (-cos h, 0, -sin h)*1.7
   + (0, 0.95, 0); target = body + (cos h, 0.1, sin h)*0.6. Sampled
   trajectory, `recorded_each_tick`, 391 samples.
3. `repeatable inspection side view` — FIXED bookmark: target (3.4, 0.5,
   -5.0) (trunk), eye = target + (14*cos(0.3), 14*sin(0.3), 0) =
   (16.771275..., 4.137068..., -5.0), distance 14.0 exactly, identical for
   all 391 samples. `fixed_bookmark`.

All cameras: `frame_id "monkey_u04_world_yup_m"`, unit m, right-handed,
orientation `quaternion_wxyz_camera_to_frame` (local +Z forward, +Y up — the
algorithm is unit-tested: rotating (0,0,1) lands on the eye->target forward,
(0,1,0) on camera up), projection perspective, vertical FOV 45 degrees, near
0.1 / far 200.0, viewport 640x360, aspect 640/360. Camera samples are
computed from the SAME trace rows the video renders; both modes of a pair
carry IDENTICAL camera objects bound to the trace sha.

## FROZEN CAPTURE SPEC

One deterministic video `evidence/capture.mp4`: six sequential segments
(V1 diagnostic, V1 clean, V2 diagnostic, V2 clean, V3 diagnostic, V3 clean),
each 391 frames (ticks 0..390) at 20 fps => segment span 19.55 s, total
117.3 s, 640x360, ffmpeg libx264 `-crf 23 -preset medium -flags +bitexact
-fflags +bitexact -x264-params threads=1:ref=4`. **PREDICTION C: building
twice from the same trace reproduces a byte-identical file.** Diagnostic
frames carry exactly the three profile layers (`input/state/tick display`:
settings vector + phase + tick + events + records banner; `camera target and
frustum diagnostics`: target crosshair + frustum edge rays; `selected creature
labels`: `monkey_body` + heading labels) and the six declared label ids
(input_state_banner, tick_banner, camera_diag, frustum_diag, creature_label,
creature_heading); clean frames carry NO diagnostic pixels. Manifest:
`chimera.visual_capture_manifest.v1`, profile_id `controls`, identity envelope
`task_id "U04"`, `run_id "mat2-u04-input-20260927-d9ce4334"`,
`subject_sha256 8d1a49d6...`, `capture_sha256` = the video's sha256,
`tick_interval [0, 390]`; six rows (3 views x diagnostic+clean pairs,
`state_binding {kind: trace, sha256: <trace.jsonl sha>}`, artifact locator
video seconds as segment spans). Validated in-process with the campaign's own
`visual_capture.validate_manifest` AND `visual_gate.verify` against
`card_task.json`.

## FAILING-FIRST FALSIFIER DEMONSTRATIONS (run BEFORE the green run; each must FIRE)

1. **PIN-DRIFT**: flip one byte of a scratch COPY of the probe import target
   (in-place edit + restore of `reference/.../input_settings.py`): the probe
   must abort at import with `PIN DRIFT` BEFORE any check; hash re-verified
   after restore.
2. **SENS-LAW-BREAK**: probe `--selftest` wraps `apply_settings` to halve the
   sensitivity it applies -> check N2 must FAIL.
3. **INVERT-BREAK**: `--selftest` drops the sign of the applied scale -> N3
   must FAIL.
4. **PERSIST-BREAK**: `--selftest` points the child at a tampered settings
   file (sensitivity 0.001) -> N6's child comparison must FAIL.
5. **GATE-NEGATIVE**: tamper one camera sample in a COPY of the manifest ->
   `visual_capture.validate_manifest` must refuse.
6. **BATTERY-NEGATIVE**: flip one byte of a scratch COPY of the records-leg
   reference module -> `run_falsifiers.py` hash proof must abort.

## BOUNDS AND ENVIRONMENT

CPU-only, headless, deterministic: python -B only; no GPU, no engine process,
no network, no desktop input; injected times only (wall-clock durations are
reported, never asserted). Probe bound 120 s wall / 16 MiB stdout; frame
render + encode bounded by the attempt output budget (16 MiB total
contribution; the video is the largest artifact, expected ~2-3 MB).
`--selftest` shares these bounds.

## HONEST BOUNDARY (declared up front)

The capture pixels are a deterministic CPU visualization of the recorded
headless trace of the pinned settings/mapper/seam modules; the walking body in
them is the harness's declared integration of the modules' REAL emitted
CommandRecords. They are NOT native engine frames and make no native-render or
W10 claim. The child-process persistence leg is a REAL separate OS process
(spawned `python -B`), and the battery leg runs the pinned test module
UNMODIFIED; everything else here is component-level qualification of the
pinned lineage. Camera obstruction AVOIDANCE (U02), focus loss (U03), climb
intent (U05) and any native checkpoint (V03/V04) are NOT claimed. No trained
gait, no new model, no full-game completion is claimed or required.

## REMAINING GATES (not claimable by this attempt)

Independent worker review of THIS candidate; lead-serialized publication to
`review/MAT2-U04`; the lead's acceptance sets `independent_review` and
`head_sha` on the qualification receipt (the in-tree copy leaves
`head_sha` null by design — it cannot know its own publication head).
