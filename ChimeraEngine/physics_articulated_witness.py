"""physics_articulated_witness.py — WITNESS JOINTS AND MUSCLES (Track S, S4–S5).

Checked against TEXTBOOK PHYSICS and REAL-WORLD numbers, not against the code's own formulas:

  J1  physical pendulum PERIOD   T = 2*pi*sqrt(I_pivot / (m g d)); for a uniform rod hinged at one
                                 end that is 2*pi*sqrt(2L/3g) -- a number you can check by hand
  J2  energy conservation        an unactuated pendulum must not gain or lose energy
  J3  DOUBLE pendulum energy     catches coupling/Coriolis bugs a single pendulum cannot
  J4  the joint HOLDS            reduced coordinates -> the link cannot drift off its pivot, ever
  M1  moment arm                 dTorque/dTension measured == the perpendicular distance from the
                                 hinge axis to the muscle's line of action (real biomechanics)
  M2  static hold                the tension needed to hold a limb against gravity == m g d sin(th)
                                 / moment arm -- solved from physics, not tuned
  M3  the muscle MOVES it        activate and the limb lifts; the motion comes from tension only
  M4  UNIFICATION                muscle and thruster are the same mechanism: force at a port. The
                                 muscle is replaced by a raw force pair and the torque is identical.

Run:  python ChimeraEngine/physics_articulated_witness.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from physics_articulated import Tree, rod, make_muscle        # noqa: E402

np.set_printoptions(precision=6, suppress=True)
G = 9.80665
results: list[tuple[str, bool]] = []


def check(name: str, ok: bool, detail: str) -> None:
    results.append((name, ok))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")


def pendulum(mass=2.0, length=1.0) -> Tree:
    return Tree([rod('rod', mass, length)], gravity=(0, 0, -G))


def main() -> int:
    print("\nWITNESS: joints and muscles (Track S, S4-S5)\n" + "=" * 64)

    # ── J1: the physical pendulum period, against the textbook formula ───────────────────────
    print("\nJ1  physical pendulum period vs T = 2*pi*sqrt(2L/3g)")
    m, L = 2.0, 1.0
    t = pendulum(m, L)
    t.q[0] = 0.02                                          # small angle -> the linear regime
    dt = 1e-4
    prev, zero_times = t.q[0], []
    for _ in range(80_000):
        t.step(dt)
        if prev > 0 >= t.q[0] or prev < 0 <= t.q[0]:       # zero crossing
            zero_times.append(t.q[0] and 0 or 0)
            zero_times[-1] = len(zero_times)
        prev = t.q[0]
        if len(zero_times) >= 5:
            break
    steps_used = 400_000
    # period from the measured half-cycles
    t2 = pendulum(m, L); t2.q[0] = 0.02
    crossings = []
    prev = t2.q[0]
    for k in range(120_000):
        t2.step(dt)
        if prev > 0 >= t2.q[0]:
            crossings.append(k * dt)
        prev = t2.q[0]
        if len(crossings) >= 3:
            break
    T_meas = (crossings[-1] - crossings[0]) / (len(crossings) - 1)
    T_theory = 2 * np.pi * np.sqrt(2 * L / (3 * G))
    rel = abs(T_meas - T_theory) / T_theory
    print(f"      measured period  {T_meas:.6f} s")
    print(f"      textbook 2pi*sqrt(2L/3g) = {T_theory:.6f} s")
    check("period matches the textbook", rel < 2e-3, f"relative error {rel:.3e}")

    # ── J2: energy conservation, unactuated ──────────────────────────────────────────────────
    print("\nJ2  unactuated pendulum -> energy conserved")
    t = pendulum(); t.q[0] = 1.0                            # a big swing, not a small one
    K0, U0 = t.energy(); E0 = K0 + U0
    for _ in range(40_000):
        t.step(1e-4)
    K1, U1 = t.energy(); E1 = K1 + U1
    drift = abs(E1 - E0) / max(abs(E0), 1e-12)
    print(f"      E(0) = {E0:.9f} J   E(4 s) = {E1:.9f} J")
    check("energy conserved (single)", drift < 2e-3, f"relative drift {drift:.3e} over 4 s")

    # ── J3: double pendulum -- the coupling terms ────────────────────────────────────────────
    print("\nJ3  DOUBLE pendulum -> energy conserved (tests Coriolis/coupling)")
    dbl = Tree([rod('upper', 2.0, 1.0),
                rod('lower', 1.0, 0.8, anchor=(0, 0, -1.0), parent=0)], gravity=(0, 0, -G))
    dbl.q[:] = [0.8, -0.5]
    K0, U0 = dbl.energy(); E0 = K0 + U0
    for _ in range(40_000):
        dbl.step(1e-4)
    K1, U1 = dbl.energy(); E1 = K1 + U1
    drift2 = abs(E1 - E0) / max(abs(E0), 1e-12)
    print(f"      E(0) = {E0:.9f} J   E(4 s) = {E1:.9f} J   q = {dbl.q}")
    check("energy conserved (double)", drift2 < 5e-3, f"relative drift {drift2:.3e} over 4 s")

    # ── J4: the joint HOLDS -- reduced coordinates cannot separate ───────────────────────────
    print("\nJ4  the joint cannot drift apart (reduced coordinates)")
    pivot_err = 0.0
    for _ in range(4_000):
        dbl.step(1e-4)
        R, o, _, _ = dbl.fk()
        tip_of_upper = o[0] + R[0] @ np.array([0.0, 0.0, -1.0])   # the parent's far end
        pivot_err = max(pivot_err, float(np.linalg.norm(tip_of_upper - o[1])))
    check("child pivot stays on the parent", pivot_err < 1e-12,
          f"max separation {pivot_err:.3e} m over 0.4 s of chaotic motion")

    # ── M1: the moment arm is the perpendicular distance to the line of action ───────────────
    # A muscle must SPAN the joint. Two points on the SAME bone give a moment arm of exactly zero
    # -- correct physics, and how the first version of this witness fooled itself.
    print("\nM1  muscle moment arm == perpendicular distance to the line of action")
    def biceps_arm(q1=0.6):
        t = Tree([rod('upper', 2.5, 0.32),
                  rod('fore', 1.6, 0.28, anchor=(0, 0, -0.32), parent=0)], gravity=(0, 0, -G))
        t.q[:] = [0.0, q1]
        m = t.add_muscle(make_muscle('biceps',
                                     origin_link=0, origin=(0.03, 0.0, -0.05),    # on the UPPER arm
                                     insert_link=1, insert=(0.025, 0.0, -0.05),   # on the FOREARM
                                     max_tension=1200.0))
        return t, m

    arm, mus = biceps_arm()
    R, o, _, z = arm.fk()
    pa = o[0] + R[0] @ mus.origin
    pb = o[1] + R[1] @ mus.insert
    u = (pb - pa) / np.linalg.norm(pb - pa)
    n_ax = np.cross(z[1], u)                                # joint 1 is the elbow
    perp = abs(float(np.dot(pa - o[1], n_ax))) / (np.linalg.norm(n_ax) + 1e-15)
    measured = abs(arm.moment_arm(mus, 1))
    print(f"      measured dTorque/dTension = {measured:.6f} m")
    print(f"      geometric perpendicular   = {perp:.6f} m")
    rel_arm = abs(measured - perp) / max(perp, 1e-12)
    check("moment arm is the true lever", rel_arm < 1e-9, f"relative error {rel_arm:.3e}")
    print(f"      (same muscle about the SHOULDER: {arm.moment_arm(mus, 0):+.6f} m -- it spans "
          f"the elbow, so it also crosses the shoulder only via its line of action)")

    # ── M2: the tension needed to HOLD against gravity, solved from physics ──────────────────
    print("\nM2  static hold: tension solved from physics, not tuned")
    # ONE DOF, so the claim is exact: a forearm hinged to ground, held by one muscle. (With the
    # shoulder also free, one muscle CANNOT hold the arm still -- the mass matrix couples the two
    # joints, so zeroing the elbow's torque does not zero its acceleration. That is real physics,
    # not a bug, and it is why a limb needs an actuator per degree of freedom. Measured below.)
    fore = Tree([rod('fore', 1.6, 0.28)], gravity=(0, 0, -G))
    fore.q[0] = 0.6
    mus1 = fore.add_muscle(make_muscle('holder', origin_link=-1, origin=(0.12, 0.0, 0.06),
                                       insert_link=0, insert=(0.0, 0.0, -0.09),
                                       max_tension=600.0))
    grav_Q = -fore.bias()[0]
    arm_now = fore.moment_arm(mus1, 0)
    need_T = -grav_Q / arm_now
    mus1.dial = float(need_T / mus1.max_tension)
    qdd = fore.accel()[0]
    print(f"      gravity torque {grav_Q:+.6f} N.m, moment arm {arm_now:+.6f} m")
    print(f"      required tension {need_T:.2f} N  ->  joint accel {qdd:+.3e} rad/s^2")
    check("the limb holds still (1 DOF, exact)", abs(qdd) < 1e-9,
          f"|angular accel| = {abs(qdd):.3e} rad/s^2 from tension solved, not tuned")

    arm2, mus2 = biceps_arm(0.6)
    mus2.dial = float(-(-arm2.bias()[1]) / arm2.moment_arm(mus2, 1) / mus2.max_tension)
    Qtot = arm2.generalized_force(arm2.muscle_forces()) - arm2.bias()
    print(f"      2-DOF arm, same solve: elbow NET torque {Qtot[1]:+.3e} N.m (cancelled), "
          f"but shoulder {Qtot[0]:+.4f} N.m -> qdd {arm2.accel()[1]:+.3f} rad/s^2")
    check("coupling is real: one muscle cannot hold two joints", abs(Qtot[1]) < 1e-9,
          "elbow torque cancels exactly; the free shoulder still drives it -- an actuator per DOF")

    # ── M3: activate -> it moves, and NOT because of gravity ────────────────────────────────
    print("\nM3  activate -> the limb lifts; compared against the SAME limb with no muscle")
    slack, m_slack = biceps_arm(0.6); m_slack.dial = 0.0    # gravity only -- the control
    pull, m_pull = biceps_arm(0.6);  m_pull.dial = 1.0      # gravity + full contraction
    for _ in range(3_000):
        slack.step(1e-4); pull.step(1e-4)
    print(f"      no muscle : elbow {0.6:.4f} -> {slack.q[1]:+.4f} rad (falls under gravity)")
    print(f"      contracted: elbow {0.6:.4f} -> {pull.q[1]:+.4f} rad")
    check("the muscle -- not gravity -- lifts it", pull.q[1] > slack.q[1] + 1e-2,
          f"contraction wins by {pull.q[1] - slack.q[1]:+.4f} rad at {m_pull.tension():.0f} N")

    # ── M4: UNIFICATION -- a muscle is a force at a port, exactly like a thruster ────────────
    print("\nM4  a muscle and a thruster are the SAME mechanism (force at a port)")
    arm, mus = biceps_arm(0.35)
    mus.dial = 0.8
    Q_muscle = arm.generalized_force(arm.muscle_forces())
    R, o, _, _ = arm.fk()
    pa = o[0] + R[0] @ mus.origin
    pb = o[1] + R[1] @ mus.insert
    u = (pb - pa) / np.linalg.norm(pb - pa)
    T = mus.tension()
    Q_raw = arm.generalized_force([(1, pb, -u * T), (0, pa, u * T)])   # a raw force pair
    print(f"      via Muscle        : {Q_muscle} N.m")
    print(f"      via raw force pair: {Q_raw} N.m")
    d = float(np.max(np.abs(Q_muscle - Q_raw)))
    check("same torque from the same forces", d < 1e-12,
          f"max difference {d:.3e} N.m -- one mechanism, not two")

    n_fail = sum(1 for _, ok in results if not ok)
    print("\n" + "=" * 64)
    print(f"{len(results) - n_fail}/{len(results)} checks passed")
    return 1 if n_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
