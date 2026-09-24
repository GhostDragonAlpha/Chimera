"""B5 subdivision coupon fixture generator.

Pure stdlib. Emits, for each subdivision level, a schema-legal
(manifest, partition, groups) triple describing ONE rigid body whose material
is the SAME box region [0,4]x[0,2]x[0,2] at uniform density 12.0 kg/m^3,
tetrahedralized by the Kuhn (Freudenthal) triangulation of its sub-box grid:

  L0: 1 box        (1x1x1 grid,  edges 4x2x2)   ->  6 tets,   8 vertices
  L1: 2x1x1 boxes  (edges 2x2x2)                -> 12 tets,  12 vertices
  L2: 4x2x2 boxes  (edges 1x1x1)                -> 96 tets,  45 vertices
  L3: 8x4x4 boxes  (edges 0.5x0.5x0.5)          -> 768 tets, 225 vertices

All coordinates are dyadic rationals (exact in float64). Every sub-box uses the
Kuhn triangulation with its main diagonal running from its min corner to its
max corner; on a regular grid this makes the induced square-face diagonals
agree across neighbors (conforming complex). The generator self-checks, with
exact Fraction arithmetic:
  (a) every tet has strictly positive orientation,
  (b) every internal face is shared by exactly two tets with opposite cyclic
      orientation and every boundary face by exactly one,
  (c) the exact total signed volume equals the box volume 16 m^3.

No tool from tools/ is imported. Writes ONLY inside agents/B5_subdivision/.
"""
from __future__ import annotations

import json
import os
from fractions import Fraction
from itertools import permutations

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.normpath(os.path.join(HERE, "..", "fixtures"))

BOX_MIN = (Fraction(0), Fraction(0), Fraction(0))
BOX_MAX = (Fraction(4), Fraction(2), Fraction(2))
DENSITY = Fraction(12)
# Analytic box values the generated complex must integrate to EXACTLY.
ANALYTIC_VOLUME = Fraction(16)          # m^3
ANALYTIC_MASS = DENSITY * ANALYTIC_VOLUME  # 192 kg

LEVELS = {
    "L0": (1, 1, 1),
    "L1": (2, 1, 1),
    "L2": (4, 2, 2),
    "L3": (8, 4, 4),
}


def kuhn_tets_of_box(min_corner, sizes):
    """Six positively oriented Kuhn tets of one rectangular box (Fraction coords)."""
    tets = []
    for perm in permutations(range(3)):
        corners = [
            tuple(min_corner[a] for a in range(3)),
            tuple(min_corner[a] + (sizes[a] if a == perm[0] else 0) for a in range(3)),
            tuple(min_corner[a] + (sizes[a] if a in (perm[0], perm[1]) else 0)
                  for a in range(3)),
            tuple(min_corner[a] + sizes[a] for a in range(3)),
        ]
        det = _det4(corners)
        if det < 0:
            corners = [corners[1], corners[0], corners[2], corners[3]]
            det = -det
        if det <= 0:
            raise AssertionError("non-positive-volume Kuhn tet generated")
        tets.append(corners)
    return tets


def _det4(corners):
    (x0, y0, z0), (x1, y1, z1), (x2, y2, z2), (x3, y3, z3) = corners
    return ((x1 - x0) * ((y2 - y0) * (z3 - z0) - (z2 - z0) * (y3 - y0))
            - (y1 - y0) * ((x2 - x0) * (z3 - z0) - (z2 - z0) * (x3 - x0))
            + (z1 - z0) * ((x2 - x0) * (y3 - y0) - (y2 - y0) * (x3 - x0)))


def _cyclic(triple):
    return (tuple(triple), tuple(triple[1:] + triple[:1]), tuple(triple[2:] + triple[:2]))


def _cyclic_reverse(a, b):
    """True iff oriented triple b is an ODD permutation of a (opposite orientation)."""
    return tuple(b) in _cyclic(tuple(reversed(a)))


def build_level(nx, ny, nz):
    sizes = tuple((BOX_MAX[a] - BOX_MIN[a]) / n for a, n in zip(range(3), (nx, ny, nz)))
    dx, dy, dz = sizes
    verts = {}
    def vid(i, j, k):
        return f"v{i}_{j}_{k}"
    def vpos(i, j, k):
        return (BOX_MIN[0] + i * dx, BOX_MIN[1] + j * dy, BOX_MIN[2] + k * dz)

    tets = []
    for i in range(nx):
        for j in range(ny):
            for k in range(nz):
                min_corner = (BOX_MIN[0] + i * dx, BOX_MIN[1] + j * dy, BOX_MIN[2] + k * dz)
                for corners in kuhn_tets_of_box(min_corner, sizes):
                    tets.append([(vid(*_index_of(pos, dx, dy, dz)), pos) for pos in corners])
    # register every used vertex
    for tet in tets:
        for name, pos in tet:
            verts[name] = pos
    return sizes, verts, tets


def _index_of(pos, dx, dy, dz):
    return (int(round((pos[0] - BOX_MIN[0]) / dx)),
            int(round((pos[1] - BOX_MIN[1]) / dy)),
            int(round((pos[2] - BOX_MIN[2]) / dz)))


def fnum(value: Fraction) -> float:
    out = float(value)
    assert Fraction(out) == value, f"{value} is not exactly representable"
    return out


def selfcheck(verts, tets):
    """Exact-arithmetic structural self-checks (a),(b),(c) from the module doc."""
    total = Fraction(0)
    for tet in tets:
        corners = [pos for _, pos in tet]
        det = _det4(corners)
        assert det > 0, "negative-volume cell in generated complex"
        total += det / 6
    assert total == ANALYTIC_VOLUME, f"exact volume {total} != {ANALYTIC_VOLUME}"
    faces = {}
    for ci, tet in enumerate(tets):
        ids = [name for name, _ in tet]
        pos = {name: pos for name, pos in tet}
        fortrip = [(0, 1, 2), (0, 3, 1), (1, 3, 2), (2, 3, 0)]
        for a, b, c in fortrip:
            key = tuple(sorted((ids[a], ids[b], ids[c])))
            faces.setdefault(key, []).append((ci, (ids[a], ids[b], ids[c])))
    for key, users in faces.items():
        if len(users) == 2:
            assert _cyclic_reverse(users[0][1], users[1][1]), \
                f"face {key} not oppositely oriented"
        else:
            assert len(users) == 1, f"face {key} used {len(users)} times (non-manifold)"
    return len(faces)


def main():
    os.makedirs(FIX, exist_ok=True)
    lines = []
    for level, (nx, ny, nz) in sorted(LEVELS.items()):
        sizes, verts, tets = build_level(nx, ny, nz)
        n_faces = selfcheck(verts, tets)

        cell_ids = [f"t{idx:05d}" for idx in range(len(tets))]
        vertex_rows = [{"vertex_id": name,
                        "position": [fnum(c) for c in pos]}
                       for name, pos in sorted(verts.items())]
        partition = {
            "schema_version": "chimera.material_partition.v1",
            "coordinate_frame": {"frame_id": "b5-subdiv-domain", "handedness": "right",
                                 "coordinate_unit": "m", "scale_to_m": 1.0},
            "vertices": vertex_rows,
            "cells": [{"cell_id": cid,
                       "vertex_ids": [name for name, _ in tet],
                       "proposals": ["subdiv-region"]}
                      for cid, tet in zip(cell_ids, tets)],
            "materials": [{"material_id": "tissue-uniform", "density_kg_m3": 12.0,
                           "density_source": "B5 subdivision coupon fixture",
                           "conditions": "uniform"}],
            "regions": [{"region_id": "subdiv-region", "mass_owner_id": "subdiv-owner",
                         "material_id": "tissue-uniform"}],
            "mass_authority": "reconstructed_tissue_mass",
        }
        manifest = {
            "schema_version": "chimera.fitting_manifest.v1",
            "fitting_id": f"b5-subdivision-fit-{level.lower()}-v1",
            "domain_id": "b5-box-coupon",
            "domain_revision": "box-0-4-x-0-2-x-0-2-v1",
            "coordinate_frame": partition["coordinate_frame"],
            "vertices": vertex_rows,
            "cells": [{"cell_id": cid, "vertex_ids": [name for name, _ in tet],
                       "component_id": "component-subdiv"}
                      for cid, tet in zip(cell_ids, tets)],
            "regions": partition["regions"],
            "mass_authority": "reconstructed_tissue_mass",
            "source_effective_segment_ids": [],
            "matter_ownership": [{"matter_id": "subdiv-matter",
                                  "representation": "tetrahedral_volume",
                                  "mass_owner_id": "subdiv-owner"}],
        }
        groups = {
            "schema_version": "chimera.rigid_body_cell_groups.v1",
            "body_groups": [{
                "body_id": "subdiv-body",
                "cell_ids": cell_ids,
                "body_frame": {"frame_id": "subdiv-frame-authored", "handedness": "right",
                               "coordinate_unit": "m",
                               "domain_from_body": {
                                   "rotation": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0],
                                                [0.0, 0.0, 1.0]],
                                   "origin_m": [0.0, 0.0, 0.0]}},
            }],
        }
        for name, doc in (("manifest", manifest), ("partition", partition), ("groups", groups)):
            path = os.path.join(FIX, f"{level.lower()}_{name}.json")
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                json.dump(doc, fh, indent=1, ensure_ascii=True)
                fh.write("\n")
        edge = float(sizes[0])
        lines.append(f"{level}: grid {nx}x{ny}x{nz} edges {sizes} -> {len(tets)} tets, "
                     f"{len(verts)} vertices, {n_faces} distinct faces "
                     f"(exact Volume={ANALYTIC_VOLUME}, Mass={ANALYTIC_MASS}) OK")
    log = os.path.join(HERE, "gen_fixtures_log.txt")
    with open(log, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
