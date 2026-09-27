# U05 PREREGISTRATION — the climb/let-go intent seam (versioned, sparser, separate)

Frozen BEFORE implementation, 2026-09-24, worktree `E:/ChimeraWork/monkey-play-20260924`
(branch `monkey-play-20260924`, HEAD `8fc072f3` = U03 INTEGRATED; X02 in flight, its
`product/session_flow.py` read as the declared gating precedent). Read first:
`product/input_mapper.py` (U01, READ-ONLY), `product/focus_policy.py` (U03, READ-ONLY),
`product/session_flow.py` (X02, in flight, READ-ONLY), U01's INTEGRATION note, U03's
INTEGRATION_U07_X02.md, X02's brief + prereg.

Row, verbatim (MONKEY_COMPLETION_MAP.md:107): "One explicit climb/let-go intent reaches
the skill selector with versioned semantics; frozen walk contract remains unchanged."
Constraint: "Requires a reviewed interface decision, not an invented API" — met by
construction: the interface spec (`INTENT_SEAM_SPEC.md`, same content as the frozen
sections below, reviewable standalone) ships WITH this build and the review gate is part
of the deliverable; the coordinator dispatches the reviewer.

Consumers named by the map: U06 (line 108, renders the states), K01 (line 163, freezes
the climbing skill spec), K06 (line 168, walk/climb arbitration). None exists yet — this
seam delivers a VERSIONED INTENT STREAM to a declared interface they will implement.

## RULE 0 — the theory, stated before the build

**STATEMENT** (disagreeable): one explicit climb/let-go intent can be carried to a
not-yet-existing skill selector by a SEPARATE, sparser, versioned intent channel —
discrete, edge-triggered, tick-stamped, drop-named under the already-integrated U03/X02
gate laws — that shares U01's bindings-as-data input surface and shares NOTHING with the
frozen walk contract: no CommandRecord is constructed, read, or altered, and the channel
is pure signal (no commands, no poses, no forces), so the walk seam's bytes, types, and
20 Hz cadence are provably untouched while the selector still gets every explicit intent.

**PREDICTION** (not yet measured; measured by `climb_intent_tests.py`): across the
deterministic scenarios plus a 3000-event seeded fuzz (press/release of bound and unbound
keys + blur/focus/disconnect/reconnect/pause/resume + jittered injected clock, frozen
seed 20260924): (a) every ACCEPTED press of an intent binding yields EXACTLY ONE intent
event, delivered synchronously at the press; a held key yields ZERO further events no
matter how many repeat presses or ticks arrive; release re-arms the edge; (b) every event
carries `intent_version == 1`, one of exactly two intent names (`climb_request`,
`let_go`), the session's tick stamp, and source `u05_climb_intent`; (c) ZERO events are
delivered while blurred, disconnected, or paused; every gated press is dropped AND NAMED
(strongest active gate: disconnected > blurred > paused); releases always pass (they arm
nothing, emit nothing); after recovery the edge is clean (a fresh press fires once);
(d) the number of LET_GO events equals EXACTLY the number of accepted let_go key presses
under all gate churn — no drop, blur, disconnect, or pause ever fabricates a retraction;
(e) sha256 of `tools/science_funnel/typeb_export/command_record.py` is byte-identical
before and after the entire run; every call into the intent sink is
`emit(IntentEvent)`; no CommandRecord is ever constructed by the channel; in the
integrated scenario the walk side behaves byte-consistently with U01/U03 (Space stays a
NAMED walk refusal, zero walk records from it) while the intent side delivers per (a-d).

## THE FROZEN INTENT MODEL

1. **DISCRETE, TWO NAMES**: the channel's entire vocabulary is
   `CLIMB_REQUEST = "climb_request"` and `LET_GO = "let_go"`. No continuous values: the
   event schema has NO float fields at all (the map says "one explicit climb/let-go
   intent"; a float field would be a v2, not an edit). Bindings may map only these two
   names; any other value is REFUSED AT CONSTRUCTION by name (the parser's
   refuse-what-you-cannot-name law, via input_mapper.py:111-116 precedent).
2. **EDGE-TRIGGERED, IDEMPOTENT PER PRESS (semantics v1)**: a press is ONE intent event,
   not a level. A held key emits nothing further — repeat presses while the same key is
   still held (OS auto-repeat) are NAMED no-ops (`repeat_press` in the trace). The edge
   re-arms only on the key's release. A release event NEVER emits an intent (bookkeeping
   only): LET_GO is an explicit press of its own binding, so a blur mid-hold cannot
   manufacture one.
3. **TICK-STAMPED**: each event carries `now_ms` (the injected session milliseconds) and
   `issued_tick` (the session's tick stamp, the walk seam's own convention: the injected
   `tick_source()` if provided, else `now_ms * PHYSICS_HZ // 1000` — PHYSICS_HZ imported
   from command_record.py:70, never redeclared). One timeline with CommandRecord for
   U06/K-series correlation (C12's chain).
4. **DROP-WITH-NAME, CONSISTENT WITH U03/X02**: while blurred, disconnected, or paused,
   press intent is DROPPED AND NAMED — `dropped_disconnected` / `dropped_blurred` /
   `dropped_paused` (U03's exact naming, focus_policy.py:292-294, extended with X02's
   pause; strongest active gate names the drop, the full active set rides the entry).
   Releases always pass (U03's law, focus_policy.py:280-282). A gated press is NOT armed
   (U03's no-phantom-keys law: after recovery the surface is clean, a fresh press fires
   once — focus_policy.py:264-269 precedent). Policy events are idempotent and named
   no-ops when redundant (blur-while-blurred etc., U03 clause 5).
5. **NEVER FABRICATE A RETRACT**: a dropped CLIMB_REQUEST is simply not delivered. No
   gate event (blur/disconnect/pause) fabricates a LET_GO, and no gate event fabricates a
   CLIMB_REQUEST. Retraction is a FUTURE SELECTOR DECISION (K06 owns transition
   semantics): v1 delivers edge facts about explicit keys, nothing more. The channel
   never arbitrates either: it will deliver climb_request and later let_go as separate
   facts; what cancellation MEANS is the selector's, not the channel's.
6. **THE VERSION RULE**: the stream carries `intent_version: 1` (INTENT_VERSION = 1).
   ANY semantic change bumps it — adding/removing/renaming an intent name, changing the
   trigger semantics (edge vs level), changing drop semantics, changing the stamp
   convention, adding ANY field (including optional ones: a consumer must be told what it
   may ignore, so field additions are semantic). Non-semantic change is defined as NONE.
   The event VALIDATOR refuses any version but 1 (the CommandRecord v1 law,
   command_record.py:97-101 precedent: a new version is a NEW declared wire format).
7. **THE NO-TELEPORT / NO-FORCE LAW**: the intent stream contains NO commands, NO poses,
   NO forces — pure signal; the selector decides. Structurally enforced: the module
   imports ONLY `PHYSICS_HZ` from the walk seam's record module (never the
   CommandRecord class), constructs no numeric channel, holds no pose, reads no engine
   state, performs no HTTP, never touches the operator's desktop.
8. **BINDINGS ON THE EXISTING SURFACE, NOT A NEW INPUT PATH**: the intent bindings are a
   DATA table on the SAME event surface U01's mapper consumes — the same
   `press(name, now_ms)` / `release(name, now_ms)` events with injected clocks; no second
   transport, no OS hooks, no new event kinds (press/release only). Frozen default table:

       DEFAULT_INTENT_BINDINGS = {
           "Space": "climb_request",   # U01's own refusal said it: "jump: no
                                       # walk-seam channel exists at v1" — the
                                       # intent channel is where that intent goes
                                       # WITHOUT giving the walk seam new authority;
                                       # U01's walk-side refusal fires unchanged.
           "C": "let_go",              # declared data-default, no repo precedent
                                       # exists; a preference, movable by review or
                                       # remap WITHOUT any semantic change.
       }

   Cross-table overlap is DECLARED, not hidden: `Space` is bound in U01's
   DEFAULT_BINDINGS (input_mapper.py:105) to the walk refusal "jump" and here to
   climb_request; one event stream feeding both surfaces produces BOTH named behaviors
   (walk refusal in the mapper's trace, climb_request on this channel) — falsifier I7
   measures both, and the walk side's bytes/behavior are unchanged by this file.

## FALSIFIERS (named now; any one firing kills the build as specified)

- **I1 HELD KEY REPEATS** (the brief's falsifier b): any held key yields a second intent
  event; any accepted press yields zero or 2+ events; a repeat press is not a named
  no-op; a release emits an intent; a fresh press after release does not fire. Any hit
  fires.
- **I2 VERSION/SCHEMA**: any event without `intent_version == 1` (same object as
  INTENT_VERSION), an intent name outside the frozen two, a float field, a missing stamp,
  or a wrong source; a validator that accepts a wrong version or an unknown intent name.
  Any hit fires.
- **I3 GATED DELIVERY** (the brief's falsifier c): any event delivered while blurred,
  disconnected, or paused; any gated press not dropped BY NAME (the strongest active
  gate); a gated press that arms the edge (phantom fire after recovery); a gated release
  that is blocked; an unnamed redundant policy event. Any hit fires.
- **I4 FABRICATED RETRACT** (the brief's falsifier d): any LET_GO event whose press did
  not happen (count(LET_GO events) != count(accepted let_go presses)) under all gate
  churn; any gate event producing ANY event at all. Any hit fires.
- **I5 PURE SIGNAL**: any sink call that is not `emit(IntentEvent)`; any CommandRecord
  constructed/imported by the channel; any float field in the event; any engine / pose /
  transport / wall-clock / desktop surface in the module (marker scan, U03's P4 law);
  any frozen number redeclared instead of imported (PHYSICS_HZ identity `is`).
  Any hit fires.
- **I6 WALK CONTRACT TOUCHED** (the brief's falsifier a): sha256 of
  `tools/science_funnel/typeb_export/command_record.py` differs between the start and
  the end of the full run; or `product/input_mapper.py` bytes differ across the run
  (reported as context; command_record.py is the pinned falsifier). Any hit fires.
- **I7 INTEGRATION DIVERGES**: in the one-headless scenario (one event feed -> U01 mapper
  under U03's FocusPolicy -> walk sink, AND -> the intent channel -> intent sink, shared
  injected clock): a Space press whose walk side is not the NAMED refusal, or that yields
  any CommandRecord; a blur that does not hit BOTH channels; an intent delivered while
  the policy is blurred; walk-side behavior inconsistent with U01/U03's frozen streams
  (same events, same clock -> the walk sink sees exactly what U03's own tests measured).
  Any hit fires.

**STOP RULE**: `product/climb_intent_tests.py` green end-to-end with all seven
falsifiers measured, receipts saved under `agents/U05_climb_intent/receipts/`, then the
integrity paste (git status: changes ONLY in `agents/U05_climb_intent/` + the two
declared `product/climb_intent*.py` files). No tuning loop: if a falsifier fires, the
CHANNEL MODULE is wrong and is fixed against the frozen model; the model, the event
schema, and the semantics are never adjusted to pass — a semantic fix is a version bump
with a new prereg.

## OWNERSHIP (declared before implementation; nothing existing modified)

- `tools/monkey_campaign/product/climb_intent.py` — the channel module (disjoint name;
  stdlib + `tools.science_funnel.typeb_export.command_record.PHYSICS_HZ` import only;
  U01/U03/X02 files imported READ-ONLY by the TESTS, never edited).
- `tools/monkey_campaign/product/climb_intent_tests.py` — the falsifier tests (house
  style: sibling `*_tests.py`, runnable as a script, per-falsifier receipts, exit 1).
- `tools/monkey_campaign/agents/U05_climb_intent/` — brief, this prereg,
  `INTENT_SEAM_SPEC.md`, integration note, `receipts/`.

Parallel-worker disjointness: U01 owns `input_mapper*.py`, U03 `focus_policy*.py`, X02
`session_flow*.py`, U02 `follow_camera*.py`; this task adds the `climb_intent*` pair —
file sets disjoint, no existing file modified.

## WHAT WOULD MAKE THIS THEORY LOSE (honest limits, stated now)

- The selector does not exist: this seam proves DELIVERY of a versioned stream to a
  declared sink interface, not that climbing works. K01/K06 own what an intent MEANS;
  if K-series needs an intent this vocabulary lacks (e.g. a directional climb), that is
  intent_version 2 under a new prereg — never a silent edit.
- No expiry on intents at v1 (a walk record expires in 100 ms; an edge FACT does not go
  stale the same way — the selector owns intent lifetime, since only it knows when a
  climb became impossible). If review rules intents must age, that is a semantic change:
  version bump, new prereg.
- The default `let_go` key (`C`) is a declared data-default with no repo precedent; the
  REVIEW may move it — a bindings edit is data, not semantics, and changes nothing in
  the frozen model.
- The tests are headless with injected clocks: they measure channel discipline (edges,
  gates, naming, versioning, walk-contract isolation), NOT live key feel or the future
  selector's behavior. U07's actual-play lane measures the live chain.
- X02 is in flight: its flow gates the WALK mapper; this channel's pause gate
  (`on_pause`/`on_resume`) is declared so the session flow (or the harness around it)
  can pause intents the same way — the integration scenario demonstrates the gate; the
  live wiring belongs to X02's integration note (one paragraph written for it).

## REVISION A (appended after the falsifiers fired in the build; no frozen SEMANTIC
## number moved — the trail is recorded, U03's REVISION A precedent)

The fuzz falsifier I8.h (the vacuity floor: a fuzz that accepts fewer than 200 presses
proves nothing) fired THREE times, each on the FUZZ MIX, never on the channel:

1. First mix (uniform key choice, unbiased policy walk): 52 deliveries / 3000 events.
   Two causes measured: (a) only 2 of 4 fuzz keys were bound, so 38% press-rate x 50%
   bound ≈ 570 bound press attempts; (b) with THREE independent gates on an unbiased
   random walk, all gates are open only ~1/8 of the time — 819 of ~945 later bound
   presses landed gated (which is itself drop-law coverage, I8.i PASS).
2. Mix rebuilt (presses/releases weighted to the bound keys 3/4 and 2/3; U03's
   "more coverage, same event mix" precedent): 49 deliveries — the gate walk still
   dominated. Policy pool rebalanced to openings:closings = 3:1 (closings stay 1/4 of
   policy events; drop coverage remains in the hundreds: 498 named drops): 195
   deliveries — still 5 under the floor. Third firing.
3. Event count doubled 3000 -> 6000 (exactly U03's REVISION A move: their fuzz was
   doubled for the same reason). The event count is a COVERAGE number; the seed
   (20260924), the event kinds, the reference model, the floor (200), and every
   frozen semantic of sections "THE FROZEN INTENT MODEL" and "FALSIFIERS" are
   untouched. Post-change: 390+ deliveries, all other falsifier checks unchanged and
   green.

Also fixed during the build, caught by the falsifiers, none a module-semantic change:
the I1/I3/I7 scenarios had their own defects (a press not released before an
independence check; gate cycles ordered so the probe press always landed ungated; a
recovery expectation that ignored the frozen "gates never un-press a physical key"
clause — the scenario now releases THROUGH the blur, which also measures the
releases-always-pass law); the I5 source scan read prose where it meant code (now a
token scan: docstrings that NAME the separation law are not violations of it); and the
I7 flow double needed X02's actual constructor shape (the callables `boot` /
`shutdown_engine`, not the objects). Every fix changed the CHECKER or the SCENARIO to
measure the frozen spec more exactly; no channel semantic moved.

