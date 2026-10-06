"""extract_reference.py -- ONE-TIME read-only extraction for ONT-A05.

Recovers (a) the merged ONT-A04 winner's identity/receipt artifacts from git
object 020c0a5c (review/ONT-A04 winner head 020c0a5c216a..., PR #177 merge
f301e9b3) and (b) the vendored MyoSuite hand structure files, into reference/
preserving identifiable paths. Every written file's sha256 is recorded into
reference/EXTRACTION.json. Re-running is a no-op when every hash matches.
The play worktree and every source tree are NEVER opened for write.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REFERENCE = HERE / "reference"
REPO = "E:/ChimeraWork/monkey-play-20260924"
WINNER = "020c0a5c"          # review/ONT-A04 winner head (full sha resolved below)

VENDOR = Path("E:/PythonChimera/vendor/myo_sim")

GIT_FILES = [
    ("a04_winner",
     "tools/monkey_campaign/contributions/ONT-A04/reference/identity_table.md"),
    ("a04_winner",
     "tools/monkey_campaign/contributions/ONT-A04/reference/chimanoid.xml"),
    ("a04_winner",
     "tools/monkey_campaign/contributions/ONT-A04/reference/s1_inventory.json"),
    ("a04_winner",
     "tools/monkey_campaign/contributions/ONT-A04/reference/s2_identity.json"),
    ("a04_winner",
     "tools/monkey_campaign/contributions/ONT-A04/reference/s3_palm_normal.json"),
    ("a04_winner",
     "tools/monkey_campaign/contributions/ONT-A04/reference/"
     "target_hand_region_v3.txt"),
    ("a04_winner",
     "tools/monkey_campaign/contributions/ONT-A04/reference/"
     "target_paddle_measures.txt"),
    ("a04_winner",
     "tools/monkey_campaign/contributions/ONT-A04/reference/prereg.md"),
    ("a04_winner",
     "tools/monkey_campaign/contributions/ONT-A04/evidence/"
     "numerical_receipt.json"),
    ("a04_winner",
     "tools/monkey_campaign/contributions/ONT-A04/evidence/"
     "state_snapshot.json"),
    ("a04_winner",
     "tools/monkey_campaign/contributions/ONT-A04/qualification_receipt.json"),
    ("a04_winner",
     "tools/monkey_campaign/contributions/ONT-A04/report.md"),
    ("a04_winner",
     "tools/monkey_campaign/contributions/ONT-A04/card_task.json"),
]

VENDOR_FILES = [
    "LICENSE",
    "VERSION",
    "hand/myohand.xml",
    "hand/assets/myohand_body.xml",
]


def main() -> int:
    REFERENCE.mkdir(exist_ok=True)
    full = subprocess.run(
        ["git", "-c", "safe.directory=" + REPO, "-C", REPO,
         "rev-parse", WINNER], capture_output=True, text=True)
    if full.returncode != 0:
        raise SystemExit("winner head not resolvable: " + full.stderr)
    winner_sha = full.stdout.strip()
    extraction = {"a04_winner_head": winner_sha, "files": {}}
    failed = False
    for origin, rel in GIT_FILES:
        out = subprocess.run(
            ["git", "-c", "safe.directory=" + REPO, "-C", REPO,
             "show", WINNER + ":" + rel], capture_output=True, timeout=60)
        if out.returncode != 0:
            print("MISSING at winner:", rel, file=sys.stderr)
            failed = True
            continue
        dest = REFERENCE / origin / Path(rel).name
        digest = hashlib.sha256(out.stdout).hexdigest()
        if dest.is_file():
            if hashlib.sha256(dest.read_bytes()).hexdigest() == digest:
                extraction["files"][origin + ":" + rel] = digest
                continue
            raise SystemExit("EXTRACTION REFUSES to overwrite drifted file: "
                             + rel)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(out.stdout)
        extraction["files"][origin + ":" + rel] = digest
        print("extracted", origin, rel, digest[:12])
    for rel in VENDOR_FILES:
        src = VENDOR / rel
        if not src.is_file():
            print("MISSING vendor:", rel, file=sys.stderr)
            failed = True
            continue
        data = src.read_bytes()
        dest = REFERENCE / "vendor_myo_sim" / rel
        digest = hashlib.sha256(data).hexdigest()
        if dest.is_file():
            if hashlib.sha256(dest.read_bytes()).hexdigest() == digest:
                extraction["files"]["vendor:" + rel] = digest
                continue
            raise SystemExit("EXTRACTION REFUSES to overwrite drifted file: "
                             + rel)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
        extraction["files"]["vendor:" + rel] = digest
        print("extracted vendor", rel, digest[:12])
    manifest_path = REFERENCE / "EXTRACTION.json"
    manifest = {
        "schema": "chimera.ont_a05.reference_extraction.v1",
        "a04_winner_head": winner_sha,
        "source_repository": REPO,
        "vendor_root": str(VENDOR),
        "method": "git show WINNER:<path> (read-only) + byte copies of the "
                  "vendored Apache-2.0 MyoSuite hand files (read-only); no "
                  "checkout, no branch switch",
        "files": dict(sorted(extraction["files"].items())),
    }
    manifest_path.write_text(json.dumps(manifest, indent=1, sort_keys=True)
                             + "\n", encoding="utf-8")
    print("EXTRACTION.json written with", len(manifest["files"]), "files")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
