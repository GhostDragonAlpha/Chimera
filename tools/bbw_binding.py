"""bbw_binding.py -- seam route 3 (A3): BOUNDED BIHARMONIC WEIGHTS on the
welded monkey mesh, truncated to the engine's 3-pin payload format, with the
swap-impact measurement that tests the truncation theory itself.

SOURCE (cited, per mission): Astra's answer to fleet Q2 (skin-binding
question, 2026-09-13). Verbatim load-bearing points:
  - a thin elastic shell implies NO universal distance-to-pin weighting law;
    the derived object is a boundary-value problem (geometry-dependent,
    matrix-valued) -- kernel search (softmax lambda etc.) is RETIRED;
  - why bounded-falloff laws FAILED (matches E2_SEAM_SOFTMAX's measured
    refutation): a transition of width l gives |u''| ~ |du|/l^2 -- suppressing
    distant pins NARROWS transitions and RAISES curvature. Small distant
    weights != small strain;
  - the defensible smoothness surrogate is BOUNDED BIHARMONIC WEIGHTS:
    min_{w_i} sum_i int_S (Lap_S w_i)^2 dA with handle interpolation,
    bounds [0,1], partition of unity. Not physics -- the standard surrogate;
  - point attachments create unbounded pointwise curvature -- use FINITE
    attachment PATCHES (handles = vertex patches per joint, not points);
  - curvature metric must be resolution-normalized (dihedral / local edge
    spacing), not raw degrees.

RULE 0 membrane (stated before the build):
  STATEMENT   the residual W8 crease (180 knee45 / 212 compound >10-deg
              introduced edges, G7-reproduced) is carried by the RAGGED
              weight-magnitude field near top-3 dominance boundaries: IDW^2
              swaps whole-strength pins across single vertex rings (E2
              measured 0.17-0.26 pivot weight crossing one ring). The BBW
              minimizer is smooth by construction (it minimizes the squared
              surface-Laplacian energy), so its top-3 truncation swaps
              happen where the leaving pin's weight is tiny -- dominance
              boundaries become benign under the engine's 15-byte format.
  PREDICTION  (1) knee-region >10-deg introduced crease edges drop >=50%
              vs W8 on BOTH poses (knee45 180 -> <=90, compound
              212 -> <=106); (2) zero pose-introduced inverted-winding sane
              faces on either pose; (3) >=95% of the BBW binding's top-3
              swap edges are BENIGN, benign(e) <=> step_e < h_e*tan(10 deg)
              where step_e is the actual displacement step the set-flip
              moves across edge e (defined below, RULE 1) -- and the BBW
              leaving-weight distribution sits below W8's (p95).
  FALSIFIER   (frozen before any run; any prong fires = REFUTED):
              (a) knee45 creases > 90 OR compound creases > 106;
              (b) any pose-introduced inverted-winding face (>0 either pose);
              (c) benign swap-edge fraction < 95%.
              If (a)+(b) PASS but (c) fails while creases remain, that is
              the mission's named REAL FINDING: the 15-byte 3-pin payload
              format itself is the limit -- record it, recommend the
              dense-weight format extension, do NOT force a pass.

RULE 1 -- every constant is derived from measured quantities, none chosen:
  PATCH LAW   handle patch for pin k = the nearest QUARTILE (by count,
              ties broken by distance then vertex index) of pin k's
              classified cell (W8's vjoint inheritance). Derivation: the
              patch must be FINITE (Astra) and resolution-independent in
              METRIC: a cell covers a fixed surface area, so its nearest
              quarter covers a fixed quarter-area regardless of tessellation
              density. The alternative reading -- a metric ball around the
              pin -- was measured DEAD before the build: the spine pins are
              INTERIOR (0 surface verts within 0.5x cell mean radius for
              spine_upper/mid/lower), so a pin-centered ball misses the
              surface entirely; the nearest quartile of the cell attaches
              at the surface's nearest patch to the joint, which exists for
              every pin (measured cell sizes 165-1521, quartile >= 41).
  SWAP BAR    benign(e) uses the crease bar itself, no new constant: a set
              flip across edge e moves the edge-midpoint pose by step_e;
              a shear step s over local edge spacing h_e bends the strip by
              ~atan(s/h_e), so the flip alone cannot create a >10-deg
              artifact iff step_e < h_e*tan(10 deg). Worst-case weight-only
              form (for the reported leaving-weight distribution):
              m < h_e*tan(10 deg) / |u_leave - u_replace| <=
                  h_med*tan(10 deg)/(2*D)  [knee region: h_med 0.1356 m,
              D = 0.2606 m max knee-region displacement at knee45, H4
              measured] -> m < ~0.046. --report re-measures h_med and D and
              prints the bar it implies.
  SOLVER      box-constrained active set (the standard BBW QP method, in
              the mission's allowed projected-iteration class): per handle,
              equality-constrained sparse-LU solve on the free set; clamp
              bound violators to {0,1}; when feasible, RELEASE clamped
              verts whose KKT multiplier is violated ((Qw)_v < 0 at the 0
              bound / > 0 at the 1 bound) and re-solve; terminates at the
              bounded-QP KKT point. The release phase is load-bearing:
              without it the heavy biharmonic overshoot between the 28
              patches over-constrains the solve, breaks partition of unity
              by up to 1.555 (measured) and produces all-zero rows (NaN
              poison). Discretization: cotangent Laplacian L (half-sum
              cotan weights, clamped to +/-1e3 as a numerical guard; faces
              with area < 1e-8 -- E2's 206 recorded slivers, which span the
              body -- are excluded from L and the mass matrix entirely, or
              they would wire the solve across the mesh with near-singular
              weights), lumped barycentric mass M, energy matrix
              Q = L^T M^{-1} L (discrete int (Lap w)^2 dA). SciPy splu; the
              round-1 factorization is shared across all 28 handles.

Same-limb law (W8) RETAINED: the shipped top-3 selection takes the vertex's
OWN-LIMB pins by BBW weight first; out-of-limb fill only where the limb has
<3 pins, capped at 0.25 combined (W8's exact law), rows renormalized to sum 1.

Hard payload format (MembraneTick::load_vertbind): [u32 n] then per vertex
one 15-byte row = 3 pin indices (u8) + 3 weights (f32 LE), 4 + n*15 bytes
(276889 for n=18459). The engine consumes weights RAW, so shipped rows sum
to 1 in float32.

--report : offline derivation + solve + metrics + payload write (no posts).
--ab     : scratch-engine A/B, PRIVATE port 8157, isolated cwd, frames gated
           on /verts matching the offline prediction (the H4 stale-frame
           catch), portrait crops, engine killed BY PID. The live world at
           8107 is never touched and the payload is NEVER posted there.
"""
from __future__ import annotations

import argparse
import json
import shutil
import struct
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

ROOT = Path(__file__).resolve().parents[1]
TMP = ROOT / ".tmp"
EVID = ROOT / "docs" / "evidence" / "agent_fleet" / "SHIP" / "E2_BBW"
ENGINE = TMP / "build_tick" / "Release" / "chimera_engine.exe"
RUN_DIR = TMP / "bbw_run"                     # ISOLATED cwd (gallery pattern)
PORT = 8157                                   # PRIVATE: never 8107

COT_CLAMP = 1e3          # numerical guard on cotan weights (sliver angles)
AREA_MIN = 1e-8          # E2's sane-face threshold; slivers leave the solve
TAN10 = float(np.tan(np.radians(10.0)))


# -- mesh + metric machinery (verbatim methods of classify_run.py / W8 /
#    vertbind_softmax.py -- byte-identical arithmetic) -----------------------
def parse_full(path: Path):
    raw = path.read_bytes()
    n, ic = struct.unpack_from("<II", raw, 0)
    verts = np.frombuffer(raw, dtype=np.float32, count=n * 9,
                          offset=24).reshape(n, 9)
    idx = np.frombuffer(raw, dtype=np.uint32, count=ic,
                        offset=24 + n * 36).reshape(-1, 3)
    return verts, idx


def vert_normal_acc(pos: np.ndarray, idx: np.ndarray) -> np.ndarray:
    f = np.cross(pos[idx][:, 1] - pos[idx][:, 0],
                 pos[idx][:, 2] - pos[idx][:, 0])
    acc = np.zeros((len(pos), 3))
    for k in range(3):
        for d in range(3):
            acc[:, d] += np.bincount(idx[:, k], weights=f[:, d],
                                     minlength=len(pos))
    return acc


def unit(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v, axis=1, keepdims=True)
    n[n < 1e-12] = 1.0
    return v / n


def ang(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return np.degrees(np.arccos(np.clip((a * b).sum(1), -1, 1)))


def posed(pos: np.ndarray, pins: np.ndarray, order: np.ndarray,
          w: np.ndarray, deg: np.ndarray) -> np.ndarray:
    """MembraneTick::apply_travel in numpy (same arithmetic path)."""
    pv = pins[order]
    b = pos[:, None, :] - pv
    th = deg[order]
    c, s = np.cos(th), np.sin(th)
    return np.stack([
        (w * (b[:, :, 0] + pv[:, :, 0])).sum(1),
        (w * (b[:, :, 1] * c - b[:, :, 2] * s + pv[:, :, 1])).sum(1),
        (w * (b[:, :, 1] * s + b[:, :, 2] * c + pv[:, :, 2])).sum(1)], 1)


def blend_point(p: np.ndarray, pins: np.ndarray, order_row: np.ndarray,
                w_row: np.ndarray, deg: np.ndarray) -> np.ndarray:
    """apply_travel for ONE arbitrary point (an edge midpoint)."""
    pv = pins[order_row]
    b = p[None, :] - pv
    th = deg[order_row]
    c, s = np.cos(th), np.sin(th)
    return np.array([
        (w_row * (b[:, 0] + pv[:, 0])).sum(),
        (w_row * (b[:, 1] * c - b[:, 2] * s + pv[:, 1])).sum(),
        (w_row * (b[:, 1] * s + b[:, 2] * c + pv[:, 2])).sum()])


def pin_key(order3: np.ndarray, npins: int) -> np.ndarray:
    s = np.sort(order3.astype(np.int64), axis=1)
    return (s[:, 0] * npins + s[:, 1]) * npins + s[:, 2]


def flip_band(key: np.ndarray, edges: np.ndarray, nv: int) -> np.ndarray:
    band = np.zeros(nv, dtype=bool)
    diff = key[edges[:, 0]] != key[edges[:, 1]]
    band[edges[diff].ravel()] = True
    return band


def limb_graph(pos, idx, pins, tri_joint, sane):
    """W8's limb derivation (verbatim): vertex inherits its triangles' joint;
    the limb is that joint's cell group plus the groups that touch it
    (edge-adjacent sane faces only)."""
    nv = len(pos)
    npins = len(pins)
    edge_faces = defaultdict(list)
    for t in range(len(idx)):
        a, b, c = idx[t]
        for e in ((a, b), (b, c), (c, a)):
            edge_faces[(min(e), max(e))].append(t)
    touches = defaultdict(set)
    for e, ts in edge_faces.items():
        if len(ts) == 2 and sane[ts[0]] and sane[ts[1]]:
            x, y = int(tri_joint[ts[0]]), int(tri_joint[ts[1]])
            if x != y:
                touches[x].add(y)
                touches[y].add(x)
    votes = np.zeros((nv, npins), np.int32)
    votes[idx.ravel(), np.repeat(tri_joint, 3)] = 1
    tied = votes == votes.max(axis=1, keepdims=True)
    d2v = ((pos[:, None, :] - pins[None, :, :]) ** 2).sum(axis=2)
    vjoint = np.where(tied, d2v, np.inf).argmin(axis=1)
    limb_of = [{j} | touches[j] for j in range(npins)]
    order_all = np.argsort(d2v, axis=1)
    return vjoint, limb_of, d2v, order_all, edge_faces


def w8_binding(nv, npins, vjoint, limb_of, d2v, order_all):
    """The SHIPPED W8 binding (same-limb idw2 top-3, 0.25 fill cap),
    verbatim arithmetic of tools/classify_run.py. Returns (order, w64)."""
    order_new = np.empty((nv, 3), dtype=np.int64)
    w_new = np.empty((nv, 3), dtype=np.float64)
    for v in range(nv):
        limb = limb_of[vjoint[v]]
        rank = order_all[v]
        chosen = [int(p) for p in rank if p in limb][:3]
        if len(chosen) < 3:
            for p in rank:
                if p not in limb:
                    chosen.append(int(p))
                    if len(chosen) == 3:
                        break
        d3 = d2v[v, chosen]
        raw = 1.0 / (d3 + 1e-6) ** 2
        is_in = np.fromiter((p in limb for p in chosen), dtype=bool, count=3)
        raw64 = raw.astype(np.float64)
        s_in = raw64[is_in].sum()
        s_out = raw64[~is_in].sum()
        if s_in > 0 and s_out / (s_in + s_out) > 0.25:
            w = np.where(is_in, raw64 * (0.75 / s_in), raw64 * (0.25 / s_out))
        else:
            w = raw64 / raw64.sum()
        order_new[v] = chosen
        w_new[v] = w
    return order_new, w_new


# -- BBW: cotangent Laplacian, mass, active-set solve ------------------------
def face_areas(pos: np.ndarray, idx: np.ndarray) -> np.ndarray:
    return 0.5 * np.linalg.norm(np.cross(pos[idx][:, 1] - pos[idx][:, 0],
                                         pos[idx][:, 2] - pos[idx][:, 0]),
                                axis=1)


def cotan_system(pos: np.ndarray, idx: np.ndarray):
    """Cotangent Laplacian L (half-sum convention, symmetric) + lumped
    barycentric masses. Faces with area < AREA_MIN (E2's recorded slivers,
    which span the body) are excluded ENTIRELY or their near-singular cotans
    would wire the solve across the mesh. Cotans clamped to +/-COT_CLAMP.
    Returns (L csr, mass np array, kept_face_mask)."""
    nv = len(pos)
    area = face_areas(pos, idx)
    keep = area >= AREA_MIN
    f = idx[keep]
    ar = area[keep]
    p0, p1, p2 = pos[f[:, 0]], pos[f[:, 1]], pos[f[:, 2]]
    # cot at the vertex OPPOSITE each edge; edge (i,j) accumulates the cot
    # of the angle at the remaining vertex, halved (half-sum convention).
    e_i = np.concatenate([f[:, 1], f[:, 2], f[:, 0]])
    e_j = np.concatenate([f[:, 2], f[:, 0], f[:, 1]])
    e_o = np.concatenate([f[:, 0], f[:, 1], f[:, 2]])   # opposite vertex
    u = pos[e_i] - pos[e_o]      # e_i - e_o, per (edge, opposite) triple
    v = pos[e_j] - pos[e_o]
    num = (u * v).sum(1)
    denom = np.linalg.norm(np.cross(u, v), axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        cot = num / denom
    cot = np.nan_to_num(cot, nan=0.0, posinf=0.0, neginf=0.0)
    cot = np.clip(cot, -COT_CLAMP, COT_CLAMP) * 0.5
    w = cot
    L = sp.coo_matrix((np.concatenate([w, w]),
                       (np.concatenate([e_i, e_j]),
                        np.concatenate([e_j, e_i]))),
                      shape=(nv, nv)).tocsr()
    L = L - sp.diags(np.asarray(L.sum(axis=1)).ravel())
    mass = np.bincount(f.ravel(), weights=np.repeat(ar / 3.0, 3),
                       minlength=nv)   # barycentric: area/3 to each corner
    return L, mass, keep


def bbw_energy_matrix(L: sp.csr_matrix, mass: np.ndarray) -> sp.csr_matrix:
    """Q = L^T M^{-1} L  (discrete int (Lap w)^2 dA)."""
    Dinv = sp.diags(1.0 / mass)
    Q = (L.T @ (Dinv @ L)).tocsr()
    return ((Q + Q.T) * 0.5).tocsr()


def bbw_solve(Q: sp.csr_matrix, patches: list, nv: int,
              kkt_rel: float = 1e-9, max_rounds: int = 100):
    """Bounded biharmonic weights: box-constrained QP by the STANDARD
    two-phase active-set method (clamp-in + RELEASE), the mission's allowed
    projected-iteration class done right.

    Per handle: minimize w^T Q w s.t. w=1 on patch i, w=0 on other patches,
    0<=w<=1 free. Round: (1) equality-constrained sparse-LU solve on the
    free set; (2) clamp bound violators to {0,1}, fix; (3) when feasible,
    KKT-check the clamped (non-patch) verts -- a vert clamped at 0 whose
    reduced gradient (Qw)_v < -tol wants to go NEGATIVE (energy would drop
    by releasing it), a vert at 1 with (Qw)_v > +tol wants to go positive
    -- release ALL violators and re-solve. Terminates at the KKT point of
    the bounded QP; max_rounds guards the (theoretical) cycling risk.

    The release phase is NOT optional cosmetics: without it the naive
    clamp-in over-constrains the heavy-overshoot regions between the 28
    patches, breaks partition of unity by up to 1.555 (measured), and can
    clamp a vert to 0 for EVERY handle -> an all-zero row that cannot be
    renormalized (NaN poison downstream). Returns (W nv x npins, diag),
    rows NOT yet normalized."""
    npins = len(patches)
    constrained = np.zeros(nv, dtype=bool)
    for p in patches:
        constrained[p] = True
    free0 = np.where(~constrained)[0]
    bvals = np.zeros((nv, npins))
    for i, p in enumerate(patches):
        bvals[p, i] = 1.0
    Q = Q.tocsc()
    lu0 = spla.splu(Q[free0][:, free0])   # shared: round 1 free set is same
    Qcsr = Q.tocsr()
    W = np.zeros((nv, npins))
    diag = {"rounds": [], "clamped_verts": [], "released_verts": [],
            "lu_facs": 1}
    for i in range(npins):
        is_patch = constrained.copy()
        fixed_idx = np.where(constrained)[0]
        fixed_val = bvals[constrained, i].copy()
        n_clamped = 0
        n_released = 0
        rnd = 0
        while True:
            rnd += 1
            assert rnd <= max_rounds, "active set did not converge"
            fmask = np.ones(nv, dtype=bool)
            fmask[fixed_idx] = False
            F = np.where(fmask)[0]
            if len(fixed_idx) == constrained.sum():
                w_f = lu0.solve(-(Q[F][:, constrained]
                                  @ bvals[constrained, i]))
            else:
                lu = spla.splu(Q[F][:, F])
                diag["lu_facs"] += 1
                w_f = lu.solve(-(Q[F][:, fixed_idx] @ fixed_val))
            assert np.isfinite(w_f).all(), "non-finite solve"
            viol = (w_f < -1e-12) | (w_f > 1.0 + 1e-12)
            if viol.any():
                n_clamped += int(viol.sum())
                fixed_idx = np.concatenate([fixed_idx, F[viol]])
                fixed_val = np.concatenate(
                    [fixed_val, np.clip(w_f[viol], 0.0, 1.0)])
                continue
            W[np.asarray(fixed_idx), i] = fixed_val
            W[F, i] = w_f
            # KKT release check on CLAMPED (non-patch) fixed verts only
            g = Qcsr @ W[:, i]
            clamp_sel = ~is_patch[np.asarray(fixed_idx)]
            ci = np.asarray(fixed_idx)[clamp_sel]
            cv = fixed_val[clamp_sel]
            cg = g[ci]
            ktol = kkt_rel * max(1.0, float(np.abs(g).max()))
            at0 = (cv <= 0.0) & (cg < -ktol)
            at1 = (cv >= 1.0) & (cg > ktol)
            if not (at0 | at1).any():
                break
            rel = ci[at0 | at1]
            slot = np.full(nv, -1, dtype=np.int64)
            slot[fixed_idx] = np.arange(len(fixed_idx))
            keep = slot[rel]
            assert (keep >= 0).all()
            mask = np.ones(len(fixed_idx), dtype=bool)
            mask[keep] = False
            fixed_idx = np.asarray(fixed_idx)[mask]
            fixed_val = fixed_val[mask]
            n_released += int(len(rel))
        W[:, i] = np.where(constrained, bvals[:, i], W[:, i])
        diag["rounds"].append(rnd)
        diag["clamped_verts"].append(int(n_clamped))
        diag["released_verts"].append(int(n_released))
    return W, diag


# -- selection: same-limb top-3 (W8 law) over BBW dense weights --------------
def select_top3(nv, npins, vjoint, limb_of, W):
    """W8's selection law applied to BBW weights: own-limb pins by weight
    first, <3-pin limbs fill out-of-limb by weight, fill capped at 0.25
    combined, rows renormalized. Returns (order nvx3 int64, w nvx3 f64,
    diag)."""
    order_new = np.zeros((nv, 3), dtype=np.int64)
    w_new = np.zeros((nv, 3), dtype=np.float64)
    diag = {"fill": 0, "capped": 0}
    for v in range(nv):
        limb = limb_of[vjoint[v]]
        wrow = W[v]
        rank = np.argsort(-wrow, kind="stable")
        cand = [int(p) for p in rank if p in limb][:3]
        is_in = [True] * len(cand)
        if len(cand) < 3:                       # chain ends: fill out of limb
            for p in rank:
                if p not in cand:
                    cand.append(int(p))
                    is_in.append(False)
                    if len(cand) >= 3:
                        break
            diag["fill"] += 1
        ww = wrow[cand].astype(np.float64)
        if ww.sum() <= 0.0:
            # degenerate limb (every in-limb weight 0): fall back to the
            # global top-3 by weight (W8's extreme-fill reading), honestly
            # counted as fill, all three marked out-of-limb for the cap
            cand = [int(p) for p in rank[:3]]
            is_in = [False, False, False]
            ww = wrow[cand].astype(np.float64)
            diag["fill"] += 1
        in_m = np.array(is_in, dtype=bool)
        s_in = ww[in_m].sum()
        s_out = ww[~in_m].sum()
        if s_in > 0 and s_out / (s_in + s_out) > 0.25:
            diag["capped"] += 1
            ww = np.where(in_m, ww * (0.75 / s_in), ww * (0.25 / s_out))
        order_new[v] = cand
        w_new[v] = ww / ww.sum()
    return order_new, w_new, diag


# -- swap-impact machinery ----------------------------------------------------
def posed_dense(pos: np.ndarray, pins: np.ndarray, w: np.ndarray,
                deg: np.ndarray) -> np.ndarray:
    """apply_travel with the FULL dense weight row (nv x npins): the blend
    the 3-slot format cannot ship."""
    pv = pins[None]
    b = pos[:, None, :] - pv
    th = deg[None, :]
    c, s = np.cos(th), np.sin(th)
    return np.stack([
        (w * (b[:, :, 0] + pv[:, :, 0])).sum(1),
        (w * (b[:, :, 1] * c - b[:, :, 2] * s + pv[:, :, 1])).sum(1),
        (w * (b[:, :, 1] * s + b[:, :, 2] * c + pv[:, :, 2])).sum(1)], 1)


def bbw_solve_unbounded(Q: sp.csr_matrix, patches: list, nv: int):
    """The same BBW system WITHOUT the [0,1] bounds: one equality-constrained
    solve per handle on the patch-free set. Partition of unity then holds
    EXACTLY by linearity; individual weights may leave [0,1] (that is the
    cost being measured). Shares lu0 across handles."""
    npins = len(patches)
    constrained = np.zeros(nv, dtype=bool)
    for p in patches:
        constrained[p] = True
    free0 = np.where(~constrained)[0]
    bvals = np.zeros((nv, npins))
    for i, p in enumerate(patches):
        bvals[p, i] = 1.0
    Q = Q.tocsc()
    lu0 = spla.splu(Q[free0][:, free0])
    W = np.zeros((nv, npins))
    W[free0] = lu0.solve(-(Q[free0][:, constrained] @ bvals[constrained]))
    W[constrained] = bvals[constrained]
    return W
def swap_edge_list(edges: np.ndarray, interior_mask: np.ndarray,
                   key: np.ndarray):
    diff = interior_mask & (key[edges[:, 0]] != key[edges[:, 1]])
    return np.where(diff)[0]


def leaving_weights(edges, swap_e, order3, w3, npins):
    """For each swap edge: the max weight, over both endpoints and all pins
    in the triples' symmetric difference, of a LEAVING pin (present on one
    side only). This is the mass a set-flip moves across the edge."""
    out = np.empty(len(swap_e))
    for k, e in enumerate(swap_e):
        a, b = edges[e]
        sa = set(order3[a].tolist())
        sb = set(order3[b].tolist())
        leaving = sa ^ sb
        m = 0.0
        for v, s in ((a, sa), (b, sb)):
            for j, p in enumerate(order3[v]):
                if int(p) in leaving:
                    m = max(m, float(w3[v, j]))
        out[k] = m
    return out


def swap_step_test(edges, swap_e, pos64, pins64, order3, w3, deg, hlen):
    """benign(e) <=> |posed(mid under triple_a) - posed(mid under triple_b)|
    < h_e * tan(10 deg): the flip alone cannot push the local dihedral past
    the crease bar. Returns (step, benign_frac)."""
    ok = np.empty(len(swap_e), dtype=bool)
    step = np.empty(len(swap_e))
    for k, e in enumerate(swap_e):
        a, b = edges[e]
        mid = (pos64[a] + pos64[b]) * 0.5
        pa = blend_point(mid, pins64, order3[a], w3[a], deg)
        pb = blend_point(mid, pins64, order3[b], w3[b], deg)
        step[k] = np.linalg.norm(pa - pb)
        ok[k] = step[k] < hlen[e] * TAN10
    return step, ok


# -- E2 crease metric + resolution-normalized curvature ----------------------
def crease_metric(pos64, pins64, idx, region, nd0, order, w64, npins,
                  KNEE, HIP, ef, hlen):
    """E2/W8 metric (verbatim law) + the resolution-normalized curvature
    (introduced dihedral degrees per METRE of edge length, per Astra)."""
    out = {}
    for pose, degv in (("knee45", {KNEE: 45.0}),
                       ("hip20+knee45", {KNEE: 45.0, HIP: 20.0})):
        deg = np.zeros(npins)
        for j, d in degv.items():
            deg[j] = np.radians(d)
        pp = posed(pos64, pins64, order, w64, deg)
        acc = unit(vert_normal_acc(pp, idx))
        intro = np.maximum(0, ang(acc[ef[:, 0]], acc[ef[:, 1]]) - nd0)
        f_rest = np.cross(pos64[idx][:, 1] - pos64[idx][:, 0],
                          pos64[idx][:, 2] - pos64[idx][:, 0])
        f_pos = np.cross(pp[idx][:, 1] - pp[idx][:, 0],
                         pp[idx][:, 2] - pp[idx][:, 0])
        sane = 0.5 * np.linalg.norm(f_rest, axis=1) > 1e-8
        flips = int(((f_rest * f_pos).sum(1)[sane] < 0).sum())
        out[pose] = {"crease": int((region & (intro > 10)).sum()),
                     "max_deg": float(intro[region].max()),
                     "winding_flips": flips,
                     "norm_p95_deg_per_m": float(
                         np.percentile(intro[region] / hlen[region], 95)),
                     "norm_max_deg_per_m": float(
                         (intro[region] / hlen[region]).max())}
    return out


# -- scratch engine (private port, isolated cwd; H4/softmax pattern) ---------
def post(base: str, path: str, body: bytes | str, timeout: int = 300) -> dict:
    data = body.encode() if isinstance(body, str) else body
    req = urllib.request.Request(base + path, data=data, method="POST",
                                 headers={"Content-Type":
                                          "application/octet-stream"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def get_json(base: str, path: str, timeout: int = 60) -> dict:
    with urllib.request.urlopen(base + path, timeout=timeout) as r:
        return json.loads(r.read().decode())


def get_bytes(base: str, path: str, timeout: int = 120) -> bytes:
    with urllib.request.urlopen(base + path, timeout=timeout) as r:
        return r.read()


class ScratchEngine:
    """Throwaway engine on a PRIVATE port. Boot is the gallery's measured
    pattern: ISOLATED cwd holding its own shaders copy, so the tick is born
    EMPTY (the --no-restore semantics) without --no-restore itself, which
    fail-fasts at boot on this build when combined with --hidden
    (measured 2/2, tools/gallery/run_gallery.py). The LIVE world at 8107 is
    never touched."""

    def __init__(self, port: int):
        self.port = port
        self.base = f"http://127.0.0.1:{port}"
        self.proc = None
        self.log_path = RUN_DIR / f"engine_{port}.log"

    def start(self, wait_s: float = 90.0):
        assert ENGINE.is_file(), f"engine binary missing: {ENGINE}"
        RUN_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copytree(ENGINE.parent / "shaders", RUN_DIR / "shaders",
                        dirs_exist_ok=True)
        logf = open(self.log_path, "ab")
        self.proc = subprocess.Popen(
            [str(ENGINE), str(self.port), "--hidden"],
            cwd=str(RUN_DIR), stdout=logf, stderr=logf,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        deadline = time.time() + wait_s
        while time.time() < deadline:
            if self.proc.poll() is not None:
                raise RuntimeError(f"engine exited at boot "
                                   f"(code {self.proc.returncode})")
            try:
                st = get_json(self.base, "/tick_state", timeout=2)
                assert st.get("sealed") is not True, "booted SEALED?!"
                time.sleep(1.0)
                return
            except (urllib.error.URLError, OSError):
                time.sleep(0.5)
        raise RuntimeError("engine did not answer")

    def kill(self):
        if self.proc is not None and self.proc.poll() is None:
            subprocess.run(["taskkill", "/F", "/T", "/PID",
                            str(self.proc.pid)], capture_output=True)
            self.proc.wait(timeout=15)


def save_bookmark(base: str, name: str, radius, theta, phi, tgt, pan=(0, 0)):
    v = [radius, theta, phi, tgt[0], tgt[1], tgt[2], pan[0], pan[1]]
    return post(base, "/cameras", json.dumps(
        {"op": "save", "name": name,
         "v": [float(x) for x in v]}))


# -- main -------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true",
                    help="offline: derivation + BBW solve + metric + payload")
    ap.add_argument("--ab", action="store_true",
                    help="scratch-engine A/B with captures (port 8157)")
    ap.add_argument("--ship", metavar="BASE",
                    help="POST the payload to BASE /tick_vertbind only")
    args = ap.parse_args()
    if not (args.report or args.ab or args.ship):
        args.report = True

    joints = json.loads((TMP / "joints28.json").read_text())
    names = [j["name"] for j in joints]
    pins = np.asarray([j["J"] for j in joints], dtype=np.float32)
    npins = len(pins)
    KNEE, HIP = names.index("knee_L"), names.index("hip_L")

    verts, idx = parse_full(TMP / "monkey_full.bin")
    pos = verts[:, 0:3].astype(np.float32)
    idx = idx.astype(np.int64)
    nv = len(pos)
    pos64 = pos.astype(np.float64)
    pins64 = pins.astype(np.float64)

    # per-triangle CA types: nearest measured joint to the centroid
    # (float32 -- byte-identical to the shipped classification)
    centroids = pos[idx].mean(axis=1)
    d2t = ((centroids[:, None, :] - pins[None, :, :]) ** 2).sum(axis=2)
    tri_joint = d2t.argmin(axis=1).astype(np.uint8)
    sane = 0.5 * np.linalg.norm(np.cross(pos[idx][:, 1] - pos[idx][:, 0],
                                         pos[idx][:, 2] - pos[idx][:, 0]),
                                axis=1) > 1e-8

    vjoint, limb_of, d2v, order_all, edge_faces = \
        limb_graph(pos, idx, pins, tri_joint, sane)

    # ---- edges, spacing, knee region --------------------------------------
    e = np.concatenate([idx[:, [0, 1]], idx[:, [1, 2]], idx[:, [2, 0]]])
    edges = np.unique(np.sort(e, axis=1), axis=0)
    interior = {e_: fs for e_, fs in edge_faces.items() if len(fs) == 2}
    ef = np.array(sorted(interior.keys()), dtype=np.int64)
    ft = np.array([interior[(a, b)] for a, b in ef])
    hlen_all = np.linalg.norm(pos64[edges[:, 0]] - pos64[edges[:, 1]], axis=1)
    mid_e = (pos64[edges[:, 0]] + pos64[edges[:, 1]]) * 0.5
    # per-unique-edge interior/sane flags; ef (interior list) -> edges row map
    edge_pos = {(int(a), int(b)): i for i, (a, b) in enumerate(edges)}
    ef_rows = np.array([edge_pos[(int(a), int(b))] for a, b in ef])
    interior_u = np.zeros(len(edges), dtype=bool)
    interior_u[ef_rows] = True
    sane_u = np.zeros(len(edges), dtype=bool)
    sane_u[ef_rows] = sane[ft[:, 0]] & sane[ft[:, 1]]
    region_e = ((np.linalg.norm(mid_e - pins64[KNEE], axis=1) < 1.5)
                & sane_u)

    # ---- RULE 1: the two derived constants, re-measured now ---------------
    print("== RULE 1: patch law + swap bar (measured now) ==")
    patches = []
    patch_rows = []
    for k in range(npins):
        cell = np.where(vjoint == k)[0]
        assert cell.size >= 8, f"pin {names[k]} cell too small: {cell.size}"
        dk = np.sqrt(d2v[cell, k].astype(np.float64))
        order = np.lexsort((cell, dk))           # ties by vertex index
        q = max(1, cell.size // 4)
        patch = np.sort(cell[order[:q]])
        patches.append(patch)
        patch_rows.append({"pin": k, "name": names[k], "cell": int(cell.size),
                           "patch": int(patch.size),
                           "r_quartile_m": float(dk[order[q - 1]])})
        print(f"  pin {k:2d} {names[k]:14s} cell {cell.size:5d} "
              f"patch {patch.size:4d} r_q {dk[order[q-1]]:.4f} m")
    ball_dead = [names[k] for k in range(npins)
                 if not (np.sqrt(d2v[:, k]) <=
                         0.5 * np.sqrt(d2v[vjoint == k, k]).astype(np.float64)
                         .mean()).any()]
    print(f"  metric-ball alternative DEAD for {len(ball_dead)} pins "
          f"(zero surface verts within 0.5x cell radius): {ball_dead}")

    h_med = float(np.median(hlen_all[region_e]))
    # D: max knee-region displacement at knee45 under the W8 binding,
    # measured below with the binding itself (printed with the A/B numbers).
    print(f"  knee-region median edge spacing h_med = {h_med:.5f} m")
    print(f"  worst-case swap bar form: m < h_med*tan(10deg)/(2*D)")

    # ---- the bindings ------------------------------------------------------
    order_old = order_all[:, :3]                   # pre-W8 (reference)
    d3o = np.take_along_axis(d2v, order_old, axis=1)
    w_old = 1.0 / (d3o + 1e-6) ** 2
    w_old /= w_old.sum(axis=1, keepdims=True)

    order_w8, w_w8 = w8_binding(nv, npins, vjoint, limb_of, d2v, order_all)

    print("\n== BBW solve (cotan Laplacian, active set, 28 handles) ==")
    L, mass, kept = cotan_system(pos, idx)
    print(f"  faces kept {int(kept.sum())}/{len(idx)} "
          f"(excluded area<{AREA_MIN} slivers), "
          f"mass median {np.median(mass):.3e}")
    tiny = int((mass < 1e-8 * np.median(mass)).sum())
    print(f"  verts with degenerate mass (<1e-8 x median): {tiny}")
    Q = bbw_energy_matrix(L, mass)
    t0 = time.time()
    W, sdiag = bbw_solve(Q, patches, nv)
    print(f"  solved in {time.time()-t0:.1f}s "
          f"({sdiag['lu_facs']} LU factorizations)")
    print(f"  active-set rounds: min {min(sdiag['rounds'])} "
          f"max {max(sdiag['rounds'])}; clamp events {sum(sdiag['clamped_verts'])} "
          f"release events {sum(sdiag['released_verts'])} "
          f"({sdiag['lu_facs']} LU factorizations)")
    pou_err = float(np.abs(W.sum(1) - 1.0).max())
    rowsum = W.sum(axis=1)
    zeromask = rowsum < 1e-10
    zero_rows = int(zeromask.sum())
    pou_nz = float(np.abs(rowsum[~zeromask] - 1.0).max()) if zero_rows < nv \
        else float("nan")
    print(f"  partition-of-unity max|sum-1| BEFORE normalization: "
          f"{pou_err:.3e} (non-degenerate rows only: {pou_nz:.3e})")
    print(f"  all-zero weight rows (bounded QP optimum degenerate): "
          f"{zero_rows}")
    # STRUCTURAL FACT, recorded: with 28 FINITE patches, the bounded QP
    # optimum genuinely violates partition of unity in the far field
    # (biharmonic overshoot dips negative for EVERY handle there; the KKT
    # release phase confirms those clamps are real, not solver artifacts).
    # Bounds [0,1] and PoU cannot both hold at those verts. PoU wins (the
    # engine needs sum-1 rows): those verts fall back to the SHIPPED W8 law.
    assert np.isfinite(W).all()
    Wn = np.where(rowsum[:, None] > 1e-10,
                  W / np.maximum(rowsum, 1e-300)[:, None], 0.0)
    fallback = np.where(zeromask)[0]
    fb_hist = np.bincount(vjoint[fallback], minlength=npins) \
        if zero_rows else np.zeros(npins, dtype=np.int64)
    if zero_rows:
        print(f"  PoU-vs-bounds fallback (W8 law) on {zero_rows} verts "
              f"({100*zero_rows/nv:.2f}%); by owning pin: "
              f"{ {names[k]: int(c) for k, c in enumerate(fb_hist) if c} }")

    order_bbw, w_bbw, seldiag = select_top3(nv, npins, vjoint, limb_of, Wn)
    if zero_rows:                       # degenerate rows ship the W8 row
        order_bbw[fallback] = order_w8[fallback]
        w_bbw[fallback] = w_w8[fallback]
        seldiag["fallback_rows"] = zero_rows
    w_bbw32 = w_bbw.astype(np.float32)
    w_bbw64 = w_bbw32.astype(np.float64)           # the shipped precision

    # truncation mass of the DENSE field (the theory quantity); fallback
    # rows carry the W8 row, whose mass is 1 by construction
    dense_top3_mass = np.take_along_axis(
        Wn, np.argsort(-Wn, axis=1, kind="stable")[:, :3], 1).sum(1)
    dense_top3_mass[fallback] = 1.0

    # ---- hard constraints on the NEW binding ------------------------------
    sum_err = np.abs(w_bbw32.astype(np.float64).sum(1) - 1.0).max()
    deg0 = np.zeros(npins)
    rest_err = np.abs(posed(pos64, pins64, order_bbw, w_bbw64,
                            deg0) - pos64).max()
    print("\n== hard constraints (BBW binding) ==")
    print(f"  float32 weight-sum max|sum-1|: {sum_err:.3e}")
    print(f"  deg-0 blend rest error (max m): {rest_err:.3e}")
    print(f"  dense top-3 truncation mass: median "
          f"{np.median(dense_top3_mass):.6f} p5 "
          f"{np.percentile(dense_top3_mass,5):.6f} min "
          f"{dense_top3_mass.min():.6f}")
    print(f"  fill verts: {seldiag['fill']}  (0.25 cap hit: {seldiag['capped']})")
    ok = (sum_err < 1e-6 and rest_err < 1e-6)
    print(f"  -> {'PASS' if ok else 'FAIL'}")

    # ---- D: measured max knee-region displacement, per binding ------------
    knee_ids = np.where(np.linalg.norm(pos64 - pins64[KNEE], axis=1) < 0.35)[0]
    deg_k = np.zeros(npins); deg_k[KNEE] = np.radians(45.0)
    d_w8 = float(np.linalg.norm(
        posed(pos64, pins64, order_w8, w_w8.astype(np.float32)
              .astype(np.float64), deg_k)[knee_ids] - pos64[knee_ids],
        axis=1).max())
    d_bbw = float(np.linalg.norm(
        posed(pos64, pins64, order_bbw, w_bbw64, deg_k)[knee_ids]
        - pos64[knee_ids], axis=1).max())
    D = max(d_w8, d_bbw)
    swap_bar = h_med * TAN10 / (2.0 * D)
    print(f"\n== swap bar (RULE 1, measured) ==")
    print(f"  D knee45 max displacement: W8 {d_w8:.4f} m, BBW {d_bbw:.4f} m")
    print(f"  worst-case leaving-weight bar = "
          f"{h_med:.5f}*{TAN10:.5f}/(2*{D:.4f}) = {swap_bar:.4f}")

    # ---- E2 crease metric, W8's method + resolution-normalized ------------
    acc0 = unit(vert_normal_acc(pos64, idx))
    nd0 = ang(acc0[ef[:, 0]], acc0[ef[:, 1]])
    hlen_ef = hlen_all[ef_rows]                    # per interior edge

    print("\n== E2 posed-surface crease metric (knee region, >10 deg) ==")
    res = {}
    for label, order, w in (("pre-W8 (reference)", order_old, w_old),
                            ("W8 (shipped OLD)", order_w8, w_w8.astype(
                                np.float32).astype(np.float64)),
                            ("BBW (NEW)", order_bbw, w_bbw64)):
        res[label] = crease_metric(pos64, pins64, idx, region_e[ef_rows],
                                   nd0, order, w, npins, KNEE, HIP, ef,
                                   hlen_ef)
        r = res[label]
        print(f"  {label:20s} knee45: {r['knee45']['crease']:4d} "
              f"(max {r['knee45']['max_deg']:.1f} deg, flips "
              f"{r['knee45']['winding_flips']}, normmax "
              f"{r['knee45']['norm_max_deg_per_m']:.0f} deg/m) | "
              f"hip20+knee45: {r['hip20+knee45']['crease']:4d} (max "
              f"{r['hip20+knee45']['max_deg']:.1f} deg, flips "
              f"{r['hip20+knee45']['winding_flips']}, normmax "
              f"{r['hip20+knee45']['norm_max_deg_per_m']:.0f} deg/m)")
    old_n = res["W8 (shipped OLD)"]["knee45"]["crease"]
    new_n = res["BBW (NEW)"]["knee45"]["crease"]
    old_c = res["W8 (shipped OLD)"]["hip20+knee45"]["crease"]
    new_c = res["BBW (NEW)"]["hip20+knee45"]["crease"]
    drop1, drop2 = 1 - new_n / old_n, 1 - new_c / old_c
    print(f"  drop vs W8: knee45 {100*drop1:.1f}% | compound {100*drop2:.1f}%"
          f"  (falsifier bar: >=50% both)")
    flips_bbw = (res["BBW (NEW)"]["knee45"]["winding_flips"],
                 res["BBW (NEW)"]["hip20+knee45"]["winding_flips"])
    print(f"  pose-introduced winding flips (BBW vs rest): "
          f"knee45 {flips_bbw[0]}, compound {flips_bbw[1]}")

    # ---- DIAGNOSTIC: format limit or field limit? (the mission's own
    # question -- run BEFORE any verdict interpretation) --------------------
    # (a) the DENSE 28-pin blend of the bounded solve: the smooth field the
    #     3-slot format CANNOT ship. If clean while the shipped truncation
    #     creases, the format is the limit.
    # (b) the UNBOUNDED solve truncated to top-3: isolates what the
    #     bounds/clamp/renormalize path costs.
    diag_metric = {}
    Wn_dense = Wn.copy()
    Wn_dense[fallback] = 0.0
    Wn_dense[fallback[:, None], order_w8[fallback]] = w_w8[fallback]
    for pose, degv in (("knee45", {KNEE: 45.0}),
                       ("hip20+knee45", {KNEE: 45.0, HIP: 20.0})):
        deg = np.zeros(npins)
        for j, d in degv.items():
            deg[j] = np.radians(d)
        pp = posed_dense(pos64, pins64, Wn_dense, deg)
        acc = unit(vert_normal_acc(pp, idx))
        intro = np.maximum(0, ang(acc[ef[:, 0]], acc[ef[:, 1]]) - nd0)
        f_rest = np.cross(pos64[idx][:, 1] - pos64[idx][:, 0],
                          pos64[idx][:, 2] - pos64[idx][:, 0])
        f_pos = np.cross(pp[idx][:, 1] - pp[idx][:, 0],
                         pp[idx][:, 2] - pp[idx][:, 0])
        sn = 0.5 * np.linalg.norm(f_rest, axis=1) > 1e-8
        fl = int(((f_rest * f_pos).sum(1)[sn] < 0).sum())
        diag_metric.setdefault("dense_bounded", {})[pose] = {
            "crease": int((region_e[ef_rows] & (intro > 10)).sum()),
            "max_deg": float(intro[region_e[ef_rows]].max()),
            "winding_flips": fl}
    Wu = bbw_solve_unbounded(Q, patches, nv)
    pou_u = float(np.abs(Wu.sum(1) - 1.0).max())
    order_u, w_u, selu = select_top3(nv, npins, vjoint, limb_of, Wu)
    neg_rows = int((w_u < -1e-9).any(axis=1).sum())
    w_u32 = w_u.astype(np.float32).astype(np.float64)
    diag_metric["unbounded"] = {"pou_max_err": pou_u,
                                "out_of_bound_rows": int(
                                    ((Wu < -1e-9) | (Wu > 1 + 1e-9))
                                    .any(axis=1).sum()),
                                "shipped_negative_rows": neg_rows}
    for pose, degv in (("knee45", {KNEE: 45.0}),
                       ("hip20+knee45", {KNEE: 45.0, HIP: 20.0})):
        diag_metric["unbounded"][pose] = crease_metric(
            pos64, pins64, idx, region_e[ef_rows], nd0, order_u, w_u32,
            npins, KNEE, HIP, ef, hlen_ef)[pose]
    print("\n== DIAGNOSTIC: format limit or field limit? ==")
    for pose in ("knee45", "hip20+knee45"):
        d = diag_metric["dense_bounded"][pose]
        u = diag_metric["unbounded"][pose]
        print(f"  {pose:14s} DENSE bounded: {d['crease']:4d} creases "
              f"(max {d['max_deg']:.1f}, flips {d['winding_flips']}) | "
              f"UNBOUNDED top-3: {u['crease']:4d} creases "
              f"(max {u['max_deg']:.1f}, flips {u['winding_flips']})")
    print(f"  unbounded: PoU max err {pou_u:.2e}, rows out of [0,1]: "
          f"{diag_metric['unbounded']['out_of_bound_rows']}, "
          f"shipped rows with negative weights: {neg_rows}")

    # ---- swap-impact measurement (THE theory test) -------------------------
    print("\n== swap-impact (top-3 set flips across interior edges) ==")
    key_w8 = pin_key(order_w8, npins)
    key_bbw = pin_key(order_bbw, npins)
    _, invu = np.unique(pos, axis=0, return_inverse=True)
    gsize = npins ** 3

    def split_groups(key):
        first = np.unique(invu.astype(np.int64) * gsize + key) // gsize
        _, cnt = np.unique(first, return_counts=True)
        return int((cnt > 1).sum())

    swap_summary = {}
    for label, order, w in (("W8", order_w8, w_w8.astype(np.float32)
                             .astype(np.float64)),
                            ("BBW", order_bbw, w_bbw64)):
        key = pin_key(order, npins)
        swap_e = swap_edge_list(edges, interior_u, key)
        band = flip_band(key, edges, nv)
        lw = leaving_weights(edges, swap_e, order, w, npins)
        row = {"swap_edges": int(len(swap_e)), "flip_band_verts":
               int(band.sum()), "dup_splits": split_groups(key),
               "leave_w_p50": float(np.percentile(lw, 50)),
               "leave_w_p95": float(np.percentile(lw, 95)),
               "leave_w_max": float(lw.max()),
               "leave_w_below_bar_frac": float((lw < swap_bar).mean())}
        for pose, degv in (("knee45", {KNEE: 45.0}),
                           ("hip20+knee45", {KNEE: 45.0, HIP: 20.0})):
            deg = np.zeros(npins)
            for j, d in degv.items():
                deg[j] = np.radians(d)
            step, ben = swap_step_test(edges, swap_e, pos64, pins64, order,
                                       w, deg, hlen_all)
            inreg = region_e[swap_e]
            lw_r = lw[inreg] if inreg.any() else np.array([np.nan])
            row[pose] = {"benign_frac": float(ben.mean()),
                         "step_p95": float(np.percentile(step, 95)),
                         "step_max": float(step.max()),
                         "region_swap_edges": int(inreg.sum()),
                         "region_leave_w_p95": float(np.nanpercentile(
                             lw_r, 95)),
                         "region_benign_frac": float(ben[inreg].mean())
                         if inreg.any() else float("nan")}
        swap_summary[label] = row
        print(f"  {label}: swap edges {row['swap_edges']}, "
              f"leave-w p50 {row['leave_w_p50']:.4f} p95 "
              f"{row['leave_w_p95']:.4f} max {row['leave_w_max']:.4f} "
              f"(bar {swap_bar:.4f}: {100*row['leave_w_below_bar_frac']:.1f}%"
              f" below)")
        for pose in ("knee45", "hip20+knee45"):
            r = row[pose]
            print(f"    {pose:14s} benign {100*r['benign_frac']:.1f}% "
                  f"(step p95 {r['step_p95']*1000:.1f} mm, max "
                  f"{r['step_max']*1000:.1f} mm) | region swaps "
                  f"{r['region_swap_edges']}: leave-w p95 "
                  f"{r['region_leave_w_p95']:.4f}, benign "
                  f"{100*r['region_benign_frac']:.1f}%")

    # falsifier prongs, exactly as frozen in the header
    prong_a = (new_n <= 90) and (new_c <= 106)
    prong_b = (flips_bbw[0] == 0) and (flips_bbw[1] == 0)
    worst_benign = min(swap_summary["BBW"][p]["benign_frac"]
                       for p in ("knee45", "hip20+knee45"))
    prong_c = worst_benign >= 0.95
    verdict = bool(prong_a and prong_b and prong_c)
    print(f"\n  FALSIFIER PRONGS: (a) creases<=90/106: "
          f"{'PASS' if prong_a else 'FAIL'} | (b) zero flips: "
          f"{'PASS' if prong_b else 'FAIL'} | (c) benign>=95%: "
          f"{'PASS' if prong_c else 'FAIL'}")
    print(f"  OFFLINE FALSIFIER VERDICT: "
          f"{'LAW HELD' if verdict else 'LAW REFUTED'}")
    if prong_a and prong_b and not prong_c:
        print("  -> the mission's REAL FINDING branch: the 15-byte 3-pin "
              "payload FORMAT is the limit; recommend the dense-weight "
              "format extension.")

    # ---- payload file: the exact /tick_vertbind body -----------------------
    EVID.mkdir(parents=True, exist_ok=True)
    body = (struct.pack("<I", nv)
            + np.concatenate([order_bbw.astype(np.uint8),
                              w_bbw32.view(np.uint8).reshape(nv, 12)],
                             axis=1).tobytes())
    assert len(body) == 4 + nv * 15
    payload_path = EVID / "vertbind_bbw_payload.bin"
    payload_path.write_bytes(body)
    (TMP / "vertbind_bbw_payload.bin").write_bytes(body)
    print(f"\n  payload written: {payload_path} ({len(body)} bytes)")

    metrics = {"astra_source": "Astra answer to fleet Q2 (skin-binding), "
                               "2026-09-13: no universal distance-to-pin law; "
                               "bounded biharmonic weights = the surrogate; "
                               "finite patches; resolution-normalized metric",
               "patch_law": "nearest quartile of the pin's classified cell",
               "patches": patch_rows, "metric_ball_dead": ball_dead,
               "h_med_knee": h_med, "D_w8": d_w8, "D_bbw": d_bbw,
               "swap_bar_worstcase": swap_bar,
               "solver": {"class": "box-constrained active set (clamp-in + "
                                   "KKT release), sparse LU",
                          "lu_facs": sdiag["lu_facs"],
                          "rounds_max": max(sdiag["rounds"]),
                          "clamp_events": sum(sdiag["clamped_verts"]),
                          "release_events": sum(sdiag["released_verts"]),
                          "pou_max_err_prenorm": pou_err,
                          "pou_max_err_prenorm_nondeg": pou_nz,
                          "zero_rows": zero_rows,
                          "fallback_hist": {names[k]: int(c)
                                            for k, c in enumerate(fb_hist)
                                            if c},
                          "degenerate_mass_verts": tiny},
               "sum_err": float(sum_err), "rest_err": float(rest_err),
               "dense_top3_mass": {
                   "median": float(np.median(dense_top3_mass)),
                   "p5": float(np.percentile(dense_top3_mass, 5)),
                   "min": float(dense_top3_mass.min())},
               "fill": seldiag["fill"], "capped": seldiag["capped"],
               "metric": res, "swap": swap_summary,
               "diagnostic": diag_metric,
               "drop_knee45": float(drop1), "drop_compound": float(drop2),
               "prongs": {"a_creases": bool(prong_a), "b_flips": bool(prong_b),
                          "c_benign": bool(prong_c)},
               "offline_verdict": "HELD" if verdict else "REFUTED"}
    (EVID / "metrics.json").write_text(json.dumps(metrics, indent=2),
                                       encoding="utf-8")
    if args.ship:
        base = args.ship
        print("vertbind:", post(base, "/tick_vertbind", body, timeout=120))
        return 0

    if not args.ab:
        return 0

    # ---- scratch-engine A/B with captures (H4 recipe, port 8157) -----------
    # Every frame GATED on /verts matching the offline predicted displacement
    # (2 mm) before the grab -- a stale or lost pose can never ship.
    print(f"\n== scratch engine A/B on 127.0.0.1:{PORT} (live world 8107 "
          f"untouched) ==")
    deg_poses = {"knee45": {KNEE: 45.0},
                 "compound": {KNEE: 45.0, HIP: 20.0}}

    def predicted(order, w, deg):
        pp = posed(pos64, pins64, order, w, deg)
        return float(np.linalg.norm(pp[knee_ids] - pos64[knee_ids],
                                    axis=1).max())

    def deg_vec(dg):
        d = np.zeros(npins)
        for j, v in dg.items():
            d[int(j)] = np.radians(float(v))
        return d

    pred = {(tag, pose): predicted(order, w, deg_vec(dg))
            for tag, order, w in (("old", order_w8,
                                   w_w8.astype(np.float32)
                                   .astype(np.float64)),
                                  ("new", order_bbw, w_bbw64))
            for pose, dg in deg_poses.items()}

    eng = ScratchEngine(PORT)
    eng.start()
    shots = {}
    ab_log = {}
    try:
        base = eng.base
        mesh = (TMP / "monkey_full.bin").read_bytes()
        print("mesh:", post(base, "/mesh_bin", mesh, timeout=300))
        pins_body = struct.pack("<I", npins) \
            + np.ascontiguousarray(pins).tobytes()
        print("joints:", post(base, "/tick_joints", pins_body))
        print("classify:", post(base, "/tick_classify",
                                struct.pack("<I", len(tri_joint))
                                + tri_joint.tobytes()))

        tgt = pins64[KNEE]
        print("camera:", save_bookmark(base, "a3knee", 0.6, np.pi / 2,
                                       0.15, tgt))

        def live_disp():
            b = get_bytes(base, "/verts")
            n = struct.unpack_from("<I", b, 0)[0]
            lv = np.frombuffer(b, np.float32, n * 9, 4).reshape(n, 9)[:, 0:3]
            return float(np.linalg.norm(lv[knee_ids] - pos64[knee_ids],
                                        axis=1).max())

        def pose_capture(pose, tag, vb_body):
            print(f"vertbind({tag}):", post(base, "/tick_vertbind", vb_body,
                                            timeout=120))
            for j in (HIP, KNEE):
                post(base, "/tick_pose",
                     json.dumps({"joint_index": j, "deg": 0}))
            time.sleep(0.7)
            rest_d = live_disp()
            for j, d in deg_poses[pose].items():
                r = post(base, "/tick_pose",
                         json.dumps({"joint_index": int(j), "deg": float(d)}))
                assert r.get("ok"), f"pose refused {r}"
            obs = rest_d
            for _ in range(20):                # verified pose: <= 10 s wait
                time.sleep(0.5)
                obs = live_disp()
                if abs(obs - pred[(tag, pose)]) < 0.002:
                    break
            assert abs(obs - pred[(tag, pose)]) < 0.002, \
                f"pose never verified: obs {obs:.4f} vs " \
                f"pred {pred[(tag, pose)]:.4f}"
            post(base, "/cameras", json.dumps({"op": "recall",
                                               "name": "a3knee"}))
            time.sleep(0.5)
            png = get_bytes(base, "/frame?w=1280", timeout=120)
            assert png[:8] == b"\x89PNG\r\n\x1a\n", "no PNG from /frame"
            p = EVID / f"{pose}_{tag}.png"
            p.write_bytes(png)
            ab_log[f"{pose}_{tag}"] = {
                "pred_disp": pred[(tag, pose)], "observed_disp": obs,
                "rest_disp": rest_d, "png_bytes": len(png)}
            print(f"  capture {pose}/{tag}: disp pred "
                  f"{pred[(tag,pose)]:.4f} obs {obs:.4f} "
                  f"(rest {rest_d:.6f}) -> {p.name}")
            return p

        old_body = (struct.pack("<I", nv)
                    + np.concatenate(
                        [order_w8.astype(np.uint8),
                         w_w8.astype(np.float32).view(np.uint8)
                         .reshape(nv, 12)], axis=1).tobytes())
        assert len(old_body) == 4 + nv * 15
        shots[("knee45", "old")] = pose_capture("knee45", "old", old_body)
        shots[("knee45", "new")] = pose_capture("knee45", "new", body)
        shots[("compound", "old")] = pose_capture("compound", "old",
                                                  old_body)
        shots[("compound", "new")] = pose_capture("compound", "new", body)

        st = get_json(base, "/tick_state")
        (EVID / "tick_state_after.json").write_text(
            json.dumps(st, indent=2), encoding="utf-8")
    finally:
        eng.kill()
    metrics["ab"] = ab_log
    (EVID / "metrics.json").write_text(json.dumps(metrics, indent=2),
                                       encoding="utf-8")

    # portrait crops: same tall box both frames, knee pin near frame center
    try:
        from PIL import Image
        for (pose, tag), p in shots.items():
            im = Image.open(p)
            w, h = im.size
            box = (int(w * 0.36), int(h * 0.10), int(w * 0.64), int(h * 0.90))
            im.crop(box).save(EVID / f"{pose}_{tag}_crop.png")
        print("crops written (portrait boxes)")
    except ImportError:
        print("PIL unavailable -- full frames stand as the crops")

    shutil.copy(RUN_DIR / f"engine_{PORT}.log",
                EVID / f"engine_{PORT}_log.txt")
    print("\nAB captures in", EVID)
    return 0


if __name__ == "__main__":
    sys.exit(main())
