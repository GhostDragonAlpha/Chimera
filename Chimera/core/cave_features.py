"""cave_features — what is IN a cave. Space becomes space worth exploring.

A carved Cave (core/cave.py) is empty air. This fills it from the SAME deterministic physics
that made it -- nothing painted on (the operator's "no aesthetic passes"):

  WALL ORE   the cave's walls are rock, and that rock is the host layer, which may bear a
             deposit. Where a vein meets the cavity it is EXPOSED -- mineable off the wall,
             no shaft from the surface. Just probe() the rock cells bordering the void.
  WATER      groundwater fills open space below the WATER TABLE. The table sits a vadose zone
             below the surface (deeper under high ground, near sea level at the coast), so a
             chamber that dips below it is a POOL / underground lake, and one above stays dry.
  DARKNESS   light enters only at the opening you broke in through; it falls off with distance,
             so the far chambers are pitch black -- bring a torch, and only chemosynthesis
             lives there. Light is a BFS from the entry over the open cells.
  SPELEOTHEMS in karst (dissolved limestone), dripping mineral water builds stalactites and
             stalagmites -- deterministic drips on ceiling and floor.

Everything is a pure function of position: the same cave is furnished the same way, forever.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass

import numpy as np

from core.cave import Cave
from core.planet_layers import _hash01, _parcel_xyz

_NEIGH6 = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
LIGHT_RANGE_M = 14.0                       # how far daylight reaches from an opening


def vadose_m(surface_elev: float) -> float:
    """Depth of the unsaturated zone above the water table: a few metres near sea level,
    deeper under high ground (a damped function of terrain)."""
    return 8.0 + 0.28 * max(surface_elev, 0.0)


@dataclass
class CaveContents:
    cave: Cave
    water: np.ndarray            # bool (nx,ny,nz): flooded open cells
    water_elev: float            # absolute elevation of the pool surface (m)
    light: np.ndarray            # float (nx,ny,nz): 1 lit .. 0 pitch black (open cells)
    ore_type: np.ndarray         # object (nx,ny,nz): exposed deposit on the wall at this cell, or None
    ore_counts: dict             # deposit -> exposed wall cells
    speleo: np.ndarray           # bool (nx,ny,nz): a speleothem (stalactite/mite) here

    def measure(self) -> dict:
        c = self.cave
        vox3 = c.vox ** 3
        openn = int(c.open.sum())
        wet = int(self.water.sum())
        lit = int((self.light > 0.25).sum())
        return {
            'pool_volume_m3': round(wet * vox3, 0),
            'pool_fraction': round(wet / max(openn, 1), 2),
            'water_elev_m': round(self.water_elev, 1),
            'exposed_ore': {k: int(v) for k, v in self.ore_counts.items()},
            'lit_fraction': round(lit / max(openn, 1), 2),
            'dark_volume_m3': round((openn - lit) * vox3, 0),
            'speleothems': int(self.speleo.sum()),
        }


def populate(cave: Cave) -> CaveContents:
    """Furnish a cave from physics: pools below the water table, ore exposed on the walls,
    a light gradient from the opening, and karst speleothems."""
    nx, ny, nz = cave.open.shape
    E = float(cave.planet.onion.sample(cave.lat, cave.lon)['elevation'])
    water_elev = E - vadose_m(E)                  # absolute elevation of the water table

    water = np.zeros_like(cave.open)
    light = np.zeros(cave.open.shape, dtype=float)
    ore_type = np.empty(cave.open.shape, dtype=object)
    speleo = np.zeros_like(cave.open)
    ore_counts: dict = {}

    open_cells = np.argwhere(cave.open)

    # WATER: an open cell floods if it sits below the water table (or below sea level).
    for ix, iy, iz in open_cells:
        _, _, d = cave.voxel_latlondepth(ix, iy, iz)
        z_abs = E - d
        if z_abs < water_elev or z_abs < 0.0:
            water[ix, iy, iz] = True

    # WALL ORE: probe rock cells bordering the cavity; a vein at the wall is exposed.
    for ix, iy, iz in open_cells:
        best, bg = None, 0.0
        for dx, dy, dz in _NEIGH6:
            jx, jy, jz = ix + dx, iy + dy, iz + dz
            if 0 <= jx < nx and 0 <= jy < ny and 0 <= jz < nz and cave.open[jx, jy, jz]:
                continue                          # neighbour is air, not a wall
            lat, lon, d = cave.voxel_latlondepth(jx, jy, jz)
            r = cave.planet.probe(lat, lon, max(d, 0.6))
            if r['deposit'] and r['grade'] > bg and r['grade'] > 0.15:
                best, bg = r['deposit'], r['grade']
        if best:
            ore_type[ix, iy, iz] = best
            ore_counts[best] = ore_counts.get(best, 0) + 1

    # DARKNESS: BFS light from the entry opening over open cells; fall off with distance.
    ex, ey, ez = cave.entry
    if cave.open[ex, ey, ez]:
        dist = {(ex, ey, ez): 0.0}
        dq = deque([(ex, ey, ez)])
        while dq:
            cx, cy, cz = dq.popleft()
            here = dist[(cx, cy, cz)]
            for dx, dy, dz in _NEIGH6:
                nb = (cx + dx, cy + dy, cz + dz)
                if (0 <= nb[0] < nx and 0 <= nb[1] < ny and 0 <= nb[2] < nz
                        and cave.open[nb] and nb not in dist):
                    dist[nb] = here + cave.vox
                    dq.append(nb)
        for (cx, cy, cz), dm in dist.items():
            light[cx, cy, cz] = max(0.0, 1.0 - dm / LIGHT_RANGE_M)

    # SPELEOTHEMS: karst only. A ceiling cell (rock above, air below) or floor cell drips.
    if cave.kind == 'karst_cave':
        for ix, iy, iz in open_cells:
            ceiling = iz + 1 < nz and not cave.open[ix, iy, iz + 1]
            floor = iz - 1 >= 0 and not cave.open[ix, iy, iz - 1]
            if (ceiling or floor) and not water[ix, iy, iz]:
                px, py, pz = _parcel_xyz(*cave.voxel_latlondepth(ix, iy, iz), 3.0)
                if _hash01(int(px), int(py), int(pz), 321) < 0.10:
                    speleo[ix, iy, iz] = True

    return CaveContents(cave, water, water_elev, light, ore_type, ore_counts, speleo)


# --- rendering: the furnished cave -------------------------------------------


def _render_section(cc: CaveContents, scale: int = 7):
    """Vertical slice through the entry, furnished: rock, void (dimmed by darkness), water
    (blue), exposed ore (its colour on the wall), speleothems (pale), the break-in (green)."""
    from core.planet_layers import _CUM  # noqa
    ORE = {'gold_placer': (255, 214, 0), 'iron_ore': (200, 96, 60), 'coal': (30, 30, 36),
           'copper_vein': (60, 200, 140), 'diamond': (150, 235, 255)}
    cave = cc.cave
    floor_z, _ = cave.floor_map()
    nx, ny, nz = cave.open.shape
    ey = cave.entry[1]
    img = np.zeros((nz, nx, 3), np.uint8)
    for ix in range(nx):
        for iz in range(nz):
            yy = nz - 1 - iz
            if cave.open[ix, ey, iz]:
                if cc.water[ix, ey, iz]:
                    img[yy, ix] = (30, 90, 175)                      # water
                else:
                    lg = cc.light[ix, ey, iz]
                    v = int(14 + 30 * lg)                            # darkness dims the air
                    img[yy, ix] = (v, v, int(v * 1.2) + 6)
                if cc.speleo[ix, ey, iz]:
                    img[yy, ix] = (210, 205, 225)
            else:
                ot = cc.ore_type[ix, ey, iz] if False else None      # walls colored below
                img[yy, ix] = (96, 74, 54)                           # rock
        if floor_z[ix, ey] >= 0:
            img[nz - 1 - int(floor_z[ix, ey]), ix] = (200, 172, 125)
    # paint exposed ore on the wall cells (from the air cell that borders them)
    for ix in range(nx):
        for iz in range(nz):
            ot = cc.ore_type[ix, ey, iz]
            if ot and cave.open[ix, ey, iz]:
                for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    jx, jz = ix + dx, iz + dz
                    if 0 <= jx < nx and 0 <= jz < nz and not cave.open[jx, ey, jz]:
                        img[nz - 1 - jz, jx] = ORE.get(ot, (255, 0, 255))
    ex, _, ez = cave.entry
    img[nz - 1 - ez, ex] = (80, 240, 90)
    return np.kron(img, np.ones((scale, scale, 1), np.uint8))


def _main() -> int:
    import argparse
    import sys
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    from core.cave import carve
    from core.planet_layers import LayeredPlanet, void_at

    ap = argparse.ArgumentParser(description='what is IN a cave: ore, water, dark, speleothems')
    ap.add_argument('--seed', type=int, default=3)
    ap.add_argument('--render', action='store_true')
    a = ap.parse_args()
    lp = LayeredPlanet.earthlike(seed=a.seed)

    def show(cave, title):
        cc = populate(cave)
        m = cc.measure()
        E = lp.onion.sample(cave.lat, cave.lon)['elevation']
        print(f"\n  === {title}: ({cave.lat:.1f},{cave.lon:.1f}) surface {E:+.0f} m, "
              f"cave at {cave.depth:.0f} m ===")
        print(f"    water table at {vadose_m(E):.0f} m depth -> pool {m['pool_volume_m3']:,.0f} m^3 "
              f"({m['pool_fraction']*100:.0f}% of the cave flooded)")
        print(f"    exposed ore on walls: {m['exposed_ore'] or 'none'}")
        print(f"    lit {m['lit_fraction']*100:.0f}% near the opening; "
              f"{m['dark_volume_m3']:,.0f} m^3 in the dark")
        print(f"    speleothems: {m['speleothems']}")
        return cc

    # a high-and-dry cave: walls may show ore, mostly lit near the hole, no pool
    dry = carve(lp, 35.0, 200.0, 10.0)
    cc_dry = show(dry, "High cave (dry)") if dry else None

    # hunt a low-elevation karst cave that dips below its shallow water table -> a pool
    wet = None
    rng = np.random.default_rng(a.seed)
    for _ in range(6000):
        la = float(rng.uniform(-60, 60)); lo = float(rng.uniform(0, 360))
        E = lp.onion.sample(la, lo)['elevation']
        if 5 < E < 45 and void_at(la, lo, 22.0, E) == 'karst_cave':
            wet = carve(lp, la, lo, 22.0)
            if wet:
                break
    cc_wet = show(wet, "Low coastal cave (flooded)") if wet else None
    if cc_wet is None:
        print("\n  (no low-elevation karst cave found in budget)")

    if a.render:
        from pathlib import Path
        try:
            from PIL import Image
        except Exception:
            print('\n  (PIL absent -- skipping render)'); return 0
        out = Path('Saved/SplatEmit'); out.mkdir(parents=True, exist_ok=True)
        panels = [cc for cc in (cc_dry, cc_wet) if cc]
        imgs = [_render_section(cc) for cc in panels]
        h = max(i.shape[0] for i in imgs)
        imgs = [np.pad(i, ((0, h - i.shape[0]), (0, 0), (0, 0))) for i in imgs]
        gap = np.zeros((h, 14, 3), np.uint8) + 30
        canvas = imgs[0]
        for i in imgs[1:]:
            canvas = np.hstack([canvas, gap, i])
        Image.fromarray(canvas).save(out / 'cave_populated.png')
        print(f"\n  wrote {out}/cave_populated.png (dry cave w/ wall ore | flooded cave w/ pool)")
    return 0


if __name__ == '__main__':
    raise SystemExit(_main())
