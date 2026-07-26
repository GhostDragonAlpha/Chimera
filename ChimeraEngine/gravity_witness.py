"""gravity_witness.py — WITNESS "UP IS DECIDED BY THE PULL" (operator ruling, 2026-07-25).

  U1  up is local           at four points around a planet, "up" points four different ways -- and
                            each one is exactly the outward radial there
  U2  no global +Z          the angle between local up and world +Z grows to 90 deg at the equator,
                            which is the whole reason a global up is wrong
  U3  surface gravity       g at the surface matches what the body was built to have
  U4  ORBIT                 given v = sqrt(mu/r) sideways, a body CIRCLES instead of falling. Same
                            equation as standing on the ground -- one law, not two.
  U5  falls toward centre   dropped from anywhere, it accelerates along the local down
  U6  TIDAL GRADIENT        a long structure feels different gravity at its two ends, for free,
                            because each part is asked what gravity is where IT is
  U7  planet as ground      SphereGround: a body lands on a planet with no special cases, and its
                            tilt is measured against LOCAL up

Run:  python ChimeraEngine/gravity_witness.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gravity import Uniform, PointMass, Composite, local_frame, as_field   # noqa: E402
from physics_articulated import rod                                        # noqa: E402
from physics_floating import FloatingTree                                  # noqa: E402
from physics import inertia_box                                            # noqa: E402
from contact import SphereGround, ContactModel, Foot, tree_contacts        # noqa: E402

np.set_printoptions(precision=6, suppress=True)
results: list[tuple[str, bool]] = []


def check(name: str, ok: bool, detail: str) -> None:
    results.append((name, ok))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")


def main() -> int:
    print("\nWITNESS: up is decided by the pull of gravity\n" + "=" * 66)

    # A small world, so a whole orbit is quick to integrate and easy to read.
    R = 1000.0
    planet = PointMass.from_surface_g(center=(0, 0, 0), radius=R, g_surface=9.80665)
    print(f"      planet: radius {R:.0f} m, surface g {planet.surface_g():.4f} m/s^2, "
          f"mu = {planet.mu:.4e}")

    # ── U1 / U2: up is LOCAL ─────────────────────────────────────────────────────────────────
    print("\nU1  four points around the planet -> four different ups")
    pts = {'north pole': np.array([0, 0, R]), 'equator +x': np.array([R, 0, 0]),
           'equator -y': np.array([0, -R, 0]), 'south pole': np.array([0, 0, -R])}
    worst_radial = 0.0
    for nm, p in pts.items():
        up = planet.up_at(p)
        radial = p / np.linalg.norm(p)
        err = float(np.linalg.norm(up - radial))
        worst_radial = max(worst_radial, err)
        ang_z = float(np.degrees(np.arccos(np.clip(np.dot(up, [0, 0, 1]), -1, 1))))
        print(f"      {nm:11s} up = {np.round(up, 4)}   angle from world +Z: {ang_z:5.1f} deg")
    check("up is the local outward radial", worst_radial < 1e-12,
          f"max deviation from radial {worst_radial:.2e} at four points around the world")
    ang_eq = float(np.degrees(np.arccos(np.clip(
        np.dot(planet.up_at(pts['equator +x']), [0, 0, 1]), -1, 1))))
    check("a global +Z is wrong away from one point", abs(ang_eq - 90.0) < 1e-9,
          f"at the equator local up is {ang_eq:.1f} deg from world +Z -- 'up' cannot be a constant")

    # ── U3: surface gravity ──────────────────────────────────────────────────────────────────
    print("\nU3  surface gravity matches what the planet was built with")
    g_surf = planet.strength_at(pts['equator +x'])
    check("g at the surface is as specified", abs(g_surf - 9.80665) < 1e-9,
          f"{g_surf:.6f} m/s^2 vs 9.80665 requested")

    # ── U4: ORBIT ────────────────────────────────────────────────────────────────────────────
    print("\nU4  ORBIT: sideways at sqrt(mu/r) -> it circles instead of falling")
    r_orb = 1.5 * R
    v_c = planet.circular_speed(r_orb)
    period = 2 * np.pi * r_orb / v_c
    x = np.array([r_orb, 0.0, 0.0])
    v = np.array([0.0, v_c, 0.0])
    dt = period / 20000.0
    rmin, rmax = r_orb, r_orb
    for _ in range(20000):                       # one full revolution, leapfrog (symplectic)
        a = planet.at(x)
        v = v + a * dt
        x = x + v * dt
        rr = float(np.linalg.norm(x))
        rmin, rmax = min(rmin, rr), max(rmax, rr)
    ecc = (rmax - rmin) / (rmax + rmin)
    ang = float(np.degrees(np.arctan2(x[1], x[0])))
    print(f"      v_circular {v_c:.4f} m/s,  period {period:.2f} s")
    print(f"      after one predicted period: radius {np.linalg.norm(x):.3f} m "
          f"(started {r_orb:.1f}), returned to {ang:+.2f} deg")
    print(f"      radius stayed within [{rmin:.2f}, {rmax:.2f}] -> eccentricity {ecc:.2e}")
    check("a circular orbit stays circular", ecc < 2e-3,
          f"eccentricity {ecc:.2e} over a full revolution -- falling and orbiting are one law")
    check("it comes back round", abs(ang) < 3.0,
          f"returned to {ang:+.2f} deg after exactly one computed period")

    # ── U5: it falls toward the centre, from anywhere ────────────────────────────────────────
    print("\nU5  dropped anywhere, it accelerates along the LOCAL down")
    worst = 0.0
    for nm, p in pts.items():
        start = p * 1.05
        pos, vel = start.copy(), np.zeros(3)
        for _ in range(200):
            vel = vel + planet.at(pos) * 0.01
            pos = pos + vel * 0.01
        moved = pos - start
        toward = -start / np.linalg.norm(start)
        align = float(np.dot(moved / (np.linalg.norm(moved) + 1e-15), toward))
        worst = min(worst, align) if worst else align
        print(f"      from above {nm:11s}: moved {np.linalg.norm(moved):.3f} m, "
              f"alignment with local down {align:.6f}")
    check("everything falls toward the centre", worst > 1 - 1e-9,
          f"worst alignment with local down {worst:.9f} (1.0 = exactly down)")

    # ── U6: TIDAL gradient ───────────────────────────────────────────────────────────────────
    print("\nU6  a long structure feels a GRADIENT (tidal), because each part asks locally")
    near = np.array([R * 1.02, 0, 0]); far = np.array([R * 1.30, 0, 0])
    gn, gf = planet.strength_at(near), planet.strength_at(far)
    print(f"      g at {np.linalg.norm(near):.0f} m = {gn:.4f},  at {np.linalg.norm(far):.0f} m = "
          f"{gf:.4f} m/s^2   -> {100*(gn-gf)/gn:.1f}% weaker at the far end")
    check("gravity differs along a long body", (gn - gf) / gn > 0.1,
          f"{100*(gn-gf)/gn:.1f}% difference across the structure -- tidal forces for free")

    # ── U7: a PLANET is ground, with no special cases ────────────────────────────────────────
    print("\nU7  land on the planet at an arbitrary point; tilt measured against LOCAL up")
    site = np.array([0.0, R, 0.0])               # on the equator, where world +Z is useless
    up_hat = site / np.linalg.norm(site)
    torso_m, ext = 12.0, np.array([0.30, 0.20, 0.50])
    # orient the body so its own +Z is the LOCAL up at the landing site
    ref = np.array([1.0, 0.0, 0.0])
    right = np.cross(ref, up_hat); right /= np.linalg.norm(right)
    fwd = np.cross(up_hat, right)
    Rb = np.column_stack([right, fwd, up_hat])
    from physics import quat_identity
    body = FloatingTree(base_mass=torso_m, base_inertia=inertia_box(torso_m, ext),
                        links=[rod('armL', 1.0, 0.2, anchor=(0, 0.1, 0.2), axis=(0, 1, 0), parent=-1)],
                        gravity=planet, base_pos=site + up_hat * 0.40)
    body.base_rot = Rb
    from physics import quat_to_mat
    # set the quaternion to match Rb (via its rotation matrix -> quaternion)
    tr = np.trace(Rb)
    w_ = np.sqrt(max(1e-12, 1 + tr)) / 2
    body.base_quat = np.array([(Rb[2, 1] - Rb[1, 2]) / (4 * w_), (Rb[0, 2] - Rb[2, 0]) / (4 * w_),
                               (Rb[1, 0] - Rb[0, 1]) / (4 * w_), w_])
    body.base_rot = quat_to_mat(body.base_quat)
    ground = SphereGround(center=(0, 0, 0), radius=R)
    model = ContactModel(k=3.0e5, zeta=5.0e3, mu=0.9, v_eps=2e-5)
    pads = [Foot(link=-1, at=(sx * 0.12, sy * 0.09, -0.25), radius=0.03, name=f'c{i}')
            for i, (sx, sy) in enumerate([(1, 1), (1, -1), (-1, 1), (-1, -1)])]
    print(f"      local up at the site {np.round(up_hat, 4)} (world +Z would be "
          f"{np.degrees(np.arccos(abs(float(np.dot(up_hat,[0,0,1]))))):.0f} deg wrong)")
    fn = 0.0
    for _ in range(12_000):
        f, info = tree_contacts(body, pads, ground, model)
        body.step(2e-4, extra_forces=f)
        fn = sum(ci['Fn'] for ci in info)
    alt = float(np.linalg.norm(body.base_com_world())) - R
    weight = body.total_mass() * planet.strength_at(body.base_com_world())
    print(f"      settled at altitude {alt:.4f} m above the surface, tilt {body.tilt_deg():.3f} deg "
          f"from LOCAL up")
    print(f"      normal force {fn:.2f} N vs weight {weight:.2f} N")
    check("it stands on a sphere with no special cases", 0.24 < alt < 0.32 and body.tilt_deg() < 5.0,
          f"altitude {alt:.3f} m, tilt {body.tilt_deg():.2f} deg from the LOCAL up -- "
          "the same contact code that handled a flat floor")

    # ── U8: A GRAVITATIONAL BODY IS A MEMBRANE ───────────────────────────────────────────────
    print("\nU8  a gravitational body IS a membrane -- the tree decides which way is down")
    from gravity import MembraneField
    from core.membranes import Membrane, Port
    star = Membrane(name='theStar', scale=8000.0, serial='star',
                    properties={'surface_g': 28.0})
    star.ports['pull'] = Port(name='pull', kind='gravitational', at=(0, 0, 0), facing=(0, 0, 1))
    world = star.add(Membrane(name='aPlanet', scale=1000.0, serial='planet',
                              origin=np.array([60000.0, 0.0, 0.0]),
                              properties={'surface_g': 9.80665}))
    world.ports['pull'] = Port(name='pull', kind='gravitational', at=(0, 0, 0), facing=(0, 0, 1))
    moon = world.add(Membrane(name='aMoon', scale=270.0, serial='moon',
                              origin=np.array([9000.0, 0.0, 0.0]),
                              properties={'surface_g': 1.62}))
    moon.ports['pull'] = Port(name='pull', kind='gravitational', at=(0, 0, 0), facing=(0, 0, 1))
    fieldm = MembraneField(root=star)
    print(f"      wells found in the tree: {[m.name for m, _ in fieldm.wells]}")
    probes = {'on the planet': np.array([60000.0 + 1000.0, 0.0, 0.0]),
              'on the moon':   np.array([60000.0 + 9000.0 + 270.0, 0.0, 0.0]),
              'near the star': np.array([8000.0 + 500.0, 0.0, 0.0])}
    names = []
    for nm, pp in probes.items():
        m, _, s = fieldm.dominant(pp)
        up = fieldm.up_at(pp)
        names.append(m.name)
        print(f"      {nm:14s} -> pulled by {m.name:8s} at {s:7.3f} m/s^2, "
              f"path {fieldm.down_path(pp):22s} up = {np.round(up, 3)}")
    check("the membrane tree decides what pulls you",
          names == ['aPlanet', 'aMoon', 'theStar'],
          f"dominant body changes with where you are: {names} -- sphere of influence, "
          "from the same hierarchy that gives address, LOD and clock rate")
    # Gravity SUPERPOSES, so what you feel standing on a planet is its own g PLUS everything else
    # pulling on you. Decompose it rather than asserting the planet's number alone -- the sum is the
    # physical answer, and the fact that the star measurably contributes is the point of a Composite.
    stand = probes['on the planet']
    total = fieldm.strength_at(stand)
    parts = {m.name: float(np.linalg.norm(wl.at(stand))) for m, wl in fieldm.wells}
    print(f"      standing on aPlanet you feel {total:.4f} m/s^2, made of: "
          + ", ".join(f"{k} {v:.4f}" for k, v in sorted(parts.items(), key=lambda kv: -kv[1])))
    own = parts['aPlanet']
    # VECTORS sum, not magnitudes -- |a| + |b| != |a + b| unless they are exactly parallel. Summing
    # the magnitudes gave 10.2900 against a true 10.2864, which is what the check caught.
    vsum = np.zeros(3)
    for _m, _w in fieldm.wells:
        vsum = vsum + _w.at(stand)
    check("each membrane contributes its own declared pull, and they SUM",
          abs(own - 9.80665) < 1e-6 and abs(total - float(np.linalg.norm(vsum))) < 1e-9,
          f"aPlanet's own share is exactly {own:.5f} m/s^2 as declared; the total {total:.4f} is the "
          f"SUM of every well -- the star really does pull you while you stand on the planet")

    n_fail = sum(1 for _, ok in results if not ok)
    print("\n" + "=" * 66)
    print(f"{len(results) - n_fail}/{len(results)} checks passed")
    return 1 if n_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
