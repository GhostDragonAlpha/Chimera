"""session_flow_tests.py -- X02's falsifiers, measured (agents/X02_flow/PREREGISTRATION.md).

Headless: an injected millisecond clock, the REAL U01 mapper + MockSink, and
doubles for the two declared world calls (World.boot / World.shutdown_engine).
No window, no process, no HTTP, no desktop input. The frozen table, the
input-gating rule, the declared restart path, the teardown ordering, and the
no-hidden-transitions law:

  F1  NO CODE-ONLY STATE     every state is reachable by key events through the
                             bindings alone; bindings and table actions cover
                             each other; every (state, action) NOT in the table
                             is a named no-op.
  F2  PAUSE LEAKS ZERO       deterministic mid-press pause: zero sink records
                             while paused, zero mapper events while suspended;
                             the resume tail is <= 2 records, each <= the
                             pre-pause speed, landing EXACTLY 0.0 then silence.
                             Plus a seeded 4000-event fuzz: no record is ever
                             attributed to a non-playing tick.
  F3  RESTART = DECLARED     the restart transition's world contact is EXACTLY
                             [release_all, boot x1] on the recording double; a
                             StrictWorld fuzz shows zero undeclared attempts; a
                             raising boot transitions NOWHERE; restart is
                             unreachable outside (paused, restart).
  F4  EXIT TEARDOWN          teardown exactly once per session from any state,
                             recorded as terminate -> wait -> kill (the declared
                             shutdown_engine shape); second exit is a named
                             drop; after exit the mapper is never called again.
  F5  NO HIDDEN TRANSITIONS  zero events + advancing clock transitions nothing;
                             the module's only public mutators are key/mouse/
                             tick; the import set adds no forbidden module; the
                             frozen numbers are the SAME OBJECTS as U01's.

    python tools/monkey_campaign/product/session_flow_tests.py
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import input_mapper as M                                        # noqa: E402
import session_flow as SF                                       # noqa: E402
from session_flow import (                                      # noqa: E402
    RecordingRestart, TeardownDouble, StrictWorld, CountingMapper,
)
from tools.monkey_campaign.product.input_mapper import (        # noqa: E402
    InputMapper, MockSink,
)

FAILURES = []
CHECKS = [0]                   # total checks fired (the receipt's count)
FUZZ_SEED = 20260924           # frozen with the prereg; never tuned
FUZZ_EVENTS = 4000

# THE GATING FUZZ'S KEY SET: no `Q` -- exit is TERMINAL and would make the rest
# of a randomized run vacuous; its post-state coverage is F4's own dedicated
# 500-event post-exit fuzz. Everything else cycles attract/playing/paused.
FUZZ_KEYS = [k for k in SF.DEFAULT_FLOW_BINDINGS if k != "Q"] + ["W", "A", "X", "F12"]


def check(name, ok, detail=""):
    CHECKS[0] += 1
    tag = "PASS" if ok else "FAIL"
    print(f"  [{tag}] {name}" + (f"  -- {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def make_flow(mapper=None, restart=None, teardown=None):
    """A real flow over the REAL mapper and MockSink unless doubles are given.
    The world calls are injected the way the live wiring will inject them:
    as BOUND METHODS of the declared referents (world.boot / world.shutdown_engine)."""
    sink = MockSink()
    mapper = mapper if mapper is not None else InputMapper(sink)
    world = restart if restart is not None else RecordingRestart()
    teardown_world = teardown if teardown is not None else TeardownDouble()
    flow = SF.SessionFlow(mapper, world.boot, teardown_world.shutdown_engine)
    return flow, mapper, sink, world, teardown_world


def press(flow, key, t):
    return flow.key(key, 1, t)


def dense_ticks(flow, t0, t1, step=1):
    """Tick every `step` ms; return the records the FLOW hands back."""
    out = []
    for t in range(t0, t1 + 1, step):
        out.extend(flow.tick(t))
    return out


# ── F1 NO CODE-ONLY STATE ────────────────────────────────────────────────────────
def falsifier_1():
    print("F1 NO CODE-ONLY STATE: all four states reachable by keys alone; "
          "bindings and table cover each other; off-table actions are named no-ops")
    # (a) every state reachable by key events alone -- no method call exists
    flow, mapper, sink, restart, teardown = make_flow()
    check("F1 attract is the initial state", flow.state == SF.ATTRACT)
    press(flow, "Return", 0)
    check("F1 attract->playing via Return", flow.state == SF.PLAYING)
    press(flow, "Escape", 1000)
    check("F1 playing->paused via Escape", flow.state == SF.PAUSED)
    press(flow, "R", 2000)
    check("F1 paused->playing via R (declared boot)", flow.state == SF.PLAYING
          and restart.calls == [("boot",)])
    press(flow, "Escape", 3000)
    press(flow, "Return", 4000)
    check("F1 paused->playing via Return (resume)", flow.state == SF.PLAYING)
    press(flow, "Escape", 5000)
    press(flow, "Q", 6000)
    check("F1 paused->exited via Q", flow.state == SF.EXITED
          and teardown.calls == ["terminate", "wait", "kill"])
    flow2, *_ = make_flow()
    press(flow2, "Q", 0)
    check("F1 attract->exited via Q (owned processes die from anywhere)",
          flow2.state == SF.EXITED)

    # (b) bindings and table actions cover each other, both directions
    bvals = set(SF.DEFAULT_FLOW_BINDINGS.values())
    tactions = {a for (_, a) in SF.TRANSITIONS}
    check("F1 every table action is a bindings value", tactions == bvals,
          f"table={sorted(tactions)} bindings={sorted(bvals)}")
    check("F1 every state appears as a transition source",
          {s for (s, _) in SF.TRANSITIONS} >= set(SF.STATES) - {SF.EXITED})

    # (c) every (state, action) NOT in the table is a named no-op, no transition
    bad = []
    for st in SF.STATES:
        for act in SF.FLOW_ACTIONS:
            if (st, act) in SF.TRANSITIONS:
                continue                     # legal rows are F1(a)'s coverage
            f, *_ = make_flow()
            f._state = st            # test rig: place the machine directly
            before = f.state
            f._transition(act, "<synthetic>", 0)
            if f.state != before or not f.last_trace.get("dropped"):
                bad.append((st, act))
    check("F1 all off-table (state, action) pairs are named no-ops",
          not bad, str(bad))

    # (d) an unbound key never transitions anything, in any state
    bad = []
    for st in SF.STATES:
        f, *_ = make_flow()
        f._state = st
        before = f.state
        for key in ("Z", "F12", "K"):
            f.key(key, 1, 0)
            f.key(key, 0, 1)
        if f.state != before:
            bad.append(st)
    check("F1 unbound keys never transition (no developer commands)", not bad,
          str(bad))


# ── F2 PAUSE LEAKS ZERO ──────────────────────────────────────────────────────────
def falsifier_2():
    print("F2 PAUSE LEAKS ZERO: no record while paused; mapper untouched while "
          "suspended; bounded decay tail on resume, exact 0.0, then silence")
    # (a) deterministic mid-press pause over the REAL mapper
    flow, mapper, sink, _, _ = make_flow()
    press(flow, "Return", 0)                          # attract -> playing (start)
    press(flow, "W", 1000)
    recs = dense_ticks(flow, 1000, 1000)
    v0 = recs[0].v_forward
    check("F2 the demand is live before the pause", len(sink) == 1 and v0 > 0.5,
          f"v0={v0}")
    press(flow, "Escape", 1010)                       # the pause (quiesce first)
    check("F2 the quiesce emptied held keys (U03 clause 4 floor)",
          len(mapper.held) == 0)
    n_at_pause, calls_at_pause = len(sink), None
    leaked = []
    for t in range(1011, 1391):                       # paused: dense boundaries
        got = flow.tick(t)
        if got or len(sink) != n_at_pause:
            leaked.append((t, got))
    check("F2 zero records while paused (dense 1 ms probe, 380 ms)",
          not leaked, str(leaked[:3]))
    press(flow, "Return", 1400)                       # resume
    tail = dense_ticks(flow, 1400, 1700)
    vals = [r.v_forward for r in tail]
    check("F2 resume tail is bounded (<= 2 records)", 0 < len(vals) <= 2,
          f"vals={vals}")
    check("F2 every tail record <= the pre-pause speed",
          all(v <= v0 for v in vals), f"v0={v0} vals={vals}")
    check("F2 the tail lands on EXACTLY 0.0", vals and vals[-1] == 0.0,
          f"vals={vals}")
    check("F2 the tail is monotone nonincreasing",
          all(a >= b for a, b in zip(vals, vals[1:])), f"vals={vals}")
    n_after = len(sink)
    silence = dense_ticks(flow, 1700, 2000)
    check("F2 then TOTAL silence until a fresh press",
          len(sink) == n_after and not silence)

    # (b) a SHORT pause (inside the decay window) still never exceeds v0
    flow, mapper, sink, _, _ = make_flow()
    press(flow, "Return", 0)                          # attract -> playing (start)
    press(flow, "W", 1000)
    v0 = dense_ticks(flow, 1000, 1000)[0].v_forward
    press(flow, "Escape", 1010)
    press(flow, "Return", 1050)                       # resume 40 ms later
    vals = [r.v_forward for r in dense_ticks(flow, 1050, 1400)]
    check("F2 short-pause tail bounded and exact-zero landing",
          0 < len(vals) <= 2 and all(v <= v0 for v in vals)
          and vals[-1] == 0.0, f"v0={v0} vals={vals}")

    # (c) while paused the mapper receives NO press/release/mouse/tick at all
    cm = CountingMapper()
    flow, _, sink, _, _ = make_flow(mapper=cm)
    press(flow, "Return", 0)                        # attract -> playing
    press(flow, "W", 10)
    flow.tick(10)
    press(flow, "Escape", 20)                       # the quiesce (release_all)
    base = list(cm.calls)
    check("F2 setup: the only pre-pause mapper calls are the declared ones",
          all(c[0] in ("press", "tick", "release_all") for c in base), str(base))
    press(flow, "W", 30)            # gameplay intent while paused -> named drop
    flow.mouse(5)
    flow.tick(40)
    flow.tick(50)
    grew = [c for c in cm.calls[len(base):]]
    check("F2 the mapper is untouched while suspended (event fuzz, 4 kinds)",
          not grew, str(grew[:3]))
    check("F2 the drops are NAMED, never silent",
          len(flow.last_trace.get("dropped", [])) >= 4)

    # (d) THE FUZZ: 4000 seeded events; no record is ever attributed to a
    # non-playing tick; the machine always reports a legal state
    rng = random.Random(FUZZ_SEED)
    flow, mapper, sink, restart, teardown = make_flow()
    keys = FUZZ_KEYS
    t, bad, n_records, n_ticks_paused = 0, [], 0, 0
    for i in range(FUZZ_EVENTS):
        r = rng.random()
        t += rng.randint(1, 40)
        if r < 0.45:
            flow.key(rng.choice(keys), rng.randint(0, 1), t)
        elif r < 0.60:
            flow.mouse(rng.randint(-3, 3))
        else:
            before, n0 = flow.state, len(sink)
            got = flow.tick(t)
            if before != SF.PLAYING:
                n_ticks_paused += 1
                if len(sink) != n0 or got:
                    bad.append((i, t, before, len(got)))
            else:
                n_records += len(got)
        if flow.state not in SF.STATES:
            bad.append((i, t, "illegal state", flow.state))
    check(f"F2 fuzz ({FUZZ_EVENTS} events, seed {FUZZ_SEED}): zero records "
          f"attributed to non-playing ticks ({n_ticks_paused} such ticks; "
          f"{n_records} records while playing)", not bad, str(bad[:3]))
    check("F2 fuzz exercised every non-playing state's tick path",
          n_ticks_paused > 500, f"{n_ticks_paused}")
    check("F2 fuzz produced records and transitions at all (not vacuous)",
          n_records > 20 and len(flow.last_trace.get("transitions", [])) > 3)


# ── F3 RESTART = THE DECLARED PATH ───────────────────────────────────────────────
def falsifier_3():
    print("F3 RESTART EQUALS THE DECLARED PATH: [release_all, boot x1] exactly; "
          "a StrictWorld sees zero undeclared attempts; a raising boot "
          "transitions nowhere; restart is unreachable outside paused")
    # (a) the exact contact sequence on the recording double
    flow, mapper, sink, restart, _ = make_flow()
    press(flow, "Return", 0)
    press(flow, "W", 1000)
    flow.tick(1000)
    press(flow, "Escape", 2000)
    restart.calls.clear()
    press(flow, "R", 3000)
    check("F3 restart world contact is EXACTLY one boot",
          restart.calls == [("boot",)], str(restart.calls))
    check("F3 the restart is NAMED as the declared world_boot path",
          flow.last_trace.get("restart_path") == [{"at_ms": 3000,
                                                   "declared": "world_boot"}])
    check("F3 restart quiesced the held keys across the boot",
          len(mapper.held) == 0)
    check("F3 restart lands in playing", flow.state == SF.PLAYING)

    # (b) StrictWorld fuzz: the flow never ATTEMPTS anything but boot
    rng = random.Random(FUZZ_SEED + 1)
    strict = StrictWorld()
    cm = CountingMapper()
    flow = SF.SessionFlow(cm, strict.boot, TeardownDouble().shutdown_engine)
    keys = [k for k in SF.DEFAULT_FLOW_BINDINGS if k != "Q"] + ["W", "Z"]
    t = 0
    for i in range(1500):
        r = rng.random()
        t += rng.randint(1, 30)
        if r < 0.5:
            flow.key(rng.choice(keys), rng.randint(0, 1), t)
        elif r < 0.65:
            flow.mouse(rng.randint(-2, 2))
        else:
            flow.tick(t)
    # count restarts that actually fired (each fired restart names world_boot)
    boots_expected = len(flow.last_trace.get("restart_path", []))
    check("F3 StrictWorld: zero undeclared contact attempts", not strict.attempts,
          str(strict.attempts[:3]))
    check("F3 StrictWorld: boot called exactly once per fired restart",
          strict.boot_calls == boots_expected > 0,
          f"boots={strict.boot_calls} restarts={boots_expected}")

    # (c) a RAISING boot transitions NOWHERE and is named
    flow, mapper, sink, restart, _ = make_flow(
        restart=RecordingRestart(error=RuntimeError("engine exe missing")))
    press(flow, "Return", 0)
    press(flow, "Escape", 1000)
    press(flow, "R", 2000)
    check("F3 failed boot: state stays paused (no half-restart claim)",
          flow.state == SF.PAUSED)
    check("F3 failed boot: the failure is NAMED",
          any("engine exe missing" in str(d) for d in
              flow.last_trace.get("restart_failed", [])))
    check("F3 failed boot: no transition recorded for it",
          not any(tr[1] == "restart" for tr in
                  flow.last_trace.get("transitions", [])))
    # a working resume is still possible after the refused restart
    press(flow, "Return", 3000)
    check("F3 after a refused restart, resume still works",
          flow.state == SF.PLAYING)

    # (d) restart is unreachable outside (paused, restart)
    for st in (SF.ATTRACT, SF.PLAYING, SF.EXITED):
        f, _, _, restart2, _ = make_flow()
        f._state = st
        press(f, "R", 0)
        check(f"F3 restart in {st} is a named no-op (no boot)",
              f.state == st and restart2.calls == [])


# ── F4 EXIT TEARDOWN ─────────────────────────────────────────────────────────────
def falsifier_4():
    print("F4 EXIT LEAVES NOTHING ALIVE: teardown exactly once per session, "
          "terminate->wait->kill; terminal afterwards; mapper never called again")
    for st in (SF.ATTRACT, SF.PLAYING, SF.PAUSED):
        cm = CountingMapper()
        td = TeardownDouble()
        flow = SF.SessionFlow(cm, RecordingRestart().boot, td.shutdown_engine)
        flow._state = st
        n_calls = len(cm.calls)
        press(flow, "Q", 1000)
        check(f"F4 exit from {st}: declared ordering terminate->wait->kill, once",
              td.calls == ["terminate", "wait", "kill"], str(td.calls))
        check(f"F4 exit from {st}: state is terminal exited", flow.state == SF.EXITED)
        rng = random.Random(FUZZ_SEED + 7)
        t = 2000
        for _ in range(500):                    # everything after exit: dropped
            t += rng.randint(1, 10)
            r = rng.random()
            if r < 0.5:
                flow.key(rng.choice(list(SF.DEFAULT_FLOW_BINDINGS) + ["W"]),
                         rng.randint(0, 1), t)
            elif r < 0.7:
                flow.mouse(3)
            else:
                flow.tick(t)
        check(f"F4 exit from {st}: 500 post-exit events, zero mapper calls, "
              f"state still exited",
              len(cm.calls) == n_calls and flow.state == SF.EXITED,
              f"grew by {len(cm.calls) - n_calls}")
        td2_calls_before = list(td.calls)
        press(flow, "Q", 9000)
        check(f"F4 exit from {st}: second Q never re-tears-down",
              td.calls == td2_calls_before)

    # a RAISING teardown does not claim exit
    class _Boom(TeardownDouble):
        def shutdown_engine(self):
            self.calls.append("boom")
            raise RuntimeError("engine already dead")

    flow, mapper, sink, _, td = make_flow(teardown=_Boom())
    press(flow, "Return", 0)
    press(flow, "Q", 1000)
    check("F4 failed teardown: state stays playing (no false exit claim)",
          flow.state == SF.PLAYING and any("engine already dead" in str(d)
                                           for d in flow.last_trace.get(
                                               "exit_failed", [])))


# ── F5 NO HIDDEN TRANSITIONS ─────────────────────────────────────────────────────
def falsifier_5():
    print("F5 NO HIDDEN TRANSITIONS / NO DEVELOPER COMMANDS: clock alone moves "
          "nothing; the only mutators are key/mouse/tick; imports are clean; "
          "frozen numbers are U01's own objects")
    # (a) 3000 ms of injected clock with zero events transitions nothing
    for st in SF.STATES:
        flow, *_ = make_flow()
        flow._state = st
        for t in range(0, 3000, 5):
            flow.tick(t)
        check(f"F5 clock alone never transitions {st}", flow.state == st)

    # (b) the public surface is exactly the three mutators + two reads
    import inspect
    pub = [n for n, _ in inspect.getmembers(SF.SessionFlow, inspect.isfunction)
           if not n.startswith("_")]
    check("F5 SessionFlow public methods are exactly key/mouse/tick",
          sorted(pub) == ["key", "mouse", "tick"], str(sorted(pub)))

    # (c) importing the module adds no forbidden capability
    before = set(sys.modules)
    import importlib
    importlib.reload(SF)
    added = set(sys.modules) - before
    forbidden = {"time", "datetime", "threading", "socket", "subprocess",
                 "urllib", "ctypes", "win32api", "pyautogui", "pynput"}
    hit = {m.split(".")[0] for m in added} & forbidden
    check("F5 import adds no time/thread/transport/desktop module", not hit,
          str(sorted(hit)))

    # (d) the source text declares no forbidden surface either: strip comments
    # and string literals with the tokenizer, then scan the CODE text
    import io
    import tokenize
    src = Path(SF.__file__).read_text(encoding="utf-8")
    pieces = [t.string for t in tokenize.generate_tokens(io.StringIO(src).readline)
              if t.type not in (tokenize.COMMENT, tokenize.STRING)]
    code_text = " ".join(pieces)
    for pat in ("import time", "import datetime", "import threading",
                "import socket", "import subprocess", "import urllib",
                "import ctypes", "keybd_event", "SendInput", "SetCursorPos",
                "perf_counter", "time.time"):
        check(f"F5 no forbidden surface in code: {pat!r}", pat not in code_text)

    # (e) the frozen numbers are the SAME OBJECTS as U01's (never redeclared)
    check("F5 INTERVAL_MS is U01's object", SF.INTERVAL_MS is M.INTERVAL_MS)
    check("F5 RELEASE_DECAY_MS is U01's object",
          SF.RELEASE_DECAY_MS is M.RELEASE_DECAY_MS)
    check("F5 VALID_MS is U01's object", SF.VALID_MS is M.VALID_MS)
    reassigned = [pat for pat in ("INTERVAL_MS =", "RELEASE_DECAY_MS =",
                                  "VALID_MS =", "= 0.763", "V_MAX")
                  if pat in code_text]
    check("F5 no frozen number redeclared anywhere in the module",
          not reassigned, str(reassigned))


def main():
    print("session_flow_tests -- X02 falsifiers "
          f"(seed {FUZZ_SEED}, {FUZZ_EVENTS} fuzz events)")
    falsifier_1()
    falsifier_2()
    falsifier_3()
    falsifier_4()
    falsifier_5()
    print()
    if FAILURES:
        print(f"RESULT: {len(FAILURES)} FAILED: {FAILURES}")
        rc = 1
    else:
        print("RESULT: ALL CHECKS PASS")
        rc = 0

    # ── the receipt (agents/X02_flow/receipts/) ──────────────────────────────
    def sha(p):
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()

    receipt = {
        "schema": "chimera.monkey.x02_flow_tests.v1",
        "date": "2026-09-24",
        "seed": FUZZ_SEED,
        "fuzz_events": FUZZ_EVENTS,
        "result": "PASS" if rc == 0 else "FAIL",
        "checks_total": CHECKS[0],
        "failed": FAILURES,
        "modules": {
            "session_flow.py": sha(Path(SF.__file__).resolve()),
            "input_mapper.py": sha(Path(M.__file__).resolve()),
            "session_flow_tests.py": sha(Path(__file__).resolve()),
        },
        "declared_referents": {
            "restart": "tools/playable_slice/slice_server.py:94-135 World.boot()",
            "teardown": "tools/playable_slice/slice_server.py:174-181 "
                        "World.shutdown_engine()",
            "quiesce_hook": "tools/monkey_campaign/product/input_mapper.py:225-228 "
                            "release_all",
        },
    }
    out = _ROOT / "tools/monkey_campaign/agents/X02_flow/receipts"
    out.mkdir(parents=True, exist_ok=True)
    (out / "session_flow_tests_receipt.json").write_text(
        json.dumps(receipt, indent=1), encoding="utf-8")
    print(f"receipt: {out / 'session_flow_tests_receipt.json'}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
