"""player_diagnostics.py -- I-S04: player-facing translation of REAL named refusals.

Card I-S04-PLAYER-DIAGNOSTICS (attempt d24bd30d38234a4cae33288048cce14f,
branch-9). Source of truth: pinned revision
9afbddcd90164b5544a16fd0bc72278d985eb6e3 of tools/monkey_campaign/product/
(input_settings.py, session_flow.py, state_feedback.py). Byte-exact copies of
everything this inventory was built from live in the attempt workspace's
reference/ directory; reference/EXTRACTION_LEDGER.json records each file's
sha256 (extracted via `git show`; the source repo was never edited).

RULE 0 (docs: CHIMERA-LAW): preregistered in PREREGISTRATION.md BEFORE this
file existed. Falsifiers, any one fails the build:
  F1  the player receives raw local paths (E:\\..., C:\\Users\\...).
  F2  a message claims an unsupported action (an action the pinned modules'
      real states do not offer).
  F3  unknown errors silently report success (or are mapped to a known
      refusal instead of the honest fallback).

WHAT THIS MODULE IS: a pure, stdlib-only, deterministic translator from the
NAMED failure identities those pinned modules actually produce to (message,
actions) records a player can read. It invents NO climbing capability and NO
new physical behavior -- U06's law (state_feedback.py: FORBIDDEN_CLAIM_TOKENS;
falling and recovery are deliberately never claimed) is inherited here: the
words this module ships never claim a capability no landed module provides.

THE INVENTORY IT SERVES (every identity cites its pinned source):
  * input_settings.Refusal codes -- input_settings.py, one per offense class:
    root_not_object:202, key_missing:211, key_unknown:213, schema_type:223,
    schema_unknown:228, bindings_type:256, binding_name_invalid:264,
    binding_type:270, action_unknown:276, action_unbound:287,
    axis_unknown:304+352, axis_missing:310+357, value_not_finite:329,
    value_out_of_range:334, io_error:398+403, json_corrupt:411+431,
    key_duplicate:419, not_finite_json:425 -- plus the two COMPUTED codes
    f"{key}_type" for the only two validator keys: sensitivity_type:299,
    invert_type:364. Real consequence, measured at the pinned revision: EVERY
    refusal loads U01's default settings (input_settings.py:145-151, 248-249,
    384-389) -- so every settings message says exactly that and never more.
  * session_flow named drops + failed transitions -- session_flow.py:
    key_press:280, key_release:286, mouse:294, decision_tick:305 (drops only
    happen while NOT playing, session_flow.py:279-306), flow_action:316
    ("action@state", the explicit-user-action-only law: the named no-op),
    restart_failed:340 (boot failed -> transition NOWHERE, the old scene
    stays), exit_failed:351 (teardown failed -> no transition, still running).
    Player-offered keys are grounded in DEFAULT_FLOW_BINDINGS:93-101 and the
    frozen TRANSITIONS table:102-110 -- nothing else is ever offered.

HONESTY MECHANICS:
  * Player text is COMPOSED from frozen templates plus, at most, one
    scrubbed, length-capped offense token parsed out of the refusal detail.
    The raw detail (paths, exception reprs, everything) goes to the
    SEPARATE `diagnostic` field, developer-facing only.
  * scrub(): drive-letter paths, backslash chains, UNC, file:// URIs,
    POSIX home/tmp paths and %ENV%/`${ENV}`/$ENV references are replaced
    with "[removed]" in ALL player-facing text, as a final defense pass.
  * Unknown is a first-class outcome: any identity outside the inventory
    (including flow trace kinds like "quiesced"/"transitions", which are not
    failures, and a flow drop claimed in a state the pinned module cannot
    produce it in) returns the UNKNOWN fallback: status "unknown", no
    actions, "Reference: <id>" in player text. It NEVER reports success.
  * correlation_id = sha256(name + unit-separator + raw detail + unit-
    separator + caller-supplied nonce), hex, truncated to 16 chars (64 bits,
    documented). No wall clock, no randomness, no environment reads.

Headless, deterministic, Python 3.11+, stdlib only.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field

__all__ = [
    "PlayerDiagnostic", "explain", "explain_settings_refusal",
    "explain_flow_drop", "explain_exception", "scrub", "correlation_id",
    "KNOWN_SETTINGS_CODES", "KNOWN_FLOW_KINDS", "supported_identities",
    "PINNED_REVISION",
]

PINNED_REVISION = "9afbddcd90164b5544a16fd0bc72278d985eb6e3"

_INPUT_SETTINGS = "tools/monkey_campaign/product/input_settings.py"
_SESSION_FLOW = "tools/monkey_campaign/product/session_flow.py"
_PIN = "pinned " + PINNED_REVISION


# ── determinism primitives (never a wall clock, never random) ────────────────
def correlation_id(name: str, detail: str, nonce: str = "") -> str:
    """Deterministic 64-bit correlation id: sha256 over the identity name, the
    raw detail and a CALLER-SUPPLIED nonce (never a wall clock, never the OS).
    Truncated to 16 hex chars -- collision risk 2^-64 per pair, fine for
    correlating a support conversation, and documented as such."""
    payload = "\x1f".join((name, detail, nonce))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


# ── the scrubber (falsifier F1's enforcer) ────────────────────────────────────
_REMOVED = "[removed]"

_SECRET_PATTERNS = (
    # Windows drive paths: E:\repo\secret\forest.bin, C:/Users/allen/...
    re.compile(r"[A-Za-z]:[\\/][^\s\"'<>|]*"),
    # UNC shares and backslash path chains: \\srv\share\x, \repo\secret\
    re.compile(r"\\\\[^\s\"'<>|]+"),
    re.compile(r"\\[^\s\\/:*?\"<>|]+(?:\\[^\s\\/:*?\"<>|]+)+"),
    # file URIs and POSIX home/tmp style absolute paths
    re.compile(r"file://[^\s\"'<>|]+", re.IGNORECASE),
    re.compile(r"(?:~/|/home/|/Users/|/root/|/tmp/|/var/|/etc/)[^\s\"'<>|]*"),
    # environment variable references, three syntaxes
    re.compile(r"%[A-Za-z_][A-Za-z0-9_]*%"),
    re.compile(r"\$\{[A-Za-z_][A-Za-z0-9_]*\}"),
    re.compile(r"\$[A-Za-z_][A-Za-z0-9_]*"),
)


def scrub(text: str) -> str:
    """Replace path-shaped and env-shaped substrings with [removed].

    Deterministic, order-fixed, stdlib only. Applied to every player-facing
    string this module emits (and to offense tokens before templating), so a
    raw local path can only survive if it matches NONE of these shapes --
    falsifier F1's test sweeps drive-letter paths through every identity.
    """
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub(_REMOVED, text)
    return text


def _offense_token(detail: str, limit: int = 48) -> str:
    """The one scrubbed, length-capped quoted token from a refusal detail
    (the pinned details name the offense in single quotes), or "". A token is
    scrubbed BEFORE it can enter player text; if anything suspicious remains
    after scrubbing the token is dropped whole -- a template without the
    token is always acceptable, a leaked path never is."""
    match = re.search(r"'([^']*)'", detail)
    if match is None:
        return ""
    token = scrub(match.group(1))
    if _REMOVED in token or "\\" in token or "/" in token:
        return _REMOVED
    if len(token) > limit:
        token = token[: limit - 3] + "..."
    return token


# ── the record ────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class PlayerDiagnostic:
    """One translation result.

    `message` and `actions` are PLAYER-facing (scrubbed; actions are only
    what the pinned modules' real states support). `diagnostic` is the
    DEVELOPER field: raw detail verbatim, origin citation, scrub decisions --
    paths and stack details belong here and nowhere else. `ok` is False by
    construction: a diagnostic is never a success record, so an unknown
    refusal can never be silently mapped to success (falsifier F3).
    """

    name: str
    status: str                 # "refused" | "dropped" | "failed" | "unknown"
    message: str
    actions: tuple = ()
    correlation_id: str = ""
    diagnostic: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        """ALWAYS False. This module translates failures; it never blesses
        one as success. (A successful operation simply needs no diagnostic.)"""
        return False

    def to_record(self) -> dict:
        """The JSON-able structured record (deterministic key order below)."""
        return {
            "name": self.name,
            "status": self.status,
            "ok": self.ok,
            "message": self.message,
            "actions": list(self.actions),
            "correlation_id": self.correlation_id,
            "diagnostic": dict(self.diagnostic),
        }

    def to_json(self) -> bytes:
        """Byte-identical JSON for equal diagnostics (sorted keys, fixed
        separators, one trailing newline) -- the determinism contract."""
        return (json.dumps(self.to_record(), sort_keys=True,
                           ensure_ascii=False, separators=(",", ":"),
                           allow_nan=False) + "\n").encode("utf-8")


def _diag(origin: str, name_raw: str, detail_raw: str, extra: dict | None = None) -> dict:
    record = {"origin": origin, "raw_name": name_raw, "raw_detail": detail_raw}
    if extra:
        record.update(extra)
    return record


# ── SETTINGS: input_settings.Refusal codes at the pinned revision ────────────
# Every entry: (player lead sentence template, grounded action strings, origin
# line(s)). {tok} slots receive scrub(_offense_token(detail)) or "".
# THE REAL CONSEQUENCE, cited above: every refusal -> default settings active.
# No settings message ever mentions a key or an in-game settings menu: at the
# pinned revision this surface is file load + defaults, nothing else (F2).
_A_FIX = "Fix the settings file, then load it again."
_A_DEFAULTS = "Default controls are active -- you can keep playing."
_A_REBIND = "Bind a key to the missing action in the settings file."

_SETTINGS_REFUSALS: dict[str, tuple[str, tuple, str]] = {
    "root_not_object": (
        "The settings file could not be used. Default controls are active.",
        (_A_FIX, _A_DEFAULTS), f"{_INPUT_SETTINGS}:201-205 ({_PIN})"),
    "key_missing": (
        "The settings file is missing a required section{tok}. "
        "Default controls are active.",
        (_A_FIX, _A_DEFAULTS), f"{_INPUT_SETTINGS}:210-211 ({_PIN})"),
    "key_unknown": (
        "The settings file has an entry this game does not recognize{tok}. "
        "Default controls are active.",
        (_A_FIX, _A_DEFAULTS), f"{_INPUT_SETTINGS}:212-217 ({_PIN})"),
    "schema_type": (
        "The settings file is from a different version. "
        "Default controls are active.",
        (_A_FIX, _A_DEFAULTS), f"{_INPUT_SETTINGS}:222-226 ({_PIN})"),
    "schema_unknown": (
        "The settings file is from a different version. "
        "Default controls are active.",
        (_A_FIX, _A_DEFAULTS), f"{_INPUT_SETTINGS}:227-232 ({_PIN})"),
    "bindings_type": (
        "A key binding in the settings file is not usable. "
        "Default controls are active.",
        (_A_FIX, _A_DEFAULTS), f"{_INPUT_SETTINGS}:254-259 ({_PIN})"),
    "binding_name_invalid": (
        "A key binding in the settings file is not usable. "
        "Default controls are active.",
        (_A_FIX, _A_DEFAULTS), f"{_INPUT_SETTINGS}:263-267 ({_PIN})"),
    "binding_type": (
        "A key binding in the settings file is not usable. "
        "Default controls are active.",
        (_A_FIX, _A_DEFAULTS), f"{_INPUT_SETTINGS}:269-273 ({_PIN})"),
    "action_unknown": (
        "The settings file names an action this game does not have{tok}. "
        "Default controls are active.",
        (_A_FIX, _A_DEFAULTS), f"{_INPUT_SETTINGS}:275-280 ({_PIN})"),
    "action_unbound": (
        "No key is bound to a required action{tok}. Default controls are "
        "active.",
        (_A_REBIND, _A_FIX, _A_DEFAULTS),
        f"{_INPUT_SETTINGS}:283-291 ({_PIN})"),
    "sensitivity_type": (
        "The mouse sensitivity setting is not a usable number. "
        "Default controls are active.",
        (_A_FIX, _A_DEFAULTS), f"{_INPUT_SETTINGS}:295-325 ({_PIN})"),
    "invert_type": (
        "The invert setting is not on or off. Default controls are active.",
        (_A_FIX, _A_DEFAULTS), f"{_INPUT_SETTINGS}:344-366 ({_PIN})"),
    "axis_unknown": (
        "The settings file names a control axis this game does not have. "
        "Default controls are active.",
        (_A_FIX, _A_DEFAULTS), f"{_INPUT_SETTINGS}:303-308,351-355 ({_PIN})"),
    "axis_missing": (
        "The settings file is missing a required axis setting. "
        "Default controls are active.",
        (_A_FIX, _A_DEFAULTS), f"{_INPUT_SETTINGS}:309-314,356-360 ({_PIN})"),
    "value_not_finite": (
        "The mouse sensitivity setting must be a normal number. "
        "Default controls are active.",
        (_A_FIX, _A_DEFAULTS), f"{_INPUT_SETTINGS}:328-332 ({_PIN})"),
    "value_out_of_range": (
        "The mouse sensitivity setting is outside the allowed range. "
        "Default controls are active.",
        (_A_FIX, _A_DEFAULTS), f"{_INPUT_SETTINGS}:333-338 ({_PIN})"),
    "io_error": (
        "The settings file could not be read. Default controls are active.",
        (_A_DEFAULTS,), f"{_INPUT_SETTINGS}:396-405 ({_PIN})"),
    "json_corrupt": (
        "The settings file is damaged. Default controls are active.",
        (_A_FIX, _A_DEFAULTS), f"{_INPUT_SETTINGS}:409-413,429-433 ({_PIN})"),
    "key_duplicate": (
        "The settings file lists an entry more than once{tok}. "
        "Default controls are active.",
        (_A_FIX, _A_DEFAULTS), f"{_INPUT_SETTINGS}:417-422 ({_PIN})"),
    "not_finite_json": (
        "The settings file contains a number that is not finite{tok}. "
        "Default controls are active.",
        (_A_FIX, _A_DEFAULTS), f"{_INPUT_SETTINGS}:423-428 ({_PIN})"),
}

KNOWN_SETTINGS_CODES = frozenset(_SETTINGS_REFUSALS)


def explain_settings_refusal(code: str, detail: str = "", *, nonce: str = ""
                             ) -> PlayerDiagnostic:
    """Translate one input_settings.Refusal (its .code and .detail verbatim).

    An unknown code is NOT guessed: it falls through to the honest unknown
    fallback (falsifier F3). The player message is template + scrubbed token
    only; the raw detail is preserved in the diagnostic field.
    """
    entry = _SETTINGS_REFUSALS.get(code)
    if entry is None:
        return _unknown("unknown_error", detail,
                        _diag(f"{_INPUT_SETTINGS} (Refusal)", code, detail,
                              {"note": "code is outside the pinned refusal "
                                       "inventory"}), nonce)
    template, actions, origin = entry
    token = _offense_token(detail)
    slot = f" ('{token}')" if token else ""
    message = scrub(template.format(tok=slot))
    return PlayerDiagnostic(
        name=code, status="refused", message=message, actions=tuple(actions),
        correlation_id=correlation_id(code, detail, nonce),
        diagnostic=_diag(origin, code, detail,
                         {"scrub_token": token}))


# ── FLOW: session_flow named drops and failed transitions ─────────────────────
# Grounded in the frozen table (session_flow.py:93-110): the ONLY player keys
# are Return=confirm, Escape=pause, R=restart, Q=exit, and the ONLY offered
# (state, action) pairs are rows of TRANSITIONS. The key names below mirror
# DEFAULT_FLOW_BINDINGS (session_flow.py:94-101) and the test parses the
# pinned bindings + transitions out of the extracted source bytes and checks
# every action sentence against them (falsifier F2's enforcer).
_KEY_FOR_ACTION = {"confirm": "Return", "pause": "Escape",
                   "restart": "R", "exit": "Q"}


def _action_sentence(action: str, state: str) -> str:
    """One player-readable imperative, grounded in the pair (state, action).
    `confirm` reads as start at attract and resume at paused (the pinned
    table's own two confirm rows, session_flow.py:103,105)."""
    verb = ("start" if state == "attract" else "resume") \
        if action == "confirm" else action
    return f"Press {_KEY_FOR_ACTION[action]} to {verb}."
_FLOW_STATE_GUIDANCE: dict[str, tuple[str, tuple, str]] = {
    "attract": (
        "Nothing is running yet. Press Return to start.",
        (("attract", "confirm"),),
        f"{_SESSION_FLOW}:103 TRANSITIONS ({_PIN})"),
    "playing": (
        "You are playing. Press Escape to pause, or Q to exit.",
        (("playing", "pause"), ("playing", "exit")),
        f"{_SESSION_FLOW}:104,108 TRANSITIONS ({_PIN})"),
    "paused": (
        "Paused. Press Return to resume, R to restart, or Q to exit.",
        (("paused", "confirm"), ("paused", "restart"), ("paused", "exit")),
        f"{_SESSION_FLOW}:105-107,109 TRANSITIONS ({_PIN})"),
    "exited": (
        "The session has ended. It cannot be resumed with a key.",
        (),
        f"{_SESSION_FLOW}:111-117 (terminal: no exited rows) ({_PIN})"),
}

# flow_action no-ops with a per-pair answer (the named "action@state" drop,
# session_flow.py:313-317 -- the explicit-user-action-only law).
_FLOW_ACTION_GUIDANCE: dict[tuple[str, str], tuple[str, tuple, str]] = {
    ("restart", "playing"): (
        "Restart works from pause. Press Escape to pause, then R to restart.",
        (("playing", "pause"), ("paused", "restart")),
        f"{_SESSION_FLOW}:104,106 TRANSITIONS ({_PIN})"),
    ("confirm", "playing"): (
        "You are already playing. Press Escape to pause.",
        (("playing", "pause"),),
        f"{_SESSION_FLOW}:104 TRANSITIONS ({_PIN})"),
    ("pause", "attract"): (
        "Nothing is running yet. Press Return to start.",
        (("attract", "confirm"),),
        f"{_SESSION_FLOW}:103 TRANSITIONS ({_PIN})"),
    ("restart", "attract"): (
        "Nothing is running yet. Press Return to start.",
        (("attract", "confirm"),),
        f"{_SESSION_FLOW}:103 TRANSITIONS ({_PIN})"),
    ("pause", "paused"): (
        "Already paused. Press Return to resume.",
        (("paused", "confirm"),),
        f"{_SESSION_FLOW}:105 TRANSITIONS ({_PIN})"),
}

# Lead sentences for the plain input drops (kinds at session_flow.py:280,286,
# 294,305 -- each only ever fires while NOT playing, :279-306).
_FLOW_DROP_LEADS: dict[str, tuple[str, str]] = {
    "key_press": ("That key does nothing right now.",
                  f"{_SESSION_FLOW}:279-282 ({_PIN})"),
    "key_release": ("That key does nothing right now.",
                    f"{_SESSION_FLOW}:284-288 ({_PIN})"),
    "mouse": ("Mouse input is not active right now.",
              f"{_SESSION_FLOW}:290-296 ({_PIN})"),
    "decision_tick": ("The game is not running right now.",
                      f"{_SESSION_FLOW}:298-307 ({_PIN})"),
}

_FLOW_FAILURES: dict[str, tuple[str, tuple, str, str]] = {
    "restart_failed": (
        "Restart did not finish. The current scene is still running. "
        "Press R to try again.",
        (("paused", "restart"),),
        f"{_SESSION_FLOW}:335-342 (boot failed -> transition NOWHERE)",
        _SESSION_FLOW),
    "exit_failed": (
        "Exit did not finish. The session is still running. "
        "Press Q to try again.",
        (("attract", "exit"), ("playing", "exit"), ("paused", "exit")),
        f"{_SESSION_FLOW}:343-353 (teardown failed -> no transition)",
        _SESSION_FLOW),
}

KNOWN_FLOW_KINDS = frozenset(_FLOW_DROP_LEADS) | frozenset(_FLOW_FAILURES) | {
    "flow_action"}

_STATES = ("attract", "playing", "paused", "exited")


def _flow_guidance(state: str | None) -> tuple[str, tuple, str] | None:
    if state in _FLOW_STATE_GUIDANCE:
        return _FLOW_STATE_GUIDANCE[state]
    return None


def explain_flow_drop(kind: str, detail: str = "", *, state: str | None = None,
                      nonce: str = "") -> PlayerDiagnostic:
    """Translate one session_flow named drop or failed transition.

    `kind` is last_trace['dropped'][-1]['kind'] (or the trace key
    restart_failed / exit_failed). `state` is SessionFlow.state at the drop;
    flow_action's detail is the pinned "action@state" string
    (session_flow.py:316). Honesty rules enforced here:
      * a drop claimed in a state the pinned module cannot produce it in
        (e.g. key_press while playing) returns the UNKNOWN fallback -- the
        translator refuses what the source cannot produce (F2);
      * a state outside session_flow.STATES returns the UNKNOWN fallback;
      * trace keys that are not failures ("quiesced", "transitions",
        "restart_path", "dropped") are NOT translated into failure messages
        -- they get the unknown fallback, never a known mapping (F3).
    """
    if kind == "flow_action":
        action, _, at_state = detail.partition("@")
        at_state = at_state or (state or "")
        pair = (action, at_state)
        entry = _FLOW_ACTION_GUIDANCE.get(pair)
        if entry is not None:
            message, actions, origin = entry
        elif at_state in _FLOW_STATE_GUIDANCE:
            message, actions, origin = _FLOW_STATE_GUIDANCE[at_state]
            message = "That key does nothing here. " + message
        else:
            return _unknown("unknown_error", detail,
                            _diag(f"{_SESSION_FLOW}:316 flow_action",
                                  kind, detail,
                                  {"note": f"state {at_state!r} is outside "
                                           "session_flow.STATES"}), nonce)
        message = scrub(message)
        return PlayerDiagnostic(
            name=f"flow_action:{action}@{at_state}", status="dropped",
            message=message,
            actions=tuple(_action_sentence(pair[1], pair[0])
                         for pair in actions),
            correlation_id=correlation_id(kind, detail, nonce),
            diagnostic=_diag(origin, kind, detail,
                             {"grounding": [list(p) for p in actions]}))

    failure = _FLOW_FAILURES.get(kind)
    if failure is not None:
        message, actions, origin, module = failure
        return PlayerDiagnostic(
            name=kind, status="failed", message=scrub(message),
            actions=tuple(_action_sentence(pair[1], pair[0])
                         for pair in actions),
            correlation_id=correlation_id(kind, detail, nonce),
            diagnostic=_diag(origin, kind, detail,
                             {"grounding": [list(p) for p in actions]}))

    lead = _FLOW_DROP_LEADS.get(kind)
    if lead is None:
        return _unknown("unknown_error", detail,
                        _diag(f"{_SESSION_FLOW} (last_trace)", kind, detail,
                              {"note": "kind is not a named drop or a "
                                       "failure in the pinned source"}),
                        nonce)
    lead_text, origin = lead
    if state not in _FLOW_STATE_GUIDANCE:
        return _unknown("unknown_error", detail,
                        _diag(origin, kind, detail,
                              {"note": f"state {state!r} is outside "
                                       "session_flow.STATES"}), nonce)
    if state == "playing":
        # The pinned module drops these ONLY while not playing
        # (session_flow.py:279-306); a "drop while playing" identity is not
        # a real state, so it is refused, not translated.
        return _unknown("unknown_error", detail,
                        _diag(origin, kind, detail,
                              {"note": "the pinned module cannot produce a "
                                       f"{kind} drop while playing"}), nonce)
    guidance, actions, g_origin = _FLOW_STATE_GUIDANCE[state]
    message = scrub(f"{lead_text} {guidance}")
    return PlayerDiagnostic(
        name=f"{kind}@{state}", status="dropped", message=message,
        actions=tuple(_action_sentence(pair[1], pair[0])
                         for pair in actions),
        correlation_id=correlation_id(kind, f"{detail}@{state}", nonce),
        diagnostic=_diag(origin, kind, detail,
                         {"state": state,
                          "grounding": [list(p) for p in actions]}))


# ── the honest unknown fallback (falsifier F3's enforcer) ─────────────────────
def _unknown(name: str, detail: str, diagnostic: dict, nonce: str
             ) -> PlayerDiagnostic:
    """The ONLY honest answer for an unrecognized identity: nothing was
    claimed, nothing was changed, no action is offered, the player gets a
    deterministic reference code, and the developer field keeps the truth."""
    cid = correlation_id(name, detail, nonce)
    return PlayerDiagnostic(
        name=name, status="unknown",
        message=("Something went wrong on our side. Nothing was changed. "
                 f"Reference: {cid}."),
        actions=(), correlation_id=cid, diagnostic=diagnostic)


def explain_exception(exc: BaseException, *, nonce: str = ""
                      ) -> PlayerDiagnostic:
    """Translate an exception object.

    Refusal-shaped objects (a .code string in the pinned inventory, with
    optional .detail) translate through the settings table; everything else
    -- including FlowError, raw OSErrors, anything at all -- gets the honest
    unknown fallback. The repr (paths, stack facts, memory addresses) is
    preserved ONLY in the diagnostic field; player text is template-only.
    """
    code = getattr(exc, "code", None)
    if isinstance(code, str) and code in KNOWN_SETTINGS_CODES:
        detail = getattr(exc, "detail", "")
        if not isinstance(detail, str):
            detail = repr(detail)
        result = explain_settings_refusal(code, detail, nonce=nonce)
        return PlayerDiagnostic(
            name=result.name, status=result.status, message=result.message,
            actions=result.actions,
            correlation_id=correlation_id(code, detail, nonce),
            diagnostic=_diag(result.diagnostic["origin"], code, detail,
                             {"exception_type": type(exc).__name__,
                              "exception_repr": repr(exc)}))
    return _unknown("unknown_error", repr(exc),
                    _diag("exception", type(exc).__name__, repr(exc),
                          {"note": "not a pinned refusal shape",
                           "exception_type": type(exc).__name__}), nonce)


def explain(name: str, detail: str = "", *, state: str | None = None,
            nonce: str = "") -> PlayerDiagnostic:
    """Translate a failure identity by name.

    Known settings refusal codes and known flow kinds dispatch to their
    pinned translations. ANYTHING ELSE -- a typo, a future code, a trace key
    like "quiesced", the load statuses "loaded"/"first_run" -- gets the
    honest unknown fallback: never a known message, never success (F3).
    """
    if name in KNOWN_SETTINGS_CODES:
        return explain_settings_refusal(name, detail, nonce=nonce)
    if name in KNOWN_FLOW_KINDS:
        return explain_flow_drop(name, detail, state=state, nonce=nonce)
    return _unknown("unknown_error", detail,
                    _diag("explain", name, detail,
                          {"note": "name is outside the pinned failure "
                                   "inventory"}), nonce)


def supported_identities() -> tuple[str, ...]:
    """Every failure identity this module translates (deterministic order).
    Anything not listed here gets the unknown fallback -- by construction."""
    names = sorted(KNOWN_SETTINGS_CODES)
    names += sorted(f"flow_action:{a}@{s}"
                    for (a, s) in _FLOW_ACTION_GUIDANCE)
    names += sorted(f"{kind}@{state}"
                    for kind in _FLOW_DROP_LEADS for state in _FLOW_STATE_GUIDANCE
                    if state != "playing")
    names += sorted(_FLOW_FAILURES)
    return tuple(names)
