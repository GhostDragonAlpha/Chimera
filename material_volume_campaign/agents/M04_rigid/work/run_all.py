"""M04 rigid-covariance: execute the 7 preregistered exporter runs.

Runs the byte-identical work/ copy of tools/material_volume_body_export.py once
per preregistered run (CPU-only, PYTHONDONTWRITEBYTECODE=1), capturing stdout,
stderr, exit code, command, and input/output hashes under receipts/.  No tools/
or docs/ file is written.  Expectations are NOT consulted here.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
AGENTS = HERE.parent
FIXTURES = AGENTS / "fixtures"
RECEIPTS = AGENTS / "receipts"
EXPECT = json.loads((AGENTS / "prereg_expectations.json").read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    RECEIPTS.mkdir(exist_ok=True)
    module_hashes = {name: sha256(HERE / name) for name in (
        "material_volume.py", "material_volume_admission.py",
        "material_volume_body_export.py", "material_volume_body_export_reader.py")}
    (RECEIPTS / "module_hashes.json").write_text(
        json.dumps(module_hashes, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.pop("CUDA_VISIBLE_DEVICES", None)  # CPU-only lane; numpy is CPU anyway

    log = []
    for run_id in EXPECT["expectations"]["runs"]:
        cmd = [sys.executable, str(HERE / "material_volume_body_export.py"),
               "--manifest", str(FIXTURES / f"{run_id}_manifest.json"),
               "--partition", str(FIXTURES / f"{run_id}_partition.json"),
               "--groups", str(FIXTURES / f"{run_id}_groups.json")]
        proc = subprocess.run(cmd, capture_output=True, text=True, env=env,
                              cwd=str(AGENTS))
        out_path = RECEIPTS / f"{run_id}.json"
        out_path.write_text(proc.stdout, encoding="utf-8")
        entry = {"run_id": run_id,
                 "command": cmd,
                 "exit_code": proc.returncode,
                 "stdout_sha256": sha256(out_path),
                 "stdout_bytes": len(proc.stdout),
                 "stderr": proc.stderr,
                 "input_sha256": {
                     "manifest": sha256(FIXTURES / f"{run_id}_manifest.json"),
                     "partition": sha256(FIXTURES / f"{run_id}_partition.json"),
                     "groups": sha256(FIXTURES / f"{run_id}_groups.json")}}
        (RECEIPTS / f"{run_id}.log").write_text(
            json.dumps(entry, indent=2) + "\n", encoding="utf-8")
        status = None
        if proc.stdout.strip():
            try:
                status = json.loads(proc.stdout).get("export_status")
            except json.JSONDecodeError:
                status = "UNPARSEABLE"
        entry["export_status"] = status
        log.append(entry)
        print(f"{run_id}: exit={proc.returncode} status={status}")
    (RECEIPTS / "execution_log.json").write_text(
        json.dumps({"runs": log, "module_hashes": module_hashes},
                   indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
