"""MAT2-M08: the coupled material passes on RESIDENT GPU state (CUDA).

This module is the mechanical CUDA transcription of kernel_mirror.py, whose
logic is validated BITWISE against the sealed M07 oracle on the frozen
agreement fixture (see local_rehearsal.py; mirror commit 01012cb4). The GPU
world keeps ALL physical state in device arrays from construction to
release; the host submits bounded commands (scheduled delta_p, dt, the
host-computed Maxwell factor) and reads the bounded per-component 96-f64
diagnostic block. No per-tick state roundtrip exists (falsifier F1 gates
the recorded bytes). See PREREGISTRATION.md for the frozen statement,
windows, falsifier arms and the Barnes-Hut reconciliation (resident_bh.py).

Numerics law: float64; no float atomics; no RNG; no wall-clock in results;
per-element arithmetic mirrors M07's numpy expression order; recorded sums
use numpy's pairwise/block reduction order; sequential loops run in the
declared index order; the only state-path transcendental (the Maxwell
exponential factor) arrives as a host-computed command. Refusals are named
codes. Upstream authority unchanged: MAT2-M07 + its frozen pins.
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
import sys

import numpy as np
from numba import cuda

HERE = pathlib.Path(__file__).resolve().parent
CONTRIB = HERE.parent
for _p in (str(HERE), str(CONTRIB / 'MAT2-M01'), str(CONTRIB / 'MAT2-M03'),
           str(CONTRIB / 'MAT2-M04'), str(CONTRIB / 'MAT2-M06'),
           str(CONTRIB / 'MAT2-M07')):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import integrated_step as iw  # noqa: E402  (M07 sealed oracle; constants)

# ---- frozen constants (kernel_mirror.py is the single transcription source) --
from kernel_mirror import (  # noqa: E402
    N_TRI, N_VERT, N_EDGES, N_ENTRIES, N_SUB, DT_S, GS_TOL_N_S, GS_CAP,
    XPBD_TOL_M, XPBD_ITERATIONS_CAP, XPBD_COMPLIANCE, THICKNESS_M,
    CONTACT_MARGIN_M, BETA_OVER_DT, SLOP_M, MU_TINY, REST, CCD_TOL_M,
    MEM_MU_S, MEM_MU_K, PLA_MU_S, PLA_MU_K, GRD_MU_S, GRD_MU_K,
    RESID_FRACTION, G_M_S2, DIAG, N_PASS,
    D_KE, D_USCAFF, D_UMAT, D_QMAT, D_WIN, D_F, D_PLX, D_PLVX, D_PLVY,
    D_PLVZ, D_COMX, D_COMY, D_COMZ, D_VOL, D_MAXSPD, D_WPRESS, D_WGRAV,
    D_WMAT, D_QTICK, D_WCKE, D_DFRIC, D_DIMP, D_ESTAB, D_JNTOT, D_TRAP,
    D_PROJ, D_RESID, D_BOUND, D_WEXT, D_ITERS, D_GSRES, D_ACTIVE, D_MINJN,
    D_MINVN, D_CONE, D_STICK, D_ANCX, D_ANCY, D_ANCZ, D_WALLX, D_WALLY,
    D_WALLZ, D_GIMX, D_GIMY, D_GIMZ, D_GIPX, D_GIPY, D_GIPZ, D_CMX, D_CMY,
    D_CMZ, D_CPX, D_CPY, D_CPZ, D_CGX, D_CGY, D_CGZ, D_MATIMP, D_DP, D_TICK,
    D_DIGEST, D_STATUS, D_SUBCLOSE, D_RECIP, D_WSG, D_SGIMPX, D_SGIMPY,
    D_SGIMPZ, D_BHERR, D_BHRMS, D_BHDIR, D_PROJDMX, D_PROJDMY, D_PROJDMZ,
    D_ANCHORRES, D_PROJDPLATE,
    P_WPRESS, P_WGRAVM, P_WGRAVP, P_GIMX, P_GIMY, P_GIMZ, P_GIPX, P_GIPY,
    P_GIPZ, P_WMAT, P_Q, P_MATIMP, P_SUBCLOSE, P_WCKE, P_DFRIC, P_DIMP,
    P_ESTAB, P_JNTOT, P_TRAP, P_ITERS, P_GSRES, P_ACTIVE, P_MINJN, P_MINVN,
    P_CONE, P_STICK, P_ANCX, P_ANCY, P_ANCZ, P_CMX, P_CMY, P_CMZ, P_CPX,
    P_CPY, P_CPZ, P_CGX, P_CGY, P_CGZ, P_RECIPX, P_RECIPY, P_RECIPZ, P_PROJ,
    P_WSG, P_SGIMPX, P_SGIMPY, P_SGIMPZ,
    E_ORDER, E_TICK, E_UNEXPLAINED, E_MOMENTUM, E_CONV, E_SUBLEDGER,
    E_RECIPOCITY, E_SEPARATION, E_STICK, E_ANCHOR, E_STALE, E_BH,
    block_digest, sha_digest, require, body_kind)

SCHEMA = 'chimera.resident_gpu_world.v1'
MAX_ACTIVE = 64
CMD_F64 = 12

E_BYTES = 'state_roundtrip_budget_exceeded'
E_PAIRCAP = 'contact_pair_slot_overflow'
STATUS_OK = 0.0
STATUS_PAIRCAP = 102.0


# ===========================================================================
# device helpers (transcribed from kernel_mirror / numpy semantics)
# ===========================================================================

@cuda.jit(device=True, inline=True)
def norm3_seq(x, y, z):
    t = x * x + y * y
    t = t + z * z
    return math.sqrt(t)


@cuda.jit(device=True, inline=True)
def npsum(a, n):
    """numpy ndarray.sum() pairwise order (n<=128 here: sequential n<8,
    else the 8-accumulator blocked scheme with sequential remainder)."""
    if n < 8:
        res = 0.0
        for i in range(n):
            res += a[i]
        return res
    r0 = a[0]; r1 = a[1]; r2 = a[2]; r3 = a[3]
    r4 = a[4]; r5 = a[5]; r6 = a[6]; r7 = a[7]
    lim = n - (n % 8)
    i = 8
    while i < lim:
        r0 += a[i]; r1 += a[i + 1]; r2 += a[i + 2]; r3 += a[i + 3]
        r4 += a[i + 4]; r5 += a[i + 5]; r6 += a[i + 6]; r7 += a[i + 7]
        i += 8
    res = ((r0 + r1) + (r2 + r3)) + ((r4 + r5) + (r6 + r7))
    while i < n:
        res += a[i]
        i += 1
    return res


@cuda.jit(device=True, inline=True)
def npsum42(MASSES, b):
    """numpy-order sum of MASSES[b+i], i in [0,42)."""
    r0 = MASSES[b + 0]; r1 = MASSES[b + 1]; r2 = MASSES[b + 2]
    r3 = MASSES[b + 3]; r4 = MASSES[b + 4]; r5 = MASSES[b + 5]
    r6 = MASSES[b + 6]; r7 = MASSES[b + 7]
    i = 8
    while i < 40:
        r0 += MASSES[b + i]; r1 += MASSES[b + i + 1]
        r2 += MASSES[b + i + 2]; r3 += MASSES[b + i + 3]
        r4 += MASSES[b + i + 4]; r5 += MASSES[b + i + 5]
        r6 += MASSES[b + i + 6]; r7 += MASSES[b + i + 7]
        i += 8
    res = ((r0 + r1) + (r2 + r3)) + ((r4 + r5) + (r6 + r7))
    res += MASSES[b + 40] + MASSES[b + 41]
    return res


@cuda.jit(device=True, inline=True)
def port_velocity(MV, b, t0, t1, t2):
    """MembranePort.velocity: comp.v[vids].mean(axis=0) = ((v0+v1)+v2)/3."""
    return ((MV[b + t0, 0] + MV[b + t1, 0] + MV[b + t2, 0]) / 3.0,
            (MV[b + t0, 1] + MV[b + t1, 1] + MV[b + t2, 1]) / 3.0,
            (MV[b + t0, 2] + MV[b + t1, 2] + MV[b + t2, 2]) / 3.0)


@cuda.jit(device=True, inline=True)
def add_port_delta(MV, b, t0, t1, t2, dx, dy, dz):
    MV[b + t0, 0] += dx; MV[b + t1, 0] += dx; MV[b + t2, 0] += dx
    MV[b + t0, 1] += dy; MV[b + t1, 1] += dy; MV[b + t2, 1] += dy
    MV[b + t0, 2] += dz; MV[b + t1, 2] += dz; MV[b + t2, 2] += dz


@cuda.jit(device=True, inline=True)
def entry_kind(e):
    return 0 if e < N_TRI else (1 if e < N_TRI + 2 else 2)


@cuda.jit(device=True, inline=True)
def entry_idx(e):
    """Triangle vertex row ids within the entry's vertex array."""
    tt = (e - N_TRI) % 2
    if tt == 0:
        return 0, 1, 2
    return 0, 2, 3


@cuda.jit(device=True, inline=True)
def body_vel_t(MV, PV, TRIS, b, comp, e):
    k = entry_kind(e)
    if k == 0:
        return port_velocity(MV, b, TRIS[comp, e, 0], TRIS[comp, e, 1],
                             TRIS[comp, e, 2])
    if k == 1:
        return PV[comp, 0], PV[comp, 1], PV[comp, 2]
    return 0.0, 0.0, 0.0


@cuda.jit(device=True, inline=True)
def write_body_vel_t(MV, PV, TRIS, b, comp, e, vx, vy, vz):
    k = entry_kind(e)
    if k == 0:
        t0 = TRIS[comp, e, 0]
        t1 = TRIS[comp, e, 1]
        t2 = TRIS[comp, e, 2]
        cx, cy, cz = port_velocity(MV, b, t0, t1, t2)
        add_port_delta(MV, b, t0, t1, t2, vx - cx, vy - cy, vz - cz)
    elif k == 1:
        PV[comp, 0] = vx
        PV[comp, 1] = vy
        PV[comp, 2] = vz


@cuda.jit(device=True, inline=True)
def body_inv_m_t(PORT_MASS, PLATE_MASS, comp, e):
    k = entry_kind(e)
    if k == 0:
        return 1.0 / PORT_MASS[comp, e]
    if k == 1:
        return 1.0 / PLATE_MASS[comp]
    return 0.0


@cuda.jit(device=True, inline=True)
def pair_mu_t(ea, eb):
    ka = entry_kind(ea)
    kb = entry_kind(eb)
    mu_s = 1.0e300
    mu_k = 1.0e300
    for kind in (ka, kb):
        if kind == 0:
            if MEM_MU_S < mu_s:
                mu_s = MEM_MU_S
            if MEM_MU_K < mu_k:
                mu_k = MEM_MU_K
        elif kind == 1:
            if PLA_MU_S < mu_s:
                mu_s = PLA_MU_S
            if PLA_MU_K < mu_k:
                mu_k = PLA_MU_K
        else:
            if GRD_MU_S < mu_s:
                mu_s = GRD_MU_S
            if GRD_MU_K < mu_k:
                mu_k = GRD_MU_K
    return mu_s, mu_k


@cuda.jit(device=True, inline=True)
def scaffold_edges(X, EDGES, REST, b, comp, inv2c):
    """((lengths - rest)**2).sum() / (2*compliance) in numpy order."""
    tmp = cuda.local.array(N_EDGES, dtype=np.float64)
    for e in range(N_EDGES):
        a1 = EDGES[comp, e, 0] + b
        a2 = EDGES[comp, e, 1] + b
        dx = X[a2, 0] - X[a1, 0]
        dy = X[a2, 1] - X[a1, 1]
        dz = X[a2, 2] - X[a1, 2]
        length = norm3_seq(dx, dy, dz)
        tmp[e] = (length - REST[comp, e]) ** 2
    return npsum(tmp, N_EDGES) * inv2c


@cuda.jit(device=True, inline=True)
def point_tri_closest(px, py, pz, a0, a1, a2, b0, b1, b2, c0, c1, c2, out):
    """Ericson point-triangle closest point (M06 transcription)."""
    ab0 = b0 - a0; ab1 = b1 - a1; ab2 = b2 - a2
    ac0 = c0 - a0; ac1 = c1 - a1; ac2 = c2 - a2
    ap0 = px - a0; ap1 = py - a1; ap2 = pz - a2
    d1 = ab0 * ap0 + ab1 * ap1 + ab2 * ap2
    d2 = ac0 * ap0 + ac1 * ap1 + ac2 * ap2
    if d1 <= 0.0 and d2 <= 0.0:
        rx = px - a0; ry = py - a1; rz = pz - a2
        out[0] = a0; out[1] = a1; out[2] = a2
        out[3] = rx * rx + ry * ry + rz * rz
        return
    bp0 = px - b0; bp1 = py - b1; bp2 = pz - b2
    d3 = ab0 * bp0 + ab1 * bp1 + ab2 * bp2
    d4 = ac0 * bp0 + ac1 * bp1 + ac2 * bp2
    if d3 >= 0.0 and d4 <= d3:
        rx = px - b0; ry = py - b1; rz = pz - b2
        out[0] = b0; out[1] = b1; out[2] = b2
        out[3] = rx * rx + ry * ry + rz * rz
        return
    vc = d1 * d4 - d3 * d2
    if vc <= 0.0 and d1 >= 0.0 and d3 <= 0.0:
        t = d1 / (d1 - d3)
        qx = a0 + ab0 * t; qy = a1 + ab1 * t; qz = a2 + ab2 * t
        rx = px - qx; ry = py - qy; rz = pz - qz
        out[0] = qx; out[1] = qy; out[2] = qz
        out[3] = rx * rx + ry * ry + rz * rz
        return
    cp0 = px - c0; cp1 = py - c1; cp2 = pz - c2
    d5 = ab0 * cp0 + ab1 * cp1 + ab2 * cp2
    d6 = ac0 * cp0 + ac1 * cp1 + ac2 * cp2
    if d6 >= 0.0 and d5 <= d6:
        rx = px - c0; ry = py - c1; rz = pz - c2
        out[0] = c0; out[1] = c1; out[2] = c2
        out[3] = rx * rx + ry * ry + rz * rz
        return
    vb = d5 * d2 - d1 * d6
    if vb <= 0.0 and d2 >= 0.0 and d6 <= 0.0:
        t = d2 / (d2 - d6)
        qx = a0 + ac0 * t; qy = a1 + ac1 * t; qz = a2 + ac2 * t
        rx = px - qx; ry = py - qy; rz = pz - qz
        out[0] = qx; out[1] = qy; out[2] = qz
        out[3] = rx * rx + ry * ry + rz * rz
        return
    va = d3 * d6 - d5 * d4
    if va <= 0.0 and (d4 - d3) >= 0.0 and (d5 - d6) >= 0.0:
        t = (d4 - d3) / ((d4 - d3) + (d5 - d6))
        cb0 = c0 - b0; cb1 = c1 - b1; cb2 = c2 - b2
        qx = b0 + cb0 * t; qy = b1 + cb1 * t; qz = b2 + cb2 * t
        rx = px - qx; ry = py - qy; rz = pz - qz
        out[0] = qx; out[1] = qy; out[2] = qz
        out[3] = rx * rx + ry * ry + rz * rz
        return
    denom = 1.0 / (va + vb + vc)
    v = vb * denom
    w = vc * denom
    qx = a0 + ab0 * v + ac0 * w
    qy = a1 + ab1 * v + ac1 * w
    qz = a2 + ab2 * v + ac2 * w
    rx = px - qx; ry = py - qy; rz = pz - qz
    out[0] = qx; out[1] = qy; out[2] = qz
    out[3] = rx * rx + ry * ry + rz * rz


@cuda.jit(device=True, inline=True)
def seg_seg_closest(p1x, p1y, p1z, q1x, q1y, q1z,
                    p2x, p2y, p2z, q2x, q2y, q2z, out):
    """Ericson segment-segment closest points (M06 transcription)."""
    d10 = q1x - p1x; d11 = q1y - p1y; d12 = q1z - p1z
    d20 = q2x - p2x; d21 = q2y - p2y; d22 = q2z - p2z
    r0 = p1x - p2x; r1 = p1y - p2y; r2 = p1z - p2z
    a = d10 * d10 + d11 * d11 + d12 * d12
    e = d20 * d20 + d21 * d21 + d22 * d22
    f = d20 * r0 + d21 * r1 + d22 * r2
    eps = 1e-30
    s = 0.0
    t = 0.0
    if a <= eps and e <= eps:
        out[0] = p1x; out[1] = p1y; out[2] = p1z
        out[3] = p2x; out[4] = p2y; out[5] = p2z
        return
    if a <= eps:
        t = f / e
        if t < 0.0:
            t = 0.0
        elif t > 1.0:
            t = 1.0
    else:
        c = d10 * r0 + d11 * r1 + d12 * r2
        if e <= eps:
            t = 0.0
            s = -c / a
            if s < 0.0:
                s = 0.0
            elif s > 1.0:
                s = 1.0
        else:
            b = d10 * d20 + d11 * d21 + d12 * d22
            denom = a * e - b * b
            if denom > eps:
                s = (b * f - c * e) / denom
                if s < 0.0:
                    s = 0.0
                elif s > 1.0:
                    s = 1.0
            t = (b * s + f) / e
            if t < 0.0:
                t = 0.0
                s = -c / a
                if s < 0.0:
                    s = 0.0
                elif s > 1.0:
                    s = 1.0
            elif t > 1.0:
                t = 1.0
                s = (b - c) / a
                if s < 0.0:
                    s = 0.0
                elif s > 1.0:
                    s = 1.0
    out[0] = p1x + d10 * s; out[1] = p1y + d11 * s; out[2] = p1z + d12 * s
    out[3] = p2x + d20 * t; out[4] = p2y + d21 * t; out[5] = p2z + d22 * t


@cuda.jit(device=True, inline=True)
def tri_verts_of_t(X, PX, GX, TRIS, e, comp, out):
    k = entry_kind(e)
    if k == 0:
        b = comp * N_VERT
        for r in range(3):
            v = TRIS[comp, e, r] + b
            out[r, 0] = X[v, 0]; out[r, 1] = X[v, 1]; out[r, 2] = X[v, 2]
    else:
        i0, i1, i2 = entry_idx(e)
        src = PX if k == 1 else GX
        rows0 = (i0, i1, i2)
        for r in range(3):
            out[r, 0] = src[comp, rows0[r], 0]
            out[r, 1] = src[comp, rows0[r], 1]
            out[r, 2] = src[comp, rows0[r], 2]


@cuda.jit(device=True, inline=True)
def tri_tri_closest_dev(TA, TB, best):
    """M06 tri_tri_closest probe order with strict < best selection;
    best = (dist, px,py,pz, qx,qy,qz)."""
    tmp = cuda.local.array(4, dtype=np.float64)
    tmp2 = cuda.local.array(6, dtype=np.float64)
    bd = 1.0e300
    bpx = 0.0; bpy = 0.0; bpz = 0.0
    bqx = 0.0; bqy = 0.0; bqz = 0.0
    for k in range(3):
        point_tri_closest(TA[k, 0], TA[k, 1], TA[k, 2],
                          TB[0, 0], TB[0, 1], TB[0, 2],
                          TB[1, 0], TB[1, 1], TB[1, 2],
                          TB[2, 0], TB[2, 1], TB[2, 2], tmp)
        d = math.sqrt(tmp[3])
        if d < bd:
            bd = d
            bpx = TA[k, 0]; bpy = TA[k, 1]; bpz = TA[k, 2]
            bqx = tmp[0]; bqy = tmp[1]; bqz = tmp[2]
    for k in range(3):
        point_tri_closest(TB[k, 0], TB[k, 1], TB[k, 2],
                          TA[0, 0], TA[0, 1], TA[0, 2],
                          TA[1, 0], TA[1, 1], TA[1, 2],
                          TA[2, 0], TA[2, 1], TA[2, 2], tmp)
        d = math.sqrt(tmp[3])
        if d < bd:
            bd = d
            bqx = TB[k, 0]; bqy = TB[k, 1]; bqz = TB[k, 2]
            bpx = tmp[0]; bpy = tmp[1]; bpz = tmp[2]
    for e1 in range(3):
        p1x = TA[e1, 0]; p1y = TA[e1, 1]; p1z = TA[e1, 2]
        n1 = e1 + 1
        if n1 == 3:
            n1 = 0
        q1x = TA[n1, 0]; q1y = TA[n1, 1]; q1z = TA[n1, 2]
        for e2 in range(3):
            p2x = TB[e2, 0]; p2y = TB[e2, 1]; p2z = TB[e2, 2]
            n2 = e2 + 1
            if n2 == 3:
                n2 = 0
            q2x = TB[n2, 0]; q2y = TB[n2, 1]; q2z = TB[n2, 2]
            seg_seg_closest(p1x, p1y, p1z, q1x, q1y, q1z,
                            p2x, p2y, p2z, q2x, q2y, q2z, tmp2)
            rx = tmp2[0] - tmp2[3]
            ry = tmp2[1] - tmp2[4]
            rz = tmp2[2] - tmp2[5]
            d = math.sqrt(rx * rx + ry * ry + rz * rz)
            if d < bd:
                bd = d
                bpx = tmp2[0]; bpy = tmp2[1]; bpz = tmp2[2]
                bqx = tmp2[3]; bqy = tmp2[4]; bqz = tmp2[5]
    best[0] = bd
    best[1] = bpx; best[2] = bpy; best[3] = bpz
    best[4] = bqx; best[5] = bqy; best[6] = bqz


# ===========================================================================
# pass kernels (one per declared pass; all state arrives as arguments)
# ===========================================================================

@cuda.jit
def k_reset(MV, PV, SC, VSTART, PVSTART, PASS, X, EDGES, REST, MASSES,
            PLATE_MASS, INV2C, E_PREV, UMAT_PRE, US_PREV):
    comp = cuda.grid(1)
    if comp >= MV.shape[0]:
        return
    b = comp * N_VERT
    for i in range(126):
        fl = i // 3
        c = i % 3
        VSTART[b + fl, c] = MV[b + fl, c]
    for c in range(3):
        PVSTART[comp, c] = PV[comp, c]
    ke = ke_membrane_plate(MV, PV, MASSES, PLATE_MASS, b, comp)
    us = scaffold_edges(X, EDGES, REST, b, comp, INV2C)
    E_PREV[comp] = ke + us + SC[comp, 1]
    UMAT_PRE[comp] = SC[comp, 1]
    US_PREV[comp] = us
    for s in range(4):
        for p in range(N_PASS):
            PASS[comp, s, p] = 0.0


@cuda.jit
def k_pressure_geometry(X, TRIS, DP_A, FTRI, AREAS):
    idx = cuda.grid(1)
    comp = idx // N_TRI
    tri = idx % N_TRI
    if comp >= X.shape[0]:
        return
    b = comp * N_VERT
    i0 = TRIS[comp, tri, 0] + b
    i1 = TRIS[comp, tri, 1] + b
    i2 = TRIS[comp, tri, 2] + b
    e1x = X[i1, 0] - X[i0, 0]; e1y = X[i1, 1] - X[i0, 1]
    e1z = X[i1, 2] - X[i0, 2]
    e2x = X[i2, 0] - X[i0, 0]; e2y = X[i2, 1] - X[i0, 1]
    e2z = X[i2, 2] - X[i0, 2]
    cx = e1y * e2z - e1z * e2y
    cy = e1z * e2x - e1x * e2z
    cz = e1x * e2y - e1y * e2x
    two_area = norm3_seq(cx, cy, cz)
    dp = DP_A[0]
    area = 0.5 * two_area
    AREAS[comp, tri] = area
    FTRI[comp, tri, 0] = dp * area * (cx / two_area)
    FTRI[comp, tri, 1] = dp * area * (cy / two_area)
    FTRI[comp, tri, 2] = dp * area * (cz / two_area)


@cuda.jit
def k_pressure_lump_velocity(MV, MVPRE, LOADS, GLOADS, GLH, MASSES, INV_M,
                             ADJ_OFF, ADJ_VAL, FTRI, GRAV, H):
    comp = cuda.blockIdx.x
    v = cuda.threadIdx.x
    if comp >= MV.shape[0] or v >= N_VERT:
        return
    gv = comp * N_VERT + v
    lx = 0.0; ly = 0.0; lz = 0.0
    for k in range(ADJ_OFF[gv], ADJ_OFF[gv + 1]):
        tri = ADJ_VAL[k] >> 2
        lx += FTRI[comp, tri, 0] / 3.0
        ly += FTRI[comp, tri, 1] / 3.0
        lz += FTRI[comp, tri, 2] / 3.0
    LOADS[gv, 0] = lx; LOADS[gv, 1] = ly; LOADS[gv, 2] = lz
    MVPRE[gv, 0] = MV[gv, 0]; MVPRE[gv, 1] = MV[gv, 1]
    MVPRE[gv, 2] = MV[gv, 2]
    glx = MASSES[gv] * GRAV[0]
    gly = MASSES[gv] * GRAV[1]
    glz = MASSES[gv] * GRAV[2]
    GLOADS[gv, 0] = glx; GLOADS[gv, 1] = gly; GLOADS[gv, 2] = glz
    GLH[gv, 0] = glx * H[0]
    GLH[gv, 1] = gly * H[0]
    GLH[gv, 2] = glz * H[0]
    pim = INV_M[gv]
    MV[gv, 0] = MV[gv, 0] + (lx + glx) * pim * H[0]
    MV[gv, 1] = MV[gv, 1] + (ly + gly) * pim * H[0]
    MV[gv, 2] = MV[gv, 2] + (lz + glz) * pim * H[0]


@cuda.jit
def k_pressure_plate(PV, PVPRE, PLATE_MASS, GRAV, H, PASS, SUB):
    comp = cuda.grid(1)
    if comp >= PV.shape[0]:
        return
    m = PLATE_MASS[comp]
    gmx = GRAV[0] * m; gmy = GRAV[1] * m; gmz = GRAV[2] * m
    vx0 = PV[comp, 0]; vy0 = PV[comp, 1]; vz0 = PV[comp, 2]
    inv_m = 1.0 / m
    vx1 = vx0 + gmx * inv_m * H[0]
    vy1 = vy0 + gmy * inv_m * H[0]
    vz1 = vz0 + gmz * inv_m * H[0]
    PV[comp, 0] = vx1; PV[comp, 1] = vy1; PV[comp, 2] = vz1
    PVPRE[comp, 0] = vx0; PVPRE[comp, 1] = vy0; PVPRE[comp, 2] = vz0
    bx = 0.5 * (vx0 + vx1); by = 0.5 * (vy0 + vy1); bz = 0.5 * (vz0 + vz1)
    PASS[comp, SUB, P_WGRAVP] = ((gmx * bx + gmy * by) + gmz * bz) * H[0]
    PASS[comp, SUB, P_GIPX] = gmx * H[0]
    PASS[comp, SUB, P_GIPY] = gmy * H[0]
    PASS[comp, SUB, P_GIPZ] = gmz * H[0]


@cuda.jit
def k_pressure_diag_sub(MV, MVPRE, LOADS, GLOADS, GLH, H, PASS, SUB):
    comp = cuda.grid(1)
    if comp >= MV.shape[0]:
        return
    b = comp * N_VERT
    tmp = cuda.local.array(126, dtype=np.float64)
    for i in range(126):
        fl = i // 3
        c = i % 3
        vbar = 0.5 * (MVPRE[b + fl, c] + MV[b + fl, c])
        tmp[i] = LOADS[b + fl, c] * vbar
    w_press = npsum(tmp, 126) * H[0]
    for i in range(126):
        fl = i // 3
        c = i % 3
        vbar = 0.5 * (MVPRE[b + fl, c] + MV[b + fl, c])
        tmp[i] = GLOADS[b + fl, c] * vbar
    w_grav_mem = npsum(tmp, 126) * H[0]
    # (g_loads * h) column sums in numpy order (g_loads*h is in GLH)
    g0 = 0.0; g1 = 0.0; g2 = 0.0
    tmpc = cuda.local.array(42, dtype=np.float64)
    for c in range(3):
        for r in range(42):
            tmpc[r] = GLH[b + r, c]
        s = npsum(tmpc, 42)
        if c == 0:
            g0 = s
        elif c == 1:
            g1 = s
        else:
            g2 = s
    PASS[comp, SUB, P_WPRESS] = w_press
    PASS[comp, SUB, P_WGRAVM] = w_grav_mem
    PASS[comp, SUB, P_GIMX] = g0
    PASS[comp, SUB, P_GIMY] = g1
    PASS[comp, SUB, P_GIMZ] = g2


@cuda.jit
def k_material(SC, PV, ALPHA, K, C, H, PLATE_MASS, PASS, SUB):
    comp = cuda.grid(1)
    if comp >= PV.shape[0]:
        return
    a = SC[comp, 0]
    v1x = PV[comp, 0]
    dt = H[0]
    k = K[0]
    c = C[0]
    alpha = ALPHA[0]
    tau = c / k
    b = c * v1x
    d = a - b
    int_F_dt = b * dt + (a - b) * tau * (1.0 - alpha)
    int_F2_dt = b * b * dt + 2.0 * b * d * tau * (1.0 - alpha) \
        + d * d * (tau / 2.0) * (1.0 - alpha * alpha)
    F_next = alpha * a + c * v1x * (1.0 - alpha)
    u_prev = a * a / (2.0 * k)
    u_i = F_next * F_next / (2.0 * k)
    q_i = int_F2_dt / c
    J = int_F_dt
    inv_m = 1.0 / PLATE_MASS[comp]
    v_pre_x = PV[comp, 0]
    PV[comp, 0] = PV[comp, 0] - J * inv_m
    w_on_plate = -J * (0.5 * (v_pre_x + PV[comp, 0]))
    SC[comp, 0] = F_next
    SC[comp, 1] = u_i
    SC[comp, 2] = SC[comp, 2] + q_i
    SC[comp, 3] = SC[comp, 3] + v1x * J
    PASS[comp, SUB, P_WMAT] = w_on_plate
    PASS[comp, SUB, P_Q] = q_i
    PASS[comp, SUB, P_MATIMP] = -J
    PASS[comp, SUB, P_SUBCLOSE] = abs((v1x * J) - ((u_i - u_prev) + q_i))


@cuda.jit
def k_contact(X, PX, GX, MV, PV, TRIS, MASSES, PLATE_MASS, PORT_MASS, H,
              PASS, SUB):
    """M06 sweep -> narrow -> Gauss-Seidel, single sequential thread per
    component (the declared order; kernel_mirror.k_contact transcription)."""
    comp = cuda.blockIdx.x
    if comp >= MV.shape[0]:
        return
    b = comp * N_VERT

    ta = cuda.local.array((3, 3), dtype=np.float64)
    tb = cuda.local.array((3, 3), dtype=np.float64)
    lo = cuda.local.array((N_ENTRIES, 3), dtype=np.float64)
    hi = cuda.local.array((N_ENTRIES, 3), dtype=np.float64)
    order = cuda.local.array(N_ENTRIES, dtype=np.int64)
    centers = cuda.local.array((N_ENTRIES, 3), dtype=np.float64)
    cand_i = cuda.local.array(256, dtype=np.int64)
    cand_j = cuda.local.array(256, dtype=np.int64)
    act_a = cuda.local.array(MAX_ACTIVE, dtype=np.int64)
    act_b = cuda.local.array(MAX_ACTIVE, dtype=np.int64)
    act_gap = cuda.local.array(MAX_ACTIVE, dtype=np.float64)
    act_nx = cuda.local.array(MAX_ACTIVE, dtype=np.float64)
    act_ny = cuda.local.array(MAX_ACTIVE, dtype=np.float64)
    act_nz = cuda.local.array(MAX_ACTIVE, dtype=np.float64)
    rec_jn = cuda.local.array(MAX_ACTIVE, dtype=np.float64)
    rec_jt = cuda.local.array(MAX_ACTIVE, dtype=np.float64)
    rec_mode = cuda.local.array(MAX_ACTIVE, dtype=np.int64)
    best = cuda.local.array(7, dtype=np.float64)

    ke_pre = ke_membrane_plate(MV, PV, MASSES, PLATE_MASS, b, comp)

    speed_m = 0.0
    for v in range(N_VERT):
        s = norm3_seq(MV[b + v, 0], MV[b + v, 1], MV[b + v, 2])
        if s > speed_m:
            speed_m = s
    speed_p = norm3_seq(PV[comp, 0], PV[comp, 1], PV[comp, 2])
    motion = speed_m * H[0]
    if speed_p * H[0] > motion:
        motion = speed_p * H[0]
    inflate = motion + THICKNESS_M + CONTACT_MARGIN_M
    for e in range(N_ENTRIES):
        tri_verts_of_t(X, PX, GX, TRIS, e, comp, ta)
        lox = ta[0, 0]
        if ta[1, 0] < lox:
            lox = ta[1, 0]
        if ta[2, 0] < lox:
            lox = ta[2, 0]
        hix = ta[0, 0]
        if ta[1, 0] > hix:
            hix = ta[1, 0]
        if ta[2, 0] > hix:
            hix = ta[2, 0]
        loy = ta[0, 1]
        if ta[1, 1] < loy:
            loy = ta[1, 1]
        if ta[2, 1] < loy:
            loy = ta[2, 1]
        hiy = ta[0, 1]
        if ta[1, 1] > hiy:
            hiy = ta[1, 1]
        if ta[2, 1] > hiy:
            hiy = ta[2, 1]
        loz = ta[0, 2]
        if ta[1, 2] < loz:
            loz = ta[1, 2]
        if ta[2, 2] < loz:
            loz = ta[2, 2]
        hiz = ta[0, 2]
        if ta[1, 2] > hiz:
            hiz = ta[1, 2]
        if ta[2, 2] > hiz:
            hiz = ta[2, 2]
        lo[e, 0] = lox - inflate
        lo[e, 1] = loy - inflate
        lo[e, 2] = loz - inflate
        hi[e, 0] = hix + inflate
        hi[e, 1] = hiy + inflate
        hi[e, 2] = hiz + inflate
        centers[e, 0] = (lo[e, 0] + hi[e, 0]) * 0.5
        centers[e, 1] = (lo[e, 1] + hi[e, 1]) * 0.5
        centers[e, 2] = (lo[e, 2] + hi[e, 2]) * 0.5
    m0 = 0.0; m1 = 0.0; m2 = 0.0
    for e in range(N_ENTRIES):
        m0 += centers[e, 0]
        m1 += centers[e, 1]
        m2 += centers[e, 2]
    m0 /= N_ENTRIES
    m1 /= N_ENTRIES
    m2 /= N_ENTRIES
    v0 = 0.0; v1 = 0.0; v2 = 0.0
    for e in range(N_ENTRIES):
        dv = centers[e, 0] - m0
        v0 += dv * dv
        dv = centers[e, 1] - m1
        v1 += dv * dv
        dv = centers[e, 2] - m2
        v2 += dv * dv
    axis = 0
    best_var = v0
    if v1 > best_var:
        axis = 1
        best_var = v1
    if v2 > best_var:
        axis = 2
        best_var = v2
    for e in range(N_ENTRIES):
        order[e] = e
    for i in range(1, N_ENTRIES):
        key = order[i]
        j = i - 1
        while j >= 0:
            ko = order[j]
            swap = lo[key, axis] < lo[ko, axis]
            if lo[key, axis] == lo[ko, axis] and key < ko:
                swap = True
            if swap:
                order[j + 1] = ko
                j -= 1
            else:
                break
        order[j + 1] = key
    ncand = 0
    for pos in range(N_ENTRIES):
        ei = order[pos]
        kgi = entry_kind(ei)
        loi0 = lo[ei, 0]; loi1 = lo[ei, 1]; loi2 = lo[ei, 2]
        hii0 = hi[ei, 0]; hii1 = hi[ei, 1]; hii2 = hi[ei, 2]
        for p2 in range(pos + 1, N_ENTRIES):
            ej = order[p2]
            if lo[ej, axis] > hi[ei, axis]:
                break
            kgj = entry_kind(ej)
            if kgi == kgj:
                continue
            if loi0 <= hi[ej, 0] and lo[ej, 0] <= hii0 \
                    and loi1 <= hi[ej, 1] and lo[ej, 1] <= hii1 \
                    and loi2 <= hi[ej, 2] and lo[ej, 2] <= hii2:
                if ei < ej:
                    cand_i[ncand] = ei
                    cand_j[ncand] = ej
                else:
                    cand_i[ncand] = ej
                    cand_j[ncand] = ei
                ncand += 1
    for i in range(1, ncand):
        ki = cand_i[i]
        kj = cand_j[i]
        j = i - 1
        while j >= 0 and (cand_i[j] > ki or (cand_i[j] == ki
                                             and cand_j[j] > kj)):
            cand_i[j + 1] = cand_i[j]
            cand_j[j + 1] = cand_j[j]
            j -= 1
        cand_i[j + 1] = ki
        cand_j[j + 1] = kj
    nact = 0
    pair_cap_hit = False
    for k in range(ncand):
        ea = cand_i[k]
        eb = cand_j[k]
        tri_verts_of_t(X, PX, GX, TRIS, ea, comp, ta)
        tri_verts_of_t(X, PX, GX, TRIS, eb, comp, tb)
        tri_tri_closest_dev(ta, tb, best)
        dist = best[0]
        gap = dist - THICKNESS_M
        if gap <= CONTACT_MARGIN_M + CCD_TOL_M:
            if dist > 0.0:
                nx = (best[1] - best[4]) / dist
                ny = (best[2] - best[5]) / dist
                nz = (best[3] - best[6]) / dist
            else:
                nx = 0.0
                ny = 0.0
                nz = 1.0
            if nact < MAX_ACTIVE:
                act_a[nact] = ea
                act_b[nact] = eb
                act_gap[nact] = gap
                act_nx[nact] = nx
                act_ny[nact] = ny
                act_nz[nact] = nz
            else:
                pair_cap_hit = True
            nact += 1
    if pair_cap_hit:
        PASS[comp, SUB, P_ACTIVE] = float(nact)
        PASS[comp, SUB, P_ITERS] = 0.0
        PASS[comp, SUB, P_GSRES] = 1.0e300
        return
    contact_mx = 0.0; contact_my = 0.0; contact_mz = 0.0
    contact_px = 0.0; contact_py = 0.0; contact_pz = 0.0
    contact_gx = 0.0; contact_gy = 0.0; contact_gz = 0.0
    recip_x = 0.0; recip_y = 0.0; recip_z = 0.0
    d_friction = 0.0
    d_impact = 0.0
    trap = 0.0
    jn_total = 0.0
    iterations = 0
    max_jn = 0.0
    for iteration in range(GS_CAP):
        iterations = iteration + 1
        pass_max = 0.0
        for k in range(nact):
            ea = act_a[k]
            eb = act_b[k]
            gap = act_gap[k]
            nx = act_nx[k]; ny = act_ny[k]; nz = act_nz[k]
            vax0, vay0, vaz0 = body_vel_t(MV, PV, TRIS, b, comp, ea)
            vbx0, vby0, vbz0 = body_vel_t(MV, PV, TRIS, b, comp, eb)
            inv_ma = body_inv_m_t(PORT_MASS, PLATE_MASS, comp, ea)
            inv_mb = body_inv_m_t(PORT_MASS, PLATE_MASS, comp, eb)
            denom = inv_ma + inv_mb
            m_eff = 1.0 / denom
            rvx = vax0 - vbx0; rvy = vay0 - vby0; rvz = vaz0 - vbz0
            vn = rvx * nx + rvy * ny + rvz * nz
            pen = -gap
            bias = BETA_OVER_DT * (pen - SLOP_M)
            if bias < 0.0:
                bias = 0.0
            jn = m_eff * (-(1.0 + REST) * vn + bias)
            if jn < 0.0:
                jn = 0.0
            jx = nx * jn; jy = ny * jn; jz = nz * jn
            write_body_vel_t(MV, PV, TRIS, b, comp, ea,
                             vax0 + jx * inv_ma, vay0 + jy * inv_ma,
                             vaz0 + jz * inv_ma)
            write_body_vel_t(MV, PV, TRIS, b, comp, eb,
                             vbx0 - jx * inv_mb, vby0 - jy * inv_mb,
                             vbz0 - jz * inv_mb)
            vax1, vay1, vaz1 = body_vel_t(MV, PV, TRIS, b, comp, ea)
            vbx1, vby1, vbz1 = body_vel_t(MV, PV, TRIS, b, comp, eb)
            rvx = vax1 - vbx1; rvy = vay1 - vby1; rvz = vaz1 - vbz1
            vn_after = rvx * nx + rvy * ny + rvz * nz
            tvx = rvx - nx * vn_after
            tvy = rvy - ny * vn_after
            tvz = rvz - nz * vn_after
            vt_pre = norm3_seq(tvx, tvy, tvz)
            mu_s, mu_k = pair_mu_t(ea, eb)
            jt_mag = 0.0
            mode = 0
            tx = 0.0; ty = 0.0; tz = 0.0
            if vt_pre > MU_TINY:
                jt_req = m_eff * vt_pre
                if jt_req <= mu_s * jn:
                    jt_mag = jt_req
                    mode = 1
                else:
                    jt_mag = mu_k * jn
                    mode = 2
                tx = -tvx / vt_pre
                ty = -tvy / vt_pre
                tz = -tvz / vt_pre
                write_body_vel_t(MV, PV, TRIS, b, comp, ea,
                                 vax1 + tx * jt_mag * inv_ma,
                                 vay1 + ty * jt_mag * inv_ma,
                                 vaz1 + tz * jt_mag * inv_ma)
                write_body_vel_t(MV, PV, TRIS, b, comp, eb,
                                 vbx1 - tx * jt_mag * inv_mb,
                                 vby1 - ty * jt_mag * inv_mb,
                                 vbz1 - tz * jt_mag * inv_mb)
            vax2, vay2, vaz2 = body_vel_t(MV, PV, TRIS, b, comp, ea)
            vbx2, vby2, vbz2 = body_vel_t(MV, PV, TRIS, b, comp, eb)
            rvx = vax2 - vbx2; rvy = vay2 - vby2; rvz = vaz2 - vbz2
            vn2 = rvx * nx + rvy * ny + rvz * nz
            tvx = rvx - nx * vn2
            tvy = rvy - ny * vn2
            tvz = rvz - nz * vn2
            vt_post = norm3_seq(tvx, tvy, tvz)
            w_f = 0.5 * m_eff * (vt_pre * vt_pre - vt_post * vt_post)
            if w_f < 0.0:
                w_f = 0.0
            rec_jn[k] = jn
            rec_jt[k] = jt_mag
            rec_mode[k] = mode
            if jn > pass_max:
                pass_max = jn
            if jt_mag > pass_max:
                pass_max = jt_mag
            ix = jx + tx * jt_mag
            iy = jy + ty * jt_mag
            iz = jz + tz * jt_mag
            kga = entry_kind(ea)
            if kga == 0:
                contact_mx += ix; contact_my += iy; contact_mz += iz
            elif kga == 1:
                contact_px += ix; contact_py += iy; contact_pz += iz
            else:
                contact_gx += ix; contact_gy += iy; contact_gz += iz
            kgb = entry_kind(eb)
            if kgb == 0:
                contact_mx -= ix; contact_my -= iy; contact_mz -= iz
            elif kgb == 1:
                contact_px -= ix; contact_py -= iy; contact_pz -= iz
            else:
                contact_gx -= ix; contact_gy -= iy; contact_gz -= iz
            recip_x += ix
            recip_y += iy
            recip_z += iz
            recip_x -= ix
            recip_y -= iy
            recip_z -= iz
            abx = 0.5 * (vax0 + vax2)
            aby = 0.5 * (vay0 + vay2)
            abz = 0.5 * (vaz0 + vaz2)
            bbx = 0.5 * (vbx0 + vbx2)
            bby = 0.5 * (vby0 + vby2)
            bbz = 0.5 * (vbz0 + vbz2)
            trap += 0.5 * ((abx * ix + aby * iy + abz * iz)
                           - (bbx * ix + bby * iy + bbz * iz))
            if jn > 0.0:
                jn_total += jn
            else:
                jn_total -= jn
            vn_pre = (vax0 - vbx0) * nx + (vay0 - vby0) * ny \
                + (vaz0 - vbz0) * nz
            if vn_pre < 0.0:
                d_impact += 0.5 * m_eff * vn_pre * vn_pre
        max_jn = pass_max
        if pass_max <= GS_TOL_N_S:
            break
    ke_post = ke_membrane_plate(MV, PV, MASSES, PLATE_MASS, b, comp)
    w_contact_ke = -(ke_post - ke_pre)
    min_jn = 0.0
    if nact > 0:
        min_jn = rec_jn[0]
    min_vn = 0.0
    cone = 0.0
    stick = 0.0
    for k in range(nact):
        if rec_jn[k] < min_jn:
            min_jn = rec_jn[k]
        ea = act_a[k]
        eb = act_b[k]
        vax, vay, vaz = body_vel_t(MV, PV, TRIS, b, comp, ea)
        vbx, vby, vbz = body_vel_t(MV, PV, TRIS, b, comp, eb)
        vn = (vax - vbx) * act_nx[k] + (vay - vby) * act_ny[k] \
            + (vaz - vbz) * act_nz[k]
        if vn < min_vn:
            min_vn = vn
        if rec_jn[k] > 0.0 and rec_mode[k] != 0:
            mu_s, mu_k = pair_mu_t(ea, eb)
            mu_used = mu_s if rec_mode[k] == 1 else mu_k
            viol = rec_jt[k] if rec_jt[k] > 0.0 else -rec_jt[k]
            viol = viol - mu_used * rec_jn[k] - 1e-15
            if viol > cone:
                cone = viol
        if rec_mode[k] == 1:
            rvx = vax - vbx; rvy = vay - vby; rvz = vaz - vbz
            tvx = rvx - act_nx[k] * vn
            tvy = rvy - act_ny[k] * vn
            tvz = rvz - act_nz[k] * vn
            vt = norm3_seq(tvx, tvy, tvz)
            if vt > stick:
                stick = vt
    PASS[comp, SUB, P_WCKE] = w_contact_ke
    PASS[comp, SUB, P_DFRIC] = d_friction
    PASS[comp, SUB, P_DIMP] = d_impact
    PASS[comp, SUB, P_ESTAB] = -w_contact_ke + d_friction + d_impact
    PASS[comp, SUB, P_JNTOT] = jn_total
    PASS[comp, SUB, P_TRAP] = trap
    PASS[comp, SUB, P_ITERS] = float(iterations)
    PASS[comp, SUB, P_GSRES] = max_jn
    PASS[comp, SUB, P_ACTIVE] = float(nact)
    PASS[comp, SUB, P_MINJN] = min_jn
    PASS[comp, SUB, P_MINVN] = min_vn
    PASS[comp, SUB, P_CONE] = cone
    PASS[comp, SUB, P_STICK] = stick
    PASS[comp, SUB, P_ANCX] = -contact_gx
    PASS[comp, SUB, P_ANCY] = -contact_gy
    PASS[comp, SUB, P_ANCZ] = -contact_gz
    PASS[comp, SUB, P_CMX] = contact_mx
    PASS[comp, SUB, P_CMY] = contact_my
    PASS[comp, SUB, P_CMZ] = contact_mz
    PASS[comp, SUB, P_CPX] = contact_px
    PASS[comp, SUB, P_CPY] = contact_py
    PASS[comp, SUB, P_CPZ] = contact_pz
    PASS[comp, SUB, P_CGX] = contact_gx
    PASS[comp, SUB, P_CGY] = contact_gy
    PASS[comp, SUB, P_CGZ] = contact_gz
    PASS[comp, SUB, P_RECIPX] = recip_x
    PASS[comp, SUB, P_RECIPY] = recip_y
    PASS[comp, SUB, P_RECIPZ] = recip_z


@cuda.jit(device=True, inline=True)
def ke_membrane_plate(MV, PV, MASSES, PLATE_MASS, b, comp):
    tmp = cuda.local.array(126, dtype=np.float64)
    for i in range(126):
        fl = i // 3
        c = i % 3
        tmp[i] = (0.5 * MASSES[b + fl]) * (MV[b + fl, c] * MV[b + fl, c])
    ke = npsum(tmp, 126)
    dot = PV[comp, 0] * PV[comp, 0] + PV[comp, 1] * PV[comp, 1] \
        + PV[comp, 2] * PV[comp, 2]
    return ke + 0.5 * PLATE_MASS[comp] * dot


@cuda.jit
def k_integrate_mem(X, XPRE, MV, H):
    gv = cuda.grid(1)
    if gv >= X.shape[0]:
        return
    XPRE[gv, 0] = X[gv, 0]
    XPRE[gv, 1] = X[gv, 1]
    XPRE[gv, 2] = X[gv, 2]
    X[gv, 0] = X[gv, 0] + MV[gv, 0] * H[0]
    X[gv, 1] = X[gv, 1] + MV[gv, 1] * H[0]
    X[gv, 2] = X[gv, 2] + MV[gv, 2] * H[0]


@cuda.jit
def k_integrate_plate(PX, PV, H):
    comp = cuda.grid(1)
    if comp >= PX.shape[0]:
        return
    for r in range(4):
        PX[comp, r, 0] = PX[comp, r, 0] + PV[comp, 0] * H[0]
        PX[comp, r, 1] = PX[comp, r, 1] + PV[comp, 1] * H[0]
        PX[comp, r, 2] = PX[comp, r, 2] + PV[comp, 2] * H[0]


@cuda.jit
def k_xpbd(X, XPRE, MV, PV, EDGES, REST, INV_M, MASSES, PLATE_MASS, H,
           PASS, SUB):
    comp = cuda.blockIdx.x
    if comp >= MV.shape[0]:
        return
    b = comp * N_VERT
    ke_pre = ke_membrane_plate(MV, PV, MASSES, PLATE_MASS, b, comp)
    us_pre = scaffold_edges(XPRE, EDGES, REST, b, comp,
                            1.0 / (2.0 * XPBD_COMPLIANCE))
    alpha_tilde = XPBD_COMPLIANCE / (H[0] * H[0])
    lam = cuda.local.array(N_EDGES, dtype=np.float64)
    for e in range(N_EDGES):
        lam[e] = 0.0
    for _it in range(XPBD_ITERATIONS_CAP):
        max_c = 0.0
        for e in range(N_EDGES):
            a1 = EDGES[comp, e, 0] + b
            a2 = EDGES[comp, e, 1] + b
            dx = X[a2, 0] - X[a1, 0]
            dy = X[a2, 1] - X[a1, 1]
            dz = X[a2, 2] - X[a1, 2]
            length = norm3_seq(dx, dy, dz)
            if length == 0.0:
                continue
            gx = dx / length
            gy = dy / length
            gz = dz / length
            cc = length - REST[comp, e]
            if cc < 0.0:
                ccabs = -cc
            else:
                ccabs = cc
            if ccabs > max_c:
                max_c = ccabs
            w_sum = INV_M[a1] + INV_M[a2]
            dlam = (-cc - alpha_tilde * lam[e]) / (w_sum + alpha_tilde)
            lam[e] += dlam
            X[a1, 0] -= INV_M[a1] * dlam * gx
            X[a1, 1] -= INV_M[a1] * dlam * gy
            X[a1, 2] -= INV_M[a1] * dlam * gz
            X[a2, 0] += INV_M[a2] * dlam * gx
            X[a2, 1] += INV_M[a2] * dlam * gy
            X[a2, 2] += INV_M[a2] * dlam * gz
        if max_c <= XPBD_TOL_M:
            break
    for i in range(126):
        fl = i // 3
        c = i % 3
        MV[b + fl, c] = (X[b + fl, c] - XPRE[b + fl, c]) / H[0]
    ke_post = ke_membrane_plate(MV, PV, MASSES, PLATE_MASS, b, comp)
    us_post = scaffold_edges(X, EDGES, REST, b, comp,
                             1.0 / (2.0 * XPBD_COMPLIANCE))
    PASS[comp, SUB, P_PROJ] = (ke_post - ke_pre) + (us_post - us_pre)


@cuda.jit
def k_tick_diag(MV, PV, X, PX, TRIS, EDGES, REST, MASSES, PLATE_MASS,
                VSTART, PVSTART, SC, PASS, E_PREV, UMAT_PRE, US_PREV, TICK,
                DP_A, BHERR, BHRMS, BHDIR, BLOCK):
    """Tick fold (M07's declared accumulation order), state scalars,
    ledgers, gates inputs, chained digest — one thread per component."""
    comp = cuda.blockIdx.x
    if comp >= MV.shape[0]:
        return
    b = comp * N_VERT
    w_press = 0.0
    w_grav = 0.0
    gimx = 0.0; gimy = 0.0; gimz = 0.0
    gipx = 0.0; gipy = 0.0; gipz = 0.0
    w_mat = 0.0
    q_tick = 0.0
    mat_imp = 0.0
    subclose = 0.0
    wcke = 0.0
    dfric = 0.0
    dimp = 0.0
    estab = 0.0
    jntot = 0.0
    trap = 0.0
    iters = 0.0
    gsres = 0.0
    active = 0.0
    minjn = 0.0
    minvn = 0.0
    cone = 0.0
    stick = 0.0
    cmx = 0.0; cmy = 0.0; cmz = 0.0
    cpx = 0.0; cpy = 0.0; cpz = 0.0
    cgx = 0.0; cgy = 0.0; cgz = 0.0
    anx = 0.0; any_ = 0.0; anz = 0.0
    rx = 0.0; ry = 0.0; rz = 0.0
    proj = 0.0
    w_sg = 0.0
    sgx = 0.0; sgy = 0.0; sgz = 0.0
    sgpx = 0.0; sgpy = 0.0; sgpz = 0.0
    first = True
    for s in range(4):
        w_press = w_press + PASS[comp, s, P_WPRESS]
        w_grav = w_grav + (PASS[comp, s, P_WGRAVM] + PASS[comp, s, P_WGRAVP])
        gimx = gimx + PASS[comp, s, P_GIMX]
        gimy = gimy + PASS[comp, s, P_GIMY]
        gimz = gimz + PASS[comp, s, P_GIMZ]
        gipx = gipx + PASS[comp, s, P_GIPX]
        gipy = gipy + PASS[comp, s, P_GIPY]
        gipz = gipz + PASS[comp, s, P_GIPZ]
        w_mat = w_mat + PASS[comp, s, P_WMAT]
        q_tick = q_tick + PASS[comp, s, P_Q]
        mat_imp = mat_imp + PASS[comp, s, P_MATIMP]
        if PASS[comp, s, P_SUBCLOSE] > subclose:
            subclose = PASS[comp, s, P_SUBCLOSE]
        wcke = wcke + PASS[comp, s, P_WCKE]
        dfric = dfric + PASS[comp, s, P_DFRIC]
        dimp = dimp + PASS[comp, s, P_DIMP]
        estab = estab + PASS[comp, s, P_ESTAB]
        jntot = jntot + PASS[comp, s, P_JNTOT]
        trap = trap + PASS[comp, s, P_TRAP]
        iters = iters + PASS[comp, s, P_ITERS]
        if PASS[comp, s, P_GSRES] > gsres:
            gsres = PASS[comp, s, P_GSRES]
        active = active + PASS[comp, s, P_ACTIVE]
        if first:
            minjn = PASS[comp, s, P_MINJN]
            minvn = PASS[comp, s, P_MINVN]
            first = False
        else:
            if PASS[comp, s, P_MINJN] < minjn:
                minjn = PASS[comp, s, P_MINJN]
            if PASS[comp, s, P_MINVN] < minvn:
                minvn = PASS[comp, s, P_MINVN]
        if PASS[comp, s, P_CONE] > cone:
            cone = PASS[comp, s, P_CONE]
        if PASS[comp, s, P_STICK] > stick:
            stick = PASS[comp, s, P_STICK]
        cmx = cmx + PASS[comp, s, P_CMX]
        cmy = cmy + PASS[comp, s, P_CMY]
        cmz = cmz + PASS[comp, s, P_CMZ]
        cpx = cpx + PASS[comp, s, P_CPX]
        cpy = cpy + PASS[comp, s, P_CPY]
        cpz = cpz + PASS[comp, s, P_CPZ]
        cgx = cgx + PASS[comp, s, P_CGX]
        cgy = cgy + PASS[comp, s, P_CGY]
        cgz = cgz + PASS[comp, s, P_CGZ]
        anx = anx + PASS[comp, s, P_ANCX]
        any_ = any_ + PASS[comp, s, P_ANCY]
        anz = anz + PASS[comp, s, P_ANCZ]
        rx = rx + PASS[comp, s, P_RECIPX]
        ry = ry + PASS[comp, s, P_RECIPY]
        rz = rz + PASS[comp, s, P_RECIPZ]
        proj = proj + PASS[comp, s, P_PROJ]
        w_sg = w_sg + PASS[comp, s, P_WSG]
        sgx = sgx + PASS[comp, s, P_SGIMPX]
        sgy = sgy + PASS[comp, s, P_SGIMPY]
        sgz = sgz + PASS[comp, s, P_SGIMPZ]
        sgpx = sgpx + PASS[comp, s, P_SGIPX]
        sgpy = sgpy + PASS[comp, s, P_SGIPY]
        sgpz = sgpz + PASS[comp, s, P_SGIPZ]
    ke = ke_membrane_plate(MV, PV, MASSES, PLATE_MASS, b, comp)
    us = scaffold_edges(X, EDGES, REST, b, comp,
                        1.0 / (2.0 * XPBD_COMPLIANCE))
    umat = SC[comp, 1]
    e_mech = ke + us + umat
    w_ext = w_press + w_grav + w_sg
    turnover = 0.0
    tv = w_press
    if tv < 0.0:
        tv = -tv
    turnover = turnover + tv
    tv = w_grav
    if tv < 0.0:
        tv = -tv
    turnover = turnover + tv
    tv = w_mat
    if tv < 0.0:
        tv = -tv
    turnover = turnover + tv
    tv = wcke
    if tv < 0.0:
        tv = -tv
    turnover = turnover + tv
    turnover = turnover + ke
    bound = RESID_FRACTION * turnover + umat + UMAT_PRE[comp] + us \
        + US_PREV[comp] + 1e-9
    residual = e_mech - E_PREV[comp] - w_ext + q_tick + dfric + dimp \
        - estab - proj
    # momentum ledger
    tmp = cuda.local.array(42, dtype=np.float64)
    mdvx = 0.0
    mdvy = 0.0
    mdvz = 0.0
    for c in range(3):
        for r in range(42):
            tmp[r] = MASSES[b + r] * (MV[b + r, c] - VSTART[b + r, c])
        s = npsum(tmp, 42)
        if c == 0:
            mdvx = s
        elif c == 1:
            mdvy = s
        else:
            mdvz = s
    pdmx = mdvx - (gimx + sgx + cmx)
    pdmy = mdvy - (gimy + sgy + cmy)
    pdmz = mdvz - (gimz + sgz + cmz)
    pmx = PLATE_MASS[comp] * (PV[comp, 0] - PVSTART[comp, 0])
    pmy = PLATE_MASS[comp] * (PV[comp, 1] - PVSTART[comp, 1])
    pmz = PLATE_MASS[comp] * (PV[comp, 2] - PVSTART[comp, 2])
    ptx = gipx + sgpx + cpx + mat_imp
    pty = gipy + cpy
    ptz = gipz + cpz
    pdplx = pmx - ptx
    pdply = pmy - pty
    pdplz = pmz - ptz
    anres = norm3_seq(anx + cgx, any_ + cgy, anz + cgz)
    # boundary cumulative updates (M07 per-tick)
    SC[comp, 4] = SC[comp, 4] + anx
    SC[comp, 5] = SC[comp, 5] + any_
    SC[comp, 6] = SC[comp, 6] + anz
    SC[comp, 7] = SC[comp, 7] - mat_imp
    # state scalars
    comx = 0.0
    comy = 0.0
    comz = 0.0
    for c in range(3):
        for r in range(42):
            tmp[r] = X[b + r, c] * MASSES[b + r]
        s = npsum(tmp, 42)
        if c == 0:
            comx = s
        elif c == 1:
            comy = s
        else:
            comz = s
    m_tot = npsum42(MASSES, b)
    comx /= m_tot
    comy /= m_tot
    comz /= m_tot
    tmp8 = cuda.local.array(N_TRI, dtype=np.float64)
    for t in range(N_TRI):
        i0 = TRIS[comp, t, 0] + b
        i1 = TRIS[comp, t, 1] + b
        i2 = TRIS[comp, t, 2] + b
        c1y = X[i1, 1] * X[i2, 2] - X[i1, 2] * X[i2, 1]
        c1z = X[i1, 2] * X[i2, 0] - X[i1, 0] * X[i2, 2]
        c1x = X[i1, 0] * X[i2, 1] - X[i1, 1] * X[i2, 0]
        tmp8[t] = X[i0, 0] * c1x + X[i0, 1] * c1y + X[i0, 2] * c1z
    vol = npsum(tmp8, N_TRI) / 6.0
    maxspd = 0.0
    for v in range(N_VERT):
        s = norm3_seq(MV[b + v, 0], MV[b + v, 1], MV[b + v, 2])
        if s > maxspd:
            maxspd = s
    # fill the declared block
    BLOCK[comp, D_KE] = ke
    BLOCK[comp, D_USCAFF] = us
    BLOCK[comp, D_UMAT] = umat
    BLOCK[comp, D_QMAT] = SC[comp, 2]
    BLOCK[comp, D_WIN] = SC[comp, 3]
    BLOCK[comp, D_F] = SC[comp, 0]
    BLOCK[comp, D_PLX] = ((PX[comp, 0, 0] + PX[comp, 1, 0])
                          + PX[comp, 2, 0] + PX[comp, 3, 0]) / 4.0
    BLOCK[comp, D_PLVX] = PV[comp, 0]
    BLOCK[comp, D_PLVY] = PV[comp, 1]
    BLOCK[comp, D_PLVZ] = PV[comp, 2]
    BLOCK[comp, D_COMX] = comx
    BLOCK[comp, D_COMY] = comy
    BLOCK[comp, D_COMZ] = comz
    BLOCK[comp, D_VOL] = vol
    BLOCK[comp, D_MAXSPD] = maxspd
    BLOCK[comp, D_WPRESS] = w_press
    BLOCK[comp, D_WGRAV] = w_grav
    BLOCK[comp, D_WMAT] = w_mat
    BLOCK[comp, D_QTICK] = q_tick
    BLOCK[comp, D_WCKE] = wcke
    BLOCK[comp, D_DFRIC] = dfric
    BLOCK[comp, D_DIMP] = dimp
    BLOCK[comp, D_ESTAB] = estab
    BLOCK[comp, D_JNTOT] = jntot
    BLOCK[comp, D_TRAP] = trap
    BLOCK[comp, D_PROJ] = proj
    BLOCK[comp, D_RESID] = residual
    BLOCK[comp, D_BOUND] = bound
    BLOCK[comp, D_WEXT] = w_ext
    BLOCK[comp, D_ITERS] = iters
    BLOCK[comp, D_GSRES] = gsres
    BLOCK[comp, D_ACTIVE] = active
    BLOCK[comp, D_MINJN] = minjn
    BLOCK[comp, D_MINVN] = minvn
    BLOCK[comp, D_CONE] = cone
    BLOCK[comp, D_STICK] = stick
    BLOCK[comp, D_ANCX] = SC[comp, 4]
    BLOCK[comp, D_ANCY] = SC[comp, 5]
    BLOCK[comp, D_ANCZ] = SC[comp, 6]
    BLOCK[comp, D_WALLX] = SC[comp, 7]
    BLOCK[comp, D_WALLY] = SC[comp, 8]
    BLOCK[comp, D_WALLZ] = SC[comp, 9]
    BLOCK[comp, D_GIMX] = gimx
    BLOCK[comp, D_GIMY] = gimy
    BLOCK[comp, D_GIMZ] = gimz
    BLOCK[comp, D_GIPX] = gipx
    BLOCK[comp, D_GIPY] = gipy
    BLOCK[comp, D_GIPZ] = gipz
    BLOCK[comp, D_CMX] = cmx
    BLOCK[comp, D_CMY] = cmy
    BLOCK[comp, D_CMZ] = cmz
    BLOCK[comp, D_CPX] = cpx
    BLOCK[comp, D_CPY] = cpy
    BLOCK[comp, D_CPZ] = cpz
    BLOCK[comp, D_CGX] = cgx
    BLOCK[comp, D_CGY] = cgy
    BLOCK[comp, D_CGZ] = cgz
    BLOCK[comp, D_MATIMP] = mat_imp
    BLOCK[comp, D_DP] = DP_A[0]
    BLOCK[comp, D_TICK] = float(TICK[0])
    BLOCK[comp, D_STATUS] = STATUS_OK
    BLOCK[comp, D_SUBCLOSE] = subclose
    BLOCK[comp, D_RECIP] = norm3_seq(rx, ry, rz)
    BLOCK[comp, D_WSG] = w_sg
    BLOCK[comp, D_SGIMPX] = sgx
    BLOCK[comp, D_SGIMPY] = sgy
    BLOCK[comp, D_SGIMPZ] = sgz
    BLOCK[comp, D_BHERR] = BHERR[comp]
    BLOCK[comp, D_BHRMS] = BHRMS[comp]
    BLOCK[comp, D_BHDIR] = BHDIR[comp]
    BLOCK[comp, D_PROJDMX] = pdmx
    BLOCK[comp, D_PROJDMY] = pdmy
    BLOCK[comp, D_PROJDMZ] = pdmz
    BLOCK[comp, D_ANCHORRES] = anres
    BLOCK[comp, D_PROJDPLATE] = norm3_seq(pdplx, pdply, pdplz)
    d = 0.0
    for i in range(DIAG):
        if i != D_DIGEST:
            d = (d * 1.0000000000000002 + BLOCK[comp, i] * (i + 1)) \
                % 1000000007.0
    d = (d + float(TICK[0]) * 7919.0) % 1000000007.0
    BLOCK[comp, D_DIGEST] = d


# ===========================================================================
# the resident world (host orchestration; MirrorWorld's device twin)
# ===========================================================================

class ResidentGpuWorld:
    """GPU-resident executor of M07's declared step. All physical state
    lives in device arrays from construction to release; the host submits
    the bounded command block (dp, h, alpha: 96 B/tick) and reads the
    bounded diagnostic block (96 f64 per component = 768 B/tick)."""

    def __init__(self, components, dt_s=DT_S, gravity=True, far_field=False):
        require(len(components) >= 1, 'world_components_invalid')
        self.dt_s = float(dt_s)
        self.gravity = bool(gravity)
        self.far_field = bool(far_field)
        self.tick = 0
        self.host_bytes_up = 0
        self.host_bytes_down = 0
        self.snapshots = {}
        comps = components
        self._host_components = list(components)
        self.n_comp = len(comps)
        c0 = comps[0]
        self.n_vert = c0.x.shape[0]
        self.n_tri = c0.membrane.triangles.shape[0]
        self.k_el, self.c_el = (float(v) for v in c0.maxwell_element())
        x = np.empty((self.n_comp * self.n_vert, 3))
        v = np.zeros_like(x)
        masses = np.empty(self.n_comp * self.n_vert)
        for ci, c in enumerate(comps):
            x[ci * self.n_vert:(ci + 1) * self.n_vert] = c.x
            v[ci * self.n_vert:(ci + 1) * self.n_vert] = c.v
            masses[ci * self.n_vert:(ci + 1) * self.n_vert] = c.masses
        self.d_x = cuda.to_device(np.ascontiguousarray(x))
        self.d_v = cuda.to_device(np.ascontiguousarray(v))
        self.d_v_pre = cuda.device_array_like(self.d_v)
        self.d_x_pre = cuda.device_array_like(self.d_x)
        self.d_masses = cuda.to_device(np.ascontiguousarray(masses))
        self.d_inv_m = cuda.to_device(
            np.ascontiguousarray(1.0 / masses))
        tris = np.stack([np.asarray(c.membrane.triangles) for c in comps])
        self.d_tris = cuda.to_device(np.ascontiguousarray(tris,
                                                          dtype=np.int64))
        edges = np.stack([np.asarray(_edge_list(c)) for c in comps])
        self.d_edges = cuda.to_device(np.ascontiguousarray(edges,
                                                           dtype=np.int64))
        rest = np.stack([np.asarray(_rest_lengths(c)) for c in comps])
        self.d_rest = cuda.to_device(np.ascontiguousarray(rest))
        self.d_px = cuda.to_device(np.ascontiguousarray(
            np.stack([c.plate.x for c in comps])))
        self.d_pv = cuda.to_device(np.ascontiguousarray(
            np.stack([c.plate.velocity for c in comps])))
        self.d_pv_pre = cuda.device_array_like(self.d_pv)
        self.d_pmass = cuda.to_device(np.ascontiguousarray(
            np.array([c.plate.mass_kg for c in comps])))
        self.d_gx = cuda.to_device(np.ascontiguousarray(
            np.stack([c.ground.x for c in comps])))
        port_mass = np.stack([np.asarray(_port_masses(c)) for c in comps])
        self.d_port_mass = cuda.to_device(
            np.ascontiguousarray(port_mass))
        sc = np.zeros((self.n_comp, 10))
        for ci, c in enumerate(comps):
            sc[ci, 0] = c.F
            sc[ci, 1] = c.U_mat
            sc[ci, 2] = c.Q_mat
            sc[ci, 3] = c.W_in_mat
        self.d_sc = cuda.to_device(sc)
        self.d_pass = cuda.device_array((self.n_comp, 4, N_PASS),
                                        dtype=np.float64)
        self.d_vstart = cuda.device_array_like(self.d_v)
        self.d_pvstart = cuda.device_array_like(self.d_pv)
        self.d_e_prev = cuda.device_array(self.n_comp, dtype=np.float64)
        self.d_umat_prev = cuda.device_array(self.n_comp, dtype=np.float64)
        self.d_us_prev = cuda.device_array(self.n_comp, dtype=np.float64)
        self.d_ftri = cuda.device_array((self.n_comp, self.n_tri, 3),
                                        dtype=np.float64)
        self.d_areas = cuda.device_array((self.n_comp, self.n_tri),
                                         dtype=np.float64)
        self.d_loads = cuda.device_array_like(self.d_x)
        self.d_gloads = cuda.device_array_like(self.d_x)
        self.d_glh = cuda.device_array_like(self.d_x)
        adj_off, adj_val = _lumping_adjacency(c0, self.n_comp)
        self.d_adj_off = cuda.to_device(adj_off)
        self.d_adj_val = cuda.to_device(adj_val)
        self.d_dp = cuda.to_device(np.zeros(1))
        self.d_h = cuda.to_device(np.array([self.dt_s / N_SUB]))
        self.d_grav = cuda.to_device(np.array(
            [0.0, 0.0, -G_M_S2 * (1.0 if self.gravity else 0.0)]))
        self.d_k = cuda.to_device(np.array([self.k_el]))
        self.d_c = cuda.to_device(np.array([self.c_el]))
        self.d_alpha = cuda.to_device(np.array([1.0]))
        self.d_tick = cuda.to_device(np.zeros(1, dtype=np.int64))
        self.d_bherr = cuda.to_device(np.zeros(self.n_comp))
        self.d_bhrms = cuda.to_device(np.zeros(self.n_comp))
        self.d_bhdir = cuda.to_device(np.zeros(self.n_comp))
        self.d_diag = cuda.device_array((self.n_comp, DIAG), dtype=np.float64)
        self.h_diag = np.zeros((self.n_comp, DIAG))
        self.inv2c = 1.0 / (2.0 * XPBD_COMPLIANCE)
        self.bh = None
        if self.far_field:
            from resident_bh import ResidentBH
            self.bh = ResidentBH(self, self._host_components)
        self.declaration = {
            'schema': SCHEMA,
            'order': list(iw.DECLARED_ORDER),
            'dt_s': self.dt_s,
            'substeps_per_tick': N_SUB,
            'far_field': self.far_field,
            'telemetry_f64_per_comp': DIAG,
            'cmd_f64': CMD_F64,
        }
        self.order_digest = sha_digest(self.declaration)

    # -- the single writer ------------------------------------------------
    def step_tick(self, tick, dp_pa):
        require(tick == self.tick, E_TICK)
        require(tuple(self.declaration['order'])
                == ('pressure', 'material', 'contact'), E_ORDER)
        n = self.n_comp
        h = self.dt_s / N_SUB
        k_reset[n, 1](self.d_v, self.d_pv, self.d_sc, self.d_vstart,
                      self.d_pvstart, self.d_pass, self.d_x, self.d_edges,
                      self.d_rest, self.d_masses, self.d_pmass, self.inv2c,
                      self.d_e_prev, self.d_umat_prev, self.d_us_prev)
        for sub in range(N_SUB):
            # bounded command block (host -> device): dp, h, alpha
            alpha = math.exp(-h / (self.c_el / self.k_el))
            self.d_dp.copy_to_device(np.array([float(dp_pa)]))
            self.d_h.copy_to_device(np.array([h]))
            self.d_alpha.copy_to_device(np.array([alpha]))
            self.host_bytes_up += 24
            k_pressure_geometry[((n * N_TRI + 63) // 64, 1), 64](
                self.d_x, self.d_tris, self.d_dp, self.d_ftri, self.d_areas)
            k_pressure_lump_velocity[n, 64](
                self.d_v, self.d_v_pre, self.d_loads, self.d_gloads,
                self.d_glh, self.d_masses, self.d_inv_m, self.d_adj_off,
                self.d_adj_val, self.d_ftri, self.d_grav, self.d_h)
            k_pressure_plate[n, 1](self.d_pv, self.d_pv_pre, self.d_pmass,
                                   self.d_grav, self.d_h, self.d_pass, sub)
            k_pressure_diag_sub[n, 1](
                self.d_v, self.d_v_pre, self.d_loads, self.d_gloads,
                self.d_glh, self.d_h, self.d_pass, sub)
            k_material[n, 1](self.d_sc, self.d_pv, self.d_alpha, self.d_k,
                             self.d_c, self.d_h, self.d_pmass, self.d_pass,
                             sub)
            k_contact[n, 1](self.d_x, self.d_px, self.d_gx, self.d_v,
                            self.d_pv, self.d_tris, self.d_masses,
                            self.d_pmass, self.d_port_mass, self.d_h,
                            self.d_pass, sub)
            if self.bh is not None:
                self.bh.apply(sub)
            k_integrate_mem[((n * N_VERT + 127) // 128, 1), 128](
                self.d_x, self.d_x_pre, self.d_v, self.d_h)
            k_integrate_plate[n, 1](self.d_px, self.d_pv, self.d_h)
            k_xpbd[n, 1](self.d_x, self.d_x_pre, self.d_v, self.d_pv,
                         self.d_edges, self.d_rest, self.d_inv_m,
                         self.d_masses, self.d_pmass, self.d_h, self.d_pass,
                         sub)
        self.d_tick.copy_to_device(np.array([tick], dtype=np.int64))
        self.host_bytes_up += 8
        k_tick_diag[n, 1](self.d_v, self.d_pv, self.d_x, self.d_px,
                          self.d_tris, self.d_edges, self.d_rest,
                          self.d_masses, self.d_pmass, self.d_vstart,
                          self.d_pvstart, self.d_sc, self.d_pass,
                          self.d_e_prev, self.d_umat_prev, self.d_us_prev,
                          self.d_tick, self.d_dp, self.d_bherr, self.d_bhrms,
                          self.d_bhdir, self.d_diag)
        self.tick = tick + 1

    def diagnostics(self):
        """Bounded async diagnostic read: exactly the per-component 96-f64
        blocks — the steady-state telemetry."""
        self.d_diag.copy_to_host(self.h_diag)
        self.host_bytes_down += self.d_diag.nbytes
        return self.h_diag

    def check_gates(self, block):
        """Host-side named refusals (the declared gates)."""
        require(int(block[D_ACTIVE]) <= MAX_ACTIVE, E_PAIRCAP)
        require(block[D_GSRES] <= GS_TOL_N_S, E_CONV)
        require(block[D_MINVN] >= -1e-9, E_SEPARATION)
        require(block[D_STICK] <= 1e-9, E_STICK)
        require(block[D_RECIP] <= 1e-12, E_RECIPOCITY)
        require(block[D_ANCHORRES] <= 1e-12, E_ANCHOR)
        require(block[D_PROJDPLATE] <= 1e-12, E_MOMENTUM)
        require(block[D_SUBCLOSE] <= 1e-9, E_SUBLEDGER)
        require(abs(block[D_RESID]) <= block[D_BOUND], E_UNEXPLAINED)
        if self.far_field:
            require(block[D_BHERR] <= BH_ERROR_WINDOW, E_BH)

    def snapshot(self, tick):
        """Declared async snapshot consumer (capture ticks only)."""
        x = self.d_x.copy_to_host()
        px = self.d_px.copy_to_host()
        self.host_bytes_down += x.nbytes + px.nbytes
        self.snapshots[tick] = {
            'membrane_positions_m':
                x[:self.n_vert].tolist(),
            'plate_vertices_m': px[0].tolist(),
        }
        return self.snapshots[tick]

    def release(self):
        for name in [a for a in dir(self) if a.startswith('d_')]:
            delattr(self, name)
        self.h_diag = None
        if self.bh is not None:
            self.bh.release()


# ---- host-side topology helpers (construction only; never per tick) --------

def _edge_list(comp):
    edges = {}
    for a, b, c in comp.membrane.triangles.tolist():
        for u, w in ((a, b), (b, c), (c, a)):
            edges[(min(u, w), max(u, w))] = True
    return sorted(edges)


def _rest_lengths(comp):
    return [float(np.linalg.norm(comp.rest[b] - comp.rest[a]))
            for a, b in _edge_list(comp)]


def _port_masses(comp):
    return [comp.masses[list(t)].sum() for t in comp.membrane.triangles]


def _lumping_adjacency(comp, n_comp=1):
    """Per vertex (component-tiled, flat): slot-0 tris ascending, then
    slot-1, then slot-2 (exactly np.add.at's accumulation order); the
    packed value carries the component-offset triangle index."""
    tris = np.asarray(comp.membrane.triangles)
    n_vert = comp.membrane.vertices.shape[0]
    n_tri = tris.shape[0]
    adj = [[] for _ in range(n_comp * n_vert)]
    for ci in range(n_comp):
        for slot in range(3):
            for ti in range(n_tri):
                adj[ci * n_vert + int(tris[ti, slot])].append(
                    ((ti + ci * n_tri) << 2) | slot)
    adj_val = []
    adj_off = [0]
    for lst in adj:
        adj_val.extend(lst)
        adj_off.append(len(adj_val))
    return (np.array(adj_off, dtype=np.int64),
            np.array(adj_val, dtype=np.int64))
