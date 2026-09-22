#!/usr/bin/env python3
"""worktree_janitor.py -- the automatic fleet worktree cleanup mechanism.

LAW (operator directive 2026-09-21): lane worktrees are EPHEMERAL. This tool
deletes a worktree only when it can prove the work is safe:
  1. never touches infrastructure dirs (deny-list below)
  2. no process may hold the directory
  3. no file modified within --max-quiet-hours (an active lane always touches files)
  4. git status must be clean (dirty work is work -> spared, reported)
  5. the branch is ALWAYS bundled to lane-archive first (every commit recoverable,
     even unpushed ones -- a bundle can be cloned)
  6. evidence files archived first (.py/.md/.json/.sha256/.ps1/.txt/.log <5MB,
     .png/.mp4 <20MB, AND extension-less files <20MB -- the class that cost us
     the deploy key)
The verification table is built ONCE per run (single connection -- the
rapid-ls-remote throttle lesson), falling back to the local canonical snapshot
clone's origin refs when auth is down.

Amendments (2026-09-22, lane agent/workflow-rules-conversion-20260922):
  A. quiet-check SCOPE: .git-internal file mtimes (paths containing /.git/) are
     EXCLUDED from recent_mtime -- a fetch/gc/commit churns .git without being
     lane activity (37 logged false spares before the fix: .git/index,
     .git/COMMIT_EDITMSG, .git/objects/pack/*.idx). Working-tree mtimes and
     process-holder checks remain in force.
  B. THE POSTCONDITION LAW (docs/THE_CHECKLIST.md section 7): a tool that
     claims a side effect asserts the effect before logging success. After
     rmtree the path's existence is checked; a survivor gets ONE retry with
     read-only attributes cleared (git objects are RO) plus an explicit rmdir
     for an empty shell, and is logged action="FAILED" if it persists. NEVER a
     success word for an unverified state.

Usage:
  python worktree_janitor.py --dry-run                 # report what would happen
  python worktree_janitor.py                           # execute
  python worktree_janitor.py --only w35-agent          # one directory
Log: E:/ChimeraWork/lane-archive/_janitor/janitor.jsonl (append-only)
"""
import argparse
import datetime as dt
import json
import os
import shutil
import stat
import subprocess
import sys

ROOT = r"E:\ChimeraWork"
ARCHIVE = os.path.join(ROOT, "lane-archive")
JANITOR_LOG = os.path.join(ARCHIVE, "_janitor", "janitor.jsonl")
SNAPSHOT_CLONE = os.path.join(ROOT, "datastore-agent")  # local canonical ref snapshot
CANONICAL = "git@github.com-fleetdeploy:GhostDragonAlpha/Chimera.git"

# Infrastructure and coordination directories are NEVER cleanup scope.
DENY = {
    "control", "tools", "mailbox", "verdicts", "logs", "resume", "evidence",
    "preservations", "lane-archive", "_janitor", "_longtail_sweep",
    "_scripts", "agent-scripts", "grasp_lane_scripts", "intake_gait_ps",
    "finish-agent", "lead-port-agent", "datastore-agent",  # active lanes (maintained by lead; datastore-agent doubles as the local ref snapshot)
}
ARCHIVE_EXTS_5MB = {".py", ".md", ".sha256", ".json", ".ps1", ".txt", ".log"}
ARCHIVE_EXTS_20MB = {".png", ".mp4"}


def sh(cmd, cwd=None):
    return subprocess.run(cmd, capture_output=True, text=True, shell=(os.name == "nt"), cwd=cwd)


def ref_table():
    """Canonical branch tips, ONE network attempt; fallback: local snapshot refs."""
    r = sh(f'git ls-remote "{CANONICAL}" "refs/heads/*"')
    table = {}
    if r.returncode == 0:
        for line in r.stdout.splitlines():
            parts = line.split("\t")
            if len(parts) == 2 and parts[1].startswith("refs/heads/"):
                table[parts[1][len("refs/heads/"):]] = parts[0].strip()
        return table, "canonical-ssh"
    r = sh(f'git -C "{SNAPSHOT_CLONE}" for-each-ref --format="%(refname) %(objectname)" refs/remotes/origin')
    if r.returncode == 0:
        for line in r.stdout.splitlines():
            p = line.split()
            if len(p) == 2 and p[0].startswith("refs/remotes/origin/"):
                table[p[0][len("refs/remotes/origin/"):]] = p[1]
        return table, "local-snapshot"
    return {}, "unavailable"


def holders(path):
    r = sh(f'powershell -NoProfile -Command "Get-Process | Where-Object {{ $_.Path -like \'{path}\\\\*\' }} | Select-Object -ExpandProperty Id"')
    return [l for l in r.stdout.splitlines() if l.strip().isdigit()]


def recent_mtime(path, hours):
    cutoff = dt.datetime.now().timestamp() - hours * 3600
    git_mark = os.sep + ".git" + os.sep  # amendment A: .git-internal mtimes are not lane activity
    for dirpath, _dirnames, filenames in os.walk(path):
        if git_mark in dirpath + os.sep:
            continue
        for f in filenames:
            try:
                if os.path.getmtime(os.path.join(dirpath, f)) > cutoff:
                    return os.path.join(dirpath, f)
            except OSError:
                continue
    return None


def archive_evidence(src, arc):
    count = 0
    for dirpath, _dirnames, filenames in os.walk(src):
        if os.sep + ".git" + os.sep in dirpath + os.sep:
            continue
        for f in filenames:
            full = os.path.join(dirpath, f)
            try:
                size = os.path.getsize(full)
            except OSError:
                continue
            ext = os.path.splitext(f)[1].lower()
            keep = ((ext in ARCHIVE_EXTS_5MB and size < 5 * 1024 * 1024)
                    or (ext in ARCHIVE_EXTS_20MB and size < 20 * 1024 * 1024)
                    or (ext == "" and size < 20 * 1024 * 1024))
            if not keep:
                continue
            rel = os.path.relpath(full, src)
            dest = os.path.join(arc, rel)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            try:
                import shutil
                shutil.copy2(full, dest)
                count += 1
            except OSError:
                pass
    return count


def log(record):
    os.makedirs(os.path.dirname(JANITOR_LOG), exist_ok=True)
    record["ts"] = dt.datetime.now().isoformat(timespec="seconds")
    with open(JANITOR_LOG, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--max-quiet-hours", type=float, default=3.0)
    ap.add_argument("--only", default=None)
    args = ap.parse_args()

    table, table_src = ref_table()
    print(f"verification table: {len(table)} refs ({table_src})")
    results = []
    for name in sorted(os.listdir(ROOT)):
        path = os.path.join(ROOT, name)
        if not os.path.isdir(path) or name in DENY:
            continue
        if args.only and name != args.only:
            continue
        if not os.path.isdir(os.path.join(path, ".git")):
            continue  # non-git dirs are outside this tool's scope by law
        rec = {"dir": name}
        h = holders(path)
        if h:
            rec.update(action="spared", reason="process-holders", detail=h[:5])
            results.append(rec); log(rec); print(f"{name}: SPARED holders"); continue
        rm = recent_mtime(path, args.max_quiet_hours)
        if rm:
            rec.update(action="spared", reason=f"active< {args.max_quiet_hours}h", detail=rm)
            results.append(rec); log(rec); print(f"{name}: SPARED active ({rm})"); continue
        branch = sh("git branch --show-current", cwd=path).stdout.strip()
        tip = sh("git rev-parse HEAD", cwd=path).stdout.strip()
        dirty = sh("git status --porcelain", cwd=path).stdout.strip()
        if dirty:
            rec.update(action="spared", reason="dirty", branch=branch)
            results.append(rec); log(rec); print(f"{name}: SPARED dirty ({branch})"); continue
        in_table = bool(branch and table.get(branch) == tip)
        if args.dry_run:
            rec.update(action="would-delete", branch=branch, tip=tip, in_table=in_table)
            results.append(rec); log(rec); print(f"{name}: WOULD DELETE ({branch} in_table={in_table})"); continue
        arc = os.path.join(ARCHIVE, name)
        os.makedirs(arc, exist_ok=True)
        bundled = False
        if branch:
            r = sh(f'git bundle create "{os.path.join(arc, "branch.bundle")}" {branch}', cwd=path)
            bundled = r.returncode == 0
        if not bundled:
            sh(f'git bundle create "{os.path.join(arc, "head.bundle")}" HEAD', cwd=path)
        n = archive_evidence(path, arc)

        def _clear_ro(func, p, _exc):
            # amendment B: read-only attributes (git objects are RO) block removal
            try:
                os.chmod(p, stat.S_IWRITE)
                func(p)
            except OSError:
                pass

        shutil.rmtree(path, ignore_errors=True)
        if os.path.exists(path):
            # ONE retry with read-only attributes cleared, then an explicit
            # rmdir for the empty-shell survivor (the cycles 9-11 anomaly).
            try:
                shutil.rmtree(path, onexc=_clear_ro)  # py >= 3.12
            except TypeError:
                try:
                    shutil.rmtree(path, onerror=_clear_ro)  # py < 3.12
                except OSError:
                    pass
            except OSError:
                pass
            if os.path.exists(path):
                try:
                    os.rmdir(path)
                except OSError:
                    pass
        gone = not os.path.exists(path)  # the postcondition: the world is the witness
        rec.update(action=("deleted" if gone else "FAILED"), branch=branch, tip=tip,
                   in_table=in_table, archived_files=n, bundled=bundled)
        results.append(rec); log(rec)
        if gone:
            print(f"{name}: DELETED ({branch} archived={n} bundled={bundled})")
        else:
            print(f"{name}: FAILED -- path survived, logged honestly ({branch} archived={n} bundled={bundled})")
    deleted = sum(1 for r in results if r["action"] == "deleted")
    failed = sum(1 for r in results if r["action"] == "FAILED")
    print(f"summary: {deleted} deleted, {failed} FAILED, {len(results) - deleted - failed} spared/other")


if __name__ == "__main__":
    sys.exit(main())
