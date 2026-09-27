"""Preregistration derivation for the two body-export proof coupons.

This script runs BEFORE any proof suite and freezes:

  * the fixture definitions (documents printed below as JSON),
  * the analytic expectations (exact rationals and float literals),
  * numerical tolerances and falsifier thresholds,
  * the composed authored-frame matrices for the frame-composition coupon.

Deliberately independent of tools/material_volume*.py. Three methods are used
and cross-checked here (any disagreement > 1e-12 fails this script and would
invalidate the preregistration):

  H  Hand-derived exact rational mass properties (fractions.Fraction), from
     the raw moment integrals of a uniform right tetrahedron
     (int x_a dm = m*S_a/4, int x_a x_b dm = m/20 * [sum_i p_ia p_ib + S_a S_b]).
  Q  Hammer-Stroud 4-point degree-3 tetrahedron quadrature with irrational
     barycentric points, applied to vertices transformed into the target
     frame first (never a tensor congruence).
  R2 Congruence transform of the H values through the authored frames
     (c_body = R^T (c - t), I_body = R^T I R) -- cross-check only.

The frozen Q literals (route 1: vertex transform + quadrature) are the values
embedded in the preregistration documents and proof suites.  Because route 1
never uses a tensor congruence, the expectations do not share the algebra of
the exporter's frame transform.

Run: python tools/material_volume_export_proof_prereg_derivation.py
"""
from __future__ import annotations

import json
import math
from fractions import Fraction as F

TOL = 1e-12                 # frozen comparison tolerance (absolute, rtol 0)
T_PROTECTED = 0.002         # falsifier F4: protected off-diagonal magnitude
Q_GUARD = 5                 # cross-check guard digits exponent (1e-5 design gate
                            # is not used; cross-checks require TOL agreement)

# --------------------------------------------------------------------------
# Fixture definitions (the preregistered fixtures themselves).
# --------------------------------------------------------------------------

SI_VERTICES = [
    ("v0", (0.0, 0.0, 0.0)),
    ("v1", (1.0, 0.0, 0.0)),
    ("v2", (0.0, 1.0, 0.0)),
    ("v3", (0.0, 0.0, 1.0)),
    ("v4", (0.0, 0.0, -1.0)),
]
SI_CELLS = [
    # (cell_id, vertex_ids, region_id, component_id)
    ("cell-upper", ("v0", "v1", "v2", "v3"), "si-region-A", "si-component-0"),
    ("cell-lower", ("v0", "v2", "v1", "v4"), "si-region-B", "si-component-0"),
]
SI_DENSITY = {"si-tissue-A": 12.0, "si-tissue-B": 6.0}
SI_REGIONS = [
    ("si-region-A", "si-owner-A", "si-tissue-A"),
    ("si-region-B", "si-owner-B", "si-tissue-B"),
]

FC_VERTICES = [
    ("a0", (0.0, 0.0, 0.0)),
    ("a1", (1.0, 0.0, 0.0)),
    ("a2", (0.0, 1.0, 0.0)),
    ("a3", (0.0, 0.0, 1.0)),
    ("b0", (2.0, -1.0, 0.5)),
    ("b1", (2.0, 0.0, 0.5)),
    ("b2", (2.0, -1.0, 1.5)),
    ("b3", (3.0, -1.0, 0.5)),
]
FC_CELLS = [
    ("fc-cell-A", ("a0", "a1", "a2", "a3"), "fc-region-A", "fc-component-A"),
    ("fc-cell-B", ("b0", "b1", "b2", "b3"), "fc-region-B", "fc-component-B"),
]
FC_DENSITY = {"fc-tissue-A": 12.0, "fc-tissue-B": 6.0}
FC_REGIONS = [
    ("fc-region-A", "fc-owner-A", "fc-tissue-A"),
    ("fc-region-B", "fc-owner-B", "fc-tissue-B"),
]

# Authored-frame chain for the frame-composition coupon:
#   x_domain = R_parent_from_parentframe? ...
# Contract: x_domain = R * x_body + origin_m.
#   Parent P : x_domain = R_DP x_P + t_DP
#   A-in-P   : x_P     = R_PA x_LA + t_PA
#   B-in-P   : x_P     = R_PB x_LB + t_PB
_C30 = math.sqrt(3.0) / 2.0
S30 = 0.5
R_DP = [[_C30, -S30, 0.0], [S30, _C30, 0.0], [0.0, 0.0, 1.0]]   # Rz(+30 deg)
T_DP = [1.0, -2.0, 0.5]
R_PA = [[0.0, -1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]]     # Rz(+90 deg)
T_PA = [0.5, 0.0, 0.25]
R_PB = [[0.0, 0.0, 1.0], [0.0, 1.0, 0.0], [-1.0, 0.0, 0.0]]     # Ry(+90 deg)
T_PB = [0.0, 0.75, -0.5]

# --------------------------------------------------------------------------
# Small pure-Python linear algebra (no numpy).
# --------------------------------------------------------------------------


def m_mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)]
            for i in range(3)]


def m_vec(a, v):
    return tuple(sum(a[i][k] * v[k] for k in range(3)) for i in range(3))


def m_t(a):
    return [[a[j][i] for j in range(3)] for i in range(3)]


def v_sub(a, b):
    return tuple(a[i] - b[i] for i in range(3))


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def det3(a):
    return (a[0][0] * (a[1][1] * a[2][2] - a[1][2] * a[2][1])
            - a[0][1] * (a[1][0] * a[2][2] - a[1][2] * a[2][0])
            + a[0][2] * (a[1][0] * a[2][1] - a[1][1] * a[2][0]))


def _check_rotation(r, label):
    ident = m_mul(m_t(r), r)
    for i in range(3):
        for j in range(3):
            assert abs(ident[i][j] - (1.0 if i == j else 0.0)) < 1e-15, label
    assert abs(det3(r) - 1.0) < 1e-15, label


# --------------------------------------------------------------------------
# Method Q: Hammer-Stroud 4-point degree-3 tetrahedron quadrature.
# --------------------------------------------------------------------------

_HS_A = (5.0 + 3.0 * math.sqrt(5.0)) / 20.0
_HS_B = (5.0 - math.sqrt(5.0)) / 20.0
HS_POINTS = (
    (_HS_A, _HS_B, _HS_B, _HS_B),
    (_HS_B, _HS_A, _HS_B, _HS_B),
    (_HS_B, _HS_B, _HS_A, _HS_B),
    (_HS_B, _HS_B, _HS_B, _HS_A),
)


def quad_props(points4, density):
    """Mass properties of one uniform tet via degree-3 quadrature.

    Integrands are degree <= 2 (constant density, first and second raw
    moments), inside the rule's exactness degree.
    """
    p0, p1, p2, p3 = points4
    det = 0.0
    e1, e2, e3 = v_sub(p1, p0), v_sub(p2, p0), v_sub(p3, p0)
    cx = cross(e2, e3)
    det = sum(e1[k] * cx[k] for k in range(3))
    assert det > 0.0, "preregistered fixtures must be positively oriented"
    volume = det / 6.0
    mass = density * volume
    nodes = [tuple(lam[0] * p0[k] + lam[1] * p1[k] + lam[2] * p2[k] + lam[3] * p3[k]
                   for k in range(3)) for lam in HS_POINTS]
    first = tuple(mass * 0.25 * sum(x[a] for x in nodes) for a in range(3))
    second = [[mass * 0.25 * sum(x[a] * x[b] for x in nodes) for b in range(3)]
              for a in range(3)]
    return props_from_raw(mass, first, second, volume)


def props_from_raw(mass, first, second, volume):
    com = tuple(first[a] / mass for a in range(3))
    central = [[second[a][b] - mass * com[a] * com[b] for b in range(3)]
               for a in range(3)]
    trace = central[0][0] + central[1][1] + central[2][2]
    inertia = [[(trace if a == b else 0.0) - central[a][b] for b in range(3)]
               for a in range(3)]
    return {"mass": mass, "volume": volume, "com": com, "inertia": inertia,
            "first": first, "second": second}


def combine_raw(quad_parts):
    """Total properties by summing raw moments (independent of parallel axis)."""
    mass = sum(q["mass"] for q in quad_parts)
    first = tuple(sum(q["first"][a] for q in quad_parts) for a in range(3))
    second = [[sum(q["second"][a][b] for q in quad_parts) for b in range(3)]
              for a in range(3)]
    return props_from_raw(mass, first, second,
                          sum(q["volume"] for q in quad_parts))


# --------------------------------------------------------------------------
# Method H: hand-derived exact rationals (see preregistration documents).
# --------------------------------------------------------------------------


def h_props(mass, com, inertia_rows):
    return {"mass": F(mass), "com": tuple(F(c) for c in com),
            "inertia": [[F(v) for v in row] for row in inertia_rows]}


SI_H = {
    # Unit right tet legs +x,+y,+z from the corner, rho=12:  m=2.
    "cell-upper": h_props(2, (F(1, 4), F(1, 4), F(1, 4)),
                          [[F(3, 20), F(1, 40), F(1, 40)],
                           [F(1, 40), F(3, 20), F(1, 40)],
                           [F(1, 40), F(1, 40), F(3, 20)]]),
    # Unit right tet legs +y,+x,-z from the corner, rho=6:  m=1.
    "cell-lower": h_props(1, (F(1, 4), F(1, 4), F(-1, 4)),
                          [[F(3, 40), F(1, 80), F(-1, 80)],
                           [F(1, 80), F(3, 40), F(-1, 80)],
                           [F(-1, 80), F(-1, 80), F(3, 40)]]),
}
SI_H_TOTAL = h_props(
    3, (F(1, 4), F(1, 4), F(1, 12)),
    [[F(47, 120), F(3, 80), F(1, 80)],
     [F(3, 80), F(47, 120), F(1, 80)],
     [F(1, 80), F(1, 80), F(9, 40)]])

FC_H = {
    "fc-cell-A": h_props(2, (F(1, 4), F(1, 4), F(1, 4)),
                         [[F(3, 20), F(1, 40), F(1, 40)],
                          [F(1, 40), F(3, 20), F(1, 40)],
                          [F(1, 40), F(1, 40), F(3, 20)]]),
    # Unit right tet legs +y,+z,+x from corner (2,-1,1/2), rho=6:  m=1.
    "fc-cell-B": h_props(1, (F(9, 4), F(-3, 4), F(3, 4)),
                         [[F(3, 40), F(1, 80), F(1, 80)],
                          [F(1, 80), F(3, 40), F(1, 80)],
                          [F(1, 80), F(1, 80), F(3, 40)]]),
}
# Combined total = [I_A + m_A((d_A.d_A)E - d_A d_A^T)] + [I_B + ...] with
# d_A = COM_A - COM_total = (-2/3, 1/3, -1/6), d_B = -2 d_A (mass ratio 2:1).
# Full per-cell contributions about the total COM:
#   A: xx 77/180, yy 197/180, zz 227/180, xy 169/360, xz -71/360, yz 49/360
#   B: xx 227/360, yy 707/360, zz 827/360, xy 649/720, xz -311/720, yz 169/720
# (A draft of this table double-counted the per-cell tensors in 8 of 9 entries;
#  the preregistration cross-check below caught it before any execution.)
FC_H_TOTAL = h_props(
    3, (F(11, 12), F(-1, 12), F(5, 12)),
    [[F(127, 120), F(329, 240), F(-151, 240)],
     [F(329, 240), F(367, 120), F(89, 240)],
     [F(-151, 240), F(89, 240), F(427, 120)]])


def h_to_float(p):
    return {"mass": float(p["mass"]), "volume": None,
            "com": tuple(float(c) for c in p["com"]),
            "inertia": [[float(v) for v in row] for row in p["inertia"]]}


def combine_central(parts):
    """Combine (mass, com, inertia-about-com) parts about their total COM.

    Fraction arithmetic: exact.  Used to cross-check the hand totals.
    """
    mass = sum(p["mass"] for p in parts)
    com = tuple(sum(p["mass"] * p["com"][a] for p in parts) / mass
                for a in range(3))
    inertia = [[F(0) for _ in range(3)] for _ in range(3)]
    for p in parts:
        d = tuple(p["com"][a] - com[a] for a in range(3))
        dd = sum(d[a] * d[a] for a in range(3))
        for a in range(3):
            for b in range(3):
                inertia[a][b] += p["inertia"][a][b] + p["mass"] * (
                    (dd if a == b else F(0)) - d[a] * d[b])
    return {"mass": mass, "com": com, "inertia": inertia}


def close(a, b):
    assert abs(a - b) <= TOL, f"cross-check disagreement {a!r} vs {b!r}"


def close_props(p_float, p_ref, label):
    close(p_float["mass"], float(p_ref["mass"]))
    for a in range(3):
        close(p_float["com"][a], float(p_ref["com"][a]))
        for b in range(3):
            close(p_float["inertia"][a][b], float(p_ref["inertia"][a][b]))


def transform_props(R, t, p_ref):
    """Route 2: congruence transform of reference properties (cross-check)."""
    base = h_to_float(p_ref)
    com = m_vec(m_t(R), v_sub(base["com"], t))
    Rt = m_t(R)
    inertia = m_mul(m_mul(Rt, base["inertia"]), R)
    return {"mass": base["mass"], "com": com, "inertia": inertia}


def transform_points(R, t, points):
    """Route 1 step: x_body = R^T (x_domain - t)."""
    Rt = m_t(R)
    return [m_vec(Rt, v_sub(p, t)) for p in points]


# --------------------------------------------------------------------------
# Fixture document builders (printed verbatim into the example JSON files).
# --------------------------------------------------------------------------


def si_manifest():
    return {
        "schema_version": "chimera.fitting_manifest.v1",
        "fitting_id": "shared-interface-fit-v1",
        "domain_id": "triangular-bipyramid-shared-interface",
        "domain_revision": "si-fixture-v1",
        "coordinate_frame": {"frame_id": "si-domain", "handedness": "right",
                             "coordinate_unit": "m", "scale_to_m": 1.0},
        "vertices": [{"vertex_id": v, "position": list(p)} for v, p in SI_VERTICES],
        "cells": [{"cell_id": c, "vertex_ids": list(vs), "component_id": comp}
                  for c, vs, _reg, comp in SI_CELLS],
        "regions": [{"region_id": r, "mass_owner_id": o, "material_id": m}
                    for r, o, m in SI_REGIONS],
        "mass_authority": "reconstructed_tissue_mass",
        "source_effective_segment_ids": [],
        "matter_ownership": [
            {"matter_id": "si-matter-A", "representation": "tetrahedral_volume",
             "mass_owner_id": "si-owner-A"},
            {"matter_id": "si-matter-B", "representation": "tetrahedral_volume",
             "mass_owner_id": "si-owner-B"}],
    }


def partition_doc(vertices, cells, regions, density_by_material, frame_id):
    return {
        "schema_version": "chimera.material_partition.v1",
        "coordinate_frame": {"frame_id": frame_id, "handedness": "right",
                             "coordinate_unit": "m", "scale_to_m": 1.0},
        "vertices": [{"vertex_id": v, "position": list(p)} for v, p in vertices],
        "cells": [{"cell_id": c, "vertex_ids": list(vs), "proposals": [reg]}
                  for c, vs, reg, _comp in cells],
        "materials": [{"material_id": m,
                       "density_kg_m3": density_by_material[m],
                       "density_source": "preregistered analytic coupon fixture",
                       "conditions": "uniform"}
                      for m in sorted(density_by_material)],
        "regions": [{"region_id": r, "mass_owner_id": o, "material_id": m}
                    for r, o, m in regions],
        "mass_authority": "reconstructed_tissue_mass",
    }


def groups_doc(body_rows):
    groups = []
    for body_id, cell_ids, frame_id, rotation, origin in body_rows:
        groups.append({
            "body_id": body_id,
            "cell_ids": list(cell_ids),
            "body_frame": {
                "frame_id": frame_id,
                "handedness": "right",
                "coordinate_unit": "m",
                "domain_from_body": {"rotation": [list(row) for row in rotation],
                                     "origin_m": list(origin)}}})
    return {"schema_version": "chimera.rigid_body_cell_groups.v1",
            "body_groups": groups}


def fc_manifest():
    return {
        "schema_version": "chimera.fitting_manifest.v1",
        "fitting_id": "frame-composition-fit-v1",
        "domain_id": "two-tetrahedron-frame-composition",
        "domain_revision": "fc-fixture-v1",
        "coordinate_frame": {"frame_id": "fc-domain", "handedness": "right",
                             "coordinate_unit": "m", "scale_to_m": 1.0},
        "vertices": [{"vertex_id": v, "position": list(p)} for v, p in FC_VERTICES],
        "cells": [{"cell_id": c, "vertex_ids": list(vs), "component_id": comp}
                  for c, vs, _reg, comp in FC_CELLS],
        "regions": [{"region_id": r, "mass_owner_id": o, "material_id": m}
                    for r, o, m in FC_REGIONS],
        "mass_authority": "reconstructed_tissue_mass",
        "source_effective_segment_ids": [],
        "matter_ownership": [
            {"matter_id": "fc-matter-A", "representation": "tetrahedral_volume",
             "mass_owner_id": "fc-owner-A"},
            {"matter_id": "fc-matter-B", "representation": "tetrahedral_volume",
             "mass_owner_id": "fc-owner-B"}],
    }


def composed_frames():
    _check_rotation(R_DP, "R_DP")
    _check_rotation(R_PA, "R_PA")
    _check_rotation(R_PB, "R_PB")
    r_da = m_mul(R_DP, R_PA)
    t_da = tuple(m_vec(R_DP, T_PA)[i] + T_DP[i] for i in range(3))
    r_db = m_mul(R_DP, R_PB)
    t_db = tuple(m_vec(R_DP, T_PB)[i] + T_DP[i] for i in range(3))
    _check_rotation(r_da, "R_DA")
    _check_rotation(r_db, "R_DB")
    return (r_da, t_da), (r_db, t_db)


def cell_points(vertices, cell):
    table = dict(vertices)
    return [table[v] for v in cell[1]]


def interface_facts(vertices, cells):
    """Own face-adjacency computation: shared (internal) faces and areas."""
    table = dict(vertices)
    faces = {}
    for cell_id, vids, _reg, _comp in cells:
        for omit in range(4):
            key = tuple(sorted(v for i, v in enumerate(vids) if i != omit))
            faces.setdefault(key, []).append(cell_id)
    shared = [key for key, owners in faces.items() if len(owners) == 2]
    out = []
    for key in sorted(shared):
        p = [table[v] for v in key]
        area = 0.5 * math.sqrt(sum(c * c for c in cross(v_sub(p[1], p[0]),
                                                        v_sub(p[2], p[0]))))
        out.append({"face": list(key), "area_m2": area})
    return out


def main() -> int:
    failures = []

    # ---------------- shared-interface coupon cross-checks -----------------
    si_points = {"cell-upper": cell_points(SI_VERTICES, SI_CELLS[0]),
                 "cell-lower": cell_points(SI_VERTICES, SI_CELLS[1])}
    si_density = {"cell-upper": 12.0, "cell-lower": 6.0}
    si_quad = {cid: quad_props(pts, si_density[cid]) for cid, pts in si_points.items()}
    for cid in ("cell-upper", "cell-lower"):
        try:
            close_props(si_quad[cid], SI_H[cid], f"SI {cid}")
        except AssertionError as error:
            failures.append(str(error))
    # Combined total: exact parallel-axis recombination of the hand parts.
    combined_h = combine_central([SI_H["cell-upper"], SI_H["cell-lower"]])
    for a in range(3):
        if combined_h["com"][a] != SI_H_TOTAL["com"][a]:
            failures.append("SI combined COM mismatch in hand arithmetic")
        for b in range(3):
            if combined_h["inertia"][a][b] != SI_H_TOTAL["inertia"][a][b]:
                failures.append("SI combined inertia mismatch in hand arithmetic")
    # Third method guard: raw-moment quadrature total vs the hand total.
    try:
        close_props(combine_raw([si_quad["cell-upper"], si_quad["cell-lower"]]),
                    SI_H_TOTAL, "SI combined quadrature")
    except AssertionError as error:
        failures.append(str(error))
    si_faces = interface_facts(SI_VERTICES, SI_CELLS)

    # ---------------- frame-composition coupon cross-checks ----------------
    (r_da, t_da), (r_db, t_db) = composed_frames()
    fc_points_domain = {"fc-cell-A": cell_points(FC_VERTICES, FC_CELLS[0]),
                        "fc-cell-B": cell_points(FC_VERTICES, FC_CELLS[1])}
    fc_density = {"fc-cell-A": 12.0, "fc-cell-B": 6.0}
    fc_quad = {cid: quad_props(pts, fc_density[cid])
               for cid, pts in fc_points_domain.items()}
    for cid in ("fc-cell-A", "fc-cell-B"):
        try:
            close_props(fc_quad[cid], FC_H[cid], f"FC {cid} domain")
        except AssertionError as error:
            failures.append(str(error))
    combined_fc = combine_central([FC_H["fc-cell-A"], FC_H["fc-cell-B"]])
    for a in range(3):
        if combined_fc["com"][a] != FC_H_TOTAL["com"][a]:
            failures.append("FC combined COM mismatch in hand arithmetic")
        for b in range(3):
            if combined_fc["inertia"][a][b] != FC_H_TOTAL["inertia"][a][b]:
                failures.append("FC combined inertia mismatch in hand arithmetic")
    try:
        close_props(combine_raw([fc_quad["fc-cell-A"], fc_quad["fc-cell-B"]]),
                    FC_H_TOTAL, "FC combined quadrature")
    except AssertionError as error:
        failures.append(str(error))

    # Frozen expectations: route 1 (vertex transform + quadrature), then
    # cross-checked against route 2 (congruence of hand rationals).
    run_shared = {"fc-body-A": ("fc-cell-A", R_DP, T_DP),
                  "fc-body-B": ("fc-cell-B", R_DP, T_DP)}
    run_composed = {"fc-body-A": ("fc-cell-A", r_da, t_da),
                    "fc-body-B": ("fc-cell-B", r_db, t_db)}
    frozen = {}
    for run_name, run in (("shared_parent_frame", run_shared),
                          ("composed_body_frames", run_composed)):
        frozen[run_name] = {}
        for body_id, (cell_id, rot, origin) in run.items():
            points = transform_points(rot, origin, fc_points_domain[cell_id])
            route1 = quad_props(points, fc_density[cell_id])
            route2 = transform_props(rot, origin, FC_H[cell_id])
            label = f"FC {run_name} {body_id}"
            try:
                close_props(route1, route2, label)
            except AssertionError as error:
                failures.append(str(error))
            frozen[run_name][body_id] = route1

    # ---------------- design gates ---------------------------------------
    def all_off_diagonals(tensors):
        values = []
        for rows in tensors:
            for a in range(3):
                for b in range(3):
                    if a != b:
                        values.append(abs(rows[a][b]))
        return values

    gate_tensors = [SI_H["cell-upper"]["inertia"], SI_H["cell-lower"]["inertia"],
                    SI_H_TOTAL["inertia"]]
    for run in frozen.values():
        for body in run.values():
            gate_tensors.append(body["inertia"])
    smallest = min(all_off_diagonals(gate_tensors))
    if not smallest > T_PROTECTED:
        failures.append(f"design gate: smallest protected off-diagonal {smallest} "
                        f"is not above T_PROTECTED={T_PROTECTED}")

    # ---------------- print frozen artifacts ------------------------------
    def dump(label, value):
        print(f"----- {label}")
        print(json.dumps(value, indent=2, sort_keys=True))
        print()

    def props_json(p):
        fl = h_to_float(p)
        return {"mass_kg": fl["mass"],
                "com_m": list(fl["com"]),
                "inertia_kg_m2": [list(row) for row in fl["inertia"]]}

    (r_da, t_da), (r_db, t_db) = composed_frames()
    dump("FIXTURE si_manifest", si_manifest())
    dump("FIXTURE si_partition",
         partition_doc(SI_VERTICES, SI_CELLS, SI_REGIONS, SI_DENSITY, "si-domain"))
    dump("FIXTURE si_groups",
         groups_doc([("si-body-A", ("cell-upper",), "si-domain",
                      [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
                      [0.0, 0.0, 0.0]),
                     ("si-body-B", ("cell-lower",), "si-domain",
                      [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
                      [0.0, 0.0, 0.0])]))
    dump("FIXTURE fc_manifest", fc_manifest())
    dump("FIXTURE fc_partition",
         partition_doc(FC_VERTICES, FC_CELLS, FC_REGIONS, FC_DENSITY, "fc-domain"))
    dump("FIXTURE fc_groups_shared",
         groups_doc([("fc-body-A", ("fc-cell-A",), "fc-parent-P", R_DP, T_DP),
                     ("fc-body-B", ("fc-cell-B",), "fc-parent-P", R_DP, T_DP)]))
    dump("FIXTURE fc_groups_composed",
         groups_doc([("fc-body-A", ("fc-cell-A",), "fc-body-A-local", r_da, t_da),
                     ("fc-body-B", ("fc-cell-B",), "fc-body-B-local", r_db, t_db)]))
    dump("FROZEN si_expectations", {
        "si-body-A": props_json(SI_H["cell-upper"]),
        "si-body-B": props_json(SI_H["cell-lower"]),
        "combined": props_json(SI_H_TOTAL),
        "interfaces": si_faces,
    })
    dump("FROZEN fc_domain_expectations", {
        "fc-cell-A": props_json(FC_H["fc-cell-A"]),
        "fc-cell-B": props_json(FC_H["fc-cell-B"]),
        "combined": props_json(FC_H_TOTAL),
    })
    dump("FROZEN fc_run_expectations", {
        run: {body: props_json(props) for body, props in bodies.items()}
        for run, bodies in frozen.items()})
    dump("FROZEN fc_composed_matrices", {
        "R_DA": [list(row) for row in r_da], "t_DA": list(t_da),
        "R_DB": [list(row) for row in r_db], "t_DB": list(t_db)})
    dump("DESIGN_GATES", {"tolerance": TOL, "t_protected": T_PROTECTED,
                          "smallest_protected_off_diagonal": smallest})

    if failures:
        print("PREREGISTRATION CROSS-CHECK FAILURES:")
        for line in failures:
            print("  " + line)
        return 1
    print("PREREGISTRATION CROSS-CHECK OK (H == Q == R2 within 1e-12; "
          "hand totals exact)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
