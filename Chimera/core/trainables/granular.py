"""granular — the box of sand as a trainable domain: local rules in, emergent physics out.

Commissioned 2026-07-18, the human: "each particle is held in, not by the force of
gravity, but by the force of the surrounding objects... autonomous functions that
don't require calculation because the aggregate of simple calculations allows for
emergence." That is (1) local update rules, (2) cellular-automata emergence, and
(3) fixed points + sleeping — a settled pile is a computation that has HALTED.

THE MODEL (v0 — a stochastic sandpile height-field, Bak-Tang-Wiesenfeld family):
    - The world is W columns; each column is a stack of grain cells. h[x] = height.
    - Grains pour in at the top of a center region, one column landing per grain.
    - THE ONLY PHYSICS PRIMITIVE is the local rule: a column whose top stands more
      than `crit` cells above a neighbor TOPPLES its top grain onto that neighbor
      (probability p_topple per sweep). `crit` is quenched per-SITE disorder:
      resampled every time a grain lands, because a grain's stability is its local
      packing geometry, not its identity. With probability p_stick a landing grain
      FREEZES (cohesion bond — it never topples again, crit = infinity).
    - Cells are anisotropic parcels: CELL_W x CELL_H = 2 x 1 (a slope of d cells
      per column = atan(d * CELL_H/CELL_W)), so stable angles land in the
      researched granular range (d=1 -> 26.6 deg, d=2 -> 45 deg, d=3 -> 56.3 deg;
      the h_crit_mean mix interpolates between them). The library's real grains
      (regolith D50 = 72 um, Carrier 2003) are far below cell scale — a cell is a
      parcel of matter, not a grain, same coarse-graining as every rung of the
      scale ladder.

NOTHING IN THE GENOME NAMES AN ANGLE. The pile's slope, its settling, and how far
a poke propagates are all EMERGENT — which is exactly why they are usable as
objectives: they cannot be faked, only produced.

WHAT v0 DELIBERATELY CANNOT MEASURE (honest scope, do not cite it for these):
    - No pressure, no load network -> no Janssen effect, no Beverloo constancy.
      A height-field has no arches, so orifice clogging cannot emerge here.
      Those need the full 2D occupancy grid (v1) where lateral support is real.
    - Packing fraction: a lattice quantizes it away (always 1 inside the pile).

TOTALITY (terrarium Rule 2): every loop is a bounded `for`; a config that fails
to settle inside the sweep budget is REPORTED as unsettled_worst=1 and the
objective walls it out — runaway dynamics are measurable, not possible to hang on.

HONEST EVAL (TRAINING_PROTOCOL S3.5): the dynamics are stochastic, so one rollout
is a coin toss. measure() runs N_RESTARTS fixed-seed restarts (EVAL_SEED + r for
every genome alike) and reports means for context and WORST-CASE facts for the
objective to bind — angle_spread_deg across restarts IS the robustness fact.

THE SLEEP THESIS, MEASURED: after the pour ends the pile must reach a true fixed
point (zero topples, K_QUIET consecutive sweeps). Then PROBES drop single grains
and count the avalanche each one triggers: cost proportional to CHANGE, not to
world size. probe_locality = 1/(1+mean avalanche) is the climbing term — the
"autonomous function" property as a number.

DOMAIN CONTRACT: seed(rng) -> genome ; mutate(genome, rng) -> genome ;
measure(genome) -> {fact: float}. Facts only — docs/objectives/granular.json
(LLM-authored, research-pinned) says which facts are GOOD.
"""

from __future__ import annotations

import math

import numpy as np

# --- sim settings (test conditions, NOT genome) --------------------------------
W = 161                  # columns; walls at both ends (no topple off-world)
HMAX = 1200              # crit-grid rows; a stack this tall is already degenerate
N_GRAINS = 2600          # grains poured per restart
POUR_PER_SWEEP = 4       # pour rate (grains per sweep while any remain)
POUR_HALF = 2            # grains land on columns center +/- POUR_HALF
CELL_W, CELL_H = 2.0, 1.0    # parcel aspect: angle(d) = atan(d * CELL_H / CELL_W)
BUILD_SWEEPS = 6000      # hard for-loop cap on the build phase
K_QUIET = 50             # consecutive zero-topple sweeps = settled (fixed point)
N_PROBES = 100           # single-grain pokes after settling
PROBE_SWEEPS = 400       # hard for-loop cap per probe
PROBE_QUIET = 10         # consecutive quiet sweeps ending one probe
N_RESTARTS = 10          # honest eval: fixed seeds, worst-case facts
EVAL_SEED = 20260718
FROZEN = 255             # crit sentinel: cohesion bond, never topples

GENOME_SCHEMA = {
    # Mean per-site toppling threshold, in cells. Landing grains draw
    # floor(mean) + Bernoulli(frac) — the MIX of thresholds is what lets the
    # emergent angle interpolate between the lattice's discrete stable slopes.
    "h_crit_mean": {"min": 1.0, "max": 3.0, "init": 1.5},
    # Per-sweep probability an over-threshold column actually topples
    # (kinetics: how fast the pile relaxes, and how bursty avalanches are).
    "p_topple":    {"min": 0.05, "max": 1.0, "init": 0.6},
    # Probability a landing grain freezes permanently (cohesion). Lunar
    # regolith is cohesive (angular grains, vacuum welding) — this is the
    # locus that lets slopes exceed the loose-lattice maximum.
    "p_stick":     {"min": 0.0, "max": 0.25, "init": 0.03},
}


def seed(rng=None) -> dict:
    r = _rand01_fn(rng)
    return {k: s["min"] + r() * (s["max"] - s["min"])
            for k, s in GENOME_SCHEMA.items()}


def mutate(genome: dict, rng=None) -> dict:
    r = _gauss_fn(rng)
    out = dict(genome)
    for k, s in GENOME_SCHEMA.items():
        sigma = (s["max"] - s["min"]) * 0.12
        out[k] = float(min(s["max"], max(s["min"], genome[k] + r(sigma))))
    return out


def _rand01_fn(rng):
    if rng is None:
        rng = np.random.default_rng()
    if hasattr(rng, "random"):
        return rng.random
    return rng.rand                                      # legacy RandomState


def _gauss_fn(rng):
    if rng is None:
        rng = np.random.default_rng()
    if hasattr(rng, "normal"):
        return lambda s: float(rng.normal(0.0, s))
    return lambda s: rng.gauss(0.0, s)                   # random.Random


# --- the automaton --------------------------------------------------------------

def _sample_crit(rng, n: int, h_crit_mean: float, p_stick: float) -> np.ndarray:
    """Per-landing quenched thresholds: floor+Bernoulli(frac), FROZEN w.p. p_stick."""
    base = int(math.floor(h_crit_mean))
    frac = h_crit_mean - base
    crit = base + (rng.random(n) < frac).astype(np.uint8)
    crit[rng.random(n) < p_stick] = FROZEN
    return crit.astype(np.uint8)


def _scatter_new_tops(crit_grid: np.ndarray, h: np.ndarray,
                      cols: np.ndarray, fresh: np.ndarray) -> None:
    """Write fresh crit samples into the top-|group| cells of each landing column.
    Duplicate columns get consecutive stack positions (rank within group)."""
    order = np.argsort(cols, kind="stable")
    sc, sf = cols[order], fresh[order]
    new_group = np.r_[True, sc[1:] != sc[:-1]]
    group_start = np.maximum.accumulate(
        np.where(new_group, np.arange(sc.size), 0))
    rank = np.arange(sc.size) - group_start
    pos = h[sc] - 1 - rank                               # h already updated
    ok = pos >= 0
    crit_grid[pos[ok], sc[ok]] = sf[ok]


def _topple_sweep(h, crit_grid, rng, p_topple, h_crit_mean, p_stick, parity):
    """One synchronous relaxation sweep. Returns number of topples."""
    occ = h > 0
    if not occ.any():
        return 0
    top_crit = np.full(W, FROZEN, dtype=np.uint16)
    idx = np.flatnonzero(occ)
    top_crit[idx] = crit_grid[h[idx] - 1, idx]

    d_l = np.empty(W, dtype=np.int32)
    d_r = np.empty(W, dtype=np.int32)
    d_l[1:] = h[1:] - h[:-1]
    d_r[:-1] = h[:-1] - h[1:]
    d_l[0] = -1                                          # walls: never topple out
    d_r[-1] = -1

    go_left = d_l > d_r if parity else d_l >= d_r        # tie-break alternates
    d_best = np.where(go_left, d_l, d_r)
    eligible = occ & (top_crit != FROZEN) & (d_best > top_crit)
    eligible &= rng.random(W) < p_topple
    src = np.flatnonzero(eligible)
    if src.size == 0:
        return 0
    dst = np.where(go_left[src], src - 1, src + 1).astype(np.int64)

    np.subtract.at(h, src, 1)
    np.add.at(h, dst, 1)
    # Rearranged grains re-wedge into new local geometry: stability resampled.
    fresh = _sample_crit(rng, dst.size, h_crit_mean, p_stick)
    _scatter_new_tops(crit_grid, h, dst, fresh)
    return int(src.size)


def _rollout(genome: dict, restart: int) -> dict | None:
    """One full restart: pour + settle + probes. Returns per-restart facts,
    or None if the config never settles / stacks out (degenerate)."""
    rng = np.random.default_rng(EVAL_SEED + restart)
    hm, pt, ps = genome["h_crit_mean"], genome["p_topple"], genome["p_stick"]
    h = np.zeros(W, dtype=np.int32)
    crit_grid = np.full((HMAX, W), FROZEN, dtype=np.uint8)
    center = W // 2

    poured, total_topples, settle_sweep, quiet = 0, 0, None, 0
    for sweep in range(BUILD_SWEEPS):
        if poured < N_GRAINS:
            n = min(POUR_PER_SWEEP, N_GRAINS - poured)
            cols = center + rng.integers(-POUR_HALF, POUR_HALF + 1, size=n)
            np.add.at(h, cols, 1)
            if h.max() >= HMAX - 2:
                return None                              # degenerate mega-tower
            _scatter_new_tops(crit_grid, h, cols,
                              _sample_crit(rng, n, hm, ps))
            poured += n
        t = _topple_sweep(h, crit_grid, rng, pt, hm, ps, sweep & 1)
        total_topples += t
        if poured >= N_GRAINS:
            quiet = quiet + 1 if t == 0 else 0
            if quiet >= K_QUIET:
                settle_sweep = sweep - (N_GRAINS // POUR_PER_SWEEP) - K_QUIET
                break
    if settle_sweep is None:
        return None                                      # never reached fixed point

    angle, aspect = _angles_deg(h)

    sizes = []
    for p in range(N_PROBES):
        pile_cols = np.flatnonzero(h >= max(2, int(0.3 * h.max())))
        col = int(rng.choice(pile_cols))
        h[col] += 1
        _scatter_new_tops(crit_grid, h, np.array([col]),
                          _sample_crit(rng, 1, hm, ps))
        av, q = 0, 0
        for sweep in range(PROBE_SWEEPS):
            t = _topple_sweep(h, crit_grid, rng, pt, hm, ps, sweep & 1)
            av += t
            q = q + 1 if t == 0 else 0
            if q >= PROBE_QUIET:
                break
        sizes.append(av)
    sizes = np.asarray(sizes, dtype=float)

    n_frozen = 0
    for x in np.flatnonzero(h > 0):
        n_frozen += int(np.count_nonzero(crit_grid[:h[x], x] == FROZEN))

    return {"angle_deg": angle,
            "aspect_deg": aspect,
            "settle_sweeps": float(max(settle_sweep, 0)),
            "avalanche_mean": float(sizes.mean()),
            "avalanche_max": float(sizes.max()),
            "topples_per_grain": total_topples / float(N_GRAINS),
            "frozen_fraction": n_frozen / float(max(h.sum(), 1))}


def _angles_deg(h: np.ndarray) -> tuple[float, float]:
    """(flank_angle, aspect_angle) of the settled height field, in degrees.

    flank: |slope| fitted on each side of the apex over a ROBUST height band —
    0.2..0.8 of the 85th-percentile pile height, not of the raw peak. A frozen
    needle (p_stick chimney: 5 columns at ~360 on an apron of ~40, seen live on
    the first smoke run) makes a raw-peak band select ~1 point per side; the
    percentile band still sees the apron the free grains actually organized.

    aspect: atan(peak / footprint-halfwidth), cell aspect applied — the pile's
    GLOBAL form. For a true repose pile flank ~= aspect; a needle-on-apron sends
    aspect toward 80+ deg while the flank stays sane. Their divergence is the
    needle detector, reported so the objective can wall composite piles out —
    never smuggled into either estimate. Fit failure falls back to aspect: this
    function must never report 0.0 for a pile that visibly stands."""
    nz = np.flatnonzero(h)
    if nz.size < 5 or h.max() < 4:
        return 0.0, 0.0
    halfwidth = max((nz.max() - nz.min()) / 2.0, 1.0)
    aspect = math.degrees(math.atan(float(h.max()) / halfwidth * CELL_H / CELL_W))
    h_ref = float(np.percentile(h[nz].astype(float), 85.0))
    lo, hi = 0.2 * h_ref, 0.8 * h_ref
    apex = int(np.argmax(h))
    slopes = []
    for side in (slice(None, apex + 1), slice(apex, None)):
        xs = np.arange(W)[side]
        ys = h[side]
        m = (ys >= lo) & (ys <= hi)
        if m.sum() >= 4:
            slopes.append(abs(np.polyfit(xs[m], ys[m], 1)[0]))
    if not slopes:
        return aspect, aspect
    flank = math.degrees(math.atan(float(np.mean(slopes)) * CELL_H / CELL_W))
    return flank, aspect


# --- the domain measure ----------------------------------------------------------

def measure(genome: dict) -> dict:
    """FACTS ONLY, worst-cased across N_RESTARTS fixed-seed restarts."""
    runs = [_rollout(genome, r) for r in range(N_RESTARTS)]
    bad = sum(1 for r in runs if r is None)
    runs = [r for r in runs if r is not None]
    if not runs:
        return {"unsettled_worst": 1.0, "angle_mean_deg": 0.0,
                "angle_spread_deg": 90.0, "aspect_angle_mean_deg": 90.0,
                "angle_consistency_deg": 90.0,
                "settle_sweeps_worst": float(BUILD_SWEEPS),
                "avalanche_mean_worst": float(N_GRAINS),
                "avalanche_max_worst": float(N_GRAINS),
                "probe_locality_worst": 0.0, "topples_per_grain_mean": 0.0,
                "frozen_fraction_mean": 0.0}
    angles = np.array([r["angle_deg"] for r in runs])
    aspects = np.array([r["aspect_deg"] for r in runs])
    av_means = np.array([r["avalanche_mean"] for r in runs])
    return {
        "unsettled_worst": 1.0 if bad else 0.0,
        "angle_mean_deg": float(angles.mean()),
        "angle_spread_deg": float(angles.max() - angles.min()),
        "aspect_angle_mean_deg": float(aspects.mean()),
        "angle_consistency_deg": float(np.abs(angles - aspects).mean()),
        "settle_sweeps_worst": float(max(r["settle_sweeps"] for r in runs)),
        "avalanche_mean_worst": float(av_means.max()),
        "avalanche_max_worst": float(max(r["avalanche_max"] for r in runs)),
        "probe_locality_worst": float((1.0 / (1.0 + av_means)).min()),
        "topples_per_grain_mean": float(np.mean(
            [r["topples_per_grain"] for r in runs])),
        "frozen_fraction_mean": float(np.mean(
            [r["frozen_fraction"] for r in runs])),
    }


if __name__ == "__main__":
    import json as _json
    import time as _time
    g = {k: s["init"] for k, s in GENOME_SCHEMA.items()}
    t0 = _time.perf_counter()
    facts = measure(g)
    dt = _time.perf_counter() - t0
    print(_json.dumps(facts, indent=1))
    print(f"one eval ({N_RESTARTS} restarts): {dt:.2f}s "
          f"-> {1.0 / dt:.2f} evals/sec/worker")
