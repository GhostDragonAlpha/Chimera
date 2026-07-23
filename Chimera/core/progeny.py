"""progeny — CHILDREN of an isolated object, and where you PUT them.

THE CORRECTION (operator, 2026-07-23): the pipeline had been painting a material onto a
membrane, which is texturing. Games are not built that way. You isolate ONE object — a
grass tuft, a rock, a bolt — generate many VARIATIONS of it, and then PLACE instances,
by hand or by rule. Without that you have surfaces; with it you have game content.

WHY THE GENOME ALREADY SUPPORTS THIS: Construction/export_genome.py stores every feature
as mean + p10..p90 — a RANGE, not a value. That range is the space a child is sampled
from. Siblings differ from each other while staying inside the measured distribution, so
they read as the same KIND of thing without being copies. The range was never only for
identification.

    parent   = isolate(...)                      # one object, from a scan or authored
    kids     = spawn_children(parent, n=24)      # 24 variations, all in-range
    scene    = place(kids, positions, scales)    # granular control: you decide where

Nothing here scatters automatically unless you ask it to. `place()` takes explicit
transforms; `scatter()` is a convenience you can override per-instance.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RECOVERED_PATH = ROOT / 'docs/matter/recovered_genomes.json'


# ---------------------------------------------------------------------------
# THE PARENT — an object genome, either recovered from a scan or authored
# ---------------------------------------------------------------------------


def load_genome(name: str) -> dict:
    """Load a recovered object genome (mean + p10..p90 per feature)."""
    if not RECOVERED_PATH.exists():
        raise FileNotFoundError(f'no recovered genomes at {RECOVERED_PATH}')
    g = json.loads(RECOVERED_PATH.read_text()).get('genomes', {})
    if name not in g:
        raise KeyError(f'{name!r} not in genomes: {sorted(g)[:10]}')
    return g[name]


def _sample_in_range(feat: dict, rng, spread: float = 1.0) -> float:
    """Draw one value from a feature's measured range.

    p10..p90 covers 80% of a normal distribution (+/- 1.2816 sigma), so that is the
    conversion used. `spread` scales how far siblings may diverge: 0 = clones,
    1 = the measured population, >1 = exaggerated variety (useful, but no longer honest
    to the scan, so it is recorded on the child).
    """
    mean = feat['mean']
    sigma = (feat['p90'] - feat['p10']) / 2.5631 if feat.get('p90') is not None else feat.get('std', 0.0)
    return float(mean + rng.standard_normal() * sigma * spread)


# ---------------------------------------------------------------------------
# CHILDREN — variations sampled from the parent's ranges
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# QUANTITATIVE GENETICS
#
# The vocabulary is the real one because the problem is the real one.
#   GENOTYPE      the stored distribution (recovered_genomes.json)
#   PHENOTYPE     the expressed splat cloud (build_child output)
#   HERITABILITY  h2 = V_between / (V_between + V_within) -- the fraction of variation
#                 that BREEDS TRUE. Undefined from a single specimen, which is why two
#                 scans of a kind are the minimum useful sample.
#   LINKAGE       traits inherited as a block. R/G/B are linked (pleiotropy): they are
#                 driven largely by one underlying factor, luminance.
#   RECOMBINATION a child draws each linkage group from one of two parents
#                 (independent assortment), so siblings differ in whole blocks.
#   MUTATION      a separate, low-rate perturbation -- NOT the same thing as parental
#                 variance. Conflating them is why one-parent sampling looked like noise.
#   PLASTICITY    one genotype expressed differently by environment == the VERB and the
#                 MEMBRANE. Not inherited.
# ---------------------------------------------------------------------------

LINKAGE_GROUPS = {
    'colour': ('R', 'G', 'B'),      # pleiotropic: one luminance factor drives all three
    'form': ('size', 'aniso'),      # grain and shape covary in real material
    'body': ('opacity',),
}

# A genotype cannot code for an impossible phenotype. anisotropy is 1 - min/max, so it is
# bounded [0,1] BY CONSTRUCTION; colour and opacity are [0,1]; size is strictly positive.
# Sampling a Gaussian around a mean of 0.95 walked straight out of the valid domain and
# produced aniso = 1.07, which no splat can express.
TRAIT_BOUNDS = {
    'aniso': (0.0, 1.0), 'opacity': (0.0, 1.0),
    'R': (0.0, 1.0), 'G': (0.0, 1.0), 'B': (0.0, 1.0),
    'size': (1e-5, None), 'green': (-1.0, 1.0),
}


def _clamp_trait(name: str, value: float) -> float:
    lo, hi = TRAIT_BOUNDS.get(name, (None, None))
    if lo is not None:
        value = max(lo, value)
    if hi is not None:
        value = min(hi, value)
    return float(value)


# THE LIABILITY SCALE.
# Sampling a Gaussian directly on a bounded trait piles probability onto the boundary:
# a mean of 0.95 on [0,1] saturated children to pure white, and size drew negative and
# clamped to zero. Quantitative genetics models such traits on an UNBOUNDED scale and
# transforms back -- logit for proportions, log for strictly-positive quantities. The
# inverse transform cannot leave the domain, so no clamping is ever needed.
_PROPORTION = {'aniso', 'opacity', 'R', 'G', 'B'}
_POSITIVE = {'size'}


def _to_liability(name: str, v: float) -> float:
    if name in _PROPORTION:
        p = min(max(float(v), 1e-4), 1 - 1e-4)
        return float(np.log(p / (1 - p)))                  # logit
    if name in _POSITIVE:
        return float(np.log(max(float(v), 1e-9)))          # log
    return float(v)


def _from_liability(name: str, x: float) -> float:
    if name in _PROPORTION:
        return float(1.0 / (1.0 + np.exp(-x)))             # expit
    if name in _POSITIVE:
        return float(np.exp(x))
    return float(x)


def _liability_sigma(name: str, mean: float, sigma: float) -> float:
    """Convert an observed-scale sigma to the liability scale by the local derivative."""
    if sigma <= 0:
        return 0.0
    if name in _PROPORTION:
        p = min(max(float(mean), 1e-4), 1 - 1e-4)
        return float(sigma / (p * (1 - p)))                # d(logit)/dp = 1/(p(1-p))
    if name in _POSITIVE:
        return float(sigma / max(abs(float(mean)), 1e-9))  # d(log)/dx = 1/x
    return float(sigma)


def _draw(name: str, mean: float, sigma: float, z: float) -> float:
    """Draw a trait value from a standard normal deviate, on the correct scale."""
    lz = _liability_sigma(name, mean, sigma)
    return _from_liability(name, _to_liability(name, mean) + z * lz)


def heritability(genome: dict) -> dict:
    """h2 per trait. Requires a CLASS genome (>= 2 specimens) or returns undefined."""
    out = {}
    for f, d in genome.get('features', {}).items():
        b, w = d.get('between_std'), d.get('within_std')
        if b is None or w is None:
            out[f] = None                     # single specimen: not measurable
            continue
        vb, vw = b * b, w * w
        out[f] = float(vb / (vb + vw)) if (vb + vw) > 0 else 0.0
    return out


def recombine(parent_a: dict, parent_b: dict, n: int = 12, mutation_rate: float = 0.08,
              mutation_size: float = 0.35, seed: int = 0) -> list:
    """Sexual reproduction: each child inherits linkage groups from either parent.

    Independent assortment at the level of the linkage group, then a low-rate mutation.
    Two parents of the same kind give siblings that differ in BLOCKS -- one child with
    parent A's colour and parent B's form -- which is what makes a population read as
    related individuals rather than as noise around one mean.
    """
    rng = np.random.default_rng(seed)
    fa, fb = parent_a['features'], parent_b['features']
    kids = []
    for i in range(n):
        sampled, inherited = {}, {}
        for group, traits in LINKAGE_GROUPS.items():
            src = fa if rng.random() < 0.5 else fb
            inherited[group] = 'A' if src is fa else 'B'
            # PLEIOTROPY: ONE underlying factor expresses across the whole group. Drawing
            # each trait separately is what produced (1.00,0.82,0.81) and (0.14,0.50,0.53)
            # from the same green-grey stock -- linkage decides WHICH PARENT, pleiotropy
            # decides that the traits move TOGETHER.
            z = rng.standard_normal()
            mut = rng.standard_normal() * mutation_size * 3.0 if rng.random() < mutation_rate else 0.0
            for t in traits:
                if t not in src:
                    continue
                d = src[t]
                sigma = d.get('within_std', d.get('std', 0.0))
                sampled[t] = _draw(t, d['mean'], sigma, z + mut)
        for t, d in fa.items():                                     # unlinked traits
            if t not in sampled:
                sampled[t] = _draw(t, d['mean'], d.get('std', 0.0), rng.standard_normal())
        sampled['_scale'] = float(np.clip(1.0 + rng.standard_normal() * 0.18, 0.45, 1.9))
        sampled['_yaw'] = float(rng.uniform(0, 2 * np.pi))
        sampled['_lean'] = float(np.clip(rng.standard_normal() * 0.12, -0.4, 0.4))
        kids.append({'index': i, 'seed': int(rng.integers(1 << 30)), 'sampled': sampled,
                     'spread': 1.0, 'honest': True, 'inherited': inherited,
                     'sexual': True})
    return kids


def spawn_children(parent: dict, n: int = 12, spread: float = 1.0, seed: int = 0) -> list:
    """ASEXUAL reproduction from one parent -- cloning with variance.

    Honest about what it is: with a single parent there is no recombination and no
    measurable heritability, so every child is a rearrangement of one individual. Use
    recombine() with two parents of the same kind for a real population.
    """
    rng = np.random.default_rng(seed)
    feats = parent['features']
    kids = []
    for i in range(n):
        sampled = {k: _sample_in_range(v, rng, spread) for k, v in feats.items()}

        # COLOUR MOVES TOGETHER. Sampling R, G and B independently produced rainbow
        # confetti from a green-grey material: the genome stores a range per channel but
        # not their CORRELATION, and real material varies mostly in brightness along one
        # line. Draw a single luminance factor plus a small per-channel wobble instead.
        if all(c in feats for c in 'RGB'):
            base = np.array([feats[c]['mean'] for c in 'RGB'], dtype=float)
            width = np.array([(feats[c]['p90'] - feats[c]['p10']) for c in 'RGB']) / 2.5631
            lum = 1.0 + rng.standard_normal() * (float(width.mean()) /
                                                 max(float(base.mean()), 1e-6)) * spread
            tint = rng.standard_normal(3) * width * 0.25 * spread     # slight hue drift only
            rgbv = np.clip(base * lum + tint, 0.0, 1.0)
            sampled['R'], sampled['G'], sampled['B'] = (float(v) for v in rgbv)
        # a child is also allowed to differ in gross form, within bounds
        sampled['_scale'] = float(np.clip(1.0 + rng.standard_normal() * 0.18 * spread, 0.45, 1.9))
        sampled['_yaw'] = float(rng.uniform(0, 2 * np.pi))
        sampled['_lean'] = float(np.clip(rng.standard_normal() * 0.12 * spread, -0.4, 0.4))
        kids.append({'index': i, 'seed': int(rng.integers(1 << 30)), 'sampled': sampled,
                     'spread': spread, 'honest': spread <= 1.0})
    return kids


def build_child(child: dict, form: str = 'tuft', n_splats: int = 400,
                material: str | None = None) -> dict:
    """Turn a child spec into an actual splat cloud.

    `form` is the object's structural archetype -- the arrangement, not the material.
    A tuft of grass and a rock use the same genome features and differ entirely in how
    their pieces are placed, which is the point the operator made: what must be learned
    is HOW THE PIECES FIT.
    """
    from core.splat_types import emit_fiber, emit_point, emit_surface

    s = child['sampled']
    rng = np.random.default_rng(child['seed'])
    scale = s['_scale']
    size = max(float(s.get('size', 0.02)), 1e-4)

    if form == 'tuft':
        # blades from a common root, splaying outward and upward
        n_blade = max(6, int(14 * scale))
        per = max(3, n_splats // n_blade)
        P, D = [], []
        for _ in range(n_blade):
            a = rng.uniform(0, 2 * np.pi)
            lean = rng.uniform(0.15, 0.75)
            L = scale * rng.uniform(0.6, 1.4)
            t = np.linspace(0, 1, per)[:, None]
            tip = np.array([np.cos(a) * lean, np.sin(a) * lean, 1.0]) * L
            arc = np.array([0, 0, -0.25 * L])            # gravity droop
            pts = t * tip + (t ** 2) * arc
            P.append(pts)
            d = np.tile(tip / (np.linalg.norm(tip) + 1e-9), (per, 1))
            D.append(d)
        pos = np.vstack(P); dirs = np.vstack(D)
        cov = emit_fiber(dirs, tangent_scale=size * 6, normal_scale=size * 1.2,
                         fiber_dir=dirs, elongation=4.0)

    elif form == 'clump':
        # rock / debris: isotropic mass with a rough shell
        pos = rng.standard_normal((n_splats, 3)) * 0.35 * scale
        pos[:, 2] = np.abs(pos[:, 2])
        dirs = pos / (np.linalg.norm(pos, axis=1, keepdims=True) + 1e-9)
        cov = emit_point(pos, radius=size * 3 * scale)

    else:  # 'shard' — flat plates, e.g. bark, panels, ice
        pos = rng.standard_normal((n_splats, 3)) * np.array([0.5, 0.5, 0.12]) * scale
        dirs = np.zeros_like(pos); dirs[:, 2] = 1.0
        cov = emit_surface(dirs, tangent_scale=size * 5 * scale, normal_scale=size * 0.6)

    # yaw + lean, so siblings do not all face the same way
    cy, sy = np.cos(s['_yaw']), np.sin(s['_yaw'])
    Rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1.0]])
    cl, sl = np.cos(s['_lean']), np.sin(s['_lean'])
    Rx = np.array([[1, 0, 0], [0, cl, -sl], [0, sl, cl]])
    R = Rz @ Rx
    pos = pos @ R.T
    cov = R @ cov @ R.T

    rgb = np.clip([s.get('R', 0.5), s.get('G', 0.5), s.get('B', 0.5)], 0, 1)
    alpha = float(np.clip(s.get('opacity', 0.9), 0.05, 1.0))
    n = len(pos)
    return {
        'pos': pos, 'normal': dirs, 'cov': cov,
        'albedo': np.tile(rgb, (n, 1)),
        'roughness': np.full(n, float(np.clip(s.get('aniso', 0.5), 0, 1))),
        'alpha': np.full(n, alpha),
        'subsurface': np.zeros(n),
        'metallic': np.zeros(n),
        '_form': form, '_child': child['index'], '_honest': child['honest'],
    }


# ---------------------------------------------------------------------------
# PLACEMENT — granular control. You decide where things go.
# ---------------------------------------------------------------------------


def place(children: list, positions, scales=None, yaws=None) -> dict:
    """Instance children at explicit transforms. One entry per instance.

    positions: (M,3). scales/yaws optional, length M. children are cycled if M > len.
    This is the hand-placement path -- nothing is decided for you.
    """
    positions = np.asarray(positions, dtype=np.float64).reshape(-1, 3)
    M = len(positions)
    scales = np.ones(M) if scales is None else np.asarray(scales, dtype=float).reshape(M)
    yaws = np.zeros(M) if yaws is None else np.asarray(yaws, dtype=float).reshape(M)
    if not children:
        raise ValueError('no children to place')

    keys = ('pos', 'normal', 'cov', 'albedo', 'roughness', 'alpha', 'subsurface', 'metallic')
    acc = {k: [] for k in keys}
    for i in range(M):
        kid = children[i % len(children)]
        k = float(scales[i])
        cy, sy = np.cos(yaws[i]), np.sin(yaws[i])
        R = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1.0]])
        acc['pos'].append(kid['pos'] @ R.T * k + positions[i])
        acc['normal'].append(kid['normal'] @ R.T)
        acc['cov'].append((R @ kid['cov'] @ R.T) * (k * k))
        for f in ('albedo', 'roughness', 'alpha', 'subsurface', 'metallic'):
            acc[f].append(kid[f])
    out = {k: np.concatenate(v, axis=0) for k, v in acc.items()}
    out['_instances'] = M
    out['_unique_children'] = len(children)
    return out


def scatter(children: list, count: int = 500, area: float = 100.0, seed: int = 0,
            height_fn=None, jitter_scale: float = 0.25) -> dict:
    """Convenience: place instances over a square area, optionally on a height field.

    height_fn(x, y) -> z lets you drop instances onto an authored heightmap, which is the
    operator's own example: get grass working, then make any terrain and apply it.
    """
    rng = np.random.default_rng(seed)
    xy = rng.uniform(-area, area, (count, 2))
    z = np.zeros(count) if height_fn is None else np.asarray(
        [float(height_fn(float(a), float(b))) for a, b in xy])
    pos = np.column_stack([xy, z])
    scales = 1.0 + rng.standard_normal(count) * jitter_scale
    return place(children, pos, np.clip(scales, 0.3, 2.2), rng.uniform(0, 2 * np.pi, count))


# ---------------------------------------------------------------------------
# THE VERB — apply motion to placed instances (the tree-in-wind concept)
# ---------------------------------------------------------------------------


def pose(scene: dict, verb: str = 'wind', t: float = 0.0, strength: float = 1.0,
         direction=(1.0, 0.0, 0.0), anchor_z: float | None = None) -> dict:
    """Apply a VERB to a placed scene. Nouns are what things are; verbs are what they do.

    Deformation is ROOTED: displacement scales with height above the anchor, so bases stay
    planted and tips move most — the same principle as Construction/tree.pose(). A verb
    that moved every splat equally would slide the object rather than bend it.

    verb='wind'  sway with a travelling phase, so neighbours are never in lockstep
    verb='grow'  scale from the root, t in 0..1
    verb='settle' droop under gravity
    """
    out = {k: (v.copy() if isinstance(v, np.ndarray) else v) for k, v in scene.items()}
    p = out['pos']
    z0 = float(p[:, 2].min()) if anchor_z is None else float(anchor_z)
    h = np.clip(p[:, 2] - z0, 0.0, None)
    hn = h / (h.max() + 1e-9)                       # 0 at the root, 1 at the tip

    d = np.asarray(direction, dtype=float)
    d = d / (np.linalg.norm(d) + 1e-9)

    if verb == 'wind':
        # travelling wave across the field: phase depends on position along the wind axis
        phase = (p @ d) * 0.35 + t * 2.2
        gust = 0.65 + 0.35 * np.sin(t * 0.7)         # slow gusting envelope
        amp = strength * 0.35 * (hn ** 1.6) * gust   # bend, not slide
        out['pos'] = p + d[None, :] * (amp * np.sin(phase))[:, None]
        out['pos'][:, 2] -= 0.12 * strength * (hn ** 2) * np.abs(np.sin(phase))  # arc shortens height

    elif verb == 'grow':
        k = float(np.clip(t, 0.0, 1.0))
        out['pos'] = np.column_stack([p[:, 0], p[:, 1], z0 + h * k])
        out['cov'] = scene['cov'] * (k * k + 1e-6)

    elif verb == 'settle':
        out['pos'] = p.copy()
        out['pos'][:, 2] = z0 + h * (1.0 - 0.4 * strength * hn)

    out['_verb'] = f'{verb}@t={t:.2f}'
    return out


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description='Spawn children of an object and place them.')
    ap.add_argument('--genome', default='cluster_07')
    ap.add_argument('--form', default='tuft', choices=['tuft', 'clump', 'shard'])
    ap.add_argument('--children', type=int, default=16)
    ap.add_argument('--instances', type=int, default=400)
    ap.add_argument('--area', type=float, default=6.0)
    ap.add_argument('--spread', type=float, default=1.0)
    ap.add_argument('--splats', type=int, default=300)
    ap.add_argument('--verb', default='', choices=['', 'wind', 'grow', 'settle'])
    ap.add_argument('--t', type=float, default=0.0)
    ap.add_argument('--out', default='Saved/SplatEmit/progeny.png')
    a = ap.parse_args()

    parent = load_genome(a.genome)
    kids_spec = spawn_children(parent, n=a.children, spread=a.spread)
    kids = [build_child(k, form=a.form, n_splats=a.splats) for k in kids_spec]
    print(f'parent {a.genome}: {a.children} children, form={a.form}, spread={a.spread}')
    sz = [k['sampled']['_scale'] for k in kids_spec]
    print(f'  child scale range {min(sz):.2f}..{max(sz):.2f}  '
          f'({"honest to the scan" if a.spread <= 1 else "EXAGGERATED past the measured range"})')

    scene = scatter(kids, count=a.instances, area=a.area)
    print(f'  placed {scene["_instances"]} instances of {scene["_unique_children"]} '
          f'unique children -> {len(scene["pos"]):,} splats')

    if a.verb:
        scene = pose(scene, verb=a.verb, t=a.t, strength=1.0)
        print(f'  verb applied: {scene["_verb"]}')

    from core.render_world import render_orbit
    render_orbit(scene, out_path=a.out, n_views=6, elev_deg=12.0)


if __name__ == '__main__':
    main()
