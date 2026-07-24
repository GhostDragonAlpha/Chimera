"""cave_system — follow the passages: one chamber becomes a connected NETWORK.

A single Cave (core/cave.py) knows where it CONTINUES -- its passages are the faces where the
cavity exits its box. This walks those leads: step a box through each passage, carve the next
chamber, and connect them, breadth-first, until the void stops or a budget is hit. The result
is a cave SYSTEM -- a graph of chambers linked by passages, something you can traverse
room-to-room, not one undifferentiated blob.

This IS the studio's work-queue, literally: an unfilled passage port is "unexplored this way",
the BFS frontier is the queue, and carving through a passage fills it and may open new ones.
Boxes tile space on a fixed grid (step = box size), so each region is carved once and
dedup is just its integer box coordinate -- the same determinism the whole subsurface has.

An edge exists only where BOTH adjacent chambers' cavities reach the shared face: the void is
continuous across it, so you can actually walk between them. No edge is asserted from geometry
alone.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

import numpy as np

from core.cave import Cave, carve
from core.planet_layers import LayeredPlanet

# box faces: (axis, side, box-step). side 0 = low index, 1 = high index. +z (axis 2 high) = deeper.
_FACES = [(0, 1, (1, 0, 0)), (0, 0, (-1, 0, 0)),
          (1, 1, (0, 1, 0)), (1, 0, (0, -1, 0)),
          (2, 1, (0, 0, 1)), (2, 0, (0, 0, -1))]


def _face_open(grid: np.ndarray, axis: int, side: int) -> bool:
    """Does the cavity reach this face of its box? (a lead continues that way)."""
    sl = [slice(None)] * 3
    sl[axis] = 0 if side == 0 else -1
    return bool(grid[tuple(sl)].any())


@dataclass
class CaveSystem:
    """A connected network of chambers. nodes: box-coord -> Cave; edges: (boxA, boxB)."""
    planet: LayeredPlanet
    lat0: float
    lon0: float
    depth0: float
    box_m: float
    nodes: dict = field(default_factory=dict)      # (bi,bj,bk) -> Cave
    edges: list = field(default_factory=list)       # ((bi,bj,bk),(bi,bj,bk))

    def box_center(self, bc):
        """The (lat, lon, depth) at the centre of a box coordinate."""
        bi, bj, bk = bc
        m = np.pi / 180 * self.planet.onion.radius
        dlat = (bj * self.box_m) / m
        dlon = (bi * self.box_m) / (m * np.cos(np.radians(self.lat0)))
        return self.lat0 + dlat, self.lon0 + dlon, self.depth0 + bk * self.box_m

    def measure(self) -> dict:
        vols = [c.measure() for c in self.nodes.values()]
        total_v = sum(v['volume_m3'] for v in vols)
        total_f = sum(v['floor_area_m2'] for v in vols)
        depths = [self.box_center(bc)[2] for bc in self.nodes]
        bis = [bc[0] for bc in self.nodes]; bjs = [bc[1] for bc in self.nodes]
        return {
            'n_chambers': len(self.nodes),
            'n_passages': len(self.edges),
            'total_volume_m3': round(total_v, 0),
            'total_floor_m2': round(total_f, 0),
            'depth_range_m': [round(min(depths), 1), round(max(depths), 1)] if depths else [0, 0],
            'span_m': [round((max(bis) - min(bis) + 1) * self.box_m, 0) if bis else 0,
                       round((max(bjs) - min(bjs) + 1) * self.box_m, 0) if bjs else 0],
            'graph_diameter_chambers': self._diameter(),
        }

    def _diameter(self) -> int:
        """Longest shortest-path between chambers (how deep the system is to traverse)."""
        if len(self.nodes) < 2:
            return 0
        adj = {n: [] for n in self.nodes}
        for a, b in self.edges:
            adj[a].append(b); adj[b].append(a)
        best = 0
        for src in self.nodes:
            seen = {src: 0}
            dq = deque([src])
            while dq:
                u = dq.popleft()
                for w in adj[u]:
                    if w not in seen:
                        seen[w] = seen[u] + 1
                        best = max(best, seen[w])
                        dq.append(w)
        return best

    def to_membranes(self):
        """One system Membrane with every chamber nested inside, each carrying its own ports."""
        from core import membranes as M
        sysm = M.Membrane('cave_system', scale=max(self.measure()['span_m'] + [self.box_m]),
                          serial=f'SYS@{self.lat0:.2f},{self.lon0:.2f},{self.depth0:.0f}m')
        for bc, cave in self.nodes.items():
            sysm.add(cave.to_membrane())
        return sysm


def explore(planet: LayeredPlanet, lat: float, lon: float, depth: float,
            max_chambers: int = 20, box_m: float = 48.0, vox: float = 2.0) -> CaveSystem:
    """BFS the void: carve the break-in chamber, then follow every passage to the next, until
    the void stops or `max_chambers` is reached. Returns the connected cave system."""
    sysm = CaveSystem(planet, lat, lon, depth, box_m)
    start = (0, 0, 0)
    c0 = carve(planet, lat, lon, depth, box_m=box_m, depth_span_m=box_m, vox=vox)
    if c0 is None:
        return sysm
    sysm.nodes[start] = c0
    dead = set()                                   # box coords tried and found voidless/unlinked
    q = deque([start])
    while q and len(sysm.nodes) < max_chambers:
        bc = q.popleft()
        cave = sysm.nodes[bc]
        for axis, side, step in _FACES:
            if not _face_open(cave.open, axis, side):
                continue                            # cavity does not reach this face -> no lead
            nb = (bc[0] + step[0], bc[1] + step[1], bc[2] + step[2])
            if nb in dead:
                continue
            if nb in sysm.nodes:
                edge = (bc, nb) if bc < nb else (nb, bc)
                if edge not in sysm.edges and _face_open(sysm.nodes[nb].open, axis, 1 - side):
                    sysm.edges.append(edge)
                continue
            if len(sysm.nodes) >= max_chambers:
                break
            nlat, nlon, ndepth = sysm.box_center(nb)
            ncave = carve(planet, nlat, nlon, ndepth, box_m=box_m, depth_span_m=box_m, vox=vox)
            if ncave is not None and _face_open(ncave.open, axis, 1 - side):
                sysm.nodes[nb] = ncave              # connects back through the shared face
                sysm.edges.append((bc, nb) if bc < nb else (nb, bc))
                q.append(nb)
            else:
                dead.add(nb)
    return sysm


def from_break(planet: LayeredPlanet, excavation, **kw) -> CaveSystem | None:
    """Explore the whole system a mining dig broke into (its first void event)."""
    for rec in getattr(excavation, 'column', []):
        if rec.get('state') == 'void':
            return explore(planet, excavation.lat, excavation.lon, rec['depth'], **kw)
    return None


# --- rendering: the network map ----------------------------------------------


def _render_map(sysm: CaveSystem, W: int = 520):
    """Node-link map: chambers as discs (size ~ volume, colour ~ depth), passages as edges.
    Left = plan (east-north); right = section (east-depth). Entry chamber ringed green."""
    import numpy as np
    nodes = list(sysm.nodes)
    if not nodes:
        return np.zeros((200, W, 3), np.uint8)
    bis = [n[0] for n in nodes]; bjs = [n[1] for n in nodes]; bks = [n[2] for n in nodes]
    vols = {n: sysm.nodes[n].measure()['volume_m3'] for n in nodes}
    vmax = max(vols.values()) or 1.0

    def col_for(bk):
        t = (bk - min(bks)) / max(1, (max(bks) - min(bks)))    # 0 shallow .. 1 deep
        return (int(200 - 150 * t), int(180 - 80 * t), int(120 + 120 * t))

    H = 300
    img = np.zeros((H, W, 3), np.uint8) + 16
    halfW = W // 2

    def layout(vals):
        lo, hi = min(vals), max(vals)
        span = max(1, hi - lo)
        return lo, span

    def draw(panel_x0, panel_w, ax_vals, ay_vals):
        lox, spx = layout(ax_vals); loy, spy = layout(ay_vals)
        pad = 34
        def px(v): return int(panel_x0 + pad + (v - lox) / spx * (panel_w - 2 * pad))
        def py(v): return int(pad + (v - loy) / spy * (H - 2 * pad))
        pos = {}
        for n, ax, ay in zip(nodes, ax_vals, ay_vals):
            pos[n] = (px(ax), py(ay))
        for a, b in sysm.edges:                              # passages first (under nodes)
            xa, ya = pos[a]; xb, yb = pos[b]
            steps = max(abs(xb - xa), abs(yb - ya)) or 1
            for t in range(steps + 1):
                x = int(xa + (xb - xa) * t / steps); y = int(ya + (yb - ya) * t / steps)
                if 0 <= y < H and 0 <= x < W:
                    img[y, x] = (110, 110, 120)
        for n in nodes:
            x, y = pos[n]
            r = 3 + int(9 * (vols[n] / vmax) ** 0.5)
            c = col_for(n[2])
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    if dx * dx + dy * dy <= r * r and 0 <= y + dy < H and 0 <= x + dx < W:
                        img[y + dy, x + dx] = c
            if n == (0, 0, 0):                               # entry ring
                for a_ in range(0, 360, 12):
                    xx = int(x + (r + 2) * np.cos(np.radians(a_)))
                    yy = int(y + (r + 2) * np.sin(np.radians(a_)))
                    if 0 <= yy < H and 0 <= xx < W:
                        img[yy, xx] = (80, 240, 90)

    draw(0, halfW, bis, [-j for j in bjs])                   # plan: east vs north (y up)
    draw(halfW, W - halfW, bis, bks)                          # section: east vs depth (down)
    img[:, halfW] = (40, 40, 48)                              # divider
    return img


def _main() -> int:
    import argparse
    import sys
    import time
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    ap = argparse.ArgumentParser(description='follow the passages: cave systems')
    ap.add_argument('--seed', type=int, default=3)
    ap.add_argument('--max', type=int, default=20)
    ap.add_argument('--render', action='store_true')
    a = ap.parse_args()

    lp = LayeredPlanet.earthlike(seed=a.seed)
    t0 = time.time()
    sysm = explore(lp, 35.0, 200.0, 10.0, max_chambers=a.max)
    dt = time.time() - t0

    if not sysm.nodes:
        print("  no void at the start point"); return 0
    m = sysm.measure()
    print(f"  === followed the passages from (35,200,10 m) in {dt:.1f}s ===")
    print(f"    chambers        {m['n_chambers']}")
    print(f"    passages        {m['n_passages']}  (verified void-continuous links)")
    print(f"    total volume    {m['total_volume_m3']:>12,.0f} m^3")
    print(f"    total floor     {m['total_floor_m2']:>12,.0f} m^2")
    print(f"    depth range     {m['depth_range_m'][0]:.0f} - {m['depth_range_m'][1]:.0f} m")
    print(f"    horizontal span {m['span_m'][0]:.0f} x {m['span_m'][1]:.0f} m")
    print(f"    traverse depth  {m['graph_diameter_chambers']} chambers end to end")

    if a.render:
        from pathlib import Path
        try:
            from PIL import Image
        except Exception:
            print('\n  (PIL absent -- skipping render)'); return 0
        out = Path('Saved/SplatEmit'); out.mkdir(parents=True, exist_ok=True)
        Image.fromarray(_render_map(sysm)).save(out / 'cave_system_map.png')
        print(f"\n  wrote {out}/cave_system_map.png "
              f"(left: plan east-north | right: section east-depth; disc=chamber, line=passage)")
    return 0


if __name__ == '__main__':
    raise SystemExit(_main())
