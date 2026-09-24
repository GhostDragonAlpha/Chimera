"""Generate M07 fixtures by minimal diffs from the existing example schemas.

Read-only inputs: tools/material_volume_body_export_{manifest,partition,groups}_example.json.
Outputs: fixtures/case-*.json. Deterministic; run with PYTHONDONTWRITEBYTECODE=1.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

TOOLS = Path("E:/ChimeraWork/mvc-20260924/tools")
HERE = Path(__file__).resolve().parent.parent
FIX = HERE / "fixtures"


def load(name: str) -> dict:
    return json.loads((TOOLS / name).read_text(encoding="utf-8"))


def write(name: str, doc) -> None:
    path = FIX / name
    path.write_text(json.dumps(doc, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    print(f"wrote {path}")


def main() -> None:
    FIX.mkdir(exist_ok=True)
    manifest = load("material_volume_body_export_manifest_example.json")
    partition = load("material_volume_body_export_partition_example.json")
    groups = load("material_volume_body_export_groups_example.json")

    # C1: happy-path control = the example fixtures verbatim (copies).
    write("case-c1-manifest.json", copy.deepcopy(manifest))
    write("case-c1-partition.json", copy.deepcopy(partition))
    write("case-c1-groups.json", copy.deepcopy(groups))

    # C2: duplicate cell ownership - two bodies claim cell-A.
    g2 = copy.deepcopy(groups)
    g2["body_groups"][0]["body_id"] = "body-1"
    g2["body_groups"][0]["cell_ids"] = ["cell-A"]
    g2["body_groups"][1]["body_id"] = "body-2"
    g2["body_groups"][1]["cell_ids"] = ["cell-A", "cell-B"]
    write("case-c2-groups.json", g2)

    # C2b: duplicate body_id - same body_id twice.
    g2b = copy.deepcopy(groups)
    g2b["body_groups"][1]["body_id"] = "coupon-body-A"
    write("case-c2b-groups.json", g2b)

    # C3: unassigned cell - third disjoint positive tet cell-C in no group.
    man3 = copy.deepcopy(manifest)
    man3["fitting_id"] = "two-body-coupon-fit-v1-plus-unassigned-c"
    man3["vertices"] += [
        {"vertex_id": "c0", "position": [0.0, 3.0, 0.0]},
        {"vertex_id": "c1", "position": [1.0, 3.0, 0.0]},
        {"vertex_id": "c2", "position": [0.0, 4.0, 0.0]},
        {"vertex_id": "c3", "position": [0.0, 3.0, 1.0]},
    ]
    man3["cells"].append(
        {"cell_id": "cell-C", "vertex_ids": ["c0", "c1", "c2", "c3"],
         "component_id": "component-C"})
    man3["regions"].append(
        {"region_id": "region-C", "mass_owner_id": "owner-C", "material_id": "tissue-C"})
    man3["matter_ownership"].append(
        {"matter_id": "coupon-matter-C", "representation": "tetrahedral_volume",
         "mass_owner_id": "owner-C"})
    par3 = copy.deepcopy(partition)
    par3["vertices"] = man3["vertices"]
    par3["cells"].append(
        {"cell_id": "cell-C", "vertex_ids": ["c0", "c1", "c2", "c3"],
         "proposals": ["region-C"]})
    par3["materials"].append(
        {"material_id": "tissue-C", "density_kg_m3": 3.0,
         "density_source": "analytic coupon fixture", "conditions": "uniform"})
    par3["regions"] = man3["regions"]
    write("case-c3-manifest.json", man3)
    write("case-c3-partition.json", par3)
    write("case-c3-groups.json", copy.deepcopy(groups))

    # C4: blocked body - cell-B's material has null density (admission-doc construction).
    par4 = copy.deepcopy(partition)
    for material in par4["materials"]:
        if material["material_id"] == "tissue-B":
            material["density_kg_m3"] = None
    write("case-c4-manifest.json", copy.deepcopy(manifest))
    write("case-c4-partition.json", par4)
    write("case-c4-groups.json", copy.deepcopy(groups))

    # C5: mixed groups - cell-B unresolved (proposals: []), cell-A complete.
    par5 = copy.deepcopy(partition)
    for cell in par5["cells"]:
        if cell["cell_id"] == "cell-B":
            cell["proposals"] = []
    write("case-c5-manifest.json", copy.deepcopy(manifest))
    write("case-c5-partition.json", par5)
    write("case-c5-groups.json", copy.deepcopy(groups))

    # C6: group claims a cell absent from the partition.
    g6 = copy.deepcopy(groups)
    g6["body_groups"][1]["cell_ids"] = ["cell-B", "cell-Z"]
    write("case-c6-groups.json", g6)

    print("done")


if __name__ == "__main__":
    main()
