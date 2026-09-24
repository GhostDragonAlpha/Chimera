"""Generate the GENUINE exporter blocked report used by the W6 MV-O1 regression.

Construction identical to M07's C4 (ownership receipt): the shipped example
inputs with one input defect — partition material ``tissue-B`` has
``density_kg_m3: null`` — fed to ``tools/material_volume_body_export.build_export_report``
(the exporter revalidates and blocks the reconstructed-mass admission). The
result is a genuine producer artifact: root ``blocked``, both bodies
``not_exported``, each body ``admission_report_sha256`` binding the REDUCED
object ``{"decision": ..., "reason_codes": ...}`` (exporter ``_blocked_group``),
per M07 decision request O1 and the decided MV-O1.

Frozen output: ``genuine_blocked_report.json`` (+ ``genuine_blocked_inputs.json``
recording the exact inputs, for reproducibility). tools/ is never touched;
bytecode writing is disabled for the read-only import.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parents[4] / "tools"
sys.path.insert(0, str(TOOLS))

import material_volume_body_export as exporter  # noqa: E402


def load(name: str):
    return exporter.read_json_file(str(TOOLS / name))


def main() -> int:
    manifest = load("material_volume_body_export_manifest_example.json")
    partition = load("material_volume_body_export_partition_example.json")
    groups = load("material_volume_body_export_groups_example.json")
    # The single input defect (M07 C4): one material loses its density.
    blocked_partition = json.loads(json.dumps(partition))
    for row in blocked_partition["materials"]:
        if row["material_id"] == "tissue-B":
            row["density_kg_m3"] = None
    report = exporter.build_export_report(manifest, blocked_partition, groups)
    assert report["export_status"] == "blocked", report["export_status"]
    assert all(row["export_status"] == "not_exported"
               for row in report["body_groups"]), report["body_groups"]
    out = HERE / "genuine_blocked_report.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False,
                              allow_nan=False) + "\n", encoding="utf-8")
    print(f"frozen {out}")
    for row in report["body_groups"]:
        print(row["body_id"], row["export_status"], row["admission_status"],
              row.get("admission_reason_codes"), row["admission_report_sha256"])
    print("root:", report["admission_status"], report["admission_report_sha256"])

    # The genuine PARTIAL report (M07 C3 construction, replicated from the M07
    # ownership receipt's frozen generator): a third disjoint positive tet
    # cell-C in no authored group, fully resolved through its own region-C /
    # tissue-C — root 'partial' with the cell surfaced as an explicit unassigned
    # gap while both bodies still export. This is the shape the decided D2
    # diagnostic-display duty (CON-3) talks about.
    partial_manifest = json.loads(json.dumps(manifest))
    partial_partition = json.loads(json.dumps(partition))
    partial_manifest["fitting_id"] = "two-body-coupon-fit-v1-plus-unassigned-c"
    tet_c = [{"vertex_id": "c0", "position": [0.0, 3.0, 0.0]},
             {"vertex_id": "c1", "position": [1.0, 3.0, 0.0]},
             {"vertex_id": "c2", "position": [0.0, 4.0, 0.0]},
             {"vertex_id": "c3", "position": [0.0, 3.0, 1.0]}]
    partial_manifest["vertices"] += tet_c
    partial_manifest["cells"].append(
        {"cell_id": "cell-C", "vertex_ids": ["c0", "c1", "c2", "c3"],
         "component_id": "component-C"})
    partial_manifest["regions"].append(
        {"region_id": "region-C", "mass_owner_id": "owner-C",
         "material_id": "tissue-C"})
    partial_manifest["matter_ownership"].append(
        {"matter_id": "coupon-matter-C", "representation": "tetrahedral_volume",
         "mass_owner_id": "owner-C"})
    partial_partition["vertices"] = partial_manifest["vertices"]
    partial_partition["cells"].append(
        {"cell_id": "cell-C", "vertex_ids": ["c0", "c1", "c2", "c3"],
         "proposals": ["region-C"]})
    partial_partition["materials"].append(
        {"material_id": "tissue-C", "density_kg_m3": 3.0,
         "density_source": "analytic coupon fixture", "conditions": "uniform"})
    partial_partition["regions"] = partial_manifest["regions"]
    partial_report = exporter.build_export_report(
        partial_manifest, partial_partition, groups)
    assert partial_report["export_status"] == "partial", partial_report["export_status"]
    assert partial_report["unassigned_cell_ids"] == ["cell-C"], \
        partial_report["unassigned_cell_ids"]
    assert all(row["export_status"] == "exported"
               for row in partial_report["body_groups"]), partial_report["body_groups"]
    pout = HERE / "genuine_partial_report.json"
    pout.write_text(json.dumps(partial_report, indent=2, ensure_ascii=False,
                               allow_nan=False) + "\n", encoding="utf-8")
    print(f"frozen {pout}")
    print("root:", partial_report["export_status"],
          partial_report["unassigned_cell_ids"],
          partial_report["all_supplied_cells_assigned"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
