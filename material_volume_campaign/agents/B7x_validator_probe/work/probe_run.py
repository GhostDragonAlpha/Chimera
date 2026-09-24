"""B7x — run B7's nine MISSED mutations through M10's static consumption validator.

Preregistration-gated: refuses to run unless work/preregistration.md exists and
was written before this first execution (it is hashed into the results).

Everything is written ONLY inside agents/B7x_validator_probe/.
B7's and M10's directories are READ-ONLY here: B7 fixtures are read and copied,
M10's validator is invoked via its CLI path (module never modified, and
PYTHONDONTWRITEBYTECODE=1 is set in every subprocess env).
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent            # .../agents/B7x_validator_probe/work
PROBE = HERE.parent                                # .../agents/B7x_validator_probe
AGENTS = PROBE.parent                              # .../material_volume_campaign/agents
B7 = AGENTS / "B7_faultinjection"
M10 = AGENTS / "M10_validator"
VALIDATOR = M10 / "rigid_body_mass_consumption_validator.py"

FIX_REGEN = PROBE / "fixtures" / "regenerated"
FIX_FROZEN = PROBE / "fixtures" / "b7_frozen"
RECEIPTS = PROBE / "receipts"
for d in (FIX_REGEN, FIX_FROZEN, RECEIPTS):
    d.mkdir(parents=True, exist_ok=True)

MISSED = ["M02", "M04", "M06", "M07", "M08", "M09", "M10", "M11", "M12"]


# ---------------------------------------------------------------- mutations --
def apply_mutation(report: dict, mid: str) -> dict:
    """Replicates B7's frozen-matrix target exactly (one mutation per copy)."""
    doc = json.loads(json.dumps(report))  # deep copy
    bodies = {b["body_id"]: b for b in doc["body_groups"]}
    a = bodies["coupon-body-A"]
    b_ = bodies["coupon-body-B"]
    if mid == "M02":
        inertia = b_["mass_properties"]["inertia_tensor_about_com"]
        assert inertia["value"][0][0] == 0.07500000000000001
        inertia["value"][0][0] = 0.076
    elif mid == "M04":
        assert a["mass_properties"]["mass"]["value"] == 2.0
        a["mass_properties"]["mass"]["value"] = 2.5
    elif mid == "M06":
        com = a["mass_properties"]["center_of_mass"]["value"]
        assert com[0] == 0.25
        com[0] = 0.75
    elif mid == "M07":
        for row in a["cell_provenance"]:
            assert row["density_kg_m3"] == 12.0
            row["density_kg_m3"] = 13.0
        records = a["material_mass_source_provenance"]["material_records"]
        for rec in records:
            if rec.get("density_kg_m3") == 12.0:
                rec["density_kg_m3"] = 13.0
    elif mid == "M08":
        del a["material_mass_source_provenance"]
    elif mid == "M09":
        for row in a["cell_provenance"]:
            assert row["mass_owner_id"] == "owner-A"
            row["mass_owner_id"] = "owner-IMPOSTOR"
        owners = a["material_mass_source_provenance"]["mass_owner_ids"]
        owners[:] = ["owner-IMPOSTOR" if o == "owner-A" else o for o in owners]
    elif mid == "M10":
        assert doc["export_status"] == "complete"
        doc["export_status"] = "partial"
    elif mid == "M11":
        assert doc["dynamics_readiness_claimed"] is False
        doc["dynamics_readiness_claimed"] = True
    elif mid == "M12":
        a["admission_report_sha256"] = "0" * 64
    else:
        raise ValueError(f"unknown mutation id {mid}")
    return doc


def build_l2_probe(report: dict) -> dict:
    """M10's declared limit class (adversarial probe A5): silently diagonalized
    tensor — off-diagonals zeroed, symmetry and all three flags kept."""
    doc = json.loads(json.dumps(report))
    b_ = doc["body_groups"][1]
    inertia = b_["mass_properties"]["inertia_tensor_about_com"]
    value = inertia["value"]
    for i in range(3):
        for j in range(3):
            if i != j:
                value[i][j] = 0.0
    assert inertia["full_symmetric_tensor"] is True
    assert inertia["off_diagonal_terms_preserved"] is True
    assert inertia["principal_axis_transform_applied"] is False
    return doc


# ------------------------------------------------------------------ runner --
def run_validator(path: Path) -> dict:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.pop("CHIMERA_TOOLS_DIR", None)  # let the module resolve ../tools itself
    proc = subprocess.run(
        [sys.executable, str(VALIDATOR), str(path), "--indent", "2"],
        capture_output=True, text=True, env=env, timeout=120)
    entry = {"fixture": str(path), "exit_code": proc.returncode,
             "stderr": proc.stderr.strip()}
    if proc.stdout.strip():
        try:
            verdict = json.loads(proc.stdout)
            entry["verdict"] = verdict["verdict"]
            entry["rules_violated"] = verdict.get("rules_violated", [])
            entry["failure_reasons"] = [
                {"rule": f["rule"], "reason": f["reason"]}
                for f in verdict.get("all_rule_failures", [])]
            entry["reader_cross_check"] = verdict.get("reader_cross_check")
        except json.JSONDecodeError:
            entry["verdict"] = "UNPARSEABLE"
            entry["raw_stdout"] = proc.stdout[:2000]
    else:
        entry["verdict"] = "COULD_NOT_EVALUATE"
    return entry


def deep_equal(x, y) -> bool:
    return json.loads(json.dumps(x, sort_keys=True)) == json.loads(json.dumps(y, sort_keys=True))


def main() -> int:
    prereg = HERE / "preregistration.md"
    if not prereg.exists():
        raise SystemExit("preregistration.md missing — refusing to run (preregistration-gated)")
    results = {
        "agent": "B7x_validator_probe",
        "preregistration_sha256": hashlib.sha256(prereg.read_bytes()).hexdigest(),
        "validator": str(VALIDATOR),
        "validator_sha256": hashlib.sha256(VALIDATOR.read_bytes()).hexdigest(),
        "b7_matrix_sha256": hashlib.sha256(
            (B7 / "work" / "mutation_matrix_frozen.json").read_bytes()).hexdigest(),
        "rows": [],
    }

    valid = json.loads((B7 / "fixtures" / "valid_report.json").read_text(encoding="utf-8"))

    # 1. stage frozen copies (read B7, write MY dir)
    (FIX_FROZEN / "valid_report.json").write_bytes(
        (B7 / "fixtures" / "valid_report.json").read_bytes())
    for mid in MISSED:
        (FIX_FROZEN / f"corrupt_{mid}.json").write_bytes(
            (B7 / "fixtures" / f"corrupt_{mid}.json").read_bytes())

    # 2. regenerate mutants locally from the baseline per the frozen matrix
    regen_match = {}
    for mid in MISSED:
        mutant = apply_mutation(valid, mid)
        out = FIX_REGEN / f"corrupt_{mid}.json"
        out.write_text(json.dumps(mutant, indent=2, ensure_ascii=False) + "\n",
                       encoding="utf-8")
        frozen = json.loads(
            (B7 / "fixtures" / f"corrupt_{mid}.json").read_text(encoding="utf-8"))
        regen_match[mid] = deep_equal(mutant, frozen)
    results["regeneration_matches_b7_frozen"] = regen_match

    # 3. L2 probe fixture
    (FIX_REGEN / "L2_diagonalized.json").write_text(
        json.dumps(build_l2_probe(valid), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")

    # 4. run: baseline sanity, then the nine (frozen copy = primary evidence),
    #    regenerated copies as the reproducibility receipt, then the L2 probe.
    log_lines = []
    baseline = run_validator(FIX_FROZEN / "valid_report.json")
    results["baseline"] = baseline
    log_lines.append(f"baseline valid_report -> exit {baseline['exit_code']} "
                     f"{baseline.get('verdict')}")
    if baseline.get("verdict") != "ACCEPT":
        results["infrastructure_failure"] = (
            "clean baseline REJECTED — staging broken; per preregistration falsifier (d), "
            "fix staging, never verdicts")
        (PROBE / "work" / "results.json").write_text(
            json.dumps(results, indent=2), encoding="utf-8")
        print(json.dumps(results, indent=2))
        return 2

    for mid in MISSED:
        row = {"id": mid,
               "frozen": run_validator(FIX_FROZEN / f"corrupt_{mid}.json"),
               "regenerated": run_validator(FIX_REGEN / f"corrupt_{mid}.json"),
               "regeneration_matches_b7_frozen": regen_match[mid]}
        results["rows"].append(row)
        log_lines.append(
            f"{mid} frozen -> exit {row['frozen']['exit_code']} "
            f"{row['frozen'].get('verdict')} rules={row['frozen'].get('rules_violated')} | "
            f"regen -> exit {row['regenerated']['exit_code']} "
            f"{row['regenerated'].get('verdict')} rules={row['regenerated'].get('rules_violated')}")
        (RECEIPTS / f"verdict_{mid}_frozen.json").write_text(
            json.dumps(row["frozen"], indent=2, sort_keys=True), encoding="utf-8")

    l2 = run_validator(FIX_REGEN / "L2_diagonalized.json")
    results["l2_probe"] = l2
    log_lines.append(f"L2 diagonalized probe -> exit {l2['exit_code']} {l2.get('verdict')} "
                     f"rules={l2.get('rules_violated')}")
    (RECEIPTS / "verdict_L2_diagonalized.json").write_text(
        json.dumps(l2, indent=2, sort_keys=True), encoding="utf-8")

    (RECEIPTS / "run_log.txt").write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    (PROBE / "work" / "results.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8")
    print("\n".join(log_lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
