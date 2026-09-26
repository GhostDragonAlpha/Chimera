# PREREGISTRATION — ONT-U01 REAL command-boundary/receiver run (correction leg)

Correction for lead CHANGES_REQUIRED on #147 at
`9ad277d73268476a51809becc36c021e020d8d35` (finding msg-6764166dfb7b4a40b59fab6120243ed9,
also delivered msg-e5fc4f0de8af4f1892c538860bf164b8): the component probe's
body referent is an integral of the emitted records, so it cannot witness
no-teleportation. THIS file is written and frozen BEFORE the real run below
executes (this commit precedes every `evidence/real/` artifact). The driver
`real_seam_session.py` implements EXACTLY the frozen phases, checks and
views; any misprediction is recorded FIRED in
`evidence/real/numerical_receipt_real.json.prediction_deviations`, never
smoothed.

Attempt `29bb1ccc4ea449d7ba2524a441d0cc49`, agent
`arrival-b35169cde2d04886afbeefeef25bd8cf`, criteria
`7c54e8356f287c08e694fc7455d64b31e1d0d295a1835d921f8163fa39b2fa62`.
Established pattern (READ-ONLY reference, never written): the accepted
ONT-X02 integrated-session work, attempt workspace
`E:/ChimeraWork/monkey-coordination/kanban-attempts/ONT-X02/35676f7dcb9f4ceea1c2fc41fbe45aa2`
(pinned playable_slice @ `8550b634` served by its own `slice_server.py`
owning a real native `chimera_engine.exe` built from the pinned engine
source; headless Chrome channel `chrome` driving the served page; real
PID/port/process evidence; exe `a9964009`).

## THE DEMAND BEING ANSWERED (the finding, verbatim core)

"Supply a bounded real command-boundary/receiver run with independently
observed body state and corresponding camera-pinned capture, or retain this
as component evidence with qualification incomplete. No trained gait,
climbing, new model, or full-game completion is demanded. Preserve original
captures as explicitly synthetic; do not relabel them."

## WHAT IS REAL IN THIS RUN (and what is not — declared in advance)

REAL: the pinned playable-slice application reconstructed byte-exact (raw
git blobs, no EOL smudge) from play pin `8550b634ebd7034bb8873eed41d8bdce4d3843d0`
into THIS attempt's scratch; a native `chimera_engine.exe` built for this run
from the pinned `ChimeraEngine/engine` sources of the same commit (recipe:
`cmake -S . -B build -G "Visual Studio 17 2022" -A x64; cmake --build build
--config Release`; toolchain cmake 4.2.1 + MSVC 14.44.35207 + Vulkan SDK
1.4.328.1); the `slice_server.py` process that boots and owns the engine
(free-port law, mesh_import of the real body, gravity, settle); the served
page in headless Chrome channel `chrome` (fallback bundled chromium recorded
as a deviation) — key events traverse the browser's real input pipeline into
the page's real `keydown`/`keyup` handlers; the REAL pinned `InputMapper`
(`7a36a45e`) + CommandRecord v1 seam (`67711759`) + `V1FamilyAdapter`/
`decode_v1`, imported byte-exact from this contribution's hash-asserted
`reference/` subtree inside the real driver process; the engine's own HTTP
state/frame path (`/tick_state`, `/api/snapshot`, `/verts`, `/frame`).
NOT REAL (declared): the automation channel delivers the key events
(Playwright keyboard) and one additive in-page hook (`page.evaluate`) mirrors
the page's received events to the driver — the pinned page file is not
edited; the recording sink stays `MockSink` (records every seam call); the
driver process hosts the seam because the pinned app has no V1 ingestion
route (measured in R5, predicted missing).

## FROZEN PHASES AND CHECKS

- **R1 REAL BOOT.** slice_server `--no-browser --engine-exe <built exe>
  --port 0`; exactly one `chimera_engine.exe` child of the server PID;
  `/api/health` `world_booted`; scene `settled` at the standing start with
  `start_state_sha256` recorded. Falsifier: no engine child, boot timeout,
  or no settle.

- **R2 OBSERVER VALIDATION (control, anti-dead-sensor).** The page's own
  SPACE key (300 N real press through the page handler → `/api/press` →
  engine `/tick_touch`) must produce an OBSERVED transient in the
  independent `/tick_state` samples: predicted max |root_vy| > 0.01 m/s and
  max |root_y − pre-press rest| > 1e-3 m, returning to the rest value
  afterwards (within 5e-4 m when settled). Falsifier: no observed transient
  (the observation channel would be blind and R4 meaningless).

- **R3 REAL INPUT AT THE 20 Hz COMMAND BOUNDARY.** Real key events (page
  pipeline, R-prefixed hook) feed the REAL pinned mapper in the driver
  process; a real monotonic wall-clock loop calls `mapper.tick(now_ms)`
  every ≤5 ms; every emitted CommandRecord is logged (wall time, issued_tick,
  v_forward, yaw_rate) into `command_stream.jsonl` at emission time. Frozen
  timeline (real-clock seconds from stream start; W/A/D only — they are
  UNBOUND on the pinned page, so no page action collides; S/arrows are page
  keys and are not used as mapper input):
  t=0.0 `W` down; t=1.0 `A` down; t=2.0 `A` up; t=3.0 `D` down; t=3.5 `D`
  up; t=4.0 `W` up (decay); t=6.0 `W` down; t=7.0 real page BLUR event →
  `mapper.release_all`; t=10.0 `W` down; t=12.0 `W` up (decay); stream ends
  t=16.0 (+4 s tail observation).
  Predictions: every |v_forward| ≤ 0.763625; every |yaw_rate| ≤ 1.6; held-W
  emission gap 50 ms ± 15 ms wall jitter; first decay boundary after `W` up
  strictly below the last held rate, second decay boundary EXACTLY 0.0,
  silence after; same for the blur release_all; idle emits nothing; records
  only ever leave through `sink.emit` (the sink log contains ONLY
  ("emit", record) entries).

- **R4 INDEPENDENTLY OBSERVED BODY vs THE COMMAND STREAM (the
  no-teleportation law, non-circular).** The body state is read ONLY from
  the engine's own state/frame path: `/tick_state` sampled every 40 ms
  (ts_us, ticks, root_y, root_vy — the engine's own monotonic stamps) into
  `trace_real.jsonl`, plus engine-composed `/api/snapshot` FULL36 pulls at
  ~1 s during the stream giving the full vertex set; the body's horizontal
  centroid (mean x, mean z over ALL vertices) is computed from that
  engine-authored geometry, never from any command. Law: for every
  consecutive pair of geometry observations (and every 50 ms window implied
  by the tick samples' root stream), observed displacement must satisfy
  |Δ·| ≤ v_max·Δt + 1e-4 m with v_max = 0.763625 (heading bound n/a to the
  root's observed translation). Prediction (honest): the observed centroid
  displacement over the whole stream is ≈ 0 — the pinned engine has NO
  locomotion consumer for V1 records (R5), so the commanded stream cannot
  translate the body; the law's bound is then trivially satisfied by
  observation, and the INPUT→BODY-EXECUTION leg is recorded INCOMPLETE with
  the missing dependency named, per the finding's own alternative
  ("retain this as component evidence with qualification incomplete").
  Falsifier: any observed per-window displacement exceeding the commanded
  bound, or a discontinuous jump between consecutive engine observations.

- **R5 RECEIVER CAPABILITY MEASURED, NOT ASSERTED.** On the RUNNING engine
  (its real listening port discovered from the engine PID's own TCP
  listeners): (a) `POST /tick_gait {"on":true}` — predicted a real refusal
  naming its block (`body_active`/`unclassified` class); (b) `POST` of a
  command-shaped record to candidate ingestion routes (`/command`,
  `/api/command`, `/tick_command`) — predicted the engine's own 404
  `"not found"`; (c) the served page's own declarations recorded
  (`REALITY/FANTASY` panel naming locomotion pending; banner "real walking
  is pending" on mock carry). This clause RECORDS the real answers whatever
  they are; only an actual consuming route would complete the execution leg.

- **R6 CAMERA-PINNED CAPTURE of the observed behavior.** Real headless-Chrome
  video of the live page for the whole session; the three declared card views
  produced with the page's OWN real camera keys on the live `__CHIMERA_VIEW`
  handle: V1 "normal follow-camera distance" (the page default
  yaw 0.7/pit 0.42/dist 2.2), V2 "obstructed and close-target views" (real
  `+` presses to dist ≤ 1.2 m — the close-target half), V3 "repeatable
  inspection side view" (real `←` presses to a recorded yaw, value logged).
  Per view: diagnostic still (full page) + clean still (the canvas's OWN
  toDataURL in the draw rAF task) + engine `/frame?w=640` PNG through the
  server passthru. Manifest per `chimera.visual_capture_manifest.v1`
  (profile `controls`, kind `motion`, capture = the mp4, trace binding =
  `trace_real.jsonl` + `command_stream.jsonl`, camera fields from
  `__CHIMERA_VIEW` + the page's pinned persp(0.9, a, 0.05, 60)), validated
  with `visual_capture.validate_manifest` AND `visual_gate.verify` against
  `card_task.json`. FROZEN HONEST VIEW NOTES: the real scene contains NO
  obstruction object, so the "obstructed" half of V2 cannot be produced for
  real — it stays component-level (FollowCamera's declared obstacle model,
  original C7) and is recorded as such; no synthetic pillar is drawn into
  real pixels.

- **R7 BOUNDED SESSION AND TEARDOWN.** Stream+capture phases ≤ 10 min wall;
  at end: server process and its engine child terminated (processes THIS
  driver started, by PID), engine port verified closed, zero leftover
  processes of mine. Logs/artifacts only in THIS attempt workspace. No GPU
  compute or training (the engine's render path only — the operator-
  sanctioned real-app run class of the accepted X02 lane).

## PRESERVED (frozen, untouched)

All original component evidence stays byte-identical and stays labeled
synthetic: `evidence/capture.mp4` remains "a deterministic CPU visualization
of the headless command-seam trace, NOT native engine frames";
`PREREGISTRATION.md`, `controls_profile_probe.py`, `evidence/trace.jsonl`,
`capture_manifest.json`, `numerical_receipt.json` unchanged. Nothing is
relabelled; the real-run artifacts live in `evidence/real/` with their own
receipts and never overwrite the synthetic ones.

## WHAT THIS LEG DOES NOT CLAIM

No trained gait, no climbing, no new model, no full-game completion, no
native locomotion execution of the emitted commands (R5 measures the
receiver's real answer), no visual acceptance beyond structural
camera-metadata validation (independent visual review remains the
reviewer's gate).
