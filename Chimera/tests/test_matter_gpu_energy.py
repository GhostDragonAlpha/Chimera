"""test_matter_gpu_energy — THE_LIVING_MATTER Phase 1's instrument, under test.

Two guarantees, both measured against CPU ground truth on a small lattice:

  1. EXACTNESS. The on-device energy trace IS the Hamiltonian of the grid, with the
     flip kernel's own conventions (18-connectivity, out-of-bounds = MEDIUM, pair sum
     halved, area term over t != MEDIUM only): the last trace value must equal the
     CPU-computed H of the grid close() returns. (First measured 2026-08-03: 0.0000%
     diff at n=48, 30 sweeps.)

  2. THE FLIP DYNAMICS MINIMIZE. With lam = 0 (area constraint off), the trace falls
     monotone: 0 pass-to-pass sign flips of dH (first measured: 0 of 238 at n=48).
     This isolates the area term as the source of the overshoot the phase falsifier
     caught -- see docs/THE_LIVING_MATTER.md, Phase 1 verdict.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from core.matter import BONE, MUSCLE, SKIN, J_PROVEN_DIFFERENTIAL
from core.matter_gpu import open_lattice, step, close, _OFF18

N, SWEEPS, LAM = 32, 10, 0.9


def _scramble():
    shape = (N, N, N)
    rng = np.random.RandomState(0)
    grid = np.zeros(shape, dtype=np.int16)
    c, r = N // 2, N // 3
    zz, yy, xx = np.mgrid[0:N, 0:N, 0:N]
    blob = (zz - c) ** 2 + (yy - c) ** 2 + (xx - c) ** 2 < r * r
    grid[blob] = rng.choice((BONE, MUSCLE, SKIN), size=int(blob.sum()))
    targets = {t: int((grid == t).sum()) for t in (BONE, MUSCLE, SKIN)}
    return grid, targets, shape


def cpu_H(g, targets, lam):
    """The Hamiltonian, kernel conventions, in numpy -- the ground truth."""
    J = J_PROVEN_DIFFERENTIAL
    gi = g.astype(np.int64)
    pair = np.zeros(gi.shape, dtype=np.float64)
    for dz, dy, dx in _OFF18:
        nb = np.zeros_like(gi)                       # out-of-bounds reads as MEDIUM = 0
        z0, z1 = max(0, -dz), gi.shape[0] - max(0, dz)
        y0, y1 = max(0, -dy), gi.shape[1] - max(0, dy)
        x0, x1 = max(0, -dx), gi.shape[2] - max(0, dx)
        nb[z0:z1, y0:y1, x0:x1] = gi[z0 + dz:z1 + dz, y0 + dy:y1 + dy, x0 + dx:x1 + dx]
        pair += J[gi, nb]
    h = 0.5 * float(pair.sum())
    for t, tgt in targets.items():
        a = int((gi == t).sum())
        h += lam * (a - tgt) ** 2
    return h


def test_trace_matches_cpu_hamiltonian():
    grid, targets, shape = _scramble()
    h = open_lattice(grid, shape, targets, J_PROVEN_DIFFERENTIAL, lam=LAM, seed=0)
    tr = step(h, 8 * SWEEPS, trace=True)
    final = close(h)
    want = cpu_H(final, targets, LAM)
    assert tr.shape == (8 * SWEEPS,)
    assert abs(tr[-1] - want) / max(abs(want), 1e-9) < 1e-4, \
        f"trace[-1] {tr[-1]:.1f} != cpu H {want:.1f} -- the on-device Hamiltonian is " \
        f"not the one in the kernel"


def test_flip_dynamics_minimize_without_area_term():
    grid, targets, shape = _scramble()
    h = open_lattice(grid, shape, targets, J_PROVEN_DIFFERENTIAL, lam=0.0, seed=0)
    tr = step(h, 8 * SWEEPS, trace=True)
    close(h)
    d = np.diff(tr)
    flips = int((d[1:] * d[:-1] < 0).sum())
    assert tr[-1] < tr[0], "lam=0 trace did not fall"
    assert flips == 0, f"lam=0 trace is not monotone ({flips} sign flips) -- the flip " \
                       f"dynamics themselves are suspect, not just the area term"


if __name__ == "__main__":
    test_trace_matches_cpu_hamiltonian()
    print("PASS  trace == CPU Hamiltonian")
    test_flip_dynamics_minimize_without_area_term()
    print("PASS  lam=0 trace monotone")
