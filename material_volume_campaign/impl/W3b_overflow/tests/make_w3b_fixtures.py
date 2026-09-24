"""Generate W3b's own fixtures (F-R2-3), regenerated from the description.

Layout is frozen in ../PREREGISTRATION.md:
  w3b_v0_valid_control.json   minimal VALID report (reader exits 0)
  w3b_v1_mass_hugeint.json    v0 with body_groups[1].mass.value: 1.0 -> 10**400
  w3b_v2_tensor_hugeint.json  v0 with body_groups[1].inertia.value[2][2]: 0.075 -> 10**400
Mirrors R2's r2_v1_mass_hugeint.json / r2_v2_tensor_hugeint.json placement
(group index 1; tensor [2][2] diagonal so symmetry still holds) with a
purpose-built minimal valid scaffold instead of R2's corpus copy.

Run: python tests/make_w3b_fixtures.py   (from impl/W3b_overflow/)
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "fixtures"
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / "tools"))
import material_volume_body_export as exporter  # noqa: E402

HUGE = 10 ** 400  # the 401-digit JSON integer literal of F-R2-3


def _group(body_id, mass, tensor_diag, tensor_off):
    tensor = [[tensor_diag, tensor_off, tensor_off],
              [tensor_off, tensor_diag, tensor_off],
              [tensor_off, tensor_off, tensor_diag]]
    return {
        "body_id": body_id,
        "export_status": "exported",
        "admission_status": "validation_only_admissible",
        "owned_cell_ids": [f"cell-{body_id[-1].upper()}"],
        "input_hashes": {"coupon": "w3b-fixture", "purpose": "F-R2-3 W3b"},
        "admission_report_sha256": "0" * 64,
        "mass_properties": {
            "mass": {"value": mass, "unit": "kg"},
            "center_of_mass": {"value": [0.25, 0.25, 0.25], "unit": "m",
                               "coordinate_frame": "coupon-authored"},
            "inertia_tensor_about_com": {
                "value": tensor, "unit": "kg*m^2",
                "coordinate_frame": "coupon-authored",
                "basis": "body_frame",
                "full_symmetric_tensor": True,
                "off_diagonal_terms_preserved": True,
                "principal_axis_transform_applied": False},
        },
    }


BASE = {
    "schema_version": exporter.EXPORT_SCHEMA,
    "export_status": "complete",
    "admission_status": "validation_only_admissible",
    "unassigned_cell_ids": [],
    "input_hashes": {"coupon": "w3b-fixture", "purpose": "F-R2-3 W3b"},
    "body_groups": [
        _group("coupon-body-A", 2.0, 0.15, 0.025),
        _group("coupon-body-B", 1.0, 0.075, 0.0125),
    ],
}


def _write(name, doc):
    path = FIXTURES / name
    path.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n",
                    encoding="utf-8")
    print(f"wrote {path}")


def main():
    FIXTURES.mkdir(parents=True, exist_ok=True)
    v1 = copy.deepcopy(BASE)
    v1["body_groups"][1]["mass_properties"]["mass"]["value"] = HUGE
    v2 = copy.deepcopy(BASE)
    v2["body_groups"][1]["mass_properties"]["inertia_tensor_about_com"]["value"][2][2] = HUGE
    _write("w3b_v0_valid_control.json", BASE)
    _write("w3b_v1_mass_hugeint.json", v1)
    _write("w3b_v2_tensor_hugeint.json", v2)


if __name__ == "__main__":
    main()
