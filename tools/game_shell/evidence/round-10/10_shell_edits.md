# Round-10 — FEEL THE MUSCLE shell edits (static-only, no servers)

Scope: energy increment step 3, shell side only. Engine untouched
(ChimeraEngine/, Saved/, tools/creature_graph/ never opened for write;
membrane_tick.cpp read read-only for field names). No builds, no servers,
no process control — the engine-rebuild agent was live.

## State found at dispatch
The working tree ALREADY carried a prior dispatch's uncommitted
feel_the_muscle work in all three files (lessons.json had 12 lessons with
feel_the_muscle at position 6, not appended as 12; server.py had the proxy
map; index.html had the full control/judge/disarm wiring). This round
audited that work against the engine facts, fixed two real gaps, and
applied the keyboard edit the assignment asked for.

## server.py — changed (this round)
- Proxy map (do_POST): /api/effort -> /tick_effort, /api/sever ->
  /tick_sever, same style as /api/pose (prior dispatch; verified).
- GAP FIXED THIS ROUND: /api/effort and /api/sever were missing from
  STREAM_PATHS, so they fell into the api class (30/min, burst 15). The
  effort slider POSTs on every input event (a full 0..100 drag is up to
  100 posts) — one drag would exhaust the bucket and 429 the muscle dead
  mid-lesson; postJSON is a bare fetch with no retry, so the failure is
  silent. Both paths now join /api/pose in the stream class (1200/min),
  with a dated comment. This is what "same style as /api/pose" requires.
- Verified: python -m py_compile server.py -> OK (after the edit).

## lessons.json — verified (prior dispatch, unchanged this round)
- 12 lessons; feel_the_muscle at index 5 (lesson 6), goal
  {type: effort_reach, joint: knee_L, deg: 40, then_sever: true,
  sever_below_deg: 5}; _format documents the goal shape.
- The assignment's "pose_reach knee_L 90" alternative was checked and
  rejected for the right reason: pose_reach judges the POSTED intent
  (observePose), never the live angle, so it cannot express "the muscle
  raised the shin" — effort_reach reads tendon_q_deg from /api/state.
  deg 40 (not 90) matches the engine probe (q reaches ~145 deg at full u;
  40 is a modest, reachable flex).
- Verified: json.load -> OK; ids unique; goal fields present.
## index.html — changed (this round: keyboard + help text; prior dispatch: control)
- Prior dispatch (verified against engine facts, unchanged):
  effort-btn-wrap div; KNOWN_GOAL_TYPES += effort_reach; flexMet latch;
  buildEffortCtrl (slider 0-100 -> postEffort(v/100), SEVER button ->
  POST /api/sever {joint_index:15}, live readout battery_J / F_n / q_deg /
  SEVERED|armed — field names match membrane_tick.cpp state_json exactly);
  judge branch latches flex on measured tendon_q_deg >= 40, passes only
  after tendon_severed AND q < 5; disarm u=-1 awaited on lesson switch
  (showLesson), on stand-at-rest, and on page load.
- GAP FIXED THIS ROUND (the assignment's keyboard item): added 'q' ->
  feel_the_muscle when LESSONS.length > 11. The assignment said
  "'q' -> lesson 12", but the pack holds the muscle at 6 (not appended
  last) and backtick is already dynamic (-> last lesson), so a positional
  lesson-12 binding would duplicate backtick and miss the muscle; 'q'
  resolves the lesson BY ID, dynamic like the backtick binding.
  'q' verified unclaimed first (claimed: [ ] space Escape p r s - = +
  Enter digits backtick; the overlay handler claims s/S/Enter/space/Escape
  only, and the main handler ignores text inputs).
- Keyboard-section header comment updated (it said "` lesson 11", stale
  since the pack grew to 12; now documents dynamic backtick + 'q').
- Verified: tree-sitter JS gate (evidence/_ts_gate.py) on the extracted
  inline script -> PARSE_OK, zero ERROR/MISSING nodes (run after the
  edits); diff re-read for brace/quote balance.

## Residual risks (cannot close statically)
- No live play test: the engine-rebuild agent owns the build; per dispatch
  rules no server was launched. Playability evidence is the prior
  round-09 integration probe (09_integration_probe.txt: arm/flex/sever/
  refuse/disarm all ok on a scratch build) — not this build.
- Effort slider drag at stream class: worst case ~100 posts/drag vs the
  1200/min shared bucket alongside verts+state polls (~264/min/player);
  fine for one player dragging, four simultaneous drags behind one NAT
  could lean on it. Accepted: same class as /api/pose by design.
- /api/effort and /api/sever are NOT in the anatomy-scene 409 guard
  (touch/gravity are). On the anatomical scene the engine has no tendon
  drive; the effort control only renders on effort_reach lessons, so the
  page never posts there in practice. Flagged, not changed.
- Sever does not disarm (engine keeps refusing pose on 15 until u<0);
  the page models this (tendonArmed stays true after sever; the exit
  disarm still fires). Verified by reading both sides.
