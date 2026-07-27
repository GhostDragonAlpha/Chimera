"""emissive — the light genome. Light is NOT matter, so it needs its own family.

THE GAP THIS FILLS (2026-07-24, backlog T4). bricks.py's `energy` port returned an honest
empty set: nothing in the library EMITS. But a laser, an engine glow, a muzzle flash, a fire
are as much a part of a space game as rock and metal -- and they cannot be described by a
material genome, because a material genome is albedo + roughness + metalness, and light has
none of those. A photon does not reflect; it IS the source.

So this is a SEPARATE genome family, over the fields light actually has (CLAUDE.md's spec):

    colour        the emission hue (as EMISSION, HDR-capable -- intensity can exceed 1)
    intensity     brightness multiplier
    falloff       how brightness drops from the core outward (a plasma bolt: bright core,
                  dim halo)
    elongation    axis stretch -- 1 = isotropic (fire), 12 = a drawn line (a laser is a fire
                  genome stretched along one axis and recoloured, per CLAUDE.md)
    core_gradient how the colour whitens toward the core (white-hot centre -> red edge)
    lifetime      fade time (for animation; a static render uses the full life)

A SPLAT IS THE RIGHT PRIMITIVE for this: an anisotropic blob with a radial falloff IS a
plasma bolt. The same rasterizer draws it; only the SHADING differs -- emissive splats skip
the Lambert term (light emits, it does not reflect) and render additive.

HONEST INTAKE STATUS: these archetypes are AUTHORED from emission physics, not MEASURED --
the legitimate second intake method (CLAUDE.md: authored vs measured, both feed one
codebook). The real captured references exist (WorldModel/training_data/downloads/fx/
flame.splatv, sear.splatv) but .splatv is a 4D animated volume with a 396 KB per-frame
header; recovering a measured emissive genome from it is a future upgrade, and until then
this says AUTHORED and does not pretend otherwise.
"""
from __future__ import annotations

import numpy as np

# base emission colour + the five shape fields. Colour is stored as a hue the archetype sets;
# intensity carries the HDR brightness separately so a dim red and a bright red share a hue.
EMISSIVE_SCHEMA = {
    'r': (0.0, 1.0), 'g': (0.0, 1.0), 'b': (0.0, 1.0),
    'intensity':     (0.6, 4.0),      # HDR: >1 blooms
    'falloff':       (0.8, 4.0),      # radial brightness exponent; high = tight core
    'elongation':    (1.0, 12.0),     # 1 = fire, 12 = laser
    'core_gradient': (0.0, 1.0),      # 0 = flat colour, 1 = white-hot core
    'lifetime':      (0.1, 3.0),      # animation fade; static render ignores
}

# AUTHORED archetypes, each grounded in what the thing physically IS.
ARCHETYPES = {
    'laser':       dict(r=0.95, g=0.15, b=0.20, intensity=3.4, falloff=3.2,
                        elongation=11.0, core_gradient=0.25, lifetime=0.3),
    'plasma_bolt': dict(r=0.35, g=0.55, b=1.00, intensity=3.6, falloff=2.2,
                        elongation=4.5, core_gradient=0.6, lifetime=0.5),
    'fire':        dict(r=1.00, g=0.55, b=0.15, intensity=2.1, falloff=1.4,
                        elongation=1.3, core_gradient=0.85, lifetime=1.6),
    'engine_glow': dict(r=0.45, g=0.65, b=1.00, intensity=2.6, falloff=1.8,
                        elongation=3.0, core_gradient=0.4, lifetime=3.0),
}


def seed_genome(name: str = 'laser') -> dict:
    if name not in ARCHETYPES:
        raise KeyError(f'no emissive archetype {name!r}; have {sorted(ARCHETYPES)}')
    return dict(ARCHETYPES[name])


def recombine(a: dict, b: dict, t: float = 0.5) -> dict:
    """Blend two emissive archetypes -- a plasma-tinged laser, a fiery engine glow. The same
    "genomes are a range you draw new members from" idea, on the light family."""
    return {k: float(a[k] * (1 - t) + b[k] * t) for k in EMISSIVE_SCHEMA}


def emit_emissive(genome: dict, n_splats: int = 400, seed: int = 0) -> dict:
    """A light genome -> renderable emissive splats.

    Splats are laid along the elongation axis (+Z) with a radial spread, each carrying an
    `emission` brightness that falls off from the core (radially by `falloff`, and toward the
    ends). The colour whitens toward the bright core by `core_gradient`. The covariance is
    anisotropic -- long along the axis, thin across it -- so a high-elongation genome draws a
    line and a low one draws a blob, with no branching in this function.
    """
    from core.splat_types import emit_fiber

    rng = np.random.default_rng(seed)
    g = genome
    elong = float(g['elongation'])

    # position: z along the axis (dimmer toward the ends), radius small and shrinking with |z|
    z = rng.uniform(-1.0, 1.0, n_splats)
    taper = 1.0 - 0.6 * np.abs(z)                       # the bolt narrows toward its tips
    ang = rng.uniform(0, 2 * np.pi, n_splats)
    rad = 0.14 * taper * np.sqrt(rng.uniform(0, 1, n_splats))
    pos = np.stack([rad * np.cos(ang), rad * np.sin(ang), z * elong * 0.12], 1)

    # brightness: bright core, falling off radially and toward the ends.
    r_norm = rad / (0.14 + 1e-9)
    bright = (1.0 - r_norm) ** float(g['falloff']) * taper
    emission = float(g['intensity']) * np.clip(bright, 0.02, 1.0)

    # colour: base hue, whitened toward the core by core_gradient.
    base = np.array([g['r'], g['g'], g['b']], dtype=np.float64)
    white = np.ones(3)
    mix = (float(g['core_gradient']) * (1.0 - r_norm))[:, None]
    rgb = base[None, :] * (1 - mix) + white[None, :] * mix
    rgb = np.clip(rgb, 0.0, 1.0)

    # anisotropic covariance along +Z (the axis). Direction is the axis for every splat.
    dirs = np.tile([0.0, 0.0, 1.0], (n_splats, 1))
    cov = emit_fiber(dirs, tangent_scale=0.02 * max(elong, 1.0), normal_scale=0.02,
                     fiber_dir=dirs, elongation=max(elong, 1.0))

    return {
        'pos': pos, 'normal': dirs, 'cov': cov,
        'albedo': rgb.astype(np.float32),
        'alpha': np.clip(emission, 0.05, 1.0).astype(np.float32),
        'emission': emission.astype(np.float32),         # THE flag: >0 -> render additive, no Lambert
        'kind': 'emissive',
    }


def propose(n: int = 8, seed: int = 0) -> list:
    """N admissible emissive fillings for an `energy` stud, each measured, ranked, never chosen.

    Same contract as bricks.propose for matter: recombined from the archetypes (so a candidate
    can be a laser/plasma blend that does not exist as a named archetype), returned with the
    facts a caller ranks on. Taste is the operator's; this only offers.
    """
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
            'intensity': round(float(g['intensity']), 3),
            'elongation': round(float(g['elongation']), 3),
            'falloff': round(float(g['falloff']), 3),
            'genome': g, 'seed': seed + i,
        })
    # ranked by measurable facts only: brighter and more-elongated first (a laser reads as
    # more "energy" than a soft glow). Never by preference.
    out.sort(key=lambda c: (-c['intensity'], -c['elongation']))
    return out


def facts(genome: dict, seed: int = 0) -> dict:
    """Measured facts of an emissive genome, for scoring/ranking. All from the emitted splats."""
    sp = emit_emissive(genome, 300, seed)
    em = sp['emission']
    ext = sp['pos'].max(0) - sp['pos'].min(0)
    return {
        'mean_emission': float(em.mean()),
        'peak_emission': float(em.max()),
        'aspect': float(ext[2] / max(np.hypot(ext[0], ext[1]), 1e-6)),   # >1 = a line
        'colour': [round(float(genome[c]), 3) for c in 'rgb'],
    }


def _main() -> int:
    import argparse
    import sys
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    ap = argparse.ArgumentParser(description='the light genome')
    ap.add_argument('--archetype', default=None, help='render one archetype')
    ap.add_argument('--render', action='store_true')
    a = ap.parse_args()

    print('  EMISSIVE ARCHETYPES (authored from emission physics):')
    for name in ARCHETYPES:
        f = facts(seed_genome(name))
        print(f"    {name:12} colour {f['colour']}  peak {f['peak_emission']:.2f}  "
              f"aspect {f['aspect']:.2f}  ({'a line' if f['aspect'] > 3 else 'a blob'})")
    print('\n  eight proposed energy fillings (recombined), ranked:')
    for i, c in enumerate(propose(8)):
        print(f"    {i}  {c['parents'][0]:11} x {c['parents'][1]:11} "
              f"intensity {c['intensity']:.2f}  elong {c['elongation']:.2f}")
    return 0


if __name__ == '__main__':
    raise SystemExit(_main())
