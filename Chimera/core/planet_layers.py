"""planet_layers — what is WITHIN and UNDER the onion: resources, and voids (caves).

Layering OVER the membrane is `sample()` on the surface (the stud an object attaches to).
This module does the other two the operator named: things EMBEDDED WITHIN the layers (ore,
gems -- for mining) and voids UNDER the surface (caves, lava tubes).

THE PRINCIPLE, and it is free realism: a resource's LAYER is not a lookup table someone
invents -- it is set by how the resource FORMS. Diamonds need >4 GPa, which is deeper than
~136 km (P = rho*g*h), so they sit in the mantle and reach the surface only through kimberlite
pipes. Placer gold is concentrated by erosion in shallow topsoil. Banded iron is sedimentary
bedrock. So "different things in different layers" derives from formation conditions -- the
pressure, temperature and depth the onion already knows -- exactly as the operator's "no
aesthetic passes" rule demands: content DERIVES from the matter model, it is not painted on.

Two more rules, inherited from the rest of the studio:
- DEPTH-BELOW-SURFACE, not absolute radius. A deposit at "150 km below the surface" stays
  150 km below when the surface uplifts -- it rides with the base, the same child-relative-to-
  parent invariant that the onion itself obeys. Uplift a mountain and its veins come along.
- A PURE FUNCTION OF POSITION. Presence is hashed from absolute position (progeny.world_height's
  doctrine, extended to 3-D): same parcel, same content, forever; no storage, infinite world,
  no neighbour consultation. Caves and veins are DISCOVERED by probing, never placed by hand.

Voids are layer-typed too: lava tubes drain through shallow crust; karst caves dissolve in
soluble bedrock below the water table. Both are the negative space matter grows around.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from core.planet_membrane import LAYERS, R_EARTH, PlanetOnion

# cumulative depth (m) to the BOTTOM of each sub-surface layer -> which layer a depth is in
_CUM = []
_acc = 0.0
for _nm, _th in LAYERS[1:]:
    _acc += _th
    _CUM.append((_nm, _acc))


def layer_at(depth_m: float) -> str:
    for nm, bot in _CUM:
        if depth_m <= bot:
            return nm
    return 'core'


# --- the physics the layers carry -----------------------------------------


def pressure_GPa(depth_m: float) -> float:
    """Lithostatic pressure rho*g*h, with crust (2800) over mantle (3300) density."""
    if depth_m <= 35_000:
        col = 2800.0 * depth_m
    else:
        col = 2800.0 * 35_000 + 3300.0 * (depth_m - 35_000)
    return 9.81 * col / 1e9


def temperature_C(depth_m: float) -> float:
    """A piecewise geotherm: ~25 C/km through the crust, flattening to an adiabat below."""
    km = depth_m / 1000.0
    return 15 + 25 * km if km <= 35 else 890 + 0.5 * (km - 35)


# --- deterministic position hashing (pure function of the rock parcel) ------

_PRIMES = (73856093, 19349663, 83492791, 50331653)   # progeny.tile_seed's family, +z


def _hash01(*ints) -> float:
    h = 2166136261
    for k, i in zip(_PRIMES, ints):
        h = (h ^ ((int(i) & 0x7FFFFFFF) * k)) & 0xFFFFFFFF
        h = (h * 16777619) & 0xFFFFFFFF
    return h / 0xFFFFFFFF


def _vnoise3(x: float, y: float, z: float, salt: int = 0) -> float:
    """Trilinear value noise on the integer lattice -- smooth, deterministic, for clustering
    veins and cave chambers rather than salt-and-pepper speckle."""
    ix, iy, iz = int(np.floor(x)), int(np.floor(y)), int(np.floor(z))
    fx, fy, fz = x - ix, y - iy, z - iz
    ux, uy, uz = (fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy), fz * fz * (3 - 2 * fz))
    out = 0.0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (ux if dx else 1 - ux) * (uy if dy else 1 - uy) * (uz if dz else 1 - uz)
                out += w * _hash01(ix + dx, iy + dy, iz + dz, salt)
    return out


def _parcel_xyz(lat_deg: float, lon_deg: float, depth_m: float, scale_m: float):
    """A stable 3-D noise coordinate for a rock parcel, in units of `scale_m`. Uses a FIXED
    reference radius so the pattern does not shift when the surface is edited -- the parcel
    keeps its identity; only its depth-below-surface ties it to the moving base."""
    lat, lon = np.radians(lat_deg), np.radians(lon_deg)
    r = (R_EARTH - depth_m)
    x = r * np.cos(lat) * np.cos(lon)
    y = r * np.cos(lat) * np.sin(lon)
    z = r * np.sin(lat)
    return x / scale_m, y / scale_m, z / scale_m


# --- what forms where: the deposit catalog (physics-keyed) ------------------


@dataclass
class Deposit:
    """A resource type. WHERE it can be found is a physical predicate on (P, T, depth); HOW
    common and HOW clustered are the game-economy numbers (trainable later against an economy
    objective -- the geology is fixed, the abundance is data)."""
    name: str
    layers: tuple                     # which onion layers it can occur in
    suitability: object               # callable(P_GPa, T_C, depth_m) -> 0..1 (formation window)
    abundance: float                  # base fraction of suitable parcels that bear it
    cluster_km: float                 # size of a vein/orebody (clustering scale)
    value: float                      # relative worth (the economy hook)
    salt: int = 0
    needs_land: bool = False          # placers are fluvial -> land only

    def grade_at(self, lat, lon, depth, P, T, surf: float = 1.0) -> float:
        """Ore grade in [0,1] at a parcel: formation window x clustered density x fine speckle.
        0 means barren. Deterministic."""
        if layer_at(depth) not in self.layers or (self.needs_land and surf <= 0):
            return 0.0
        s = float(self.suitability(P, T, depth))
        if s <= 0:
            return 0.0
        # Occurrence gate uses the RAW per-cell hash, which is genuinely uniform, so exactly
        # `abundance` of orebody-cells bear the deposit. (Interpolated noise clusters near 0.5
        # and would make low-abundance gems unreachable -- the bug the prospect scan caught.)
        cx, cy, cz = _parcel_xyz(lat, lon, depth, self.cluster_km * 1000.0)
        ci = (int(np.floor(cx)), int(np.floor(cy)), int(np.floor(cz)))
        if _hash01(ci[0], ci[1], ci[2], self.salt) > self.abundance:
            return 0.0                                    # this orebody cell is barren
        body = _vnoise3(cx, cy, cz, self.salt + 7)        # smooth shape WITHIN the bearing cell
        fx, fy, fz = _parcel_xyz(lat, lon, depth, self.cluster_km * 40.0)
        speckle = _vnoise3(fx, fy, fz, self.salt + 991)   # fine richness (3-D lenses)
        return float(np.clip(s * body * speckle * 2.4, 0, 1))


def _window(lo, hi):
    """A soft depth/pressure formation window -> 1 inside [lo,hi], tapering outside."""
    def f(v):
        if v < lo:
            return max(0.0, 1 - (lo - v) / (0.4 * lo + 1e-9))
        if v > hi:
            return max(0.0, 1 - (v - hi) / (0.4 * hi + 1e-9))
        return 1.0
    return f


DEPOSITS = [
    # placer gold: erosion-concentrated in shallow soil, near sea level. Rare, patchy.
    Deposit('gold_placer', ('topsoil', 'subsoil'),
            lambda P, T, d: _window(0.0, 1.4)(d), abundance=0.06, cluster_km=0.4,
            value=40.0, salt=11, needs_land=True),
    # banded iron: sedimentary bedrock, layered, common.
    Deposit('iron_ore', ('bedrock',),
            lambda P, T, d: _window(2.0, 61.0)(d), abundance=0.28, cluster_km=1.2,
            value=3.0, salt=22),
    # coal: sedimentary basins in bedrock, shallow, seams.
    Deposit('coal', ('bedrock',),
            lambda P, T, d: _window(5.0, 60.0)(d), abundance=0.16, cluster_km=2.5,
            value=2.0, salt=33),
    # copper: hydrothermal veins in the crust, moderate depth, strongly veined.
    Deposit('copper_vein', ('crust',),
            lambda P, T, d: _window(200.0, 6000.0)(d), abundance=0.10, cluster_km=3.0,
            value=8.0, salt=44),
    # diamond: needs >4 GPa (>~136 km) and 900-1400 C -> deep mantle, kimberlite-rare.
    Deposit('diamond', ('mantle',),
            lambda P, T, d: 1.0 if (P > 4.0 and 850 < T < 1500) else 0.0,
            abundance=0.015, cluster_km=8.0, value=500.0, salt=55),
]


# --- voids: caves and lava tubes (the negative space) ----------------------


def void_at(lat_deg: float, lon_deg: float, depth_m: float, surface_elev: float) -> str | None:
    """Is this parcel OPEN (a void)? Returns the void type or None. Layer-typed by genesis."""
    layer = layer_at(depth_m)
    # karst caves: soluble bedrock, below a shallow water table, blobby chambers.
    if layer == 'bedrock' and depth_m > 3.0:
        cx, cy, cz = _parcel_xyz(lat_deg, lon_deg, depth_m, 30.0)     # ~30 m chambers
        soluble = _vnoise3(*_parcel_xyz(lat_deg, lon_deg, 0.0, 5000.0), salt=7)  # limestone regions
        if soluble > 0.55 and _vnoise3(cx, cy, cz, salt=8) > 0.72:
            return 'karst_cave'
    # lava tubes: shallow crust, volcanic regions (high ground), horizontal tunnels.
    if layer in ('bedrock', 'crust') and 5.0 < depth_m < 400.0 and surface_elev > 800.0:
        volcanic = _vnoise3(*_parcel_xyz(lat_deg, lon_deg, 0.0, 8000.0), salt=13)
        if volcanic > 0.60:
            tube = _vnoise3(*_parcel_xyz(lat_deg, lon_deg, depth_m, 120.0), salt=14)
            if tube > 0.74:
                return 'lava_tube'
    return None


# --- the layered planet: probe, borehole, mine -----------------------------


@dataclass
class LayeredPlanet:
    """A PlanetOnion plus what fills and voids its layers. The subsurface query engine."""
    onion: PlanetOnion
    _cache: dict = field(default_factory=dict)

    @classmethod
    def earthlike(cls, seed: int = 3) -> 'LayeredPlanet':
        return cls(onion=PlanetOnion.earthlike(seed=seed))

    def probe(self, lat_deg: float, lon_deg: float, depth_m: float) -> dict:
        """What is at this parcel: layer, base material, void (cave), or deposit (ore/gem)."""
        surf = self.onion.sample(lat_deg, lon_deg)['elevation']
        layer = layer_at(depth_m)
        P, T = pressure_GPa(depth_m), temperature_C(depth_m)
        void = void_at(lat_deg, lon_deg, depth_m, surf)
        if void:
            return {'layer': layer, 'state': 'void', 'void': void, 'material': 'air',
                    'deposit': None, 'grade': 0.0, 'P_GPa': P, 'T_C': T}
        best, best_g = None, 0.0
        for dep in DEPOSITS:
            g = dep.grade_at(lat_deg, lon_deg, depth_m, P, T, surf)
            if g > best_g:
                best, best_g = dep, g
        return {'layer': layer, 'state': 'solid', 'void': None,
                'material': layer if best is None else best.name,
                'deposit': None if best is None else best.name,
                'grade': best_g, 'P_GPa': P, 'T_C': T}

    def borehole(self, lat_deg: float, lon_deg: float, max_depth: float,
                 steps: int = 400) -> list:
        """A core sample: the sequence of transitions drilling straight down -- what a mine
        shaft would cross. Log-spaced so both the top six inches and the diamond zone show."""
        surf = self.onion.sample(lat_deg, lon_deg)['elevation']
        depths = np.concatenate([[0.0], np.geomspace(0.05, max_depth, steps)])
        out, last = [], None
        for d in depths:
            r = self.probe(lat_deg, lon_deg, float(d))
            key = (r['state'], r['void'], r['deposit'], r['layer'])
            if key != last:
                out.append({'depth_m': float(d), **r})
                last = key
        out.insert(0, {'depth_m': 0.0, 'surface_elev': float(surf)})
        return out

    def prospect(self, n_lat=18, n_lon=18, per_deposit=900) -> dict:
        """Scan the globe and MEASURE, per deposit, the fraction of parcels bearing it and the
        layers it occurs in -- proof that the physics-keying holds (iron->bedrock, diamond->
        mantle), not just that a render looks plausible. Samples each deposit at depths inside
        its own host layers, so a rare deep gem is not drowned by the shallow column."""
        rng = np.random.default_rng(12345)
        report = {}
        for dep in DEPOSITS:
            bands = []
            for nm, bot in _CUM:
                if nm in dep.layers:
                    top = bot - dict(LAYERS[1:])[nm]
                    bands.append((nm, top, bot))
            hits, layers_seen, grades = 0, {}, []
            for _ in range(per_deposit):
                la = float(rng.uniform(-75, 75)); lo = float(rng.uniform(0, 360))
                surf = self.onion.sample(la, lo)['elevation']
                nm, top, bot = bands[rng.integers(len(bands))]
                d = float(rng.uniform(top, min(bot, top + 500_000)))
                P, T = pressure_GPa(d), temperature_C(d)
                g = dep.grade_at(la, lo, d, P, T, surf)
                if g > 0.15:
                    hits += 1
                    grades.append(g)
                    layers_seen[layer_at(d)] = layers_seen.get(layer_at(d), 0) + 1
            report[dep.name] = {
                'bearing_fraction': hits / per_deposit,
                'mean_grade': float(np.mean(grades)) if grades else 0.0,
                'layers': layers_seen,
            }
        return report

    def to_membranes(self, lat_deg: float, lon_deg: float, depth_m: float, radius_m: float = 20.0):
        """Materialize the deposits/voids near a point as child Membrane nodes (for the local
        scene). Below `radius_m` a solid deposit is a substrate stud; a void is negative space."""
        from core import membranes as M
        host = M.Membrane(f'parcel@{lat_deg:.2f},{lon_deg:.2f},{depth_m:.0f}m',
                          scale=radius_m, serial='PARCEL')
        r = self.probe(lat_deg, lon_deg, depth_m)
        if r['state'] == 'void':
            child = host.add(M.Membrane(r['void'], scale=radius_m, serial=f'VOID-{r["void"]}'))
            child.prop(open_void=True, void_type=r['void'])
        elif r['deposit']:
            child = host.add(M.Membrane(r['deposit'], scale=radius_m * (0.3 + 0.7 * r['grade']),
                                        serial=f'ORE-{r["deposit"]}'))
            child.prop(grade=r['grade'], value=next(d.value for d in DEPOSITS
                                                    if d.name == r['deposit']))
            child.port('face', 'substrate', at=[0, 0, 0], facing=[0, 0, 1], size=radius_m)
        return host


def _cross_section(lp: LayeredPlanet, lat0, lon0, lat1, lon1, max_depth, W=800, H=420):
    """A vertical slice: x = along a surface transect, y = depth. Layers as bands riding the
    relief; deposits as coloured specks in their host layer; voids black. The money render."""
    img = np.zeros((H, W, 3), np.uint8)
    COL = {'topsoil': (110, 84, 58), 'subsoil': (140, 110, 70), 'bedrock': (120, 120, 132),
           'crust': (95, 88, 100), 'mantle': (150, 70, 55), 'core': (200, 120, 60),
           'gold_placer': (255, 214, 0), 'iron_ore': (188, 92, 60), 'coal': (25, 25, 30),
           'copper_vein': (60, 190, 130), 'diamond': (150, 235, 255)}
    for i in range(W):
        f = i / (W - 1)
        lat = lat0 + (lat1 - lat0) * f
        lon = lon0 + (lon1 - lon0) * f
        surf = lp.onion.sample(lat, lon)['elevation']
        for j in range(H):
            depth = (j / (H - 1)) * max_depth
            r = lp.probe(lat, lon, depth)
            if r['state'] == 'void':
                img[j, i] = (8, 8, 10)
            elif r['deposit'] and r['grade'] > 0.15:
                base = COL.get(r['deposit'], (255, 0, 255))
                b = 0.4 + 0.6 * r['grade']                # brightness tracks grade
                img[j, i] = tuple(int(c * b) for c in base)
            else:
                img[j, i] = COL.get(r['layer'], (60, 60, 60))
        # a thin sky band above the surface so relief is legible
        sky_h = int(np.clip((1 - (surf + 6000) / 12000), 0, 0.12) * H)
        img[:sky_h, i] = (30, 40, 70)
    return img


def _main() -> int:
    import argparse
    import sys
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    ap = argparse.ArgumentParser(description='what is within and under the onion')
    ap.add_argument('--seed', type=int, default=3)
    ap.add_argument('--render', action='store_true')
    a = ap.parse_args()

    lp = LayeredPlanet.earthlike(seed=a.seed)

    print("  === the deposit catalog (layer set by FORMATION conditions) ===")
    for d in DEPOSITS:
        print(f"    {d.name:13} layers={'/'.join(d.layers):20} value={d.value:5.0f} "
              f"abundance={d.abundance:.3f} vein~{d.cluster_km}km")

    print("\n  === prospecting scan: deposits land in their FORMATION layer (measured) ===")
    for name, r in lp.prospect().items():
        layers = ', '.join(f'{k} {v}' for k, v in sorted(r['layers'].items(),
                                                          key=lambda x: -x[1])) or '(none found)'
        print(f"    {name:13} bearing {r['bearing_fraction']*100:4.1f}% of host-layer parcels "
              f"· mean grade {r['mean_grade']:.2f} · in: {layers}")

    print("\n  === boreholes: drill straight down, list what you cross ===")
    for (la, lo) in [(35.0, 200.0), (12.0, 47.0), (48.0, 305.0)]:
        surf = lp.onion.sample(la, lo)['elevation']
        tag = 'LAND' if surf > 0 else 'SEABED'
        print(f"\n    ({la:+.0f},{lo:.0f})  surface {surf:+.0f} m  [{tag}]")
        for seg in lp.borehole(la, lo, max_depth=200_000.0):
            if 'surface_elev' in seg and 'state' not in seg:
                continue
            d = seg['depth_m']
            unit = f"{d:8.2f} m" if d < 1000 else f"{d/1000:8.2f} km"
            if seg['state'] == 'void':
                print(f"      {unit}  ── {seg['void'].upper()} (open cave)")
            elif seg['deposit']:
                print(f"      {unit}  ── {seg['layer']:8} · {seg['deposit'].upper()} "
                      f"grade {seg['grade']:.2f}  (P={seg['P_GPa']:.1f} GPa, T={seg['T_C']:.0f} C)")
            else:
                print(f"      {unit}  ── {seg['layer']:8} ({seg['material']})")

    if a.render:
        from pathlib import Path
        try:
            from PIL import Image
        except Exception:
            print('\n  (PIL absent -- skipping render)'); return 0
        out = Path('Saved/SplatEmit'); out.mkdir(parents=True, exist_ok=True)
        # shallow MINING view: a NARROW ~350 m transect (near 1:4 aspect) so orebodies read as
        # lenses, not aspect-ratio stripes. 0-90 m: soils, bedrock ores, karst caves.
        sh = _cross_section(lp, 34.000, 200.000, 34.003, 200.004, max_depth=90.0, H=360)
        Image.fromarray(sh).save(out / 'planet_layers_shallow.png')
        # DEEP view: a ~60 km transect to 250 km, crust -> mantle, reaching the diamond zone.
        dp = _cross_section(lp, 34.0, 200.0, 34.0, 200.55, max_depth=250_000.0, H=360)
        Image.fromarray(dp).save(out / 'planet_layers_deep.png')
        print(f"\n  wrote {out}/planet_layers_shallow.png (0-90 m: soil/bedrock ores + caves)")
        print(f"  wrote {out}/planet_layers_deep.png     (0-250 km: crust->mantle + diamond zone)")
    return 0


if __name__ == '__main__':
    raise SystemExit(_main())
