# INTENT_SEAM_SPEC — the climb/let-go intent stream, v1 (REVIEW COPY)

Status: frozen with `PREREGISTRATION.md` (same content, review framing) BEFORE
implementation, 2026-09-24. This document is the REVIEWED INTERFACE DECISION that
completion-map item U05's constraint demands ("Requires a reviewed interface decision,
not an invented API"). The coordinator dispatches the reviewer; this spec is reviewable
standalone — everything a reviewer needs is on this page. The implementation
(`product/climb_intent.py`) is conformant to THIS document, not the reverse.

Reviewers and stakes: K-series (skill selector, K01 spec-freeze, K06 arbitration) — the
consumer side, section 7; U06 (state feedback) — renders gate/intent states, sections 5-6;
U01/U03/X02 — the surface and gate consistency this spec claims, sections 5-6, 8.

---

## 1. PURPOSE AND SCOPE

One explicit climb/let-go intent must reach the (not yet built) skill selector with
versioned semantics while the frozen walk contract (CommandRecord v1, 20 Hz,
`tools/science_funnel/typeb_export/command_record.py`) remains byte-unchanged. The
decision: intents ride a SEPARATE, SPARSER channel with its own version field — not a
field or mode bolted onto the walk record. What this spec defines: the event wire
format (section 3), the trigger semantics (section 4), the delivery and drop guarantees
(sections 5-6), the consumer interface the selector will implement (section 7), and the
walk-contract independence proof (section 8). What it deliberately does NOT define: what
a climb_request MEANS to the animal (K01/K06), any retraction policy (section 6.4), any
physical key truth beyond the data-defaults (section 9).

## 2. THE INTENT MODEL (v1)

- Exactly two discrete intents: `CLIMB_REQUEST = "climb_request"`, `LET_GO = "let_go"`.
- NO continuous values: the event schema contains no float field. "One explicit
  climb/let-go intent" is the map's own wording; an analog axis would be a different,
  reviewable model (v2 territory).
- EDGE-TRIGGERED: a key press is ONE intent event, not a level. Idempotent per press:
  repeat presses of an already-held key (OS auto-repeat) are named no-ops. The edge
  re-arms on the key's RELEASE. A release emits nothing (section 6.4).
- The channel is PURE SIGNAL: it carries facts about explicit input edges. It contains
  no commands, no poses, no forces, and it never arbitrates (it will happily deliver
  climb_request and later let_go as separate facts; what cancellation means is the
  selector's decision).

## 3. THE EVENT (wire format, intent_version 1)

A frozen, immutable record (`IntentEvent`); canonical form (also the JSON field set):

```json
{
  "intent_version": 1,
  "intent": "climb_request" | "let_go",
  "issued_tick": 300000,     // the session's tick stamp (300 Hz physics ticks)
  "now_ms": 1000000,         // the session milliseconds the press arrived at
  "source": "u05_climb_intent"
}
```

- `intent_version` (int): exactly 1 at v1. The validator REFUSES any other value
  (CommandRecord v1's law: a new version is a NEW declared wire format, not a free
  field).
- `intent` (str): one of the two frozen names; the validator refuses anything else.
- `issued_tick` (int, >= 0): the session's tick stamp — the walk seam's own convention:
  the injected `tick_source()` when the harness provides one, else
  `now_ms * PHYSICS_HZ // 1000` (PHYSICS_HZ = 300, imported from command_record.py,
  never redeclared). Both clocks ride the event so the selector and U06 can correlate
  intents with CommandRecords on one timeline (C12's timestamp chain).
- `now_ms` (int, >= 0): the injected session milliseconds of the press. Injected only:
  the channel never reads a wall clock.
- `source` (str): fixed `"u05_climb_intent"` (provenance, CommandRecord's `source`
  precedent).

There are no other fields at v1. Any field addition is a semantic change (a consumer
must be told what it may ignore) and therefore bumps the version (section 4).

## 4. THE VERSION RULE

The stream carries `intent_version: 1`. ANY of the following bumps it to 2 (with a new
prereg + a new review):

- adding, removing, renaming, or re-typing ANY field (including optional ones);
- adding or removing an intent name;
- changing trigger semantics (edge vs level, auto-repeat behavior, re-arm rule);
- changing delivery or drop semantics (sections 5-6), including adding expiry;
- changing the stamp convention or the source id.

Non-semantic change is defined as NONE. Remapping WHICH PHYSICAL KEYS map to the two
intents is data (section 9) and never bumps the version. Consumers MUST check
`intent_version` before interpreting an event (section 7).

## 5. DELIVERY GUARANTEES

To a consumer that implements the sink interface (section 7):

1. AT-MOST-ONCE PER PRESS, EXACTLY-ONCE PER ACCEPTED PRESS: one accepted press of an
   intent binding produces exactly one event, delivered synchronously during the press
   call, before it returns. There is NO queue, NO background emitter, NO decision grid:
   a slow consumer stalls the producer, it does not accumulate a backlog.
2. NO REPLAY: there are no boundaries to miss and nothing is ever resent. (The walk
   seam's stall/re-issue law is about sustained COMMANDS; an intent is an edge FACT —
   a missed delivery is a lost press, which the operator re-presses. Declared so the
   K-series does not build replay logic on a stream that has none.)
3. ORDERED: delivery order equals press order (single-threaded, synchronous).
4. STAMPED: every event carries the session's `now_ms` and `issued_tick` (section 3).
5. HOLD-SILENT: a held key emits nothing further — zero events per tick, per repeat
   press, per anything — until the key's release re-arms the edge.
6. NOTHING ELSE ARRIVES: the ONLY call a sink ever receives is
   `emit(IntentEvent)`. No control calls, no periodic traffic, no idle noise.

## 6. DROP SEMANTICS (the gates)

6.1 THE THREE GATES. The channel drops (never delivers) press intent while any of:
`disconnected` (device gone, U03's named state), `blurred` (window lost focus, U03),
`paused` (session flow not playing, X02). These mirror the already-integrated laws:
U03's focus policy drops new press/mouse intent by name while blurred/disconnected
(`product/focus_policy.py:272-278`), and X02's session flow forwards nothing while not
playing (`product/session_flow.py:298-307`).

6.2 NAMED, NEVER SILENT. Every gated press is recorded by name:
`dropped_disconnected` / `dropped_blurred` / `dropped_paused` — the STRONGEST active
gate names the drop, with dominance `disconnected > blurred > paused` (U03's law:
disconnected dominates blurred, `focus_policy.py:188-194`; pause ranks weakest because
it is a session fact, not a claim about the input surface). The drop entry also records
the full active gate set.

6.3 NO PHANTOM EDGES. A gated press does NOT arm the edge (U03's no-phantom-keys law,
`focus_policy.py:264-269`): after recovery, the surface is clean and the NEXT press
fires once. Gated releases ALWAYS pass (they can only un-arm; U03's release law,
`focus_policy.py:280-282`). Redundant policy events (blur while blurred, resume while
not paused) are named no-ops (U03 clause 5).

6.4 NEVER FABRICATE A RETRACT. No gate event, no drop, and no release ever produces an
intent. A CLIMB_REQUEST dropped by a gate is simply NOT DELIVERED — no compensating
LET_GO is manufactured. LET_GO exists only as an explicit press of the let_go binding.
Consequence (declared, reviewable): if a climb_request is delivered and the session is
then paused/blurred, the selector has NOT been told to retract — the selector (or the
session flow above it) owns retraction semantics at v1. The channel also never
arbitrates: climb_request followed by let_go are two delivered facts; their
interpretation is K06's.

6.5 RECOVERY. `on_focus` / `on_reconnect` / `on_resume` clear only their own named
state. The edge state tracks physical keys only (press arms, release un-arms; gates
never touch it beyond refusing to arm on gated presses), so one physical hold remains
one consumed edge across any number of gate cycles — no re-fire, no phantom.

## 7. THE CONSUMER INTERFACE (what the K-series selector implements)

```python
class SkillSelectorIntentSink:            # the DECLARED consumer surface, v1
    def emit(self, event: IntentEvent) -> None: ...
```

That is the entire surface. Consumer-side rules (binding on K-series):

1. CHECK THE VERSION: an event with `intent_version != 1` is NOT interpretable by a v1
   consumer — refuse it loudly (log/raise by the consumer's own policy); never guess.
2. THE VOCABULARY IS CLOSED at v1: `climb_request`, `let_go`. An unknown intent name at
   version 1 cannot occur (the producer validates); if a consumer sees one, the producer
   is broken — treat as a fault, not as data.
3. INTENTS DO NOT EXPIRE at v1. A walk CommandRecord goes stale in 100 ms because it is
   a sustained demand; an intent is an edge FACT and does not decay. Intent lifetime
   (when a climb_request stops being actionable) is the SELECTOR's policy — only it
   knows when a climb became impossible. If review rules otherwise, expiry is a semantic
   change: version bump, new prereg.
4. ORDER MEANS NOTHING MORE THAN ORDER: v1 delivers facts in press order; the consumer
   owns state machines (e.g. a climb_request while already climbing may be a no-op, an
   error, or a re-grab — K06's decision, not encoded here).
5. NO BACKPRESSURE CONTRACT: emit is synchronous; a slow consumer stalls the producer
   (section 5.1). If K-series needs buffering/queueing, it owns the queue.
6. WIRING: the harness constructs the channel with the selector's sink:
   `ClimbIntentChannel(sink, bindings=None, tick_source=None)`. The selector never
   touches the walk seam, and the walk mapper never touches this channel.

## 8. WALK-CONTRACT INDEPENDENCE (the proof the reviewer can demand)

- The channel imports exactly ONE thing from the walk seam's module: `PHYSICS_HZ` (a
  constant). It never imports or constructs `CommandRecord`. Structural: the channel
  CANNOT emit a walk command.
- The frozen walk contract's file
  (`tools/science_funnel/typeb_export/command_record.py`) is hashed (sha256) before and
  after the channel's full test run and MUST be byte-identical (falsifier I6);
  `product/input_mapper.py` is likewise reported unchanged.
- SURFACE SHARING, DECLARED: the intent bindings live on the same press/release event
  surface U01's mapper consumes (same injected-clock event kinds, bindings-as-data —
  input_mapper.py:26-29, 99-106), NOT on a new input path. `Space` is bound in BOTH
  default tables: U01's walk side refuses it BY NAME ("jump: no walk-seam channel
  exists at v1", input_mapper.py:105,115-116) — unchanged, measured — while this
  channel delivers climb_request. One physical key, two declared channels, both named;
  the walk seam gains no authority.
- The channel's events and the walk mapper's records never cross sinks: the integrated
  scenario asserts the walk sink receives only CommandRecords (exactly U01/U03's frozen
  behavior) and the intent sink only IntentEvents.

## 9. BINDINGS (data, on the existing surface)

Frozen data-defaults (`DEFAULT_INTENT_BINDINGS`):

```python
{"Space": "climb_request",   # cited: U01's own refusal names the missing channel
 "C": "let_go"}              # declared default; no repo precedent — movable by review
```

Rules: values may only be the two intent names (anything else is REFUSED AT
CONSTRUCTION by name — the parser's refuse-what-you-cannot-name law); remapping is a
data edit with no semantic effect; cross-table overlap with U01's walk bindings is
declared (section 8), not hidden. One physical key maps to at most one intent (it is a
dict).

## 10. POLICY EVENT SURFACE (for the harness, U03/X02-consistent)

`on_blur(now_ms)` / `on_focus(now_ms)` / `on_disconnect(now_ms)` / `on_reconnect(now_ms)`
mirror U03's exact event names; `on_pause(now_ms)` / `on_resume(now_ms)` mirror X02's
pause gate (the session flow, or the harness around it, calls these when the session
leaves/enters `playing`). All times are injected integer milliseconds. The channel also
exposes `press(name, now_ms)` / `release(name, now_ms)` (the SAME event kinds U01's
surface consumes), the queryable `state` (strongest active gate: `"disconnected"` >
`"blurred"` > `"paused"`, else `"ready"`), the full `gates_active` frozenset, `paused`,
and `held` (physically-held intent keys). X02 integration note: while the flow is not
playing, the harness calls `on_pause` once (idempotent); `on_resume` on return to
`playing` — one line in the session loop, no change to X02's module.

## 11. WHAT THE REVIEWER IS ASKED TO RULE ON

1. The two-intent vocabulary suffices for U06's language and K01's first skill family
   (attach, ascend, hold, descend, release) — or name the missing intent NOW (pre-K01),
   because adding one is a version bump.
2. Edge-triggered-only (no level/hold semantics, no auto-repeat) is the right v1
   trigger model for climbing.
3. No intent expiry at v1; the selector owns intent lifetime (section 7.3).
4. No fabricated retraction on drop; retraction is the selector's (section 6.4).
5. The `C` default for let_go (section 9) — a data choice, but cheapest to fix here.
6. The drop-dominance order `disconnected > blurred > paused` for DROP NAMING only
   (section 6.2) — all three gates drop identically; only the name differs.

Approval of this spec is approval of interface semantics v1; the implementation is
measured against sections 2-10 by `product/climb_intent_tests.py` (falsifiers I1-I7 in
`PREREGISTRATION.md`), with receipts under `agents/U05_climb_intent/receipts/`.

---

## 12. R4 REVIEW AMENDMENTS (BINDING — landed inside v1, NO version bump)

Appended 2026-09-24 by M-U05b per the R4 review verdict (APPROVED-WITH-AMENDMENTS;
`agents/R4_intent_review/report.md`). The six interface rulings (section 11 items 1-6)
all APPROVE, so these four implementation-level amendments land **inside v1 without a
version bump**: none touches the wire format, the delivered event set, or any ruling.
Landed with the 73-check suite green plus 4 new amendment checks (77/77;
`product/climb_intent_amr_tests.py`, failing-first receipt in
`agents/U05b_amendments_U06/receipts/`) and R4's adversarial probe battery re-run
(27/27 expectations reproduce post-fix; the four former FINDING probes now flip to the
fixed refusal).

- **AMR-1 (BINDING, validator):** `intent_version` must be `int` and never `bool` —
  `True == 1` would otherwise be ACCEPTED and JSON-encode as `"intent_version": true`
  on the wire (R4 probes A1.g, A1.g'). The version check now applies the same
  non-bool int test the stamps always had. Measured post-fix: `True`, `"1"`, `1.0`,
  `2` all REFUSED; `1` constructs unchanged.
- **AMR-2 (BINDING, validator):** `source` is now VALIDATED: anything other than
  `SOURCE_ID` is REFUSED at construction. Provenance a constructor could forge is not
  provenance (R4 probe A5.e). Wire format unchanged — the delivered field set and
  values are identical; consumers were already promised the fixed id.
- **AMR-3 (BINDING, ordering):** VALIDATE-THEN-ARM. The `IntentEvent` is now
  built/validated BEFORE the edge arms (`press()` calls `_stamp()` first, then arms,
  then delivers synchronously). Measured gap (R4 A5.b-d): a press with a negative
  `now_ms` or a raising `tick_source` used to ARM first and raise second, so the next
  valid press was a named no-op — the physical press silently consumed. Post-fix the
  bad press raises WITHOUT arming and the next valid press DELIVERS. Behavior-identical
  on every valid path; the 73-check suite stayed green.
- **AMR-4 (BINDING, docstring):** `press()`'s docstring previously claimed "returns the
  intent name if ONE event was emitted, else None", but the repeat (held) branch
  returns the bound action with NO event (R4 A5.f) — the return value cannot
  distinguish delivery from no-op. The docstring now states the measured two-case
  contract (fresh press: name + one event; repeat: name + zero events, named
  `repeat_press` in the trace). Code behavior unchanged; the declared consumer
  interface (section 7, `emit` only) is unaffected.

## 13. SPEC-NOTES FOR v2 (recorded, NOT defects, NO binding on v1 — do NOT implement as v1 semantics)

Recorded verbatim from the R4 review (section 5); each is a declared v2 candidate, not
a v1 gap:

- **N1:** declare one-channel-per-sink exclusivity (two channels on one sink
  double-deliver — A4.a; a guard or a declared rule, either).
- **N2:** surface times are `int()`-truncated silently (`press`/`release`/policy) — the
  house convention, but a named refusal would match the event validator's strictness.
- **N3:** binding KEYS are not type-checked (an int key works if pressed with an int);
  the surface contract says strings — cheap to enforce at construction.
- **N4:** state explicitly in §5 that same-`now_ms` events resolve in CALL order
  (measured deterministic; A3).
- **N5:** declare sink-exception semantics (currently: exception propagates, edge stays
  armed, event lost — the operator re-presses; §5.2's no-replay law arguably already
  implies this, but say it). AMR-3's reorder shrank the armed-without-delivery window
  to the emit call itself.
- **N6:** two presses inside the same millisecond share stamps; if K06's arbitration
  logs need total ordering beyond delivery order, v2 should say what the (ms, tick) pair
  does and does not promise.
