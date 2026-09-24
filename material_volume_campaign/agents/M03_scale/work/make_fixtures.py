"""M03 fixture generator: emits 4 manifest/partition pairs (scale varies ONLY in
coordinate_frame.scale_to_m) + one scale-independent groups file.

Coordinates are byte-identical mesh numbers at every scale. Density is SI kg/m^3
and is never scaled. Fixture spec is frozen in ../PREREG.md.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURES = HERE.parent / "fixtures"
FIXTURES.mkdir(parents=True, exist_ok=True)

SCALES = [1.0, 0.5, 2.0, 0.065]

VERTICES = [
    {"vertex_id": "a0", "position": [0.0, 0.0, 0.0]},
    {"vertex_id": "a1", "position": [1.0, 0.0, 0.0]},
    {"vertex_id": "a2", "position": [0.0, 1.0, 0.0]},
    {"vertex_id": "a3", "position": [0.0, 0.0, 1.0]},
    {"vertex_id": "b0", "position": [3.0, -2.0, 1.0]},
    {"vertex_id": "b1", "position": [3.0, -1.0, 1.0]},
    {"vertex_id": "b2", "position": [2.0, -2.0, 1.0]},
    {"vertex_id": "b3", "position": [3.0, -2.0, 2.0]},
]

CELLS = [
    {"cell_id": "cell-A", "vertex_ids": ["a0", "a1", "a2", "a3"]},
    {"cell_id": "cell-B", "vertex_ids": ["b0", "b1", "b2", "b3"]},
]

REGIONS = [
    {"region_id": "region-A", "mass_owner_id": "owner-A", "material_id": "tissue-A"},
    {"region_id": "region-B", "mass_owner_id": "owner-B", "material_id": "tissue-B"},
]

MATERIALS = [
    {"material_id": "tissue-A", "density_kg_m3": 12.0,
     "density_source": "m03 preregistered analytic fixture", "conditions": "uniform"},
    {"material_id": "tissue-B", "density_kg_m3": 6.0,
     "density_source": "m03 preregistered analytic fixture", "conditions": "uniform"},
]


def frame(scale: float) -> dict:
    return {"frame_id": "m03-mesh-frame", "handedness": "right",
            "coordinate_unit": "mesh-unit", "scale_to_m": scale}


def manifest(scale: float) -> dict:
    return {
        "schema_version": "chimera.fitting_manifest.v1",
        "fitting_id": "m03-scale-fit",
        "domain_id": "m03-two-tet-mesh",
        "domain_revision": "m03-mesh-v1",
        "coordinate_frame": frame(scale),
        "vertices": VERTICES,
        "cells": [{**cell, "component_id": f"component-{cell['cell_id'][-1]}"}
                  for cell in CELLS],
        "regions": REGIONS,
        "mass_authority": "reconstructed_tissue_mass",
        "source_effective_segment_ids": [],
        "matter_ownership": [
            {"matter_id": "m03-matter-A", "representation": "tetrahedral_volume",
             "mass_owner_id": "owner-A"},
            {"matter_id": "m03-matter-B", "representation": "tetrahedral_volume",
             "mass_owner_id": "owner-B"},
        ],
    }


def partition(scale: float) -> dict:
    return {
        "schema_version": "chimera.material_partition.v1",
        "coordinate_frame": frame(scale),
        "vertices": VERTICES,
        "cells": [{**cell, "proposals": [f"region-{cell['cell_id'][-1]}"]}
                  for cell in CELLS],
        "materials": MATERIALS,
        "regions": REGIONS,
        "mass_authority": "reconstructed_tissue_mass",
    }


GROUPS = {
    "schema_version": "chimera.rigid_body_cell_groups.v1",
    "body_groups": [
        {
            "body_id": "m03-body-A",
            "cell_ids": ["cell-A"],
            "body_frame": {
                "frame_id": "m03-frame-A",
                "handedness": "right",
                "coordinate_unit": "m",
                "domain_from_body": {
                    "rotation": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
                    "origin_m": [0.0, 0.0, 0.0],
                },
            },
        },
        {
            "body_id": "m03-body-B",
            "cell_ids": ["cell-B"],
            "body_frame": {
                "frame_id": "m03-frame-B",
                "handedness": "right",
                "coordinate_unit": "m",
                "domain_from_body": {
                    "rotation": [[0.0, -1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]],
                    "origin_m": [3.0, -2.0, 1.0],
                },
            },
        },
    ],
}


def dump(path: Path, document: dict) -> None:
    path.write_text(json.dumps(document, indent=2, ensure_ascii=True) + "\n",
                    encoding="utf-8")


def main() -> None:
    for scale in SCALES:
        tag = str(scale).replace("-", "neg").replace(".", "p")
        dump(FIXTURES / f"manifest_s{tag}.json", manifest(scale))
        dump(FIXTURES / f"partition_s{tag}.json", partition(scale))
    dump(FIXTURES / "groups.json", GROUPS)
    print(f"wrote {2 * len(SCALES) + 1} fixture files to {FIXTURES}")


if __name__ == "__main__":
    main()
