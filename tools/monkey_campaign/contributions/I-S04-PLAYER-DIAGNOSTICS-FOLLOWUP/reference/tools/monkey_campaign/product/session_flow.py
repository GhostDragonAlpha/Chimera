"""session_flow.py -- M-X02: the start / pause / restart / exit session flow.

X02, verbatim (MONKEY_COMPLETION_MAP.md:179): "Player reaches play and can
pause/restart/exit without developer commands; reset is an explicit user action."

THE SHAPE (agents/X02_flow/PREREGISTRATION.md, frozen before this build): a
FOUR-STATE MACHINE -- attract -> playing <=> paused -> exited (terminal) -- that is
a pure FILTER in front of U01's UNTOUCHED mapper (tools/monkey_campaign/product/
input_mapper.py) and touches the world ONLY through two injected calls whose
declared referents are the slice's own lifecycle paths:

  * restart_scene  -> World.boot()  (tools/playable_slice/slice_server.py:94-135:
    shutdown_engine -> free port -> fresh `chimera_engine.exe ... --no-restore`
    process -> sb.wait_engine -> sb.boot_standing_start [POST /mesh_import + the
    real settle] -> per-boot state resets). A FULL SCENE RELOAD through the
    existing load path -- NEVER a state teleport, never a gravity-off re-seat
    (the drop test's trick, slice_server.py:313-339, EDITS physics), never a
    /scene term swap (that is the membrane deck's lineage, live_viewer.py:979).
  * teardown       -> World.shutdown_engine() (slice_server.py:174-181:
    terminate -> wait(10 s) -> kill). Exit's declared teardown, exactly the
    ordering R05 verifies owned-children closure against.

THE NO-DEVELOPER-COMMANDS RULE: every transition is triggered by `key(name,
down=1, now_ms)` through DEFAULT_FLOW_BINDINGS -- keyboard bindings as DATA (the
parser's law via input_mapper.py:26-29). There is no start()/pause()/restart()
method to call: the module's only public mutators are key/mouse/tick. No timer,
no thread, no wall clock, no transport can move the state (falsifier F5).

THE INPUT-GATING RULE (frozen prereg rule 1): press/release/mouse/tick reach the
mapper ONLY in `playing`. The one declared exception is the quiesce
`mapper.release_all(now_ms)` INSIDE the pause and restart transitions -- U01's own
declared focus-loss hook (input_mapper.py:153, 225-228). While not playing there
are NO mapper boundaries at all: `flow.tick` drives nothing, so zero records are
emitted -- the decision clock is SUSPENDED with the session, not suppressed
(falsifier F2 reads the sink: any record while not playing kills the build).

THE RESUME TAIL (frozen prereg rule 3): a pause that interrupted an emission
leaves U01's OWN decay tail pending; the first `playing` boundaries sample it --
at most 2 records, each at or below the pre-pause speed, landing on EXACTLY 0.0,
then silence and the grid dissolves (input_mapper.py:293-313, 262-267). This
module adds NO clearing primitive: a hard final-zero would flip the seam to its
LIVE-ZERO state (the two-state seam law, input_mapper.py:10-21,
gait_controller.hpp:121-123) -- the exact mistake U03's clause 1 refuses. Resume
re-arms per U03's DECLARED clause 4 (agents/U03_focus/PREREGISTRATION.md): the
pause quiesce left the mapper held-empty, so the next accepted press arms a
FRESH 50 ms grid -- no phantom keys, no replayed tail. When U03's focus_policy
lands it wraps the mapper behind the same surface and this module is unchanged.

Headless by construction: every time is an INJECTED integer millisecond; the
world calls are INJECTED callables; the tests drive doubles. No window, no
process, no HTTP lives in this module.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# U01's frozen numbers and doubles are IMPORTED, never redeclared: a second copy
# of a frozen constant is exactly where a silent divergence lives (U03's P2 law).
from tools.monkey_campaign.product.input_mapper import (  # noqa: E402
    InputMapper,
    MockSink,
    INTERVAL_MS,
    RELEASE_DECAY_MS,
    VALID_MS,
)

__all__ = [
    "SessionFlow", "FlowError",
    "RecordingRestart", "TeardownDouble", "StrictWorld", "CountingMapper",
    "ATTRACT", "PLAYING", "PAUSED", "EXITED", "STATES",
    "FLOW_ACTIONS", "DEFAULT_FLOW_BINDINGS", "TRANSITIONS", "FLOW_SCHEMA",
    "INTERVAL_MS", "RELEASE_DECAY_MS", "VALID_MS",
]

FLOW_SCHEMA = "chimera-monkey-session-flow-v1"

# ── THE FROZEN STATES ────────────────────────────────────────────────────────────
ATTRACT = "attract"        # before play: only confirm (start) or exit live here
PLAYING = "playing"        # the only state where the mapper is driven at all
PAUSED = "paused"          # quiesced: no mapper events, no decision boundaries
EXITED = "exited"          # terminal: teardown done, everything dropped by name
STATES = (ATTRACT, PLAYING, PAUSED, EXITED)

# ── THE FROZEN TABLE (agents/X02_flow/PREREGISTRATION.md; the ONLY transitions) ──
# (state, action) -> dest. Every action here is a bindings value and every
# bindings value is an action here -- F1 checks both directions and that all
# four states are reachable by keys alone.
FLOW_ACTIONS = ("confirm", "pause", "restart", "exit")
DEFAULT_FLOW_BINDINGS = {
    "Return": "confirm",   # attract: START the session; paused: RESUME
    "Escape": "pause",     # playing -> paused (the quiesce transition)
    "R": "restart",        # paused -> playing via World.boot (the page's own
                           # restart-key precedent, index.html:1072)
    "Q": "exit",           # any non-exited state -> exited (owned processes
                           # must die from anywhere)
}
TRANSITIONS = {
    (ATTRACT, "confirm"): PLAYING,   # 1 start: the gate opens
    (PLAYING, "pause"): PAUSED,      # 2 quiesce FIRST, then the gate closes
    (PAUSED, "confirm"): PLAYING,    # 3 resume: gate reopens, fresh grid
    (PAUSED, "restart"): PLAYING,    # 4 release_all + World.boot, then reopen
    (ATTRACT, "exit"): EXITED,       # 5-7 teardown exactly once, from anywhere
    (PLAYING, "exit"): EXITED,
    (PAUSED, "exit"): EXITED,
}
# Deliberately ABSENT from the table (each is a named no-op, falsifier F1/F5):
#   (playing, restart)  -- an accidental R mid-play must never wipe the session;
#                          restart is reached through pause, deliberately;
#   (playing, confirm)  -- play is already playing;
#   (attract, pause) / (attract, restart) -- nothing is running yet;
#   (paused, pause)     -- no double-pause;
#   (exited, *)         -- terminal: teardown never runs twice.


class FlowError(TypeError):
    """A constructed flow is missing the declared surface it gates."""


# ── headless doubles (the tests' world; the flow never builds a real one) ────────
class RecordingRestart:
    """The declared restart referent, recorded: World.boot()
    (slice_server.py:94-135). Falsifier F3 asserts the flow's world contact is
    EXACTLY one boot call -- never anything else."""

    def __init__(self, error: Exception | None = None):
        self.calls = []
        self._error = error

    def boot(self):
        self.calls.append(("boot",))
        if self._error is not None:
            raise self._error
        return {"booted": True}


class TeardownDouble:
    """The declared teardown referent, recorded: World.shutdown_engine()
    (slice_server.py:174-181) -- terminate -> wait -> kill, in that order.
    Falsifier F4 asserts EXACTLY this sequence, exactly once per session: the
    headless proof that the owned engine process dies through the declared
    path (R05's owned-children contract)."""

    def __init__(self):
        self.calls = []

    def shutdown_engine(self):
        self.calls.append("terminate")
        self.calls.append("wait")
        self.calls.append("kill")
        return True


class StrictWorld:
    """A world that offers ONLY the declared surface. Any other attribute the
    flow ever tries to touch is recorded and raised -- an undeclared contact
    (a teleport, a pose write, a gravity toggle) cannot happen silently."""

    def __init__(self):
        self.boot_calls = 0
        self.attempts = []

    def boot(self):
        self.boot_calls += 1
        return {"booted": True}

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        self.attempts.append(name)      # recorded BEFORE the raise: evidence
        raise AttributeError(
            "StrictWorld: %r is not a declared flow surface (only boot)" % name)


class CountingMapper:
    """A mapper-shaped double that records EVERY call it receives. Falsifier
    F2/F4 read this log: while not playing the log must not grow; after exit
    it must never grow again."""

    def __init__(self):
        self.calls = []
        self._held = frozenset()

    @property
    def held(self):
        return self._held

    def press(self, name, now_ms):
        self.calls.append(("press", name, int(now_ms)))
        return None

    def release(self, name, now_ms):
        self.calls.append(("release", name, int(now_ms)))
        return None

    def mouse(self, dx_counts):
        self.calls.append(("mouse", float(dx_counts)))

    def tick(self, now_ms):
        self.calls.append(("tick", int(now_ms)))
        return []

    def release_all(self, now_ms):
        self.calls.append(("release_all", int(now_ms)))


class SessionFlow:
    """The four-state session flow, a filter in front of an U01 mapper.

    Usage (all times INJECTED integer milliseconds -- never a wall clock):

        mapper = InputMapper(MockSink())
        flow = SessionFlow(mapper, restart_scene=World(...).boot,
                           teardown=World(...).shutdown_engine)
        flow.key("Return", down=1, now_ms=0)      # attract -> playing (start)
        flow.key("W", down=1, now_ms=1000)        # reaches the mapper
        flow.tick(1000)                           # -> CommandRecord (playing)
        flow.key("Escape", down=1, now_ms=2000)   # playing -> paused (quiesce)
        flow.tick(3000)                           # -> [] and the mapper is
                                                  #    untouched (suspended)
        flow.key("R", down=1, now_ms=4000)        # paused -> World.boot -> playing
        flow.key("Q", down=1, now_ms=5000)        # -> teardown once, terminal

    The public mutators are exactly key/mouse/tick (frozen prereg rule 6):
    nothing else can move the state, so there is no developer command and no
    hidden transition.
    """

    def __init__(self, mapper, restart_scene, teardown, bindings=None):
        for surface in ("press", "release", "mouse", "tick", "release_all",
                        "held"):
            if not hasattr(mapper, surface):
                raise FlowError("mapper must provide the declared U01 surface "
                                "(press/release/mouse/tick/release_all/held); "
                                "missing %r -- the flow can only gate, never "
                                "replace" % surface)
        if not callable(restart_scene):
            raise FlowError("restart_scene must be callable -- the declared "
                            "referent is World.boot() (slice_server.py:94-135)")
        if not callable(teardown):
            raise FlowError("teardown must be callable -- the declared referent "
                            "is World.shutdown_engine() (slice_server.py:174-181)")
        self._mapper = mapper
        self._restart_scene = restart_scene
        self._teardown = teardown
        self.bindings = dict(DEFAULT_FLOW_BINDINGS if bindings is None
                             else bindings)
        self._state = ATTRACT
        self.last_trace = {}

    # ── reads ────────────────────────────────────────────────────────────────
    @property
    def state(self):
        return self._state

    @property
    def is_playing(self):
        return self._state == PLAYING

    def _drop(self, kind, detail):
        """Every swallowed input is NAMED, never silent (U03's clause-2 law)."""
        self.last_trace.setdefault("dropped", []).append(
            {"kind": kind, "detail": detail, "state": self._state})

    # ── the only public mutators (frozen prereg rule 6) ──────────────────────
    def key(self, name, down, now_ms):
        """One key event. Flow-bound keys are CONSUMED by the flow in every
        state (they never reach the mapper); unbound keys forward to the mapper
        only in `playing` and are named-drops otherwise."""
        now_ms = int(now_ms)
        if down:
            action = self.bindings.get(name)
            if action is not None:
                return self._transition(action, name, now_ms)
            if self._state != PLAYING:
                self._drop("key_press", name)
                return None
            return self._mapper.press(name, now_ms)
        # a key release: only ever a gameplay event (releases can only reduce
        # demand), so it follows the same gate
        if self._state != PLAYING:
            self._drop("key_release", name)
            return None
        return self._mapper.release(name, now_ms)

    def mouse(self, dx_counts):
        """Mouse counts reach the mapper only in `playing`; otherwise a named
        drop (a paused surface cannot honestly produce intent -- U03 clause 2)."""
        if self._state != PLAYING:
            self._drop("mouse", float(dx_counts))
            return
        self._mapper.mouse(dx_counts)

    def tick(self, now_ms):
        """The 20 Hz decision boundary. In `playing` this passes through to the
        mapper (0 or 1 records). In any other state it is a named drop and
        emits NOTHING: while paused there are no boundaries at all -- the
        decision clock is suspended with the session (frozen prereg rule 2)."""
        now_ms = int(now_ms)
        if self._state != PLAYING:
            self._drop("decision_tick", now_ms)
            return []
        return self._mapper.tick(now_ms)

    # ── the frozen table, applied ────────────────────────────────────────────
    def _transition(self, action, key_name, now_ms):
        dest = TRANSITIONS.get((self._state, action))
        if dest is None:
            # THE EXPLICIT-USER-ACTION-ONLY law: an action the current state
            # does not accept is a NAMED no-op -- never a fallback, never a
            # "nearest legal" rewrite of the player's request.
            self._drop("flow_action", "%s@%s" % (action, self._state))
            return None
        src = self._state
        if action == "pause":
            # THE QUIESCE, in this order (frozen table row 2): release every
            # held key EXACTLY as a physical release (U01's declared hook) --
            # the mapper is then held-empty, which is U03's declared re-arm
            # guarantee -- and only then does the gate close.
            self._mapper.release_all(now_ms)
            self.last_trace.setdefault("quiesced", []).append(
                {"at_ms": now_ms, "held": sorted(self._mapper.held)})
        elif action == "restart":
            # THE RESTART RULE (frozen table row 4): quiesce, then the DECLARED
            # path -- World.boot(), the full scene reload (DISCOVERY.md section
            # 2). No other world contact exists in this module to make: no pose
            # write, no gravity toggle, no scene-term call.
            self._mapper.release_all(now_ms)
            self.last_trace.setdefault("restart_path", []).append(
                {"at_ms": now_ms, "declared": "world_boot"})
            try:
                self._restart_scene()
            except Exception as exc:                     # noqa: BLE001
                # A failed boot is NAMED and transitions NOWHERE: the old
                # scene is still the scene; a half-restart is never claimed.
                self.last_trace.setdefault("restart_failed", []).append(
                    {"at_ms": now_ms, "error": repr(exc)})
                return None
        elif action == "exit":
            # THE TEARDOWN (frozen table rows 5-7): the DECLARED shutdown --
            # terminate -> wait -> kill (slice_server.py:174-181) -- exactly
            # once; the table makes (exited, exit) impossible, so a second Q
            # is a named drop, never a second teardown.
            try:
                self._teardown()
            except Exception as exc:                     # noqa: BLE001
                self.last_trace.setdefault("exit_failed", []).append(
                    {"at_ms": now_ms, "error": repr(exc)})
                return None
        self._state = dest
        self.last_trace.setdefault("transitions", []).append(
            (src, action, dest, now_ms))
        return dest
