"""input_mapper_tests.py -- U01's falsifiers, measured (PREREGISTRATION.md).

Headless: an injected millisecond clock, a MockSink seam double, no window,
no desktop input, no engine process. The mapper cannot touch state -- the
tests measure that, plus the bounds, the 50 ms discipline, the release decay,
and the remap law:

  F1  NO-TELEPORT   every sink call is emit(CommandRecord); the module's
                    imports are exactly the declared set; no pose-route /
                    state-writing / desktop-injection strings exist in it.
  F2  OUT-OF-BOUNDS 5000-event fuzz: every emitted record has
                    0 <= v_forward <= 0.763625 (the seam's measured in-band
                    ceiling) and |yaw_rate| <= 1.6 (the declared input-side
                    steer bound); nothing non-finite; never a negative speed.
  F3  CLOCK         injected 1 ms ticks: held-key records EXACTLY 50 ms apart;
                    early ticks emit nothing; a stall yields exactly ONE
                    record (current state), never a replay burst.
  F4  RELEASE       the decay tail is monotone, lands on EXACTLY 0.0 at or
                    before release+100 ms, and emission then STOPS (the seam's
                    inert path resumes).
  F5  REMAP         a bindings remap changes emitted VALUES only: same record
                    type/version, same bounds, same clock, same adapter
                    projection (routed_yaw_rate False; velocity passthrough).
  F6  SEAM STATES   the two seam states stay distinct and reachable: idle
                    emits NOTHING (inert), S held emits LIVE ZEROS; steering
                    alone emits nothing; sprint/jump refuse BY NAME; the
                    expiry contract expires at 2 intervals.

    python tools/monkey_campaign/product/input_mapper_tests.py
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import input_mapper as M                                    # noqa: E402
from tools.science_funnel.typeb_export.command_record import (  # noqa: E402
    CommandRecord, V1FamilyAdapter, V_MAX_IN_BAND_M_S as V_MAX,
)

OMEGA = M.OMEGA_MAX_RAD_S
FAILURES = []


def check(name, ok, detail=""):
    tag = "PASS" if ok else "FAIL"
    print(f"  [{tag}] {name}" + (f"  -- {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


# ── shared harness ───────────────────────────────────────────────────────────────
def dense_ticks(m, t0, t1, step=1):
    """Tick every `step` ms; return (records, timestamps-of-records)."""
    recs, ts = [], []
    for t in range(t0, t1 + 1, step):
        for r in m.tick(t):
            recs.append(r)
            ts.append(t)
    return recs, ts


# ── F1 NO-TELEPORT ───────────────────────────────────────────────────────────────
def falsifier_1():
    print("F1 NO-TELEPORT: the only output is emit(CommandRecord); no state writes")
    sink = M.MockSink()
    m = M.InputMapper(sink)
    m.press("W", 1000)
    m.mouse(300)
    m.press("A", 1001)
    dense_ticks(m, 1000, 1300)
    m.release("W", 1310)
    m.press("Shift", 1311)
    dense_ticks(m, 1310, 1450)
    m.release_all(1451)
    dense_ticks(m, 1451, 1700)

    ok_calls = all(name == "emit" and isinstance(rec, CommandRecord)
                   for name, rec in sink.calls)
    check("F1a every sink call is emit(CommandRecord)", ok_calls,
          f"{len(sink.calls)} calls, {len(sink.records)} records")
    check("F1b calls == records (nothing else was handed to the seam)",
          len(sink.calls) == len(sink.records))

    source = Path(M.__file__).read_text(encoding="utf-8")
    forbidden = ["pose_apply", "hinge_bin", "joints_bin", "stride_bin", "gait_bin",
                 "urllib", "socket", "requests", "ctypes", "subprocess",
                 "qpos", "keybd_event", "SetCursorPos", "SendInput"]
    hits = [s for s in forbidden if s in source]
    check("F1c no pose-route / transport / desktop-injection strings in the module",
          not hits, f"hits: {hits}" if hits else "none of 14 markers present")
    import_lines = [ln for ln in source.splitlines()
                    if ln.startswith(("import ", "from "))]
    mods = set()
    for ln in import_lines:
        mods.add(ln.split()[1] if ln.startswith("from ") else ln.split()[1].split(".")[0])
    allowed = {"__future__", "sys", "pathlib",
               "tools.science_funnel.typeb_export.command_record"}
    check("F1d imports are exactly the declared set (stdlib + the seam's record)",
          mods <= allowed, f"imports: {sorted(mods)}")


# ── F2 OUT-OF-BOUNDS (the 5000-event fuzz) ───────────────────────────────────────
def falsifier_2():
    print("F2 OUT-OF-BOUNDS: 5000 random input events never leave the band")
    rng = random.Random(20260924)               # frozen seed: the run reproduces
    sink = M.MockSink()
    m = M.InputMapper(sink)
    keys = ["W", "A", "S", "D", "Up", "Down", "Left", "Right", "Shift",
            "Space", "X"]                      # X unbound on purpose
    now = 10_000
    bad = []
    for i in range(5000):
        r = rng.random()
        if r < 0.30:
            m.press(rng.choice(keys), now)
        elif r < 0.55:
            m.release(rng.choice(keys), now)
        elif r < 0.70:
            m.mouse(rng.uniform(-5000.0, 5000.0))
        else:
            now += rng.randint(1, 250)         # dense stretches AND stalls
        for rec in m.tick(now):
            if (not isinstance(rec, CommandRecord)
                    or rec.v_forward != rec.v_forward or rec.v_forward in (float("inf"), float("-inf"))
                    or not (0.0 <= rec.v_forward <= V_MAX)
                    or rec.yaw_rate != rec.yaw_rate or abs(rec.yaw_rate) > OMEGA
                    or rec.v_forward < 0.0):
                bad.append((i, rec))
    check("F2a every one of the fuzz records is finite and inside the bounds",
          not bad, f"{len(sink.records)} records checked, "
                   f"{len(bad)} violations" + (f", first: {bad[0]}" if bad else ""))
    check("F2b the fuzz actually exercised emission (not vacuously green)",
          len(sink.records) >= 500, f"{len(sink.records)} records emitted")


# ── F3 CLOCK (interval discipline, no burst) ─────────────────────────────────────
def falsifier_3():
    print("F3 CLOCK: held-key records exactly 50 ms apart; stall -> one record")
    sink = M.MockSink()
    m = M.InputMapper(sink)
    m.press("W", 1000)
    recs, ts = dense_ticks(m, 1000, 1300)      # dense 1 ms ticks
    diffs = {b - a for a, b in zip(ts, ts[1:])}
    check("F3a held-key records are EXACTLY 50 ms apart under the injected clock",
          bool(ts) and diffs == {50}, f"{len(ts)} records at {ts[0]}..{ts[-1]}, "
          f"diffs {sorted(diffs)}")
    check("F3b the interval grid starts AT the press (first boundary emits)",
          ts[0] == 1000)

    # early ticks emit nothing (the interval is the boundary, not a target rate)
    n_before = len(sink.records)
    m.tick(1301); m.tick(1320); m.tick(1349)
    check("F3c ticks inside the interval emit nothing", len(sink.records) == n_before)

    # a stall: no replay burst -- exactly ONE current-state record
    m2 = M.MockSink()
    m3 = M.InputMapper(m2)
    m3.press("W", 1000)
    dense_ticks(m3, 1000, 1250)
    before = len(m2.records)
    m3.tick(1700)                              # the first tick after a 450 ms gap
    burst = len(m2.records) - before
    dense_ticks(m3, 1701, 1750)
    resumed = len(m2.records) - before - burst
    check("F3d a 450 ms stall yields exactly ONE record (current state), no burst",
          burst == 1 and resumed == 1, f"stall emitted {burst}, next interval {resumed}")
    ts2 = [r.issued_tick for r in m2.records[-2:]]
    check("F3e the grid re-anchors after the stall (50 ms cadence resumes)",
          ts2[-1] - ts2[-2] == M.PHYSICS_HZ * M.INTERVAL_MS // 1000,
          f"last issued ticks {ts2} (physics ticks; 15 = 50 ms at 300 Hz)")


# ── F4 RELEASE (decay to exactly zero, then stop) ────────────────────────────────
def falsifier_4():
    print("F4 RELEASE: monotone decay, exact 0.0 within 100 ms, then silence")
    sink = M.MockSink()
    m = M.InputMapper(sink)
    m.press("W", 1000)
    dense_ticks(m, 1000, 1070)
    m.release("W", 1070)
    recs, ts = dense_ticks(m, 1071, 1400)
    vs = [(r.v_forward, t) for r, t in zip(recs, ts)]
    tail = [(v, t) for v, t in vs if t >= 1070]
    check("F4a the tail is monotone non-increasing",
          all(a[0] >= b[0] for a, b in zip(tail, tail[1:])), f"tail {tail}")
    check("F4a' the whole record stream is monotone while decaying",
          all(a[0] >= b[0] for a, b in zip(vs, vs[1:])))
    zero = [(v, t) for v, t in tail if v == 0.0]
    check("F4b a record with EXACTLY 0.0 exists at or before release+100 ms",
          bool(zero) and zero[0][1] <= 1070 + M.RELEASE_DECAY_MS,
          f"zero at {zero[0] if zero else None}")
    later = [(v, t) for v, t in vs if t > zero[0][1]] if zero else [("?", "?")]
    check("F4c emission STOPS after the zero (the inert path resumed)",
          not later, f"{len(later)} records after the zero")
    check("F4d no record with v>0 later than release+100 ms",
          all(v <= 0.0 for v, t in vs if t > 1070 + M.RELEASE_DECAY_MS))


# ── F5 REMAP (values change; the contract does not) ──────────────────────────────
def falsifier_5():
    print("F5 REMAP: a binding swap changes emitted values, nothing else")
    sink_def, sink_rem = M.MockSink(), M.MockSink()
    md = M.InputMapper(sink_def)
    mr = M.InputMapper(sink_rem, bindings={"W": "backward"})   # the remap: W -> S
    md.press("W", 1000); md.tick(1000)
    mr.press("W", 1000); mr.tick(1000)
    rd, rr = sink_def.records[0], sink_rem.records[0]
    check("F5a the remap changed the emitted value (default W -> band ceiling)",
          rd.v_forward == V_MAX and rr.v_forward == 0.0,
          f"default {rd.v_forward}, remapped {rr.v_forward}")
    check("F5b same record type and version on both sides",
          isinstance(rr, CommandRecord) and rr.record_version == rd.record_version)
    check("F5c same bounds and clock after the remap",
          M.V_MAX_IN_BAND_M_S == V_MAX and M.INTERVAL_MS == 50
          and M.EXPIRY_TICKS == 30)
    adapter = V1FamilyAdapter()
    pd, pr = adapter.project(rd), adapter.project(rr)
    check("F5d the adapter projection is untouched by the remap "
          "(velocity passthrough, yaw routed nowhere)",
          pd["commanded_target_velocity_x"] == rd.v_forward
          and pr["commanded_target_velocity_x"] == rr.v_forward
          and pd["routed_yaw_rate"] is False and pr["routed_yaw_rate"] is False)


# ── F6 SEAM STATES (inert vs live-zero; refusals; steering; expiry) ─────────────
def falsifier_6():
    print("F6 SEAM STATES: idle emits nothing; S emits live zeros; refusals named")
    sink = M.MockSink()
    m = M.InputMapper(sink)
    idle = m.tick(500)
    check("F6a idle emits NOTHING (the machinery's inert path stays reachable)",
          idle == [] and len(sink.records) == 0)

    m.press("S", 1000)
    recs, _ = dense_ticks(m, 1000, 1150)
    check("F6b S held emits LIVE ZERO-advance records (a distinct seam state)",
          len(recs) == 4 and all(r.v_forward == 0.0 for r in recs),
          f"{len(recs)} records, values {[r.v_forward for r in recs]}")

    sink3 = M.MockSink()
    m3 = M.InputMapper(sink3)
    m3.press("A", 1000)                       # steering alone
    dense_ticks(m3, 1000, 1200)
    m3.mouse(400)                             # mouse alone, idle
    m3.tick(1300)
    m3.tick(1400)
    check("F6c steering alone emits nothing (yaw is carried, no route at v1)",
          len(sink3.records) == 0)
    check("F6d idle mouse counts are consumed into the trace, named, not resent",
          any("steer_without_speed" in k for k in
              [k for k in m3.last_trace]) or "steer_without_speed" in m3.last_trace,
          f"trace keys {sorted(m3.last_trace)}")

    sink4 = M.MockSink()
    m4 = M.InputMapper(sink4)
    m4.press("Shift", 1000)
    m4.press("Space", 1000)
    m4.tick(1000)
    refused = dict(m4.last_trace.get("refused", []))
    check("F6e sprint/jump refuse BY NAME (registered refusals, never silent)",
          "sprint" in refused and "jump" in refused
          and len(sink4.records) == 0,
          f"refused: {sorted(refused)}")

    sink5 = M.MockSink()
    m5 = M.InputMapper(sink5)
    m5.press("W", 1000); m5.press("A", 1000)
    r1 = m5.tick(1000)
    m5.mouse(10_000)                          # a violent flick: 400 rad/s raw
    r2 = m5.tick(1050)
    check("F6f yaw is clamped to the declared steer bound (keys) and mouse",
          r1[0].yaw_rate == OMEGA and r2[0].yaw_rate == OMEGA,
          f"{r1[0].yaw_rate}, {r2[0].yaw_rate}")
    r3 = m5.tick(1100)
    check("F6g a held key RE-ISSUES its record every interval (the R4 rule)",
          r3 and r3[0].v_forward == V_MAX and len(sink5.records) == 3)

    rec = sink5.records[0]
    check("F6h the expiry contract: valid at 95 ms, expired at 105 ms",
          not M.InputMapper.is_expired(rec, 1000 + 95)
          and M.InputMapper.is_expired(rec, 1000 + 105))

    sink6 = M.MockSink()
    m6 = M.InputMapper(sink6, tick_source=lambda: 777)
    m6.press("W", 1000)
    rec6 = m6.tick(1000)[0]
    check("F6i the tick source is injectable (the live harness pins issued_tick)",
          rec6.issued_tick == 777, f"issued_tick {rec6.issued_tick}")

    # speed-key conflict is resolved by the frozen precedence and NAMED
    sink7 = M.MockSink()
    m7 = M.InputMapper(sink7)
    m7.press("S", 1000); m7.press("W", 1000)
    r7 = m7.tick(1000)
    check("F6j W+S resolves to forward (precedence) and is named in the trace",
          r7[0].v_forward == V_MAX
          and any("forward" in c and "backward" in c
                  for c in m7.last_trace.get("conflicts", [])),
          f"conflicts {m7.last_trace.get('conflicts')}")


def main():
    print("input_mapper_tests -- U01 falsifiers "
          "(prereg: agents/U01_input/PREREGISTRATION.md)")
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
    print("VERDICT: GREEN -- all falsifier checks passed; the frozen numbers held.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
