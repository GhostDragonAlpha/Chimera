"""membrane_shapes — the CONTAINER you train against.

THE PROBLEM THIS SOLVES, measured 2026-07-23:
    rebuild_world's terrain seeded 300 random blobs into a 256^3 grid and asked the
    Cellular Potts shaker to anneal them. Result: 22% of columns carried any matter at
    all, spread over a 2,000-unit vertical range. The physics ran correctly and produced
    noise, because there was no boundary to converge on. "Extract the surface" has no
    defined answer when there is no defined shape.

THE FIX: start from a MEMBRANE — a simple parametric shape you choose — and let the
matter model and the trained splat compositions fill and texture it. The membrane is a
boundary condition, and a boundary is what makes a result attributable. Same principle as
core/membrane.py for infrastructure, applied to geometry.

    membrane = sphere(radius=100, n=20000)      # or plane / cylinder / box / dome
    splats   = clothe(membrane, material='cluster_07')
    render_orbit(splats)

Every membrane returns the same contract:
    {'pos': (N,3), 'normal': (N,3), 'name': str, 'params': dict}

so anything downstream (splat emission, matter growth, ML refinement) can consume any
shape without knowing which one it got.
"""
from __future__ import annotations

import numpy as np

# ---------------------------------------------------------------------------
# PRIMITIVES — each returns surface points with outward normals
# ---------------------------------------------------------------------------


def sphere(radius: float = 100.0, n: int = 20_000, seed: int = 0) -> dict:
    """Fibonacci sphere — even coverage, no pole clustering."""
    i = np.arange(n, dtype=np.float64) + 0.5
    phi = np.arccos(1 - 2 * i / n)                 # polar, area-uniform
    theta = np.pi * (1 + 5 ** 0.5) * i             # golden angle
    d = np.stack([np.cos(theta) * np.sin(phi),
                  np.sin(theta) * np.sin(phi),
                  np.cos(phi)], 1)
    return {'pos': d * radius, 'normal': d, 'name': 'sphere',
            'params': {'radius': radius, 'n': n}}


def plane(size: float = 1000.0, n: int = 20_000, seed: int = 0) -> dict:
    """Flat ground membrane. The honest baseline: no relief, but CLOSED and complete."""
    k = int(np.sqrt(n))
    xs = np.linspace(-size, size, k)
    xx, yy = np.meshgrid(xs, xs)
    pos = np.stack([xx.ravel(), yy.ravel(), np.zeros(xx.size)], 1)
    nrm = np.zeros_like(pos); nrm[:, 2] = 1.0
    return {'pos': pos, 'normal': nrm, 'name': 'plane',
            'params': {'size': size, 'n': pos.shape[0]}}


def cylinder(radius: float = 50.0, height: float = 200.0, n: int = 20_000,
             seed: int = 0, caps: bool = True) -> dict:
    """Trunk / pillar / hull section."""
    rng = np.random.default_rng(seed)
    n_side = int(n * 0.85) if caps else n
    th = rng.uniform(0, 2 * np.pi, n_side)
    z = rng.uniform(-height / 2, height / 2, n_side)
    d = np.stack([np.cos(th), np.sin(th), np.zeros(n_side)], 1)
    pos = d * radius; pos[:, 2] = z
    nrm = d.copy()
    if caps:
        n_cap = n - n_side
        for sign in (1, -1):
            m = n_cap // 2
            r = radius * np.sqrt(rng.uniform(0, 1, m))
            a = rng.uniform(0, 2 * np.pi, m)
            cp = np.stack([r * np.cos(a), r * np.sin(a),
                           np.full(m, sign * height / 2)], 1)
            cn = np.zeros_like(cp); cn[:, 2] = sign
            pos = np.vstack([pos, cp]); nrm = np.vstack([nrm, cn])
    return {'pos': pos, 'normal': nrm, 'name': 'cylinder',
            'params': {'radius': radius, 'height': height, 'n': pos.shape[0]}}


def box(size=(100.0, 100.0, 100.0), n: int = 20_000, seed: int = 0) -> dict:
    """Crate / hull panel / shelter block."""
    rng = np.random.default_rng(seed)
    sx, sy, sz = (np.asarray(size, dtype=float) / 2.0)
    areas = np.array([sy * sz, sy * sz, sx * sz, sx * sz, sx * sy, sx * sy])
    counts = np.floor(areas / areas.sum() * n).astype(int)
    axes = [(0, 1), (0, -1), (1, 1), (1, -1), (2, 1), (2, -1)]
    P, Nrm = [], []
    half = np.array([sx, sy, sz])
    for (ax, sign), c in zip(axes, counts):
        if c <= 0:
            continue
        p = rng.uniform(-1, 1, (c, 3)) * half
        p[:, ax] = sign * half[ax]
        nn = np.zeros((c, 3)); nn[:, ax] = sign
        P.append(p); Nrm.append(nn)
    return {'pos': np.vstack(P), 'normal': np.vstack(Nrm), 'name': 'box',
            'params': {'size': tuple(map(float, size)), 'n': int(sum(counts))}}


def dome(radius: float = 500.0, n: int = 20_000, seed: int = 0) -> dict:
    """Ground you can stand on with relief: the upper half of a sphere, flattened."""
    s = sphere(radius, n * 2, seed)
    keep = s['pos'][:, 2] >= 0
    pos = s['pos'][keep].copy(); nrm = s['normal'][keep].copy()
    pos[:, 2] *= 0.25                                    # flatten to a landscape
    nrm[:, 2] *= 4.0
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-9
    return {'pos': pos, 'normal': nrm, 'name': 'dome',
            'params': {'radius': radius, 'n': int(keep.sum())}}


SHAPES = {'sphere': sphere, 'plane': plane, 'cylinder': cylinder, 'box': box, 'dome': dome}


# ---------------------------------------------------------------------------
# DISPLACEMENT — where ML will act. The membrane is the domain; this is the field.
# ---------------------------------------------------------------------------


def displace(membrane: dict, amplitude: float = 0.0, frequency: float = 3.0,
             octaves: int = 3, seed: int = 0) -> dict:
    """Push the membrane along its normals by a smooth multi-octave field.

    amplitude=0 returns the membrane untouched. This is the knob a trainer turns:
    the SHAPE is given (the membrane), the RELIEF is learned. Separating them is what
    makes the result attributable -- a bad surface is now either a wrong membrane or a
    wrong field, and you can tell which.
    """
    if amplitude == 0.0:
        return membrane
    rng = np.random.default_rng(seed)
    p = membrane['pos']
    scale = np.abs(p).max() + 1e-9
    h = np.zeros(len(p))
    amp, freq = 1.0, frequency
    for _ in range(octaves):
        ph = rng.uniform(0, 2 * np.pi, 3)
        h += amp * np.sin(freq * p[:, 0] / scale + ph[0]) \
                 * np.sin(freq * p[:, 1] / scale + ph[1]) \
                 * np.cos(freq * p[:, 2] / scale + ph[2])
        amp *= 0.5; freq *= 2.0
    h /= (np.abs(h).max() + 1e-9)
    out = dict(membrane)
    out['pos'] = p + membrane['normal'] * (h * amplitude)[:, None]
    out['params'] = {**membrane.get('params', {}),
                     'displace': {'amplitude': amplitude, 'frequency': frequency,
                                  'octaves': octaves, 'seed': seed}}
    return out


# ---------------------------------------------------------------------------
# CLOTHE — dress a membrane in a material's TRAINED splat composition
# ---------------------------------------------------------------------------


def clothe(membrane: dict, material: str = 'sand', splat_scale: float = 1.0,
           seed: int = 0) -> dict:
    """Emit splats over a membrane using the material's trained composition.

    This is where the two halves meet: the membrane says WHERE matter is, the trained
    composition (measured from a real scan, via Construction/export_genome.py) says WHAT
    it looks like.
    """
    from core.splat_level import _get_optical, _get_composition
    from core.splat_types import (emit_surface, emit_fiber, emit_point, emit_shell,
                                  emit_beam, emit_cloud, emit_glow)

    pos = np.asarray(membrane['pos'], dtype=np.float64)
    nrm = np.asarray(membrane['normal'], dtype=np.float64)
    n = len(pos)
    s = splat_scale

    emitters = {
        'surface': lambda v, k: emit_surface(v, tangent_scale=s*1.5*k, normal_scale=s*0.5*k),
        'fiber':   lambda v, k: emit_fiber(v, tangent_scale=s*1.5*k, normal_scale=s*0.5*k,
                                           fiber_dir=np.roll(v, 1, axis=1)),
        'point':   lambda v, k: emit_point(np.zeros_like(v), radius=s*k),
        'shell':   lambda v, k: emit_shell(np.zeros_like(v), v, thickness=s*0.2*k, spread=s*k),
        'beam':    lambda v, k: emit_beam(v, length=s*3.0*k, thickness=s*0.3*k),
        'cloud':   lambda v, k: emit_cloud(np.zeros_like(v), radius=s*2.0*k, alpha=0.1),
        'glow':    lambda v, k: emit_glow(np.zeros_like(v), radius=s*k),
    }

    layers = _get_composition(material)
    tot = sum(l['weight'] for l in layers) or 1.0
    pick = np.random.default_rng(seed).choice(
        len(layers), size=n, p=[l['weight'] / tot for l in layers])

    cov = np.zeros((n, 3, 3))
    for li, layer in enumerate(layers):
        m = pick == li
        if not m.any():
            continue
        cov[m] = emitters.get(layer['type'], emitters['surface'])(
            nrm[m], float(layer.get('scale', 1.0)))

    opt = _get_optical(material)
    return {
        'pos': pos, 'normal': nrm, 'cov': cov,
        'albedo': np.tile(opt['albedo'], (n, 1)),
        'roughness': np.full(n, opt['roughness']),
        'alpha': np.full(n, opt['alpha']),
        'subsurface': np.full(n, opt['subsurface']),
        'metallic': np.full(n, opt.get('metallic', 0.0)),
        '_membrane': membrane.get('name'),
        '_material': material,
        '_layers': layers,
    }


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description='Build a membrane, clothe it, render it.')
    ap.add_argument('shape', choices=sorted(SHAPES), nargs='?', default='sphere')
    ap.add_argument('--material', default='cluster_07')
    ap.add_argument('--n', type=int, default=20000)
    ap.add_argument('--amplitude', type=float, default=0.0)
    ap.add_argument('--splat-scale', type=float, default=2.0)
    ap.add_argument('--views', type=int, default=6)
    ap.add_argument('--out', default='Saved/SplatEmit/membrane.png')
    a = ap.parse_args()

    mem = SHAPES[a.shape](n=a.n)
    if a.amplitude:
        mem = displace(mem, amplitude=a.amplitude)
    print(f'membrane {mem["name"]}: {len(mem["pos"]):,} points  {mem["params"]}')

    sp = clothe(mem, material=a.material, splat_scale=a.splat_scale)
    print(f'clothed in {a.material}: '
          + ' + '.join(f"{l['type']}({l['weight']:.0%})" for l in sp['_layers']))

    from core.render_world import render_orbit
    render_orbit(sp, out_path=a.out, n_views=a.views)


if __name__ == '__main__':
    main()
