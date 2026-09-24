"""A7 step 5 - baseline integrity receipt.

Verifies, read-only:
  I1 git cleanliness of the snapshot tree (criterion 5);
  I2 sha256 of every file this audit consumed == the sha256 pinned in the
     snapshot's own MANIFEST.json (byte-identical claim, re-measured today);
  I3 the audit wrote nothing inside baseline_snapshot/ (its mtimes are unchanged
     is implied by I2; the git check covers tracked visibility).
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

BASE = Path(r"E:\PythonChimera\forearm_package\baseline_snapshot")
OUT = Path(r"E:\PythonChimera\forearm_package\audits\A7_paths\receipts")

CONSUMED = [
    "MANIFEST.json",
    "code/DERIVATION.md",
    "code/compiler.py",
    "code/experiment_transverse_fit.py",
    "code/schema.py",
    "code/mesh_target.py",
    "code/actual_target_fit.py",
    "inputs/monkey_birth.bin",
    "inputs/monkey_joints.bin",
    "runs/actual_monkey_fit.json",
    "runs/attachment_candidates.json",
    "runs/experiment_transverse_candidate.json",
    "runs/admission_actual_monkey.json",
    "session_reports/anatomy_compiler_05.md",
    "source_xml/chimanoid.xml",
]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    man = json.loads((BASE / "MANIFEST.json").read_text(encoding="utf-8"))
    results = {}
    mismatch = []
    for rel in CONSUMED:
        actual = sha256(BASE / rel)
        if rel not in man["files"]:
            results[rel] = {"actual": actual, "pinned": None,
                            "match": None, "note": "not pinned in MANIFEST files map"}
            continue
        pinned = man["files"][rel]["sha256"]
        results[rel] = {"actual": actual, "pinned": pinned, "match": actual == pinned}
        if actual != pinned:
            mismatch.append(rel)

    git = subprocess.run(
        ["git", "-C", r"E:\PythonChimera", "status", "--porcelain", "--",
         "forearm_package/baseline_snapshot"],
        capture_output=True, text=True, check=True,
    )
    receipt = {
        "I1_git_status_porcelain_baseline_snapshot": git.stdout,
        "I1_empty": git.stdout == "",
        "I2_files_checked": len(CONSUMED),
        "I2_sha_mismatches": mismatch,
        "I2_results": results,
        "git_head_at_snapshot_pinned_in_MANIFEST": man.get("git_head_at_snapshot"),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "step5_integrity_receipt.json").write_text(json.dumps(receipt, indent=1), encoding="utf-8")
    print("I1 git status --porcelain (baseline_snapshot):", repr(git.stdout))
    print("I2 files checked:", len(CONSUMED), "mismatches:", mismatch)


if __name__ == "__main__":
    main()
