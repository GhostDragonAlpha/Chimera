# ONT-U01 report — controls/motion-profile qualification

**Card**: ONT-U01 "Map gameplay input to the existing command seam"
(planning U01, group "Player controls and camera", scope core, calculation
C12). **Done_when**: "Input emits bounded speed/heading commands at the
existing 20 Hz boundary, without state teleportation". **Profile**:
`controls`, kind `motion` (visual + numerical evidence required).
**Attempt**: `243e4030e63d47059cb2b8eb3fe98082`, agent
`arrival-def19617206b427aa7b8a40d66b59f72`, criteria
`7c54e8356f287c08e694fc7455d64b31e1d0d295a1835d921f8163fa39b2fa62`.

## 1. Reconcile (records reused, nothing duplicated)

- The command seam EXISTS and is pinned: at play commit `f30f2224` the seam
  module `tools/science_funnel/typeb_export/command_record.py` is
  `6771175933ad20ac6d20c360df96f6a9729a56deb31c58a13be5e76e1cc4355e` (the
  versioned CommandRecord v1 + V1FamilyAdapter projection law; 20 Hz decision
  clock over 300 Hz physics, HOLD_TICKS 15, in-band ceiling 0.763625 m/s).
- M-U01 is ALREADY IMPLEMENTED and integrated: play commit `8550b634`
  ("U01 integrated — input mapper on the real CommandRecord v1 seam";
  ancestor of the pinned head) added
  `tools/monkey_campaign/product/input_mapper.py` — at `f30f2224` it is
  `7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d02720ac970b42cfe6b44` — THE
  QUALIFIED SUBJECT — plus the original frozen prereg (`0aadc3cd…`),
  discovery note (`38efdf39…`), falsifier tests (`95f44e90…`) and their GREEN
  receipt 26/26 (`00c73e34…`), all recovered read-only via
  `git -C E:/ChimeraWork/monkey-play-20260924 show f30f2224…:<path>` into
  `reference/` (hash-asserted at probe import; play worktree untouched at
  HEAD `8d16d3c1`).
- Dependencies: ONT-P01 and ONT-P03 are DONE with qualified winners
  (lead-verified publications; P03 criteria `1fcf0eea…` lead-verified READY
  with 5/5 hashes ok in lead-verify-20260926; P01 criteria `395fc0d6…`
  ACCEPTED with worker reviews PASS — see the assignment packet dependency
  receipts). No dependency blocks this card.
- Camera referent: `follow_camera.py` `d61347f0…` (U02's pinned engine eye/up
  laws, 45 deg FOV, declared obstacle model) — used as the declared camera
  referent, unmodified.
- The MISSING work (this candidate): the controls/motion-profile
  QUALIFICATION — the frozen probe, trace, capture and camera manifest; the
  preserved U01 records are headless falsifier receipts with no
  controls-profile camera evidence.

## 2. Preregistration (frozen before execution)

`PREREGISTRATION.md` was written and frozen BEFORE the probe or capture ran
(first probe run `2026-09-26T13:00:35` per runtime_receipt; this file is
committed before any evidence artifact). It freezes the timeline, the nine
checks, the three views, the obstruction construction and the falsifier.

## 3. What was measured (evidence/numerical_receipt.json, 9/9 GREEN)

Probe: `controls_profile_probe.py` — CPU-only, headless, deterministic
(injected integer milliseconds only; the REAL pinned `InputMapper` +
`CommandRecord`/`V1FamilyAdapter` + `FollowCamera`; recording doubles only
for the seam sink and the camera client). Scripted timeline 0..3000 ms on the
mapper's own 50 ms grid (61 trace rows, 40 records) exercising controls
(W/A/D + mouse steering), the mid-interval press, both steering clamps
(±1.6 rad/s), release decay, FOCUS LOSS (`release_all@1050`), reconnect,
the camera-only window (1500..1800) and the named refusals (Shift/Space).

- C1 bounded + no-teleport: 5000 seeded randomized schedules
  (seed 20260926), 117,142 fuzz records — ZERO out-of-bounds, ZERO non-emit
  sink calls; scripted records all inside [0, 0.763625] x |yaw| <= 1.6;
  none of the 14 forbidden markers in the subject source.
- C2 the 20 Hz boundary: commanded spans differ by EXACTLY 50 ms; at most
  ONE record per tick; a 500 ms stall yields exactly ONE current-state
  record (no burst) and the grid re-anchors; dense 1 ms clock emits only at
  the 50 ms boundaries.
- C3 release decay: every tail <= 2 records, monotone, <= pre-release speed,
  landing EXACTLY 0.0 by release+100 ms, zero tail-driven emission after.
- C4 focus loss: held set empty at once; tail exactly [0.763625@1050,
  0.0@1100]; no stuck command; reconnect re-arms at the pre-loss rate;
  expiry strictly after 2 intervals (not at +95 ms, expired at +105 ms).
- C5 the existing v1 seam: every record projects through the REAL
  V1FamilyAdapter to commanded_target_velocity_x == v_forward (float64
  passthrough), routed_yaw_rate False, actor conditioning empty; issued_tick
  == t_ms*300//1000 for all 40; decode_v1 round-trip bit-identity sampled.
- C6 no camera-induced body movement: camera-only window has zero input
  events, zero records, body EXACTLY still; body position equals the record
  integral with residual 0.0 at EVERY tick; max per-boundary step
  0.03818125 m == v_max*dt (no teleport); all 36 camera writes carry exactly
  the 8 declared camera fields on the single /camera route.
- C7 obstruction declared, target readable: the measured occlusion ray
  (pinned `FC.ray_clear`) is BLOCKED at every one of the 61 ticks; close
  target distances in [2.20, 2.64] m; anchor center inside the frustum every
  tick; the pillar is drawn in front (declared, never concealed).
- C8 remap is data (the observation clause): a bindings remap (I/K/J/L)
  emits identical values with identical type/version/bounds/clock and
  bit-identical adapter projections; the module's imports are exactly
  stdlib + the seam record — no retraining surface exists.
- C9 timing chain bound: issued_tick chain exact for every record;
  press-to-first-record gaps measured in [0, 50] ms (the mid-interval press
  at 1975 first emits at 2000, a 25 ms gap) — C12's "50 ms command interval,
  not an end-to-end latency guarantee" is measured, not just declared.

### Honest fired sub-clauses (3, recorded in prediction_deviations; laws green)

1. C3 at release t=700 and t=1050: the frozen ">= 300 ms of zero emission"
   number is not met because the FROZEN TIMELINE itself schedules the next
   input event 100-150 ms after the zero; the resumed records come from that
   new press (a new grid) — zero tail-driven records. The tail laws
   (<= 2 records, monotone, exact 0.0 deadline) are green.
2. C6a "camera writes are observed" in the window: the deadband-honest
   camera had already settled (0 writes inside 1500..1800; 36 on the run);
   the camera surface still cannot carry a body command (exact 8-field
   writes) and the body-stillness/record-silence laws are green.

## 4. Runtime and visual evidence

- `evidence/trace.jsonl` `1624fded79cde3f0def7caf29b409d025cc869aa4468da99b0
  55c93fcc2fa3aa` — 61 rows, byte-identical on rerun (run A == run B).
- `evidence/capture.mp4` `a51fcbc84390047c0eff7253c86577a132c0a1cad0e58fda42
  30d444a065ba16` — 640x360, 366 frames @ 20 fps (18.4 s), ffmpeg libx264
  yuv420p bitexact threads=1; BITEXACT rebuild reproduces the identical file.
  Three declared views, each rendered as a diagnostic segment AND a clean
  segment (clean frames are their OWN pixels — no diagnostics at all):
  `normal follow-camera distance` (REAL pinned FollowCamera applied
  solution, recorded each tick), `obstructed and close-target views` (frozen
  through-pillar construction, measured occlusion ray per tick), `repeatable
  inspection side view` (engine side bookmark radius 12 / theta pi/2 /
  phi 0.3, identical all 61 samples).
- `evidence/capture_manifest.json` `513d65488527b047b83ec92911f88cbbf645c43b
  e5e7b9df7e0c819e133cacc9` — chimera.visual_capture_manifest.v1, profile
  `controls`, 3 views x diagnostic+clean pairs, trace-bound state binding,
  all 16 profile camera fields present (frame monkey_session_world_yup_m,
  metres, right-handed, quaternion wxyz camera->frame, +Z forward / +Y up,
  near/far 0.1/200, 640x360, 16:9, perspective 45 deg vertical FOV, samples
  covering tick_interval [0, 60] exactly). VALIDATED in-process with the
  campaign's own `visual_gate.verify` against `card_task.json`:
  `structurally_valid: true` (including this qualification receipt's
  camera/visual entries).

### HONEST BOUNDARY (declared in PREREGISTRATION, receipts and here)

The capture pixels are a deterministic CPU visualization of the recorded
headless command-seam trace of the qualified subject (the mapper and the
seam are headless by construction). They are NOT native engine frames, and
no native playable-runtime claim is made: that integrated checkpoint remains
with the integration lane. The body referent is probe-owned and declared
(positions are OUTPUTS of records; the heading integration of the carried
yaw demand is a declared referent preview — the v1 adapter routes yaw
NOWHERE, measured in C5). Structural manifest validation does not decode
pixels or authenticate physics; independent capture review remains required.

## 5. Tests

- `python -B tools/monkey_campaign/contributions/ONT-U01/controls_profile_probe.py`
  -> 9/9 checks PASS (exit 0), all-green receipts written.
- `python -B -m unittest test_controls_profile_probe -v` (cwd
  contributions/ONT-U01) -> 11/11 OK.
- Determinism: probe rerun trace byte-identical; capture rebuild bit-exact.

## 6. Artifacts (all inside this attempt checkout)

| file | sha256 |
|---|---|
| PREREGISTRATION.md | see §7 commit (frozen first) |
| card_task.json | (frozen card contract; gate-verified) |
| controls_profile_probe.py | (candidate probe) |
| capture_build.py | (candidate capture) |
| test_controls_profile_probe.py | (candidate suite) |
| evidence/trace.jsonl | 1624fded79cde3f0def7caf29b409d025cc869aa4468da99b055c93fcc2fa3aa |
| evidence/runtime_receipt.json | c4fbfc8e6cce287237689c0bbbaabc1393c26c7eb913b83322280b8bece7e58b |
| evidence/numerical_receipt.json | 6a10de37b60cce7558f5f92265d67667c7450ea0b9ebe03bea641bd8fae6e0cd |
| evidence/capture.mp4 | a51fcbc84390047c0eff7253c86577a132c0a1cad0e58fda4230d444a065ba16 |
| evidence/capture_manifest.json | 513d65488527b047b83ec92911f88cbbf645c43be5e7b9df7e0c819e133cacc9 |
| evidence/capture_receipt.json | b5c4ab42b6b42cfd01a5f8711fd43cda412b178463a1c83e76481a9bee5c2437 |
| reference/ (7 pinned files) | hashes asserted in probe + receipts |

## 7. Publication and remaining gates

Candidate: local commit on `branch-7` in this attempt checkout (base
`c525b82c7c3ce0128565424764293a3c85811ab3`), NOT pushed; lead publishes to
`review/ONT-U01` per LEAD_SERIALIZED policy. REMAINING GATES: (1)
independent worker review of this candidate; (2) lead ACCEPTED review must
pass `qualification_receipt.json` with head_sha set to the EXACT reviewed
head (the in-tree copy ships null + binding note); (3) the native integrated
playable-runtime/visual checkpoint stays with the integration lane (this
capture is a declared CPU visualization, not native frames). writes_stopped:
task tree untouched after the candidate commit.
