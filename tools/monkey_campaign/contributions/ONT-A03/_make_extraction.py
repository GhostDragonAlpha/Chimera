"""ONT-A03 reference extraction — byte-preserved pinned inputs (read-only elsewhere).

Copies the U-STR record chain out of the MERGED ONT-A02 contribution at the pinned
base commit `2e258b45c9c4e24fa6843a65d9d5324156d10b8d` (branch `astra/gait-capture`
of `E:/PythonChimera`, read-only `git show`), WITHOUT touching any source
repository. Every extracted file is recorded in `reference/EXTRACTION.json` with
its origin commit/path, the git blob sha1, its raw sha256 and byte size. Re-running
the script is idempotent and byte-identical.

The merged A02 package is itself a hash-pinned extraction of the
`forearm-package-20260924` branch records (see ONT-A02/reference/EXTRACTION.json,
merged and lead-accepted as PR #181); this attempt's provenance therefore chains:
base commit -> merged A02 file -> raw sha256 (== A02's recorded raw sha256 for
every entry).

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
BRANCH = "astra/gait-capture"
COMMIT = "2e258b45c9c4e24fa6843a65d9d5324156d10b8d"
SRC_PREFIX = "tools/monkey_campaign/contributions/ONT-A02/"


def _checkout_root() -> Path | None:
    """The attempt checkout that carries this contribution, when it is a git clone."""
    here = HERE.resolve()
    for parent in here.parents:
        if (parent / ".git").exists():
            return parent
    return None


def _repo_candidates() -> list[Path]:
    """Repositories that may carry COMMIT, byte-identical by content hash.

    The attempt checkout is tried first (it fetched the base branch during
    preparation); the shared source checkout is the second source. Content is
    content-addressed: whichever repository serves `COMMIT:path`, the blob sha1
    and raw sha256 recorded in EXTRACTION.json pin the exact bytes, so any
    reviewer with either object can re-verify byte-identity."""
    candidates: list[Path] = []
    root = _checkout_root()
    if root is not None:
        candidates.append(root)
    candidates.append(REPO)
    return candidates

# (path under the merged ONT-A02 contribution at COMMIT, destination under reference/)
FILES = [
    ("reference/USTR_DIAGNOSTIC_RECEIPT.md", "USTR_DIAGNOSTIC_RECEIPT.md"),
    ("reference/ANATOMICAL_DECISION_TABLE.md", "ANATOMICAL_DECISION_TABLE.md"),
    ("reference/baseline_snapshot/MANIFEST.json", "baseline_snapshot/MANIFEST.json"),
    ("reference/baseline_snapshot/source_xml/chimanoid.xml", "baseline_snapshot/source_xml/chimanoid.xml"),
    ("reference/baseline_snapshot/runs/actual_monkey_fit.json", "baseline_snapshot/runs/actual_monkey_fit.json"),
    ("reference/baseline_snapshot/code/compiler.py", "baseline_snapshot/code/compiler.py"),
    ("reference/receipts/R1_report.md", "receipts/R1_report.md"),
    ("reference/receipts/R1_arithmetic.txt", "receipts/R1_arithmetic.txt"),
    ("reference/receipts/R1_citations.md", "receipts/R1_citations.md"),
    ("reference/receipts/C1_c1_geometry.txt", "receipts/C1_c1_geometry.txt"),
    ("reference/receipts/I7_report.md", "receipts/I7_report.md"),
    ("reference/receipts/I7_00_candidate_declaration.json", "receipts/I7_00_candidate_declaration.json"),
    ("reference/receipts/I7_07_gate_table.json", "receipts/I7_07_gate_table.json"),
    ("reference/receipts/I7_08_radius_before_after.json", "receipts/I7_08_radius_before_after.json"),
    ("reference/receipts/I7_09_c1_replacement.json", "receipts/I7_09_c1_replacement.json"),
    ("reference/receipts/I7_10_coverage_topology.json", "receipts/I7_10_coverage_topology.json"),
    ("reference/receipts/o1_combine_sign.json", "receipts/o1_combine_sign.json"),
    ("reference/receipts/B4_01_known_good_records.json", "receipts/B4_01_known_good_records.json"),
    ("reference/meshes/ulna.stl", "meshes/ulna.stl"),
    ("reference/meshes/radius.stl", "meshes/radius.stl"),
    # A02's own extraction record, carried as provenance evidence for the chain
    ("reference/EXTRACTION.json", "provenance/ONT_A02_EXTRACTION.json"),
]


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def git_bytes(repo: Path, path: str) -> bytes:
    out = subprocess.run(
        ["git", "-c", f"safe.directory={repo}", "-C", str(repo), "show", f"{COMMIT}:{path}"],
        capture_output=True, check=True)
    return out.stdout


def git_blob_sha(repo: Path, path: str) -> str:
    out = subprocess.run(
        ["git", "-c", f"safe.directory={repo}", "-C", str(repo), "rev-parse", f"{COMMIT}:{path}"],
        capture_output=True, check=True, text=True)
    return out.stdout.strip()


def first_repo_with(path: str) -> tuple[Path, bytes, str]:
    for repo in _repo_candidates():
        probe = subprocess.run(
            ["git", "-c", f"safe.directory={repo}", "-C", str(repo), "cat-file", "-e",
             f"{COMMIT}:{path}"],
            capture_output=True)
        if probe.returncode == 0:
            return repo, git_bytes(repo, path), git_blob_sha(repo, path)
    raise ValueError(f"no available repository carries {COMMIT}:{path}")


def main() -> int:
    REFERENCE.mkdir(exist_ok=True)
    entries = []
    for src, dest in FILES:
        path = SRC_PREFIX + src
        served_by, data, blob = first_repo_with(path)
        target = REFERENCE / dest
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        entries.append({
            "dest": dest,
            "origin": "git",
            "served_by": str(served_by),
            "repository": str(REPO),
            "branch": BRANCH,
            "commit": COMMIT,
            "path": path,
            "blob_sha1": blob,
            "bytes": len(data),
            "sha256": sha256_bytes(data),
        })
    doc = {
        "schema": "chimera.ont_a03_extraction.v1",
        "task_id": "A03", "card_id": "ONT-A03",
        "note": "Read-only byte-preserved copies for ONT-A03, extracted from the MERGED "
                "ONT-A02 contribution at the pinned base commit; no source repository was "
                "modified and no git write occurred.",
        "provenance_chain": "astra/gait-capture @ " + COMMIT + " -> merged ONT-A02 "
                            "(PR #181, review-accepted) -> forearm-package-20260924 records "
                            "(see provenance/ONT_A02_EXTRACTION.json)",
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
