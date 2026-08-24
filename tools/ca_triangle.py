#!/usr/bin/env python
"""ca_triangle.py -- T2 FIRST CA RUN on cad_bear (pre-registered in docs/THE_TRIANGLE_CARRIER.md).

One area mode per triangle: F(v) = -k*(A/A0 - 1)*grad_A, symplectic Euler at dt=DT.
R7b closure: the CA area-bond is DERIVED from the SAME edge-bond energy as the
resistance (one energy, two consistent gradients -- no free number). A0_bond = import
area scaled to R_BOND edges; k_A = K_BOND/(4*A0_bond), so the CA restoring slope
equals the bond algebra's K_BOND/R_BOND**2 (RUN A passes by construction).
Space = walk space, S = R_BOND / e_med (median shared-edge length of the parsed
lattice); vertex mass m = 1 each (seed convention).

RUN A (static): central-difference CA restoring slope across one named shared edge
around r=R_BOND vs the M=0 bond algebra's linearized slope K_BOND/R_BOND**2,
gate <= 1% relative. Derivation is by construction; this gate catches algebra and
index bugs in the update rule (honestly labeled).
RUN B (live): from rest at import pose under the fold walk read by compute_forces_mod
(GPU if available), octree rebuilt per tick -- a live frame's tree moves with its
points. Gates: finiteness; energy accounting net of radiated wall power,
dE <= W_rad + 1%*peak_E (radiation is honest dissipation, not drift); max |A/A0-1|
printed as the honesty line feeding the band-clamp sub-gate (number stays derived
after this run per the sub-gate).

Usage:   python tools/ca_triangle.py
Output:  models/cad_bear/ca_run.json + verdict table on stdout.
"""
from __future__ import annotations

import json
import math
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))

# Operator directive: pin numba's parallel thread pool to my 24 physical cores.
os.environ.setdefault("NUMBA_NUM_THREADS", "24")

import numpy as np
from numba import njit, prange

from cad_sample import load_glb_triangles                     # bit-exact import chain
from LightEngine import constants as C                        # noqa: E402
from LightEngine.bh_draw import build_octree, DEFAULT_THETA   # noqa: E402
from LightEngine.modifier import compute_forces_mod           # noqa: E402

GLB = ROOT / "models" / "cad_bear" / "cad_bear.glb"
OUT = ROOT / "models" / "cad_bear" / "ca_run.json"
PROG = ROOT / "agent_logs" / "ca_run_progress.txt"   # line-buffered per-tick evidence

TICKS = 1000          # RUN B length, named before the run (flagged synthesis)
GATE_REL = 0.01       # <= 1% relative -- same number as the energy gate
RSS_GUARD_GB = 8.0    # memory guard: dump partial JSON and stop if RSS exceeds this
NEAR_ZERO_A0 = 1e-15  # float64 floor: A0 < this is degenerate
EVERY_TICK = os.environ.get("CA_EVERY_TICK") == "1"   # long-horizon leak diagnostic


def _rss_mb() -> float:
    """Process RSS in MB (psutil if present, else Windows ctypes)."""
    try:
        import psutil
        return psutil.Process().memory_info().rss / 1e6
    except Exception:
        pass
    import ctypes
    class _PMI(ctypes.Structure):
        _fields_ = [("cb", ctypes.c_size_t), ("WorkingSet", ctypes.c_size_t)]
    pmi = _PMI()
    ok = ctypes.windll.psapi.GetProcessMemoryInfo(
        ctypes.windll.kernel32.GetCurrentProcess(),
        ctypes.byref(pmi), ctypes.sizeof(_PMI))
    return pmi.WorkingSet / 1e6 if ok else -1.0


_dev_handle = None
try:
    import pynvml as _pynvml
    _pynvml.nvmlInit()
    _dev_handle = _pynvml.nvmlDeviceGetHandleByIndex(0)
except Exception:  # NVML unavailable in this context -> telemetry degrades to -1
    _dev_handle = None


def _dev_mb() -> float:
    """GPU device memory in MB (best-effort; -1 if NVML unavailable). Per-tick curve
    evidence for the operator's 'memory leak' observation -- captures peak-hold on disk."""
    if _dev_handle is None:
        return -1.0
    try:
        i = _pynvml.nvmlDeviceGetMemoryInfo(_dev_handle)
        return (i.total - i.free) / 1e6
    except Exception:
        return -1.0


def build_lattice():
    """Parse GLB -> global verts scaled to walk space, tris, A0, S."""
    parts = load_glb_triangles(GLB)

    def part_edges(v, t):
        slots = ((0, 1), (1, 2), (2, 0))
        pairs = [np.sort(np.stack([t[:, j], t[:, k]], axis=1), axis=1) for j, k in slots]
        L = [np.linalg.norm(v[t[:, b]] - v[t[:, a]], axis=1) for a, b in ((0, 1), (1, 2), (2, 0))]
        allp = np.vstack(pairs)
        _, inv = np.unique(allp, axis=0, return_inverse=True)
        cntE = np.bincount(inv, minlength=int(inv.max()) + 1 if len(inv) else 1)
        shared_rows = (cntE == 2)
        k = t.shape[0]
        masks = [shared_rows[inv[s * k:(s + 1) * k]] for s in range(3)]
        return L, masks

    edge_lens = []
    per_part_tris = []
    for name, v, i in parts:
        t = np.ascontiguousarray(i)
        per_part_tris.append(t)
        Ls, masks = part_edges(v, t)
        for L, m in zip(Ls, masks):
            edge_lens.append(L[m])

    e_med = float(np.median(np.concatenate(edge_lens)))
    S = C.R_BOND / e_med

    Vg, Tg = [], []
    base = 0
    for (_, v, _), t in zip(parts, per_part_tris):
        Vg.append(np.ascontiguousarray(v * S))
        Tg.append(t + base)
        base += len(v)                                  # offset by VERTS, not tris
    Vg = np.concatenate(Vg); Tg = np.ascontiguousarray(np.concatenate(Tg))

    # EXACT-duplicate-vertex merge (NO free parameter): two vertices at the identical float32
    # location are ONE point for the walk. cad_bear's degenerate triangles pile up to 48 verts
    # on one spot; left raw they make build_octree pathologically slow (>480 s, single core) and
    # its traversal overflow _STACK_SIZE=64 -> nan at tick 0 (measured). Merging the bit-identical
    # rows makes the build 0.38 s / finite (measured on this lattice). Counted in the ledger;
    # total faders (tris) unchanged. Tris that collapse to zero area after a merge are dropped by
    # the existing degen filter downstream, so CA + walk stay consistent in deduped space.
    Vg32 = np.ascontiguousarray(Vg, dtype=np.float32)          # what the walk actually sees
    key = np.stack([Vg32[:, 0].view(np.int32), Vg32[:, 1].view(np.int32),
                    Vg32[:, 2].view(np.int32)], axis=1)
    uniq_key, vmap_inv = np.unique(key, axis=0, return_inverse=True)
    n_orig_verts = int(Vg.shape[0])
    n_exact_merged = n_orig_verts - int(uniq_key.shape[0])
    Vg = uniq_key.view(np.float32).reshape(-1, 3).astype(np.float64)   # deduped positions
    Tg = np.ascontiguousarray(vmap_inv[Tg].astype(Tg.dtype))          # remap tri verts to unique idx

    e1 = Vg[Tg[:, 1]] - Vg[Tg[:, 0]]
    e2 = Vg[Tg[:, 2]] - Vg[Tg[:, 0]]
    A0 = 0.5 * np.linalg.norm(np.cross(e1, e2), axis=1)        # import areas, walk space (deduped)
    return Vg.astype(np.float64), Tg, A0, S, e_med, n_orig_verts, n_exact_merged


def area_grads(V, T):
    """Per-triangle grads g_{t,j} = grad wrt vertex j of the SIGNED area.

    For oriented double-area D = (e1 x e2).n0 with e1=v_b-v_a, e2=v_c-v_a and a
    FIXED reference normal n0 (the import-pose normal), the gradient is
      g_a = 0.5 * cross(n0, c - b),  g_b = 0.5 * cross(n0, a - c),  g_c = 0.5 * cross(n0, b - a).
    The reference normal is FIXED (not the live current normal): the area energy must
    be a single-valued function of vertex positions, so the signed area A_s = D.n0 is
    used consistently in BOTH the force (g = dA_s/dv) and the state (s = A_s/A0 - 1).
    Using the live normal in g but the magnitude in s (the old bug) made the force
    ANTI-restoring through inversion -> blow up. Verified vs central FD on signed area."""
    # Vectorized gradient computation: ONE pass over ALL nT tris, zero copies.
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    nrm = np.cross(b - a, c - a)
    n0 = nrm / np.linalg.norm(nrm, axis=1, keepdims=True)        # fixed reference normal
    G = np.stack([
        0.5 * np.cross(n0, c - b),
        0.5 * np.cross(n0, a - c),
        0.5 * np.cross(n0, b - a)], axis=1)                     # (nT3, 3, 3)

    # Spot-check FD on random sample against SIGNED area w.r.t. the SAME n0.
    import random as _rand
    rng = _rand.Random(42)
    n_sample = min(50, len(T))
    sampled = rng.sample(range(len(T)), n_sample)
    eps = 1e-6
    baseA_single = 0.5 * (np.cross(b - a, c - a) * n0).sum(axis=1)   # signed area (nT3,)
    worst = 0.0
    for t_idx in sampled:
        tri = T[t_idx]
        va, vb, vc = V[tri[0]], V[tri[1]], V[tri[2]]
        A0_t = float(baseA_single[t_idx])
        for j in range(3):
            vj = V[tri[j]].copy()
            for comp in range(3):
                vp = vj.copy(); vp[comp] += eps
                if j == 0:
                    pa, pb, pc = vp, vb, vc
                elif j == 1:
                    pa, pb, pc = va, vp, vc
                else:
                    pa, pb, pc = va, vb, vp
                A_pert = float(0.5 * np.dot(np.cross(pb - pa, pc - pa), n0[t_idx]))
                fd_val = (A_pert - A0_t) / eps
                an_val = float(G[t_idx, j, comp])
                worst = max(worst, abs(fd_val - an_val))
    return G, n0, worst


def ca_state(P, Tg, A0, G, k):
    """Area-mode state: per-vertex forces, total spring PE, areas."""
    a = P[Tg[:, 0]]; b = P[Tg[:, 1]]; c = P[Tg[:, 2]]
    e1 = b - a; e2 = c - a
    A = 0.5 * np.linalg.norm(np.cross(e1, e2), axis=1)
    s = A / A0 - 1.0
    U = float(0.5 * (k * A0 * s * s).sum())                   # dU/dv_j == k*s*G_j
    f = np.zeros_like(P)
    np.add.at(f, Tg[:, 0], -k[:, None] * s[:, None] * G[:, 0])
    np.add.at(f, Tg[:, 1], -k[:, None] * s[:, None] * G[:, 1])
    np.add.at(f, Tg[:, 2], -k[:, None] * s[:, None] * G[:, 2])
    return f, U, A


@njit(cache=True)
def _k1_state(P, Tg, A0, k, N0):
    """Per-triangle SIGNED strain s and spring PE u -- prange parallel over tris.

    A_s = 0.5*(e1 x e2).N0 is the SIGNED area against the FIXED reference normal N0
    (import pose), consistent with the force gradient G = dA_s/dv. At inversion A_s
    goes negative and the force stays restoring (no anti-restoring blow up)."""
    nT3 = Tg.shape[0]
    s = np.empty(nT3); u = np.empty(nT3)
    for t in prange(nT3):
        p0 = P[Tg[t, 0]]; p1 = P[Tg[t, 1]]; p2 = P[Tg[t, 2]]
        e1x = p1[0] - p0[0]; e1y = p1[1] - p0[1]; e1z = p1[2] - p0[2]
        e2x = p2[0] - p0[0]; e2y = p2[1] - p0[1]; e2z = p2[2] - p0[2]
        cx = e1y * e2z - e1z * e2y; cy = e1z * e2x - e1x * e2z
        cz = e1x * e2y - e1y * e2x
        As = 0.5 * (cx * N0[t, 0] + cy * N0[t, 1] + cz * N0[t, 2])
        st = As / A0[t] - 1.0
        s[t] = st; u[t] = 0.5 * k[t] * A0[t] * st * st
    return s, u


@njit(cache=True)
def _k2_forces(sarr, G, k, start, entries):
    """Per-vertex area force: sum over incident (tri, slot) -- prange parallel."""
    nV = len(start) - 1
    f = np.zeros((nV, 3))
    for i in prange(nV):
        fx = 0.0; fy = 0.0; fz = 0.0
        for e in range(start[i], start[i + 1]):
            r = entries[e]; t = r // 3; sl = r % 3
            w = -k[t] * sarr[t]
            fx += w * G[t, sl, 0]; fy += w * G[t, sl, 1]; fz += w * G[t, sl, 2]
        f[i, 0] = fx; f[i, 1] = fy; f[i, 2] = fz
    return f


# ----------------------------------------------------------------------------
# BENDING ENERGY (R7c): discrete dihedral-angle springs between adjacent
# triangles. Resists out-of-plane folding -- the missing stiffness that makes
# the area-only membrane collapse under self-DRAW. DERIVED, no free number:
# the rest dihedral theta0 is the import-pose angle (geometry), and K_bend is
# tied to the one physical constant K_BOND. The gradient d(theta)/dv is the
# standard analytic dihedral gradient; it is verified by a finite-difference
# self-check in RUN A (same methodology as the area grad check).
# ----------------------------------------------------------------------------
def build_hinges(Tc):
    """Internal edges shared by exactly two kept triangles -> bending hinges.

    Returns hi0,hi1 (shared edge), hi2 (3rd vertex of tri A), hi3 (3rd vertex of
    tri B), all global vertex indices. Orientation is kept consistent so the
    SAME dihedral convention is used for rest and dynamic angles.
    """
    edges = np.vstack([np.sort(np.stack([Tc[:, 0], Tc[:, 1]], axis=1), axis=1),
                       np.sort(np.stack([Tc[:, 1], Tc[:, 2]], axis=1), axis=1),
                       np.sort(np.stack([Tc[:, 2], Tc[:, 0]], axis=1), axis=1)])
    tri_of_edge = np.tile(np.arange(Tc.shape[0]), 3)
    slot_of_edge = np.tile(np.array([0, 1, 2]), Tc.shape[0])
    uniq, inv, cnt = np.unique(edges, axis=0, return_inverse=True, return_counts=True)
    internal = np.flatnonzero(cnt == 2)
    h0, h1, h2, h3 = [], [], [], []
    for ei in internal:
        rows = np.flatnonzero(inv == ei)              # the two (tri, slot) sharing this edge
        tA, sA = tri_of_edge[rows[0]], slot_of_edge[rows[0]]
        tB, sB = tri_of_edge[rows[1]], slot_of_edge[rows[1]]
        A, B = Tc[tA], Tc[tB]
        shared = np.intersect1d(A, B)                 # the two shared edge endpoints (global ids)
        sset = set(shared.tolist())
        p1, p2 = int(shared[0]), int(shared[1])
        p3 = int(list(set(A.tolist()) - sset)[0])    # opposite vertex in tri A (global id)
        p4 = int(list(set(B.tolist()) - sset)[0])    # opposite vertex in tri B (global id)
        h0.append(p1); h1.append(p2); h2.append(p3); h3.append(p4)
    return (np.array(h0, dtype=np.int64), np.array(h1, dtype=np.int64),
            np.array(h2, dtype=np.int64), np.array(h3, dtype=np.int64))


def dihedral_theta(a, b, c, d):
    """Signed dihedral angle of the hinge (a,b edge; c,d opposite). Pure-python (rest + FD check)."""
    e = b - a
    na = np.cross(c - a, e)
    nb = np.cross(d - a, e)
    L = np.linalg.norm(e)
    ea = e / L
    C = float(na.dot(nb))
    cr = np.cross(na, nb)
    S = float(cr.dot(ea))
    return math.atan2(S, C)


def compute_theta0(hi0, hi1, hi2, hi3, Vg):
    th = np.empty(len(hi0))
    for h in range(len(hi0)):
        th[h] = dihedral_theta(Vg[hi0[h]], Vg[hi1[h]], Vg[hi2[h]], Vg[hi3[h]])
    return th


@njit(cache=True, parallel=True)
def _bend_forces(hi0, hi1, hi2, hi3, P, theta0, Kb, theta_band=1e9):
    """Per-hinge dihedral bending force F = -dU/dv, U = 0.5*Kb*(theta-theta0)^2. prange over hinges.
    theta_band (rad): derived band-clamp on the dihedral deviation (inherited from THETA_CLAMP's
    1%-linearization band, 0.244 rad). Default 1e9 = no clamp (used by the FD self-check so the
    RAW analytic gradient is verified). The RUN B loop passes 0.244 to clamp + flag exceedance."""
    nH = hi0.shape[0]
    nV = P.shape[0]
    f = np.zeros((nV, 3))
    U = 0.0
    mx = 0.0
    for h in prange(nH):
        a = P[hi0[h]]; b = P[hi1[h]]; c = P[hi2[h]]; d = P[hi3[h]]
        ex = b[0]-a[0]; ey = b[1]-a[1]; ez = b[2]-a[2]
        # n_a = (c-a) x e
        cax = c[0]-a[0]; cay = c[1]-a[1]; caz = c[2]-a[2]
        na0 = cay*ez - caz*ey; na1 = caz*ex - cax*ez; na2 = cax*ey - cay*ex
        # n_b = (d-a) x e
        dax = d[0]-a[0]; day = d[1]-a[1]; daz = d[2]-a[2]
        nb0 = day*ez - daz*ey; nb1 = daz*ex - dax*ez; nb2 = dax*ey - day*ex
        Le = math.sqrt(ex*ex + ey*ey + ez*ez)
        if Le < 1e-12:
            continue
        eax = ex/Le; eay = ey/Le; eaz = ez/Le
        C = na0*nb0 + na1*nb1 + na2*nb2
        cr0 = na1*nb2 - na2*nb1; cr1 = na2*nb0 - na0*nb2; cr2 = na0*nb1 - na1*nb0
        S = cr0*eax + cr1*eay + cr2*eaz
        theta = math.atan2(S, C)
        dth = theta - theta0[h]
        if abs(dth) > mx:
            mx = abs(dth)
        # band-clamp the dihedral deviation (THETA_CLAMP semantics): the bending force uses the
        # clamped deviation so a single huge fold cannot dominate/blow up; U uses the SAME clamped
        # value so F = -dU/dv stays exact. mx tracks the RAW deviation for the falsifier.
        dthc = dth
        if dthc > theta_band:
            dthc = theta_band
        elif dthc < -theta_band:
            dthc = -theta_band
        U += 0.5 * Kb * dthc * dthc
        n2a = na0*na0 + na1*na1 + na2*na2
        n2b = nb0*nb0 + nb1*nb1 + nb2*nb2
        norm2 = n2a * n2b
        if norm2 < 1e-20:
            continue
        edc = eax*cr0 + eay*cr1 + eaz*cr2            # ea . cr
        # --- grad of C  (gC_X = d(C)/dX,  C = n_a.n_b) ---
        bc0,bc1,bc2 = b[0]-c[0], b[1]-c[1], b[2]-c[2]
        bd0,bd1,bd2 = b[0]-d[0], b[1]-d[1], b[2]-d[2]
        ca0,ca1,ca2 = c[0]-a[0], c[1]-a[1], c[2]-a[2]
        da0,da1,da2 = d[0]-a[0], d[1]-a[1], d[2]-a[2]
        # gC_a = -(b-c) x n_b - (b-d) x n_a   (transpose of skew gives the leading minus)
        gCAx = -bc1*nb2 + bc2*nb1 - bd1*na2 + bd2*na1
        gCAy = -bc2*nb0 + bc0*nb2 - bd2*na0 + bd0*na2
        gCAz = -bc0*nb1 + bc1*nb0 - bd0*na1 + bd1*na0
        # gC_b = -(c-a) x n_b - (d-a) x n_a
        gCBx = -ca1*nb2 + ca2*nb1 - da1*na2 + da2*na1
        gCBy = -ca2*nb0 + ca0*nb2 - da2*na0 + da0*na2
        gCBz = -ca0*nb1 + ca1*nb0 - da0*na1 + da1*na0
        # gC_c = e x n_b
        gCCx = ey*nb2 - ez*nb1
        gCCy = ez*nb0 - ex*nb2
        gCCz = ex*nb1 - ey*nb0
        # gC_d = e x n_a
        gCDx = ey*na2 - ez*na1
        gCDy = ez*na0 - ex*na2
        gCDz = ex*na1 - ey*na0
        # --- grad of S  (gS_X = d(S)/dX,  S = (n_a x n_b).ea) ---
        # tmp = n_b x ea ; t2 = n_a x ea
        tbx = nb1*eaz - nb2*eay; tby = nb2*eax - nb0*eaz; tbz = nb0*eay - nb1*eax
        t2x = na1*eaz - na2*eay; t2y = na2*eax - na0*eaz; t2z = na0*eay - na1*eax
        # gS_a = -[(b-c) x tmp - (b-d) x t2 + (ea*edc - cr)/L]   (vertices a,b get the leading minus)
        gSAx = -bc1*tbz + bc2*tby + (bd1*t2z - bd2*t2y) - (eax*edc - cr0)/Le
        gSAy = -bc2*tbx + bc0*tbz + (bd2*t2x - bd0*t2z) - (eay*edc - cr1)/Le
        gSAz = -bc0*tby + bc1*tbx + (bd0*t2y - bd1*t2x) - (eaz*edc - cr2)/Le
        # gS_b = -[(c-a) x tmp - (d-a) x t2 + (cr - ea*edc)/L]
        gSBx = -ca1*tbz + ca2*tby + (da1*t2z - da2*t2y) - (cr0 - eax*edc)/Le
        gSBy = -ca2*tbx + ca0*tbz + (da2*t2x - da0*t2z) - (cr1 - eay*edc)/Le
        gSBz = -ca0*tby + ca1*tbx + (da0*t2y - da1*t2x) - (cr2 - eaz*edc)/Le
        # gS_c = e x tmp
        gSCx = ey*tbz - ez*tby
        gSCy = ez*tbx - ex*tbz
        gSCz = ex*tby - ey*tbx
        # gS_d = - e x t2
        gSDx = ez*t2y - ey*t2z
        gSDy = ex*t2z - ez*t2x
        gSDz = ey*t2x - ex*t2y
        # dtheta = (C*gS - S*gC)/norm2 ; F = -Kb*dthc*dtheta
        coef = -Kb * dthc
        # vertex a
        dta = (C*gSAx - S*gCAx)/norm2
        dtb = (C*gSBx - S*gCBx)/norm2
        dtc = (C*gSCx - S*gCCx)/norm2
        dtd = (C*gSDx - S*gCDx)/norm2
        fa0 = coef * dta; fa1 = coef * ((C*gSAy - S*gCAy)/norm2); fa2 = coef * ((C*gSAz - S*gCAz)/norm2)
        fb0 = coef * dtb; fb1 = coef * ((C*gSBy - S*gCBy)/norm2); fb2 = coef * ((C*gSBz - S*gCBz)/norm2)
        fc0 = coef * dtc; fc1 = coef * ((C*gSCy - S*gCCy)/norm2); fc2 = coef * ((C*gSCz - S*gCCz)/norm2)
        fd0 = coef * dtd; fd1 = coef * ((C*gSDy - S*gCDy)/norm2); fd2 = coef * ((C*gSDz - S*gCDz)/norm2)
        f[hi0[h], 0] += fa0; f[hi0[h], 1] += fa1; f[hi0[h], 2] += fa2
        f[hi1[h], 0] += fb0; f[hi1[h], 1] += fb1; f[hi1[h], 2] += fb2
        f[hi2[h], 0] += fc0; f[hi2[h], 1] += fc1; f[hi2[h], 2] += fc2
        f[hi3[h], 0] += fd0; f[hi3[h], 1] += fd1; f[hi3[h], 2] += fd2
    return f, U, mx


# ── CLOSED-MESH rest volume + OUTWARD PRESSURE (Rule-0 SURFACE axis: rest-exterior) ──
# Rest enclosed volume V0 from geometry (divergence theorem); the rest-exterior constraint is
# a surface/areal field on the triangle carrier, NOT a third point-to-point force. k_vol is
# DERIVED (tied to the one physical constant K_BOND), no free number -- like k_area / k_bend.

@njit(parallel=True, fastmath=True)
def enclosed_volume(V, Tg):
    nT = Tg.shape[0]
    vol = 0.0
    for t in prange(nT):
        a = V[Tg[t, 0]]; b = V[Tg[t, 1]]; c = V[Tg[t, 2]]
        vol += a[0] * (b[1] * c[2] - b[2] * c[1]) - \
               a[1] * (b[0] * c[2] - b[2] * c[0]) + \
               a[2] * (b[0] * c[1] - b[1] * c[0])
    return vol / 6.0


@njit(parallel=True, fastmath=True)
def _pressure_forces(V, Tg, V0, k_vol, band, G):
    # OUTWARD volume-restoring pressure as a rest-state constraint on the closed triangle
    # carrier.  U_v = 1/2 k_vol (V/V0 - 1)^2  (V0 = rest enclosed volume) so V0 is a TRUE
    # rest state (force = 0 at V = V0).  F_i = -dU_v/dv_i = -k_vol (V/V0-1)/V0 * gradV_i,
    # gradV_i = (1/6) sum_incident (b x c)  (volume gradient / fan area vector).
    nT = Tg.shape[0]
    nV = V.shape[0]
    G[:] = 0.0
    vol = 0.0
    for t in range(nT):                       # sequential: tris share vertices -> race-free
        a = V[Tg[t, 0]]; b = V[Tg[t, 1]]; c = V[Tg[t, 2]]
        bxc = np.array([b[1] * c[2] - b[2] * c[1],
                        b[2] * c[0] - b[0] * c[2],
                        b[0] * c[1] - b[1] * c[0]])
        cxa = np.array([c[1] * a[2] - c[2] * a[1],
                        c[2] * a[0] - c[0] * a[2],
                        c[0] * a[1] - c[1] * a[0]])
        axb = np.array([a[1] * b[2] - a[2] * b[1],
                        a[2] * b[0] - a[0] * b[2],
                        a[0] * b[1] - a[1] * b[0]])
        G[Tg[t, 0], 0] += bxc[0] / 6.0
        G[Tg[t, 0], 1] += bxc[1] / 6.0
        G[Tg[t, 0], 2] += bxc[2] / 6.0
        G[Tg[t, 1], 0] += cxa[0] / 6.0
        G[Tg[t, 1], 1] += cxa[1] / 6.0
        G[Tg[t, 1], 2] += cxa[2] / 6.0
        G[Tg[t, 2], 0] += axb[0] / 6.0
        G[Tg[t, 2], 1] += axb[1] / 6.0
        G[Tg[t, 2], 2] += axb[2] / 6.0
        vol += a[0] * (b[1] * c[2] - b[2] * c[1]) - \
               a[1] * (b[0] * c[2] - b[2] * c[0]) + \
               a[2] * (b[0] * c[1] - b[1] * c[0])
    vol /= 6.0
    dev = vol / V0 - 1.0
    dev_c = dev if abs(dev) < band else (band if dev > 0.0 else -band)
    F = np.zeros((nV, 3))
    for i in prange(nV):                      # parallel: reads G only, independent per vertex
        F[i, 0] = -k_vol * dev_c / V0 * G[i, 0]
        F[i, 1] = -k_vol * dev_c / V0 * G[i, 1]
        F[i, 2] = -k_vol * dev_c / V0 * G[i, 2]
    U = 0.5 * k_vol * dev_c * dev_c
    return F, U, abs(dev)


def build_sphere(n_lat=32, n_lon=64, R=None):
    # CLOSED UV sphere. Radius chosen so equatorial edge length ~ R_BOND => bonds at rest
    # (no free number; R is derived from R_BOND and n_lon). Outward winding enforced by the
    # signed-volume sign check (V0 must be positive for the rest-exterior constraint).
    if R is None:
        R = C.R_BOND * n_lon / (2.0 * math.pi)
    verts = [np.array([0.0, 0.0, R], dtype=np.float64)]   # north pole
    for i in range(1, n_lat):
        theta = math.pi * i / n_lat
        st = math.sin(theta); ct = math.cos(theta)
        for j in range(n_lon):
            phi = 2.0 * math.pi * j / n_lon
            verts.append(np.array([R * st * math.cos(phi),
                                   R * st * math.sin(phi),
                                   R * ct], dtype=np.float64))
    verts.append(np.array([0.0, 0.0, -R], dtype=np.float64))  # south pole
    Vg = np.ascontiguousarray(np.stack(verts), dtype=np.float64)
    tris = []
    for j in range(n_lon):                              # north cap
        tris.append([0, 1 + j, 1 + (j + 1) % n_lon])
    for i in range(0, n_lat - 2):                      # middle bands
        r0 = 1 + i * n_lon; r1 = 1 + (i + 1) * n_lon
        for j in range(n_lon):
            a = r0 + j; b = r0 + (j + 1) % n_lon
            c = r1 + j; d = r1 + (j + 1) % n_lon
            tris.append([a, b, d]); tris.append([a, d, c])
    s = len(verts) - 1; rlast = 1 + (n_lat - 2) * n_lon  # south cap
    for j in range(n_lon):
        tris.append([s, rlast + (j + 1) % n_lon, rlast + j])
    Tg = np.ascontiguousarray(np.array(tris, dtype=np.int64))
    if enclosed_volume(Vg, Tg) < 0.0:
        Tg = np.ascontiguousarray(Tg[:, ::-1], dtype=np.int64)
    return Vg, Tg


def main() -> int:
    # ── mesh selector (Rule-0 SURFACE axis): closed mesh FIRST (sphere) where rest volume
    # V0 is unambiguous; the open bear (rest-exterior not yet defined) follows. No free number:
    # the sphere radius is DERIVED from R_BOND so its bonds start at rest.
    MESH = os.environ.get("MESH", "bear").lower()
    if MESH == "sphere":
        Vg, Tg = build_sphere()                          # R -> edge ~ R_BOND (bonds at rest)
        e1 = Vg[Tg[:, 1]] - Vg[Tg[:, 0]]
        e2 = Vg[Tg[:, 2]] - Vg[Tg[:, 0]]
        e3 = Vg[Tg[:, 2]] - Vg[Tg[:, 1]]
        A0 = 0.5 * np.linalg.norm(np.cross(e1, e2), axis=1)
        _em = np.stack([np.linalg.norm(e1, axis=1),
                        np.linalg.norm(e2, axis=1),
                        np.linalg.norm(e3, axis=1)], axis=1)
        e_med = float(np.median(_em))
        S = C.R_BOND / e_med
        n_orig_verts = len(Vg); n_exact_merged = 0
        is_closed = True; scale0 = 0.98                 # start compressed -> outward pressure exercised
    else:
        Vg, Tg, A0, S, e_med, n_orig_verts, n_exact_merged = build_lattice()
        is_closed = False; scale0 = 1.0
    nV, nT3 = len(Vg), len(Tg)
    # k (CA area stiffness) is now DERIVED per-triangle from the bond below (R7b),
    # not a free number.

    # Degenerate gate: filter zero-area AND near-zero-area tris (float64 noise floor).
    degen = A0 < NEAR_ZERO_A0
    keep = ~degen
    Tc = np.ascontiguousarray(Tg[keep])                     # CA arrays: kept tris only
    Ac = np.ascontiguousarray(A0[keep], dtype=np.float64)
    # closed mesh -> rest enclosed volume V0 (Rule-0 rest-exterior; derived, no free number)
    V0 = float(enclosed_volume(Vg, Tc)) if is_closed else None

    # ── R7b / OPTION B: the CA area mode IS the area channel of the SAME edge-bond
    # energy (ONE energy, two consistent gradients -- RUN A proves d2U_s/dlam^2 = 3*K_BOND,
    # 0% error, so it does NOT fight its own edge). It is applied as a REAL push-back
    # force (F = -dU_s/dv) in the RUN B loop: the area spring resists area CHANGE, the
    # edge bond resists edge CHANGE; both are restoring and consistent (no double-count,
    # no conflict). Rest area is DERIVED from bond geometry (per-tri import area), never picked.
    # per-triangle median edge length (walk space)
    e1 = Vg[Tc[:, 1]] - Vg[Tc[:, 0]]
    e2 = Vg[Tc[:, 2]] - Vg[Tc[:, 0]]
    e3 = Vg[Tc[:, 2]] - Vg[Tc[:, 1]]
    _em = np.median(np.stack([
        np.linalg.norm(e1, axis=1), np.linalg.norm(e2, axis=1), np.linalg.norm(e3, axis=1)
    ], axis=1), axis=1)
    # OPTION B derivation (real area rigidity, no free number): stiffness is DERIVED so the
    # isotropic area response of a triangle equals its 3-edge bond-network response. RUN A
    # (below) measures d2U_s/dlam^2 and requires it == 3*K_BOND; solving gives k_t = 0.75*K_BOND/A0_t
    # (per-tri). This is UNIFORM (no 1/Ac^2 blow-up) and dt-stable. The earlier (e_med/Ac)^2 form
    # is rejected: tiny Ac -> huge k -> dt-unstable. A0_eq is the equilateral@R_BOND area, used
    # only as the RUN A derivation reference (NOT as the applied rest area -- the applied rest
    # area is each tri's own Ac, see below).
    A0_eq = (C.R_BOND ** 2) * math.sqrt(3.0) / 4.0          # equilateral@R_BOND area (RUN A derivation ref)
    # CA rest area = each triangle's OWN reference (import) area Ac: the solid's undeformed
    # configuration. DERIVED from bond geometry (edge lengths -> area, no free number, no 54%
    # mismatch) so every triangle starts AT rest (s=0) -> no initial snap. The area spring then
    # resists AREA CHANGE during dynamics -> genuine solid rigidity, without fighting the bond
    # rest. Per-tri stiffness k_t = 0.75*K_BOND/A0_t (RUN A-validated) gives area curvature
    # d2U/dA2 = k_t/A0_t = 0.75*K_BOND/A0_t^2, UNIFORM and dt-stable. RUN A below validates this k.
    A0_bond = Ac.copy()
    k = 0.75 * C.K_BOND / Ac                       # derived: isotropic area response of a tri
                                                 # equals its 3-edge bond network (d2U/dlam^2 = 3*K_BOND);
                                                 # gives U_s = 0.5*k*A0*s^2 with k in energy/length^2 (no free number)
    k_area = float(k[0])
    print(f"DIAG scaled-edge_med={float(np.median(_em)):.6g}  Ac_med={float(np.median(Ac)):.6g}  "
           f"A0_eq(ref)={A0_eq:.6g}  s0_med={float(np.median(Ac / A0_bond - 1.0)):.6g}")
    print(f"lattice: {nT3:,} tris / {nV:,} verts (19 per-part shells; shared-edge law within part)")
    print(f"exact-vertex merge: {n_orig_verts:,} -> {nV:,} unique ({n_exact_merged:,} bit-identical merged, "
          f"no free param); total faders ledger unchanged")
    print(f"degenerate (A0<{NEAR_ZERO_A0:.0e}): {int(degen.sum()):,} dropped from area mode; "
          f"CA runs on {keep.sum():,}; total faders ledger unchanged")
    print(f"e_med={e_med:.6g}  R_BOND/e_med={S:.6g}  A0_eq(derived)={float(A0_bond[0]):.6g}  "
           f"k_area(derived median)={float(np.median(k)):.6g}  R7b: CA rest area = equilateral@R_BOND (no free number)")

    G, N0, fd_worst = area_grads(Vg, Tc)
    print(f"grad self-check |FD - analytic| max = {fd_worst:.3e}")
    assert fd_worst < 1e-4, "area gradient algebra failed its own FD check -- build stops"

    # ── R7c: bending hinges (dihedral-angle springs) ──
    hi0, hi1, hi2, hi3 = build_hinges(Tc)
    theta0 = compute_theta0(hi0, hi1, hi2, hi3, Vg)
    K_bend = C.K_BOND                                  # DERIVED: tied to the one physical constant
    print(f"bending hinges: {len(hi0):,}  K_bend={K_bend:.4g} (tied to K_BOND, no free number)")
    K_vol = C.K_BOND                                  # DERIVED: volume-restoring pressure tied to K_BOND
    S_BAND_VOL = 0.244                                # volume-deviation band, inherited THETA_CLAMP precedent
    band_exceeded_vol = False
    G_press = np.zeros((nV, 3), dtype=np.float64) if is_closed else None

    # ── R7b integration: substep BELOW the measured dt cliff (ca_stab.txt: finite at
    # 5e-7, diverges at 5e-6). This is the PRIMARY stability fix (Hole 1). The area/bending
    # forces are verified-conservative and cannot inject energy; the cliff is the self-DRAW
    # singularity (1/(r^2+EPS^2)) near r->EPS. iso7.txt confirms [draw+wall+bond] is finite
    # once dt is below the cliff. dt derived from where finiteness flips (THETA_CLAMP precedent),
    # not picked.
    dt_int = 5.0e-7          # cliff-safe substep (ca_stab.txt)
    S_BAND = 0.244           # dihedral band, inherited from THETA_CLAMP (1%-linearization band)
    band_exceeded = False    # fired falsifier if any tri's dihedral deviation exceeds S_BAND

    # CSR incidence over the KEPT set: vertex i -> rows r of the flattened (tri, slot) table.
    Tg_flat = np.ascontiguousarray(Tc.ravel())
    cnt = np.bincount(Tg_flat, minlength=nV)
    start = np.empty(nV + 1, dtype=np.int64); start[0] = 0
    np.cumsum(cnt, out=start[1:])
    entries = np.empty(3 * len(Tc), dtype=np.int64)
    cursor = start[:-1].copy()
    for r in range(Tg_flat.shape[0]):
        v = int(Tg_flat[r]); entries[int(cursor[v])] = r; cursor[v] += 1

    # energy consistency on the first kept triangle: F = -dU/dv per component (central FD)
    f0, U0, _ = ca_state(Vg, Tc, A0_bond, G, k)
    t0n = Tc[0]
    jx = int(t0n[2])                                        # vertex c of that triangle
    Vp = Vg.copy(); Vp[jx] += 1e-5
    fp, Up, _ = ca_state(Vp, Tc, A0_bond, G, k)             # perturbed call MUST use A0_bond too
    dF = (fp - f0)[jx] / 1e-5
    dU = (Up - U0) / 1e-5
    resid = max(abs(dF[dF != 0]).max(), abs(dU)) if np.any(dF != 0) else abs(dU)
    print(f"energy-consistency tri 0: F=-dU/dv residual scale = {resid:.3e}")

    # ── bending gradient FD self-check (R7c): single-hinge energy vs analytic force ──
    if len(hi0) > 0:
        rng = np.random.default_rng(0)
        Ptest = Vg.copy()
        for vi in (int(hi0[0]), int(hi1[0]), int(hi2[0]), int(hi3[0])):
            Ptest[vi] += rng.standard_normal(3) * 0.01      # lift off rest so dth != 0 (force nonzero)
        fchk, Uchk, _ = _bend_forces(np.array([hi0[0]]), np.array([hi1[0]]),
                                     np.array([hi2[0]]), np.array([hi3[0]]),
                                     Ptest, np.array([theta0[0]]), K_bend)
        verts = [int(hi0[0]), int(hi1[0]), int(hi2[0]), int(hi3[0])]
        maxfd = 0.0; hh = 1e-6
        for vidx in verts:
            for comp in range(3):
                Pp = Ptest.copy(); Pp[vidx, comp] += hh
                Pm = Ptest.copy(); Pm[vidx, comp] -= hh
                _, Up, _ = _bend_forces(np.array([hi0[0]]), np.array([hi1[0]]),
                                        np.array([hi2[0]]), np.array([hi3[0]]),
                                        Pp, np.array([theta0[0]]), K_bend)
                _, Um, _ = _bend_forces(np.array([hi0[0]]), np.array([hi1[0]]),
                                        np.array([hi2[0]]), np.array([hi3[0]]),
                                        Pm, np.array([theta0[0]]), K_bend)
                dU = (Up - Um) / (2 * hh)                   # F = -dU/dv  =>  dU/dv = -F
                maxfd = max(maxfd, abs(dU + fchk[vidx, comp]))
        print(f"bending grad self-check |FD + analytic| max = {maxfd:.3e}")
        assert maxfd < 1e-3, "bending gradient algebra failed its own FD check -- build stops"

    # ── pressure (rest-exterior) gradient FD self-check (Rule-0 SURFACE axis): single-vertex
    # energy vs analytic force. U_v = 1/2 k_vol (V/V0-1)^2 ; F_i = -dU_v/dv_i. Verifies the
    # volume-gradient algebra before the closed-mesh run (band disabled here so FD sees the raw slope).
    if V0 is not None:
        rng = np.random.default_rng(1)
        Ptest = Vg.copy()
        pv = rng.choice(nV, size=min(8, nV), replace=False)
        Ptest[pv] += rng.standard_normal((len(pv), 3)) * 0.01
        Fchk, Uchk, devraw = _pressure_forces(Ptest, Tc, V0, K_vol, 1e9, np.zeros((nV, 3)))
        maxfd = 0.0; hh = 1e-6
        for vidx in pv:
            for comp in range(3):
                Pp = Ptest.copy(); Pp[vidx, comp] += hh
                Pm = Ptest.copy(); Pm[vidx, comp] -= hh
                _, Up, _ = _pressure_forces(Pp, Tc, V0, K_vol, 1e9, np.zeros((nV, 3)))
                _, Um, _ = _pressure_forces(Pm, Tc, V0, K_vol, 1e9, np.zeros((nV, 3)))
                dU = (Up - Um) / (2 * hh)                    # F = -dU/dv
                maxfd = max(maxfd, abs(dU + Fchk[vidx, comp]))
        print(f"pressure grad self-check |FD + analytic| max = {maxfd:.3e}")
        assert maxfd < 1e-3, "pressure gradient algebra failed its own FD check -- build stops"

    # ---- RUN A: bond-law match, one named shared edge -- first KEPT triangle whose slot-0
    # (a-b) pair is SHARED. Sharedness must be counted across ALL THREE slots of every kept tri.
    pairs_all = [np.sort(np.stack([Tc[:, j], Tc[:, k]], axis=1), axis=1) for j, k in ((0, 1), (1, 2), (2, 0))]
    allp_ab = np.vstack(pairs_all)
    _, inv_ab = np.unique(allp_ab, axis=0, return_inverse=True)
    cnt_ab = np.bincount(inv_ab, minlength=int(inv_ab.max()) + 1 if len(inv_ab) else 1)
    k3 = Tc.shape[0]
    shared_slot0 = (cnt_ab[inv_ab] == 2)[0 * k3:k3]
    sel = int(np.flatnonzero(shared_slot0)[0]) if shared_slot0.any() else -1
    assert sel >= 0, "no shared a-b edge among kept tris -- named-edge pre-registration cannot run"
    t_named_kept = Tc[sel]
    print(f"RUN A named triangle: kept #{sel} (global {int(np.flatnonzero(keep)[sel])}), slot-0 edge")
    p, q = int(t_named_kept[0]), int(t_named_kept[1])
    d = Vg[q] - Vg[p]; r0 = float(np.linalg.norm(d)); d /= r0
    A_named = float(A0_bond[sel])                            # derived equilateral@R_BOND rest area

    t0 = Tc[sel]
    def force_on_q(stretch):
        # CA contribution of the NAMED triangle only. RUN A isolates one
        # bond/area mode; summing every incident triangle aggregates many modes
        # and is not comparable to a single edge's bond slope (the original gate's
        # second mistake, after the dimensional one).
        P2 = Vg.copy(); P2[q] = Vg[p] + d * stretch
        aa, bb, cc = P2[t0[0]], P2[t0[1]], P2[t0[2]]
        e1 = bb - aa; e2 = cc - aa
        A = 0.5 * np.linalg.norm(np.cross(e1, e2))
        nrm2 = np.cross(e1, e2); nh = nrm2 / np.linalg.norm(nrm2)
        gb = 0.5 * np.cross(nh, aa - cc)                     # area grad wrt vertex b (slot 1)
        s = A / A_named - 1.0
        fq = -k[sel] * s * gb
        return float(np.dot(fq, -d))                         # restoring magnitude toward p

    h = 0.005 * C.R_BOND                                    # 0.5% central difference step
    slope_ca = (force_on_q(C.R_BOND + h) - force_on_q(C.R_BOND - h)) / (2 * h)
    # ---- RUN A: validate the DERIVED area stiffness (R7b principle). No free number:
    # k = 0.75*K_BOND/A0 is derived by matching a triangle's isotropic (equi-biaxial)
    # area response to its THREE edge bonds (each U_edge = 0.5*K_BOND*(r-R)^2/R^2), which
    # gives d2U_s/dlambda^2 |_{lambda=1} = 3*K_BOND -- the bond network's own isotropic
    # stiffness. RUN A proves the algebra is wired right (and the force is genuinely
    # restoring, not a free second spring).
    e = C.R_BOND
    V_syn = np.stack([np.array([0.0, 0.0, 0.0]),
                      np.array([e, 0.0, 0.0]),
                      np.array([0.5 * e, 0.5 * math.sqrt(3.0) * e, 0.0])])
    T_syn = np.array([[0, 1, 2]], dtype=np.int64)
    G_syn, N0_syn, _fd = area_grads(V_syn, T_syn)
    A0_eq_syn = 0.25 * math.sqrt(3.0) * e * e
    k_syn = np.array([0.75 * C.K_BOND / A0_eq_syn])      # DERIVED (no free number)

    def _area_pe(lam):
        c = V_syn.mean(0)
        Vp = c + (V_syn - c) * lam                          # isotropic scale about centroid
        s, _u = _k1_state(Vp, T_syn, np.array([A0_eq_syn]), k_syn, N0_syn)
        return float(0.5 * (k_syn * A0_eq_syn * s * s).sum())

    h = 1e-4
    d2U = (_area_pe(1 + h) - 2.0 * _area_pe(1.0) + _area_pe(1 - h)) / (h * h)
    expected = 3.0 * C.K_BOND                              # bond network isotropic stiffness
    relA = abs(d2U - expected) / expected
    okA = relA <= GATE_REL
    print(f"RUN A synthetic equilateral@R_BOND: d2U_s/dlam^2={d2U:.6g} vs bond-network 3*K_BOND={expected:.6g}")
    print(f"         rel err = {relA * 100:.3f}% (gate {GATE_REL * 100:.0f}%): "
           + ("PASS" if okA else "FALSIFIER FIRES"))
    r0 = e
    sel = -1                                                # synthetic; not a mesh tri

    # ---- RUN B: live liveness + energy accounting under the fold walk
    try:
        from numba import cuda as _cuda
        have_cuda = bool(_cuda.is_available())
    except Exception:
        have_cuda = False
    pos32 = np.ascontiguousarray(Vg * scale0, dtype=np.float32)  # walk-space positions (scale0=1 for bear)
    vel32 = np.zeros((nV, 3), dtype=np.float32)
    out_buf = np.empty((nV, 3), dtype=np.float32)             # preallocated: interface fills it
    dev = {}                                                  # build-once device buffers (flat VRAM)
    f0b, U_b, _ = ca_state(np.ascontiguousarray(pos32), Tc, A0_bond, G, k)
    # warmup walk: capture rest-frame conservative PE (draw + wall + bond) so E0 is the
    # full energy, not just the CA spring PE. Energy gate then verifies dE against radiation.
    _, _, pot0 = compute_forces_mod(pos32, vel32, dev=dev)
    # Consistent initial CA energy: a compressed closed mesh starts with rest-state PE (U_s, U_v),
    # which MUST be in E0 too or the gate mis-measures a one-time offset as drift. Bear starts at
    # rest (U_s=U_v=0) so this reduces to the original E0.
    P64_0 = np.ascontiguousarray(pos32, dtype=np.float64)
    sarr_0, _u = _k1_state(P64_0, Tc, A0_bond, k, N0)
    U_s_init = float(0.5 * (k * A0_bond * sarr_0 ** 2).sum())
    U_v_init = float(_pressure_forces(P64_0, Tc, V0, K_vol, S_BAND_VOL, G_press)[1]) if V0 is not None else 0.0
    E0 = float(U_s_init + U_b + U_v_init + 0.5 * (vel32 ** 2).sum() + pot0)
    rad_total, peak_E, max_strain, finite = 0.0, abs(E0), 0.0, True
    max_bend = 0.0
    U_bend_tot = 0.0
    pot = 0.0
    U_s = 0.0
    U_vol_tot = 0.0
    max_vol_dev = 0.0
    mem_guard_fired = False
    rss_now = _rss_mb()
    ms_tree = ms_walk = ms_ca = 0.0
    # Effective threading layer (operator directive): what we asked for vs what is live.
    try:
        from numba.np.ufunc import get_num_threads as _get_nt
        active_pool = int(_get_nt())          # reads the same NUMBA_NUM_THREADS config we pinned above
    except Exception:
        active_pool = -1                     # honest: could not read; verdict falls to the ms breakdown
    print(f"RUN B backend: cuda={have_cuda}  "
          f"NUMBA_NUM_THREADS_env={os.environ.get('NUMBA_NUM_THREADS')}  "
          f"numba_active_pool={active_pool}  os_cpu_count={os.cpu_count()}  "
          f"rss_start={rss_now / 1000:.2f} GB", flush=True)

    # Line-buffered per-tick progress (operator directive): survives a Task-Manager kill by flushing
    # every 25 ticks, so the next agent gets tick-level localization from disk even if killed again.
    PROG.parent.mkdir(parents=True, exist_ok=True)
    prog = open(PROG, "w", encoding="utf-8")

    def _prog_line(tick_n, E_v, rad_v, strain_v, tag):
        line = (f"tick={int(tick_n):4d}  E={E_v:.6g}  rad_total={rad_v:.6g}  "
                f"max_strain={strain_v:.3e}  rss_gb={_rss_mb() / 1000:.3f}  "
                f"ms_tree_cum={ms_tree * 1000:.1f}  ms_walk_cum={ms_walk * 1000:.1f}  "
                f"ms_ca_cum={ms_ca * 1000:.1f}  dev_mb={_dev_mb():.1f}  {tag}")
        prog.write(line + "\n"); prog.flush()

    _prog_line(0, E0, 0.0, 0.0, "START")
    for tick in range(TICKS):
        _t1 = time.perf_counter()
        tree = build_octree(pos32, leaf_size=16)            # live frame: tree moves with points
        ms_tree += time.perf_counter() - _t1
        _t1 = time.perf_counter()
        try:
            acc, power, pot = compute_forces_mod(pos32, vel32, tree=tree, out=out_buf, dev=dev)
        except RuntimeError:
            # Barnes-Hut kernel stack overflow / non-finite (e.g. during a
            # divergent frame). Honest termination: record and stop.
            finite = False
            _prog_line(tick + 1, float("nan"), rad_total, max_strain, "WALK_NAN")
            break
        ms_walk += time.perf_counter() - _t1                # GPU: one thread per point (or prange CPU)
        rad_total += float(power) * dt_int                  # radiated ENERGY this tick = power * dt (honest dissipation)
        _t1 = time.perf_counter()
        # R7b (root fix, applied): CA rest area = each triangle's OWN reference area (solid's
        # undeformed config), derived from geometry (no free number). The area force is the
        # area channel of the ONE edge-bond energy (fca = -dU_s/dv), a genuinely restoring
        # solid-element rigidity. k is DERIVED (0.75*K_BOND/A0) so the area mode is dt-stable.
        P64 = np.ascontiguousarray(pos32, dtype=np.float64)
        sarr, _u = _k1_state(P64, Tc, A0_bond, k, N0)        # CA state: s = A/A0 - 1 (signed, fixed N0)
        fca = _k2_forces(sarr, G, k, start, entries)         # area force F = -dU_s/dv (Option B: real push-back)
        fbend, U_b, max_dth = _bend_forces(hi0, hi1, hi2, hi3, P64, theta0, K_bend, S_BAND)  # bending F=-dU_b/dv, band-clamped
        ms_ca += time.perf_counter() - _t1                  # multi-core prange over tris
        max_strain = max(max_strain, float(np.abs(sarr).max()))
        max_bend = max(max_bend, float(max_dth))
        if max_dth > S_BAND:
            band_exceeded = True                            # dihedral exceeded derived band -> fired falsifier (bending successor)
        a_tot = np.asarray(acc, dtype=np.float64) + fca + fbend   # draw + wall + bond + area + bending
        # Rule-0 SURFACE axis: rest-exterior pressure (closed mesh only). V0 = rest enclosed volume;
        # F = -dU_v/dv restores the outside when deviated. Bear: V0=None -> skipped (open, no V0 yet).
        U_vol_tot = 0.0
        if V0 is not None:
            Fvol, U_v, dev_raw = _pressure_forces(P64, Tc, V0, K_vol, S_BAND_VOL, G_press)
            a_tot = a_tot + Fvol
            U_vol_tot = float(U_v)
            max_vol_dev = max(max_vol_dev, float(dev_raw))
            if dev_raw > S_BAND_VOL:
                band_exceeded_vol = True                    # volume-deviation band exceeded -> falsifier
        if not bool(np.all(np.isfinite(a_tot))):
            finite = False
            _prog_line(tick + 1, float("nan"), rad_total, max_strain, "WALK_NAN")
            break
        vel32 += (a_tot * dt_int).astype(np.float32)        # symplectic Euler: kick then drift (dt below cliff)
        pos32 = np.ascontiguousarray(pos32 + vel32.astype(np.float64) * dt_int, dtype=np.float32)
        U_s = float(0.5 * (k * A0_bond * sarr ** 2).sum())  # applied area PE (real, part of E)
        U_bend_tot = U_b                                    # bending PE (real, INSTANTANEOUS part of E; was wrongly accumulated)
        E = float(0.5 * (vel32 ** 2).sum() + pot + U_s + U_bend_tot + U_vol_tot)  # REAL integrated energy
        peak_E = max(peak_E, abs(E))
        if EVERY_TICK or tick % 25 == 0 or tick == TICKS - 1:  # per-tick if CA_EVERY_TICK=1 (long-horizon leak diagnostic)
            _prog_line(tick + 1, E, rad_total, max_strain, "")
        if tick % 100 == 99 or tick == TICKS - 1:
            rss_now = _rss_mb()
            print(f"  tick {tick + 1:4d}/{TICKS}  E={E:.4g}  rad={rad_total:.4g}  "
                  f"strain_max={max_strain:.3e}  rss={rss_now / 1000:.2f} GB", flush=True)
            if rss_now / 1000 > RSS_GUARD_GB:
                mem_guard_fired = True
                print(f"MEMORY GUARD FIRED at tick {tick + 1}: rss {rss_now / 1000:.2f} GB "
                      f"> {RSS_GUARD_GB} -- stopping to dump partial state", flush=True)
                _prog_line(tick + 1, E, rad_total, max_strain, "MEMGUARD")
                break
    KE_end = float(0.5 * (vel32 ** 2).sum())
    E_end = float(KE_end + pot + (U_s + U_bend_tot + U_vol_tot if (finite and not mem_guard_fired) else float("nan")))
    dE = abs(E_end - E0) if (finite and not mem_guard_fired) else float("inf")
    V_end = float(enclosed_volume(np.ascontiguousarray(pos32, dtype=np.float64), Tc)) if V0 is not None else None
    ok_energy = finite and (dE <= rad_total + GATE_REL * peak_E)
    done = int(tick + 1)
    print(f"RUN B  {done} ticks dt={dt_int:.1e} (cliff-safe; ca_stab: finite@5e-7, diverge@5e-6) "
           f"theta={DEFAULT_THETA} leaf=16 cuda_probe={have_cuda}  mesh={MESH} closed={is_closed}")
    print(f"         per-tick mean ms: tree={ms_tree / done:.2f}  walk={ms_walk / done:.2f} "
           f"ca_numpy={ms_ca / done:.2f}   (threading verdict from THESE numbers, not vibes)", flush=True)
    print(f"         finiteness: {'HOLDS' if finite else 'BROKEN'}")
    print(f"         E0={E0:.4g}  E_end={E_end:.4g}  "
           f"wall power radiated (sum)={rad_total:.4g}")
    print(f"         max |A/A0-1| over run = {max_strain:.4e}   "
           f"(HONESTY LINE: area rigidity (Option B, derived) + bending BOTH applied; low strain = solid elements held shape)")
    print(f"         max |dihedral - rest| over run = {max_bend:.4e}   "
           f"(bending rigidity: low = sheet stayed unfolded; high = folded/crumpled as intended)")
    print(f"         dihedral band 0.244 rad (THETA_CLAMP): {'EXCEEDED -> falsifier fires' if band_exceeded else 'held'}")
    if V0 is not None:
        print(f"         OUTWARD PRESSURE (rest-exterior): V0={V0:.4g}  V_end={V_end:.4g}  "
               f"(V/V0-1 held = {(V_end / V0 - 1.0) * 100 if V_end is not None else float('nan'):.3f}%)  "
               f"max |V/V0-1| over run = {max_vol_dev:.4e}  "
               f"vol band 0.244: {'EXCEEDED -> falsifier fires' if band_exceeded_vol else 'held'}  "
               f"k_vol={K_vol:.4g} (tied to K_BOND, no free number)")
    else:
        print(f"         OUTWARD PRESSURE: not applied (open mesh, V0 undefined -- bear comes after closed-mesh validation)")
    print(f"         energy gate net of radiation ({GATE_REL * 100:.0f}%): "
           + ("PASS" if ok_energy else "FALSIFIER FIRES"))

    prog.close()                                            # flush+close the per-tick evidence file (already flushed every 25 ticks)
    OUT.write_text(json.dumps(dict(
        n_tris=nT3, n_verts=nV,
        mesh=MESH, closed=is_closed, start_scale=float(scale0),
        n_original_verts=n_orig_verts,                             # pre-merge vertex count
        n_exact_merged=n_exact_merged,                             # bit-identical verts merged (no free param)
        n_degenerate_dropped=int(degen.sum()),                      # bijection ledger: counted
        n_ca_tris=int(keep.sum()),                                  # total faders unchanged (n_tris)
        e_med=float(e_med), scale_S=float(S), k_area_derived_median=float(np.median(k)),
        dt=float(dt_int), dt_cliff=5.0e-7, diverging_term="self-draw near EPS (iso7: draw+bond no wall diverges; draw-only diverges)",
        ticks=TICKS, gate_rel=GATE_REL, cuda_probe=have_cuda,
        grad_fd_worst=float(fd_worst), energy_consistency_resid=float(resid),
        runA=dict(r0=r0, named_tri_slope_ca=float(slope_ca),
                  iso_d2U=float(d2U), iso_expected=float(expected),
                  rel_err=float(relA), gate_pass=bool(okA), named_tri_kept=sel,
                  named_tri_global=int(np.flatnonzero(keep)[sel])),
        runB=dict(E0=E0, E_end=E_end,
                   wall_power_rad=float(rad_total), dE=float(dE),
                   ticks_done=done,
                   ms_per_tick=dict(tree=float(ms_tree / done), walk=float(ms_walk / done),
                                    ca_numpy=float(ms_ca / done)),
                     max_strain_abs=max_strain, max_bend_abs=max_bend, finite=finite,
                    memory_guard_fired=mem_guard_fired,
                     theta_band=float(S_BAND), band_exceeded=bool(band_exceeded),
                     rss_end_gb=float(rss_now / 1000), energy_pass=bool(ok_energy),
                     surface_axis=dict(
                         is_closed=is_closed,
                         V0=(float(V0) if V0 is not None else None),
                         V_end=(float(V_end) if V_end is not None else None),
                         vol_held_rel=(float(V_end / V0 - 1.0) if (V0 is not None and V_end is not None) else None),
                         max_vol_dev_abs=float(max_vol_dev),
                         vol_band=float(S_BAND_VOL), band_exceeded_vol=bool(band_exceeded_vol),
                         k_vol=(float(K_vol) if V0 is not None else None),
                         note="rest-exterior = surface/areal constraint on triangle carrier (area+bending+outward volume); "
                              "not a third point-to-point force. V0 derived from geometry (no free number).")),
    ), indent=1), encoding="utf-8")
    print(f"  JSON: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
