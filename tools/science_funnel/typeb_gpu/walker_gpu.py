"""walker_gpu.py -- the gait walk's FULL BODY + REFLEX CORE, batched in Warp.

A faithful f64 reimplementation of ChimeraEngine/engine/gait_controller.hpp
(GaitWalker) + coupled_articulation.hpp (Model::evaluate) as a batched
training environment on one CUDA device. The equations are the CPU
reference's; the port is structural (per-env sequential code inside one
kernel per tick). The reference's loud budgets become per-env refusal
classes (the C++ throws Refusal; the GPU env latches refused_class).

FIDELITY SCOPE: see FIDELITY_MANIFEST.md. Deferral sites carry
DEFERRED-Wnn comments. reflex_level=0 runs the body only (the settle/stage-E
hold, no reflexes); reflex_level=1 is the full deterministic core.

Trailer Agent: GLM 5.3.
"""
import numpy as np
import warp as wp
from walker_model import (WalkerSpec, T_CYCLE, DUTY_SAMPLED, TOE_OFF, FS_HZ,
                          ZETA, CAPTURE_PHI, K_TOUCH, K_SLIP, K_RELEASE_BAND,
                          NB, NDRIVE, FOLD_BUDGET_TICKS, UNLOAD_TICKS,
                          SINK_RATE_MAX)

F = wp.float64
Q18 = wp.fixedarray(dtype=wp.float64, shape=18)
M324 = wp.fixedarray(dtype=wp.float64, shape=324)
F16 = wp.fixedarray(dtype=wp.float64, shape=16)
F3 = wp.fixedarray(dtype=wp.float64, shape=3)
F224 = wp.fixedarray(dtype=wp.float64, shape=224)   # 14 bodies x 16
F24 = wp.fixedarray(dtype=wp.float64, shape=24)     # 8 points x 3
F54 = wp.fixedarray(dtype=wp.float64, shape=54)     # 18 axes x 3
F216 = wp.fixedarray(dtype=wp.float64, shape=216)   # 4 reps x 3 comps x 18
F12 = wp.fixedarray(dtype=wp.float64, shape=12)     # 4 reps x 3
F8 = wp.fixedarray(dtype=wp.float64, shape=8)
F180 = wp.fixedarray(dtype=wp.float64, shape=180)   # 10 rows x 18
F10 = wp.fixedarray(dtype=wp.float64, shape=10)
F100 = wp.fixedarray(dtype=wp.float64, shape=100)   # 10x10 gram
I10 = wp.fixedarray(dtype=wp.int32, shape=10)
F36 = wp.fixedarray(dtype=wp.float64, shape=36)
F576 = wp.fixedarray(dtype=wp.float64, shape=576)   # 16 advance frames x 36
H16 = wp.fixedarray(dtype=wp.float64, shape=16)
I16 = wp.fixedarray(dtype=wp.int32, shape=16)
F13 = wp.fixedarray(dtype=wp.float64, shape=13)
I1 = wp.fixedarray(dtype=wp.int32, shape=1)
F1 = wp.fixedarray(dtype=wp.float64, shape=1)

PI = F(3.141592653589793)


# ───────────────────────── small linear algebra ─────────────────────────
@wp.func
def mm(a: F16, b: F16, out: F16):
    for i in range(4):
        for j in range(4):
            s = F(0.0)
            for k in range(4):
                s = s + a[i * 4 + k] * b[k * 4 + j]
            out[i * 4 + j] = s


@wp.func
def rot_axis(axis: F3, ang: F, out: F16):
    c = wp.cos(ang)
    s = wp.sin(ang)
    t = F(1.0) - c
    x = axis[0]; y = axis[1]; z = axis[2]
    out[0] = c + x * x * t; out[1] = x * y * t - z * s; out[2] = x * z * t + y * s; out[3] = F(0.0)
    out[4] = y * x * t + z * s; out[5] = c + y * y * t; out[6] = y * z * t - x * s; out[7] = F(0.0)
    out[8] = z * x * t - y * s; out[9] = z * y * t + x * s; out[10] = c + z * z * t; out[11] = F(0.0)
    out[12] = F(0.0); out[13] = F(0.0); out[14] = F(0.0); out[15] = F(1.0)


@wp.func
def eye16(out: F16):
    for i in range(16):
        out[i] = F(0.0)
    out[0] = F(1.0); out[5] = F(1.0); out[10] = F(1.0); out[15] = F(1.0)


@wp.func
def axial3(m: F16, out: F3):
    out[0] = (m[2 * 4 + 1] - m[1 * 4 + 2]) * F(0.5)
    out[1] = (m[0 * 4 + 2] - m[2 * 4 + 0]) * F(0.5)
    out[2] = (m[1 * 4 + 0] - m[0 * 4 + 1]) * F(0.5)


@wp.func
def apply_point(m: F16, p: F3, out: F3):
    for i in range(3):
        out[i] = m[i * 4 + 0] * p[0] + m[i * 4 + 1] * p[1] + m[i * 4 + 2] * p[2] + m[i * 4 + 3]


@wp.func
def rot_cols(m: F16, v: F3, out: F3):
    for i in range(3):
        out[i] = m[i * 4 + 0] * v[0] + m[i * 4 + 1] * v[1] + m[i * 4 + 2] * v[2]


@wp.func
def transpose_rot(m: F16, out: F16):
    # 4x4 transpose of the rotational part with identity last row/col,
    # translation zeroed (rt used only as a 3x3 in the C++ formulas)
    for i in range(16):
        out[i] = F(0.0)
    for i in range(3):
        for j in range(3):
            out[i * 4 + j] = m[j * 4 + i]
    out[15] = F(1.0)


@wp.func
def load16(src: wp.array(dtype=wp.float64), off: wp.int32, out: F16):
    for i in range(16):
        out[i] = src[off + i]


@wp.func
def inverse_spd18(a: M324, out: M324) -> wp.int32:
    l = wp.zeros(shape=324, dtype=wp.float64)
    for i in range(324):
        l[i] = F(0.0)
    for i in range(18):
        for j in range(i + 1):
            t = a[i * 18 + j]
            if wp.abs(t - a[j * 18 + i]) > F(1e-12):
                return 0
            if wp.isnan(t):
                return 0
            for k in range(j):
                t = t - l[i * 18 + k] * l[j * 18 + k]
            if i == j:
                if not (t > F(0.0)):
                    return 0
                l[i * 18 + j] = wp.sqrt(t)
            else:
                l[i * 18 + j] = t / l[j * 18 + j]
    for col in range(18):
        y = wp.zeros(shape=18, dtype=wp.float64)
        x = wp.zeros(shape=18, dtype=wp.float64)
        for i in range(18):
            t = F(0.0)
            if i == col:
                t = F(1.0)
            for k in range(i):
                t = t - l[i * 18 + k] * y[k]
            y[i] = t / l[i * 18 + i]
        ii = wp.int32(17)
        while ii >= 0:
            t = y[ii]
            for k in range(ii + 1, 18):
                t = t - l[k * 18 + ii] * x[k]
            x[ii] = t / l[ii * 18 + ii]
            out[ii * 18 + col] = x[ii]
            ii = ii - 1
    an = F(0.0)
    bn = F(0.0)
    for i in range(18):
        ar = F(0.0)
        br = F(0.0)
        for j in range(18):
            ar = ar + wp.abs(a[i * 18 + j])
            br = br + wp.abs(out[i * 18 + j])
        if ar > an:
            an = ar
        if br > bn:
            bn = br
    if wp.isnan(an * bn) or an * bn >= F(1e12):
        return 0
    return 1


@wp.func
def mv18(a: M324, x: Q18, out: Q18):
    for i in range(18):
        s = F(0.0)
        for j in range(18):
            s = s + a[i * 18 + j] * x[j]
        out[i] = s


# ───────────────────────── the dynamics evaluation ─────────────────────────
@wp.func
def fk_eval(q: Q18, v: Q18,
            ax_rot: wp.array(dtype=wp.int32),
            ax_axis: wp.array(dtype=wp.float64), ax_slot: wp.array(dtype=wp.int32),
            ax_slope: wp.array(dtype=wp.float64), ax_const: wp.array(dtype=wp.float64),
            body_axoff: wp.array(dtype=wp.int32), body_parent: wp.array(dtype=wp.int32),
            body_mass: wp.array(dtype=wp.float64), body_com: wp.array(dtype=wp.float64),
            body_inertia: wp.array(dtype=wp.float64),
            body_fp: wp.array(dtype=wp.float64), body_fc: wp.array(dtype=wp.float64),
            chain_off: wp.array(dtype=wp.int32), chain_ax: wp.array(dtype=wp.int32),
            pt_body: wp.array(dtype=wp.int32), pt_local: wp.array(dtype=wp.float64),
            pt_radius: wp.array(dtype=wp.float64),
            nbod: wp.int32, naxes: wp.int32, plane_y: F, gy: F,
            M: M324, gv: Q18, bv: Q18,
            fr: F224, frd: F224, frdd: F224,
            axw: F54, axpiv: F54, axdir: F54,
            ptp: F24, ptJ: F216, ptcop: F12, ptbias: F12) -> wp.float64:
    grav = wp.zeros(shape=3, dtype=wp.float64); grav[0] = F(0.0); grav[1] = -gy; grav[2] = F(0.0)
    for i in range(18):
        gv[i] = F(0.0); bv[i] = F(0.0)
    for i in range(324):
        M[i] = F(0.0)
    for i in range(224):
        fr[i] = F(0.0); frd[i] = F(0.0); frdd[i] = F(0.0)
    # identity frames for the ground body
    fr[0] = F(1.0); fr[5] = F(1.0); fr[10] = F(1.0); fr[15] = F(1.0)
    frd[0] = F(1.0); frd[5] = F(1.0); frd[10] = F(1.0); frd[15] = F(1.0)
    frdd[0] = F(1.0); frdd[5] = F(1.0); frdd[10] = F(1.0); frdd[15] = F(1.0)
    for i in range(54):
        axw[i] = F(0.0); axpiv[i] = F(0.0); axdir[i] = F(0.0)
    potential = F(0.0)
    one = wp.zeros(shape=16, dtype=wp.float64); one_dt = wp.zeros(shape=16, dtype=wp.float64); one_ddt = wp.zeros(shape=16, dtype=wp.float64); sk = wp.zeros(shape=16, dtype=wp.float64)
    motion = wp.zeros(shape=16, dtype=wp.float64); motion_dt = wp.zeros(shape=16, dtype=wp.float64); motion_ddt = wp.zeros(shape=16, dtype=wp.float64)
    pfp = wp.zeros(shape=16, dtype=wp.float64); t1 = wp.zeros(shape=16, dtype=wp.float64); t2 = wp.zeros(shape=16, dtype=wp.float64); t3 = wp.zeros(shape=16, dtype=wp.float64); t4 = wp.zeros(shape=16, dtype=wp.float64)
    fp16 = wp.zeros(shape=16, dtype=wp.float64); fc16 = wp.zeros(shape=16, dtype=wp.float64)
    rt = wp.zeros(shape=16, dtype=wp.float64); mtmp = wp.zeros(shape=16, dtype=wp.float64); mtmp2 = wp.zeros(shape=16, dtype=wp.float64)
    jv = wp.zeros(shape=54, dtype=wp.float64)
    jw = wp.zeros(shape=54, dtype=wp.float64)
    for b in range(1, nbod):
        par = body_parent[b]
        load16(body_fp, b * 16, fp16)
        load16(body_fc, b * 16, fc16)
        # pfp = fr[par] * fp
        for i in range(16):
            t1[i] = fr[par * 16 + i]
        mm(t1, fp16, pfp)
        eye16(motion); eye16(motion_dt); eye16(motion_ddt)
        tvx = F(0.0); tvy = F(0.0); tvz = F(0.0)
        vvx = F(0.0); vvy = F(0.0); vvz = F(0.0)
        a0 = body_axoff[b]
        a1 = body_axoff[b + 1]
        for ai in range(a0, a1):
            slot = ax_slot[ai]
            ang = ax_const[ai]
            rate = F(0.0)
            if slot >= 0:
                ang = ang + ax_slope[ai] * q[slot]
                rate = ax_slope[ai] * v[slot]
            axis = wp.zeros(shape=3, dtype=wp.float64); axis[0] = ax_axis[ai * 3]; axis[1] = ax_axis[ai * 3 + 1]; axis[2] = ax_axis[ai * 3 + 2]
            if ax_rot[ai] != 0:
                rot_axis(axis, ang, one)
                # sk = skew(axis); dr = sk*R; one_dt = dr*rate; one_ddt = sk*dr*rate^2
                for i in range(16):
                    sk[i] = F(0.0)
                sk[0 * 4 + 1] = -axis[2]; sk[0 * 4 + 2] = axis[1]
                sk[1 * 4 + 0] = axis[2]; sk[1 * 4 + 2] = -axis[0]
                sk[2 * 4 + 0] = -axis[1]; sk[2 * 4 + 1] = axis[0]
                mm(sk, one, t2)                       # t2 = dr
                for i in range(16):
                    one_dt[i] = t2[i] * rate
                mm(sk, t2, t3)                        # t3 = sk*dr
                for i in range(16):
                    one_ddt[i] = t3[i] * rate * rate
                mm(motion, one, t1)                   # motion = motion*one
                for i in range(16):
                    motion[i] = t1[i]
                mm(motion_dt, one, t1)
                mm(motion, one_dt, t2)
                for i in range(16):
                    motion_dt[i] = t1[i] + t2[i]
                mm(motion_ddt, one, t1)
                mm(motion_dt, one_dt, t2)
                for i in range(16):
                    motion_ddt[i] = t1[i] + F(2.0) * t2[i]
                mm(motion, one_ddt, t3)
                for i in range(16):
                    motion_ddt[i] = motion_ddt[i] + t3[i]
            else:
                tvx = tvx + axis[0] * ang; tvy = tvy + axis[1] * ang; tvz = tvz + axis[2] * ang
                vvx = vvx + axis[0] * rate; vvy = vvy + axis[1] * rate; vvz = vvz + axis[2] * rate
        for k in range(3):
            motion[k * 4 + 3] = F(0.0)
        motion[0 * 4 + 3] = tvx; motion[1 * 4 + 3] = tvy; motion[2 * 4 + 3] = tvz
        motion_dt[0 * 4 + 3] = vvx; motion_dt[1 * 4 + 3] = vvy; motion_dt[2 * 4 + 3] = vvz
        # fr_b = pfp*motion*fc ; frd = prd*fp? -> the product rule with fixed(fp):
        # f   = par*fp*motion*fc
        # fd  = par*fp*motion_dt*fc              (fixed(fp) and fixed(fc) have no dt)
        # fdd = par*fp*motion_ddt*fc
        mm(pfp, motion, t1)
        mm(t1, fc16, t2)
        for i in range(16):
            fr[b * 16 + i] = t2[i]
        mm(pfp, motion_dt, t1)
        mm(t1, fc16, t2)
        for i in range(16):
            frd[b * 16 + i] = t2[i]
        mm(pfp, motion_ddt, t1)
        mm(t1, fc16, t2)
        for i in range(16):
            frdd[b * 16 + i] = t2[i]
        # per-axis world geometric data (Jacobians + pivots)
        for ai in range(a0, a1):
            axis = wp.zeros(shape=3, dtype=wp.float64); axis[0] = ax_axis[ai * 3]; axis[1] = ax_axis[ai * 3 + 1]; axis[2] = ax_axis[ai * 3 + 2]
            wx = F(0.0); wy = F(0.0); wz = F(0.0)
            for i in range(3):
                for j in range(3):
                    aij = pfp[i * 4 + j]
                    if j == 0:
                        wx = wx + aij * axis[0]
                    elif j == 1:
                        wy = wy + aij * axis[1]
                    else:
                        wz = wz + aij * axis[2]
            if ax_rot[ai] != 0:
                axw[ai * 3] = wx; axw[ai * 3 + 1] = wy; axw[ai * 3 + 2] = wz
                # pivot = pfp.t + pfp.R * t_m
                px = pfp[0 * 4 + 3] + (pfp[0 * 4 + 0] * tvx + pfp[0 * 4 + 1] * tvy + pfp[0 * 4 + 2] * tvz)
                py = pfp[1 * 4 + 3] + (pfp[1 * 4 + 0] * tvx + pfp[1 * 4 + 1] * tvy + pfp[1 * 4 + 2] * tvz)
                pz = pfp[2 * 4 + 3] + (pfp[2 * 4 + 0] * tvx + pfp[2 * 4 + 1] * tvy + pfp[2 * 4 + 2] * tvz)
                axpiv[ai * 3] = px; axpiv[ai * 3 + 1] = py; axpiv[ai * 3 + 2] = pz
            else:
                axdir[ai * 3] = wx; axdir[ai * 3 + 1] = wy; axdir[ai * 3 + 2] = wz
        # ── the body's Jacobian columns over its ancestor chain ──
        for i in range(54):
            jv[i] = F(0.0); jw[i] = F(0.0)
        comw = wp.zeros(shape=3, dtype=wp.float64)
        com = wp.zeros(shape=3, dtype=wp.float64); com[0] = body_com[b * 3]; com[1] = body_com[b * 3 + 1]; com[2] = body_com[b * 3 + 2]
        for i in range(16):
            t1[i] = fr[b * 16 + i]
        apply_point(t1, com, comw)
        for idx in range(chain_off[b], chain_off[b + 1]):
            ai = chain_ax[idx]
            slot = ax_slot[ai]
            if slot < 0:
                continue
            if ax_rot[ai] != 0:
                w = wp.zeros(shape=3, dtype=wp.float64); w[0] = axw[ai * 3]; w[1] = axw[ai * 3 + 1]; w[2] = axw[ai * 3 + 2]
                pv = wp.zeros(shape=3, dtype=wp.float64); pv[0] = axpiv[ai * 3]; pv[1] = axpiv[ai * 3 + 1]; pv[2] = axpiv[ai * 3 + 2]
                rx = comw[0] - pv[0]; ry = comw[1] - pv[1]; rz = comw[2] - pv[2]
                jv[slot * 3] = jv[slot * 3] + (w[1] * rz - w[2] * ry)
                jv[slot * 3 + 1] = jv[slot * 3 + 1] + (w[2] * rx - w[0] * rz)
                jv[slot * 3 + 2] = jv[slot * 3 + 2] + (w[0] * ry - w[1] * rx)
                jw[slot * 3] = jw[slot * 3] + w[0]
                jw[slot * 3 + 1] = jw[slot * 3 + 1] + w[1]
                jw[slot * 3 + 2] = jw[slot * 3 + 2] + w[2]
            else:
                jv[slot * 3] = jv[slot * 3] + axdir[ai * 3]
                jv[slot * 3 + 1] = jv[slot * 3 + 1] + axdir[ai * 3 + 1]
                jv[slot * 3 + 2] = jv[slot * 3 + 2] + axdir[ai * 3 + 2]
        # ── omega/alpha/acc/moment (the C++ formulas) ──
        for i in range(16):
            t1[i] = fr[b * 16 + i]
        for i in range(16):
            t2[i] = frd[b * 16 + i]
        transpose_rot(t1, rt)
        mm(t2, rt, mtmp)                     # frd * R^T
        omega = wp.zeros(shape=3, dtype=wp.float64); axial3(mtmp, omega)
        for i in range(16):
            t3[i] = frdd[b * 16 + i]
        mm(t3, rt, mtmp)                     # frdd * R^T
        transpose_rot(t2, rt)
        mm(t2, rt, mtmp2)                    # frd * frd^T (3x3 part used)
        for i in range(3):
            for j in range(3):
                mtmp[i * 4 + j] = mtmp[i * 4 + j] + mtmp2[i * 4 + j]
        alpha = wp.zeros(shape=3, dtype=wp.float64); axial3(mtmp, alpha)
        acc_com = wp.zeros(shape=3, dtype=wp.float64)
        comloc = wp.zeros(shape=3, dtype=wp.float64); comloc[0] = body_com[b * 3]; comloc[1] = body_com[b * 3 + 1]; comloc[2] = body_com[b * 3 + 2]
        for i in range(16):
            t3[i] = frdd[b * 16 + i]
        apply_point(t3, comloc, acc_com)
        # Iw = R * diag(I) * R^T
        It = wp.zeros(shape=3, dtype=wp.float64); It[0] = body_inertia[b * 3]; It[1] = body_inertia[b * 3 + 1]; It[2] = body_inertia[b * 3 + 2]
        for i in range(16):
            t1[i] = fr[b * 16 + i]
        for i in range(16):
            t2[i] = F(0.0)
        for i in range(3):
            for j in range(3):
                s = F(0.0)
                for k in range(3):
                    s = s + t1[i * 4 + k] * (It[k] * t1[j * 4 + k])
                t2[i * 4 + j] = s
        Iw = t2
        # moment = Iw*alpha + omega x (Iw*omega)
        Iwom = wp.zeros(shape=3, dtype=wp.float64)
        for i in range(3):
            Iwom[i] = Iw[i * 4 + 0] * omega[0] + Iw[i * 4 + 1] * omega[1] + Iw[i * 4 + 2] * omega[2]
        moment = wp.zeros(shape=3, dtype=wp.float64)
        moment[0] = Iw[0 * 4 + 0] * alpha[0] + Iw[0 * 4 + 1] * alpha[1] + Iw[0 * 4 + 2] * alpha[2] + (omega[1] * Iwom[2] - omega[2] * Iwom[1])
        moment[1] = Iw[1 * 4 + 0] * alpha[0] + Iw[1 * 4 + 1] * alpha[1] + Iw[1 * 4 + 2] * alpha[2] + (omega[2] * Iwom[0] - omega[0] * Iwom[2])
        moment[2] = Iw[2 * 4 + 0] * alpha[0] + Iw[2 * 4 + 1] * alpha[1] + Iw[2 * 4 + 2] * alpha[2] + (omega[0] * Iwom[1] - omega[1] * Iwom[0])
        m = body_mass[b]
        if m > F(0.0):
            nslots = chain_off[b + 1] - chain_off[b]
            # Iw*jw_j per pair (computed on the fly)
            for ii in range(nslots):
                ai_i = chain_ax[chain_off[b] + ii]
                si = ax_slot[ai_i]
                if si < 0:
                    continue
                for jj in range(nslots):
                    ai_j = chain_ax[chain_off[b] + jj]
                    sj = ax_slot[ai_j]
                    if sj < 0:
                        continue
                    jvd = F(0.0)
                    for c in range(3):
                        jvd = jvd + jv[si * 3 + c] * jv[sj * 3 + c]
                    jwd = F(0.0)
                    for c in range(3):
                        Iwj = Iw[c * 4 + 0] * jw[sj * 3 + 0] + Iw[c * 4 + 1] * jw[sj * 3 + 1] + Iw[c * 4 + 2] * jw[sj * 3 + 2]
                        jwd = jwd + jw[si * 3 + c] * Iwj
                    M[si * 18 + sj] = M[si * 18 + sj] + m * jvd + jwd
            for ii in range(nslots):
                ai_i = chain_ax[chain_off[b] + ii]
                si = ax_slot[ai_i]
                if si < 0:
                    continue
                gv[si] = gv[si] + m * (jv[si * 3 + 0] * grav[0] + jv[si * 3 + 1] * grav[1] + jv[si * 3 + 2] * grav[2])
                bv[si] = bv[si] + m * (jv[si * 3 + 0] * acc_com[0] + jv[si * 3 + 1] * acc_com[1] + jv[si * 3 + 2] * acc_com[2])
                bv[si] = bv[si] + (jw[si * 3 + 0] * moment[0] + jw[si * 3 + 1] * moment[1] + jw[si * 3 + 2] * moment[2])
            potential = potential - m * (grav[0] * comw[0] + grav[1] * comw[1] + grav[2] * comw[2])
    # ── contact points ──
    for k in range(8):
        pb = pt_body[k]
        p = wp.zeros(shape=3, dtype=wp.float64); p[0] = pt_local[k * 3]; p[1] = pt_local[k * 3 + 1]; p[2] = pt_local[k * 3 + 2]
        for i in range(16):
            t1[i] = fr[pb * 16 + i]
        out = wp.zeros(shape=3, dtype=wp.float64); apply_point(t1, p, out)
        ptp[k * 3] = out[0]; ptp[k * 3 + 1] = out[1]; ptp[k * 3 + 2] = out[2]
    # sole representatives r=0..3 (points 2r, 2r+1): CoP interpolation
    for r in range(4):
        k = r * 2
        gh = ptp[k * 3 + 1] + pt_radius[k] - plane_y
        gm = ptp[(k + 1) * 3 + 1] + pt_radius[k + 1] - plane_y
        dy = ptp[(k + 1) * 3 + 1] - ptp[k * 3 + 1]
        a = F(0.5)
        if not ((gh <= F(2e-6) and gm <= F(2e-6)) or wp.abs(dy) < F(1e-8)):
            if dy < F(0.0):
                a = F(1.0)
            else:
                a = F(0.0)
        loc = wp.zeros(shape=3, dtype=wp.float64)
        for c in range(3):
            loc[c] = pt_local[k * 3 + c] + (pt_local[(k + 1) * 3 + c] - pt_local[k * 3 + c]) * a
        ptcop[r * 3] = loc[0]; ptcop[r * 3 + 1] = loc[1]; ptcop[r * 3 + 2] = loc[2]
        pb = pt_body[k]
        for i in range(16):
            t1[i] = fr[pb * 16 + i]
        solew = wp.zeros(shape=3, dtype=wp.float64); apply_point(t1, loc, solew)
        t3v = wp.zeros(shape=3, dtype=wp.float64)
        for i in range(16):
            t4[i] = frdd[pb * 16 + i]
        apply_point(t4, loc, t3v)
        ptbias[r * 3] = t3v[0]; ptbias[r * 3 + 1] = t3v[1]; ptbias[r * 3 + 2] = t3v[2]
        for c in range(18):
            ptJ[(r * 3 + 0) * 18 + c] = F(0.0)
            ptJ[(r * 3 + 1) * 18 + c] = F(0.0)
            ptJ[(r * 3 + 2) * 18 + c] = F(0.0)
        for idx in range(chain_off[pb], chain_off[pb + 1]):
            ai = chain_ax[idx]
            slot = ax_slot[ai]
            if slot < 0:
                continue
            if ax_rot[ai] != 0:
                w = wp.zeros(shape=3, dtype=wp.float64); w[0] = axw[ai * 3]; w[1] = axw[ai * 3 + 1]; w[2] = axw[ai * 3 + 2]
                pv = wp.zeros(shape=3, dtype=wp.float64); pv[0] = axpiv[ai * 3]; pv[1] = axpiv[ai * 3 + 1]; pv[2] = axpiv[ai * 3 + 2]
                rx = solew[0] - pv[0]; ry = solew[1] - pv[1]; rz = solew[2] - pv[2]
                jx = w[1] * rz - w[2] * ry
                jy = w[2] * rx - w[0] * rz
                jz = w[0] * ry - w[1] * rx
                ptJ[(r * 3 + 0) * 18 + slot] = ptJ[(r * 3 + 0) * 18 + slot] + jx
                ptJ[(r * 3 + 1) * 18 + slot] = ptJ[(r * 3 + 1) * 18 + slot] + jy
                ptJ[(r * 3 + 2) * 18 + slot] = ptJ[(r * 3 + 2) * 18 + slot] + jz
            else:
                ptJ[(r * 3 + 0) * 18 + slot] = ptJ[(r * 3 + 0) * 18 + slot] + axdir[ai * 3]
                ptJ[(r * 3 + 1) * 18 + slot] = ptJ[(r * 3 + 1) * 18 + slot] + axdir[ai * 3 + 1]
                ptJ[(r * 3 + 2) * 18 + slot] = ptJ[(r * 3 + 2) * 18 + slot] + axdir[ai * 3 + 2]
    return potential




# ───────────────────────── contact machinery ─────────────────────────
@wp.func
def gap_of_k(ptp: F24, pt_radius: wp.array(dtype=wp.float64), k: wp.int32, plane_y: F) -> wp.float64:
    h = k - (k % 2)
    gh = ptp[h * 3 + 1] + pt_radius[h] - plane_y
    gm = ptp[(h + 1) * 3 + 1] + pt_radius[h + 1] - plane_y
    if gh < gm:
        return gh
    return gm


@wp.func
def row_dot(row: Q18, x: Q18) -> wp.float64:
    s = F(0.0)
    for i in range(18):
        s = s + row[i] * x[i]
    return s


@wp.func
def mat_vec(inv: M324, row: Q18, out: Q18):
    # out = inv * row
    for i in range(18):
        s = F(0.0)
        for j in range(18):
            s = s + inv[i * 18 + j] * row[j]
        out[i] = s


@wp.func
def rows_row(rows: F180, k: wp.int32, out: Q18):
    for i in range(18):
        out[i] = rows[k * 18 + i]


@wp.func
def gram_factor10(g: F100, k: wp.int32, rhs: F10, lam: F10) -> wp.int32:
    scale = F(0.0)
    for i in range(k):
        d = g[i * k + i]
        if d < F(0.0):
            d = -d
        if d > scale:
            scale = d
    if not (scale > F(0.0)):
        return 0
    for i in range(k):
        for j in range(i):
            avg = (g[i * k + j] + g[j * k + i]) * F(0.5)
            g[i * k + j] = avg
            g[j * k + i] = avg
    l = wp.zeros(shape=100, dtype=wp.float64)
    for i in range(k):
        for j in range(i + 1):
            t = g[i * k + j]
            for m in range(j):
                t = t - l[i * k + m] * l[j * k + m]
            if i == j:
                if not (t > F(1e-9) * scale):
                    return 0
                l[i * k + j] = wp.sqrt(t)
            else:
                l[i * k + j] = t / l[j * k + j]
    for i in range(k):
        lam[i] = F(0.0)
    for col in range(k):
        y = wp.zeros(shape=10, dtype=wp.float64)
        x = wp.zeros(shape=10, dtype=wp.float64)
        for i in range(k):
            t = F(0.0)
            if col == i:
                t = F(1.0)
            for m in range(i):
                t = t - l[i * k + m] * y[m]
            y[i] = t / l[i * k + i]
        ii = k - 1
        while ii >= 0:
            t = y[ii]
            for m in range(ii + 1, k):
                t = t - l[m * k + ii] * x[m]
            x[ii] = t / l[ii * k + ii]
            lam[ii] = lam[ii] + x[ii] * rhs[col]
            ii = ii - 1
    return 1


@wp.func
def project_rows(initial: Q18, inv: M324, rows: F180, floors: F10, R: wp.int32, n_stops: wp.int32,
                 p_out: Q18, multipliers: F10) -> wp.int32:
    # Mass-metric active-set projection (the free-root D6 law, lifted
    # row-count-only): the deterministic full subset enumeration, the
    # stop-holding tier first. Returns 1 with p_out, or 0 = gait_row_budget.
    if R < 1 or R > 10:
        return 0
    tier = wp.int32(0)
    while tier <= 1:
        mask = wp.int32(0)
        while mask < (1 << R):
            skip = wp.int32(0)
            if mask != 0:
                holds = wp.int32(1)
                for k in range(n_stops):
                    if not ((mask >> k) & 1):
                        holds = 0
                if holds != wp.int32(tier == 0):
                    skip = 1
            else:
                if tier != 0:
                    skip = 1
            if skip == 0:
                act = wp.zeros(shape=10, dtype=wp.int32)
                cnt = wp.int32(0)
                for k in range(R):
                    if (mask >> k) & 1:
                        act[cnt] = k
                        cnt = cnt + 1
                legal = wp.int32(1)
                if cnt > 18:
                    legal = 0
                if legal == 1:
                    if cnt == 0:
                        allok = wp.int32(1)
                        rk = wp.zeros(shape=18, dtype=wp.float64)
                        for k in range(R):
                            rows_row(rows, k, rk)
                            tol = F(1e-9) * (F(1.0) + wp.abs(floors[k]))
                            if row_dot(rk, initial) < floors[k] - tol:
                                allok = 0
                        if allok == 1:
                            for i in range(18):
                                p_out[i] = F(0.0)
                            for k in range(R):
                                multipliers[k] = F(0.0)
                            return 1
                    else:
                        gram = wp.zeros(shape=100, dtype=wp.float64)
                        rhs = wp.zeros(shape=10, dtype=wp.float64)
                        ra = wp.zeros(shape=18, dtype=wp.float64)
                        rb = wp.zeros(shape=18, dtype=wp.float64)
                        ia = wp.zeros(shape=18, dtype=wp.float64)
                        for a in range(cnt):
                            for b in range(cnt):
                                rows_row(rows, act[a], ra)
                                rows_row(rows, act[b], rb)
                                mat_vec(inv, ra, ia)
                                s = F(0.0)
                                for i in range(18):
                                    s = s + ia[i] * rb[i]
                                gram[a * cnt + b] = s
                            rows_row(rows, act[a], ra)
                            rhs[a] = floors[act[a]] - row_dot(ra, initial)
                        lam = wp.zeros(shape=10, dtype=wp.float64)
                        if gram_factor10(gram, cnt, rhs, lam) == 1:
                            valid = wp.int32(1)
                            for k in range(cnt):
                                if lam[k] < F(-1e-10):
                                    valid = 0
                            if valid == 1:
                                for i in range(18):
                                    p_out[i] = F(0.0)
                                for k in range(cnt):
                                    l = lam[k]
                                    if l < F(0.0):
                                        l = F(0.0)
                                    rk = wp.zeros(shape=18, dtype=wp.float64)
                                    rows_row(rows, act[k], rk)
                                    for i in range(18):
                                        p_out[i] = p_out[i] + l * rk[i]
                                chg = wp.zeros(shape=18, dtype=wp.float64)
                                mat_vec(inv, p_out, chg)
                                rk = wp.zeros(shape=18, dtype=wp.float64)
                                for k in range(R):
                                    tol = F(1e-9) * (F(1.0) + wp.abs(floors[k]))
                                    rows_row(rows, k, rk)
                                    got = row_dot(rk, initial) + row_dot(rk, chg)
                                    if got < floors[k] - tol:
                                        valid = 0
                                if valid == 1:
                                    for k in range(R):
                                        multipliers[k] = F(0.0)
                                    for k in range(cnt):
                                        l = lam[k]
                                        if l < F(0.0):
                                            l = F(0.0)
                                        multipliers[act[k]] = l
                                    return 1
            mask = mask + 1
        tier = tier + 1
    return 0


@wp.func
def friction_solve(initial: Q18, inv: M324, row_n: Q18, row_t: Q18,
                   floor_n: F, floor_t: F, mu: F, slip_sign: wp.int32,
                   force: Q18, ln: F1, lt: F1, mode: I1):
    # gait_controller friction_solve verbatim; mode: 0 none, 1 cone, 2 slide,
    # -1 = the gait_friction_slide_singular swallow
    for i in range(18):
        force[i] = F(0.0)
    ln[0] = F(0.0)
    lt[0] = F(0.0)
    mode[0] = 0
    rn_v = wp.zeros(shape=18, dtype=wp.float64)
    mat_vec(inv, row_n, rn_v)
    rt_v = wp.zeros(shape=18, dtype=wp.float64)
    mat_vec(inv, row_t, rt_v)
    A = row_dot(row_n, rn_v)
    B = row_dot(row_n, rt_v)
    C = row_dot(row_t, rt_v)
    rn = -(row_dot(row_n, initial) - floor_n)
    rt = -(row_dot(row_t, initial) - floor_t)
    det = A * C - B * B
    if det > F(1e-18):
        nn = (rn * C - rt * B) / det
        t = (rt * A - rn * B) / det
        at = t
        if at < F(0.0):
            at = -at
        if nn >= F(0.0) and at <= mu * nn + F(1e-12) and (slip_sign == 0 or t * F(slip_sign) <= F(0.0)):
            for i in range(18):
                force[i] = row_n[i] * nn + row_t[i] * t
            ln[0] = nn
            lt[0] = t
            mode[0] = 1
            return
    s = F(0.0)
    if slip_sign != 0:
        s = F(slip_sign)
    else:
        if rt >= F(0.0):
            s = F(-1.0)
        else:
            s = F(1.0)
    den = A - s * mu * B
    if den <= F(1e-12):
        mode[0] = -1
        return
    nn = rn / den
    t = -s * mu * nn
    if nn >= F(0.0):
        for i in range(18):
            force[i] = row_n[i] * nn + row_t[i] * t
        ln[0] = nn
        lt[0] = t
        mode[0] = 2
        return
    ln[0] = F(0.0)
    lt[0] = F(0.0)
    mode[0] = 0




# ───────────────────────── model bundles ─────────────────────────
I4 = wp.fixedarray(dtype=wp.int32, shape=4)


@wp.struct
class ModelIn:
    ax_rot: wp.array(dtype=wp.int32)
    ax_axis: wp.array(dtype=wp.float64)
    ax_slot: wp.array(dtype=wp.int32)
    ax_slope: wp.array(dtype=wp.float64)
    ax_const: wp.array(dtype=wp.float64)
    body_axoff: wp.array(dtype=wp.int32)
    body_parent: wp.array(dtype=wp.int32)
    body_mass: wp.array(dtype=wp.float64)
    body_com: wp.array(dtype=wp.float64)
    body_inertia: wp.array(dtype=wp.float64)
    body_fp: wp.array(dtype=wp.float64)
    body_fc: wp.array(dtype=wp.float64)
    chain_off: wp.array(dtype=wp.int32)
    chain_ax: wp.array(dtype=wp.int32)
    pt_body: wp.array(dtype=wp.int32)
    pt_local: wp.array(dtype=wp.float64)
    pt_radius: wp.array(dtype=wp.float64)
    lower: wp.array(dtype=wp.float64)
    upper: wp.array(dtype=wp.float64)
    drive_coord: wp.array(dtype=wp.int32)
    drive_cap: wp.array(dtype=wp.float64)
    drive_damping: wp.array(dtype=wp.float64)
    kp: wp.array(dtype=wp.float64)
    kd: wp.array(dtype=wp.float64)
    tab_hip: wp.array(dtype=wp.float64)
    tab_knee: wp.array(dtype=wp.float64)
    tab_ankle: wp.array(dtype=wp.float64)
    tab_mp: wp.array(dtype=wp.float64)
    zeros4: wp.array(dtype=wp.float64)
    vault: wp.array(dtype=wp.float64)
    fore_coord: wp.array(dtype=wp.int32)
    hind_coord: wp.array(dtype=wp.int32)
    hind_drive: wp.array(dtype=wp.int32)
    fore_drive: wp.array(dtype=wp.int32)
    fore_heel_pt: wp.array(dtype=wp.int32)
    hind_heel_pt: wp.array(dtype=wp.int32)
    fore_mount_local: wp.array(dtype=wp.float64)
    hind_mount: wp.array(dtype=wp.float64)


@wp.struct
class ModelConst:
    nbod: wp.int32
    naxes: wp.int32
    plane_y: wp.float64
    gy: wp.float64
    dt: wp.float64
    mu: wp.float64
    k_touch: wp.float64
    k_slip: wp.float64
    k_release: wp.float64
    t_cycle: wp.float64
    duty: wp.float64
    toe_off: wp.float64
    fs_hz: wp.float64
    zeta: wp.float64
    capture_phi: wp.float64
    settle_total: wp.int32
    contact: wp.int32
    power: wp.int32
    gait_enabled: wp.int32
    capture_enabled: wp.int32
    posture_drive: wp.int32
    drive_en: wp.int32
    reflex_level: wp.int32
    kp_post: wp.float64
    kd_post: wp.float64
    store_post: wp.float64
    height_crit: wp.float64
    height_floor: wp.float64
    fore_L1: wp.float64
    fore_rho: wp.float64
    fore_beta: wp.float64
    hind_L1: wp.float64
    hind_L2: wp.float64
    hind_xm: wp.float64
    fore_pose_sh: wp.float64
    fore_pose_el: wp.float64
    fold_budget: wp.int32
    unload_ticks: wp.int32
    tair: wp.int32
    pelvis_row: wp.int32
    upperarm_body: wp.int32
    forearm_body: wp.int32


@wp.func
def rate(q: Q18, v: Q18, tau: Q18, live: I4, plane: I4,
         mdl: ModelIn, cst: ModelConst,
         M: M324, gv: Q18, bv: Q18, fr: F224, frd: F224, frdd: F224,
         axw: F54, axpiv: F54, axdir: F54, ptp: F24, ptJ: F216, ptcop: F12, ptbias: F12,
         inv: M324, free: Q18, rq: Q18, rv: Q18) -> wp.int32:
    pot = fk_eval(q, v, mdl.ax_rot, mdl.ax_axis, mdl.ax_slot, mdl.ax_slope, mdl.ax_const,
                  mdl.body_axoff, mdl.body_parent, mdl.body_mass, mdl.body_com, mdl.body_inertia,
                  mdl.body_fp, mdl.body_fc, mdl.chain_off, mdl.chain_ax, mdl.pt_body, mdl.pt_local,
                  mdl.pt_radius, cst.nbod, cst.naxes, cst.plane_y, cst.gy,
                  M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias)
    if inverse_spd18(M, inv) == 0:
        return 8
    for i in range(18):
        free[i] = gv[i] - bv[i]
        rq[i] = F(0.0)
    for d in range(12):
        c = mdl.drive_coord[d]
        free[c] = free[c] + tau[c] - mdl.drive_damping[d] * v[c]
    mat_vec(inv, free, free)
    rows = wp.zeros(shape=180, dtype=wp.float64)
    floors = wp.zeros(shape=10, dtype=wp.float64)
    R = wp.int32(0)
    n_stops = wp.int32(0)
    stop = wp.int32(0)
    jn = wp.zeros(shape=18, dtype=wp.float64)
    for d in range(12):
        c = mdl.drive_coord[d]
        jn[c] = F(0.0)
        if wp.abs(q[c] - mdl.lower[c]) < F(1e-10):
            jn[c] = F(1.0)
        elif wp.abs(q[c] - mdl.upper[c]) < F(1e-10):
            jn[c] = F(-1.0)
    speed_scale = F(0.0)
    for d in range(12):
        speed_scale = speed_scale + wp.abs(v[mdl.drive_coord[d]])
    gate = F(1e-6) + F(1e-3) * speed_scale
    for d in range(12):
        c = mdl.drive_coord[d]
        if jn[c] != F(0.0) and wp.abs(v[c]) <= F(1e-9):
            if R >= 10:
                return 5
            for i in range(18):
                rows[R * 18 + i] = F(0.0)
            rows[R * 18 + c] = jn[c]
            floors[R] = F(0.0)
            R = R + 1
            n_stops = n_stops + 1
            stop = 1
    touching = wp.zeros(shape=4, dtype=wp.int32)
    mode_k = wp.zeros(shape=4, dtype=wp.int32)
    rn = wp.zeros(shape=18, dtype=wp.float64)
    for r in range(4):
        for i in range(18):
            rn[i] = ptJ[(r * 3 + 1) * 18 + i]
        g = gap_of_k(ptp, mdl.pt_radius, r * 2, cst.plane_y)
        touching[r] = 0
        if plane[r] != 0:
            touching[r] = 1
        elif live[r] != 0 and g <= cst.k_touch and row_dot(rn, v) <= gate:
            touching[r] = 1
    if cst.contact != 0 and cst.mu > F(0.0) and stop == 0:
        jt1 = wp.zeros(shape=18, dtype=wp.float64)
        jt2 = wp.zeros(shape=18, dtype=wp.float64)
        row_t = wp.zeros(shape=18, dtype=wp.float64)
        force = wp.zeros(shape=18, dtype=wp.float64)
        corr = wp.zeros(shape=18, dtype=wp.float64)
        ln = wp.zeros(shape=1, dtype=wp.float64)
        lt = wp.zeros(shape=1, dtype=wp.float64)
        md = wp.zeros(shape=1, dtype=wp.int32)
        for r in range(4):
            if touching[r] == 0:
                continue
            for i in range(18):
                jt1[i] = ptJ[(r * 3 + 0) * 18 + i]
                jt2[i] = ptJ[(r * 3 + 2) * 18 + i]
            bx = ptbias[r * 3]
            by = ptbias[r * 3 + 1]
            bz = ptbias[r * 3 + 2]
            svx = row_dot(jt1, v)
            svz = row_dot(jt2, v)
            planar = wp.sqrt(svx * svx + svz * svz)
            dir_x = F(0.0)
            dir_z = F(0.0)
            slip_sign = wp.int32(0)
            if planar > cst.k_slip:
                dir_x = svx / planar
                dir_z = svz / planar
                slip_sign = 1
            else:
                d1 = bx
                d2 = bz
                for i in range(18):
                    d1 = d1 + jt1[i] * free[i]
                    d2 = d2 + jt2[i] * free[i]
                accel = wp.sqrt(d1 * d1 + d2 * d2)
                if accel > F(1e-9):
                    dir_x = d1 / accel
                    dir_z = d2 / accel
                    slip_sign = 1
            if dir_x == F(0.0) and dir_z == F(0.0):
                continue
            for i in range(18):
                row_t[i] = dir_x * jt1[i] + dir_z * jt2[i]
            friction_solve(free, inv, rn, row_t, -by, -(dir_x * bx + dir_z * bz), cst.mu, slip_sign,
                           force, ln, lt, md)
            if md[0] > 0:
                mat_vec(inv, force, corr)
                for i in range(18):
                    free[i] = free[i] + corr[i]
                mode_k[r] = md[0]
    for r in range(4):
        if touching[r] == 0:
            continue
        for i in range(18):
            rn[i] = ptJ[(r * 3 + 1) * 18 + i]
        floor_k = -ptbias[r * 3 + 1]
        if mode_k[r] != 0 and row_dot(rn, free) >= floor_k - F(1e-9):
            continue
        if R >= 10:
            return 5
        for i in range(18):
            rows[R * 18 + i] = rn[i]
        floors[R] = floor_k
        R = R + 1
    if R > 0:
        p = wp.zeros(shape=18, dtype=wp.float64)
        mult = wp.zeros(shape=10, dtype=wp.float64)
        if project_rows(free, inv, rows, floors, R, n_stops, p, mult) == 0:
            return 5
        corr = wp.zeros(shape=18, dtype=wp.float64)
        mat_vec(inv, p, corr)
        for i in range(18):
            free[i] = free[i] + corr[i]
    for i in range(18):
        rv[i] = free[i]
        rq[i] = v[i]
    return 0


@wp.func
def free_step(q0: Q18, v0: Q18, w0: Q18, tau: Q18, live: I4, h: F,
              mdl: ModelIn, cst: ModelConst,
              M: M324, gv: Q18, bv: Q18, fr: F224, frd: F224, frdd: F224,
              axw: F54, axpiv: F54, axdir: F54, ptp: F24, ptJ: F216, ptcop: F12, ptbias: F12,
              inv: M324, free: Q18, srq: Q18, srv: Q18,
              qa: Q18, va: Q18, qb: Q18, vb: Q18, qc: Q18, vc: Q18, qd: Q18, vd: Q18,
              q1: Q18, v1: Q18, w1: Q18) -> wp.int32:
    rq = wp.zeros(shape=18, dtype=wp.float64)
    rv = wp.zeros(shape=18, dtype=wp.float64)
    plane = wp.zeros(shape=4, dtype=wp.int32)
    pot = fk_eval(q0, v0, mdl.ax_rot, mdl.ax_axis, mdl.ax_slot, mdl.ax_slope, mdl.ax_const,
                  mdl.body_axoff, mdl.body_parent, mdl.body_mass, mdl.body_com, mdl.body_inertia,
                  mdl.body_fp, mdl.body_fc, mdl.chain_off, mdl.chain_ax, mdl.pt_body, mdl.pt_local,
                  mdl.pt_radius, cst.nbod, cst.naxes, cst.plane_y, cst.gy,
                  M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias)
    speed_scale = F(0.0)
    for d in range(12):
        speed_scale = speed_scale + wp.abs(v0[mdl.drive_coord[d]])
    gate = F(1e-6) + F(1e-3) * speed_scale
    rn = wp.zeros(shape=18, dtype=wp.float64)
    for r in range(4):
        for i in range(18):
            rn[i] = ptJ[(r * 3 + 1) * 18 + i]
        g = gap_of_k(ptp, mdl.pt_radius, r * 2, cst.plane_y)
        if live[r] != 0 and g <= cst.k_touch and row_dot(rn, v0) <= gate:
            plane[r] = 1
    rc = rate(q0, v0, tau, live, plane, mdl, cst, M, gv, bv, fr, frd, frdd,
              axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, srq, srv)
    if rc != 0:
        return rc
    half = h * F(0.5)
    for i in range(18):
        qb[i] = q0[i] + qa[i] * half
        vb[i] = v0[i] + va[i] * half
    rc = rate(qb, vb, tau, live, plane, mdl, cst, M, gv, bv, fr, frd, frdd,
              axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, srq, srv)
    if rc != 0:
        return rc
    brq = wp.zeros(shape=18, dtype=wp.float64)
    brv = wp.zeros(shape=18, dtype=wp.float64)
    for i in range(18):
        brq[i] = qb[i]
        brv[i] = vb[i]
    for i in range(18):
        qc[i] = q0[i] + brq[i] * half
        vc[i] = v0[i] + brv[i] * half
    rc = rate(qc, vc, tau, live, plane, mdl, cst, M, gv, bv, fr, frd, frdd,
              axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, srq, srv)
    if rc != 0:
        return rc
    crq = wp.zeros(shape=18, dtype=wp.float64)
    crv = wp.zeros(shape=18, dtype=wp.float64)
    for i in range(18):
        crq[i] = qc[i]
        crv[i] = vc[i]
    for i in range(18):
        qd[i] = q0[i] + crq[i] * h
        vd[i] = v0[i] + crv[i] * h
    rc = rate(qd, vd, tau, live, plane, mdl, cst, M, gv, bv, fr, frd, frdd,
              axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, srq, srv)
    if rc != 0:
        return rc
    drq = wp.zeros(shape=18, dtype=wp.float64)
    drv = wp.zeros(shape=18, dtype=wp.float64)
    for i in range(18):
        drq[i] = qd[i]
        drv[i] = vd[i]
    sixth = h / F(6.0)
    for i in range(18):
        q1[i] = q0[i] + sixth * (qa[i] + F(2.0) * brq[i] + F(2.0) * crq[i] + drq[i])
        v1[i] = v0[i] + sixth * (va[i] + F(2.0) * brv[i] + F(2.0) * crv[i] + drv[i])
        w1[i] = w0[i] + tau[i] * (q1[i] - q0[i])
    return 0


@wp.func
def gram_factor4(g: wp.fixedarray(dtype=wp.float64, shape=16), k: wp.int32,
                 rhs: wp.fixedarray(dtype=wp.float64, shape=4),
                 lam: wp.fixedarray(dtype=wp.float64, shape=4)) -> wp.int32:
    scale = F(0.0)
    for i in range(k):
        d = g[i * k + i]
        if d < F(0.0):
            d = -d
        if d > scale:
            scale = d
    if not (scale > F(0.0)):
        return 0
    l = wp.zeros(shape=16, dtype=wp.float64)
    for i in range(k):
        for j in range(i + 1):
            t = g[i * k + j]
            for m in range(j):
                t = t - l[i * k + m] * l[j * k + m]
            if i == j:
                if not (t > F(1e-9) * scale):
                    return 0
                l[i * k + j] = wp.sqrt(t)
            else:
                l[i * k + j] = t / l[j * k + j]
    for i in range(k):
        lam[i] = F(0.0)
    for col in range(k):
        y = wp.zeros(shape=4, dtype=wp.float64)
        x = wp.zeros(shape=4, dtype=wp.float64)
        for i in range(k):
            t = F(0.0)
            if col == i:
                t = F(1.0)
            for m in range(i):
                t = t - l[i * k + m] * y[m]
            y[i] = t / l[i * k + i]
        ii = k - 1
        while ii >= 0:
            t = y[ii]
            for m in range(ii + 1, k):
                t = t - l[m * k + ii] * x[m]
            x[ii] = t / l[ii * k + ii]
            lam[ii] = lam[ii] + x[ii] * rhs[col]
            ii = ii - 1
    return 1


@wp.func
def impact(q: Q18, v: Q18,
           mdl: ModelIn, cst: ModelConst,
           M: M324, gv: Q18, bv: Q18, fr: F224, frd: F224, frdd: F224,
           axw: F54, axpiv: F54, axdir: F54, ptp: F24, ptJ: F216, ptcop: F12, ptbias: F12,
           inv: M324, free: Q18, rc: I1) -> wp.float64:
    pot = fk_eval(q, v, mdl.ax_rot, mdl.ax_axis, mdl.ax_slot, mdl.ax_slope, mdl.ax_const,
                  mdl.body_axoff, mdl.body_parent, mdl.body_mass, mdl.body_com, mdl.body_inertia,
                  mdl.body_fp, mdl.body_fc, mdl.chain_off, mdl.chain_ax, mdl.pt_body, mdl.pt_local,
                  mdl.pt_radius, cst.nbod, cst.naxes, cst.plane_y, cst.gy,
                  M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias)
    if inverse_spd18(M, inv) == 0:
        rc[0] = 8
        return F(0.0)
    caught = F(0.0)
    rows = wp.zeros(shape=180, dtype=wp.float64)
    floors = wp.zeros(shape=10, dtype=wp.float64)
    R = wp.int32(0)
    n_stops = wp.int32(0)
    jn = wp.zeros(shape=18, dtype=wp.float64)
    for d in range(12):
        c = mdl.drive_coord[d]
        jn[c] = F(0.0)
        if wp.abs(q[c] - mdl.lower[c]) < F(1e-10):
            jn[c] = F(1.0)
        elif wp.abs(q[c] - mdl.upper[c]) < F(1e-10):
            jn[c] = F(-1.0)
    for d in range(12):
        c = mdl.drive_coord[d]
        if jn[c] != F(0.0):
            if R >= 10:
                rc[0] = 5
                return F(0.0)
            for i in range(18):
                rows[R * 18 + i] = F(0.0)
            rows[R * 18 + c] = jn[c]
            floors[R] = F(0.0)
            R = R + 1
            n_stops = n_stops + 1
    touching = wp.zeros(shape=4, dtype=wp.int32)
    for r in range(4):
        g = gap_of_k(ptp, mdl.pt_radius, r * 2, cst.plane_y)
        touching[r] = wp.int32(1) if (cst.contact != 0 and g <= cst.k_touch) else wp.int32(0)
    rn = wp.zeros(shape=18, dtype=wp.float64)
    if cst.mu > F(0.0) and n_stops == 0 and cst.contact != 0:
        jt1 = wp.zeros(shape=18, dtype=wp.float64)
        jt2 = wp.zeros(shape=18, dtype=wp.float64)
        row_t = wp.zeros(shape=18, dtype=wp.float64)
        force = wp.zeros(shape=18, dtype=wp.float64)
        corr = wp.zeros(shape=18, dtype=wp.float64)
        ln = wp.zeros(shape=1, dtype=wp.float64)
        lt = wp.zeros(shape=1, dtype=wp.float64)
        md = wp.zeros(shape=1, dtype=wp.int32)
        for r in range(4):
            if touching[r] == 0:
                continue
            for i in range(18):
                jt1[i] = ptJ[(r * 3 + 0) * 18 + i]
                jt2[i] = ptJ[(r * 3 + 2) * 18 + i]
                rn[i] = ptJ[(r * 3 + 1) * 18 + i]
            closing = row_dot(rn, v)
            if closing > F(-1e-12):
                continue
            svx = row_dot(jt1, v)
            svz = row_dot(jt2, v)
            planar = wp.sqrt(svx * svx + svz * svz)
            if planar <= cst.k_slip:
                continue
            for i in range(18):
                row_t[i] = (svx * jt1[i] + svz * jt2[i]) / planar
            friction_solve(v, inv, rn, row_t, F(0.0), F(0.0), cst.mu, 1, force, ln, lt, md)
            if md[0] > 0:
                mat_vec(inv, force, corr)
                for i in range(18):
                    v[i] = v[i] + corr[i]
                if ln[0] > caught:
                    caught = ln[0]
    for r in range(4):
        if touching[r] == 0:
            continue
        if R >= 10:
            rc[0] = 5
            return F(0.0)
        for i in range(18):
            rows[R * 18 + i] = ptJ[(r * 3 + 1) * 18 + i]
        floors[R] = F(0.0)
        R = R + 1
    if R > 0:
        p = wp.zeros(shape=18, dtype=wp.float64)
        mult = wp.zeros(shape=10, dtype=wp.float64)
        if project_rows(v, inv, rows, floors, R, n_stops, p, mult) == 0:
            rc[0] = 5
            return F(0.0)
        corr = wp.zeros(shape=18, dtype=wp.float64)
        mat_vec(inv, p, corr)
        for i in range(18):
            v[i] = v[i] + corr[i]
    pot = fk_eval(q, v, mdl.ax_rot, mdl.ax_axis, mdl.ax_slot, mdl.ax_slope, mdl.ax_const,
                  mdl.body_axoff, mdl.body_parent, mdl.body_mass, mdl.body_com, mdl.body_inertia,
                  mdl.body_fp, mdl.body_fc, mdl.chain_off, mdl.chain_ax, mdl.pt_body, mdl.pt_local,
                  mdl.pt_radius, cst.nbod, cst.naxes, cst.plane_y, cst.gy,
                  M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias)
    pen = wp.zeros(shape=4, dtype=wp.int32)
    npen = wp.int32(0)
    gaps = wp.zeros(shape=4, dtype=wp.float64)
    for r in range(4):
        g = gap_of_k(ptp, mdl.pt_radius, r * 2, cst.plane_y)
        if cst.contact != 0 and g < F(-1e-6):
            pen[npen] = r
            gaps[npen] = g
            npen = npen + 1
    if npen > 0:
        gram = wp.zeros(shape=16, dtype=wp.float64)
        rhs = wp.zeros(shape=4, dtype=wp.float64)
        lam = wp.zeros(shape=4, dtype=wp.float64)
        ra = wp.zeros(shape=18, dtype=wp.float64)
        ia = wp.zeros(shape=18, dtype=wp.float64)
        for a in range(npen):
            for i in range(18):
                ra[i] = ptJ[(pen[a] * 3 + 1) * 18 + i]
            mat_vec(inv, ra, ia)
            for b in range(npen):
                s = F(0.0)
                for i in range(18):
                    s = s + ia[i] * ptJ[(pen[b] * 3 + 1) * 18 + i]
                gram[a * 4 + b] = s
            rhs[a] = -gaps[a]
        if gram_factor4(gram, npen, rhs, lam) == 1:
            corr = wp.zeros(shape=18, dtype=wp.float64)
            for a in range(npen):
                for i in range(18):
                    ra[i] = ptJ[(pen[a] * 3 + 1) * 18 + i]
                mat_vec(inv, ra, ia)
                for i in range(18):
                    corr[i] = corr[i] + lam[a] * ia[i]
            dq_max = F(0.0)
            for i in range(18):
                if wp.abs(corr[i]) > dq_max:
                    dq_max = wp.abs(corr[i])
            if dq_max > F(0.05):
                rc[0] = 3
                return F(0.0)
            for i in range(18):
                q[i] = q[i] + corr[i]
    return caught


# ───────────────────────── the event-driven advance ─────────────────────────
@wp.func
def advance(q0: Q18, v0: Q18, w0: Q18, tau: Q18, h: F,
            mdl: ModelIn, cst: ModelConst,
            M: M324, gv: Q18, bv: Q18, fr: F224, frd: F224, frdd: F224,
            axw: F54, axpiv: F54, axdir: F54, ptp: F24, ptJ: F216, ptcop: F12, ptbias: F12,
            inv: M324, free: Q18, srq: Q18, srv: Q18,
            qa: Q18, va: Q18, qb: Q18, vb: Q18, qc: Q18, vc: Q18, qd: Q18, vd: Q18,
            qe: Q18, ve: Q18, we: Q18,
            sq: F576, sh: H16, sdep: I16, scl: I16,
            adv: I1, rc: I1,
            q1: Q18, v1: Q18, w1: Q18):
    # The C++ recursive advance() as an explicit LIFO interval stack over the
    # single "current state" thread (q1/v1/w1) -- DFS order preserved.
    for i in range(18):
        q1[i] = q0[i]
        v1[i] = v0[i]
        w1[i] = w0[i]
    if h < F(1e-12):
        return
    sp = wp.int32(0)
    rem = h
    depth = wp.int32(0)
    clamps = wp.int32(0)
    live = wp.zeros(shape=4, dtype=wp.int32)
    probe = wp.zeros(shape=4, dtype=wp.int32)
    it = wp.int32(0)
    done = wp.int32(0)
    rcv = wp.zeros(shape=1, dtype=wp.int32)
    while done == 0:
        it = it + 1
        if it > 4000:
            rc[0] = 6
            return
        if rem < F(1e-12):
            if sp > 0:
                sp = sp - 1
                rem = sh[sp]
                depth = sdep[sp]
                clamps = scl[sp]
                continue
            else:
                done = 1
                break
        adv[0] = adv[0] + 1
        if adv[0] > 3000:
            rc[0] = 2
            return
        if depth >= 10 + 6 * 8:
            rc[0] = 6
            return
        rcv[0] = 0
        caught = impact(q1, v1, mdl, cst, M, gv, bv, fr, frd, frdd,
                        axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, rcv)
        if rcv[0] != 0:
            rc[0] = rcv[0]
            return
        if cst.mu > F(0.0) and caught > F(1e-9) and depth < 5:
            sh[sp] = rem * F(0.5)
            sdep[sp] = depth + 3
            scl[sp] = clamps
            sp = sp + 1
            rem = rem * F(0.5)
            depth = depth + 3
            continue
        pot = fk_eval(q1, v1, mdl.ax_rot, mdl.ax_axis, mdl.ax_slot, mdl.ax_slope, mdl.ax_const,
                      mdl.body_axoff, mdl.body_parent, mdl.body_mass, mdl.body_com, mdl.body_inertia,
                      mdl.body_fp, mdl.body_fc, mdl.chain_off, mdl.chain_ax, mdl.pt_body, mdl.pt_local,
                      mdl.pt_radius, cst.nbod, cst.naxes, cst.plane_y, cst.gy,
                      M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias)
        for r in range(4):
            g = gap_of_k(ptp, mdl.pt_radius, r * 2, cst.plane_y)
            live[r] = wp.int32(1) if (cst.contact != 0 and g <= cst.k_touch) else wp.int32(0)
        rcs = free_step(q1, v1, w1, tau, live, rem, mdl, cst, M, gv, bv, fr, frd, frdd,
                        axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, srq, srv,
                        qa, va, qb, vb, qc, vc, qd, vd, qe, ve, we)
        if rcs != 0:
            rc[0] = rcs
            return
        hit = rem
        which = wp.int32(-1)
        khit = wp.int32(-1)
        wall = F(0.0)
        d = wp.int32(0)
        while d < 12:
            d = d + 1
            c = mdl.drive_coord[d - 1]
            low = wp.int32(1) if qe[c] < mdl.lower[c] else wp.int32(0)
            if low == 0 and qe[c] <= mdl.upper[c]:
                continue
            if low != 0:
                depth_v = mdl.lower[c] - qe[c]
            else:
                depth_v = qe[c] - mdl.upper[c]
            if depth_v <= F(1e-12):
                continue
            bound = mdl.lower[c] if low != 0 else mdl.upper[c]
            left = F(0.0)
            right = rem
            j = wp.int32(0)
            while j < 42:
                j = j + 1
                mid = (left + right) * F(0.5)
                rcb = free_step(q1, v1, w1, tau, live, mid, mdl, cst, M, gv, bv, fr, frd, frdd,
                                axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, srq, srv,
                                qa, va, qb, vb, qc, vc, qd, vd, qe, ve, we)
                if rcb != 0:
                    rc[0] = rcb
                    return
                if low != 0:
                    ok2 = wp.int32(1) if qe[c] <= bound else wp.int32(0)
                else:
                    ok2 = wp.int32(1) if qe[c] >= bound else wp.int32(0)
                if ok2 != 0:
                    right = mid
                else:
                    left = mid
            t = (left + right) * F(0.5)
            if t < hit or (t == hit and which >= 0 and (d - 1) < which):
                hit = t
                which = d - 1
                khit = -1
                wall = bound
        if cst.contact != 0:
            pot = fk_eval(qe, ve, mdl.ax_rot, mdl.ax_axis, mdl.ax_slot, mdl.ax_slope, mdl.ax_const,
                          mdl.body_axoff, mdl.body_parent, mdl.body_mass, mdl.body_com, mdl.body_inertia,
                          mdl.body_fp, mdl.body_fc, mdl.chain_off, mdl.chain_ax, mdl.pt_body, mdl.pt_local,
                          mdl.pt_radius, cst.nbod, cst.naxes, cst.plane_y, cst.gy,
                          M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias)
            r = wp.int32(0)
            while r < 4:
            # (while-form of the rep scan; body below)
                r = r + 1
                if live[r - 1] != 0:
                    continue
                g = gap_of_k(ptp, mdl.pt_radius, (r - 1) * 2, cst.plane_y)
                if g >= F(0.0):
                    continue
                for rr in range(4):
                    probe[rr] = live[rr]
                probe[r - 1] = 0
                left = F(0.0)
                right = rem
                j = wp.int32(0)
                while j < 42:
                    j = j + 1
                    mid = (left + right) * F(0.5)
                    rcb = free_step(q1, v1, w1, tau, probe, mid, mdl, cst, M, gv, bv, fr, frd, frdd,
                                    axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, srq, srv,
                                    qa, va, qb, vb, qc, vc, qd, vd, qe, ve, we)
                    if rcb != 0:
                        rc[0] = rcb
                        return
                    if gap_of_k(ptp, mdl.pt_radius, r * 2, cst.plane_y) <= F(0.0):
                        right = mid
                    else:
                        left = mid
                t = (left + right) * F(0.5)
                if t < hit:
                    hit = t
                    which = -2
                    khit = r - 1
                r = r
        if which == -1:
            for i in range(18):
                q1[i] = qe[i]
                v1[i] = ve[i]
                w1[i] = we[i]
            if sp > 0:
                sp = sp - 1
                rem = sh[sp]
                depth = sdep[sp]
                clamps = scl[sp]
                continue
            else:
                done = 1
                break
        if hit <= F(1e-12):
            if clamps >= 64:
                rc[0] = 6
                return
            if which >= 0:
                q1[mdl.drive_coord[which]] = wall
            rcv[0] = 0
            caught = impact(q1, v1, mdl, cst, M, gv, bv, fr, frd, frdd,
                            axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, rcv)
            if rcv[0] != 0:
                rc[0] = rcv[0]
                return
            clamps = clamps + 1
            continue
        if which == -2:
            for rr in range(4):
                probe[rr] = live[rr]
            probe[khit] = 0
            rcc = free_step(q1, v1, w1, tau, probe, hit, mdl, cst, M, gv, bv, fr, frd, frdd,
                            axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, srq, srv,
                            qa, va, qb, vb, qc, vc, qd, vd, qe, ve, we)
            if rcc != 0:
                rc[0] = rcc
                return
            for i in range(18):
                q1[i] = qe[i]
                v1[i] = ve[i]
                w1[i] = we[i]
            rcv[0] = 0
            caught = impact(q1, v1, mdl, cst, M, gv, bv, fr, frd, frdd,
                            axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, rcv)
            if rcv[0] != 0:
                rc[0] = rcv[0]
                return
            if cst.mu > F(0.0):
                sh[sp] = (rem - hit) * F(0.5)
                sdep[sp] = depth + 2
                scl[sp] = clamps
                sp = sp + 1
                rem = (rem - hit) * F(0.5)
                depth = depth + 1
            else:
                rem = rem - hit
                depth = depth + 1
            continue
        rcw = free_step(q1, v1, w1, tau, live, hit, mdl, cst, M, gv, bv, fr, frd, frdd,
                        axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, srq, srv,
                        qa, va, qb, vb, qc, vc, qd, vd, qe, ve, we)
        if rcw != 0:
            rc[0] = rcw
            return
        for i in range(18):
            q1[i] = qe[i]
            v1[i] = ve[i]
            w1[i] = we[i]
        q1[mdl.drive_coord[which]] = wall
        rcv[0] = 0
        caught = impact(q1, v1, mdl, cst, M, gv, bv, fr, frd, frdd,
                        axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, rcv)
        if rcv[0] != 0:
            rc[0] = rcv[0]
            return
        rem = rem - hit
        depth = depth + 1
        continue


# ───────────────────────── the closed-form IK helpers ─────────────────────────
@wp.func
def fore_ik_at(mdl: ModelIn, cst: ModelConst, fr: F224, leg: wp.int32, paw: F3, branch: wp.int32):
    off = cst.pelvis_row * 16
    rx = paw[0] - fr[off + 3]
    ry = paw[1] - fr[off + 7]
    rz = paw[2] - fr[off + 11]
    ml0 = mdl.fore_mount_local[leg * 3]
    ml1 = mdl.fore_mount_local[leg * 3 + 1]
    dx = fr[off + 0] * rx + fr[off + 4] * ry + fr[off + 8] * rz - ml0
    dy = fr[off + 1] * rx + fr[off + 5] * ry + fr[off + 9] * rz - ml1
    D = wp.sqrt(dx * dx + dy * dy)
    dmax = cst.fore_L1 + cst.fore_rho
    dmin = wp.abs(cst.fore_L1 - cst.fore_rho)
    sat = wp.int32(0)
    if D > dmax * (F(1.0) - F(1e-12)) or D < dmin + F(1e-9):
        sat = 1
        Dc = wp.min(wp.max(D, dmin + F(1e-9)), dmax * (F(1.0) - F(1e-12)))
        dx = dx * Dc / D
        dy = dy * Dc / D
        D = Dc
    ca = (D * D + cst.fore_L1 * cst.fore_L1 - cst.fore_rho * cst.fore_rho) / (F(2.0) * D * cst.fore_L1)
    ca = wp.min(F(1.0), wp.max(F(-1.0), ca))
    th1 = wp.atan2(dy, dx) + F(branch) * wp.acos(ca)
    q1 = th1 + PI * F(0.5)
    ex = dx - cst.fore_L1 * wp.cos(th1)
    ey = dy - cst.fore_L1 * wp.sin(th1)
    q2 = wp.atan2(ey, ex) - q1 - cst.fore_beta
    c1 = mdl.fore_coord[leg * 2]
    c2 = mdl.fore_coord[leg * 2 + 1]
    q1r = q1
    q2r = q2
    q1 = wp.min(mdl.upper[c1], wp.max(mdl.lower[c1], q1))
    q2 = wp.min(mdl.upper[c2], wp.max(mdl.lower[c2], q2))
    return q1, q2, q1r, q2r, sat


@wp.func
def fore_D_at(mdl: ModelIn, cst: ModelConst, fr: F224, leg: wp.int32, paw: F3) -> wp.float64:
    off = cst.pelvis_row * 16
    rx = paw[0] - fr[off + 3]
    ry = paw[1] - fr[off + 7]
    rz = paw[2] - fr[off + 11]
    ml0 = mdl.fore_mount_local[leg * 3]
    ml1 = mdl.fore_mount_local[leg * 3 + 1]
    dx = fr[off + 0] * rx + fr[off + 4] * ry + fr[off + 8] * rz - ml0
    dy = fr[off + 1] * rx + fr[off + 5] * ry + fr[off + 9] * rz - ml1
    return wp.sqrt(dx * dx + dy * dy)


@wp.func
def hind_ik_at(mdl: ModelIn, cst: ModelConst, fr: F224, tgt: F3, ap: F, branch: wp.int32):
    off = cst.pelvis_row * 16
    rx = tgt[0] - fr[off + 3]
    ry = tgt[1] - fr[off + 7]
    rz = tgt[2] - fr[off + 11]
    dx = fr[off + 0] * rx + fr[off + 4] * ry + fr[off + 8] * rz
    dy = fr[off + 1] * rx + fr[off + 5] * ry + fr[off + 9] * rz
    wx = dx - cst.hind_xm * wp.cos(ap)
    wy = dy - cst.hind_xm * wp.sin(ap)
    D = wp.sqrt(wx * wx + wy * wy)
    dmax = cst.hind_L1 + cst.hind_L2
    dmin = wp.abs(cst.hind_L1 - cst.hind_L2)
    Dc = wp.min(wp.max(D, dmin + F(1e-9)), dmax * (F(1.0) - F(1e-12)))
    ca = (Dc * Dc - cst.hind_L1 * cst.hind_L1 - cst.hind_L2 * cst.hind_L2) / (F(2.0) * cst.hind_L1 * cst.hind_L2)
    ca = wp.min(F(1.0), wp.max(F(-1.0), ca))
    k = F(branch) * wp.acos(ca)
    a1 = wp.atan2(wy, wx) - wp.atan2(-cst.hind_L1 - cst.hind_L2 * wp.cos(k), cst.hind_L2 * wp.sin(k))
    qh = a1
    qk = k
    qa = ap - a1 - k
    return qh, qk, qa


@wp.func
def tables_at(mdl: ModelIn, phi: F) -> Q18:
    out = wp.zeros(shape=18, dtype=wp.float64)
    p = phi - wp.floor(phi)
    x = p * F(20.0)
    k = wp.int32(x)
    if k > 19:
        k = 19
    f = x - F(k)
    out[0] = mdl.tab_hip[k] * (F(1.0) - f) + mdl.tab_hip[k + 1] * f + mdl.zeros4[0]
    out[1] = mdl.tab_knee[k] * (F(1.0) - f) + mdl.tab_knee[k + 1] * f + mdl.zeros4[1]
    out[2] = mdl.tab_ankle[k] * (F(1.0) - f) + mdl.tab_ankle[k + 1] * f + mdl.zeros4[2]
    out[3] = mdl.tab_mp[k] * (F(1.0) - f) + mdl.tab_mp[k + 1] * f + mdl.zeros4[3]
    return out


@wp.func
def vault_at(mdl: ModelIn, phi: F) -> wp.float64:
    p = phi - wp.floor(phi)
    x = p * F(20.0)
    k = wp.int32(x)
    if k > 19:
        k = 19
    f = x - F(k)
    return mdl.vault[k] * (F(1.0) - f) + mdl.vault[k + 1] * f

# ───────────────────────── the reset kernel ─────────────────────────
@wp.kernel
def reset_kernel(a_q0: wp.array(dtype=wp.float64), a_v0: wp.array(dtype=wp.float64),
                 a_touching0: wp.array(dtype=wp.int32), phi_l0: wp.float64, phi_r0: wp.float64,
                 settle_total: wp.int32, a_store_floor: wp.array(dtype=wp.float64), store_post: wp.float64,
                 a_q: wp.array(dtype=wp.float64), a_v: wp.array(dtype=wp.float64),
                 a_work: wp.array(dtype=wp.float64), a_last_torque: wp.array(dtype=wp.float64),
                 a_battery: wp.array(dtype=wp.float64), a_battery_post: wp.array(dtype=wp.float64),
                 a_phi: wp.array(dtype=wp.float64), a_touching: wp.array(dtype=wp.int32),
                 a_captured: wp.array(dtype=wp.int32), a_settle: wp.array(dtype=wp.int32),
                 a_ik_branch: wp.array(dtype=wp.int32), a_paw_target: wp.array(dtype=wp.float64),
                 a_paw_plant_y: wp.array(dtype=wp.float64),
                 a_swing_from: wp.array(dtype=wp.float64), a_swing_to: wp.array(dtype=wp.float64),
                 a_fore_t: wp.array(dtype=wp.float64), a_fore_stance: wp.array(dtype=wp.float64),
                 a_fore_cycle: wp.array(dtype=wp.float64), a_fore_mode: wp.array(dtype=wp.int32),
                 a_fore_entry: wp.array(dtype=wp.int32), a_fore_conv: wp.array(dtype=wp.int32),
                 a_fore_td_plant: wp.array(dtype=wp.int32), a_fore_clamped: wp.array(dtype=wp.int32),
                 a_fore_replants: wp.array(dtype=wp.int32), a_fore_td_count: wp.array(dtype=wp.int32),
                 a_hind_mode: wp.array(dtype=wp.int32), a_hind_t: wp.array(dtype=wp.float64),
                 a_hind_from: wp.array(dtype=wp.float64), a_hind_to: wp.array(dtype=wp.float64),
                 a_hind_plant_y: wp.array(dtype=wp.float64), a_hind_ap: wp.array(dtype=wp.float64),
                 a_hind_mp: wp.array(dtype=wp.float64), a_hind_branch: wp.array(dtype=wp.int32),
                 a_hind_held: wp.array(dtype=wp.int32), a_hind_last_fire: wp.array(dtype=wp.int64),
                 a_hind_last_td: wp.array(dtype=wp.int64), a_hind_fires: wp.array(dtype=wp.int32),
                 a_hind_tds: wp.array(dtype=wp.int32), a_hind_xoff: wp.array(dtype=wp.float64),
                 a_height_latched: wp.array(dtype=wp.int32),
                 a_cmd_vx: wp.array(dtype=wp.float64), a_cmd_live: wp.array(dtype=wp.int32),
                 a_cmd_first_tick: wp.array(dtype=wp.int64), a_cmd_fires: wp.array(dtype=wp.int32),
                 a_ticks: wp.array(dtype=wp.int64), a_adv_calls: wp.array(dtype=wp.int32),
                 a_refused: wp.array(dtype=wp.int32), a_refused_class: wp.array(dtype=wp.int32),
                 a_collapsed: wp.array(dtype=wp.int32)):
    e = wp.tid()
    for i in range(18):
        a_q[e * 18 + i] = a_q0[e * 18 + i]
        a_v[e * 18 + i] = a_v0[e * 18 + i]
        a_work[e * 18 + i] = wp.float64(0.0)
        a_last_torque[e * 18 + i] = wp.float64(0.0)
    for d in range(12):
        a_battery[e * 12 + d] = a_store_floor[d]
    a_battery_post[e] = store_post
    a_phi[e * 2] = phi_l0
    a_phi[e * 2 + 1] = phi_r0
    for l in range(2):
        a_touching[e * 2 + l] = a_touching0[e * 2 + l]
    a_captured[e] = 0
    a_settle[e] = settle_total
    a_ik_branch[e * 2] = 1
    a_ik_branch[e * 2 + 1] = 1
    for l in range(2):
        a_paw_plant_y[e * 2 + l] = wp.float64(0.0)
        a_fore_t[e * 2 + l] = wp.float64(0.0)
        a_fore_stance[e * 2 + l] = wp.float64(0.0)
        a_fore_cycle[e * 2 + l] = wp.float64(0.0)
        a_fore_mode[e * 2 + l] = 0
        a_fore_entry[e * 2 + l] = 0
        a_fore_conv[e * 2 + l] = 0
        a_fore_td_plant[e * 2 + l] = 1
        a_fore_clamped[e * 2 + l] = 0
        a_fore_replants[e * 2 + l] = 0
        a_fore_td_count[e * 2 + l] = 0
        a_hind_mode[e * 2 + l] = 0
        a_hind_t[e * 2 + l] = wp.float64(0.0)
        a_hind_plant_y[e * 2 + l] = wp.float64(0.0)
        a_hind_ap[e * 2 + l] = wp.float64(0.0)
        a_hind_mp[e * 2 + l] = wp.float64(0.0)
        a_hind_branch[e * 2 + l] = -1
        a_hind_held[e * 2 + l] = 0
        a_hind_last_fire[e * 2 + l] = wp.int64(0)
        a_hind_last_td[e * 2 + l] = wp.int64(0)
        a_hind_fires[e * 2 + l] = 0
        a_hind_tds[e * 2 + l] = wp.int32(0)
        a_hind_xoff[e * 2 + l] = wp.float64(0.0)
        for c in range(3):
            a_paw_target[e * 6 + l * 3 + c] = wp.float64(0.0)
            a_swing_from[e * 6 + l * 3 + c] = wp.float64(0.0)
            a_swing_to[e * 6 + l * 3 + c] = wp.float64(0.0)
            a_hind_from[e * 6 + l * 3 + c] = wp.float64(0.0)
            a_hind_to[e * 6 + l * 3 + c] = wp.float64(0.0)
    a_height_latched[e] = 0
    a_cmd_vx[e] = wp.float64(0.0)
    a_cmd_live[e] = 0
    a_cmd_first_tick[e] = wp.int64(-1)
    a_cmd_fires[e] = 0
    a_ticks[e] = wp.int64(0)
    a_adv_calls[e] = 0
    a_refused[e] = 0
    a_refused_class[e] = 0
    a_collapsed[e] = 0


# ───────────────────────── fore-clock helpers ─────────────────────────
@wp.func
def fore_target_headroom(mdl: ModelIn, cst: ModelConst, fr: F224, leg: wp.int32,
                         paw: F3, branch: wp.int32) -> wp.float64:
    d1a, d1b, q1r, q2r, d1c = fore_ik_at(mdl, cst, fr, leg, paw, branch)
    c1 = mdl.fore_coord[leg * 2]
    c2 = mdl.fore_coord[leg * 2 + 1]
    h1 = wp.min(q1r - mdl.lower[c1], mdl.upper[c1] - q1r)
    h2 = wp.min(q2r - mdl.lower[c2], mdl.upper[c2] - q2r)
    return wp.min(h1, h2)


@wp.func
def fore_follow(mdl: ModelIn, cst: ModelConst, fr: F224, leg: wp.int32,
                paw_t: wp.fixedarray(dtype=wp.float64, shape=6), branch: wp.int32):
    p = wp.zeros(shape=3, dtype=wp.float64)
    p[0] = paw_t[leg * 3]
    p[1] = paw_t[leg * 3 + 1]
    p[2] = paw_t[leg * 3 + 2]
    px = wp.zeros(shape=3, dtype=wp.float64)
    py = wp.zeros(shape=3, dtype=wp.float64)
    px[0] = p[0] + F(1e-3)
    px[1] = p[1]
    px[2] = p[2]
    py[0] = p[0] - F(1e-3)
    py[1] = p[1]
    py[2] = p[2]
    dirn = F(1.0)
    if fore_target_headroom(mdl, cst, fr, leg, px, branch) < fore_target_headroom(mdl, cst, fr, leg, py, branch):
        dirn = F(-1.0)
    dmax = cst.fore_L1 + cst.fore_rho
    lo = F(0.0)
    hi = F(2.0) * dmax
    for j in range(42):
        mid = (lo + hi) * F(0.5)
        t = wp.zeros(shape=3, dtype=wp.float64)
        t[0] = p[0] + dirn * mid
        t[1] = p[1]
        t[2] = p[2]
        if fore_D_at(mdl, cst, fr, leg, t) < dmax:
            lo = mid
        else:
            hi = mid
    edge = (lo + hi) * F(0.5)
    te = wp.zeros(shape=3, dtype=wp.float64)
    te[0] = p[0] + dirn * edge
    te[1] = p[1]
    te[2] = p[2]
    if fore_target_headroom(mdl, cst, fr, leg, te, branch) < F(0.1022):
        return te
    lo = F(0.0)
    hi = edge
    for j in range(42):
        mid = (lo + hi) * F(0.5)
        t = wp.zeros(shape=3, dtype=wp.float64)
        t[0] = p[0] + dirn * mid
        t[1] = p[1]
        t[2] = p[2]
        if fore_target_headroom(mdl, cst, fr, leg, t, branch) < F(0.1022):
            lo = mid
        else:
            hi = mid
    out = wp.zeros(shape=3, dtype=wp.float64)
    out[0] = p[0] + dirn * ((lo + hi) * F(0.5))
    out[1] = p[1]
    out[2] = p[2]
    return out


@wp.func
def fore_env(mdl: ModelIn, cst: ModelConst, fr: F224, leg: wp.int32,
             paw_t: wp.fixedarray(dtype=wp.float64, shape=6), v3: F) -> wp.float64:
    m16 = wp.zeros(shape=16, dtype=wp.float64)
    for i in range(16):
        m16[i] = fr[cst.pelvis_row * 16 + i]
    shw = wp.zeros(shape=3, dtype=wp.float64)
    ml = wp.zeros(shape=3, dtype=wp.float64)
    ml[0] = mdl.fore_mount_local[leg * 3]
    ml[1] = mdl.fore_mount_local[leg * 3 + 1]
    ml[2] = mdl.fore_mount_local[leg * 3 + 2]
    apply_point(m16, ml, shw)
    off = paw_t[leg * 3] - shw[0]
    hgt = wp.max(F(0.0), shw[1] - paw_t[leg * 3 + 1])
    dd = cst.fore_L1 + cst.fore_rho
    a2 = dd * dd - hgt * hgt
    amax = wp.sqrt(a2) if a2 > F(0.0) else F(0.0)
    vv = wp.max(F(0.0), v3)
    if vv <= F(1e-9):
        return F(0.0)
    env_s = (amax + off - vv * cst.dt) / vv / cst.dt
    if env_s < F(0.0):
        env_s = F(0.0)
    return env_s


@wp.func
def hind_deadline_fn(h_lt_o: wp.int64, h_lt_h: wp.int64, tair: wp.int32,
                     fold_budget: wp.int32, unload_ticks: wp.int32):
    # returns (deadline_tick, is_unload); 0 deadline = no completed other step
    dl = wp.int64(0)
    is_unload = wp.int32(0)
    if h_lt_o == wp.int64(0):
        return dl, is_unload
    fold = h_lt_o + wp.int64(fold_budget - tair - 1)
    dl = fold
    if h_lt_h != wp.int64(0):
        unload = h_lt_o + wp.int64(unload_ticks - 1)
        if unload < fold:
            dl = unload
            is_unload = 1
    return dl, is_unload


@wp.func
def paw_leg(paw_t: wp.fixedarray(dtype=wp.float64, shape=6), leg: wp.int32):
    out = wp.zeros(shape=3, dtype=wp.float64)
    out[0] = paw_t[leg * 3]
    out[1] = paw_t[leg * 3 + 1]
    out[2] = paw_t[leg * 3 + 2]
    return out


# ───────────────────────── the tick kernel ─────────────────────────
@wp.kernel
def tick_kernel(mdl: ModelIn, cst: ModelConst,
                a_q: wp.array(dtype=wp.float64), a_v: wp.array(dtype=wp.float64),
                a_work: wp.array(dtype=wp.float64), a_last_torque: wp.array(dtype=wp.float64),
                a_battery: wp.array(dtype=wp.float64), a_battery_post: wp.array(dtype=wp.float64),
                a_phi: wp.array(dtype=wp.float64), a_touching: wp.array(dtype=wp.int32),
                a_captured: wp.array(dtype=wp.int32), a_settle: wp.array(dtype=wp.int32),
                a_ik_branch: wp.array(dtype=wp.int32), a_paw_target: wp.array(dtype=wp.float64),
                a_paw_plant_y: wp.array(dtype=wp.float64),
                a_swing_from: wp.array(dtype=wp.float64), a_swing_to: wp.array(dtype=wp.float64),
                a_fore_t: wp.array(dtype=wp.float64), a_fore_stance: wp.array(dtype=wp.float64),
                a_fore_cycle: wp.array(dtype=wp.float64), a_fore_mode: wp.array(dtype=wp.int32),
                a_fore_entry: wp.array(dtype=wp.int32), a_fore_conv: wp.array(dtype=wp.int32),
                a_fore_td_plant: wp.array(dtype=wp.int32), a_fore_clamped: wp.array(dtype=wp.int32),
                a_fore_replants: wp.array(dtype=wp.int32), a_fore_td_count: wp.array(dtype=wp.int32),
                a_hind_mode: wp.array(dtype=wp.int32), a_hind_t: wp.array(dtype=wp.float64),
                a_hind_from: wp.array(dtype=wp.float64), a_hind_to: wp.array(dtype=wp.float64),
                a_hind_plant_y: wp.array(dtype=wp.float64), a_hind_ap: wp.array(dtype=wp.float64),
                a_hind_mp: wp.array(dtype=wp.float64), a_hind_branch: wp.array(dtype=wp.int32),
                a_hind_held: wp.array(dtype=wp.int32), a_hind_last_fire: wp.array(dtype=wp.int64),
                a_hind_last_td: wp.array(dtype=wp.int64), a_hind_fires: wp.array(dtype=wp.int32),
                a_hind_tds: wp.array(dtype=wp.int32), a_hind_xoff: wp.array(dtype=wp.float64),
                a_height_latched: wp.array(dtype=wp.int32),
                a_cmd_vx: wp.array(dtype=wp.float64), a_cmd_live: wp.array(dtype=wp.int32),
                a_cmd_first_tick: wp.array(dtype=wp.int64), a_cmd_fires: wp.array(dtype=wp.int32),
                a_ticks: wp.array(dtype=wp.int64), a_adv_calls: wp.array(dtype=wp.int32),
                a_refused: wp.array(dtype=wp.int32), a_refused_class: wp.array(dtype=wp.int32),
                a_collapsed: wp.array(dtype=wp.int32),
                rb: wp.array(dtype=wp.float64), rbi: wp.array(dtype=wp.int32)):
    e = wp.tid()
    if a_refused[e] != 0 or a_collapsed[e] != 0:
        return
    rc = wp.int32(0)
    tick = a_ticks[e]
    q = wp.zeros(shape=18, dtype=wp.float64)
    v = wp.zeros(shape=18, dtype=wp.float64)
    w = wp.zeros(shape=18, dtype=wp.float64)
    ltau = wp.zeros(shape=18, dtype=wp.float64)
    for i in range(18):
        q[i] = a_q[e * 18 + i]
        v[i] = a_v[e * 18 + i]
        w[i] = a_work[e * 18 + i]
        ltau[i] = a_last_torque[e * 18 + i]
    bat = wp.zeros(shape=12, dtype=wp.float64)
    for d in range(12):
        bat[d] = a_battery[e * 12 + d]
    bat_post = a_battery_post[e]
    phi = wp.zeros(shape=2, dtype=wp.float64)
    phi[0] = a_phi[e * 2]
    phi[1] = a_phi[e * 2 + 1]
    tch = wp.zeros(shape=2, dtype=wp.int32)
    tch[0] = a_touching[e * 2]
    tch[1] = a_touching[e * 2 + 1]
    capt = a_captured[e]
    settle_n = a_settle[e]
    ikb = wp.zeros(shape=2, dtype=wp.int32)
    ikb[0] = a_ik_branch[e * 2]
    ikb[1] = a_ik_branch[e * 2 + 1]
    paw_t = wp.zeros(shape=6, dtype=wp.float64)
    paw_y = wp.zeros(shape=2, dtype=wp.float64)
    swf = wp.zeros(shape=6, dtype=wp.float64)
    swt = wp.zeros(shape=6, dtype=wp.float64)
    f_t = wp.zeros(shape=2, dtype=wp.float64)
    f_st = wp.zeros(shape=2, dtype=wp.float64)
    f_cy = wp.zeros(shape=2, dtype=wp.float64)
    f_mo = wp.zeros(shape=2, dtype=wp.int32)
    f_en = wp.zeros(shape=2, dtype=wp.int32)
    f_cv = wp.zeros(shape=2, dtype=wp.int32)
    f_dp = wp.zeros(shape=2, dtype=wp.int32)
    f_cl = wp.zeros(shape=2, dtype=wp.int32)
    f_rp = wp.zeros(shape=2, dtype=wp.int32)
    f_td = wp.zeros(shape=2, dtype=wp.int32)
    for l in range(2):
        for c in range(3):
            paw_t[l * 3 + c] = a_paw_target[e * 6 + l * 3 + c]
            swf[l * 3 + c] = a_swing_from[e * 6 + l * 3 + c]
            swt[l * 3 + c] = a_swing_to[e * 6 + l * 3 + c]
        paw_y[l] = a_paw_plant_y[e * 2 + l]
        f_t[l] = a_fore_t[e * 2 + l]
        f_st[l] = a_fore_stance[e * 2 + l]
        f_cy[l] = a_fore_cycle[e * 2 + l]
        f_mo[l] = a_fore_mode[e * 2 + l]
        f_en[l] = a_fore_entry[e * 2 + l]
        f_cv[l] = a_fore_conv[e * 2 + l]
        f_dp[l] = a_fore_td_plant[e * 2 + l]
        f_cl[l] = a_fore_clamped[e * 2 + l]
        f_rp[l] = a_fore_replants[e * 2 + l]
        f_td[l] = a_fore_td_count[e * 2 + l]
    h_mo = wp.zeros(shape=2, dtype=wp.int32)
    h_t = wp.zeros(shape=2, dtype=wp.float64)
    h_from = wp.zeros(shape=6, dtype=wp.float64)
    h_to = wp.zeros(shape=6, dtype=wp.float64)
    h_py = wp.zeros(shape=2, dtype=wp.float64)
    h_ap = wp.zeros(shape=2, dtype=wp.float64)
    h_mp = wp.zeros(shape=2, dtype=wp.float64)
    h_br = wp.zeros(shape=2, dtype=wp.int32)
    h_held = wp.zeros(shape=2, dtype=wp.int32)
    h_lf = wp.zeros(shape=2, dtype=wp.int64)
    h_lt = wp.zeros(shape=2, dtype=wp.int64)
    h_fi = wp.zeros(shape=2, dtype=wp.int32)
    h_tds = wp.zeros(shape=2, dtype=wp.int32)
    h_xo = wp.zeros(shape=2, dtype=wp.float64)
    for l in range(2):
        h_mo[l] = a_hind_mode[e * 2 + l]
        h_t[l] = a_hind_t[e * 2 + l]
        h_py[l] = a_hind_plant_y[e * 2 + l]
        h_ap[l] = a_hind_ap[e * 2 + l]
        h_mp[l] = a_hind_mp[e * 2 + l]
        h_br[l] = a_hind_branch[e * 2 + l]
        h_held[l] = a_hind_held[e * 2 + l]
        h_lf[l] = a_hind_last_fire[e * 2 + l]
        h_lt[l] = a_hind_last_td[e * 2 + l]
        h_fi[l] = a_hind_fires[e * 2 + l]
        h_tds[l] = a_hind_tds[e * 2 + l]
        h_xo[l] = a_hind_xoff[e * 2 + l]
        for c in range(3):
            h_from[l * 3 + c] = a_hind_from[e * 6 + l * 3 + c]
            h_to[l * 3 + c] = a_hind_to[e * 6 + l * 3 + c]
    h_latched = a_height_latched[e]
    cmd_v = a_cmd_vx[e]
    cmd_on = a_cmd_live[e]
    cmd_first = a_cmd_first_tick[e]
    cmd_fires = a_cmd_fires[e]
    adv = wp.zeros(shape=1, dtype=wp.int32)
    adv[0] = a_adv_calls[e]

    Tf = cst.t_cycle / cst.dt
    tair = F(cst.tair)
    walking = wp.int32(1)
    if cst.gait_enabled == 0 or settle_n > 0 or cst.reflex_level == 0:
        walking = 0
    M = wp.zeros(shape=324, dtype=wp.float64)
    gv = wp.zeros(shape=18, dtype=wp.float64)
    bv = wp.zeros(shape=18, dtype=wp.float64)
    fr = wp.zeros(shape=224, dtype=wp.float64)
    frd = wp.zeros(shape=224, dtype=wp.float64)
    frdd = wp.zeros(shape=224, dtype=wp.float64)
    axw = wp.zeros(shape=54, dtype=wp.float64)
    axpiv = wp.zeros(shape=54, dtype=wp.float64)
    axdir = wp.zeros(shape=54, dtype=wp.float64)
    ptp = wp.zeros(shape=24, dtype=wp.float64)
    ptJ = wp.zeros(shape=216, dtype=wp.float64)
    ptcop = wp.zeros(shape=12, dtype=wp.float64)
    ptbias = wp.zeros(shape=12, dtype=wp.float64)
    inv = wp.zeros(shape=324, dtype=wp.float64)
    free = wp.zeros(shape=18, dtype=wp.float64)
    qa = wp.zeros(shape=18, dtype=wp.float64)
    va = wp.zeros(shape=18, dtype=wp.float64)
    qb = wp.zeros(shape=18, dtype=wp.float64)
    vb = wp.zeros(shape=18, dtype=wp.float64)
    qc = wp.zeros(shape=18, dtype=wp.float64)
    vc = wp.zeros(shape=18, dtype=wp.float64)
    qd = wp.zeros(shape=18, dtype=wp.float64)
    vd = wp.zeros(shape=18, dtype=wp.float64)
    qe = wp.zeros(shape=18, dtype=wp.float64)
    ve = wp.zeros(shape=18, dtype=wp.float64)
    we = wp.zeros(shape=18, dtype=wp.float64)
    sq = wp.zeros(shape=576, dtype=wp.float64)
    sh16 = wp.zeros(shape=16, dtype=wp.float64)
    sdep = wp.zeros(shape=16, dtype=wp.int32)
    scl = wp.zeros(shape=16, dtype=wp.int32)
    tr_q = wp.zeros(shape=18, dtype=wp.float64)
    tr_v = wp.zeros(shape=18, dtype=wp.float64)
    tr_w = wp.zeros(shape=18, dtype=wp.float64)
    cd_q = wp.zeros(shape=18, dtype=wp.float64)
    cd_v = wp.zeros(shape=18, dtype=wp.float64)
    cd_w = wp.zeros(shape=18, dtype=wp.float64)
    tau = wp.zeros(shape=18, dtype=wp.float64)
    srq = wp.zeros(shape=18, dtype=wp.float64)
    srv = wp.zeros(shape=18, dtype=wp.float64)
    scales = wp.zeros(shape=13, dtype=wp.float64)
    round_n = wp.int32(0)
    dsf = wp.zeros(shape=1, dtype=wp.int32)
    trial_q = wp.zeros(shape=18, dtype=wp.float64)
    trial_v = wp.zeros(shape=18, dtype=wp.float64)
    trial_w = wp.zeros(shape=18, dtype=wp.float64)
    o_q = wp.zeros(shape=18, dtype=wp.float64)
    o_v = wp.zeros(shape=18, dtype=wp.float64)
    o_w = wp.zeros(shape=18, dtype=wp.float64)
    cur_w = wp.zeros(shape=18, dtype=wp.float64)
    eff = wp.zeros(shape=18, dtype=wp.float64)
    lta = wp.zeros(shape=18, dtype=wp.float64)

    if settle_n > 0:
        settle_n = settle_n - 1

    # ── the tick-start evaluation (eval0) ──
    pot = fk_eval(q, v, mdl.ax_rot, mdl.ax_axis, mdl.ax_slot, mdl.ax_slope, mdl.ax_const,
                  mdl.body_axoff, mdl.body_parent, mdl.body_mass, mdl.body_com, mdl.body_inertia,
                  mdl.body_fp, mdl.body_fc, mdl.chain_off, mdl.chain_ax, mdl.pt_body, mdl.pt_local,
                  mdl.pt_radius, cst.nbod, cst.naxes, cst.plane_y, cst.gy,
                  M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias)

    # the plant law's v argument (the adapter's authority law)
    v_eff = wp.max(F(0.0), v[3])
    if cmd_on != 0:
        cmd_fires = cmd_fires + 1
        if cmd_first < wp.int64(0):
            cmd_first = tick
        v_eff = cmd_v

    # ── the plant capture at the settle end (wave 12/13/14) ──
    if capt == 0 and cst.settle_total > 0 and settle_n == 0 and walking != 0 and cst.power != 0 and cst.contact != 0:
        for leg in range(2):
            hpt = mdl.fore_heel_pt[leg]
            prl = wp.zeros(shape=3, dtype=wp.float64)
            for c in range(3):
                prl[c] = (mdl.pt_local[hpt * 3 + c] + mdl.pt_local[(hpt + 1) * 3 + c]) * F(0.5)
            T16 = wp.zeros(shape=16, dtype=wp.float64)
            fb = mdl.pt_body[hpt]
            for i in range(16):
                T16[i] = fr[fb * 16 + i]
            pw = wp.zeros(shape=3, dtype=wp.float64)
            apply_point(T16, prl, pw)
            for c in range(3):
                paw_t[leg * 3 + c] = pw[c]
            c1 = mdl.fore_coord[leg * 2]
            c2 = mdl.fore_coord[leg * 2 + 1]
            qa1, qa2, qa1r, qa2r, sata = fore_ik_at(mdl, cst, fr, leg, pw, 1)
            qb1, qb2, qb1r, qb2r, satb = fore_ik_at(mdl, cst, fr, leg, pw, -1)
            e0 = wp.sqrt((qa1 - q[c1]) * (qa1 - q[c1]) + (qa2 - q[c2]) * (qa2 - q[c2]))
            e1 = wp.sqrt((qb1 - q[c1]) * (qb1 - q[c1]) + (qb2 - q[c2]) * (qb2 - q[c2]))
            ikb[leg] = 1
            if e1 < e0:
                ikb[leg] = -1
        capt = 1
        # arm_fore_clock (the wave-14 lateral-grid arm)
        for leg in range(2):
            paw_y[leg] = paw_t[leg * 3 + 1]
            shw = wp.zeros(shape=3, dtype=wp.float64)
            ml = wp.zeros(shape=3, dtype=wp.float64)
            m16 = wp.zeros(shape=16, dtype=wp.float64)
            for i in range(16):
                m16[i] = fr[cst.pelvis_row * 16 + i]
            ml[0] = mdl.fore_mount_local[leg * 3]
            ml[1] = mdl.fore_mount_local[leg * 3 + 1]
            ml[2] = mdl.fore_mount_local[leg * 3 + 2]
            apply_point(m16, ml, shw)
            off = paw_t[leg * 3] - shw[0]
            xoff = v_eff * (cst.duty * cst.t_cycle) * F(0.5)
            hgt = wp.max(F(0.0), shw[1] - paw_y[leg])
            dd = cst.fore_L1 + cst.fore_rho
            a2 = dd * dd - hgt * hgt
            amax = wp.sqrt(a2) if a2 > F(0.0) else F(0.0)
            vv = wp.max(F(0.0), v[3])
            tau1 = F(0.0)
            if off < F(0.0) and vv > F(1e-9):
                f_en[leg] = 1
                env_s = (amax + off - vv * cst.dt) / vv
                if env_s < F(0.0):
                    env_s = F(0.0)
                tau1 = wp.max(F(0.0), env_s / cst.dt - (tair + F(1.0)))
            elif xoff > F(0.0) and vv > F(1e-9):
                lift_wait = wp.max(F(0.0), cst.duty - phi[leg]) * cst.t_cycle + F(0.25) * cst.t_cycle
                tau_env = (amax + off - vv * cst.dt) / vv
                if tau_env < F(0.0):
                    tau_env = F(0.0)
                tau1 = wp.min(lift_wait, tau_env)
            f_st[leg] = tau1 / cst.dt
            if f_en[leg] != 0:
                f_cy[leg] = f_st[leg] + tair
            else:
                f_cy[leg] = f_st[leg] + (F(1.0) - cst.duty) / cst.dt
            f_t[leg] = F(0.0)
            f_mo[leg] = 0
            f_cv[leg] = 0
            f_cl[leg] = 0
            f_rp[leg] = 0
            f_td[leg] = 0

    # ── the contact-reset hybrid clock (Section 5.1, wave 22 classes) ──
    if walking != 0:
        for leg in range(2):
            g0 = gap_of_k(ptp, mdl.pt_radius, leg * 2, cst.plane_y)
            g1 = gap_of_k(ptp, mdl.pt_radius, leg * 2 + 1, cst.plane_y)
            gmin = wp.min(g0, g1)
            cls = wp.int32(0)
            if gmin <= cst.k_touch:
                cls = 1
            elif gmin > cst.k_touch + cst.k_release:
                cls = 0
            else:
                cls = tch[leg]
            if cls != 0 and tch[leg] == 0:
                phi[leg] = F(0.0)
            else:
                phi[leg] = (phi[leg] + cst.dt / cst.t_cycle) % F(1.0)
            tch[leg] = cls
    else:
        for leg in range(2):
            g0 = gap_of_k(ptp, mdl.pt_radius, leg * 2, cst.plane_y)
            g1 = gap_of_k(ptp, mdl.pt_radius, leg * 2 + 1, cst.plane_y)
            gmin = wp.min(g0, g1)
            cls = wp.int32(0)
            if gmin <= cst.k_touch:
                cls = 1
            elif gmin > cst.k_touch + cst.k_release:
                cls = 0
            else:
                cls = tch[leg]
            tch[leg] = cls

    # ── the stepping-strut fore clock (the deterministic core) ──
    if walking != 0 and capt != 0:
        leg = wp.int32(-1)
        while leg < 1:
            leg = leg + 1
            o = 1 - leg
            f_t[leg] = f_t[leg] + F(1.0)
            if f_mo[leg] == 1:
                sg = (f_t[leg] - f_st[leg]) / (f_cy[leg] - f_st[leg])
                if sg < F(0.0):
                    sg = F(0.0)
                if sg > F(1.0):
                    sg = F(1.0)
                carch = F(2.0) * mdl.pt_radius[mdl.fore_heel_pt[leg]]
                # DEFERRED-W24: the pocket-clear hold; the standard line+arch
                for c in range(3):
                    paw_t[leg * 3 + c] = swf[leg * 3 + c] + (swt[leg * 3 + c] - swf[leg * 3 + c]) * sg
                paw_t[leg * 3 + 1] = paw_t[leg * 3 + 1] + carch * wp.sin(PI * sg)
            if f_mo[leg] == 0 and f_t[leg] >= f_st[leg]:
                c1 = mdl.fore_coord[leg * 2]
                c2 = mdl.fore_coord[leg * 2 + 1]
                h1 = wp.min(q[c1] - mdl.lower[c1], mdl.upper[c1] - q[c1])
                h2 = wp.min(q[c2] - mdl.lower[c2], mdl.upper[c2] - q[c2])
                wall_hr = wp.min(h1, h2)
                wall_bound = wp.int32(0)
                if wall_hr <= F(0.0511):
                    wall_bound = 1
                gated = wp.int32(0)
                if f_en[leg] != 0:
                    if f_mo[o] == 1:
                        gated = 1
                    elif f_mo[o] == 0 and f_en[o] != 0 and f_dp[o] != 0 and f_t[o] < F(1.0):
                        gated = 1
                    elif f_mo[o] == 0 and f_en[o] != 0 and f_t[o] >= f_st[o]:
                        o_prior = wp.int32(0)
                        if f_t[o] > f_t[leg]:
                            o_prior = 1
                        if f_t[o] == f_t[leg]:
                            m16 = wp.zeros(shape=16, dtype=wp.float64)
                            for i in range(16):
                                m16[i] = fr[cst.pelvis_row * 16 + i]
                            sha = wp.zeros(shape=3, dtype=wp.float64)
                            ml0 = wp.zeros(shape=3, dtype=wp.float64)
                            ml0[0] = mdl.fore_mount_local[leg * 3]
                            ml0[1] = mdl.fore_mount_local[leg * 3 + 1]
                            ml0[2] = mdl.fore_mount_local[leg * 3 + 2]
                            apply_point(m16, ml0, sha)
                            sho = wp.zeros(shape=3, dtype=wp.float64)
                            ml1 = wp.zeros(shape=3, dtype=wp.float64)
                            ml1[0] = mdl.fore_mount_local[o * 3]
                            ml1[1] = mdl.fore_mount_local[o * 3 + 1]
                            ml1[2] = mdl.fore_mount_local[o * 3 + 2]
                            apply_point(m16, ml1, sho)
                            if (paw_t[o * 3] - sho[0]) < (paw_t[leg * 3] - sha[0]):
                                o_prior = 1
                        gated = o_prior
                plt = paw_leg(paw_t, leg)
                dq1, dq2, tq1r, tq2r, dsat = fore_ik_at(mdl, cst, fr, leg, plt, ikb[leg])
                th1 = wp.min(tq1r - mdl.lower[c1], mdl.upper[c1] - tq1r)
                th2 = wp.min(tq2r - mdl.lower[c2], mdl.upper[c2] - tq2r)
                thin_seat = wp.int32(0)
                if wp.min(th1, th2) < F(0.1022):
                    thin_seat = 1
                due = wp.int32(0)
                if f_t[leg] >= f_st[leg] or wall_bound != 0:
                    due = 1
                env_t = fore_env(mdl, cst, fr, leg, paw_t, v[3])
                act = wp.int32(0)
                seat = wp.zeros(shape=3, dtype=wp.float64)
                if gated == 0 and due != 0 and (thin_seat == 0 or wall_bound == 0):
                    act = 1
                elif gated == 0 and due != 0 and thin_seat != 0 and wall_bound != 0:
                    seat = fore_follow(mdl, cst, fr, leg, paw_t, ikb[leg])
                    dsx = seat[0] - paw_t[leg * 3]
                    dsy = seat[1] - paw_t[leg * 3 + 1]
                    if wp.sqrt(dsx * dsx + dsy * dsy) < cst.k_touch:
                        act = 1
                    else:
                        act = 2
                elif gated != 0 and wall_bound != 0 and wall_hr < F(0.008040):
                    # the wave-26 wall-adjacent wait override (kWaitFloor)
                    act = 1
                elif f_t[leg] >= f_cy[leg] or f_t[leg] >= env_t:
                    # the wave-20 in-place ground re-plant
                    if wall_bound != 0 and wp.min(th1, th2) < F(0.1022):
                        seat = fore_follow(mdl, cst, fr, leg, paw_t, ikb[leg])
                        dsx = seat[0] - paw_t[leg * 3]
                        dsy = seat[1] - paw_t[leg * 3 + 1]
                        if wp.sqrt(dsx * dsx + dsy * dsy) < cst.k_touch:
                            act = 3
                        else:
                            act = 2
                    else:
                        act = 3
                if act == 1:
                    f_mo[leg] = 1
                    if f_en[leg] != 0:
                        f_t[leg] = F(0.0)
                    hpt = mdl.fore_heel_pt[leg]
                    prl = wp.zeros(shape=3, dtype=wp.float64)
                    for c in range(3):
                        prl[c] = (mdl.pt_local[hpt * 3 + c] + mdl.pt_local[(hpt + 1) * 3 + c]) * F(0.5)
                    T16 = wp.zeros(shape=16, dtype=wp.float64)
                    fb = mdl.pt_body[hpt]
                    for i in range(16):
                        T16[i] = fr[fb * 16 + i]
                    pw = wp.zeros(shape=3, dtype=wp.float64)
                    apply_point(T16, prl, pw)
                    m16 = wp.zeros(shape=16, dtype=wp.float64)
                    for i in range(16):
                        m16[i] = fr[cst.pelvis_row * 16 + i]
                    shw = wp.zeros(shape=3, dtype=wp.float64)
                    ml = wp.zeros(shape=3, dtype=wp.float64)
                    ml[0] = mdl.fore_mount_local[leg * 3]
                    ml[1] = mdl.fore_mount_local[leg * 3 + 1]
                    ml[2] = mdl.fore_mount_local[leg * 3 + 2]
                    apply_point(m16, ml, shw)
                    for c in range(3):
                        swf[leg * 3 + c] = pw[c]
                    xoff = v_eff * (cst.duty * cst.t_cycle) * F(0.5)
                    hgt = wp.max(F(0.0), shw[1] - paw_y[leg])
                    dd = cst.fore_L1 + cst.fore_rho
                    a2 = dd * dd - hgt * hgt
                    amax = wp.sqrt(a2) if a2 > F(0.0) else F(0.0)
                    if xoff > amax:
                        xoff = amax
                        f_cl[leg] = f_cl[leg] + 1
                    swt[leg * 3] = shw[0] + xoff
                    swt[leg * 3 + 1] = paw_y[leg]
                    swt[leg * 3 + 2] = pw[2]
                elif act == 2:
                    for c in range(3):
                        paw_t[leg * 3 + c] = seat[c]
                    f_dp[leg] = 0
                    f_rp[leg] = f_rp[leg] + 1
                    f_t[leg] = F(0.0)
                    env_t2 = fore_env(mdl, cst, fr, leg, paw_t, v[3])
                    f_st[leg] = wp.max(F(0.0), env_t2 - (tair + F(1.0)))
                    f_cy[leg] = f_st[leg] + tair
                elif act == 3:
                    hpt = mdl.fore_heel_pt[leg]
                    prl = wp.zeros(shape=3, dtype=wp.float64)
                    for c in range(3):
                        prl[c] = (mdl.pt_local[hpt * 3 + c] + mdl.pt_local[(hpt + 1) * 3 + c]) * F(0.5)
                    T16 = wp.zeros(shape=16, dtype=wp.float64)
                    fb = mdl.pt_body[hpt]
                    for i in range(16):
                        T16[i] = fr[fb * 16 + i]
                    pw = wp.zeros(shape=3, dtype=wp.float64)
                    apply_point(T16, prl, pw)
                    for c in range(3):
                        paw_t[leg * 3 + c] = pw[c]
                    cc1 = mdl.fore_coord[leg * 2]
                    cc2 = mdl.fore_coord[leg * 2 + 1]
                    qa1, qa2, qa1r, qa2r, sata = fore_ik_at(mdl, cst, fr, leg, pw, 1)
                    qb1, qb2, qb1r, qb2r, satb = fore_ik_at(mdl, cst, fr, leg, pw, -1)
                    e0 = wp.sqrt((qa1 - q[cc1]) * (qa1 - q[cc1]) + (qa2 - q[cc2]) * (qa2 - q[cc2]))
                    e1 = wp.sqrt((qb1 - q[cc1]) * (qb1 - q[cc1]) + (qb2 - q[cc2]) * (qb2 - q[cc2]))
                    ikb[leg] = 1
                    if e1 < e0:
                        ikb[leg] = -1
                    f_dp[leg] = 0
                    f_rp[leg] = f_rp[leg] + 1
                    f_t[leg] = F(0.0)
                    env_t2 = fore_env(mdl, cst, fr, leg, paw_t, v[3])
                    f_st[leg] = wp.max(F(0.0), env_t2 - (tair + F(1.0)))
                    f_cy[leg] = f_st[leg] + tair
            if f_t[leg] >= f_cy[leg]:
                # TOUCHDOWN: re-capture the actual paw
                hpt = mdl.fore_heel_pt[leg]
                prl = wp.zeros(shape=3, dtype=wp.float64)
                for c in range(3):
                    prl[c] = (mdl.pt_local[hpt * 3 + c] + mdl.pt_local[(hpt + 1) * 3 + c]) * F(0.5)
                T16 = wp.zeros(shape=16, dtype=wp.float64)
                fb = mdl.pt_body[hpt]
                for i in range(16):
                    T16[i] = fr[fb * 16 + i]
                pw = wp.zeros(shape=3, dtype=wp.float64)
                apply_point(T16, prl, pw)
                for c in range(3):
                    paw_t[leg * 3 + c] = pw[c]
                cc1 = mdl.fore_coord[leg * 2]
                cc2 = mdl.fore_coord[leg * 2 + 1]
                qa1, qa2, qa1r, qa2r, sata = fore_ik_at(mdl, cst, fr, leg, pw, 1)
                qb1, qb2, qb1r, qb2r, satb = fore_ik_at(mdl, cst, fr, leg, pw, -1)
                e0 = wp.sqrt((qa1 - q[cc1]) * (qa1 - q[cc1]) + (qa2 - q[cc2]) * (qa2 - q[cc2]))
                e1 = wp.sqrt((qb1 - q[cc1]) * (qb1 - q[cc1]) + (qb2 - q[cc2]) * (qb2 - q[cc2]))
                ikb[leg] = 1
                if e1 < e0:
                    ikb[leg] = -1
                f_rp[leg] = f_rp[leg] + 1
                f_td[leg] = f_td[leg] + 1
                f_t[leg] = F(0.0)
                f_mo[leg] = 0
                f_dp[leg] = 1
                if f_en[leg] != 0:
                    m16 = wp.zeros(shape=16, dtype=wp.float64)
                    for i in range(16):
                        m16[i] = fr[cst.pelvis_row * 16 + i]
                    shw = wp.zeros(shape=3, dtype=wp.float64)
                    ml = wp.zeros(shape=3, dtype=wp.float64)
                    ml[0] = mdl.fore_mount_local[leg * 3]
                    ml[1] = mdl.fore_mount_local[leg * 3 + 1]
                    ml[2] = mdl.fore_mount_local[leg * 3 + 2]
                    apply_point(m16, ml, shw)
                    if paw_t[leg * 3] - shw[0] >= F(0.0):
                        f_en[leg] = 0
                if f_en[leg] != 0:
                    env_t2 = fore_env(mdl, cst, fr, leg, paw_t, v[3])
                    f_st[leg] = wp.max(F(0.0), env_t2 - (tair + F(1.0)))
                    f_cy[leg] = f_st[leg] + tair
                elif f_cv[leg] != 0:
                    f_st[leg] = cst.duty / cst.dt
                    f_cy[leg] = Tf
                else:
                    # the grid convergence search (wave 15)
                    swing = (F(1.0) - cst.duty) / cst.dt
                    slot = F(cst.settle_total)
                    if leg == 0:
                        slot = slot + F(0.25) * Tf
                    else:
                        slot = slot + F(0.75) * Tf
                    while slot <= F(tick) + F(1.0) + swing:
                        slot = slot + Tf
                    dslot = slot - (F(tick) + F(1.0) + Tf)
                    if wp.abs(dslot) <= F(0.5):
                        f_cv[leg] = 1
                        f_st[leg] = cst.duty / cst.dt
                        f_cy[leg] = Tf
                    else:
                        m16 = wp.zeros(shape=16, dtype=wp.float64)
                        for i in range(16):
                            m16[i] = fr[cst.pelvis_row * 16 + i]
                        shw = wp.zeros(shape=3, dtype=wp.float64)
                        ml = wp.zeros(shape=3, dtype=wp.float64)
                        ml[0] = mdl.fore_mount_local[leg * 3]
                        ml[1] = mdl.fore_mount_local[leg * 3 + 1]
                        ml[2] = mdl.fore_mount_local[leg * 3 + 2]
                        apply_point(m16, ml, shw)
                        offc = paw_t[leg * 3] - shw[0]
                        vv = wp.max(F(0.0), v[3])
                        hgt = wp.max(F(0.0), shw[1] - paw_t[leg * 3 + 1])
                        dd = cst.fore_L1 + cst.fore_rho
                        a2 = dd * dd - hgt * hgt
                        amax = wp.sqrt(a2) if a2 > F(0.0) else F(0.0)
                        envc = F(-1.0)
                        if vv > F(1e-9):
                            envc = (offc + amax - vv * cst.dt) / vv / cst.dt
                        smin = swing
                        found = wp.int32(0)
                        for kk in range(1, 9):
                            for ww in range(2):
                                step = (dslot - (F(ww) * Tf)) / F(kk)
                                stc = cst.duty / cst.dt + step
                                if stc < smin - F(1e-9):
                                    continue
                                if step > F(0.0) and (envc < F(0.0) or stc > envc + F(1e-9)):
                                    continue
                                f_st[leg] = stc
                                f_cy[leg] = stc + swing
                                if kk == 1 and ww == 0:
                                    f_cv[leg] = 1
                                found = 1
                                break
                            if found != 0:
                                break
                        if found == 0:
                            f_st[leg] = cst.duty / cst.dt
                            f_cy[leg] = Tf

    # ── the height emergency (wave 27) ──
    if walking != 0 and capt != 0 and cst.height_crit > F(0.0) and h_latched == 0:
        m16 = wp.zeros(shape=16, dtype=wp.float64)
        for i in range(16):
            m16[i] = fr[cst.pelvis_row * 16 + i]
        shl = wp.zeros(shape=3, dtype=wp.float64)
        ml0 = wp.zeros(shape=3, dtype=wp.float64)
        ml0[0] = mdl.fore_mount_local[0]
        ml0[1] = mdl.fore_mount_local[1]
        ml0[2] = mdl.fore_mount_local[2]
        apply_point(m16, ml0, shl)
        shr = wp.zeros(shape=3, dtype=wp.float64)
        ml1 = wp.zeros(shape=3, dtype=wp.float64)
        ml1[0] = mdl.fore_mount_local[3]
        ml1[1] = mdl.fore_mount_local[4]
        ml1[2] = mdl.fore_mount_local[5]
        apply_point(m16, ml1, shr)
        shmin = wp.min(shl[1], shr[1])
        if shmin - cst.height_crit <= cst.height_floor:
            h_latched = 1

    # ── the hind step law (waves 28/29/31/32/35/36/38 core) ──
    if walking != 0 and capt != 0 and h_latched != 0:
        for hl in range(2):
            if h_mo[hl] == 1:
                if h_held[hl] != 0:
                    g1 = gap_of_k(ptp, mdl.pt_radius, mdl.hind_heel_pt[hl], cst.plane_y)
                    g2 = gap_of_k(ptp, mdl.pt_radius, mdl.hind_heel_pt[hl] + 1, cst.plane_y)
                    if wp.min(g1, g2) > cst.k_touch + cst.k_release:
                        h_held[hl] = 0
                h_t[hl] = h_t[hl] + F(1.0)
                if h_t[hl] >= tair:
                    g1 = gap_of_k(ptp, mdl.pt_radius, mdl.hind_heel_pt[hl], cst.plane_y)
                    g2 = gap_of_k(ptp, mdl.pt_radius, mdl.hind_heel_pt[hl] + 1, cst.plane_y)
                    if wp.min(g1, g2) <= cst.k_touch:
                        h_mo[hl] = 0
                        h_t[hl] = F(0.0)
                        h_held[hl] = 0
                        h_lt[hl] = tick
                        h_tds[hl] = h_tds[hl] + 1
        for hl in range(2):
            o = 1 - hl
            if h_mo[hl] != 0:
                continue
            # the alternation-due predicate (wave 29/35 concentration form)
            alt_due = wp.int32(0)
            dl, is_unload = hind_deadline_fn(h_lt[o], h_lt[hl], cst.tair, cst.fold_budget, cst.unload_ticks)
            if h_lt[o] != wp.int64(0):
                conc = wp.int32(1)
                if h_lf[o] < h_lt[hl] and h_lt[o] < h_lt[hl]:
                    conc = 0
                if conc != 0 and phi[hl] < cst.toe_off:
                    wait = (cst.toe_off - phi[hl]) / (cst.dt / cst.t_cycle)
                    if F(tick) + wait > F(dl):
                        alt_due = 1
            live_slot = wp.int32(0)
            if phi[hl] >= cst.toe_off and tch[hl] != 0:
                live_slot = 1
            alt_fire = wp.int32(0)
            if alt_due != 0 and tch[hl] != 0:
                alt_fire = 1
            if live_slot == 0 and alt_fire == 0:
                continue
            gated = wp.int32(0)
            gated_b = wp.int32(0)
            floor_gated = wp.int32(0)
            if h_mo[o] == 1:
                gated = 1
            elif h_lt[o] + wp.int64(1) > tick:
                gated = 1
                gated_b = 1
            else:
                # the support floor: the other three legs >= 2 live pads
                livec = wp.int32(0)
                for l2 in range(2):
                    mn = F(1e300)
                    for pt in range(2):
                        g = gap_of_k(ptp, mdl.pt_radius, 4 + l2 * 2 + pt, cst.plane_y)
                        if g < mn:
                            mn = g
                    if mn <= cst.k_touch:
                        livec = livec + 1
                mn = F(1e300)
                for pt in range(2):
                    g = gap_of_k(ptp, mdl.pt_radius, o * 2 + pt, cst.plane_y)
                    if g < mn:
                        mn = g
                if mn <= cst.k_touch:
                    livec = livec + 1
                if livec < 2:
                    floor_gated = 1
                # the kick-stand promise (wave 29 clause d, alt fires only;
                # DEFERRED-W24 held-glide term treated false)
                if alt_fire != 0 and gated == 0 and floor_gated == 0:
                    promised = wp.int32(0)
                    if tch[o] != 0:
                        for l2 in range(2):
                            mn2 = F(1e300)
                            for pt in range(2):
                                g = gap_of_k(ptp, mdl.pt_radius, 4 + l2 * 2 + pt, cst.plane_y)
                                if g < mn2:
                                    mn2 = g
                            if mn2 > cst.k_touch:
                                continue
                            if f_mo[l2] == 0 and f_st[l2] - f_t[l2] >= tair:
                                promised = 1
                                break
                    if promised == 0:
                        floor_gated = 1
            deadline_fire = wp.int32(0)
            if alt_due != 0 and dl > wp.int64(0) and F(tick) >= F(dl):
                deadline_fire = 1
            if floor_gated != 0 and deadline_fire != 0:
                floor_gated = 0
            # DEFERRED-W36: the waive-era hand-off preservation requires the
            # per-leg waive census (waive_last); ported as a local census:
            # this port tracks waive_last in h_xo reuse? No -- DEFERRED-W36
            # documented in the manifest: gated_b yields unconditionally.
            if gated_b != 0 and deadline_fire != 0:
                gated = 0
                gated_b = 0
            # the wave-35 (a)-waive with the wave-38 stall-era scope guard
            stall_era_link = wp.int32(0)
            if h_lt[hl] != wp.int64(0) and h_lt[hl] - h_lf[hl] == wp.int64(cst.tair):
                stall_era_link = 1
            if gated != 0 and gated_b == 0 and floor_gated == 0 and alt_fire != 0 and is_unload != 0 and deadline_fire != 0 and h_held[o] == 0:
                if stall_era_link != 0:
                    pass  # the guard blocks the waive (census DEFERRED)
                else:
                    gated = 0
            if gated != 0 or floor_gated != 0:
                continue
            # FIRE: the wave-20 glide, hind side
            h_mo[hl] = 1
            h_t[hl] = F(0.0)
            h_held[hl] = 1
            h_fi[hl] = h_fi[hl] + 1
            h_lf[hl] = tick
            hpt = mdl.hind_heel_pt[hl]
            p1 = wp.zeros(shape=3, dtype=wp.float64)
            p2 = wp.zeros(shape=3, dtype=wp.float64)
            for c in range(3):
                p1[c] = mdl.pt_local[hpt * 3 + c]
                p2[c] = mdl.pt_local[(hpt + 1) * 3 + c]
            T16 = wp.zeros(shape=16, dtype=wp.float64)
            fb = mdl.pt_body[hpt]
            for i in range(16):
                T16[i] = fr[fb * 16 + i]
            w1p = wp.zeros(shape=3, dtype=wp.float64)
            apply_point(T16, p1, w1p)
            w2p = wp.zeros(shape=3, dtype=wp.float64)
            apply_point(T16, p2, w2p)
            fx = (w1p[0] + w2p[0]) * F(0.5)
            fy = (w1p[1] + w2p[1]) * F(0.5)
            fz = (w1p[2] + w2p[2]) * F(0.5)
            h_from[hl * 3] = fx
            h_from[hl * 3 + 1] = fy
            h_from[hl * 3 + 2] = fz
            h_to[hl * 3 + 2] = fz
            h_py[hl] = fy
            c0 = mdl.hind_coord[hl * 4 + 0]
            c1h = mdl.hind_coord[hl * 4 + 1]
            c2h = mdl.hind_coord[hl * 4 + 2]
            h_ap[hl] = q[c0] + q[c1h] + q[c2h]
            h_mp[hl] = q[mdl.hind_coord[hl * 4 + 3]]
            h_br[hl] = 1
            if q[c1h] < F(0.0):
                h_br[hl] = -1
            xoff = v_eff * (cst.duty * cst.t_cycle) * F(0.5)
            m16 = wp.zeros(shape=16, dtype=wp.float64)
            for i in range(16):
                m16[i] = fr[cst.pelvis_row * 16 + i]
            hipw = wp.zeros(shape=3, dtype=wp.float64)
            mlh = wp.zeros(shape=3, dtype=wp.float64)
            mlh[0] = mdl.hind_mount[hl * 3]
            mlh[1] = mdl.hind_mount[hl * 3 + 1]
            mlh[2] = mdl.hind_mount[hl * 3 + 2]
            apply_point(m16, mlh, hipw)
            hgt = wp.max(F(0.0), hipw[1] - h_py[hl])
            a2m = cst.hind_L1 + cst.hind_L2
            dxs = cst.hind_xm * wp.cos(h_ap[hl])
            dys = hgt + cst.hind_xm * wp.sin(h_ap[hl])
            under = a2m * a2m - dys * dys
            xmax = dxs
            if under > F(0.0):
                xmax = dxs + wp.sqrt(under)
            if xoff > xmax:
                xoff = xmax
            h_xo[hl] = xoff
            h_to[hl * 3] = hipw[0] + xoff
            h_to[hl * 3 + 1] = h_py[hl]

    # ── the capture-step reflex (wave 21 arming law) ──
    if walking != 0 and cst.capture_enabled != 0:
        hx = wp.zeros(shape=8, dtype=wp.float64)
        hz = wp.zeros(shape=8, dtype=wp.float64)
        hn = wp.int32(0)
        for k in range(8):
            g = gap_of_k(ptp, mdl.pt_radius, k, cst.plane_y)
            if cst.contact != 0 and g <= cst.k_touch:
                hx[hn] = ptp[k * 3]
                hz[hn] = ptp[k * 3 + 2]
                hn = hn + 1
        # the CoM projection (support_state's body sum)
        mtot = F(0.0)
        comx = F(0.0)
        comy = F(0.0)
        comz = F(0.0)
        cw = wp.zeros(shape=3, dtype=wp.float64)
        cb = wp.zeros(shape=3, dtype=wp.float64)
        T16b = wp.zeros(shape=16, dtype=wp.float64)
        for b in range(1, cst.nbod):
            mb = mdl.body_mass[b]
            if mb == F(0.0):
                continue
            cb[0] = mdl.body_com[b * 3]
            cb[1] = mdl.body_com[b * 3 + 1]
            cb[2] = mdl.body_com[b * 3 + 2]
            for i in range(16):
                T16b[i] = fr[b * 16 + i]
            apply_point(T16b, cb, cw)
            comx = comx + mb * cw[0]
            comy = comy + mb * cw[1]
            comz = comz + mb * cw[2]
            mtot = mtot + mb
        comx = comx / mtot
        comz = comz / mtot
        if hn >= 3:
            # lexicographic sort + unique
            for i in range(hn):
                for j in range(i + 1, hn):
                    if hx[j] < hx[i] or (hx[j] == hx[i] and hz[j] < hz[i]):
                        tx = hx[i]; hx[i] = hx[j]; hx[j] = tx
                        tz = hz[i]; hz[i] = hz[j]; hz[j] = tz
            ux = wp.zeros(shape=8, dtype=wp.float64)
            uz = wp.zeros(shape=8, dtype=wp.float64)
            un = wp.int32(0)
            for i in range(hn):
                if un == 0 or hx[i] != ux[un - 1] or hz[i] != uz[un - 1]:
                    ux[un] = hx[i]
                    uz[un] = hz[i]
                    un = un + 1
            if un >= 3:
                # Andrew monotone chain
                chx = wp.zeros(shape=16, dtype=wp.float64)
                chz = wp.zeros(shape=16, dtype=wp.float64)
                kk = wp.int32(0)
                for i in range(un):
                    while kk >= 2:
                        cr = (chx[kk - 1] - chx[kk - 2]) * (uz[i] - chz[kk - 2]) - (chz[kk - 1] - chz[kk - 2]) * (ux[i] - chx[kk - 2])
                        if cr <= F(0.0):
                            kk = kk - 1
                        else:
                            break
                    chx[kk] = ux[i]
                    chz[kk] = uz[i]
                    kk = kk + 1
                t2 = kk + 1
                for i in range(un - 1, -1, -1):
                    while kk >= t2:
                        cr = (chx[kk - 1] - chx[kk - 2]) * (uz[i] - chz[kk - 2]) - (chz[kk - 1] - chz[kk - 2]) * (ux[i] - chx[kk - 2])
                        if cr <= F(0.0):
                            kk = kk - 1
                        else:
                            break
                    chx[kk] = ux[i]
                    chz[kk] = uz[i]
                    kk = kk + 1
                cn = kk - 1
                if cn >= 3:
                    # the slip-cone clause
                    v_bound = cst.mu * cst.gy * (F(1.0) - cst.capture_phi) * cst.t_cycle
                    slip_mx = F(0.0)
                    for r in range(4):
                        g = gap_of_k(ptp, mdl.pt_radius, r * 2, cst.plane_y)
                        if not (cst.contact != 0 and g <= cst.k_touch):
                            continue
                        svx = F(0.0)
                        svz = F(0.0)
                        for i in range(18):
                            svx = svx + ptJ[(r * 3 + 0) * 18 + i] * v[i]
                            svz = svz + ptJ[(r * 3 + 2) * 18 + i] * v[i]
                        sl = wp.sqrt(svx * svx + svz * svz)
                        if sl > slip_mx:
                            slip_mx = sl
                    if slip_mx <= v_bound:
                        # the true-hull containment; the first violated edge
                        # supplies the outward probe
                        side = wp.int32(0)
                        viol = wp.int32(-1)
                        for i in range(cn):
                            j = (i + 1) % cn
                            cr = (chx[j] - chx[i]) * (comz - chz[i]) - (chz[j] - chz[i]) * (comx - chx[i])
                            if wp.abs(cr) < F(1e-15):
                                continue
                            s = wp.int32(1) if cr > F(0.0) else wp.int32(-1)
                            if side == 0:
                                side = s
                            elif s != side:
                                viol = i
                                break
                        if viol >= 0:
                            i = viol
                            j = (viol + 1) % cn
                            ex = chx[j] - chx[i]
                            ez = chz[j] - chz[i]
                            nl = wp.sqrt(ex * ex + ez * ez)
                            if nl >= F(1e-12):
                                nx = ez / nl
                                nz = -ex / nl
                                cx = F(0.0)
                                cz = F(0.0)
                                for i2 in range(cn):
                                    cx = cx + chx[i2]
                                    cz = cz + chz[i2]
                                cx = cx / F(cn)
                                cz = cz / F(cn)
                                if (cx - chx[i]) * nx + (cz - chz[i]) * nz < F(0.0):
                                    nx = -nx
                                    nz = -nz
                                if v[3] * nx + v[5] * nz > F(0.0):
                                    # (ii) the swing-clock clause: non-touching AND in swing
                                    for leg in range(2):
                                        touching_leg = wp.int32(0)
                                        g0 = gap_of_k(ptp, mdl.pt_radius, leg * 2, cst.plane_y)
                                        g1 = gap_of_k(ptp, mdl.pt_radius, leg * 2 + 1, cst.plane_y)
                                        if cst.contact != 0 and wp.min(g0, g1) <= cst.k_touch:
                                            touching_leg = 1
                                        if touching_leg == 0 and phi[leg] >= cst.toe_off:
                                            phi[leg] = cst.capture_phi
                                            break

    # ── integrate 4 substeps: servo + store bisection + advance ──
    # (dynamic loop: the unrolled body is too large to JIT)
    sub = wp.int32(0)
    while sub < 4:
        sub = sub + 1
        for i in range(18):
            tau[i] = F(0.0)
            eff[i] = F(0.0)
        # the servo: capped mass-normalized PD (targets per the current state)
        pot = fk_eval(q, v, mdl.ax_rot, mdl.ax_axis, mdl.ax_slot, mdl.ax_slope, mdl.ax_const,
                      mdl.body_axoff, mdl.body_parent, mdl.body_mass, mdl.body_com, mdl.body_inertia,
                      mdl.body_fp, mdl.body_fc, mdl.chain_off, mdl.chain_ax, mdl.pt_body, mdl.pt_local,
                      mdl.pt_radius, cst.nbod, cst.naxes, cst.plane_y, cst.gy,
                      M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias)
        d = wp.int32(0)
        while d < 12:
            d = d + 1
            c = mdl.drive_coord[d - 1]
            if cst.power == 0 or ((cst.drive_en >> (d - 1)) & 1) == 0 or bat[d - 1] <= F(1e-12):
                continue
            target = F(0.0)
            if cst.gait_enabled != 0:
                if (d - 1) < 8:
                    hl = (d - 1) // 4
                    ji = (d - 1) % 4
                    if h_mo[hl] == 1:
                        sg = h_t[hl] / tair
                        if sg < F(0.0):
                            sg = F(0.0)
                        if sg > F(1.0):
                            sg = F(1.0)
                        carch = F(2.0) * mdl.pt_radius[mdl.hind_heel_pt[hl]]
                        tgt = wp.zeros(shape=3, dtype=wp.float64)
                        if h_held[hl] != 0:
                            for cc2 in range(3):
                                tgt[cc2] = h_from[hl * 3 + cc2]
                            tgt[1] = tgt[1] + carch
                        else:
                            for cc2 in range(3):
                                tgt[cc2] = h_from[hl * 3 + cc2] + (h_to[hl * 3 + cc2] - h_from[hl * 3 + cc2]) * sg
                            tgt[1] = tgt[1] + carch * wp.sin(PI * sg)
                        qh_h, qk_h, qa_h = hind_ik_at(mdl, cst, fr, tgt, h_ap[hl], h_br[hl])
                        if ji == 0:
                            target = qh_h
                        elif ji == 1:
                            target = qk_h
                        elif ji == 2:
                            target = qa_h
                        else:
                            target = h_mp[hl]
                    else:
                        qstar = tables_at(mdl, phi[hl])
                        target = qstar[ji]
                        if h_latched != 0 and tch[hl] != 0:
                            target = target + ltau[c] / mdl.kp[d]
                else:
                    fl = (d - 9) // 2
                    ji = (d - 9) % 2
                    if capt != 0:
                        plt = paw_leg(paw_t, fl)
                        q1f, q2f, q1rx, q2rx, satf = fore_ik_at(mdl, cst, fr, fl, plt, ikb[fl])
                        if ji == 0:
                            target = q1f
                        else:
                            target = q2f
                    else:
                        if ji == 0:
                            target = cst.fore_pose_sh
                        else:
                            target = cst.fore_pose_el
            tq = mdl.kp[d - 1] * (target - q[c]) - mdl.kd[d - 1] * v[c]
            cap = mdl.drive_cap[d - 1]
            tq = wp.min(cap, wp.max(-cap, tq))
            tau[c] = tq
        if cst.power != 0 and cst.posture_drive != 0 and bat_post > F(1e-12):
            amp = F(0.0)
            if cst.gait_enabled != 0:
                if cst.settle_total > 0:
                    amp = F(1.0) - F(settle_n) / F(cst.settle_total)
                else:
                    amp = F(1.0)
            tpost = amp * vault_at(mdl, phi[0])
            tq = cst.kp_post * (tpost - q[2]) - cst.kd_post * v[2]
            cap = mdl.drive_cap[0]
            tq = wp.min(cap, wp.max(-cap, tq))
            tau[2] = tq
        # the store-bisection loop (the per-drive depletive stores)
        for d in range(13):
            scales[d] = F(1.0)
        adv[0] = 0
        for i in range(18):
            cur_w[i] = w[i]
        rca = wp.zeros(shape=1, dtype=wp.int32)
        rcs = wp.int32(0)
        # NOTE: advance resets adv per tick in the C++ (adv_calls_=0 before the
        # substep loop); the budget is per tick over all 4 substeps, so adv
        # accumulates across substeps -- do NOT reset per substep.
        if sub == 0:
            adv[0] = 0
        for i in range(18):
            eff[i] = tau[i]
        for d in range(12):
            eff[mdl.drive_coord[d]] = tau[mdl.drive_coord[d]] * scales[d]
        eff[2] = tau[2] * scales[12]
        advance(q, v, w, eff, cst.dt * F(0.25), mdl, cst, M, gv, bv, fr, frd, frdd,
                axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, srq, srv,
                qa, va, qb, vb, qc, vc, qd, vd, qe, ve, we, sq, sh16, sdep, scl,
                adv, rca, o_q, o_v, o_w)
        for i in range(18):
            trial_q[i] = o_q[i]
            trial_v[i] = o_v[i]
            trial_w[i] = o_w[i]
        if rca[0] != 0:
            rc = rca[0]
        if rc == 0:
            round_n = wp.int32(0)
            dsf[0] = 0
            while round_n < 8:
                dsf[0] = 0
                d = wp.int32(0)
                while d < 13:
                    d = d + 1
                    c = 2 if (d - 1) == 12 else mdl.drive_coord[d - 1]
                    enabled = wp.int32(1)
                    if cst.power == 0:
                        enabled = 0
                    elif (d - 1) < 12 and ((cst.drive_en >> (d - 1)) & 1) == 0:
                        enabled = 0
                    elif (d - 1) == 12 and cst.posture_drive == 0:
                        enabled = 0
                    if enabled == 0:
                        continue
                    store = bat[d - 1] if (d - 1) < 12 else bat_post
                    wd = trial_w[c] - cur_w[c]
                    if wd < F(0.0):
                        wd = F(0.0)
                    if wd > store:
                        lo = F(0.0)
                        hi = F(1.0)
                        j = wp.int32(0)
                        while j < 40:
                            j = j + 1
                            mid = (lo + hi) * F(0.5)
                            scales[d] = mid
                            for i in range(18):
                                eff[i] = tau[i]
                            for dsc in range(12):
                                eff[mdl.drive_coord[dsc]] = tau[mdl.drive_coord[dsc]] * scales[dsc]
                            eff[2] = tau[2] * scales[12]
                            advance(q, v, w, eff, cst.dt * F(0.25), mdl, cst, M, gv, bv, fr, frd, frdd,
                                    axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, srq, srv,
                                    qa, va, qb, vb, qc, vc, qd, vd, qe, ve, we, sq, sh16, sdep, scl,
                                    adv, rca, o_q, o_v, o_w)
                            if rca[0] != 0:
                                rc = rca[0]
                            wdc = o_w[c] - cur_w[c]
                            if wdc < F(0.0):
                                wdc = F(0.0)
                            if wdc <= store:
                                lo = mid
                                for i in range(18):
                                    trial_q[i] = o_q[i]
                                    trial_v[i] = o_v[i]
                                    trial_w[i] = o_w[i]
                            else:
                                hi = mid
                        scales[d - 1] = lo
                        dsf[0] = 1
                if dsf[0] == 0:
                    break
                for i in range(18):
                    eff[i] = tau[i]
                for dsc in range(12):
                    eff[mdl.drive_coord[dsc]] = tau[mdl.drive_coord[dsc]] * scales[dsc]
                eff[2] = tau[2] * scales[12]
                advance(q, v, w, eff, cst.dt * F(0.25), mdl, cst, M, gv, bv, fr, frd, frdd,
                        axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, srq, srv,
                        qa, va, qb, vb, qc, vc, qd, vd, qe, ve, we, sq, sh16, sdep, scl,
                        adv, rca, o_q, o_v, o_w)
                for i in range(18):
                    trial_q[i] = o_q[i]
                    trial_v[i] = o_v[i]
                    trial_w[i] = o_w[i]
                if rca[0] != 0:
                    rc = rca[0]
                if rc != 0:
                    break
                # the final-round unresolved check
                if round_n == 7:
                    for d in range(13):
                        c = 2 if d == 12 else mdl.drive_coord[d]
                        enabled = wp.int32(1)
                        if cst.power == 0:
                            enabled = 0
                        elif d < 12 and ((cst.drive_en >> d) & 1) == 0:
                            enabled = 0
                        elif d == 12 and cst.posture_drive == 0:
                            enabled = 0
                        if enabled == 0:
                            continue
                        store = bat[d] if d < 12 else bat_post
                        wdc = trial_w[c] - cur_w[c]
                        if wdc < F(0.0):
                            wdc = F(0.0)
                        if wdc > store:
                            rc = 4
                round_n = round_n + 1
        if rc != 0:
            break
        # the store spend + the substep commit
        for d in range(13):
            c = 2 if d == 12 else mdl.drive_coord[d]
            store = bat[d] if d < 12 else bat_post
            spent = trial_w[c] - cur_w[c]
            if spent < F(0.0):
                spent = F(0.0)
            if d < 12:
                bat[d] = store - spent
            else:
                bat_post = store - spent
        for i in range(18):
            q[i] = trial_q[i]
            v[i] = trial_v[i]
            w[i] = trial_w[i]
        for d in range(12):
            lta[mdl.drive_coord[d]] = lta[mdl.drive_coord[d]] + tau[mdl.drive_coord[d]] * F(0.25)
        lta[2] = lta[2] + tau[2] * F(0.25)

    # ── the tick bookkeeping ──
    if rc == 0:
        for i in range(18):
            if wp.isnan(q[i]) or wp.isnan(v[i]) or wp.isinf(q[i]) or wp.isinf(v[i]):
                rc = 1
    collapsed = wp.int32(0)
    if rc == 0 and q[4] < F(0.20):
        collapsed = 1
    if rc != 0:
        a_refused[e] = 1
        a_refused_class[e] = rc
    if collapsed != 0:
        a_collapsed[e] = 1
    for i in range(18):
        a_q[e * 18 + i] = q[i]
        a_v[e * 18 + i] = v[i]
        a_work[e * 18 + i] = w[i]
        a_last_torque[e * 18 + i] = lta[i]
    for d in range(12):
        a_battery[e * 12 + d] = bat[d]
    a_battery_post[e] = bat_post
    a_phi[e * 2] = phi[0]
    a_phi[e * 2 + 1] = phi[1]
    a_touching[e * 2] = tch[0]
    a_touching[e * 2 + 1] = tch[1]
    a_captured[e] = capt
    a_settle[e] = settle_n
    a_ik_branch[e * 2] = ikb[0]
    a_ik_branch[e * 2 + 1] = ikb[1]
    for l in range(2):
        for c in range(3):
            a_paw_target[e * 6 + l * 3 + c] = paw_t[l * 3 + c]
            a_swing_from[e * 6 + l * 3 + c] = swf[l * 3 + c]
            a_swing_to[e * 6 + l * 3 + c] = swt[l * 3 + c]
            a_hind_from[e * 6 + l * 3 + c] = h_from[l * 3 + c]
            a_hind_to[e * 6 + l * 3 + c] = h_to[l * 3 + c]
        a_paw_plant_y[e * 2 + l] = paw_y[l]
        a_fore_t[e * 2 + l] = f_t[l]
        a_fore_stance[e * 2 + l] = f_st[l]
        a_fore_cycle[e * 2 + l] = f_cy[l]
        a_fore_mode[e * 2 + l] = f_mo[l]
        a_fore_entry[e * 2 + l] = f_en[l]
        a_fore_conv[e * 2 + l] = f_cv[l]
        a_fore_td_plant[e * 2 + l] = f_dp[l]
        a_fore_clamped[e * 2 + l] = f_cl[l]
        a_fore_replants[e * 2 + l] = f_rp[l]
        a_fore_td_count[e * 2 + l] = f_td[l]
        a_hind_mode[e * 2 + l] = h_mo[l]
        a_hind_t[e * 2 + l] = h_t[l]
        a_hind_plant_y[e * 2 + l] = h_py[l]
        a_hind_ap[e * 2 + l] = h_ap[l]
        a_hind_mp[e * 2 + l] = h_mp[l]
        a_hind_branch[e * 2 + l] = h_br[l]
        a_hind_held[e * 2 + l] = h_held[l]
        a_hind_last_fire[e * 2 + l] = h_lf[l]
        a_hind_last_td[e * 2 + l] = h_lt[l]
        a_hind_fires[e * 2 + l] = h_fi[l]
        a_hind_tds[e * 2 + l] = h_tds[l]
        a_hind_xoff[e * 2 + l] = h_xo[l]
    a_height_latched[e] = h_latched
    a_cmd_vx[e] = cmd_v
    a_cmd_live[e] = cmd_on
    a_cmd_first_tick[e] = cmd_first
    a_cmd_fires[e] = cmd_fires
    a_adv_calls[e] = adv[0]
    if rc == 0 and collapsed == 0:
        a_ticks[e] = tick + wp.int64(1)
    bat_sum = F(0.0)
    for d in range(12):
        bat_sum = bat_sum + bat[d]
    rb[e * 6 + 0] = q[3]
    rb[e * 6 + 1] = q[4]
    rb[e * 6 + 2] = v[3]
    rb[e * 6 + 3] = phi[0]
    rb[e * 6 + 4] = phi[1]
    rb[e * 6 + 5] = bat_sum
    rbi[e * 6 + 0] = h_fi[0]
    rbi[e * 6 + 1] = h_fi[1]
    rbi[e * 6 + 2] = f_mo[0]
    rbi[e * 6 + 3] = f_mo[1]
    rbi[e * 6 + 4] = tch[0]
    rbi[e * 6 + 5] = tch[1]


# ───────────────────────── the batched environment ─────────────────────────


# ───────────────────────── the batched environment ─────────────────────────
class GaitWalkEnv:
    """The batched training environment: N independent walker worlds on one
    GPU. reset() installs per-env reset states; step(n) advances n ticks;
    set_command(v) feeds the adapter's channel (zero-order hold at the tick
    boundary, value-only)."""

    def __init__(self, spec: WalkerSpec, n_envs: int, device='cuda:0',
                 reflex_level: int = 1, collapse_y: float = 0.20):
        self.spec = spec
        self.E = int(n_envs)
        self.device = device
        E = self.E
        f64 = wp.float64
        self.a_q = wp.zeros(E * 18, dtype=f64, device=device)
        self.a_v = wp.zeros(E * 18, dtype=f64, device=device)
        self.a_work = wp.zeros(E * 18, dtype=f64, device=device)
        self.a_last_torque = wp.zeros(E * 18, dtype=f64, device=device)
        self.a_battery = wp.zeros(E * 12, dtype=f64, device=device)
        self.a_battery_post = wp.zeros(E, dtype=f64, device=device)
        self.a_phi = wp.zeros(E * 2, dtype=f64, device=device)
        self.a_touching = wp.zeros(E * 2, dtype=wp.int32, device=device)
        self.a_captured = wp.zeros(E, dtype=wp.int32, device=device)
        self.a_settle = wp.zeros(E, dtype=wp.int32, device=device)
        self.a_ik_branch = wp.zeros(E * 2, dtype=wp.int32, device=device)
        self.a_paw_target = wp.zeros(E * 6, dtype=f64, device=device)
        self.a_paw_plant_y = wp.zeros(E * 2, dtype=f64, device=device)
        self.a_swing_from = wp.zeros(E * 6, dtype=f64, device=device)
        self.a_swing_to = wp.zeros(E * 6, dtype=f64, device=device)
        self.a_fore_t = wp.zeros(E * 2, dtype=f64, device=device)
        self.a_fore_stance = wp.zeros(E * 2, dtype=f64, device=device)
        self.a_fore_cycle = wp.zeros(E * 2, dtype=f64, device=device)
        self.a_fore_mode = wp.zeros(E * 2, dtype=wp.int32, device=device)
        self.a_fore_entry = wp.zeros(E * 2, dtype=wp.int32, device=device)
        self.a_fore_conv = wp.zeros(E * 2, dtype=wp.int32, device=device)
        self.a_fore_td_plant = wp.zeros(E * 2, dtype=wp.int32, device=device)
        self.a_fore_clamped = wp.zeros(E * 2, dtype=wp.int32, device=device)
        self.a_fore_replants = wp.zeros(E * 2, dtype=wp.int32, device=device)
        self.a_fore_td_count = wp.zeros(E * 2, dtype=wp.int32, device=device)
        self.a_hind_mode = wp.zeros(E * 2, dtype=wp.int32, device=device)
        self.a_hind_t = wp.zeros(E * 2, dtype=f64, device=device)
        self.a_hind_from = wp.zeros(E * 6, dtype=f64, device=device)
        self.a_hind_to = wp.zeros(E * 6, dtype=f64, device=device)
        self.a_hind_plant_y = wp.zeros(E * 2, dtype=f64, device=device)
        self.a_hind_ap = wp.zeros(E * 2, dtype=f64, device=device)
        self.a_hind_mp = wp.zeros(E * 2, dtype=f64, device=device)
        self.a_hind_branch = wp.zeros(E * 2, dtype=wp.int32, device=device)
        self.a_hind_held = wp.zeros(E * 2, dtype=wp.int32, device=device)
        self.a_hind_last_fire = wp.zeros(E * 2, dtype=wp.int64, device=device)
        self.a_hind_last_td = wp.zeros(E * 2, dtype=wp.int64, device=device)
        self.a_hind_fires = wp.zeros(E * 2, dtype=wp.int32, device=device)
        self.a_hind_tds = wp.zeros(E * 2, dtype=wp.int32, device=device)
        self.a_hind_xoff = wp.zeros(E * 2, dtype=f64, device=device)
        self.a_height_latched = wp.zeros(E, dtype=wp.int32, device=device)
        self.a_cmd_vx = wp.zeros(E, dtype=f64, device=device)
        self.a_cmd_live = wp.zeros(E, dtype=wp.int32, device=device)
        self.a_cmd_first_tick = wp.zeros(E, dtype=wp.int64, device=device)
        self.a_cmd_fires = wp.zeros(E, dtype=wp.int32, device=device)
        self.a_ticks = wp.zeros(E, dtype=wp.int64, device=device)
        self.a_adv_calls = wp.zeros(E, dtype=wp.int32, device=device)
        self.a_refused = wp.zeros(E, dtype=wp.int32, device=device)
        self.a_refused_class = wp.zeros(E, dtype=wp.int32, device=device)
        self.a_collapsed = wp.zeros(E, dtype=wp.int32, device=device)
        self.rb = wp.zeros(E * 6, dtype=f64, device=device)
        self.rbi = wp.zeros(E * 6, dtype=wp.int32, device=device)

        axrot = np.array([a["rot"] for a in spec.axes], dtype=np.int32)
        axaxis = np.concatenate([a["axis"] for a in spec.axes]).astype(np.float64)
        axslot = np.array([a["slot"] for a in spec.axes], dtype=np.int32)
        axslope = np.array([a["slope"] for a in spec.axes], dtype=np.float64)
        axconst = np.array([a["const"] for a in spec.axes], dtype=np.float64)
        chain_ax_list, chain_off = [], [0]
        for b in range(spec.nbod):
            chain_ax_list += spec.body_slots[b]
            chain_off.append(len(chain_ax_list))
        mi = ModelIn()
        mi.ax_rot = wp.array(axrot, dtype=wp.int32, device=device)
        mi.ax_axis = wp.array(axaxis, dtype=f64, device=device)
        mi.ax_slot = wp.array(axslot, dtype=wp.int32, device=device)
        mi.ax_slope = wp.array(axslope, dtype=f64, device=device)
        mi.ax_const = wp.array(axconst, dtype=f64, device=device)
        mi.body_axoff = wp.array(spec.body_axoff, dtype=wp.int32, device=device)
        mi.body_parent = wp.array(spec.body_parent, dtype=wp.int32, device=device)
        mi.body_mass = wp.array(spec.body_mass, dtype=f64, device=device)
        mi.body_com = wp.array(spec.body_com.reshape(-1), dtype=f64, device=device)
        mi.body_inertia = wp.array(spec.body_inertia.reshape(-1), dtype=f64, device=device)
        mi.body_fp = wp.array(spec.body_fp.reshape(-1), dtype=f64, device=device)
        mi.body_fc = wp.array(spec.body_fc.reshape(-1), dtype=f64, device=device)
        mi.chain_off = wp.array(np.array(chain_off, np.int32), dtype=wp.int32, device=device)
        mi.chain_ax = wp.array(np.array(chain_ax_list, np.int32), dtype=wp.int32, device=device)
        mi.pt_body = wp.array(spec.pt_body, dtype=wp.int32, device=device)
        mi.pt_local = wp.array(spec.pt_local.reshape(-1), dtype=f64, device=device)
        mi.pt_radius = wp.array(spec.pt_radius, dtype=f64, device=device)
        mi.lower = wp.array(spec.lower, dtype=f64, device=device)
        mi.upper = wp.array(spec.upper, dtype=f64, device=device)
        mi.drive_coord = wp.array(spec.drive_coord, dtype=wp.int32, device=device)
        mi.drive_cap = wp.array(spec.drive_cap, dtype=f64, device=device)
        mi.drive_damping = wp.array(spec.drive_damping, dtype=f64, device=device)
        mi.kp = wp.array(spec.kp, dtype=f64, device=device)
        mi.kd = wp.array(spec.kd, dtype=f64, device=device)
        mi.tab_hip = wp.array(spec.tab_hip, dtype=f64, device=device)
        mi.tab_knee = wp.array(spec.tab_knee, dtype=f64, device=device)
        mi.tab_ankle = wp.array(spec.tab_ankle, dtype=f64, device=device)
        mi.tab_mp = wp.array(spec.tab_mp, dtype=f64, device=device)
        mi.zeros4 = wp.array(spec.zeros, dtype=f64, device=device)
        mi.vault = wp.array(spec.trunk_vault, dtype=f64, device=device)
        mi.fore_coord = wp.array(np.array(spec.fore_coord, np.int32).reshape(-1), dtype=wp.int32, device=device)
        mi.hind_coord = wp.array(np.array(spec.hind_coord, np.int32).reshape(-1), dtype=wp.int32, device=device)
        mi.hind_drive = wp.array(np.array(spec.hind_drive_idx, np.int32).reshape(-1), dtype=wp.int32, device=device)
        mi.fore_drive = wp.array(np.array(spec.fore_drive_idx, np.int32).reshape(-1), dtype=wp.int32, device=device)
        mi.fore_heel_pt = wp.array(np.array(spec.fore_heel_pt, np.int32), dtype=wp.int32, device=device)
        mi.hind_heel_pt = wp.array(np.array(spec.hind_heel_pt, np.int32), dtype=wp.int32, device=device)
        mi.fore_mount_local = wp.array(np.concatenate([spec.fore_mount_local['fore_left'], spec.fore_mount_local['fore_right']]), dtype=wp.float64, device=device)
        mi.hind_mount = wp.array(np.concatenate([spec.hind_mount['left'], spec.hind_mount['right']]), dtype=wp.float64, device=device)
        self.mdl = mi

        mc = ModelConst()
        mc.nbod = wp.int32(spec.nbod)
        mc.naxes = wp.int32(spec.naxes)
        mc.plane_y = wp.float64(spec.plane_model_y)
        mc.gy = wp.float64(9.80665)
        mc.dt = wp.float64(spec.dt)
        mc.mu = wp.float64(spec.mu)
        mc.k_touch = wp.float64(K_TOUCH)
        mc.k_slip = wp.float64(K_SLIP)
        mc.k_release = wp.float64(K_RELEASE_BAND)
        mc.t_cycle = wp.float64(T_CYCLE)
        mc.duty = wp.float64(DUTY_SAMPLED)
        mc.toe_off = wp.float64(TOE_OFF)
        mc.fs_hz = wp.float64(FS_HZ)
        mc.zeta = wp.float64(ZETA)
        mc.capture_phi = wp.float64(CAPTURE_PHI)
        mc.settle_total = wp.int32(spec.settle_total)
        mc.contact = wp.int32(1 if spec.contact_enabled else 0)
        mc.power = wp.int32(1)
        mc.gait_enabled = wp.int32(1)
        mc.capture_enabled = wp.int32(1)
        mc.posture_drive = wp.int32(1)
        mc.drive_en = wp.int32(sum(1 << d for d in range(12) if spec.drive_enabled[d]))
        mc.reflex_level = wp.int32(reflex_level)
        mc.kp_post = wp.float64(spec.kp_post)
        mc.kd_post = wp.float64(spec.kd_post)
        mc.store_post = wp.float64(spec.store_post)
        mc.height_crit = wp.float64(spec.height_crit)
        mc.height_floor = wp.float64(spec.height_floor)
        mc.fore_L1 = wp.float64(spec.fore_L1)
        mc.fore_rho = wp.float64(spec.fore_rho)
        mc.fore_beta = wp.float64(spec.fore_beta)
        mc.hind_L1 = wp.float64(spec.hind_L1)
        mc.hind_L2 = wp.float64(spec.hind_L2)
        mc.hind_xm = wp.float64(spec.hind_xm)
        mc.fore_pose_sh = wp.float64(spec.fore_pose_sh)
        mc.fore_pose_el = wp.float64(spec.fore_pose_el)
        mc.fold_budget = wp.int32(FOLD_BUDGET_TICKS)
        mc.unload_ticks = wp.int32(UNLOAD_TICKS)
        mc.tair = wp.int32(int(np.ceil((T_CYCLE - DUTY_SAMPLED) / spec.dt)))
        mc.pelvis_row = wp.int32(spec.pelvis_row)
        mc.upperarm_body = wp.int32(spec.upperarm_body[0])
        mc.forearm_body = wp.int32(spec.forearm_body[0])
        self.cst = mc
        self.collapse_y = float(collapse_y)

    def reset(self, q0=None, v0=None, touching0=None, contact=True):
        spec = self.spec
        if q0 is None:
            q, v, phi = spec.reset_state()
            q0 = np.tile(q, self.E)
            v0 = np.tile(v, self.E)
        if touching0 is None:
            frames, _, _ = spec._fk(np.asarray(q0)[:18])
            t0 = []
            for leg in range(2):
                gmin = 1e300
                for pt in range(2):
                    k = leg * 2 + pt
                    p = frames[spec.pt_body[k]] @ np.append(spec.pt_local[k], 1.0)
                    gmin = min(gmin, p[1] + spec.pt_radius[k] - spec.plane_model_y)
                t0.append(1 if gmin <= K_TOUCH else 0)
            touching0 = np.tile(np.array(t0, np.int32), self.E)
        self._q0_host = np.asarray(q0, dtype=np.float64).copy()
        self._v0_host = np.asarray(v0, dtype=np.float64).copy()
        qa = wp.array(self._q0_host, dtype=wp.float64, device=self.device)
        va = wp.array(self._v0_host, dtype=wp.float64, device=self.device)
        ta = wp.array(np.asarray(touching0, dtype=np.int32), dtype=wp.int32, device=self.device)
        sf = wp.array(self.spec.drive_store_floor, dtype=wp.float64, device=self.device)
        wp.launch(reset_kernel, dim=self.E,
                  inputs=[qa, va, ta, wp.float64(self.spec.start_phase_left), wp.float64(self.spec.start_phase_right),
                          wp.int32(self.spec.settle_total), sf, wp.float64(self.spec.store_post)],
                  outputs=[self.a_q, self.a_v, self.a_work, self.a_last_torque,
                           self.a_battery, self.a_battery_post, self.a_phi, self.a_touching,
                           self.a_captured, self.a_settle, self.a_ik_branch, self.a_paw_target,
                           self.a_paw_plant_y, self.a_swing_from, self.a_swing_to,
                           self.a_fore_t, self.a_fore_stance, self.a_fore_cycle, self.a_fore_mode,
                           self.a_fore_entry, self.a_fore_conv, self.a_fore_td_plant,
                           self.a_fore_clamped, self.a_fore_replants, self.a_fore_td_count,
                           self.a_hind_mode, self.a_hind_t, self.a_hind_from, self.a_hind_to,
                           self.a_hind_plant_y, self.a_hind_ap, self.a_hind_mp, self.a_hind_branch,
                           self.a_hind_held, self.a_hind_last_fire, self.a_hind_last_td,
                           self.a_hind_fires, self.a_hind_tds, self.a_hind_xoff,
                           self.a_height_latched, self.a_cmd_vx, self.a_cmd_live,
                           self.a_cmd_first_tick, self.a_cmd_fires, self.a_ticks, self.a_adv_calls,
                           self.a_refused, self.a_refused_class, self.a_collapsed])
        self.cst.contact = wp.int32(1 if contact else 0)

    def set_command(self, v, env_mask=None):
        if env_mask is None:
            self.a_cmd_vx.fill(float(v))
            self.a_cmd_live.fill(1)
        else:
            host_v = self.a_cmd_vx.numpy()
            host_l = self.a_cmd_live.numpy()
            for i in np.where(env_mask)[0]:
                host_v[i] = float(v)
                host_l[i] = 1
            self.a_cmd_vx = wp.array(host_v, dtype=wp.float64, device=self.device)
            self.a_cmd_live = wp.array(host_l.astype(np.int32), dtype=wp.int32, device=self.device)

    def step(self, n=1, readback=False):
        for _ in range(n):
            wp.launch(tick_kernel, dim=self.E,
                      inputs=[self.mdl, self.cst, self.a_q, self.a_v, self.a_work,
                              self.a_last_torque, self.a_battery, self.a_battery_post,
                              self.a_phi, self.a_touching, self.a_captured, self.a_settle,
                              self.a_ik_branch, self.a_paw_target, self.a_paw_plant_y,
                              self.a_swing_from, self.a_swing_to, self.a_fore_t,
                              self.a_fore_stance, self.a_fore_cycle, self.a_fore_mode,
                              self.a_fore_entry, self.a_fore_conv, self.a_fore_td_plant,
                              self.a_fore_clamped, self.a_fore_replants, self.a_fore_td_count,
                              self.a_hind_mode, self.a_hind_t, self.a_hind_from, self.a_hind_to,
                              self.a_hind_plant_y, self.a_hind_ap, self.a_hind_mp,
                              self.a_hind_branch, self.a_hind_held, self.a_hind_last_fire,
                              self.a_hind_last_td, self.a_hind_fires, self.a_hind_tds,
                              self.a_hind_xoff, self.a_height_latched, self.a_cmd_vx,
                              self.a_cmd_live, self.a_cmd_first_tick, self.a_cmd_fires,
                              self.a_ticks, self.a_adv_calls, self.a_refused,
                              self.a_refused_class, self.a_collapsed, self.rb, self.rbi],
                      outputs=[])
        if readback:
            wp.synchronize()
            return {'rb': self.rb.numpy().reshape(self.E, 6),
                    'rbi': self.rbi.numpy().reshape(self.E, 6),
                    'refused': self.a_refused.numpy(),
                    'refused_class': self.a_refused_class.numpy(),
                    'collapsed': self.a_collapsed.numpy(),
                    'ticks': self.a_ticks.numpy()}
        return None

    def status(self):
        wp.synchronize()
        return {'rb': self.rb.numpy().reshape(self.E, 6),
                'rbi': self.rbi.numpy().reshape(self.E, 6),
                'refused': self.a_refused.numpy(),
                'refused_class': self.a_refused_class.numpy(),
                'collapsed': self.a_collapsed.numpy(),
                'ticks': self.a_ticks.numpy(),
                'cmd_fires': self.a_cmd_fires.numpy(),
                'cmd_first_tick': self.a_cmd_first_tick.numpy(),
                'hind_tds': self.a_hind_tds.numpy().reshape(self.E, 2),
                'fore_td_count': self.a_fore_td_count.numpy().reshape(self.E, 2)}
