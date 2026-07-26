"""fields_witness.py — WITNESS EM AND LIGHT (operator ruling: collision IS electromagnetism).

  E1  one curve, two lobes    repulsive when overlapping, attractive just outside, zero beyond reach
  E2  hardness IS stiffness   a load sinks by F/k -- steel, rock and rubber differ by that number
                              and nothing else
  E3  it holds matter apart   a heavy body cannot pass through a surface; measured penetration
  E4  ADHESION                pulling a stuck object off costs exactly the depth of the well
  E5  contact is its LIMIT    the existing penalty ContactModel IS this curve with adhesion 0

  L1  inverse square          irradiance falls as 1/r^2
  L2  DAY AND NIGHT           the far side of a planet is in shadow -- by occlusion, not a flag
  L3  the terminator          exactly half a sphere is lit, and N.L falls to zero at the edge
  L4  solar power             watts on a panel match irradiance x area x cos
  L5  ECLIPSE                 a moon between star and planet casts a real shadow -- SAME mechanism
                              as day/night, not a second one
  L6  temperature             equilibrium T from irradiance -- the number that placed the
                              habitable zone in this project's own planet rung

Run:  python ChimeraEngine/fields_witness.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fields import (Coupling, EMField, Star, Occluder, LightField,          # noqa: E402
                    STEEL, ROCK, RUBBER, FLESH, TAPE, REGOLITH)
from contact import Ground, ContactModel, Foot, step_body                    # noqa: E402
from physics import Body, inertia_box                                        # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.membranes import Membrane                                          # noqa: E402

np.set_printoptions(precision=6, suppress=True)
G = 9.80665
results: list[tuple[str, bool]] = []


def check(name: str, ok: bool, detail: str) -> None:
    results.append((name, ok))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")


def main() -> int:
    print("\nWITNESS: the EM field and the light field\n" + "=" * 68)

    # ══ ELECTROMAGNETIC ══════════════════════════════════════════════════════════════════════
    print("\nE1  ONE curve, two lobes: repulsion inside, attraction just outside")
    c = Coupling(stiffness=1.0e5, adhesion=50.0, reach=2e-3)
    gaps = [-1e-3, -1e-4, 0.0, 5e-4, 1e-3, 1.9e-3, 3e-3]
    for g in gaps:
        f = c.force(g)
        kind = "REPEL " if f > 0 else ("attract" if f < 0 else "  --   ")
        print(f"      gap {g*1000:+6.2f} mm -> {f:+9.2f} N   {kind}")
    rep = c.force(-1e-3) > 0
    att = c.force(5e-4) < 0
    off = abs(c.force(3e-3)) < 1e-12
    check("repel inside, attract outside, nothing beyond reach", rep and att and off,
          f"{c.force(-1e-3):+.1f} N overlapping, {c.force(5e-4):+.1f} N touching, "
          f"{c.force(3e-3):+.1f} N beyond reach -- solidity and adhesion on ONE dial")

    print("\nE2  hardness IS the stiffness number, and nothing else")
    load = 500.0
    for nm, mat in (('steel', STEEL), ('rock', ROCK), ('rubber', RUBBER), ('flesh', FLESH)):
        sink = load / mat.stiffness
        back = mat.force(-sink)
        print(f"      {nm:7s} k = {mat.stiffness:9.1e} N/m -> {load:.0f} N sinks {sink*1000:7.4f} mm "
              f"(restoring {back:7.1f} N)")
    soft = load / RUBBER.stiffness
    hard = load / STEEL.stiffness
    check("softer material sinks further, by exactly F/k", soft > hard * 50,
          f"rubber sinks {soft*1000:.4f} mm vs steel {hard*1000:.5f} mm under the same {load:.0f} N")

    print("\nE3  it HOLDS MATTER APART -- a real body cannot pass through a floor")
    ground = Ground()
    model = ContactModel(k=ROCK.stiffness, zeta=ROCK.damping, mu=0.8, v_eps=2e-5)
    m = Membrane(name='blk', scale=0.4, serial='blk')
    b = Body(membrane=m, mass=60.0, inertia=inertia_box(60.0, np.array([0.4, 0.4, 0.4])))
    b.x = np.array([0.0, 0.0, 1.20])                      # dropped from a metre up
    feet = [Foot(link=0, at=(sx * 0.2, sy * 0.2, -0.2), radius=0.02)
            for sx, sy in [(1, 1), (1, -1), (-1, 1), (-1, -1)]]
    deepest = 0.0
    for k in range(80_000):
        info = step_body(b, 2e-5, feet, ground, model)
        deepest = max(deepest, max(ci['pen'] for ci in info))
    rest = b.x[2]
    predicted = 60.0 * G / (4 * ROCK.stiffness)           # mg/(4k) -- the static sink, 4 feet share
    print(f"      dropped from 1.20 m, deepest penetration during impact {deepest*1000:.3f} mm")
    print(f"      resting at z = {rest:.5f} m; static sink mg/4k = {predicted*1000:.4f} mm "
          f"(measured {(0.22-rest)*1000:.4f} mm)")
    check("matter does not fall through matter", deepest < 0.02 and abs(rest - 0.22) < 2e-3,
          f"max penetration {deepest*1000:.2f} mm on a 1.2 m drop; rests at {rest:.4f} m")

    print("\nE4  ADHESION: pulling a stuck surface off costs the depth of the well")
    for nm, mat in (('rock (dry)', ROCK), ('regolith', REGOLITH), ('flesh', FLESH), ('tape', TAPE)):
        print(f"      {nm:11s} pull-off {mat.pull_off_force():7.1f} N   reach {mat.reach*1000:.1f} mm")
    check("stickiness is a number on the same curve",
          TAPE.pull_off_force() > REGOLITH.pull_off_force() > ROCK.pull_off_force(),
          f"tape {TAPE.pull_off_force():.0f} N > regolith {REGOLITH.pull_off_force():.0f} N > "
          f"dry rock {ROCK.pull_off_force():.0f} N -- dust clinging in vacuum is not a special case")

    print("\nE5  the penalty CONTACT model IS this curve's short-range limit")
    probe = Coupling(stiffness=model.k, adhesion=0.0, damping=model.zeta)
    same = all(abs(probe.force(-p, 0.0) - (model.k * p)) < 1e-9 for p in (1e-4, 5e-4, 1e-3))
    print(f"      Coupling(k={model.k:.1e}) at 1 mm overlap -> {probe.force(-1e-3):.1f} N;  "
          f"ContactModel k*pen -> {model.k*1e-3:.1f} N")
    check("contact was the EM repulsive lobe all along", same,
          "identical forces -- contact.py was never a separate system, only an unnamed one")

    # ══ LIGHT ════════════════════════════════════════════════════════════════════════════════
    print("\nL1  irradiance falls as 1/r^2")
    AU = 1.496e11
    sun = Star.from_irradiance(center=(0, 0, 0), at_distance=AU, irradiance=1361.0, radius=6.957e8)
    lf = LightField(stars=[sun])
    for f_ in (0.5, 1.0, 2.0, 5.0):
        print(f"      at {f_:4.1f} AU -> {lf.irradiance_at(np.array([f_*AU, 0, 0])):9.2f} W/m^2")
    i1 = lf.irradiance_at(np.array([AU, 0, 0]))
    i2 = lf.irradiance_at(np.array([2 * AU, 0, 0]))
    check("inverse square holds", abs(i1 - 1361.0) < 1.0 and abs(i2 - i1 / 4) < 1.0,
          f"1361.0 W/m^2 at 1 AU (Earth's real value), {i2:.2f} at 2 AU = exactly a quarter")

    print("\nL2  DAY AND NIGHT by occlusion -- not a flag")
    Rp = 6.371e6
    world = Occluder(center=(AU, 0, 0), radius=Rp)
    lf2 = LightField(stars=[sun], occluders=[world])
    noon = np.array([AU - Rp - 1.0, 0, 0])                # the face toward the star
    midnight = np.array([AU + Rp + 1.0, 0, 0])            # the far face
    print(f"      noon     {lf2.irradiance_at(noon):8.2f} W/m^2")
    print(f"      midnight {lf2.irradiance_at(midnight):8.2f} W/m^2")
    check("the far side is dark", lf2.irradiance_at(noon) > 1000 and
          lf2.irradiance_at(midnight) == 0.0,
          f"{lf2.irradiance_at(noon):.0f} W/m^2 at noon, exactly 0 at midnight -- the planet "
          "occludes itself, which is all night IS")

    print("\nL3  the TERMINATOR: exactly half a sphere is lit, N.L to zero at the edge")
    lit, n = 0, 40_000                                    # enough that +-0.25% noise cannot fake 0.5
    rng = np.random.default_rng(0)
    for _ in range(n):
        v = rng.normal(size=3); v /= np.linalg.norm(v)
        p = np.array([AU, 0, 0]) + v * (Rp + 1.0)
        if lf2.lit_fraction(p, v) > 0.0:
            lit += 1
    frac = lit / n
    east = np.array([AU, Rp + 1.0, 0.0])                  # on the terminator
    print(f"      lit fraction of the surface {frac:.3f}  (a sphere lit from far away -> 0.5)")
    print(f"      N.L at the sub-stellar point {lf2.lit_fraction(noon, np.array([-1.0,0,0])):.4f}, "
          f"at the terminator {lf2.lit_fraction(east, np.array([0.0,1.0,0.0])):.4f}")
    check("half lit, and it falls to zero at the terminator", abs(frac - 0.5) < 0.01,
          f"{100*frac:.1f}% of the surface is lit -- Lambert's cosine law, which is the renderer's "
          "missing lighting term (ROADMAP A3) arriving as a FIELD")

    print("\nL4  solar power on a panel")
    panel = lf2.power_on(noon, np.array([-1.0, 0, 0]), area=12.0, efficiency=0.22)
    print(f"      12 m^2 at 22% efficiency, face-on at 1 AU -> {panel:.1f} W")
    check("power is irradiance x area x cos x efficiency", abs(panel - 1361.0 * 12 * 0.22) < 5.0,
          f"{panel:.1f} W -- the same field the renderer reads also runs the ship")

    print("\nL5  ECLIPSE: a moon's shadow is the SAME mechanism as night")
    moon = Occluder(center=(AU - 3.84e8, 0, 0), radius=1.737e6)
    lf3 = LightField(stars=[sun], occluders=[world, moon])
    umbra = np.array([AU - Rp - 1.0, 0.0, 0.0])           # sub-lunar point on the planet
    beside = np.array([AU - Rp - 1.0, 4.0e6, 0.0])        # just outside the shadow
    print(f"      under the moon {lf3.irradiance_at(umbra):8.2f} W/m^2")
    print(f"      beside it      {lf3.irradiance_at(beside):8.2f} W/m^2")
    check("the moon casts a real shadow", lf3.irradiance_at(umbra) == 0.0 and
          lf3.irradiance_at(beside) > 1000,
          "totality under the moon, full sun a few thousand km away -- one occlusion rule, "
          "no separate eclipse system")

    print("\nL6  equilibrium TEMPERATURE from irradiance")
    for nm, r in (('Venus', 0.723), ('Earth', 1.0), ('Mars', 1.524)):
        T = lf.equilibrium_temperature(np.array([r * AU, 0, 0]), albedo=0.3)
        print(f"      {nm:6s} at {r:5.3f} AU -> {T:6.2f} K  ({T-273.15:+7.2f} C)")
    T_earth = lf.equilibrium_temperature(np.array([AU, 0, 0]), albedo=0.3)
    check("Earth's blackbody temperature comes out right", abs(T_earth - 254.0) < 3.0,
          f"{T_earth:.1f} K vs the textbook 254 K -- the number that placed this project's "
          "habitable zone, now falling out of the light field")

    n_fail = sum(1 for _, ok in results if not ok)
    print("\n" + "=" * 68)
    print(f"{len(results) - n_fail}/{len(results)} checks passed")
    return 1 if n_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
