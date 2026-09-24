"""M04 rigid-covariance: compare receipts against the FROZEN expectations.

Reads prereg_expectations.json (want + tolerance + falsifier, written before
any run) and receipts/<run>.json (got).  Emits receipts/comparison.json with
per-run per-quantity verdicts and prints the report tables.  No expectation is
recomputed or adjusted here; this script only measures.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
AGENTS = HERE.parent
RECEIPTS = AGENTS / "receipts"
EXPECT = json.loads((AGENTS / "prereg_expectations.json").read_text(encoding="utf-8"))
LIMIT = float(EXPECT["tolerance"]["limit"])


def check(got: np.ndarray, want: np.ndarray) -> dict:
    dev = np.abs(got - want)
    dev_max = float(dev.max())
    scale = float(np.abs(want).max())
    fro = float(np.linalg.norm(got - want) / np.linalg.norm(want))
    return {"dev_max": dev_max, "want_scale": scale,
            "entrywise_ok": bool(dev_max <= LIMIT * scale),
            "frobenius_ratio": fro,
            "frobenius_ok": bool(fro <= LIMIT),
            "pass": bool(dev_max <= LIMIT * scale and fro <= LIMIT)}


def main() -> int:
    report = {"limit": LIMIT, "runs": {}, "all_pass": True}
    for run_id, want_run in EXPECT["expectations"]["runs"].items():
        doc = json.loads((RECEIPTS / f"{run_id}.json").read_text(encoding="utf-8"))
        group = doc["body_groups"][0]
        row: dict = {"export_status": doc["export_status"],
                     "admission_status": doc["admission_status"],
                     "group_status": group["export_status"],
                     "unassigned_cell_ids": doc["unassigned_cell_ids"],
                     "frame_id": group["body_frame"]["frame_id"],
                     "quantities": {}}
        structural_ok = (doc["export_status"] == "complete"
                         and group["export_status"] == "exported"
                         and doc["unassigned_cell_ids"] == []
                         and doc["admission_status"] == "validation_only_admissible")
        row["structural_ok"] = structural_ok
        props = group.get("mass_properties") or {}
        mass = props.get("mass", {})
        volume = props.get("volume", {})
        com = props.get("center_of_mass", {})
        inertia = props.get("inertia_tensor_about_com", {})
        got_mass = np.asarray([[float(mass.get("value", math.nan))]])
        got_volume = np.asarray([[float(volume.get("value", math.nan))]])
        got_com = np.asarray(com.get("value", [math.nan] * 3), dtype=np.float64)
        got_inertia = np.asarray(inertia.get("value",
                                            [[math.nan] * 3] * 3), dtype=np.float64)
        row["quantities"]["mass_kg"] = check(got_mass, np.asarray(
            [[EXPECT["expectations"]["mass_kg"]]]))
        row["quantities"]["volume_m3"] = check(got_volume, np.asarray(
            [[EXPECT["expectations"]["volume_m3"]]]))
        row["quantities"]["center_of_mass"] = check(got_com, np.asarray(
            want_run["com"], dtype=np.float64))
        row["quantities"]["inertia_tensor"] = check(got_inertia, np.asarray(
            want_run["inertia"], dtype=np.float64))
        row["tensor_contract"] = {
            "full_symmetric_tensor": inertia.get("full_symmetric_tensor"),
            "off_diagonal_terms_preserved": inertia.get("off_diagonal_terms_preserved"),
            "principal_axis_transform_applied": inertia.get("principal_axis_transform_applied"),
            "coordinate_frame": inertia.get("coordinate_frame"),
            "basis": inertia.get("basis")}
        run_pass = (structural_ok
                    and all(q["pass"] for q in row["quantities"].values()))
        row["run_pass"] = run_pass
        report["all_pass"] = report["all_pass"] and run_pass
        report["runs"][run_id] = row

    # independent float cross-check: A2 export must equal R @ A0_export @ R.T
    a0 = json.loads((RECEIPTS / "run_A0_identity.json").read_text(encoding="utf-8"))
    a2 = json.loads((RECEIPTS / "run_A2_rotation.json").read_text(encoding="utf-8"))
    R = np.asarray(EXPECT["motion"]["R"], dtype=np.float64)
    com0 = np.asarray(a0["body_groups"][0]["mass_properties"]["center_of_mass"]["value"])
    I0 = np.asarray(a0["body_groups"][0]["mass_properties"]["inertia_tensor_about_com"]["value"])
    com2 = np.asarray(a2["body_groups"][0]["mass_properties"]["center_of_mass"]["value"])
    I2 = np.asarray(a2["body_groups"][0]["mass_properties"]["inertia_tensor_about_com"]["value"])
    report["float_crosscheck"] = {
        "com_R_com0": check(com2, R @ com0),
        "inertia_R_I0_RT": check(I2, R @ I0 @ R.T),
    }

    (RECEIPTS / "comparison.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")

    # ---- printed tables
    print(f"tolerance: {LIMIT:g} relative (entrywise vs max|want| AND Frobenius)")
    print(f"{'run':34s} {'qty':16s} {'dev_max':>12s} {'1e-9*scale':>12s} "
          f"{'fro_ratio':>12s} {'pass':>5s}")
    for run_id, row in report["runs"].items():
        for qty, res in row["quantities"].items():
            print(f"{run_id:34s} {qty:16s} {res['dev_max']:12.3e} "
                  f"{LIMIT * res['want_scale']:12.3e} "
                  f"{res['frobenius_ratio']:12.3e} {str(res['pass']):>5s}")
        print(f"{run_id:34s} {'STRUCTURE':16s} "
              f"status={row['export_status']}/{row['group_status']} "
              f"unassigned={row['unassigned_cell_ids']} pass={row['run_pass']}")
    print("float crosscheck (independent of exact expectations):")
    print(f"  com_A2 vs R@com_A0        dev {report['float_crosscheck']['com_R_com0']}")
    print(f"  I_A2   vs R@I_A0@R^T      dev {report['float_crosscheck']['inertia_R_I0_RT']}")
    print("ALL_PASS =", report["all_pass"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
