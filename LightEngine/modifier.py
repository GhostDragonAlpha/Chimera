"""
LightEngine MODIFIER — the two-force fold (docs/THE_LIGHT_SEED.md, 2026-08-06).

THE MODIFIER (the operator's unification):

    "Then there are not two passes. There is ONE tree walk, and every pairwise
     draw the walk computes is multiplied by a modifier M — and M lives inside
     the membranes."

This module merges the two passes of LightEngine.kernel:

  PASS 1  DRAW        — long-range softened inverse-square
  PASS 2  RESISTANCE  — short-range wall / bond + contact radiation

into ONE modified Barnes-Hut tree walk over ONE octree:

  * FAR nodes (s < theta * d) that lie outside the resistance range
    aggregate the draw and apply no modifier: M -> 1.  A distant neutral
    clump's resistances screen themselves away; the draw alone orbits it.
  * NEAR nodes are descended to leaves; each leaf pair receives the exact
    pairwise draw AND the exact pairwise resistance where |r| <= R_C.
    M awakens in the leaves: M < 0 is the wall, M = 0 is the bond.

The force LAWS are unchanged; only the traversal changed.  kernel.py remains
the two-pass referee; this module is the v2 folded walk.
"""

from __future__ import annotations

import math
import numpy as np
from numba import njit, prange, cuda
from numba.core.errors import NumbaPerformanceWarning
import warnings

from LightEngine.constants import (
    G, K_WALL, K_BOND, R_WALL, R_BOND, R_C, P_WALL, EPS, GAMMA_W, S_WALL,
)
from LightEngine.bh_draw import build_octree, DEFAULT_THETA

warnings.filterwarnings("ignore", category=NumbaPerformanceWarning)

# Softening squared, exactly as the pairwise kernel uses it.
EPS2 = float(EPS * EPS)

# Per-thread traversal stack size, matching bh_draw._STACK_SIZE.
_STACK_SIZE = 64

# ── CUDA availability probe ───────────────────────────────────────
try:
    _cuda_available = bool(cuda.is_available())
except Exception:  # pragma: no cover
    _cuda_available = False


# ═══════════════════════════════════════════════════════════════════
#  CPU / Numba merged walk
# ═══════════════════════════════════════════════════════════════════
@njit(parallel=True, cache=True)
def _mod_walk_cpu(pos: np.ndarray, vel: np.ndarray,
                  sorted_pos: np.ndarray, sorted_idx: np.ndarray,
                  cell_min: np.ndarray, cell_max: np.ndarray,
                  cell_com: np.ndarray, cell_mass: np.ndarray,
                  cell_child: np.ndarray, cell_is_leaf: np.ndarray,
                  cell_leaf_start: np.ndarray, cell_leaf_count: np.ndarray,
                  theta: float, G_val: float, eps2: float,
                  rw: float, rb: float, rc: float, p: float, kw: float,
                  kb: float, gamma_w: float, s_wall: float,
                  out: np.ndarray, power_out: np.ndarray):
    """
    ONE tree walk computing DRAW + RESISTANCE for every point.

    Draw is aggregated at far nodes outside the resistance range (M -> 1);
    leaves compute the exact pairwise draw AND the exact pairwise resistance
    within the cutoff.  Radiated wall power is accumulated per unordered pair
    (half per visit, matching kernel._resist_cpu).
    """
    n = pos.shape[0]
    n_cells = cell_min.shape[0]
    rc2 = rc * rc
    for i in prange(n):
        stack = np.empty(n_cells, dtype=np.int32)
        xi = pos[i, 0]
        yi = pos[i, 1]
        zi = pos[i, 2]
        vxi = vel[i, 0]
        vyi = vel[i, 1]
        vzi = vel[i, 2]
        ax = 0.0
        ay = 0.0
        az = 0.0
        power = 0.0
        sp = 0
        stack[sp] = 0
        sp += 1
        while sp > 0:
            sp -= 1
            c = stack[sp]
            if cell_is_leaf[c]:
                start = cell_leaf_start[c]
                end = start + cell_leaf_count[c]
                for k in range(start, end):
                    pidx = sorted_idx[k]
                    if pidx == i:
                        continue
                    dx = sorted_pos[k, 0] - xi
                    dy = sorted_pos[k, 1] - yi
                    dz = sorted_pos[k, 2] - zi
                    # DRAW — exact pairwise, softened inverse-square
                    r2d = dx * dx + dy * dy + dz * dz + eps2
                    inv_r3 = 1.0 / (r2d * math.sqrt(r2d))
                    f = G_val * inv_r3
                    ax += f * dx
                    ay += f * dy
                    az += f * dz
                    # RESISTANCE (the modifier M) within the cutoff
                    r2 = dx * dx + dy * dy + dz * dz
                    if r2 > rc2 or r2 < 1e-18:
                        continue
                    r = math.sqrt(r2)
                    if r < rw:
                        inv_r = 1.0 / r
                        ux = dx * inv_r
                        uy = dy * inv_r
                        uz = dz * inv_r
                        r_eff = math.sqrt(r2 + s_wall * s_wall)
                        fw = kw * ((rw / r_eff) ** p) / r_eff
                        ax += fw * (-ux)
                        ay += fw * (-uy)
                        az += fw * (-uz)
                        dvx = vel[pidx, 0] - vxi
                        dvy = vel[pidx, 1] - vyi
                        dvz = vel[pidx, 2] - vzi
                        v_rad = dvx * ux + dvy * uy + dvz * uz
                        damp = gamma_w * v_rad
                        ax += damp * ux
                        ay += damp * uy
                        az += damp * uz
                        # each unordered pair visited twice; accumulate half each
                        power += 0.5 * gamma_w * v_rad * v_rad
                    elif r <= rb:
                        fb = kb * (r - rb) / (rb * r)
                        ax += fb * dx
                        ay += fb * dy
                        az += fb * dz
                continue

            # internal node
            dx = cell_com[c, 0] - xi
            dy = cell_com[c, 1] - yi
            dz = cell_com[c, 2] - zi
            d2 = dx * dx + dy * dy + dz * dz
            d = math.sqrt(d2)
            sx = cell_max[c, 0] - cell_min[c, 0]
            sy = cell_max[c, 1] - cell_min[c, 1]
            sz = cell_max[c, 2] - cell_min[c, 2]
            s = max(sx, max(sy, sz))

            # min squared distance from the point to the node's bounding box
            md2 = 0.0
            if xi < cell_min[c, 0]:
                q = cell_min[c, 0] - xi
                md2 += q * q
            elif xi > cell_max[c, 0]:
                q = xi - cell_max[c, 0]
                md2 += q * q
            if yi < cell_min[c, 1]:
                q = cell_min[c, 1] - yi
                md2 += q * q
            elif yi > cell_max[c, 1]:
                q = yi - cell_max[c, 1]
                md2 += q * q
            if zi < cell_min[c, 2]:
                q = cell_min[c, 2] - zi
                md2 += q * q
            elif zi > cell_max[c, 2]:
                q = zi - cell_max[c, 2]
                md2 += q * q

            if s < theta * d and md2 > rc2:
                # far and entirely outside the resistance range:
                # aggregate draw, M -> 1 (pure draw)
                r2 = d2 + eps2
                inv_r3 = 1.0 / (r2 * math.sqrt(r2))
                f = G_val * cell_mass[c] * inv_r3
                ax += f * dx
                ay += f * dy
                az += f * dz
            else:
                # near for draw, or possibly holding resistance partners:
                # descend
                for k in range(8):
                    child = cell_child[c, k]
                    if child >= 0:
                        stack[sp] = child
                        sp += 1
        out[i, 0] = ax
        out[i, 1] = ay
        out[i, 2] = az
        power_out[i] = power


# ═══════════════════════════════════════════════════════════════════
#  CUDA merged walk
# ═══════════════════════════════════════════════════════════════════
@cuda.jit(cache=True)
def _mod_walk_cuda(pos, vel, sorted_pos, sorted_idx, out,
                   cell_min, cell_max, cell_com, cell_mass, cell_child,
                   cell_is_leaf, cell_leaf_start, cell_leaf_count,
                   theta, G_val, eps2, rw, rb, rc, p, kw, kb, gamma_w,
                   s_wall, power_dev, n):
    """ONE modified Barnes-Hut walk on the GPU (DRAW + RESISTANCE)."""
    i = cuda.grid(1)
    if i >= n:
        return

    stack = cuda.local.array(_STACK_SIZE, dtype=np.int32)
    xi = pos[i, 0]
    yi = pos[i, 1]
    zi = pos[i, 2]
    vxi = vel[i, 0]
    vyi = vel[i, 1]
    vzi = vel[i, 2]
    ax = 0.0
    ay = 0.0
    az = 0.0
    power = 0.0
    rc2 = rc * rc
    sp = 0
    stack[sp] = 0
    sp += 1

    while sp > 0:
        sp -= 1
        c = stack[sp]
        if cell_is_leaf[c]:
            start = cell_leaf_start[c]
            end = start + cell_leaf_count[c]
            for k in range(start, end):
                pidx = sorted_idx[k]
                if pidx == i:
                    continue
                dx = sorted_pos[k, 0] - xi
                dy = sorted_pos[k, 1] - yi
                dz = sorted_pos[k, 2] - zi
                r2d = dx * dx + dy * dy + dz * dz + eps2
                inv_r3 = 1.0 / (r2d * math.sqrt(r2d))
                f = G_val * inv_r3
                ax += f * dx
                ay += f * dy
                az += f * dz
                r2 = dx * dx + dy * dy + dz * dz
                if r2 > rc2 or r2 < 1e-18:
                    continue
                r = math.sqrt(r2)
                if r < rw:
                    inv_r = 1.0 / r
                    ux = dx * inv_r
                    uy = dy * inv_r
                    uz = dz * inv_r
                    r_eff = math.sqrt(r2 + s_wall * s_wall)
                    fw = kw * ((rw / r_eff) ** p) / r_eff
                    ax += fw * (-ux)
                    ay += fw * (-uy)
                    az += fw * (-uz)
                    dvx = vel[pidx, 0] - vxi
                    dvy = vel[pidx, 1] - vyi
                    dvz = vel[pidx, 2] - vzi
                    v_rad = dvx * ux + dvy * uy + dvz * uz
                    damp = gamma_w * v_rad
                    ax += damp * ux
                    ay += damp * uy
                    az += damp * uz
                    power += 0.5 * gamma_w * v_rad * v_rad
                elif r <= rb:
                    fb = kb * (r - rb) / (rb * r)
                    ax += fb * dx
                    ay += fb * dy
                    az += fb * dz
            continue

        dx = cell_com[c, 0] - xi
        dy = cell_com[c, 1] - yi
        dz = cell_com[c, 2] - zi
        d2 = dx * dx + dy * dy + dz * dz
        d = math.sqrt(d2)
        sx = cell_max[c, 0] - cell_min[c, 0]
        sy = cell_max[c, 1] - cell_min[c, 1]
        sz = cell_max[c, 2] - cell_min[c, 2]
        s = sx
        if sy > s:
            s = sy
        if sz > s:
            s = sz

        md2 = 0.0
        if xi < cell_min[c, 0]:
            q = cell_min[c, 0] - xi
            md2 += q * q
        elif xi > cell_max[c, 0]:
            q = xi - cell_max[c, 0]
            md2 += q * q
        if yi < cell_min[c, 1]:
            q = cell_min[c, 1] - yi
            md2 += q * q
        elif yi > cell_max[c, 1]:
            q = yi - cell_max[c, 1]
            md2 += q * q
        if zi < cell_min[c, 2]:
            q = cell_min[c, 2] - zi
            md2 += q * q
        elif zi > cell_max[c, 2]:
            q = zi - cell_max[c, 2]
            md2 += q * q

        if s < theta * d and md2 > rc2:
            r2 = d2 + eps2
            inv_r3 = 1.0 / (r2 * math.sqrt(r2))
            f = G_val * cell_mass[c] * inv_r3
            ax += f * dx
            ay += f * dy
            az += f * dz
        else:
            for k in range(8):
                child = cell_child[c, k]
                if child >= 0:
                    if sp >= _STACK_SIZE:
                        out[i, 0] = float("nan")
                        out[i, 1] = float("nan")
                        out[i, 2] = float("nan")
                        return
                    stack[sp] = child
                    sp += 1

    out[i, 0] = ax
    out[i, 1] = ay
    out[i, 2] = az
    if power != 0.0:
        cuda.atomic.add(power_dev, 0, power)


# ═══════════════════════════════════════════════════════════════════
#  Public merged interface
# ═══════════════════════════════════════════════════════════════════
def compute_forces_mod(positions: np.ndarray,
                       velocities: np.ndarray,
                       theta: float | None = None,
                       leaf_size: int = 16,
                       tree: dict | None = None,
                       out: np.ndarray | None = None,
                       use_cuda: bool | None = None,
                       ) -> tuple[np.ndarray, float]:
    """
    Compute DRAW + RESISTANCE in ONE modified Barnes-Hut tree walk.

    Interface merges ``kernel.compute_draw`` + ``kernel.compute_resistance``
    (+ the radiated-power bookkeeping) into a single call over a single
    octree.  The force laws are identical to the two-pass kernel; only the
    traversal changed.

    Parameters
    ----------
    positions : (N, 3) float array
    velocities : (N, 3) float array
    theta : opening angle (default: ``bh_draw.DEFAULT_THETA``)
    leaf_size : particles per leaf (default 16)
    tree : optional prebuilt octree from ``build_octree``
    out : optional (N, 3) float array to fill
    use_cuda : if True, require GPU; if False, force CPU; if None, auto

    Returns
    -------
    acc : (N, 3) float array of DRAW + RESISTANCE accelerations
    power : float total radiated wall power this tick
    """
    positions = np.asarray(positions, dtype=np.float32)
    velocities = np.asarray(velocities, dtype=np.float32)
    n = positions.shape[0]
    if theta is None:
        theta = DEFAULT_THETA
    if out is None:
        out = np.empty((n, 3), dtype=np.float32)
    else:
        out = np.asarray(out, dtype=np.float32)
    if n == 0:
        return out, 0.0

    if tree is None:
        tree = build_octree(positions, leaf_size=leaf_size)

    gpu = (use_cuda is True) or (use_cuda is None and _cuda_available)
    if gpu:
        d_pos = cuda.to_device(positions)
        d_vel = cuda.to_device(velocities)
        d_sorted_pos = cuda.to_device(tree["sorted_pos"])
        d_sorted_idx = cuda.to_device(tree["sorted_idx"])
        d_out = cuda.to_device(out)
        d_cell_min = cuda.to_device(tree["cell_min"])
        d_cell_max = cuda.to_device(tree["cell_max"])
        d_cell_com = cuda.to_device(tree["cell_com"])
        d_cell_mass = cuda.to_device(tree["cell_mass"])
        d_cell_child = cuda.to_device(tree["cell_child"])
        d_cell_is_leaf = cuda.to_device(tree["cell_is_leaf"])
        d_cell_leaf_start = cuda.to_device(tree["cell_leaf_start"])
        d_cell_leaf_count = cuda.to_device(tree["cell_leaf_count"])
        d_power = cuda.device_array(1, dtype=np.float32)
        threads = 256
        blocks = (n + threads - 1) // threads
        _mod_walk_cuda[blocks, threads](
            d_pos, d_vel, d_sorted_pos, d_sorted_idx, d_out,
            d_cell_min, d_cell_max, d_cell_com, d_cell_mass, d_cell_child,
            d_cell_is_leaf, d_cell_leaf_start, d_cell_leaf_count,
            float(theta), float(G), EPS2, float(R_WALL), float(R_BOND),
            float(R_C), float(P_WALL), float(K_WALL), float(K_BOND),
            float(GAMMA_W), float(S_WALL), d_power, n,
        )
        cuda.synchronize()
        d_out.copy_to_host(out)
        power = float(d_power.copy_to_host()[0])
    else:
        power_per = np.empty(n, dtype=np.float32)
        _mod_walk_cpu(
            positions, velocities,
            tree["sorted_pos"], tree["sorted_idx"],
            tree["cell_min"], tree["cell_max"],
            tree["cell_com"], tree["cell_mass"],
            tree["cell_child"], tree["cell_is_leaf"],
            tree["cell_leaf_start"], tree["cell_leaf_count"],
            float(theta), float(G), EPS2, float(R_WALL), float(R_BOND),
            float(R_C), float(P_WALL), float(K_WALL), float(K_BOND),
            float(GAMMA_W), float(S_WALL), out, power_per,
        )
        power = float(np.sum(power_per))

    if not np.all(np.isfinite(out)):
        raise RuntimeError("MODIFIER walk produced non-finite output; "
                           "increase _STACK_SIZE or reduce theta.")
    return out, power
