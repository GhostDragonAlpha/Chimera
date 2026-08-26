"""V62 probe -- dirty-set grain sweep economy (corrected draft).

STMT      A dirty-set grain sweep makes a settled world hold at ~0 cost: per-sweep work is
          O(columns whose neighborhood changed), not O(W). The first draft of this probe was
          flawed in three ways and could have printed PASS while proving nothing: (1) its
          masked path dropped metastable eligible columns outside the dirty set, so it was NOT
          physically identical to the reference; (2) Phase 1 never exercised the masked branch
          (dirty started empty on a settled field); (3) Phase 2 timed the full-sweep branch and
          reported len(dirty)=0 as "touches". This draft fixes all three.

          The load-bearing design change: the per-column topple gate is a PURE function of
          (world_seed, sweep_index, column) -- splitmix64 finalizer -> [0,1), compared to
          p_topple. Production's rng.random(W)-per-sweep couples every column to one O(W) draw;
          that is an implementation artifact, not the law. The law is "each over-threshold
          column topples independently with probability p_topple per sweep", and a pure gate
          implements exactly that while making evaluation skippable: a column whose state did
          not change keeps its eligibility, so only changed neighborhoods are re-checked, and
          an empty eligible set means the sweep returns in O(1) touching nothing.

PREDICT   Settled hold touches <1% of columns (exactly 0 when the eligible set is empty) and
          costs ~constant wall-clock across W=161..1281; a k-topple wake touches only its
          neighborhood (<50% of W); per-sweep topple counts AND final h/crit fields are
          bit-identical between full-field reference and dirty sweep on the same seed.

FALSIFIER The falsifier fires if (a) any physics divergence vs the full-field reference on any
          width, or (b) a settled hold touches >=1% of columns, or (c) hold wall-clock grows
          >3x from W=161 to W=1281, or (d) one grain-drop wake touches >50% of W, or (e) the
          gate law itself is broken (frequency/autocorrelation off Bernoulli(p_topple)).

Run:  python tools/probes/dirty_set_economy.py
"""
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Chimera")))
from core.trainables import granular as g   # noqa: E402

GENOME = {"h_crit_mean": 1.5, "p_topple": 0.6, "p_stick": 0.03}
WIDTHS = [161, 321, 641, 1281]
HOLD_SWEEPS = 2000
N_POKES = 5
WALL_RATIO_MAX = 3.0
MASK64 = (1 << 64) - 1


# --- the deterministic gate law -------------------------------------------------

def _gate_u(seed: int, sweep: int, col: int) -> float:
    """u in [0,1): splitmix64 finalizer over (seed, sweep+1, col+1). Pure -- no stream
    state, so gating a subset of columns is bit-identical to gating all of them."""
    z = (seed + 0x9E3779B97F4A7C15 * (sweep + 1)) & MASK64
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK64
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK64
    z ^= z >> 31
    z = (z + 0xC2B2AE3D27D4EB4F * (col + 1)) & MASK64
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK64
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK64
    z ^= z >> 31
    return (z >> 11) * 1.1102230246251565e-16


def _eligible(j, h, crit_grid, W):
    """Over-threshold at column j? d_best = max(d_l, d_r): production's parity tie-break
    only picks a DIRECTION when d_l == d_r, where both branches yield the same value -- so
    eligibility is parity-independent and an eligible set computed after sweep s stays valid
    for sweep s+1."""
    hj = int(h[j])
    if hj == 0:
        return False
    tc = int(crit_grid[hj - 1, j])
    if tc == g.FROZEN:
        return False
    dl = -1 if j == 0 else int(h[j] - h[j - 1])
    dr = -1 if j == W - 1 else int(h[j] - h[j + 1])
    return max(dl, dr) > tc


# --- the two sweeps ---------------------------------------------------------------

def _ref_sweep_v2(h, crit_grid, rng, p_topple, h_crit_mean, p_stick, parity, world_seed, s):
    """Full-field sweep under the deterministic gate law. O(W). THE reference."""
    W = len(h)
    occ = h > 0
    if not occ.any():
        return 0
    top_crit = np.full(W, g.FROZEN, dtype=np.uint16)
    idx = np.flatnonzero(occ)
    top_crit[idx] = crit_grid[h[idx] - 1, idx]

    d_l = np.empty(W, dtype=np.int32)
    d_r = np.empty(W, dtype=np.int32)
    d_l[1:] = h[1:] - h[:-1]
    d_r[:-1] = h[:-1] - h[1:]
    d_l[0] = -1
    d_r[-1] = -1
    go_left = d_l > d_r if parity else d_l >= d_r
    d_best = np.where(go_left, d_l, d_r)
    elig_idx = np.flatnonzero(occ & (top_crit != g.FROZEN) & (d_best > top_crit))
    if elig_idx.size == 0:
        return 0
    src_list = [int(j) for j in elig_idx if _gate_u(world_seed, s, int(j)) < p_topple]
    if not src_list:
        return 0
    src = np.array(src_list, dtype=np.int64)
    dst = np.where(go_left[src], src - 1, src + 1).astype(np.int64)

    np.subtract.at(h, src, 1)
    np.add.at(h, dst, 1)
    fresh = g._sample_crit(rng, dst.size, h_crit_mean, p_stick)
    g._scatter_new_tops(crit_grid, h, dst, fresh)
    return int(src.size)


def _dirty_sweep(h, crit_grid, rng, E, p_topple, h_crit_mean, p_stick, parity, world_seed, s):
    """Dirty sweep. Invariant: E is exactly the eligible set at pre-sweep state. Gates only
    E; re-checks eligibility only on the changed neighborhood. Returns (topples, new_E, touches)."""
    W = len(h)
    if not E:
        return 0, E, 0
    src_list = [j for j in E if _gate_u(world_seed, s, j) < p_topple]
    touches = len(E)
    if not src_list:
        return 0, E, touches
    src = np.array(sorted(src_list), dtype=np.int64)

    jl = np.clip(src - 1, 0, W - 1)
    jr = np.clip(src + 1, 0, W - 1)
    d_l = h[src] - h[jl]
    d_r = h[src] - h[jr]
    m0 = src == 0
    if m0.any():
        d_l[m0] = -1
    me = src == W - 1
    if me.any():
        d_r[me] = -1
    go_left = d_l > d_r if parity else d_l >= d_r
    dst = np.where(go_left, src - 1, src + 1).astype(np.int64)

    np.subtract.at(h, src, 1)
    np.add.at(h, dst, 1)
    fresh = g._sample_crit(rng, dst.size, h_crit_mean, p_stick)
    g._scatter_new_tops(crit_grid, h, dst, fresh)

    changed = np.unique(np.concatenate([src, dst]))
    region = set()
    for k in changed.tolist():
        if k - 1 >= 0:
            region.add(k - 1)
        region.add(int(k))
        if k + 1 < W:
            region.add(k + 1)
    touches += len(region)
    new_E = (set(E) - region) | {j for j in region if _eligible(j, h, crit_grid, W)}
    return int(src.size), new_E, touches


def _poke(h, crit_grid, rng, E, col, hm, ps):
    """Drop one grain at col and refresh eligibility on its neighborhood."""
    W = len(h)
    h[col] += 1
    g._scatter_new_tops(crit_grid, h, np.array([col]), g._sample_crit(rng, 1, hm, ps))
    region = {j for j in (col - 1, col, col + 1) if 0 <= j < W}
    return (set(E) - region) | {j for j in region if _eligible(j, h, crit_grid, W)}


# --- build a settled field under the reference ------------------------------------

def _build_settled(W, seed):
    hm, pt, ps = GENOME["h_crit_mean"], GENOME["p_topple"], GENOME["p_stick"]
    rng = np.random.default_rng(seed)
    h = np.zeros(W, dtype=np.int32)
    crit_grid = np.full((g.HMAX, W), g.FROZEN, dtype=np.uint8)
    center = W // 2
    poured, quiet = 0, 0
    for s in range(g.BUILD_SWEEPS):
        if poured < g.N_GRAINS:
            n = min(g.POUR_PER_SWEEP, g.N_GRAINS - poured)
            cols = center + rng.integers(-g.POUR_HALF, g.POUR_HALF + 1, size=n)
            np.add.at(h, cols, 1)
            if h.max() >= g.HMAX - 2:
                return None
            g._scatter_new_tops(crit_grid, h, cols, g._sample_crit(rng, n, hm, ps))
            poured += n
        t = _ref_sweep_v2(h, crit_grid, rng, pt, hm, ps, s & 1, seed, s)
        if poured >= g.N_GRAINS:
            quiet = quiet + 1 if t == 0 else 0
            if quiet >= g.K_QUIET:
                return h, crit_grid
    return None


# --- Phase 0: the gate law itself ---------------------------------------------------

def phase0_gate_law():
    """u must be Uniform[0,1) and uncorrelated; the topple INDICATOR [u < p] must be
    Bernoulli(p). (Testing u itself against p is a category error -- u IS uniform.)"""
    p = GENOME["p_topple"]
    n = 200_000
    cols = np.fromiter((_gate_u(12345, 7, j) for j in range(n)), dtype=np.float64, count=n)
    rows = np.fromiter((_gate_u(12345, s, 99) for s in range(n)), dtype=np.float64, count=n)
    u_mean, u_std = float(cols.mean()), float(cols.std())
    ind = cols < p
    i_mean, i_std = float(ind.mean()), float(ind.astype(np.float64).std())
    tol_u = 4.0 * (1 / 12 / n) ** 0.5          # uniform variance 1/12
    tol_i = 4.0 * (p * (1 - p) / n) ** 0.5     # Bernoulli variance p(1-p)
    rho_c = float(np.corrcoef(cols[:-1], cols[1:])[0, 1])
    rho_t = float(np.corrcoef(rows[:-1], rows[1:])[0, 1])
    print(f"  u uniformity: mean={u_mean:.4f} (0.5+/-{tol_u:.4f})  std={u_std:.3f} "
          f"(uniform {1 / 12 ** 0.5:.3f})")
    print(f"  [u<p] Bernoulli: freq={i_mean:.4f} (p={p}, tol+/-{tol_i:.4f})  std={i_std:.3f} "
          f"(Bernoulli {(p * (1 - p)) ** 0.5:.3f})  rho_col={rho_c:+.4f}  rho_time={rho_t:+.4f}")
    bad = []
    if abs(u_mean - 0.5) > tol_u or abs(u_std - 1 / 12 ** 0.5) > tol_u:
        bad.append(f"gate u not uniform (mean {u_mean:.4f}, std {u_std:.3f})")
    if abs(i_mean - p) > tol_i:
        bad.append(f"topple frequency {i_mean:.4f} off p_topple by >4 sigma")
    if abs(i_std - (p * (1 - p)) ** 0.5) > tol_i:
        bad.append(f"topple std {i_std:.3f} not Bernoulli-like")
    if abs(rho_c) > 0.05 or abs(rho_t) > 0.05:
        bad.append(f"gate autocorrelation too high (col {rho_c:+.4f}, time {rho_t:+.4f})")
    return bad


# --- Phase 1: physics identity, full-field vs dirty ---------------------------------

def phase1_identity(W):
    built = _build_settled(W, g.EVAL_SEED)
    if built is None:
        return False, "field never settled under reference"
    h0, c0 = built
    hm, pt, ps = GENOME["h_crit_mean"], GENOME["p_topple"], GENOME["p_stick"]
    seed_cmp = 987654321 + W
    rng_a = np.random.default_rng(seed_cmp)
    rng_b = np.random.default_rng(seed_cmp)
    hA, cA = h0.copy(), c0.copy()
    hB, cB = h0.copy(), c0.copy()
    E = {j for j in range(W) if _eligible(j, hB, cB, W)}
    s = 0

    for i in range(HOLD_SWEEPS):
        tA = _ref_sweep_v2(hA, cA, rng_a, pt, hm, ps, s & 1, seed_cmp, s)
        tB, E, _ = _dirty_sweep(hB, cB, rng_b, E, pt, hm, ps, s & 1, seed_cmp, s)
        if tA != tB or not np.array_equal(hA, hB) or not np.array_equal(cA, cB):
            return False, f"hold diverged at sweep {i} (t_ref={tA}, t_dirty={tB})"
        s += 1

    for p in range(N_POKES):
        col_a = int(rng_a.integers(0, W))
        col_b = int(rng_b.integers(0, W))
        if col_a != col_b:
            return False, f"poke {p}: rng streams desynced (col {col_a} vs {col_b})"
        E_pre = set(E)
        E_A = _poke(hA, cA, rng_a, E_pre, col_a, hm, ps)
        E_B = _poke(hB, cB, rng_b, E_pre, col_b, hm, ps)
        if E_A != E_B:
            return False, f"poke {p}: eligible sets diverged ({len(E_A)} vs {len(E_B)})"
        E = E_B
        quiet = 0
        for q in range(g.PROBE_SWEEPS):
            tA = _ref_sweep_v2(hA, cA, rng_a, pt, hm, ps, s & 1, seed_cmp, s)
            tB, E, _ = _dirty_sweep(hB, cB, rng_b, E, pt, hm, ps, s & 1, seed_cmp, s)
            if tA != tB or not np.array_equal(hA, hB) or not np.array_equal(cA, cB):
                return False, f"poke {p} diverged at sweep {q} (t_ref={tA}, t_dirty={tB})"
            quiet = quiet + 1 if tA == 0 else 0
            s += 1
            if quiet >= g.PROBE_QUIET:
                break
    return True, f"{HOLD_SWEEPS} hold sweeps + {N_POKES} pokes bit-identical"


# --- Phase 2: the economy -------------------------------------------------------------

def phase2_economy(W):
    built = _build_settled(W, g.EVAL_SEED)
    if built is None:
        return None
    h0, c0 = built
    hm, pt, ps = GENOME["h_crit_mean"], GENOME["p_topple"], GENOME["p_stick"]
    seed2 = 424242 + W

    E = {j for j in range(W) if _eligible(j, h0, c0, W)}
    rng_d = np.random.default_rng(seed2)
    t0 = time.perf_counter()
    max_touches = 0
    for i in range(HOLD_SWEEPS):
        _, E, tc = _dirty_sweep(h0, c0, rng_d, E, pt, hm, ps, i & 1, seed2, i)
        if tc > max_touches:
            max_touches = tc
    dirty_us = (time.perf_counter() - t0) / HOLD_SWEEPS * 1e6

    h_r, c_r = h0.copy(), c0.copy()
    rng_r = np.random.default_rng(seed2)
    t0 = time.perf_counter()
    for i in range(HOLD_SWEEPS):
        _ref_sweep_v2(h_r, c_r, rng_r, pt, hm, ps, i & 1, seed2, i)
    ref_us = (time.perf_counter() - t0) / HOLD_SWEEPS * 1e6

    # one grain-drop wake: total touches over the whole avalanche
    h_w, c_w = h0.copy(), c0.copy()
    Ew = {j for j in range(W) if _eligible(j, h_w, c_w, W)}
    rng_w = np.random.default_rng(seed2 + 1)
    col = int(np.argmax(h_w))
    Ew = _poke(h_w, c_w, rng_w, Ew, col, hm, ps)
    wake_touches = 0
    quiet = 0
    for i in range(g.PROBE_SWEEPS):
        _, Ew, tc = _dirty_sweep(h_w, c_w, rng_w, Ew, pt, hm, ps, i & 1, seed2 + 1, i)
        wake_touches += tc
        quiet = quiet + 1 if tc == 0 else 0   # no topples -> state (and E) unchanged
        if quiet >= g.PROBE_QUIET:
            break
    return {"dirty_us": dirty_us, "ref_us": ref_us,
            "hold_max_touches": max_touches, "wake_touches": wake_touches}


def main():
    print("V62 probe -- dirty-set grain sweep economy (corrected draft)")
    print(f"  genome: {GENOME}   widths: {WIDTHS}")
    fired = []

    print("\nPhase 0 -- gate law (must be Bernoulli(p_topple), uncorrelated):")
    for bad in phase0_gate_law():
        fired.append("gate law: " + bad)

    print(f"\nPhase 1 -- physics identity, full-field ref vs dirty ({HOLD_SWEEPS} hold sweeps"
          f" + {N_POKES} pokes per width):")
    for W in WIDTHS:
        ok, detail = phase1_identity(W)
        print(f"  W={W:>5}: {'IDENTICAL' if ok else 'DIVERGED'} -- {detail}")
        if not ok:
            fired.append(f"W={W} physics divergence: {detail}")

    print("\nPhase 2 -- economy (settled hold + one grain-drop wake):")
    stats = {}
    for W in WIDTHS:
        st = phase2_economy(W)
        if st is None:
            fired.append(f"W={W} field never settled")
            continue
        stats[W] = st
        print(f"  W={W:>5}: hold dirty {st['dirty_us']:8.2f} us/sweep (max touches "
              f"{st['hold_max_touches']})   ref {st['ref_us']:8.2f} us/sweep   "
              f"wake touches {st['wake_touches']} ({100*st['wake_touches']/W:.1f}% of W)")

    if len(stats) == len(WIDTHS):
        ratio = stats[WIDTHS[-1]]["dirty_us"] / max(stats[WIDTHS[0]]["dirty_us"], 1e-9)
        print(f"\n  hold wall-clock ratio W={WIDTHS[-1]}/W={WIDTHS[0]}: {ratio:.2f}x "
              f"(bound {WALL_RATIO_MAX}x)")
        if ratio > WALL_RATIO_MAX:
            fired.append(f"hold wall-clock grew {ratio:.2f}x across widths (>{WALL_RATIO_MAX}x)")
    for W, st in stats.items():
        if st["hold_max_touches"] >= max(1, int(0.01 * W)):
            fired.append(f"W={W}: settled hold touched {st['hold_max_touches']} columns "
                         f"(>=1% of W)")
        if st["wake_touches"] > 0.5 * W:
            fired.append(f"W={W}: grain-drop wake touched {st['wake_touches']} columns (>50% of W)")

    print("\n" + "=" * 72)
    if fired:
        print("VERDICT: FALSIFIER FIRED")
        for f in fired:
            print(f"  - {f}")
    else:
        print("VERDICT: FALSIFIER NOT FIRED -- dirty-set sweep holds a settled field at "
              "~0 cost with bit-identical physics to the full-field reference.")


if __name__ == "__main__":
    main()
