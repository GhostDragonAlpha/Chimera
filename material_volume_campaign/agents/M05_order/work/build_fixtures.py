"""M05 fixture builder.

Constructs the base manifest/partition/groups triple from the EXISTING schemas
(chimera.fitting_manifest.v1, chimera.material_partition.v1,
chimera.rigid_body_cell_groups.v1) over a Kuhn-subdivided unit cube
(6 conforming positively oriented tetrahedra), validates the complex with pure
numpy geometry checks (no exporter import, no pipeline execution), derives the
five preregistered permuted variants, and writes everything with sha256s.

Writes only inside agents/M05_order/fixtures/.
"""
from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
FIX = HERE.parent / "fixtures"

SEED = 20260924  # frozen permutation seed

# --- geometry: unit cube, Kuhn subdivision (6 tets along the main diagonal) ---
VERTS = {
    "n0": (0.0, 0.0, 0.0), "n1": (1.0, 0.0, 0.0), "n2": (0.0, 1.0, 0.0),
    "n3": (0.0, 0.0, 1.0), "n4": (1.0, 1.0, 0.0), "n5": (1.0, 0.0, 1.0),
    "n6": (0.0, 1.0, 1.0), "n7": (1.0, 1.0, 1.0),
}
PATHS = [  # axis permutations; path 0 -> a -> a+b -> 7 (bitmask x=1,y=2,z=4)
    ("n0", "n1", "n4", "n7"),  # x,y,z
    ("n0", "n1", "n5", "n7"),  # x,z,y
    ("n0", "n2", "n4", "n7"),  # y,x,z
    ("n0", "n2", "n6", "n7"),  # y,z,x
    ("n0", "n3", "n5", "n7"),  # z,x,y
    ("n0", "n3", "n6", "n7"),  # z,y,x
]


def oriented(paths):
    """Return paths with positive signed volume (swap last two nodes if negative)."""
    out = []
    for p in paths:
        v = [np.asarray(VERTS[q], dtype=np.float64) for q in p]
        det = float(np.linalg.det(np.column_stack([v[1] - v[0], v[2] - v[0], v[3] - v[0]])))
        q = list(p)
        if det < 0:
            q[2], q[3] = q[3], q[2]
            det = -det
        out.append((tuple(q), det))
    return out


def face_key(tri):
    return tuple(sorted(tri))


def validate(tets):
    """Pure-geometry conformance checks (mirror of the compiler's topology claims)."""
    ids = sorted(VERTS)
    pos = np.asarray([VERTS[v] for v in ids], dtype=np.float64)
    assert np.unique(pos, axis=0).shape[0] == len(ids), "coincident node positions"
    keys = [tuple(sorted(t)) for t in tets]
    assert len(set(keys)) == len(keys), "duplicate unordered tetrahedra"
    assert all(len(set(t)) == 4 for t in tets), "repeated node within a tet"
    for t in tets:  # positive orientation (already fixed, assert)
        v = [np.asarray(VERTS[q]) for q in t]
        det = float(np.linalg.det(np.column_stack([v[1] - v[0], v[2] - v[0], v[3] - v[0]])))
        assert det > 0, f"non-positive tet {t}"
        edges = np.column_stack([v[1] - v[0], v[2] - v[0], v[3] - v[0]])
        scale = max(float(np.linalg.norm(e)) for e in
                    (v[1] - v[0], v[2] - v[0], v[3] - v[0], v[1] - v[2], v[1] - v[3], v[2] - v[3]))
        assert abs(det) / scale**3 > 64 * np.finfo(np.float64).eps, "degenerate scale gate"
    # face incidence: interior faces exactly 2 incident tets, boundary exactly 1,
    # and the two incident tets must traverse the shared face with opposite orientation
    faces = {}
    for t in tets:
        for tri in itertools.combinations(t, 3):
            faces.setdefault(face_key(tri), []).append((t, tri))
    boundary = []
    for key, inc in faces.items():
        assert len(inc) in (1, 2), f"non-manifold face {key}: {len(inc)}"
        if len(inc) == 1:
            boundary.append((key, inc[0]))
    # rigorous opposite-orientation check via outward normals (full vectors)
    for key, inc in faces.items():
        if len(inc) != 2:
            continue
        normals = []
        for t, tri in inc:
            v0, v1, v2 = (np.asarray(VERTS[q]) for q in tri)
            apex = [np.asarray(VERTS[q]) for q in t if q not in tri][0]
            n = np.cross(v1 - v0, v2 - v0)
            if float(np.dot(n, v0 - apex)) > 0:  # point away from apex = outward
                pass
            else:
                n = -n
            normals.append(n)
        assert np.allclose(normals[0], -normals[1], rtol=0.0, atol=0.0), \
            f"shared face not oppositely oriented: {key}"
    # boundary edge closure: every boundary edge on exactly two boundary triangles
    edge_count = {}
    for key, _ in boundary:
        for e in itertools.combinations(key, 2):
            edge_count[tuple(sorted(e))] = edge_count.get(tuple(sorted(e)), 0) + 1
    assert edge_count and all(c == 2 for c in edge_count.values()), "boundary not edge-closed"
    # vertex links: boundary vertices need disk links (count boundary faces per vertex == edges/2 ...)
    # minimal sound proxy: every vertex used, and interior-edge test
    used = {q for t in tets for q in t}
    assert used == set(ids), "unused nodes"
    return len(boundary)


def build_docs(tets):
    cell_regions = {  # mixed densities inside body-alpha make summation order observable
        "cell-t0": "region-d12", "cell-t1": "region-d6", "cell-t2": "region-d35",
        "cell-t3": "region-d12", "cell-t4": "region-d6", "cell-t5": "region-d35",
    }
    cell_ids = [f"cell-t{i}" for i in range(len(tets))]
    region_of = dict(zip(cell_ids, cell_regions.values()))
    frame_alpha = {"frame_id": "alpha-frame", "handedness": "right", "coordinate_unit": "m",
                   "domain_from_body": {"rotation": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0],
                                                     [0.0, 0.0, 1.0]], "origin_m": [0.0, 0.0, 0.0]}}
    frame_beta = {"frame_id": "beta-frame", "handedness": "right", "coordinate_unit": "m",
                  "domain_from_body": {"rotation": [[0.0, -1.0, 0.0], [1.0, 0.0, 0.0],
                                                    [0.0, 0.0, 1.0]], "origin_m": [1.0, 1.0, 1.0]}}
    frame_gamma = {"frame_id": "gamma-frame", "handedness": "right", "coordinate_unit": "m",
                   "domain_from_body": {"rotation": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0],
                                                     [0.0, 0.0, 1.0]], "origin_m": [0.0, 0.0, 0.0]}}
    manifest = {
        "schema_version": "chimera.fitting_manifest.v1",
        "fitting_id": "mvc-m05-order-cube-fit-v1",
        "domain_id": "mvc-m05-kuhn-cube",
        "domain_revision": "mvc-m05-cube-v1",
        "coordinate_frame": {"frame_id": "m05-domain", "handedness": "right",
                             "coordinate_unit": "m", "scale_to_m": 1.0},
        "vertices": [{"vertex_id": v, "position": list(VERTS[v])} for v in VERTS],
        "cells": [{"cell_id": cid, "vertex_ids": list(tets[i]),
                   "component_id": "cube-core"} for i, cid in enumerate(cell_ids)],
        "regions": [
            {"region_id": "region-d12", "mass_owner_id": "owner-d12", "material_id": "mat-d12"},
            {"region_id": "region-d6", "mass_owner_id": "owner-d6", "material_id": "mat-d6"},
            {"region_id": "region-d35", "mass_owner_id": "owner-d35", "material_id": "mat-d35"},
        ],
        "mass_authority": "reconstructed_tissue_mass",
        "source_effective_segment_ids": [],
        "matter_ownership": [
            {"matter_id": "matter-d12", "representation": "tetrahedral_volume",
             "mass_owner_id": "owner-d12"},
            {"matter_id": "matter-d6", "representation": "tetrahedral_volume",
             "mass_owner_id": "owner-d6"},
            {"matter_id": "matter-d35", "representation": "tetrahedral_volume",
             "mass_owner_id": "owner-d35"},
        ],
    }
    partition = {
        "schema_version": "chimera.material_partition.v1",
        "coordinate_frame": manifest["coordinate_frame"],
        "vertices": manifest["vertices"],
        "cells": [{"cell_id": cid, "vertex_ids": list(tets[i]),
                   "proposals": [region_of[cid]]} for i, cid in enumerate(cell_ids)],
        "materials": [
            {"material_id": "mat-d12", "density_kg_m3": 12.0,
             "density_source": "mvc-m05 analytic fixture", "conditions": "uniform"},
            {"material_id": "mat-d6", "density_kg_m3": 6.0,
             "density_source": "mvc-m05 analytic fixture", "conditions": "uniform"},
            {"material_id": "mat-d35", "density_kg_m3": 3.5,
             "density_source": "mvc-m05 analytic fixture", "conditions": "uniform"},
        ],
        "regions": manifest["regions"],
        "mass_authority": "reconstructed_tissue_mass",
    }
    groups = {
        "schema_version": "chimera.rigid_body_cell_groups.v1",
        "body_groups": [
            {"body_id": "body-alpha", "cell_ids": ["cell-t0", "cell-t1", "cell-t2"],
             "body_frame": frame_alpha},
            {"body_id": "body-beta", "cell_ids": ["cell-t3", "cell-t4"],
             "body_frame": frame_beta},
            {"body_id": "body-gamma", "cell_ids": ["cell-t5"],
             "body_frame": frame_gamma},
        ],
    }
    return manifest, partition, groups


def write(path: Path, doc) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(doc, indent=1, ensure_ascii=True) + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def permute(name, manifest, partition, groups):
    m = json.loads(json.dumps(manifest))
    p = json.loads(json.dumps(partition))
    g = json.loads(json.dumps(groups))
    if name == "base":
        pass
    elif name == "P1-cells-reversed":
        p["cells"] = list(reversed(p["cells"]))
    elif name == "P2-cells-shuffled":
        import random
        random.Random(SEED).shuffle(p["cells"])
    elif name == "P3-groups-reordered":
        g["body_groups"] = list(reversed(g["body_groups"]))
    elif name == "P4-group-cell-records-reversed":
        for row in g["body_groups"]:
            row["cell_ids"] = list(reversed(row["cell_ids"]))
    elif name == "P5-manifest-entries-reversed":
        m["vertices"] = list(reversed(m["vertices"]))
        m["cells"] = list(reversed(m["cells"]))
        m["regions"] = list(reversed(m["regions"]))
        m["matter_ownership"] = list(reversed(m["matter_ownership"]))
        # source_effective_segment_ids is [] in the base; reversing is a no-op (recorded)
    else:
        raise KeyError(name)
    return m, p, g


def main():
    oriented_tets = oriented(PATHS)
    tets = [q for q, _ in oriented_tets]
    n_boundary = validate(tets)
    manifest, partition, groups = build_docs(tets)
    hashes = {}
    for name in ["base", "P1-cells-reversed", "P2-cells-shuffled", "P3-groups-reordered",
                 "P4-group-cell-records-reversed", "P5-manifest-entries-reversed"]:
        m, p, g = permute(name, manifest, partition, groups)
        d = FIX / name
        hashes[name] = {
            "manifest": write(d / "manifest.json", m),
            "partition": write(d / "partition.json", p),
            "groups": write(d / "groups.json", g),
        }
    order_p2 = [row["cell_id"] for row in json.loads(
        (FIX / "P2-cells-shuffled" / "partition.json").read_text(encoding="utf-8"))["cells"]]
    print("boundary_faces:", n_boundary)
    print("tet_paths:", [list(q) for q, _ in oriented_tets])
    print("P2 cell order:", order_p2)
    print(json.dumps(hashes, indent=1))


if __name__ == "__main__":
    main()
