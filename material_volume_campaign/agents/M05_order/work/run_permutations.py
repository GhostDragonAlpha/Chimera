"""M05 run harness: executes the frozen run plan (P0a, P0b, P1..P5).

Each run invokes the MODULE COPY of material_volume_body_export.py (cwd=work/modules,
so imports resolve to the copies) with one fixture triple, capturing raw stdout bytes,
stderr, and the exit code into receipts/. No pipeline code is modified.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FIX = ROOT / "fixtures"
REC = ROOT / "receipts"
MODULES = HERE / "modules"

RUNS = ["P0a", "P0b", "P1-cells-reversed", "P2-cells-shuffled", "P3-groups-reordered",
        "P4-group-cell-records-reversed", "P5-manifest-entries-reversed"]
FIX_FOR = {"P0a": "base", "P0b": "base"}


def main() -> int:
    REC.mkdir(parents=True, exist_ok=True)
    env_note = {"python": sys.version.split()[0], "bytecode": "PYTHONDONTWRITEBYTECODE=1"}
    summary = {}
    for run in RUNS:
        fixture = FIX_FOR.get(run, run)
        cmd = [sys.executable, "material_volume_body_export.py",
               "--manifest", str(FIX / fixture / "manifest.json"),
               "--partition", str(FIX / fixture / "partition.json"),
               "--groups", str(FIX / fixture / "groups.json")]
        import os
        child_env = dict(os.environ)
        child_env["PYTHONDONTWRITEBYTECODE"] = "1"
        proc = subprocess.run(cmd, cwd=MODULES, capture_output=True, env=child_env)
        out_path = REC / f"run_{run}.stdout.json"
        err_path = REC / f"run_{run}.stderr.txt"
        out_path.write_bytes(proc.stdout)
        err_path.write_bytes(proc.stderr)
        digest = hashlib.sha256(proc.stdout).hexdigest()
        summary[run] = {
            "fixture": fixture, "exit_code": proc.returncode,
            "stdout_sha256": digest, "stdout_bytes": len(proc.stdout),
            "stderr": proc.stderr.decode("utf-8", "replace") or None,
            "cmd": cmd, "env": env_note,
        }
        print(run, proc.returncode, digest, len(proc.stdout), "bytes")
    (REC / "runs_summary.json").write_text(
        json.dumps(summary, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
