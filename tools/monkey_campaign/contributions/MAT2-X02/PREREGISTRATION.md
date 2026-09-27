# PREREGISTRATION — MAT2-X02 session wiring (frozen BEFORE implementation)

Card MAT2-X02, criteria_sha256 e50bf1e89689aac419c95c1b3a8ce02bb0f5ca5b3c67cf50b575662c0bd63c20,
verification_profile recovery (kind=motion), checkpoint V08 (downstream milestone,
not a prerequisite). done_when verbatim: "Player reaches play and can
pause/restart/exit without developer commands; reset is an explicit user action."

## Statement

The pinned playable-slice application (8550b634) ships NO player session flow
(archived M1: no session_flow/input_mapper import, no pause/exit control, no
Escape/Q/Enter bindings; the page boots straight into live play). The verified
SessionFlow module (f30f2224, sha 30e06c04) implements the four-state flow
(attract -> playing <=> paused -> exited) but has never been wired into the app.
This attempt implements THAT missing task-owned behavior: an app-level, additive
wiring layer (`session_app.py`) that binds the pinned SessionFlow to the pinned
World lifecycle seam (restart_scene=World.boot, teardown=World.shutdown_engine)
and exposes it to the player through the page, plus the falsifier probes that
qualify it.

## The implementation claim (falsifiable)

An additive overlay module can give the player key-only start/pause/restart/exit
over the real World seam while every pinned legacy route and byte stays intact,
such that:

- every state change is caused ONLY by `SessionFlow.key(...)` (the flow's public
  mutator law); no timer, no transport, no wall clock moves the state;
- while not `playing`, zero mapper boundaries occur (the decision clock is
  suspended; the mapper call log does not grow);
- pause quiesces the mapper exactly like a physical release (`release_all`), and
  resume re-arms a fresh grid (no replayed tail);
- restart is reachable ONLY from `paused` and makes EXACTLY ONE World.boot world
  contact; R while playing is a named no-op with zero world calls;
- exit performs the pinned teardown ordering (terminate -> wait -> kill) EXACTLY
  once and is terminal.

## Frozen predictions (probe level; recorded PASS/FIRE AS MEASURED)

- P1 (unit, CPU): the full done_when clause set over the wiring with strict
  doubles — key-only start; Escape pause with quiesce + zero mapper events while
  paused; Q exit with ordered teardown exactly once to terminal EXITED; R
  restart ONLY from paused with exactly one boot; R-while-playing named no-op
  with zero world calls; resume via Return accepts fresh keys.
- P2 (unit, CPU): the wired server adds ONLY new routes
  (/api/session, /api/session/key, /api/session/tick, /session_overlay.js) and
  serves the pinned page bytes with ONE disclosed additive script tag; legacy
  routes answer identically with and without the wiring (same handler code
  paths).
- P3 (integrated, motion): the REAL reconstructed app + REAL native engine +
  REAL headless Chrome: boot to attract; Enter -> playing (ticks advance, W
  press produces a mapper record); Escape -> paused (page HUD shows the session
  state; zero records while paused); R -> exactly ONE new engine boot
  (boot_count 1->2, new PID, scene_sha256 byte-equal, start_state_sha256
  compared as measured); Q -> engine process dead through the app's own
  teardown path, server port closed after driver shutdown, zero surviving
  engines.
- P4 (honest deviation expectation): none of the frozen clauses above is
  expected to fire; any FIRED clause is recorded as measured, never tuned away.

## Frozen falsifiers (bite demonstrated live)

- F1: deleting/altering any wiring guarantee (a restart reachable while playing,
  a second teardown, a mapper event while paused, a transition without a key)
  makes `python -B test_session_app.py` exit nonzero with the named clause id.
  Demonstrated by mutation before the green run (failing-first).
- F2 (card falsifier, motion): changed pinned state across the restart
  (scene_sha256 drift), stale commands after restore, leaked owned engine
  processes/ports after exit, or camera/state evidence mismatch fails the
  integrated session.

## Frozen probes

1. `python -B test_session_app.py` (CPU-only unit probe over the wiring + strict
   doubles; also runs the pinned session_flow_tests suite byte-exact).
2. Integrated wired session driver (motion probe; my workspace only):
   reconstruct the pinned play subset by raw blob bytes (archived recipe),
   build chimera_engine.exe from the pinned engine source (cmake+MSVC+Vulkan
   SDK, Release), apply the wiring overlay, and run the browser session with
   real receipts (PIDs, ports, timings, byte-equality of pinned states).
3. `visual_capture.validate_manifest` + `visual_gate.verify` against the
   registry card definition (structural gate; independent visual review remains
   the reviewer's; visual_acceptance is false by validator law).

## Frozen views (recovery profile; captured only in the integrated probe)

- "matched before/after camera bookmark" — diagnostic + clean, before/after the
  restart at the page's own default camera bookmark (declared from
  window.__CHIMERA_VIEW + the page's projection; never guessed).
- "normal follow view during recovery" — the same camera through the live
  session segments (attract -> playing -> paused -> restart -> exit) in the
  real video record.
- Clean views are canvas-only pixels (the page's own draw-path toDataURL);
  diagnostic views are full-page captures including the session HUD. Diagnostic
  layers map onto the page's REAL overlay groups: "state and tick IDs" (tick
  counter), "resource/session diagnostics" (the session HUD line: state, held
  keys, record count, boot_count), "active skill/contact labels" — declared
  MISSING on-screen at the standing start if no referent exists (never
  invented).

## Source pins

- Play repo E:/ChimeraWork/monkey-play-20260924 (read-only; live worktree
  8d16d3c1 never written): f30f2224 (session modules), 8550b634 (playable
  slice + engine source for the build). Extraction: raw `git cat-file` bytes,
  sha256 per file recorded in reference_manifest.json.
- Engine binary: built DURING the run from the pinned 8550b634 engine source in
  my scratch; sha256 recorded in the runtime receipt AFTER the build (the
  prereg freezes the recipe and source pin, not the output hash).
- MAT2 dependency: MAT2-P01 contract (done, PR #192) — carried as context; its
  merge 97993cbe is this attempt's base revision.

## Evidence-class declaration

The integrated probe is designed to produce MOTION-class evidence (real runtime,
real browser input path, real video). Unit probes are records-class. Each
submitted artifact is labeled with its class in the qualification receipt; no
records artifact is offered as runtime proof, and no synthetic frame or test
double is relabeled as runtime capture.

## Honest boundaries (frozen)

- The wired overlay intercepts the flow-bound keys in the CAPTURE phase on the
  page it serves; the pinned index.html bytes and its handlers are unchanged and
  remain fully functional when the overlay is absent (the wiring is additive and
  disclosed).
- The mapper record stream has no locomotion consumer (archived M4 stands,
  declared missing, never fabricated).
- V08 acceptance is the lead's call; this card submits constituent evidence.
- Human player acceptance is the operator's receipt and is not claimed.
- Nothing outside my attempt workspace is written; the play repo and the live
  worktree stay read-only; no push to any branch (lead-serialized publication).
