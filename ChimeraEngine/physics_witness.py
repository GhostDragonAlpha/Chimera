"""physics_witness.py — WITNESS BALANCE (ROADMAP Track S, step S3).

The project's rule: a claim needs a MEASUREMENT, and the measurement has to be able to fail.
So this does not render a ship and look at it. It fires actuators and checks the numbers against
the analytic answer:

  W1  thrust through the centre of mass          -> pure translation, ZERO spin
  W2  thrust off-axis                            -> angular accel == I^-1 (r x F), MEASURED from
                                                    the integrator, not from the same formula
  W3  linear accel is independent of WHERE       -> a = F/m on-axis and off-axis alike (the
                                                    classic thruster bug is for off-axis to push
                                                    the body less; Newton says it does not)
  W4  BALANCE: centre of thrust vs centre of mass -> moving the COM to the thrust line kills the
                                                    spin. This is the `BALANCE` verb by name.
  W5  nothing firing                             -> linear and angular momentum conserved
  W6  the VERB drives it                         -> the dial, not a hand-set number, sets the force

Run:  python ChimeraEngine/physics_witness.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from physics import (Body, World, thruster, inertia_box, inertia_sphere,   # noqa: E402
                     quat_to_mat, Membrane)

np.set_printoptions(precision=6, suppress=True)
PASS, FAIL = "PASS", "FAIL"
results: list[tuple[str, str, str]] = []


def check(name: str, ok: bool, detail: str) -> None:
    results.append((name, PASS if ok else FAIL, detail))
    print(f"  [{PASS if ok else FAIL}] {name}: {detail}")


def make_ship(com_local=(0.0, 0.0, 0.0)) -> Body:
    """A 2x1x1 m hull, 1200 kg. The membrane is the real primitive; the body gives it mass."""
    m = Membrane(name='aShip', scale=2.0, serial='ship-0')
    extents = np.array([2.0, 1.0, 1.0])
    mass = 1200.0
    return Body(membrane=m, mass=mass, inertia=inertia_box(mass, extents),
                com_local=np.asarray(com_local, float))


def measure_wdot(body: Body, dt: float = 1e-6) -> np.ndarray:
    """Angular acceleration as the INTEGRATOR actually produces it: (w1 - w0)/dt.
    Deliberately NOT reusing angular_accel(), or the test would only check itself."""
    w0 = body.w.copy()
    body.step(dt)
    return (body.w - w0) / dt


def main() -> int:
    print("\nWITNESS: the actuated membrane (Track S, S1-S3)\n" + "=" * 62)

    # ── W1: thrust straight through the centre of mass -> no spin ────────────────────────────
    print("\nW1  thrust through the COM -> pure translation")
    b = make_ship()
    t = b.add(thruster('main', at=(-1.0, 0.0, 0.0), facing=(1.0, 0.0, 0.0), max_force=9000.0))
    t.dial = 1.0
    wdot = measure_wdot(b)
    check("no spin from an on-axis push", float(np.linalg.norm(wdot)) < 1e-9,
          f"|angular accel| = {np.linalg.norm(wdot):.3e} rad/s^2")

    b2 = make_ship()
    b2.add(thruster('main', at=(-1.0, 0, 0), facing=(1, 0, 0), max_force=9000.0)).dial = 1.0
    a = b2.linear_accel_world()
    expect = 9000.0 / 1200.0
    check("linear accel = F/m", abs(a[0] - expect) < 1e-9,
          f"measured {a[0]:.6f} m/s^2, analytic {expect:.6f}")

    # ── W2: off-axis thrust -> tau = r x F, and I^-1 tau out of the integrator ───────────────
    print("\nW2  off-axis thrust -> angular accel == I^-1 (r x F)")
    b = make_ship()
    at = np.array([-1.0, 0.0, 0.4])                  # 0.4 m off the thrust axis
    facing = np.array([1.0, 0.0, 0.0])
    F = 9000.0
    b.add(thruster('main', at=at, facing=facing, max_force=F)).dial = 1.0
    r = at - b.com_local
    tau_analytic = np.cross(r, facing * F)
    wdot_analytic = np.linalg.inv(b.inertia) @ tau_analytic
    wdot_measured = measure_wdot(b)
    err = float(np.linalg.norm(wdot_measured - wdot_analytic))
    rel = err / max(float(np.linalg.norm(wdot_analytic)), 1e-12)
    print(f"      tau = r x F           = {tau_analytic} N.m")
    print(f"      analytic I^-1 tau     = {wdot_analytic} rad/s^2")
    print(f"      MEASURED (integrator) = {wdot_measured} rad/s^2")
    check("angular accel matches r x F", rel < 1e-6, f"relative error {rel:.3e}")

    # ── W3: the application point must NOT change the linear acceleration ────────────────────
    print("\nW3  linear accel is independent of WHERE the force is applied")
    on = make_ship();  on.add(thruster('m', (-1, 0, 0.0), (1, 0, 0), F)).dial = 1.0
    off = make_ship(); off.add(thruster('m', (-1, 0, 0.4), (1, 0, 0), F)).dial = 1.0
    a_on, a_off = on.linear_accel_world(), off.linear_accel_world()
    d = float(np.linalg.norm(a_on - a_off))
    check("off-axis pushes just as hard", d < 1e-12,
          f"on-axis {a_on[0]:.6f} vs off-axis {a_off[0]:.6f} m/s^2, diff {d:.3e}")

    # ── W4: BALANCE -- centre of thrust vs centre of gravity ─────────────────────────────────
    print("\nW4  BALANCE: move the COM onto the thrust line -> the spin goes away")
    spin_by_offset = []
    for off_z in (0.0, 0.1, 0.2, 0.4):
        bb = make_ship(com_local=(0.0, 0.0, off_z))
        bb.add(thruster('m', at=(-1.0, 0.0, 0.4), facing=(1, 0, 0), max_force=F)).dial = 1.0
        spin_by_offset.append((off_z, float(np.linalg.norm(measure_wdot(bb)))))
    for oz, s in spin_by_offset:
        print(f"      COM z = {oz:.2f} m  ->  |angular accel| = {s:.6f} rad/s^2")
    aligned = spin_by_offset[-1][1]
    worst = spin_by_offset[0][1]
    check("spin vanishes when COT and COG align", aligned < 1e-9 and worst > 1e-3,
          f"aligned {aligned:.3e}, misaligned {worst:.6f} rad/s^2")

    # ── W5: nothing firing -> momentum conserved ─────────────────────────────────────────────
    print("\nW5  coasting -> momentum conserved")
    w = World()
    b = make_ship()
    b.add(thruster('m', (-1, 0, 0.4), (1, 0, 0), F)).dial = 1.0
    w.add(b)
    for _ in range(200):                              # spin it up
        w.step(1e-3)
    b.actuators[0].dial = 0.0                         # cut the engine
    P0, L0 = w.momentum()
    for _ in range(2000):
        w.step(1e-3)
    P1, L1 = w.momentum()
    dP = float(np.linalg.norm(P1 - P0)) / max(float(np.linalg.norm(P0)), 1e-12)
    dL = float(np.linalg.norm(L1 - L0)) / max(float(np.linalg.norm(L0)), 1e-12)
    print(f"      spun up to w = {b.w} rad/s (body frame)")
    check("linear momentum conserved", dP < 1e-9, f"relative drift {dP:.3e} over 2 s")
    check("angular momentum conserved", dL < 1e-3, f"relative drift {dL:.3e} over 2 s")

    # ── W6: the VERB drives it (the same machinery a muscle will use) ────────────────────────
    print("\nW6  the dial -- not a hand-set number -- sets the force")
    b = make_ship()
    th = b.add(thruster('m', (-1, 0, 0), (1, 0, 0), max_force=9000.0))
    reads = []
    for dial in (0.0, 0.25, 0.5, 1.0):
        th.dial = dial
        reads.append((dial, float(np.linalg.norm(b.linear_accel_world()) * b.mass)))
    for d_, f_ in reads:
        print(f"      dial {d_:.2f} -> {f_:8.1f} N")
    # RELATIVE tolerance, not absolute: Port.__post_init__ normalizes with f/(norm + 1e-12), so a
    # unit facing comes back 1e-12 short. Physically irrelevant, but it means the force is exact to
    # float64 round-off rather than bit-exact -- and a witness should say which it is checking.
    worst_rel = max(abs(f_ - d_ * 9000.0) / max(d_ * 9000.0, 1.0) for d_, f_ in reads)
    check("force follows the verb's dial", worst_rel < 1e-9,
          f"force == dial x max to {worst_rel:.2e} relative (limit: the port's 1e-12 normalize epsilon)")
    print(f"      verb states: {th.verb.lo.name!r} -> {th.verb.hi.name!r}; "
          f"port {th.port.name!r} kind {th.port.kind!r} at {th.port.at} facing {th.port.facing}")
    print(f"      membrane path: {b.membrane.path()}   ports on membrane: {list(b.membrane.ports)}")

    # ── verdict ──────────────────────────────────────────────────────────────────────────────
    n_fail = sum(1 for _, s, _ in results if s == FAIL)
    print("\n" + "=" * 62)
    print(f"{len(results) - n_fail}/{len(results)} checks passed")
    return 1 if n_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
