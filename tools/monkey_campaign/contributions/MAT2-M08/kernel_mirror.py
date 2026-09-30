"""MAT2-M08 kernel mirror — the declared CUDA kernel logic in pure numpy.

Each function is the EXACT statement-level mirror of one resident_gpu_world
kernel (same op order, same index order, float64), so the kernel logic is
validated against the sealed M07 oracle on any CPU before the CUDA port runs
on the GPU box; the CUDA kernels are a mechanical transcription of these
functions and X1 (GPU/direct-reference agreement) measures the port.
MirrorWorld is the shared host orchestration (commands, diagnostic block,
tick-digest chain, ledger gates) used for the local rehearsal and for the
falsifier arms. No GPU is touched here.

Upstream authority unchanged: MAT2-M07/integrated_step.py and its frozen
pins (M01/M03/M04/M06). Refusals are named codes.
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
CONTRIB = HERE.parent
for _p in (str(HERE), str(CONTRIB / 'MAT2-M01'), str(CONTRIB / 'MAT2-M03'),
           str(CONTRIB / 'MAT2-M04'), str(CONTRIB / 'MAT2-M06'),
           str(CONTRIB / 'MAT2-M07')):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import integrated_step as iw  # noqa: E402
import local_contact as lc    # noqa: E402  (M06 narrow phase, verbatim)

N_TRI, N_VERT, N_EDGES, N_ENTRIES = 80, 42, 120, 84
N_SUB = iw.N_SUB
DT_S = iw.DT_S
GS_TOL_N_S = iw.GS_TOL_N_S
GS_CAP = iw.GS_CAP
XPBD_TOL_M = iw.XPBD_TOL_M
XPBD_ITERATIONS_CAP = iw.XPBD_ITERATIONS_CAP
XPBD_COMPLIANCE = iw.XPBD_COMPLIANCE_M_PER_N
THICKNESS_M = iw.THICKNESS_M
CONTACT_MARGIN_M = iw.CONTACT_MARGIN_M
BETA_OVER_DT = iw.lc.BETA / iw.lc.DT
SLOP_M = iw.lc.SLOP_M
MU_TINY = iw.lc.MU_TINY
REST = iw.lc.RESTITUTION
CCD_TOL_M = iw.lc.CCD_TOL_M
MEM_MU_S, MEM_MU_K = iw.MEMBRANE_MU
PLA_MU_S, PLA_MU_K = iw.PLATE_MU
GRD_MU_S, GRD_MU_K = iw.GROUND_MU
RESID_FRACTION = iw.RESIDUAL_TURNOVER_FRACTION
G_M_S2 = iw.G_M_S2
DIAG = 96

# diagnostic block slots (must match resident_gpu_world exactly)
(D_KE, D_USCAFF, D_UMAT, D_QMAT, D_WIN, D_F, D_PLX, D_PLVX, D_PLVY, D_PLVZ,
 D_COMX, D_COMY, D_COMZ, D_VOL, D_MAXSPD, D_WPRESS, D_WGRAV, D_WMAT, D_QTICK,
 D_WCKE, D_DFRIC, D_DIMP, D_ESTAB, D_JNTOT, D_TRAP, D_PROJ, D_RESID, D_BOUND,
 D_WEXT, D_ITERS, D_GSRES, D_ACTIVE, D_MINJN, D_MINVN, D_CONE, D_STICK,
 D_ANCX, D_ANCY, D_ANCZ, D_WALLX, D_WALLY, D_WALLZ, D_GIMX, D_GIMY, D_GIMZ,
 D_GIPX, D_GIPY, D_GIPZ, D_CMX, D_CMY, D_CMZ, D_CPX, D_CPY, D_CPZ, D_CGX,
 D_CGY, D_CGZ, D_MATIMP, D_DP, D_TICK, D_DIGEST, D_STATUS, D_SUBCLOSE,
 D_RECIP, D_WSG, D_SGIMPX, D_SGIMPY, D_SGIMPZ, D_BHERR, D_BHRMS, D_BHDIR,
 D_PROJDMX, D_PROJDMY, D_PROJDMZ, D_ANCHORRES, D_PROJDPLATE, D_SPARE1,
 D_SPARE2, D_SPARE3, D_SPARE4, D_SPARE5, D_SPARE6, D_SPARE7, D_SPARE8,
 D_SPARE9, D_SPARE10, D_SPARE11, D_SPARE12, D_SPARE13, D_SPARE14, D_SPARE15,
 D_SPARE16, D_SPARE17, D_SPARE18, D_SPARE19, D_SPARE20) = range(DIAG)

N_PASS = 49
(P_WPRESS, P_WGRAVM, P_WGRAVP, P_GIMX, P_GIMY, P_GIMZ, P_GIPX, P_GIPY,
 P_GIPZ, P_WMAT, P_Q, P_MATIMP, P_SUBCLOSE, P_WCKE, P_DFRIC, P_DIMP,
 P_ESTAB, P_JNTOT, P_TRAP, P_ITERS, P_GSRES, P_ACTIVE, P_MINJN, P_MINVN,
 P_CONE, P_STICK, P_ANCX, P_ANCY, P_ANCZ, P_CMX, P_CMY, P_CMZ, P_CPX,
 P_CPY, P_CPZ, P_CGX, P_CGY, P_CGZ, P_RECIPX, P_RECIPY, P_RECIPZ, P_PROJ,
 P_WSG, P_SGIMPX, P_SGIMPY, P_SGIMPZ, P_SGIPX, P_SGIPY,
 P_SGIPZ) = range(N_PASS)

E_ORDER = 'declared_order_mismatch'
E_TICK = 'tick_sequence_invalid'
E_UNEXPLAINED = 'unexplained_energy'
E_MOMENTUM = 'momentum_ledger_open'
E_CONV = 'convergence_gate_not_met'
E_SUBLEDGER = 'material_subledger_open'
E_RECIPOCITY = 'ledger_imbalance'
E_SEPARATION = 'contact_separation_violation'
E_STICK = 'contact_stick_violation'
E_ANCHOR = 'anchor_reaction_imbalance'
E_STALE = 'stale_diagnostics_detected'
E_BH = 'bh_error_window_exceeded'
STATUS_OK = 0.0


def require(condition, code):
    if not condition:
        raise ValueError(code)


def sha_digest(value):
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(',', ':'),
        ensure_ascii=False, allow_nan=False).encode('utf-8')).hexdigest()


def block_digest(block, tick):
    """The declared tick-digest chain over the diagnostic block (deterministic
    float arithmetic; recomputed by the host to catch stale reads — F3)."""
    d = 0.0
    for i in range(DIAG):
        d = (d * 1.0000000000000002 + block[i] * (i + 1)) % 1000000007.0
    return (d + float(tick) * 7919.0) % 1000000007.0


# ---- body accessors (the entry layout: 0..79 membrane tris, 80..81 plate, ----
# ---- 82..83 ground; kind 0 membrane port, 1 plate, 2 ground) -----------------

def body_kind(e):
    return 0 if e < N_TRI else (1 if e < N_TRI + 2 else 2)


def body_vel(st, e):
    k = body_kind(e)
    if k == 0:
        vids = st['tris'][e]
        return st['v'][vids].mean(axis=0)
    if k == 1:
        return st['pv'].copy()
    return np.zeros(3)


def write_body_vel(st, e, value):
    k = body_kind(e)
    if k == 0:
        vids = st['tris'][e]
        delta = np.asarray(value, dtype=np.float64) \
            - st['v'][vids].mean(axis=0)
        st['v'][vids] += delta
    elif k == 1:
        st['pv'][:] = value


def body_inv_m(st, e):
    k = body_kind(e)
    if k == 0:
        return 1.0 / st['port_mass'][e]
    if k == 1:
        return 1.0 / st['plate_mass']
    return 0.0


def pair_mu(ea, eb):
    mus = {0: (MEM_MU_S, MEM_MU_K), 1: (PLA_MU_S, PLA_MU_K),
           2: (GRD_MU_S, GRD_MU_K)}
    a, b = mus[body_kind(ea)], mus[body_kind(eb)]
    return min(a[0], b[0]), min(a[1], b[1])


def entry_tri(st, e):
    """The 3 current vertices of entry e (M07 shells order: membrane tris
    0..79, plate tris 80..81 = (0,1,2)/(0,2,3), ground 82..83 same)."""
    if e < N_TRI:
        return st['x'][st['tris'][e]]
    tt = (e - N_TRI) % 2
    idx = [0, 1, 2] if tt == 0 else [0, 2, 3]
    src = st['px'] if e < N_TRI + 2 else st['gx']
    return src[idx]


# ---- kernels (statement mirrors of the CUDA passes) --------------------------

def k_reset(st):
    st['v_start'] = st['v'].copy()
    st['pv_start'] = st['pv'].copy()
    st['e_prev'] = ke_total(st) + scaffold_energy(st) + st['U_mat']
    st['u_mat_prev'] = st['U_mat']
    st['u_scaff_prev'] = scaffold_energy(st)
    st['P'] = np.zeros((N_SUB, N_PASS))
    st['sg_imp_mem'] = np.zeros(3)
    st['sg_imp_plate'] = np.zeros(3)
    st['w_sg'] = 0.0


def k_pressure_geometry(st, dp):
    tri = st['x'][st['tris']]
    e1 = tri[:, 1] - tri[:, 0]
    e2 = tri[:, 2] - tri[:, 0]
    cross = np.cross(e1, e2)
    two_area = np.linalg.norm(cross, axis=1)
    normals = cross / two_area[:, None]
    areas = 0.5 * two_area
    st['areas'] = areas
    st['forces'] = dp * areas[:, None] * normals


def k_pressure_lump_velocity(st, grav, h):
    forces = st['forces']
    loads = np.zeros_like(st['x'])
    tris = st['tris']
    np.add.at(loads, tris[:, 0], forces / 3.0)
    np.add.at(loads, tris[:, 1], forces / 3.0)
    np.add.at(loads, tris[:, 2], forces / 3.0)
    st['loads'] = loads
    st['v_pre'] = st['v'].copy()
    g_loads = st['masses'][:, None] * grav[None, :]
    st['g_loads'] = g_loads
    st['v'] = st['v'] + (loads + g_loads) * st['inv_masses'][:, None] * h


def k_pressure_plate(st, grav, h, sub):
    P = st['P']
    m = st['plate_mass']
    gmx, gmy, gmz = grav[0] * m, grav[1] * m, grav[2] * m
    vx0, vy0, vz0 = st['pv']
    inv_m = 1.0 / m
    st['pv'] = np.array([vx0 + gmx * inv_m * h, vy0 + gmy * inv_m * h,
                         vz0 + gmz * inv_m * h])
    bx = 0.5 * (vx0 + st['pv'][0])
    by = 0.5 * (vy0 + st['pv'][1])
    bz = 0.5 * (vz0 + st['pv'][2])
    P[sub, P_WGRAVP] = ((gmx * bx + gmy * by) + gmz * bz) * h
    P[sub, P_GIPX] = gmx * h
    P[sub, P_GIPY] = gmy * h
    P[sub, P_GIPZ] = gmz * h


def k_pressure_diag_sub(st, h, sub):
    P = st['P']
    loads, g_loads = st['loads'], st['g_loads']
    v_bar = 0.5 * (st['v_pre'] + st['v'])
    P[sub, P_WPRESS] = float((loads * v_bar).sum()) * h
    P[sub, P_WGRAVM] = float((g_loads * v_bar).sum()) * h
    P[sub, P_GIMX:P_GIMZ + 1] = (g_loads * h).sum(axis=0)


def k_material(st, alpha, k_el, c_el, h, sub):
    P = st['P']
    a = st['F']
    v1x = float(st['pv'][0])
    tau = c_el / k_el
    b = c_el * v1x
    d = a - b
    int_F_dt = b * h + (a - b) * tau * (1.0 - alpha)
    int_F2_dt = b * b * h + 2.0 * b * d * tau * (1.0 - alpha) \
        + d * d * (tau / 2.0) * (1.0 - alpha * alpha)
    F_next = alpha * a + c_el * v1x * (1.0 - alpha)
    u_prev = a * a / (2.0 * k_el)
    u_i = F_next * F_next / (2.0 * k_el)
    q_i = int_F2_dt / c_el
    J = int_F_dt
    inv_m = 1.0 / st['plate_mass']
    v_pre_x = float(st['pv'][0])
    st['pv'][0] = st['pv'][0] - J * inv_m
    w_on_plate = -J * (0.5 * (v_pre_x + st['pv'][0]))
    st['F'] = F_next
    st['U_mat'] = u_i
    st['Q_mat'] += q_i
    st['W_in'] += v1x * J
    P[sub, P_WMAT] = w_on_plate
    P[sub, P_Q] = q_i
    P[sub, P_MATIMP] = -J
    P[sub, P_SUBCLOSE] = abs((v1x * J) - ((u_i - u_prev) + q_i))


def ke_total(st):
    ke = float((0.5 * st['masses'][:, None] * st['v'] ** 2).sum())
    ke += 0.5 * st['plate_mass'] * float(np.dot(st['pv'], st['pv']))
    return ke


def scaffold_energy(st):
    diff = st['x'][st['edges'][:, 0]] - st['x'][st['edges'][:, 1]]
    lengths = np.linalg.norm(diff, axis=1)
    return float(((lengths - st['rest']) ** 2).sum()
                 / (2.0 * XPBD_COMPLIANCE))


def signed_volume(st):
    tri = st['x'][st['tris']]
    return float(np.einsum('ij,ij->i', tri[:, 0],
                           np.cross(tri[:, 1], tri[:, 2])).sum() / 6.0)


def k_contact(st, h, sub):
    """M06 sweep -> narrow -> GS on the flat entry layout (single declared
    sequential order). Buckets: 0 membrane ports, 1 plate, 2 ground."""
    P = st['P']
    speed_m = float(np.linalg.norm(st['v'], axis=1).max())
    speed_p = float(np.linalg.norm(st['pv']))
    motion = max(speed_m, speed_p) * h
    inflate = motion + THICKNESS_M + CONTACT_MARGIN_M
    entries = []
    for e in range(N_ENTRIES):
        corners = entry_tri(st, e)
        entries.append((body_kind(e), e,
                        tuple(corners.min(axis=0) - inflate),
                        tuple(corners.max(axis=0) + inflate)))
    cand = lc.sweep_prune(entries)
    ke_pre = ke_total(st)
    active = []
    for (i, j) in cand:
        p, q, dist = lc.tri_tri_closest(
            *[tuple(v) for v in entry_tri(st, i)],
            *[tuple(v) for v in entry_tri(st, j)])
        gap = dist - THICKNESS_M
        if gap <= CONTACT_MARGIN_M + CCD_TOL_M:
            normal = lc.vunit(lc.vsub(p, q)) if dist > 0.0 else (0.0, 0.0, 1.0)
            active.append((i, j, gap, normal))
    contact = {0: np.zeros(3), 1: np.zeros(3), 2: np.zeros(3)}
    recip = np.zeros(3)
    d_friction = 0.0
    d_impact = 0.0
    trap = 0.0
    jn_total = 0.0
    iterations = 0
    max_jn = 0.0
    records = []
    for iteration in range(GS_CAP):
        iterations = iteration + 1
        records = []
        pass_max = 0.0
        for (ea, eb, gap, normal) in active:
            va_pre = body_vel(st, ea).copy()
            vb_pre = body_vel(st, eb).copy()
            inv_ma = body_inv_m(st, ea)
            inv_mb = body_inv_m(st, eb)
            m_eff = 1.0 / (inv_ma + inv_mb)
            rv = va_pre - vb_pre
            vn = float(np.dot(rv, np.asarray(normal)))
            pen = -gap
            bias = BETA_OVER_DT * max(pen - SLOP_M, 0.0)
            jn = max(m_eff * (-(1.0 + REST) * vn + bias), 0.0)
            jn_vec = np.asarray(normal) * jn
            write_body_vel(st, ea, va_pre + jn_vec * inv_ma)
            write_body_vel(st, eb, vb_pre - jn_vec * inv_mb)
            va_post = body_vel(st, ea)
            vb_post = body_vel(st, eb)
            rv = va_post - vb_post
            vn_after = float(np.dot(rv, np.asarray(normal)))
            vt_vec = rv - np.asarray(normal) * vn_after
            vt_pre = float(np.linalg.norm(vt_vec))
            mu_s, mu_k = pair_mu(ea, eb)
            jt_mag, mode = 0.0, 'still'
            jt_vec = np.zeros(3)
            if vt_pre > MU_TINY:
                jt_req = m_eff * vt_pre
                jt_dir = vt_vec * (-1.0 / vt_pre)
                if jt_req <= mu_s * jn:
                    jt_mag, mode = jt_req, 'stick'
                else:
                    jt_mag, mode = mu_k * jn, 'slip'
                jt_vec = jt_dir * jt_mag
                write_body_vel(st, ea, va_post + jt_vec * inv_ma)
                write_body_vel(st, eb, vb_post - jt_vec * inv_mb)
            va_post2 = body_vel(st, ea)
            vb_post2 = body_vel(st, eb)
            rv = va_post2 - vb_post2
            vn2 = float(np.dot(rv, np.asarray(normal)))
            vt_post = float(np.linalg.norm(rv - np.asarray(normal) * vn2))
            w_f = 0.5 * m_eff * max(vt_pre * vt_pre - vt_post * vt_post, 0.0)
            records.append({'jn': jn, 'jt': jt_mag, 'mode': mode,
                            'm_eff': m_eff, 'ea': ea, 'eb': eb,
                            'normal': normal})
            pass_max = max(pass_max, jn, abs(jt_mag))
            impulse = jn_vec + jt_vec
            for holder, imp in ((ea, impulse), (eb, -impulse)):
                contact[body_kind(holder)] += imp
            recip = recip + impulse + (-impulse)
            trap += float(0.5 * np.dot(0.5 * (va_pre + va_post2), impulse)
                          + 0.5 * np.dot(0.5 * (vb_pre + vb_post2), -impulse))
            d_friction += float(w_f)
            jn_total += abs(jn)
            vn_pre = float(np.dot(va_pre - vb_pre, np.asarray(normal)))
            if vn_pre < 0.0:
                d_impact += 0.5 * m_eff * vn_pre * vn_pre
        max_jn = pass_max
        if pass_max <= GS_TOL_N_S:
            break
    ke_post = ke_total(st)
    w_contact_ke = -(ke_post - ke_pre)
    min_jn = min((r['jn'] for r in records), default=0.0)
    min_vn = 0.0
    cone = 0.0
    stick = 0.0
    for r, (ea, eb, gap, normal) in zip(records, active):
        va = body_vel(st, ea)
        vb = body_vel(st, eb)
        rv = va - vb
        vn_post = float(np.dot(rv, np.asarray(normal)))
        min_vn = min(min_vn, vn_post)
        if r['jn'] > 0.0 and r['mode'] != 'still':
            mu_s, mu_k = pair_mu(ea, eb)
            mu_used = mu_s if r['mode'] == 'stick' else mu_k
            cone = max(cone, max(0.0, abs(r['jt']) - mu_used * r['jn']
                                 - 1e-15))
        if r['mode'] == 'stick':
            vt = rv - vn_post * np.asarray(normal)
            stick = max(stick, float(np.linalg.norm(vt)))
    P[sub, P_WCKE] = w_contact_ke
    P[sub, P_DFRIC] = d_friction
    P[sub, P_DIMP] = d_impact
    P[sub, P_ESTAB] = -w_contact_ke + d_friction + d_impact
    P[sub, P_JNTOT] = jn_total
    P[sub, P_TRAP] = trap
    P[sub, P_ITERS] = float(iterations)
    P[sub, P_GSRES] = max_jn
    P[sub, P_ACTIVE] = float(len(active))
    P[sub, P_MINJN] = min_jn
    P[sub, P_MINVN] = min_vn
    P[sub, P_CONE] = cone
    P[sub, P_STICK] = stick
    P[sub, P_ANCX:P_ANCZ + 1] = -contact[2]
    P[sub, P_CMX:P_CMZ + 1] = contact[0]
    P[sub, P_CPX:P_CPZ + 1] = contact[1]
    P[sub, P_CGX:P_CGZ + 1] = contact[2]
    P[sub, P_RECIPX:P_RECIPZ + 1] = recip
    st['records'] = records
    require(max_jn <= GS_TOL_N_S, E_CONV)
    require(min_vn >= -1e-9, E_SEPARATION)
    require(stick <= 1e-9, E_STICK)
    require(float(np.linalg.norm(recip)) <= 1e-12, E_RECIPOCITY)


def k_integrate(st, h):
    st['x_pre'] = st['x'].copy()
    st['x'] = st['x'] + st['v'] * h
    st['px'] = st['px'] + st['pv'] * h


def k_xpbd(st, h, sub):
    P = st['P']
    ke_pre = ke_total(st)          # velocities unchanged by integration
    us_pre = scaffold_energy({'x': st['x_pre'], 'edges': st['edges'],
                              'rest': st['rest']})   # M07: pre-integration x
    x = st['x']
    inv = st['inv_masses']
    alpha_tilde = XPBD_COMPLIANCE / (h * h)
    lam = np.zeros(len(st['edges']))
    for _ in range(XPBD_ITERATIONS_CAP):
        max_c = 0.0
        for e, (a1, a2) in enumerate(st['edges']):
            d = x[a2] - x[a1]
            length = float(np.linalg.norm(d))
            if length == 0.0:
                continue
            grad = d / length
            cc = length - st['rest'][e]
            max_c = max(max_c, abs(cc))
            w_sum = inv[a1] + inv[a2]
            dlam = (-cc - alpha_tilde * lam[e]) / (w_sum + alpha_tilde)
            lam[e] += dlam
            x[a1] -= inv[a1] * dlam * grad
            x[a2] += inv[a2] * dlam * grad
        if max_c <= XPBD_TOL_M:
            break
    st['v'] = (st['x'] - st['x_pre']) / h
    P[sub, P_PROJ] = (ke_total(st) - ke_pre) + (scaffold_energy(st) - us_pre)


# ---- tick fold: per-substep accumulation in M07's declared order -------------

def fold_tick(st, tick, dp, h):
    P = st['P']
    tot = np.zeros(N_PASS)
    for sub in range(N_SUB):
        for s in range(N_PASS):
            tot[s] = tot[s] + P[sub, s]
    w_press = tot[P_WPRESS]
    # per-substep w_grav = membrane + plate (membrane first), folded in order
    w_grav = 0.0
    g_imp_mem = np.zeros(3)
    g_imp_plate = np.zeros(3)
    for sub in range(N_SUB):
        w_grav = w_grav + (P[sub, P_WGRAVM] + P[sub, P_WGRAVP])
        g_imp_mem = g_imp_mem + P[sub, P_GIMX:P_GIMZ + 1]
        g_imp_plate = g_imp_plate + P[sub, P_GIPX:P_GIPZ + 1]
    w_mat = 0.0
    q_tick = 0.0
    mat_imp = 0.0
    subclose = 0.0
    for sub in range(N_SUB):
        w_mat = w_mat + P[sub, P_WMAT]
        q_tick = q_tick + P[sub, P_Q]
        mat_imp = mat_imp + P[sub, P_MATIMP]
        subclose = max(subclose, P[sub, P_SUBCLOSE])
    wcke = 0.0
    dfric = 0.0
    dimp = 0.0
    estab = 0.0
    jntot = 0.0
    trap = 0.0
    iters = 0.0
    gsres = 0.0
    active = 0.0
    minjn = None
    minvn = None
    cone = 0.0
    stick = 0.0
    contact_mem = np.zeros(3)
    contact_pl = np.zeros(3)
    contact_gnd = np.zeros(3)
    anchor_tick = np.zeros(3)
    recip = np.zeros(3)
    proj = 0.0
    for sub in range(N_SUB):
        wcke = wcke + P[sub, P_WCKE]
        dfric = dfric + P[sub, P_DFRIC]
        dimp = dimp + P[sub, P_DIMP]
        estab = estab + P[sub, P_ESTAB]
        jntot = jntot + P[sub, P_JNTOT]
        trap = trap + P[sub, P_TRAP]
        iters = iters + P[sub, P_ITERS]
        gsres = max(gsres, P[sub, P_GSRES])
        active = active + P[sub, P_ACTIVE]
        minjn = P[sub, P_MINJN] if minjn is None else min(minjn,
                                                          P[sub, P_MINJN])
        minvn = P[sub, P_MINVN] if minvn is None else min(minvn,
                                                          P[sub, P_MINVN])
        cone = max(cone, P[sub, P_CONE])
        stick = max(stick, P[sub, P_STICK])
        contact_mem = contact_mem + P[sub, P_CMX:P_CMZ + 1]
        contact_pl = contact_pl + P[sub, P_CPX:P_CPZ + 1]
        contact_gnd = contact_gnd + P[sub, P_CGX:P_CGZ + 1]
        anchor_tick = anchor_tick + P[sub, P_ANCX:P_ANCZ + 1]
        recip = recip + P[sub, P_RECIPX:P_RECIPZ + 1]
        proj = proj + P[sub, P_PROJ]
    # state at the closed tick (M05 A1 rule: energies at THIS configuration)
    ke = ke_total(st)
    uscaff = scaffold_energy(st)
    umat = st['U_mat']
    e_mech = ke + uscaff + umat
    w_sg = st.get('w_sg', 0.0)
    w_external = w_press + w_grav + w_sg
    turnover = abs(w_press) + abs(w_grav) + abs(w_mat) + abs(wcke) + ke
    bound = (RESID_FRACTION * turnover + umat + st['u_mat_prev']
             + uscaff + st['u_scaff_prev'] + 1e-9)
    residual = (e_mech - st['e_prev'] - w_external + q_tick + dfric + dimp
                - estab - proj)
    require(abs(residual) <= bound, E_UNEXPLAINED)
    # momentum ledger (M07 Amendment A1 (iii); far-field terms per M08 A1)
    mem_dv = (st['masses'][:, None] * (st['v'] - st['v_start'])).sum(axis=0)
    proj_delta_mem = mem_dv - (g_imp_mem + st['sg_imp_mem'] + contact_mem)
    plate_dv = st['plate_mass'] * (st['pv'] - st['pv_start'])
    mat_imp_vec = np.array([mat_imp, 0.0, 0.0])
    plate_terms = g_imp_plate + contact_pl + st['sg_imp_plate'] + mat_imp_vec
    proj_delta_plate = plate_dv - plate_terms
    require(float(np.linalg.norm(proj_delta_plate)) <= 1e-12, E_MOMENTUM)
    anchor_resid = float(np.linalg.norm(anchor_tick + contact_gnd))
    require(anchor_resid <= 1e-12, E_ANCHOR)
    require(subclose <= 1e-9, E_SUBLEDGER)
    # boundary cumulative updates (M07 per-tick)
    st['anchor_cum'] = st['anchor_cum'] + anchor_tick
    st['wall_cum'] = st['wall_cum'] + (-mat_imp_vec)
    com = (st['x'] * st['masses'][:, None]).sum(axis=0) \
        / st['masses'].sum()
    block = np.zeros(DIAG)
    block[D_KE] = ke
    block[D_USCAFF] = uscaff
    block[D_UMAT] = umat
    block[D_QMAT] = st['Q_mat']
    block[D_WIN] = st['W_in']
    block[D_F] = st['F']
    block[D_PLX] = float(st['px'][:, 0].mean())
    block[D_PLVX:D_PLVZ + 1] = st['pv']
    block[D_COMX:D_COMZ + 1] = com
    block[D_VOL] = signed_volume(st)
    block[D_MAXSPD] = float(np.abs(st['v']).max())
    block[D_WPRESS] = w_press
    block[D_WGRAV] = w_grav
    block[D_WMAT] = w_mat
    block[D_QTICK] = q_tick
    block[D_WCKE] = wcke
    block[D_DFRIC] = dfric
    block[D_DIMP] = dimp
    block[D_ESTAB] = estab
    block[D_JNTOT] = jntot
    block[D_TRAP] = trap
    block[D_PROJ] = proj
    block[D_RESID] = residual
    block[D_BOUND] = bound
    block[D_WEXT] = w_external
    block[D_ITERS] = iters
    block[D_GSRES] = gsres
    block[D_ACTIVE] = active
    block[D_MINJN] = minjn
    block[D_MINVN] = minvn
    block[D_CONE] = cone
    block[D_STICK] = stick
    block[D_ANCX:D_ANCZ + 1] = st['anchor_cum']
    block[D_WALLX:D_WALLZ + 1] = st['wall_cum']
    block[D_GIMX:D_GIMZ + 1] = g_imp_mem
    block[D_GIPX:D_GIPZ + 1] = g_imp_plate
    block[D_CMX:D_CMZ + 1] = contact_mem
    block[D_CPX:D_CPZ + 1] = contact_pl
    block[D_CGX:D_CGZ + 1] = contact_gnd
    block[D_MATIMP] = mat_imp
    block[D_DP] = dp
    block[D_TICK] = float(tick)
    block[D_STATUS] = STATUS_OK
    block[D_SUBCLOSE] = subclose
    block[D_RECIP] = float(np.linalg.norm(recip))
    block[D_PROJDMX:D_PROJDMZ + 1] = proj_delta_mem
    block[D_ANCHORRES] = anchor_resid
    block[D_PROJDPLATE] = float(np.linalg.norm(proj_delta_plate))
    block[D_WSG] = w_sg
    block[D_SGIMPX:D_SGIMPZ + 1] = st['sg_imp_mem']
    block[D_DIGEST] = 0.0
    block[D_DIGEST] = block_digest(block, tick)
    return block


# ---- the mirror world (shared host orchestration) ----------------------------

class MirrorWorld:
    """CPU executor with the resident world's exact host/kernel structure:
    bounded commands, a fixed per-component diagnostic block, the chained
    tick digest, snapshots only at declared ticks."""

    def __init__(self, components, dt_s=DT_S, gravity=True, far_field=False):
        require(len(components) >= 1, 'world_components_invalid')
        self.dt_s = float(dt_s)
        self.gravity = bool(gravity)
        self.far_field = bool(far_field)
        self.tick = 0
        self.host_bytes_up = 0
        self.host_bytes_down = 0
        self.snapshots = {}
        self.states = []
        for c in components:
            edges = {}
            for a, b, cc in c.membrane.triangles.tolist():
                for u, w in ((a, b), (b, cc), (cc, a)):
                    edges[(min(u, w), max(u, w))] = True
            edge_list = sorted(edges)
            port_mass = np.array([
                c.masses[list(t)].sum() for t in c.membrane.triangles])
            self.states.append({
                'x': c.x.copy(), 'v': c.v.copy(),
                'px': c.plate.x.copy(), 'pv': c.plate.velocity.copy(),
                'gx': c.ground.x.copy(),
                'tris': np.asarray(c.membrane.triangles),
                'edges': np.array(edge_list, dtype=np.int64),
                'rest': np.array([float(np.linalg.norm(c.rest[b] - c.rest[a]))
                                  for a, b in edge_list]),
                'masses': c.masses.copy(),
                'inv_masses': c.inv_masses.copy(),
                'port_mass': port_mass,
                'plate_mass': float(c.plate.mass_kg),
                'F': float(c.F), 'U_mat': float(c.U_mat),
                'Q_mat': float(c.Q_mat), 'W_in': float(c.W_in_mat),
                'anchor_cum': np.zeros(3), 'wall_cum': np.zeros(3),
            })
        k_el, c_el = components[0].maxwell_element()
        self.k_el = float(k_el)
        self.c_el = float(c_el)
        self.grav = np.array([0.0, 0.0,
                              -G_M_S2 * (1.0 if self.gravity else 0.0)])
        self.declaration = {
            'schema': 'chimera.resident_gpu_world.v1',
            'order': list(iw.DECLARED_ORDER),
            'dt_s': self.dt_s,
            'substeps_per_tick': N_SUB,
            'far_field': self.far_field,
            'telemetry_f64_per_comp': DIAG,
            'cmd_f64': 12,
        }
        self.order_digest = sha_digest(self.declaration)

    def step_tick(self, tick, dp_pa):
        require(tick == self.tick, E_TICK)
        h = self.dt_s / N_SUB
        alpha = math.exp(-h / (self.c_el / self.k_el))
        self.host_bytes_up += 8 * 3        # dp, h, alpha commands
        for st in self.states:
            st['declared_digest_ok'] = True
            k_reset(st)
            for sub in range(N_SUB):
                k_pressure_geometry(st, float(dp_pa))
                k_pressure_lump_velocity(st, self.grav, h)
                k_pressure_plate(st, self.grav, h, sub)
                k_pressure_diag_sub(st, h, sub)
                k_material(st, alpha, self.k_el, self.c_el, h, sub)
                k_contact(st, h, sub)
                if self.far_field:
                    self._far_field(st, h, sub)
                k_integrate(st, h)
                k_xpbd(st, h, sub)
            block = fold_tick(st, tick, float(dp_pa), h)
            st['block'] = block
        self.tick = tick + 1

    def _far_field(self, st, h, sub):
        """Rehearsal form of the declared far-field pass (Amendment A1): the
        exact direct sum stands in for the theta-gated traversal here (the
        CUDA Barnes-Hut is validated against this same direct reference on
        the GPU by its own frozen error window). External point-mass
        self-gravity on the resident state; work = trapezoid over the dv."""
        from resident_bh import bh_bodies_host, bh_direct_numpy, G_N

        class _C:
            pass
        comps = []
        for s2 in self.states:
            c = _C()
            c.x = s2['x']
            c.masses = s2['masses']
            c.plate = _C()
            c.plate.x = s2['px']
            c.plate.mass_kg = s2['plate_mass']
            comps.append(c)
        xs, ms = bh_bodies_host(comps)
        accel = bh_direct_numpy(xs, ms)
        v_pre = st['v'].copy()
        pv_pre = st['pv'].copy()
        st['v'] = st['v'] + accel[:N_VERT] * h
        dv_plate = accel[N_VERT:].sum(axis=0) * h
        st['pv'] = st['pv'] + dv_plate
        sg_imp_mem = (st['masses'][:, None] * accel[:N_VERT] * h).sum(axis=0)
        sg_imp_plate = st['plate_mass'] * dv_plate
        v_bar = 0.5 * (v_pre + st['v'])
        w_sg = float((st['masses'][:, None] * accel[:N_VERT] * v_bar).sum()) \
            * h
        pv_bar = 0.5 * (pv_pre + st['pv'])
        w_sg += float(np.dot(st['plate_mass'] * accel[N_VERT:].sum(axis=0),
                             pv_bar)) * h
        st['P'][sub, P_WSG] = w_sg
        st['P'][sub, P_SGIMPX:P_SGIMPZ + 1] = sg_imp_mem
        st['P'][sub, P_SGIPX:P_SGIPZ + 1] = sg_imp_plate
        st['sg_imp_mem'] = st['sg_imp_mem'] + sg_imp_mem
        st['sg_imp_plate'] = st['sg_imp_plate'] + sg_imp_plate
        st['w_sg'] = st['w_sg'] + w_sg

    def diagnostics(self):
        self.host_bytes_down += 8 * DIAG * len(self.states)
        return np.stack([st['block'] for st in self.states])

    def snapshot(self, tick):
        st = self.states[0]
        self.host_bytes_down += st['x'].nbytes + st['px'].nbytes
        self.snapshots[tick] = {
            'membrane_positions_m': st['x'].tolist(),
            'plate_vertices_m': st['px'].tolist(),
        }
        return self.snapshots[tick]
