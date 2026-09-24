"""Generate the preregistered W3 malformed/control fixtures.

Each fixture is a minimal diff of B7's valid two-body coupon report
(agents/B7_faultinjection/fixtures/valid_report.json); every mutation lands on
body_groups[1] (coupon-body-B) unless the case needs otherwise, matching the
M13 evidence location. Deterministic; canonical JSON output.

Run: python work/make_fixtures.py   (from impl/W3_reader_m13/, repo checkout E:/ChimeraWork/mvc-20260924)
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
IMPL = HERE.parent
REPO = IMPL.parents[1].parent
VALID = REPO / "material_volume_campaign/agents/B7_faultinjection/fixtures/valid_report.json"
FIXTURES = IMPL / "tests" / "fixtures"

# Convenience paths into body_groups[1].
TENSOR = ["body_groups", 1, "mass_properties", "inertia_tensor_about_com", "value"]
CENTER = ["body_groups", 1, "mass_properties", "center_of_mass", "value"]
MASS = ["body_groups", 1, "mass_properties", "mass", "value"]


def dig(document, path):
    for key in path:
        document = document[key]
    return document


def mutated(path, value, base=None):
    document = copy.deepcopy(json.loads(VALID.read_text(encoding="utf-8"))) if base is None else base
    dig(document, path[:-1])[path[-1]] = copy.deepcopy(value)
    return document


ROW_A = [0.025, 0.15, 0.025]   # body-B's authored rows (symmetric, finite)
ROW_B = [0.025, 0.025, 0.15]
FULL = [ROW_A, ROW_B, ROW_A]

CASES = {
    # --- crash class (prereg T1..T13): currently UNCAUGHT coercion exceptions ---
    "t01_ragged_truncated_row": mutated(TENSOR, [ROW_A[:2], ROW_B, ROW_A]),
    "t02_deep_ragged":          mutated(TENSOR, [ROW_A, ROW_B[:2] + [[0.15]], ROW_A]),
    "t03_rect_string_entry":    mutated(TENSOR, [["x"] + ROW_A[1:], ROW_B, ROW_A]),
    "t04_dict_value":           mutated(TENSOR, {"diagonal": [0.15, 0.15, 0.15], "off_diagonal": 0.025}),
    "t05_string_scalar":        mutated(TENSOR, "abc"),
    "t06_center_ragged":        mutated(CENTER, [0.25, 0.25, [0.25]]),
    "t07_center_string_entry":  mutated(CENTER, [0.25, 0.25, "x"]),
    "t08_center_dict_value":    mutated(CENTER, {"x": 0.25, "y": 0.25, "z": 0.25}),
    "t09_center_string_scalar": mutated(CENTER, "abc"),
    "t10_mass_null":            mutated(MASS, None),
    "t11_mass_string_bad":      mutated(MASS, "abc"),
    "t12_mass_list":            mutated(MASS, [2.0]),
    "t13_mass_dict":            mutated(MASS, {"kg": 2.0}),
    # --- already-named controls (prereg K1..K5): refusals must stay byte-identical ---
    "k1_wrong_shape_2x2":       mutated(TENSOR, [[0.15, 0.025], [0.025, 0.15]]),
    "k2_center_1x3":            mutated(CENTER, [[0.25, 0.25, 0.25]]),
    "k3_none_entries":          mutated(TENSOR, [[None] + ROW_A[1:], ROW_B, ROW_A]),
    "k4_scalar_tensor":         mutated(TENSOR, 5),
    "k5_combo_wrongshape_badmass": mutated(TENSOR, [[0.15, 0.025], [0.025, 0.15]],
                                           base=mutated(MASS, "abc")),
}

# Shared non-fixture inputs the suite reads in place (never copied/edited):
READ_IN_PLACE = {
    "b7_valid_report": REPO / "material_volume_campaign/agents/B7_faultinjection/fixtures/valid_report.json",
    "b7_corrupt_m13": REPO / "material_volume_campaign/agents/B7_faultinjection/fixtures/corrupt_M13.json",
    "b3_rotcoupon_report": REPO / "material_volume_campaign/agents/B3_roundtrip/fixtures/rotcoupon/report.json",
    "b3_rotcoupon_summary_golden": REPO / "material_volume_campaign/agents/B3_roundtrip/fixtures/rotcoupon/summary.json",
    "b3_shipped_report": REPO / "material_volume_campaign/agents/B3_roundtrip/fixtures/shipped_example/report.json",
    "b3_shipped_summary_golden": REPO / "material_volume_campaign/agents/B3_roundtrip/fixtures/shipped_example/summary.json",
    "shipped_example_report": REPO / "tools/material_volume_body_export_example_report.json",
    "m07_c1_report": REPO / "material_volume_campaign/agents/M07_ownership/receipts/case-c1-export.json",
    "m07_c2_report": REPO / "material_volume_campaign/agents/M07_ownership/receipts/case-c2-export.json",
    "m07_c3_report": REPO / "material_volume_campaign/agents/M07_ownership/receipts/case-c3-export.json",
    "m07_c4_report": REPO / "material_volume_campaign/agents/M07_ownership/receipts/case-c4-export.json",
    "m07_r5_tampered": REPO / "material_volume_campaign/agents/M07_ownership/fixtures/probe-r5-tampered-blocked-with-mass.json",
}


def main() -> int:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    written = []
    for name, document in CASES.items():
        text = json.dumps(document, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=True, allow_nan=False) + "\n"
        target = FIXTURES / f"{name}.json"
        target.write_text(text, encoding="utf-8", newline="\n")
        written.append(target.name)
    print(f"wrote {len(written)} fixtures to {FIXTURES}")
    missing = [str(p) for p in READ_IN_PLACE.values() if not p.is_file()]
    if missing:
        print("MISSING read-in-place inputs:", missing)
        return 1
    print(f"verified {len(READ_IN_PLACE)} read-in-place evidence inputs exist")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
