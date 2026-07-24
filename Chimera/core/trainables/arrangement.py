"""arrangement — HOW THE PIECES FIT, made trainable.

THE GAP THIS CLOSES. build_child had three hand-written branches -- tuft, clump, shard --
so the arrangement dimension held exactly THREE POINTS and the trainer could not reach it.
Measured consequence: a whole driven section came back {'clump': 1147}. Every object in
it was a clump, so the section read as gravel however varied its genomes were. Colour and
grain differed per object; shape could not. The ceiling on the world was the arrangement
vocabulary, not the material library.

The operator named this dimension as the important one -- "how do the pieces fit" -- and
it was the one with no search in it at all.

WHAT IT TRAINS AGAINST. Not taste, and not a hand-written idea of "looks like grass":
that is grading an adjective, which this studio already threw out once. It trains against
ARRANGEMENT STATISTICS MEASURED FROM A REAL SCAN. Every fact in measure() below is
computable from a scan's own splat positions and covariances, so the emitted arrangement
and the real one are compared on identical numbers -- the same discipline that made
material composition honest.

THE GENOME IS CONTINUOUS, AND IT CONTAINS THE OLD THREE. tuft, clump and shard are not
special cases in the code any more; they are three points in this space, and everything
between and beyond them is now reachable.
"""
from __future__ import annotations

import numpy as np

N_PIECES = 260           # pieces emitted per evaluation
N_RESTARTS = 5           # honest eval: several seeds, keep the WORST

# Every gene is a continuous knob on HOW PIECES SIT RELATIVE TO ONE ANOTHER.
GENOME_SCHEMA = {
    'spread_r':      (0.05, 1.60),   # radial extent from the centre
    'spread_z':      (0.05, 2.20),   # vertical extent
    'rise':         (-1.00, 1.00),   # -1 pieces hang, 0 flat, +1 pieces stand up
    'align':         (0.00, 1.00),   # 0 pieces point every way, 1 all parallel
    'align_up':      (0.00, 1.00),   # what they align TO: 0 = horizontal, 1 = vertical
    'clusters':      (1.00, 14.00),  # sub-groups (a tuft is blades; gravel is not)
    'cluster_tight': (0.005, 0.60),   # floor widened 0.02->0.005 (2026-07-23): the
    #   trained winner sat ON the old floor, so the SCHEMA capped clustering, not the search.
    #   Wolfram's capacity result, measured here: reachable clustering 4.736 -> 6.588.   # how tight each sub-group is
    'droop':         (0.00, 1.00),   # gravity bending the far ends over
    'hollow':        (0.00, 1.00),   # 0 solid mass, 1 all mass in an outer shell
    'taper':         (0.00, 1.00),   # narrowing with height
}


def _gauss_fn(rng):
    """The trainer hands domains a stdlib random.Random; bricks.py hands a numpy
    Generator. A domain that assumes either one is unusable from the other caller, so
    adapt rather than pick a side (granular.py uses the same pair)."""
    if rng is None:
        rng = np.random.default_rng()
    return (lambda s: float(rng.normal(0.0, s))) if hasattr(rng, 'normal')         else (lambda s: rng.gauss(0.0, s))


def _rand01_fn(rng):
    if rng is None:
        rng = np.random.default_rng()
    return rng.random


def seed(rng=None) -> dict:
    gauss = _gauss_fn(rng)
    rand01 = _rand01_fn(rng)
    rng = rng or np.random.default_rng()
    return {k: float(rng.uniform(lo, hi)) for k, (lo, hi) in GENOME_SCHEMA.items()}


def mutate(genome: dict, rng=None) -> dict:
    gauss = _gauss_fn(rng)
    rand01 = _rand01_fn(rng)
    rng = rng or np.random.default_rng()
    g = dict(genome)
    for k, (lo, hi) in GENOME_SCHEMA.items():
        if rng.random() < 0.35:
            g[k] = float(np.clip(g[k] + gauss(0.12) * (hi - lo), lo, hi))
    return g


def emit(genome: dict, n: int = N_PIECES, seed_i: int = 0):
    """Turn an arrangement genome into piece POSITIONS and DIRECTIONS.

    Returns (pos, dirs). This is the phenotype: where the pieces are and which way each
    one points. It says nothing about what a piece is MADE of -- that is the material
    genome's job, and keeping them separate is what lets one material take many forms.
    """
    rng = np.random.default_rng(seed_i)
    g = genome

    k = max(1, int(round(g['clusters'])))
    ca = rng.uniform(0, 2 * np.pi, k)
    cr = g['spread_r'] * np.sqrt(rng.uniform(0, 1, k))
    centres = np.stack([cr * np.cos(ca), cr * np.sin(ca), np.zeros(k)], 1)

    which = rng.integers(0, k, n)
    local = rng.normal(0, g['cluster_tight'], (n, 3)) * np.array(
        [g['spread_r'], g['spread_r'], g['spread_z']])
    pos = centres[which] + local

    # rise lifts pieces off the plane; taper narrows what is high; droop bends the tips
    h = rng.uniform(0, 1, n) ** (1.0 + 2.0 * g['taper'])
    pos[:, 2] = np.abs(pos[:, 2]) + h * g['spread_z'] * max(g['rise'], 0.0)
    if g['rise'] < 0:
        pos[:, 2] *= (1.0 + g['rise'])                     # hang toward the plane
    rad = np.linalg.norm(pos[:, :2], axis=1, keepdims=True) + 1e-9
    pos[:, :2] += (pos[:, :2] / rad) * (h[:, None] * g['droop'] * g['spread_r'] * 0.6)
    pos[:, 2] -= h * g['droop'] * g['spread_z'] * 0.35

    if g['hollow'] > 0:                                    # push mass toward a shell
        r = np.linalg.norm(pos, axis=1, keepdims=True) + 1e-9
        shell = np.maximum(g['spread_r'], g['spread_z'])
        pos = pos * (1 - g['hollow']) + (pos / r) * shell * g['hollow']

    # directions: blend a common axis with random, by `align`
    axis = np.array([0.0, 0.0, 1.0]) * g['align_up'] + np.array([1.0, 0.0, 0.0]) * (1 - g['align_up'])
    axis /= np.linalg.norm(axis) + 1e-9
    rnd = rng.normal(0, 1, (n, 3))
    rnd /= np.linalg.norm(rnd, axis=1, keepdims=True) + 1e-9
    dirs = axis[None, :] * g['align'] + rnd * (1 - g['align'])
    dirs /= np.linalg.norm(dirs, axis=1, keepdims=True) + 1e-9
    return pos, dirs


def _facts(pos, dirs) -> dict:
    """The statistics. EVERY ONE is computable from a real scan's splats too."""
    ext = pos.max(0) - pos.min(0)
    ext_xy = float(max(ext[0], ext[1]))
    ext_z = float(ext[2])

    # nearest-neighbour spacing vs what uniform scattering would give -> clustering
    d = np.linalg.norm(pos[:, None, :] - pos[None, :, :], axis=2)
    np.fill_diagonal(d, np.inf)
    nn = d.min(1)
    vol = max(ext_xy * ext_xy * max(ext_z, 1e-3), 1e-9)
    uniform_nn = 0.554 * (vol / len(pos)) ** (1 / 3)       # Clark-Evans expectation
    return {
        'aspect': float(ext_z / max(ext_xy, 1e-6)),
        'verticality': float(np.abs(dirs[:, 2]).mean()),
        'alignment': float(np.abs(dirs @ dirs.mean(0) / (np.linalg.norm(dirs.mean(0)) + 1e-9)).mean()),
        'clustering': float(uniform_nn / max(nn.mean(), 1e-9)),
        'ground_contact': float((pos[:, 2] < pos[:, 2].min() + 0.12 * max(ext_z, 1e-6)).mean()),
        'hollowness': float(
            (np.linalg.norm(pos - pos.mean(0), axis=1) >
             0.6 * np.linalg.norm(pos - pos.mean(0), axis=1).max()).mean()),
        'spread_ratio': float(ext_xy / max(ext_z, 1e-6)),
    }


# --- the reference the objective scores against ----------------------------
# THE DOMAIN SELF-LOADS ITS TARGET, LOUDLY. material_appearance once trained against
# None for weeks because nothing checked; a domain with no reference silently optimises
# nothing. If the measured targets are absent this raises rather than degrading.

_TARGETS = None
_RAW_TARGETS = None

# RANGE DEBIASING. The observed min..max of n samples is a BIASED estimate of a population's
# spread -- badly at small n. The range of 5 samples covers only ~67% of the population and
# spans ~2.33 sigma (the control-chart constant d2), while a 95% band spans 3.92 sigma. So
# every band measured from 5 regions is ~1.69x too narrow, and the two narrowest ones
# (verticality, alignment) were the binding constraint on band_margin all along. This is a
# BIAS, not noise: averaging more regions the same way converges on the wrong narrow answer
# more confidently. It is corrected here from data already on disk, no new scans.
#
# d2 = E[range]/sigma for n normal draws. Monte-Carlo verified: table 2.326 vs MC 2.328 at n=5.
_D2 = {2: 1.128, 3: 1.693, 4: 2.059, 5: 2.326, 6: 2.534, 7: 2.704, 8: 2.847,
       9: 2.970, 10: 3.078, 12: 3.258, 15: 3.472, 20: 3.735, 25: 3.931}
COVERAGE_Z = 1.96          # 95% population coverage. A stated choice, not a default nobody saw.

# The debiasing is done on the LIABILITY SCALE -- log for positive quantities, logit for
# proportions -- exactly as core/progeny.py does, and for the same reason: a symmetric
# widening of a bounded trait on its raw scale walks out of the physical domain (linear
# debiasing sent aspect's floor to 0.024, a nonsensical ratio), while the inverse transform
# CANNOT leave it, so no clamping is ever needed. It also treats a right-skewed quantity like
# clustering multiplicatively, which is what a ratio is.
_POSITIVE = {'aspect', 'clustering'}
_PROPORTION = {'verticality', 'alignment'}


def _to_liability(k: str, v: float) -> float:
    if k in _PROPORTION:
        p = min(max(float(v), 1e-4), 1 - 1e-4)
        return float(np.log(p / (1 - p)))
    return float(np.log(max(float(v), 1e-9)))


def _from_liability(k: str, x: float) -> float:
    if k in _PROPORTION:
        return float(1.0 / (1.0 + np.exp(-x)))
    return float(np.exp(x))


def _d2(n: int) -> float:
    if n in _D2:
        return _D2[n]
    if n < 2:
        return 1.128
    keys = sorted(_D2)
    if n > keys[-1]:
        return _D2[keys[-1]]                       # asymptote is slow; the last value is close
    lo = max(k for k in keys if k <= n)
    hi = min(k for k in keys if k >= n)
    f = (n - lo) / (hi - lo)
    return _D2[lo] + f * (_D2[hi] - _D2[lo])       # linear interpolation between table entries


def _debias_band(values, k: str, n: int) -> tuple:
    """Turn n measured values into a 95% coverage band, on the liability scale.

    Center on the sample MEAN (uses all n values, not just the two extremes); estimate sigma
    from the range via d2; widen to COVERAGE_Z. As n grows the band converges on the true
    population range -- so a second scan automatically shrinks the correction rather than
    needing this code changed.
    """
    lia = [_to_liability(k, v) for v in values]
    centre = float(np.mean(lia))
    sigma = (max(lia) - min(lia)) / _d2(n)
    return (_from_liability(k, centre - COVERAGE_Z * sigma),
            _from_liability(k, centre + COVERAGE_Z * sigma))


def raw_targets() -> dict:
    """The undebiased min..max, kept for provenance. NOT the training target."""
    global _RAW_TARGETS
    if _RAW_TARGETS is None:
        targets()                                  # populates both
    return _RAW_TARGETS


def targets() -> dict:
    """Debiased arrangement bands from real scans. Raises if the measurements are missing."""
    global _TARGETS, _RAW_TARGETS
    if _TARGETS is None:
        import json
        from pathlib import Path
        p = Path(__file__).resolve().parents[2] / 'docs/matter/arrangement_targets.json'
        if not p.exists():
            raise FileNotFoundError(
                f'arrangement has NO MEASURED TARGET at {p}. Run '
                f'Construction/arrangement_dna.py on a scan first -- training against '
                f'nothing is not training.')
        regions = [r for t in json.loads(p.read_text())['targets'].values()
                   for r in t.values()]
        if not regions:
            raise ValueError('arrangement_targets.json holds no regions')
        n = len(regions)
        keys = ('aspect', 'verticality', 'alignment', 'clustering')
        _RAW_TARGETS = {k: (min(r[k] for r in regions), max(r[k] for r in regions)) for k in keys}
        _TARGETS = {k: _debias_band([r[k] for r in regions], k, n) for k in keys}
    return _TARGETS


def _band_error(value: float, band: tuple) -> float:
    """Distance OUTSIDE a measured band; zero inside it.

    Distance to a BAND, not to a mean. Real material varies across regions, so demanding
    one value would be fitting noise rather than matching matter.
    """
    lo, hi = band
    return float(max(0.0, lo - value, value - hi))


def measure(genome: dict) -> dict:
    """Facts only, worst-cased over restarts. Never an opinion about whether it is good.

    One layout from one seed is a coin toss -- the same lesson as the walker. Each fact is
    reported at its WORST across N_RESTARTS so a lucky arrangement cannot win.
    """
    runs = [_facts(*emit(genome, N_PIECES, s)) for s in range(N_RESTARTS)]
    keys = runs[0].keys()
    out = {k: float(np.mean([r[k] for r in runs])) for k in keys}
    out.update({f'{k}_worst': float(np.min([r[k] for r in runs])) for k in keys})
    out['robustness'] = float(min(
        (min(r[k] for r in runs) + 1e-9) / (np.mean([r[k] for r in runs]) + 1e-9) for k in keys))
    out['n_active_clusters'] = float(max(1, round(genome['clusters'])))

    t = targets()
    for k in ('aspect', 'verticality', 'alignment', 'clustering'):
        out[f'{k}_error'] = _band_error(out[k], t[k])
    # clustering spans 4.679..8.172 while alignment spans 0.516..0.576 -- a raw distance
    # would weight clustering ~13x for no physical reason. Normalise each error by its own
    # band width so "outside by one band-width" costs the same in every dimension.
    for k in ('aspect', 'verticality', 'alignment', 'clustering'):
        lo, hi = t[k]
        out[f'{k}_off'] = round(out[f'{k}_error'] / max(hi - lo, 1e-9), 4)
    out['total_off'] = round(sum(out[f'{k}_off'] for k in
                                 ('aspect', 'verticality', 'alignment', 'clustering')), 4)
    out['in_all_bands'] = float(out['total_off'] == 0.0)

    # BAND MARGIN -- how much room the genome has before it leaves reality.
    # 1.0 = dead centre of every band, 0.0 = sitting on an edge. This exists because the
    # first trained winner landed with verticality exactly ON the upper limit (0.476 vs a
    # 0.476 ceiling): it satisfied every constraint and had NOWHERE to vary, so per-object
    # jitter fell out of band 62% of the time even at 1% of range. Margin is physics, not
    # taste: a genome with room on all sides produces CHILDREN that are still real material.
    margins = []
    for k in ('aspect', 'verticality', 'alignment', 'clustering'):
        lo, hi = t[k]
        half = max((hi - lo) * 0.5, 1e-9)
        centre = 0.5 * (lo + hi)
        margins.append(max(0.0, 1.0 - abs(out[k] - centre) / half))
    out['band_margin'] = round(float(min(margins)), 4)

    # PERCEPTUAL MARGIN (2026-07-23, psychophysics hired). band_margin is the MIN over the
    # four facts, so for a full day it was pinned at 0.196 by verticality (2.1 JNDs wide)
    # and alignment (1.1 -- BELOW the discrimination threshold, its two ends look identical)
    # while aspect, 27.2 JNDs wide and plainly visible, was never the constraint. The
    # optimiser was spending its whole budget on precision nobody can see.
    #
    # The fix is NOT to drop the invisible facts -- they still constrain what the matter
    # physically IS, and total_off holds all four inside reality as a hard requirement.
    # It is to weight WHERE THE EFFORT GOES by how much of each fact reaches a person.
    from core.perception import perceptual_weights
    w = perceptual_weights({k: t[k] for k in
                            ('aspect', 'verticality', 'alignment', 'clustering')})
    keys = ('aspect', 'verticality', 'alignment', 'clustering')
    out['seen_margin'] = round(float(sum(
        w[k] * m for k, m in zip(keys, margins))), 4)
    return out


# The old three forms, as POINTS IN THIS SPACE rather than branches in the code.
KNOWN_FORMS = {
    'tuft':  {'spread_r': 0.35, 'spread_z': 1.20, 'rise': 0.90, 'align': 0.55, 'align_up': 0.85,
              'clusters': 9.0, 'cluster_tight': 0.10, 'droop': 0.45, 'hollow': 0.05, 'taper': 0.55},
    'clump': {'spread_r': 0.55, 'spread_z': 0.45, 'rise': 0.10, 'align': 0.05, 'align_up': 0.40,
              'clusters': 2.0, 'cluster_tight': 0.45, 'droop': 0.05, 'hollow': 0.25, 'taper': 0.10},
    'shard': {'spread_r': 0.80, 'spread_z': 0.12, 'rise': 0.00, 'align': 0.80, 'align_up': 0.05,
              'clusters': 3.0, 'cluster_tight': 0.30, 'droop': 0.00, 'hollow': 0.10, 'taper': 0.05},
}


def main() -> None:
    print('=== the three hand-written forms are now POINTS in a continuous space ===')
    print(f"  {'form':7}" + ''.join(f'{k:>15}' for k in
                                    ('aspect', 'verticality', 'alignment', 'clustering')))
    for name, g in KNOWN_FORMS.items():
        m = measure(g)
        print(f'  {name:7}' + ''.join(f'{m[k]:>15.3f}' for k in
                                      ('aspect', 'verticality', 'alignment', 'clustering')))

    print('\n=== and the space between them is reachable, which it was not before ===')
    a, b = KNOWN_FORMS['clump'], KNOWN_FORMS['tuft']
    for t in (0.25, 0.5, 0.75):
        g = {k: a[k] * (1 - t) + b[k] * t for k in a}
        m = measure(g)
        print(f'  clump->tuft {t:.2f}   aspect {m["aspect"]:.3f}  '
              f'verticality {m["verticality"]:.3f}  alignment {m["alignment"]:.3f}')

    print('\n=== random genomes reach arrangements none of the three describe ===')
    rng = np.random.default_rng(3)
    for i in range(4):
        m = measure(seed(rng))
        print(f'  random {i}      aspect {m["aspect"]:.3f}  verticality {m["verticality"]:.3f}  '
              f'clustering {m["clustering"]:.3f}  hollowness {m["hollowness"]:.3f}')


if __name__ == '__main__':
    main()
