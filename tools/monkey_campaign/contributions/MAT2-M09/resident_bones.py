"""MAT2-M09: the two-bone assembly world on RESIDENT GPU state (CUDA).

This module is the mechanical CUDA transcription of kernel_mirror.py, whose
logic is validated BITWISE against the sealed M09 oracle (assembly.py) on
the frozen 90-tick fixture (see mirror_rehearsal.py; Amendment A2, worst
difference 0.0). The GPU world keeps ALL physical state in device arrays
from construction to release; the host submits the bounded 5-f64 command
block (tick, per-vertex actuator x-load on bone_b, damping, bind, release
= 40 B/tick) and reads the bounded per-bone 96-f64 diagnostic block plus
the 16-row vertex snapshot (1920 B/tick = 960 B per component, inside the
1024 B/component/tick budget). No per-tick state roundtrip exists. See
PREREGISTRATION.md for the frozen statement, windows and the X3 clause.

Declared layout (fixed by kernel_mirror.py, the single transcription
source): flat 16-row state X/V (bone_a rows 0..7, bone_b 8..15); the
pinned ground is a static constant table (4 verts, 2 tris); 26 contact
entries (12+12 bone triangle ports, then the 2 ground triangles);
per-bone/per-substep partials PASS[2,4,18] (slots P_*) and system
per-substep slots SYS[4,31] (slots S_*); per-bone 96-f64 diagnostic block
(slots D_*; the system scalars live in component 0's block); the
declared-order block_digest chain folded on device every tick.

Numerics law: float64; no float atomics; no RNG; no wall-clock in results;
per-element arithmetic mirrors the oracle's numpy expression order;
recorded sums use numpy's pairwise/block reduction order (the npsum
helper; pairwise-8 per column) or the declared sequential loop order; the
only transcendentals are the norm sqrts and the digest fmod. Refusals are
named codes. Upstream authority unchanged: M09 kernel_mirror + pins.
"""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np
from numba import cuda

HERE = pathlib.Path(__file__).resolve().parent
CONTRIB = HERE.parent
for _p in (str(HERE), str(CONTRIB / 'MAT2-M01'), str(CONTRIB / 'MAT2-M03'),
           str(CONTRIB / 'MAT2-M05'), str(CONTRIB / 'MAT2-M06')):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import assembly as asm  # noqa: E402  (the sealed CPU oracle; constants)

# ---- frozen constants (kernel_mirror.py is the single transcription source) --
from kernel_mirror import (  # noqa: E402
    N_BONES, N_VERT, N_TRI, N_EDGES, NV, N_ENTRIES, N_SUB, DT_S, H_SUB,
    GS_TOL_N_S, GS_CAP, XPBD_TOL_M, XPBD_ITERATIONS_CAP, XPBD_COMPLIANCE,
    THICKNESS_M, CONTACT_MARGIN_M, CCD_TOL_M, BETA_OVER_DT, SLOP_M, MU_TINY,
    RESTITUTION, G_M_S2, TICKS, MAX_ACTIVE, CMD_F64,
    D_KE, D_USCAFF, D_COMX, D_COMY, D_COMZ, D_MAXSPD, D_MINZ, D_GAP, D_JGAP,
    D_JNX, D_JNY, D_JNZ, D_JJN, D_ACTIVE, D_ITERS, D_GSRES, D_JNTOT, D_DFRIC,
    D_DIMP, D_WCKE, D_WACT, D_WLIG, D_WCAP, D_WGRAV, D_QDAMP, D_QCONTACT,
    D_QPROJ, D_EDISS, D_RESID, D_BOUND, D_EMECH, D_LIGT, D_LIGFX, D_LIGFY,
    D_LIGFZ, D_LIGEXT, D_CAPAX, D_CAPFX, D_CAPFY, D_CAPFZ, D_ULIG, D_UCAP,
    D_LIGBOUND, D_CAPBOUND, D_REST00, D_REST01, D_REST02, D_REST10, D_REST11,
    D_REST12, D_REST20, D_REST21, D_REST22, D_LEDGERW, D_ANCHORERR, D_GIMPX,
    D_GIMPY, D_GIMPZ, D_GJNA, D_GJNB, D_RECIP, D_TICK, D_STATUS, D_DIGEST,
    P_WGRAV, P_QDAMP, P_IMPGX, P_IMPGY, P_IMPGZ, P_DMPX, P_DMPY, P_DMPZ,
    P_WLIG, P_WCAP, P_WACT, P_ELMX, P_ELMY, P_ELMZ, P_CIMPX, P_CIMPY,
    P_CIMPZ, P_LEDGER,
    S_QCONTACT, S_DFRIC, S_DIMP, S_JNTOT, S_ITERS, S_GSRES, S_ACTIVE, S_JGAP,
    S_JHAS, S_JNX, S_JNY, S_JNZ, S_JJN, S_GJNA, S_GJNB, S_BBIX, S_BBIY,
    S_BBIZ, S_CAX, S_CAY, S_CAZ, S_CBX, S_CBY, S_CBZ, S_CGX, S_CGY, S_CGZ,
    S_RECX, S_RECY, S_RECZ, S_QPROJ,
    E_ORDER, E_TICK, E_BYTES, block_digest, sha_digest, require)

# element law constants live on the oracle module (assembly.py)
LIG_REST_LENGTH_M = asm.LIG_REST_LENGTH_M
LIG_K_T_N_PER_M = asm.LIG_K_T_N_PER_M
LIG_K_S_N_PER_M = asm.LIG_K_S_N_PER_M
CAP_K_C_N_PER_M = asm.CAP_K_C_N_PER_M
CAP_K_S_N_PER_M = asm.CAP_K_S_N_PER_M

SCHEMA = 'chimera.m09_resident_bones.v1'
DIAG = 96
N_PASS = 18
N_SYS = 31
NM_CAND = 192               # cross-body candidate bound (12*12 + 24 + 24)

STATUS_OK = 0.0
STATUS_PAIRCAP = 102.0

E_CONV = 'convergence_gate_not_met'
E_LEDGER = 'ledger_imbalance'
E_SUPPORT = 'support_lost_or_hidden'
E_UNEXPLAINED = 'unexplained_energy'
E_NONFINITE = 'nonfinite_state'
E_DIGEST = 'digest_chain_stale'
E_PAIRCAP = 'contact_pair_slot_overflow'

TELEMETRY_BUDGET_UP_PER_TICK = 256
TELEMETRY_BUDGET_DOWN_PER_COMP = 1024

BONE_MU_S, BONE_MU_K = asm.BONE_MU
GROUND_MU_S, GROUND_MU_K = asm.GROUND_MU
PRESS_LOADER_X = (asm.PRESS_FORCE_N / 8.0) * -1.0
PULL_LOADER_X = asm.PULL_FORCE_N / 8.0

DIGEST_MULT = 1.0000000000000002
DIGEST_MOD = 1000000007.0
RELEASE_TICK_F = float(asm.RELEASE_TICK)   # device-side release comparison


def actuator_x_of(tick):
    """The per-vertex actuator x-load on bone_b (assembly._actuator_load)."""
    if tick in asm.PRESS_TICKS:
        return PRESS_LOADER_X
    if tick in asm.PULL_TICKS:
        return PULL_LOADER_X
    return 0.0


# ===========================================================================
# device helpers (transcribed from kernel_mirror / numpy semantics)
# ===========================================================================
#
# Shape-literal law (measured on hardware, m09-gmain-001): numba CUDA
# typing requires cuda.local.array shapes to be INTEGER LITERALS - a
# BinOp of freevar constants (N_VERT * 3) types as plain int64 and the
# overload refuses it (TypingError before any tick runs). The literals
# below are pinned to the declared constants by
# p_bone_local_array_literals (8=N_VERT, 24=N_VERT*3=N_EDGES, 26=
# N_ENTRIES, 192=NM_CAND, 128=MAX_ACTIVE).

@cuda.jit(device=True, inline=True)
def norm3_seq(x, y, z):
    """np.linalg.norm of a 3-vector: sequential dot, then sqrt."""
    t = x * x + y * y
    t = t + z * z
    return math.sqrt(t)


@cuda.jit(device=True, inline=True)
def npsum(a, n):
    """numpy ndarray.sum() pairwise order (n<8 sequential from 0.0, else
    the 8-accumulator blocked scheme with sequential remainder; n == 8
    folds as ((r0+r1)+(r2+r3))+((r4+r5)+(r6+r7)))."""
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
def sum8_col(A, base, c):
    """numpy (8,3) .sum(axis=0) per column: pairwise-8 over the 8 rows."""
    r0 = A[base + 0, c]; r1 = A[base + 1, c]
    r2 = A[base + 2, c]; r3 = A[base + 3, c]
    r4 = A[base + 4, c]; r5 = A[base + 5, c]
    r6 = A[base + 6, c]; r7 = A[base + 7, c]
    return ((r0 + r1) + (r2 + r3)) + ((r4 + r5) + (r6 + r7))


@cuda.jit(device=True, inline=True)
def mass_diff_col8(A_new, base_new, A_old, base_old, c, MASSES, bone, out):
    """out[r] = MASSES[bone, r] * (A_new - A_old) per column (the operand
    order of the mirror's per-column momentum-delta folds)."""
    for r in range(N_VERT):
        out[r] = MASSES[bone, r] * (A_new[base_new + r, c]
                                    - A_old[base_old + r, c])


@cuda.jit(device=True, inline=True)
def entry_body(e):
    """0 = bone_a triangle port, 1 = bone_b triangle port, 2 = ground."""
    return 0 if e < N_TRI else (1 if e < 2 * N_TRI else 2)


@cuda.jit(device=True, inline=True)
def entry_tri_verts(e, X, GX, TRIS, GTRI, out):
    """The entry's triangle vertices (out is (3,3)); bone rows are flat."""
    if e < 2 * N_TRI:
        b = 0 if e < N_TRI else 1
        t = e - b * N_TRI
        base = b * N_VERT
        for r in range(3):
            v = TRIS[b, t, r] + base
            out[r, 0] = X[v, 0]; out[r, 1] = X[v, 1]; out[r, 2] = X[v, 2]
    else:
        g = e - 2 * N_TRI
        for r in range(3):
            v = GTRI[g, r]
            out[r, 0] = GX[v, 0]; out[r, 1] = GX[v, 1]; out[r, 2] = GX[v, 2]


@cuda.jit(device=True, inline=True)
def port_velocity(e, V, TRIS, out):
    """Port velocity: ((v0 + v1) + v2) / 3 over the triangle's vertices;
    the pinned ground reads zeros."""
    if e < 2 * N_TRI:
        b = 0 if e < N_TRI else 1
        t = e - b * N_TRI
        base = b * N_VERT
        v0 = TRIS[b, t, 0] + base
        v1 = TRIS[b, t, 1] + base
        v2 = TRIS[b, t, 2] + base
        for c in range(3):
            out[c] = ((V[v0, c] + V[v1, c]) + V[v2, c]) / 3.0
    else:
        out[0] = 0.0; out[1] = 0.0; out[2] = 0.0


@cuda.jit(device=True, inline=True)
def set_port_velocity(e, V, TRIS, wx, wy, wz):
    """The port velocity setter: delta = value - mean3(current); every
    vertex of the triangle receives the same delta. Pinned ground: the
    declared no-op."""
    if e >= 2 * N_TRI:
        return
    b = 0 if e < N_TRI else 1
    t = e - b * N_TRI
    base = b * N_VERT
    v0 = TRIS[b, t, 0] + base
    v1 = TRIS[b, t, 1] + base
    v2 = TRIS[b, t, 2] + base
    for c in range(3):
        mx = (V[v0, c] + V[v1, c]) + V[v2, c]
        mx = mx / 3.0
        if c == 0:
            delta = wx - mx
        elif c == 1:
            delta = wy - mx
        else:
            delta = wz - mx
        V[v0, c] += delta
        V[v1, c] += delta
        V[v2, c] += delta


@cuda.jit(device=True, inline=True)
def port_inv_mass(e, MASSES, TRIS):
    """GroundPort.inv_mass() = 0.0; bone port = 1 / (m0 + m1 + m2)."""
    if e >= 2 * N_TRI:
        return 0.0
    b = 0 if e < N_TRI else 1
    t = e - b * N_TRI
    m0 = MASSES[b, TRIS[b, t, 0]]
    m1 = MASSES[b, TRIS[b, t, 1]]
    m2 = MASSES[b, TRIS[b, t, 2]]
    return 1.0 / ((m0 + m1) + m2)


@cuda.jit(device=True, inline=True)
def pair_mu_dev(ba, bb):
    """lc.pair_mu: elementwise min of the two surface declarations."""
    mu_s = 1.0e300
    mu_k = 1.0e300
    for kk in range(2):
        kind = ba if kk == 0 else bb
        if kind == 2:
            if GROUND_MU_S < mu_s:
                mu_s = GROUND_MU_S
            if GROUND_MU_K < mu_k:
                mu_k = GROUND_MU_K
        else:
            if BONE_MU_S < mu_s:
                mu_s = BONE_MU_S
            if BONE_MU_K < mu_k:
                mu_k = BONE_MU_K
    return mu_s, mu_k


@cuda.jit(device=True, inline=True)
def tri_area_now_dev(b, t, X, TRIS):
    """pm.Membrane.areas[t] for the bone's CURRENT shape: 0.5 * |cross|."""
    base = b * N_VERT
    i0 = TRIS[b, t, 0] + base
    i1 = TRIS[b, t, 1] + base
    i2 = TRIS[b, t, 2] + base
    e1x = X[i1, 0] - X[i0, 0]; e1y = X[i1, 1] - X[i0, 1]
    e1z = X[i1, 2] - X[i0, 2]
    e2x = X[i2, 0] - X[i0, 0]; e2y = X[i2, 1] - X[i0, 1]
    e2z = X[i2, 2] - X[i0, 2]
    cx = e1y * e2z - e1z * e2y
    cy = e1z * e2x - e1x * e2z
    cz = e1x * e2y - e1y * e2x
    return 0.5 * norm3_seq(cx, cy, cz)


@cuda.jit(device=True, inline=True)
def distribute_to_head_dev(b, fx, fy, fz, X, TRIS, HEAD_VIDS, out):
    """BoneBody.distribute_to_head: split across the two head triangles by
    CURRENT area share with the exact complement on the second share, then
    equal thirds per triangle, accumulating in the declared triangle
    order."""
    a0 = tri_area_now_dev(b, 0, X, TRIS)
    a1 = tri_area_now_dev(b, 1, X, TRIS)
    total = a0 + a1
    share0x = fx * (a0 / total)
    share0y = fy * (a0 / total)
    share0z = fz * (a0 / total)
    share1x = fx - share0x
    share1y = fy - share0y
    share1z = fz - share0z
    for i in range(N_VERT):
        out[i, 0] = 0.0; out[i, 1] = 0.0; out[i, 2] = 0.0
    for r in range(3):
        vid = HEAD_VIDS[b, 0, r]
        out[vid, 0] += share0x / 3.0
        out[vid, 1] += share0y / 3.0
        out[vid, 2] += share0z / 3.0
    for r in range(3):
        vid = HEAD_VIDS[b, 1, r]
        out[vid, 0] += share1x / 3.0
        out[vid, 1] += share1y / 3.0
        out[vid, 2] += share1z / 3.0


@cuda.jit(device=True, inline=True)
def heads_of(X, REST_ANCHOR, REST_MEAN, h0, h1):
    """head_anchor[b] = rest_head_anchor[b] + (mean(x_b) - rest_mean[b])."""
    for c in range(3):
        m0 = sum8_col(X, 0, c) / 8.0
        m1 = sum8_col(X, N_VERT, c) / 8.0
        h0[c] = REST_ANCHOR[0, c] + (m0 - REST_MEAN[0, c])
        h1[c] = REST_ANCHOR[1, c] + (m1 - REST_MEAN[1, c])


@cuda.jit(device=True, inline=True)
def kinetic_bone(b, V, MASSES, tmp):
    """_kinetic_bone: ((0.5*m) * v**2).sum() over the (8,3) block in
    numpy pairwise order."""
    base = b * N_VERT
    for i in range(N_VERT * 3):
        fl = i // 3
        c = i % 3
        tmp[i] = (0.5 * MASSES[b, fl]) * (V[base + fl, c] * V[base + fl, c])
    return npsum(tmp, N_VERT * 3)


@cuda.jit(device=True, inline=True)
def scaffold_energy_dev(b, X, EDGES, RESTLEN):
    """_scaffold_energy: sequential sum over the declared edge order."""
    base = b * N_VERT
    total = 0.0
    for e in range(N_EDGES):
        a1 = EDGES[b, e, 0] + base
        a2 = EDGES[b, e, 1] + base
        dx = X[a2, 0] - X[a1, 0]
        dy = X[a2, 1] - X[a1, 1]
        dz = X[a2, 2] - X[a1, 2]
        length = norm3_seq(dx, dy, dz)
        diff = length - RESTLEN[b, e]
        total += diff * diff / (2.0 * XPBD_COMPLIANCE)
    return total


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
def tri_tri_closest_dev(TA, TB, best):
    """lc.tri_tri_closest probe order with strict < best selection;
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
        d = norm3_seq(TA[k, 0] - tmp[0], TA[k, 1] - tmp[1],
                      TA[k, 2] - tmp[2])
        if d < bd:
            bd = d
            bpx = TA[k, 0]; bpy = TA[k, 1]; bpz = TA[k, 2]
            bqx = tmp[0]; bqy = tmp[1]; bqz = tmp[2]
    for k in range(3):
        point_tri_closest(TB[k, 0], TB[k, 1], TB[k, 2],
                          TA[0, 0], TA[0, 1], TA[0, 2],
                          TA[1, 0], TA[1, 1], TA[1, 2],
                          TA[2, 0], TA[2, 1], TA[2, 2], tmp)
        d = norm3_seq(TB[k, 0] - tmp[0], TB[k, 1] - tmp[1],
                      TB[k, 2] - tmp[2])
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
            d = norm3_seq(tmp2[0] - tmp2[3], tmp2[1] - tmp2[4],
                          tmp2[2] - tmp2[5])
            if d < bd:
                bd = d
                bpx = tmp2[0]; bpy = tmp2[1]; bpz = tmp2[2]
                bqx = tmp2[3]; bqy = tmp2[4]; bqz = tmp2[5]
    best[0] = bd
    best[1] = bpx; best[2] = bpy; best[3] = bpz
    best[4] = bqx; best[5] = bqy; best[6] = bqz


@cuda.jit(device=True, inline=True)
def solve_contact_dev(ea, eb, gap, nx, ny, nz, V, TRIS, MASSES, imp_out):
    """Statement-level transcription of kernel_mirror.solve_contact_mirror
    (the hash-pinned M06 solve_contact): the normal impulse, then Coulomb
    stick/slip, written through the port setters. Returns (jn, jt_mag,
    mode, m_eff, w_f_ke, vn_pre); imp_out rows = (impulse_on_a,
    impulse_on_b) with impulse_on_b the exact negative."""
    inv_ma = port_inv_mass(ea, MASSES, TRIS)
    inv_mb = port_inv_mass(eb, MASSES, TRIS)
    denom = inv_ma + inv_mb
    m_eff = 1.0 / denom
    va = cuda.local.array(3, dtype=np.float64)
    vb = cuda.local.array(3, dtype=np.float64)
    port_velocity(ea, V, TRIS, va)
    port_velocity(eb, V, TRIS, vb)
    rvx = va[0] - vb[0]; rvy = va[1] - vb[1]; rvz = va[2] - vb[2]
    vn = rvx * nx + rvy * ny + rvz * nz
    vn_pre = vn
    pen = -gap
    bias = BETA_OVER_DT * max(pen - SLOP_M, 0.0)
    jn = max(m_eff * (-(1.0 + RESTITUTION) * vn + bias), 0.0)
    jx = nx * jn; jy = ny * jn; jz = nz * jn
    set_port_velocity(ea, V, TRIS,
                      va[0] + jx * inv_ma, va[1] + jy * inv_ma,
                      va[2] + jz * inv_ma)
    set_port_velocity(eb, V, TRIS,
                      vb[0] - jx * inv_mb, vb[1] - jy * inv_mb,
                      vb[2] - jz * inv_mb)
    port_velocity(ea, V, TRIS, va)
    port_velocity(eb, V, TRIS, vb)
    rvx = va[0] - vb[0]; rvy = va[1] - vb[1]; rvz = va[2] - vb[2]
    vn_after = rvx * nx + rvy * ny + rvz * nz
    tvx = rvx - nx * vn_after
    tvy = rvy - ny * vn_after
    tvz = rvz - nz * vn_after
    vt_pre = norm3_seq(tvx, tvy, tvz)
    mu_s, mu_k = pair_mu_dev(entry_body(ea), entry_body(eb))
    jt_mag = 0.0
    mode = 0
    jtx = 0.0; jty = 0.0; jtz = 0.0
    if vt_pre > MU_TINY:
        jt_req = m_eff * vt_pre
        s_dir = -1.0 / vt_pre
        tdx = tvx * s_dir; tdy = tvy * s_dir; tdz = tvz * s_dir
        if jt_req <= mu_s * jn:
            jt_mag = jt_req
            mode = 1
        else:
            jt_mag = mu_k * jn
            mode = 2
        jtx = tdx * jt_mag; jty = tdy * jt_mag; jtz = tdz * jt_mag
        set_port_velocity(ea, V, TRIS,
                          va[0] + jtx * inv_ma, va[1] + jty * inv_ma,
                          va[2] + jtz * inv_ma)
        set_port_velocity(eb, V, TRIS,
                          vb[0] - jtx * inv_mb, vb[1] - jty * inv_mb,
                          vb[2] - jtz * inv_mb)
    port_velocity(ea, V, TRIS, va)
    port_velocity(eb, V, TRIS, vb)
    rvx = va[0] - vb[0]; rvy = va[1] - vb[1]; rvz = va[2] - vb[2]
    vn2 = rvx * nx + rvy * ny + rvz * nz
    tvx = rvx - nx * vn2
    tvy = rvy - ny * vn2
    tvz = rvz - nz * vn2
    vt_post = norm3_seq(tvx, tvy, tvz)
    w_f_ke = 0.5 * m_eff * max(vt_pre * vt_pre - vt_post * vt_post, 0.0)
    imp_out[0, 0] = jx + jtx; imp_out[0, 1] = jy + jty
    imp_out[0, 2] = jz + jtz
    imp_out[1, 0] = -(jx + jtx); imp_out[1, 1] = -(jy + jty)
    imp_out[1, 2] = -(jz + jtz)
    return jn, jt_mag, mode, m_eff, w_f_ke, vn_pre


# ===========================================================================
# kernels (one per declared stage; all state arrives as arguments)
# ===========================================================================

@cuda.jit
def k_vstart_tick(V, VSTART_TICK):
    """Tick-start velocity snapshot (the mirror's _vstart_tick copies)."""
    gv = cuda.grid(1)
    if gv >= VSTART_TICK.shape[0]:
        return
    for c in range(3):
        VSTART_TICK[gv, c] = V[gv, c]


@cuda.jit
def k_bind(X, REST_ANCHOR, REST_MEAN, BOUND, CAP_REST, EVER_BOUND):
    """The bind act: the capsule's rest length freezes at the CURRENT head
    anchor distance (assembly.AssemblyRun.bind_connections). EVER_BOUND
    records that the elements EXIST from here on: the ligament's geometric
    extension stays a declared measurement even after release (the oracle
    row keeps recording it; only its force/energy go bitwise zero)."""
    h0 = cuda.local.array(3, dtype=np.float64)
    h1 = cuda.local.array(3, dtype=np.float64)
    heads_of(X, REST_ANCHOR, REST_MEAN, h0, h1)
    dx = h1[0] - h0[0]; dy = h1[1] - h0[1]; dz = h1[2] - h0[2]
    CAP_REST[0] = norm3_seq(dx, dy, dz)
    BOUND[0] = 1.0
    EVER_BOUND[0] = 1.0


@cuda.jit
def k_release(X, TRIS, REST_ANCHOR, REST_MEAN, BOUND, CAP_REST, E_RELEASE):
    """The release act: e_release captures BOTH stored energies at the
    release configuration (assembly.AssemblyRun.release_connections)."""
    h0 = cuda.local.array(3, dtype=np.float64)
    h1 = cuda.local.array(3, dtype=np.float64)
    heads_of(X, REST_ANCHOR, REST_MEAN, h0, h1)
    dx = h1[0] - h0[0]; dy = h1[1] - h0[1]; dz = h1[2] - h0[2]
    norm = norm3_seq(dx, dy, dz)
    ax = dx / norm; ay = dy / norm; az = dz / norm
    ddot = dx * ax + dy * ay + dz * az
    sx = dx - ddot * ax; sy = dy - ddot * ay; sz = dz - ddot * az
    sdot = sx * sx + sy * sy + sz * sz
    e_lig = max(0.0, norm - LIG_REST_LENGTH_M)
    u_lig = 0.5 * LIG_K_T_N_PER_M * e_lig * e_lig \
        + 0.5 * LIG_K_S_N_PER_M * sdot
    ext_cap = norm - CAP_REST[0]
    u_cap = 0.5 * CAP_K_C_N_PER_M * ext_cap * ext_cap \
        + 0.5 * CAP_K_S_N_PER_M * sdot
    E_RELEASE[0] = u_lig + u_cap
    BOUND[0] = 0.0


@cuda.jit
def k_stage1_gravity_damp(V, VSTART_SUB, VGRAV, PASS, SUB, H, DAMPING,
                          MASSES, TOTAL_MASS):
    """Stage 1 per bone: gravity (trapezoid work recorded), then the
    declared damping (KE dissipation recorded). One thread per bone; the
    guard compares the grid variable against the PASS dimension it
    indexes."""
    comp = cuda.grid(1)
    if comp >= PASS.shape[0]:
        return
    base = comp * N_VERT
    tmp24 = cuda.local.array(24, dtype=np.float64)
    tmp8 = cuda.local.array(8, dtype=np.float64)
    v0 = cuda.local.array((8, 3), dtype=np.float64)
    vg = cuda.local.array((8, 3), dtype=np.float64)
    dxw = cuda.local.array((8, 3), dtype=np.float64)
    for r in range(N_VERT):
        for c in range(3):
            v0[r, c] = V[base + r, c]
            gc = -G_M_S2 if c == 2 else 0.0
            vg[r, c] = v0[r, c] + gc * H
            dxw[r, c] = (0.5 * (v0[r, c] + vg[r, c])) * H
    for i in range(N_VERT * 3):
        fl = i // 3
        c = i % 3
        gc = -G_M_S2 if c == 2 else 0.0
        tmp24[i] = (MASSES[comp, fl] * gc) * dxw[fl, c]
    w_grav = npsum(tmp24, N_VERT * 3)
    for i in range(N_VERT * 3):
        fl = i // 3
        c = i % 3
        tmp24[i] = (0.5 * MASSES[comp, fl]) * (vg[fl, c] * vg[fl, c])
    kin0 = npsum(tmp24, N_VERT * 3)
    dfac = 1.0 - DAMPING * H
    for r in range(N_VERT):
        for c in range(3):
            V[base + r, c] = vg[r, c] * dfac
    for i in range(N_VERT * 3):
        fl = i // 3
        c = i % 3
        tmp24[i] = (0.5 * MASSES[comp, fl]) * (V[base + fl, c]
                                               * V[base + fl, c])
    kin1 = npsum(tmp24, N_VERT * 3)
    q_damp = kin0 - kin1
    tg = TOTAL_MASS[comp]
    imp_gx = (tg * 0.0) * H
    imp_gy = (tg * 0.0) * H
    imp_gz = (tg * -G_M_S2) * H
    for c in range(3):
        mass_diff_col8(V, base, vg, 0, c, MASSES, comp, tmp8)
        s = npsum(tmp8, N_VERT)
        if c == 0:
            imp_dx = s
        elif c == 1:
            imp_dy = s
        else:
            imp_dz = s
    for r in range(N_VERT):
        for c in range(3):
            VSTART_SUB[comp, SUB, r, c] = v0[r, c]
            VGRAV[comp, SUB, r, c] = vg[r, c]
    PASS[comp, SUB, P_WGRAV] = w_grav
    PASS[comp, SUB, P_QDAMP] = q_damp
    PASS[comp, SUB, P_IMPGX] = imp_gx
    PASS[comp, SUB, P_IMPGY] = imp_gy
    PASS[comp, SUB, P_IMPGZ] = imp_gz
    PASS[comp, SUB, P_DMPX] = imp_dx
    PASS[comp, SUB, P_DMPY] = imp_dy
    PASS[comp, SUB, P_DMPZ] = imp_dz


@cuda.jit
def k_stage2_element_act(X, V, TRIS, MASSES, INVM, REST_ANCHOR, REST_MEAN,
                         HEAD_VIDS, LD, PASS, SUB, H, BOUND, CAP_REST,
                         ACT_X):
    """Stage 2 (one thread): the connective element forces + the bone_b
    actuator load, applied in the declared bone order with trapezoid work
    recorded. Element forces come from the CURRENT resident positions."""
    h0 = cuda.local.array(3, dtype=np.float64)
    h1 = cuda.local.array(3, dtype=np.float64)
    fbl = cuda.local.array(3, dtype=np.float64)
    fbc = cuda.local.array(3, dtype=np.float64)
    lig_ld = cuda.local.array((8, 3), dtype=np.float64)
    cap_ld = cuda.local.array((8, 3), dtype=np.float64)
    ld = cuda.local.array((8, 3), dtype=np.float64)
    v_pre = cuda.local.array((8, 3), dtype=np.float64)
    dxw = cuda.local.array((8, 3), dtype=np.float64)
    tmp24 = cuda.local.array(24, dtype=np.float64)
    tmp8 = cuda.local.array(8, dtype=np.float64)
    heads_of(X, REST_ANCHOR, REST_MEAN, h0, h1)
    dxh = h1[0] - h0[0]; dyh = h1[1] - h0[1]; dzh = h1[2] - h0[2]
    norm = norm3_seq(dxh, dyh, dzh)
    ax = dxh / norm; ay = dyh / norm; az = dzh / norm
    ddot = dxh * ax + dyh * ay + dzh * az
    sx = dxh - ddot * ax; sy = dyh - ddot * ay; sz = dzh - ddot * az
    fbl[0] = 0.0; fbl[1] = 0.0; fbl[2] = 0.0
    fbc[0] = 0.0; fbc[1] = 0.0; fbc[2] = 0.0
    if BOUND[0] == 1.0:
        ext_lig = norm - LIG_REST_LENGTH_M
        t = LIG_K_T_N_PER_M * max(0.0, ext_lig)
        fbl[0] = (-t) * ax - LIG_K_S_N_PER_M * sx
        fbl[1] = (-t) * ay - LIG_K_S_N_PER_M * sy
        fbl[2] = (-t) * az - LIG_K_S_N_PER_M * sz
        ext_cap = norm - CAP_REST[0]
        fc = CAP_K_C_N_PER_M * ext_cap
        fbc[0] = (-fc) * ax - CAP_K_S_N_PER_M * sx
        fbc[1] = (-fc) * ay - CAP_K_S_N_PER_M * sy
        fbc[2] = (-fc) * az - CAP_K_S_N_PER_M * sz
    for b in range(N_BONES):
        if BOUND[0] == 1.0:
            if b == 0:
                distribute_to_head_dev(0, -fbl[0], -fbl[1], -fbl[2], X,
                                       TRIS, HEAD_VIDS, lig_ld)
                distribute_to_head_dev(0, -fbc[0], -fbc[1], -fbc[2], X,
                                       TRIS, HEAD_VIDS, cap_ld)
            else:
                distribute_to_head_dev(1, fbl[0], fbl[1], fbl[2], X,
                                       TRIS, HEAD_VIDS, lig_ld)
                distribute_to_head_dev(1, fbc[0], fbc[1], fbc[2], X,
                                       TRIS, HEAD_VIDS, cap_ld)
        else:
            for r in range(N_VERT):
                lig_ld[r, 0] = 0.0; lig_ld[r, 1] = 0.0; lig_ld[r, 2] = 0.0
                cap_ld[r, 0] = 0.0; cap_ld[r, 1] = 0.0; cap_ld[r, 2] = 0.0
        base = b * N_VERT
        for r in range(N_VERT):
            for c in range(3):
                acc = lig_ld[r, c] + cap_ld[r, c]
                if b == 1:
                    acc = acc + (ACT_X if c == 0 else 0.0)
                ld[r, c] = acc
                v_pre[r, c] = V[base + r, c]
                V[base + r, c] = v_pre[r, c] + (ld[r, c] * INVM[b, r]) * H
        for r in range(N_VERT):
            for c in range(3):
                dxw[r, c] = (0.5 * (v_pre[r, c] + V[base + r, c])) * H
        for i in range(N_VERT * 3):
            fl = i // 3
            c = i % 3
            tmp24[i] = lig_ld[fl, c] * dxw[fl, c]
        w_lig = npsum(tmp24, N_VERT * 3)
        for i in range(N_VERT * 3):
            fl = i // 3
            c = i % 3
            tmp24[i] = cap_ld[fl, c] * dxw[fl, c]
        w_cap = npsum(tmp24, N_VERT * 3)
        w_act = 0.0
        if b == 1:
            for i in range(N_VERT * 3):
                fl = i // 3
                c = i % 3
                actc = ACT_X if c == 0 else 0.0
                tmp24[i] = actc * dxw[fl, c]
            w_act = npsum(tmp24, N_VERT * 3)
        for c in range(3):
            mass_diff_col8(V, base, v_pre, 0, c, MASSES, b, tmp8)
            s = npsum(tmp8, N_VERT)
            if c == 0:
                imp_x = s
            elif c == 1:
                imp_y = s
            else:
                imp_z = s
        for r in range(N_VERT):
            for c in range(3):
                LD[b, SUB, r, c] = ld[r, c]
        PASS[b, SUB, P_WLIG] = w_lig
        PASS[b, SUB, P_WCAP] = w_cap
        PASS[b, SUB, P_WACT] = w_act
        PASS[b, SUB, P_ELMX] = imp_x
        PASS[b, SUB, P_ELMY] = imp_y
        PASS[b, SUB, P_ELMZ] = imp_z


@cuda.jit
def k_contact_stage(X, V, GX, GTRI, TRIS, MASSES, SYS, PASS, SUB, H):
    """Stage 3 (one thread): the declared system-wide sequential contact
    solve — sweep and prune over the 26 inflated entry AABBs, exact
    triangle-triangle closest features, canonical pair order, Gauss-Seidel
    to the declared gate; SYS/PASS partials recorded per substep."""
    ta = cuda.local.array((3, 3), dtype=np.float64)
    tb = cuda.local.array((3, 3), dtype=np.float64)
    lo = cuda.local.array((26, 3), dtype=np.float64)
    hi = cuda.local.array((26, 3), dtype=np.float64)
    centers = cuda.local.array((26, 3), dtype=np.float64)
    order = cuda.local.array(26, dtype=np.int64)
    cand_i = cuda.local.array(192, dtype=np.int64)
    cand_j = cuda.local.array(192, dtype=np.int64)
    act_a = cuda.local.array(128, dtype=np.int64)
    act_b = cuda.local.array(128, dtype=np.int64)
    act_gap = cuda.local.array(128, dtype=np.float64)
    act_nx = cuda.local.array(128, dtype=np.float64)
    act_ny = cuda.local.array(128, dtype=np.float64)
    act_nz = cuda.local.array(128, dtype=np.float64)
    act_jn = cuda.local.array(128, dtype=np.float64)
    act_jt = cuda.local.array(128, dtype=np.float64)
    act_ix = cuda.local.array(128, dtype=np.float64)
    act_iy = cuda.local.array(128, dtype=np.float64)
    act_iz = cuda.local.array(128, dtype=np.float64)
    act_mode = cuda.local.array(128, dtype=np.int64)
    accum_jn = cuda.local.array(128, dtype=np.float64)
    best = cuda.local.array(7, dtype=np.float64)
    imp_out = cuda.local.array((2, 3), dtype=np.float64)
    va = cuda.local.array(3, dtype=np.float64)
    tmpk = cuda.local.array(24, dtype=np.float64)

    motion = 0.0
    for e in range(N_ENTRIES):
        port_velocity(e, V, TRIS, va)
        s = norm3_seq(va[0], va[1], va[2])
        m = s * H
        if m > motion:
            motion = m
    inflate = motion + THICKNESS_M + CONTACT_MARGIN_M
    for e in range(N_ENTRIES):
        entry_tri_verts(e, X, GX, TRIS, GTRI, ta)
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
    # sweep axis: largest center variance (Python-sequential sums; ties
    # resolved to the lowest axis)
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
        kgi = entry_body(ei)
        loi0 = lo[ei, 0]; loi1 = lo[ei, 1]; loi2 = lo[ei, 2]
        hii0 = hi[ei, 0]; hii1 = hi[ei, 1]; hii2 = hi[ei, 2]
        for p2 in range(pos + 1, N_ENTRIES):
            ej = order[p2]
            if lo[ej, axis] > hi[ei, axis]:
                break
            kgj = entry_body(ej)
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
    # narrow phase: canonical pair order (body_a carries the smaller body
    # id) with the declared dist == 0 fallback normals
    nact = 0
    for k in range(ncand):
        e1 = cand_i[k]
        e2 = cand_j[k]
        ba = e1
        bb = e2
        if entry_body(ba) > entry_body(bb):
            ba = e2
            bb = e1
        entry_tri_verts(ba, X, GX, TRIS, GTRI, ta)
        entry_tri_verts(bb, X, GX, TRIS, GTRI, tb)
        tri_tri_closest_dev(ta, tb, best)
        dist = best[0]
        gap = dist - 0.5 * (THICKNESS_M + THICKNESS_M)
        if gap <= CONTACT_MARGIN_M + CCD_TOL_M:
            if dist > 0.0:
                nx = (best[1] - best[4]) / dist
                ny = (best[2] - best[5]) / dist
                nz = (best[3] - best[6]) / dist
            else:
                if entry_body(ba) < 2 and entry_body(bb) < 2:
                    nx = 1.0; ny = 0.0; nz = 0.0
                else:
                    nx = 0.0; ny = 0.0; nz = 1.0
            if nact < MAX_ACTIVE:
                act_a[nact] = ba
                act_b[nact] = bb
                act_gap[nact] = gap
                act_nx[nact] = nx
                act_ny[nact] = ny
                act_nz[nact] = nz
                accum_jn[nact] = 0.0
            nact += 1
    SYS[SUB, S_ACTIVE] = float(nact)
    SYS[SUB, S_ITERS] = 0.0
    SYS[SUB, S_GSRES] = 0.0
    SYS[SUB, S_JHAS] = 0.0
    if nact > MAX_ACTIVE:
        # declared pair-slot overflow path: refuse through the convergence
        # gate (the host's named check); no solve is attempted
        SYS[SUB, S_GSRES] = 1.0e300
        return
    ka_pre = kinetic_bone(0, V, MASSES, tmpk)
    kb_pre = kinetic_bone(1, V, MASSES, tmpk)
    ci_a0 = 0.0; ci_a1 = 0.0; ci_a2 = 0.0
    ci_b0 = 0.0; ci_b1 = 0.0; ci_b2 = 0.0
    ci_g0 = 0.0; ci_g1 = 0.0; ci_g2 = 0.0
    recip_x = 0.0; recip_y = 0.0; recip_z = 0.0
    d_friction = 0.0
    d_impact = 0.0
    jn_total = 0.0
    max_jn = 0.0
    iterations = 0
    for iteration in range(GS_CAP):
        iterations = iteration + 1
        pass_max = 0.0
        for k in range(nact):
            ea = act_a[k]
            eb = act_b[k]
            gap = act_gap[k]
            nx = act_nx[k]; ny = act_ny[k]; nz = act_nz[k]
            jn, jt_mag, mode, m_eff, w_f_ke, vn_pre = solve_contact_dev(
                ea, eb, gap, nx, ny, nz, V, TRIS, MASSES, imp_out)
            jn_abs = jn if jn > 0.0 else -jn
            jt_abs = jt_mag if jt_mag > 0.0 else -jt_mag
            act_jn[k] = jn
            act_jt[k] = jt_mag
            act_mode[k] = mode
            act_ix[k] = imp_out[0, 0]
            act_iy[k] = imp_out[0, 1]
            act_iz[k] = imp_out[0, 2]
            if jn > pass_max:
                pass_max = jn
            if jt_abs > pass_max:
                pass_max = jt_abs
            accum_jn[k] += jn_abs
            kga = entry_body(ea)
            kgb = entry_body(eb)
            if kga == 0:
                ci_a0 += imp_out[0, 0]; ci_a1 += imp_out[0, 1]
                ci_a2 += imp_out[0, 2]
            elif kga == 1:
                ci_b0 += imp_out[0, 0]; ci_b1 += imp_out[0, 1]
                ci_b2 += imp_out[0, 2]
            else:
                ci_g0 += imp_out[0, 0]; ci_g1 += imp_out[0, 1]
                ci_g2 += imp_out[0, 2]
            if kgb == 0:
                ci_a0 += imp_out[1, 0]; ci_a1 += imp_out[1, 1]
                ci_a2 += imp_out[1, 2]
            elif kgb == 1:
                ci_b0 += imp_out[1, 0]; ci_b1 += imp_out[1, 1]
                ci_b2 += imp_out[1, 2]
            else:
                ci_g0 += imp_out[1, 0]; ci_g1 += imp_out[1, 1]
                ci_g2 += imp_out[1, 2]
            recip_x += imp_out[0, 0]
            recip_y += imp_out[0, 1]
            recip_z += imp_out[0, 2]
            recip_x += imp_out[1, 0]
            recip_y += imp_out[1, 1]
            recip_z += imp_out[1, 2]
            d_friction += w_f_ke
            jn_total += jn_abs
            if vn_pre < 0.0:
                d_impact += 0.5 * m_eff * vn_pre * vn_pre
        max_jn = pass_max
        if pass_max <= GS_TOL_N_S:
            break
    ka_post = kinetic_bone(0, V, MASSES, tmpk)
    kb_post = kinetic_bone(1, V, MASSES, tmpk)
    w_contact_ke = -((ka_post + kb_post) - (ka_pre + kb_pre))
    # joint (bone_a vs bone_b) and ground summaries from the FINAL pass,
    # exactly as kernel_mirror._contact_stage folds them
    joint_found = 0.0
    joint_gap = 0.0
    jnx = 0.0; jny = 0.0; jnz = 0.0
    joint_jn = 0.0
    gja = 0.0
    gjb = 0.0
    bbx = 0.0; bby = 0.0; bbz = 0.0
    for k in range(nact):
        bA = entry_body(act_a[k])
        bB = entry_body(act_b[k])
        if bA == 0 and bB == 1:
            joint_found = 1.0
            joint_gap = act_gap[k]
            jnx = act_nx[k]; jny = act_ny[k]; jnz = act_nz[k]
            joint_jn += accum_jn[k]
            bbx += act_ix[k] + (-act_ix[k])
            bby += act_iy[k] + (-act_iy[k])
            bbz += act_iz[k] + (-act_iz[k])
        elif bB == 2:
            if bA == 0:
                gja += accum_jn[k]
            else:
                gjb += accum_jn[k]
    SYS[SUB, S_QCONTACT] = w_contact_ke
    SYS[SUB, S_DFRIC] = d_friction
    SYS[SUB, S_DIMP] = d_impact
    SYS[SUB, S_JNTOT] = jn_total
    SYS[SUB, S_ITERS] = float(iterations)
    SYS[SUB, S_GSRES] = max_jn
    SYS[SUB, S_ACTIVE] = float(nact)
    SYS[SUB, S_JHAS] = joint_found
    SYS[SUB, S_JGAP] = joint_gap
    SYS[SUB, S_JNX] = jnx
    SYS[SUB, S_JNY] = jny
    SYS[SUB, S_JNZ] = jnz
    SYS[SUB, S_JJN] = joint_jn
    SYS[SUB, S_GJNA] = gja
    SYS[SUB, S_GJNB] = gjb
    SYS[SUB, S_BBIX] = bbx
    SYS[SUB, S_BBIY] = bby
    SYS[SUB, S_BBIZ] = bbz
    SYS[SUB, S_CAX] = ci_a0
    SYS[SUB, S_CAY] = ci_a1
    SYS[SUB, S_CAZ] = ci_a2
    SYS[SUB, S_CBX] = ci_b0
    SYS[SUB, S_CBY] = ci_b1
    SYS[SUB, S_CBZ] = ci_b2
    SYS[SUB, S_CGX] = ci_g0
    SYS[SUB, S_CGY] = ci_g1
    SYS[SUB, S_CGZ] = ci_g2
    recip = norm3_seq(recip_x, recip_y, recip_z)
    SYS[SUB, S_RECX] = recip
    SYS[SUB, S_RECY] = recip
    SYS[SUB, S_RECZ] = recip
    PASS[0, SUB, P_CIMPX] = ci_a0
    PASS[0, SUB, P_CIMPY] = ci_a1
    PASS[0, SUB, P_CIMPZ] = ci_a2
    PASS[1, SUB, P_CIMPX] = ci_b0
    PASS[1, SUB, P_CIMPY] = ci_b1
    PASS[1, SUB, P_CIMPZ] = ci_b2


@cuda.jit
def k_ledger(V, VSTART_SUB, VGRAV, LD, MASSES, INVM, PASS, SUB, H, DAMPING):
    """The per-substep momentum ledger over stages 1-3 (one thread per
    bone): m*(v4-v0) == gravity + damping + element/actuator, telescoping
    recorded deltas recomputed from the saved per-substep velocities and
    loads."""
    comp = cuda.grid(1)
    if comp >= PASS.shape[0]:
        return
    base = comp * N_VERT
    dfac = 1.0 - DAMPING * H
    tmp8 = cuda.local.array(8, dtype=np.float64)
    v1 = cuda.local.array((8, 3), dtype=np.float64)
    v2 = cuda.local.array((8, 3), dtype=np.float64)
    v3 = cuda.local.array((8, 3), dtype=np.float64)
    for r in range(N_VERT):
        for c in range(3):
            v1[r, c] = VGRAV[comp, SUB, r, c]
            v2[r, c] = v1[r, c] * dfac
            v3[r, c] = v2[r, c] + (LD[comp, SUB, r, c] * INVM[comp, r]) * H
    worst = 0.0
    for c in range(3):
        gc = -G_M_S2 if c == 2 else 0.0
        for r in range(N_VERT):
            tmp8[r] = MASSES[comp, r] * (gc * H)
        gh = npsum(tmp8, N_VERT)
        for r in range(N_VERT):
            tmp8[r] = MASSES[comp, r] * (v2[r, c] - v1[r, c])
        d21 = npsum(tmp8, N_VERT)
        for r in range(N_VERT):
            tmp8[r] = MASSES[comp, r] * (v3[r, c] - v2[r, c])
        d32 = npsum(tmp8, N_VERT)
        for r in range(N_VERT):
            tmp8[r] = MASSES[comp, r] * (V[base + r, c] - v3[r, c])
        d43 = npsum(tmp8, N_VERT)
        for r in range(N_VERT):
            tmp8[r] = MASSES[comp, r] * (V[base + r, c]
                                         - VSTART_SUB[comp, SUB, r, c])
        d40 = npsum(tmp8, N_VERT)
        err = d40 - (gh + d21 + d32 + d43)
        if err < 0.0:
            err = -err
        if c == 0:
            worst = err
        elif err > worst:
            worst = err
    PASS[comp, SUB, P_LEDGER] = worst


@cuda.jit
def k_stage4_project(X, V, MASSES, EDGES, RESTLEN, INVM, SYS, SUB, H):
    """Stage 4 (one thread): position integration + tolerance-driven XPBD
    per bone in the declared order; the projection's kinetic-energy
    exchange is recorded per substep."""
    tmpk = cuda.local.array(24, dtype=np.float64)
    x_pre = cuda.local.array((8, 3), dtype=np.float64)
    lam = cuda.local.array(24, dtype=np.float64)
    kap = kinetic_bone(0, V, MASSES, tmpk)
    kbp = kinetic_bone(1, V, MASSES, tmpk)
    for b in range(N_BONES):
        base = b * N_VERT
        for r in range(N_VERT):
            for c in range(3):
                x_pre[r, c] = X[base + r, c]
                X[base + r, c] = x_pre[r, c] + V[base + r, c] * H
        alpha_tilde = XPBD_COMPLIANCE / (H * H)
        for e in range(N_EDGES):
            lam[e] = 0.0
        for _it in range(XPBD_ITERATIONS_CAP):
            worst = 0.0
            for e in range(N_EDGES):
                a1 = EDGES[b, e, 0]
                a2 = EDGES[b, e, 1]
                fa1 = a1 + base
                fa2 = a2 + base
                dx = X[fa2, 0] - X[fa1, 0]
                dy = X[fa2, 1] - X[fa1, 1]
                dz = X[fa2, 2] - X[fa1, 2]
                length = norm3_seq(dx, dy, dz)
                if length == 0.0:
                    continue
                gx = dx / length
                gy = dy / length
                gz = dz / length
                cc = length - RESTLEN[b, e]
                if cc < 0.0:
                    ccabs = -cc
                else:
                    ccabs = cc
                if ccabs > worst:
                    worst = ccabs
                w_sum = INVM[b, a1] + INVM[b, a2]
                dlam = (-cc - alpha_tilde * lam[e]) / (w_sum + alpha_tilde)
                lam[e] += dlam
                X[fa1, 0] -= (INVM[b, a1] * dlam) * gx
                X[fa1, 1] -= (INVM[b, a1] * dlam) * gy
                X[fa1, 2] -= (INVM[b, a1] * dlam) * gz
                X[fa2, 0] += (INVM[b, a2] * dlam) * gx
                X[fa2, 1] += (INVM[b, a2] * dlam) * gy
                X[fa2, 2] += (INVM[b, a2] * dlam) * gz
            if worst <= XPBD_TOL_M:
                break
        for r in range(N_VERT):
            for c in range(3):
                V[base + r, c] = (X[base + r, c] - x_pre[r, c]) / H
    kaq = kinetic_bone(0, V, MASSES, tmpk)
    kbq = kinetic_bone(1, V, MASSES, tmpk)
    SYS[SUB, S_QPROJ] = (kap + kbp) - (kaq + kbq)


@cuda.jit
def k_tick_diag(X, V, PASS, SYS, VSTART_TICK, TRIS, EDGES, RESTLEN, MASSES,
                INVM, REST_ANCHOR, REST_MEAN, HEAD_VIDS, CMD, BOUND,
                CAP_REST, E_RELEASE, EVER_BOUND, PREV, HAS_PREV, DIAG_OUT):
    """The declared tick fold (one thread): the interleaved substep-then-
    bone work/damping fold, the sequential SYS folds, the momentum anchor
    identity, the element energies at the end-of-tick configuration, the
    residual bound, both 96-f64 diagnostic blocks and the chained digest.
    System scalars live in component 0's block."""
    tmpk = cuda.local.array(24, dtype=np.float64)
    tmp8 = cuda.local.array(8, dtype=np.float64)
    h0 = cuda.local.array(3, dtype=np.float64)
    h1 = cuda.local.array(3, dtype=np.float64)
    heads_of(X, REST_ANCHOR, REST_MEAN, h0, h1)
    tick = CMD[0]
    bound = BOUND[0] == 1.0
    e_rel = 0.0
    if tick == RELEASE_TICK_F:
        e_rel = E_RELEASE[0]
    # ---- declared interleaved fold (substep-major, bone-minor) ----------
    w_act = 0.0
    w_lig = 0.0
    w_cap = 0.0
    w_grav = 0.0
    q_damp = 0.0
    for s in range(N_SUB):
        for b in range(N_BONES):
            w_grav = w_grav + PASS[b, s, P_WGRAV]
            q_damp = q_damp + PASS[b, s, P_QDAMP]
            w_lig = w_lig + PASS[b, s, P_WLIG]
            w_cap = w_cap + PASS[b, s, P_WCAP]
            w_act = w_act + PASS[b, s, P_WACT]
    # ---- sequential SYS folds (substep order) ---------------------------
    q_contact = 0.0
    d_friction = 0.0
    d_impact = 0.0
    jn_total = 0.0
    q_proj = 0.0
    gs_worst = 0.0
    iters = 0.0
    n_active = 0.0
    joint_found = 0.0
    joint_gap = 0.0
    jnx = 0.0; jny = 0.0; jnz = 0.0
    joint_jn = 0.0
    gja = 0.0
    gjb = 0.0
    bbx = 0.0; bby = 0.0; bbz = 0.0
    ca0 = 0.0; ca1 = 0.0; ca2 = 0.0
    cb0 = 0.0; cb1 = 0.0; cb2 = 0.0
    cg0 = 0.0; cg1 = 0.0; cg2 = 0.0
    recip_worst = 0.0
    for s in range(N_SUB):
        q_contact = q_contact + SYS[s, S_QCONTACT]
        d_friction = d_friction + SYS[s, S_DFRIC]
        d_impact = d_impact + SYS[s, S_DIMP]
        jn_total = jn_total + SYS[s, S_JNTOT]
        if SYS[s, S_GSRES] > gs_worst:
            gs_worst = SYS[s, S_GSRES]
        iters = SYS[s, S_ITERS]
        n_active = SYS[s, S_ACTIVE]
        if SYS[s, S_JHAS] == 1.0:
            joint_found = 1.0
            joint_gap = SYS[s, S_JGAP]
            jnx = SYS[s, S_JNX]
            jny = SYS[s, S_JNY]
            jnz = SYS[s, S_JNZ]
            if SYS[s, S_JJN] > joint_jn:
                joint_jn = SYS[s, S_JJN]
        gja = gja + SYS[s, S_GJNA]
        gjb = gjb + SYS[s, S_GJNB]
        bbx = bbx + SYS[s, S_BBIX]
        bby = bby + SYS[s, S_BBIY]
        bbz = bbz + SYS[s, S_BBIZ]
        ca0 = ca0 + SYS[s, S_CAX]
        ca1 = ca1 + SYS[s, S_CAY]
        ca2 = ca2 + SYS[s, S_CAZ]
        cb0 = cb0 + SYS[s, S_CBX]
        cb1 = cb1 + SYS[s, S_CBY]
        cb2 = cb2 + SYS[s, S_CBZ]
        cg0 = cg0 + SYS[s, S_CGX]
        cg1 = cg1 + SYS[s, S_CGY]
        cg2 = cg2 + SYS[s, S_CGZ]
        q_proj = q_proj + SYS[s, S_QPROJ]
        if SYS[s, S_RECX] > recip_worst:
            recip_worst = SYS[s, S_RECX]
    # ---- per-bone end-of-tick quantities ---------------------------------
    ka = kinetic_bone(0, V, MASSES, tmpk)
    kb = kinetic_bone(1, V, MASSES, tmpk)
    us0 = scaffold_energy_dev(0, X, EDGES, RESTLEN)
    us1 = scaffold_energy_dev(1, X, EDGES, RESTLEN)
    lw0 = 0.0
    lw1 = 0.0
    for s in range(N_SUB):
        if PASS[0, s, P_LEDGER] > lw0:
            lw0 = PASS[0, s, P_LEDGER]
        if PASS[1, s, P_LEDGER] > lw1:
            lw1 = PASS[1, s, P_LEDGER]
    z0 = X[0, 2]
    for r in range(1, N_VERT):
        if X[r, 2] < z0:
            z0 = X[r, 2]
    z1 = X[N_VERT, 2]
    for r in range(1, N_VERT):
        if X[N_VERT + r, 2] < z1:
            z1 = X[N_VERT + r, 2]
    # momentum anchor identity (kernel_mirror's pred_anchor fold)
    imp_ga0 = 0.0; imp_ga1 = 0.0; imp_ga2 = 0.0
    imp_da0 = 0.0; imp_da1 = 0.0; imp_da2 = 0.0
    imp_ea0 = 0.0; imp_ea1 = 0.0; imp_ea2 = 0.0
    imp_gb0 = 0.0; imp_gb1 = 0.0; imp_gb2 = 0.0
    imp_db0 = 0.0; imp_db1 = 0.0; imp_db2 = 0.0
    imp_eb0 = 0.0; imp_eb1 = 0.0; imp_eb2 = 0.0
    for s in range(N_SUB):
        imp_ga0 = imp_ga0 + PASS[0, s, P_IMPGX]
        imp_ga1 = imp_ga1 + PASS[0, s, P_IMPGY]
        imp_ga2 = imp_ga2 + PASS[0, s, P_IMPGZ]
        imp_da0 = imp_da0 + PASS[0, s, P_DMPX]
        imp_da1 = imp_da1 + PASS[0, s, P_DMPY]
        imp_da2 = imp_da2 + PASS[0, s, P_DMPZ]
        imp_ea0 = imp_ea0 + PASS[0, s, P_ELMX]
        imp_ea1 = imp_ea1 + PASS[0, s, P_ELMY]
        imp_ea2 = imp_ea2 + PASS[0, s, P_ELMZ]
        imp_gb0 = imp_gb0 + PASS[1, s, P_IMPGX]
        imp_gb1 = imp_gb1 + PASS[1, s, P_IMPGY]
        imp_gb2 = imp_gb2 + PASS[1, s, P_IMPGZ]
        imp_db0 = imp_db0 + PASS[1, s, P_DMPX]
        imp_db1 = imp_db1 + PASS[1, s, P_DMPY]
        imp_db2 = imp_db2 + PASS[1, s, P_DMPZ]
        imp_eb0 = imp_eb0 + PASS[1, s, P_ELMX]
        imp_eb1 = imp_eb1 + PASS[1, s, P_ELMY]
        imp_eb2 = imp_eb2 + PASS[1, s, P_ELMZ]
    pa0 = 0.0; pa1 = 0.0; pa2 = 0.0
    for c in range(3):
        for r in range(N_VERT):
            tmp8[r] = MASSES[0, r] * (V[r, c] - VSTART_TICK[r, c])
        dvc = npsum(tmp8, N_VERT)
        if c == 0:
            dva0 = dvc
            pa0 = pa0 + ((dva0 - imp_ga0) - imp_da0) - imp_ea0
        elif c == 1:
            dva1 = dvc
            pa1 = pa1 + ((dva1 - imp_ga1) - imp_da1) - imp_ea1
        else:
            dva2 = dvc
            pa2 = pa2 + ((dva2 - imp_ga2) - imp_da2) - imp_ea2
    for c in range(3):
        for r in range(N_VERT):
            tmp8[r] = MASSES[1, r] * (V[N_VERT + r, c]
                                      - VSTART_TICK[N_VERT + r, c])
        dvc = npsum(tmp8, N_VERT)
        if c == 0:
            dvb0 = dvc
            pa0 = pa0 + ((dvb0 - imp_gb0) - imp_db0) - imp_eb0
        elif c == 1:
            dvb1 = dvc
            pa1 = pa1 + ((dvb1 - imp_gb1) - imp_db1) - imp_eb1
        else:
            dvb2 = dvc
            pa2 = pa2 + ((dvb2 - imp_gb2) - imp_db2) - imp_eb2
    pa0 = pa0 - bbx
    pa1 = pa1 - bby
    pa2 = pa2 - bbz
    ae0 = pa0 - (-cg0)
    ae1 = pa1 - (-cg1)
    ae2 = pa2 - (-cg2)
    if ae0 < 0.0:
        ae0 = -ae0
    if ae1 < 0.0:
        ae1 = -ae1
    if ae2 < 0.0:
        ae2 = -ae2
    anchor_err = ae0
    if ae1 > anchor_err:
        anchor_err = ae1
    if ae2 > anchor_err:
        anchor_err = ae2
    # element energies at the end-of-tick configuration
    u_lig = 0.0
    u_cap = 0.0
    lig_t = 0.0
    lig_ex = 0.0
    lig_fx = 0.0; lig_fy = 0.0; lig_fz = 0.0
    cap_ax = 0.0
    cap_fx = 0.0; cap_fy = 0.0; cap_fz = 0.0
    kmat = cuda.local.array((3, 3), dtype=np.float64)
    for ii in range(3):
        for jj in range(3):
            kmat[ii, jj] = 0.0
    dxh = h1[0] - h0[0]; dyh = h1[1] - h0[1]; dzh = h1[2] - h0[2]
    norm = norm3_seq(dxh, dyh, dzh)
    exists = bound or (EVER_BOUND[0] == 1.0)
    if exists:
        # the geometric extension is a MEASUREMENT for as long as the
        # elements exist (bound .. released); the oracle row records it
        # even post-release (only force/energy go bitwise zero)
        lig_ex = norm - LIG_REST_LENGTH_M
    if bound:
        ax = dxh / norm; ay = dyh / norm; az = dzh / norm
        ddot = dxh * ax + dyh * ay + dzh * az
        sx = dxh - ddot * ax; sy = dyh - ddot * ay; sz = dzh - ddot * az
        sdot = sx * sx + sy * sy + sz * sz
        e_lig = max(0.0, lig_ex)
        lig_t = LIG_K_T_N_PER_M * e_lig
        u_lig = 0.5 * LIG_K_T_N_PER_M * e_lig * e_lig \
            + 0.5 * LIG_K_S_N_PER_M * sdot
        lig_fx = (-lig_t) * ax - LIG_K_S_N_PER_M * sx
        lig_fy = (-lig_t) * ay - LIG_K_S_N_PER_M * sy
        lig_fz = (-lig_t) * az - LIG_K_S_N_PER_M * sz
        ext_cap = norm - CAP_REST[0]
        cap_ax = CAP_K_C_N_PER_M * ext_cap
        u_cap = 0.5 * CAP_K_C_N_PER_M * ext_cap * ext_cap \
            + 0.5 * CAP_K_S_N_PER_M * sdot
        cap_fx = (-cap_ax) * ax - CAP_K_S_N_PER_M * sx
        cap_fy = (-cap_ax) * ay - CAP_K_S_N_PER_M * sy
        cap_fz = (-cap_ax) * az - CAP_K_S_N_PER_M * sz
        # restraint matrix (measurement only): k = 0 + k_lig + k_cap,
        # elementwise in the declared order; row-major slots below
        a1d = cuda.local.array(3, dtype=np.float64)
        a1d[0] = ax; a1d[1] = ay; a1d[2] = az
        taut = 1.0 if lig_ex > 0.0 else 0.0
        for ii in range(3):
            for jj in range(3):
                outer = a1d[ii] * a1d[jj]
                eye = 1.0 if ii == jj else 0.0
                kmat[ii, jj] = kmat[ii, jj] \
                    + (LIG_K_T_N_PER_M * taut) * outer \
                    + LIG_K_S_N_PER_M * (eye - outer)
        for ii in range(3):
            for jj in range(3):
                outer = a1d[ii] * a1d[jj]
                eye = 1.0 if ii == jj else 0.0
                kmat[ii, jj] = kmat[ii, jj] \
                    + (CAP_K_C_N_PER_M * 1.0) * outer \
                    + CAP_K_S_N_PER_M * (eye - outer)
    # residual and bound (the declared form)
    kin = ka + kb
    us = us0 + us1
    e_mech = kin + u_lig + u_cap + us
    q_total = q_damp + q_contact + q_proj + e_rel
    w_sum = w_act + w_lig + w_cap + w_grav
    e_prev = 0.0
    if HAS_PREV[0] == 1.0:
        e_prev = PREV[0]
    residual = e_mech - e_prev - w_sum + q_total
    turnover = abs(w_sum) + q_total + kin
    bound_j = 1e-9 + 5e-2 * turnover
    if HAS_PREV[0] == 1.0:
        bound_j = bound_j + (PREV[1] + u_lig + PREV[2] + u_cap
                             + PREV[3] + us)
    if e_rel > 0.0:
        cap_b = max(5e-2 * e_rel, 1e-12)
        if cap_b < bound_j:
            bound_j = cap_b
    # ---- block fill -------------------------------------------------------
    bflag = 1.0 if bound else 0.0
    for b in range(N_BONES):
        base = b * N_VERT
        if b == 0:
            DIAG_OUT[b, D_KE] = ka
            DIAG_OUT[b, D_USCAFF] = us0
            DIAG_OUT[b, D_LEDGERW] = lw0
            DIAG_OUT[b, D_MINZ] = z0
        else:
            DIAG_OUT[b, D_KE] = kb
            DIAG_OUT[b, D_USCAFF] = us1
            DIAG_OUT[b, D_LEDGERW] = lw1
            DIAG_OUT[b, D_MINZ] = z1
        for c in range(3):
            DIAG_OUT[b, D_COMX + c] = sum8_col(X, base, c) / 8.0
        spd = abs(V[base, 0])
        for r in range(N_VERT):
            for c in range(3):
                s = abs(V[base + r, c])
                if s > spd:
                    spd = s
        DIAG_OUT[b, D_MAXSPD] = spd
        DIAG_OUT[b, D_LIGBOUND] = bflag
        DIAG_OUT[b, D_CAPBOUND] = bflag
        DIAG_OUT[b, D_TICK] = tick
        DIAG_OUT[b, D_STATUS] = STATUS_OK
    DIAG_OUT[0, D_GAP] = h1[0] - h0[0]
    DIAG_OUT[0, D_JGAP] = joint_gap
    DIAG_OUT[0, D_JNX] = jnx
    DIAG_OUT[0, D_JNY] = jny
    DIAG_OUT[0, D_JNZ] = jnz
    DIAG_OUT[0, D_JJN] = joint_jn
    DIAG_OUT[0, D_ACTIVE] = n_active
    DIAG_OUT[0, D_ITERS] = iters
    DIAG_OUT[0, D_GSRES] = gs_worst
    DIAG_OUT[0, D_JNTOT] = jn_total
    DIAG_OUT[0, D_DFRIC] = d_friction
    DIAG_OUT[0, D_DIMP] = d_impact
    DIAG_OUT[0, D_WCKE] = q_contact
    DIAG_OUT[0, D_WACT] = w_act
    DIAG_OUT[0, D_WLIG] = w_lig
    DIAG_OUT[0, D_WCAP] = w_cap
    DIAG_OUT[0, D_WGRAV] = w_grav
    DIAG_OUT[0, D_QDAMP] = q_damp
    DIAG_OUT[0, D_QCONTACT] = q_contact
    DIAG_OUT[0, D_QPROJ] = q_proj
    DIAG_OUT[0, D_EDISS] = e_rel
    DIAG_OUT[0, D_RESID] = residual
    DIAG_OUT[0, D_BOUND] = bound_j
    DIAG_OUT[0, D_EMECH] = e_mech
    DIAG_OUT[0, D_LIGT] = lig_t
    DIAG_OUT[0, D_LIGFX] = lig_fx
    DIAG_OUT[0, D_LIGFY] = lig_fy
    DIAG_OUT[0, D_LIGFZ] = lig_fz
    DIAG_OUT[0, D_LIGEXT] = lig_ex
    DIAG_OUT[0, D_CAPAX] = cap_ax
    DIAG_OUT[0, D_CAPFX] = cap_fx
    DIAG_OUT[0, D_CAPFY] = cap_fy
    DIAG_OUT[0, D_CAPFZ] = cap_fz
    DIAG_OUT[0, D_ULIG] = u_lig
    DIAG_OUT[0, D_UCAP] = u_cap
    DIAG_OUT[0, D_REST00] = kmat[0, 0]
    DIAG_OUT[0, D_REST01] = kmat[0, 1]
    DIAG_OUT[0, D_REST02] = kmat[0, 2]
    DIAG_OUT[0, D_REST10] = kmat[1, 0]
    DIAG_OUT[0, D_REST11] = kmat[1, 1]
    DIAG_OUT[0, D_REST12] = kmat[1, 2]
    DIAG_OUT[0, D_REST20] = kmat[2, 0]
    DIAG_OUT[0, D_REST21] = kmat[2, 1]
    DIAG_OUT[0, D_REST22] = kmat[2, 2]
    DIAG_OUT[0, D_ANCHORERR] = anchor_err
    DIAG_OUT[0, D_GIMPX] = -cg0
    DIAG_OUT[0, D_GIMPY] = -cg1
    DIAG_OUT[0, D_GIMPZ] = -cg2
    DIAG_OUT[0, D_GJNA] = gja
    DIAG_OUT[0, D_GJNB] = gjb
    DIAG_OUT[0, D_RECIP] = recip_worst
    DIAG_OUT[0, D_TICK] = tick
    DIAG_OUT[0, D_STATUS] = STATUS_OK
    # ---- declared-order digest chain (D_DIGEST folds as 0.0) -------------
    for b in range(N_BONES):
        d = 0.0
        for i in range(DIAG):
            v = 0.0 if i == D_DIGEST else DIAG_OUT[b, i]
            d = (d * DIGEST_MULT + v * (i + 1)) % DIGEST_MOD
        d = (d + tick * 7919.0) % DIGEST_MOD
        DIAG_OUT[b, D_DIGEST] = d
    # ---- previous-tick reservoirs for the next bound ----------------------
    PREV[0] = e_mech
    PREV[1] = u_lig
    PREV[2] = u_cap
    PREV[3] = us
    HAS_PREV[0] = 1.0


# ===========================================================================
# the resident world (host orchestration; MirrorWorld's device twin)
# ===========================================================================

DIGEST_GATE_TOLERANCE = 1e-9


def digest_matches(block_row, tick):
    """The declared digest-chain gate, in the M08-proven form (measured on
    hardware twice now): the device fold's fused arithmetic can drift the
    host recompute by ~1 ULP (m09-gmain-002: comp0 bit-exact, comp1 off by
    1.1e-16; M08 F3: 9.1e-13 on a ~4.3e3 digest), while a STALE or
    tampered block changes the digest by O(1) — nine orders above the
    tolerance. The tick slot is checked exactly; the folded digest is
    checked within DIGEST_GATE_TOLERANCE relative (floor 1.0)."""
    if int(round(block_row[D_TICK])) != int(tick):
        return False
    want = block_digest(block_row, tick)
    got = float(block_row[D_DIGEST])
    return abs(want - got) <= DIGEST_GATE_TOLERANCE * max(1.0, abs(want))

class ResidentBonesWorld:
    """GPU-resident executor of M09's declared tick. All physical state
    lives in device arrays from construction to release; the host submits
    the bounded 5-f64 command block (40 B/tick) and reads the bounded
    per-bone 96-f64 diagnostic block (1536 B) plus the 16-row vertex
    snapshot (384 B) each tick."""

    def __init__(self):
        require(N_BONES == 2, 'world_components_invalid')
        self.tick = 0
        self.host_bytes_up = 0
        self.host_bytes_down = 0
        tabs = km_tables()
        self._host_components = None
        self.d_x = cuda.to_device(np.ascontiguousarray(tabs['x']))
        self.d_v = cuda.to_device(np.ascontiguousarray(tabs['v']))
        self.d_gx = cuda.to_device(np.ascontiguousarray(tabs['gx']))
        self.d_gtri = cuda.to_device(np.ascontiguousarray(tabs['gtri'],
                                                          dtype=np.int64))
        self.d_tris = cuda.to_device(np.ascontiguousarray(tabs['tris'],
                                                          dtype=np.int64))
        self.d_edges = cuda.to_device(np.ascontiguousarray(tabs['edges'],
                                                           dtype=np.int64))
        self.d_restlen = cuda.to_device(
            np.ascontiguousarray(tabs['restlen']))
        self.d_masses = cuda.to_device(
            np.ascontiguousarray(tabs['masses']))
        self.d_invm = cuda.to_device(np.ascontiguousarray(tabs['invm']))
        self.d_rest_anchor = cuda.to_device(
            np.ascontiguousarray(tabs['rest_anchor']))
        self.d_rest_mean = cuda.to_device(
            np.ascontiguousarray(tabs['rest_mean']))
        self.d_head_vids = cuda.to_device(
            np.ascontiguousarray(tabs['head_vids'], dtype=np.int64))
        self.d_total_mass = cuda.to_device(
            np.ascontiguousarray(tabs['total_mass']))
        # scratch partials and the diagnostic block start ZEROED: the
        # declared digest folds the whole 96-slot row, so the spare slots
        # 64..95 must be declared zeros, never uninitialized memory
        self.d_pass = cuda.to_device(
            np.zeros((N_BONES, N_SUB, N_PASS)))
        self.d_sys = cuda.to_device(np.zeros((N_SUB, N_SYS)))
        self.d_vstart_tick = cuda.device_array((NV, 3), dtype=np.float64)
        self.d_vstart_sub = cuda.device_array((N_BONES, N_SUB, N_VERT, 3),
                                              dtype=np.float64)
        self.d_vgrav = cuda.device_array((N_BONES, N_SUB, N_VERT, 3),
                                         dtype=np.float64)
        self.d_ld = cuda.device_array((N_BONES, N_SUB, N_VERT, 3),
                                      dtype=np.float64)
        self.d_cmd = cuda.to_device(np.zeros(CMD_F64))
        self.d_bound = cuda.to_device(np.zeros(1))
        self.d_ever_bound = cuda.to_device(np.zeros(1))
        self.d_cap_rest = cuda.to_device(np.zeros(1))
        self.d_e_release = cuda.to_device(np.zeros(1))
        self.d_prev = cuda.to_device(np.zeros(4))
        self.d_has_prev = cuda.to_device(np.zeros(1))
        self.d_diag = cuda.to_device(np.zeros((N_BONES, DIAG)))
        self.h_diag = np.zeros((N_BONES, DIAG))
        self.declaration = {
            'schema': SCHEMA,
            'order': list(asm.DECLARED_ORDER),
            'dt_s': DT_S, 'substeps_per_tick': N_SUB, 'ticks': TICKS,
            'n_bones': N_BONES, 'n_vert_per_bone': N_VERT,
            'n_entries': N_ENTRIES, 'max_active': MAX_ACTIVE,
            'diag_f64_per_comp': DIAG, 'cmd_f64': CMD_F64,
            'telemetry_budget_up_bytes_per_tick':
                TELEMETRY_BUDGET_UP_PER_TICK,
            'telemetry_budget_down_bytes_per_comp':
                TELEMETRY_BUDGET_DOWN_PER_COMP,
            'windows': {'position_m': 1e-12, 'scalar_relative': 1e-9},
        }
        self.order_digest = sha_digest(self.declaration)

    # -- the single writer ------------------------------------------------
    def step_tick(self, tick):
        require(tick == self.tick, E_TICK)
        require(tuple(self.declaration['order'])
                == tuple(asm.DECLARED_ORDER), E_ORDER)
        act_x = actuator_x_of(tick)
        damping = asm.damping_of_tick(tick)
        bind_flag = 1.0 if tick == asm.BIND_TICK else 0.0
        release_flag = 1.0 if tick == asm.RELEASE_TICK else 0.0
        self.d_cmd.copy_to_device(np.array([float(tick), act_x, damping,
                                            bind_flag, release_flag]))
        self.host_bytes_up += CMD_F64 * 8
        if bind_flag == 1.0:
            k_bind[(1, 1), (1, 1)](self.d_x,
                                   self.d_rest_anchor, self.d_rest_mean,
                                   self.d_bound, self.d_cap_rest,
                                   self.d_ever_bound)
        if release_flag == 1.0:
            k_release[(1, 1), (1, 1)](self.d_x, self.d_tris,
                                      self.d_rest_anchor, self.d_rest_mean,
                                      self.d_bound, self.d_cap_rest,
                                      self.d_e_release)
        k_vstart_tick[(NV, 1), (1, 1)](self.d_v, self.d_vstart_tick)
        for sub in range(N_SUB):
            k_stage1_gravity_damp[(N_BONES, 1), (1, 1)](
                self.d_v, self.d_vstart_sub, self.d_vgrav, self.d_pass,
                sub, H_SUB, damping, self.d_masses, self.d_total_mass)
            k_stage2_element_act[(1, 1), (1, 1)](
                self.d_x, self.d_v, self.d_tris, self.d_masses,
                self.d_invm, self.d_rest_anchor, self.d_rest_mean,
                self.d_head_vids, self.d_ld, self.d_pass, sub, H_SUB,
                self.d_bound, self.d_cap_rest, act_x)
            k_contact_stage[(1, 1), (1, 1)](
                self.d_x, self.d_v, self.d_gx, self.d_gtri, self.d_tris,
                self.d_masses, self.d_sys, self.d_pass, sub, H_SUB)
            k_ledger[(N_BONES, 1), (1, 1)](
                self.d_v, self.d_vstart_sub, self.d_vgrav, self.d_ld,
                self.d_masses, self.d_invm, self.d_pass, sub, H_SUB,
                damping)
            k_stage4_project[(1, 1), (1, 1)](
                self.d_x, self.d_v, self.d_masses, self.d_edges,
                self.d_restlen, self.d_invm, self.d_sys, sub, H_SUB)
        k_tick_diag[(1, 1), (1, 1)](
            self.d_x, self.d_v, self.d_pass, self.d_sys,
            self.d_vstart_tick, self.d_tris, self.d_edges, self.d_restlen,
            self.d_masses, self.d_invm, self.d_rest_anchor,
            self.d_rest_mean, self.d_head_vids, self.d_cmd, self.d_bound,
            self.d_cap_rest, self.d_e_release, self.d_ever_bound,
            self.d_prev, self.d_has_prev, self.d_diag)
        self.tick = tick + 1

    def diagnostics(self):
        """Bounded async diagnostic read: exactly the per-bone 96-f64
        blocks — the steady-state telemetry."""
        self.d_diag.copy_to_host(self.h_diag)
        self.host_bytes_down += DIAG * 8 * N_BONES
        return self.h_diag

    def snapshot(self):
        """Declared async snapshot consumer (vertex positions, every tick
        under the frozen X3 position window)."""
        x = self.d_x.copy_to_host()
        self.host_bytes_down += NV * 3 * 8
        return x

    def check_gates(self, block, tick):
        """Host-side named refusals (the declared gates; kernel_mirror's
        per-tick requires, transcribed)."""
        require(block[0][D_STATUS] == STATUS_OK, E_PAIRCAP)
        require(block[0][D_GSRES] <= GS_TOL_N_S, E_CONV)
        require(block[0][D_RECIP] <= 1e-12, E_LEDGER)
        require(block[0][D_ANCHORERR] <= 1e-12, E_LEDGER)
        require(max(block[0][D_LEDGERW], block[1][D_LEDGERW]) <= 1e-12,
                E_LEDGER)
        require(min(block[0][D_MINZ], block[1][D_MINZ])
                >= -THICKNESS_M - 2.5e-3, E_SUPPORT)
        require(abs(block[0][D_RESID]) <= block[0][D_BOUND], E_UNEXPLAINED)
        for b in range(N_BONES):
            for v in block[b]:
                require(np.isfinite(v), E_NONFINITE)
            require(digest_matches(block[b], tick), E_DIGEST)

    def release(self):
        # Idempotent teardown. The synchronize() drains every pending
        # async op THIS world enqueued, so a latent fault surfaces here —
        # inside the owning run — instead of going sticky and detonating
        # in the next world that shares the context (M8 lesson). A sync
        # failure is reported to stderr and swallowed: teardown cannot
        # heal a poisoned context, but it must never mask the in-flight
        # exception either.
        if getattr(self, '_released', False):
            return
        self._released = True
        try:
            cuda.synchronize()
        except Exception as exc:  # noqa: BLE001
            print(f'release-sync fault (context suspect): {exc!r}',
                  file=sys.stderr)
        for name in [a for a in dir(self) if a.startswith('d_')]:
            delattr(self, name)
        self.h_diag = None


# ---- host topology tables (construction only; never per tick) --------------

def km_tables():
    """Immutable topology extracted ONCE from the declared BoneBody
    construction (kernel_mirror.TABLES is the authority)."""
    from kernel_mirror import TABLES
    x = np.array([TABLES.rest[0], TABLES.rest[1]],
                 dtype=np.float64).reshape(NV, 3).copy()
    v = np.zeros_like(x)
    gx = np.array(TABLES.ground_verts, dtype=np.float64)
    gtri = np.array(TABLES.ground_tris, dtype=np.int64)
    tris = np.stack([np.asarray(t, dtype=np.int64) for t in TABLES.tris])
    edges = np.stack([np.asarray(e, dtype=np.int64) for e in TABLES.edges])
    restlen = np.stack([np.asarray(r, dtype=np.float64)
                        for r in TABLES.rest_lengths])
    masses = np.stack([np.asarray(m, dtype=np.float64)
                       for m in TABLES.masses])
    invm = np.stack([np.asarray(m, dtype=np.float64)
                     for m in TABLES.inv_masses])
    rest_anchor = np.stack([np.asarray(a, dtype=np.float64)
                            for a in TABLES.rest_head_anchor])
    rest_mean = np.stack([np.asarray(m, dtype=np.float64)
                          for m in TABLES.rest_mean])
    head_vids = np.array([[list(t) for t in tri] for tri in
                          TABLES.head_tri_vids], dtype=np.int64)
    total_mass = np.array([float(m) for m in TABLES.total_mass],
                          dtype=np.float64)
    return {'x': x, 'v': v, 'gx': gx, 'gtri': gtri, 'tris': tris,
            'edges': edges, 'restlen': restlen, 'masses': masses,
            'invm': invm, 'rest_anchor': rest_anchor, 'rest_mean': rest_mean,
            'head_vids': head_vids, 'total_mass': total_mass}
