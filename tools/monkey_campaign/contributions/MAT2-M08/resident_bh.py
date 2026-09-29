"""MAT2-M08 Barnes-Hut far-field pass — the DSL's declared gravity kernel.

Reconciles the kernel DSL's declared gravity kernel (quantity="mass",
aggregate="weighted_sum" monopole, kernel_fn="inverse_squared",
sign="attractive", coupling="G"; ChimeraEngine/engine/kernel_dsl.py) as a
RESIDENT CUDA pass: a Morton-sorted binary hierarchy of STATIC SHAPE whose
aggregates (AABB, mass, center of mass) are refit ON DEVICE each substep
from the resident positions — no CPU tree, no per-tick upload (the spiace
prototype's per-frame CPU tree/upload/readback defect replaced).

Law (eligible, declared): Newtonian point-mass gravity,
U = -G_N m_i m_j / r,  a_i = G_N sum_j m_j (x_j - x_i)/|x_j - x_i|^3,
G_N = 6.674e-11 SI. Declared mass elements: the lumped membrane vertices
(their lumped masses) and the plate corners at plate_mass/4. Applicability:
a far-field self-gravity coupling of the coupled world's matter set; it is
DISABLED on the X1 agreement fixture (the sealed oracle has no self-gravity)
and its work/impulse contribution is a measured record on the BH fixture.

Error criterion (frozen): aggregate a node iff s <= theta*d (s = node AABB
diagonal, d = distance body -> node COM), theta = 0.5; acceptance window
max relative acceleration error <= 5e-3 against the on-device exact direct
sum at every declared measurement tick (`bh_error_window_exceeded` refusal).

Near-field reference test (frozen form, Amendment A1): rerunning the SAME
traversal with theta = 0 forces every pair down the leaf-direct path; that
run must reproduce the direct sum pair-exact (<= 1e-12 relative) for every
body — proving the near path is direct, not aggregated. The law itself is
covered by the closed-form two-body identity a = G_N m / r^2 (1e-12).

Determinism: fixed sort keys (code, index), static tree shape, fixed
traversal child order (right pushed first so left resolves first), no float
atomics. Host involvement per substep is the bounded command block only.
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np
from numba import cuda

HERE = pathlib.Path(__file__).resolve().parent
for _p in (str(HERE),):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from kernel_mirror import (N_VERT, P_WSG, P_SGIMPX, P_SGIMPY, P_SGIMPZ,   # noqa
                           P_SGIPX, P_SGIPY, P_SGIPZ, require)

G_N = 6.674e-11
BH_THETA = 0.5
BH_ERROR_WINDOW = 5e-3
BH_NEAR_WINDOW = 1e-12
PAD_CODE = 9223372036854775807              # int64 max (padding key)


def _morton21(x):
    x &= 0x1FFFFF
    x = (x | (x << 32)) & 0x1F00000000FFFF
    x = (x | (x << 16)) & 0x1F0000FF0000FF
    x = (x | (x << 8)) & 0x100F00F00F00F00F
    x = (x | (x << 4)) & 0x10C30C30C30C30C3
    x = (x | (x << 2)) & 0x1249249249249249
    return int(x)


def _morton_code(qx, qy, qz):
    return (_morton21(qz) << 2) | (_morton21(qy) << 1) | _morton21(qx)


def bh_two_body_identity():
    """Closed-form law reference: a = G_N m_source / r^2 on the attracted
    body (the acceleration on body 0 comes from body 1's mass)."""
    m_source = 2.5
    r = 0.37
    a_exact = G_N * m_source / (r * r)
    xs = np.array([[0.0, 0.0, 0.0], [r, 0.0, 0.0]])
    ms = np.array([1.0, m_source])
    a = bh_direct_numpy(xs, ms)
    return abs(a[0, 0] - a_exact) / a_exact


def bh_direct_numpy(xs, ms, g=G_N):
    """Exact direct-sum reference (host, vectorized)."""
    d = xs[None, :, :] - xs[:, None, :]
    r2 = (d * d).sum(axis=2)
    np.fill_diagonal(r2, 1.0)
    inv = 1.0 / (r2 * np.sqrt(r2))
    return (g * (d * inv[:, :, None] * ms[None, :, None])).sum(axis=1)


def bh_bodies_host(components):
    """Positions and masses of the declared mass elements (host view)."""
    xs = []
    ms = []
    for c in components:
        xs.append(c.x)
        ms.append(c.masses)
        xs.append(c.plate.x)
        ms.append(np.full(4, c.plate.mass_kg / 4.0))
    return (np.ascontiguousarray(np.concatenate(xs)),
            np.ascontiguousarray(np.concatenate(ms)))


def _declared_bounds(components):
    xs, _ = bh_bodies_host(components)
    lo = xs.min(axis=0) - 1.0
    hi = xs.max(axis=0) + 1.0
    scale = float((hi - lo).max())
    return lo, scale


# ---- device kernels ----------------------------------------------------------

@cuda.jit(device=True, inline=True)
def bh_body_pos_mass(X, PX, MASSES, PMASS, body, pos, out_m):
    nb = body // (N_VERT + 4)
    within = body % (N_VERT + 4)
    if within < N_VERT:
        pos[0] = X[nb * N_VERT + within, 0]
        pos[1] = X[nb * N_VERT + within, 1]
        pos[2] = X[nb * N_VERT + within, 2]
        out_m[0] = MASSES[nb * N_VERT + within]
    else:
        pos[0] = PX[nb, within - N_VERT, 0]
        pos[1] = PX[nb, within - N_VERT, 1]
        pos[2] = PX[nb, within - N_VERT, 2]
        out_m[0] = PMASS[nb] / 4.0


@cuda.jit(device=True, inline=True)
def bh_part1by2(v):
    v = v & 0x1FFFFF
    v = (v | (v << 32)) & 0x1F00000000FFFF
    v = (v | (v << 16)) & 0x1F0000FF0000FF
    v = (v | (v << 8)) & 0x100F00F00F00F00F
    v = (v | (v << 4)) & 0x10C30C30C30C30C3
    v = (v | (v << 2)) & 0x1249249249249249
    return v


@cuda.jit
def k_bh_codes(X, PX, MASSES, PMASS, BLO, BSCALE, CODES, IDX, NPOW, N_REAL):
    i = cuda.grid(1)
    if i >= NPOW[0]:
        return
    if i >= N_REAL[0]:
        CODES[i] = PAD_CODE
        IDX[i] = -1
        return
    pos = cuda.local.array(1, dtype=np.float64)
    out_m = cuda.local.array(1, dtype=np.float64)
    bh_body_pos_mass(X, PX, MASSES, PMASS, i, pos, out_m)
    qx = int((pos[0] - BLO[0]) / BSCALE[0] * 2097151.0)
    qy = int((pos[1] - BLO[1]) / BSCALE[1] * 2097151.0)
    qz = int((pos[2] - BLO[2]) / BSCALE[2] * 2097151.0)
    if qx < 0:
        qx = 0
    if qx > 2097151:
        qx = 2097151
    if qy < 0:
        qy = 0
    if qy > 2097151:
        qy = 2097151
    if qz < 0:
        qz = 0
    if qz > 2097151:
        qz = 2097151
    CODES[i] = bh_part1by2(qz) * 4 + bh_part1by2(qy) * 2 + bh_part1by2(qx)
    IDX[i] = i


@cuda.jit
def k_bh_bitonic(CODES, IDX):
    """In-place bitonic sort of (CODES, IDX); single-thread driver over the
    pow2-sized arrays (deterministic)."""
    if cuda.grid(1) != 0:
        return
    npow = CODES.shape[0]
    width = 2
    while width <= npow:
        half = width >> 1
        start = 0
        while start < npow:
            for a in range(half):
                p = start + a
                q = p + half
                if (p & width) == 0:
                    if CODES[p] > CODES[q]:
                        cp = CODES[p]
                        CODES[p] = CODES[q]
                        CODES[q] = cp
                        ip = IDX[p]
                        IDX[p] = IDX[q]
                        IDX[q] = ip
                else:
                    if CODES[p] < CODES[q]:
                        cp = CODES[p]
                        CODES[p] = CODES[q]
                        CODES[q] = cp
                        ip = IDX[p]
                        IDX[p] = IDX[q]
                        IDX[q] = ip
            start += width
        width <<= 1


@cuda.jit
def k_bh_agg_ranges(X, PX, MASSES, PMASS, IDX, FIRST, LAST, NPOW,
                    NMIN, NMAX, NM, NCOM):
    """Refit every internal node over its static slot range (one thread per
    node; sequential scan in slot order)."""
    node = cuda.grid(1)
    nn = NPOW[0] - 1
    if node >= nn:
        return
    lo = FIRST[node]
    hi = LAST[node]
    msum = 0.0
    cx = 0.0
    cy = 0.0
    cz = 0.0
    minx = 1.0e300
    miny = 1.0e300
    minz = 1.0e300
    maxx = -1.0e300
    maxy = -1.0e300
    maxz = -1.0e300
    pos = cuda.local.array(1, dtype=np.float64)
    out_m = cuda.local.array(1, dtype=np.float64)
    for k in range(lo, hi + 1):
        body = IDX[k]
        if body < 0:
            continue
        bh_body_pos_mass(X, PX, MASSES, PMASS, body, pos, out_m)
        px = pos[0]
        py = pos[1]
        pz = pos[2]
        mass = out_m[0]
        msum += mass
        cx += mass * px
        cy += mass * py
        cz += mass * pz
        if px < minx:
            minx = px
        if px > maxx:
            maxx = px
        if py < miny:
            miny = py
        if py > maxy:
            maxy = py
        if pz < minz:
            minz = pz
        if pz > maxz:
            maxz = pz
    if msum > 0.0:
        NM[node] = msum
        NCOM[node, 0] = cx / msum
        NCOM[node, 1] = cy / msum
        NCOM[node, 2] = cz / msum
    else:
        NM[node] = 0.0
        NCOM[node, 0] = 0.0
        NCOM[node, 1] = 0.0
        NCOM[node, 2] = 0.0
    NMIN[node, 0] = minx
    NMIN[node, 1] = miny
    NMIN[node, 2] = minz
    NMAX[node, 0] = maxx
    NMAX[node, 1] = maxy
    NMAX[node, 2] = maxz


@cuda.jit
def k_bh_force(X, PX, MASSES, PMASS, IDX, NPOW, N_REAL, NMIN, NMAX, NM,
               NCOM, THETA, SGA):
    """Per-body Barnes-Hut traversal with the declared theta gate; near
    field resolves on the leaf-direct path."""
    body = cuda.grid(1)
    if body >= N_REAL[0]:
        return
    nn = NPOW[0] - 1
    pos = cuda.local.array(1, dtype=np.float64)
    out_m = cuda.local.array(1, dtype=np.float64)
    bh_body_pos_mass(X, PX, MASSES, PMASS, body, pos, out_m)
    xi = pos[0]
    yi = pos[1]
    zi = pos[2]
    ax = 0.0
    ay = 0.0
    az = 0.0
    stack = cuda.local.array(64, dtype=np.int64)
    sp = 0
    stack[sp] = 0
    sp += 1
    while sp > 0:
        sp -= 1
        node = stack[sp]
        if node >= nn:
            j = IDX[node - nn]
            if j >= 0 and j != body:
                bh_body_pos_mass(X, PX, MASSES, PMASS, j, pos, out_m)
                mj = out_m[0]
                if mj > 0.0:
                    dx = pos[0] - xi
                    dy = pos[1] - yi
                    dz = pos[2] - zi
                    r2 = dx * dx + dy * dy + dz * dz
                    if r2 > 0.0:
                        inv = 1.0 / (r2 * np.sqrt(r2))
                        f = G_N * mj * inv
                        ax += f * dx
                        ay += f * dy
                        az += f * dz
        else:
            dx = NCOM[node, 0] - xi
            dy = NCOM[node, 1] - yi
            dz = NCOM[node, 2] - zi
            d2 = dx * dx + dy * dy + dz * dz
            d = np.sqrt(d2)
            sx = NMAX[node, 0] - NMIN[node, 0]
            sy = NMAX[node, 1] - NMIN[node, 1]
            sz = NMAX[node, 2] - NMIN[node, 2]
            s = np.sqrt(sx * sx + sy * sy + sz * sz)
            if NM[node] > 0.0 and s <= THETA[0] * d:
                if d2 > 0.0:
                    inv = 1.0 / (d2 * d)
                    f = G_N * NM[node] * inv
                    ax += f * dx
                    ay += f * dy
                    az += f * dz
            elif sp < 63:
                stack[sp] = 2 * node + 2
                sp += 1
                stack[sp] = 2 * node + 1
                sp += 1
    SGA[body, 0] = ax
    SGA[body, 1] = ay
    SGA[body, 2] = az


@cuda.jit
def k_bh_apply_dv(X, PX, V, PV, MASSES, PMASS, SGA, H, PASS, SUB):
    """Apply the far-field dv to the resident state; record work (trapezoid)
    and impulses in the pass slots (M08 Amendment A1)."""
    comp = cuda.grid(1)
    if comp >= PV.shape[0]:
        return
    base = comp * (N_VERT + 4)
    for vv in range(N_VERT):
        gv = comp * N_VERT + vv
        ax = SGA[base + vv, 0]
        ay = SGA[base + vv, 1]
        az = SGA[base + vv, 2]
        vpx = V[gv, 0]; vpy = V[gv, 1]; vpz = V[gv, 2]
        V[gv, 0] = V[gv, 0] + ax * H[0]
        V[gv, 1] = V[gv, 1] + ay * H[0]
        V[gv, 2] = V[gv, 2] + az * H[0]
        m = MASSES[gv]
        w = m * (ax * 0.5 * (vpx + V[gv, 0])
                 + ay * 0.5 * (vpy + V[gv, 1])
                 + az * 0.5 * (vpz + V[gv, 2])) * H[0]
        PASS[comp, SUB, P_WSG] = PASS[comp, SUB, P_WSG] + w
        PASS[comp, SUB, P_SGIMPX] = PASS[comp, SUB, P_SGIMPX] + m * ax * H[0]
        PASS[comp, SUB, P_SGIMPY] = PASS[comp, SUB, P_SGIMPY] + m * ay * H[0]
        PASS[comp, SUB, P_SGIMPZ] = PASS[comp, SUB, P_SGIMPZ] + m * az * H[0]
    a0 = SGA[base + N_VERT, 0] + SGA[base + N_VERT + 1, 0] \
        + SGA[base + N_VERT + 2, 0] + SGA[base + N_VERT + 3, 0]
    a1 = SGA[base + N_VERT, 1] + SGA[base + N_VERT + 1, 1] \
        + SGA[base + N_VERT + 2, 1] + SGA[base + N_VERT + 3, 1]
    a2 = SGA[base + N_VERT, 2] + SGA[base + N_VERT + 1, 2] \
        + SGA[base + N_VERT + 2, 2] + SGA[base + N_VERT + 3, 2]
    dvx = a0 * H[0] / 4.0
    dvy = a1 * H[0] / 4.0
    dvz = a2 * H[0] / 4.0
    m = PMASS[comp]
    vpx = PV[comp, 0]; vpy = PV[comp, 1]; vpz = PV[comp, 2]
    PV[comp, 0] = PV[comp, 0] + dvx
    PV[comp, 1] = PV[comp, 1] + dvy
    PV[comp, 2] = PV[comp, 2] + dvz
    PASS[comp, SUB, P_WSG] = PASS[comp, SUB, P_WSG] \
        + m * (a0 * 0.5 * (vpx + PV[comp, 0]) / 4.0
               + a1 * 0.5 * (vpy + PV[comp, 1]) / 4.0
               + a2 * 0.5 * (vpz + PV[comp, 2]) / 4.0) * H[0]
    PASS[comp, SUB, P_SGIPX] = m * dvx
    PASS[comp, SUB, P_SGIPY] = m * dvy
    PASS[comp, SUB, P_SGIPZ] = m * dvz


@cuda.jit
def k_bh_check(X, PX, MASSES, PMASS, SGA, BH_ERRS, MODE):
    """Relative error of the current SGA buffer against the exact direct
    sum (MODE only labels the receipt: 0.0 production theta, 1.0 theta=0
    near-field reference)."""
    body = cuda.grid(1)
    if body >= SGA.shape[0]:
        return
    pos = cuda.local.array(1, dtype=np.float64)
    out_m = cuda.local.array(1, dtype=np.float64)
    bh_body_pos_mass(X, PX, MASSES, PMASS, body, pos, out_m)
    xi = pos[0]
    yi = pos[1]
    zi = pos[2]
    ax = 0.0
    ay = 0.0
    az = 0.0
    for j in range(SGA.shape[0]):
        if j == body:
            continue
        bh_body_pos_mass(X, PX, MASSES, PMASS, j, pos, out_m)
        mj = out_m[0]
        if mj <= 0.0:
            continue
        dx = pos[0] - xi
        dy = pos[1] - yi
        dz = pos[2] - zi
        r2 = dx * dx + dy * dy + dz * dz
        if r2 > 0.0:
            inv = 1.0 / (r2 * np.sqrt(r2))
            f = G_N * mj * inv
            ax += f * dx
            ay += f * dy
            az += f * dz
    ref = np.sqrt(ax * ax + ay * ay + az * az)
    dx = SGA[body, 0] - ax
    dy = SGA[body, 1] - ay
    dz = SGA[body, 2] - az
    err = np.sqrt(dx * dx + dy * dy + dz * dz)
    BH_ERRS[body] = err / max(ref, 1.0e-300)


@cuda.jit
def k_bh_reduce(BH_ERRS, OUT_MAX, OUT_RMS, OUT_N, N_REAL):
    """Deterministic max/rms reduction (single thread; sequential sums)."""
    if cuda.grid(1) != 0:
        return
    n = N_REAL[0]
    mx = 0.0
    for i in range(n):
        if BH_ERRS[i] > mx:
            mx = BH_ERRS[i]
    s = 0.0
    for i in range(n):
        s += BH_ERRS[i] * BH_ERRS[i]
    OUT_MAX[0] = mx
    OUT_RMS[0] = np.sqrt(s / n)
    OUT_N[0] = float(n)


class ResidentBH:
    """Resident Barnes-Hut state; apply() runs once per substep on the
    world's resident buffers. Tree shape is static; aggregates refit in
    place each substep from resident positions."""

    def __init__(self, world, components):
        self.world = world
        self.bodies_per_comp = N_VERT + 4
        self.n_real = world.n_comp * self.bodies_per_comp
        npow = 2
        while npow < self.n_real:
            npow *= 2
        self.npow = npow
        self.d_codes = cuda.to_device(np.full(npow, PAD_CODE, dtype=np.int64))
        self.d_idx = cuda.to_device(np.full(npow, -1, dtype=np.int64))
        nn = npow - 1
        first = np.zeros(nn, dtype=np.int64)
        last = np.zeros(nn, dtype=np.int64)
        for node in range(nn):
            level = (node + 1).bit_length() - 1   # root at level 0
            span = npow >> level
            idx_in_level = node - ((1 << level) - 1)
            start = idx_in_level * span
            first[node] = start
            last[node] = start + span - 1
        self.d_first = cuda.to_device(first)
        self.d_last = cuda.to_device(last)
        self.d_nmin = cuda.device_array((nn, 3), dtype=np.float64)
        self.d_nmax = cuda.device_array((nn, 3), dtype=np.float64)
        self.d_nm = cuda.device_array(nn, dtype=np.float64)
        self.d_ncom = cuda.device_array((nn, 3), dtype=np.float64)
        blo, scale = _declared_bounds(components)
        self.d_blo = cuda.to_device(np.ascontiguousarray(blo))
        self.d_scale = cuda.to_device(np.array([scale]))
        self.d_nreal = cuda.to_device(np.array([self.n_real],
                                               dtype=np.int64))
        self.d_npow = cuda.to_device(np.array([npow], dtype=np.int64))
        self.d_theta = cuda.to_device(np.array([BH_THETA]))
        self.d_sga = cuda.device_array((self.n_real, 3), dtype=np.float64)
        self.d_bh_errs = cuda.device_array(self.n_real, dtype=np.float64)
        self.d_out_max = cuda.to_device(np.zeros(1))
        self.d_out_rms = cuda.to_device(np.zeros(1))
        self.d_out_n = cuda.to_device(np.zeros(1))
        self.d_mode = cuda.to_device(np.zeros(1))
        self.last_max = 0.0
        self.last_rms = 0.0

    def _refit(self):
        w = self.world
        k_bh_codes[((self.npow + 127) // 128, 1), 128](
            w.d_x, w.d_px, w.d_masses, w.d_pmass, self.d_blo, self.d_scale,
            self.d_codes, self.d_idx, self.d_npow, self.d_nreal)
        k_bh_bitonic[1, 1](self.d_codes, self.d_idx)
        k_bh_agg_ranges[self.npow - 1, 1](
            w.d_x, w.d_px, w.d_masses, w.d_pmass, self.d_idx, self.d_first,
            self.d_last, self.d_npow, self.d_nmin, self.d_nmax, self.d_nm,
            self.d_ncom)

    def apply(self, sub):
        w = self.world
        self._refit()
        k_bh_force[self.n_real, 1](w.d_x, w.d_px, w.d_masses, w.d_pmass,
                                   self.d_idx, self.d_npow, self.d_nreal,
                                   self.d_nmin, self.d_nmax, self.d_nm,
                                   self.d_ncom, self.d_theta, self.d_sga)
        k_bh_apply_dv[w.n_comp, 1](w.d_x, w.d_px, w.d_v, w.d_pv, w.d_masses,
                                   w.d_pmass, self.d_sga, w.d_h, w.d_pass,
                                   sub)

    def measure(self, theta0=False):
        """Declared measurement: relative error of the traversal against the
        on-device direct sum; theta0=True is the near-field reference form
        (every pair forced down the leaf-direct path)."""
        w = self.world
        self.d_theta.copy_to_device(np.array([0.0 if theta0 else BH_THETA]))
        k_bh_force[self.n_real, 1](w.d_x, w.d_px, w.d_masses, w.d_pmass,
                                   self.d_idx, self.d_npow, self.d_nreal,
                                   self.d_nmin, self.d_nmax, self.d_nm,
                                   self.d_ncom, self.d_theta, self.d_sga)
        self.d_mode.copy_to_device(np.array([1.0 if theta0 else 0.0]))
        k_bh_check[self.n_real, 1](w.d_x, w.d_px, w.d_masses, w.d_pmass,
                                   self.d_sga, self.d_bh_errs, self.d_mode)
        k_bh_reduce[1, 1](self.d_bh_errs, self.d_out_max, self.d_out_rms,
                          self.d_out_n, self.d_nreal)
        self.last_max = float(self.d_out_max.copy_to_host()[0])
        self.last_rms = float(self.d_out_rms.copy_to_host()[0])
        self.d_theta.copy_to_device(np.array([BH_THETA]))
        return self.last_max, self.last_rms

    def write_measurements(self):
        w = self.world
        w.d_bherr.copy_to_device(np.full(w.n_comp, self.last_max))
        w.d_bhrms.copy_to_device(np.full(w.n_comp, self.last_rms))
        w.d_bhdir.copy_to_device(np.full(w.n_comp, float(self.n_real)))

    def release(self):
        for name in [a for a in dir(self) if a.startswith('d_')]:
            delattr(self, name)
