"""climb_intent_tests.py -- U05's falsifiers, measured (PREREGISTRATION.md).

Headless: injected millisecond clocks, recording sinks, synthetic events only,
no window, no desktop input, no engine process, no wall clock. The channel is
measured against the frozen INTENT_SEAM_SPEC.md / PREREGISTRATION.md and against
the integrated U01 mapper + U03 focus policy (both READ-ONLY):

  I1  EDGE/HOLD      a held key NEVER emits a second event; one accepted press
                     = exactly ONE event; release re-arms; a release never
                     emits; unbound keys are ignored (named in the trace).
  I2  VERSION/SCHEMA every event carries intent_version == 1, one of the two
                     frozen names, both stamps, the source; the canonical field
                     set is exactly five, no floats; the validator refuses a
                     wrong version / unknown name / bad stamps.
  I3  GATES          zero events while blurred/disconnected/paused; every gated
                     press dropped BY NAME (strongest active gate names it); a
                     gated press does NOT arm (no phantom after recovery); gated
                     releases pass; redundant policy events are named no-ops.
  I4  NO FABRICATED RETRACT  LET_GO events == accepted let_go presses under all
                     gate churn; no gate event, drop, or release ever emits.
  I5  PURE SIGNAL    every sink call is emit(IntentEvent); no CommandRecord in
                     the channel's namespace or source; imports are exactly the
                     declared set; PHYSICS_HZ is imported (identity), no frozen
                     literal redeclared; no desktop/transport/wall-clock surface.
  I6  WALK BYTES     sha256 of command_record.py identical start->end of the
                     full run (the pinned falsifier); input_mapper.py likewise
                     (context); the walk and intent sinks never receive each
                     other's records.
  I7  INTEGRATION    one headless scenario: one event feed -> U01 mapper under
                     U03's FocusPolicy (walk sink) AND -> the channel (intent
                     sink), shared clock: Space press = walk NAMED refusal +
                     zero walk records + ONE climb_request; blur hits BOTH
                     channels (walk decay to exact 0.0 then silence per U01/U03,
                     intent dropped by name); pause parity with X02's SessionFlow.

    python tools/monkey_campaign/product/climb_intent_tests.py
"""
from __future__ import annotations

import ast
import hashlib
import random
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import input_mapper as M                                    # noqa: E402
import focus_policy as FP                                   # noqa: E402
import session_flow as SF                                   # noqa: E402
import climb_intent as CI                                   # noqa: E402
from tools.science_funnel.typeb_export.command_record import (  # noqa: E402
    CommandRecord, PHYSICS_HZ,
)

FAILURES = []
SEED = 20260924                       # house seed (U01/U03 precedent)
FUZZ_EVENTS = 6000                    # REVISION A (prereg): doubled from the
                                      # frozen 3000 -- the same defect class
                                      # U03's REVISION A caught (their fuzz was
                                      # doubled too); coverage number, not a law
                                      # number. Semantics untouched.
VACUITY_FLOOR = 200                   # a fuzz that accepts fewer presses than
                                      # this proves nothing (U03's REVISION A law)

_SEAM_PATH = _ROOT / "tools" / "science_funnel" / "typeb_export" / "command_record.py"
_MAPPER_PATH = _ROOT / "tools" / "monkey_campaign" / "product" / "input_mapper.py"


def sha256_file(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


SHA_SEAM_START = sha256_file(_SEAM_PATH)
SHA_MAPPER_START = sha256_file(_MAPPER_PATH)


def check(name, ok, detail=""):
    tag = "PASS" if ok else "FAIL"
    print(f"  [{tag}] {name}" + (f"  -- {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def channel(tick_source=None, bindings=None):
    sink = CI.MockIntentSink()
    chan = CI.ClimbIntentChannel(sink, bindings=bindings, tick_source=tick_source)
    return chan, sink


def ticks_from_ms(ms):
    """The walk seam's default stamp convention, as a callable for injection."""
    return (ms * PHYSICS_HZ) // 1000


# ── I1 EDGE/HOLD (the brief's falsifier b) ────────────────────────────────────
def falsifier_1():
    print("I1 EDGE/HOLD: a press is ONE event; a hold is silence; release re-arms")
    chan, sink = channel()

    n = chan.press("Space", 1000)
    check("I1.a one accepted press -> exactly ONE event", len(sink) == 1 and n == "climb_request",
          f"ret={n}, events={len(sink)}")
    for i, t in enumerate(range(1001, 1101, 10)):
        chan.press("Space", t)            # OS auto-repeat while held
        chan.release("Q", t)              # noise
        chan.press("X", t)                # unbound noise
    check("I1.b a HELD key emits ZERO further events across repeat presses",
          len(sink) == 1, f"events={len(sink)}")
    check("I1.c repeat presses are NAMED no-ops, never silent",
          len(chan.last_trace.get("repeat_press", [])) == 10,
          f"repeat_press={chan.last_trace.get('repeat_press')}")
    check("I1.d unbound presses are ignored (recorded, no event)",
          len(chan.last_trace.get("pressed", [])) == 21 and "X" not in chan.bindings,
          f"pressed={len(chan.last_trace.get('pressed', []))}")

    n = chan.release("Space", 1200)
    check("I1.e a release emits NOTHING", len(sink) == 1 and n == "climb_request",
          f"events={len(sink)}")
    n = chan.press("Space", 1300)
    check("I1.f the edge RE-ARMED: a fresh press after release fires ONCE",
          len(sink) == 2 and n == "climb_request", f"events={len(sink)}")
    check("I1.g the held key still emits nothing more",
          (chan.press("Space", 1400), len(sink))[-1] == 2, f"events={len(sink)}")

    chan.release("Q", 1500)               # release of a never-pressed key
    check("I1.h a release without a press is a harmless no-op (no event)",
          len(sink) == 2, f"events={len(sink)}")

    # the two intents are independent edges (Space is released first: the edge
    # state tracks PHYSICAL keys, and Space is still held from 1300)
    chan.release("Space", 1550)
    chan.press("C", 1600)
    chan.press("C", 1610)                 # held
    chan.press("Space", 1620)             # other key, independent edge
    check("I1.i the two bindings are INDEPENDENT edges (C held does not eat Space)",
          len(sink) == 4, f"events={len(sink)}")
    check("I1.j C held emits nothing further",
          (chan.press("C", 1630), len(sink))[-1] == 4, f"events={len(sink)}")


# ── I2 VERSION/SCHEMA ─────────────────────────────────────────────────────────
def falsifier_2():
    print("I2 VERSION/SCHEMA: every event is versioned, named, stamped; no floats")
    chan, sink = channel()
    for t, key in [(1000, "Space"), (1100, "C"), (1200, "Space")]:
        chan.press(key, t)
        chan.release(key, t + 10)

    ok_v = all(e.intent_version == CI.INTENT_VERSION for e in sink.events)
    ok_name = all(e.intent in CI.INTENTS for e in sink.events)
    ok_src = all(e.source == CI.SOURCE_ID for e in sink.events)
    ok_stamp = all(e.now_ms in (1000, 1100, 1200)
                   and e.issued_tick == ticks_from_ms(e.now_ms) for e in sink.events)
    check("I2.a every event carries intent_version == 1 (the SAME object)",
          ok_v and CI.INTENT_VERSION == 1, f"versions={[e.intent_version for e in sink.events]}")
    check("I2.b every intent is one of the frozen two", ok_name,
          f"names={[e.intent for e in sink.events]}")
    check("I2.c source is stamped on every event", ok_src)
    check("I2.d both stamps ride every event (ms + tick, the seam's convention)",
          ok_stamp, f"stamps={[(e.now_ms, e.issued_tick) for e in sink.events]}")

    canon = [set(e.canonical_fields()) for e in sink.events]
    check("I2.e the canonical field set is EXACTLY five, on every event",
          all(c == {"intent_version", "intent", "issued_tick", "now_ms", "source"}
              for c in canon), f"{canon[0]}")
    check("I2.f NO float field exists in the wire format (pure signal: the only "
          "numbers are stamps)",
          all(type(v) in (int, str)
              for e in sink.events for v in e.canonical_fields().values()))

    import json
    blob = json.dumps([e.canonical_fields() for e in sink.events])
    check("I2.g the canonical form is JSON-serializable and round-trips",
          json.loads(blob)[0]["intent"] == "climb_request")

    # the validator refuses anything outside v1 (the CommandRecord v1 law)
    def raises(fn):
        try:
            fn()
            return False
        except CI.IntentEventError:
            return True

    check("I2.h a wrong intent_version is REFUSED",
          raises(lambda: CI.IntentEvent("climb_request", 0, 0, intent_version=2)))
    check("I2.i an unknown intent name is REFUSED",
          raises(lambda: CI.IntentEvent("climb_grab", 0, 0)))
    check("I2.j a float stamp is REFUSED (stamps are ints)",
          raises(lambda: CI.IntentEvent("let_go", 1.5, 0)))
    check("I2.k a negative stamp is REFUSED",
          raises(lambda: CI.IntentEvent("let_go", -1, 0)))
    check("I2.l a bool stamp is REFUSED",
          raises(lambda: CI.IntentEvent("let_go", True, 0)))

    # a bindings table can only ever name the two intents (refuse-what-you-
    # cannot-name, the parser's law via input_mapper.py:111-116)
    try:
        CI.ClimbIntentChannel(CI.MockIntentSink(), bindings={"J": "jump"})
        ok = False
    except ValueError:
        ok = True
    check("I2.m a binding outside the vocabulary is REFUSED AT CONSTRUCTION", ok)


# ── I3 GATES (the brief's falsifier c) ────────────────────────────────────────
def falsifier_3():
    print("I3 GATES: blurred/disconnected/paused drop BY NAME; clean recovery")
    # pause (X02's gate)
    chan, sink = channel()
    chan.press("Space", 1000)             # fires
    chan.release("Space", 1100)
    chan.on_pause(1200)
    check("I3.a state names the pause", chan.state == "paused" and chan.paused)
    n = len(sink)
    r = chan.press("Space", 1300)
    check("I3.b press while paused: ZERO events, dropped BY NAME",
          len(sink) == n and r is None
          and chan.last_trace.get("dropped_paused") == [("Space", 1300)],
          f"{chan.last_trace.get('dropped_paused')}")
    drops = chan.last_trace.get("drops", [])
    check("I3.c the drop entry records the reason AND the active gate set",
          drops and drops[-1] == {"what": "Space", "at_ms": 1300,
                                  "reason": "dropped_paused", "gates": ["paused"]},
          f"{drops}")
    chan.on_resume(1400)
    n = len(sink)
    r = chan.press("Space", 1500)
    check("I3.d resume opens the gate and the press FIRES (a gated press did "
          "NOT arm a phantom edge)", len(sink) == n + 1 and r == "climb_request",
          f"events={len(sink)}")
    chan.release("Space", 1600)

    # blur (U03's gate)
    chan2, sink2 = channel()
    chan2.on_blur(1000)
    check("I3.e blur names the state", chan2.state == "blurred")
    r = chan2.press("Space", 1100)
    check("I3.f press while blurred: dropped_blurred, ZERO events",
          r is None and len(sink2) == 0
          and chan2.last_trace.get("dropped_blurred") == [("Space", 1100)],
          f"{chan2.last_trace.get('dropped_blurred')}")
    chan2.on_focus(1200)
    r = chan2.press("Space", 1300)
    check("I3.g after focus the surface is clean: the press fires ONCE",
          len(sink2) == 1 and r == "climb_request", f"events={len(sink2)}")

    # disconnect (U03's gate) + dominance
    chan3, sink3 = channel()
    chan3.on_disconnect(1000)
    check("I3.h disconnect names the state", chan3.state == "disconnected")
    chan3.on_blur(1001)
    check("I3.i disconnected DOMINATES blurred (U03's law)",
          chan3.state == "disconnected")
    chan3.on_pause(1002)
    check("I3.j disconnected dominates paused too", chan3.state == "disconnected")
    r = chan3.press("C", 1100)
    check("I3.k the drop is named by the STRONGEST active gate, full set recorded",
          r is None and len(sink3) == 0
          and chan3.last_trace.get("dropped_disconnected") == [("C", 1100)]
          and chan3.last_trace["drops"][-1]["gates"] == ["blurred", "disconnected", "paused"],
          f"{chan3.last_trace.get('drops')}")

    # releases ALWAYS pass, even gated; and never emit
    n = len(sink3)
    chan3.release("C", 1200)
    check("I3.l a gated release PASSES (only un-arms) and emits NOTHING",
          len(sink3) == n and "C" not in chan3.held)

    # redundant policy events are NAMED no-ops (U03 clause 5)
    chan4, _ = channel()
    for ev in (chan4.on_pause(1), chan4.on_pause(2), chan4.on_resume(3),
               chan4.on_resume(4), chan4.on_blur(5), chan4.on_blur(6),
               chan4.on_focus(7), chan4.on_focus(8), chan4.on_disconnect(9),
               chan4.on_disconnect(10), chan4.on_reconnect(11), chan4.on_reconnect(12)):
        pass
    check("I3.m redundant policy events are recorded as named no-ops (12 events, "
          "6 no-ops)", len(chan4.last_trace.get("events", [])) == 12
          and len(chan4.last_trace.get("no_op", [])) == 6,
          f"no_ops={chan4.last_trace.get('no_op')}")

    # one physical hold stays ONE consumed edge across any number of gate cycles
    chan5, sink5 = channel()
    chan5.press("Space", 1000)            # fires; key STAYS held
    for t in range(1100, 2000, 100):
        chan5.on_pause(t)
        chan5.press("Space", t + 5)       # inside the pause: dropped_paused
        chan5.on_resume(t + 10)
        chan5.on_blur(t + 20)
        chan5.press("Space", t + 25)      # inside the blur: dropped_blurred
        chan5.on_focus(t + 30)
        chan5.on_disconnect(t + 40)
        chan5.press("Space", t + 45)      # inside the disconnect: dropped_disconnected
        chan5.on_reconnect(t + 50)
        chan5.press("Space", t + 55)      # gates open: repeat_press no-op
    check("I3.n one physical hold = one consumed edge across ALL gate cycles "
          "(no re-fire, no phantom)",
          len(sink5) == 1, f"events={len(sink5)}")
    check("I3.o the trace shows every gated repeat NAMED under its own gate, "
          "none silent",
          all(k in chan5.last_trace for k in
              ("dropped_paused", "dropped_blurred", "dropped_disconnected",
               "repeat_press"))
          and len(chan5.last_trace["dropped_paused"]) == 9
          and len(chan5.last_trace["dropped_blurred"]) == 9
          and len(chan5.last_trace["dropped_disconnected"]) == 9
          and len(chan5.last_trace["repeat_press"]) == 9,
          f"keys={sorted(chan5.last_trace)}")


# ── I4 NO FABRICATED RETRACT (the brief's falsifier d) ────────────────────────
def falsifier_4():
    print("I4 NO FABRICATED RETRACT: only explicit let_go presses produce LET_GO")
    chan, sink = channel()
    chan.press("Space", 1000)             # the climb_request DELIVERED
    # ... then every gate slams shut, in every order, repeatedly:
    for t, ev in [(1100, chan.on_blur), (1200, chan.on_disconnect),
                  (1300, chan.on_pause), (1400, chan.on_blur),
                  (1500, chan.on_disconnect), (1600, chan.on_pause)]:
        ev(t)
    releases = [chan.release("Space", t) for t in range(1700, 2200, 100)]
    for t, ev in [(2300, chan.on_focus), (2400, chan.on_reconnect),
                  (2500, chan.on_resume)]:
        ev(t)
    check("I4.a NO gate event, drop, or release ever fabricated an intent",
          len(sink) == 1, f"events={len(sink)}")
    check("I4.b no LET_GO exists anywhere in the stream",
          not [e for e in sink.events if e.intent == CI.LET_GO])
    chan.press("C", 2600)                 # the ONE explicit let_go
    lets = [e for e in sink.events if e.intent == CI.LET_GO]
    check("I4.c the ONLY LET_GO is the explicit one (1 press == 1 event)",
          len(sink) == 2 and len(lets) == 1 and lets[0].now_ms == 2600,
          f"events={len(sink)}, let_gos={len(lets)}")
    check("I4.d every release call returned cleanly (releases always pass: a "
          "release reports its binding, never an event)",
          all(r in (CI.CLIMB_REQUEST, CI.LET_GO, None) for r in releases))

    # the same law under the fuzz's gate churn is checked in falsifier_6;
    # here: a climb_request followed by let_go are TWO delivered facts and the
    # channel arbitrates nothing (the spec's declared limit, section 6.4)
    chan.press("Space", 2700)
    check("I4.e the channel never arbitrates: climb_request then let_go both "
          "delivered as facts", len(sink) == 3
          and [e.intent for e in sink.events] ==
          ["climb_request", "let_go", "climb_request"])


# ── I5 PURE SIGNAL ────────────────────────────────────────────────────────────
FORBIDDEN_MARKERS = (
    "import time", "datetime", "socket", "urllib", "ctypes", "subprocess",
    "threading", "keybd_event", "SendInput", "SetCursorPos", "win32",
    "pyautogui", "pynput", "CommandRecord", "v_forward", "yaw_rate",
    "pose_apply", "http", "requests",
)
FROZEN_LITERALS = ("= 100", "= 50", "0.763", "1.6", "= 300", "= 30")


def falsifier_5(module_source=""):
    print("I5 PURE SIGNAL: no commands, no poses, no forces, no desktop")
    chan, sink = channel()
    chan.press("Space", 1000)
    chan.press("C", 1100)
    ok_shape = all(call == ("emit", ev) and isinstance(ev, CI.IntentEvent)
                   for call, ev in zip(sink.calls, sink.events))
    check("I5.a every sink call is exactly emit(IntentEvent)", ok_shape,
          f"calls={[c[0] for c in sink.calls]}")
    check("I5.b the channel's namespace holds NO CommandRecord",
          not hasattr(CI, "CommandRecord"))
    src = module_source or Path(CI.__file__).read_text(encoding="utf-8")
    # the scan reads CODE, not prose: docstrings/comments may (and must) NAME
    # the law they enforce ("never the CommandRecord class"); only executable
    # tokens can violate it (tokenize, STRING and COMMENT dropped)
    import io
    import tokenize
    code_tokens = []
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type not in (tokenize.STRING, tokenize.COMMENT):
            code_tokens.append(tok.string)
    code = " ".join(code_tokens)
    hits = [m for m in FORBIDDEN_MARKERS if m in code]
    check("I5.c no command/pose/transport/desktop/wall-clock surface in the "
          "module source", not hits, f"hits={hits}")
    tree = ast.parse(src)
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    declared = {"__future__", "sys", "dataclasses", "pathlib",
                "tools.science_funnel.typeb_export.command_record"}
    check("I5.d the import set is EXACTLY the declared one (the walk seam "
          "contributes a CONSTANT, never a type)", imports == declared,
          f"imports={sorted(imports)}")
    check("I5.e PHYSICS_HZ is the SAME OBJECT as the seam's (imported, never "
          "redeclared)", CI.PHYSICS_HZ is PHYSICS_HZ)
    lit = [m for m in FROZEN_LITERALS if m in src]
    check("I5.f no frozen number is redeclared as a literal", not lit,
          f"hits={lit}")


# ── I6 WALK-CONTRACT BYTES (the brief's falsifier a) ──────────────────────────
def falsifier_6_start():
    print("I6 WALK BYTES: the frozen walk contract is hashed at run start")
    check("I6.a seam hash captured at start (compared at end)",
          len(SHA_SEAM_START) == 64, f"sha256={SHA_SEAM_START[:16]}...")


def falsifier_6_end():
    print("I6 WALK BYTES (end of run): byte-identity of the frozen contract")
    sha_seam_end = sha256_file(_SEAM_PATH)
    sha_mapper_end = sha256_file(_MAPPER_PATH)
    check("I6.b command_record.py is BYTE-IDENTICAL before/after the full run "
          "(the pinned falsifier)", sha_seam_end == SHA_SEAM_START,
          f"{SHA_SEAM_START} == {sha_seam_end}")
    check("I6.c input_mapper.py is BYTE-IDENTICAL before/after (U01 frozen, "
          "context)", sha_mapper_end == SHA_MAPPER_START,
          f"{SHA_MAPPER_START} == {sha_mapper_end}")


# ── I7 INTEGRATION: one feed -> U01+U03 (walk) AND the channel (intent) ───────
def falsifier_7():
    print("I7 INTEGRATION: U01 mapper + U03 policy + the channel, one clock")
    walk_sink = M.MockSink()
    fp = FP.FocusPolicy(walk_sink, mapper_factory=lambda gate: M.InputMapper(gate))
    chan, intent_sink = channel()
    released_space_walk = []

    def feed_press(name, t):
        """One physical key-down, fed to BOTH declared channels (spec §8):
        the walk side through U03's policy, the intent side through the seam."""
        released_space_walk.append(fp.press(name, t))
        return chan.press(name, t)

    def feed_release(name, t):
        fp.release(name, t)
        chan.release(name, t)

    def dense(f, t0, t1, step=1):
        got = []
        for t in range(t0, t1 + 1, step):
            got.extend((t, r) for r in f(t))
        return got

    # 1. walking: W produces U01's frozen stream; the intent side stays silent
    feed_press("W", 1000)
    walk = dense(fp.tick, 1000, 1120)
    check("I7.a the walk side is U01's own stream (band ceiling re-issued per "
          "50 ms)", len(walk) == 3
          and all(r.v_forward == M.V_MAX_IN_BAND_M_S for _, r in walk)
          and [t for t, _ in walk] == [1000, 1050, 1100],
          f"{[(t, r.v_forward) for t, r in walk]}")
    check("I7.b walking emits ZERO intents (separate, sparser channel)",
          len(intent_sink) == 0, f"events={len(intent_sink)}")

    # 2. THE SEAM MOMENT: Space is bound on BOTH surfaces, each named
    n_walk = len(walk_sink.records)
    r_intent = feed_press("Space", 1130)
    refusal = fp.mapper.last_trace.get("refused", [])
    check("I7.c the walk side keeps its NAMED refusal and emits ZERO records "
          "for Space", refusal and refusal[-1][0] == "jump"
          and len(walk_sink.records) == n_walk,
          f"refusal={refusal[-1][0] if refusal else None}")
    check("I7.d the intent side delivers ONE climb_request for the same press",
          r_intent == "climb_request" and len(intent_sink) == 1
          and intent_sink.events[-1].canonical_fields() ==
          {"intent_version": 1, "intent": "climb_request",
           "issued_tick": ticks_from_ms(1130), "now_ms": 1130,
           "source": "u05_climb_intent"},
          f"{intent_sink.events[-1].canonical_fields() if len(intent_sink) else None}")

    # 3. holding Space while walking: the walk stream continues (U01 R4), the
    #    intent side stays silent (edge consumed)
    feed_press("W", 1140)
    walk_more = dense(fp.tick, 1140, 1230)
    for t in range(1140, 1230, 10):
        chan.press("Space", t)
    check("I7.e held Space + walking: walk stream continues, ZERO further "
          "intents", len(walk_more) == 2 and len(intent_sink) == 1,
          f"walk={len(walk_more)}, intents={len(intent_sink)}")

    # 4. BLUR hits BOTH channels (one event, two consumers)
    feed_release("W", 1240)
    fp.on_blur(1240)
    chan.on_blur(1240)
    tail = dense(fp.tick, 1241, 1400)
    vs = [r.v_forward for _, r in tail]
    zero_at = next((t for t, r in tail if r.v_forward == 0.0), None)
    check("I7.f the walk side decays EXACTLY per U01/U03: monotone tail, exact "
          "0.0 at or before +100 ms, then silence",
          all(a >= b for a, b in zip(vs, vs[1:])) and zero_at is not None
          and zero_at <= 1240 + M.RELEASE_DECAY_MS
          and not [1 for t, _ in tail if t > zero_at],
          f"zero at {zero_at}, tail={vs}")
    r = chan.press("C", 1300)
    check("I7.g the intent side dropped the press BY NAME under the same blur",
          r is None and len(intent_sink) == 1
          and chan.last_trace.get("dropped_blurred") == [("C", 1300)],
          f"{chan.last_trace.get('dropped_blurred')}")
    # the operator's hand comes off the key while blurred: a RELEASE always
    # passes both channels (U03's law), so the intent edge is un-armed
    feed_release("Space", 1350)
    check("I7.g' the blurred RELEASE passed (the edge is un-armed, nothing "
          "emitted)", "Space" not in chan.held and len(intent_sink) == 1,
          f"held={sorted(chan.held)}")

    # 5. recovery hits both; a fresh Space press behaves exactly like the first
    fp.on_focus(1500)
    chan.on_focus(1500)
    check("I7.h after recovery the walk mapper is key-free (U03's re-arm law)",
          fp.held == frozenset(), f"held={sorted(fp.held)}")
    n_before = len(intent_sink)
    r = feed_press("Space", 1600)
    check("I7.i the recovered Space press delivers ONE climb_request (no "
          "phantom, no re-fire)", r == "climb_request"
          and len(intent_sink) == n_before + 1)
    feed_release("Space", 1700)

    # 6. the sinks never cross (spec §8)
    check("I7.j the walk sink holds ONLY CommandRecords",
          all(isinstance(r, CommandRecord) for r in walk_sink.records),
          f"n={len(walk_sink.records)}")
    check("I7.k the intent sink holds ONLY IntentEvents",
          all(isinstance(e, CI.IntentEvent) for e in intent_sink.events),
          f"n={len(intent_sink.events)}")

    # 7. PAUSE PARITY with X02's session flow: the same pause signal gates both
    walk_sink2 = M.MockSink()
    flow_mapper = M.InputMapper(walk_sink2)
    flow = SF.SessionFlow(flow_mapper, SF.RecordingRestart().boot,
                          SF.TeardownDouble().shutdown_engine)
    flow.key("Return", 1, 2000)           # attract -> playing
    flow.key("W", 1, 2010)                # walk demand armed
    flow.tick(2020)                       # -> U01's boundary record
    n_live = len(walk_sink2.records)
    chan2, intent_sink2 = channel()
    flow.key("Escape", 1, 2100)           # playing -> paused (X02's quiesce)
    chan2.on_pause(2100)                  # the SAME pause signal, intent side
    check("I7.l the flow paused; gameplay keys are named drops on BOTH sides",
          flow.state == "paused"
          and flow.key("Space", 1, 2200) is None
          and any(d["kind"] == "key_press" for d in flow.last_trace["dropped"])
          and chan2.press("Space", 2200) is None
          and chan2.last_trace.get("dropped_paused") == [("Space", 2200)],
          f"flow_drop={flow.last_trace['dropped'][-1]}, "
          f"chan_drop={chan2.last_trace.get('dropped_paused')}")
    flow.tick(2300)                       # a paused decision tick: dropped, [] returned
    check("I7.m ZERO walk records while paused (X02's own falsifier, still "
          "green under the composition) and zero intents",
          len(walk_sink2.records) == n_live and flow.tick(2305) == []
          and len(walk_sink2.records) == n_live and len(intent_sink2) == 0,
          f"walk={len(walk_sink2.records)} (pre-pause {n_live}), intents={len(intent_sink2)}")
    flow.key("Return", 1, 2400)           # resume
    chan2.on_resume(2400)
    check("I7.n resume re-opens BOTH gates; the intent edge is clean",
          flow.state == "playing" and chan2.state == "ready"
          and chan2.press("Space", 2500) == "climb_request"
          and len(intent_sink2) == 1, f"events={len(intent_sink2)}")


# ── the FUZZ (model-checked; feeds I1/I3/I4/I5 measurements) ──────────────────
KEYS = ["Space", "C", "W", "X"]           # X unbound
# REVISION A mix (see prereg): presses/releases weighted toward the BOUND keys
# so the fuzz clears its own vacuity floor -- same 3000 events, same seed,
# same model, same frozen semantics (U03 REVISION A's precedent: rebuild the
# mix, never the law).
PRESS_POOL = ["Space", "C", "Space", "C", "Space", "C", "W", "X"]  # 3/4 bound
RELEASE_POOL = ["Space", "C", "Space", "C", "W", "X"]              # 2/3 bound
POLICY = ["blur", "focus", "disconnect", "reconnect", "pause", "resume"]
# openings weighted 3:1 over closings: three independent gates on an UNBIASED
# walk are all-open only ~1/8 of the time (measured: 819/945 bound presses
# gated, 49 deliveries -- I8.h fired twice on the vacuity floor). The DROP law
# needs churn; the ACCEPT law needs volume. Both get theirs: closings stay 1/4
# of policy events (drop coverage stays in the hundreds), openings clear the
# delivery floor with margin. (REVISION A, prereg.)
POLICY_POOL = (["blur", "disconnect", "pause"]
               + ["focus", "reconnect", "resume"] * 3)     # 3 closings of 12
STRONGEST = ("disconnected", "blurred", "paused")


def falsifier_8():
    print(f"I8 FUZZ: {FUZZ_EVENTS} seeded events, checked against a reference "
          "model (edge law, gates, naming, no fabrication)")
    rng = random.Random(SEED)
    chan, sink = channel()
    armed = set()                          # the model's edge state
    gates = set()                          # the model's gate set
    accepted_presses = 0
    accepted_let_go = 0
    expected_events = 0
    t = 1000

    def model_strongest():
        for g in STRONGEST:
            if g in gates:
                return g
        return None

    for i in range(FUZZ_EVENTS):
        t += rng.randint(1, 40)
        roll = rng.random()
        if roll < 0.42:                                    # a press
            k = rng.choice(PRESS_POOL)
            chan.press(k, t)
            action = CI.DEFAULT_INTENT_BINDINGS.get(k)
            if action is None:
                pass                                       # unbound: nothing
            elif gates:
                pass                                       # gated: dropped, NOT armed
            elif k in armed:
                pass                                       # repeat: named no-op
            else:
                armed.add(k)
                accepted_presses += 1
                expected_events += 1
                if action == CI.LET_GO:
                    accepted_let_go += 1
        elif roll < 0.72:                                  # a release (always passes)
            k = rng.choice(RELEASE_POOL)
            chan.release(k, t)
            armed.discard(k)
        elif roll < 0.92:                                  # a policy event
            ev = rng.choice(POLICY_POOL)
            closing = ev in ("blur", "disconnect", "pause")
            gate = {"blur": "blurred", "focus": "blurred",
                    "disconnect": "disconnected", "reconnect": "disconnected",
                    "pause": "paused", "resume": "paused"}[ev]
            chan.__getattribute__("on_" + ev)(t)
            if gate in gates and closing:
                pass
            elif gate not in gates and not closing:
                pass
            elif closing:
                gates.add(gate)
            else:
                gates.discard(gate)
        else:                                              # idle time passes
            chan.press("Q", t)                             # unbound: nothing

        # the model is the law, checked after EVERY event:
        if len(sink.events) > expected_events:
            check("I8.a an event the model did not accept", False,
                  f"event {len(sink.events)} > expected {expected_events} at t={t}")
            return
        if sink.events:
            e = sink.events[-1]
            if e.intent_version != CI.INTENT_VERSION or e.intent not in CI.INTENTS:
                check("I8.b a schema violation in the fuzz", False,
                      f"{e.canonical_fields()}")
                return
            if e.now_ms > t:
                check("I8.c a stamp from the future", False, f"{e.now_ms} > {t}")
                return
        if chan.held != frozenset(armed):
            check("I8.d the edge state diverged from the model", False,
                  f"chan={sorted(chan.held)} model={sorted(armed)} at t={t}")
            return
        if model_strongest() is None:
            if chan.state != "ready":
                check("I8.e the named state diverged (model: ready)", False,
                      f"chan={chan.state} at t={t}")
                return
        elif chan.state != model_strongest():
            check("I8.e the named state diverged (model: strongest gate)", False,
                  f"chan={chan.state} model={model_strongest()} at t={t}")
            return

    # aggregate laws over the whole fuzz:
    check("I8.f events == accepted presses (one press, one event; nothing else)",
          len(sink.events) == accepted_presses,
          f"events={len(sink.events)}, accepted={accepted_presses}")
    check("I8.g LET_GO events == accepted let_go presses (no fabricated retract)",
          len([e for e in sink.events if e.intent == CI.LET_GO]) == accepted_let_go,
          f"let_go={accepted_let_go}")
    check("I8.h the fuzz is not vacuous (>= the delivery floor)",
          accepted_presses >= VACUITY_FLOOR, f"accepted={accepted_presses}")
    named_drops = sum(len(v) for k, v in chan.last_trace.items()
                      if k.startswith("dropped_"))
    check("I8.i every gated press was dropped AND NAMED (never silent)",
          named_drops >= sum(1 for _ in chan.last_trace.get("drops", []))
          and named_drops > 0, f"named_drops={named_drops}")
    check("I8.j every sink call is emit(IntentEvent) (pure signal, whole fuzz)",
          all(c[0] == "emit" for c in sink.calls), f"calls={len(sink.calls)}")
    check("I8.k repeat presses while held were NAMED no-ops (the edge law held)",
          len(chan.last_trace.get("repeat_press", [])) > 0
          and len(chan.last_trace.get("no_op", [])) > 0,
          f"repeat={len(chan.last_trace.get('repeat_press', []))}, "
          f"no_op={len(chan.last_trace.get('no_op', []))}")


def main():
    print("climb_intent_tests -- U05 falsifiers "
          "(prereg: agents/U05_climb_intent/PREREGISTRATION.md)")
    print(f"seam sha256 at start: {SHA_SEAM_START}")
    print(f"mapper sha256 at start: {SHA_MAPPER_START}")
    falsifier_1()
    falsifier_2()
    falsifier_3()
    falsifier_4()
    falsifier_5()
    falsifier_6_start()
    falsifier_7()
    falsifier_8()
    falsifier_6_end()                     # the pinned check runs LAST
    print()
    if FAILURES:
        print(f"RESULT: FAIL ({len(FAILURES)} falsifier checks fired)")
        for f in FAILURES:
            print(f"  FIRED: {f}")
        return 1
    print("RESULT: GREEN -- all falsifier checks passed")
    print(f"seam sha256 at end:   {sha256_file(_SEAM_PATH)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
