"""dig — the DIG verb, and its clock scales with the density of what you are cutting.

The first verb a player's hand touches, built entirely on the primitives already here:

  IT IS A VERB          a membranes.Verb -- two states (intact, excavated) and a dial. The dial
                        is scoop progress, and INPUT drives it (holding the dig button). You do
                        not animate a scoop; you exhibit its two ends and let the world compute
                        the in-between (DESIGN section 3 / membranes.py).
  ITS CLOCK IS DENSITY  the dial advances at the density-scaled clock. A membrane made of a
                        material carries that material's density (a ratio), so scoop.clock_rate()
                        = sqrt(density) -- the free-fall law. Denser material has a FASTER
                        internal clock (it re-settles quicker, more mass per volume), so an
                        action done AGAINST it makes less net progress per second:
                            dig_rate = power / scoop.clock_rate() = power / sqrt(relative density).
                        Loose topsoil comes away fast; dense bedrock slow; a kimberlite pipe
                        slowest. One rule, every material, every planet.
  INPUT -> YIELD        holding the button advances the dial; when it reaches 1 a scoop is
                        removed and yields whatever planet_layers says was there -- valued by the
                        TRAINED economy. Input -> verb -> density clock -> yield, end to end.

This is the cause-and-effect a player can actually touch, and it is the same density term the
membrane carries for its own clock -- relative mass and relative scale, used here to say how
long a scoop takes.
"""
from __future__ import annotations

import numpy as np

from core.membranes import Membrane

# Material densities (kg/m^3). The dig only ever uses them RELATIVE to a reference, which makes
# them a relative-mass term (the operator's identity) -- dimensionless, root at the loosest.
REF_MATERIAL = 'topsoil'
MATERIAL_DENSITY = {
    'air': 1.0, 'topsoil': 1300.0, 'subsoil': 1500.0, 'bedrock': 2700.0, 'crust': 2900.0,
    'mantle': 3300.0, 'core': 5500.0, 'ocean': 1025.0,
    'gold_placer': 1800.0, 'iron_ore': 5000.0, 'coal': 1400.0, 'copper_vein': 4000.0,
    'diamond': 3500.0,
}
REF_DENSITY = MATERIAL_DENSITY[REF_MATERIAL]
SCOOP_SECONDS = 1.5             # baseline time to dig one scoop of the reference material at power 1

# Repose angle of the LOOSENED material (degrees): soil slumps low, rock rubble stands steep.
# This is the friction the freed grains settle under once a scoop fractures.
REPOSE_ANGLE = {
    'air': 0.0, 'ocean': 0.0, 'topsoil': 32.0, 'subsoil': 34.0, 'bedrock': 40.0, 'crust': 41.0,
    'mantle': 42.0, 'core': 43.0, 'gold_placer': 33.0, 'iron_ore': 38.0, 'coal': 35.0,
    'copper_vein': 39.0, 'diamond': 40.0,
}


def relative_density(material: str) -> float:
    """The material's density as a RATIO to the reference (topsoil = 1). Denser rock > 1."""
    return MATERIAL_DENSITY.get(material, REF_DENSITY) / REF_DENSITY


def scoop_membrane(material: str, parent: Membrane = None, scale: float = 0.5) -> Membrane:
    """A scoop-sized membrane MADE OF `material`, carrying its relative density so that
    scoop.clock_rate() is the density-scaled clock -- and a dig verb on it (intact -> excavated)."""
    m = Membrane('scoop', scale=scale, serial=f'SCOOP-{material}')
    m.prop(density=relative_density(material), material=material)
    if parent is not None:
        parent.add(m)
    m.state('intact', occupancy=1.0, loosened=0.0)
    m.state('excavated', occupancy=0.0, loosened=1.0)
    m.verb('dig', 'intact', 'excavated')
    return m


def dig_rate(scoop: Membrane, power: float = 1.0) -> float:
    """Dial advance per second: power / clock_rate. Uses the membrane's OWN clock_rate()
    (= sqrt(density)), inverted because the dig works against the material. Denser = slower."""
    return power / (scoop.clock_rate() * SCOOP_SECONDS)


def seconds_per_scoop(material: str, power: float = 1.0) -> float:
    return SCOOP_SECONDS * float(np.sqrt(relative_density(material))) / max(power, 1e-9)


def hold(material: str, seconds: float, power: float = 1.0) -> dict:
    """Simulate holding the dig button for `seconds` on `material`. Returns how far the dial got,
    how many whole scoops came loose, and the per-scoop time (set by the density clock)."""
    scoop = scoop_membrane(material)
    rate = dig_rate(scoop, power)                       # dial per second
    progress = rate * seconds                           # total scoops as a float
    return {
        'material': material,
        'relative_density': relative_density(material),
        'clock_rate': scoop.clock_rate(),               # sqrt(density) -- the membrane's own
        'seconds_per_scoop': seconds_per_scoop(material, power),
        'scoops_completed': int(progress),
        'dial': float(min(progress - int(progress), 1.0)),
        'verb_state_at_dial': scoop.apply('dig', min(progress - int(progress), 1.0)),
    }


def fracture_scoop(material: str, seed: int = 11) -> dict:
    """When a scoop COMPLETES, the loosened material fractures into free grains and falls --
    terrain_matter's real MuJoCo grain sim, driven by THIS material's density and repose (not
    hardcoded sand). Denser material -> denser grains that carry more momentum and settle
    harder. The dig verb's 'loosened' dimension, made physical. Returns grain facts + the arrays
    a render needs. Imports terrain_matter lazily so the verb/clock need no MuJoCo."""
    import math

    import core.terrain_matter as tm
    density = MATERIAL_DENSITY.get(material, REF_DENSITY)
    mu = math.tan(math.radians(REPOSE_ANGLE.get(material, 34.0)))
    heights = np.full((tm.N_SIDE, tm.N_SIDE), tm.H0, dtype=np.float64)
    live = np.zeros((tm.N_SIDE, tm.N_SIDE), dtype=bool)
    rng = np.random.default_rng(seed)
    cyc = tm.run_dig_cycle(heights, live, (2, 2), density, mu, rng)
    grain_mass = density * (4.0 / 3.0 * math.pi * tm.GRAIN_RADIUS ** 3)
    n_exit = tm.recoalesce(heights, live, cyc['freed_idx'], cyc['final_positions'],
                           grain_mass, density)
    seam = tm.seam_integrity(heights, cyc['mask'])
    return {
        'material': material, 'density': density, 'repose_deg': REPOSE_ANGLE.get(material, 34.0),
        'grains_freed': cyc['k_freed'], 'settled': cyc['settled_at'] is not None,
        'grains_exited': int(n_exit), 'seam_max_m': round(seam['max_discontinuity_m'], 3),
        'mass_moved_kg': round(cyc['k_freed'] * grain_mass, 1),
        '_mask': cyc['mask'], '_mid': cyc['mid_positions'], '_heights_after': heights,
    }


def fracture_strip(fr: dict, path: str = 'Saved/SplatEmit/dig_fracture.png'):
    """before | during (grains flying) | after (recoalesced) -- SEE the material come loose.
    Reuses terrain_matter's own splat render; optics are sand as a stand-in (the MOTION is the
    proof, and it is material-agnostic)."""
    import core.terrain_matter as tm
    from core.matter_items import load_library, register_material
    from core.splat_emit import hstack_strip
    from pathlib import Path
    lib = load_library(); ext = register_material(lib, 'sand')
    rng = np.random.default_rng(11)
    flat = np.full((tm.N_SIDE, tm.N_SIDE), tm.H0, dtype=np.float64)
    zero = np.zeros((tm.N_SIDE, tm.N_SIDE), dtype=bool)
    b, _ = tm.render_snapshot(flat, zero, None, ext, rng, 'before')
    d, _ = tm.render_snapshot(flat, fr['_mask'], fr['_mid'], ext, rng, 'during')
    a, _ = tm.render_snapshot(fr['_heights_after'], zero, None, ext, rng, 'after')
    strip = hstack_strip([b, d, a], ['intact', f"fracture ({fr['material']}, n={fr['grains_freed']})",
                                     'settled'])
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    strip.save(path)
    return path


def dig_at(planet, lat_deg: float, lon_deg: float, depth_m: float, seconds: float,
           power: float = 1.0) -> dict:
    """Dig at a real point on a LayeredPlanet: probe what is there, dig it at the density clock,
    and -- if a scoop completes -- report the yield (valued by the trained economy). Input ->
    verb -> density clock -> yield."""
    from core.planet_layers import DEPOSITS
    r = planet.probe(lat_deg, lon_deg, depth_m)
    material = 'air' if r['state'] == 'void' else (r['deposit'] or r['layer'])
    h = hold(material, seconds, power)
    out = {**h, 'layer': r['layer'], 'state': r['state'], 'void': r['void'], 'yield': None}
    if h['scoops_completed'] >= 1 and r['state'] != 'void' and r['deposit'] and r['grade'] > 0.15:
        dep = next((d for d in DEPOSITS if d.name == r['deposit']), None)
        if dep is not None:
            # one scoop of ~1 m^3 of ore -> mineral won -> credits (the trained price)
            ore_kg = MATERIAL_DENSITY.get(r['layer'], REF_DENSITY) * (h['scoops_completed'])
            won = r['grade'] * ore_kg * dep.mineral_frac
            out['yield'] = {'deposit': r['deposit'], 'mineral_kg': won,
                            'credits': won * dep.price}
    return out


def _main() -> int:
    import argparse
    import sys
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    ap = argparse.ArgumentParser(description='the dig verb with its density-scaled clock')
    ap.add_argument('--seconds', type=float, default=3.0)
    ap.add_argument('--seed', type=int, default=3)
    ap.add_argument('--render', action='store_true', help='render the fracture strip')
    a = ap.parse_args()

    print("  === the dig verb: two states + a dial (membranes.Verb) ===")
    s = scoop_membrane('bedrock')
    v = s.verbs['dig']
    print(f"    verb 'dig' moves: {v.differs_in()}   lo=intact hi=excavated")
    for t in (0.0, 0.5, 1.0):
        st = s.apply('dig', t)
        print(f"    dial {t:>3} -> occupancy {st['occupancy']:.2f} loosened {st['loosened']:.2f}")

    print(f"\n  === the clock scales with density: hold the button {a.seconds:.0f}s on each ===")
    print(f"  {'material':12} {'rel.density':>11} {'clock=√ρ':>9} {'s/scoop':>8} {'scoops in '+str(int(a.seconds))+'s':>13}")
    for mat in ('topsoil', 'subsoil', 'bedrock', 'crust', 'mantle', 'iron_ore', 'diamond'):
        h = hold(mat, a.seconds)
        print(f"    {mat:12} {h['relative_density']:>11.2f} {h['clock_rate']:>9.2f} "
              f"{h['seconds_per_scoop']:>8.2f} {h['scoops_completed']:>10} + {h['dial']:.2f} dial")
    print("    ^ loose topsoil comes away fast; dense rock slow -- the density clock, on the verb")

    print("\n  === input -> verb -> density clock -> YIELD (a real dig into a planet) ===")
    from core.planet_layers import LayeredPlanet
    from core.mining import find_deposit_site
    lp = LayeredPlanet.earthlike(seed=a.seed)
    site = find_deposit_site(lp, 'iron_ore', 30.0, seed=a.seed + 1, land_only=True) or (35.0, 200.0)
    d = dig_at(lp, site[0], site[1], 30.0, seconds=8.0)
    print(f"    dig at {tuple(round(x,1) for x in site)}, 30 m ({d['layer']}, {d['material']}): "
          f"{d['seconds_per_scoop']:.2f}s/scoop -> {d['scoops_completed']} scoops in 8s")
    if d['yield']:
        y = d['yield']
        print(f"    yielded {y['mineral_kg']:,.0f} kg {y['deposit']} = {y['credits']:,.0f} credits "
              f"(TRAINED price)")
    else:
        print(f"    (barren rock this scoop -- overburden)")

    print("\n  === and the scoop FRACTURES: real grain physics, driven by the material density ===")
    for mat in ('topsoil', 'bedrock'):
        fr = fracture_scoop(mat, seed=11)
        print(f"    {mat:9} (rho {fr['density']:.0f}, repose {fr['repose_deg']:.0f} deg): "
              f"{fr['grains_freed']} grains freed, settled={fr['settled']}, "
              f"exited={fr['grains_exited']}, {fr['mass_moved_kg']:,.0f} kg moved, "
              f"seam {fr['seam_max_m']:.2f} m")
    print("    ^ same verb, same clock -- denser rock throws denser, heavier grains")

    if d['state'] != 'void' and d['scoops_completed'] >= 1:
        fr = fracture_scoop(d['material'], seed=a.seed)
        print(f"\n    the iron dig's scoop fractured: {fr['grains_freed']} grains of "
              f"{fr['material']} (rho {fr['density']:.0f}) came loose and fell")
        if a.render:
            path = fracture_strip(fr)
            print(f"    wrote {path} (intact | fracture | settled)")
    return 0


if __name__ == '__main__':
    raise SystemExit(_main())
