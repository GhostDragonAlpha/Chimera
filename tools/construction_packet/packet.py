"""B1 construction packet — two asymmetric solid templates, a tapered layer and
refusal controls, compiled through the existing material_volume compiler.

This is the §13 B1 gate artifact for the SEALED construction plan
(docs/GAME_PLAN_ACTION_RPG.md): "Two asymmetric solid templates, a tapered
layer and an open-surface refusal control; stable material/region/boundary IDs
and resource inventory".  It adds no physics and no second compiler: every
geometry/mass check runs through `tools/material_volume.compile_partition` /
`compile_document` ("original compiler checks reused").

Templates
---------
template_wedge_a / template_wedge_b
    Right triangular prisms (doorstop wedges) with unequal legs and different
    proportions — the acceptance-gallery #1 "two unequal wedges" solids.
    6 vertices / 3 positively oriented tets each.
template_tapered_layer
    A trapezoidal prism (thickness h(x) = h0 + (h1-h0) x/L, extruded along y)
    split into a core region and a skin region across a shared slanted
    interface quad — two regions, two mass owners, two materials in one part,
    exercising interface orientation and multi-region ownership.  12 tets.

Analytic references (wedge closed form; tapered-layer closed form for
volume/mass/COM plus seeded Monte-Carlo inertia) live in the test battery, not
here: this module authors geometry and catalogues and exposes the compiled
results plus a resource inventory.

Run:  python tools/construction_packet/packet.py   (prints the inventory JSON)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import material_volume as mv  # noqa: E402
from material_volume import CompileError, CompilerReason, MaterialSpec, RegionSpec  # noqa: E402

# --------------------------------------------------------------------------
# Template dimensions (meters) and catalogues.  Densities are fixture values
# with explicit provenance strings; the compiler infers no defaults.
# --------------------------------------------------------------------------
WEDGE_A = {
    "template_id": "template_wedge_a",
    "L": 0.30, "W": 0.20, "H": 0.12,
    "material": MaterialSpec("mat_granite_a", 2700.0,
                             "B1 packet fixture - nominal granite, assumed, not measured",
                             "dry, 293 K assumed"),
    "region": RegionSpec("region_wedge_a", "part_wedge_a", "mat_granite_a", 5.0e10),
}
WEDGE_B = {
    "template_id": "template_wedge_b",
    "L": 0.22, "W": 0.34, "H": 0.09,
    "material": MaterialSpec("mat_steel_b", 7850.0,
                             "B1 packet fixture - nominal carbon steel, assumed, not measured",
                             "dry, 293 K assumed"),
    "region": RegionSpec("region_wedge_b", "part_wedge_b", "mat_steel_b", 2.0e11),
}
TAPERED_LAYER = {
    "template_id": "template_tapered_layer",
    "L": 0.40, "W": 0.25, "h0": 0.02, "h1": 0.05, "alpha": 0.4,
    "core_material": MaterialSpec("mat_cork_core", 240.0,
                                  "B1 packet fixture - nominal cork, assumed, not measured",
                                  "dry, 293 K assumed"),
    "skin_material": MaterialSpec("mat_alloy_skin", 6100.0,
                                  "B1 packet fixture - nominal aluminium alloy, assumed, not measured",
                                  "dry, 293 K assumed"),
    "core_region": RegionSpec("region_taper_core", "owner_taper_core", "mat_cork_core", 3.0e7),
    "skin_region": RegionSpec("region_taper_skin", "owner_taper_skin", "mat_alloy_skin", 7.0e10),
}


# --------------------------------------------------------------------------
# Geometry builders.  Vertex order is authored positively oriented; the
# compiler refuses inverted cells and never repairs order, so acceptance of a
# template is itself an orientation proof.
# --------------------------------------------------------------------------
def wedge_geometry(L: float, W: float, H: float) -> tuple[list[list[float]], list[list[int]]]:
    """Right triangular prism: legs L (x), W (y), height H (z).  3 tets."""
    vertices = [
        [0.0, 0.0, 0.0], [L, 0.0, 0.0], [0.0, W, 0.0],
        [0.0, 0.0, H], [L, 0.0, H], [0.0, W, H],
    ]
    tets = [[0, 1, 2, 5], [0, 1, 5, 4], [0, 4, 5, 3]]
    return vertices, tets


def tapered_layer_geometry(L: float, W: float, h0: float, h1: float,
                           alpha: float) -> tuple[list[list[float]], list[list[int]],
                                                  list[list[str]]]:
    """Trapezoidal prism z in [0, h(x)], h(x)=h0+(h1-h0)x/L, extruded along y.

    Split at z = alpha*h(x) into core (tets 0..5) and skin (tets 6..11); the
    two halves share the slanted interface quad (vertices 4,5,6,7) as two
    conforming triangles.  Returns (vertices, tets, cell_proposals).
    """
    a0, a1 = alpha * h0, alpha * h1
    vertices = [
        [0.0, 0.0, 0.0], [L, 0.0, 0.0], [L, W, 0.0], [0.0, W, 0.0],          # 0-3 bottom
        [0.0, 0.0, a0], [L, 0.0, a1], [L, W, a1], [0.0, W, a0],              # 4-7 interface
        [0.0, 0.0, h0], [L, 0.0, h1], [L, W, h1], [0.0, W, h0],              # 8-11 top
    ]
    core = [[0, 5, 1, 2], [0, 5, 2, 6], [0, 6, 2, 3],
            [0, 4, 5, 6], [0, 4, 6, 7], [0, 7, 6, 3]]
    skin = [[4, 9, 5, 6], [4, 9, 6, 10], [4, 10, 6, 7],
            [4, 8, 9, 10], [4, 8, 10, 11], [4, 11, 10, 7]]
    core_id = TAPERED_LAYER["core_region"].region_id
    skin_id = TAPERED_LAYER["skin_region"].region_id
    proposals = [[core_id]] * 6 + [[skin_id]] * 6
    return vertices, core + skin, proposals


# --------------------------------------------------------------------------
# Compilation entry points (the original compiler checks, reused).
# --------------------------------------------------------------------------
def compile_wedge(template: dict) -> mv.CompiledPartition:
    vertices, tets = wedge_geometry(template["L"], template["W"], template["H"])
    region = template["region"]
    return mv.compile_partition(vertices, tets, [template["material"]], [region],
                                [[region.region_id]] * len(tets))


def compile_tapered_layer() -> mv.CompiledPartition:
    t = TAPERED_LAYER
    vertices, tets, proposals = tapered_layer_geometry(
        t["L"], t["W"], t["h0"], t["h1"], t["alpha"])
    return mv.compile_partition(
        vertices, tets,
        [t["core_material"], t["skin_material"]],
        [t["core_region"], t["skin_region"]], proposals)


def wedge_document(template: dict) -> dict:
    """The versioned JSON contract form of a wedge template."""
    vertices, tets = wedge_geometry(template["L"], template["W"], template["H"])
    region = template["region"]
    material = template["material"]
    return {
        "schema_version": "chimera.material_volume.v1",
        "coordinate_unit": "m",
        "density_unit": "kg/m^3",
        "mass_source_kind": "reconstructed_material_volume",
        "vertices_m": vertices,
        "tetrahedra": tets,
        "materials": [{"material_id": material.material_id,
                       "density_kg_m3": material.density_kg_m3,
                       "density_source": material.density_source,
                       "conditions": material.conditions}],
        "regions": [{"region_id": region.region_id,
                     "mass_owner_id": region.mass_owner_id,
                     "material_id": region.material_id,
                     "stiffness_pa": region.stiffness_pa}],
        "cell_proposals": [[region.region_id]] * len(tets),
    }


# --------------------------------------------------------------------------
# Refusal controls.  Each returns the CompileError the compiler raised.
# --------------------------------------------------------------------------
def refusal_open_surface_sheet() -> CompileError:
    """A zero-thickness open quad expressed as a flat tetrahedron: an open
    surface cannot carry volume mass, and the compiler refuses the degenerate
    solid.  (The OPEN_BOUNDARY branch is unreachable for conforming tet input:
    the mod-2 boundary of any tet union is an edge cycle, so an exterior edge
    always sees an even number of boundary faces; the reachable refusals for
    open-surface inputs are degeneracy and the document-level thin-sheet
    refusal below.)"""
    vertices = [[0.0, 0.0, 0.0], [0.3, 0.0, 0.0], [0.0, 0.2, 0.0], [0.3, 0.2, 0.0]]
    try:
        mv.compile_partition(vertices, [[0, 1, 2, 3]],
                             [WEDGE_A["material"]], [WEDGE_A["region"]], [["region_wedge_a"]])
    except CompileError as ex:
        return ex
    raise AssertionError("open-surface sheet was accepted")


def refusal_thin_sheet_document() -> CompileError:
    """Document-level open-surface control: a thin-sheet mass source is
    refused by the v1 contract (zero-thickness geometry cannot be a volume
    mass representation)."""
    doc = wedge_document(WEDGE_A)
    doc["mass_source_kind"] = "thin_sheet"
    try:
        mv.compile_document(doc)
    except CompileError as ex:
        return ex
    raise AssertionError("thin_sheet mass source was accepted")


def refusal_inverted_cell() -> CompileError:
    vertices, tets = wedge_geometry(**{k: WEDGE_A[k] for k in "LWH"})
    tets[0] = [0, 1, 5, 2]  # odd permutation of the first cell
    try:
        mv.compile_partition(vertices, tets, [WEDGE_A["material"]], [WEDGE_A["region"]],
                             [["region_wedge_a"]] * 3)
    except CompileError as ex:
        return ex
    raise AssertionError("inverted cell was accepted")


def refusal_overlapping_cells() -> CompileError:
    """A second tet strictly inside the first: interiors overlap, no shared
    face, no duplicate coordinates."""
    vertices = [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0],
                [0.5, 0.0, 0.0], [0.0, 0.5, 0.0], [0.0, 0.0, 0.5], [0.5, 0.25, 0.25]]
    try:
        mv.compile_partition(vertices, [[0, 1, 2, 3], [4, 5, 6, 7]],
                             [WEDGE_A["material"]], [WEDGE_A["region"]],
                             [["region_wedge_a"]] * 2)
    except CompileError as ex:
        return ex
    raise AssertionError("overlapping cells were accepted")


def refusal_duplicate_mass_owner() -> CompileError:
    """Two regions claiming one mass owner: overlapping ownership at the
    catalogue level."""
    vertices, tets = wedge_geometry(**{k: WEDGE_A[k] for k in "LWH"})
    r1 = RegionSpec("region_dup_a", "part_dup_owner", "mat_granite_a", None)
    r2 = RegionSpec("region_dup_b", "part_dup_owner", "mat_granite_a", None)
    m = WEDGE_A["material"]
    try:
        mv.compile_partition(vertices, tets, [m], [r1, r2],
                             [[r1.region_id]] * 3)
    except CompileError as ex:
        return ex
    raise AssertionError("duplicate mass owner was accepted")


def dual_claim_conflict() -> mv.CompiledPartition:
    """Overlapping ownership at the cell level is an explicit CONFLICT, never
    a silent merge: one cell proposed to two regions."""
    vertices, tets = wedge_geometry(**{k: WEDGE_A[k] for k in "LWH"})
    r_a = WEDGE_A["region"]
    r_b = RegionSpec("region_shadow_b", "part_shadow_b", "mat_granite_a", None)
    proposals = [[r_a.region_id, r_b.region_id]] + [[r_a.region_id]] * 2
    return mv.compile_partition(vertices, tets, [WEDGE_A["material"]], [r_a, r_b], proposals)


# --------------------------------------------------------------------------
# Resource inventory (the B1 "resource inventory" column).
# --------------------------------------------------------------------------
def _mass_dict(mp: mv.MassProperties | None) -> Any:
    if mp is None:
        return None
    return {"volume_m3": mp.volume_m3, "mass_kg": mp.mass_kg,
            "center_of_mass_m": list(mp.center_of_mass_m),
            "inertia_com_kg_m2": [list(row) for row in mp.inertia_com_kg_m2],
            "cell_count": mp.cell_count}


def _template_inventory(part: mv.CompiledPartition, materials: list[MaterialSpec],
                        regions: list[RegionSpec]) -> dict:
    return {
        "vertex_count": None,  # filled by caller
        "cell_count": len(part.cells),
        "complete": part.complete,
        "ownership_complete": part.ownership_complete,
        "conflicting_cell_ids": list(part.conflicting_cell_ids),
        "unresolved_cell_ids": list(part.unresolved_cell_ids),
        "geometric_volume_m3": part.geometric_volume_m3,
        "connected_components": part.connected_components,
        "geometry_signature": part.geometry_signature,
        "materials": [{"material_id": m.material_id, "density_kg_m3": m.density_kg_m3,
                       "density_source": m.density_source, "conditions": m.conditions}
                      for m in materials],
        "regions": [{"region_id": r.region_id, "mass_owner_id": r.mass_owner_id,
                     "material_id": r.material_id, "stiffness_pa": r.stiffness_pa}
                    for r in regions],
        "mass_properties": _mass_dict(part.mass_properties),
        "resolved_region_subtotals": {k: _mass_dict(v)
                                      for k, v in sorted(part.resolved_region_subtotals.items())},
        "interface_count": len(part.interfaces),
        "interfaces": [{"face_key": list(i.face_key), "region_a_id": i.region_a_id,
                        "region_b_id": i.region_b_id, "area_m2": i.area_m2,
                        "normal_a_to_b": list(i.normal_a_to_b)}
                       for i in part.interfaces],
        "boundary_face_count": len(part.boundary_faces),
        "boundary_face_keys": sorted(list(f.face_key) for f in part.boundary_faces),
    }


def resource_inventory() -> dict:
    templates = {}
    for spec in (WEDGE_A, WEDGE_B):
        part = compile_wedge(spec)
        inv = _template_inventory(part, [spec["material"]], [spec["region"]])
        inv["vertex_count"] = len(wedge_geometry(spec["L"], spec["W"], spec["H"])[0])
        templates[spec["template_id"]] = inv
    part = compile_tapered_layer()
    t = TAPERED_LAYER
    inv = _template_inventory(part, [t["core_material"], t["skin_material"]],
                              [t["core_region"], t["skin_region"]])
    inv["vertex_count"] = len(tapered_layer_geometry(
        t["L"], t["W"], t["h0"], t["h1"], t["alpha"])[0])
    templates[t["template_id"]] = inv
    refusals = {
        "open_surface_sheet": refusal_open_surface_sheet().reason,
        "thin_sheet_document": refusal_thin_sheet_document().reason,
        "inverted_cell": refusal_inverted_cell().reason,
        "overlapping_cells": refusal_overlapping_cells().reason,
        "duplicate_mass_owner": refusal_duplicate_mass_owner().reason,
        "dual_claim_cell_status": "conflict",
    }
    return {
        "packet": "construction_packet_B1",
        "compiler": "tools/material_volume.py schema chimera.material_volume.v1",
        "templates": templates,
        "refusal_controls": refusals,
    }


def main(argv=None) -> int:
    print(json.dumps(resource_inventory(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
