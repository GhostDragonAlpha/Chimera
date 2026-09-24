"""B7 fault-injection runner. Preregistration-gated: refuses to run without
work/mutation_matrix_frozen.json. Applies each mutation to a COPY of the valid
baseline report (never to tools/), runs the reader (in-process + CLI) and the
exporter-regeneration oracle on each corrupted copy, and judges the observed
result against the FROZEN prediction. All writes stay inside this agent dir.
"""
from __future__ import annotations

import copy
import difflib
import json
import os
import subprocess
import sys
from pathlib import Path

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
HERE = Path(__file__).resolve().parent
WORK = HERE / "work"
FIX = HERE / "fixtures"
RCPT = HERE / "receipts"
sys.path.insert(0, str(WORK))

import material_volume_body_export as exporter          # work/ copy
import material_volume_body_export_reader as reader     # work/ copy

MATRIX_PATH = WORK / "mutation_matrix_frozen.json"
if not MATRIX_PATH.exists():
    sys.exit("FROZEN MATRIX MISSING - preregistration violated; refusing to run.")
MATRIX = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
PRED = {row["id"]: row for row in MATRIX["matrix"]}

VALID = json.loads((FIX / "valid_report.json").read_text(encoding="utf-8"))
VALID_BYTES = (FIX / "valid_report.json").read_bytes()
PRISTINE_REGEN = exporter.canonical_json(VALID)

INPUTS = {}
for name in ("material_volume_body_export_manifest_example.json",
             "material_volume_body_export_partition_example.json",
             "material_volume_body_export_groups_example.json"):
    INPUTS[name] = json.loads((FIX / "inputs" / name).read_text(encoding="utf-8"))

# body_groups are sorted by body_id by the exporter: index 0 = coupon-body-A.
A = "coupon-body-A"
B = "coupon-body-B"


def group(doc, body_id):
    return next(row for row in doc["body_groups"] if row["body_id"] == body_id)


def m01(d):
    group(d, B)["mass_properties"]["inertia_tensor_about_com"]["value"][0][1] = -0.0125

def m02(d):
    group(d, B)["mass_properties"]["inertia_tensor_about_com"]["value"][0][0] = 0.076

def m03(d):
    group(d, A)["mass_properties"]["inertia_tensor_about_com"]["value"][0][1] = 0.0251

def m04(d):
    group(d, A)["mass_properties"]["mass"]["value"] = 2.5

def m05(d):
    group(d, A)["mass_properties"]["mass"]["value"] = -2.0

def m06(d):
    group(d, A)["mass_properties"]["center_of_mass"]["value"][0] = 0.75

def m07(d):
    g = group(d, A)
    for row in g["cell_provenance"]:
        row["density_kg_m3"] = 13.0
    for rec in g["material_mass_source_provenance"]["material_records"]:
        rec["density_kg_m3"] = 13.0

def m08(d):
    del group(d, A)["material_mass_source_provenance"]

def m09(d):
    g = group(d, A)
    for row in g["cell_provenance"]:
        row["mass_owner_id"] = "owner-IMPOSTOR"
    g["material_mass_source_provenance"]["mass_owner_ids"] = ["owner-IMPOSTOR"]

def m10(d):
    d["export_status"] = "partial"

def m10b(d):
    group(d, A)["export_status"] = "not_exported"

def m11(d):
    d["dynamics_readiness_claimed"] = True

def m12(d):
    group(d, A)["admission_report_sha256"] = "0" * 64

def m13(d):
    group(d, B)["mass_properties"]["inertia_tensor_about_com"]["value"][0] = [0.075, 0.0125]

def m14(d):
    group(d, A)["mass_properties"]["inertia_tensor_about_com"]["value"][2][2] = float("nan")


MUTATORS = {f"M{i:02d}": fn for i, fn in
            [(1, m01), (2, m02), (3, m03), (4, m04), (5, m05), (6, m06),
             (7, m07), (8, m08), (9, m09), (10, m10), (11, m11), (12, m12),
             (13, m13), (14, m14)]}
MUTATORS["M10b"] = m10b
REPORT_IDS = ["M01", "M02", "M03", "M04", "M05", "M06", "M07", "M08", "M09",
              "M10", "M10b", "M11", "M12", "M13", "M14"]


def run_input_control(cid: str) -> dict:
    """M07b / M09b: mutate INPUT copies, regenerate via the exporter public API."""
    manifest = copy.deepcopy(INPUTS["material_volume_body_export_manifest_example.json"])
    partition = copy.deepcopy(INPUTS["material_volume_body_export_partition_example.json"])
    groups = copy.deepcopy(INPUTS["material_volume_body_export_groups_example.json"])
    if cid == "M07b":
        for mat in partition["materials"]:
            if mat["material_id"] == "tissue-A":
                mat["density_kg_m3"] = None
                mat["density_source"] = None
                mat["conditions"] = None
    elif cid == "M09b":
        owner_a = partition["regions"][0]["mass_owner_id"]
        partition["regions"][1]["mass_owner_id"] = owner_a
        manifest["regions"][1]["mass_owner_id"] = owner_a
        manifest["matter_ownership"][1]["mass_owner_id"] = owner_a
    else:
        sys.exit(f"unknown control {cid}")
    in_dir = FIX / f"inputs_mutated_{cid}"
    in_dir.mkdir(exist_ok=True)
    for name, doc in (("manifest.json", manifest), ("partition.json", partition),
                      ("groups.json", groups)):
        (in_dir / name).write_text(json.dumps(doc, indent=2, allow_nan=False) + "\n",
                                   encoding="utf-8")
    report = exporter.build_export_report(manifest, partition, groups)
    observed = {
        "export_status": report["export_status"],
        "admission_status": report["admission_status"],
        "admission_reason_codes": report.get("admission_reason_codes", []),
        "reason_codes": report.get("reason_codes", []),
        "group0_mass_properties_none":
            report["body_groups"][0]["mass_properties"] is None,
    }
    return {"observed": observed,
            "mutated_inputs_dir": str(in_dir),
            "regenerated_report": report}


def reader_cli(path: Path) -> tuple[int, str]:
    proc = subprocess.run([sys.executable, str(WORK / "material_volume_body_export_reader.py"),
                           str(path)], capture_output=True, text=True, encoding="utf-8",
                          env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    return proc.returncode, (proc.stderr.strip() or proc.stdout.strip()[:400])


def predict_match(row: dict, detected: bool, reason: str | None) -> str:
    pv = row["predicted_verdict"]
    if pv == "DETECTED":
        return "MATCH-DETECTED" if detected else \
            f"FALSIFIED (predicted {row['predicted_detector']} would catch; silent pass: {reason})"
    if detected:
        return f"SURPRISE-DETECTED (predicted MISSED; caught as {reason})"
    return "MATCH-MISSED (silent pass confirmed)"


results = []
for cid in REPORT_IDS:
    row = PRED[cid]
    mutated = copy.deepcopy(VALID)
    MUTATORS[cid](mutated)
    fix_path = FIX / f"corrupt_{cid}.json"
    fix_path.write_text(json.dumps(mutated, indent=2, allow_nan=True) + "\n",
                        encoding="utf-8")
    before = json.dumps(VALID, sort_keys=True, indent=1).splitlines()
    after = json.dumps(mutated, sort_keys=True, indent=1, allow_nan=True).splitlines()
    diff = "\n".join(difflib.unified_diff(before, after, "valid", cid, lineterm=""))
    (RCPT / "diffs").mkdir(exist_ok=True)
    (RCPT / "diffs" / f"{cid}.diff").write_text(diff + "\n", encoding="utf-8")

    # (a) in-process reader validation (the consumption-time check)
    inproc = "PASS"
    try:
        reader.summarize_export_report(json.loads(fix_path.read_text(encoding="utf-8")))
    except exporter.ExportInputError as err:
        inproc = f"ExportInputError({err.reason}: {err.detail})"
    except (ValueError, TypeError, KeyError) as err:
        # A crash that is NOT a named ExportInputError: still a loud failure,
        # but the reader's refusal contract (named reason) is violated.
        inproc = f"UNCAUGHT-{type(err).__name__}({err})"
    # (b) reader CLI on the corrupted file (strict loader + validation)
    code, msg = reader_cli(fix_path)
    # (c) regeneration oracle (secondary evidence, not an existing check)
    try:
        regen_differs = exporter.canonical_json(mutated) != PRISTINE_REGEN
    except ValueError:
        # e.g. M14: the canonical serializer itself (allow_nan=False) refuses NaN
        regen_differs = "True (canonical_json refuses to serialize: non-NaN-compliant value)"
    detected = inproc != "PASS" or code != 0
    reason = inproc if inproc != "PASS" else (f"CLI exit {code}: {msg}" if code else None)
    if detected and inproc.startswith("UNCAUGHT-"):
        judgement = ("MATCH-DETECTED-PATH-DIFFERS (loud failure confirmed, but via an "
                     "uncaught exception, not the predicted named refusal)")
    else:
        judgement = predict_match(row, detected, reason)
    results.append({
        "id": cid, "canonical_mutation": row["canonical_mutation"],
        "variant": row["variant"], "target": row["target"],
        "predicted_verdict": row["predicted_verdict"],
        "predicted_detector": row["predicted_detector"],
        "reader_in_process": inproc, "reader_cli_exit": code, "reader_cli_msg": msg,
        "regeneration_diff_would_flag": regen_differs,
        "observed_detected": detected, "detection_evidence": reason,
        "judgement": judgement,
    })
    print(f"[{cid}] predicted={row['predicted_verdict']:8s} "
          f"inproc={inproc[:60]:60s} cli_exit={code} -> {results[-1]['judgement'][:80]}")

for cid in ("M07b", "M09b"):
    row = PRED[cid]
    out = run_input_control(cid)
    obs = out["observed"]
    detected = (obs["export_status"] in {"blocked", "refused", "unsupported"}
                and obs["export_status"] != "complete")
    why = (f"export_status={obs['export_status']}, admission={obs['admission_status']}, "
           f"admission_reason_codes={obs['admission_reason_codes']}, "
           f"reason_codes={obs['reason_codes']}, group0 mass_properties is None: "
           f"{obs['group0_mass_properties_none']}")
    (RCPT / f"{cid}_regenerated_report.json").write_text(
        exporter.canonical_json(out["regenerated_report"]), encoding="utf-8")
    results.append({
        "id": cid, "canonical_mutation": row["canonical_mutation"],
        "variant": row["variant"], "target": row["target"],
        "predicted_verdict": row["predicted_verdict"],
        "predicted_detector": row["predicted_detector"],
        "reader_in_process": "n/a (input-level control)",
        "reader_cli_exit": None, "reader_cli_msg": None,
        "regeneration_diff_would_flag": None,
        "observed_detected": detected, "detection_evidence": why,
        "judgement": predict_match(row, detected, why),
    })
    print(f"[{cid}] predicted={row['predicted_verdict']:8s} {why[:100]} -> "
          f"{results[-1]['judgement'][:60]}")

(HERE / "work" / "results.json").write_text(
    json.dumps(results, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

falsified = [r for r in results if r["judgement"].startswith("FALSIFIED")]
surprises = [r for r in results if r["judgement"].startswith("SURPRISE")]
missed = [r for r in results if r["judgement"].startswith("MATCH-MISSED")]
detected = [r for r in results if r["judgement"] == "MATCH-DETECTED"]
print("\n==== TALLY ====")
print(f"DETECTED (as predicted): {len(detected)} -> {[r['id'] for r in detected]}")
print(f"MISSED   (as predicted): {len(missed)} -> {[r['id'] for r in missed]}")
print(f"SURPRISE-DETECTED:       {len(surprises)} -> {[r['id'] for r in surprises]}")
print(f"FALSIFIED (headline):    {len(falsified)} -> {[r['id'] for r in falsified]}")
for r in falsified:
    print(f"  FALSIFIER {r['id']}: {r['judgement']}")
