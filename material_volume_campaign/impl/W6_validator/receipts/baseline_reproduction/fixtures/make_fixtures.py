"""Generate the FROZEN M10 fixture set (PREREGISTRATION.md test plan).

Deterministic: reads the verbatim copy of the tools example report and writes
single-mutation reject fixtures + the adversarial probe fixtures into this
directory. Never touches tools/ (the copy here is the only input).
Run once:  python fixtures/make_fixtures.py
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE.parent))
from rigid_body_mass_consumption_validator import canonical_hash  # noqa: E402

TOOLS_EXAMPLE = HERE.parents[3] / "tools" / "material_volume_body_export_example_report.json"
ACCEPT = HERE / "accept_complete_report.json"
ADMISSION_DOC = {"decision": "validation_only_admissible", "reason_codes": []}


def dump(name: str, document) -> None:
    path = HERE / name
    path.write_text(json.dumps(document, sort_keys=True, separators=(",", ":"),
                               ensure_ascii=True, allow_nan=False) + "\n",
                    encoding="utf-8")
    print(f"wrote {path.name}")


_REGISTRY: list[tuple[str, dict]] = []


def mutant(base, name: str) -> dict:
    """Register a deep copy; mutations applied by the caller AFTER this call are
    captured because the registry is dumped at the end of main()."""
    document = copy.deepcopy(base)
    _REGISTRY.append((name, document))
    return document


def main() -> int:
    accept = json.loads(TOOLS_EXAMPLE.read_text(encoding="utf-8"))
    ACCEPT.write_text(TOOLS_EXAMPLE.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"wrote {ACCEPT.name} (verbatim copy of {TOOLS_EXAMPLE.name})")

    body_a = accept["body_groups"][0]
    body_b = accept["body_groups"][1]

    # ---- root export_status variants (R2; partial/blocked/unsupported/refused
    # are modeled on the exporter's real output shapes) ----
    partial = mutant(accept, "reject_partial.json")
    partial["export_status"] = "partial"
    partial["all_supplied_cells_assigned"] = False
    partial["unassigned_cell_ids"] = ["cell-U"]
    partial["unassigned_cells"] = [{"cell_id": "cell-U", "assignment_status": "unassigned"}]
    partial["reason_codes"] = ["unassigned_cells"]

    blocked = mutant(accept, "reject_blocked.json")
    blocked["export_status"] = "blocked"
    blocked["reason_codes"] = ["missing_density"]
    blocked["body_groups"][0] = {
        "body_id": body_a["body_id"],
        "owned_cell_ids": ["cell-A"],
        "body_frame": body_a["body_frame"],
        "export_status": "not_exported",
        "admission_status": "missing_density",
        "admission_report_sha256": accept["admission_report_sha256"],
        "input_hashes": accept["input_hashes"],
        "admission_reason_codes": ["missing_density"],
        "blocking_cell_ids": ["cell-A"],
        "blocking_assignment_statuses": [{"cell_id": "cell-A", "status": "missing_density"}],
        "reason_codes": ["missing_density"],
        "mass_properties": None,
    }

    unsupported = mutant(accept, "reject_unsupported.json")
    unsupported["export_status"] = "unsupported"
    unsupported["reason_codes"] = ["source_effective_segment_mass_unsupported"]
    unsupported["body_groups"][0] = {
        "body_id": body_a["body_id"],
        "owned_cell_ids": ["cell-A"],
        "export_status": "not_exported",
        "admission_status": "validation_only_admissible",
        "admission_report_sha256": accept["admission_report_sha256"],
        "input_hashes": accept["input_hashes"],
        "reason_codes": ["source_effective_segment_mass_unsupported"],
        "mass_properties": None,
    }

    refused = {
        "schema_version": accept["schema_version"],
        "export_status": "refused",
        "validation_only": True,
        "dynamics_readiness_claimed": False,
        "physical_state_mutated": False,
        "production_wired": False,
        "admission_status": "not_evaluated",
        "admission_report_sha256": None,
        "input_hashes": {"algorithm": "sha256", "serialization": "canonical JSON",
                         "manifest_sha256": None, "partition_sha256": None,
                         "body_groups_sha256": None},
        "body_groups": [],
        "unassigned_cell_ids": [],
        "unassigned_cells": [],
        "reason_codes": ["duplicate_json_key"],
        "detail": "duplicate JSON key",
        "surface_mass_overlay_generated": False,
        "anatomical_completeness_certified": False,
    }
    dump("reject_refused.json", refused)

    unknown = mutant(accept, "reject_unknown_status.json")
    unknown["export_status"] = "assembled"

    case_variant = mutant(accept, "adversarial_case_variant_status.json")
    case_variant["export_status"] = "Complete"
    for row in case_variant["body_groups"]:
        row["export_status"] = "Exported"

    # ---- R3 admission_status ----
    for name, value in (("reject_admission_case.json", "Validation_Only_Admissible"),
                        ("reject_admission_loose.json", "admissible")):
        doc = mutant(accept, name)
        doc["admission_status"] = value
        for row in doc["body_groups"]:
            row["admission_status"] = value

    # ---- R4 hash binding ----
    doc = mutant(accept, "reject_hash_missing.json")
    del doc["body_groups"][0]["admission_report_sha256"]

    doc = mutant(accept, "reject_hash_short.json")
    doc["body_groups"][0]["admission_report_sha256"] = "a" * 63

    doc = mutant(accept, "reject_hash_mismatch.json")
    doc["body_groups"][1]["admission_report_sha256"] = "b" * 64

    doc = mutant(accept, "reject_hash_uppercase.json")
    doc["body_groups"][0]["admission_report_sha256"] = \
        doc["body_groups"][0]["admission_report_sha256"].upper()

    # Recomputation path: report bound to a KNOWN admission document.
    doc = mutant(accept, "recompute_report.json")
    known_hash = canonical_hash(ADMISSION_DOC)
    doc["admission_report_sha256"] = known_hash
    for row in doc["body_groups"]:
        row["admission_report_sha256"] = known_hash
    dump("recompute_admission.json", ADMISSION_DOC)
    dump("recompute_admission_mismatched.json",
         {"decision": "validation_only_admissible", "reason_codes": ["tampered"]})

    # ---- R5 per-body status ----
    doc = mutant(accept, "reject_not_exported.json")
    doc["body_groups"][1] = {
        "body_id": body_b["body_id"],
        "owned_cell_ids": ["cell-B"],
        "export_status": "not_exported",
        "admission_status": "validation_only_admissible",
        "admission_report_sha256": accept["admission_report_sha256"],
        "input_hashes": accept["input_hashes"],
        "reason_codes": ["ownership_conflict"],
        "blocking_cell_ids": ["cell-B"],
        "mass_properties": None,
    }

    doc = mutant(accept, "reject_placeholder_mass.json")
    doc["body_groups"][1]["export_status"] = "not_exported"
    doc["body_groups"][1]["reason_codes"] = ["ownership_conflict"]

    # ---- R6/R7/R8 mass fields ----
    doc = mutant(accept, "reject_mass_unit.json")
    doc["body_groups"][0]["mass_properties"]["mass"]["unit"] = "g"
    doc = mutant(accept, "reject_mass_negative.json")
    doc["body_groups"][0]["mass_properties"]["mass"]["value"] = -2.0
    doc = mutant(accept, "reject_mass_not_invariant.json")
    doc["body_groups"][0]["mass_properties"]["mass"]["frame_invariant"] = False
    doc = mutant(accept, "reject_volume_unit.json")
    doc["body_groups"][0]["mass_properties"]["volume"]["unit"] = "cm^3"
    doc = mutant(accept, "reject_com_frame.json")
    doc["body_groups"][0]["mass_properties"]["center_of_mass"]["coordinate_frame"] = "other-frame"
    doc = mutant(accept, "reject_com_short.json")
    doc["body_groups"][0]["mass_properties"]["center_of_mass"]["value"] = [0.25, 0.25]

    # ---- R9 full-tensor integrity ----
    doc = mutant(accept, "reject_tensor_truncated.json")  # adversarial A1
    doc["body_groups"][0]["mass_properties"]["inertia_tensor_about_com"]["value"] = \
        body_a["mass_properties"]["inertia_tensor_about_com"]["value"][:2]
    doc = mutant(accept, "reject_tensor_asymmetric.json")  # adversarial A2
    tensor = copy.deepcopy(body_a["mass_properties"]["inertia_tensor_about_com"]["value"])
    tensor[1][0] = 0.0125  # transposed/mismatched off-diagonal pair (0,1)=0.025 vs (1,0)
    doc["body_groups"][0]["mass_properties"]["inertia_tensor_about_com"]["value"] = tensor
    doc = mutant(accept, "reject_tensor_pa_true.json")
    doc["body_groups"][0]["mass_properties"]["inertia_tensor_about_com"][
        "principal_axis_transform_applied"] = True
    doc = mutant(accept, "reject_tensor_offdiag_flag.json")
    doc["body_groups"][0]["mass_properties"]["inertia_tensor_about_com"][
        "off_diagonal_terms_preserved"] = False
    doc = mutant(accept, "reject_tensor_full_flag.json")
    doc["body_groups"][0]["mass_properties"]["inertia_tensor_about_com"][
        "full_symmetric_tensor"] = False
    doc = mutant(accept, "reject_tensor_unit.json")
    doc["body_groups"][0]["mass_properties"]["inertia_tensor_about_com"]["unit"] = "kg m^2"
    doc = mutant(accept, "reject_tensor_frame.json")
    doc["body_groups"][0]["mass_properties"]["inertia_tensor_about_com"][
        "coordinate_frame"] = "other-frame"

    # ---- R10 body frame ----
    doc = mutant(accept, "reject_frame_lefthanded.json")
    left = copy.deepcopy(body_b["body_frame"]["domain_from_body"]["rotation"])
    left[0] = [-v for v in left[0]]  # det -> -1, still orthonormal
    doc["body_groups"][1]["body_frame"]["domain_from_body"]["rotation"] = left
    doc = mutant(accept, "reject_frame_nonorthonormal.json")
    scaled = [[1.01 * v for v in row]
              for row in body_a["body_frame"]["domain_from_body"]["rotation"]]
    doc["body_groups"][0]["body_frame"]["domain_from_body"]["rotation"] = scaled
    doc = mutant(accept, "reject_frame_handedness.json")
    doc["body_groups"][0]["body_frame"]["handedness"] = "left"
    doc = mutant(accept, "reject_frame_unit.json")
    doc["body_groups"][0]["body_frame"]["coordinate_unit"] = "cm"

    # ---- R11 ownership / provenance ----
    doc = mutant(accept, "reject_provenance_stripped.json")
    del doc["body_groups"][0]["cell_provenance"]
    doc = mutant(accept, "reject_owned_missing_provenance.json")
    doc["body_groups"][0]["owned_cell_ids"] = ["cell-A", "cell-Z"]
    doc = mutant(accept, "reject_conflicting_owner.json")
    conflict = copy.deepcopy(body_a["cell_provenance"][0])
    conflict["mass_owner_id"] = "owner-B"
    doc["body_groups"][0]["cell_provenance"].append(conflict)
    doc = mutant(accept, "reject_owner_ids_mismatch.json")
    doc["body_groups"][0]["material_mass_source_provenance"]["mass_owner_ids"] = ["owner-B"]
    doc = mutant(accept, "reject_source_kind.json")
    doc["body_groups"][0]["material_mass_source_provenance"]["mass_source_kind"] = \
        "source_effective_segment_mass"
    doc = mutant(accept, "reject_mass_authority_source.json")  # T-D5
    doc["body_groups"][0]["material_mass_source_provenance"]["mass_authority"] = \
        "source_effective_segment_mass"

    # ---- R12 readiness (D1) ----
    doc = mutant(accept, "reject_readiness_root.json")
    doc["dynamics_readiness_claimed"] = True
    doc = mutant(accept, "reject_readiness_body.json")
    doc["body_groups"][0]["dynamics_readiness_claimed"] = True
    doc = mutant(accept, "adversarial_readiness_nested.json")  # adversarial A4
    doc["body_groups"][0]["admission"] = {"decision": "validation_only_admissible",
                                          "dynamics_ready": True}

    # ---- R13 safety flags ----
    for name, field in (("reject_production_wired.json", "production_wired"),
                        ("reject_state_mutated.json", "physical_state_mutated"),
                        ("reject_source_payloads.json",
                         "source_effective_segment_payloads_consumed"),
                        ("reject_validation_only_false.json", "validation_only")):
        doc = mutant(accept, name)
        doc[field] = not doc[field]

    # ---- R14 unassigned cells (D2) ----
    doc = mutant(accept, "reject_unassigned_in_complete.json")
    doc["unassigned_cell_ids"] = ["cell-U"]
    doc["unassigned_cells"] = [{"cell_id": "cell-U", "assignment_status": "unassigned"}]
    doc["all_supplied_cells_assigned"] = False
    doc = mutant(accept, "reject_all_supplied_false.json")
    doc["all_supplied_cells_assigned"] = False

    # ---- R15/R16 reserved fields (D3/D4) ----
    doc = mutant(accept, "reject_composite.json")
    doc["body_groups"][0]["composite_of"] = ["coupon-body-B"]
    doc = mutant(accept, "reject_lineage.json")
    doc["body_groups"][0]["body_frame"]["frame_lineage"] = {"schema": "v2"}

    # ---- adversarial A5: silently diagonalized tensor, flags unchanged.
    # PREDICTED (PREREGISTRATION LIMIT 2): validator ACCEPTS — statically
    # indistinguishable from a genuinely diagonal authored body.
    doc = mutant(accept, "adversarial_diagonalized.json")
    doc["body_groups"][0]["mass_properties"]["inertia_tensor_about_com"]["value"] = \
        [[0.2, 0.0, 0.0], [0.0, 0.2, 0.0], [0.0, 0.0, 0.2]]

    for name, document in _REGISTRY:
        dump(name, document)
    print("fixture generation complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
