"""B2a snapshot tool: SHA-256 + st_mtime_ns of tools/ and Chimera/docs/matter."""
from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path

WORKTREE = Path("E:/ChimeraWork/mvc-20260924")
ROOTS = [WORKTREE / "tools", WORKTREE / "Chimera" / "docs" / "matter"]


def snapshot() -> dict:
    state = {}
    for root in ROOTS:
        for path in sorted(root.rglob("*")):
            if path.is_file():
                stat = path.stat()
                state[str(path.relative_to(WORKTREE)).replace("\\", "/")] = {
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "mtime_ns": stat.st_mtime_ns,
                }
    return state


def diff(before: dict, after: dict) -> dict:
    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    changed = sorted(p for p in set(before) & set(after) if before[p] != after[p])
    return {"added": added, "removed": removed, "changed": changed,
            "files_snapshotted": len(before),
            "before_after_identical": not (added or removed or changed)}


if __name__ == "__main__":
    mode, out_path = sys.argv[1], sys.argv[2]
    if mode == "take":
        Path(out_path).write_text(json.dumps(snapshot(), indent=1, sort_keys=True),
                                  encoding="utf-8")
        print(f"snapshot taken: {out_path}")
    elif mode == "cmp":
        d = diff(json.loads(Path(sys.argv[3]).read_text(encoding="utf-8")),
                 snapshot())
        Path(out_path).write_text(json.dumps(d, indent=1, sort_keys=True),
                                  encoding="utf-8")
        print(json.dumps(d, indent=1, sort_keys=True))
