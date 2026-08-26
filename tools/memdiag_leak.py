#!/usr/bin/env python
"""memdiag_leak.py -- DEFINITIVE long-horizon leak isolation (T2/RUN B memory bug).

Per the handoff, short slices are USELESS: host AND device were FLAT over 12-30
ticks. The leak only fires after many ticks. This harness loops each prime-suspect
component ALONE over a long horizon (N=1000) with positions that MOVE so n_cells
jitters across a wide range (mimicking the live dynamics), logging BOTH
rss_gb (host) and dev_mb (device) every tick. The component whose curve climbs is
the leak. Run in background; poll agent_logs/memdiag_leak.log.
"""
from __future__ import annotations
import sys, time, json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools")); sys.path.insert(0, str(ROOT))

import numpy as np

# reuse ca_triangle's telemetry + lattice loader (sets NUMBA_NUM_THREADS etc.)
import tools.ca_triangle as CT
from LightEngine.bh_draw import build_octree
from LightEngine.modifier import compute_forces_mod

N = 1000
LOG = ROOT / "agent_logs" / "memdiag_leak.log"
LOG.parent.mkdir(parents=True, exist_ok=True)
log = open(LOG, "w", encoding="utf-8")


def L(msg):
    log.write(msg + "\n"); log.flush()


# ---- faithful moving lattice: load once, then evolve with slow sinusoid so
# n_cells spans a wide band (not just the 6473<->6766 of 12 ticks) ----
Vg, Tg, A0, S, e_med, n_orig, n_merge = CT.build_lattice()
nV = len(Vg)
base = Vg.astype(np.float64)
amp = 0.8 * e_med                      # displacement amplitude (walk-space units)
rng = np.random.default_rng(12345)
phase = rng.uniform(0, 6.28, size=(nV, 3))
omega = rng.uniform(0.02, 0.10, size=(nV, 3))


def moving_pos(t):
    return np.ascontiguousarray((base + amp * np.sin(omega * t + phase)).astype(np.float32))


# ---- CA setup (replicate ca_triangle main's kept-tri CSR + gradients) ----
degen = A0 < CT.NEAR_ZERO_A0
keep = ~degen
Tc = np.ascontiguousarray(Tg[keep])
Ac = np.ascontiguousarray(A0[keep], dtype=np.float64)
G, _ = CT.area_grads(Vg, Tc)
Tg_flat = np.ascontiguousarray(Tc.ravel())
cnt = np.bincount(Tg_flat, minlength=nV)
start = np.empty(nV + 1, dtype=np.int64); start[0] = 0
np.cumsum(cnt, out=start[1:])
entries = np.empty(3 * len(Tc), dtype=np.int64)
cursor = start[:-1].copy()
for r in range(Tg_flat.shape[0]):
    v = int(Tg_flat[r]); entries[int(cursor[v])] = r; cursor[v] += 1
k = CT.C.K_BOND / CT.C.R_BOND ** 2
vel32 = np.zeros((nV, 3), dtype=np.float32)


def run_build_only():
    L("=== TEST A: build_octree only (host RSS) ===")
    for t in range(N):
        pos = moving_pos(t)
        tree = build_octree(pos, leaf_size=16)
        if t % 5 == 0 or t == N - 1:
            L(f"A tick={t:4d} n_cells={tree['n_cells']:6d} rss_gb={CT._rss_mb()/1000:.3f} "
              f"dev_mb={CT._dev_mb():.1f}")
    L("=== TEST A done ===")


def run_walk_dev():
    L("=== TEST B: build_octree + compute_forces_mod(dev={}) (device VRAM) ===")
    dev = {}
    for t in range(N):
        pos = moving_pos(t)
        tree = build_octree(pos, leaf_size=16)
        acc, power = compute_forces_mod(pos, vel32, tree=tree, out=np.empty((nV,3),np.float32), dev=dev)
        if t % 5 == 0 or t == N - 1:
            L(f"B tick={t:4d} n_cells={tree['n_cells']:6d} rss_gb={CT._rss_mb()/1000:.3f} "
              f"dev_mb={CT._dev_mb():.1f}")
        del tree
    L("=== TEST B done ===")


def run_ca_prange():
    L("=== TEST C: _k1_state + _k2_forces prange only (host RSS) ===")
    for t in range(N):
        pos = moving_pos(t)
        P64 = np.ascontiguousarray(pos, dtype=np.float64)
        sarr, uarr = CT._k1_state(P64, Tc, Ac, k)
        fca = CT._k2_forces(sarr, G, k, start, entries)
        if t % 5 == 0 or t == N - 1:
            L(f"C tick={t:4d} rss_gb={CT._rss_mb()/1000:.3f} dev_mb={CT._dev_mb():.1f}")
    L("=== TEST C done ===")


if __name__ == "__main__":
    L(f"start rss_gb={CT._rss_mb()/1000:.3f} dev_mb={CT._dev_mb():.1f} nV={nV} nT_kept={len(Tc)}")
    run_build_only()
    run_walk_dev()
    run_ca_prange()
    L(f"END rss_gb={CT._rss_mb()/1000:.3f} dev_mb={CT._dev_mb():.1f}")
    log.close()
