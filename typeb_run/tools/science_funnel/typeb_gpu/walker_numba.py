"""walker_numba.py -- the gait walk's FULL BODY + REFLEX CORE, batched in
Numba CUDA.

This is the same port as walker_gpu.py (the Warp form) re-targeted to Numba
CUDA after the Warp JIT hit its compile wall (see receipt: release and debug
modes both stall >45 min at ~7 GB on this kernel). The equations, budgets,
and the fidelity scope (FIDELITY_MANIFEST.md) are IDENTICAL; only the
toolchain differs. f64 math throughout (the CUDA-side wall was Warp's
compiler, not fp64 coverage).

Model constants are packed into ONE device array (mdl, f64) + one int array
(mdi, int32) with fixed offsets (see MDL/MDI index maps) so the kernel and
device-function signatures stay small. Per-env state lives in device arrays
(the training environment's state layout); the kernel is one thread per env.

Trailer Agent: GLM 5.3.
"""
import math
import numpy as np
from numba import cuda, float64, int32, int64, boolean
from walker_model import (WalkerSpec, T_CYCLE, DUTY_SAMPLED, TOE_OFF, FS_HZ,
                          ZETA, CAPTURE_PHI, K_TOUCH, K_SLIP, K_RELEASE_BAND,
                          NB, NDRIVE, FOLD_BUDGET_TICKS, UNLOAD_TICKS,
                          SINK_RATE_MAX)

# ── mdl (f64 model constants) index map ──
MF = {
    'ax_axis': 0,      # naxes*3
    'ax_slope': None,  # filled at build
}
NBOD = 14
NAXES = 18
CHN = 104         # chain_ax length: MEASURED chain_off[-1]=104 for the compiled
                  # scene (body_slots repeat axes across the 13 moving bodies;
                  # the old "<=60 covers 14 bodies x ~4" guess overflowed and
                  # every later mdi table stomped chain_ax[60:104] — found as an
                  # illegal-memory-access in fk_eval's ax_slot[chain_ax[idx]]
                  # on the nvcc route, 2026-09-22)
PTN = 8
# f64 blocks: [ax_axis 54][ax_slope 18][ax_const 18][body_mass 14][body_com 42]
# [body_inertia 42][body_fp 224][body_fc 224][pt_local 24][pt_radius 8]
# [lower 18][upper 18][drive_cap 12][drive_damping 12][kp 12][kd 12]
# [tabs 84][zeros4 4][vault 21][fore_mount_local 6][hind_mount 6]
OF = {}
_off = 0
for name, size in [('ax_axis', 54), ('ax_slope', 18), ('ax_const', 18),
                   ('body_mass', 14), ('body_com', 42), ('body_inertia', 42),
                   ('body_fp', 224), ('body_fc', 224), ('pt_local', 24),
                   ('pt_radius', 8), ('lower', 18), ('upper', 18),
                   ('drive_cap', 12), ('drive_damping', 12), ('kp', 12),
                   ('kd', 12), ('tab_hip', 21), ('tab_knee', 21),
                   ('tab_ankle', 21), ('tab_mp', 21), ('zeros4', 4),
                   ('vault', 21), ('fore_mount_local', 6), ('hind_mount', 6)]:
    OF[name] = _off
    _off += size
NF64 = _off

# int blocks: [ax_rot 18][ax_slot 18][body_axoff 15][body_parent 14]
# [chain_off 15][chain_ax 104][pt_body 8][drive_coord 12][fore_coord 4]
# [hind_coord 8][hind_drive 8][fore_drive 4][fore_heel_pt 2][hind_heel_pt 2]
OI = {}
_off = 0
for name, size in [('ax_rot', 18), ('ax_slot', 18), ('body_axoff', 15),
                   ('body_parent', 14), ('chain_off', 15), ('chain_ax', CHN),
                   ('pt_body', 8), ('drive_coord', 12), ('fore_coord', 4),
                   ('hind_coord', 8), ('hind_drive', 8), ('fore_drive', 4),
                   ('fore_heel_pt', 2), ('hind_heel_pt', 2)]:
    OI[name] = _off
    _off += size
NI32 = _off

# cst (f64 scalars) index map
CF = {'plane_y': 0, 'gy': 1, 'dt': 2, 'mu': 3, 'k_touch': 4, 'k_slip': 5,
      'k_release': 6, 't_cycle': 7, 'duty': 8, 'toe_off': 9, 'capture_phi': 10,
      'kp_post': 11, 'kd_post': 12, 'store_post': 13, 'height_crit': 14,
      'height_floor': 15, 'fore_L1': 16, 'fore_rho': 17, 'fore_beta': 18,
      'hind_L1': 19, 'hind_L2': 20, 'hind_xm': 21, 'fore_pose_sh': 22,
      'fore_pose_el': 23, 'collapse_y': 24, 'pi': 25}
# cst (int scalars)
CI = {'nbod': 12, 'naxes': 13, 'settle_total': 0, 'contact': 1, 'power': 2, 'gait_enabled': 3,
      'capture_enabled': 4, 'posture_drive': 5, 'drive_en': 6,
      'reflex_level': 7, 'fold_budget': 8, 'unload_ticks': 9, 'tair': 10,
      'pelvis_row': 11}


# ═══════════════════ device helpers ═══════════════════
@cuda.jit(device=True, inline=True)
def mm(a, b, out):
    for i in range(4):
        for j in range(4):
            sm = 0.0
            for k in range(4):
                sm += a[i * 4 + k] * b[k * 4 + j]
            out[i * 4 + j] = sm


@cuda.jit(device=True, inline=True)
def rot_axis(axis, ang, out):
    c = math.cos(ang)
    s = math.sin(ang)
    t = 1.0 - c
    x = axis[0]; y = axis[1]; z = axis[2]
    out[0] = c + x * x * t; out[1] = x * y * t - z * s; out[2] = x * z * t + y * s; out[3] = 0.0
    out[4] = y * x * t + z * s; out[5] = c + y * y * t; out[6] = y * z * t - x * s; out[7] = 0.0
    out[8] = z * x * t - y * s; out[9] = z * y * t + x * s; out[10] = c + z * z * t; out[11] = 0.0
    out[12] = 0.0; out[13] = 0.0; out[14] = 0.0; out[15] = 1.0


@cuda.jit(device=True, inline=True)
def eye16(out):
    for i in range(16):
        out[i] = 0.0
    out[0] = 1.0; out[5] = 1.0; out[10] = 1.0; out[15] = 1.0


@cuda.jit(device=True, inline=True)
def axial3(m, out):
    out[0] = (m[8 + 1] - m[4 + 2]) * 0.5
    out[1] = (m[0 + 2] - m[8 + 0]) * 0.5
    out[2] = (m[4 + 0] - m[0 + 1]) * 0.5


@cuda.jit(device=True, inline=True)
def apply_point(m, p, out):
    for i in range(3):
        out[i] = m[i * 4 + 0] * p[0] + m[i * 4 + 1] * p[1] + m[i * 4 + 2] * p[2] + m[i * 4 + 3]


@cuda.jit(device=True, inline=True)
def transpose_rot(m, out):
    for i in range(16):
        out[i] = 0.0
    for i in range(3):
        for j in range(3):
            out[i * 4 + j] = m[j * 4 + i]
    out[15] = 1.0


@cuda.jit(device=True, inline=True)
def load16(src, off, out):
    for i in range(16):
        out[i] = src[off + i]


@cuda.jit(device=True, inline=True)
def inverse_spd18(a, out):
    # returns 1 ok / 0 refusal (coupled_mass / ill-conditioned)
    l = cuda.local.array(324, dtype=float64)
    for i in range(324):
        l[i] = 0.0
    for i in range(18):
        for j in range(i + 1):
            t = a[i * 18 + j]
            if abs(t - a[j * 18 + i]) > 1e-12:
                return 0
            if math.isnan(t):
                return 0
            for k in range(j):
                t -= l[i * 18 + k] * l[j * 18 + k]
            if i == j:
                if not (t > 0.0):
                    return 0
                l[i * 18 + j] = math.sqrt(t)
            else:
                l[i * 18 + j] = t / l[j * 18 + j]
    for col in range(18):
        y = cuda.local.array(18, dtype=float64)
        x = cuda.local.array(18, dtype=float64)
        for i in range(18):
            t = 0.0
            if i == col:
                t = 1.0
            for k in range(i):
                t -= l[i * 18 + k] * y[k]
            y[i] = t / l[i * 18 + i]
        ii = 17
        while ii >= 0:
            t = y[ii]
            for k in range(ii + 1, 18):
                t -= l[k * 18 + ii] * x[k]
            x[ii] = t / l[ii * 18 + ii]
            out[ii * 18 + col] = x[ii]
            ii -= 1
    an = 0.0
    bn = 0.0
    for i in range(18):
        ar = 0.0
        br = 0.0
        for j in range(18):
            ar += abs(a[i * 18 + j])
            br += abs(out[i * 18 + j])
        if ar > an:
            an = ar
        if br > bn:
            bn = br
    if math.isnan(an * bn) or an * bn >= 1e12:
        return 0
    return 1


@cuda.jit(device=True, inline=True)
def mat_vec(a, x, out):
    for i in range(18):
        s = 0.0
        for j in range(18):
            s += a[i * 18 + j] * x[j]
        out[i] = s


@cuda.jit(device=True, inline=True)
def row_dot(row, x):
    s = 0.0
    for i in range(18):
        s += row[i] * x[i]
    return s


