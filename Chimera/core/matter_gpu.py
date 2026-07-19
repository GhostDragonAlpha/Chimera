"""matter_gpu — THE SHAKER ON THE GPU: assemble_3d as a Warp kernel.

Commissioned 2026-07-18, the human, watching a cold 4090 during the 'scaled test':
"Something's not right, my GPU should be cooking right now." Correct: growth was the
named wall ('pure-Python adhesion sweeps: 3s -> 486s at 992k — needs GPU, not
patience', task_progress sub-30) and every scaled ambition dies on it. This module
is the unlock: the Cellular Potts / Metropolis shaker (core/matter.py assemble_3d,
semantics mirrored line-for-line) run as a Warp kernel — 'shaking it up in our big
shaker to find out which position is most optimal', at tens of millions of
cell-updates per second.

PARALLELIZATION, HONESTLY STATED (the bigbang_gpu discipline — deviations named):
  - 8-COLOR CHECKERBOARD: each sweep runs 8 phases keyed by (x%2, y%2, z%2). Two
    same-color cells differ by an EVEN delta on every axis, so they are never
    neighbours under any Chebyshev-1 connectivity (6/18/26): a phase's writes are
    disjoint from every cell it reads. Race-free by construction, no locks.
  - AREA LAG: the CPU original updates global per-type areas after EVERY accepted
    copy; the GPU accumulates atomic deltas and folds them in at PHASE boundaries,
    so the soft area constraint sees counts stale by < one phase. A documented
    approximation (lambda's quadratic is soft; targets are ~10^4-10^6), verified
    by the parity gate in __main__: same layering order, areas within tolerance.
  - RNG: wp.rand_init(seed, unique_offset) per site per phase per sweep —
    deterministic for a given (seed, shape), independent of launch config.
  - FROZEN SCAFFOLD: frozen cells are never selected and never copied — the
    negative-space contract (bone axes today; TERRAIN tomorrow: the ground as
    the mold objects grow around, per the operator's directive).

Same signature as matter.assemble_3d, so the CPU heart can be swapped out from
under core/limb.py without touching it:

    import core.limb as limb_mod, core.matter_gpu as mg
    limb_mod.assemble = mg.assemble_3d_gpu          # (or matter.assemble_3d)

FACTS ONLY; the objective files say what good means. Parity gate: __main__ grows
the same scrambled blob on CPU and GPU and compares the STRUCTURE (bone core /
muscle between / skin shell radius ordering + area errors), never bitwise cells —
two correct stochastic anneals need not agree cell-for-cell.
"""

from __future__ import annotations

import math

import numpy as np
import warp as wp

from core.matter import MEDIUM

wp.init()


@wp.kernel
def k_potts_phase(L: wp.array(dtype=wp.int32),
                  areas: wp.array(dtype=wp.int32),
                  deltas: wp.array(dtype=wp.int32),
                  J: wp.array2d(dtype=wp.float32),
                  targets: wp.array(dtype=wp.float32),
                  offsets: wp.array(dtype=wp.int32),
                  n_off: int,
                  nx: int, ny: int, nz: int,
                  phase: int, sweep: int, seed: int,
                  temp: float, lam: float, frozen: int,
                  n_types: int):
    tid = wp.tid()
    # Decode this thread's cell inside the phase's sub-lattice (interior only).
    px = phase & 1
    py = (phase >> 1) & 1
    pz = (phase >> 2) & 1
    sx = (nx - 2 + 1 - px) / 2
    sy = (ny - 2 + 1 - py) / 2
    sz = (nz - 2 + 1 - pz) / 2
    if tid >= sx * sy * sz:
        return
    cx = 1 + px + 2 * (tid % sx)
    cy = 1 + py + 2 * ((tid / sx) % sy)
    cz = 1 + pz + 2 * (tid / (sx * sy))
    if cx >= nx - 1 or cy >= ny - 1 or cz >= nz - 1:
        return
    s = (cz * ny + cy) * nx + cx

    old = L[s]
    if old == frozen:
        return

    state = wp.rand_init(seed, (sweep * 8 + phase) * (nx * ny * nz) + s)
    k = wp.randi(state, 0, n_off)
    new = L[s + offsets[k]]
    if new == old or new == frozen:
        return

    dH = float(0.0)
    for d in range(n_off):
        nb = L[s + offsets[d]]
        dH += J[new, nb] - J[old, nb]
    if old != MEDIUM:
        a = float(areas[old] + deltas[old])
        t = targets[old]
        dH += lam * ((a - 1.0 - t) * (a - 1.0 - t) - (a - t) * (a - t))
    if new != MEDIUM:
        a = float(areas[new] + deltas[new])
        t = targets[new]
        dH += lam * ((a + 1.0 - t) * (a + 1.0 - t) - (a - t) * (a - t))

    if dH <= 0.0 or wp.randf(state) < wp.exp(-dH / temp):
        L[s] = new
        if old != MEDIUM:
            wp.atomic_add(deltas, old, -1)
        if new != MEDIUM:
            wp.atomic_add(deltas, new, 1)


def assemble_3d_gpu(grid, shape, targets, J, connectivity=18, sweeps=90,
                    temp=12.0, lam=0.9, seed=0, frozen_type=None):
    """Drop-in GPU twin of matter.assemble_3d (see module docstring for the two
    stated deviations). Returns the annealed grid as int16 numpy, same as CPU."""
    nz, ny, nx = int(shape[0]), int(shape[1]), int(shape[2])
    n_types = int(J.shape[0])

    # Neighbour offsets in FLAT index space, same construction as _nd_offsets.
    offs = []
    for dz in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dz == 0 and dy == 0 and dx == 0:
                    continue
                order = abs(dz) + abs(dy) + abs(dx)
                if connectivity == 6 and order > 1:
                    continue
                if connectivity == 18 and order > 2:
                    continue
                offs.append((dz * ny + dy) * nx + dx)
    offsets_np = np.array(offs, dtype=np.int32)

    dev = wp.get_device()
    L = wp.array(np.ascontiguousarray(grid.reshape(-1)).astype(np.int32),
                 dtype=wp.int32, device=dev)
    Jw = wp.array(J.astype(np.float32), dtype=wp.float32, device=dev)
    tgt = np.zeros(n_types, dtype=np.float32)
    for t, v in targets.items():
        tgt[int(t)] = float(v)
    tw = wp.array(tgt, dtype=wp.float32, device=dev)
    ow = wp.array(offsets_np, dtype=wp.int32, device=dev)

    areas0 = np.zeros(n_types, dtype=np.int32)
    for t in range(n_types):
        areas0[t] = int((grid == t).sum())
    areas = wp.array(areas0, dtype=wp.int32, device=dev)
    deltas = wp.zeros(n_types, dtype=wp.int32, device=dev)

    frz = int(frozen_type) if frozen_type is not None else -999
    max_threads = ((nx // 2) + 1) * ((ny // 2) + 1) * ((nz // 2) + 1)

    @wp.kernel
    def k_fold(areas_: wp.array(dtype=wp.int32),
               deltas_: wp.array(dtype=wp.int32)):
        i = wp.tid()
        areas_[i] = areas_[i] + deltas_[i]
        deltas_[i] = 0

    for sweep in range(int(sweeps)):
        for phase in range(8):
            wp.launch(k_potts_phase, dim=max_threads,
                      inputs=[L, areas, deltas, Jw, tw, ow,
                              len(offs), nx, ny, nz,
                              phase, sweep, int(seed) + 101,
                              float(temp), float(lam), frz, n_types],
                      device=dev)
            wp.launch(k_fold, dim=n_types, inputs=[areas, deltas], device=dev)
    wp.synchronize_device(dev)
    return L.numpy().astype(np.int16).reshape(shape)


if __name__ == "__main__":
    import time

    from core import matter

    rng = np.random.default_rng(0)
    S = (72, 72, 72)
    J, _mc = (matter.J, None) if hasattr(matter, "J") else (None, None)
    if J is None:
        J = matter._build_J_from_library()[0]
    J = np.asarray(J, dtype=float)

    # Scrambled blob: a sphere of random tissue in medium (the classic start).
    zz, yy, xx = np.mgrid[0:S[0], 0:S[1], 0:S[2]]
    r2 = (zz - 36) ** 2 + (yy - 36) ** 2 + (xx - 36) ** 2
