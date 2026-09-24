"""B2a C1.5/C1.6/C1.7: fixture authenticity, exit codes, readiness sweep.

Runs a verbatim copy of the committed CLI (work/m09_copy) on:
  - the shipped example report (read-only)
  - my own genuine exporter fixtures (built here, written only in my dir)
  - two hand-written malformed fixtures
and checks exit codes + readiness in every output (human and JSON).
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
sys.path.insert(0, str(TOOLS))
sys.dont_write_bytecode = True  # re-assert after path ops
import material_volume_body_export as exporter  # noqa: E402

import os
env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
lines = []


def run(args, label):
    proc = subprocess.run([sys.executable, str(CLI), *args],
                          capture_output=True, text=True, env=env)
    lines.append(f"=== {label}: exit={proc.returncode} ===")
    if proc.stderr.strip():
        lines.append(f"[stderr] {proc.stderr.strip()}")
    return proc


manifest = exporter.read_json_file(str(TOOLS / "material_volume_body_export_manifest_example.json"))
partition = exporter.read_json_file(str(TOOLS / "material_volume_body_export_partition_example.json"))
groups = exporter.read_json_file(str(TOOLS / "material_volume_body_export_groups_example.json"))

# C1.5 fixture authenticity, my own construction
mine_complete = exporter.build_export_report(manifest, partition, groups)
shipped_bytes = (TOOLS / "material_volume_body_export_example_report.json").read_text(encoding="utf-8")
rebuilt_bytes = exporter.canonical_json(mine_complete)
authentic = rebuilt_bytes == shipped_bytes
lines.append(f"C1.5 build_export_report(examples) canonical == shipped example bytes: {authentic}")

fixtures = {}
fixtures["complete"] = MY / "fx_complete.json"
fixtures["complete"].write_text(rebuilt_bytes, encoding="utf-8")

g2 = copy.deepcopy(groups); g2["body_groups"] = [r for r in g2["body_groups"] if r["body_id"] != "coupon-body-B"]
fixtures["partial"] = MY / "fx_partial.json"
fixtures["partial"].write_text(exporter.canonical_json(exporter.build_export_report(manifest, partition, g2)), encoding="utf-8")

p2 = copy.deepcopy(partition); p2["regions"][1]["material_id"] = "tissue-MISSING"
fixtures["blocked"] = MY / "fx_blocked.json"
fixtures["blocked"].write_text(exporter.canonical_json(exporter.build_export_report(manifest, p2, groups)), encoding="utf-8")

m2 = copy.deepcopy(manifest); m2["mass_authority"] = "source_effective_segment_mass"
fixtures["unsupported"] = MY / "fx_unsupported.json"
fixtures["unsupported"].write_text(exporter.canonical_json(exporter.build_export_report(m2, partition, groups)), encoding="utf-8")

g3 = copy.deepcopy(groups); g3["body_groups"][0]["body_id"] = "   "
fixtures["refused"] = MY / "fx_refused.json"
fixtures["refused"].write_text(exporter.canonical_json(exporter.build_export_report(manifest, partition, g3)), encoding="utf-8")

fixtures["malformed_version"] = MY / "fx_malformed_version.json"
fixtures["malformed_version"].write_text(json.dumps({
    "schema_version": "chimera.rigid_body_mass_export.v0",
    "export_status": "complete", "body_groups": []}), encoding="utf-8")

# C1.6 + C1.7 over all fixtures, human + json
readiness_bad = []
exit_map = {}
for name, path in fixtures.items():
    proc = run([str(path)], f"{name} human")
    exit_map.setdefault(name, set()).add(proc.returncode)
    tail = proc.stdout.rstrip("\n").splitlines()[-1]
    lines.append(f"  final line: {tail}")
    if tail != "readiness: false":
        readiness_bad.append((name, "human", tail))
    if "readiness_claimed: true" in proc.stdout or "readiness: true" in proc.stdout:
        readiness_bad.append((name, "human", "true literal found"))
    proc = run([str(path), "--json"], f"{name} json")
    exit_map.setdefault(name, set()).add(proc.returncode)
    payload = json.loads(proc.stdout)
    if payload["readiness"] is not False:
        readiness_bad.append((name, "json", payload["readiness"]))
    for entry in payload["reports"]:
        if entry.get("ok") and entry["readiness_claimed"] is not False:
            readiness_bad.append((name, "json", entry["readiness_claimed"]))
lines.append(f"C1.6 exit codes observed: {json.dumps({k: sorted(v) for k, v in exit_map.items()})}")
lines.append(f"C1.7 readiness violations found: {readiness_bad if readiness_bad else 'NONE'}")
(Path(__file__).resolve().parents[1] / "receipts" / "b2a_claims_receipt.txt").write_text(
    "\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
