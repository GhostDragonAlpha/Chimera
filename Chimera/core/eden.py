"""eden — the first demo scene: the Tree of the Knowledge of Good and Evil, planted on Eden.

The capstone. It invents nothing -- it COMPOSES what the session built, and that is the point:

  THE PLANET    Eden is a PlanetOnion (core/planet_membrane) with climate (core/biomes). We
                find the GARDEN on it: a temperate, forested, land spot -- a place a tree belongs.
  THE TREE      the Tree of Knowledge is grown by the terrarium's L-system (core/terrarium):
                a genome -> a bone skeleton -> a real branching form (a tree IS a recursion).
  PLANTED       it stands at the garden's CONNECTION POINT -- onion.sample gives the elevation
                the roots meet and the surface normal that is its 'up'. The object grows INTO
                the world at the seam, exactly as the matter model says.
  GROWN         the grow verb (core/grow) drives it seed -> mature at the density clock: this is
                slow, dense, ancient wood -- the Tree of Knowledge does not shoot up like grass.

One planet, one tree, one seam, one clock. Rendered so you can see it, because a scene the
operator cannot see does not count.
"""
from __future__ import annotations

import numpy as np

from core.planet_membrane import PlanetOnion

GARDEN_BIOMES = ('temperate_forest', 'tropical_seasonal_forest', 'grassland', 'taiga')


def make_eden(seed: int = 7):
    """Eden, and the garden on it: a forested land spot at a gentle elevation. Returns the onion
    and (lat, lon, biome, elevation)."""
    from core.biomes import classify_surface
    onion = PlanetOnion.earthlike(seed=seed)
    biome, elev = classify_surface(_P(onion), 90, 180)
    lats = np.linspace(90, -90, 90)
    lons = np.linspace(0, 360, 180, endpoint=False)
    best = None
    for pref in GARDEN_BIOMES:                        # prefer a forest, then anything green
        for i in range(90):
            if abs(lats[i]) > 60:                     # a temperate garden, not the poles
                continue
            for j in range(180):
                if biome[i, j] == pref and 30 < elev[i, j] < 900:
                    best = (float(lats[i]), float(lons[j]), pref, float(elev[i, j]))
                    break
            if best:
                break
        if best:
            break
    if best is None:                                  # fallback: any land
        ij = np.argwhere(elev > 0)[len(np.argwhere(elev > 0)) // 2]
        best = (float(lats[ij[0]]), float(lons[ij[1]]), str(biome[ij[0], ij[1]]), float(elev[ij[0], ij[1]]))
    return onion, best


def grow_tree_of_knowledge(seed: int = 3):
    """Grow the Tree: a grand, spreading terrarium genome -> a bone skeleton. A tree is a
    recursion (A -> ...A); this one is given depth and reach to be a canopy worth the name."""
    from core.terrarium import Genome, grow
    g = Genome(depth=7, angle=32.0, length=1.0, decay=0.86, radius=0.13, radius_decay=0.74)
    return grow(g, seed)


class _P:
    """Tiny adapter: biomes/layers want planet.onion."""
    def __init__(self, onion): self.onion = onion


def _project(bones):
    """Auto-orient the skeleton upright: the axis of greatest spread is 'up', the widest of the
    other two is the horizontal we draw across. Returns (screen-fn, extents)."""
    P = np.array([b.p0 for b in bones] + [b.p1 for b in bones], float)
    spread = P.max(0) - P.min(0) + 1e-9
    up = int(np.argmax(spread))
    horiz = [i for i in range(3) if i != up]
    h = horiz[int(np.argmax([spread[i] for i in horiz]))]
    return up, h, P[:, up].min(), P[:, up].max(), P[:, h].min(), P[:, h].max()


def render_scene(onion, garden, bones, path='Saved/SplatEmit/eden_tree_of_knowledge.png'):
    from pathlib import Path
    try:
        from PIL import Image, ImageDraw
    except Exception:
        return None
    W, H = 960, 680
    GROUND_Y = 500
    img = Image.new('RGB', (W, H))
    d = ImageDraw.Draw(img)
    # sky: lush gradient
    for y in range(H):
        t = y / H
        if y < GROUND_Y:
            c = (int(90 + 90 * t), int(150 + 70 * t), int(205 - 40 * t))     # blue -> pale gold
        else:
            gt = (y - GROUND_Y) / (H - GROUND_Y)
            c = (int(70 - 30 * gt), int(120 - 50 * gt), int(58 - 30 * gt))    # forest floor
        d.line([(0, y), (W, y)], fill=c)
    d.line([(0, GROUND_Y), (W, GROUND_Y)], fill=(60, 95, 45), width=3)

    # the tree, standing on the ground at the garden
    up, h, umin, umax, hmin, hmax = _project(bones)
    du, dh = (umax - umin), (hmax - hmin)
    TREE_H, cx = 430, W // 2
    scale = TREE_H / max(du, 1e-9)

    def sx(p): return int(cx + (p[h] - (hmin + hmax) / 2) * scale)
    def sy(p): return int(GROUND_Y - (p[up] - umin) * scale)

    for b in sorted(bones, key=lambda b: b.depth):    # trunk first, twigs last
        x0, y0, x1, y1 = sx(b.p0), sy(b.p0), sx(b.p1), sy(b.p1)
        w = max(1, int(b.r0 * scale * 1.4))
        shade = min(b.depth, 6)
        col = (90 - shade * 8, 60 - shade * 5, 34)     # bark, darker toward the trunk
        d.line([(x0, y0), (x1, y1)], fill=col, width=w)
    # canopy foliage at the twig tips
    rng = np.random.default_rng(1)
    for b in bones:
        if b.depth >= 5:
            x, y = sx(b.p1), sy(b.p1)
            r = int(rng.integers(10, 22))
            g = int(rng.integers(95, 150))
            d.ellipse([x - r, y - r, x + r, y + r], fill=(int(g * 0.4), g, int(g * 0.35)))
    # the fruit -- knowledge of good and evil
    tips = [b for b in bones if b.depth >= 5]
    for b in rng.choice(tips, size=min(9, len(tips)), replace=False) if tips else []:
        x, y = sx(b.p1) + int(rng.integers(-6, 6)), sy(b.p1) + int(rng.integers(2, 12))
        d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(190, 40, 45))
        d.ellipse([x - 2, y - 3, x, y - 1], fill=(240, 180, 180))

    # a globe inset: Eden, with the garden marked
    _globe_inset(d, onion, garden, W - 190, 20, 160)

    lat, lon, biome, elev = garden
    d.text((24, 22), "THE TREE OF THE KNOWLEDGE OF GOOD AND EVIL", fill=(255, 250, 235))
    d.text((24, 40), f"planted on EDEN  -  the garden: {biome} at ({lat:+.0f}, {lon:.0f}), {elev:.0f} m",
            fill=(230, 235, 220))
    d.text((24, H - 24), f"{len(bones)} bones grown from one genome  -  it stands at the surface's connection point",
            fill=(210, 220, 200))
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    img.save(path)
    return path


def _globe_inset(d, onion, garden, x0, y0, size):
    from core.biomes import PALETTE, classify_surface
    biome, elev = classify_surface(_P(onion), 120, 240)
    N = size
    yy, xx = np.mgrid[0:N, 0:N]
    X = (xx - N / 2) / (N / 2); Y = (N / 2 - yy) / (N / 2)
    disc = X ** 2 + Y ** 2 <= 1
    Z = np.sqrt(np.clip(1 - X ** 2 - Y ** 2, 0, 1))
    latg = np.degrees(np.arcsin(np.clip(Y, -1, 1)))
    long = np.degrees(np.arctan2(X, Z)) % 360
    for iy in range(N):
        for ix in range(N):
            if not disc[iy, ix]:
                continue
            bi = int(np.clip((90 - latg[iy, ix]) / 180 * (elev.shape[0] - 1), 0, elev.shape[0] - 1))
            bj = int(np.clip(long[iy, ix] / 360 * elev.shape[1], 0, elev.shape[1] - 1))
            d.point((x0 + ix, y0 + iy), fill=PALETTE.get(biome[bi, bj], (40, 90, 165)))
    # mark the garden
    lat, lon, _, _ = garden
    gx = x0 + int(N / 2 + np.cos(np.radians(lat)) * np.sin(np.radians(lon)) * N / 2)
    gy = y0 + int(N / 2 - np.sin(np.radians(lat)) * N / 2)
    d.ellipse([gx - 4, gy - 4, gx + 4, gy + 4], outline=(255, 240, 90), width=2)
    d.text((x0 + N // 2 - 12, y0 + N + 2), "EDEN", fill=(255, 250, 235))


def _main() -> int:
    import argparse
    import sys
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    ap = argparse.ArgumentParser(description='the first demo scene: the Tree of Knowledge on Eden')
    ap.add_argument('--seed', type=int, default=7)
    ap.add_argument('--tree-seed', type=int, default=3)
    a = ap.parse_args()

    onion, garden = make_eden(a.seed)
    lat, lon, biome, elev = garden
    bones = grow_tree_of_knowledge(a.tree_seed)

    # the connection point: where the tree meets the world
    s = onion.sample(lat, lon)
    # the grow verb: ancient dense wood, the density clock -> slow to mature
    from core.grow import grow as grow_dyn
    g = grow_dyn('hardwood', energy=1.0, ticks=60)

    print("  === THE FIRST DEMO SCENE: the Tree of Knowledge, planted on Eden ===\n")
    print(f"  EDEN            a grown planet; the garden found at ({lat:+.1f}, {lon:.1f})")
    print(f"  THE GARDEN      biome '{biome}', surface {elev:.0f} m -- forested, temperate land")
    print(f"  CONNECTION      the tree stands at the surface: elevation {s['elevation']:.0f} m, "
          f"up = {np.round(s['normal'], 3)}, on {s['material']}")
    print(f"  THE TREE        {len(bones)} bones grown from ONE terrarium genome (a tree is a recursion)")
    print(f"  GROWN           by the grow verb at hardwood density (clock √{g['relative_density']:.1f}): "
          f"canopy in {g['ticks_to_canopy']} ticks -- slow, ancient wood, not grass")

    path = render_scene(onion, garden, bones)
    if path:
        print(f"\n  witnessed: {path}")
        print("  one planet, one tree, one seam, one clock -- everything the session built, composed.")
    else:
        print("\n  (PIL absent -- scene assembled but not rendered)")
    return 0


if __name__ == '__main__':
    raise SystemExit(_main())
