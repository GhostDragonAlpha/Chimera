"""focus_policy_tests.py -- U03's falsifiers, measured (PREREGISTRATION.md).

Headless: injected millisecond clocks, MockSink seam doubles (U01's own),
synthetic events only, no window, no desktop input, no engine process, no
real focus change, no process touched. The policy module is measured
against U01's frozen numbers (product/input_mapper.py, READ-ONLY):

  P1  NO-STUCK      after any release/blur/disconnect at E: no positive-speed
                    record later than E + the decay deadline; the stream lands
                    on an EXACT 0.0 record and then goes silent; post-E
                    records stay inside U01's bounds; a decay tail is monotone.
  P2  CONSISTENCY   blur's sink stream is byte-identical to U01's own
                    release_all at the same instant (same count, values,
                    issued ticks, source); the frozen numbers are the SAME
                    OBJECTS (imported, not redeclared); no frozen literal is
                    duplicated in the module source.
  P3  EXPIRY FLOOR  a stalled injected tick clock + a held key: every record
                    that ages past the max age is dropped AT EMISSION, named,
                    never delivered; a healthy clock drops ZERO (the belt
                    never fires spuriously); the boundary matches is_expired
                    exactly (strictly-greater).
  P4  NO DESKTOP    the module's imports are exactly the declared set; no
                    transport / desktop-injection / wall-clock surface; the
                    tests drive it with synthetic events only.
  P5  NAMED STATE   the disconnected state is a queryable name (disconnect
                    dominates blur); dropped intent is named, never silent;
                    recovery re-arms with an EMPTY held set (no phantom keys)
                    and a fresh grid.
  P6  CYCLES        a 2000-event randomized fuzz (input + policy events +
                    jittered clock, frozen seed) never restarts a decay tail
                    and satisfies the no-stuck invariant at EVERY demand-
                    clearing event instant.

    python tools/monkey_campaign/product/focus_policy_tests.py
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import input_mapper as M                                    # noqa: E402
import focus_policy as FP                                   # noqa: E402
from tools.science_funnel.typeb_export.command_record import (  # noqa: E402
    CommandRecord, V_MAX_IN_BAND_M_S as V_MAX,
)

OMEGA = M.OMEGA_MAX_RAD_S
DECAY = M.RELEASE_DECAY_MS
FAILURES = []
SPEED_ACTIONS = ("forward", "backward")
KEYS = ["W", "A", "S", "D", "Up", "Down", "Left", "Right", "Shift", "Space", "X"]


def check(name, ok, detail=""):
    tag = "PASS" if ok else "FAIL"
    print(f"  [{tag}] {name}" + (f"  -- {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def dense_ticks(fp, t0, t1, step=1):
    """Tick every `step` ms; return [(t, record)] for what reached the sink."""
    out = []
    for t in range(t0, t1 + 1, step):
        for rec in fp.tick(t):
            out.append((t, rec))
    return out


def build(bindings=None, tick_source=None):
    """A policy + sink pair wired exactly as the live harness would: ONE
    emission path, mapper -> gate -> sink (the factory makes the caller's
    mapper with the policy's gate as its sink)."""
    sink = M.MockSink()
    fp = FP.FocusPolicy(
        sink,
        mapper_factory=lambda gate: M.InputMapper(gate, bindings=bindings,
                                                  tick_source=tick_source))
    return fp, fp.mapper, sink


# ── P1 NO-STUCK (deterministic scenarios) ─────────────────────────────────────
def falsifier_1():
    print("P1 NO-STUCK: every clearing event decays to exact zero, then silence")

    # S1: blur with a speed key held mid-command
    fp, _, sink = build()
    fp.press("W", 1000)
    dense_ticks(fp, 1000, 1119)
    n_pre = len(sink.records)
    fp.on_blur(1120)
    tail = dense_ticks(fp, 1121, 1500)
    vs = [(t, r.v_forward) for t, r in tail]
    check("P1.a blur mid-command: post-blur stream is monotone non-increasing",
          all(a[1] >= b[1] for a, b in zip(vs, vs[1:])), f"{vs[:6]}")
    zeros = [(t, v) for t, v in vs if v == 0.0]
    check("P1.b an EXACT-0.0 record lands at or before blur+decay deadline",
          bool(zeros) and zeros[0][0] <= 1120 + DECAY,
          f"zero at {zeros[0] if zeros else None}, deadline {1120 + DECAY}")
    after = [(t, v) for t, v in vs if t > zeros[0][0]] if zeros else None
    check("P1.c TOTAL SILENCE after the zero (the inert path resumed)",
          after == [], f"{len(after or [])} records after the zero")
    check("P1.d no positive-speed record later than blur+decay deadline",
          all(v <= 0.0 for t, v in vs if t > 1120 + DECAY))
    check("P1.e the pre-blur command was live (the scenario is not vacuous)",
          n_pre >= 3, f"{n_pre} records before the blur")

    # S2: blur DURING an active decay tail must NOT restart it (a restart
    # would EXTEND movement past the deadline)
    fp, _, sink = build()
    fp.press("W", 1000)
    dense_ticks(fp, 1000, 1119)
    v0 = sink.records[-1].v_forward
    fp.release("W", 1119)                      # physical release: tail from 1119
    fp.on_blur(1125)                           # blur 6 ms into the tail: no-op release
    tail = dense_ticks(fp, 1126, 1500)
    at_1150 = [r.v_forward for t, r in tail if t == 1150]
    check("P1.f blur during a tail does NOT restart it (the tail keeps its "
          "original release instant)",
          at_1150 == [v0 * (1.0 - 31.0 / 100.0)],
          f"v(1150) = {at_1150} (expected the 1119-tail sample v0*0.69, "
          f"not the restarted v0*0.75)")
    zeros = [(t, r.v_forward) for t, r in tail if r.v_forward == 0.0]
    check("P1.g the interrupted tail still lands exact zero at or before its "
          "own deadline, then silence",
          bool(zeros) and zeros[0][0] <= 1119 + DECAY
          and not [1 for t, r in tail if t > zeros[0][0]],
          f"zero at {zeros[0] if zeros else None}, deadline {1119 + DECAY}")

    # S3: blur while the live-zero key (S) is held: the LAST record is already
    # exactly zero, and blur then produces silence
    fp, _, sink = build()
    fp.press("S", 1000)
    dense_ticks(fp, 1000, 1100)
    check("P1.h the pre-blur stream ends on an exact live-zero record",
          bool(sink.records) and sink.records[-1].v_forward == 0.0)
    fp.on_blur(1105)
    tail = dense_ticks(fp, 1106, 1400)
    check("P1.i blur from the live-zero state emits NOTHING further (already "
          "at zero; no stuck demand)",
          tail == [], f"{len(tail)} post-blur records")

    # S4: blur while idle
    fp, _, sink = build()
    fp.on_blur(1000)
    check("P1.j blur while idle emits nothing and stays inert",
          dense_ticks(fp, 1001, 1200) == [] and len(sink.records) == 0)

    # S5: disconnect mid-command: same decay, named state, then clean re-arm
    fp, _, sink = build()
    fp.press("W", 1000)
    dense_ticks(fp, 1000, 1119)
    fp.on_disconnect(1120)
    tail = dense_ticks(fp, 1121, 1500)
    zeros = [(t, r.v_forward) for t, r in tail if r.v_forward == 0.0]
    check("P1.k disconnect mid-command: exact zero lands at or before "
          "disconnect+decay deadline, then silence",
          bool(zeros) and zeros[0][0] <= 1120 + DECAY
          and not [1 for t, r in tail if t > zeros[0][0]],
          f"zero at {zeros[0] if zeros else None}, deadline {1120 + DECAY}")

    # S6: blur while disconnected must not restart the tail either
    fp, _, sink = build()
    fp.press("W", 900)
    dense_ticks(fp, 900, 949)
    v0 = sink.records[-1].v_forward
    fp.on_disconnect(950)                      # tail from 950
    fp.on_blur(960)                            # blur 10 ms into the tail
    tail = dense_ticks(fp, 950, 1400)          # the grid was due AT 950
    at_950 = [r.v_forward for t, r in tail if t == 950]
    at_1000 = [r.v_forward for t, r in tail if t == 1000]
    check("P1.l blur-while-disconnected does not restart the tail (the "
          "boundary-sampled tail keeps the 950 release instant: sample at "
          "950, EXACT zero at the second boundary)",
          at_950 == [v0] and at_1000 == [0.0],
          f"v(950) = {at_950}, v(1000) = {at_1000} (a restarted tail from "
          f"960 would show v0*0.6 at 1000, not exact zero)")


# ── P2 CONSISTENCY WITH U01 ──────────────────────────────────────────────────
def falsifier_2():
    print("P2 CONSISTENCY: policy blur == U01's own release_all, byte for byte")

    def drive(surface):
        surface.press("W", 1000)
        surface.press("A", 1000)
        surface.mouse(500)
        for t in range(1000, 1121):
            surface.tick(t)

    bare_sink = M.MockSink()
    bare = M.InputMapper(bare_sink)
    drive(bare)
    bare.release_all(1120)                     # U01's physical-release path
    for t in range(1121, 1401):
        bare.tick(t)

    pol_sink = M.MockSink()
    fp = FP.FocusPolicy(pol_sink)              # ONE path: mapper -> gate -> sink
    drive(fp)
    fp.on_blur(1120)                           # the policy path
    for t in range(1121, 1401):
        fp.tick(t)

    same_len = len(bare_sink.records) == len(pol_sink.records)
    fields = ("v_forward", "yaw_rate", "issued_tick", "source", "record_version")
    mismatches = []
    if same_len:
        for i, (rb, rp) in enumerate(zip(bare_sink.records, pol_sink.records)):
            for f in fields:
                if getattr(rb, f) != getattr(rp, f):
                    mismatches.append((i, f, getattr(rb, f), getattr(rp, f)))
    check("P2.a blur's sink stream is BYTE-IDENTICAL to U01 release_all at the "
          "same instant (count, values, issued ticks, source, version)",
          same_len and not mismatches,
          f"{len(bare_sink.records)} vs {len(pol_sink.records)} records, "
          f"{len(mismatches)} field mismatches")
    check("P2.a' the policy never rewrote a record (source stays U01's)",
          all(r.source == M.SOURCE_ID for r in pol_sink.records))

    consts = {"RELEASE_DECAY_MS": M.RELEASE_DECAY_MS, "VALID_MS": M.VALID_MS,
              "INTERVAL_MS": M.INTERVAL_MS, "EXPIRY_TICKS": M.EXPIRY_TICKS,
              "V_MAX_IN_BAND_M_S": M.V_MAX_IN_BAND_M_S,
              "OMEGA_MAX_RAD_S": M.OMEGA_MAX_RAD_S}
    bad = [n for n, v in consts.items() if not (getattr(FP, n) is v)]
    check("P2.b every frozen number is the SAME OBJECT as U01's (imported, "
          "not redeclared)", not bad, f"redeclared: {bad}" if bad
          else "identity holds for all 6")
    check("P2.b' MAX_AGE_MS is the expiry floor itself",
          FP.MAX_AGE_MS is M.VALID_MS)

    source = Path(FP.__file__).read_text(encoding="utf-8")
    literals = ["= 100", "= 50", "0.763", "1.6", "300", "= 30"]
    hits = [s for s in literals if s in source]
    check("P2.c no frozen literal is duplicated anywhere in the module source",
          not hits, f"hits: {hits}" if hits else f"none of {literals} present")


# ── P3 EXPIRY FLOOR (belt over decay) ────────────────────────────────────────
def falsifier_3():
    print("P3 EXPIRY FLOOR: stale records are dropped at emission, by name")

    # a stalled injected tick source: issued_tick freezes while now_ms advances
    box = {"tick": 300}                        # the physics tick of now_ms = 1000
    fp, mapper, sink = build(tick_source=lambda: box["tick"])
    fp.press("W", 1000)
    schedule = [1000, 1050, 1100, 1150, 1200, 1300]
    delivered = []
    for t in schedule:
        for rec in fp.tick(t):
            delivered.append((t, rec))
    check("P3.a exactly the fresh records reached the sink (3 of 6 boundary "
          "ticks; the stalled clock aged the rest past the max age)",
          [t for t, _ in delivered] == [1000, 1050, 1100],
          f"delivered at {[t for t, _ in delivered]}")
    ages = [(t * M.PHYSICS_HZ // 1000) - rec.issued_tick for t, rec in delivered]
    check("P3.b every DELIVERED record was within the max age at delivery "
          "(strictly-greater boundary, same as is_expired)",
          len(ages) == 3 and all(a <= M.EXPIRY_TICKS for a in ages),
          f"delivery ages in physics ticks: {ages} (0/15/30 kept; 45/60/90 "
          f"dropped)")
    drops = fp.last_trace.get("expired_at_gate", [])
    check("P3.c every drop is NAMED in the trace with its issued tick",
          len(drops) == 3 and all(d[0] == 300 for d in drops),
          f"trace: {drops}")
    check("P3.d the gate's stats agree with its trace",
          fp.gate_stats["expired_at_gate"] == 3 and fp.gate_stats["passed"] == 3,
          f"{fp.gate_stats}")

    # the healthy-clock control: the belt never fires spuriously
    fp2, _, sink2 = build()
    fp2.press("W", 1000)
    dense_ticks(fp2, 1000, 1119)
    fp2.on_blur(1120)
    dense_ticks(fp2, 1121, 1400)
    check("P3.e a healthy clock: ZERO records dropped at the gate",
          fp2.gate_stats["expired_at_gate"] == 0
          and "expired_at_gate" not in fp2.last_trace,
          f"stats {fp2.gate_stats}")


# ── P4 NO OPERATOR DESKTOP (headless purity) ─────────────────────────────────
def falsifier_4():
    print("P4 NO DESKTOP: imports, surfaces, and the test's own honesty")
    source = Path(FP.__file__).read_text(encoding="utf-8")
    mods = set()
    for ln in source.splitlines():
        if not ln.startswith(("import ", "from ")):
            continue
        ln = ln.split("#")[0].strip()
        if not ln:
            continue
        parts = ln.split()
        if parts[0] == "from":
            mods.add(parts[1])
        else:
            mods.add(parts[1].split(" as ")[0].split(".")[0])
    allowed = {"__future__", "sys", "pathlib",
               "tools.science_funnel.typeb_export.command_record", "input_mapper"}
    check("P4.a imports are exactly the declared set (stdlib + the seam's "
          "record + U01's mapper)", mods <= allowed, f"imports: {sorted(mods)}")

    forbidden = ["keybd_event", "SendInput", "SetCursorPos", "GetCursorPos",
                 "GetForegroundWindow", "AttachThreadInput", "socket", "urllib",
                 "requests", "ctypes", "subprocess", "win32", "pyautogui",
                 "pynput", "import time", "datetime", "psutil", "os.startfile",
                 "qpos", "pose_apply", "hinge_bin", "joints_bin", "stride_bin"]
    hits = [s for s in forbidden if s in source]
    check("P4.b no desktop-injection / transport / wall-clock / pose surface "
          "in the module", not hits,
          f"hits: {hits}" if hits else f"none of {len(forbidden)} markers present")

    # the test file's own honesty: imports only stdlib + the modules under test
    test_mods = set()
    for ln in Path(__file__).read_text(encoding="utf-8").splitlines():
        if not ln.startswith(("import ", "from ")):
            continue
        ln = ln.split("#")[0].strip()
        if not ln:
            continue
        parts = ln.split()
        if parts[0] == "from":
            test_mods.add(parts[1])
        else:
            test_mods.add(parts[1].split(" as ")[0].split(".")[0])
    test_allowed = {"__future__", "random", "sys", "pathlib", "input_mapper",
                    "focus_policy",
                    "tools.science_funnel.typeb_export.command_record"}
    check("P4.c the TESTS themselves are synthetic-event only (imports are "
          "exactly stdlib + U01's mapper + the policy)", test_mods <= test_allowed,
          f"imports: {sorted(test_mods)}")


# ── P5 NAMED STATE + CLEAN RE-ARM ────────────────────────────────────────────
def falsifier_5():
    print("P5 NAMED STATE: disconnect dominates; drops named; recovery re-arms")
    fp, _, sink = build()
    check("P5.a fresh policy reports 'focused'", fp.state == "focused")
    fp.on_blur(1000)
    check("P5.b blur -> 'blurred'", fp.state == "blurred")
    fp.on_blur(1001)
    check("P5.c double blur is a NAMED no-op (one release receipt only)",
          fp.state == "blurred"
          and len(fp.last_trace.get("released_all", [])) == 1
          and ("blur", 1001) in fp.last_trace.get("no_op", []),
          f"released_all {fp.last_trace.get('released_all')}, "
          f"no_op {fp.last_trace.get('no_op')}")
    fp.on_disconnect(1002)
    check("P5.d disconnect DOMINATES blur in the named state",
          fp.state == "disconnected")
    fp.on_reconnect(1003)
    check("P5.e reconnect restores 'blurred' (the two states are independent)",
          fp.state == "blurred")
    fp.on_focus(1004)
    check("P5.f focus restores 'focused'", fp.state == "focused")

    # dropped intent is named, never silent, and never reaches the mapper
    fp.on_blur(1010)
    fp.press("W", 1011)
    fp.mouse(120)
    drops = fp.last_trace.get("dropped_blurred", [])
    check("P5.g press/mouse while blurred are DROPPED and NAMED (the mapper's "
          "held set stays empty)",
          fp.held == frozenset()
          and ("W", 1011) in drops
          and (("mouse", 120.0), "n/a") in drops,
          f"drops: {drops}")
    fp.on_disconnect(1012)
    fp.press("S", 1013)
    ddrops = fp.last_trace.get("dropped_disconnected", [])
    check("P5.h press while disconnected is DROPPED under the disconnect name",
          fp.held == frozenset() and ("S", 1013) in ddrops, f"drops: {ddrops}")

    # releases are never gated
    fp2, mapper2, _ = build()
    fp2.press("W", 1000)
    fp2.on_disconnect(1010)
    fp2.release("W", 1011)                     # must pass through
    check("P5.i a release is NEVER gated -- the mapper saw it (a release can "
          "only reduce demand)",
          any(n == "W" for n, _ in mapper2.last_trace.get("released", []))
          and "W" not in [w for w, _ in
                          fp2.last_trace.get("dropped_disconnected", [])])

    # clean re-arm: empty held set, fresh grid, first press emits at ITS boundary
    fp.on_reconnect(1020)
    fp.on_focus(1021)
    check("P5.j recovery receipts show an EMPTY held set (no phantom keys)",
          fp.held == frozenset()
          and all(held == [] for _, _, held in fp.last_trace.get("rearmed", [])),
          f"rearmed: {fp.last_trace.get('rearmed')}")
    fp.press("W", 1030)
    recs = fp.tick(1030)
    check("P5.k the first accepted press arms a FRESH grid (emits at its own "
          "boundary, at the band ceiling, and nothing existed before it)",
          len(recs) == 1 and recs[0].v_forward == V_MAX
          and len(sink.records) == 1, f"{len(sink.records)} record(s) total")


# ── P6 CYCLES + the 2000-event randomized fuzz ───────────────────────────────
def falsifier_6():
    print("P6 CYCLES + FUZZ: the invariant holds at every clearing event "
          "(4000 frames, seed 20260924; the brief's floor is 200 events)")
    rng = random.Random(20260924)
    sink = M.MockSink()
    fp = FP.FocusPolicy(sink)                  # default: a plain InputMapper
    mapper = fp.mapper

    now = 10_000
    deliveries = []                # (t, record) -- what reached the sink, in order
    clears = []                    # demand-clearing event instants (E)
    speed_presses = []             # accepted speed-press instants (window ends)
    n_blur = n_disc = n_drops = 0
    states_seen = set()
    phantom = None

    for i in range(4000):
        r = rng.random()
        if r < 0.15:
            act = fp.press(rng.choice(KEYS), now)
            if act in SPEED_ACTIONS:
                speed_presses.append(now)
            elif act is None and fp.state != "focused":
                n_drops += 1
        elif r < 0.30:
            k = rng.choice(KEYS)
            held_speeds = [n for n in fp.held
                           if mapper.bindings.get(n) in SPEED_ACTIONS]
            fp.release(k, now)
            if (mapper.bindings.get(k) in SPEED_ACTIONS
                    and held_speeds == [k]):
                clears.append(now)          # the walk demand just cleared
        elif r < 0.37:
            fp.mouse(rng.uniform(-2000.0, 2000.0))
        elif r < 0.40:
            fp.on_blur(now)
            n_blur += 1
            clears.append(now)
        elif r < 0.43:
            fp.on_focus(now)
        elif r < 0.46:
            fp.on_disconnect(now)
            n_disc += 1
            clears.append(now)
        elif r < 0.49:
            fp.on_reconnect(now)
        # else: a quiet frame
        for rec in fp.tick(now):
            deliveries.append((now, rec))
        states_seen.add(fp.state)
        if fp.state != "focused" and len(fp.held) != 0:
            phantom = (i, fp.state, sorted(fp.held))
            break
        # every frame advances the injected clock (a real harness loop),
        # with occasional stalls
        now += rng.randint(100, 700) if rng.random() < 0.04 else rng.randint(1, 40)

    # flush: land any in-flight decay tail before the run ends (no new
    # intent, so nothing fresh can arm)
    for t in range(now + 1, now + 401):
        for rec in fp.tick(t):
            deliveries.append((t, rec))

    check("P6.z no phantom key while the gate is closed (a blur/disconnect "
          "released everything; drops never arm keys)",
          phantom is None,
          f"violation at {phantom}" if phantom else
          f"{len(deliveries)} deliveries across states {sorted(states_seen)}")
    if phantom is not None:
        return

    # the no-stuck invariant, evaluated at EVERY demand-clearing instant E.
    # Window: (E, next accepted speed press) -- EXCLUSIVE of the press instant,
    # whose records are the NEW command, not the old one. The prereg's exact
    # wording is measured here: no POSITIVE-speed record later than
    # E + the decay deadline (the exact-zero RECORD may ARRIVE at the first
    # boundary after a stall past the deadline -- U01's frozen no-replay
    # clause; between the deadline and that arrival the consumer holds only
    # an expired record, which its own is_expired contract makes inert);
    # the tail lands on zero and then goes silent.
    bad = []
    for E in clears:
        later = [t for t in speed_presses if t > E]
        w_end = min(later) if later else None
        if w_end is None:
            R = [(t, rec) for t, rec in deliveries if t > E]
        else:
            R = [(t, rec) for t, rec in deliveries if E < t < w_end]
        for t, rec in R:                    # (i) the positive-speed deadline
            if rec.v_forward > 0.0 and t > E + DECAY:
                bad.append(("late-positive", E, t, rec.v_forward))
        if not R or w_end is not None:
            continue                        # a fresh accepted press owns the rest
        zeros = [t for t, rec in R if rec.v_forward == 0.0]
        if not zeros:
            bad.append(("no-zero", E, [(t, rec.v_forward) for t, rec in R[:3]]))
            continue
        zt = zeros[0]
        for t, rec in R:                    # (ii) silence after the zero
            if t > zt:
                bad.append(("post-zero", E, t, rec.v_forward))
                break
    check("P6.a no clearing event leaves a positive-speed record past its "
          "deadline, a missing zero, or a post-zero emission",
          not bad, f"{len(clears)} clearing events, {len(deliveries)} "
          f"deliveries, {len(bad)} violations"
          + (f", first: {bad[0]}" if bad else ""))

    bad_bounds = [r for _, r in deliveries
                  if not isinstance(r, CommandRecord)
                  or not (0.0 <= r.v_forward <= V_MAX)
                  or abs(r.yaw_rate) > OMEGA
                  or r.v_forward != r.v_forward or r.yaw_rate != r.yaw_rate]
    check("P6.b every delivered record is finite and inside U01's bounds",
          not bad_bounds, f"{len(deliveries)} records checked, "
          f"{len(bad_bounds)} bad")
    stale = [(t, r) for t, r in deliveries if mapper.is_expired(r, t)]
    check("P6.c no DELIVERED record was already expired at delivery (the belt, "
          "re-checked per record)", not stale, f"{len(stale)} stale deliveries")

    nonvac = (n_blur >= 30 and n_disc >= 30 and n_drops >= 5
              and len(deliveries) >= 200 and len(clears) >= 60)
    check("P6.d the fuzz is not vacuous (policy events, drops, clears, and "
          "emissions all exercised)",
          nonvac, f"blur {n_blur}, disconnect {n_disc}, drops {n_drops}, "
          f"clears {len(clears)}, deliveries {len(deliveries)}, "
          f"states {sorted(states_seen)}")


def main():
    print("focus_policy_tests -- U03 falsifiers "
          "(prereg: agents/U03_focus/PREREGISTRATION.md)")
    falsifier_1()
    falsifier_2()
    falsifier_3()
    falsifier_4()
    falsifier_5()
    falsifier_6()
    print()
    if FAILURES:
        print(f"VERDICT: FAIL -- {len(FAILURES)} falsifier check(s) fired: {FAILURES}")
        return 1
    print("VERDICT: GREEN -- all falsifier checks passed; U01's frozen numbers "
          "held under the focus/disconnect policy.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
