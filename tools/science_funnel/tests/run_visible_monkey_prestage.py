"""Run the Visible Monkey prestage fixtures and BANK the measured numbers.

Writes tools/science_funnel/validation/visible_monkey_intake_20260921/
verify.json (the per-run record: synthetic proof numbers + falsifier
verdicts). Run from repo root:
    python -B tools/science_funnel/tests/run_visible_monkey_prestage.py
"""
from __future__ import annotations

import json
import math
import shutil
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tools.science_funnel import visible_monkey_import as vmi  # noqa: E402
from tools.science_funnel import visible_monkey_volume_route as vmv  # noqa: E402
import test_visible_monkey_intake as batt  # noqa: E402

VALIDATION = (REPO_ROOT / "tools/science_funnel/validation/"
              "visible_monkey_intake_20260921")


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="vm_prestage_measure_"))
    record: dict = {"schema": "chimera.visible_monkey.verify_record.v1"}
    try:
        # ---- translator: synthetic specimen
        spec_path = batt.make_specimen(tmp / "translator")
        vmi.main(["x", "build", str(spec_path)])
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        body = json.loads((Path(spec["output_dir"]) /
                           "visible_monkey.body.json").read_text(encoding="utf-8"))
        book = json.loads((Path(spec["validation_dir"]) /
                           "derivation.json").read_text(encoding="utf-8"))
        checks = json.loads((Path(spec["validation_dir"]) /
                             "verify.json").read_text(encoding="utf-8"))
        mem = {m["structure_id"]: m for m in body["membranes"]}

        vols = {}
        for sid, m in mem.items():
            analytic = batt.ANALYTIC_VOLUME_MM3[sid]
            vols[sid] = {
                "volume_mm3_mesh": round(m["volume_mm3"], 6),
                "volume_mm3_analytic": round(analytic, 6),
                "rel": round(abs(m["volume_mm3"] - analytic) / analytic, 9),
                "mass_kg": m["mass"],
                "system": m["system"],
            }
        sphere = vols["skin_sphere"]
        record["translator"] = {
            "compartments": len(mem),
            "expected_count_spec": 7,
            "volumes": vols,
            "sphere_ratio_vs_bound": round(
                sphere["volume_mm3_mesh"]
                / batt.ANALYTIC_VOLUME_MM3["skin_sphere"], 6),
            "worst_exact_volume_rel": max(
                vols[s]["rel"] for s in vols
                if s != "skin_sphere"),
            "worst_mass_identity_rel": checks["mass_book"]["measured"][
                "worst_mass_identity_rel_vs_Vrho"],
            "kernel_stated_vs_derived_max_rel": checks["kernel_conformance"][
                "measured"]["stated_vs_kernel_derived_mass_max_rel"],
            "total_mass_g": book["totals"]["total_mass_g"],
            "mass_by_system_kg": book["totals"]["mass_by_system_kg"],
            "whole_animal": book["totals"]["whole_animal_check"],
            "stage": body["stage"],
            "geometry": checks["geometry_preserved"]["measured"],
            "closed_manifold": checks["closed_manifold"]["measured"],
            "euler_characteristics": {
                sid: mem[sid]["euler_characteristic"] for sid in sorted(mem)},
        }

        # ---- translator: adjacency variant (bonds from measured edges only)
        adj_spec = batt.make_specimen(
            tmp / "adjacency",
            adjacency=[{"pair": ["bone_box", "bone_octa"], "gap_mm": 1.23,
                        "source": "synthetic touching-edge measurement"}])
        vmi.main(["x", "build", str(adj_spec)])
        adj_body = batt.read_body(adj_spec)
        record["translator_adjacency"] = {
            "bonds": len(adj_body["bonds"]),
            "rest_lengths": [b["rest_length_mm"] for b in adj_body["bonds"]],
        }

        # ---- volume route: synthetic phantom
        vspec_path = batt.VolumeRoute.phantom_spec(tmp / "volume")
        vmv.main(["x", "build", str(vspec_path)])
        vspec = json.loads(vspec_path.read_text(encoding="utf-8"))
        manifest = json.loads(
            Path(vspec["outputs"]["manifest"]).read_text(encoding="utf-8"))
        comp = manifest["components"][0]
        analytic = (4 / 3 * math.pi * 12 * 17 * 25 * 0.5 * 0.5 * 0.5)
        record["volume_route"] = {
            "components_kept": manifest["segmentation"]["components_kept"],
            "threshold": manifest["threshold"],
            "voxel_mm": manifest["voxel_mm"],
            "volume_mm3_mesh": comp["volume_mm3_mesh"],
            "volume_mm3_analytic": round(analytic, 6),
            "volume_rel_err": round(
                abs(comp["volume_mm3_mesh"] - analytic) / analytic, 6),
            "voxel_delta_pct": comp["voxel_delta_pct"],
            "faces": comp["faces"],
            "preview_faces": comp["preview_faces"],
            "receipt_sha256_entries": len(
                json.loads(Path(vspec["outputs"]["receipt"])
                           .read_text(encoding="utf-8"))["sha256"]),
        }
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    VALIDATION.mkdir(parents=True, exist_ok=True)
    text = json.dumps(record, indent=1, ensure_ascii=False,
                      allow_nan=False) + "\n"
    (VALIDATION / "verify.json").write_text(text, encoding="utf-8",
                                            newline="\n")
    print(text)
    print(f"banked: {VALIDATION / 'verify.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
