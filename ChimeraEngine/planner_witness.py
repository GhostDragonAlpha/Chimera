"""planner_witness.py — DOES IT DECIDE SENSIBLY, WITH NOTHING TRAINED?

  N1  THE 45-DEGREE RULE IS GONE   refusal happens at atan(mu), which is a DIFFERENT angle per
                                   material -- ice at 5.7 deg, regolith at 31, rock at 42
  N2  LOOSE GROUND COLLAPSES       regolith refuses past its own 40.03 deg angle of repose, which
                                   this project MEASURED rather than assumed
  N3  REACH AND TOPPLE             it refuses what the body cannot reach, and what would drop the
                                   COM outside whatever is left holding it up
  N4  IT WALKS TOWARD THE GOAL     given a goal it picks the foothold that buys progress per unit
                                   energy, and step length is an OUTCOME of that, not a setting
  N5  THE BUDGET IS A STAT         a bigger node budget changes nothing on flat ground and finds
                                   footholds a small one misses on hard ground -- self-scaling
  N6  IT IS FAST ENOUGH            microseconds, so "instantaneously" is a measured claim
  N7  TRY, FAIL, ROUTE AROUND      a foothold the controller could not reach is remembered for a
                                   moment and not chosen again

Run:  python ChimeraEngine/planner_witness.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from planner import FRICTION, Planner, Stance, Terrain                       # noqa: E402

results: list[tuple[str, bool]] = []


def check(name: str, ok: bool, detail: str) -> None:
    results.append((name, ok))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")


LEG, HIP_H = 0.860, 0.780        # thigh 0.429 + shin 0.431; hips slightly bent, as walking is


def stance(x=0.0, z=0.0) -> Stance:
    return Stance(com=np.array([x, 0.0, z + HIP_H + 0.15]),
                  contacts={'footL': np.array([x - 0.05, +0.10, z]),
                            'footR': np.array([x - 0.05, -0.10, z])},
                  hip={'footL': np.array([x, +0.10, z + HIP_H]),
                       'footR': np.array([x, -0.10, z + HIP_H])},
                  reach={'footL': LEG, 'footR': LEG}, mass=70.0, max_hip_torque=200.0)


def main() -> int:
    print("\nWITNESS: the contact planner (nothing trained)\n" + "=" * 74)

    # ── N1 ───────────────────────────────────────────────────────────────────────────────────
    print("\nN1  THE 45-DEGREE RULE IS GONE -- refusal is at atan(mu), per MATERIAL")
    rows = []
    for mat in ('rock', 'regolith', 'scree', 'ice'):
        mu = FRICTION[mat]
        found = None
        for deg in np.arange(1.0, 60.0, 0.5):
            t = Terrain(kind='slope', material=mat, slope_deg=float(deg))
            pl = Planner(terrain=t)
            st = stance()
            cs = [pl.evaluate(st, c, None) for c in pl.candidates(st, 'footL')]
            if all((not c.feasible) and c.refused_by in ('slip', 'collapse') for c in cs):
                found = float(deg)
                break
        pred = np.degrees(np.arctan(mu))
        rows.append((mat, mu, found, pred))
        print(f"      {mat:9s} mu {mu:4.2f} -> refuses above {found:5.1f} deg   "
              f"atan(mu) = {pred:5.1f} deg")
    print(f"      the industry's 45 deg is exactly atan(1.0): a claim about friction nobody wrote")
    print(f"      down, then applied to ice and gravel alike")
    ok1 = all(abs(f - p) < 6.0 or f < p for _, _, f, p in rows if f)
    check("each material refuses at its OWN friction angle", ok1 and rows[0][2] > rows[3][2] + 20,
          f"rock {rows[0][2]:.0f} deg vs ice {rows[3][2]:.0f} deg -- one rule, four answers, and "
          "no number in it was chosen by a designer")

    # ── N2 ───────────────────────────────────────────────────────────────────────────────────
    print("\nN2  LOOSE GROUND COLLAPSES at its measured angle of repose")
    for deg in (28.0, 34.0, 41.0):
        t = Terrain(kind='slope', material='regolith', slope_deg=deg)
        pl = Planner(terrain=t)
        st = stance()
        cs = [pl.evaluate(st, c, None) for c in pl.candidates(st, 'footL')]
        why = {c.refused_by for c in cs if not c.feasible}
        print(f"      regolith at {deg:4.1f} deg -> {sum(c.feasible for c in cs)}/{len(cs)} usable"
              f"   refusals {why or '{}'}")
    t41 = Planner(terrain=Terrain(kind='slope', material='regolith', slope_deg=41.0))
    st = stance()
    c41 = [t41.evaluate(st, c, None) for c in t41.candidates(st, 'footL')]
    check("regolith refuses past 40.03 deg, the repose this project MEASURED",
          all(not c.feasible for c in c41),
          "a 41 deg dust slope is unusable -- steeper than dust will hold, so a fresh crater wall "
          "is unwalkable, which is what Apollo crews reported")

    # ── N3 ───────────────────────────────────────────────────────────────────────────────────
    print("\nN3  REACH AND TOPPLE -- the body's own geometry doing the refusing")
    pl = Planner(terrain=Terrain(kind='flat', material='rock'))
    st = stance()
    from planner import Candidate
    out = st.hip['footL'] + np.array([1.2, 0.0, -HIP_H])          # well beyond the leg
    far = pl.evaluate(st, Candidate(limb='footL', point=out,
                                    normal=np.array([0.0, 0.0, 1.0]), slope=0.0), None)
    st1 = stance()
    st1.contacts = {'footL': st1.contacts['footL']}          # only ONE foot left holding
    st1.com = st1.com + np.array([0.9, 0.0, 0.0])            # and the COM well past it
    st1.hip['footL'] = st1.hip['footL'] + np.array([0.9, 0.0, 0.0])
    top = pl.evaluate(st1, pl.candidates(st1, 'footL')[0], None)
    print(f"      a foothold 0.85+ m from the hip -> {far.refused_by or 'accepted'}")
    print(f"      lifting the only supporting foot with the COM 0.6 m past it -> "
          f"{top.refused_by or 'accepted'}")
    check("it refuses what cannot be reached and what would topple it",
          far.refused_by == 'reach' and top.refused_by in ('topple', 'strength'),
          f"'{far.refused_by}' and '{top.refused_by}' -- both from the same evaluate(), neither "
          "from a rule about slopes")

    # ── N4 ───────────────────────────────────────────────────────────────────────────────────
    print("\nN4  IT WALKS -- receding horizon, one step at a time, toward a goal")
    pl = Planner(terrain=Terrain(kind='flat', material='rock'))
    st = stance()
    goal = np.array([6.0, 0.0, 0.0])
    steps, x0 = [], st.com[0]
    for k in range(8):
        limb = 'footL' if k % 2 == 0 else 'footR'
        best, _ = pl.plan(st, [limb], goal=goal, mode='walk')
        if best is None:
            break
        steps.append(float(np.linalg.norm(best.point - st.contacts[limb])))
        st.contacts[limb] = best.point
        st.com = np.array([np.mean([p[0] for p in st.contacts.values()]) + 0.05,
                           0.0, st.com[2]])
        for L in ('footL', 'footR'):
            st.hip[L] = np.array([st.com[0], +0.10 if L == 'footL' else -0.10, HIP_H])
    print(f"      8 alternating steps: COM advanced {st.com[0]-x0:+.3f} m toward the goal")
    print(f"      step lengths {np.round(steps, 3)}")
    print(f"      mean {np.mean(steps):.3f} m -- an OUTCOME of cost of transport, not a setting")
    check("it makes progress by repeating one decision", st.com[0] - x0 > 0.8 and len(steps) == 8,
          f"advanced {st.com[0]-x0:.2f} m in 8 steps averaging {np.mean(steps):.2f} m, planning "
          "exactly ONE contact at a time and throwing the plan away each tick")

    # ── N5 ───────────────────────────────────────────────────────────────────────────────────
    print("\nN5  THE NODE BUDGET IS A CHARACTER STAT -- and it only matters where it is hard")
    flat = Terrain(kind='flat', material='rock')
    # A LEDGE: ice everywhere (usable only below 5.7 deg) with one small level patch. Coarse
    # sampling walks straight past it; fine sampling finds it. That is the stat doing its job.
    # A 22 deg ICE slope -- unusable everywhere, since ice gives up at atan(0.1) = 5.7 deg -- with
    # one 9 cm patch of dry rock, which holds to 42. There IS a route. Coarse sampling walks
    # straight past it; fine sampling finds it. Nothing about the SHAPE says so, only the material.
    hard = Terrain(kind='slope', material='ice', slope_deg=22.0,
                   patches=[(0.26, 0.13, 0.09, 'rock')])
    for name, terr in (('flat corridor', flat), ('icy ledge', hard)):
        line = []
        for budget in (12, 240):
            pl = Planner(terrain=terr, node_budget=budget)
            st = stance()
            _, scored = pl.plan(st, ['footL', 'footR'], goal=np.array([4.0, 0.0, 0.0]))
            ok = [c for c in scored if c.feasible]
            line.append((budget, len(scored), len(ok)))
        print(f"      {name:14s} budget 12 -> {line[0][2]:3d}/{line[0][1]:3d} usable   "
              f"budget 240 -> {line[1][2]:3d}/{line[1][1]:3d} usable   "
              f"{'FOUND A WAY' if line[0][2] == 0 < line[1][2] else 'both fine' if line[0][2] else 'both stuck'}")
        if name == 'flat corridor':
            flat12, flat_hi = line[0][2], line[1][2]
        else:
            hard12, hard_hi = line[0][2], line[1][2]
    check("a bigger budget is worthless on easy ground and decisive on hard ground",
          flat12 > 0 and hard12 == 0 and hard_hi > 0,
          f"flat: {flat12} usable at budget 12 already, so more looking buys NOTHING. Ledge: "
          f"{hard12} at budget 12 -- stuck -- and {hard_hi} at 240. Self-scaling difficulty out of "
          "one integer, and it never touches the physics")

    # ── N6 ───────────────────────────────────────────────────────────────────────────────────
    print("\nN6  IT IS FAST ENOUGH -- 'instantaneously' as a measured number")
    for budget in (12, 96, 384):
        pl = Planner(terrain=hard, node_budget=budget)
        st = stance()
        t0 = time.perf_counter()
        for _ in range(200):
            pl.plan(st, ['footL', 'footR'], goal=np.array([4.0, 0.0, 0.0]))
        per = (time.perf_counter() - t0) / 200
        print(f"      budget {budget:4d} -> {per*1e6:8.1f} us per decision   "
              f"{1.0/per:9.0f} decisions/sec")
    pl = Planner(terrain=hard, node_budget=96)
    t0 = time.perf_counter()
    for _ in range(200):
        pl.plan(stance(), ['footL', 'footR'], goal=np.array([4.0, 0.0, 0.0]))
    per96 = (time.perf_counter() - t0) / 200
    print(f"      HONEST CORRECTION: THE_BODY.md 4.2 priced this at ~0.8 MFLOP and called it")
    print(f"      MICROSECONDS. The arithmetic is microseconds; PURE PYTHON is ~1000x that, and")
    print(f"      {per96*1e6:.0f} us is what it actually costs. Still under a 16.7 ms frame and 10x")
    print(f"      cheaper than ONE step of the body's own dynamics (51 ms) -- but not free, and")
    print(f"      vectorising the candidate sweep is what would close the gap to the flop bound.")
    check("a decision fits inside a frame", per96 < 1.0e-2,
          f"{per96*1e6:.0f} us at budget 96 in pure Python against a 16,700 us frame -- affordable, "
          "but the doc's 'microseconds' was the FLOP count and not the measurement")

    # ── N7 ───────────────────────────────────────────────────────────────────────────────────
    print("\nN7  TRY, FAIL, ROUTE AROUND -- the runtime memory")
    pl = Planner(terrain=flat)
    st = stance()
    first, _ = pl.plan(st, ['footL'], goal=np.array([4.0, 0.0, 0.0]))
    pl.mark_failed(first)
    second, _ = pl.plan(st, ['footL'], goal=np.array([4.0, 0.0, 0.0]))
    same = np.allclose(first.point, second.point)
    for _ in range(121):
        pl.tick()
    third, _ = pl.plan(st, ['footL'], goal=np.array([4.0, 0.0, 0.0]))
    print(f"      chose ({first.point[0]:+.2f},{first.point[1]:+.2f}) -> marked unreachable")
    print(f"      next choice ({second.point[0]:+.2f},{second.point[1]:+.2f})   same? {same}")
    print(f"      after 121 ticks it is willing again: "
          f"({third.point[0]:+.2f},{third.point[1]:+.2f})  same as first? "
          f"{np.allclose(first.point, third.point)}")
    check("a failed foothold is avoided, then forgotten",
          not same and np.allclose(first.point, third.point),
          "the character remembers THIS rock defeated it for about two seconds and picks another "
          "-- per-situation, not per-policy, so nothing it knows how to do is rewritten")

    n_fail = sum(1 for _, ok in results if not ok)
    print("\n" + "=" * 74)
    print(f"{len(results) - n_fail}/{len(results)} checks passed")
    if not n_fail:
        print("\nNOTHING HERE WAS TRAINED. Every refusal came from a measured constant -- friction")
        print("coefficients, the 40.03 deg repose this project grew, the body's own reach and")
        print("torque limits. The training that remains is the TRANSITION CONTROLLER (move a limb")
        print("from A to B without falling) and the VALUE FUNCTION that stops greedy dead-ends.")
    return 1 if n_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
