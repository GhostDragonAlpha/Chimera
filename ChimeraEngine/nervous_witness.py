"""nervous_witness.py — WITNESS THE NERVOUS SYSTEM (Track S, S6).

  N1  muscles only PULL         negative activation must never become a push
  N2  antagonists oppose        the pair's moment arms have OPPOSITE signs, measured not assumed
  N3  the loop closes           the reflex holds a target angle against gravity, from tension alone
  N4  ROBUSTNESS                scored from 8 RANDOMISED starts, keeping the WORST -- the lesson
                                this project already paid for (one rollout is a coin toss)
  N5  it is the muscles doing it  same body, brain switched off -> it falls; brain on -> it holds
  N6  co-contraction stiffens   SWEPT, not asserted: bracing reduces deflection up to an
                                optimum (~0.2) and DESTABILISES beyond it, because the
                                pair's bias torque outgrows what the reflex can absorb
  N7  a LEARNED brain fits      a weight-vector Policy drives the same body through the same seam

Run:  python ChimeraEngine/nervous_witness.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from physics_articulated import Tree, rod, make_muscle            # noqa: E402
from nervous import (Antagonist, attach_antagonist, Reflex, Policy,   # noqa: E402
                     NervousSystem, run, robust_score)

np.set_printoptions(precision=6, suppress=True)
G = 9.80665
results: list[tuple[str, bool]] = []


def check(name: str, ok: bool, detail: str) -> None:
    results.append((name, ok))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")


def limb():
    """A two-segment limb -- upper + fore -- with an antagonist pair across EACH joint.
    Muscles only pull, so two joints need four muscles. That is biology's arithmetic, not ours."""
    t = Tree([rod('upper', 2.5, 0.32),
              rod('fore', 1.6, 0.28, anchor=(0, 0, -0.32), parent=0)], gravity=(0, 0, -G))
    p0 = attach_antagonist(t, joint=0, parent_link=-1, child_link=0,
                           offset=0.09, along=0.07, max_tension=900.0, name='shoulder')
    p1 = attach_antagonist(t, joint=1, parent_link=0, child_link=1,
                           offset=0.07, along=0.06, max_tension=700.0, name='elbow')
    t.q[:] = [0.25, 0.55]          # the posture the body is BUILT for...
    t.set_rest_lengths(width=0.35)  # ...is where each muscle is strongest (Hill force-length)
    t.q[:] = 0.0
    return t, [p0, p1]


def main() -> int:
    print("\nWITNESS: the nervous system (Track S, S6)\n" + "=" * 64)

    # ── N1: muscles only pull ────────────────────────────────────────────────────────────────
    print("\nN1  a muscle can only PULL")
    m = make_muscle('m', -1, (0, 0, 0), 0, (0, 0, -0.1), max_tension=100.0)
    vals = []
    for d in (-1.0, -0.3, 0.0, 0.5, 1.0):
        m.dial = d
        vals.append((d, m.tension()))
    for d, T in vals:
        print(f"      dial {d:+.2f} -> {T:+7.1f} N")
    check("no negative tension", all(T >= 0 for _, T in vals),
          "a negative activation goes slack, it does not push")

    # ── N2: the antagonists genuinely oppose ─────────────────────────────────────────────────
    print("\nN2  the antagonist pair opposes (moment arms measured, not assumed)")
    t, pairs = limb()
    ok_all = True
    for k, p in enumerate(pairs):
        af = t.moment_arm(p.flexor, p.joint)
        ae = t.moment_arm(p.extensor, p.joint)
        print(f"      joint {k}: flexor arm {af:+.5f} m,  extensor arm {ae:+.5f} m")
        ok_all &= (af > 0 > ae)
    check("flexor and extensor pull opposite ways", ok_all, "signs are opposite on every joint")

    # ── N3: the loop closes -- hold a pose against gravity ───────────────────────────────────
    print("\nN3  the reflex holds a target pose against gravity")
    goal = np.array([0.25, 0.55])
    t, pairs = limb()
    t.q[:] = [0.0, 0.0]
    brain = Reflex(n=2, kp=4.0, kd=0.5)
    r = run(t, brain, pairs, goal, seconds=2.5)
    print(f"      goal {goal}  ->  reached {t.q}")
    print(f"      settle error {r['settle_err']:.4f} rad (jitter {r['settle_jitter']:.4f}), "
          f"peak {r['peak_err']:.4f}")
    check("holds the pose", (not r['diverged']) and r['settle_err'] < 0.12,
          f"steady-state error {r['settle_err']:.4f} rad from muscle tension alone")

    # ── N4: ROBUSTNESS -- N randomised starts, keep the WORST ────────────────────────────────
    print("\nN4  scored from 8 RANDOMISED starts, keeping the WORST")
    rs = robust_score(limb, brain, goal, n_starts=8, seconds=2.5, spread=0.35)
    print(f"      per-start settle error: {np.round(rs['scores'], 4)}")
    print(f"      worst {rs['worst_err']:.4f}   mean {rs['mean_err']:.4f}   "
          f"robustness {rs['robustness']:.3f}   diverged {rs['n_diverged']}/8")
    check("worst case is still controlled",
          rs['n_diverged'] == 0 and rs['worst_err'] < 0.2 and rs['robustness'] > 0.5,
          f"robustness {rs['robustness']:.3f} (1.0 = every start alike; ~0 = one lucky roll)")

    # ── N5: it is the MUSCLES doing it, not gravity finding a resting pose ───────────────────
    print("\nN5  brain OFF vs brain ON, same body, same start")
    class Dead(NervousSystem):
        def act(self, obs):
            return np.zeros(2)
    t_off, p_off = limb(); t_off.q[:] = [0.0, 0.0]
    r_off = run(t_off, Dead(), p_off, goal, seconds=2.5)
    t_on, p_on = limb();  t_on.q[:] = [0.0, 0.0]
    r_on = run(t_on, Reflex(n=2, kp=4.0, kd=0.5), p_on, goal, seconds=2.5)
    print(f"      brain OFF: q = {t_off.q}  (settle err {r_off['settle_err']:.4f})")
    print(f"      brain ON : q = {t_on.q}   (settle err {r_on['settle_err']:.4f})")
    check("the nervous system is what holds it",
          r_on['settle_err'] < r_off['settle_err'] * 0.5,
          f"{r_off['settle_err']:.4f} -> {r_on['settle_err']:.4f} rad")

    # ── N6: co-contraction stiffens without moving the goal ──────────────────────────────────
    print("\nN6  co-contraction braces the joint (both muscles at once)")
    def kick(co, force=60.0, seconds=0.8):
        """Shove the tip while the reflex KEEPS RUNNING. Bracing means holding the brace under
        load -- freezing the activations instead makes it open-loop, and an open-loop limb with
        both muscles at 90% runs away as soon as the moment arms stop being equal."""
        tt, pp = limb(); tt.q[:] = goal.copy()
        b = Reflex(n=2, kp=4.0, kd=0.5)
        push = lambda: [(1, tt.point_world(1, (0, 0, -0.28)), np.array([force, 0.0, 0.0]))]
        r = run(tt, b, pp, goal, seconds=seconds, co_contract=co, extra_forces=push)
        return r['peak_err'], r['diverged']

    # SWEEP instead of assert: let the data say what co-contraction does.
    sweep = [(co,) + kick(co) for co in (0.0, 0.05, 0.10, 0.20, 0.40, 0.85)]
    print(f"      60 N shove at the tip, reflex running throughout:")
    for co, peak, dv in sweep:
        note = "  <-- destabilised" if peak > 1.0 else ""
        print(f"        co-contraction {co:4.2f}  ->  peak deflection {peak:8.4f} rad{note}")
    base = sweep[0][1]
    best_co, best_peak, _ = min(sweep, key=lambda s: s[1])
    print(f"      best at co = {best_co:.2f}: {base:.4f} -> {best_peak:.4f} rad "
          f"({100*(1-best_peak/base):.0f}% less give); beyond it the pair's own bias torque "
          f"grows faster than the reflex can absorb -- which is why real bodies brace, but lightly.")
    check("bracing stiffens the joint, up to an optimum",
          best_peak < base * 0.8 and best_co > 0.0,
          f"optimum co={best_co:.2f} gives {100*(1-best_peak/base):.0f}% less deflection; "
          f"over-bracing (0.85) destabilises at {sweep[-1][1]:.1f} rad")

    # ── N7: a LEARNED brain plugs into the same seam ─────────────────────────────────────────
    print("\nN7  a weight-vector Policy drives the same body through the same interface")
    pol = Policy(n_obs=6, n_act=2, hidden=16)
    t2, p2 = limb(); t2.q[:] = [0.0, 0.0]
    u = pol.drive(t2, p2, goal)
    r2 = run(t2, pol, p2, goal, seconds=0.5)
    print(f"      genome length {pol.genome().size} weights; first action {np.round(u, 3)}")
    print(f"      untrained policy settle error {r2['settle_err']:.4f} rad "
          f"(nonsense, as an untrained brain should be)")
    check("the learned seam works", pol.genome().size > 0 and not r2['diverged'],
          "same body, same muscles, weights instead of a rule -- ready for brain_gpu to fill in")

    n_fail = sum(1 for _, ok in results if not ok)
    print("\n" + "=" * 64)
    print(f"{len(results) - n_fail}/{len(results)} checks passed")
    return 1 if n_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
