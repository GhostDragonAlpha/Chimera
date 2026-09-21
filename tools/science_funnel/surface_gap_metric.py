"""CANDIDATE surface-gap law metrics for the touching-edge measurement.

STATUS: candidate. The committed law metric is still vertex-to-vertex
(identify_bones_v2.py surface_gaps, origin/buffy/bone-id-v2-20260919); adopting
this module's point-triangle metric as the default is the law owner's act. This
module is ADDITIVE: the old metric is reproduced verbatim so all committed
history stays measurable forever.

TWO metrics, one contract:
  gap_v2(A,B)      -- identify_bones_v2.py surface_gaps() VERBATIM: symmetric
                      min vertex-to-nearest-vertex, scipy cKDTree, float64, on
                      trimesh.load(preview, process=False) vertices.
  gap_ptt(A,B)     -- the CANDIDATE DEFAULT: symmetric min VERTEX-to-TRIANGLE
                      (exact Ericson point-to-triangle), certified per-vertex
                      by k-escalation over triangle-centroid KD order.

DERIVATION (why ptt <= v2 on every pair): every vertex of B lies on some
triangle of B, so for each v in V_A, dist(v, T_B) <= dist(v, V_B); the same
holds mirrored, and mins preserve the inequality:
      gap_ptt(A,B) = min( min_v dist(v,T_B), min_v dist(v,T_A) )
                 <=  min( min_v dist(v,V_B), min_v dist(v,V_A) ) = gap_v2(A,B).
Both are upper bounds of the true surface-to-surface distance; gap_ptt's only
slack over truth is the edge-edge-interior corner (the closest features lie on
two edge interiors and neither mesh contributes a vertex). That caveat is
inherited unchanged from the estimator's origin
(tools/science_funnel/validation/axial_adjacency_20260920/measure_adjacency.py),
which this module promotes verbatim -- same arithmetic, same order of
operations, so the committed refined numbers re-measure bit-identically.

THE K-ESCALATION GUARANTEE (the certificate that makes this a law metric, not
a heuristic): queries go over the k nearest TRIANGLE CENTROIDS of the other
mesh. A triangle whose centroid is the k-th nearest lies >= kth(v) - R_max from
v (R_max = max circumradius over the mesh, a global conservative cap), so a
vertex v is exempt from deeper search iff kth(v) - R_max >= best_global: no
unevaluated triangle for v can beat the global best. Non-exempt vertices get k
quadrupled (cap n_tri, which is full enumeration). best_global only decreases,
and the exempt set is re-derived every round from scratch, so the certificate
is sound at exit; the pair result records whether every vertex was exempted
(guaranteed=True) or the cap forced full enumeration (also guaranteed=True).
A pair whose certificate fails to close reports guaranteed=False and any
consumer MUST treat it as refusal (see the lane receipt, falsifier F8).

Determinism: float64 throughout, numpy first-index argmin ties, no timestamps,
no threading-dependent reductions. Byte-exact on rerun.

Run head:  python -B tools/science_funnel/surface_gap_metric.py  (self-test)

Trailer: Agent: GLM 5.3
"""

from __future__ import annotations

import sys

import numpy as np
from scipy.spatial import cKDTree

# The committed cut, inherited (bone_identification_v3.json
# derived_cuts.joint_gap_mm): never re-chosen here; the lane re-derives the
# valley around it.
JOINT_GAP_MM = 3.0

_LAW_RESOLUTION = 2   # 0.01 mm, the committed gap_mm resolution
_REF_RESOLUTION = 3   # 0.001 mm for exact coordinates


# ---------------------------------------------------------------------------
# shared mesh prep
# ---------------------------------------------------------------------------

def prep_vertex_metric(verts):
    """KD-tree over vertices (the v2 metric's only structure)."""
    return cKDTree(np.asarray(verts, dtype=float))


class TriMetric:
    """Precomputed structures for the point-to-triangle metric of one mesh."""

    def __init__(self, verts, faces):
        self.verts = np.asarray(verts, dtype=float)
        self.faces = np.asarray(faces)
        self.tri = self.verts[self.faces]                 # (T, 3, 3)
        self.cen = self.tri.mean(axis=1)                  # (T, 3)
        # max circumradius over the whole mesh (shared vertices, global cap)
        rr = np.sqrt(((self.tri - self.cen[:, None, :]) ** 2).sum(-1))
        self.r_max = float(rr.max())
        self.tree_c = cKDTree(self.cen)
        self.n_tri = len(self.cen)


# ---------------------------------------------------------------------------
# v2 metric, verbatim
# ---------------------------------------------------------------------------

def vertex_vertex_gap(tree_a, tree_b):
    """identify_bones_v2.py surface_gaps() body, verbatim arithmetic, plus the
    argmin provenance pair. tree_a / tree_b: prep_vertex_metric outputs."""
    d1, i1 = tree_b.query(tree_a.data, k=1)   # each A vertex -> nearest B vertex
    d2, i2 = tree_a.query(tree_b.data, k=1)   # each B vertex -> nearest A vertex
    if d1.min() <= d2.min():
        j = int(np.argmin(d1))
        prox = ("vertex", j, "vertex", int(i1[j]))
    else:
        j = int(np.argmin(d2))
        prox = ("vertex", int(i2[j]), "vertex", j)
    return float(min(d1.min(), d2.min())), prox


# ---------------------------------------------------------------------------
# exact point-triangle arithmetic (Ericson), vectorized over candidates
# ---------------------------------------------------------------------------

def _seg_point_dist(p, a, b):
    ab = b - a
    t = ((p - a) * ab).sum(-1) / np.clip((ab * ab).sum(-1), 1e-20, None)
    t = np.clip(t, 0.0, 1.0)
    proj = a + t[..., None] * ab
    return np.linalg.norm(p - proj, axis=-1)


def tri_point_dist(p, tri_a, tri_b, tri_c):
    """Exact point-to-triangle distance, vectorized over triangles (Ericson),
    with the degenerate-triangle guard.

    Guard derivation: det = d11*d22 - d12^2 equals |ab x ac|^2 exactly
    (Lagrange identity). The barycentric coordinates u, v are quotients with
    denominator det; they carry no information once det sinks into the float64
    rounding noise of the product d11*d22, i.e. when
        det <= 64 * eps_machine * d11 * d22      (64 = robustness margin 2^6).
    For such triangles (the preview meshes contain 314 exactly-zero-area
    triangles plus a sliver continuum, measured 2026-09-21) the face case is
    undefined and the EXACT distance to the degenerate triangle is the
    minimum over its three edges; the guard's error is bounded by the
    sliver's own height (<= ~1e-6 mm at the guard threshold for mm-scale
    edges), far below the 0.001 mm record resolution. Without the guard a
    zero-area triangle yields n = 0, face_d = 0/1e-20 = 0, and a garbage
    face_ok -- a forged 0.000 contact at any true separation.
    """
    ap = p - tri_a
    ab, ac = tri_b - tri_a, tri_c - tri_a
    d11 = (ab * ab).sum(-1)
    d12 = (ab * ac).sum(-1)
    d22 = (ac * ac).sum(-1)
    dp1 = (ap * ab).sum(-1)
    dp2 = (ap * ac).sum(-1)
    det = d11 * d22 - d12 * d12
    degenerate = det <= 64.0 * 2.220446049250313e-16 * np.maximum(d11 * d22, 0.0)
    det = np.where(np.abs(det) < 1e-20, 1e-20, det)
    u = (d22 * dp1 - d12 * dp2) / det
    v = (d11 * dp2 - d12 * dp1) / det
    face_ok = (u >= 0) & (v >= 0) & (u + v <= 1) & ~degenerate
    n = np.cross(ab, ac)
    face_d = np.abs((n * ap).sum(-1)) / np.sqrt(np.clip((n * n).sum(-1), 1e-20, None))
    edge_d = np.minimum(_seg_point_dist(p, tri_a, tri_b),
                        np.minimum(_seg_point_dist(p, tri_b, tri_c),
                                   _seg_point_dist(p, tri_c, tri_a)))
    return np.where(face_ok, np.minimum(face_d, edge_d), edge_d)


def _closest_point_on_tri(p, tri):
    """Single point-triangle closest point (Ericson), for coordinates."""
    a, b, c = tri
    ab, ac = b - a, c - a
    ap = p - a
    d1 = (ab * ap).sum()
    d2 = (ac * ap).sum()
    if d1 <= 0 and d2 <= 0:
        return a
    bp = p - b
    d3 = (ab * bp).sum()
    d4 = (ac * bp).sum()
    if d3 >= 0 and d4 <= d3:
        return b
    vc = d1 * d4 - d3 * d2
    if vc <= 0 and d1 >= 0 and d3 <= 0:
        den = d1 - d3
        t = d1 / den if den != 0 else 0.0
        return a + t * ab
    cp = p - c
    d5 = (ab * cp).sum()
    d6 = (ac * cp).sum()
    if d6 >= 0 and d5 <= d6:
        return c
    vb = d5 * d2 - d1 * d6
    if vb <= 0 and d2 >= 0 and d6 <= 0:
        den = d2 - d6
        t = d2 / den if den != 0 else 0.0
        return a + t * ac
    va = d3 * d6 - d5 * d4
    if va <= 0 and (d4 - d3) >= 0 and (d5 - d6) >= 0:
        den = (d4 - d3) + (d5 - d6)
        t = (d4 - d3) / den if den != 0 else 0.0
        return b + t * (c - b)
    denom = 1.0 / (va + vb + vc)
    v = vb * denom
    w = vc * denom
    return a + ab * v + ac * w


# ---------------------------------------------------------------------------
# the certified point-to-triangle metric
# ---------------------------------------------------------------------------

def _evaluate(pv, rows, tri, kk_idx):
    """Exact distances for vertex rows x candidate triangle columns.
    Returns per-row min and the winning triangle index (first-index ties)."""
    flat_idx = kk_idx.reshape(-1)
    flat_ver = np.repeat(np.arange(len(rows)), kk_idx.shape[1])
    d_parts = []
    chunk = 1 << 21
    for s in range(0, flat_idx.size, chunk):
        vi = flat_ver[s:s + chunk]
        ti = flat_idx[s:s + chunk]
        d_parts.append(tri_point_dist(pv[rows[vi]], tri[ti, 0], tri[ti, 1], tri[ti, 2]))
    d_all = np.concatenate(d_parts)
    starts = np.flatnonzero(np.r_[True, flat_ver[1:] != flat_ver[:-1]])
    ends = np.r_[starts[1:], flat_ver.size]
    mins = np.empty(len(rows))
    argmins = np.empty(len(rows), dtype=np.int64)
    for i in range(len(rows)):
        seg = d_all[starts[i]:ends[i]]
        mins[i] = seg.min()
        argmins[i] = flat_idx[starts[i] + int(seg.argmin())]
    return mins, argmins


def _direction(pv, tm, tag, verbose=False):
    """Exact global-min point-to-triangle from every vertex of pv onto tm's
    triangles, with the per-vertex k-escalation certificate.

    Returns (best_global, (vertex_index, triangle_index), guaranteed, rounds).
    """
    n_tri = tm.n_tri
    k0 = 64
    k = min(k0, n_tri)
    dc, ic = tm.tree_c.query(pv, k=k)
    ic = np.asarray(ic)
    if ic.ndim == 1:
        ic = ic[:, None]
        dc = np.asarray(dc)[:, None]
    kth = np.asarray(dc)[:, -1].copy()

    rows = np.arange(len(pv))
    best_v, arg_v = _evaluate(pv, rows, tm.tri, ic)
    g = int(np.argmin(best_v))
    best_global, best_pair = float(best_v[g]), (int(rows[g]), int(arg_v[g]))
    rounds = 0
    while True:
        rounds += 1
        exempt = (kth - tm.r_max) >= best_global
        active = rows[~exempt]
        if active.size == 0 or k >= n_tri:
            # certificate closed: every vertex exempt (or cap = full enumeration)
            return best_global, best_pair, True, rounds
        k = min(k * 4, n_tri)
        dc2, ic2 = tm.tree_c.query(pv[active], k=k)
        ic2 = np.asarray(ic2)
        if ic2.ndim == 1:
            ic2 = ic2[:, None]
        kth[active] = np.asarray(dc2)[:, -1]
        b2, a2 = _evaluate(pv, active, tm.tri, ic2)
        upd = b2 < best_v[active]
        best_v[active[upd]] = b2[upd]
        arg_v[active[upd]] = a2[upd]
        g = int(np.argmin(best_v))
        best_global, best_pair = float(best_v[g]), (int(rows[g]), int(arg_v[g]))
        if verbose:
            print("ptt %s: round %d k=%d active=%d best=%.3f"
                  % (tag, rounds, k, active.size, best_global),
                  file=sys.stderr, flush=True)


def point_triangle_gap(tma, tmb, tag="", verbose=False):
    """The CANDIDATE DEFAULT law metric: symmetric min vertex-to-triangle with
    the per-vertex k-escalation guarantee, both directions.

    Returns dict:
      gap_mm            exact float64 gap
      guaranteed        True iff both directions' certificates closed
      a_vertex_index    index of the winning vertex on mesh A (query side)
      b_triangle_index  index of the winning triangle on mesh B
      direction         "a_vertex_to_b_tri" or "b_vertex_to_a_tri"
      closest_mm        (point on A, point on B), 0.001 mm rounding is the
                        caller's choice; raw float64 here
      rounds_ab/rounds_ba  escalation rounds per direction
    """
    e_ab, (vi_a, ti_b), g_ab, r_ab = _direction(
        tma.verts, tmb, tag + "->ab", verbose=verbose)
    e_ba, (vi_b, ti_a), g_ba, r_ba = _direction(
        tmb.verts, tma, tag + "->ba", verbose=verbose)
    guaranteed = bool(g_ab and g_ba)
    if e_ab <= e_ba:
        p = tma.verts[vi_a]
        q = _closest_point_on_tri(p, tmb.tri[ti_b])
        return {"gap": float(e_ab), "guaranteed": guaranteed,
                "vertex_mesh": "A", "vertex_index": vi_a,
                "triangle_mesh": "B", "triangle_index": ti_b,
                "direction": "a_vertex_to_b_tri",
                "closest_a": p, "closest_b": q,
                "rounds_ab": r_ab, "rounds_ba": r_ba}
    p = tmb.verts[vi_b]
    q = _closest_point_on_tri(p, tma.tri[ti_a])
    return {"gap": float(e_ba), "guaranteed": guaranteed,
            "vertex_mesh": "B", "vertex_index": vi_b,
            "triangle_mesh": "A", "triangle_index": ti_a,
            "direction": "b_vertex_to_a_tri",
            "closest_a": q, "closest_b": p,
            "rounds_ab": r_ab, "rounds_ba": r_ba}


# ---------------------------------------------------------------------------
# resolutions
# ---------------------------------------------------------------------------

def r_law(x):
    """The committed law resolution: 0.01 mm."""
    return round(x, _LAW_RESOLUTION)


def r_ref(x):
    """Secondary exact-coordinate resolution: 0.001 mm."""
    return round(x, _REF_RESOLUTION)


if __name__ == "__main__":
    # Self-test: the derivation's invariants on synthetic meshes.
    import math

    # two parallel unit squares 2 mm apart: v2 sees vertex pairs (2.0);
    # ptt sees the face (2.0 as well here); now slide one square half a cell:
    va = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]], dtype=float)
    fa = np.array([[0, 1, 2], [0, 2, 3]])
    vb = va + np.array([0.0, 0.0, 2.0])
    fb = fa.copy()
    ta, tb = TriMetric(va, fa), TriMetric(vb, fb)
    g_ptt = point_triangle_gap(ta, tb)
    ka, kb = prep_vertex_metric(va), prep_vertex_metric(vb)
    g_v2, _ = vertex_vertex_gap(ka, kb)
    assert abs(g_ptt["gap"] - 2.0) < 1e-12 and abs(g_v2 - 2.0) < 1e-12
    assert g_ptt["guaranteed"]

    # the artifact class: vb is one huge triangle; a vertex of va hovers over
    # its INTERIOR at 0.5 mm while the nearest vb VERTEX is 4.24 mm away.
    va2 = np.array([[3, 3, 0.5], [3.1, 3, 0.5], [3, 3.1, 0.5]], dtype=float)
    fa2 = np.array([[0, 1, 2]])
    vb2 = np.array([[0, 0, 0], [10, 0, 0], [0, 10, 0]], dtype=float)
    fb2 = np.array([[0, 1, 2]])
    ta2, tb2 = TriMetric(va2, fa2), TriMetric(vb2, fb2)
    g2 = point_triangle_gap(ta2, tb2)
    g2v2, _ = vertex_vertex_gap(prep_vertex_metric(va2), prep_vertex_metric(vb2))
    assert abs(g2["gap"] - 0.5) < 1e-12, g2["gap"]
    assert abs(g2v2 - math.sqrt(18.25)) < 1e-9, g2v2
    assert g2["gap"] < g2v2                       # the derivation, instance
    assert g2["guaranteed"]

    # the degenerate-triangle guard: a zero-area triangle 100 mm away must NOT
    # read as contact (the forge the committed preview meshes contain: 314
    # exactly-zero-area triangles, measured 2026-09-21).
    p_far = np.array([[124.4, 47.04, 47.84]], dtype=float)
    tri_sliver = np.array([[23.76, 28.32, 50.72],
                           [23.68, 28.48, 50.64],
                           [23.68, 28.48, 50.64]], dtype=float)
    d_bad = tri_point_dist(p_far, tri_sliver[0:1], tri_sliver[1:2], tri_sliver[2:3])
    d_true = float(np.linalg.norm(p_far[0] - tri_sliver[0]))
    assert abs(d_bad[0] - d_true) < 1e-9, (d_bad, d_true)
    print("degenerate-triangle guard OK: sliver at 100 mm reads %.6f mm, not 0"
          % d_bad[0])
    print("self-test OK: v2 sees %.3f mm where the surfaces are 0.500 mm apart;"
          " ptt certifies 0.500; monotonicity holds" % g2v2)
    print("candidate module only -- the committed law is unchanged until adopted")
