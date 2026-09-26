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

## 8. CORRECTION (lead CHANGES_REQUIRED msg-6764166d): the bounded REAL
command-boundary/receiver run

The lead's exact-head review of #147 at `9ad277d7` overruled the ACCEPT with
a circularity finding: the component probe's body referent is the integral
of the emitted records, so it cannot witness no-teleportation. This section
supplies the demanded bounded real run; the component evidence above stays,
and the original captures stay EXPLICITLY SYNTHETIC (nothing relabeled).

Frozen first: `PREREGISTRATION_REAL_RUN.md` (sha256
`da5dba00b0cbe24713408e1cf3e4ead834f3edf5fcadbaf14bf7d478e8421b48`,
commit `5751ae10`) was written and committed BEFORE any `evidence/real/`
artifact existed; the driver implements exactly the frozen phases R1-R7.
Established pattern reused read-only: the accepted ONT-X02 integrated-session
work (attempt `35676f7dcb9f4ceea1c2fc41fbe45aa2`).

WHAT RAN (all real; `evidence/real/runtime_receipt_real.json`):
- 252-file raw-blob reconstruction of the pinned playable slice at play
  `8550b634ebd7034bb8873eed41d8bdce4d3843d0` (`pinned_blob_manifest.json`,
  0 failed) and a native `chimera_engine.exe` BUILT for this run from the
  pinned engine source of the same commit (184 source files; cmake 4.2.1 +
  MSVC 14.44.35207 + Vulkan SDK 1.4.328.1; exe sha256 `4bbf2a98d8b2bff6...`
  in `engine_build_receipt.json`; same recipe as the X02 lane's `a9964009`
  build — non-deterministic link explains the byte difference).
- `slice_server.py` (the R1 automated mode) booted and owned the real
  engine: server PID 89148, engine child PID 9532 on 127.0.0.1:62944
  (discovered from the engine PID's own TCP listeners), boot 2.38 s, scene
  `bc9033bf...`, settled standing start `start_state_sha256 8c040418...`
  (byte-equal to the X02 lane's reload state), settled root_y 0.124510.
- The served page in headless Chrome channel `chrome` (no deviation), real
  key events through the page's real handlers; an ADDITIVE in-page hook
  (page.evaluate; pinned page file untouched) mirrored received events to
  the driver.
- The REAL pinned seam imported byte-exact with hash assertion:
  input_mapper `7a36a45e`, command_record `67711759`.

R2 OBSERVER VALIDATION: the page's own SPACE press (300 N, real handler →
/api/press → engine /tick_touch) produced only a sub-resolution transient —
the frozen magnitude guess (max|vy|>0.01, max|dy|>1e-3) FIRED and is
recorded in `numerical_receipt_real.json.prediction_deviations`. The
observer-validation purpose is carried by the measured transient itself and
by the AUXILIARY fall test (the page's own [3], the engine's root-law demo):
observed max |root_vy| 3.896 m/s, peak root_y +0.9103 m, landing back at
root_y 0.1245 — the independent /tick_state channel demonstrably reports
real body motion, and the body returns to the attractor.

R3 THE REAL COMMAND STREAM (139 -> this run 138 records,
`command_stream.jsonl`): real key events (W/A/D — unbound on the pinned
page, so no page action collides) drove the REAL pinned InputMapper on the
real monotonic clock; every record left only through `sink.emit`
(sink log pure), every |v_forward| <= 0.763625, every |yaw_rate| <= 1.6,
held-W boundary gaps 50 ms (one gap of 67 ms — 2 ms outside the frozen
+/-15 ms band — FIRED and recorded: one late boundary, no burst, no lost
record), all three releases decay to EXACTLY 0.0 at the second boundary and
stay silent until the next press (blur → release_all included); every
record's V1FamilyAdapter projection passes `commanded_target_velocity_x`
through bit-exactly and decode_v1 round-trips canonically. issued_tick is
anchored to the ENGINE's own tick counter (4934 → 9459 observed across the
stream).

R4 INDEPENDENT OBSERVATION (non-circular) — `trace_real.jsonl`: the body
state was read ONLY from the engine's own state/frame path: /tick_state at
25 Hz (the engine's own ts_us + ticks + root_y/root_vy) and engine-composed
/api/snapshot FULL36 pulls (~1 s; 249,743-vertex real body), plus the
engine's own /frame PNGs. RESULT: the horizontal centroid of the real body
is BIT-IDENTICAL across the entire command stream (cx -0.0482328534,
cz 0.0783496797, first to last), every root_y step is 0.0, ticks monotonic
— NO TELEPORTATION OBSERVED, under a law bound of v_max*dt+1e-4 per
window. This is the engine's own answer about its own body, never a
reconstruction from the commands.

R5 RECEIVER CAPABILITY (measured, not asserted): the running engine's real
answers — `POST /tick_gait {"on":true}` (compact body; the boolean is parsed
by literal substring) → `{"ok":false,"error":"refused: needs gravity,
stance, classification, pins 13-18, and a sealed feet cell"}` — the engine's
own named refusal; `POST /tick_stance {"on":true}` refused likewise; command-
shaped POSTs to `/command`, `/api/command`, `/tick_command` → the engine's
"Not found" (200-text fallback; no such route); and the page's own
declarations recorded verbatim: "pending: real locomotion (the gait machine)
· physics target 426" and the MOCK mock_carry panel. THE INPUT→BODY-
EXECUTION LEG IS THEREFORE INCOMPLETE and is recorded as exactly that, per
the finding's own alternative ("retain this as component evidence with
qualification incomplete").

R6 CAMERA-PINNED CAPTURE: real headless-Chrome video of the live application
through the whole session (`real_session.webm` → `real_capture.mp4`,
44.2 s, h264 yuv420p 1280x720@25, sha256 `846f0b3281c15abc...`), three
declared views driven by the page's OWN camera keys (+ zoom to dist<=1.2 m;
ArrowLeft side orbit to a recorded yaw), diagnostic stills (full page) +
clean stills (the canvas's OWN toDataURL) + the engine's own /frame PNGs;
manifest `real_capture_manifest.json` per chimera.visual_capture_manifest.v1
(profile controls, kind motion, trace binding = trace_real.jsonl, camera
from the live __CHIMERA_VIEW + the page's pinned persp(0.9,a,0.05,60)),
validated GREEN by visual_capture.validate_manifest AND visual_gate.verify
against card_task.json (structurally_valid true, 6 views, visual_acceptance
false by law — independent visual review remains the reviewer's gate).
Honest view note frozen in advance: the real scene has NO obstruction
object, so the "obstructed" half of view 2 stays component-level (FollowCamera
declared obstacle model, C7); no synthetic pillar is drawn into real pixels.

CORROBORATION: this run's engine /frame PNGs (all three views:
`1ae0b509...`) and the default-camera canvas clean still (`7fe200a4...`) are
BYTE-IDENTICAL to the accepted X02 lane's engine frames and clean still —
the deterministic pinned engine at the same scene/start-state answers with
the same bytes through two independent runs.

R7 BOUNDED SESSION: ~2 min wall; server and engine terminated by PID
(processes this driver started); zero leftover engine processes (verified
globally); logs/artifacts only inside this attempt workspace + checkout.

PRESERVED: `evidence/capture.mp4` (`a51fcbc8...`) and all original probe
artifacts are untouched and remain labeled SYNTHETIC (a deterministic CPU
visualization of the headless command-seam trace, NOT native engine frames);
`PREREGISTRATION.md`, `controls_profile_probe.py`, `evidence/trace.jsonl`
byte-unchanged.

REMAINING GATES (unchanged in kind): independent worker review of this
correction; lead ACCEPTED review with head_sha bound to the exact reviewed
head; the locomotion execution leg (a real consumer of V1 speed/heading
records in the engine) remains with the integration lane.

writes_stopped: the task tree is untouched after the correction commit.
