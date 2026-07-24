"""cave — a void you broke into becomes explorable SPACE, not a log line.

Mining reports "broke into a karst cave" and moves on. This turns that event into somewhere
you can actually GO: it flood-fills the connected void around the break-in point into a
navigable cavity, wraps it as a MEMBRANE (negative space -- air inside, rock outside), finds
the floor you stand on and the passages that lead deeper, and hands back a local frame to
enter.

A cave is the membrane primitive run INSIDE-OUT. A solid brick has matter inside and air
outside; a cave inverts it. So nothing new is invented -- the void field of planet_layers IS
the cave (measured: karst chambers flood-fill to ~20,000 m3, ~25 m across), and a Membrane's
PORTS are exactly the passages where the cavity exits the sampled box, i.e. where the cave
CONTINUES. An unfilled passage is the world's "unexplored this way" marker -- the work queue,
for caves.

Deterministic and pure-function-of-position, like everything under the surface: the same
break-in point yields the same cave, forever, with no storage.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

import numpy as np

from core.planet_layers import LayeredPlanet, layer_at, void_at

_NEIGH6 = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))


@dataclass
class Cave:
    """A connected navigable void, anchored at a break-in point. Voxels are OPEN (air) cells;
    everything else in the box is rock. The floor is where you stand, passages lead on."""
    planet: LayeredPlanet
    lat: float
    lon: float
    depth: float                     # depth-below-surface of the box centre (m)
    vox: float                       # voxel edge (m)
    open: np.ndarray                 # (nx, ny, nz) bool -- the connected cavity
    entry: tuple                     # voxel index where the dig broke in
    kind: str = 'cave'
    _floor: tuple = field(default=None, repr=False)

    # --- geometry: voxel <-> world ----------------------------------------

    def _mperdeg(self) -> float:
        return np.pi / 180 * self.planet.onion.radius

    def voxel_latlondepth(self, ix, iy, iz):
        nx, ny, nz = self.open.shape
        m = self._mperdeg()
        dlat = (iy - ny / 2) * self.vox / m
        dlon = (ix - nx / 2) * self.vox / (m * np.cos(np.radians(self.lat)))
        d = self.depth + (iz - nz / 2) * self.vox
        return self.lat + dlat, self.lon + dlon, d

    # --- the floor you stand on -------------------------------------------

    def floor_map(self):
        """Per (x,y) column: the lowest open voxel (floor sits on the rock below it) and the
        headroom above it. This is the walkable surface -- a cave you can stand up in."""
        if self._floor is not None:
            return self._floor
        nx, ny, nz = self.open.shape
        floor_z = -np.ones((nx, ny), dtype=int)
        head = np.zeros((nx, ny), dtype=float)
        for ix in range(nx):
            for iy in range(ny):
                col = self.open[ix, iy]
                if not col.any():
                    continue
                z0 = int(np.argmax(col))            # lowest open cell in the column
                floor_z[ix, iy] = z0
                h = 0
                for z in range(z0, nz):
                    if self.open[ix, iy, z]:
                        h += 1
                    else:
                        break
                head[ix, iy] = h * self.vox
        self._floor = (floor_z, head)
        return self._floor

    # --- passages: where the cave continues (the ports) -------------------

    def passages(self) -> list:
        """Open cavity cells touching a side/top/bottom face of the box -> the cave leads on
        that way. Clustered into distinct openings; each becomes a membrane port."""
        nx, ny, nz = self.open.shape
        boundary = set()
        for ix in range(nx):
            for iy in range(ny):
                for iz in range(nz):
                    if not self.open[ix, iy, iz]:
                        continue
                    if ix in (0, nx - 1) or iy in (0, ny - 1) or iz in (0, nz - 1):
                        boundary.add((ix, iy, iz))
        # cluster boundary cells into openings
        seen, openings = set(), []
        for cell in boundary:
            if cell in seen:
                continue
            comp, dq = [], deque([cell])
            seen.add(cell)
            while dq:
                c = dq.popleft()
                comp.append(c)
                for d in _NEIGH6:
                    nb = (c[0] + d[0], c[1] + d[1], c[2] + d[2])
                    if nb in boundary and nb not in seen:
                        seen.add(nb)
                        dq.append(nb)
            cx = np.mean([c[0] for c in comp]); cy = np.mean([c[1] for c in comp])
            cz = np.mean([c[2] for c in comp])
            # outward direction from the box centre
            dirv = np.array([cx - nx / 2, cy - ny / 2, cz - nz / 2], float)
            dirv = dirv / (np.linalg.norm(dirv) + 1e-9)
            openings.append({'cells': len(comp), 'center_voxel': (cx, cy, cz),
                             'facing': dirv, 'area_m2': len(comp) * self.vox ** 2})
        return [o for o in openings if o['cells'] >= 2]     # drop single-voxel nicks

    # --- measurement ------------------------------------------------------

    def measure(self) -> dict:
        floor_z, head = self.floor_map()
        vol = int(self.open.sum()) * self.vox ** 3
        walkable = int((floor_z >= 0).sum())
        cells = np.argwhere(self.open)
        extent = (cells.max(0) - cells.min(0) + 1) * self.vox if len(cells) else np.zeros(3)
        passages = self.passages()
        return {
            'kind': self.kind,
            'volume_m3': round(vol, 1),
            'floor_area_m2': round(walkable * self.vox ** 2, 1),
            'max_headroom_m': round(float(head.max()), 1),
            'mean_headroom_m': round(float(head[head > 0].mean()) if (head > 0).any() else 0, 1),
            'extent_m': [round(float(e), 1) for e in extent],
            'n_passages': len(passages),
            'standable': bool(head.max() >= 1.8),          # can a person stand up somewhere?
        }

    # --- enter: the local frame -------------------------------------------

    def enter(self) -> dict:
        """Step inside. Returns where you stand (on the floor under the break-in), which way is
        up, and the LOCAL bounds -- coordinates local to this membrane, so precision is bounded
        by the cave's own size, never the planet's."""
        floor_z, head = self.floor_map()
        ex, ey, _ = self.entry
        # nearest walkable column to the entry
        best, bd = None, 1e9
        for ix, iy in np.argwhere(floor_z >= 0):
            d = (ix - ex) ** 2 + (iy - ey) ** 2
            if d < bd:
                bd, best = d, (ix, iy)
        if best is None:
            return {'ok': False}
        ix, iy = best
        lat, lon, depth = self.voxel_latlondepth(ix, iy, int(floor_z[ix, iy]))
        nx, ny, nz = self.open.shape
        return {'ok': True,
                'stand_latlondepth': (round(float(lat), 4), round(float(lon), 4), round(float(depth), 1)),
                'up': [0.0, 0.0, 1.0],                     # local: away from planet centre
                'headroom_m': round(float(head[ix, iy]), 1),
                'bounds_m': [round(nx * self.vox, 1), round(ny * self.vox, 1), round(nz * self.vox, 1)]}

    def contains(self, ix, iy, iz) -> bool:
        nx, ny, nz = self.open.shape
        return 0 <= ix < nx and 0 <= iy < ny and 0 <= iz < nz and bool(self.open[ix, iy, iz])

    # --- as a membrane in the hierarchy -----------------------------------

    def to_membrane(self):
        """A negative-space Membrane: inside is AIR, outside is rock. Ports = the passages that
        lead on (plus the entry). Nests under the layer it was dug in, so its address is the
        path of membranes crossed to reach it."""
        from core import membranes as M
        nx, ny, nz = self.open.shape
        m = M.Membrane(self.kind, scale=max(nx, ny, nz) * self.vox,
                       serial=f'VOID-{self.kind}@{self.lat:.2f},{self.lon:.2f},{self.depth:.0f}m')
        info = self.measure()
        m.prop(open_void=True, volume_m3=info['volume_m3'], layer=layer_at(self.depth),
               standable=info['standable'])
        m.port('entry', 'structural', at=[0, 0, nz * self.vox / 2], facing=[0, 0, 1],
               size=self.vox * 3)
        for k, p in enumerate(self.passages()):
            m.port(f'passage_{k}', 'structural', at=list(np.asarray(p['center_voxel']) * self.vox),
                   facing=list(p['facing']), size=np.sqrt(p['area_m2']))
        return m


def carve(planet: LayeredPlanet, lat: float, lon: float, depth: float,
          box_m: float = 54.0, depth_span_m: float = 42.0, vox: float = 1.5) -> Cave | None:
    """Flood-fill the connected void around a break-in point into a Cave. Returns None if there
    is no void here (you did not actually break through)."""
    surf = planet.onion.sample(lat, lon)['elevation']
    nx = ny = int(round(box_m / vox))
    nz = int(round(depth_span_m / vox))
    m = np.pi / 180 * planet.onion.radius
    coslat = np.cos(np.radians(lat))
    kinds = np.empty((nx, ny, nz), dtype=object)

    def vkind(ix, iy, iz):
        dlat = (iy - ny / 2) * vox / m
        dlon = (ix - nx / 2) * vox / (m * coslat)
        d = depth + (iz - nz / 2) * vox
        if d < 0.5:
            return None
        return void_at(lat + dlat, lon + dlon, d, surf)

    # seed: the centre if open, else the nearest open cell (the dig may enter at an edge)
    cz = nz // 2
    seed = None
    if vkind(nx // 2, ny // 2, cz):
        seed = (nx // 2, ny // 2, cz)
    else:
        for rad in range(1, max(nx, ny)):
            for ix in range(max(0, nx // 2 - rad), min(nx, nx // 2 + rad + 1)):
                for iy in range(max(0, ny // 2 - rad), min(ny, ny // 2 + rad + 1)):
                    if vkind(ix, iy, cz):
                        seed = (ix, iy, cz)
                        break
                if seed:
                    break
            if seed:
                break
    if seed is None:
        return None

    open_grid = np.zeros((nx, ny, nz), dtype=bool)
    kind0 = vkind(*seed)
    dq = deque([seed])
    open_grid[seed] = True
    while dq:
        x, y, z = dq.popleft()
        for dx, dy, dz in _NEIGH6:
            xx, yy, zz = x + dx, y + dy, z + dz
            if 0 <= xx < nx and 0 <= yy < ny and 0 <= zz < nz and not open_grid[xx, yy, zz]:
                if vkind(xx, yy, zz):
                    open_grid[xx, yy, zz] = True
                    dq.append((xx, yy, zz))
    # entry = highest open voxel nearest the shaft column (the break-in from above)
    col = open_grid[nx // 2, ny // 2]
    entry_z = int(np.max(np.where(col))) if col.any() else cz
    return Cave(planet, lat, lon, depth, vox, open_grid, (nx // 2, ny // 2, entry_z),
                kind=kind0 or 'cave')


def from_break(planet: LayeredPlanet, excavation) -> Cave | None:
    """Carve the cave a mining Excavation broke into (its first void event). Duck-typed on
    .lat/.lon/.column so cave.py need not import mining (avoids a cycle)."""
    for rec in getattr(excavation, 'column', []):
        if rec.get('state') == 'void':
            return carve(planet, excavation.lat, excavation.lon, rec['depth'])
    return None


# --- rendering: see the space -------------------------------------------------


def _render_section(cave: Cave, scale: int = 7):
    """Vertical slice through the entry: rock (brown) vs void (dark), the floor line (tan), the
    break-in (green). z up."""
    floor_z, _ = cave.floor_map()
    nx, ny, nz = cave.open.shape
    ey = cave.entry[1]
    img = np.zeros((nz, nx, 3), np.uint8)
    for ix in range(nx):
        for iz in range(nz):
            img[nz - 1 - iz, ix] = (10, 12, 18) if cave.open[ix, ey, iz] else (96, 74, 54)
        if floor_z[ix, ey] >= 0:
            img[nz - 1 - int(floor_z[ix, ey]), ix] = (210, 180, 130)      # the floor
    ex, _, ez = cave.entry
    img[nz - 1 - ez, ex] = (80, 240, 90)                                   # break-in
    return np.kron(img, np.ones((scale, scale, 1), np.uint8))


def _render_plan(cave: Cave, scale: int = 7):
    """Top-down floor map: walkable area coloured by headroom (brighter = taller), passages
    red on the edges, the break-in green."""
    floor_z, head = cave.floor_map()
    nx, ny, _ = cave.open.shape
    img = np.zeros((nx, ny, 3), np.uint8) + 18
    hmax = max(head.max(), 1e-6)
    for ix in range(nx):
        for iy in range(ny):
            if floor_z[ix, iy] >= 0:
                t = head[ix, iy] / hmax
                img[ix, iy] = (int(40 + 60 * t), int(120 + 135 * t), int(150 + 105 * t))
    for p in cave.passages():
        cx, cy, _ = p['center_voxel']
        img[int(np.clip(cx, 0, nx - 1)), int(np.clip(cy, 0, ny - 1))] = (235, 70, 60)
    ex, ey, _ = cave.entry
    img[ex, ey] = (80, 240, 90)
    return np.kron(img, np.ones((scale, scale, 1), np.uint8))


def _main() -> int:
    import argparse
    import sys
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    ap = argparse.ArgumentParser(description='a void you broke into becomes explorable space')
    ap.add_argument('--seed', type=int, default=3)
    ap.add_argument('--render', action='store_true')
    a = ap.parse_args()

    lp = LayeredPlanet.earthlike(seed=a.seed)

    # the karst cave the borehole at (35,200) broke into at ~10 m
    cave = carve(lp, 35.0, 200.0, 10.0)
    if cave is None:
        print("  no void at the break-in point"); return 0

    info = cave.measure()
    print(f"  === broke into a {info['kind'].replace('_', ' ')} at (35,200), 10 m down ===")
    print(f"    volume        {info['volume_m3']:>10,.0f} m^3")
    print(f"    floor area    {info['floor_area_m2']:>10,.0f} m^2")
    print(f"    headroom      {info['mean_headroom_m']:.1f} m avg, {info['max_headroom_m']:.1f} m max")
    print(f"    extent        {info['extent_m'][0]:.0f} x {info['extent_m'][1]:.0f} x {info['extent_m'][2]:.0f} m")
    print(f"    passages out  {info['n_passages']}  (the cave continues that many ways)")
    print(f"    stand up?     {'YES' if info['standable'] else 'no -- crawlspace'}")

    frame = cave.enter()
    if frame['ok']:
        print(f"\n  === enter: you stand at {frame['stand_latlondepth']} (lat,lon,depth m) ===")
        print(f"    up = {frame['up']} (local)   headroom here {frame['headroom_m']} m")
        print(f"    local bounds {frame['bounds_m']} m  -- coordinates local to THIS membrane")

    mem = cave.to_membrane()
    print(f"\n  === as a membrane (negative space: air inside, rock outside) ===")
    print(f"    {mem.serial}")
    print(f"    open ports (entry + passages that lead on): "
          f"{', '.join(p.name for p in mem.open_ports())}")

    if a.render:
        from pathlib import Path
        try:
            from PIL import Image
        except Exception:
            print('\n  (PIL absent -- skipping render)'); return 0
        out = Path('Saved/SplatEmit'); out.mkdir(parents=True, exist_ok=True)
        Image.fromarray(_render_section(cave)).save(out / 'cave_section.png')
        Image.fromarray(_render_plan(cave)).save(out / 'cave_plan.png')
        print(f"\n  wrote {out}/cave_section.png (side view: rock|void, floor, break-in)")
        print(f"  wrote {out}/cave_plan.png    (top-down floor, headroom, passages)")
    return 0


if __name__ == '__main__':
    raise SystemExit(_main())
