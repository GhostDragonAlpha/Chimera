"""extract_pinned_app.py -- MAT2-X02: re-extract the pinned playable-slice
subset byte-exact (raw blob bytes, no EOL smudge) into the attempt scratch.

READ-ONLY w.r.t. the play repo: `git cat-file blob` only; the live worktree is
never written and never checked out. Every consumed file's sha256 is recorded
into the extraction manifest (the archived ONT-X02 recipe, re-run for the
MAT2 pins).

Usage:
  python -B extract_pinned_app.py --pin 8550b634... --dest <scratch>/run/play \
      --manifest <scratch>/evidence/pinned_blob_manifest.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path

DEFAULT_REPO = r"E:/ChimeraWork/monkey-play-20260924"

# the archived extraction list: everything the pinned boot needs
PATHS = [
    "tools/playable_slice",
    "tools/science_funnel/data/morphosource_ct/meshes_preview",
    "tools/science_funnel/data/morphosource_ct/meshes_body_20260922/"
    "body_manifest.json",
    "tools/science_funnel/data/morphosource_ct/meshes/manifest.json",
    "tools/science_funnel/data/morphosource_ct/bone_identification.json",
    "tools/science_funnel/ct_skeleton_layer.py",
    "tools/science_funnel/ct_skeleton_triangle.py",
    "tools/science_funnel/validation/standing_pose_20260921/pose.json",
    "tools/science_funnel/validation/standing_pose_20260921/"
    "standing_pose_core.py",
    "tools/science_funnel/validation/hip_pivot_proof_20260921",
    "tools/science_funnel/validation/gait_controller_20260918/"
    "derived_numbers.json",
    "tools/matter_kernel",
    "ChimeraEngine/engine",
    "ChimeraEngine/native/viewer3rd/json.hpp",
]


def git(repo: str, *args) -> bytes:
    return subprocess.run(["git", "-C", repo, *args], capture_output=True,
                          check=True).stdout


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=DEFAULT_REPO)
    ap.add_argument("--pin", default="8550b634ebd7034bb8873eed41d8bdce4d3843d0")
    ap.add_argument("--dest", type=Path, required=True)
    ap.add_argument("--manifest", type=Path, required=True)
    a = ap.parse_args()
    dest: Path = a.dest
    manifest = {}
    failed = []
    listed = []
    t0 = time.time()
    for p in PATHS:
        kind = git(a.repo, "cat-file", "-t", "%s:%s" % (a.pin, p)).decode().strip()
        if kind == "tree":
            out = git(a.repo, "ls-tree", "-r", "--name-only",
                      "%s:%s" % (a.pin, p)).decode().splitlines()
            prefix = "" if p == "ChimeraEngine" else p.rstrip("/") + "/"
            listed += [prefix + n for n in out]
        else:
            listed.append(p)
    for rel in listed:
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            raw = git(a.repo, "cat-file", "blob", "%s:%s" % (a.pin, rel))
            target.write_bytes(raw)
            manifest[rel] = hashlib.sha256(raw).hexdigest()
        except subprocess.CalledProcessError:
            failed.append(rel)
        if len(manifest) % 100 == 0 and len(manifest):
            print("  %d files (%.0fs)" % (len(manifest), time.time() - t0))
    a.manifest.parent.mkdir(parents=True, exist_ok=True)
    a.manifest.write_text(json.dumps({
        "pin": a.pin,
        "repo": a.repo,
        "method": "git cat-file blob (raw bytes; NO EOL smudge)",
        "files": manifest,
        "file_count": len(manifest),
        "failed": failed,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }, indent=1))
    print("extracted %d files, %d failed -> %s" % (len(manifest), len(failed),
                                                   a.manifest))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
