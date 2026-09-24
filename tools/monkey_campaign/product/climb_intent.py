"""climb_intent.py -- M-U05: the climb/let-go intent seam (versioned, sparser, separate).

U05, verbatim (MONKEY_COMPLETION_MAP.md:107): "One explicit climb/let-go intent
reaches the skill selector with versioned semantics; frozen walk contract remains
unchanged." Constraint: "Requires a reviewed interface decision, not an invented
API" -- THIS MODULE CONFORMS TO A FROZEN, REVIEWABLE SPEC written before it:
agents/U05_climb_intent/INTENT_SEAM_SPEC.md (+ PREREGISTRATION.md, the same
decisions in falsifier form). The selector does not exist yet (K-series); this
channel delivers a VERSIONED INTENT STREAM to the declared sink interface the
selector will implement (spec section 7). U06 renders the states; K01/K06 own
what an intent MEANS.

THE SEPARATION LAW (what this file must never break): the channel is a SEPARATE,
SPARSER channel beside the frozen walk contract (CommandRecord v1, 20 Hz). The
ONLY import from the walk seam's module is PHYSICS_HZ (a constant) -- never the
CommandRecord class -- so the channel structurally CANNOT emit a walk command.
Its events carry NO commands, NO poses, NO forces: pure signal, no float fields
at all; the selector decides. The walk contract's bytes are proven unchanged by
the tests (falsifier I6: sha256 of command_record.py before/after the run).

THE FROZEN MODEL (spec sections 2-4; prereg clauses 1-8):
  * TWO DISCRETE INTENTS -- CLIMB_REQUEST ("climb_request") and LET_GO
    ("let_go"); the vocabulary is closed; no continuous values ever.
  * EDGE-TRIGGERED, IDEMPOTENT PER PRESS -- a press is ONE intent event, not a
    level: a held key emits NOTHING further (OS auto-repeat presses are NAMED
    no-ops, "repeat_press" in the trace); the edge re-arms only on the key's
    release. A release NEVER emits an intent (bookkeeping only) -- so LET_GO is
    always an explicit press of its own binding, and a blur mid-hold can never
    manufacture one.
  * TICK-STAMPED -- each event carries now_ms (injected session ms) and
    issued_tick (the walk seam's own stamp convention: the injected
    tick_source() if provided, else now_ms * PHYSICS_HZ // 1000) so U06 and the
    K-series correlate intents with CommandRecords on ONE timeline (C12's
    chain). PHYSICS_HZ is imported, never redeclared.
  * DROP-WITH-NAME -- while blurred, disconnected, or paused, a bound press is
    DROPPED AND NAMED: dropped_disconnected / dropped_blurred / dropped_paused
    (U03's exact naming, focus_policy.py:292-294, + X02's pause). The STRONGEST
    active gate names the drop (disconnected > blurred > paused -- U03's
    dominance, focus_policy.py:188-194; pause ranks weakest: a session fact, not
    a claim about the input surface); the full active gate set rides the entry.
    A gated press does NOT arm the edge (U03's no-phantom-keys law,
    focus_policy.py:264-269); releases ALWAYS pass (they can only un-arm,
    focus_policy.py:280-282); redundant policy events are named no-ops (U03
    clause 5). An UNBOUND press carries no intent, so there is nothing to drop:
    it is recorded in "pressed" and ignored (U01's rule, input_mapper.py:198-199).
  * NEVER FABRICATE A RETRACT -- a dropped CLIMB_REQUEST is simply not
    delivered; no gate event, drop, or release ever produces ANY intent.
    Retraction is a FUTURE SELECTOR DECISION (spec section 6.4): the channel
    never arbitrates, it delivers edge facts.
  * THE VERSION RULE -- every event carries intent_version: 1; ANY semantic
    change (fields, names, trigger/drop/stamp semantics) bumps it under a new
    prereg + review (spec section 4). The validator refuses any other version
    (the CommandRecord v1 law, command_record.py:97-101 precedent).
  * BINDINGS ON THE EXISTING SURFACE, NOT A NEW INPUT PATH -- the intent
    bindings are a DATA table on the SAME press/release events U01's mapper
    consumes (bindings-as-data, input_mapper.py:26-29); no second transport, no
    OS hooks, no new event kinds. DEFAULT_INTENT_BINDINGS binds "Space" ->
    climb_request (U01's own refusal said where the intent goes: "jump: no
    walk-seam channel exists at v1", input_mapper.py:105,115-116 -- the walk
    side's named refusal fires UNCHANGED) and "C" -> let_go (a declared
    data-default, no repo precedent; movable by review or remap, never
    semantics). Cross-table overlap is DECLARED (spec section 8), not hidden.

Headless by construction: every time is an INJECTED integer millisecond; the
sink is injected; this module never reads a wall clock, never opens a window,
never touches the operator's desktop, never spawns or signals a process.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# THE ONLY IMPORT FROM THE WALK SEAM'S MODULE: a constant. The channel never
# imports or constructs CommandRecord -- structurally it CANNOT emit a walk
# command (INTENT_SEAM_SPEC.md section 8; falsifier I5 checks the import set).
from tools.science_funnel.typeb_export.command_record import PHYSICS_HZ  # noqa: E402

__all__ = [
    "IntentEvent", "IntentEventError", "ClimbIntentChannel", "MockIntentSink",
    "CLIMB_REQUEST", "LET_GO", "INTENTS", "INTENT_VERSION",
    "DEFAULT_INTENT_BINDINGS", "SOURCE_ID",
    "READY", "BLURRED", "DISCONNECTED", "PAUSED", "GATE_DOMINANCE",
    "PHYSICS_HZ",
]

SOURCE_ID = "u05_climb_intent"

# ── THE FROZEN INTENT MODEL (spec section 2) ────────────────────────────────────
INTENT_VERSION = 1            # ANY semantic change bumps this (spec section 4)
CLIMB_REQUEST = "climb_request"
LET_GO = "let_go"
INTENTS = (CLIMB_REQUEST, LET_GO)   # the closed vocabulary; nothing else is legal

# ── THE FROZEN BINDINGS (data, on the existing press/release surface; spec §9) ──
# Values outside INTENTS are REFUSED AT CONSTRUCTION by name (the parser's
# refuse-what-you-cannot-name law, via input_mapper.py:111-116 precedent).
DEFAULT_INTENT_BINDINGS = {
    "Space": CLIMB_REQUEST,   # U01's own refusal names the missing channel
                              # ("jump: no walk-seam channel exists at v1") --
                              # the intent channel is where that intent goes,
                              # WITHOUT giving the walk seam new authority; the
                              # walk side's NAMED refusal fires unchanged.
    "C": LET_GO,              # declared data-default; no repo precedent exists
                              # -- a preference, movable by review or remap
                              # WITHOUT any semantic change (spec section 9).
}

# ── THE NAMED GATES (U03's names + X02's pause; spec sections 6, 10) ────────────
DISCONNECTED = "disconnected"   # device gone (U03's named state)
BLURRED = "blurred"             # window lost focus (U03)
PAUSED = "paused"               # session flow not playing (X02)
READY = "ready"                 # no gate active
GATE_DOMINANCE = (DISCONNECTED, BLURRED, PAUSED)   # orders DROP NAMING only:
# all three gates drop identically; the strongest active gate supplies the name.


class IntentEventError(ValueError):
    """An event violates the v1 intent wire format (the message says which)."""


@dataclass(frozen=True)
class IntentEvent:
    """One explicit intent, versioned -- the stream's entire currency (spec §3).

    NO commands, NO poses, NO forces: there is no float field, no target, no
    magnitude -- the ONLY numbers are the two stamps. The selector decides.

    Fields (v1 -- the whole wire format):
      intent         : "climb_request" | "let_go" (the closed vocabulary)
      issued_tick    : int >= 0, the session's tick stamp (300 Hz physics ticks;
                       the walk seam's own convention, PHYSICS_HZ imported)
      now_ms         : int >= 0, the injected session milliseconds of the press
      intent_version : int, exactly INTENT_VERSION (1); any other value raises
      source         : provenance, fixed SOURCE_ID
    """

    intent: str
    issued_tick: int
    now_ms: int
    intent_version: int = INTENT_VERSION
    source: str = SOURCE_ID

    def __post_init__(self):
        if self.intent_version != INTENT_VERSION:
            raise IntentEventError(
                f"intent_version {self.intent_version} != {INTENT_VERSION} "
                "(a new version is a NEW declared wire format, not a free field)")
        if self.intent not in INTENTS:
            raise IntentEventError(
                f"intent {self.intent!r} is outside the frozen vocabulary "
                f"{INTENTS} (adding one is a version bump, never an edit)")
        for name in ("issued_tick", "now_ms"):
            v = getattr(self, name)
            if not isinstance(v, int) or isinstance(v, bool) or v < 0:
                raise IntentEventError(
                    f"{name} must be a non-negative int (a stamp), got {v!r}")

    # ---- the wire format (canonical fields; the JSON form is json.dumps of it)
    def canonical_fields(self) -> dict:
        return {
            "intent_version": self.intent_version,
            "intent": self.intent,
            "issued_tick": int(self.issued_tick),
            "now_ms": int(self.now_ms),
            "source": self.source,
        }


class MockIntentSink:
    """The clean test double for the stream (U01's MockSink shape, intent-typed).

    The pure-signal falsifier reads this log: every entry must be
    ("emit", <IntentEvent>) -- anything else is I5 and the build is dead.
    """

    def __init__(self):
        self.calls = []            # every (method_name, args) tuple, in order
        self.events = []           # convenience: the IntentEvents emitted

    def emit(self, event):
        self.calls.append(("emit", event))
        self.events.append(event)
        return len(self.events)

    def __len__(self):
        return len(self.events)


class ClimbIntentChannel:
    """The climb/let-go intent seam: explicit key edges -> a versioned stream.

    Usage (all times INJECTED integer milliseconds -- never a wall clock):

        sink = MockIntentSink()          # or the K-series selector's sink
        chan = ClimbIntentChannel(sink)
        chan.press("Space", now_ms=1000)   # -> ONE climb_request, stamped
        chan.press("Space", now_ms=1010)   # held: named no-op, ZERO events
        chan.release("Space", now_ms=1100) # re-arms the edge; emits NOTHING
        chan.press("Space", now_ms=1200)   # -> ONE climb_request again
        chan.on_pause(now_ms=1300)         # X02: session left `playing`
        chan.press("C", now_ms=1400)       # -> dropped_paused (named), NO event
        chan.on_resume(now_ms=1500)        # clean: the edge is still un-armed
        chan.press("C", now_ms=1600)       # -> ONE let_go
        chan.state                         # "ready"/"paused"/"blurred"/
                                           # "disconnected" (strongest gate)

    Deliberate orders, each frozen (spec sections 5-6):
      * press: unbound -> ignored (no intent existed to drop); bound -> the
        gate FIRST (U03's press order, focus_policy.py:272-278) -> the edge
        (repeat = named no-op) -> arm + emit ONCE.
      * release: ALWAYS passes, even gated (it can only un-arm; U03's law) --
        and NEVER emits.
      * policy events are idempotent and named no-ops when redundant.
      * gates never touch the armed set beyond refusing to arm on gated
        presses: one physical hold stays one consumed edge across any number
        of gate cycles -- no re-fire, no phantom (spec section 6.5).
    """

    def __init__(self, sink, bindings=None, *, tick_source=None):
        if not hasattr(sink, "emit"):
            raise TypeError("sink must provide emit(event) -- the channel can "
                            "only deliver intent facts, never touch state")
        table = dict(DEFAULT_INTENT_BINDINGS if bindings is None else bindings)
        for key in sorted(table):
            action = table[key]
            if action not in INTENTS:
                raise ValueError(
                    f"binding {key!r} -> {action!r}: not one of {INTENTS} -- "
                    f"refusing what the channel cannot name (the parser's law)")
        self._sink = sink
        self.bindings = table            # DATA: remapping is never a semantic change
        self._tick_source = tick_source  # callable() -> int tick, or None
        self._held = set()               # physically-held INTENT keys (edge state)
        self._blurred = False
        self._disconnected = False
        self._paused = False
        self.last_trace = {}             # house style: the named trace

    # ── state ────────────────────────────────────────────────────────────────
    @property
    def gates_active(self):
        """The full truth about the gates (the drop NAME is only the strongest)."""
        return frozenset(g for g in GATE_DOMINANCE
                         if getattr(self, "_" + g))

    @property
    def state(self):
        """The strongest active gate: disconnected > blurred > paused > ready
        (U03's dominance law, focus_policy.py:188-194, pause appended weakest)."""
        for g in GATE_DOMINANCE:
            if getattr(self, "_" + g):
                return g
        return READY

    @property
    def paused(self):
        """X02's gate, queryable on its own."""
        return self._paused

    @property
    def held(self):
        """Physically-held INTENT keys (the edge state -- NOT walk demand)."""
        return frozenset(self._held)

    @property
    def _gate_open(self):
        """Whether press intent is accepted. Closed while paused, blurred, or
        disconnected; a release is never gated either way."""
        return not (self._disconnected or self._blurred or self._paused)

    # ── input events (the SAME kinds U01's surface consumes; spec section 10) ─
    def press(self, name, now_ms):
        """A key went down. Returns the intent name if ONE event was emitted,
        else None -- every swallow is NAMED in the trace, never silent."""
        now_ms = int(now_ms)
        action = self.bindings.get(name)
        self.last_trace.setdefault("pressed", []).append((name, now_ms))
        if action is None:
            return None                 # an unbound input is not an error
        if not self._gate_open:
            self._drop(name, now_ms)    # named; and NOT armed (no phantom edge)
            return None
        if name in self._held:
            # OS auto-repeat or a duplicate press of a still-held key: the edge
            # law says a press is ONE event -- a NAMED no-op, never a second.
            self.last_trace.setdefault("repeat_press", []).append((name, now_ms))
            return action
        self._held.add(name)            # the edge arms exactly here
        self._emit(action, now_ms)      # ONE event, synchronously, stamped
        return action

    def release(self, name, now_ms):
        """A key went up. ALWAYS passes (gated or not -- a release can only
        un-arm; U03's release law) and NEVER emits an intent: LET_GO is an
        explicit press of its own binding, so nothing here can fabricate one."""
        now_ms = int(now_ms)
        self.last_trace.setdefault("released", []).append((name, now_ms))
        self._held.discard(name)        # the edge re-arms exactly here
        return self.bindings.get(name)

    # ── the policy events (U03's names + X02's pause; spec section 10) ───────
    def on_blur(self, now_ms):
        """The window lost focus: new press intent is dropped, named."""
        return self._policy_event("blur", "blurred", True, now_ms)

    def on_focus(self, now_ms):
        """Focus regained: the blurred gate opens. The edge state is untouched
        (a still-held key stays a consumed edge -- no re-fire, no phantom)."""
        return self._policy_event("focus", "blurred", False, now_ms)

    def on_disconnect(self, now_ms):
        """The input device is gone: new press intent is dropped, named."""
        return self._policy_event("disconnect", "disconnected", True, now_ms)

    def on_reconnect(self, now_ms):
        """The device is back: the disconnected gate opens."""
        return self._policy_event("reconnect", "disconnected", False, now_ms)

    def on_pause(self, now_ms):
        """The session left `playing` (X02's flow pause): new press intent is
        dropped, named. Idempotent: pause-while-paused is a named no-op."""
        return self._policy_event("pause", "paused", True, now_ms)

    def on_resume(self, now_ms):
        """The session returned to `playing`: the paused gate opens."""
        return self._policy_event("resume", "paused", False, now_ms)

    def _policy_event(self, event, gate, closing, now_ms):
        """The ONE policy-event path: set the named gate; redundant transitions
        are named no-ops (U03 clause 5). NEVER touches the armed set and NEVER
        emits: gates refuse intent, they cannot fabricate it (spec §6.4-6.5)."""
        now_ms = int(now_ms)
        self.last_trace.setdefault("events", []).append((event, now_ms))
        if getattr(self, "_" + gate) is closing:
            self.last_trace.setdefault("no_op", []).append((event, now_ms))
            return self.state
        setattr(self, "_" + gate, closing)
        return self.state

    # ── the named drop (U03's exact naming, + pause; spec section 6.2) ───────
    def _drop(self, what, now_ms):
        reason = "dropped_" + self.state   # the strongest active gate names it
        self.last_trace.setdefault(reason, []).append((what, now_ms))
        self.last_trace.setdefault("drops", []).append(
            {"what": what, "at_ms": now_ms, "reason": reason,
             "gates": sorted(self.gates_active)})

    # ── the ONE delivery path ────────────────────────────────────────────────
    def _emit(self, action, now_ms):
        """ONE IntentEvent, synchronously, stamped with the session's clocks
        (spec section 5): the sink receives nothing else, ever."""
        issued_tick = (int(self._tick_source()) if self._tick_source
                       else (now_ms * PHYSICS_HZ) // 1000)
        event = IntentEvent(intent=action, issued_tick=int(issued_tick),
                            now_ms=now_ms)
        self._sink.emit(event)
        return event
