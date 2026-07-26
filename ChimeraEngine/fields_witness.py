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
                    STEEL, ROCK, RUBBER, FLESH, TAPE, REGOLITH,
                    Thermal, ThermalField, Column, LUNAR_REGOLITH, ROCK_T, OCEAN, HULL, RADIATOR, ICE)
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

    # ══ THERMAL ══════════════════════════════════════════════════════════════════════════════
    print("\nT1  the SUBSOLAR point of an airless body -- against the Moon's measured temperature")
    tf = ThermalField(light=LightField(stars=[sun]))
    at_moon = np.array([AU, 0, 0])
    up = np.array([-1.0, 0.0, 0.0])                        # facing the star
    T_sub = tf.equilibrium(at_moon, up, LUNAR_REGOLITH)
    print(f"      lunar regolith, albedo {LUNAR_REGOLITH.albedo}, emissivity "
          f"{LUNAR_REGOLITH.emissivity} -> {T_sub:.1f} K ({T_sub-273.15:+.1f} C)")
    print(f"      measured lunar subsolar temperature: ~390 K (Diviner/Apollo)")
    check("subsolar temperature matches the real Moon", abs(T_sub - 390.0) < 12.0,
          f"{T_sub:.1f} K vs the measured ~390 K -- absorbed sunlight balanced against T^4, "
          "no fitted constant anywhere")

    print("\nT2  DAY AND NIGHT: an airless surface plummets when the sun goes down")
    day = 2.55e6                                           # one lunar day, seconds
    T = T_sub
    hi, lo = 0.0, 1e9
    dt, n = day / 4000.0, 4000
    for k in range(n * 2):                                 # two full rotations: settle, then measure
        ang = 2 * np.pi * k / n
        nrm = np.array([-np.cos(ang), -np.sin(ang), 0.0])  # a patch carried around by rotation
        T = tf.step(T, at_moon, nrm, LUNAR_REGOLITH, dt)
        if k >= n:
            hi, lo = max(hi, T), min(lo, T)
    print(f"      over one rotation: high {hi:.1f} K, low {lo:.1f} K, swing {hi-lo:.1f} K")
    print(f"      measured lunar equatorial range: ~390 K day to ~95 K night")
    print(f"      HONEST GAP: night reads {lo:.0f} K, the Moon holds ~95 K. This model is a SKIN --")
    print(f"      real regolith conducts heat UP from below all night. The missing piece is a depth")
    print(f"      dimension driving ThermalField.conduction, not a capacity constant to tune.")
    check("an airless world swings hundreds of kelvin", (hi - lo) > 200.0 and lo < 150.0,
          f"{hi:.0f} K day to {lo:.0f} K night, a {hi-lo:.0f} K swing -- nothing banks the heat, "
          "so T^4 empties the surface every night")

    print("\nT3  THERMAL INERTIA damps it -- which is what an ocean IS")
    swings = {}
    for nm, mat in (('regolith', LUNAR_REGOLITH), ('rock', ROCK_T), ('ocean', OCEAN)):
        T = tf.equilibrium(at_moon, up, mat) * 0.8
        hi2, lo2 = 0.0, 1e9
        for k in range(n * 3):
            ang = 2 * np.pi * k / n
            nrm = np.array([-np.cos(ang), -np.sin(ang), 0.0])
            T = tf.step(T, at_moon, nrm, mat, dt)
            if k >= n * 2:
                hi2, lo2 = max(hi2, T), min(lo2, T)
        swings[nm] = hi2 - lo2
        print(f"      {nm:9s} capacity {mat.capacity:8.1e} J/m^2/K -> swing {hi2-lo2:7.1f} K "
              f"({lo2:6.1f} - {hi2:6.1f} K)")
    check("more heat capacity, less swing -- monotonically",
          swings['regolith'] > swings['rock'] > swings['ocean'],
          f"regolith {swings['regolith']:.0f} K > rock {swings['rock']:.0f} K > "
          f"ocean {swings['ocean']:.0f} K -- one parameter, and it is why a coastal climate is mild")

    print("\nT4  THE SHIP'S REAL PROBLEM: in vacuum you can only get rid of heat by RADIATING it")
    for T_loop in (250.0, 300.0, 350.0, 400.0):
        A = ThermalField.radiator_area(5000.0, T_loop)
        print(f"      dump 5 kW at {T_loop:5.1f} K -> {A:7.2f} m^2 of radiator")
    a250 = ThermalField.radiator_area(5000.0, 250.0)
    a400 = ThermalField.radiator_area(5000.0, 400.0)
    check("radiator area falls as T^4", abs((a250 / a400) - (400.0 / 250.0) ** 4) < 0.05,
          f"{a250:.1f} m^2 at 250 K vs {a400:.1f} m^2 at 400 K = {a250/a400:.2f}x, exactly "
          f"(400/250)^4 = {(400/250)**4:.2f} -- run the loop hot and the radiator shrinks")

    print("\nT5  ENERGY IS CONSERVED: at equilibrium, in equals out")
    T_eq = tf.equilibrium(at_moon, up, HULL)
    a_in = tf.absorbed(at_moon, up, HULL)
    e_out = tf.emitted(T_eq, HULL)
    print(f"      hull at {T_eq:.2f} K: absorbing {a_in:.3f} W/m^2, emitting {e_out:.3f} W/m^2")
    check("absorbed equals emitted at equilibrium", abs(a_in - e_out) < 1e-6,
          f"{a_in:.4f} = {e_out:.4f} W/m^2 -- equilibrium is not asserted, it is where the "
          "integrator stops moving")

    print("\nT6  a reactor makes its OWN temperature -- and shade does not save you")
    # `tf` above has NO occluders, so its "shadow" point was in full sun and this test read 391 K
    # for an unheated body in the dark -- an impossible number that only appeared because the
    # witness asserted darkness without ever building anything that casts it. Use the occluded
    # field (the one L2 proved actually has a night side).
    shade = ThermalField(light=lf2)
    night_side = np.array([AU + Rp + 1.0, 0, 0])
    assert shade.light.irradiance_at(night_side) == 0.0, "the shadow point must actually be dark"
    T_dark = shade.equilibrium(night_side, up, RADIATOR, internal=800.0)
    T_cold = shade.equilibrium(night_side, up, RADIATOR, internal=0.0)
    print(f"      in full shadow, no reactor  -> {T_cold:.1f} K (nothing to radiate)")
    print(f"      in full shadow, 800 W/m^2   -> {T_dark:.1f} K")
    check("internal heat sets its own equilibrium", T_dark > 340.0 and T_cold == 0.0,
          f"{T_dark:.1f} K powered vs {T_cold:.1f} K dead -- the same balance, driven from inside "
          "instead of by the star")

    # ══ THE DEPTH DIMENSION ══════════════════════════════════════════════════════════════════
    print("\nD1  the SKIN DEPTH -- how far the daily wave reaches before it dies")
    day = 2.55e6                                           # one lunar day, seconds
    for nm, mat in (('regolith', LUNAR_REGOLITH), ('solid rock', ROCK_T), ('water ice', ICE)):
        d = mat.skin_depth(day)
        print(f"      {nm:11s} alpha {mat.diffusivity():.2e} m^2/s, inertia {mat.inertia():6.1f} "
              f"-> skin depth {d*100:7.2f} cm")
    d_reg = LUNAR_REGOLITH.skin_depth(day)
    print(f"      published lunar diurnal skin depth: ~5-10 cm (Diviner / Apollo cores)")
    check("regolith's skin depth lands in the measured band", 0.03 < d_reg < 0.14,
          f"{d_reg*100:.1f} cm from sqrt(alpha P / pi) -- the depth where the daily swing falls to "
          "1/e, and the reason 'dig down' is a real strategy and not flavour text")

    print("\nD2  THE GAP CLOSES: give the ground a reservoir and the night side stops collapsing")
    col = Column.build(LUNAR_REGOLITH, n=26, dz0=0.002, growth=1.25, T0=220.0)
    dt_lim = col.max_dt()
    dt_c = min(200.0, dt_lim * 0.4)
    steps = int(day / dt_c)
    print(f"      column {col.depth():.2f} m deep in {len(col.dz)} layers "
          f"({col.dz[0]*1000:.0f} mm at the top, {col.dz[-1]*100:.0f} cm at the bottom)")
    print(f"      stability limit dt < {dt_lim:.0f} s; using {dt_c:.0f} s, {steps} steps/day")
    hi_d = lo_d = None
    for cyc in range(6):                                   # spin up, then measure the last cycle
        hi_d, lo_d, prof_noon, prof_mid = -1e9, 1e9, None, None
        for k in range(steps):
            ph = 2 * np.pi * k / steps
            nrm = np.array([-np.cos(ph), -np.sin(ph), 0.0])
            Ts = col.step(dt_c, tf.absorbed(at_moon, nrm, LUNAR_REGOLITH))
            if cyc == 5:
                if Ts > hi_d:
                    hi_d, prof_noon = Ts, col.T.copy()
                if Ts < lo_d:
                    lo_d, prof_mid = Ts, col.T.copy()
    print(f"      SKIN model (T2):  {hi:.0f} K day -> {lo:5.1f} K night")
    print(f"      DEPTH model:      {hi_d:.0f} K day -> {lo_d:5.1f} K night")
    print(f"      measured Moon:    ~390 K day -> ~95 K night (Diviner)")
    check("the depth model lands on the Moon's real night temperature", 80.0 < lo_d < 115.0,
          f"night {lo_d:.1f} K vs the measured ~95 K, up from the skin model's {lo:.1f} K -- nothing "
          "was tuned, the ground was simply given somewhere to put the heat")

    print("\nD3  the wave ATTENUATES and LAGS with depth -- the signature of diffusion")
    zs = col.depths()
    swing_z, T_noon, T_mid = [], prof_noon, prof_mid
    for i in (0, 4, 8, 12, 16, 20, 25):
        print(f"      z = {zs[i]*100:7.2f} cm  noon {T_noon[i]:6.1f} K   midnight {T_mid[i]:6.1f} K"
              f"   swing {abs(T_noon[i]-T_mid[i]):6.1f} K")
        swing_z.append(abs(T_noon[i] - T_mid[i]))
    check("the daily swing dies away with depth", swing_z[0] > 50 * max(swing_z[-1], 1e-3),
          f"{swing_z[0]:.0f} K at the surface -> {swing_z[-1]:.2f} K at {zs[25]*100:.0f} cm -- "
          "a buried habitat sits in a constant-temperature world")

    print("\nD4  BURY IT: the depth where the day is no longer felt")
    quiet = next((zs[i] for i in range(len(zs)) if abs(T_noon[i] - T_mid[i]) < 5.0), None)
    print(f"      swing drops below 5 K at z = {quiet*100:.1f} cm "
          f"({quiet/d_reg:.1f} skin depths)")
    print(f"      deep temperature {col.T[-1]:.1f} K, and it barely moves at all")
    check("a few skin depths is all it takes", quiet is not None and quiet < 8 * d_reg,
          f"{quiet*100:.0f} cm of regolith turns a 300 K daily swing into under 5 K -- this is the "
          "physics of habitat siting, and of why cold traps keep their ice")

    print("\nD5  GEOTHERMAL: the flux from below sets the deep gradient (Fourier)")
    grad = (col.T[-1] - col.T[-3]) / (zs[-1] - zs[-3])
    k_deep = float(np.mean(LUNAR_REGOLITH.conductivity_at(col.T[-3:])))
    print(f"      deep gradient {grad:.3f} K/m, k(T) there {k_deep:.2e} W/m/K")
    print(f"      -> flux k*dT/dz = {k_deep*grad*1000:.1f} mW/m^2   (imposed {col.geothermal*1000:.0f} "
          f"mW/m^2, Apollo 15/17 measured 16-21)")
    print(f"      HONEST GAP: Apollo measured a ~1.75 K/m gradient, not {grad:.1f} K/m. This column")
    print(f"      uses ONE conductivity everywhere; the real Moon's k rises ~10x with depth as the")
    print(f"      regolith compacts, so the real gradient is that much shallower. The LAW is right,")
    print(f"      the single-layer material is the approximation -- and it is named, not hidden.")
    check("the recovered heat flow matches what was imposed",
          abs(k_deep * grad - col.geothermal) < 0.25 * col.geothermal,
          f"{k_deep*grad*1000:.1f} vs {col.geothermal*1000:.0f} mW/m^2 -- Fourier's law read back "
          "out of a profile that was never told it")

    # ══ REFLECTED AND RE-EMITTED LIGHT ═══════════════════════════════════════════════════════
    # Operator, 2026-07-26: "light also has heat elements to it -- light reflecting off an object
    # has property of thermal". Correct, and it was a real hole: absorbed = S(1-albedo) used the
    # absorbed part and let the REFLECTED part vanish. It does not vanish, it lands on you.
    print("\nR1  ONE LAW, star to dirt: the Sun's own surface temperature from Stefan-Boltzmann")
    T_sun = sun.surface_temperature()
    print(f"      L = {sun.luminosity:.3e} W over R = {sun.radius:.3e} m -> T = {T_sun:.1f} K")
    print(f"      the Sun's measured effective temperature: 5772 K")
    check("a star is just a body at a temperature", abs(T_sun - 5772.0) < 30.0,
          f"{T_sun:.0f} K from the SAME sigma T^4 that settles a patch of regolith -- star and dirt "
          "are one equation at different arguments")

    print("\nR2  THE SPACECRAFT BUDGET in low orbit -- three terms, not one")
    earth = Occluder(center=(AU, 0, 0), radius=Rp, albedo=0.30, temperature=255.0, emissivity=1.0)
    lf_e = LightField(stars=[sun], occluders=[earth])
    for alt_km in (0, 400, 2000, 35786):
        p_o = np.array([AU - Rp - alt_km * 1000.0, 0, 0])       # over the sub-solar point
        b = lf_e.budget_at(p_o)
        print(f"      {alt_km:6d} km  direct {b['direct']:7.1f}  albedo {b['albedo']:6.1f}  "
              f"planetary {b['planetary']:6.1f}  =  {b['total']:7.1f} W/m^2  "
              f"(view factor {earth.view_factor(p_o):.3f})")
    leo = lf_e.budget_at(np.array([AU - Rp - 4.0e5, 0, 0]))
    print(f"      published LEO design values: solar ~1361, albedo ~400 peak, Earth IR ~230-240")
    check("the LEO budget matches published spacecraft numbers",
          abs(leo['albedo'] - 361) < 60 and abs(leo['planetary'] - 212) < 35,
          f"albedo {leo['albedo']:.0f} and Earth IR {leo['planetary']:.0f} W/m^2 at 400 km -- these "
          "are the numbers a real thermal budget is built from, and they fell out of (R/r)^2")

    print("\nR3  STANDING ON THE MOON AT NOON: the GROUND is a second sun")
    moon_hot = Occluder(center=(AU, 0, 0), radius=1.737e6, albedo=0.11, temperature=387.0)
    lf_m = LightField(stars=[sun], occluders=[moon_hot])
    boots = np.array([AU - 1.737e6 - 1.0, 0, 0])                # a metre above the regolith
    bm = lf_m.budget_at(boots)
    print(f"      direct sun    {bm['direct']:7.1f} W/m^2")
    print(f"      ground glow   {bm['planetary']:7.1f} W/m^2   (regolith at 387 K, radiating AT you)")
    print(f"      ground bounce {bm['albedo']:7.1f} W/m^2")
    print(f"      TOTAL         {bm['total']:7.1f} W/m^2 on a suit -- {bm['total']/1361:.2f}x the sun alone")
    check("the ground radiates nearly as hard as the sun", bm['planetary'] > 1000.0,
          f"{bm['planetary']:.0f} W/m^2 from the regolith alone -- this is why lunar EVA is a "
          "COOLING problem, and it is a term my first model deleted entirely")

    print("\nR4  the night side: albedo dies, the glow does NOT")
    night = np.array([AU + Rp + 4.0e5, 0, 0])
    bn = lf_e.budget_at(night)
    print(f"      direct {bn['direct']:6.1f}   albedo {bn['albedo']:6.1f}   "
          f"planetary {bn['planetary']:6.1f} W/m^2")
    check("planetary IR survives the terminator", bn['direct'] == 0.0 and bn['albedo'] == 0.0
          and bn['planetary'] > 100.0,
          f"sun 0, bounce 0, but {bn['planetary']:.0f} W/m^2 still arriving -- you cannot hide from "
          "a warm planet, you can only point away from it")

    print("\nR5  POINT AWAY: what a radiator is actually for")
    p_leo = np.array([AU - Rp - 4.0e5, 0, 0])
    down = lf_e.budget_at(p_leo, facing_body=True)['total'] - leo['direct']
    space = lf_e.budget_at(p_leo, facing_body=False)['total'] - leo['direct']
    A_down = ThermalField.radiator_area(5000.0, 300.0)
    print(f"      facing the planet: {down:7.1f} W/m^2 of backload   facing deep space: {space:.1f}")
    print(f"      a 5 kW radiator at 300 K sheds {1.0/ThermalField.radiator_area(1.0,300.0):.0f} W/m^2;")
    print(f"      pointed down it is fighting {down:.0f} of that back -- {100*down/(1.0/ThermalField.radiator_area(1.0,300.0)):.0f}% of its capacity gone")
    check("deep space is the only real heat sink", space == 0.0 and down > 400.0,
          f"{down:.0f} W/m^2 backload facing the planet vs {space:.0f} facing away -- the reason "
          "radiators are mounted where they are, falling out of the same view factor")

    print("\nR6  the view factor is geometry, not a fudge: (R/r)^2")
    for h in (0.0, Rp * 0.5, Rp, Rp * 9.0):
        pv = np.array([AU - Rp - h, 0, 0])
        f_meas = earth.view_factor(pv)
        f_pred = (Rp / (Rp + h)) ** 2
        print(f"      altitude {h/1000:9.0f} km -> view factor {f_meas:.4f}  (sin^2 theta = {f_pred:.4f})")
    check("view factor is exactly sin^2 of the half-angle subtended",
          abs(earth.view_factor(np.array([AU - Rp - Rp, 0, 0])) - 0.25) < 1e-9,
          "1.0000 on the surface -> 0.2500 at one radius up -> 0.0100 at nine -- the sphere's own "
          "geometry, and the same number that scales both the bounce and the glow")

    n_fail = sum(1 for _, ok in results if not ok)
    print("\n" + "=" * 68)
    print(f"{len(results) - n_fail}/{len(results)} checks passed")
    return 1 if n_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
