"""floating_witness.py — WITNESS THE FLOATING BASE (Track S, S8).

Checked against conservation laws and textbook physics, not against the code's own formulas:

  F1  free fall            the whole creature's COM follows a clean ballistic parabola, whatever
                           the limbs are doing
  F2  linear momentum      obeys the gravitational impulse exactly
  F3  energy               conserved in flight
  F4  THE FALLING CAT      with angular momentum EXACTLY zero, muscle-driven internal motion still
                           reorients the torso. A PINNED base cannot do this at all, so it is the
                           proof the base is genuinely free.
  F5  it lands             dropped onto ground it comes to rest, weight carried by the floor
  F6  IT FALLS OVER        a hard push topples it, a light one does not -- impossible when pinned

The sweeps run ACROSS PROCESSES (parallel.py): every case is an independent rollout, and this box
has 32 cores. Episode workers are module-level so they can be pickled.

Run:  python ChimeraEngine/floating_witness.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from physics_articulated import rod                                        # noqa: E402
from physics_floating import FloatingTree                                  # noqa: E402
from physics import inertia_box                                            # noqa: E402
from contact import Ground, ContactModel, Foot, tree_contacts              # noqa: E402
from nervous import attach_antagonist                                      # noqa: E402
from parallel import pmap                                                  # noqa: E402

np.set_printoptions(precision=6, suppress=True)
G = 9.80665
DT = 1e-4
results: list[tuple[str, bool]] = []


def check(name: str, ok: bool, detail: str) -> None:
    results.append((name, ok))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")


def creature(z=1.0):
    """A torso that floats free, with two hinged limbs. The torso is the BASE body."""
    torso_m, ext = 12.0, np.array([0.30, 0.20, 0.50])
    links = [rod('armL', 2.0, 0.34, anchor=(0.0, 0.10, 0.20), axis=(0, 1, 0), parent=-1),
             rod('armR', 2.0, 0.34, anchor=(0.0, -0.10, 0.20), axis=(0, 1, 0), parent=-1)]
    return FloatingTree(base_mass=torso_m, base_inertia=inertia_box(torso_m, ext),
                        base_com=(0.0, 0.0, 0.0), links=links,
                        gravity=(0, 0, -G), base_pos=(0.0, 0.0, z))


def _pads():
    return [Foot(link=-1, at=(sx * 0.12, sy * 0.09, -0.25), radius=0.03, name=f'c{i}')
            for i, (sx, sy) in enumerate([(1, 1), (1, -1), (-1, 1), (-1, -1)])]


# ── module-level episode workers, so they can be pickled to other processes ───────────────────
def _case_topple(push_N: float):
    """Push a resting body near the top and report how far from upright it ends."""
    ground = Ground()
    model = ContactModel(k=3.0e5, zeta=5.0e3, mu=0.9, v_eps=2e-5)
    b = creature(z=0.281)
    b.q[:] = [0.0, 0.0]
    ft = _pads()
    tilt = []
    for k in range(int(1.6 / DT)):
        f, _ = tree_contacts(b, ft, ground, model)
        if 2_000 <= k < 4_000:
            f = f + [(-1, b.base_pos + b.base_rot @ np.array([0.0, 0.0, 0.22]),
                      np.array([push_N, 0.0, 0.0]))]
        b.step(DT, extra_forces=f)
        up = b.base_rot @ np.array([0.0, 0.0, 1.0])
        tilt.append(float(np.degrees(np.arccos(np.clip(up[2], -1, 1)))))
    return push_N, float(np.max(tilt)), float(tilt[-1])


def main() -> int:
    print("\nWITNESS: the floating base (Track S, S8)\n" + "=" * 66)

    # ── F1 / F2 / F3: flight ─────────────────────────────────────────────────────────────────
    print("\nF1  free fall: the COM follows a ballistic parabola while the limbs swing")
    c = creature(z=5.0)
    c.q[:] = [0.4, -0.4]
    c.qd[:] = [3.0, -3.0]                       # limbs actively flailing
    c.w_base = np.array([0.0, 0.6, 0.0])
    com0 = c.com_world().copy()
    P0, L0 = c.momentum()
    K0, U0 = c.energy(); E0 = K0 + U0
    T = 0.6
    for _ in range(int(T / DT)):
        c.step(DT)
    v_com0 = P0 / c.total_mass()                # the flailing gave the COM a real initial velocity
    expected = com0 + v_com0 * T + np.array([0.0, 0.0, -0.5 * G * T ** 2])
    err = float(np.linalg.norm(c.com_world() - expected))
    print(f"      COM {np.round(com0, 5)} -> {np.round(c.com_world(), 5)}")
    print(f"      ballistic prediction {np.round(expected, 5)}   error {err:.2e} m")
    check("the COM follows a clean parabola", err < 5e-4,
          f"error {err:.2e} m over {T} s of flight -- the limbs cannot move it")

    P1, L1 = c.momentum()
    impulse = c.total_mass() * np.array([0.0, 0.0, -G]) * T
    dP = float(np.linalg.norm((P1 - P0) - impulse))
    print(f"      momentum change {np.round(P1 - P0, 4)}  vs impulse {np.round(impulse, 4)} N.s")
    check("linear momentum obeys the impulse", dP < 5e-3, f"discrepancy {dP:.2e} N.s")

    K1, U1 = c.energy(); E1 = K1 + U1
    drift = abs(E1 - E0) / max(abs(E0), 1e-9)
    check("energy conserved in flight", drift < 5e-3,
          f"E {E0:.5f} -> {E1:.5f} J, relative drift {drift:.2e}")

    # ── F4: THE FALLING CAT ──────────────────────────────────────────────────────────────────
    print("\nF4  THE FALLING CAT: angular momentum zero, yet the torso reorients")
    # The limbs must be moved by INTERNAL forces -- MUSCLES. Prescribing qd directly (my first
    # version) overwrites what the solver just computed and injects momentum from nowhere, which
    # is exactly what the |L| check exists to catch.
    cat = creature(z=50.0)
    cat.gravity = np.zeros(3)                    # no gravity: isolate the angular-momentum claim
    pL = attach_antagonist(cat, 0, -1, 0, 0.06, 0.05, 90.0, 'sL')
    pR = attach_antagonist(cat, 1, -1, 1, 0.06, 0.05, 90.0, 'sR')
    cat.q[:] = [0.0, 0.0]
    cat.set_rest_lengths(0.5)
    _, L_start = cat.momentum()
    steps = int(1.5 / DT)
    Lmax = 0.0
    for k in range(steps):
        u = np.sin(2 * np.pi * k / steps)        # out, then back: one clean cycle
        pL.drive(u)
        pR.drive(-u)                             # the limbs oppose -> an internal twist
        cat.step(DT)
        if k % 500 == 0:
            _, Lk = cat.momentum()
            Lmax = max(Lmax, float(np.linalg.norm(Lk)))
    _, L_end = cat.momentum()
    ang = float(np.degrees(np.arccos(np.clip((np.trace(cat.base_rot) - 1) / 2, -1, 1))))
    print(f"      |L| start {np.linalg.norm(L_start):.3e}   peak during {Lmax:.3e}   "
          f"end {np.linalg.norm(L_end):.3e} kg.m^2/s")
    print(f"      joints ended at {np.round(cat.q, 4)} rad; the TORSO turned {ang:.3f} deg")
    check("angular momentum stays zero throughout", Lmax < 1e-6,
          f"peak |L| = {Lmax:.2e} -- muscles are INTERNAL, so they cannot create any")
    check("internal motion reorients the body (the cat)", ang > 0.02,
          f"torso rotated {ang:.3f} deg at L = 0 -- a PINNED base cannot do this at all")

    # ── F5: it lands ─────────────────────────────────────────────────────────────────────────
    print("\nF5  dropped onto ground: it lands and the floor carries it")
    ground = Ground()
    model = ContactModel(k=3.0e5, zeta=5.0e3, mu=0.9, v_eps=2e-5)
    d = creature(z=0.60)
    d.q[:] = [0.0, 0.0]
    feet = _pads()
    fn_last = 0.0
    for _ in range(int(2.0 / DT)):
        f, info = tree_contacts(d, feet, ground, model)
        d.step(DT, extra_forces=f)
        fn_last = sum(ci['Fn'] for ci in info)
    weight = d.total_mass() * G
    print(f"      base settled at z = {d.base_pos[2]:.5f} m   (pads at -0.25, r = 0.03)")
    print(f"      total normal force {fn_last:.2f} N   vs   total weight {weight:.2f} N")
    check("it comes to rest on the floor", abs(d.base_pos[2] - 0.28) < 5e-3,
          f"base z = {d.base_pos[2]:.4f} m, expected ~0.280 = 0.25 + contact radius")
    check("the floor carries the whole creature", abs(fn_last - weight) / weight < 0.03,
          f"{fn_last:.2f} N vs {weight:.2f} N ({100*abs(fn_last-weight)/weight:.1f}% off)")

    # ── F6: IT FALLS OVER (swept in PARALLEL) ────────────────────────────────────────────────
    print("\nF6  push it -- and it TOPPLES (a pinned base could not)")
    import time
    t0 = time.time()
    sweep = pmap(_case_topple, [40.0, 60.0, 120.0, 200.0, 400.0, 600.0])
    for pN, mx, en in sweep:
        print(f"      push {pN:5.0f} N -> max tilt {mx:6.2f} deg, final {en:6.2f} deg"
              f"{'   <-- toppled' if en > 30 else ''}")
    print(f"      ({len(sweep)} episodes across processes in {time.time()-t0:.1f} s)")
    light = min(en for pN, mx, en in sweep if pN <= 60.0)
    heavy = max(en for pN, mx, en in sweep if pN >= 400.0)
    check("a hard push topples it, a light one does not", heavy > 30.0 and light < 10.0,
          f"600 N leaves it {heavy:.1f} deg from upright; 40 N only {light:.1f} deg -- "
          "the body is genuinely free to fall")

    n_fail = sum(1 for _, ok in results if not ok)
    print("\n" + "=" * 66)
    print(f"{len(results) - n_fail}/{len(results)} checks passed")
    return 1 if n_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
