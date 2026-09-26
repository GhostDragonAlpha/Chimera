"""state_feedback.py -- M-U05b/U06: readable control and state feedback (v1).

U06, verbatim (MONKEY_COMPLETION_MAP.md:108): "Prompts distinguish available
climb, unavailable support, holding, falling and recovery without claiming
nonexistent capabilities. Minimal player language; engineering diagnostics
stay optional."

THE HONESTY LAW (prereg: agents/U05b_amendments_U06/PREREGISTRATION.md §2,
frozen before this file existed): every prompt is a PURE FUNCTION of the
observed state of the four LANDED modules -- and nothing else:

  * X02 `session_flow.py`   -- the session state (attract/playing/paused/exited)
  * U03 `focus_policy.py`   -- the input-surface state (focused/blurred/disconnected)
  * U05 `climb_intent.py`   -- the intent channel (gates, held keys, the
                               delivered IntentEvent stream, named drops)
  * U01 `input_mapper.py`   -- the walk side (held walk keys, record liveness
                               via InputMapper.is_expired -- U01's own law)

WHAT IS NEVER CLAIMED (no landed module provides it):
  * CLIMBING as a capability -- no climb skill exists (K-series future). A
    delivered climb_request renders as "Climb intent sent (no climb skill
    loaded)" -- the brief's example line -- never "climbing".
  * HOLDING as a game state -- `held` is an INPUT fact (keys physically held,
    one consumed edge). It renders as "Climb key held", never "holding on".
  * FALLING -- no live airborne/contact fact exists anywhere (F04's L1 is an
    offline geometric verification, not a runtime state). No row, no word.
  * RECOVERY as a skill -- W09 future. Gate-clearing simply lets the ladder
    fall through to walking/climb_ready; the word never appears.
  * SUPPORT/CONTACT knowledge -- nothing beyond F04's L1 (also not a live
    source). Unavailability renders only as INPUT-gate facts ("keys dropped").

Headless by construction: the observation is DATA the harness assembled from
public module attributes; this module queries no engine, reads no wall clock,
opens no window, injects no input. The renderer refuses what it cannot name
(UnknownStateError) instead of guessing -- and as an IntentEvent consumer it
enforces spec section 7.1's check-the-version law on any event it renders.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

# The four declared state sources -- imported, never redeclared: a second
# copy of a frozen vocabulary is exactly where a silent divergence lives.
import input_mapper as _im        # noqa: E402  (U01: walk command state)
import focus_policy as _fp        # noqa: E402  (U03: input-surface state)
import session_flow as _sf        # noqa: E402  (X02: session state)
import climb_intent as _ci        # noqa: E402  (U05: the intent channel)

__all__ = [
    "Observation", "Feedback", "UnknownStateError", "render", "observe",
    "walk_record_live", "STATE_KEYS", "PROMPTS", "SOURCE_MAP",
    "FORBIDDEN_CLAIM_TOKENS",
]


class UnknownStateError(ValueError):
    """An observed value is outside the source modules' declared vocabularies
    -- the renderer refuses what it cannot name (never guesses a state)."""


# ── THE FROZEN VOCABULARY (prereg §2.1-2.2; every key cites its sources) ────────
STATE_KEYS = (
    "session_menu", "session_paused", "session_exited",     # X02
    "input_disconnected", "input_blurred",                  # U03 / U05 gates
    "intent_paused",                                        # U05 gate
    "climb_sent", "let_go_sent",                            # U05 delivered stream
    "climb_key_held",                                       # U05 input fact
    "walking",                                              # U01 walk stream
    "climb_ready",                                          # U05 ready + disclaimer
)

_PROMPT = " — "   # the prompt separator (player language, one dash)

PROMPTS = {
    "session_menu":        f"Menu{_PROMPT}controls inactive",
    "session_paused":      f"Paused{_PROMPT}controls inactive",
    "session_exited":      f"Exited{_PROMPT}controls inactive",
    "input_disconnected":  f"No input device{_PROMPT}keys dropped",
    "input_blurred":       f"Window lost focus{_PROMPT}keys dropped",
    "intent_paused":       f"Paused{_PROMPT}controls inactive",
    "climb_sent":          f"Climb intent sent (no climb skill loaded)",
    "let_go_sent":         f"Let-go intent sent (nothing to release)",
    "climb_key_held":      f"Climb key held (ask already sent)",
    "walking":             f"Walking{_PROMPT}movement input active",
    # climb_ready interpolates the LIVE bindings table (data, spec §9): the
    # key name comes from the observation, the disclaimer is mandatory:
    "climb_ready":         f"Climb key ready ({{key}}){_PROMPT}no climb skill loaded",
}

# where each state_key's truth comes from (the structured record's citations)
_P = "tools/monkey_campaign/product/"
SOURCE_MAP = {
    "session_menu":       (_P + "session_flow.py",),
    "session_paused":     (_P + "session_flow.py",),
    "session_exited":     (_P + "session_flow.py",),
    "input_disconnected": (_P + "focus_policy.py", _P + "climb_intent.py"),
    "input_blurred":      (_P + "focus_policy.py", _P + "climb_intent.py"),
    "intent_paused":      (_P + "climb_intent.py",),
    "climb_sent":         (_P + "climb_intent.py",),
    "let_go_sent":        (_P + "climb_intent.py",),
    "climb_key_held":     (_P + "climb_intent.py",),
    "walking":            (_P + "input_mapper.py",),
    "climb_ready":        (_P + "climb_intent.py",),
}

# the field-level citations (every displayed state cites its source module)
FIELD_SOURCES = {
    "session_state":    "x02: session_flow.py (STATES)",
    "focus_state":      "u03: focus_policy.py (FOCUSED/BLURRED/DISCONNECTED)",
    "intent_gates":     "u05: climb_intent.py (GATE_DOMINANCE / gates_active)",
    "intent_held":      "u05: climb_intent.py (held -- an INPUT fact)",
    "walk_held":        "u01: input_mapper.py (held)",
    "walk_command_live": "u01: input_mapper.py (InputMapper.is_expired -- U01's "
                         "declared expiry law, no new staleness rule)",
    "flash_event":      "u05: climb_intent.py (the delivered IntentEvent stream)",
    "last_drop":        "u05: climb_intent.py (last_trace['drops'][-1], named)",
    "climb_key":        "u05: climb_intent.py (bindings -- data, spec §9)",
    "now_ms":           "harness: injected session milliseconds (never a wall clock)",
}

# ── THE FROZEN FORBIDDEN CLAIM TOKENS (prereg §2.4; the fuzz scans for these) ───
FORBIDDEN_CLAIM_TOKENS = (
    "climbing", "climbed", "grabbed", "grabbing", "grip", "hanging", "holding",
    "attached", "attaching", "falling", "fell", "recovered", "recovering",
    "recovery", "branch", "trunk", "contact", "support", "snap", "auto-snap",
    "climb available", "unavailable", "skill active", "skill engaged",
)


def walk_record_live(records, now_ms):
    """U01's declared consumer-side liveness law, verbatim: a walk record
    commands until `InputMapper.is_expired` says otherwise (VALID_MS = 2
    intervals). NO new staleness rule is invented here."""
    return bool(records) and not _im.InputMapper.is_expired(records[-1],
                                                            now_ms)


@dataclass(frozen=True)
class Observation:
    """The observed state of the four landed modules -- pure data.

    Assembled by the harness from PUBLIC attributes (`observe()` below does
    exactly that and nothing more). Every field cites its source module
    (FIELD_SOURCES). There is deliberately NO field for falling, recovery,
    support, contact, or any climb capability: no landed module provides one,
    and a field the renderer cannot honestly fill is the one field that must
    not exist.
    """

    session_state: str            # X02 SessionFlow.state
    focus_state: str              # U03 FocusPolicy.state
    intent_gates: frozenset       # U05 ClimbIntentChannel.gates_active
    intent_held: frozenset        # U05 ClimbIntentChannel.held (INPUT fact)
    walk_held: frozenset          # U01 InputMapper.held
    walk_command_live: bool       # U01: an unexpired walk record exists
    climb_key: str = "Space"      # U05 data-defaults (bindings are data, §9)
    let_go_key: str = "C"
    flash_event: object = None    # U05: the delivered event surfaced THIS call
    last_drop: dict = None        # U05: last_trace["drops"][-1] (named)
    now_ms: int = None            # the injected ms of THIS render (or None)

    def __post_init__(self):
        # refuse what we cannot name -- a renderer that guesses is a renderer
        # that fabricates (the parser's law; every raise names its source)
        if self.session_state not in _sf.STATES:
            raise UnknownStateError(
                f"session_state {self.session_state!r} is not one of "
                f"{_sf.STATES} (source: x02 session_flow.py)")
        if self.focus_state not in (_fp.FOCUSED, _fp.BLURRED,
                                    _fp.DISCONNECTED):
            raise UnknownStateError(
                f"focus_state {self.focus_state!r} is not one of "
                f"({ _fp.FOCUSED!r}, {_fp.BLURRED!r}, {_fp.DISCONNECTED!r}) "
                "(source: u03 focus_policy.py)")
        for g in self.intent_gates:
            if g not in _ci.GATE_DOMINANCE:
                raise UnknownStateError(
                    f"intent gate {g!r} is not one of {_ci.GATE_DOMINANCE} "
                    "(source: u05 climb_intent.py)")
        for fname, keys in (("intent_held", self.intent_held),
                            ("walk_held", self.walk_held)):
            if not isinstance(keys, (frozenset, set, tuple, list)) or \
                    any(not isinstance(k, str) for k in keys):
                raise UnknownStateError(
                    f"{fname} must be a set of key-name strings, got "
                    f"{keys!r}")
        if not isinstance(self.walk_command_live, bool):
            raise UnknownStateError(
                f"walk_command_live must be a bool, got "
                f"{self.walk_command_live!r} (source: u01 input_mapper.py)")
        for fname, key in (("climb_key", self.climb_key),
                           ("let_go_key", self.let_go_key)):
            if not isinstance(key, str) or not key:
                raise UnknownStateError(
                    f"{fname} must be a non-empty binding name, got {key!r} "
                    "(source: u05 climb_intent.py bindings)")
        ev = self.flash_event
        if ev is not None:
            # spec section 7.1: a consumer CHECKS THE VERSION, refuses loudly,
            # never guesses -- state_feedback is an IntentEvent consumer.
            # AMR-1's lesson applies consumer-side too: True == 1, so the type
            # check must come FIRST or a bool smuggles through.
            evv = getattr(ev, "intent_version", None)
            if (isinstance(evv, bool) or not isinstance(evv, int)
                    or evv != _ci.INTENT_VERSION):
                raise UnknownStateError(
                    f"flash_event intent_version {evv!r} != "
                    f"{_ci.INTENT_VERSION} -- a foreign version is NOT "
                    "interpretable (spec §7.1; bools refused, AMR-1's law)")
            if getattr(ev, "intent", None) not in _ci.INTENTS:
                raise UnknownStateError(
                    f"flash_event intent {getattr(ev, 'intent', None)!r} is "
                    f"outside the frozen vocabulary {_ci.INTENTS}")
        if self.now_ms is not None and (not isinstance(self.now_ms, int)
                                        or isinstance(self.now_ms, bool)):
            raise UnknownStateError(
                f"now_ms must be an injected integer millisecond or None, "
                f"got {self.now_ms!r}")


@dataclass(frozen=True)
class Feedback:
    """The renderer's output: ONE minimal prompt line + the structured state
    record (with per-field provenance). `diagnostics` is OPTIONAL engineering
    language and is empty unless the caller asks for it."""

    state_key: str
    prompt: str
    diagnostics: str
    sources: dict          # field -> citation (FIELD_SOURCES) + state sources
    observed: dict         # the raw observed values, verbatim

    def record(self):
        """The JSON-able structured state record."""
        return {"state_key": self.state_key, "prompt": self.prompt,
                "diagnostics": self.diagnostics,
                "sources": dict(self.sources),
                "observed": dict(self.observed)}


def observe(session_flow, focus_policy, intent_channel, mapper=None, *,
            flash_event=None, now_ms=None, walk_command_live=False,
            last_drop=None):
    """Assemble an Observation from real module objects -- PUBLIC attribute
    reads only (state, gates_active, held, bindings); no engine queries, no
    wall clock, no private attribute is touched."""
    bindings = intent_channel.bindings
    climb_keys = sorted(k for k, v in bindings.items()
                        if v == _ci.CLIMB_REQUEST)
    letgo_keys = sorted(k for k, v in bindings.items() if v == _ci.LET_GO)
    return Observation(
        session_state=session_flow.state,
        focus_state=focus_policy.state,
        intent_gates=frozenset(intent_channel.gates_active),
        intent_held=frozenset(intent_channel.held),
        walk_held=frozenset(mapper.held) if mapper is not None else frozenset(),
        walk_command_live=bool(walk_command_live),
        climb_key=climb_keys[0] if climb_keys else "",
        let_go_key=letgo_keys[0] if letgo_keys else "",
        flash_event=flash_event,
        last_drop=last_drop,
        now_ms=now_ms,
    )


def _diagnostics(obs, key):
    """The OPTIONAL engineering line (never shown unless asked for). Pure
    derivation from the observation; cites sources; asserts nothing about
    capabilities."""
    parts = [
        f"state={key}",
        f"session={obs.session_state} [x02]",
        f"focus={obs.focus_state} [u03]",
        f"intent_gates={','.join(sorted(obs.intent_gates)) or 'none'} [u05]",
        f"intent_held={','.join(sorted(obs.intent_held)) or 'none'} [u05]",
        f"walk_held={','.join(sorted(obs.walk_held)) or 'none'} [u01]",
        f"walk_live={obs.walk_command_live} [u01]",
    ]
    if obs.last_drop is not None:
        parts.append(f"last_drop={obs.last_drop} [u05]")
    if obs.flash_event is not None:
        age = (None if obs.now_ms is None
               else obs.now_ms - obs.flash_event.now_ms)
        parts.append(f"flash={obs.flash_event.intent} "
                     f"(age={age if age is not None else 'n/a'} ms; intents "
                     "do not expire at v1 [spec §7.3])")
    # cross-source consistency (harness wiring), diagnostics ONLY:
    focus_gate = (None if obs.focus_state == _fp.FOCUSED else obs.focus_state)
    if focus_gate is not None and focus_gate not in obs.intent_gates:
        parts.append(f"note: focus={focus_gate} but the intent channel does "
                     f"not carry that gate (harness wiring?)")
    for g in sorted(obs.intent_gates):
        if g in ("blurred", "disconnected") and obs.focus_state != g:
            parts.append(f"note: intent gate={g} but focus={obs.focus_state} "
                         "(harness wiring?)")
    return "; ".join(parts)


def render(obs, *, diagnostics=False):
    """THE display model (pure): Observation -> Feedback.

    The ladder (prereg §2.3, frozen; first match wins -- deterministic):
      1. session not playing        -> the session row      [x02]
      2. disconnected (focus|gates) -> input_disconnected  [u03/u05]
      3. blurred (focus|gates)      -> input_blurred       [u03/u05]
      4. paused in intent gates     -> intent_paused       [u05]
      5. a flash event is surfaced  -> climb_sent/let_go_sent [u05 stream]
      6. intent keys held           -> climb_key_held      [u05 input fact]
      7. walk keys held/live record -> walking             [u01]
      8. otherwise (all gates open) -> climb_ready         [u05, + disclaimer]
    """
    if obs.session_state != _sf.PLAYING:
        key = {_sf.ATTRACT: "session_menu", _sf.PAUSED: "session_paused",
               _sf.EXITED: "session_exited"}[obs.session_state]
    elif (obs.focus_state == _fp.DISCONNECTED
            or _ci.DISCONNECTED in obs.intent_gates):
        key = "input_disconnected"
    elif obs.focus_state == _fp.BLURRED or _ci.BLURRED in obs.intent_gates:
        key = "input_blurred"
    elif _ci.PAUSED in obs.intent_gates:
        key = "intent_paused"
    elif obs.flash_event is not None:
        key = ("climb_sent" if obs.flash_event.intent == _ci.CLIMB_REQUEST
               else "let_go_sent")
    elif obs.intent_held:
        key = "climb_key_held"
    elif obs.walk_held or obs.walk_command_live:
        key = "walking"
    else:
        key = "climb_ready"        # "available climb" honestly: the channel
                                   # would HEAR the key -- and no skill exists

    prompt = PROMPTS[key]
    if key == "climb_ready":       # the ONE interpolated row: the LIVE binding
        prompt = prompt.format(key=obs.climb_key)   # name is data (spec §9)

    sources = dict(FIELD_SOURCES)
    sources["state_key"] = SOURCE_MAP[key]
    observed = {
        "session_state": obs.session_state, "focus_state": obs.focus_state,
        "intent_gates": sorted(obs.intent_gates),
        "intent_held": sorted(obs.intent_held),
        "walk_held": sorted(obs.walk_held),
        "walk_command_live": obs.walk_command_live,
        "climb_key": obs.climb_key, "let_go_key": obs.let_go_key,
        "flash_event": (None if obs.flash_event is None
                        else obs.flash_event.canonical_fields()),
        "last_drop": obs.last_drop, "now_ms": obs.now_ms,
    }
    return Feedback(state_key=key, prompt=prompt,
                    diagnostics=_diagnostics(obs, key) if diagnostics else "",
                    sources=sources, observed=observed)
