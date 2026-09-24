"""M04 rigid-covariance: deterministic fixture generation + schema validation.

Reads the FROZEN prereg_expectations.json (R, t, base vertices) and emits, for
each preregistered run, a manifest / partition / groups triple under fixtures/.
Vertices are transformed by the run's motion BEFORE writing; nothing else
changes between runs (same ids, regions, materials, densities).  Every groups
document is validated against the EXISTING tools/material_volume_body_export_schema.json
and every manifest/partition against tools/material_volume_admission_schema.json
via jsonschema.  No tools/ file is modified.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import jsonschema
import numpy as np

HERE = Path(__file__).resolve().parent
AGENTS = HERE.parent
FIXTURES = AGENTS / "fixtures"
TOOLS = Path("E:/ChimeraWork/mvc-20260924/tools")

EXPECT = json.loads((AGENTS / "prereg_expectations.json").read_text(encoding="utf-8"))
GROUPS_SCHEMA = json.loads((TOOLS / "material_volume_body_export_schema.json")
                           .read_text(encoding="utf-8"))
ADMISSION_SCHEMA = json.loads((TOOLS / "material_volume_admission_schema.json")
                              .read_text(encoding="utf-8"))

FRAME = {"frame_id": "m04-coupon-domain", "handedness": "right",
         "coordinate_unit": "m", "scale_to_m": 1.0}


def base_vertices() -> tuple[dict[str, tuple[float, float, float]], dict]:
    """Vertex positions from the frozen fixture spec, IDs positional in the
    frozen (positive-orientation) file order.  Each cell owns its own apex
    vertex (coincident at (0,0,0)); the cells are topologically disjoint,
    matching the shipped coupon example, because the material compiler refuses
    a vertex shared by three face-disconnected tetrahedra
    (non_manifold_vertex_link).  Positions are identical to the frozen spec,
    so the frozen exact expectations are unchanged."""
    spec_by_cell = {cell["cell_id"]: cell for cell in EXPECT["fixture"]["cells"]}
    names: dict[str, tuple[float, float, float]] = {}
    cell_vertex_ids: dict[str, list[str]] = {}
    for cid, cell in spec_by_cell.items():
        ids = []
        for k, pos in enumerate(cell["vertices"]):
            if k == 0:
                vid = f"apex-{cid[-1]}"
                names[vid] = tuple(pos)
                ids.append(vid)
            else:
                vid = f"{cid}_v{k}"
                names[vid] = tuple(pos)
                ids.append(vid)
        cell_vertex_ids[cid] = ids
    # compiler constraints: pairwise-distinct vertex positions, no shared
    # vertices between cells (manifold vertex links)
    assert len(set(names.values())) == len(names), "duplicate vertex positions"
    return names, cell_vertex_ids


def transform(motion: str, R: np.ndarray, t: np.ndarray, v: np.ndarray) -> list:
    if motion == "identity":
        w = v
    elif motion == "v + t":
        w = v + t
    elif motion == "R v":
        w = R @ v
    elif motion == "R v + t":
        w = R @ v + t
    else:
        raise ValueError(motion)
    return [float(x) for x in w]


def main() -> int:
    FIXTURES.mkdir(exist_ok=True)
    R = np.asarray(EXPECT["motion"]["R"], dtype=np.float64)
    t = np.asarray(EXPECT["motion"]["t_translation_m"], dtype=np.float64)
    base, cell_vertex_ids = base_vertices()
    order = ([f"apex-{c}" for c in ("x", "y", "z")]
             + [f"{cid}_v{k}" for cid in ("cell-x", "cell-y", "cell-z")
                for k in (1, 2, 3)])
    materials = [
        {"material_id": "mat-x", "density_kg_m3": 1000.0,
         "density_source": "M04 analytic rigid-covariance fixture",
         "conditions": "uniform"},
        {"material_id": "mat-y", "density_kg_m3": 800.0,
         "density_source": "M04 analytic rigid-covariance fixture",
         "conditions": "uniform"},
        {"material_id": "mat-z", "density_kg_m3": 1200.0,
         "density_source": "M04 analytic rigid-covariance fixture",
         "conditions": "uniform"},
    ]
    regions = [
        {"region_id": "region-x", "mass_owner_id": "owner-x", "material_id": "mat-x"},
        {"region_id": "region-y", "mass_owner_id": "owner-y", "material_id": "mat-y"},
        {"region_id": "region-z", "mass_owner_id": "owner-z", "material_id": "mat-z"},
    ]
    hashes = {}
    for run_id, run in EXPECT["expectations"]["runs"].items():
        positions = {vid: transform(run["motion"], R, t, np.asarray(base[vid]))
                     for vid in order}
        # every cell must stay positively oriented under the run's motion
        for cid, ids in cell_vertex_ids.items():
            p = [np.asarray(positions[vid]) for vid in ids]
            det = float(np.linalg.det(np.stack([p[1] - p[0], p[2] - p[0],
                                                p[3] - p[0]], axis=1)))
            assert det > 0.0, (run_id, cid, det)
        vertices = [{"vertex_id": vid, "position": list(positions[vid])}
                    for vid in order]
        manifest = {
            "schema_version": "chimera.fitting_manifest.v1",
            "fitting_id": "m04-rigid-covariance-fit-v1",
            "domain_id": "m04-three-tetra-asymmetric-coupon",
            "domain_revision": "m04-fixture-v1",
            "coordinate_frame": dict(FRAME),
            "vertices": vertices,
            "cells": [
                {"cell_id": cid, "vertex_ids": ids, "component_id": "component-m04"}
                for cid, ids in cell_vertex_ids.items()],
            "regions": regions,
            "mass_authority": "reconstructed_tissue_mass",
            "source_effective_segment_ids": [],
            "matter_ownership": [
                {"matter_id": f"m04-matter-{r}", "representation": "tetrahedral_volume",
                 "mass_owner_id": f"owner-{r}"} for r in ("x", "y", "z")],
        }
        partition = {
            "schema_version": "chimera.material_partition.v1",
            "coordinate_frame": dict(FRAME),
            "vertices": vertices,
            "cells": [
                {"cell_id": cid, "vertex_ids": ids, "proposals": [f"region-{cid[-1]}"]}
                for cid, ids in cell_vertex_ids.items()],
            "materials": materials,
            "regions": regions,
            "mass_authority": "reconstructed_tissue_mass",
        }
        groups = {
            "schema_version": "chimera.rigid_body_cell_groups.v1",
            "body_groups": [{
                "body_id": "m04-rigid-body",
                "cell_ids": sorted(cell_vertex_ids),
                "body_frame": {
                    "frame_id": f"m04-body-frame-{run_id}",
                    "handedness": "right",
                    "coordinate_unit": "m",
                    "domain_from_body": {
                        "rotation": run["frame"]["rotation"],
                        "origin_m": run["frame"]["origin_m"],
                    },
                },
            }],
        }
        # ---- validate against the EXISTING schemas (read-only reads of tools/)
        jsonschema.validate(groups, GROUPS_SCHEMA)
        jsonschema.validate(manifest, ADMISSION_SCHEMA)
        jsonschema.validate(partition, ADMISSION_SCHEMA)

        for kind, doc in (("manifest", manifest), ("partition", partition),
                          ("groups", groups)):
            path = FIXTURES / f"{run_id}_{kind}.json"
            path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
            hashes[f"{run_id}_{kind}.json"] = hashlib.sha256(
                path.read_bytes()).hexdigest()
    (FIXTURES / "fixture_sha256.json").write_text(
        json.dumps(hashes, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"generated + schema-validated {len(hashes)} fixture files "
          f"({len(EXPECT['expectations']['runs'])} runs x 3)")
    for key in sorted(hashes):
        print(f"  {hashes[key]}  {key}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
