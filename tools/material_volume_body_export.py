"""Validation-gated exporter for explicitly authored rigid-body cell groups.

This module is isolated from Chimera runtime, assembly, and dynamics. It
revalidates the fitting manifest and material partition through the standalone
admission adapter, then integrates selected, uniquely owned stable cells and
expresses mass properties in authored body frames. It never infers rigid bodies
from labels/stiffness, consumes source effective-segment mass, or mutates state.

Run:
    python tools/material_volume_body_export.py \\
        --manifest tools/material_volume_body_export_manifest_example.json \\
        --partition tools/material_volume_body_export_partition_example.json \\
        --groups tools/material_volume_body_export_groups_example.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np

import material_volume_admission as admission


GROUPS_SCHEMA = "chimera.rigid_body_cell_groups.v1"
EXPORT_SCHEMA = "chimera.rigid_body_mass_export.v1"
_HASH_NAMES = ("manifest_sha256", "partition_sha256", "body_groups_sha256")


class ExportInputError(ValueError):
    def __init__(self, reason: str, detail: str):
        super().__init__(detail)
        self.reason = reason
        self.detail = detail


def _fail(reason: str, detail: str) -> None:
    raise ExportInputError(reason, detail)


def _identifier(value, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        _fail("bad_identifier", f"{label} must be a non-empty string")
    return value


def _number(value, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        _fail("bad_number", f"{label} must be a finite JSON number")
    try:
        number = float(value)
    except (OverflowError, ValueError):
        _fail("nonfinite_input", f"{label} is outside the finite float64 range")
    if not math.isfinite(number):
        _fail("nonfinite_input", f"{label} must be finite")
    return number


def _strict_object(value, label: str, expected: set[str]) -> Mapping:
    if not isinstance(value, Mapping):
        _fail("bad_schema", f"{label} must be a JSON object")
    missing = sorted(expected - set(value))
    extra = sorted(set(value) - expected)
    if missing or extra:
        bits = []
        if missing:
            bits.append(f"missing fields {missing}")
        if extra:
            bits.append(f"unknown fields {extra}")
        _fail("bad_schema", f"{label}: {'; '.join(bits)}")
    return value


def _vector3(value, label: str) -> np.ndarray:
    if not isinstance(value, list) or len(value) != 3:
        _fail("bad_shape", f"{label} must be a three-element array")
    return np.asarray([_number(x, f"{label}[{i}]") for i, x in enumerate(value)],
                      dtype=np.float64)


def _rotation3(value, label: str) -> np.ndarray:
    if not isinstance(value, list) or len(value) != 3 \
            or any(not isinstance(row, list) or len(row) != 3 for row in value):
        _fail("bad_shape", f"{label} must be a 3-by-3 array")
    matrix = np.asarray([[_number(x, f"{label}[{i}][{j}]")
                          for j, x in enumerate(row)]
                         for i, row in enumerate(value)], dtype=np.float64)
    if not np.allclose(matrix.T @ matrix, np.eye(3), rtol=0.0, atol=1e-10):
        _fail("invalid_authored_frame", f"{label} must be orthonormal; no repair is applied")
    determinant = float(np.linalg.det(matrix))
    if not math.isfinite(determinant) or abs(determinant - 1.0) > 1e-10:
        _fail("invalid_authored_frame",
              f"{label} must be a proper rotation with determinant +1")
    return matrix


def _parse_groups(document) -> list[dict]:
    root = _strict_object(document, "body-group assignments",
                          {"schema_version", "body_groups"})
    if root["schema_version"] != GROUPS_SCHEMA:
        _fail("bad_schema", f"schema_version must be {GROUPS_SCHEMA!r}")
    if not isinstance(root["body_groups"], list) or not root["body_groups"]:
        _fail("bad_schema", "body_groups must be a non-empty array")
    groups = []
    body_ids = set()
    cell_owner = {}
    for i, raw in enumerate(root["body_groups"]):
        group = _strict_object(raw, f"body_groups[{i}]",
                               {"body_id", "cell_ids", "body_frame"})
        body_id = _identifier(group["body_id"], f"body_groups[{i}].body_id")
        if body_id in body_ids:
            _fail("duplicate_body_id", f"body_id {body_id!r} is assigned more than once")
        body_ids.add(body_id)
        raw_cell_ids = group["cell_ids"]
        if not isinstance(raw_cell_ids, list) or not raw_cell_ids:
            _fail("empty_body_group", f"body {body_id!r} must explicitly own at least one cell")
        cell_ids = []
        for j, cell_id in enumerate(raw_cell_ids):
            cell_id = _identifier(cell_id, f"body_groups[{i}].cell_ids[{j}]")
            if cell_id in cell_owner:
                _fail("duplicate_cell_ownership",
                      f"cell {cell_id!r} is assigned to both body "
                      f"{cell_owner[cell_id]!r} and body {body_id!r}")
            cell_owner[cell_id] = body_id
            cell_ids.append(cell_id)
        frame = _strict_object(group["body_frame"], f"body_groups[{i}].body_frame",
                               {"frame_id", "handedness", "coordinate_unit",
                                "domain_from_body"})
        frame_id = _identifier(frame["frame_id"], f"body_groups[{i}].body_frame.frame_id")
        if frame["handedness"] != "right":
            _fail("unsupported_authored_frame", "body frames must be right-handed")
        if frame["coordinate_unit"] != "m":
            _fail("unsupported_authored_frame", "body-frame coordinates must be expressed in m")
        transform = _strict_object(frame["domain_from_body"],
                                   f"body_groups[{i}].body_frame.domain_from_body",
                                   {"rotation", "origin_m"})
        rotation = _rotation3(transform["rotation"],
                              f"body_groups[{i}].body_frame.domain_from_body.rotation")
        origin = _vector3(transform["origin_m"],
                          f"body_groups[{i}].body_frame.domain_from_body.origin_m")
        groups.append({"body_id": body_id, "cell_ids": sorted(cell_ids),
                       "body_frame": {"frame_id": frame_id, "handedness": "right",
                                      "coordinate_unit": "m",
                                      "domain_from_body": {
                                          "rotation": rotation.tolist(),
                                          "origin_m": origin.tolist()}}})
    return sorted(groups, key=lambda row: row["body_id"])


def _canonical_hash(document) -> str | None:
    try:
        serialized = json.dumps(document, sort_keys=True, separators=(",", ":"),
                                ensure_ascii=True, allow_nan=False)
    except (TypeError, ValueError, OverflowError):
        return None
    return hashlib.sha256(serialized.encode("ascii")).hexdigest()


def _hashes(manifest, partition, group_document) -> dict:
    values = (_canonical_hash(manifest), _canonical_hash(partition),
              _canonical_hash(group_document))
    return {"algorithm": "sha256",
            "serialization": "UTF-8 canonical JSON (sorted object keys; array order preserved)",
            **dict(zip(_HASH_NAMES, values))}


def _cell_input_index(partition: Mapping) -> dict:
    vertex_rows = partition.get("vertices", [])
    cell_rows = partition.get("cells", [])
    if not isinstance(vertex_rows, list) or not isinstance(cell_rows, list):
        return {}
    vertices = {}
    for row in vertex_rows:
        if isinstance(row, Mapping) and isinstance(row.get("vertex_id"), str):
            vertices[row["vertex_id"]] = row.get("position")
    result = {}
    for row in cell_rows:
        if isinstance(row, Mapping) and isinstance(row.get("cell_id"), str):
            result[row["cell_id"]] = {"vertex_ids": row.get("vertex_ids"),
                                      "proposals": row.get("proposals"),
                                      "positions": [vertices.get(v) for v in row.get("vertex_ids", [])]
                                      if isinstance(row.get("vertex_ids"), list) else []}
    return result


def _input_refusal(reason: str, detail: str, hashes: dict, admission_report: dict | None,
                   unassigned: list[str] | None = None) -> dict:
    return {"schema_version": EXPORT_SCHEMA,
            "export_status": "refused",
            "validation_only": True,
            "dynamics_readiness_claimed": False,
            "physical_state_mutated": False,
            "production_wired": False,
            "admission_status": (admission_report.get("decision")
                                 if isinstance(admission_report, Mapping) else "not_evaluated"),
            "admission_report_sha256": (_canonical_hash(admission_report)
                                         if admission_report is not None else None),
            "input_hashes": hashes,
            "body_groups": [],
            "unassigned_cell_ids": unassigned or [],
            "unassigned_cells": [],
            "reason_codes": [reason],
            "detail": detail,
            "surface_mass_overlay_generated": False,
            "anatomical_completeness_certified": False}


def _blocked_group(group: dict, admission_decision: str,
                   blocking_rows: list[dict], reason: str,
                   input_hashes: dict, admission_reason_codes: list[str]) -> dict:
    return {"body_id": group["body_id"],
            "owned_cell_ids": group["cell_ids"],
            "body_frame": group["body_frame"],
            "export_status": "not_exported",
            "admission_status": admission_decision,
            "admission_report_sha256": _canonical_hash({"reason_codes": admission_reason_codes,
                                                         "decision": admission_decision}),
            "input_hashes": input_hashes,
            "admission_reason_codes": sorted(admission_reason_codes),
            "blocking_cell_ids": sorted(row["cell_id"] for row in blocking_rows),
            "blocking_assignment_statuses": [
                {"cell_id": row["cell_id"], "status": row["status"]}
                for row in sorted(blocking_rows, key=lambda row: row["cell_id"])],
            "reason_codes": [reason],
            "mass_properties": None}


def _integrate_cells(vertices_m: np.ndarray, cells: list[dict]) -> dict:
    """Integrate homogeneous tetrahedra and preserve the full COM inertia tensor."""
    if not cells:
        _fail("empty_body_group", "cannot integrate an empty body group")
    positions = {row["vertex_id"]: np.asarray(row["position"], dtype=np.float64)
                 for row in vertices_m}
    tets = np.asarray([[positions[v] for v in cell["vertex_ids"]] for cell in cells],
                       dtype=np.float64)
    densities = np.asarray([cell["density_kg_m3"] for cell in cells], dtype=np.float64)
    if tets.ndim != 3 or tets.shape[1:] != (4, 3) \
            or not np.all(np.isfinite(tets)) \
            or densities.shape != (len(cells),) \
            or not np.all(np.isfinite(densities)) or np.any(densities <= 0.0):
        _fail("invalid_group_mass_input", "group cells need finite vertices and positive densities")
    edges = tets[:, 1:] - tets[:, :1]
    determinants = np.linalg.det(np.transpose(edges, (0, 2, 1)))
    volumes = determinants / 6.0
    if not np.all(np.isfinite(volumes)) or np.any(volumes <= 0.0):
        _fail("invalid_group_cell_orientation", "group contains a non-positive-volume cell")
    cell_masses = volumes * densities
    total_mass = float(np.sum(cell_masses, dtype=np.float64))
    if not math.isfinite(total_mass) or total_mass <= 0.0:
        _fail("numeric_overflow", "group mass is non-finite or non-positive")
    centroids = tets[:, 0] + np.sum(edges, axis=1) / 4.0
    reference = tets[0, 0]
    center_relative = centroids - reference
    com = reference + np.sum(cell_masses[:, None] * center_relative, axis=0) / total_mass
    local = tets - centroids[:, None, :]
    second_moments = (cell_masses[:, None, None] / 20.0) * np.einsum(
        "tvi,tvj->tij", local, local)
    offsets = centroids - com
    eye = np.eye(3)
    cell_inertia = (np.trace(second_moments, axis1=1, axis2=2)[:, None, None] * eye
                    - second_moments
                    + cell_masses[:, None, None] * (
                        np.einsum("ti,ti->t", offsets, offsets)[:, None, None] * eye
                        - np.einsum("ti,tj->tij", offsets, offsets)))
    inertia = np.sum(cell_inertia, axis=0, dtype=np.float64)
    inertia = 0.5 * (inertia + inertia.T)
    volume = float(np.sum(volumes, dtype=np.float64))
    if not (np.all(np.isfinite(com)) and np.all(np.isfinite(inertia))
            and math.isfinite(volume) and volume > 0.0):
        _fail("numeric_overflow", "group mass properties are non-finite")
    return {"mass_kg": total_mass, "volume_m3": volume,
            "center_of_mass_domain_m": com,
            "inertia_domain_com_kg_m2": inertia}


def _body_mass_properties(group: dict, properties_domain: dict) -> dict:
    frame = group["body_frame"]
    transform = frame["domain_from_body"]
    rotation = np.asarray(transform["rotation"], dtype=np.float64)
    origin = np.asarray(transform["origin_m"], dtype=np.float64)
    center_body = rotation.T @ (properties_domain["center_of_mass_domain_m"] - origin)
    inertia_domain = properties_domain["inertia_domain_com_kg_m2"]
    inertia_body = rotation.T @ inertia_domain @ rotation
    inertia_body = 0.5 * (inertia_body + inertia_body.T)
    if not (np.all(np.isfinite(center_body)) and np.all(np.isfinite(inertia_body))):
        _fail("numeric_overflow", f"body {group['body_id']!r} frame transform overflowed")
    return {"mass": {"value": properties_domain["mass_kg"], "unit": "kg",
                      "coordinate_frame": "frame_invariant", "frame_invariant": True},
            "volume": {"value": properties_domain["volume_m3"], "unit": "m^3",
                       "coordinate_frame": "frame_invariant", "frame_invariant": True},
            "center_of_mass": {"value": center_body.tolist(), "unit": "m",
                                "coordinate_frame": frame["frame_id"]},
            "inertia_tensor_about_com": {"value": inertia_body.tolist(),
                                         "unit": "kg*m^2",
                                         "coordinate_frame": frame["frame_id"],
                                         "frame_id": frame["frame_id"],
                                         "basis": "authored_body_frame",
                                         "full_symmetric_tensor": True,
                                         "off_diagonal_terms_preserved": True,
                                         "principal_axis_transform_applied": False}}


def _material_provenance(cells: list[dict]) -> dict:
    materials = {}
    for cell in cells:
        material_id = cell["material_id"]
        record = {"material_id": material_id,
                  "density_kg_m3": cell["density_kg_m3"],
                  "density_source": cell["density_source"],
                  "conditions": cell["density_conditions"]}
        previous = materials.get(material_id)
        if previous is not None and previous != record:
            _fail("material_provenance_mismatch",
                  f"material {material_id!r} has inconsistent cell provenance")
        materials[material_id] = record
    return {"mass_authority": admission.AUTHORITY_RECONSTRUCTED,
            "mass_source_kind": "reconstructed_material_volume",
            "integration_model": "piecewise_constant_density_over_owned_tetrahedral_cells",
            "material_records": [materials[key] for key in sorted(materials)],
            "mass_owner_ids": sorted({cell["mass_owner_id"] for cell in cells}),
            "source_effective_segment_payloads_consumed": False,
            "surface_mass_overlay_consumed": False,
            "surface_mass_overlay_generated": False}


def _unassigned_cell_rows(cell_ids: list[str], assignment_rows: Mapping[str, dict]) -> list[dict]:
    result = []
    for cell_id in cell_ids:
        row = assignment_rows.get(cell_id, {})
        result.append({"cell_id": cell_id,
                       "assignment_status": row.get("status", "unknown"),
                       "reason": "not_assigned_to_an_authored_body_group"})
    return result


def build_export_report(manifest: Mapping, partition: Mapping,
                        group_document: Mapping) -> dict:
    """Revalidate all inputs and export only explicitly assigned resolved cells.

    A full material-volume admission is required before any body group receives
    mass properties. A valid admission still does not certify dynamics readiness.
    Unassigned partition cells are surfaced explicitly and make the result
    partial, never silently included or dropped.
    """
    hashes = _hashes(manifest, partition, group_document)
    try:
        groups = _parse_groups(group_document)
    except ExportInputError as error:
        return _input_refusal(error.reason, error.detail, hashes, None)

    # Recompute admission from the actual manifest + partition. No caller flag
    # or embedded prior report can bypass this check.
    admission_report = admission.build_admission_report(manifest, partition)
    admission_decision = admission_report.get("decision", "refused")
    cell_rows = admission_report.get("cells", [])
    assignment_rows = {row["cell_id"]: row for row in cell_rows
                       if isinstance(row, Mapping) and isinstance(row.get("cell_id"), str)}
    raw_cells = partition.get("cells", []) if isinstance(partition, Mapping) else []
    supplied_cell_ids = sorted({row["cell_id"] for row in raw_cells
                                if isinstance(row, Mapping)
                                and isinstance(row.get("cell_id"), str)}) \
        if isinstance(raw_cells, list) else []
    group_cell_ids = {cell_id for group in groups for cell_id in group["cell_ids"]}
    unknown_cells = sorted(group_cell_ids - set(supplied_cell_ids))
    unassigned = sorted(set(supplied_cell_ids) - group_cell_ids)
    if unknown_cells:
        return _input_refusal("unknown_group_cell_id",
                              f"body groups reference cells absent from partition: {unknown_cells}",
                              hashes, admission_report, unassigned)

    raw_authority = (manifest.get("mass_authority")
                     if isinstance(manifest, Mapping) else None)
    unsupported_authority = raw_authority == admission.AUTHORITY_EFFECTIVE_SEGMENT
    base = {"schema_version": EXPORT_SCHEMA,
            "validation_only": True,
            "dynamics_readiness_claimed": False,
            "physical_state_mutated": False,
            "production_wired": False,
            "admission_status": admission_decision,
            "admission_reason_codes": admission_report.get("reason_codes", []),
            "admission_report_sha256": _canonical_hash(admission_report),
            "admission_anatomical_completeness_certified": False,
            "mass_authority": raw_authority,
            "input_hashes": hashes,
            "unassigned_cell_ids": unassigned,
            "unassigned_cells": _unassigned_cell_rows(unassigned, assignment_rows),
            "all_supplied_cells_assigned": not unassigned,
            "surface_mass_overlay_generated": False,
            "anatomical_completeness_certified": False}

    if unsupported_authority:
        groups_out = []
        for group in groups:
            groups_out.append({"body_id": group["body_id"],
                               "owned_cell_ids": group["cell_ids"],
                               "body_frame": group["body_frame"],
                               "export_status": "not_exported",
                               "admission_status": admission_decision,
                               "admission_report_sha256": _canonical_hash(admission_report),
                               "input_hashes": hashes,
                               "reason_codes": ["source_effective_segment_mass_unsupported"],
                               "mass_properties": None,
                               "mass_values_consumed": False})
        return {**base, "export_status": "unsupported",
                "reason_codes": ["source_effective_segment_mass_unsupported"],
                "source_effective_segment_payloads_consumed": False,
                "body_groups": groups_out}

    # A partial or failed admission is never promoted to body properties. Keep
    # affected assignment IDs visible to identify what prevented export.
    if admission_decision != "validation_only_admissible":
        groups_out = []
        for group in groups:
            member_rows = [assignment_rows[cell_id] for cell_id in group["cell_ids"]
                           if cell_id in assignment_rows]
            blocking_rows = [row for row in member_rows if row.get("status") != "resolved"]
            groups_out.append(_blocked_group(group, admission_decision, blocking_rows,
                                             "reconstructed_mass_admission_required", hashes,
                                             admission_report.get("reason_codes", [])))
        return {**base, "export_status": "blocked",
                "reason_codes": ["reconstructed_mass_admission_required"],
                "source_effective_segment_payloads_consumed": False,
                "body_groups": groups_out}

    # The admission adapter only admits matching reconstructed volume authority,
    # complete assignments/density, and a valid conforming tetrahedral complex.
    if not isinstance(partition, Mapping):
        return _input_refusal("bad_partition", "partition must be an object",
                              hashes, admission_report, unassigned)
    try:
        vertices = partition["vertices"]
        frame = partition["coordinate_frame"]
        if not isinstance(vertices, list) or not isinstance(frame, Mapping):
            raise KeyError("vertices/coordinate_frame")
        scale = float(frame["scale_to_m"])
        if not math.isfinite(scale) or scale <= 0.0:
            raise KeyError("scale_to_m")
        vertices_m = [{"vertex_id": row["vertex_id"],
                       "position": [float(x) * scale for x in row["position"]]}
                      for row in vertices]
        by_cell = {row["cell_id"]: row for row in assignment_rows.values()}
        group_outputs = []
        for group in groups:
            rows = []
            for cell_id in group["cell_ids"]:
                row = by_cell.get(cell_id)
                if row is None or row.get("status") != "resolved" \
                        or not row.get("mass_owner_id"):
                    raise ExportInputError("cell_not_uniquely_owned",
                                           f"cell {cell_id!r} has no single resolved mass owner")
                rows.append(row)
            row_by_id = {row["cell_id"]: row for row in rows}
            cells = []
            for source_cell in partition["cells"]:
                cell_id = source_cell["cell_id"]
                if cell_id not in row_by_id:
                    continue
                assignment = row_by_id[cell_id]
                cells.append({"cell_id": cell_id,
                              "vertex_ids": list(source_cell["vertex_ids"]),
                              "mass_owner_id": assignment["mass_owner_id"],
                              "region_id": assignment["region_id"],
                              "material_id": assignment["material_id"],
                              "density_kg_m3": assignment["density_kg_m3"],
                              "density_source": assignment["density_source"],
                              "density_conditions": assignment["density_conditions"]})
            cells.sort(key=lambda row: row["cell_id"])
            properties_domain = _integrate_cells(vertices_m, cells)
            properties_body = _body_mass_properties(group, properties_domain)
            group_outputs.append({"body_id": group["body_id"],
                                  "owned_cell_ids": group["cell_ids"],
                                  "body_frame": group["body_frame"],
                                  "export_status": "exported",
                                  "admission_status": admission_decision,
                                  "admission_report_sha256": _canonical_hash(admission_report),
                                  "input_hashes": hashes,
                                  "material_mass_source_provenance": _material_provenance(cells),
                                  "cell_provenance": [{
                                      "cell_id": row["cell_id"],
                                      "mass_owner_id": row["mass_owner_id"],
                                      "region_id": row["region_id"],
                                      "material_id": row["material_id"],
                                      "density_kg_m3": row["density_kg_m3"],
                                      "density_source": row["density_source"],
                                      "density_conditions": row["density_conditions"]}
                                      for row in cells],
                                  "mass_properties": properties_body})
    except (ExportInputError, KeyError, TypeError, ValueError, OverflowError) as error:
        if isinstance(error, ExportInputError):
            reason, detail = error.reason, error.detail
        else:
            reason, detail = "invalid_export_input", type(error).__name__
        return _input_refusal(reason, detail, hashes, admission_report, unassigned)

    return {**base,
            "export_status": "partial" if unassigned else "complete",
            "reason_codes": ["unassigned_cells"] if unassigned else [],
            "source_effective_segment_payloads_consumed": False,
            "body_groups": group_outputs}


def canonical_json(report: Mapping) -> str:
    return json.dumps(report, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False) + "\n"


class _DuplicateJsonKey(ValueError):
    pass


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJsonKey(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_json_constant(token: str):
    raise ValueError(f"nonstandard JSON constant {token!r}")


def read_json_file(path: str) -> object:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"),
                          object_pairs_hook=_unique_pairs,
                          parse_constant=_reject_json_constant)
    except _DuplicateJsonKey as error:
        _fail("duplicate_json_key", str(error))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        _fail("input_read_error", f"unable to read {path!r}: {type(error).__name__}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, help="fitting manifest JSON")
    parser.add_argument("--partition", required=True, help="material partition JSON")
    parser.add_argument("--groups", required=True, help="explicit body-group assignment JSON")
    args = parser.parse_args(argv)
    try:
        manifest = read_json_file(args.manifest)
        partition = read_json_file(args.partition)
        group_document = read_json_file(args.groups)
        report = build_export_report(manifest, partition, group_document)
    except ExportInputError as error:
        report = _input_refusal(error.reason, error.detail,
                                {"algorithm": "sha256",
                                 "serialization": "canonical JSON",
                                 "manifest_sha256": None,
                                 "partition_sha256": None,
                                 "body_groups_sha256": None}, None)
    sys.stdout.write(canonical_json(report))
    return 0 if report["export_status"] in {"complete", "partial", "unsupported"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
