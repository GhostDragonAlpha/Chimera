"""fluid — the liquid genome. A fluid is neither matter nor light: it FLOWS and it lets you
see INTO it.

THE GAP THIS FILLS (2026-07-24, backlog T4). bricks.py's `fluid` port was an honest empty
set. But a space game is oceans, rivers, coolant, lava, mud -- and a liquid cannot be a
material genome (a material is an opaque surface with albedo + roughness) nor a light genome
(a fluid mostly does not emit). Its defining properties are the ones a solid does not have:

    colour        the tint the liquid adds to what is seen through it
    transparency   how far you see IN (water: far; mud: not at all)
    depth_tint     how the tint DEEPENS with thickness (shallow water is clear, deep is blue)
    surface_gloss  specular sharpness of the surface (a mirror-calm pool vs a churned one)
    flow           directional bias of the surface (a river flows one way; a pool is still)
    viscosity      how it spreads and pools (water thin and flat; lava and mud thick and mounded)

A fluid POOLS -- it is a near-horizontal translucent layer, not a 3D lump (matter) or a bolt
(light). emit_fluid draws that layer: low alpha (you see through it), tinted, the tint
deepening toward the thick centre, the surface facing up. The existing rasterizer already
composites translucency and shades a surface, so a fluid needs far less special-casing than
the emissive family did -- only lava carries a small emission (molten rock genuinely glows).

HONEST INTAKE STATUS: AUTHORED from fluid appearance, not MEASURED -- the same legitimate
second intake as emissive. Refraction (bending what is seen through the surface) is NOT
modelled; that needs background sampling and is a future upgrade. A fluid here is a tinted
translucent layer with a shaded surface, which reads as water/lava/mud but is not a
physically-refractive render.
"""
from __future__ import annotations

import numpy as np

FLUID_SCHEMA = {
    'r': (0.0, 1.0), 'g': (0.0, 1.0), 'b': (0.0, 1.0),
    'transparency':  (0.0, 0.9),   # 0 = opaque (mud), 0.9 = glass-clear (water)
    'depth_tint':    (0.0, 1.0),   # how much the tint deepens with thickness
    'surface_gloss': (0.0, 1.0),   # specular sharpness (recorded; specular is a future render pass)
    'flow':          (0.0, 1.0),   # directional bias of the surface
    'viscosity':     (0.0, 1.0),   # 0 = thin and flat, 1 = thick and mounded
    'emission':      (0.0, 2.0),   # >0 only for molten fluids (lava) -- most fluids do not emit
}

ARCHETYPES = {
    'water':   dict(r=0.10, g=0.30, b=0.52, transparency=0.78, depth_tint=0.70,
                    surface_gloss=0.92, flow=0.30, viscosity=0.08, emission=0.0),
    'ocean':   dict(r=0.05, g=0.22, b=0.45, transparency=0.60, depth_tint=0.92,
                    surface_gloss=0.85, flow=0.55, viscosity=0.10, emission=0.0),
    'lava':    dict(r=0.95, g=0.40, b=0.10, transparency=0.06, depth_tint=0.30,
                    surface_gloss=0.35, flow=0.40, viscosity=0.85, emission=1.4),
    'mud':     dict(r=0.34, g=0.25, b=0.16, transparency=0.10, depth_tint=0.40,
                    surface_gloss=0.18, flow=0.20, viscosity=0.70, emission=0.0),
    'coolant': dict(r=0.20, g=0.70, b=0.72, transparency=0.62, depth_tint=0.55,
                    surface_gloss=0.70, flow=0.35, viscosity=0.15, emission=0.0),
}


def seed_genome(name: str = 'water') -> dict:
    if name not in ARCHETYPES:
        raise KeyError(f'no fluid archetype {name!r}; have {sorted(ARCHETYPES)}')
    return dict(ARCHETYPES[name])


def recombine(a: dict, b: dict, t: float = 0.5) -> dict:
    return {k: float(a[k] * (1 - t) + b[k] * t) for k in FLUID_SCHEMA}


def emit_fluid(genome: dict, n_splats: int = 500, seed: int = 0) -> dict:
    """A fluid genome -> a renderable translucent pooled layer.

    Splats fill a near-horizontal disk (a fluid finds its level); viscosity mounds the centre
    (thin water stays flat, thick lava/mud domes). Alpha comes from transparency -- a clear
    fluid lets the background through -- and the tint DEEPENS toward the thick centre by
    depth_tint, which is why shallow edges read lighter than the deep middle. The surface
    faces up so the existing Lambert term shades it.
    """
    from core.splat_types import emit_surface

    rng = np.random.default_rng(seed)
    g = genome
    visc = float(g['viscosity'])

    # a disk in the XY plane, denser toward the centre
    ang = rng.uniform(0, 2 * np.pi, n_splats)
    rad = np.sqrt(rng.uniform(0, 1, n_splats))
    x = rad * np.cos(ang)
    y = rad * np.sin(ang)
    # viscosity mounds the centre; flow tilts the surface slightly along +X
    z = visc * 0.35 * (1.0 - rad) + float(g['flow']) * 0.06 * x
    z += rng.normal(0, 0.01, n_splats)                 # a little surface chop
    pos = np.stack([x, y, z], 1)

    # tint deepens toward the thick centre (1-rad), by depth_tint
    base = np.array([g['r'], g['g'], g['b']], dtype=np.float64)
    deep = base * (0.45 + 0.55 * (1.0 - float(g['depth_tint'])))   # deep = darker/more saturated
    mix = (float(g['depth_tint']) * (1.0 - rad))[:, None]
    rgb = np.clip(base[None, :] * (1 - mix) + deep[None, :] * mix, 0, 1)

    # alpha from transparency: a clearer fluid is LESS opaque per splat
    alpha = np.full(n_splats, 1.0 - 0.85 * float(g['transparency']))

    dirs = np.tile([0.0, 0.0, 1.0], (n_splats, 1))     # surface faces up
    cov = emit_surface(dirs, tangent_scale=0.05, normal_scale=0.012)

    out = {
        'pos': pos, 'normal': dirs, 'cov': cov,
        'albedo': rgb.astype(np.float32),
        'alpha': np.clip(alpha, 0.05, 1.0).astype(np.float32),
        'kind': 'fluid',
    }
    if float(g['emission']) > 0.0:                     # molten fluids glow (lava)
        em = float(g['emission']) * (0.4 + 0.6 * (1.0 - rad))
        out['emission'] = np.clip(em, 0.0, 2.0).astype(np.float32)
    return out


def propose(n: int = 8, seed: int = 0) -> list:
    """N admissible fluid fillings for a `fluid` stud, each measured, ranked, never chosen."""
    names = list(ARCHETYPES)
    rng = np.random.default_rng(seed)
    out = []
    for i in range(n):
        a, b = (names[int(rng.integers(len(names)))] for _ in range(2))
        t = float(rng.uniform(0, 1))
        g = recombine(ARCHETYPES[a], ARCHETYPES[b], t)
        out.append({
            'parents': (a, b), 'blend': round(t, 3),
            'colour': [round(float(g[c]), 3) for c in 'rgb'],
            'transparency': round(float(g['transparency']), 3),
            'viscosity': round(float(g['viscosity']), 3),
            'molten': float(g['emission']) > 0.1,
            'genome': g, 'seed': seed + i,
        })
    # ranked by measurable facts: clearer first (more "fluid-like"), then thinner.
    out.sort(key=lambda c: (-c['transparency'], c['viscosity']))
    return out


def facts(genome: dict, seed: int = 0) -> dict:
    sp = emit_fluid(genome, 300, seed)
    ext = sp['pos'].max(0) - sp['pos'].min(0)
    return {
        'mean_alpha': float(sp['alpha'].mean()),
        'flatness': float(np.hypot(ext[0], ext[1]) / max(ext[2], 1e-6)),   # high = a flat pool
        'molten': 'emission' in sp,
        'colour': [round(float(genome[c]), 3) for c in 'rgb'],
    }


def _main() -> int:
    import argparse
    import sys
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    argparse.ArgumentParser(description='the liquid genome').parse_args()
    print('  FLUID ARCHETYPES (authored from fluid appearance):')
    for name in ARCHETYPES:
        f = facts(seed_genome(name))
        print(f"    {name:9} colour {f['colour']}  mean_alpha {f['mean_alpha']:.2f}  "
              f"flatness {f['flatness']:.1f}  {'MOLTEN (glows)' if f['molten'] else ''}")
    print('\n  eight proposed fluid fillings (recombined), ranked:')
    for i, c in enumerate(propose(8)):
        print(f"    {i}  {c['parents'][0]:8} x {c['parents'][1]:8} "
              f"transparency {c['transparency']:.2f}  viscosity {c['viscosity']:.2f}"
              f"{'  molten' if c['molten'] else ''}")
    return 0


if __name__ == '__main__':
    raise SystemExit(_main())
