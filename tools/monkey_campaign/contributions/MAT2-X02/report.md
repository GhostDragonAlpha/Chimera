# MAT2-X02 — start / pause / session restart flow (app-level wiring, motion-qualified)

Worker: arrival-7d28ea9afd7f4ce5819f3aa13ce355e0, attempt 74bc0ad345074c429272982299a76f4e,
branch-5 (local), base origin/astra/gait-capture 97993cbe (the MAT2-P01 merge).
criteria_sha256 e50bf1e89689aac419c95c1b3a8ce02bb0f5ca5b3c67cf50b575662c0bd63c20.
NOT pushed; lead-serialized publication to review/MAT2-X02.

## What this attempt implements (the first unmet clause)

The done_when is "Player reaches play and can pause/restart/exit without
developer commands; reset is an explicit user action." The pinned SessionFlow
module (play f30f2224, sha 30e06c04, recovered byte-exact) implements the
four-state flow, and the archived ONT-X02 integrated run proved restart on the
real app — but MEASURED as missing integration (M1): the app imports neither
session_flow nor input_mapper and has no pause/exit/start control; the page
binds no Escape/Q/Enter. THAT missing task-owned behavior is what this
attempt implements:

- `session_app.py` — binds the pinned SessionFlow to the pinned World lifecycle
  seam (restart_scene=World.boot, teardown=World.shutdown_engine), exactly the
  module's own prescription. FOUR additive routes only:
  GET /api/session, POST /api/session/key, POST /api/session/tick,
  GET /session_overlay.js. The served page is the PINNED index.html bytes plus
  EXACTLY ONE disclosed script tag (verified byte-law in tests); every legacy
  route forwards to the pinned handler unchanged. RecordingSink is session
  diagnostics (archived M4 stands: no locomotion consumer is fabricated).
- `wired_main.py` — runs the PINNED slice_server via lazy Handler substitution;
  the shipped main() boot path is untouched; nothing in the pinned tree is
  modified.

## Frozen-first

PREREGISTRATION.md + RECONCILIATION.md committed (2ab42286) BEFORE any
implementation, with reference/ = byte-exact pinned lineage (8 files, sha256s
in reference_manifest.json; all four archived receipt claims re-verified:
session_flow 30e06c04, input_mapper 7a36a45e, session_flow_tests b6ce2bba,
command_record 67711759).

## Verification (what ran, what was observed)

### Unit probe (records class; CPU-only python -B)

- Failing-first: red_run.txt (exit 1 — implementation absent), then
  green_run.txt (exit 0): 12/12 clause checks over the wiring with the
  pinned suite's own doubles (key-only start; pause quiesce + ZERO mapper
  events while paused; exit teardown exactly once, ordered, terminal; restart
  ONLY from paused with exactly one boot; R-while-playing named no-op with
  zero world calls; resume accepts fresh keys; additive-route law; one-tag
  page-injection law).
- F1 bites: f1_mutation_run.txt (exit 1) under the stale-command mutation
  ("tick bypasses the flow gate"); implementation restored and reverified.
- Pinned session_flow_tests re-run at the recovered bytes: exit 0, ALL CHECKS
  PASS (60 checks incl. the 4000-event fuzz).

### Integrated session (MOTION class; the real thing)

`python -B session_a_wired.py` — the reconstructed REAL playable application
(252 files, raw pinned blob bytes, 0 failed — matches the archived extraction
count), a REAL chimera_engine.exe BUILT from the pinned engine source
(cmake 4.2.1 + MSVC + Vulkan SDK 1.4.328.1; exe sha256
3ea54423059d05f5badb1fba42e0fd919d050ca23c3dcb3f6d76329d1f045af2), and a REAL
headless Chrome (channel "chrome") recording REAL video, driving ONLY the
page's own capture-phase keys through /api/session/key:

- 23/23 checks PASS (session_a_wired_receipt.json): boot -> attract -> [Enter]
  playing (mapper records 0->2 while W held) -> settle (real physics) ->
  [Escape] paused with ZERO records across 2.0s of continued ticks (records
  2->2) -> [R] restart from paused: boot_count 1->2, engine PID swap
  (23776 -> 3348), old engine terminated, settled again, scene_sha256
  BYTE-EQUAL across the reload (bc9033bf... — the archived pinned scene
  identity) -> [Q] exit: engine child dead through the app's own
  shutdown_engine path, server port closed, ZERO surviving engines
  (preflight census []).
- Visual evidence (all real pixels): wired_session.webm (real browser video of
  the live app) + transcode wired_capture.mp4; five diagnostic/clean view
  PAIRS (attract / before / paused / after / exited); clean = the canvas's own
  draw-path toDataURL; engine_frame_before/after.png = the ENGINE's own /frame
  renders through the server's /api/frame passthru.
- Camera manifest `wired_capture_manifest.json` (chimera.visual_capture_manifest.v1,
  profile recovery kind motion): the page's own fixed bookmark
  (__CHIMERA_VIEW yaw/pit/dist/target read live; eye+orientation computed with
  the page's own lookFrom formula; persp(0.9, asp, 0.05, 60)), trace-bound
  state bindings, video locators from driver marks.
- VALIDATION: visual_capture.validate_manifest structurally_valid TRUE;
  visual_gate.verify structurally_valid TRUE (against card_task.json, with the
  manifest and the mp4 hashed on disk). visual_acceptance remains false by
  validator law — independent visual review is the reviewer's.

### Measured deviations (recorded AS MEASURED, never tuned)

1. start_state_sha256 differs across the restart (8c040418... -> 83e7c31e...)
   while scene identity is byte-equal and the ROOT stream is identical
   (settled root_y 0.124641 both boots; g_contact_n 135618): the full-vertex
   hash catches the engine's own reflex-breathing phase at capture instant.
   The prereg compared it "as measured"; recorded FIRED in the receipt. (The
   before-boot hash equals the archived run's 8c040418 exactly.)
2. Prior run (console preserved: session_a_wired_console_run3_fired_
   console_error.txt) measured ONE transient console error
   (net::ERR_NO_BUFFER_SPACE); the final run measured zero. Both records kept.
3. Two driver defects were fixed during bring-up (Playwright video API arg;
   an undrained stderr PIPE that stalled the pinned server's request logging
   ~8s after page load — a harness artifact, not app behavior). All console
   outputs are committed.

## Honest boundaries

- Evidence class: the integrated artifacts are MOTION-class (real runtime,
  real browser input path, real engine). Unit outputs are RECORDS-class and
  are labeled as such in qualification_receipt.json; nothing is relabeled.
- NOT claimed: V08 checkpoint acceptance (lead's decision); human player
  acceptance (operator receipt); a locomotion consumer for the mapper record
  stream (archived M4 stands).
- The play repo and live worktree stayed read-only; nothing outside the
  attempt workspace was written; no branch was pushed.

## Commands

- python -B test_session_app.py  (exit 0; 12/12)
- python -B reference/tools/monkey_campaign/product/session_flow_tests.py
  (exit 0, ALL CHECKS PASS)
- python -B extract_pinned_app.py --dest scratch/run/play --manifest ...
  (252 files, 0 failed)
- cmake -S scratch/run/play/ChimeraEngine/engine -B scratch/build &&
  cmake --build scratch/build --config Release --parallel  (exit 0)
- python -B wired_main.py (via session_a_wired.py)  (23/23 checks)
- python -B assemble_qualification_receipt.py &&
  python -B build_capture_manifest.py --evidence evidence/integrated
  (validate_manifest TRUE; visual_gate.verify TRUE)
