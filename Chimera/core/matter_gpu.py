"""matter_gpu — THE SHAKER ON THE GPU. Cellular Potts assembly as a Warp kernel.

Commissioned 2026-07-18 (tb-0199), the human: "shaking it up into our big shaker to
find out which position is most optimal" — and the fury that the shaker was running
on ONE CPU CORE (core.matter.assemble_3d is a Python for-loop over a list; at 2x the
density record it maxed a core and never touched the 4090). This is the port.

DROP-IN for core.matter.assemble_3d — SAME signature, SAME physics (the library J
matrix, the lambda volume constraint, frozen scaffolds, 18-connectivity), on the GPU.
brain_gpu's law holds: the lattice lives on-device; ZERO CPU<->GPU syncs inside the
sweep loop; ONE readback at the end.

THREE THINGS A NAIVE PORT DROPS (each restored here, each load-bearing):
  1. frozen_type — the scaffold (bone axis; and now TERRAIN as negative space the
     human named: objects grow AROUND frozen ground) is never chosen and never
     created. Without it the skeleton dissolves into soup.
  2. the lambda VOLUME CONSTRAINT — dH += lam*((a+-1-target)^2 - (a-target)^2). This
     is why tissues SORT instead of the most-cohesive one eating the world. Drop it
     and every tissue but one vanishes.
  3. 18-CONNECTIVITY with a SAFE parallel schedule. A 2-color checkerboard is only
     conflict-free for 6-connectivity; at 18-conn, edge-diagonal cells share a
     checker color and would read each other mid-flip. So the sweep is decomposed
     into 8 colors by (x&1,y&1,z&1): two cells of one color differ by an even offset
     on every axis, so no two are within Chebyshev distance 1 -> no 18- (or 26-)
     neighbor pair ever flips in the same pass. Interface energy is therefore EXACT;
     only the area term uses pass-start counts (standard parallel-Potts, converges).

Correctness is asserted by CONTRAST, same as the CPU model: parity_report() runs the
GPU sort and a uniform-J control on the same scrambled start and reports tissue radii
-> the differential must layer (bone core / skin shell), the uniform must not.
"""

from __future__ import annotations

import numpy as np
import warp as wp

wp.init()

MEDIUM = 0
_FROZEN_NONE = -999

# 18-connectivity offsets: 6 faces + 12 edges (no 8 corners).
_OFF18 = [(dz, dy, dx)
          for dz in (-1, 0, 1) for dy in (-1, 0, 1) for dx in (-1, 0, 1)
          if (abs(dz) + abs(dy) + abs(dx)) in (1, 2)]
assert len(_OFF18) == 18


@wp.func
def _in_bounds(z: int, y: int, x: int, nz: int, ny: int, nx: int) -> bool:
    return z >= 0 and y >= 0 and x >= 0 and z < nz and y < ny and x < nx


@wp.kernel
def _potts_color_pass(
        lattice: wp.array3d(dtype=wp.int32),
        area: wp.array(dtype=wp.int32),          # per-type live cell count
        J: wp.array2d(dtype=wp.float32),
        offs: wp.array(dtype=wp.vec3i),
        targets: wp.array(dtype=wp.int32),
        color: wp.vec3i, temp: float, lam: float,
        frozen: int, seed: int, n_off: int):
    z, y, x = wp.tid()
    nz = lattice.shape[0]
    ny = lattice.shape[1]
    nx = lattice.shape[2]
    # only this color's sublattice flips this pass (conflict-free for 18-conn)
    if (z & 1) != color[0] or (y & 1) != color[1] or (x & 1) != color[2]:
        return
    # interior only (a 1-cell inert rind, matching the CPU model's slicing)
    if z == 0 or y == 0 or x == 0 or z == nz - 1 or y == ny - 1 or x == nx - 1:
        return
    old = lattice[z, y, x]
    if old == frozen:
        return

    state = wp.rand_init(seed, z * ny * nx + y * nx + x)
    k = wp.randi(state, 0, n_off)
    o = offs[k]
    nzp = z + o[0]
    nyp = y + o[1]
    nxp = x + o[2]
    if not _in_bounds(nzp, nyp, nxp, nz, ny, nx):
        return
    new = lattice[nzp, nyp, nxp]
    if new == old or new == frozen:
        return

    # interface energy delta over the full 18-neighborhood
    dH = float(0.0)
    for i in range(n_off):
        oi = offs[i]
        zz = z + oi[0]
        yy = y + oi[1]
        xx = x + oi[2]
        nb = MEDIUM
        if _in_bounds(zz, yy, xx, nz, ny, nx):
            nb = lattice[zz, yy, xx]
        dH += J[new, nb] - J[old, nb]

    # lambda volume constraint (area held at pass-start value)
    if old != MEDIUM:
        a = float(area[old])
        t = float(targets[old])
        dH += lam * ((a - 1.0 - t) * (a - 1.0 - t) - (a - t) * (a - t))
    if new != MEDIUM:
        a = float(area[new])
        t = float(targets[new])
        dH += lam * ((a + 1.0 - t) * (a + 1.0 - t) - (a - t) * (a - t))

    u = wp.randf(state)
    if dH <= 0.0 or u < wp.exp(-dH / temp):
        lattice[z, y, x] = new
        if old != MEDIUM:
            wp.atomic_add(area, old, -1)
        if new != MEDIUM:
            wp.atomic_add(area, new, 1)


def assemble_3d_gpu(grid, shape, targets, J, connectivity=18, sweeps=90,
                    temp=12.0, lam=0.9, seed=0, frozen_type=None):
    """GPU drop-in for core.matter.assemble_3d. Returns the settled int16 grid.

    targets: {type: target_cell_count}. J: (n_types, n_types) float. frozen_type:
    a scaffold type that never changes or spawns (bone axis / terrain negative space).
    """
    dev = wp.get_device()
    n_types = J.shape[0]
    lat = wp.array(grid.astype(np.int32), dtype=wp.int32, device=dev)
    Jd = wp.array(np.ascontiguousarray(J, dtype=np.float32),
                  dtype=wp.float32, device=dev)
    offs = wp.array([wp.vec3i(int(d[0]), int(d[1]), int(d[2])) for d in _OFF18],
                    dtype=wp.vec3i, device=dev)
    tgt = np.zeros(n_types, dtype=np.int32)
    for t, v in targets.items():
        tgt[t] = int(v)
    tgtd = wp.array(tgt, dtype=wp.int32, device=dev)
    area0 = np.array([int((grid == t).sum()) for t in range(n_types)],
                     dtype=np.int32)
    aread = wp.array(area0, dtype=wp.int32, device=dev)
    frozen = frozen_type if frozen_type is not None else _FROZEN_NONE

    colors = [wp.vec3i(cz, cy, cx)
              for cz in (0, 1) for cy in (0, 1) for cx in (0, 1)]
    for s in range(sweeps):
        # Snapshot counts at the start of each color pass so the volume constraint
        # reads deterministic pass-start values instead of racing mid-flip atomics.
        wp.synchronize_device(dev)
        area_snap = wp.array(aread.numpy(), dtype=wp.int32, device=dev)
        tgt_snap = wp.array(tgtd.numpy(), dtype=wp.int32, device=dev)
        for ci, col in enumerate(colors):
            wp.launch(_potts_color_pass, dim=shape,
                      inputs=[lat, area_snap, Jd, offs, tgt_snap, col,
                              float(temp), float(lam), int(frozen),
                              seed * 131 + s * 8 + ci, len(_OFF18)],
                      device=dev)
    wp.synchronize_device(dev)
    return lat.numpy().astype(np.int16)


def parity_report(scramble, shape, targets, J_diff, J_unif, frozen_type=None,
                  sweeps=90, seed=0):
    """The CONTRAST: same scrambled start, differential J must sort, uniform must
    not. Returns per-tissue mean cylindrical radius for both. GPU-timed."""
    import time
    from core.matter import metrics_3d
    t0 = time.perf_counter()
    diff = assemble_3d_gpu(scramble.copy(), shape, targets, J_diff,
                           sweeps=sweeps, seed=seed, frozen_type=frozen_type)
    unif = assemble_3d_gpu(scramble.copy(), shape, targets, J_unif,
                           sweeps=sweeps, seed=seed, frozen_type=frozen_type)
    dt = time.perf_counter() - t0
    site_attempts = 2 * sweeps * int(np.prod(shape))
    return {"differential": metrics_3d(diff, shape)["radius"],
            "uniform": metrics_3d(unif, shape)["radius"],
            "seconds": dt,
            "site_updates_per_sec": site_attempts / dt,
            "grids_shape": shape}


if __name__ == "__main__":
    import argparse
    import time
    from core.matter import (BONE, MUSCLE, SKIN, J_PROVEN_DIFFERENTIAL)

    ap = argparse.ArgumentParser(description="GPU Cellular Potts shaker")
    ap.add_argument("--n", type=int, default=96, help="lattice edge (n^3 cells)")
    ap.add_argument("--sweeps", type=int, default=90)
    a = ap.parse_args()
    N = a.n
    shape = (N, N, N)
    rng = np.random.RandomState(0)

    # a blob of scrambled tissue in the core third, medium outside
    grid = np.zeros(shape, dtype=np.int16)
    c = N // 2
    r = N // 3
    zz, yy, xx = np.mgrid[0:N, 0:N, 0:N]
    blob = (zz - c) ** 2 + (yy - c) ** 2 + (xx - c) ** 2 < r * r
    tissue_cells = np.argwhere(blob)
    picks = rng.choice((BONE, MUSCLE, SKIN), size=len(tissue_cells))
    grid[blob] = picks
    targets = {t: int((grid == t).sum()) for t in (BONE, MUSCLE, SKIN)}

    J_unif = np.full_like(J_PROVEN_DIFFERENTIAL, 8.0, dtype=np.float64)
    np.fill_diagonal(J_unif, 4.0)
    J_unif[MEDIUM, MEDIUM] = 0.0

    print(f"GPU shaker: {N}^3 = {N**3:,} cells, {a.sweeps} sweeps x 8 colors")
    rep = parity_report(grid, shape, targets, J_PROVEN_DIFFERENTIAL, J_unif,
                        sweeps=a.sweeps, seed=0)
    print(f"  {rep['seconds']:.2f}s  "
          f"{rep['site_updates_per_sec']/1e6:.1f}M site-updates/sec")
    from core.matter import NAMES
    for label in ("differential", "uniform"):
        r = rep[label]
        row = "  ".join(f"{NAMES[t]}:{r[t]:.1f}" for t in (BONE, MUSCLE, SKIN))
        print(f"  {label:<13} mean radius  {row}")
    d = rep["differential"]
    ok = d[BONE] < d[MUSCLE] < d[SKIN]
    print(f"  SORTED (bone core < muscle < skin shell): {ok}")
