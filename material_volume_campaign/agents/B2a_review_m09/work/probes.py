"""B2a Area-4 adversarial probes + Area-5 U7 verification.

Fixtures are hand-crafted in MY dir. For each: first ask the reader (public API)
whether it accepts, then run a verbatim copy of the committed CLI in human and
json mode and record exit code + relevant output. Classify each probe.
"""
from __future__ import annotations
import copy
import json
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
MY = Path(__file__).resolve().parent
WORKTREE = Path("E:/ChimeraWork/mvc-20260924")
TOOLS = WORKTREE / "tools"
CLI = MY / "m09_copy" / "material_volume_diagnostic.py"
PROBE = MY / "probes"
PROBE.mkdir(exist_ok=True)
sys.path.insert(0, str(TOOLS))
import material_volume_body_export as exporter  # noqa: E402
import material_volume_body_export_reader as reader  # noqa: E402
import os
ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")

BASE = {  # skeleton accepted by the reader; mutated per probe
    "schema_version": "chimera.rigid_body_mass_export.v1",
    "export_status": "complete",
    "body_groups": [
        {"body_id": "body-A", "export_status": "exported",
         "owned_cell_ids": ["cell-A"],
         "mass_properties": {
             "mass": {"value": 2.0, "unit": "kg"},
             "center_of_mass": {"value": [0.0, 0.0, 0.0], "unit": "m",
                                "coordinate_frame": "frame-A"},
             "inertia_tensor_about_com": {
                 "value": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
                 "unit": "kg*m^2", "coordinate_frame": "frame-A",
                 "basis": "diagonal-in-body-frame",
                 "full_symmetric_tensor": True,
                 "off_diagonal_terms_preserved": True,
                 "principal_axis_transform_applied": False}},
         "input_hashes": None, "admission_report_sha256": None,
         "admission_status": None},
    ],
    "unassigned_cell_ids": [],
    "unassigned_cells": [],
    "input_hashes": None,
}

probes = {}

# P1 — empty body_groups, root complete
doc = copy.deepcopy(BASE)
doc["body_groups"] = []
probes["P1_empty_body_groups"] = doc

# P2 — all bodies omitted (blocked), row WITHOUT reason_codes/blocking keys
doc = copy.deepcopy(BASE)
doc["export_status"] = "blocked"
doc["body_groups"][0] = {"body_id": "body-A", "export_status": "not_exported",
                         "owned_cell_ids": ["cell-A"], "mass_properties": None}
probes["P2_all_omitted_minimal"] = doc

# P3 — per-body status OUTSIDE the contract vocabulary {exported, not_exported}
doc = copy.deepcopy(BASE)
doc["export_status"] = "partial"
doc["body_groups"][0]["export_status"] = "exploded"
probes["P3_out_of_vocab_body_status"] = doc

# P4 — unassigned_cell_ids as STRING (reader does not validate it)
doc = copy.deepcopy(BASE)
doc["export_status"] = "partial"
doc["unassigned_cell_ids"] = "cell-B"
probes["P4_unassigned_ids_string"] = doc

# P5 — unassigned_cells rows as plain strings (reader does not validate them)
doc = copy.deepcopy(BASE)
doc["export_status"] = "partial"
doc["unassigned_cell_ids"] = ["cell-B"]
doc["unassigned_cells"] = ["cell-B", "cell-C"]
probes["P5_unassigned_rows_strings"] = doc

# P6 — deeply nested reason_codes (parser-level recursion bomb)
doc = copy.deepcopy(BASE)
deep = []
for _ in range(2000):
    deep = [deep]
doc["export_status"] = "refused"
doc["body_groups"] = []
doc["reason_codes"] = deep
doc["detail"] = "depth bomb"
probes["P6_deep_reason_codes"] = doc

lines = []


def run_cli(args):
    return subprocess.run([sys.executable, str(CLI), *args],
                          capture_output=True, text=True, env=ENV)


for name, doc in probes.items():
    path = PROBE / f"{name}.json"
    path.write_text(json.dumps(doc), encoding="utf-8")
    # 1) does the reader accept it? (public API, in-process)
    try:
        raw = exporter.read_json_file(str(path))
        summary = reader.summarize_export_report(raw)
        reader_verdict = f"ACCEPTED status={summary['export_status']}"
    except exporter.ExportInputError as error:
        reader_verdict = f"REJECTED reason={error.reason}"
        summary = None
    lines.append(f"### {name}: reader {reader_verdict}")
    # 2) CLI json mode
    proc = run_cli([str(path), "--json"])
    crash = "Traceback" in proc.stderr
    lines.append(f"  json: exit={proc.returncode} crash={crash}"
                 + (f" LAST_ERR={proc.stderr.strip().splitlines()[-1][:160]}"
                    if crash else ""))
    # 3) CLI human mode
    proc = run_cli([str(path)])
    crash = "Traceback" in proc.stderr
    lines.append(f"  human: exit={proc.returncode} crash={crash}")
    if crash:
        lines.append(f"    LAST_ERR={proc.stderr.strip().splitlines()[-1][:200]}")
    else:
        interesting = [ln for ln in proc.stdout.splitlines()
                       if "unassigned" in ln or "export_status" in ln
                       or "reason_codes" in ln or ln.startswith("readiness")]
        lines.extend(f"    | {ln.strip()}" for ln in interesting)
lines.append("")
lines.append("### P7 invocation errors (no fixture)")
proc = run_cli([str(PROBE / "does_not_exist.json")])
lines.append(f"  nonexistent path: exit={proc.returncode} "
             f"stderr={proc.stderr.strip().splitlines()[-1][:120] if proc.stderr.strip() else ''}")
proc = run_cli([str(TOOLS)])
lines.append(f"  directory as path: exit={proc.returncode} crash={'Traceback' in proc.stderr}")
proc = run_cli([])
lines.append(f"  no arguments (usage): exit={proc.returncode} "
             f"stderr_first={proc.stderr.splitlines()[0][:80] if proc.stderr else ''}")
proc = run_cli([str(PROBE / "P1_empty_body_groups.json"), "--bogus-flag"])
lines.append(f"  bogus flag (usage): exit={proc.returncode}")

(Path(__file__).resolve().parents[1] / "receipts" / "b2a_probes_receipt.txt").write_text(
    "\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
