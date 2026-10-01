#!/usr/bin/env python3
"""MAT2-W10: the DECLARED read-only base-blob access module (NO_WORKTREES law).

This card is a pinned file package, not a checkout: upstream IN-TREE bytes
(the U01/U03 pinned seam, the W05-W09 receipts, the visual validator, the
clearing pins, the macaque asset bytes) live only in the shared repository's
Git object database at the package base. The ONLY operation in this module
is a read-only `git cat-file blob <base>:<path>` against the shared source
repository (resolved from CHIMERA_SOURCE_REPO, set by the runner, else the
canonical checkout). No clone, no worktree, no index or ref mutation, no
checkout of any kind. This module and run_capture.py (the declared ffmpeg
capture-tool calls) are the ONLY subprocess modules in the contribution
(prereg FB9).

Run: import-only. Exit codes n/a.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

DEFAULT_REPO = "E:/PythonChimera"
FALLBACK_COMMIT_TIP = "origin/review/MAT2-W10"


def source_repo() -> str:
    repo = os.environ.get("CHIMERA_SOURCE_REPO", "") or DEFAULT_REPO
    if not Path(repo).exists():
        raise FileNotFoundError("source_repo_missing:" + repo)
    return repo


def read_blob(base_sha: str, rel_path: str) -> bytes:
    """Read one blob at <base_sha>:<rel_path> from the shared object database.

    Read-only: `git cat-file blob` never touches the index, the working tree
    or any ref. The bytes are returned verbatim; identity is the caller's pin
    comparison (sha256 against the preregistered blob hash).
    """
    spec = base_sha + ":" + rel_path
    out = subprocess.run(
        ["git", "-C", source_repo(), "cat-file", "blob", spec],
        capture_output=True, check=False)
    if out.returncode != 0:
        raise RuntimeError("blob_read_refused:" + spec + ":"
                           + out.stderr.decode("utf-8", "replace")[:200])
    return out.stdout


def resolve_base(base_sha: str) -> str:
    """Read-only existence proof: the pinned base object must resolve."""
    out = subprocess.run(
        ["git", "-C", source_repo(), "cat-file", "-t", base_sha],
        capture_output=True, check=False)
    if out.returncode != 0:
        raise RuntimeError("base_unresolvable:" + base_sha)
    kind = out.stdout.decode("ascii", "replace").strip()
    if kind not in ("commit", "tag"):
        raise RuntimeError("base_not_commit:" + base_sha + ":" + kind)
    return kind
