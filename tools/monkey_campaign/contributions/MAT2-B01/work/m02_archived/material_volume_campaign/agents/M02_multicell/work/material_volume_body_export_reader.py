"""Minimal read-only reader for ``chimera.rigid_body_mass_export.v1`` JSON.

The reader validates the output version and each exported mass tensor, then
prints a compact summary without discarding off-diagonal entries. It performs
no physics imports, readiness promotion, or state mutation.

Run:
    python tools/material_volume_body_export_reader.py export.json
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np

import material_volume_body_export as exporter


def summarize_export_report(report: Mapping) -> dict:
    if not isinstance(report, Mapping):
        raise exporter.ExportInputError("bad_export_report", "export report must be an object")
    if report.get("schema_version") != exporter.EXPORT_SCHEMA:
        raise exporter.ExportInputError("bad_export_report_version",
                                        f"schema_version must be {exporter.EXPORT_SCHEMA!r}")
    status = report.get("export_status")
    allowed = {"complete", "partial", "blocked", "unsupported", "refused"}
    if status not in allowed:
        raise exporter.ExportInputError("bad_export_status", "unknown export_status")
    admission_status = report.get("admission_status")
    groups = report.get("body_groups")
    if not isinstance(groups, list):
        raise exporter.ExportInputError("bad_export_report", "body_groups must be an array")
    summaries = []
    for index, row in enumerate(groups):
        label = f"body_groups[{index}]"
        if not isinstance(row, Mapping) or not isinstance(row.get("body_id"), str):
            raise exporter.ExportInputError("bad_export_report", f"{label} must identify a body")
        group_status = row.get("export_status")
        if group_status == "exported":
            props = row.get("mass_properties")
            if not isinstance(props, Mapping):
                raise exporter.ExportInputError("bad_export_report", f"{label} has no mass properties")
            mass, center, inertia = props.get("mass"), props.get("center_of_mass"), \
                props.get("inertia_tensor_about_com")
            if not all(isinstance(value, Mapping) for value in (mass, center, inertia)):
                raise exporter.ExportInputError("bad_export_report", f"{label} has malformed mass fields")
            tensor = np.asarray(inertia.get("value"), dtype=np.float64)
            center_value = np.asarray(center.get("value"), dtype=np.float64)
            mass_value = mass.get("value")
            if tensor.shape != (3, 3) or center_value.shape != (3,) \
                    or not np.all(np.isfinite(tensor)) or not np.all(np.isfinite(center_value)) \
                    or not math.isfinite(float(mass_value)) or float(mass_value) <= 0.0:
                raise exporter.ExportInputError("bad_export_report", f"{label} has invalid numeric properties")
            if not np.allclose(tensor, tensor.T, rtol=0.0, atol=1e-12):
                raise exporter.ExportInputError("nonsymmetric_inertia", f"{label} inertia is not symmetric")
            if inertia.get("full_symmetric_tensor") is not True \
                    or inertia.get("off_diagonal_terms_preserved") is not True \
                    or inertia.get("principal_axis_transform_applied") is not False:
                raise exporter.ExportInputError("inertia_contract_mismatch",
                                                f"{label} does not preserve the authored full tensor")
            summaries.append({"body_id": row["body_id"], "export_status": group_status,
                              "owned_cell_ids": row.get("owned_cell_ids", []),
                              "mass_kg": float(mass_value),
                              "center_of_mass": {"value": center_value.tolist(),
                                                 "unit": center.get("unit"),
                                                 "coordinate_frame": center.get("coordinate_frame")},
                              "inertia_tensor_about_com": {
                                  "value": tensor.tolist(), "unit": inertia.get("unit"),
                                  "coordinate_frame": inertia.get("coordinate_frame"),
                                  "basis": inertia.get("basis"),
                                  "full_symmetric_tensor": True,
                                  "off_diagonal_terms_preserved": True,
                                  "principal_axis_transform_applied": False},
                              "input_hashes": row.get("input_hashes"),
                              "admission_report_sha256": row.get("admission_report_sha256"),
                              "admission_status": row.get("admission_status")})
        else:
            if row.get("mass_properties") is not None:
                raise exporter.ExportInputError("blocked_group_has_mass",
                                                f"{label} is not exported but includes properties")
            summaries.append({"body_id": row["body_id"], "export_status": group_status,
                              "owned_cell_ids": row.get("owned_cell_ids", []),
                              "reason_codes": row.get("reason_codes", []),
                              "input_hashes": row.get("input_hashes"),
                              "admission_report_sha256": row.get("admission_report_sha256"),
                              "admission_status": row.get("admission_status"),
                              "mass_properties": None})
    return {"schema_version": exporter.EXPORT_SCHEMA,
            "export_status": status,
            "admission_status": admission_status,
            "dynamics_readiness_claimed": False,
            "physical_state_mutated": False,
            "bodies": summaries,
            "unassigned_cell_ids": report.get("unassigned_cell_ids", []),
            "input_hashes": report.get("input_hashes")}


def canonical_json(value: Mapping) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", help="body-mass export report JSON")
    args = parser.parse_args(argv)
    try:
        report = exporter.read_json_file(args.report)
        summary = summarize_export_report(report)
    except exporter.ExportInputError as error:
        sys.stderr.write(f"{error.reason}: {error.detail}\n")
        return 2
    sys.stdout.write(canonical_json(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
