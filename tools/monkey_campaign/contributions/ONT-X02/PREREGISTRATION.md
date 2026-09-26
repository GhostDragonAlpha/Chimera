# PREREGISTRATION — ONT-X02 motion-profile qualification (correction)

Card `ONT-X02` (planning X02, verification profile `recovery`, kind **motion**),
attempt `c3f7e9025d5645248f7a7a21f3b47f8a`, agent
`arrival-2350ac01b46a42cc8c3b3aae3d545862`, criteria
`a266d16164e64af20505d4ed5d76a532ebb74f3bd0975cfd548546eaa92c71bf`,
scope `01ea5cddca8d4795caa096945edf7eadcd1f3eb3e2f084fd2ee36a08cae12ef6`.
Written BEFORE the motion probe or capture ran (timestamp of first probe run is
recorded in the runtime receipt; this file is committed first in the candidate).

## Lead correction being executed (inbox msg-f4584623, 2026-09-26)

The reconciliation leg (PR #135 @ `441582bf`, independent worker review PASS
`769540e4a2954868b37de6ce230a504c`) is PRESERVED and reused as the records leg.
The lead requires the MISSING motion-profile qualification over the
ALREADY-IMPLEMENTED M-X02 session_flow: "before/after pinned state through
reload, pause/resume, reconnect/focus loss, safe teardown, with the camera
manifest per visual_gate (position, angle, distance, framing, debug visibility)
and runtime evidence. Reuse the reconciliation as the records leg."

## SUBJECT (identity pinned before execution)

The pinned M-X02 lineage, recovered read-only via
`git -C E:/ChimeraWork/monkey-play-20260924 show f30f2224…:<path>` into this
attempt's `reference/` subtree (byte-exact, hashes below; play worktree left
untouched at HEAD `8d16d3c1`):

- `tools/monkey_campaign/product/session_flow.py`
  `30e06c04dc33da271bfe817d26a4adbf1251f392b224546fc795f307458455cf` — the
  qualified subject (`subject_sha256` of the capture).
- `tools/monkey_campaign/product/input_mapper.py`
  `7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d02720ac970b42cfe6b44` (U01).
- `tools/science_funnel/typeb_export/command_record.py`
  `6771175933ad20ac6d20c360df96f6a9729a56deb31c58a13be5e76e1cc4355e`.
- `tools/monkey_campaign/product/follow_camera.py`
  `d61347f085644e66a5f29ab1e689e2bbd2cd5ff04099856ade70e5da90a791a7` (U02,
  the declared camera referent: engine eye/up/45 deg FOV laws).

## Frozen runtime probe (the ONLY run that produces evidence)

CPU-only, stdlib + Pillow (frame drawing) + ffmpeg (frame packing). One
deterministic headless run drives the REAL pinned `SessionFlow` + REAL
`InputMapper` + `MockSink` + recording world doubles + the REAL `FollowCamera`
over a deterministic session-derived anchor provider. Injected integer
milliseconds only; no wall clock in any asserted path; no window, process,
HTTP, GPU or engine. Fixed timeline (tick grid 50 ms = `INTERVAL_MS`, ticks
0..3300, 67 ticks):

- t=100 unbound `X` press in ATTRACT (named drop); t=150 `Escape` in ATTRACT
  (named no-op); t=200 `Return` press -> PLAYING (the start).
- t=300 `W` held; ticks emit records (v=0.763625); mouse +120 counts at t=550,
  -80 at t=900 (yaw demand).
- t=800 DECLARED focus-loss hook `mapper.release_all(800)` while PLAYING (U01's
  declared focus-loss/disconnect hook, the same surface the flow itself calls);
  decay tail sampled at the next playing boundaries; t=1000 reconnect press
  `W` (fresh grid per U03 clause 4).
- t=1450 `W` re-pressed (mid-press pause setup); t=1500 `Escape` -> PAUSED with
  the quiesce; ticks t=1550..1850 suspended (zero records, zero mapper calls).
- t=1900 `R` from PAUSED -> RESTART: `release_all` + `World.boot` exactly once,
  -> PLAYING. Per-boot state resets are the DECLARED boot semantics
  (boot_standing_start): the provider resets the anchor to the origin after the
  boot call — this models the declared referent, never a probe-side teleport.
  Before/after pinned-state vector compared (held keys, anchor, bookmark pose,
  boot delta, teardown log).
- t=1950 fresh `W` press; ticks to t=2550 (records on fresh keys only).
- t=2600 `R` while PLAYING (named no-op, zero world calls — reset only through
  pause); t=2650..2700 zero-event playing ticks (clock advance transitions
  nothing); t=2750 `Escape` -> PAUSED; t=2800 `Return` -> RESUME (no boot).
- t=2850 `W` held; ticks to t=3150; t=3200 `Q` -> EXITED (teardown exactly
  once, terminate->wait->kill); t=3250 second `Q` (named drop); t=3300
  post-exit key/mouse/tick (all named drops, mapper log frozen).

Every tick is appended to `evidence/trace.jsonl` (tick id, t_ms, state, flow
events incl. drops/quiesce/restart/teardown, held keys, records, cumulative
world+mapper call logs, applied camera pose for both views).

## PREDICTION (measured by the probe; each clause is a numbered check)

1. reaches play key-only: `Return@200` -> PLAYING; the module's public mutators
   are exactly key/mouse/tick (no start/pause/restart method exists).
2. pause without developer commands: `Escape@1500` -> PAUSED with quiesce
   (release_all@1500); zero mapper events while paused; every paused tick
   emits zero records (decision clock suspended).
3. resume tail law: the mid-press pause leaves at most 2 post-resume records,
   each <= pre-pause speed, landing EXACTLY 0.0, then silence; the focus-loss
   tail at t=850/900 shows the same two-sample law mid-play.
4. reconnect/focus loss: after `release_all@800` the held set is empty, the
   reconnect press re-arms a fresh grid, records resume at the pre-loss rate
   (0.763625), no phantom keys, no replayed tail.
5. reset is an explicit user action: `R@1900` (from PAUSED) world contact is
   EXACTLY [release_all, boot x1]; `R@2600` while PLAYING is a named no-op with
   zero world calls; zero-event clock advances never transition the flow.
6. before/after pinned state through reload: pre-restart (t=1850) vs
   post-restart (t=1900) pinned vector matches (held ∅==∅, anchor at the boot
   origin both sides, bookmark camera pose identical, boot count delta == 1,
   teardown log still empty); after the reload records come only from
   post-reload presses (no stale commands replayed).
7. safe teardown: `Q@3200` -> EXITED with teardown exactly once, recorded
   terminate->wait->kill in that order; EXITED is terminal (second `Q` named
   drop; teardown log unchanged); after exit the mapper is never called again.
8. resource containment: total world contacts for the whole run are exactly
   boot x1 + the teardown triple; zero undeclared world attribute attempts
   (strict recording world); zero records attributable to non-playing ticks.

## Frozen visual capture (from the SAME trace; no second run)

One deterministic video `evidence/capture.mp4` (640x360, 134 frames = 2 views
x 67 ticks, 20 fps, ffmpeg libx264 yuv420p bitexact), rendered by
`capture_build.py` from `trace.jsonl` through the declared cameras:

- view `matched before/after camera bookmark` (seconds [0.00,3.35]):
  `fixed_bookmark` camera at the engine's default bookmark (radius 12,
  theta 0, phi 0.3, target origin) — identical pose all 67 samples; the frame
  pair shows the matched before/after reload states.
- view `normal follow view during recovery` (seconds [3.35,6.70]):
  `sampled_trajectory`, interpolation `recorded_each_tick` — the REAL pinned
  `FollowCamera`'s applied solution per tick (radius/theta/phi/target ->
  eye/up via the pinned engine laws, 45 deg vertical FOV).

Each view is a diagnostic+clean pair binding the same trace sha; diagnostic
rows carry the three profile layers ("state and tick IDs", "active
skill/contact labels", "resource/session diagnostics") with stable tag
bindings; clean rows carry the scene only (depth-tested, no diagnostics).
Camera fields: frame `monkey_session_world_yup_m`, right-handed, metres,
quaternion_wxyz_camera_to_frame, forward +Z / up +Y, near/far 0.1/200,
resolution 640x360, aspect 16:9, perspective 45 deg fov, samples covering
tick_interval [0,66] exactly. The manifest is validated in-process with the
campaign's own `visual_capture.validate_manifest` + `visual_gate.verify`
against the card's frozen profile.

HONEST BOUNDARY (declared up front): the pixels are a deterministic CPU
visualization of the recorded session trace of the qualified headless subject
(the flow is headless by construction); they are NOT native engine frames. The
integrated native playable-runtime checkpoint V08 remains with the integration
lane exactly as the preserved reconciliation recorded. This capture qualifies
the task-owned subset (session flow + input gating + declared camera laws),
which is what the lead's correction scopes ("over the ALREADY-IMPLEMENTED
M-X02 session_flow, pinned f30f2224 lineage").

## FALSIFIER

Any probe outcome deviating from checks 1-8 fires; any camera manifest field
that disagrees with the trace (position, distance-to-target, orientation,
sample coverage, bookmark stability), any clean view containing diagnostics,
any required diagnostic layer missing, any stale/replayed command after
reload, any second boot, any teardown ordering other than
terminate->wait->kill, any mapper event after exit, any leaked owned resource,
or any claim of native-engine pixels fails this correction and reopens the
card. Editing the pinned sources (any reference hash drift) fails.

## BOUNDS

CPU-only; stdlib + Pillow + ffmpeg on rendered frames; no GPU, no engine
launch, no browser, no network (github.com reads excepted); <= 16 MiB new
output (the video is <= 6 MiB); all writes inside this attempt workspace and
its prepared checkout; E:/PythonChimera and the play worktree read-only.
