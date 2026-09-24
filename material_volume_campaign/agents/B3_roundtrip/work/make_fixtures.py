"""B3 fixture realization — run AFTER the PREREG freeze (receipt 00).

Writes ONLY inside agents/B3_roundtrip/fixtures/. Canonical JSON bytes (sorted
keys, compact separators, LF) so fixture identity is canonical per B4's law.
The rotation in F1 body-R is trig-generated: R = Rz(37 deg) @ Rx(23 deg).
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

B3 = Path(__file__).resolve().parent.parent
FIX = B3 / "fixtures"
TOOLS = B3.parents[2] / "tools"


def canon(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False) + "\n"


def write(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(canon(obj))


def rotation_z(deg: float):
    t = math.radians(deg)
    c, s = math.cos(t), math.sin(t)
    return [[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]]


def rotation_x(deg: float):
    t = math.radians(deg)
    c, s = math.cos(t), math.sin(t)
    return [[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]]


def matmul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)]
            for i in range(3)]


def build_rotcoupon() -> None:
    frame = {"frame_id": "rotcoupon-domain", "handedness": "right",
             "coordinate_unit": "m", "scale_to_m": 1.0}
    vertices = [
        {"vertex_id": "p0", "position": [0.0, 0.0, 0.0]},
        {"vertex_id": "p1", "position": [2.0, 0.0, 0.0]},
        {"vertex_id": "p2", "position": [0.0, 1.0, 0.0]},
        {"vertex_id": "p3", "position": [0.0, 0.0, 1.0]},
        {"vertex_id": "q0", "position": [10.0, 0.0, 0.0]},
        {"vertex_id": "q1", "position": [12.0, 0.0, 0.0]},
        {"vertex_id": "q2", "position": [10.0, 1.0, 0.0]},
        {"vertex_id": "q3", "position": [10.0, 0.0, 1.0]},
    ]
    cells = [
        {"cell_id": "cell-P", "vertex_ids": ["p0", "p1", "p2", "p3"],
         "component_id": "component-P"},
        {"cell_id": "cell-Q", "vertex_ids": ["q0", "q1", "q2", "q3"],
         "component_id": "component-Q"},
    ]
    manifest = {
        "schema_version": "chimera.fitting_manifest.v1",
        "fitting_id": "b3-rotcoupon-fit-v1",
        "domain_id": "b3-rotcoupon",
        "domain_revision": "b3-rotcoupon-v1",
        "coordinate_frame": frame,
        "vertices": vertices,
        "cells": cells,
        "regions": [
            {"region_id": "region-P", "mass_owner_id": "owner-P",
             "material_id": "tissue-P"},
            {"region_id": "region-Q", "mass_owner_id": "owner-Q",
             "material_id": "tissue-Q"},
        ],
        "mass_authority": "reconstructed_tissue_mass",
        "source_effective_segment_ids": [],
        "matter_ownership": [
            {"matter_id": "b3-matter-P", "representation": "tetrahedral_volume",
             "mass_owner_id": "owner-P"},
            {"matter_id": "b3-matter-Q", "representation": "tetrahedral_volume",
             "mass_owner_id": "owner-Q"},
        ],
    }
    partition = {
        "schema_version": "chimera.material_partition.v1",
        "coordinate_frame": frame,
        "vertices": vertices,
        "cells": [
            {"cell_id": "cell-P", "vertex_ids": ["p0", "p1", "p2", "p3"],
             "proposals": ["region-P"]},
            {"cell_id": "cell-Q", "vertex_ids": ["q0", "q1", "q2", "q3"],
             "proposals": ["region-Q"]},
        ],
        "materials": [
            {"material_id": "tissue-P", "density_kg_m3": 7.5,
             "density_source": "b3 rotated-frame coupon fixture",
             "conditions": "uniform"},
            {"material_id": "tissue-Q", "density_kg_m3": 3.25,
             "density_source": "b3 rotated-frame coupon fixture",
             "conditions": "uniform"},
        ],
        "regions": [
            {"region_id": "region-P", "mass_owner_id": "owner-P",
             "material_id": "tissue-P"},
            {"region_id": "region-Q", "mass_owner_id": "owner-Q",
             "material_id": "tissue-Q"},
        ],
        "mass_authority": "reconstructed_tissue_mass",
    }
    generic = matmul(rotation_z(37.0), rotation_x(23.0))
    identity = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    groups = {
        "schema_version": "chimera.rigid_body_cell_groups.v1",
        "body_groups": [
            {"body_id": "body-R", "cell_ids": ["cell-P"],
             "body_frame": {"frame_id": "rotR-authored", "handedness": "right",
                            "coordinate_unit": "m",
                            "domain_from_body": {"rotation": generic,
                                                 "origin_m": [0.1, -0.2, 0.3]}}},
            {"body_id": "body-S", "cell_ids": ["cell-Q"],
             "body_frame": {"frame_id": "identS-authored", "handedness": "right",
                            "coordinate_unit": "m",
                            "domain_from_body": {"rotation": identity,
                                                 "origin_m": [10.0, 0.0, 0.0]}}},
        ],
    }
    root = FIX / "rotcoupon"
    write(root / "manifest.json", manifest)
    write(root / "partition.json", partition)
    write(root / "groups.json", groups)
    # Freeze receipts with the generic rotation actually written.
    with open(FIX / "rotcoupon" / "rotation_receipt.txt", "w",
              encoding="utf-8", newline="\n") as handle:
        handle.write("R = Rz(37deg) @ Rx(23deg), trig-generated floats\n")
        for row in generic:
            handle.write(repr(row) + "\n")
        resid = max(abs(sum(generic[i][k] * generic[j][k] for k in range(3))
                        - (1.0 if i == j else 0.0))
                    for i in range(3) for j in range(3))
        handle.write("orthonormality residual max|R^T R - I| = %r\n" % resid)


def copy_shipped() -> None:
    names = ["material_volume_body_export_manifest_example.json",
             "material_volume_body_export_partition_example.json",
             "material_volume_body_export_groups_example.json"]
    root = FIX / "shipped_example"
    root.mkdir(parents=True, exist_ok=True)
    import hashlib
    lines = []
    for name in names:
        data = (TOOLS / name).read_bytes()
        (root / name).write_bytes(data)
        lines.append("%s  source_sha256=%s  copy_sha256=%s  bytes=%d"
                     % (name, hashlib.sha256(data).hexdigest(),
                        hashlib.sha256((root / name).read_bytes()).hexdigest(),
                        len(data)))
    (root / "copy_receipt.txt").write_bytes(
        ("B3 byte-for-byte copies of tools/ examples (READ-ONLY source)\n"
         + "\n".join(lines) + "\n").encode("ascii"))


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    build_rotcoupon()
    copy_shipped()
    print("fixtures written under", FIX)
