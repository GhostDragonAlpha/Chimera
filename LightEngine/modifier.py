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
                  out: np.ndarray, power_out: np.ndarray, pot_out: np.ndarray):
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
        pot = 0.0
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
                    # conservative draw PE: U = -G/r (softened); half per visit
                    pot += -0.5 * G_val / math.sqrt(r2d)
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
                        # conservative wall PE: U = K_WALL*R_WALL^P/(P*r_eff^P)
                        pot += 0.5 * kw * ((rw / r_eff) ** p) / p
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
                        # conservative bond PE: U = 0.5*(K_BOND/R_BOND)*(r-R_BOND)^2
                        pot += 0.5 * kb * (r - rb) * (r - rb) / rb
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
                # far-node draw PE: U = -G*M/r (softened); half per visit
                pot += -0.5 * G_val * cell_mass[c] / math.sqrt(r2)
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
        pot_out[i] = pot


# ═══════════════════════════════════════════════════════════════════
#  CUDA merged walk
# ═══════════════════════════════════════════════════════════════════
@cuda.jit(cache=True)
def _mod_walk_cuda(pos, vel, sorted_pos, sorted_idx, out,
                   cell_min, cell_max, cell_com, cell_mass, cell_child,
                   cell_is_leaf, cell_leaf_start, cell_leaf_count,
                   theta, G_val, eps2, rw, rb, rc, p, kw, kb, gamma_w,
                   s_wall, power_dev, pot_dev, n):
    """ONE modified Barnes-Hut walk on the GPU (DRAW + RESISTANCE + PE)."""
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
    pot = 0.0
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
                pot += -0.5 * G_val / math.sqrt(r2d)
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
                    pot += 0.5 * kw * ((rw / r_eff) ** p) / p
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
                    pot += 0.5 * kb * (r - rb) * (r - rb) / rb
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
            pot += -0.5 * G_val * cell_mass[c] / math.sqrt(r2)
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
    if pot != 0.0:
        cuda.atomic.add(pot_dev, 0, pot)


# ═══════════════════════════════════════════════════════════════════
#  Public merged interface
# ═══════════════════════════════════════════════════════════════════
def _dev_get(dev, key, src):
    """Build-once device-buffer reuse (operator directive: no per-call waste).

    Returns a CuPy/numba device array holding ``src``. Allocates only on first
    use or when the shape/dtype changes; otherwise copies in place into the
    cached buffer so steady-state memory is flat instead of climbing each tick.
    Bit-exact: only WHERE the device array comes from changes, never its data.
    """
    if dev is None:
        return cuda.to_device(src)
    buf = dev.get(key)
    if buf is None or tuple(buf.shape) != src.shape or buf.dtype != src.dtype:
        buf = cuda.to_device(src)
        dev[key] = buf
    else:
        buf.copy_to_device(src)
    return buf


def _dev_get_cap(dev, key, src, growth=1.5):
    """Capacity-grow (never per-tick) device-buffer reuse for variable-size tree arrays.

    build_octree's n_cells jitters tick-to-tick (points move). The exact-shape
    ``_dev_get`` reallocated a fresh device buffer on every size change, and the
    numba CUDA caching allocator peak-holds each distinct size class -> device VRAM
    climbs over a long run (the RUN B memory-leak suspect #2). Here we allocate once
    at the observed n_cells and only GROW (1.5x) if a later tick needs more; steady
    state copies the used [0:n_cells] slice into the fixed-capacity buffer, so VRAM
    is flat. The walk only ever traverses cells reachable from root 0 (indices
    < n_cells), so the unused tail is never read -- bit-exact with the fresh path.
    """
    if dev is None:
        return cuda.to_device(src)
    buf = dev.get(key)
    if buf is None or buf.dtype != src.dtype:
        buf = cuda.to_device(src)
        dev[key] = buf
        return buf
    cap = buf.shape[0]
    need = src.shape[0]
    if cap >= need:
        buf[:need].copy_to_device(src)
        return buf
    new_cap = int(max(need * growth, need + 1))
    new_shape = (new_cap,) + src.shape[1:]
    new_buf = cuda.device_array(new_shape, dtype=src.dtype)
    new_buf[:need].copy_to_device(src)
    dev[key] = new_buf
    return new_buf


def compute_forces_mod(positions: np.ndarray,
                       velocities: np.ndarray,
                       theta: float | None = None,
                       leaf_size: int = 16,
                       tree: dict | None = None,
                       out: np.ndarray | None = None,
                       use_cuda: bool | None = None,
                        dev: dict | None = None,
                        ) -> tuple[np.ndarray, float, float]:
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
    dev : optional dict for build-once device-buffer reuse across ticks;
        when given, steady-state VRAM is flat instead of climbing each call.
        Bit-exact with the fresh-allocation path (same data, same math).
    use_cuda : if True, require GPU; if False, force CPU; if None, auto

    Returns
    -------
    acc : (N, 3) float array of DRAW + RESISTANCE accelerations
    power : float total radiated wall power this tick
    pot : float total conservative potential energy (draw + wall + bond)
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
        # Build-once device buffers: reuse across ticks (flat memory), not fresh each call.
        d_pos = _dev_get(dev, "pos", positions)
        d_vel = _dev_get(dev, "vel", velocities)
        d_sorted_pos = _dev_get(dev, "sorted_pos", tree["sorted_pos"])
        d_sorted_idx = _dev_get(dev, "sorted_idx", tree["sorted_idx"])
        d_out = _dev_get(dev, "out", out)
        # Capacity-grow reuse: n_cells varies tick-to-tick; fixed-capacity buffers
        # keep device VRAM flat across a long run (no per-tick realloc peak-hold).
        d_cell_min = _dev_get_cap(dev, "cell_min", tree["cell_min"])
        d_cell_max = _dev_get_cap(dev, "cell_max", tree["cell_max"])
        d_cell_com = _dev_get_cap(dev, "cell_com", tree["cell_com"])
        d_cell_mass = _dev_get_cap(dev, "cell_mass", tree["cell_mass"])
        d_cell_child = _dev_get_cap(dev, "cell_child", tree["cell_child"])
        d_cell_is_leaf = _dev_get_cap(dev, "cell_is_leaf", tree["cell_is_leaf"])
        d_cell_leaf_start = _dev_get_cap(dev, "cell_leaf_start", tree["cell_leaf_start"])
        d_cell_leaf_count = _dev_get_cap(dev, "cell_leaf_count", tree["cell_leaf_count"])
        d_power = _dev_get(dev, "power", np.zeros(1, dtype=np.float32))
        d_pot = _dev_get(dev, "pot", np.zeros(1, dtype=np.float32))
        threads = 256
        blocks = (n + threads - 1) // threads
        _mod_walk_cuda[blocks, threads](
            d_pos, d_vel, d_sorted_pos, d_sorted_idx, d_out,
            d_cell_min, d_cell_max, d_cell_com, d_cell_mass, d_cell_child,
            d_cell_is_leaf, d_cell_leaf_start, d_cell_leaf_count,
            float(theta), float(G), EPS2, float(R_WALL), float(R_BOND),
            float(R_C), float(P_WALL), float(K_WALL), float(K_BOND),
            float(GAMMA_W), float(S_WALL), d_power, d_pot, n,
        )
        cuda.synchronize()
        d_out.copy_to_host(out)
        power = float(d_power.copy_to_host()[0])
        pot = float(d_pot.copy_to_host()[0])
    else:
        power_per = np.empty(n, dtype=np.float32)
        pot_per = np.empty(n, dtype=np.float32)
        _mod_walk_cpu(
            positions, velocities,
            tree["sorted_pos"], tree["sorted_idx"],
            tree["cell_min"], tree["cell_max"],
            tree["cell_com"], tree["cell_mass"],
            tree["cell_child"], tree["cell_is_leaf"],
            tree["cell_leaf_start"], tree["cell_leaf_count"],
            float(theta), float(G), EPS2, float(R_WALL), float(R_BOND),
            float(R_C), float(P_WALL), float(K_WALL), float(K_BOND),
            float(GAMMA_W), float(S_WALL), out, power_per, pot_per,
        )
        power = float(np.sum(power_per))
        pot = float(np.sum(pot_per))

    if not np.all(np.isfinite(out)):
        raise RuntimeError("MODIFIER walk produced non-finite output; "
                           "increase _STACK_SIZE or reduce theta.")
    return out, power, pot
