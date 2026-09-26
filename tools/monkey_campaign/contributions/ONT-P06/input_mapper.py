"""input_mapper.py -- M-U01: gameplay input -> the existing 20 Hz command seam.

U01, verbatim: "Input emits bounded speed/heading commands at the existing 20 Hz
boundary, without state teleportation." C12: "20 Hz implies a 50 ms command
interval, not an end-to-end latency guarantee."

THE SEAM THIS EMITS INTO (agents/U01_input/discovery_note.md; every number
cited, none invented here):
  * The versioned CommandRecord v1 (tools/science_funnel/typeb_export/
    command_record.py, frozen at e028d6fb): `v_forward` (m/s, >= 0 -- the plant
    law's own domain), `yaw_rate` (rad/s, CARRIED, no machinery authority at
    v1), `issued_tick`, `source`. The V1FamilyAdapter routes EXACTLY
    `commanded_target_velocity_x = float64(v_forward)` to
    GaitWalker::configure() (ChimeraEngine/engine/gait_controller.hpp:2252-2255)
    between ticks; zero-order hold at the tick boundary; the decision clock is
    20 Hz over 300 Hz physics (HOLD_TICKS = 15 -> one command per 50 ms).
  * The seam has TWO states a naive mapper would collapse: NO record at all
    (the machinery is INERT and reads its legacy measured-v,
    gait_controller.hpp:121-123,1117) vs a record with v_forward = 0.0 (a live
    zero-advance target, command_record.py:81-83 -- legal, NOT a stop bar).
    This module preserves both: idle emits NOTHING; a held `S` emits zeros.

THE FROZEN CONTRACT (agents/U01_input/PREREGISTRATION.md, stated before this
build): the mapping table, the 50 ms emission rule, the release-decay and
expiry policies, the no-teleport invariant, and falsifiers F1-F5. The frozen
walk contract is UNCHANGED by this file: it only PRODUCES records into an
injected sink. A UI remap edits the bindings dict -- the parser's own
"bindings are DATA" law (tools/parser.py:39-69, parser_tests.py falsifier 2) --
and can never touch the record type, the bounds, or the clock.

THE NO-TELEPORT INVARIANT: the ONLY thing this module can do is hand
CommandRecord instances to `sink.emit(...)`. It imports no engine module,
performs no HTTP, reads no state, holds no pose. Positions are OUTPUTS
(docs/CONTROLLER_MAP.md), never inputs.

Headless by construction: the clock is INJECTED (integer milliseconds; the
tests use a deterministic counter). This module never reads a wall clock,
never opens a window, never injects operator input anywhere.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# THE SEAM'S OWN TYPES AND NUMBERS -- imported, never redeclared: a second copy
# of a frozen constant is exactly where a silent divergence lives.
from tools.science_funnel.typeb_export.command_record import (  # noqa: E402
    CommandRecord,
    HOLD_TICKS,
    PHYSICS_HZ,
    POLICY_HZ,
    V_MAX_IN_BAND_M_S,
)

__all__ = [
    "InputMapper", "MockSink", "CommandRecord",
    "INTERVAL_MS", "RELEASE_DECAY_MS", "VALID_MS", "EXPIRY_TICKS",
    "V_MAX_IN_BAND_M_S", "OMEGA_MAX_RAD_S", "SENS_RAD_PER_COUNT",
    "DEFAULT_BINDINGS", "ACTIONS", "REFUSALS", "SOURCE_ID",
    "PHYSICS_HZ", "POLICY_HZ", "HOLD_TICKS",
]

SOURCE_ID = "u01_input_mapper"

# ── THE FROZEN NUMBERS (prereg; citations inline) ────────────────────────────────
INTERVAL_MS = 50          # 20 Hz decisions over 300 Hz physics (HOLD_TICKS=15);
                          # command_record.py:68-70, infer_numpy.py:29-44,
                          # gait_controller.hpp:108-111. Declared tolerance under
                          # the tests' injected clock: EXACT.
RELEASE_DECAY_MS = 100    # key release -> the demand decays to exactly 0.0 within
                          # 2 intervals, sampled at the seam's own boundaries, then
                          # emission stops (the inert path resumes).
VALID_MS = 100            # consumer-side expiry: a record older than 2 intervals
                          # is EXPIRED (U03 builds focus-loss on this floor).
V_MAX_IN_BAND_M_S = V_MAX_IN_BAND_M_S     # 0.763625 m/s -- the seam's own measured
                                          # in-band ceiling (command_record.py:66,
                                          # R1-R4 veto-free). U01 never demands
                                          # out-of-band; the machinery's clamp is
                                          # not input's to lean on.
OMEGA_MAX_RAD_S = 1.6     # INPUT-side steering bound, declared from the existing
                          # steer constant (ChimeraEngine/controller.py:45
                          # TURN_RATE = 1.6 rad/s). yaw_rate is CARRIED ONLY at
                          # v1 (the adapter routes it nowhere,
                          # command_record.py:180-181); this bound claims no
                          # machinery authority.
SENS_RAD_PER_COUNT = 0.002  # baseline mouse sensitivity (a declared input-side
                            # preference -- "how far a hand should push a view
                            # is a preference, not a physics",
                            # ChimeraEngine/walker.py `look()`; U04 owns it).
EXPIRY_TICKS = 2 * HOLD_TICKS  # VALID_MS expressed in physics ticks (30 @ 300 Hz).

# ── THE FROZEN MAPPING TABLE (bindings are DATA; parser.py:39-69 precedent) ─────
# Physical input name -> action. Remapping edits THIS dict (or the instance's),
# never the demand logic below, never the seam.
DEFAULT_BINDINGS = {
    "W": "forward", "Up": "forward",
    "S": "backward", "Down": "backward",
    "A": "turn_left", "Left": "turn_left",
    "D": "turn_right", "Right": "turn_right",
    "Shift": "sprint",          # a REGISTERED REFUSAL, never a silent clamp
    "Space": "jump",            # a REGISTERED REFUSAL (parser.py:96-102 rule)
}
ACTIONS = ("forward", "backward", "turn_left", "turn_right")  # precedence order:
# speed-key conflicts resolve by this order and are NAMED in the trace -- the
# parser's own rule ("registration order wins AND the conflict is named",
# parser.py:19-20).
REFUSALS = {
    "sprint": "sprint: no seam authority at v1 -- the in-band ceiling IS the "
              "measured band (V_MAX_IN_BAND_M_S); refusing by name, not clamping",
    "jump": "jump: no walk-seam channel exists at v1 (commanded_heading itself "
            "is reserved for a later lane)",
}
_SPEED_ACTIONS = ("forward", "backward")


class MockSink:
    """The clean test double for the seam: records EVERY call it receives.

    The no-teleport falsifier reads this log: every entry must be
    ("emit", <CommandRecord>). Anything else is F1 and the build is dead.
    """

    def __init__(self):
        self.calls = []            # every (method_name, args) tuple, in order
        self.records = []          # convenience: the CommandRecords emitted

    def emit(self, record):
        self.calls.append(("emit", record))
        self.records.append(record)
        return len(self.records)

    def __len__(self):
        return len(self.records)


class InputMapper:
    """Keyboard/mouse -> bounded CommandRecords at the 20 Hz boundary.

    Usage (all times are INJECTED integer milliseconds -- never a wall clock):

        sink = MockSink()         # or the live harness' real seam adapter
        m = InputMapper(sink)
        m.press("W", now_ms=1000)
        m.tick(1000)              # -> CommandRecord(v_forward=0.763625)
        m.tick(1050)              # -> re-issues (held keys refresh: the R4 rule)
        m.release("W", now_ms=1070)
        m.tick(1100)              # -> decay sample  v = v0*(1 - 30/100)
        m.tick(1150)              # -> exactly 0.0, and emission now stops
        m.release_all(now_ms=...) # U03's focus-loss/disconnect hook (this floor)

    Semantic commitments (each pinned by a falsifier in input_mapper_tests.py):
      * one record per 50 ms interval at most, current state only, NO replay
        after a stall (F3);
      * a held key RE-ISSUES every interval -- the R4 discipline (a held command
        must track, command_record.py:84-87);
      * idle emits NOTHING so the seam's inert path stays reachable; `S` held
        emits LIVE ZEROS (a zero-advance target) -- the two seam states of
        gait_controller.hpp:121-123 are distinct and both reachable (F6);
      * release decays the LAST EMITTED speed -- you can only decay what you
        commanded -- sampled at boundaries: the first boundary after release
        carries the linear sample v0*(1 - elapsed/RELEASE_DECAY_MS), the second
        carries EXACTLY 0.0 (the deadline clause), then emission stops (F4);
      * steering is carried only alongside a speed demand: yaw_rate has no
        machinery route at v1, so steering alone emits nothing and its mouse
        counts are consumed into the trace, named, never resent (declared
        limit; recorded for the later heading lane);
      * `press` of a refusal action records a named refusal; nothing silent.
    """

    def __init__(self, sink, bindings=None, *, sensitivity=SENS_RAD_PER_COUNT,
                 tick_source=None):
        if not hasattr(sink, "emit"):
            raise TypeError("sink must provide emit(record) -- the mapper can "
                            "only produce commands, never touch state")
        self._sink = sink
        self.bindings = dict(DEFAULT_BINDINGS if bindings is None else bindings)
        self.sensitivity = float(sensitivity)
        self._tick_source = tick_source   # callable() -> int physics tick, or None
        self._held = set()                # physical names currently held
        self._mouse_counts = 0.0          # accumulated, consumed per boundary
        self._next_due_ms = None          # the 50 ms grid (None = no grid)
        self._last_v = 0.0                # the LAST EMITTED speed (the decay base)
        self._tail = None                 # [v0, released_ms, boundaries_seen]
        self.last_trace = {}              # the parse trace, refreshed per tick

    # ── input events (times are injected) ────────────────────────────────────
    def press(self, name, now_ms):
        """A key went down. Refusals are recorded by name; nothing is silent."""
        action = self.bindings.get(name)
        self.last_trace.setdefault("pressed", []).append((name, int(now_ms)))
        if action in REFUSALS:
            self.last_trace.setdefault("refused", []).append((action, REFUSALS[action]))
            return action
        if action is None:
            return None                     # an unbound input is not an error
        if action in _SPEED_ACTIONS:
            self._tail = None               # a fresh press overrides any decay
        self._held.add(name)
        return action

    def release(self, name, now_ms):
        """A key went up. Releasing the speed key starts the decay tail from
        the LAST EMITTED speed -- you can only decay what you commanded."""
        action = self.bindings.get(name)
        self.last_trace.setdefault("released", []).append((name, int(now_ms)))
        if action not in _SPEED_ACTIONS or name not in self._held:
            self._held.discard(name)
            return action
        self._held.discard(name)
        other_speed = any(self.bindings.get(n) in _SPEED_ACTIONS
                          for n in self._held)
        if not other_speed and self._last_v > 0.0 and self._tail is None:
            self._tail = [self._last_v, int(now_ms), 0]
        return action

    def mouse(self, dx_counts):
        """Accumulate mouse X counts (deltas consumed, never resent --
        live_viewer.py:1978-1980). Applied at boundaries, clamped to OMEGA."""
        self._mouse_counts += float(dx_counts)

    def release_all(self, now_ms):
        """Everything off (U03's focus-loss/disconnect hook builds on this)."""
        for name in sorted(self._held):
            self.release(name, now_ms)

    @property
    def held(self):
        return frozenset(self._held)

    # ── the 20 Hz boundary ───────────────────────────────────────────────────
    def tick(self, now_ms):
        """Advance to `now_ms`; emit at most ONE record if the interval elapsed.

        Returns the list of CommandRecords emitted this call (also handed to
        the sink). A tick before the due time emits nothing -- the interval is
        the boundary, and C12's warning is honored: this is a command cadence,
        not a latency guarantee.
        """
        now_ms = int(now_ms)
        speed = self._speed_demand()                   # key demand only
        pending = (speed is not None or self._tail is not None
                   or self._mouse_counts != 0.0)
        if self._next_due_ms is None:
            if not pending:
                self.last_trace["state"] = "inert"
                self.last_trace["emitted"] = 0
                return []
            self._next_due_ms = now_ms                 # a fresh grid starts here
        if now_ms < self._next_due_ms:
            return []
        # ── a boundary: ONE decision, whatever the gap since the last tick ──
        self._next_due_ms = now_ms + INTERVAL_MS       # stall -> one record, no burst
        speed = self._apply_tail(speed, now_ms)        # the decay samples HERE
        if speed is None:
            # no walk demand (mouse-only, or the tail just finished): no
            # record. The machinery stays INERT; pending mouse counts had no
            # carrier -- consumed into the trace, named, never resent.
            if self._mouse_counts:
                self.last_trace.setdefault("steer_without_speed", []) \
                    .append(self._mouse_counts)
                self._mouse_counts = 0.0
            if self._tail is None and not self._held:
                self._next_due_ms = None               # idle: the grid dissolves
            self.last_trace["state"] = "inert" if self._tail is None else "decay"
            self.last_trace["emitted"] = 0
            return []
        yaw = self._yaw_demand()
        record = self._emit(speed, yaw, now_ms)
        self.last_trace["state"] = "commanded"
        self.last_trace["emitted"] = 1
        return [record]

    # ── demand computation ───────────────────────────────────────────────────
    def _speed_demand(self):
        """The walk demand: a live zero (S), the band ceiling (W), or None.
        Speed-key conflicts resolve by ACTIONS order and are named (the
        parser's registration-order rule). The decay tail is applied AT the
        boundary by `_apply_tail`, because commands only change at boundaries."""
        held_actions = [self.bindings[n] for n in self._held
                        if self.bindings.get(n) in _SPEED_ACTIONS]
        if len(held_actions) > 1:
            self.last_trace.setdefault("conflicts", []).append(tuple(sorted(held_actions)))
        if "forward" in held_actions:
            return V_MAX_IN_BAND_M_S
        if "backward" in held_actions:
            return 0.0                                 # a LIVE zero-advance target
        return None                                    # the tail decides at the boundary

    def _apply_tail(self, speed, now_ms):
        """Sample the release-decay tail at this boundary (frozen policy):
        first boundary after release -> the linear sample
            v0 * (1 - (now - released_ms) / RELEASE_DECAY_MS)   (floored at 0),
        unless the gap already exceeded the deadline, in which case exactly
        0.0 once; second boundary after release -> EXACTLY 0.0 in any case
        (the deadline clause: the demand lands on zero at or before the
        100 ms boundary). The tail then ENDS: the next boundary is inert and
        emits nothing."""
        if self._tail is None or speed is not None:
            return speed
        v0, released_ms, seen = self._tail
        if seen == 0:
            elapsed = max(0, now_ms - released_ms)
            self._tail[2] = 1
            if elapsed >= RELEASE_DECAY_MS:
                self._tail = None                      # deadline passed in the gap
                return 0.0
            return v0 * (1.0 - elapsed / RELEASE_DECAY_MS)
        self._tail = None                              # deadline: exact zero
        return 0.0

    def _yaw_demand(self):
        """Carried yaw at this boundary: keys + clamped mouse counts. Counts
        are consumed here (never resent); L+R keys cancel (+OMEGA + -OMEGA)."""
        key_yaw = (OMEGA_MAX_RAD_S if any(self.bindings.get(n) == "turn_left"
                                          for n in self._held) else 0.0) \
                + (-OMEGA_MAX_RAD_S if any(self.bindings.get(n) == "turn_right"
                                           for n in self._held) else 0.0)
        mouse_yaw = 0.0
        if self._mouse_counts:
            interval_s = INTERVAL_MS / 1000.0
            raw = self._mouse_counts * self.sensitivity / interval_s
            mouse_yaw = max(-OMEGA_MAX_RAD_S, min(OMEGA_MAX_RAD_S, raw))
            self._mouse_counts = 0.0
        yaw = key_yaw + mouse_yaw
        return max(-OMEGA_MAX_RAD_S, min(OMEGA_MAX_RAD_S, yaw))

    def _emit(self, v_forward, yaw_rate, now_ms):
        issued_tick = (int(self._tick_source()) if self._tick_source
                       else (now_ms * PHYSICS_HZ) // 1000)
        record = CommandRecord(v_forward=float(v_forward), yaw_rate=float(yaw_rate),
                               issued_tick=int(issued_tick), source=SOURCE_ID)
        self._last_v = float(v_forward)                 # the next decay starts here
        self._sink.emit(record)
        return record

    # ── the consumer-side expiry contract (declared for U03/U07/W08) ─────────
    @staticmethod
    def is_expired(record, now_ms):
        """A record older than VALID_MS (2 intervals) is EXPIRED: the consumer
        reverts to the seam's inert path (commands nothing) until a fresh
        record arrives. `record.issued_tick` is a 300 Hz physics tick."""
        age_ms = (int(now_ms) * PHYSICS_HZ // 1000) - int(record.issued_tick)
        return age_ms > EXPIRY_TICKS
