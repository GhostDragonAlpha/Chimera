"""Validation-only fitting-manifest adapter for the material-volume compiler.

No Chimera runtime modules are imported and no physical state is read or
mutated. The adapter checks stable domain identities before validating the
supplied tetrahedral partition. It is deliberately not an anatomy-completeness
certifier, geometric repair tool, constitutive model, or production importer.

Run:
    python tools/material_volume_admission.py --manifest manifest.json \\
        --partition partition.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np

import material_volume as mv


MANIFEST_SCHEMA = "chimera.fitting_manifest.v1"
PARTITION_SCHEMA = "chimera.material_partition.v1"
REPORT_SCHEMA = "chimera.material_volume_admission_report.v1"
AUTHORITY_RECONSTRUCTED = "reconstructed_tissue_mass"
AUTHORITY_EFFECTIVE_SEGMENT = "source_effective_segment_mass"
AUTHORITIES = frozenset((AUTHORITY_RECONSTRUCTED, AUTHORITY_EFFECTIVE_SEGMENT))
FRAME_FIELDS = ("frame_id", "handedness", "coordinate_unit", "scale_to_m")


class AdmissionInputError(ValueError):
    def __init__(self, reason: str, detail: str):
        super().__init__(detail)
        self.reason = reason
        self.detail = detail


def _fail(reason: str, detail: str) -> None:
    raise AdmissionInputError(reason, detail)


def _object(value, label: str, required: set[str]) -> Mapping:
    if not isinstance(value, Mapping):
        _fail("bad_schema", f"{label} must be a JSON object")
    missing = sorted(required - set(value))
    extra = sorted(set(value) - required)
    if missing or extra:
        bits = []
        if missing:
            bits.append(f"missing fields {missing}")
        if extra:
            bits.append(f"unknown fields {extra}")
        _fail("bad_schema", f"{label}: {'; '.join(bits)}")
    return value


def _id(value, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        _fail("bad_identifier", f"{label} must be a non-empty string")
    return value


def _number(value, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        _fail("bad_number", f"{label} must be a finite JSON number")
    try:
        result = float(value)
    except (OverflowError, ValueError):
        _fail("nonfinite_input", f"{label} is outside the finite float64 range")
    if not math.isfinite(result):
        _fail("nonfinite_input", f"{label} must be finite")
    return result


def _string_list(value, label: str, *, unique: bool = False) -> list[str]:
    if not isinstance(value, list):
        _fail("bad_schema", f"{label} must be a JSON array")
    result = [_id(item, f"{label}[{i}]") for i, item in enumerate(value)]
    if unique and len(set(result)) != len(result):
        _fail("duplicate_identifier", f"{label} contains duplicate identifiers")
    return result


def _frame(value, label: str) -> dict:
    frame = _object(value, label, set(FRAME_FIELDS))
    frame_id = _id(frame["frame_id"], f"{label}.frame_id")
    handedness = _id(frame["handedness"], f"{label}.handedness")
    unit = _id(frame["coordinate_unit"], f"{label}.coordinate_unit")
    if handedness != "right":
        _fail("unsupported_coordinate_frame",
              f"{label}.handedness must be 'right'; no implicit reflection is allowed")
    scale = _number(frame["scale_to_m"], f"{label}.scale_to_m")
    if scale <= 0.0:
        _fail("bad_scale", f"{label}.scale_to_m must be positive")
    return {"frame_id": frame_id, "handedness": handedness,
            "coordinate_unit": unit, "scale_to_m": scale}


def _vertices(value, label: str) -> list[dict]:
    if not isinstance(value, list) or not value:
        _fail("bad_schema", f"{label} must be a non-empty JSON array")
    result = []
    seen = set()
    for i, raw in enumerate(value):
        row = _object(raw, f"{label}[{i}]", {"vertex_id", "position"})
        vertex_id = _id(row["vertex_id"], f"{label}[{i}].vertex_id")
        if vertex_id in seen:
            _fail("duplicate_vertex_id", f"{label} repeats vertex ID {vertex_id!r}")
        seen.add(vertex_id)
        position = row["position"]
        if not isinstance(position, list) or len(position) != 3:
            _fail("bad_shape", f"{label}[{i}].position must contain three coordinates")
        result.append({"vertex_id": vertex_id,
                       "position": tuple(_number(x, f"{label}[{i}].position")
                                         for x in position)})
    return result


def _regions(value, label: str) -> list[dict]:
    if not isinstance(value, list) or not value:
        _fail("bad_schema", f"{label} must be a non-empty JSON array")
    result = []
    seen = set()
    for i, raw in enumerate(value):
        row = _object(raw, f"{label}[{i}]",
                      {"region_id", "mass_owner_id", "material_id"})
        region_id = _id(row["region_id"], f"{label}[{i}].region_id")
        if region_id in seen:
            _fail("duplicate_region_id", f"{label} repeats region ID {region_id!r}")
        seen.add(region_id)
        result.append({"region_id": region_id,
                       "mass_owner_id": _id(row["mass_owner_id"],
                                             f"{label}[{i}].mass_owner_id"),
                       "material_id": _id(row["material_id"],
                                           f"{label}[{i}].material_id")})
    return result


def _materials(value) -> list[dict]:
    if not isinstance(value, list) or not value:
        _fail("bad_schema", "partition.materials must be a non-empty JSON array")
    result = []
    seen = set()
    for i, raw in enumerate(value):
        row = _object(raw, f"partition.materials[{i}]",
                      {"material_id", "density_kg_m3", "density_source", "conditions"})
        material_id = _id(row["material_id"], f"partition.materials[{i}].material_id")
        if material_id in seen:
            _fail("duplicate_material_id", f"partition repeats material ID {material_id!r}")
        seen.add(material_id)
        density = row["density_kg_m3"]
        if density is not None:
            density = _number(density, f"partition.materials[{i}].density_kg_m3")
        source, conditions = row["density_source"], row["conditions"]
        for field, item in (("density_source", source), ("conditions", conditions)):
            if item is not None and not isinstance(item, str):
                _fail("bad_schema", f"partition.materials[{i}].{field} must be text or null")
        result.append({"material_id": material_id, "density_kg_m3": density,
                       "density_source": source, "conditions": conditions})
    return result


def _manifest(manifest) -> dict:
    required = {"schema_version", "fitting_id", "domain_id", "domain_revision",
                "coordinate_frame", "vertices", "cells", "regions", "mass_authority",
                "source_effective_segment_ids", "matter_ownership"}
    value = _object(manifest, "manifest", required)
    if value["schema_version"] != MANIFEST_SCHEMA:
        _fail("bad_schema", f"manifest.schema_version must be {MANIFEST_SCHEMA!r}")
    authority = _id(value["mass_authority"], "manifest.mass_authority")
    if authority not in AUTHORITIES:
        _fail("bad_mass_authority", "manifest.mass_authority must explicitly select "
              "reconstructed_tissue_mass or source_effective_segment_mass")
    vertices = _vertices(value["vertices"], "manifest.vertices")
    vertex_ids = {row["vertex_id"] for row in vertices}
    if not isinstance(value["cells"], list) or not value["cells"]:
        _fail("bad_schema", "manifest.cells must be a non-empty JSON array")
    cells, cell_ids = [], set()
    for i, raw in enumerate(value["cells"]):
        row = _object(raw, f"manifest.cells[{i}]", {"cell_id", "vertex_ids", "component_id"})
        cell_id = _id(row["cell_id"], f"manifest.cells[{i}].cell_id")
        if cell_id in cell_ids:
            _fail("duplicate_cell_id", f"manifest repeats cell ID {cell_id!r}")
        cell_ids.add(cell_id)
        ids = _string_list(row["vertex_ids"], f"manifest.cells[{i}].vertex_ids", unique=True)
        if len(ids) != 4:
            _fail("bad_shape", f"manifest.cells[{i}].vertex_ids must contain four IDs")
        unknown = sorted(set(ids) - vertex_ids)
        if unknown:
            _fail("unknown_vertex_id", f"manifest cell {cell_id!r} references {unknown}")
        cells.append({"cell_id": cell_id, "vertex_ids": ids,
                      "component_id": _id(row["component_id"],
                                            f"manifest.cells[{i}].component_id")})
    used_vertices = {vertex_id for cell in cells for vertex_id in cell["vertex_ids"]}
    if used_vertices != vertex_ids:
        _fail("unused_manifest_vertex", "manifest vertices must be used by at least one expected cell")
    regions = _regions(value["regions"], "manifest.regions")
    source_ids = _string_list(value["source_effective_segment_ids"],
                              "manifest.source_effective_segment_ids", unique=True)
    if authority == AUTHORITY_RECONSTRUCTED and source_ids:
        _fail("mixed_mass_authority", "reconstructed_tissue_mass requires an empty "
              "source_effective_segment_ids list")
    if authority == AUTHORITY_EFFECTIVE_SEGMENT and not source_ids:
        _fail("missing_segment_authority", "source_effective_segment_mass requires at least "
              "one opaque source segment ID")
    if not isinstance(value["matter_ownership"], list):
        _fail("bad_schema", "manifest.matter_ownership must be a JSON array")
    ownership = []
    for i, raw in enumerate(value["matter_ownership"]):
        row = _object(raw, f"manifest.matter_ownership[{i}]",
                      {"matter_id", "representation", "mass_owner_id"})
        representation = _id(row["representation"],
                              f"manifest.matter_ownership[{i}].representation")
        supported = {"tetrahedral_volume", "surface_mass_overlay",
                     "source_effective_segment"}
        if representation not in supported:
            _fail("bad_matter_representation",
                  f"manifest.matter_ownership[{i}].representation is unsupported")
        ownership.append({"matter_id": _id(row["matter_id"],
                                            f"manifest.matter_ownership[{i}].matter_id"),
                          "representation": representation,
                          "mass_owner_id": _id(row["mass_owner_id"],
                                                f"manifest.matter_ownership[{i}].mass_owner_id")})
    return {"fitting_id": _id(value["fitting_id"], "manifest.fitting_id"),
            "domain_id": _id(value["domain_id"], "manifest.domain_id"),
            "domain_revision": _id(value["domain_revision"], "manifest.domain_revision"),
            "coordinate_frame": _frame(value["coordinate_frame"], "manifest.coordinate_frame"),
            "vertices": vertices, "cells": cells, "regions": regions,
            "mass_authority": authority,
            "source_effective_segment_ids": source_ids,
            "matter_ownership": ownership}


def _partition(partition) -> dict:
    required = {"schema_version", "coordinate_frame", "vertices", "cells", "materials",
                "regions", "mass_authority"}
    value = _object(partition, "partition", required)
    if value["schema_version"] != PARTITION_SCHEMA:
        _fail("bad_schema", f"partition.schema_version must be {PARTITION_SCHEMA!r}")
    authority = _id(value["mass_authority"], "partition.mass_authority")
    if authority not in AUTHORITIES:
        _fail("bad_mass_authority", "partition.mass_authority must explicitly select "
              "reconstructed_tissue_mass or source_effective_segment_mass")
    vertices = _vertices(value["vertices"], "partition.vertices")
    vertex_ids = {row["vertex_id"] for row in vertices}
    if not isinstance(value["cells"], list) or not value["cells"]:
        _fail("bad_schema", "partition.cells must be a non-empty JSON array")
    cells, cell_ids = [], set()
    for i, raw in enumerate(value["cells"]):
        row = _object(raw, f"partition.cells[{i}]", {"cell_id", "vertex_ids", "proposals"})
        cell_id = _id(row["cell_id"], f"partition.cells[{i}].cell_id")
        if cell_id in cell_ids:
            _fail("duplicate_cell_id", f"partition repeats cell ID {cell_id!r}")
        cell_ids.add(cell_id)
        ids = _string_list(row["vertex_ids"], f"partition.cells[{i}].vertex_ids", unique=True)
        if len(ids) != 4:
            _fail("bad_shape", f"partition.cells[{i}].vertex_ids must contain four IDs")
        unknown = sorted(set(ids) - vertex_ids)
        if unknown:
            _fail("unknown_vertex_id", f"partition cell {cell_id!r} references {unknown}")
        proposals = _string_list(row["proposals"], f"partition.cells[{i}].proposals")
        cells.append({"cell_id": cell_id, "vertex_ids": ids, "proposals": proposals})
    materials = _materials(value["materials"])
    regions = _regions(value["regions"], "partition.regions")
    return {"coordinate_frame": _frame(value["coordinate_frame"], "partition.coordinate_frame"),
            "vertices": vertices, "cells": cells, "materials": materials,
            "regions": regions, "mass_authority": authority}


def _coordinate_frame_equal(a: Mapping, b: Mapping) -> bool:
    return (a["frame_id"] == b["frame_id"]
            and a["handedness"] == b["handedness"]
            and a["coordinate_unit"] == b["coordinate_unit"])


def _float_token(value: float) -> str:
    return float(value).hex()


def _geometry_signature(vertices: list[dict], cells: list[dict], scale_to_m: float) -> str:
    positions = {}
    for row in vertices:
        scaled = tuple(x * scale_to_m for x in row["position"])
        if not all(math.isfinite(x) for x in scaled):
            _fail("numeric_overflow", f"vertex {row['vertex_id']!r} overflows SI coordinates")
        positions[row["vertex_id"]] = tuple(_float_token(x) for x in scaled)
    records = sorted(tuple(sorted(positions[vertex_id] for vertex_id in cell["vertex_ids"]))
                     for cell in cells)
    payload = json.dumps(records, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def _region_comparison(expected: list[dict], supplied: list[dict]) -> dict:
    expected_by_id = {row["region_id"]: row for row in expected}
    supplied_by_id = {row["region_id"]: row for row in supplied}
    missing = sorted(set(expected_by_id) - set(supplied_by_id))
    extra = sorted(set(supplied_by_id) - set(expected_by_id))
    mismatches = sorted(rid for rid in set(expected_by_id) & set(supplied_by_id)
                        if expected_by_id[rid] != supplied_by_id[rid])
    expected_owners = [row["mass_owner_id"] for row in expected]
    supplied_owners = [row["mass_owner_id"] for row in supplied]
    duplicate_owners = sorted({owner for owners in (expected_owners, supplied_owners)
                               for owner in set(owners) if owners.count(owner) > 1})
    return {"expected_region_ids": sorted(expected_by_id),
            "supplied_region_ids": sorted(supplied_by_id),
            "missing_region_ids": missing, "extra_region_ids": extra,
            "definition_mismatch_region_ids": mismatches,
            "duplicate_mass_owner_ids": duplicate_owners,
            "region_catalog_matches": not (missing or extra or mismatches or duplicate_owners)}


def _matter_ownership_check(manifest: dict, region_comparison: dict) -> tuple[dict, list[str]]:
    claims_by_matter: dict[str, list[dict]] = {}
    for claim in manifest["matter_ownership"]:
        claims_by_matter.setdefault(claim["matter_id"], []).append(claim)
    duplicate_matter_ids = sorted(matter_id for matter_id, claims in claims_by_matter.items()
                                  if len(claims) > 1)
    volume_surface_collisions = []
    for matter_id in duplicate_matter_ids:
        representations = sorted({row["representation"] for row in claims_by_matter[matter_id]})
        if "tetrahedral_volume" in representations and "surface_mass_overlay" in representations:
            volume_surface_collisions.append(matter_id)
    owner_claim_counts: dict[str, int] = {}
    for claim in manifest["matter_ownership"]:
        owner = claim["mass_owner_id"]
        owner_claim_counts[owner] = owner_claim_counts.get(owner, 0) + 1
    duplicate_claim_owners = sorted(owner for owner, count in owner_claim_counts.items()
                                    if count > 1)
    reasons = []
    if duplicate_matter_ids:
        reasons.append("duplicate_matter_ownership")
    if volume_surface_collisions:
        reasons.append("volume_surface_ownership_collision")
    if any(row["representation"] == "surface_mass_overlay"
           for row in manifest["matter_ownership"]):
        reasons.append("unsupported_surface_mass_overlay")
    authority = manifest["mass_authority"]
    claims = manifest["matter_ownership"]
    if authority == AUTHORITY_RECONSTRUCTED:
        expected = {row["mass_owner_id"] for row in manifest["regions"]}
        represented = [row["mass_owner_id"] for row in claims
                       if row["representation"] == "tetrahedral_volume"]
        missing_owners = sorted(expected - set(represented))
        extra_owners = sorted(set(represented) - expected)
        if any(row["representation"] != "tetrahedral_volume" for row in claims):
            reasons.append("mass_authority_ownership_mismatch")
        if missing_owners or extra_owners or len(represented) != len(set(represented)):
            reasons.append("volume_owner_ledger_mismatch")
    else:
        expected = set(manifest["source_effective_segment_ids"])
        represented = [row["mass_owner_id"] for row in claims
                       if row["representation"] == "source_effective_segment"]
        missing_owners = sorted(expected - set(represented))
        extra_owners = sorted(set(represented) - expected)
        if any(row["representation"] != "source_effective_segment" for row in claims):
            reasons.append("mass_authority_ownership_mismatch")
        if missing_owners or extra_owners or len(represented) != len(set(represented)):
            reasons.append("source_segment_ledger_mismatch")
    if duplicate_claim_owners:
        reasons.append("duplicate_matter_owner_id")
    ownership = {"claims": sorted(manifest["matter_ownership"],
                                   key=lambda row: (row["matter_id"], row["representation"],
                                                    row["mass_owner_id"])),
                 "duplicate_matter_ids": duplicate_matter_ids,
                 "volume_surface_ownership_collisions": volume_surface_collisions,
                 "duplicate_mass_owner_claim_ids": duplicate_claim_owners,
                 "missing_authority_owner_ids": missing_owners,
                 "extra_authority_owner_ids": extra_owners,
                 "ownership_ledger_matches_authority": not any(reasons)}
    if region_comparison["duplicate_mass_owner_ids"]:
        reasons.append("duplicate_mass_owner_id")
        ownership["ownership_ledger_matches_authority"] = False
    return ownership, sorted(set(reasons))


def _correspondence(manifest: dict, partition: dict) -> tuple[dict, bool]:
    expected_vertices = {row["vertex_id"]: row for row in manifest["vertices"]}
    supplied_vertices = {row["vertex_id"]: row for row in partition["vertices"]}
    expected_cells = {row["cell_id"]: row for row in manifest["cells"]}
    supplied_cells = {row["cell_id"]: row for row in partition["cells"]}
    missing_vertices = sorted(set(expected_vertices) - set(supplied_vertices))
    extra_vertices = sorted(set(supplied_vertices) - set(expected_vertices))
    common_vertices = set(expected_vertices) & set(supplied_vertices)
    position_mismatches = sorted(vertex_id for vertex_id in common_vertices
        if tuple(_float_token(x) for x in expected_vertices[vertex_id]["position"])
        != tuple(_float_token(x) for x in supplied_vertices[vertex_id]["position"]))
    missing_cells = sorted(set(expected_cells) - set(supplied_cells))
    extra_cells = sorted(set(supplied_cells) - set(expected_cells))
    connectivity_mismatches = sorted(cell_id for cell_id in set(expected_cells) & set(supplied_cells)
        if set(expected_cells[cell_id]["vertex_ids"])
        != set(supplied_cells[cell_id]["vertex_ids"]))
    expected_by_component: dict[str, set[str]] = {}
    for cell in manifest["cells"]:
        expected_by_component.setdefault(cell["component_id"], set()).add(cell["cell_id"])
    represented_cells = set(expected_cells) & set(supplied_cells)
    removed_components = sorted(component_id for component_id, ids in expected_by_component.items()
                                if not ids & represented_cells)
    incomplete_components = sorted(component_id for component_id, ids in expected_by_component.items()
                                   if ids - represented_cells)
    frame_matches = _coordinate_frame_equal(manifest["coordinate_frame"],
                                            partition["coordinate_frame"])
    scale_matches = (manifest["coordinate_frame"]["scale_to_m"].hex()
                     == partition["coordinate_frame"]["scale_to_m"].hex())
    authority_matches = manifest["mass_authority"] == partition["mass_authority"]
    complete = not (missing_vertices or extra_vertices or position_mismatches
                    or missing_cells or extra_cells or connectivity_mismatches
                    or not frame_matches or not scale_matches or not authority_matches)
    return ({"expected_vertex_count": len(manifest["vertices"]),
             "supplied_vertex_count": len(partition["vertices"]),
             "missing_vertex_ids": missing_vertices, "extra_vertex_ids": extra_vertices,
             "coordinate_mismatch_vertex_ids": position_mismatches,
             "coordinate_frame_matches": frame_matches,
             "scale_to_m_matches": scale_matches,
             "expected_cell_count": len(manifest["cells"]),
             "supplied_cell_count": len(partition["cells"]),
             "missing_cell_ids": missing_cells, "extra_cell_ids": extra_cells,
             "connectivity_mismatch_cell_ids": connectivity_mismatches,
             "expected_component_ids": sorted(expected_by_component),
             "removed_component_ids": removed_components,
             "incomplete_component_ids": incomplete_components,
             "mass_authority_matches": authority_matches,
             "intended_domain_fully_represented": complete,
             "supplied_cells_accounted_for": True,
             "supplied_cell_accounting_row_count": len(partition["cells"])}), complete


def _assignment_rows(partition: dict) -> list[dict]:
    regions = {row["region_id"]: row for row in partition["regions"]}
    materials = {row["material_id"]: row for row in partition["materials"]}
    result = []
    for cell in sorted(partition["cells"], key=lambda row: row["cell_id"]):
        candidates = sorted(set(cell["proposals"]))
        owners = sorted({regions[rid]["mass_owner_id"] for rid in candidates if rid in regions})
        unknown = sorted(set(candidates) - set(regions))
        region = regions.get(candidates[0]) if len(candidates) == 1 and not unknown else None
        material = materials.get(region["material_id"]) if region else None
        density = material["density_kg_m3"] if material else None
        if unknown:
            status = "invalid_region_reference"
        elif not candidates:
            status = "unresolved"
        elif len(candidates) > 1:
            status = "conflict"
        elif region is not None and material is None:
            status = "invalid_material_reference"
        elif density is None:
            status = "missing_density"
        else:
            status = "resolved"
        result.append({"cell_id": cell["cell_id"], "status": status,
                       "candidate_region_ids": candidates,
                       "candidate_mass_owner_ids": owners,
                       "unknown_region_ids": unknown,
                       "unknown_material_id": (region["material_id"]
                                                if region and material is None else None),
                       "region_id": region["region_id"] if region else None,
                       "mass_owner_id": region["mass_owner_id"] if region else None,
                       "material_id": region["material_id"] if region else None,
                       "density_kg_m3": density if isinstance(density, (int, float)) else None,
                       "density_source": material["density_source"] if material else None,
                       "density_conditions": material["conditions"] if material else None})
    return result


def _compiler_input(partition: dict, *, include_densities: bool = True) -> tuple[
        np.ndarray, np.ndarray, list[mv.MaterialSpec], list[mv.RegionSpec],
        list[list[str]], list[str]]:
    vertex_rows = sorted(partition["vertices"], key=lambda row: row["vertex_id"])
    vertex_ids = [row["vertex_id"] for row in vertex_rows]
    vertex_index = {vertex_id: i for i, vertex_id in enumerate(vertex_ids)}
    scale = partition["coordinate_frame"]["scale_to_m"]
    vertices_m = np.asarray([[coordinate * scale for coordinate in row["position"]]
                             for row in vertex_rows], dtype=np.float64)
    cell_rows = sorted(partition["cells"], key=lambda row: row["cell_id"])
    tetrahedra = np.asarray([[vertex_index[vertex_id] for vertex_id in row["vertex_ids"]]
                             for row in cell_rows], dtype=np.int64)
    materials = []
    for row in sorted(partition["materials"], key=lambda row: row["material_id"]):
        materials.append(mv.MaterialSpec(**row) if include_densities
                         else mv.MaterialSpec(row["material_id"], None, None, None))
    regions = [mv.RegionSpec(**row) for row in sorted(partition["regions"],
                                                       key=lambda row: row["region_id"])]
    proposals = [row["proposals"] for row in cell_rows]
    cell_ids = [row["cell_id"] for row in cell_rows]
    return vertices_m, tetrahedra, materials, regions, proposals, cell_ids


def _compiled_geometry(compiled: mv.CompiledPartition, vertex_ids: list[str],
                       cell_ids: list[str]) -> dict:
    interface_rows = []
    for face in compiled.interfaces:
        oriented = [vertex_ids[index] for index in face.vertices]
        stable_key = sorted(oriented)
        interface_rows.append({"face_vertex_ids": stable_key,
                               "oriented_vertex_ids_a_to_b": oriented,
                               "region_a_id": face.region_a_id,
                               "region_b_id": face.region_b_id,
                               "mass_owner_a_id": face.mass_owner_a_id,
                               "mass_owner_b_id": face.mass_owner_b_id,
                               "material_a_id": face.material_a_id,
                               "material_b_id": face.material_b_id,
                               "area_m2": face.area_m2,
                               "normal_a_to_b": list(face.normal_a_to_b)})
    interface_rows.sort(key=lambda row: tuple(row["face_vertex_ids"]))
    boundary_rows = []
    for face in compiled.boundary_faces:
        boundary_rows.append({"face_vertex_ids": sorted(vertex_ids[index]
                                                         for index in face.face_key),
                              "oriented_vertex_ids_outward": [vertex_ids[index]
                                                              for index in face.vertices],
                              "cell_id": cell_ids[face.cell_id],
                              "region_id": face.region_id})
    boundary_rows.sort(key=lambda row: (tuple(row["face_vertex_ids"]), row["cell_id"]))
    unresolved_rows = []
    for face in compiled.unresolved_adjacencies:
        unresolved_rows.append({"face_vertex_ids": sorted(vertex_ids[index]
                                                           for index in face.face_key),
                                "cell_ids": sorted(cell_ids[index] for index in face.cell_ids),
                                "statuses": list(face.statuses)})
    unresolved_rows.sort(key=lambda row: (tuple(row["face_vertex_ids"]), tuple(row["cell_ids"])))
    return {"topology_valid": True,
            "supplied_geometry_signature": compiled.geometry_signature,
            "geometric_volume_m3": compiled.geometric_volume_m3,
            "connected_components": compiled.connected_components,
            "interfaces": interface_rows, "boundary_faces": boundary_rows,
            "unresolved_adjacencies": unresolved_rows}


def _refusal_report(reason: str, detail: str) -> dict:
    return {"schema_version": REPORT_SCHEMA,
            "decision": "refused",
            "validation_only": True,
            "physical_state_mutated": False,
            "production_wired": False,
            "reason_codes": [reason],
            "detail": detail,
            "anatomical_completeness_certified": False}


def build_admission_report(manifest: Mapping, partition: Mapping) -> dict:
    """Return a deterministic validation report; never applies physical state.

    A well-formed but incomplete partition returns ``not_admitted`` and retains
    every supplied-cell assignment. Malformed documents and compiler refusals
    return ``refused``. ``validation_only_admissible`` means only that this
    validation boundary's declared checks passed; it is not a production import.
    """
    try:
        manifest = _manifest(manifest)
        partition = _partition(partition)
    except AdmissionInputError as error:
        return _refusal_report(error.reason, error.detail)

    correspondence, domain_complete = _correspondence(manifest, partition)
    region_comparison = _region_comparison(manifest["regions"], partition["regions"])
    ownership, ownership_reasons = _matter_ownership_check(manifest, region_comparison)
    assignments = _assignment_rows(partition)
    reason_codes = set(ownership_reasons)
    if not correspondence["coordinate_frame_matches"]:
        reason_codes.add("coordinate_frame_mismatch")
    if not correspondence["scale_to_m_matches"]:
        reason_codes.add("scale_mismatch")
    if not correspondence["mass_authority_matches"]:
        reason_codes.add("mass_authority_mismatch")
    if correspondence["missing_vertex_ids"] or correspondence["extra_vertex_ids"]:
        reason_codes.add("vertex_identity_mismatch")
    if correspondence["coordinate_mismatch_vertex_ids"]:
        reason_codes.add("vertex_coordinate_mismatch")
    if correspondence["missing_cell_ids"]:
        reason_codes.add("missing_expected_cells")
    if correspondence["extra_cell_ids"]:
        reason_codes.add("extra_supplied_cells")
    if correspondence["connectivity_mismatch_cell_ids"]:
        reason_codes.add("cell_connectivity_mismatch")
    if (region_comparison["missing_region_ids"] or region_comparison["extra_region_ids"]
            or region_comparison["definition_mismatch_region_ids"]):
        reason_codes.add("region_catalog_mismatch")
    statuses = {row["status"] for row in assignments}
    if "unresolved" in statuses:
        reason_codes.add("unresolved_assignments")
    if "conflict" in statuses:
        reason_codes.add("conflicted_assignments")
    warnings = []
    if "missing_density" in statuses:
        if manifest["mass_authority"] == AUTHORITY_RECONSTRUCTED:
            reason_codes.add("missing_density")
        else:
            warnings.append("missing_density_not_used_by_source_effective_authority")
    if "invalid_region_reference" in statuses:
        reason_codes.add("unknown_region_reference")
    if "invalid_material_reference" in statuses:
        reason_codes.add("unknown_material_reference")
    if any(status in {"unresolved", "conflict", "invalid_region_reference",
                      "invalid_material_reference"}
           for status in statuses):
        reason_codes.add("incomplete_cell_ownership")

    try:
        vertices_m, tetrahedra, materials, regions, proposals, cell_ids = _compiler_input(
            partition, include_densities=manifest["mass_authority"] == AUTHORITY_RECONSTRUCTED)
        sorted_vertices = sorted(partition["vertices"], key=lambda row: row["vertex_id"])
        vertex_ids = [row["vertex_id"] for row in sorted_vertices]
        compiled = mv.compile_partition(vertices_m, tetrahedra, materials, regions,
                                        proposals, allow_missing_density=True)
        geometry = _compiled_geometry(compiled, vertex_ids, cell_ids)
        # Compiler row order is canonical cell-ID order; remap only for a
        # defensive assertion that every supplied stable identity has a row.
        if len(compiled.cells) != len(cell_ids):
            raise mv.CompileError(mv.CompilerReason.INCOMPLETE,
                                  "compiler accounting rows do not cover supplied cells")
        topology_valid = True
        compile_refusal = None
    except mv.CompileError as error:
        compiled = None
        geometry = {"topology_valid": False, "supplied_geometry_signature": None,
                    "geometric_volume_m3": None, "connected_components": None,
                    "interfaces": [], "boundary_faces": [], "unresolved_adjacencies": []}
        topology_valid = False
        compile_refusal = {"reason": error.reason, "detail": error.detail}
        reason_codes.add(f"compiler_refusal:{error.reason}")

    try:
        expected_signature = _geometry_signature(
            manifest["vertices"], manifest["cells"],
            manifest["coordinate_frame"]["scale_to_m"])
        supplied_signature = _geometry_signature(
            partition["vertices"], partition["cells"],
            partition["coordinate_frame"]["scale_to_m"])
    except AdmissionInputError as error:
        return _refusal_report(error.reason, error.detail)
    geometry["expected_geometry_signature"] = expected_signature
    geometry["supplied_geometry_signature"] = supplied_signature
    geometry["geometry_signatures_match"] = expected_signature == supplied_signature
    geometry["identity_definition"] = (
        "SHA-256 of sorted exact float64 hexadecimal SI-coordinate tetrahedra; "
        "invariant to cell order and vertex-index renumbering, sensitive to "
        "rigid transforms, scale, and subdivision; excludes stable IDs and labels")
    if not correspondence["intended_domain_fully_represented"]:
        reason_codes.add("intended_domain_mismatch")
    if not region_comparison["region_catalog_matches"]:
        reason_codes.add("region_catalog_mismatch")

    all_assignment_rows = len(assignments) == len(partition["cells"])
    resolved = sorted(row["cell_id"] for row in assignments if row["status"] == "resolved")
    unique_owner_statuses = {"resolved", "missing_density"}
    all_assignments_have_unique_owner = all(
        row["status"] in unique_owner_statuses for row in assignments)
    all_assignments_have_known_density = all(
        row["status"] == "resolved" for row in assignments)
    unresolved = sorted(row["cell_id"] for row in assignments if row["status"] == "unresolved")
    conflicted = sorted(row["cell_id"] for row in assignments if row["status"] == "conflict")
    missing_density = sorted(row["cell_id"] for row in assignments
                             if row["status"] == "missing_density")
    invalid = sorted(row["cell_id"] for row in assignments
                     if row["status"] == "invalid_region_reference")
    invalid_material = sorted(row["cell_id"] for row in assignments
                              if row["status"] == "invalid_material_reference")
    mass_properties = None
    if compiled is not None and manifest["mass_authority"] == AUTHORITY_RECONSTRUCTED \
            and compiled.complete and domain_complete and region_comparison["region_catalog_matches"] \
            and not reason_codes:
        mass_properties = asdict(compiled.mass_properties)
    decision = "validation_only_admissible" if not reason_codes and topology_valid \
        and all_assignment_rows else "not_admitted"
    if compile_refusal is not None:
        decision = "refused"
    mass_authority = {"choice": manifest["mass_authority"],
                      "source_effective_segment_ids": sorted(
                          manifest["source_effective_segment_ids"]),
                      "source_segment_payloads_consumed": False,
                      "reconstructed_mass_properties": mass_properties,
                      "reconstructed_mass_properties_emitted": mass_properties is not None}
    return {"schema_version": REPORT_SCHEMA,
            "decision": decision,
            "validation_only": True,
            "physical_state_mutated": False,
            "production_wired": False,
            "fitting_id": manifest["fitting_id"],
            "domain_id": manifest["domain_id"],
            "domain_revision": manifest["domain_revision"],
            "mass_authority": mass_authority,
            "correspondence": correspondence,
            "identity": {"expected_geometry_signature": expected_signature,
                         "supplied_geometry_signature": supplied_signature,
                         "geometry_signatures_match": expected_signature == supplied_signature,
                         "geometry_signature_definition": geometry["identity_definition"]},
            "ownership": {**ownership, **region_comparison},
            "assignments": {"supplied_cells_accounted_for": all_assignment_rows,
                            "accounting_row_count": len(assignments),
                            "all_assignments_have_unique_owner": all_assignments_have_unique_owner,
                            "all_assignments_have_known_density": all_assignments_have_known_density,
                            "resolved_cell_ids": resolved,
                            "unresolved_cell_ids": unresolved,
                            "conflicted_cell_ids": conflicted,
                            "missing_density_cell_ids": missing_density,
                            "invalid_region_reference_cell_ids": invalid,
                            "invalid_material_reference_cell_ids": invalid_material,
                            "all_assignments_resolved": len(resolved) == len(assignments)},
            "cells": assignments,
            "geometry": geometry,
            "compiler_refusal": compile_refusal,
            "reason_codes": sorted(reason_codes),
            "warning_codes": sorted(warnings),
            "anatomical_completeness_certified": False}


def canonical_json(report: Mapping) -> str:
    """Serialize a report with stable key/array order and no NaN/Infinity."""
    return json.dumps(report, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False) + "\n"


class _DuplicateJsonKey(ValueError):
    pass


def _unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise _DuplicateJsonKey(f"duplicate JSON object key {key!r}")
        value[key] = item
    return value


def _reject_json_constant(token: str):
    raise ValueError(f"non-standard JSON numeric constant {token!r}")


def _read_json(path: str) -> object:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"),
                          object_pairs_hook=_unique_object,
                          parse_constant=_reject_json_constant)
    except _DuplicateJsonKey as error:
        _fail("duplicate_json_key", str(error))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        _fail("input_read_error", f"unable to read JSON input: {type(error).__name__}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, help="fitting manifest JSON")
    parser.add_argument("--partition", required=True, help="material partition JSON")
    args = parser.parse_args(argv)
    try:
        manifest = _read_json(args.manifest)
        partition = _read_json(args.partition)
        report = build_admission_report(manifest, partition)
    except AdmissionInputError as error:
        report = _refusal_report(error.reason, error.detail)
    sys.stdout.write(canonical_json(report))
    if report["decision"] == "validation_only_admissible":
        return 0
    if report["decision"] == "refused":
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
