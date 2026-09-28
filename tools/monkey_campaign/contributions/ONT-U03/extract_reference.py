"""extract_reference.py -- ONE-TIME read-only extraction of the pinned sources.

Reads exact bytes from the pinned play revision 9afbddcd90164b5544a16fd0bc72278d985eb6e3
via `git show` (the play worktree itself is NEVER opened for write, never
checked out, never switched) and writes them under reference/ preserving the
repository-relative paths. Every written file's sha256 is recorded into
reference/EXTRACTION.json. Re-running is a no-op when every hash matches.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REFERENCE = HERE / "reference"
REPO = "E:/ChimeraWork/monkey-play-20260924"
PIN = "9afbddcd90164b5544a16fd0bc72278d985eb6e3"

FILES = [
    # THE QUALIFIED SUBJECT (policy layer) and its frozen falsifier receipt:
    "tools/monkey_campaign/product/focus_policy.py",
    "tools/monkey_campaign/product/focus_policy_tests.py",
    "tools/monkey_campaign/agents/U03_focus/receipts/focus_policy_tests_20260924.txt",
    "tools/monkey_campaign/agents/U03_focus/PREREGISTRATION.md",
    "tools/monkey_campaign/agents/U03_focus/brief.md",
    # The mapper the policy drives (imported, never edited), its tests and records:
    "tools/monkey_campaign/product/input_mapper.py",
    "tools/monkey_campaign/product/input_mapper_tests.py",
    "tools/monkey_campaign/agents/U01_input/receipts/input_mapper_tests_20260924.txt",
    "tools/monkey_campaign/agents/U01_input/PREREGISTRATION.md",
    "tools/monkey_campaign/agents/U01_input/discovery_note.md",
    # The seam and the declared camera referent:
    "tools/science_funnel/typeb_export/command_record.py",
    "tools/monkey_campaign/product/follow_camera.py",
]


def main() -> int:
    REFERENCE.mkdir(exist_ok=True)
    extraction = {}
    failed = False
    for rel in FILES:
        out = subprocess.run(
            ["git", "-c", "safe.directory=" + REPO, "-C", REPO,
             "show", PIN + ":" + rel],
            capture_output=True, timeout=60)
        if out.returncode != 0:
            print("MISSING at pin:", rel, file=sys.stderr)
            failed = True
            continue
        data = out.stdout
        digest = hashlib.sha256(data).hexdigest()
        dest = REFERENCE / rel
        if dest.is_file():
            if hashlib.sha256(dest.read_bytes()).hexdigest() == digest:
                extraction[rel] = digest
                continue
            raise SystemExit("EXTRACTION REFUSES to overwrite drifted file: "
                             + rel)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        extraction[rel] = digest
        print("extracted", rel, digest)
    manifest_path = REFERENCE / "EXTRACTION.json"
    manifest = {
        "schema": "chimera.ont_u03.reference_extraction.v1",
        "pinned_revision": PIN,
        "source_repository": REPO,
        "method": "git show PIN:<path> (read-only); no checkout, no branch switch",
        "files": dict(sorted(extraction.items())),
    }
    manifest_path.write_text(json.dumps(manifest, indent=1, sort_keys=True)
                             + "\n", encoding="utf-8")
    print("EXTRACTION.json written with", len(extraction), "files")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
