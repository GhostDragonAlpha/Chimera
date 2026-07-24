"""grown_arrangement — arrangement GROWN by an irreducible process, not computed from ten numbers.

WHY THIS EXISTS (2026-07-23). `core/trainables/arrangement.py` computes positions directly
from its genome: a parametric formula, entirely REDUCIBLE. Wolfram's minimal model of
adaptive evolution reports that height-fitness and width-fitness produce similarly
elaborate forms, because in his model the phenotype is grown by a computation you cannot
shortcut -- so the FORM comes from the development and surprises even the person running it.

That is a falsifiable claim about our emitter, and it was tested. Training the parametric
domain against a deliberately unrelated objective produced a FLAT PANCAKE against the
band-trained hollow cage (genome distance 1.372, every fact different). His result does not
hold there -- and the reason is architectural, not a matter of tuning:

    A PARAMETRIC EMITTER CANNOT SURPRISE ANYONE. It can only interpolate its parameters,
    so its output is never richer than the objective that asked for it.

So here the genome stops describing the shape and starts describing the LOCAL RULES, and
the shape has to be grown to be known:

    genome        adhesion energies, target tissue fractions, temperature, seeding
    development   Cellular Potts annealing -- IRREDUCIBLE; no shortcut to the outcome
    phenotype     the settled lattice
    measure       the SAME four arrangement facts, so the two domains are comparable

WHAT MAKES IT IRREDUCIBLE, concretely: differential adhesion self-sorts scrambled cells
into layers by an energy rule applied locally, thousands of times. You cannot read the
final layering off the J matrix any more than you can read rule 30's row 1000 off its rule
table. That is the whole point -- it is where forms nobody specified come from.

DIRECTION IS DERIVED, NEVER DECLARED. A grown lattice has no built-in orientations, so a
piece's direction is the largest eigenvector of the covariance of its occupied neighbours
-- the local long axis. This is the SAME definition Construction/arrangement_dna.py uses on
a real scan (the longest principal axis of a splat), which is what keeps grown, emitted and
photographed matter measurable on one ruler.

THE COST IS THE TRADE. Irreducible means you must run it, so an evaluation here is orders
of magnitude dearer than the parametric domain's 1.5 ms. Benchmark before sizing a run:
    python -m core.trainables.grown_arrangement --bench
"""
from __future__ import annotations

import numpy as np

from core import matter

# The lattice. Small on purpose: this domain pays for irreducibility with time, and the
# trainer needs thousands of evaluations. 40^3 = 64,000 sites is the measured knee between
# "the layering actually resolves" and "a generation finishes this century".
N = 40
SHAPE = (N, N, N)

MEDIUM, BONE, MUSCLE, SKIN = matter.MEDIUM, matter.BONE, matter.MUSCLE, matter.SKIN
TISSUES = (BONE, MUSCLE, SKIN)

# THE GENOME IS THE RULE, NOT THE SHAPE. Six adhesion energies (the symmetric J matrix over
# three tissues plus medium), the volume each tissue is trying to hold, the temperature that
# sets how much the annealing explores, and how the seed is scattered. Nothing here says
# what the result should look like -- that is the point.
GENOME_SCHEMA = {
    'j_bone_bone':     (1.0, 16.0),
    'j_muscle_muscle': (1.0, 16.0),
    'j_skin_skin':     (1.0, 16.0),
    'j_bone_muscle':   (1.0, 16.0),
    'j_muscle_skin':   (1.0, 16.0),
    'j_medium':        (2.0, 20.0),   # every tissue's cost of touching the outside
    'frac_bone':       (0.05, 0.45),
    'frac_muscle':     (0.10, 0.60),
    'temp':            (2.0, 22.0),
    'radius':          (0.22, 0.45),  # seed blob radius, as a fraction of the lattice
    'anisotropy':      (0.35, 2.60),  # how the seed is stretched along z before annealing
}

N_RESTARTS = 3          # a grown form must repeat from a different scramble or it is luck
SWEEPS = 26             # annealing passes; see --bench for the cost/quality curve
SAMPLE = 900            # cells sampled for the facts, so cost does not scale with volume


def _gauss_fn(rng):
    if rng is None:
        rng = np.random.default_rng()
    return (lambda s: float(rng.normal(0.0, s))) if hasattr(rng, 'normal') \
        else (lambda s: rng.gauss(0.0, s))


def seed(rng=None) -> dict:
    # rng optional: the trainer calls seed() bare to make its founder genome, then seeds
    # the rest by mutation. A required argument here fails the run before generation 0.
    if rng is None:
        rng = np.random.default_rng()
    return {k: float(rng.uniform(lo, hi)) for k, (lo, hi) in GENOME_SCHEMA.items()}


def mutate(genome: dict, rng) -> dict:
    gauss = _gauss_fn(rng)
    g = dict(genome)
    for k, (lo, hi) in GENOME_SCHEMA.items():
        if rng.random() < 0.35:
            g[k] = float(np.clip(g[k] + gauss(0.12) * (hi - lo), lo, hi))
    return g


def _J(g: dict) -> np.ndarray:
    """The adhesion matrix. Symmetric by construction -- an asymmetric one is not physics."""
    m = g['j_medium']
    J = np.full((4, 4), m, dtype=np.float64)
    J[MEDIUM, MEDIUM] = 0.0
    J[BONE, BONE] = g['j_bone_bone']
    J[MUSCLE, MUSCLE] = g['j_muscle_muscle']
    J[SKIN, SKIN] = g['j_skin_skin']
    J[BONE, MUSCLE] = J[MUSCLE, BONE] = g['j_bone_muscle']
    J[MUSCLE, SKIN] = J[SKIN, MUSCLE] = g['j_muscle_skin']
    # bone-skin is NOT a free parameter: in real tissue they are separated by muscle, so
    # their contact energy is the sum of the two interfaces they would each have to cross.
    J[BONE, SKIN] = J[SKIN, BONE] = 0.5 * (g['j_bone_muscle'] + g['j_muscle_skin'])
    return J


def _scramble(g: dict, seed_i: int):
    """A stretched blob of randomly assigned tissue. The START, not the answer.

    Deliberately scrambled: differential adhesion has to SORT it. Seeding it pre-sorted
    would be authoring the phenotype and calling the result emergent.
    """
    rng = np.random.default_rng(seed_i)
    zz, yy, xx = np.mgrid[0:N, 0:N, 0:N].astype(np.float64)
    c = (N - 1) * 0.5
    a = g['anisotropy']
    r2 = ((xx - c) ** 2 + (yy - c) ** 2 + ((zz - c) / max(a, 1e-6)) ** 2)
    inside = r2 <= (g['radius'] * N) ** 2

    grid = np.full(SHAPE, MEDIUM, dtype=np.int16)
    n_in = int(inside.sum())
    if n_in < 64:
        return None, None
    fb, fm = g['frac_bone'], g['frac_muscle']
    tot = fb + fm
    if tot > 0.95:                       # leave room for skin; a genome asking for more
        fb, fm = fb * 0.95 / tot, fm * 0.95 / tot   # tissue than exists is clipped, not failed
    draw = rng.random(n_in)
    kinds = np.where(draw < fb, BONE, np.where(draw < fb + fm, MUSCLE, SKIN))
    grid[inside] = kinds.astype(np.int16)

    targets = {BONE: int((kinds == BONE).sum()),
               MUSCLE: int((kinds == MUSCLE).sum()),
               SKIN: int((kinds == SKIN).sum())}
    return grid, targets


def _local_axes(pos: np.ndarray, k: int = 12) -> np.ndarray:
    """A piece's direction = the largest eigenvector of its neighbours' covariance.

    DERIVED, NOT DECLARED. Nothing in a grown lattice carries an orientation, so the only
    honest direction is the one the surrounding matter implies -- the same definition used
    on a real scan's splats, which is what makes the two comparable.
    """
    n = len(pos)
    if n < k + 1:
        return np.tile([0.0, 0.0, 1.0], (n, 1))
    # brute-force kNN on a sampled subset: n is bounded by SAMPLE, so this stays cheap
    d = ((pos[:, None, :] - pos[None, :, :]) ** 2).sum(-1)
    idx = np.argpartition(d, k, axis=1)[:, :k + 1]
    out = np.empty((n, 3))
    for i in range(n):
        q = pos[idx[i]] - pos[idx[i]].mean(0)
        w, v = np.linalg.eigh(q.T @ q)
        out[i] = v[:, -1]
    nrm = np.linalg.norm(out, axis=1, keepdims=True)
    return out / np.maximum(nrm, 1e-9)


def grow(genome: dict, seed_i: int = 0, gpu: bool = True):
    """Run the development. The phenotype is not knowable without this call."""
    grid, targets = _scramble(genome, seed_i)
    if grid is None:
        return None
    J = _J(genome)
    kw = dict(connectivity=18, sweeps=SWEEPS, temp=genome['temp'], lam=0.9, seed=seed_i)
    if gpu:
        try:
            from core.matter_gpu import assemble_3d_gpu
            return assemble_3d_gpu(grid, SHAPE, targets, J, **kw)
        except Exception:
            pass                          # a missing GPU is a slowdown, never a wrong answer
    return matter.assemble_3d(grid, SHAPE, targets, J, **kw)


def _facts_from_grid(settled, rng) -> dict | None:
    """The same four arrangement facts, read off grown matter."""
    if settled is None:
        return None
    g = np.asarray(settled).reshape(SHAPE)
    occ = np.argwhere(g != MEDIUM).astype(np.float64)
    if len(occ) < 80:
        return None
    if len(occ) > SAMPLE:
        occ = occ[rng.choice(len(occ), SAMPLE, replace=False)]

    pos = occ - occ.mean(0)
    dirs = _local_axes(pos)

    ext = pos.max(0) - pos.min(0)
    horiz = float(np.hypot(ext[2], ext[1]))
    vert = float(max(ext[0], 1e-9))

    # clustering: mean pairwise distance over nearest-neighbour distance -- a RATIO, so it
    # is scale-free and directly comparable to the parametric domain and to a real scan.
    sub = pos[rng.choice(len(pos), min(260, len(pos)), replace=False)]
    d = np.sqrt(((sub[:, None, :] - sub[None, :, :]) ** 2).sum(-1))
    np.fill_diagonal(d, np.inf)
    nn = d.min(1)
    np.fill_diagonal(d, 0.0)
    mean_pair = d.sum() / max(len(sub) * (len(sub) - 1), 1)

    return {
        'aspect': float(horiz / vert),
        'verticality': float(np.abs(dirs[:, 0]).mean()),
        'alignment': float(np.linalg.norm(dirs.mean(0))),
        'clustering': float(mean_pair / max(nn.mean(), 1e-9)),
        'occupancy': float(len(np.argwhere(g != MEDIUM)) / (N ** 3)),
    }


def measure(genome: dict) -> dict:
    """Grow it N times from different scrambles and keep the WORST of every fact.

    One growth from one scramble is a coin toss, exactly as one rollout was for the walker.
    A form that only appears from a lucky initial scatter is not a rule, it is an accident.
    """
    runs = []
    for i in range(N_RESTARTS):
        rng = np.random.default_rng(1000 + i)
        f = _facts_from_grid(grow(genome, seed_i=i), rng)
        if f is not None:
            runs.append(f)
    if not runs:
        return {k: 0.0 for k in ('aspect', 'verticality', 'alignment', 'clustering',
                                 'occupancy', 'robustness', 'grew')}

    keys = list(runs[0])
    mean = {k: float(np.mean([r[k] for r in runs])) for k in keys}
    worst = {k: float(min(r[k] for r in runs)) for k in keys}

    out = dict(mean)
    for k in keys:
        out[f'{k}_worst'] = worst[k]
    out['robustness'] = float(np.mean(
        [worst[k] / max(abs(mean[k]), 1e-9) for k in ('clustering', 'aspect', 'alignment')]))
    out['grew'] = float(len(runs)) / N_RESTARTS

    # band errors against the same measured scan targets, so a grown form and an emitted
    # one are scored on identical ground
    try:
        from core.trainables.arrangement import targets as scan_targets, _band_error
        t = scan_targets()
        for k in ('aspect', 'verticality', 'alignment', 'clustering'):
            lo, hi = t[k]
            out[f'{k}_off'] = round(_band_error(out[k], t[k]) / max(hi - lo, 1e-9), 4)
        out['total_off'] = round(sum(out[f'{k}_off'] for k in
                                     ('aspect', 'verticality', 'alignment', 'clustering')), 4)
        out['in_all_bands'] = float(out['total_off'] == 0.0)
    except Exception:
        pass
    return out


def _main() -> int:
    import argparse
    import time
    ap = argparse.ArgumentParser(description='arrangement grown, not computed')
    ap.add_argument('--bench', action='store_true', help='cost of one evaluation')
    ap.add_argument('--n', type=int, default=6)
    a = ap.parse_args()

    rng = np.random.default_rng(0)
    if a.bench:
        print(f'\n  lattice {N}^3 = {N**3:,} sites, {SWEEPS} sweeps, '
              f'{N_RESTARTS} restarts per evaluation\n')
        for gpu in (True, False):
            g = seed(rng)
            t0 = time.time()
            grow(g, 0, gpu=gpu)
            dt = time.time() - t0
            print(f'    {"GPU" if gpu else "CPU"}  one growth {dt*1000:8.1f} ms   '
                  f'-> one evaluation ~{dt*N_RESTARTS:.2f} s')
        return 0

    print(f'\n  {a.n} random rule-genomes, each GROWN {N_RESTARTS}x:\n')
    print(f'    {"aspect":>7} {"vert":>6} {"align":>6} {"clust":>7} {"occ":>6} {"robust":>7}')
    for _ in range(a.n):
        t0 = time.time()
        m = measure(seed(rng))
        print(f"    {m['aspect']:7.3f} {m['verticality']:6.3f} {m['alignment']:6.3f} "
              f"{m['clustering']:7.3f} {m['occupancy']:6.3f} {m['robustness']:7.3f}"
              f"   ({time.time()-t0:.1f}s)")
    return 0


if __name__ == '__main__':
    raise SystemExit(_main())
