"""B3 addendum — CON-12 pair + full summary key-set diff (post-analysis).

Logged explanation (campaign law: corrections = logged explanation + new
receipt): the FROZEN PREREG's I4 sub-field list named per-cell provenance rows
only; the contract's CON-12 names `cell_provenance` AND
`material_mass_source_provenance` as the provenance pair. The frozen verdict
matrix (receipts/03) is left untouched; THIS receipt measures the CON-12 pair
and the complete key-set difference between the parsed report and the reader
summary, from the PRESERVED run artifacts (fixtures/*/report.json,
fixtures/*/summary.json). No verdict row of the frozen matrix is altered.

Also records: summary `mass_kg` vs parsed mass value (exact), owned_cell_ids,
and which dropped keys have an information-bearing surrogate in the summary
(e.g. tensor.frame_id vs tensor.coordinate_frame) vs none (information loss).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
B3 = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(B3.parents[2] / "tools"))

import material_volume_body_export as exporter  # noqa: E402

FIXTURES = ["rotcoupon", "shipped_example"]
out = {"logged_explanation":
       "CON-12 pair + key-set completeness measured post-run on preserved "
       "artifacts; frozen matrix 03 untouched (see module docstring).",
       "fixtures": {}}

for fixture in FIXTURES:
    parsed = exporter.read_json_file(str(B3 / "fixtures" / fixture / "report.json"))
    summary = exporter.read_json_file(str(B3 / "fixtures" / fixture / "summary.json"))
    entry = {}

    top_report = set(parsed)
    top_summary = set(summary)
    entry["top_level_keys_dropped_by_summary"] = sorted(top_report - top_summary)
    entry["top_level_keys_added_by_summary"] = sorted(top_summary - top_report)

    bodies = []
    by_id = {g["body_id"]: g for g in parsed["body_groups"]}
    for srow in summary["bodies"]:
        src = by_id[srow["body_id"]]
        b = {"body_id": srow["body_id"]}
        b["body_keys_dropped_by_summary"] = sorted(set(src) - set(srow))
        b["body_keys_added_by_summary"] = sorted(set(srow) - set(src))
        # CON-12 pair part 2
        b["material_mass_source_provenance_in_report"] = (
            "material_mass_source_provenance" in src)
        b["material_mass_source_provenance_in_summary"] = (
            "material_mass_source_provenance" in srow)
        # mass value preservation (not a frozen invariant; observation)
        b["mass_kg_exact_equals_report_value"] = (
            srow.get("mass_kg") == src["mass_properties"]["mass"]["value"])
        b["owned_cell_ids_exact"] = (
            srow.get("owned_cell_ids") == src["owned_cell_ids"])
        # surrogate analysis for dropped keys
        tensor = src["mass_properties"]["inertia_tensor_about_com"]
        b["tensor_frame_id_value"] = tensor["frame_id"]
        b["tensor_coordinate_frame_value_in_summary"] = (
            srow["inertia_tensor_about_com"].get("coordinate_frame"))
        b["tensor_frame_id_info_preserved_via_coordinate_frame"] = (
            srow["inertia_tensor_about_com"].get("coordinate_frame")
            == tensor["frame_id"])
        b["body_frame_info_surrogate_in_summary"] = None
        b["volume_value_in_report_not_in_summary"] = (
            src["mass_properties"]["volume"]["value"])
        bodies.append(b)
    entry["bodies"] = bodies

    # readiness + admission binding recurrence
    entry["dynamics_readiness_claimed_summary"] = (
        summary["dynamics_readiness_claimed"])
    entry["unassigned_cell_ids_exact"] = (
        summary["unassigned_cell_ids"] == parsed["unassigned_cell_ids"])
    entry["input_hashes_exact"] = summary["input_hashes"] == parsed["input_hashes"]
    out["fixtures"][fixture] = entry

dest = B3 / "receipts" / "09_con12_addendum.json"
dest.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n",
                encoding="utf-8", newline="\n")
print(json.dumps(out, indent=1, sort_keys=True)[:3000])
