# U05 integration notes — for U06 (state feedback), X02 (live pause wiring), K01/K06 (the selector)

Module: `tools/monkey_campaign/product/climb_intent.py` (+ `climb_intent_tests.py`).
Prereg: `agents/U05_climb_intent/PREREGISTRATION.md` (frozen, with REVISION A appended —
read it: three fuzz-mix firings and four checker/scenario defects were caught and are
recorded there; no frozen SEMANTIC number or clause moved). Spec:
`agents/U05_climb_intent/INTENT_SEAM_SPEC.md` — the REVIEWED INTERFACE DECISION this row's
constraint demands; the review gate is part of the deliverable (coordinator dispatches the
reviewer). Receipt: `receipts/climb_intent_tests_20260924.txt` (GREEN, 73/73 checks).
Baselines re-measured green in this worktree during the final run:
`receipts/u01_baseline_recheck_20260924.txt`, `receipts/u03_baseline_recheck_20260924.txt`,
`receipts/x02_baseline_recheck_20260924.txt`. Walk contract byte-proof:
`receipts/integrity_git_status_20260924.txt` + the I6 checks (sha256 of
`tools/science_funnel/typeb_export/command_record.py`
`061a2b55f2f5fd145e0fae918e8a9223b1d58be3bce78f1298cd45aa47aa8781`, identical before/after).

## The contract in one paragraph

`ClimbIntentChannel(sink, bindings=None, tick_source=None)` consumes the SAME two event
kinds U01's mapper consumes — `press(name, now_ms)` / `release(name, now_ms)`, injected
integer ms — and delivers `IntentEvent`s (v1: `{intent_version: 1, intent:
"climb_request"|"let_go", issued_tick, now_ms, source: "u05_climb_intent"}`) to
`sink.emit(...)`, ONE per accepted press, synchronously, hold-silent, edge re-armed by
release. No floats anywhere in the event; no CommandRecord is ever constructed (the only
walk-seam import is the CONSTANT `PHYSICS_HZ`). Gates: `on_blur/on_focus/
on_disconnect/on_reconnect` (U03's exact event names) + `on_pause/on_resume` (X02's
pause); a gated press is dropped AND NAMED (`dropped_disconnected` > `dropped_blurred` >
`dropped_paused`, strongest gate names it, full gate set in `last_trace["drops"]`), never
armed, and no gate/drop/release ever fabricates an intent — a dropped CLIMB_REQUEST is
simply not delivered; retraction is the selector's decision (spec §6.4). Queryable:
`state` ("ready"/"paused"/"blurred"/"disconnected", disconnect dominates), `gates_active`,
`paused`, `held`. Bindings are DATA: `{"Space": "climb_request", "C": "let_go"}` —
Space is DECLARED to overlap U01's walk-side "jump" refusal (both named behaviors fire;
the walk seam gains nothing), and `C` is a movable data-default awaiting review.

## U06 — readable control and state feedback (depends on U05)

- Your language prompts can distinguish states TODAY from two honest sources: the
  channel's `state`/`gates_active`/`paused` (whether climb intent would be HEARD right
  now) and the INTENT STREAM itself (what the player asked). A prompt like "climb
  available" must be gated on `state == "ready"` — the map's law: no prompting a climb
  the channel would have to drop. Do not render `held` as "climbing": it means keys
  physically held, an input fact, not a game state.
- The stream is sparser than the walk seam by design: expect ~1 event per explicit
  press, NOTHING during holds. If your UI needs a "climb requested" flash, light it
  from the delivered event (its `issued_tick`/`now_ms` are on the same clocks as
  CommandRecord, so you can correlate the flash with the walk stream's timeline).
- v1 has no "climb possible/impossible" fact — the channel is pure signal. If U06 needs
  availability semantics, that is the selector's future output (K06), not this channel's;
  do not infer it from absence of events.

## X02 — live pause wiring (one line in the session loop)

The flow module itself is UNCHANGED (X02's files untouched; measured again green — see
receipt). In the live harness, when the flow LEAVES `playing`, call
`chan.on_pause(now_ms)` once; when it RETURNS, `chan.on_resume(now_ms)`. Pause and blur
are separate gates (per U03's note, pause must not fake a blur); the channel drops by
name whichever gate is really closed, and `flow.tick` suspension means the walk side
emits nothing while paused (measured together: I7.l/I7.m). The pause/resume calls are
idempotent and named no-ops when redundant — calling `on_pause` again on an already
paused session is safe.

## K01/K06 — the skill selector (consumer side, spec §7 is binding)

- Implement exactly `emit(self, event: IntentEvent) -> None`; check
  `event.intent_version != 1` and REFUSE loudly — never guess at a foreign version.
- The vocabulary is closed at v1 (`climb_request`, `let_go`); intents DO NOT EXPIRE at
  v1 (an edge fact is not a decaying demand — the 100 ms walk-record expiry does NOT
  apply here); intent lifetime is the selector's policy. If K01's freeze needs
  availability, direction, or expiry, that is intent_version 2 under a new prereg —
  adding any of them to v1 silently is the one thing this seam refuses by construction.
- The channel arbitrates nothing: climb_request then let_go are two delivered facts;
  transition preconditions, cancellation, and ownership are yours (the map's K06 law:
  no automatic snap-to-tree — and the channel will never pretend it happened: no
  fabricated retracts, no phantom re-fires; a held key across blur/pause stays ONE
  consumed edge).

## Disjointness

U05 files: `tools/monkey_campaign/product/climb_intent*.py` +
`agents/U05_climb_intent/*`. U01's `input_mapper.py`, U03's `focus_policy.py`, and X02's
`session_flow.py` were imported READ-ONLY by the tests; no existing file modified
(`receipts/integrity_git_status_20260924.txt`). One event feed drives the walk policy and
this channel side by side in the integrated scenario — neither imports the other.
