"""W5 CLI battery: prove original M09 CLI and home promotion copy are
behaviorally identical (stdout bytes, stderr bytes, exit code) on a shared
fixture battery, and that both resolve the SAME tools/ directory by default.

Read-only: fixtures are copied ONCE from the committed agents/M09_diagnostic/
work/ fixtures into this dir (battery/); both CLIs only ever read them.
PYTHONDONTWRITEBYTECODE=1 in every child (F1 discipline).
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

WORKTREE = Path(r"E:/ChimeraWork/mvc-20260924")
W5 = WORKTREE / "material_volume_campaign/impl/W5_diag_promo"
ORIG_CLI = WORKTREE / "material_volume_campaign/agents/M09_diagnostic/material_volume_diagnostic.py"
HOME_CLI = W5 / "home/material_volume_diagnostic.py"
BATTERY = W5 / "receipts/battery"
FIXTURE_NAMES = [
    "fixture_complete.json", "fixture_partial.json", "fixture_blocked.json",
    "fixture_unsupported.json", "fixture_refused.json",
    "fixture_malformed_version.json", "fixture_malformed_duplicate_key.json",
    "fixture_hostile_string_ids.json", "fixture_hostile_string_rows.json",
    "fixture_hostile_no_unassigned_cells.json",
]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run(cli: Path, args: list[str]) -> dict:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    proc = subprocess.run([sys.executable, str(cli), *args],
                          capture_output=True, env=env)
    return {"rc": proc.returncode,
            "out_sha": sha(proc.stdout), "out_bytes": len(proc.stdout),
            "err_sha": sha(proc.stderr), "err_bytes": len(proc.stderr),
            "out": proc.stdout, "err": proc.stderr}


def main() -> int:
    BATTERY.mkdir(parents=True, exist_ok=True)
    src_dir = ORIG_CLI.parent / "work"
    for name in FIXTURE_NAMES:
        shutil.copyfile(src_dir / name, BATTERY / name)

    cases: list[tuple[str, list[str]]] = []
    for name in FIXTURE_NAMES:
        path = str(BATTERY / name)
        cases.append((f"{name} human", [path]))
        cases.append((f"{name} json", [path, "--json"]))
    cases.append(("usage no-args", []))
    cases.append(("usage bogus-flag", [str(BATTERY / "fixture_complete.json"),
                                       "--bogus-flag"]))

    rows = []
    mismatches = 0
    for label, args in cases:
        a = run(ORIG_CLI, args)
        b = run(HOME_CLI, args)
        same = (a["rc"] == b["rc"] and a["out_sha"] == b["out_sha"]
                and a["err_sha"] == b["err_sha"])
        mismatches += 0 if same else 1
        rows.append({"case": label, "identical": same,
                     "orig": {k: a[k] for k in ("rc", "out_sha", "err_sha")},
                     "home": {k: b[k] for k in ("rc", "out_sha", "err_sha")},
                     "args": args})

    # P3: default tools-dir resolution from both CLI locations
    resolution = {}
    for tag, cli in (("orig", ORIG_CLI), ("home", HOME_CLI)):
        proc = subprocess.run(
            [sys.executable, "-c",
             "import importlib.util, json, sys;"
             "spec = importlib.util.spec_from_file_location('d', sys.argv[1]);"
             "m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m);"
             "print(json.dumps(str(m.find_tools_dir(None))))",
             str(cli)],
            capture_output=True, text=True,
            env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
        resolution[tag] = json.loads(proc.stdout.strip())

    report = {
        "battery_fixture_sha256": {
            name: sha((BATTERY / name).read_bytes()) for name in FIXTURE_NAMES},
        "cases": rows,
        "case_count": len(cases),
        "mismatch_count": mismatches,
        "default_tools_dir_resolution": resolution,
        "same_resolution": resolution["orig"] == resolution["home"],
    }
    (W5 / "receipts/cli_battery_equivalence.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"cases={len(cases)} mismatches={mismatches} "
          f"same_tools_resolution={report['same_resolution']} "
          f"tools_dir={resolution['home']}")
    for row in rows:
        if not row["identical"]:
            print("MISMATCH:", row["case"])
    return 1 if (mismatches or not report["same_resolution"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
