"""Quick diagnostic for _physics_match behavior."""
import sys, numpy as np
sys.path.insert(0, 'e:/PythonChimera/Chimera')
from core.trainables import granular as g

GENOME = {'h_crit_mean': 1.5, 'p_topple': 0.6, 'p_stick': 0.03}
HOLD_SWEEPS = 5


def _ref_sweep(h, crit, rng, p_topple, h_crit_mean, p_stick, parity):
    FROZEN = g.FROZEN
    top_crit = np.full(len(h), FROZEN, dtype=np.uint16)
    idx = np.flatnonzero(h > 0)
    if idx.size == 0:
        return 0
    top_crit[idx] = crit[h[idx]-1, idx]
    d_l = np.empty_like(h, dtype=np.int32)
    d_r = np.empty_like(h, dtype=np.int32)
    d_l[1:] = h[1:] - h[:-1]
    d_r[:-1] = h[:-1] - h[1:]
    d_l[0] = -1
    d_r[-1] = -1
    go_left = d_l > d_r if parity else d_l >= d_r
    d_best = np.where(go_left, d_l, d_r)
    eligible = (h > 0) & (top_crit != FROZEN) & (d_best > top_crit)
    rand = rng.random(len(h))
    topple = eligible & (rand < p_topple)
    src = np.flatnonzero(topple)
    if src.size == 0:
        return 0
    dst = np.where(go_left[src], src-1, src+1)
    h[src] -= 1
    h[dst] += 1
    g._scatter_new_tops(crit, h, dst, g._sample_crit(rng, dst.size, h_crit_mean, p_stick))
    return int(src.size)


def _dirty_sweep(h, crit, rng, p_topple, h_crit_mean, p_stick, parity, dirty):
    W = len(h)
    FROZEN = g.FROZEN
    top_crit = np.full(W, FROZEN, dtype=np.uint16)
    idx = np.flatnonzero(h > 0)
    if idx.size == 0:
        return 0, dirty
    top_crit[idx] = crit[h[idx]-1, idx]
    d_l = np.empty(W, dtype=np.int32)
    d_r = np.empty(W, dtype=np.int32)
    d_l[1:] = h[1:] - h[:-1]
    d_r[:-1] = h[:-1] - h[1:]
    d_l[0] = -1
    d_r[-1] = -1
    go_left = d_l > d_r if parity else d_l >= d_r
    d_best = np.where(go_left, d_l, d_r)
    eligible_d = (h > 0) & (top_crit != FROZEN) & (d_best > top_crit)
    expanded = set(dirty)
    for j in dirty:
        if j > 0:
            expanded.add(j-1)
        if j < W-1:
            expanded.add(j+1)
    dm = np.zeros(W, dtype=bool)
    dm[list(expanded)] = True
    rand = rng.random(W)
    topple_d = (eligible_d & dm) & (rand < p_topple)
    src_d = np.flatnonzero(topple_d)
    if src_d.size == 0:
        return 0, dirty
    dst_d = np.where(go_left[src_d], src_d-1, src_d+1)
    h[src_d] -= 1
    h[dst_d] += 1
    g._scatter_new_tops(crit, h, dst_d, g._sample_crit(rng, dst_d.size, h_crit_mean, p_stick))
    dirty = dirty.union(src_d.tolist())
    return int(src_d.size), dirty


def test_physics_match(W):
    seed = 20260718 + W
    # Build field
    h = np.zeros(W, dtype=np.int32)
    crit = np.full((g.HMAX, W), g.FROZEN, dtype=np.uint8)
    rng = np.random.default_rng(seed)
    for _ in range(g.N_GRAINS):
        col = int(rng.integers(0, W))
        h[col] += 1
        g._scatter_new_tops(crit, h, np.array([col]), g._sample_crit(rng, 1, GENOME['h_crit_mean'], GENOME['p_stick']))

    # Settle
    for s in range(g.PROBE_SWEEPS):
        t = _ref_sweep(h, crit, rng, GENOME['p_topple'], GENOME['h_crit_mean'], GENOME['p_stick'], s & 1)
        if t == 0:
            q = 1
            while q < g.PROBE_QUIET and s+q < g.PROBE_SWEEPS:
                if _ref_sweep(h, crit, rng, GENOME['p_topple'], GENOME['h_crit_mean'], GENOME['p_stick'], (s+q) & 1) > 0:
                    break
                q += 1
            break

    # Compare ref vs dirty with shared field state per sweep
    h_a = h.copy()
    crit_a = crit.copy()
    h_b = h.copy()
    crit_b = crit.copy()
    dirty = set()
    for s in range(HOLD_SWEEPS):
        t_ref = _ref_sweep(h_a, crit_a, rng, GENOME['p_topple'], GENOME['h_crit_mean'], GENOME['p_stick'], s & 1)
        t_dirty, dirty = _dirty_sweep(h_b, crit_b, rng, GENOME['p_topple'], GENOME['h_crit_mean'], GENOME['p_stick'], s & 1, dirty)
        print(f"  W={W} s={s}: ref={t_ref} dirty={t_dirty} dirty_set_size={len(dirty)} h_a={h_a.sum()} h_b={h_b.sum()}")
        if t_ref != t_dirty:
            return False
        if not np.array_equal(h_a, h_b) or not np.array_equal(crit_a, crit_b):
            return False
    return True


for W in [161, 321, 641]:
    ok = test_physics_match(W)
    print(f"W={W}: {'PASS' if ok else 'FAIL'}")
