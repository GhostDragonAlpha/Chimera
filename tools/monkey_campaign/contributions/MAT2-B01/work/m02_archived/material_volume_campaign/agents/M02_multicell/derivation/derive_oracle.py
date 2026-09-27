"""M02 multi-cell coupon — independent derivation oracle and fixture builder.

Pure Python standard library. Imports NOTHING from tools/ (the component under
test) and no numpy. This file is the fixture source of truth: it emits the
three fixture documents and the frozen expectations.

Oracle routes (independent of the exporter's code):
  H  — exact rationals (fractions.Fraction) via the uniform-simplex moment
       formulas; authored-frame values carried EXACTLY through Q(sqrt(3))
       pair algebra (a + b*sqrt(3) with rational a, b).
  Q  — 4-point Hammer-Stroud degree-3 tetrahedron quadrature (irrational
       barycentric points (5 + 3*sqrt(5))/20 family), pure-Python float64,
       applied to fixture VERTICES mapped into each authored frame.
       Never transforms a tensor; shares no algebra with the exporter's
       R^T I R path.
  R2 — float congruence R^T I R applied to H domain values (cross-check
       only; same algebra family as the exporter's transform, never the
       primary evidence).

Anchor: H must reproduce the PUBLISHED example-report values of
tools/material_volume_body_export_example_report.json (transcribed below as
frozen literals) for the two-body example coupon, within 1e-12.

Uniform-simplex moment formulas used by H (barycentric moments
E[lambda_i] = 1/4, E[lambda_i lambda_j] = (1 + delta_ij)/20):
  V = det([x1-x0, x2-x0, x3-x0]) / 6          m = rho * V
  c = (x0 + x1 + x2 + x3) / 4
  Q_c = (m/20) * sum_i (x_i - c)(x_i - c)^T   (central second-moment matrix)
  I_c = trace(Q_c) * Eye - Q_c                (inertia about the cell centroid)
  Body combination: M = sum m, C = sum m c / M,
  I_C = sum [ I_c + m * ((d.d) Eye - d d^T) ],  d = c - C.
  Origin-referenced combination identity (used by Q): I_origin = sum I_cell_origin,
  I_COM = I_origin - M * ((C.C) Eye - C C^T).
"""
from __future__ import annotations

import json
import math
import os
from fractions import Fraction

SQRT3 = math.sqrt(3)
ROOT5 = math.sqrt(5)

# ---------------------------------------------------------------------------
# exact pair arithmetic over Q(sqrt(3)): value = a + b*sqrt(3), a,b rational
# ---------------------------------------------------------------------------


def p(a=0, b=0):
    return (Fraction(a), Fraction(b))


def padd(x, y):
    return (x[0] + y[0], x[1] + y[1])


def psub(x, y):
    return (x[0] - y[0], x[1] - y[1])


def pmul(x, y):
    return (x[0] * y[0] + 3 * x[1] * y[1], x[0] * y[1] + x[1] * y[0])


def pscale(k, x):
    return (Fraction(k) * x[0], Fraction(k) * x[1])


def pfloat(x):
    if not isinstance(x, tuple):
        return float(x)
    return float(x[0]) + float(x[1]) * SQRT3


def vadd(u, v):
    return [padd(a, b) for a, b in zip(u, v)]


def vsub(u, v):
    return [psub(a, b) for a, b in zip(u, v)]


def vscale(k, u):
    return [pscale(k, a) for a in u]


def vdot(u, v):
    total = p()
    for a, b in zip(u, v):
        total = padd(total, pmul(a, b))
    return total


def vfloat(u):
    return [pfloat(a) for a in u]


def mfloat(M):
    return [[pfloat(x) for x in row] for row in M]


def mvec(M, u):
    return [vdot(row, u) for row in M]


def mT(M):
    return [[M[j][i] for j in range(3)] for i in range(3)]


def mmm(A, B):
    return [[padd(padd(pmul(A[i][0], B[0][j]), pmul(A[i][1], B[1][j])),
                  pmul(A[i][2], B[2][j])) for j in range(3)] for i in range(3)]


def eye3_exact():
    return [[p(1) if i == j else p() for j in range(3)] for i in range(3)]


def mdet3_exact(M):
    """Exact determinant of a 3x3 matrix of Q(sqrt(3)) pairs."""
    c0 = psub(pmul(M[1][1], M[2][2]), pmul(M[1][2], M[2][1]))
    c1 = psub(pmul(M[1][0], M[2][2]), pmul(M[1][2], M[2][0]))
    c2 = psub(pmul(M[1][0], M[2][1]), pmul(M[1][1], M[2][0]))
    return padd(psub(pmul(M[0][0], c0), pmul(M[0][1], c1)), pmul(M[0][2], c2))


# ---------------------------------------------------------------------------
# exact tetrahedron moments (H route), uniform density
# ---------------------------------------------------------------------------


def tet_volume(verts):
    e1 = vsub(verts[1], verts[0])
    e2 = vsub(verts[2], verts[0])
    e3 = vsub(verts[3], verts[0])
    d = (e1[0][0] * (e2[1][0] * e3[2][0] - e2[2][0] * e3[1][0])
         - e1[1][0] * (e2[0][0] * e3[2][0] - e2[2][0] * e3[0][0])
         + e1[2][0] * (e2[0][0] * e3[1][0] - e2[1][0] * e3[0][0]))
    return Fraction(d, 6)


def tet_centroid(verts):
    s = verts[0]
    for v in verts[1:]:
        s = vadd(s, v)
    return vscale(Fraction(1, 4), s)


def tet_props(verts, rho):
    """Exact (volume, mass, centroid, inertia-about-cell-centroid)."""
    if not isinstance(rho, tuple):
        rho = p(rho)
    V = tet_volume(verts)
    m = pmul(rho, p(V))
    c = tet_centroid(verts)
    Q = [[p() for _ in range(3)] for _ in range(3)]
    for xv in verts:
        d = vsub(xv, c)
        for i in range(3):
            for j in range(3):
                Q[i][j] = padd(Q[i][j], pmul(d[i], d[j]))
    Q = [[pscale(Fraction(1, 20), pmul(m, Q[i][j])) for j in range(3)]
         for i in range(3)]
    tr = padd(padd(Q[0][0], Q[1][1]), Q[2][2])
    eye = eye3_exact()
    I = [[psub(pscale(1, tr) if i == j else p(), Q[i][j]) for j in range(3)]
         for i in range(3)]
    return V, m, c, I


def combine(cells):
    """Exact combination of rigid cells.

    cells: iterable of (mass_pair, centroid_vec, inertia_about_own_centroid).
    Returns (M, C, I_C).
    """
    M = p()
    for m, _, _ in cells:
        M = padd(M, m)
    assert M[1] == 0, "total mass must be rational"
    invM = 1 / M[0]
    C = [p(), p(), p()]
    for m, c, _ in cells:
        C = vadd(C, [pmul(m, x) for x in c])
    C = [(x[0] * invM, x[1] * invM) for x in C]
    eye = eye3_exact()
    I = [[p() for _ in range(3)] for _ in range(3)]
    for m, c, Ic in cells:
        for i in range(3):
            for j in range(3):
                I[i][j] = padd(I[i][j], Ic[i][j])
        d = vsub(c, C)
        dd = vdot(d, d)
        for i in range(3):
            for j in range(3):
                term = padd(pmul(dd, eye[i][j]), pscale(-1, pmul(d[i], d[j])))
                I[i][j] = padd(I[i][j], pmul(m, term))
    return M, C, I


def to_body(R, t, C, I):
    """Exact authored-frame transform: c_body = R^T (C - t); I_body = R^T I R."""
    d = vsub(C, t)
    RT = mT(R)
    c_body = mvec(RT, d)
    return c_body, mmm(mmm(RT, I), R)


# ---------------------------------------------------------------------------
# Q route: Hammer-Stroud 4-point degree-3 rule, pure float, vertex-transforming
# ---------------------------------------------------------------------------

BETA = (5.0 + 3.0 * ROOT5) / 20.0
ALPHA = (1.0 - BETA) / 3.0
HS_NODES = []
for _k in range(4):
    _lam = [ALPHA] * 4
    _lam[_k] = BETA
    HS_NODES.append(_lam)


def q_volume(verts_f):
    e1 = [verts_f[1][a] - verts_f[0][a] for a in range(3)]
    e2 = [verts_f[2][a] - verts_f[0][a] for a in range(3)]
    e3 = [verts_f[3][a] - verts_f[0][a] for a in range(3)]
    return (e1[0] * (e2[1] * e3[2] - e2[2] * e3[1])
            - e1[1] * (e2[0] * e3[2] - e2[2] * e3[0])
            + e1[2] * (e2[0] * e3[1] - e2[1] * e3[0])) / 6.0


def q_cell_props(verts_f, rho):
    """float64 (mass, first moment, origin-referenced inertia) for one cell,
    by 4-point degree-3 quadrature (exact for the degree <= 2 integrands)."""
    n = len(HS_NODES)
    V = q_volume(verts_f)
    mass = 0.0
    m1 = [0.0, 0.0, 0.0]
    m2 = [[0.0] * 3 for _ in range(3)]
    for lam in HS_NODES:
        x = [sum(lam[i] * verts_f[i][a] for i in range(4)) for a in range(3)]
        w = rho / n
        mass += w
        for a in range(3):
            m1[a] += w * x[a]
            for b in range(3):
                m2[a][b] += w * x[a] * x[b]
    mass *= V
    m1 = [v * V for v in m1]
    m2 = [[v * V for v in row] for row in m2]
    I_origin = [[(m2[0][0] + m2[1][1] + m2[2][2]) * (1.0 if i == j else 0.0)
                 - m2[i][j] for j in range(3)] for i in range(3)]
    return mass, m1, I_origin


def q_body_props(cells_f, R_f, t_f):
    """cells_f: list of (cell_id, verts_f, rho).

    Vertices are mapped into the authored body frame FIRST
    (x_body = R^T (x_domain - t)), then quadrature integrates there; cells are
    combined with the origin-referenced identity. No tensor congruence, no
    numpy, no exporter algebra."""
    entries = []
    for _, verts_f, rho in cells_f:
        vb = [[sum(R_f[j][i] * (verts_f[k][j] - t_f[j]) for j in range(3))
               for i in range(3)] for k in range(4)]
        entries.append(q_cell_props(vb, rho))
    M = sum(e[0] for e in entries)
    C = [sum(e[1][a] for e in entries) / M for a in range(3)]
    I_origin = [[sum(e[2][i][j] for e in entries) for j in range(3)]
                for i in range(3)]
    cc = C[0] * C[0] + C[1] * C[1] + C[2] * C[2]
    I = [[I_origin[i][j] - M * (cc * (1.0 if i == j else 0.0) - C[i] * C[j])
          for j in range(3)] for i in range(3)]
    return M, C, I


# ---------------------------------------------------------------------------
# fixture definition (source of truth)
# ---------------------------------------------------------------------------

VERTS = {
    "r0": [p(0), p(0), p(0)],
    "r1": [p(1), p(0), p(0)],
    "r2": [p(0), p(1), p(0)],
    "r3": [p(0), p(0), p(1)],
    "d0": [p(5), p(4), p(4)],
    "d1": [p(5), p(2), p(2)],
    "d2": [p(3), p(2), p(4)],
    "d3": [p(3), p(4), p(2)],
    "s0": [p(-2), p(3), p(1)],
    "s1": [p(1), p(4), p(1)],
    "s2": [p(-2), p(4), p(3)],
    "s3": [p(-1), p(2), p(4)],
}
CELLS = [
    ("cell-R", ["r0", "r1", "r2", "r3"], Fraction(12)),
    ("cell-D", ["d0", "d1", "d2", "d3"], Fraction(6)),
    ("cell-S", ["s0", "s1", "s2", "s3"], Fraction(9)),
]
BODIES = [
    ("mc-body-1", ["cell-R", "cell-S"], "mc-frame-1"),
    ("mc-body-2", ["cell-D"], "mc-frame-2"),
]

S3 = p(Fraction(0), Fraction(1, 2))  # sqrt(3)/2, exact (value = a + b*sqrt(3))
R1 = [[p(), p(), p(1)],
      [p(Fraction(1, 2)), S3, p()],
      [pscale(-1, S3), p(Fraction(1, 2)), p()]]   # Ry(90 deg) @ Rz(30 deg)
T1 = [p(2), p(-1), p(3)]
R2M = [[p(), p(Fraction(-1, 2)), S3],
       [p(1), p(), p()],
       [p(), S3, p(Fraction(1, 2))]]              # Ry(60 deg) @ Rz(90 deg)
T2 = [p(-1), p(4), p(-2)]
FRAMES = {"mc-frame-1": (R1, T1), "mc-frame-2": (R2M, T2)}
BODY_FRAME = {"mc-body-1": "mc-frame-1", "mc-body-2": "mc-frame-2"}


def h_route():
    per_cell = {}
    for cid, ids, rho in CELLS:
        verts = [VERTS[i] for i in ids]
        V, m, c, I = tet_props(verts, rho)
        per_cell[cid] = {"volume": V, "mass": m, "com": c, "inertia": I}
    bodies_domain = {}
    for bid, member_ids, _ in BODIES:
        cells = [(per_cell[c]["mass"], per_cell[c]["com"], per_cell[c]["inertia"])
                 for c in member_ids]
        M, C, I = combine(cells)
        vol = sum((per_cell[c]["volume"] for c in member_ids), Fraction(0))
        bodies_domain[bid] = {"mass": M, "volume": vol, "com": C, "inertia": I}
    Mw, Cw, Iw = combine([(per_cell[c]["mass"], per_cell[c]["com"],
                           per_cell[c]["inertia"]) for c, _, _ in CELLS])
    volw = sum((per_cell[c]["volume"] for c, _, _ in CELLS), Fraction(0))
    whole = {"mass": Mw, "volume": volw, "com": Cw, "inertia": Iw}
    bodies_authored = {}
    for bid, _, fid in BODIES:
        R, t = FRAMES[fid]
        cb, Ib = to_body(R, t, bodies_domain[bid]["com"], bodies_domain[bid]["inertia"])
        bodies_authored[bid] = {"frame_id": fid, "mass": bodies_domain[bid]["mass"],
                                "volume": bodies_domain[bid]["volume"],
                                "com": cb, "inertia": Ib}
    return per_cell, bodies_domain, whole, bodies_authored


def q_route():
    verts_f = {k: vfloat(v) for k, v in VERTS.items()}
    frames_f = {fid: (mfloat(R), vfloat(t)) for fid, (R, t) in FRAMES.items()}
    bodies = {}
    for bid, member_ids, fid in BODIES:
        R_f, t_f = frames_f[fid]
        cells_f = [(cid, [verts_f[i] for i in ids], float(rho))
                   for cid, ids, rho in CELLS if cid in member_ids]
        M, C, I = q_body_props(cells_f, R_f, t_f)
        bodies[bid] = {"frame_id": fid, "mass": M, "com": C, "inertia": I}
    return bodies


def r2_route(bodies_domain):
    """Float congruence of the H domain tensors (cross-check only)."""
    bodies = {}
    for bid, _, fid in BODIES:
        R_f = mfloat(FRAMES[fid][0])
        t_f = vfloat(FRAMES[fid][1])
        Cf = vfloat(bodies_domain[bid]["com"])
        If = mfloat(bodies_domain[bid]["inertia"])
        RT = [[R_f[j][i] for j in range(3)] for i in range(3)]
        d = [Cf[j] - t_f[j] for j in range(3)]
        cb = [sum(RT[i][j] * d[j] for j in range(3)) for i in range(3)]
        Ib = [[sum(RT[i][k] * sum(If[k][l] * R_f[l][j] for l in range(3))
                   for k in range(3)) for j in range(3)] for i in range(3)]
        bodies[bid] = {"com": cb, "inertia": Ib}
    return bodies


# ---------------------------------------------------------------------------
# anchor: H on the PUBLISHED two-body example coupon vs published literals
# ---------------------------------------------------------------------------

ANCHOR_PUBLISHED = {
    "body-A": {"mass": 2.0, "com": [0.25, 0.25, 0.25],
               "I": [[0.15000000000000002, 0.025, 0.025],
                     [0.025, 0.15000000000000002, 0.025],
                     [0.025, 0.025, 0.15000000000000002]]},
    "body-B": {"mass": 1.0, "com": [0.25, 0.25, 0.25],
               "I": [[0.07500000000000001, 0.0125, 0.0125],
                     [0.0125, 0.07500000000000001, 0.0125],
                     [0.0125, 0.0125, 0.07500000000000001]]},
}


def anchor_check():
    av = {"a0": [p(0), p(0), p(0)], "a1": [p(1), p(0), p(0)],
          "a2": [p(0), p(1), p(0)], "a3": [p(0), p(0), p(1)],
          "b0": [p(3), p(-2), p(1)], "b1": [p(3), p(-1), p(1)],
          "b2": [p(2), p(-2), p(1)], "b3": [p(3), p(-2), p(2)]}
    _, mA, cA, IA = tet_props([av[k] for k in ("a0", "a1", "a2", "a3")], Fraction(12))
    _, mB, cB, IB = tet_props([av[k] for k in ("b0", "b1", "b2", "b3")], Fraction(6))
    Rz90 = [[p(), p(-1), p()], [p(1), p(), p()], [p(), p(), p(1)]]
    cbA, IbA = to_body(eye3_exact(), [p(), p(), p()], cA, IA)
    cbB, IbB = to_body(Rz90, [p(3), p(-2), p(1)], cB, IB)
    got = {"body-A": {"mass": pfloat(mA), "com": vfloat(cbA), "I": mfloat(IbA)},
           "body-B": {"mass": pfloat(mB), "com": vfloat(cbB), "I": mfloat(IbB)}}
    worst = 0.0
    for b in ("body-A", "body-B"):
        worst = max(worst, abs(got[b]["mass"] - ANCHOR_PUBLISHED[b]["mass"]))
        worst = max(worst, max(abs(g - q) for g, q
                               in zip(got[b]["com"], ANCHOR_PUBLISHED[b]["com"])))
        for i in range(3):
            for j in range(3):
                worst = max(worst, abs(got[b]["I"][i][j]
                                       - ANCHOR_PUBLISHED[b]["I"][i][j]))
    return worst, got


def reldev(a, b):
    return abs(a - b) / max(1.0, abs(b))


def main():
    log = []
    failures = []

    def note(msg):
        log.append(msg)

    # geometry gates ---------------------------------------------------------
    for cid, ids, _ in CELLS:
        V = tet_volume([VERTS[i] for i in ids])
        if V <= 0:
            failures.append(f"nonpositive volume {cid}")
        note(f"gate volume {cid}: {V} (= {float(V)!r}) m^3")
    id_by_cell = {cid: ids for cid, ids, _ in CELLS}
    for a, b in (("cell-R", "cell-D"), ("cell-R", "cell-S"), ("cell-D", "cell-S")):
        A = [VERTS[i] for i in id_by_cell[a]]
        B = [VERTS[i] for i in id_by_cell[b]]
        separated = False
        for axis in range(3):
            ahi = max(x[axis][0] for x in A)
            blo = min(x[axis][0] for x in B)
            bhi = max(x[axis][0] for x in B)
            alo = min(x[axis][0] for x in A)
            if ahi < blo or bhi < alo:
                separated = True
        if not separated:
            failures.append(f"AABB overlap {a}/{b}")
        note(f"gate AABB disjoint {a}/{b}: ok")
    seen = {}
    for vid, pos in VERTS.items():
        key = tuple(x[0] for x in pos)
        if key in seen:
            failures.append(f"coincident vertices {seen[key]} {vid}")
        seen[key] = vid
    note("gate all 12 vertex positions pairwise distinct: ok")

    # frame gates (exact) ----------------------------------------------------
    for fid, (R, t) in FRAMES.items():
        RT = mT(R)
        for i in range(3):
            for j in range(3):
                if vdot(RT[i], RT[j]) != (p(1) if i == j else p()):
                    failures.append(f"frame {fid} not exactly orthonormal [{i}][{j}]")
        if mdet3_exact(R) != p(1):
            failures.append(f"frame {fid} exact determinant != +1")
        note(f"gate frame {fid}: exactly orthonormal, det +1; origin {vfloat(t)}")

    per_cell, bodies_domain, whole, bodies_authored = h_route()

    Hf = {}
    for bid in bodies_domain:
        Hf[bid] = {
            "frame_id": BODY_FRAME[bid],
            "mass": pfloat(bodies_domain[bid]["mass"]),
            "volume": pfloat(bodies_domain[bid]["volume"]),
            "com_domain": vfloat(bodies_domain[bid]["com"]),
            "inertia_domain": mfloat(bodies_domain[bid]["inertia"]),
            "com_body": vfloat(bodies_authored[bid]["com"]),
            "inertia_body": mfloat(bodies_authored[bid]["inertia"]),
        }
    Hf["whole_partition"] = {
        "mass": pfloat(whole["mass"]),
        "volume": pfloat(whole["volume"]),
        "com": vfloat(whole["com"]),
        "inertia_about_com": mfloat(whole["inertia"]),
    }

    # oracle agreement gates -------------------------------------------------
    Qr = q_route()
    R2r = r2_route(bodies_domain)
    GATE = 1e-12
    for bid in ("mc-body-1", "mc-body-2"):
        devs = {"mass_Q": reldev(Qr[bid]["mass"], Hf[bid]["mass"])}
        devs["com_Q"] = max(reldev(a, b) for a, b in zip(Qr[bid]["com"], Hf[bid]["com_body"]))
        devs["com_R2"] = max(reldev(a, b) for a, b in zip(R2r[bid]["com"], Hf[bid]["com_body"]))
        for i in range(3):
            for j in range(3):
                devs[f"I_Q[{i}][{j}]"] = reldev(Qr[bid]["inertia"][i][j],
                                                Hf[bid]["inertia_body"][i][j])
                devs[f"I_R2[{i}][{j}]"] = reldev(R2r[bid]["inertia"][i][j],
                                                 Hf[bid]["inertia_body"][i][j])
        bad = {k: v for k, v in devs.items() if v > GATE}
        if bad:
            failures.append(f"oracle divergence {bid}: {bad}")
        note(f"gate oracle agreement {bid}: max rel dev H vs Q/R2 = {max(devs.values()):.3g}")

    # anchor gate -------------------------------------------------------------
    worst_anchor, _ = anchor_check()
    if worst_anchor > GATE:
        failures.append(f"anchor vs published example literals: {worst_anchor}")
    note(f"gate anchor vs published example-report literals: max abs dev {worst_anchor:.3g}")

    # protected off-diagonal design gate --------------------------------------
    T_PROTECTED = 0.002
    min_od = min(abs(Hf["mc-body-1"]["inertia_body"][i][j])
                 for i in range(3) for j in range(3) if i != j)
    if min_od <= T_PROTECTED:
        failures.append(f"protected off-diagonal gate: min |off-diag| {min_od}")
    if not all(Hf["mc-body-2"]["inertia_body"][i][j] == 0.0
               for i in range(3) for j in range(3) if i != j):
        failures.append("body-2 authored off-diagonals not exactly zero")
    note(f"gate protected off-diagonals mc-body-1: min |.| = {min_od!r} > {T_PROTECTED}")
    note("gate mc-body-2 authored off-diagonals exactly 0.0 (isotropic regular tet)")

    if failures:
        for f in failures:
            note("FAIL: " + f)
        print("\n".join(log))
        raise SystemExit("DERIVATION GATES FAILED: " + "; ".join(failures))

    # emit fixture documents ---------------------------------------------------
    manifest = {
        "schema_version": "chimera.fitting_manifest.v1",
        "fitting_id": "mc-multicell-coupon-fit-v1",
        "domain_id": "mc-three-tetrahedron-coupon",
        "domain_revision": "mc-coupon-fixture-v1",
        "coordinate_frame": {"frame_id": "mc-domain", "handedness": "right",
                             "coordinate_unit": "m", "scale_to_m": 1.0},
        "vertices": [{"vertex_id": vid, "position": vfloat(VERTS[vid])}
                     for vid in ["r0", "r1", "r2", "r3", "d0", "d1", "d2", "d3",
                                 "s0", "s1", "s2", "s3"]],
        "cells": [
            {"cell_id": "cell-R", "vertex_ids": ["r0", "r1", "r2", "r3"],
             "component_id": "mc-component-R"},
            {"cell_id": "cell-D", "vertex_ids": ["d0", "d1", "d2", "d3"],
             "component_id": "mc-component-D"},
            {"cell_id": "cell-S", "vertex_ids": ["s0", "s1", "s2", "s3"],
             "component_id": "mc-component-S"},
        ],
        "regions": [
            {"region_id": "mc-region-R", "mass_owner_id": "mc-owner-R",
             "material_id": "mc-tissue-R"},
            {"region_id": "mc-region-D", "mass_owner_id": "mc-owner-D",
             "material_id": "mc-tissue-D"},
            {"region_id": "mc-region-S", "mass_owner_id": "mc-owner-S",
             "material_id": "mc-tissue-S"},
        ],
        "mass_authority": "reconstructed_tissue_mass",
        "source_effective_segment_ids": [],
        "matter_ownership": [
            {"matter_id": "mc-matter-R", "representation": "tetrahedral_volume",
             "mass_owner_id": "mc-owner-R"},
            {"matter_id": "mc-matter-D", "representation": "tetrahedral_volume",
             "mass_owner_id": "mc-owner-D"},
            {"matter_id": "mc-matter-S", "representation": "tetrahedral_volume",
             "mass_owner_id": "mc-owner-S"},
        ],
    }
    partition = {
        "schema_version": "chimera.material_partition.v1",
        "coordinate_frame": {"frame_id": "mc-domain", "handedness": "right",
                             "coordinate_unit": "m", "scale_to_m": 1.0},
        "vertices": manifest["vertices"],
        "cells": [
            {"cell_id": "cell-R", "vertex_ids": ["r0", "r1", "r2", "r3"],
             "proposals": ["mc-region-R"]},
            {"cell_id": "cell-D", "vertex_ids": ["d0", "d1", "d2", "d3"],
             "proposals": ["mc-region-D"]},
            {"cell_id": "cell-S", "vertex_ids": ["s0", "s1", "s2", "s3"],
             "proposals": ["mc-region-S"]},
        ],
        "materials": [
            {"material_id": "mc-tissue-R", "density_kg_m3": 12.0,
             "density_source": "mc analytic coupon fixture", "conditions": "uniform"},
            {"material_id": "mc-tissue-D", "density_kg_m3": 6.0,
             "density_source": "mc analytic coupon fixture", "conditions": "uniform"},
            {"material_id": "mc-tissue-S", "density_kg_m3": 9.0,
             "density_source": "mc analytic coupon fixture", "conditions": "uniform"},
        ],
        "regions": manifest["regions"],
        "mass_authority": "reconstructed_tissue_mass",
    }
    groups = {
        "schema_version": "chimera.rigid_body_cell_groups.v1",
        "body_groups": [
            {"body_id": "mc-body-1",
             "cell_ids": ["cell-R", "cell-S"],
             "body_frame": {"frame_id": "mc-frame-1", "handedness": "right",
                            "coordinate_unit": "m",
                            "domain_from_body": {"rotation": mfloat(R1),
                                                 "origin_m": vfloat(T1)}}},
            {"body_id": "mc-body-2",
             "cell_ids": ["cell-D"],
             "body_frame": {"frame_id": "mc-frame-2", "handedness": "right",
                            "coordinate_unit": "m",
                            "domain_from_body": {"rotation": mfloat(R2M),
                                                 "origin_m": vfloat(T2)}}},
        ],
    }
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.normpath(os.path.join(here, "..", "fixtures"))
    os.makedirs(out, exist_ok=True)
    for name, doc in (("mc_manifest.json", manifest), ("mc_partition.json", partition),
                      ("mc_groups.json", groups)):
        with open(os.path.join(out, name), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(doc, fh, indent=2)
            fh.write("\n")

    # emit frozen expectations (H-route floats ARE the frozen targets) ---------
    expectations = {
        "coupon": "M02-MC multi-cell mixed-density coupon",
        "oracle": "H exact rationals + Q(sqrt3) pair algebra; cross-checked by Q (quadrature) and R2 (congruence)",
        "bodies": {bid: Hf[bid] for bid in ("mc-body-1", "mc-body-2")},
        "whole_partition": Hf["whole_partition"],
        "per_cell_domain": {cid: {"volume": pfloat(per_cell[cid]["volume"]),
                                  "mass": pfloat(per_cell[cid]["mass"]),
                                  "com": vfloat(per_cell[cid]["com"]),
                                  "inertia_about_cell_com": mfloat(per_cell[cid]["inertia"])}
                            for cid, _, _ in CELLS},
        "oracle_agreement": {bid: {"mass_Q": Qr[bid]["mass"],
                                   "com_Q": Qr[bid]["com"],
                                   "inertia_Q": Qr[bid]["inertia"],
                                   "com_R2": R2r[bid]["com"],
                                   "inertia_R2": R2r[bid]["inertia"]}
                             for bid in ("mc-body-1", "mc-body-2")},
        "gates": {"oracle_gate": GATE, "T_PROTECTED": T_PROTECTED,
                  "anchor_max_abs_dev": worst_anchor,
                  "min_protected_offdiag_body1": min_od,
                  "all_gates_passed": True},
    }
    exp_path = os.path.join(here, "derived_expectations.json")
    with open(exp_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(expectations, fh, indent=2)
        fh.write("\n")
    with open(os.path.join(here, "derivation_log.txt"), "w",
              encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(log) + "\n")

    print("\n".join(log))
    print("ALL DERIVATION GATES PASSED")
    print("expectations ->", exp_path)


if __name__ == "__main__":
    main()
