# X02 PREREGISTRATION — the start / pause / restart / exit flow machine

Frozen BEFORE implementation, 2026-09-24, worktree `E:/ChimeraWork/monkey-play-20260924`
(branch `monkey-play-20260924`, HEAD `8550b634` = U01 INTEGRATED; U03 in flight).
Row, verbatim (MONKEY_COMPLETION_MAP.md:179): "Player reaches play and can
pause/restart/exit without developer commands; reset is an explicit user action."
Read first: `agents/X02_flow/DISCOVERY.md` (all machinery cited there), U01's
`product/input_mapper.py` (imported, never redeclared), U03's declared interface
(`agents/U03_focus/PREREGISTRATION.md`, clauses 1-5).

## RULE 0 — the theory, stated before the build

**STATEMENT** (disagreeable): the entire player session flow on this lineage is a
FOUR-STATE MACHINE that sits as a pure FILTER in front of U01's untouched mapper and
touches the world ONLY through the slice's two declared lifecycle calls — restart =
`World.boot()` (the existing full scene reload, slice_server.py:94-135) and exit =
`World.shutdown_engine()` (terminate→wait→kill, slice_server.py:174-181) — with every
transition triggered by a keyboard binding held as DATA, so the player reaches play
and can pause/restart/exit with zero developer commands, zero physics edits, and zero
invented state writes (no teleport, no gravity-off reset, no engine C++, no hidden
transitions).

**PREDICTION** (not yet measured; measured by `session_flow_tests.py`): across the
deterministic transition table plus a seeded 4000-event fuzz, (a) exactly the frozen
table's transitions fire and every other (state, action) pair is a named no-op;
(b) ZERO CommandRecords reach the sink while the flow is not in `playing` — in
particular while paused (the brief's falsifier b); (c) after a mid-press pause, the
sink stream shows: nothing during pause, then on resume at most 2 records (U01's own
decay tail), each at or below the pre-pause speed, landing on EXACTLY 0.0 and then
silence until a fresh press; (d) the restart transition's world contact is EXACTLY
[quiesce (`release_all`), `restart_scene()` once] against the declared `boot` double —
no other world-mutation call exists to make (a strict double raises on any undeclared
method); (e) exit calls teardown EXACTLY once per session (from any state) and the
double records the declared terminate→wait→kill ordering; after `exited` the machine
is terminal (zero mapper calls of any kind); (f) advancing the injected clock with no
events transitions nothing — no timer, no wall clock, no internal driver exists.

## THE FROZEN STATE MACHINE

States (exact strings): `attract` → `playing` ⇄ `paused` → `exited` (terminal).
Initial state: `attract`.

THE FROZEN TRANSITION TABLE (the ONLY transitions; everything else is a named no-op):

| # | (state, action)          | dest      | declared side effects, in order |
|---|--------------------------|-----------|----------------------------------|
| 1 | (attract, confirm)       | playing   | gate opens (gameplay events reach the mapper) |
| 2 | (playing, pause)         | paused    | `mapper.release_all(now_ms)` FIRST (the quiesce — U01's declared U03 hook, input_mapper.py:225-228), THEN the gate closes (the mapper receives no events of any kind while not playing) |
| 3 | (paused, confirm)        | playing   | gate reopens (resume); re-arm per U03's declared clause 4 — the mapper is held-empty because the pause quiesce released everything, so the next accepted press arms a FRESH 50 ms grid; no tail is restarted by the flow |
| 4 | (paused, restart)        | playing   | `mapper.release_all(now_ms)` (no stale held keys cross the boot), then `restart_scene()` — the DECLARED path `World.boot()` (full scene reload, DISCOVERY section 2) — then the gate reopens. If the restart callable RAISES: NO transition (state stays `paused`), the failure is named in the trace; a half-restart is never claimed |
| 5 | (attract, exit)          | exited    | `teardown()` — the DECLARED path `World.shutdown_engine()` (terminate→wait→kill, DISCOVERY section 3) — exactly once |
| 6 | (playing, exit)          | exited    | same as 5 |
| 7 | (paused, exit)           | exited    | same as 5 |

THE FROZEN BINDINGS (keyboard bindings as DATA; remapping edits this dict, never the
machine — the parser's "bindings are DATA" law, tools/parser.py:39-69 via
input_mapper.py:26-29):

    DEFAULT_FLOW_BINDINGS = {"Return": "confirm", "Escape": "pause",
                             "R": "restart", "Q": "exit"}

`R` = restart matches the slice page's existing key precedent (index.html:1072).
Disjoint from U01's gameplay bindings (W/S/A/D/arrows/Shift/Space — input_mapper.py:99-106);
a flow-bound key is CONSUMED by the flow in every state and never reaches the mapper.

## THE FROZEN RULES

1. INPUT GATING: the flow forwards `press`/`release`/`mouse`/`tick` to the mapper
   ONLY in `playing`. In `attract`/`paused`/`exited` every gameplay event and every
   decision tick is dropped AND NAMED in the trace (U03's clause-2 pattern: never
   silent). The one declared exception is the quiesce `release_all(now_ms)`, executed
   INSIDE transitions 2 and 4 (it emits nothing by itself; it is U01's own declared
   hook).
2. THE DECISION CLOCK IS SUSPENDED WITH THE SESSION: the flow never advances time and
   never invents boundaries. `flow.tick(now_ms)` reaches the mapper only in `playing`;
   while paused there are NO boundaries at all — zero emissions is SUSPENSION, not
   suppression. The pre-pause record (if any) is handled by U01's own consumer-side
   expiry floor (`is_expired`, VALID_MS = 100 ms) on the seam side, and by U01's own
   decay tail on the resume side (rule 3).
3. RESUME TAIL (bounded, U01's machinery only): if the pause interrupted an emission
   (a tail exists), the first `playing` boundaries sample U01's frozen decay — at
   most 2 records, each ≤ the pre-pause speed (`_apply_tail` can only decay),
   landing on EXACTLY 0.0, then silence and the grid dissolves
   (input_mapper.py:293-313, 262-267). The flow adds no clearing primitive: a hard
   clear would flip the seam to the live-zero state (the two-state seam law,
   input_mapper.py:10-21) — the exact mistake U03's clause 1 refuses.
4. RESTART: only via transition 4 (reached through pause — deliberate: an accidental
   `R` mid-play must never wipe the session). The injected `restart_scene` callable's
   declared referent is `World.boot()`; the flow performs NO other world contact —
   no pose write, no gravity toggle, no scene-term call (the deck's `/scene` is
   another lineage, DISCOVERY section 1).
5. EXIT: reachable from every non-exited state (owned processes must die from
   anywhere). Terminal: after `exited`, every event and every flow action is a named
   drop; the table has no exit-out of `exited`.
6. NO HIDDEN TRANSITIONS: the module's only public mutators are `key`, `mouse`,
   `tick`. No timers, no threads, no wall clock, no transport, no subprocess. All
   numeric constants the flow needs are IMPORTED from U01's module (same objects),
   except the flow's own ZERO numeric physics constants — the flow declares no
   physics number at all.

## FALSIFIERS (named now; any one firing kills the build as specified)

- **F1 NO CODE-ONLY STATE** (the brief's falsifier a): any of the four states is not
  reachable by key events through the bindings alone; or any table action is not a
  bindings value; or any bindings value is not a table action (an unreachable or
  untriggerable binding). Any hit fires.
- **F2 PAUSE LEAKS INPUT** (the brief's falsifier b): in the seeded fuzz, any
  CommandRecord reaches the sink while the flow is not in `playing`; or the mapper
  receives any call while paused; or the post-pause-resume stream violates rule 3's
  bound (a record above the pre-pause speed, a non-monotone tail, no exact-0.0
  landing, any record after the landing before a fresh press). Any hit fires.
- **F3 RESTART DIVERGES FROM THE DECLARED PATH** (the brief's falsifier c): the
  restart transition's world-contact sequence is not exactly [release_all, boot x1]
  on the recording double; or the flow calls ANY method outside the declared surface
  on a strict double (which raises on anything but `boot`); or a raising restart
  callable still flips the state; or restart is reachable outside (paused, restart).
  Any hit fires.
- **F4 EXIT LEAVES OWNED RESOURCES ALIVE** (the brief's falsifier d): the teardown
  double is not called exactly once per session across exit-from-any-state; or its
  recorded ordering is not exactly terminate→wait→kill (the declared
  shutdown_engine shape, slice_server.py:174-181); or any mapper call happens after
  `exited`; or a second exit re-tears-down. Any hit fires.
- **F5 HIDDEN TRANSITION / DEVELOPER COMMAND** (the no-developer-commands rule):
  advancing the injected clock with zero events changes the state; or any transition
  is triggered by anything but `key(name, down=1)` through the bindings; or the
  module imports/declares a forbidden surface (time/datetime/threading/socket/
  subprocess/urllib/ctypes, keybd_event/SendInput/SetCursorPos); or a frozen number
  is redeclared instead of imported (identity `is` against input_mapper's constants).
  Any hit fires.

## STOP RULE

`product/session_flow_tests.py` green end-to-end with all five falsifiers measured
and receipts saved under `agents/X02_flow/receipts/`, then the integrity paste
(git status showing changes ONLY in `agents/X02_flow/` + the two declared
`product/session_flow*.py` files). No tuning loop: if a falsifier fires, the FLOW
MODULE is wrong and is fixed against the frozen table and U01's frozen numbers;
the numbers and the table are never adjusted to pass.
