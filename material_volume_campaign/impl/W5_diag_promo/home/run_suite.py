"""M09 suite runner: runs the acceptance tests, then proves read-only behavior.

Wraps unittest with a full SHA-256 + st_mtime_ns snapshot of tools/ and
Chimera/docs/matter taken before and after the run (falsifier F1), probes the
reader's own CLI on the genuine blocked/refused fixtures (U7 receipt), and
writes everything under receipts/.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

MY_DIR = Path(__file__).resolve().parent
RECEIPTS = MY_DIR.parent / "receipts"  # W5 path adaptation: receipts live in the promotion dir, not home/
WORK_DIR = MY_DIR / "work"
WORKTREE = MY_DIR.parents[3]  # W5 path adaptation: home/ is one level deeper than agents/M09_diagnostic/
SNAPSHOT_ROOTS = [WORKTREE / "tools", WORKTREE / "Chimera" / "docs" / "matter"]
INPUT_FILES = [
    WORKTREE / "tools" / "material_volume_body_export_reader.py",
    WORKTREE / "tools" / "material_volume_body_export.py",
    WORKTREE / "tools" / "material_volume_admission.py",
    WORKTREE / "tools" / "material_volume_body_export_example_report.json",
    WORKTREE / "tools" / "material_volume_body_export_manifest_example.json",
    WORKTREE / "tools" / "material_volume_body_export_partition_example.json",
    WORKTREE / "tools" / "material_volume_body_export_groups_example.json",
    WORKTREE / "Chimera" / "docs" / "matter" /
        "rigid_body_mass_export_consumption_contract_v1_proposal.md",
]


def snapshot() -> dict:
    state = {}
    for root in SNAPSHOT_ROOTS:
        for path in sorted(root.rglob("*")):
            if path.is_file():
                stat = path.stat()
                state[str(path.relative_to(WORKTREE))] = {
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "mtime_ns": stat.st_mtime_ns,
                }
    return state


def write_output_samples() -> None:
    cli = MY_DIR / "material_volume_diagnostic.py"
    env = dict(__import__("os").environ, PYTHONDONTWRITEBYTECODE="1")
    lines = []
    for name, arg in [("complete-shipped", str(WORKTREE / "tools" /
                       "material_volume_body_export_example_report.json")),
                      ("partial", str(WORK_DIR / "fixture_partial.json")),
                      ("blocked", str(WORK_DIR / "fixture_blocked.json")),
                      ("unsupported", str(WORK_DIR / "fixture_unsupported.json")),
                      ("refused", str(WORK_DIR / "fixture_refused.json")),
                      ("malformed", str(WORK_DIR / "fixture_malformed_version.json"))]:
        proc = subprocess.run([sys.executable, str(cli), arg],
                              capture_output=True, text=True, env=env)
        lines.append(f"=== {name} (exit {proc.returncode}) ===")
        lines.append(proc.stdout.rstrip("\n"))
        if proc.stderr:
            lines.append(f"[stderr] {proc.stderr.rstrip()}")
        proc = subprocess.run([sys.executable, str(cli), arg, "--json"],
                              capture_output=True, text=True, env=env)
        lines.append(f"=== {name} --json (exit {proc.returncode}) ===")
        lines.append(proc.stdout.rstrip("\n"))
    (RECEIPTS / "output_samples.txt").write_text("\n".join(lines) + "\n",
                                                 encoding="utf-8")


def u7_reader_probe() -> None:
    """Run the reader's own main() on genuine blocked/refused fixtures (U7)."""
    env = dict(__import__("os").environ, PYTHONDONTWRITEBYTECODE="1")
    lines = []
    for name in ("blocked", "refused"):
        path = WORK_DIR / f"fixture_{name}.json"
        proc = subprocess.run(
            [sys.executable, str(WORKTREE / "tools" / "material_volume_body_export_reader.py"),
             str(path)], capture_output=True, text=True, env=env)
        summary = json.loads(proc.stdout) if proc.returncode == 0 else None
        lines.append(f"reader CLI on fixture_{name}.json: exit={proc.returncode} "
                     f"stderr={proc.stderr.strip() or '(none)'}")
        if summary is not None:
            lines.append(f"  export_status={summary.get('export_status')!r} "
                         f"bodies={len(summary.get('bodies', []))} "
                         f"dynamics_readiness_claimed="
                         f"{summary.get('dynamics_readiness_claimed')!r}")
            lines.append(f"  summary keys={sorted(summary)}")
            for index, body in enumerate(summary.get("bodies", [])):
                lines.append(f"  body[{index}] keys={sorted(body)}")
    (RECEIPTS / "u7_reader_probe.txt").write_text("\n".join(lines) + "\n",
                                                  encoding="utf-8")


def main() -> int:
    RECEIPTS.mkdir(exist_ok=True)
    before = snapshot()
    suite = unittest.defaultTestLoader.discover(str(MY_DIR / "tests"), top_level_dir=str(MY_DIR))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    after = snapshot()

    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    changed = sorted(path for path in set(before) & set(after)
                     if before[path] != after[path])
    proof = {"before_after_identical": not (added or removed or changed),
             "added": added, "removed": removed, "changed": changed,
             "files_snapshotted": len(before),
             "input_files_sha256": {str(path.relative_to(WORKTREE)):
                                    hashlib.sha256(path.read_bytes()).hexdigest()
                                    for path in INPUT_FILES}}
    (RECEIPTS / "read_only_proof.json").write_text(
        json.dumps(proof, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    write_output_samples()
    u7_reader_probe()

    git = subprocess.run(["git", "-C", str(WORKTREE), "status", "--porcelain",
                          "--", "tools", "Chimera/docs/matter"],
                         capture_output=True, text=True)
    integrity = (f"$ git -C {WORKTREE} status --porcelain -- tools Chimera/docs/matter\n"
                 f"{git.stdout if git.stdout else '(empty)'}")
    (RECEIPTS / "git_integrity.txt").write_text(integrity, encoding="utf-8")

    print(integrity)
    print(f"read-only proof: before_after_identical={proof['before_after_identical']} "
          f"(files_snapshotted={proof['files_snapshotted']}, "
          f"added={len(added)}, removed={len(removed)}, changed={len(changed)})")
    ok = result.wasSuccessful() and proof["before_after_identical"] and not git.stdout
    print(f"M09 suite verdict: {'PASS' if ok else 'FAIL'} "
          f"(tests: {result.testsRun} run, {len(result.failures)} failures, "
          f"{len(result.errors)} errors)")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
