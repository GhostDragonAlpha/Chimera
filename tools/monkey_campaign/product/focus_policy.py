"""focus_policy.py -- M-U03: focus loss, disconnect, and the age floor.

U03, verbatim: "Alt-tab, disconnect and key release clear or age commands
under a declared policy; no stuck movement." Constraint: "Keep operator
desktop focus and processes untouched."

THIS MODULE IS A POLICY LAYER ON U01'S UNTOUCHED MAPPER (prereg:
agents/U03_focus/PREREGISTRATION.md, frozen before this build; the mapper:
product/input_mapper.py, READ-ONLY here -- imported, never edited). Its
hooks were named by U01's integration note and both EXIST, so no amendment
is needed:

  * mapper.release_all(now)  -- every held key released EXACTLY as a
    physical release. This policy deliberately does NOT add a hard-clear
    record: one final zero-advance record would flip the seam into its
    LIVE-ZERO state (command_record.py:81-83 -- a live zero-advance walk
    target, a DIFFERENT seam state from inert, discovery_note.md 1.3),
    while the physical-release path lets the mapper's own frozen decay
    land on exact zero and then go silent, restoring the inert path.
  * mapper.is_expired(rec, now) -- the consumer-side expiry floor, applied
    here AT EMISSION: a record that already exceeds the max-age when the
    gate would hand it on is dropped, by name, never emitted (belt over
    decay).

THE FROZEN POLICY (prereg; every number below is IMPORTED from U01's
module -- this file declares zero numeric constants of its own):
  1. BLUR   -> release_all (physical-release semantics; the mapper's decay
     runs untouched: linear samples, exact zero at or before the decay
     deadline, then silence).
  2. DISCONNECT -> the same release_all, PLUS the named disconnected
     state. While blurred OR disconnected, NEW press/mouse intents are
     dropped and NAMED (an unfocused or disconnected surface cannot
     honestly produce intent -- accepting it would manufacture phantom
     movement, the stuck-movement family this row kills). Releases always
     pass (they can only reduce demand). Ticks always pass (the in-flight
     decay must REACH the sink -- the declared decay-to-zero then silence).
  3. AGE FLOOR -> every mapper record passes the expiry gate before the
     real sink; expired records are dropped and named.
  4. RECOVERY -> on_focus / on_reconnect clear their own named state only;
     the mapper is guaranteed key-free (the event released it), so the
     next accepted press arms a fresh grid. No phantom keys, no replayed
     tail.
  5. IDEMPOTENCE -> repeated events while already in the state are no-ops,
     recorded by name. A repeated release_all must never restart a decay
     tail: restarting would extend movement past the decay deadline.

THE NO-STUCK INVARIANT (what the tests measure): after ANY
release/blur/disconnect event at instant E, the sink never again receives
a positive-speed record later than E plus the decay deadline, the stream
lands on an exact-zero record and then goes silent, and every delivered
record stays inside U01's frozen bounds. A fresh accepted press after
recovery is a NEW command, not a resurrection of the old one.

Headless by construction: clocks are injected integer milliseconds, all
events arrive as plain method calls from the harness, and this module
never reads a wall clock, never opens a window, never injects operator
input anywhere, never spawns or signals a process.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

# THE SEAM'S TYPE AND U01'S FROZEN NUMBERS -- imported, never redeclared:
# a second copy of a frozen constant is exactly where a silent divergence
# lives (the prereg's consistency falsifier checks object identity below).
from tools.science_funnel.typeb_export.command_record import CommandRecord  # noqa: E402,F401
import input_mapper as _im                                                  # noqa: E402

__all__ = [
    "FocusPolicy",
    "FOCUSED", "BLURRED", "DISCONNECTED",
    "MAX_AGE_MS",
    "RELEASE_DECAY_MS", "VALID_MS", "INTERVAL_MS", "EXPIRY_TICKS",
    "V_MAX_IN_BAND_M_S", "OMEGA_MAX_RAD_S",
]

# ── the frozen numbers, aliased by identity (prereg P2) ─────────────────────
RELEASE_DECAY_MS = _im.RELEASE_DECAY_MS    # the decay deadline (physical release)
VALID_MS = _im.VALID_MS                    # consumer-side max age
MAX_AGE_MS = VALID_MS                      # the gate's threshold: the SAME object
INTERVAL_MS = _im.INTERVAL_MS              # the mapper owns the grid; policy never touches it
EXPIRY_TICKS = _im.EXPIRY_TICKS            # max age in physics ticks (strictly-greater test)
V_MAX_IN_BAND_M_S = _im.V_MAX_IN_BAND_M_S  # the band ceiling (the mapper's own bound)
OMEGA_MAX_RAD_S = _im.OMEGA_MAX_RAD_S      # the input-side steer bound

FOCUSED = "focused"
BLURRED = "blurred"
DISCONNECTED = "disconnected"     # the named state: queryable, never a silent flag


class _Gate:
    """The expiry floor, sitting IN the mapper's emission path: the mapper's
    own sink IS this gate, so a record either passes through here to the
    real sink or is dropped here, named. There is no second path -- a gate
    beside the mapper would see every record twice and gate nothing."""

    def __init__(self, owner):
        self._owner = owner
        self._passed = []                  # what got through this tick

    def reset(self):
        self._passed = []

    @property
    def passed(self):
        return self._passed

    def emit(self, record):
        o = self._owner
        if o._mapper.is_expired(record, o._gate_now):
            o.gate_stats["expired_at_gate"] += 1
            o.last_trace.setdefault("expired_at_gate", []) \
                .append((record.issued_tick, o._gate_now))
            return
        o.gate_stats["passed"] += 1
        self._passed.append(record)
        o._sink.emit(record)


class FocusPolicy:
    """Drives a U01 InputMapper through focus/disconnect events and gates
    its output through the expiry floor.

    THE WIRING (one emission path only): this policy hands ITSELF in as the
    mapper's sink through `mapper_factory` -- records flow mapper -> gate ->
    the real sink, and nowhere else. Bindings, sensitivity, and the tick
    source remain the CALLER's decisions, made inside the factory:

        sink = MockSink()                    # or the live harness' real sink
        fp = FocusPolicy(sink)               # default: a plain InputMapper
        fp = FocusPolicy(sink, mapper_factory=lambda gate: InputMapper(
            gate, tick_source=my_physics_tick_counter))  # the caller's clock
        fp.press("W", now_ms=1000)           # input surface (same shape as the
        fp.release("W", now_ms=1100)         # mapper's own)
        fp.tick(now_ms)
        fp.on_blur(now_ms)                   # alt-tab: everything off, decay to
                                             # silence under the mapper's policy
        fp.on_focus(now_ms)                  # back: clean re-arm, no phantom keys
        fp.on_disconnect(now_ms)             # device gone: release + NAMED state
        fp.on_reconnect(now_ms)
        fp.state                             # "focused" / "blurred" /
                                             # "disconnected" (disconnect wins)

    The gate is transparent when healthy: with the mapper's own clock the
    age of a record at emission is zero, so the floor drops nothing; it
    fires only when a record is already stale at delivery (e.g. an
    injected tick source that stalled while the harness clock advanced).
    """

    def __init__(self, sink, mapper_factory=None):
        if not hasattr(sink, "emit"):
            raise TypeError("sink must provide emit(record) -- the policy can "
                            "only gate commands, never touch state")
        self._sink = sink
        self._gate_now = 0
        self._gate = _Gate(self)
        factory = mapper_factory if mapper_factory is not None else _im.InputMapper
        self._mapper = factory(self._gate)
        for need in ("press", "release", "tick", "release_all", "is_expired", "held"):
            if not hasattr(self._mapper, need):
                raise TypeError(f"mapper must provide {need}() -- this policy "
                                f"drives U01's mapper surface, nothing else")
        self._blurred = False
        self._disconnected = False
        self.last_trace = {}               # house style: the parse trace
        self.gate_stats = {"passed": 0, "expired_at_gate": 0}

    # ── state ────────────────────────────────────────────────────────────────
    @property
    def mapper(self):
        """The wrapped mapper (read access for the harness and the tests)."""
        return self._mapper

    @property
    def held(self):
        return self._mapper.held

    @property
    def state(self):
        """The named policy state. DISCONNECTED dominates BLURRED: a device
        that is gone is the stronger claim about the input surface."""
        if self._disconnected:
            return DISCONNECTED
        if self._blurred:
            return BLURRED
        return FOCUSED

    @property
    def _gate_open(self):
        """Whether NEW intent (press/mouse) is accepted. Closed while blurred
        or disconnected; a release is never gated either way."""
        return not (self._blurred or self._disconnected)

    # ── the policy events ────────────────────────────────────────────────────
    def on_blur(self, now_ms):
        """The window lost focus: release everything exactly as a physical
        release; the mapper's decay carries the stream to silence."""
        return self._focus_event("blur", now_ms)

    def on_focus(self, now_ms):
        """The window regained focus: clear the blurred state. Clean re-arm:
        the mapper is already key-free; the next accepted press starts a
        fresh grid."""
        return self._focus_event("focus", now_ms)

    def on_disconnect(self, now_ms):
        """The input device is gone: release everything AND raise the named
        disconnected state (new intent is dropped until reconnect)."""
        return self._device_event("disconnect", now_ms)

    def on_reconnect(self, now_ms):
        """The device is back: clear the disconnected state. Clean re-arm as
        for focus. (Focus state is independent and untouched.)"""
        return self._device_event("reconnect", now_ms)

    def _focus_event(self, name, now_ms):
        self.last_trace.setdefault("events", []).append((name, int(now_ms)))
        if name == "blur":
            if self._blurred:
                self.last_trace.setdefault("no_op", []).append((name, int(now_ms)))
                return self.state
            self._blurred = True
            self._release_everything(name, now_ms)
        else:                                            # focus
            if not self._blurred:
                self.last_trace.setdefault("no_op", []).append((name, int(now_ms)))
                return self.state
            self._blurred = False
            self._record_rearm(name, now_ms)
        return self.state

    def _device_event(self, name, now_ms):
        self.last_trace.setdefault("events", []).append((name, int(now_ms)))
        if name == "disconnect":
            if self._disconnected:
                self.last_trace.setdefault("no_op", []).append((name, int(now_ms)))
                return self.state
            self._disconnected = True
            self._release_everything(name, now_ms)
        else:                                            # reconnect
            if not self._disconnected:
                self.last_trace.setdefault("no_op", []).append((name, int(now_ms)))
                return self.state
            self._disconnected = False
            self._record_rearm(name, now_ms)
        return self.state

    def _release_everything(self, event, now_ms):
        """The ONE release path, shared by blur and disconnect: the mapper's
        own release_all, i.e. physical releases of every held key. The decay
        tail (if any) is the mapper's business and is never restarted here."""
        held_before = sorted(self._mapper.held)
        self._mapper.release_all(int(now_ms))
        self.last_trace.setdefault("released_all", []) \
            .append((event, int(now_ms), held_before))

    def _record_rearm(self, event, now_ms):
        """Clean re-arm receipt: the held set MUST be empty after recovery
        (the release already happened); recorded, and asserted by the tests."""
        self.last_trace.setdefault("rearmed", []) \
            .append((event, int(now_ms), sorted(self._mapper.held)))

    # ── the input surface (same shape as the mapper's own) ──────────────────
    def press(self, name, now_ms):
        """A key went down. Dropped BY NAME while blurred/disconnected."""
        now_ms = int(now_ms)
        if not self._gate_open:
            self._drop_intent(name, now_ms)
            return None
        return self._mapper.press(name, now_ms)

    def release(self, name, now_ms):
        """A key went up. ALWAYS passed: a release can only reduce demand."""
        return self._mapper.release(name, int(now_ms))

    def mouse(self, dx_counts):
        """Mouse X counts. Dropped (named) while blurred/disconnected --
        stale counts must never fire a steer on some future fresh command."""
        if not self._gate_open:
            self._drop_intent(("mouse", float(dx_counts)), "n/a")
            return
        self._mapper.mouse(dx_counts)

    def _drop_intent(self, what, now_ms):
        reason = "dropped_disconnected" if self._disconnected else "dropped_blurred"
        self.last_trace.setdefault(reason, []).append((what, now_ms))

    # ── the boundary: tick + the expiry gate ─────────────────────────────────
    def tick(self, now_ms):
        """Advance the mapper to `now_ms`; its records flow through the gate
        (the mapper's sink IS the gate) to the real sink. Returns what
        REACHED the sink.

        The gate applies U01's own is_expired -- unchanged -- as a belt over
        the decay: a record that is already older than the max age at the
        moment of delivery is dropped and named, never emitted. With a
        healthy clock the age at emission is zero and the gate drops
        nothing; it only fires when the record is genuinely stale."""
        now_ms = int(now_ms)
        self._gate_now = now_ms
        self._gate.reset()
        self._mapper.tick(now_ms)          # emits through the gate, or not
        return list(self._gate.passed)
