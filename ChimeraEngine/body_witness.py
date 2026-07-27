"""body_witness.py — IS IT A REAL BODY?

  B1  ANTHROPOMETRY      masses sum to the person, segments sum to the height, and a taller heavier
                         person comes out taller and heavier in the right places
  B2  THE HUBS DO NOT BREAK IT   multi-DOF joints are built from massless intermediates; measure
                         the mass matrix's conditioning instead of hoping
  B3  EVERY PAIR OPPOSES the two muscles of each joint have moment arms of OPPOSITE sign, measured
  B4  PEAK TORQUE        full activation produces the torque a human actually produces, because
                         tension was sized against the arm the geometry really has
  B5  CO-CONTRACTION     THE WHOLE ARGUMENT FOR MUSCLES: both antagonists on stiffens the joint
                         WITHOUT moving it. A torque model cannot express this at all.
  B6  IT FALLS LIKE A BODY   released with no controller it collapses and lands; nothing explodes
  B7  NO FREE ENERGY     an unactuated drop does not gain energy

Run:  python ChimeraEngine/body_witness.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from body import (MASS_FRAC, LEN_FRAC, PEAK_TORQUE, OBS_DIM, ACT_DIM,        # noqa: E402
                  humanoid, spec)
from contact import ContactModel, Foot, Ground, tree_contacts                # noqa: E402

np.set_printoptions(precision=4, suppress=True)
results: list[tuple[str, bool]] = []


def check(name: str, ok: bool, detail: str) -> None:
    results.append((name, ok))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")


def joint_torques(h) -> np.ndarray:
    """Generalized torque the muscles currently produce, per joint."""
    Q = np.asarray(h.tree.generalized_force_f(h.tree.muscle_forces()), float)[-h.tree.n:]
    return Q + h.tree.muscle_torques()      # transmission muscles contribute torque directly


def main() -> int:
    print("\nWITNESS: the humanoid body\n" + "=" * 72)
    h = humanoid()
    print("  " + h.describe())

    # ── B1 ───────────────────────────────────────────────────────────────────────────────────
    print("\nB1  ANTHROPOMETRY -- Winter's table, not a shape someone drew")
    frac_sum = (MASS_FRAC['pelvis'] + MASS_FRAC['chest'] + MASS_FRAC['head'] +
                2 * (MASS_FRAC['upperarm'] + MASS_FRAC['forearm']) +
                2 * (MASS_FRAC['thigh'] + MASS_FRAC['shin'] + MASS_FRAC['foot']))
    tot = h.tree.total_mass()
    stand = (LEN_FRAC['thigh'] + LEN_FRAC['shin'] + LEN_FRAC['pelvis'] +
             LEN_FRAC['chest'] + LEN_FRAC['head'])
    print(f"      mass fractions sum to {frac_sum:.4f};  built body masses {tot:.3f} kg of 70.0")
    print(f"      ankle-to-crown fractions sum to {stand:.3f} of height "
          f"({stand*1.75:.3f} m of 1.75)")
    big = humanoid(height=1.90, mass=95.0)
    print(f"      a different person: {big.describe().split('|')[0].strip()}, "
          f"thigh {LEN_FRAC['thigh']*1.90:.3f} m vs {LEN_FRAC['thigh']*1.75:.3f} m")
    check("the body masses and measures a real person", abs(frac_sum - 1.0) < 1e-9
          and abs(tot - 70.0) < 1e-9 and 0.94 < stand < 1.02,
          f"fractions sum to exactly {frac_sum:.4f}, built mass {tot:.3f} kg of 70.0 -- the six "
          f"joint hubs are carved OUT of the pelvis, not added on top, standing {stand:.3f}")

    # ── B2 ───────────────────────────────────────────────────────────────────────────────────
    print("\nB2  THE JOINT HUBS DO NOT WRECK THE SOLVE")
    M = h.tree.mass_matrix_f()
    cond = float(np.linalg.cond(M))
    ev = np.linalg.eigvalsh(0.5 * (M + M.T))
    print(f"      mass matrix {M.shape}, condition number {cond:.3e}")
    print(f"      eigenvalues {ev.min():.3e} .. {ev.max():.3e}  (all positive => invertible)")
    print(f"      a truly massless hub would put a ZERO here and the solve would fail in a way")
    print(f"      that reads as a physics bug; {0.002*100:.1f}% of body mass buys the difference")
    check("the mass matrix is positive-definite and well-conditioned",
          ev.min() > 0 and cond < 1e9,
          f"smallest eigenvalue {ev.min():.2e} > 0, condition {cond:.1e} -- the solve is safe")

    # ── B3 ───────────────────────────────────────────────────────────────────────────────────
    print("\nB3  EVERY ANTAGONIST PAIR REALLY OPPOSES (measured, not assumed)")
    bad = []
    for nm, p in sorted(h.pairs.items()):
        j = h.joint[nm]
        af = h.tree.moment_arm(p.flexor, j)
        ae = h.tree.moment_arm(p.extensor, j)
        if af * ae >= 0:
            bad.append(nm)
        if nm in ('shinL', 'thighL', 'footL', 'forearmL', 'chest'):
            print(f"      {nm:<10} flexor arm {af:+.4f} m   extensor arm {ae:+.4f} m")
    print(f"      ... {len(h.pairs)} pairs checked, {len(bad)} that do not oppose")
    check("all 18 pairs have opposing moment arms", not bad,
          f"{len(h.pairs)}/{len(h.pairs)} oppose -- attach_antagonist REFUSES a pair that does not, "
          "so a joint that could only be driven one way cannot be built by accident")

    # ── B4 ───────────────────────────────────────────────────────────────────────────────────
    print("\nB4  PEAK TORQUE matches what a human actually produces")
    rows, worst = [], 0.0
    for nm in ('shinL', 'thighL', 'chest', 'forearmL', 'footL'):
        j = h.joint[nm]
        for p in h.pairs.values():
            p.drive(0.0)
        h.pairs[nm].drive(1.0)
        tau = abs(joint_torques(h)[j])
        for p in h.pairs.values():
            p.drive(0.0)
        rows.append((nm, tau))
    tgt = {'shinL': 'knee', 'thighL': 'hip_roll', 'chest': 'waist',
           'forearmL': 'elbow', 'footL': 'ankle_roll'}
    for nm, tau in rows:
        want = PEAK_TORQUE[tgt[nm]]
        err = abs(tau - want) / want
        worst = max(worst, err)
        print(f"      {nm:<10} full activation -> {tau:7.1f} N.m   published {want:6.1f}   "
              f"({100*err:5.1f}% off)")
    check("full activation makes a human-sized torque", worst < 0.12,
          f"worst {100*worst:.1f}% -- because tension was sized against the MEASURED moment arm, "
          "not the attachment offset I originally assumed")

    # ── B5 ───────────────────────────────────────────────────────────────────────────────────
    print("\nB5  CO-CONTRACTION: stiff WITHOUT moving -- the whole argument for muscles")
    j = h.joint['shinL']
    d = 2e-3

    def stiffness(co):
        for p in h.pairs.values():
            p.drive(0.0)
        h.pairs['shinL'].drive(0.0, co_contract=co)
        q0 = h.tree.q[j]
        h.tree.q[j] = q0 + d; tp = joint_torques(h)[j]
        h.tree.q[j] = q0 - d; tm = joint_torques(h)[j]
        h.tree.q[j] = q0
        net = joint_torques(h)[j]
        return -(tp - tm) / (2 * d), net

    for co in (0.0, 0.25, 0.5, 1.0):
        k, net = stiffness(co)
        print(f"      co-contraction {co:4.2f} -> stiffness {k:9.1f} N.m/rad, "
              f"net torque {net:+8.3f} N.m")
    k0, _ = stiffness(0.0)
    k1, net1 = stiffness(1.0)
    for p in h.pairs.values():
        p.drive(0.0)
    print("      SOLVED by the TRANSMISSION (operator, 2026-07-26). It read -1666.8 N.m/rad --")
    print("      co-contraction DESTABILISING the joint, bracing working backwards. tau = r(q)F(q),")
    print("      so dtau/dq = r'F + rF'. A straight-line cable's r swings fast with angle, so r'F")
    print("      dominated and no rest-length or curve width could beat it.")
    print("      Nature's answer is PULLEYS -- the hand's A1-A5 annular ligaments hold the tendon")
    print("      against bone so r stays controlled; rupture one and it bowstrings. So r(q) is now")
    print("      SPECIFIED, not discovered, and virtual work gives the length for free: r = -dL/dq.")
    check("both muscles on stiffens the joint while producing no net torque",
          k1 > 5.0 * max(k0, 1e-6) and abs(net1) < 2.0,
          f"stiffness {k0:.1f} -> {k1:.1f} N.m/rad at net torque {net1:+.3f} N.m, up from -1666.8 "
          "before the transmission. A TORQUE model reads 'braced' and 'limp' as the same zero -- "
          "this is what you do landing a fall, and it is why muscles were chosen over torques")

    # ── B6 ───────────────────────────────────────────────────────────────────────────────────
    print("\nB6  IT FALLS LIKE A BODY -- released limp, no controller at all")
    hh = humanoid(base_pos=(0.0, 0.0, 1.05))
    # PERTURB IT. A perfectly straight, perfectly symmetric limp body dropped exactly vertically
    # BALANCES -- an unstable equilibrium is still an equilibrium, and my first version asserted
    # "it collapses" without ever creating the asymmetry that makes collapse happen. Same mistake
    # as testing a shadow with no occluder. A few degrees of bend is the perturbation.
    rng = np.random.default_rng(3)
    hh.tree.q[:] = rng.normal(0.0, 0.08, hh.tree.n)
    ground = Ground()
    model = ContactModel(k=5.0e4, zeta=2.0e3, mu=0.8, v_eps=2e-5)   # soft floor: 56 steps/period
    pads = [Foot(link=hh.joint[n], at=(0.0, 0.0, -0.02), radius=0.05, name=n)
            for n in ('footL', 'footR', 'forearmL', 'forearmR', 'shinL', 'shinR', 'head')]
    pads.append(Foot(link=-1, at=(0.0, 0.0, 0.0), radius=0.10, name='pelvis'))
    dt, zs = 5e-4, []
    for k in range(int(0.6 / dt)):
        f, info = tree_contacts(hh.tree, pads, ground, model)
        hh.tree.step(dt, extra_forces=f)
        if k % 300 == 0:
            zs.append((k * dt, hh.tree.base_pos[2], sum(1 for c in info if c['touching'])))
    for t, z, n in zs:
        print(f"      t {t:4.2f} s   pelvis z {z:6.3f} m   {n} contacts")
    fin = hh.tree.base_pos[2]
    ok_fall = np.isfinite(fin) and 0.0 < fin < 0.95 and np.all(np.isfinite(hh.tree.q))
    check("a limp body collapses and lands, without exploding", ok_fall,
          f"pelvis fell 1.050 -> {fin:.3f} m, all {hh.tree.n} joint angles finite -- 18 hinges, "
          "36 muscles and 8 contacts integrated with nothing driving it")

    # ── B7 ───────────────────────────────────────────────────────────────────────────────────
    print("\nB7  NO FREE ENERGY in the fall")
    h2 = humanoid(base_pos=(0.0, 0.0, 3.0))
    K0, U0 = h2.tree.energy()
    for _ in range(400):
        h2.tree.step(5e-4)
    K1, U1 = h2.tree.energy()
    drift = (K1 + U1 - K0 - U0) / max(abs(K0 + U0), 1e-9)
    print(f"      free fall 0.2 s, no contact, no muscles: E {K0+U0:.4f} -> {K1+U1:.4f} J")
    check("energy is conserved in free flight", abs(drift) < 5e-3,
          f"relative drift {drift:+.2e} over 400 steps of a 24-DOF tree")

    # ── B8 ───────────────────────────────────────────────────────────────────────────────────
    print("\nB8  HOW FAST IS IT, HONESTLY -- the number that decides the whole training plan")
    import time
    h3 = humanoid(base_pos=(0.0, 0.0, 3.0))
    t0 = time.perf_counter()
    for _ in range(40):
        h3.tree.step(1e-3)
    per = (time.perf_counter() - t0) / 40
    t0 = time.perf_counter()
    for _ in range(10):
        h3.tree.mass_matrix_f()
    per_M = (time.perf_counter() - t0) / 10
    print(f"      one step {per*1000:6.2f} ms   of which the 24x24 mass matrix is {per_M*1000:6.2f} ms")
    print(f"      real time at 1 kHz needs 1.00 ms  ->  we are {per/1e-3:5.0f}x too slow")
    print(f"      one 10,000-step rollout: {per*10000/60:6.1f} minutes")
    print(f"      a 1e7-step training run: {per*1e7/86400:6.0f} DAYS")
    print(f"      mujoco-warp measured on this machine: 2,358 evals/sec, whole population per kernel")
    check("the numpy engine is TOO SLOW to train on, and this is now a measured fact", per > 5e-3,
          f"{per*1000:.1f} ms/step, {100*per_M/per:.0f}% of it building the mass matrix by 24 "
          f"unit-acceleration RNEA passes. THE_BODY.md 3.4 said witness MuJoCo before training; "
          "this says MuJoCo is not an optimisation, it is a REQUIREMENT")

    print("\n" + "=" * 72)
    print(f"FROZEN SPACES: observation {OBS_DIM}, action {ACT_DIM}")
    n_fail = sum(1 for _, ok in results if not ok)
    print(f"{len(results) - n_fail}/{len(results)} checks passed")
    return 1 if n_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
