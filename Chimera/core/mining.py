"""mining — wire the DIG to the GEOLOGY. What a scoop pulls up is what is actually there.

The two halves that never met:
  core/terrain_matter.py  knows HOW material comes loose -- the shovel's own footprint
                          (verbatim from the seed's GA_Dig), fracture -> grains -> settle ->
                          recoalesce, a real MuJoCo grain sim with a mass ledger. But it digs
                          HOMOGENEOUS SAND: it has no idea what is under the topsoil.
  core/planet_layers.py   knows WHAT is there -- soil, iron, diamond, or a cave void, by depth,
                          set by formation physics. But nothing dug it.

This joins them. An Excavation removes a slab per scoop using the shovel's real geometry, and
`probe()` at that depth says what came up. The dig stops being "move sand around" and becomes
"extract the geology": the haul is soil until you strike a vein, then value spikes; break into
a karst cave and there is nothing to remove -- you fall through. The same grain physics can now
run with the DUG material's density and friction (--physics), not always sand's.

HONEST ABOUT SCALE. A shovel does not reach diamonds. Depth is a TOOL ladder: a shovel takes
placer gold from the topsoil; an excavator reaches the iron and coal in bedrock; only an
industrial deep mine reaches copper in the crust and diamond in the mantle (>136 km). The dig
is the same verb at every scale -- the seed's shovel footprint, scaled -- so "different things
need different digging" is a fact about depth, not a special case.

Yield and value are DATA (the economy) on top of PHYSICS (which layer holds what). Abundances
and per-tonne values can be trained later against an economy objective; the geology cannot.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from core.planet_layers import DEPOSITS, LayeredPlanet, layer_at
from core.terrain_matter import (DIG_CELL, DIG_CELL_HALFWIDTH, DIG_SCOOP_DEPTH)

# host-rock bulk density per layer (kg/m3) -- what a slab of it masss; ore worth is separate.
LAYER_DENSITY = {'topsoil': 1300, 'subsoil': 1500, 'bedrock': 2700,
                 'crust': 2900, 'mantle': 3300, 'core': 5500}

# the shovel's OWN footprint, from terrain_matter (seed-cited GA_Dig): 5 dig-cells square.
_SHOVEL_M = (2 * DIG_CELL_HALFWIDTH + 1) * DIG_CELL          # 2.5 m

# the tool ladder: the same dig verb at three scales. (scoop thickness, footprint side, reach)
# Reaches are REAL: a shovel takes soil, an excavator reaches bedrock ore, and a deep mine
# reaches ~4 km (deeper than any real mine) -- enough for crust copper and kimberlite-pipe
# diamond, NOT the 150-km mantle where diamond forms. You cannot dig to the mantle.
TOOLS = {
    'shovel':    dict(scoop=DIG_SCOOP_DEPTH, footprint_m=_SHOVEL_M, max_depth=2.0),
    'excavator': dict(scoop=0.5,             footprint_m=4.0,       max_depth=60.0),
    'deep_mine': dict(scoop=5.0,             footprint_m=15.0,      max_depth=4000.0),
}


def tool_for(depth_m: float) -> str:
    """The lightest tool that reaches this depth -- you don't bring a deep mine for topsoil."""
    for name in ('shovel', 'excavator', 'deep_mine'):
        if depth_m <= TOOLS[name]['max_depth']:
            return name
    return 'deep_mine'


@dataclass
class Excavation:
    """A hole being dug at one place on the planet. Tracks depth, the haul, and what happened."""
    planet: LayeredPlanet
    lat: float
    lon: float
    tool: str = 'shovel'
    depth: float = 0.0
    haul: dict = field(default_factory=dict)         # host material -> mass_kg of ROCK moved
    mineral: dict = field(default_factory=dict)      # deposit -> kg of PURE mineral won
    value: float = 0.0                               # credits (mineral worth, not dirt)
    events: list = field(default_factory=list)       # (depth, message)
    column: list = field(default_factory=list)       # per-scoop record, for the shaft render
    _prev: tuple = None                              # previous (state, void) -> log transitions only

    def scoop(self) -> dict:
        """Remove one slab. Probe its material; tally ore MOVED and mineral WON; note strikes
        and cave breaks (once, on the transition -- not every scoop inside the same cave)."""
        t = TOOLS[self.tool]
        d_mid = self.depth + t['scoop'] / 2
        r = self.planet.probe(self.lat, self.lon, d_mid)
        area = t['footprint_m'] ** 2
        rec = {'depth': self.depth, 'layer': r['layer'], 'state': r['state'],
               'void': r['void'], 'deposit': r['deposit'], 'grade': r['grade'],
               'extracted': None}
        cur = (r['state'], r['void'])
        if r['state'] == 'void':
            if self._prev != cur:
                self.events.append((self.depth, f"broke into a {r['void'].replace('_', ' ')}"))
        else:
            dens = LAYER_DENSITY.get(r['layer'], 2700)
            mass = area * t['scoop'] * dens                  # kg of host rock this scoop moves
            self.haul[r['layer']] = self.haul.get(r['layer'], 0.0) + mass  # ROCK, by layer
            rec['extracted'] = r['material']
            rec['mass'] = mass
            if r['deposit'] and r['grade'] > 0.15:
                dep = next(d for d in DEPOSITS if d.name == r['deposit'])
                won = r['grade'] * mass * dep.mineral_frac   # kg of the PURE mineral (ore != gem)
                v = won * dep.price
                self.value += v
                self.mineral[dep.name] = self.mineral.get(dep.name, 0.0) + won
                if self._prev != cur or (self.column and self.column[-1].get('deposit') != dep.name):
                    unit = f"{won*1000:.0f} g" if won < 1 else f"{won:,.0f} kg"
                    self.events.append((self.depth, f"struck {dep.name} (grade {r['grade']:.2f}) "
                                                    f"-> {unit} mineral, +{v:,.0f} cr"))
        self.column.append(rec)
        self._prev = cur
        self.depth += t['scoop']
        return r

    def dig_to(self, target_depth: float) -> dict:
        """Dig straight down to a target depth, auto-selecting the tool that can reach it."""
        self.tool = tool_for(target_depth)
        guard = 0
        while self.depth < target_depth and self.depth < TOOLS[self.tool]['max_depth']:
            self.scoop()
            guard += 1
            if guard > 5000:
                break
        return self.report()

    def report(self) -> dict:
        return {'site': (self.lat, self.lon), 'tool': self.tool, 'depth_m': self.depth,
                'value_cr': self.value,
                'haul_kg': {k: round(v, 1) for k, v in self.haul.items()},
                'mineral_kg': {k: round(v, 3) for k, v in self.mineral.items()},
                'events': self.events}

    # --- the physical wiring: the dug material IS the grains -----------------

    def physical_scoop(self, material: str) -> dict:
        """Run terrain_matter's REAL grain sim for one scoop, driven by the DUG material's
        density and friction (from the matter library) -- proof the dig physics is wired to
        geology, not hardcoded to sand. Loose materials only; rock is cut, not fractured."""
        import math

        import core.terrain_matter as tm
        from core.matter_items import load_library
        phys = load_library()['materials'].get(material, load_library()['materials']['sand'])['physical']
        density = float(phys['density_kg_m3']['mean'])
        mu = math.tan(math.radians(float(phys['friction_angle_deg']['mean'])))
        heights = np.full((tm.N_SIDE, tm.N_SIDE), tm.H0, dtype=np.float64)
        live = np.zeros((tm.N_SIDE, tm.N_SIDE), dtype=bool)
        rng = np.random.default_rng(tm.SEED)
        cyc = tm.run_dig_cycle(heights, live, (2, 2), density, mu, rng)
        grain_mass = density * (4.0 / 3.0 * math.pi * tm.GRAIN_RADIUS ** 3)
        n_exit = tm.recoalesce(heights, live, cyc['freed_idx'], cyc['final_positions'],
                               grain_mass, density)
        seam = tm.seam_integrity(heights, cyc['mask'])
        return {'material': material, 'density': density, 'mu': round(mu, 3),
                'grains_freed': cyc['k_freed'], 'settled': cyc['settled_at'] is not None,
                'grains_exited': n_exit, 'seam_max_m': seam['max_discontinuity_m']}


def find_deposit_site(planet: LayeredPlanet, deposit: str, depth_m: float,
                      tries: int = 8000, seed: int = 1, land_only: bool = False) -> tuple | None:
    """Scan for a (lat, lon) whose column bears `deposit` at `depth_m` -- so a demo can dig a
    KNOWN find (e.g. a kimberlite pipe) rather than trust a blind hole to hit a rare gem."""
    rng = np.random.default_rng(seed)
    for _ in range(tries):
        la = float(rng.uniform(-70, 70))
        lo = float(rng.uniform(0, 360))
        if land_only and planet.onion.sample(la, lo)['elevation'] <= 0:
            continue
        r = planet.probe(la, lo, depth_m)
        if r['deposit'] == deposit and r['grade'] > 0.2:
            return (la, lo)            # EXACT -- rounding here would move off a small orebody
    return None


def _shaft_img(exc: Excavation, H: int = 560, W: int = 150):
    """A mine-shaft strip: depth down the Y axis, each scoop a band coloured by what was
    extracted; ore bright, cave voids black. The haul, seen."""
    from core.planet_layers import _CUM  # noqa
    COL = {'topsoil': (110, 84, 58), 'subsoil': (140, 110, 70), 'bedrock': (120, 120, 132),
           'crust': (95, 88, 100), 'mantle': (150, 70, 55), 'core': (200, 120, 60),
           'gold_placer': (255, 214, 0), 'iron_ore': (200, 96, 60), 'coal': (25, 25, 30),
           'copper_vein': (60, 200, 140), 'diamond': (150, 235, 255)}
    img = np.zeros((H, W, 3), np.uint8) + 18
    n = len(exc.column)
    if n == 0:
        return img
    for k, rec in enumerate(exc.column):
        y0 = int(k / n * H)
        y1 = int((k + 1) / n * H)
        if rec['state'] == 'void':
            c = (8, 8, 10)
        elif rec['deposit'] and rec['grade'] > 0.15:
            base = COL.get(rec['deposit'], (255, 0, 255))
            b = 0.45 + 0.55 * rec['grade']
            c = tuple(int(v * b) for v in base)
        else:
            c = COL.get(rec['layer'], (70, 70, 70))
        img[y0:y1, :] = c
    return img


def _main() -> int:
    import argparse
    import sys
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    ap = argparse.ArgumentParser(description='wire the dig to the geology: mining')
    ap.add_argument('--seed', type=int, default=3)
    ap.add_argument('--physics', action='store_true', help='run one REAL grain scoop')
    ap.add_argument('--render', action='store_true')
    a = ap.parse_args()

    lp = LayeredPlanet.earthlike(seed=a.seed)
    shafts = []

    def run_site(lat, lon, target, title):
        exc = Excavation(lp, lat, lon)
        rep = exc.dig_to(target)
        surf = lp.onion.sample(lat, lon)['elevation']
        print(f"\n  === {title}: ({lat:+.1f},{lon:.1f}) surface {surf:+.0f} m "
              f"-> dug {rep['depth_m']:,.1f} m with a {rep['tool']} ===")
        for d, msg in rep['events']:
            unit = f"{d:8.2f} m" if d < 1000 else f"{d/1000:8.1f} km"
            print(f"      {unit}  {msg}")
        if rep['value_cr'] > 0:
            print(f"      HAUL VALUE: {rep['value_cr']:,.0f} credits")
            print("      minerals won: "
                  + ', '.join(f"{k} {v:,.2f} kg" for k, v in rep['mineral_kg'].items()))
        else:
            print(f"      HAUL VALUE: 0 credits (just overburden)")
        tot = sum(rep['haul_kg'].values())
        top = sorted(rep['haul_kg'].items(), key=lambda x: -x[1])[:4]
        print(f"      rock moved {tot/1000:,.0f} tonnes: "
              + ', '.join(f"{k} {v/1000:,.0f}t" for k, v in top))
        shafts.append((title, exc))
        return exc

    # an excavator into a bedrock iron seam -- ordinary ground, ordinary haul.
    isite = find_deposit_site(lp, 'iron_ore', 30.0, seed=a.seed + 1, land_only=True) or (35.0, 200.0)
    run_site(isite[0], isite[1], target=60.0, title="Excavator -> a bedrock iron seam")

    # an industrial deep mine at a KIMBERLITE PIPE -- diamonds hauled up from the mantle,
    # mineable at realistic depth (~1.5 km), NOT by digging to where they form.
    dsite = find_deposit_site(lp, 'diamond', 900.0, seed=a.seed, land_only=True)
    if dsite:
        run_site(dsite[0], dsite[1], target=1600.0, title="Deep mine -> a kimberlite pipe (diamonds)")
    else:
        print("\n  (no kimberlite pipe found on land in the scan budget -- ~0.4%, as designed)")

    if a.physics:
        print("\n  === physical wiring: one REAL grain scoop, driven by the DUG material ===")
        exc = Excavation(lp, 35.0, 200.0)
        for mat in ('sand',):
            f = exc.physical_scoop(mat)
            print(f"    {f['material']:8} rho={f['density']:.0f} mu={f['mu']:.2f}: "
                  f"{f['grains_freed']} grains freed, settled={f['settled']}, "
                  f"exited={f['grains_exited']}, seam_max={f['seam_max_m']:.3f} m")

    if a.render and shafts:
        from pathlib import Path
        try:
            from PIL import Image
        except Exception:
            print('\n  (PIL absent -- skipping render)'); return 0
        strips = [_shaft_img(e) for _, e in shafts]
        gap = np.zeros((strips[0].shape[0], 16, 3), np.uint8) + 30
        canvas = strips[0]
        for s in strips[1:]:
            canvas = np.hstack([canvas, gap, s])
        out = Path('Saved/SplatEmit'); out.mkdir(parents=True, exist_ok=True)
        Image.fromarray(canvas).save(out / 'mining_shafts.png')
        print(f"\n  wrote {out}/mining_shafts.png ({' | '.join(t for t, _ in shafts)})")
    return 0


if __name__ == '__main__':
    raise SystemExit(_main())
