"""Build the MAT2-B02 frozen coupon fixtures exactly as preregistered.

Run from anywhere: python -B build_coupons.py
Writes one manifest/partition/groups triple per coupon next to this file.
Deterministic: sorted keys, indent 1, LF, trailing newline, no timestamps.
"""
from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARTITION_SCHEMA = "chimera.material_partition.v1"
MANIFEST_SCHEMA = "chimera.fitting_manifest.v1"
GROUPS_SCHEMA = "chimera.rigid_body_cell_groups.v1"

# --- frozen geometry (PREREGISTRATION.md "Frozen fixtures") -----------------
# Realization notes (forced by the pinned validation, recorded in the receipt):
# R1: the second N cell shares its face vertices with the first by vertex ID
#     (a1,a2,a3); the prereg's b0/b1/b2 aliases carried duplicate positions,
#     which the pinned compiler refuses (duplicate_vertex_position).
# R2: each region needs a DISTINCT mass owner (pinned compiler refuses one
#     owner on two regions), and one region carries exactly one material;
#     bodies still aggregate cells across regions, so the frozen physics
#     (coordinates, densities, body composition, frames) is unchanged.

N_VERTS = {
    "a0": (0, 0, 0), "a1": (1, 0, 0), "a2": (0, 1, 0), "a3": (0, 0, 1),
    "b3": (2, 1, 1),
    "c0": (5, -3, 2), "c1": (6, -3, 2), "c2": (5, -2, 2), "c3": (5, -3, 3),
}
N_CELLS = [
    ("cell-na1", ["a0", "a1", "a2", "a3"], "region-A"),
    ("cell-na2", ["a1", "a2", "a3", "b3"], "region-A2"),
    ("cell-nb1", ["c0", "c1", "c2", "c3"], "region-B"),
]
N_REGIONS = [
    ("region-A", "owner-A", "tissue-A"),    # rho 12
    ("region-A2", "owner-A2", "tissue-B"),  # rho 7 (distinct owner label)
    ("region-B", "owner-B", "tissue-C"),    # rho 1000
]
N_MATERIALS = [
    ("tissue-A", 12.0), ("tissue-B", 7.0), ("tissue-C", 1000.0),
]
N_BODIES = [
    ("coupon-body-A", ["cell-na1", "cell-na2"], "frame-A",
     [[0.0, -1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]], [0.0, 0.0, 0.0]),
    ("coupon-body-B", ["cell-nb1"], "frame-B",
     [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]], [5.0, -3.0, 2.0]),
]
R_BIJECTION = {
    "a0": "w03", "a1": "w11", "a2": "w07", "a3": "w05",
    "b0": "w02", "b1": "w10", "b2": "w06", "b3": "w00",
    "c0": "w01", "c1": "w09", "c2": "w08", "c3": "w04",
}
R_CELL_RENAME = {"cell-na1": "cell-rz9", "cell-na2": "cell-ra0",
                 "cell-nb1": "cell-rc5"}
EVEN_PERM = [1, 0, 3, 2]  # [v0,v1,v2,v3] -> [v1,v0,v3,v2]

CUBE_VERTS = {
    "000": (0, 0, 0), "001": (0, 0, 1), "010": (0, 1, 0), "011": (0, 1, 1),
    "100": (1, 0, 0), "101": (1, 0, 1), "110": (1, 1, 0), "111": (1, 1, 1),
}
CUBE_CELLS = [
    ("cube-t1", ["000", "100", "110", "111"], "region-CA"),
    ("cube-t2", ["000", "100", "101", "111"], "region-CB"),
    ("cube-t3", ["000", "010", "110", "111"], "region-CA"),
    ("cube-t4", ["000", "010", "011", "111"], "region-CB"),
    ("cube-t5", ["000", "001", "101", "111"], "region-CC"),
    ("cube-t6", ["000", "001", "011", "111"], "region-CC"),
]
CUBE_REGIONS = [
    ("region-CA", "owner-CA", "tissue-CA"),  # rho 3
    ("region-CB", "owner-CB", "tissue-CB"),  # rho 4
    ("region-CC", "owner-CC", "tissue-CC"),  # rho 5
]
CUBE_BODIES = [
    ("cube-body-A", ["cube-t1", "cube-t3"], "frame-CA"),
    ("cube-body-B", ["cube-t2", "cube-t4"], "frame-CB"),
    ("cube-body-C", ["cube-t5", "cube-t6"], "frame-CC"),
]
IDENTITY = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]

L_BASE = (1000000, -2000000, 3000000)
L_VERTS = {
    "l0": L_BASE, "l1": (1000001, -2000000, 3000000),
    "l2": (1000000, -1999999, 3000000), "l3": (1000000, -2000000, 3000001),
}
D_VERTS = {"d0": (0, 0, 0), "d1": (1, 0, 0), "d2": (0, 1, 0),
           "d3": (0.25, 0.5, 2 ** -20)}
X_VERTS = {"x0": (0, 0, 0), "x1": (1, 0, 0), "x2": (0, 1, 0), "x3": (0, 0, 1),
           "y3": (2, 1, 1)}


def _orient(verts, cells):
    """Deterministically repair vertex-order sign: if det < 0, swap the last
    two vertex IDs (same tetrahedron, positive orientation). Returns cells
    with possibly swapped vertex_ids; asserts positivity."""
    out = []
    for cid, vids, reg in cells:
        p = [[Fraction(x) for x in verts[v]] for v in vids]
        e = [[p[i][d] - p[0][d] for d in range(3)] for i in (1, 2, 3)]
        det = (e[0][0] * (e[1][1] * e[2][2] - e[1][2] * e[2][1])
               - e[1][0] * (e[0][1] * e[2][2] - e[0][2] * e[2][1])
               + e[2][0] * (e[0][1] * e[1][2] - e[0][2] * e[1][1]))
        if det == 0:
            raise AssertionError(f"{cid}: zero volume")
        if det < 0:
            vids = list(vids)
            vids[2], vids[3] = vids[3], vids[2]
        out.append((cid, vids, reg))
    return out


def _components(cells):
    """Union-find over shared vertices -> geometric component label per cell."""
    parent = {cid: cid for cid, _v, _r in cells}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    by_vertex = {}
    for cid, vids, _reg in cells:
        for v in vids:
            other = by_vertex.setdefault(v, cid)
            if other != cid:
                a, b = find(other), find(cid)
                if a != b:
                    parent[b] = a
    labels = {}
    out = {}
    for cid, _vids, _reg in cells:
        root = find(cid)
        if root not in labels:
            labels[root] = len(labels) + 1
        out[cid] = labels[root]
    return out


def _docs(name, scale, verts, cells, regions, materials, bodies,
          frame_by_body=None, cell_rename=None):
    """Build (manifest, partition, groups) for one coupon."""
    cells = _orient(verts, cells)
    vertex_rows = [{"vertex_id": vid,
                    "position": [float(x) for x in verts[vid]]}
                   for vid in verts]
    comp = _components(cells)
    manifest_cells = [{"cell_id": cid, "vertex_ids": vids,
                       "component_id": f"component-{name}-{comp[cid]}"}
                      for cid, vids, _reg in cells]
    frame = {"frame_id": f"coupon-{name}-domain", "handedness": "right",
             "coordinate_unit": "m", "scale_to_m": scale}
    owners = sorted({owner for _r, owner, _m in regions})
    manifest = {
        "schema_version": MANIFEST_SCHEMA,
        "fitting_id": f"{name}-fit-v1",
        "domain_id": f"{name}-domain",
        "domain_revision": "b02-coupon-v1",
        "coordinate_frame": dict(frame),
        "vertices": vertex_rows,
        "cells": manifest_cells,
        "regions": [{"region_id": r, "mass_owner_id": o, "material_id": m}
                    for r, o, m in regions],
        "mass_authority": "reconstructed_tissue_mass",
        "source_effective_segment_ids": [],
        "matter_ownership": [
            {"matter_id": f"matter-{o}", "representation": "tetrahedral_volume",
             "mass_owner_id": o} for o in owners],
    }
    partition = {
        "schema_version": PARTITION_SCHEMA,
        "coordinate_frame": dict(frame),
        "vertices": vertex_rows,
        "cells": [{"cell_id": cid, "vertex_ids": vids, "proposals": [reg]}
                  for cid, vids, reg in cells],
        "materials": [{"material_id": mid, "density_kg_m3": rho,
                       "density_source": "b02 analytic coupon fixture",
                       "conditions": "uniform"}
                      for mid, rho in materials],
        "regions": [{"region_id": r, "mass_owner_id": o, "material_id": m}
                    for r, o, m in regions],
        "mass_authority": "reconstructed_tissue_mass",
    }
    groups = {"schema_version": GROUPS_SCHEMA, "body_groups": []}
    for body_id, cell_ids, frame_id, *_rest in bodies:
        rotation, origin = (frame_by_body or {}).get(
            body_id, (IDENTITY, [0.0, 0.0, 0.0]))
        if cell_rename:
            cell_ids = [cell_rename.get(c, c) for c in cell_ids]
        groups["body_groups"].append({
            "body_id": body_id, "cell_ids": sorted(cell_ids),
            "body_frame": {
                "frame_id": frame_id, "handedness": "right",
                "coordinate_unit": "m",
                "domain_from_body": {"rotation": rotation,
                                     "origin_m": origin}}})
    return manifest, partition, groups


def _write(name, docs):
    for kind, doc in zip(("manifest", "partition", "groups"), docs):
        path = HERE / f"coupon_{name}_{kind}.json"
        path.write_text(json.dumps(doc, indent=1, sort_keys=True,
                                   ensure_ascii=True) + "\n",
                        encoding="utf-8", newline="\n")


def main():
    n_frames = {"coupon-body-A": (N_BODIES[0][3], list(N_BODIES[0][4])),
                "coupon-body-B": (N_BODIES[1][3], list(N_BODIES[1][4]))}
    n_docs = _docs("n", 1.0, N_VERTS, N_CELLS, N_REGIONS, N_MATERIALS,
                   N_BODIES, n_frames)
    _write("n", n_docs)

    # Coupon U: cm-authored equivalent, scale_to_m 0.01
    u_verts = {k: tuple(100 * v for v in xyz) for k, xyz in N_VERTS.items()}
    u_docs = _docs("u", 0.01, u_verts, N_CELLS, N_REGIONS, N_MATERIALS,
                   N_BODIES, n_frames)
    _write("u", u_docs)

    # Coupons S(0.5), S(2.0), S(10.0): N coordinates, scale varies
    for s in (0.5, 2.0, 10.0):
        tag = str(s).replace(".", "_")
        _write(f"s{tag}", _docs(f"s{tag}", s, N_VERTS, N_CELLS, N_REGIONS,
                                N_MATERIALS, N_BODIES, n_frames))

    # Coupon R: reorder + renumber (even per-cell vertex permutation applied
    # first, then the frozen vertex-ID bijection; cell rows reversed)
    r_cells = []
    for cid, vids, reg in reversed(N_CELLS):
        permuted = [vids[i] for i in EVEN_PERM]
        r_cells.append((R_CELL_RENAME[cid],
                        [R_BIJECTION[v] for v in permuted], reg))
    r_verts = {R_BIJECTION[k]: v for k, v in N_VERTS.items()}
    r_regions = list(N_REGIONS)  # regions keep their IDs; only cells/vertices rename
    _write("r", _docs("r", 1.0, r_verts, r_cells, r_regions, N_MATERIALS,
                      N_BODIES, n_frames, cell_rename=R_CELL_RENAME))

    # Coupon B: blocked via missing density on tissue-B
    b_materials = [("tissue-A", 12.0), ("tissue-B", None), ("tissue-C", 1000.0)]
    _write("b", _docs("b", 1.0, N_VERTS, N_CELLS, N_REGIONS, b_materials,
                      N_BODIES, n_frames))

    # Coupon G: refused, unknown group cell
    g_docs = _docs("g", 1.0, N_VERTS, N_CELLS, N_REGIONS, N_MATERIALS,
                   N_BODIES, n_frames)
    g_docs[2]["body_groups"].append({
        "body_id": "coupon-body-ghost", "cell_ids": ["cell-ghost"],
        "body_frame": {"frame_id": "frame-ghost", "handedness": "right",
                       "coordinate_unit": "m",
                       "domain_from_body": {
                           "rotation": [row[:] for row in IDENTITY],
                           "origin_m": [0.0, 0.0, 0.0]}}})
    _write("g", g_docs)

    # Coupon F: refused, non-orthonormal body frame
    f_frames = {"coupon-body-A": ([[0.0, -1.0, 0.0], [1.0, 1.0, 0.0],
                                   [0.0, 0.0, 1.0]], [0.0, 0.0, 0.0])}
    f_docs = _docs("f", 1.0, N_VERTS, N_CELLS, N_REGIONS, N_MATERIALS,
                   N_BODIES, f_frames)
    _write("f", f_docs)

    # Coupon C: cube, 6 tets, 3 regions
    c_bodies = {}
    for body_id, _cells, frame_id in CUBE_BODIES:
        c_bodies[body_id] = (IDENTITY, [0.0, 0.0, 0.0])
    _write("c", _docs("c", 1.0, CUBE_VERTS, CUBE_CELLS, CUBE_REGIONS,
                      [("tissue-CA", 3.0), ("tissue-CB", 4.0),
                       ("tissue-CC", 5.0)], CUBE_BODIES, c_bodies))

    # Coupons L, D, X: numerical stress
    _write("l", _docs("l", 1.0, L_VERTS,
                      [("cell-l1", ["l0", "l1", "l2", "l3"], "region-L")],
                      [("region-L", "owner-L", "tissue-L")],
                      [("tissue-L", 1.25)],
                      [("stress-body-L", ["cell-l1"], "frame-L")]))
    _write("d", _docs("d", 1.0, D_VERTS,
                      [("cell-d1", ["d0", "d1", "d2", "d3"], "region-D")],
                      [("region-D", "owner-D", "tissue-D")],
                      [("tissue-D", 6.0)],
                      [("stress-body-D", ["cell-d1"], "frame-D")]))
    _write("x", _docs("x", 1.0, X_VERTS,
                      [("cell-xa", ["x0", "x1", "x2", "x3"], "region-XA"),
                       ("cell-xb", ["x1", "x2", "x3", "y3"], "region-XB")],
                      [("region-XA", "owner-XA", "tissue-XA"),
                       ("region-XB", "owner-XB", "tissue-XB")],
                      [("tissue-XA", 1e-06), ("tissue-XB", 1000000000.0)],
                      [("stress-body-X", ["cell-xa", "cell-xb"], "frame-X")]))
    print("coupons written:", len(list(HERE.glob("coupon_*.json"))))


if __name__ == "__main__":
    main()
