"""scene3d -- the engine's OWN rendering of a game scene.

Not a plot of the data, not a hand-drawn stand-in: a camera placed INSIDE the world the
ChimeraEngine holds, rendering what it sees. It consumes the REAL data and nothing else --
  * the planet onion's real elevation (core/planet_membrane) for the ground it stands on,
  * the garden's real biome colour (core/biomes) for that ground,
  * the Tree's real 3D bone skeleton (core/terrarium) for the object in front of it,
  * a sun for light.
A software rasteriser: a perspective camera, painter-sorted filled terrain, the Tree in true
perspective, a ground shadow, distance haze. Early fidelity -- but it is the SCENE, from the
WORLD, not a puppet. `render()` = one frame; `turntable()` = orbit it into a GIF.
"""
from __future__ import annotations

import numpy as np

R_PLANET = 6.371e6          # m -- local lat/lon <-> metres (Earth-like onion)
TREE_H_M = 11.0             # the Tree of Knowledge stands ~11 m
SUN = np.array([-0.55, 0.35, 0.80]); SUN /= np.linalg.norm(SUN)   # warm light, up-left
SKY_TOP = np.array([70, 116, 180]); SKY_HORIZON = np.array([196, 206, 214])
HAZE = np.array([200, 210, 216])    # distance fades to this


class Camera:
    def __init__(self, eye, target, up=(0, 0, 1), fov_deg=58, w=1000, h=680):
        self.eye = np.array(eye, float)
        f = np.array(target, float) - self.eye; f /= np.linalg.norm(f)
        r = np.cross(f, np.array(up, float)); r /= np.linalg.norm(r)
        u = np.cross(r, f)
        self.f, self.r, self.u, self.w, self.h = f, r, u, w, h
        self.foc = (w / 2) / np.tan(np.radians(fov_deg) / 2)

    def project(self, P):
        """(N,3) world -> (N,3) screen (sx, sy, depth-forward)."""
        d = np.atleast_2d(P) - self.eye
        cf, cr, cu = d @ self.f, d @ self.r, d @ self.u
        z = np.where(cf > 1e-6, cf, 1e-6)
        return np.stack([self.w / 2 + self.foc * cr / z,
                         self.h / 2 - self.foc * cu / z, cf], 1)


def _sky(w, h, cam):
    """Vertical gradient + the yellow sun glow, by camera pitch."""
    img = np.zeros((h, w, 3), np.uint8)
    t = (np.arange(h) / h)[:, None]
    img[:] = (SKY_TOP * (1 - t) + SKY_HORIZON * t).astype(np.uint8)[:, None, :]
    s = cam.project(cam.eye + SUN * 4000.0)[0]
    if s[2] > 0:
        yy, xx = np.mgrid[0:h, 0:w]
        d2 = (xx - s[0]) ** 2 + (yy - s[1]) ** 2
        glow = np.clip(1 - d2 / (240.0 ** 2), 0, 1)[:, :, None]
        img = (img * (1 - glow) + np.array([255, 241, 196]) * glow).astype(np.uint8)
        img = np.where((d2 < 24 ** 2)[:, :, None], np.array([255, 252, 235], np.uint8), img)
    return img


def _terrain(onion, garden, ext=340.0, n=30):
    """Sample the REAL onion elevation on a local grid around the garden -> world verts (metres)."""
    lat0, lon0, _, elev0 = garden
    clat = max(0.05, np.cos(np.radians(lat0)))
    es = np.linspace(-ext, ext, n)
    Z = np.zeros((n, n))
    for i, nn in enumerate(np.linspace(-ext, ext, n)):
        for j, ee in enumerate(es):
            lat = lat0 + np.degrees(nn / R_PLANET)
            lon = (lon0 + np.degrees(ee / (R_PLANET * clat))) % 360
            Z[i, j] = onion.sample(lat, lon)['elevation'] - elev0
    X, Y = np.meshgrid(es, np.linspace(-ext, ext, n))
    return np.stack([X, Y, Z], -1)              # (n,n,3): x=east, y=north, z=up


def _biome_rgb(onion, garden):
    from core.biomes import PALETTE
    return np.array(PALETTE.get(garden[2], (70, 120, 60)), float)


def _tree_world(bones, height_m=TREE_H_M):
    """Orient the real 3D bones upright, scale to height_m, base on the ground at the origin."""
    from core.eden import _project
    up, h, umin, umax, hmin, hmax = _project(bones)
    third = [i for i in range(3) if i not in (up, h)][0]
    s = height_m / max(umax - umin, 1e-9)
    P = np.array([b.p0 for b in bones] + [b.p1 for b in bones])
    tmid = (P[:, third].min() + P[:, third].max()) / 2

    def tw(p):
        return np.array([(p[h] - (hmin + hmax) / 2) * s, (p[third] - tmid) * s, (p[up] - umin) * s])
    return tw


def _scene(onion, garden, bones):
    return _biome_rgb(onion, garden), _terrain(onion, garden), _tree_world(bones)


def render_frame(cam, V, base, tw, bones, w, h, extra_trees=None):
    from PIL import Image, ImageDraw
    img = Image.fromarray(_sky(w, h, cam))
    d = ImageDraw.Draw(img, 'RGBA')
    n = V.shape[0]

    cells = []                                  # painter-sorted filled terrain quads
    for i in range(n - 1):
        for j in range(n - 1):
            quad = np.array([V[i, j], V[i, j + 1], V[i + 1, j + 1], V[i + 1, j]])
            nrm = np.cross(quad[1] - quad[0], quad[3] - quad[0]); nl = np.linalg.norm(nrm)
            if nl < 1e-9:
                continue
            lam = 0.45 + 0.55 * max(0.0, float((nrm / nl) @ SUN))
            sc = cam.project(quad)
            if (sc[:, 2] <= 0.3).any():
                continue
            depth = float(sc[:, 2].mean())
            fog = float(np.clip((depth - 40) / 320.0, 0, 0.82))
            col = base * lam * (1 - fog) + HAZE * fog
            col = np.clip(col + ((i + j) % 2) * 4 - 2, 0, 255)
            cells.append((depth, [(float(p[0]), float(p[1])) for p in sc], tuple(col.astype(int))))
    for _, poly, col in sorted(cells, key=lambda c: -c[0]):
        d.polygon(poly, fill=col + (255,))

    shad = cam.project(np.array([[0.0, 0.0, 0.05]]))[0]     # ground shadow: the sun is blocked
    if shad[2] > 0.3:
        rx = 3.4 * cam.foc / max(shad[2], 0.5); ry = rx * 0.30
        d.ellipse([shad[0] - rx, shad[1] - ry, shad[0] + rx, shad[1] + ry], fill=(22, 42, 22, 95))

    prims = []                                  # the Tree: real bones, true perspective
    rng = np.random.default_rng(1)

    def tree_prims(tw_i, bones_i, off=(0.0, 0.0, 0.0), fruit=True):
        """One grown tree's prims at a world offset -- the stand is the same L-system, many times."""
        ox, oy, oz = off
        for b in bones_i:
            p0 = np.array(tw_i(b.p0)) + (ox, oy, oz)
            p1 = np.array(tw_i(b.p1)) + (ox, oy, oz)
            s0, s1 = cam.project(p0)[0], cam.project(p1)[0]
            if s0[2] <= 0.3 and s1[2] <= 0.3:
                continue
            depth = (s0[2] + s1[2]) / 2
            wpx = max(1, int(b.r0 * TREE_H_M * cam.foc / max(depth, 0.5) * 0.9))
            shade = min(b.depth, 6)
            prims.append((depth, 'line', (float(s0[0]), float(s0[1]), float(s1[0]), float(s1[1])),
                          (90 - shade * 8, 60 - shade * 5, 34), wpx))
        tips = [b for b in bones_i if b.depth >= 5]
        for b in tips:
            s1 = cam.project(np.array(tw_i(b.p1)) + (ox, oy, oz))[0]
            if s1[2] <= 0.3:
                continue
            rad = max(3, int(0.55 * cam.foc / max(s1[2], 0.5)))
            g = int(rng.integers(95, 150))
            prims.append((s1[2] + 0.3, 'leaf', (float(s1[0]), float(s1[1])),
                          (int(g * 0.4), g, int(g * 0.35)), rad))
        if fruit:
            for b in (rng.choice(tips, size=min(10, len(tips)), replace=False) if tips else []):
                s1 = cam.project(np.array(tw_i(b.p1)) + (ox, oy, oz))[0]
                if s1[2] <= 0.3:
                    continue
                rad = max(2, int(0.16 * cam.foc / max(s1[2], 0.5)))
                prims.append((s1[2] - 0.2, 'fruit', (float(s1[0]), float(s1[1])), (198, 42, 46), rad))

    tree_prims(tw, bones)                           # the Tree of Knowledge, prominent, at the origin
    for tw_i, bones_i, x, y, z in (extra_trees or []):   # THE STAND: the garden's biome IS a forest
        tree_prims(tw_i, bones_i, (x, y, z), fruit=False)
    # depth fog on the vegetation, the same haze the terrain already wears: the frame's far
    # trees melt into the distance, which is how a stand reads as a forest and not a lineup.
    fogged = []
    for depth, kind, geo, col, size in prims:
        fog = float(np.clip((depth - 40) / 320.0, 0, 0.82))
        col = tuple(np.clip(np.array(col, float) * (1 - fog) + HAZE * fog, 0, 255).astype(int))
        fogged.append((depth, kind, geo, col, size))
    prims = fogged
    for depth, kind, geo, col, size in sorted(prims, key=lambda p: -p[0]):
        if kind == 'line':
            d.line(geo, fill=col + (255,), width=size)
        else:
            x, y = geo
            d.ellipse([x - size, y - size, x + size, y + size], fill=col + (235 if kind == 'leaf' else 255,))
    return img


def _terrain_z(V, x, y):
    """The ground's real elevation at an (east, north) offset -- nearest node of the sampled grid."""
    es, nn = V[0, :, 0], V[:, 0, 1]
    j = int(np.argmin(np.abs(es - x)))
    i = int(np.argmin(np.abs(nn - y)))
    return float(V[i, j, 2])


def grow_stand(n=11, seed=12):
    """THE STAND (the dyad's FAIL_RESTART, 0.25: one specimen on empty ground cannot read as
    'a garden FULL of vegetation' -- and the garden's biome IS a forest). The same terrarium
    L-system grown at varied genomes: a stand of trees, not a puppet copied N times. Returns
    [(tw_i, bones_i, x, y)] on golden-angle spiral offsets, biased ahead of the camera."""
    from core.terrarium import Genome, grow
    rng = np.random.default_rng(seed)
    stand = []
    for k in range(n):
        a = k * 2.399963                            # golden angle: uniform, unsynchronized spacing
        r = 9.0 + 6.0 * k
        x, y = r * np.cos(a), 8.0 + r * np.sin(a)
        g = Genome(depth=6, angle=float(26 + rng.uniform(0, 14)), length=1.0, decay=0.86,
                   radius=0.13, radius_decay=0.74)
        tb = grow(g, seed=11 + k)
        stand.append((_tree_world(tb, height_m=float(rng.uniform(7, 13))), tb, float(x), float(y)))
    return stand


def render(onion, garden, bones, path='Saved/SplatEmit/eden_scene3d.png', w=1000, h=680,
           stand=True):
    from pathlib import Path
    from PIL import ImageDraw
    base, V, tw = _scene(onion, garden, bones)
    extra = None
    if stand:
        extra = [(tw_i, tb, x, y, _terrain_z(V, x, y)) for tw_i, tb, x, y in grow_stand()]
    cam = Camera(eye=(0.0, -22.0, 2.2), target=(0.0, 6.0, 5.0), fov_deg=58, w=w, h=h)
    img = render_frame(cam, V, base, tw, bones, w, h, extra_trees=extra)
    d = ImageDraw.Draw(img, 'RGBA')
    d.text((22, 20), "EDEN  -  a scene the engine rendered, standing in the world", fill=(255, 250, 235, 255))
    d.text((22, 38), f"real onion elevation - {garden[2]} - {len(bones)} bones"
                     + (f" + a stand of {len(extra)} grown trees" if extra else ""),
           fill=(235, 240, 228, 230))
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    img.convert('RGB').save(path)
    return path


def turntable(onion, garden, bones, path='Saved/SplatEmit/eden_scene3d.gif',
              frames=20, w=680, h=460):
    """Orbit the camera around the Tree; save the engine's view as an animated GIF."""
    from pathlib import Path
    from PIL import Image
    base, V, tw = _scene(onion, garden, bones)
    rad, hgt = 14.5, 2.2
    imgs = []
    for k in range(frames):
        a = 2 * np.pi * k / frames
        cam = Camera(eye=(rad * np.sin(a), -rad * np.cos(a), hgt),
                     target=(0.0, 0.0, 5.0), fov_deg=58, w=w, h=h)
        imgs.append(render_frame(cam, V, base, tw, bones, w, h)
                    .convert('RGB').convert('P', palette=Image.ADAPTIVE, colors=128))
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    imgs[0].save(path, save_all=True, append_images=imgs[1:], duration=90, loop=0, optimize=True)
    return path


def _main() -> int:
    import sys
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    from core.eden import grow_tree_of_knowledge, make_eden
    onion, garden, _ = make_eden(7, lush=True)
    bones = grow_tree_of_knowledge(3)
    print(f"  engine's view: garden {garden[2]} at ({garden[0]:+.0f},{garden[1]:.0f}), {len(bones)} bones")
    print(f"  still     -> {render(onion, garden, bones)}")
    print(f"  turntable -> {turntable(onion, garden, bones)}")
    return 0


if __name__ == '__main__':
    raise SystemExit(_main())
