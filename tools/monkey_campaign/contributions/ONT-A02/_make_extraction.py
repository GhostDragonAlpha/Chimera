"""ONT-A02 reference extraction — byte-preserved pinned inputs (read-only elsewhere).

Copies records out of the `forearm-package-20260924` git branch (read-only `git show`)
and two untracked vendor meshes from the working tree, WITHOUT touching any source
repository. Every extracted file is recorded in reference/EXTRACTION.json with its
origin (branch/path or working-tree path), the git blob sha1 when it is a git object,
its raw sha256 and byte size. Re-running the script is idempotent and byte-identical.

Run:  python -B _make_extraction.py
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REFERENCE = HERE / "reference"
REPO = Path(r"E:/PythonChimera")
BRANCH = "forearm-package-20260924"

# (git path on BRANCH, destination suffix under reference/)
GIT_FILES = [
    ("forearm_package/USTR_DIAGNOSTIC_RECEIPT.md", "USTR_DIAGNOSTIC_RECEIPT.md"),
    ("forearm_package/ANATOMICAL_DECISION_TABLE.md", "ANATOMICAL_DECISION_TABLE.md"),
    ("forearm_package/baseline_snapshot/MANIFEST.json", "baseline_snapshot/MANIFEST.json"),
    ("forearm_package/baseline_snapshot/source_xml/chimanoid.xml", "baseline_snapshot/source_xml/chimanoid.xml"),
    ("forearm_package/baseline_snapshot/runs/actual_monkey_fit.json", "baseline_snapshot/runs/actual_monkey_fit.json"),
    ("forearm_package/baseline_snapshot/code/compiler.py", "baseline_snapshot/code/compiler.py"),
    ("forearm_package/audits/R1_radioulnar_evidence/report.md", "receipts/R1_report.md"),
    ("forearm_package/audits/R1_radioulnar_evidence/receipts/arithmetic.txt", "receipts/R1_arithmetic.txt"),
    ("forearm_package/audits/R1_radioulnar_evidence/receipts/citations.md", "receipts/R1_citations.md"),
    ("forearm_package/audits/C1_ulna_evidence/receipts/c1_geometry.txt", "receipts/C1_c1_geometry.txt"),
    ("forearm_package/audits/I7_ustr_diagnostic/report.md", "receipts/I7_report.md"),
    ("forearm_package/audits/I7_ustr_diagnostic/receipts/00_candidate_declaration.json", "receipts/I7_00_candidate_declaration.json"),
    ("forearm_package/audits/I7_ustr_diagnostic/receipts/07_gate_table.json", "receipts/I7_07_gate_table.json"),
    ("forearm_package/audits/I7_ustr_diagnostic/receipts/08_radius_before_after.json", "receipts/I7_08_radius_before_after.json"),
    ("forearm_package/audits/I7_ustr_diagnostic/receipts/09_c1_replacement.json", "receipts/I7_09_c1_replacement.json"),
    ("forearm_package/audits/I7_ustr_diagnostic/receipts/10_coverage_topology.json", "receipts/I7_10_coverage_topology.json"),
    ("forearm_package/audits/O1_ulna_orientation/receipts/o1_combine_sign.json", "receipts/o1_combine_sign.json"),
    ("forearm_package/audits/B4_correspondence_challenge/receipts/01_known_good_records.json", "receipts/B4_01_known_good_records.json"),
]

# untracked working-tree inputs (read-only copy; identity by raw sha256 only)
WORKTREE_FILES = [
    ("vendor/myo_sim/meshes/ulna.stl", "meshes/ulna.stl"),
    ("vendor/myo_sim/meshes/radius.stl", "meshes/radius.stl"),
]


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def git_bytes(path: str) -> bytes:
    out = subprocess.run(
        ["git", "-C", str(REPO), "show", f"{BRANCH}:{path}"],
        capture_output=True, check=True)
    return out.stdout


def git_blob_sha(path: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(REPO), "rev-parse", f"{BRANCH}:{path}"],
        capture_output=True, check=True, text=True)
    return out.stdout.strip()


def main() -> int:
    REFERENCE.mkdir(exist_ok=True)
    entries = []
    for path, dest in GIT_FILES:
        data = git_bytes(path)
        target = REFERENCE / dest
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        entries.append({
            "dest": dest,
            "origin": "git",
            "repository": str(REPO),
            "branch": BRANCH,
            "path": path,
            "blob_sha1": git_blob_sha(path),
            "bytes": len(data),
            "sha256": sha256_bytes(data),
        })
    for path, dest in WORKTREE_FILES:
        src = REPO / path
        data = src.read_bytes()
        target = REFERENCE / dest
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        entries.append({
            "dest": dest,
            "origin": "working_tree",
            "repository": str(REPO),
            "path": path,
            "tracked": False,
            "bytes": len(data),
            "sha256": sha256_bytes(data),
        })
    doc = {
        "schema": "chimera.ont_a02_extraction.v1",
        "task_id": "A02", "card_id": "ONT-A02",
        "note": "Read-only byte-preserved copies for ONT-A02 re-measurement; no source "
                "repository was modified and no git write occurred.",
        "files": entries,
    }
    (REFERENCE / "EXTRACTION.json").write_text(
        json.dumps(doc, indent=2, sort_keys=True), encoding="utf-8")
    print(f"wrote {len(entries)} entries to reference/EXTRACTION.json")
    for e in entries:
        print(f"  {e['dest']:60s} {e['bytes']:>9d}  {e['sha256'][:16]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
