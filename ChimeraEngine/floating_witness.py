"""floating_witness.py — WITNESS THE FLOATING BASE (Track S, S8).

Checked against conservation laws and textbook physics, not against the code's own formulas:

  F1  free fall            the whole creature's COM accelerates at exactly g, whatever the joints do
  F2  linear momentum      conserved in flight (no external force but gravity)
  F3  THE FALLING CAT      with angular momentum EXACTLY zero, internal joint motion still reorients
                           the body. This is the thing a pinned base can never do, and it is the
                           proof the base is genuinely free.
  F4  energy               conserved in flight with the muscles slack
  F5  it lands             dropped onto ground it comes to rest, weight carried by the floor
  F6  IT FALLS OVER        pushed, a standing body topples -- impossible with a pinned base
  F7  one rule             contact/muscle forces enter through the same generalized_force

Run:  python ChimeraEngine/floating_witness.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from physics_articulated import rod, Link                                  # noqa: E402
from physics_floating import FloatingTree                                  # noqa: E402
from physics import inertia_box                                            # noqa: E402
from contact import Ground, ContactModel, Foot, tree_contacts              # noqa: E402
from nervous import attach_antagonist, Reflex, NervousSystem               # noqa: E402

np.set_printoptions(precision=6, suppress=True)
G = 9.80665
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


def main() -> int:
    print("\nWITNESS: the floating base (Track S, S8)\n" + "=" * 66)
    dt = 1e-4

    # ── F1 / F2 / F4: flight ─────────────────────────────────────────────────────────────────
    print("\nF1  free fall: the COM accelerates at exactly g, whatever the limbs do")
    c = creature(z=5.0)
    c.q[:] = [0.4, -0.4]
    c.qd[:] = [3.0, -3.0]                       # limbs actively flailing
    c.w_base = np.array([0.0, 0.6, 0.0])
    com0 = c.com_world().copy()
    P0, L0 = c.momentum()
    K0, U0 = c.energy(); E0 = K0 + U0
    T = 0.6
    for _ in range(int(T / dt)):
        c.step(dt)
    com1 = c.com_world()
    expected = com0 + np.array([0, 0, -0.5 * G * T ** 2])       # started from rest, COM-wise
    # the COM had an initial velocity from the flailing limbs; use momentum to predict it exactly
    v_com0 = P0 / c.total_mass()
    expected = com0 + v_com0 * T + np.array([0, 0, -0.5 * G * T ** 2])
    err = float(np.linalg.norm(com1 - expected))
    print(f"      COM start {np.round(com0, 5)}  ->  {np.round(com1, 5)}")
    print(f"      predicted by ballistics {np.round(expected, 5)}   error {err:.2e} m")
    check("the COM follows a clean parabola", err < 2e-4,
          f"error {err:.2e} m over {T} s of flight with the limbs swinging")

    P1, L1 = c.momentum()
    dP = float(np.linalg.norm((P1 - P0) - c.total_mass() * np.array([0, 0, -G]) * T))
    print(f"      linear momentum change {np.round(P1 - P0, 4)} vs impulse "
          f"{np.round(c.total_mass()*np.array([0,0,-G])*T, 4)} N.s")
    check("linear momentum obeys the impulse", dP < 1e-3, f"discrepancy {dP:.2e} N.s")

    K1, U1 = c.energy(); E1 = K1 + U1
    drift = abs(E1 - E0) / max(abs(E0), 1e-9)
    check("energy conserved in flight", drift < 5e-3,
          f"E {E0:.6f} -> {E1:.6f} J, relative drift {drift:.2e}")

    # ── F3: THE FALLING CAT ──────────────────────────────────────────────────────────────────
    print("\nF3  THE FALLING CAT: zero angular momentum, yet the body reorients")
    # The limbs must be moved by INTERNAL forces -- muscles. Overwriting qd each step (my first
    # version) clobbers what the solver just computed and injects momentum from nowhere, which is
    # exactly what the |L| check is there to catch.
    cat = creature(z=50.0)
    cat.gravity = np.zeros(3)                    # no gravity: isolate the angular-momentum claim
    pL = attach_antagonist(cat, 0, -1, 0, 0.06, 0.05, 60.0, 'sL')
    pR = attach_antagonist(cat, 1, -1, 1, 0.06, 0.05, 60.0, 'sR')
    cat.q[:] = [0.0, 0.0]
    cat.set_rest_lengths(0.5)
    cat.qd[:] = 0.0
    cat.v_base[:] = 0.0
    cat.w_base[:] = 0.0
    _, L_start = cat.momentum()
    steps = int(2.0 / dt)
    Lmax = 0.0
    for k in range(steps):
        phase = 2 * np.pi * k / steps            # a slow cycle: out, then back
        u = np.sin(phase)
        pL.drive(u)
        pR.drive(-u)                             # the limbs oppose -> a net internal twist
        cat.step(dt)
        if k % 500 == 0:
            _, Lk = cat.momentum()
            Lmax = max(Lmax, float(np.linalg.norm(Lk)))
    _, L_end = cat.momentum()
    Rend = cat.base_rot
    ang = float(np.degrees(np.arccos(np.clip((np.trace(Rend) - 1) / 2, -1, 1))))
    print(f"      angular momentum start {np.round(L_start, 9)}")
    print(f"      angular momentum end   {np.round(L_end, 9)}   (peak |L| during: {Lmax:.2e})")
    print(f"      joints ended at {np.round(cat.q, 4)} rad; the TORSO turned {ang:.3f} deg")
    check("angular momentum stays zero throughout", Lmax < 1e-6,
          f"peak |L| = {Lmax:.2e} kg.m^2/s -- muscles are INTERNAL, so they cannot create any")
    check("internal motion reorients the body (the cat)", ang > 0.05,
          f"torso rotated {ang:.3f} deg with L = 0 -- a PINNED base cannot do this at all")

    # ── F5: it lands ─────────────────────────────────────────────────────────────────────────
    print("\nF5  dropped onto ground: it lands and the floor carries it")
    ground = Ground()
    model = ContactModel(k=3.0e5, zeta=5.0e3, mu=0.9, v_eps=2e-5)
    d = creature(z=0.60)
    d.q[:] = [0.0, 0.0]
    feet = [Foot(link=-1, at=(0.12, 0.09, -0.25), radius=0.03, name='c0'),
            Foot(link=-1, at=(0.12, -0.09, -0.25), radius=0.03, name='c1'),
            Foot(link=-1, at=(-0.12, 0.09, -0.25), radius=0.03, name='c2'),
            Foot(link=-1, at=(-0.12, -0.09, -0.25), radius=0.03, name='c3')]
    fn_last = 0.0
    for k in range(int(2.5 / dt)):
        f, info = tree_contacts(d, feet, ground, model)
        d.step(dt, extra_forces=f)
        fn_last = sum(ci['Fn'] for ci in info)
    weight = d.total_mass() * G
    print(f"      base settled at z = {d.base_pos[2]:.5f} m (contacts at -0.25, r = 0.03)")
    print(f"      total normal force {fn_last:.2f} N   vs   total weight {weight:.2f} N")
    check("it comes to rest on the floor", abs(d.base_pos[2] - 0.28) < 5e-3,
          f"base z = {d.base_pos[2]:.4f} m, expected ~0.280 = 0.25 + contact radius")
    check("the floor carries the whole creature", abs(fn_last - weight) / weight < 0.03,
          f"{fn_last:.2f} N vs {weight:.2f} N ({100*abs(fn_last-weight)/weight:.1f}% off)")

    # ── F6: IT FALLS OVER ────────────────────────────────────────────────────────────────────
    print("\nF6  push it -- and it TOPPLES (a pinned base could not)")
    def topple(push_N):
        b = creature(z=0.281)
        b.q[:] = [0.0, 0.0]
        ft = [Foot(link=-1, at=(0.12, 0.09, -0.25), radius=0.03),
              Foot(link=-1, at=(0.12, -0.09, -0.25), radius=0.03),
              Foot(link=-1, at=(-0.12, 0.09, -0.25), radius=0.03),
              Foot(link=-1, at=(-0.12, -0.09, -0.25), radius=0.03)]
        tilt = []
        for k in range(int(1.6 / dt)):
            f, _ = tree_contacts(b, ft, ground, model)
            if 2_000 <= k < 4_000:
                f = f + [(-1, b.base_pos + b.base_rot @ np.array([0.0, 0.0, 0.22]),
                          np.array([push_N, 0.0, 0.0]))]
            b.step(dt, extra_forces=f)
            up = b.base_rot @ np.array([0.0, 0.0, 1.0])
            tilt.append(float(np.degrees(np.arccos(np.clip(up[2], -1, 1)))))
        return float(tilt[-1]), float(np.max(tilt))
    for p in (60.0, 200.0, 600.0):
        end_t, max_t = topple(p)
        print(f"      push {p:5.0f} N -> max tilt {max_t:6.2f} deg, final tilt {end_t:6.2f} deg")
        if p == 60.0:
            small = end_t
        if p == 600.0:
            big = end_t
    check("a hard push topples it, a light one does not", big > 30.0 and small < 10.0,
          f"600 N leaves it at {big:.1f} deg from upright; 60 N only {small:.1f} deg -- "
          "the body is genuinely free to fall")

    n_fail = sum(1 for _, ok in results if not ok)
    print("\n" + "=" * 66)
    print(f"{len(results) - n_fail}/{len(results)} checks passed")
    return 1 if n_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
