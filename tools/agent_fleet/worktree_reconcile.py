"""Read-only classification of a task worktree's Git progress."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

SHA40 = re.compile(r"[0-9a-f]{40}\Z")


def _git(repo: Path, *args: str) -> tuple[int, str, str]:
    env = dict(os.environ)
    env["GIT_OPTIONAL_LOCKS"] = "0"
    p = subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                       text=True, encoding="utf-8", errors="replace", env=env)
    return p.returncode, p.stdout, p.stderr


def _git_bytes(repo: Path, *args: str) -> tuple[int, bytes, bytes]:
    env = dict(os.environ)
    env["GIT_OPTIONAL_LOCKS"] = "0"
    p = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, env=env)
    return p.returncode, p.stdout, p.stderr


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _clean_rel(value: str) -> str | None:
    value = value.replace("\\", "/").rstrip("/")
    if not value:
        return None
    p = Path(value)
    if p.is_absolute() or ":" in value or any(part in ("", ".", "..") for part in value.split("/")):
        return None
    return "/".join(p.parts)


def _status(repo: Path) -> tuple[list[dict], list[str]]:
    rc, out, err = _git(repo, "status", "--porcelain=v1", "-z", "--untracked-files=all",
                        "--ignored=matching")
    if rc:
        return [], ["status_failed:" + err.strip()]
    raw = out.encode("utf-8", "surrogatepass") if isinstance(out, str) else out
    # subprocess text decoding preserves NUL and gives us all names. Git's
    # porcelain-v1 records are `XY path`; rename/copy records carry one more
    # NUL-delimited source path.
    bits = raw.decode("utf-8", "surrogateescape").split("\0")
    result: list[dict] = []
    i = 0
    while i < len(bits) and bits[i]:
        rec = bits[i]; i += 1
        if len(rec) < 4:
            return [], ["malformed_status_record"]
        code, name = rec[:2], rec[3:]
        result.append({"code": code, "path": name})
        if "R" in code or "C" in code:
            if i >= len(bits) or not bits[i]:
                return [], ["malformed_rename_record"]
            result[-1]["old_path"] = bits[i]; i += 1
    return result, []


def _committed(repo: Path, old: str, new: str) -> tuple[list[dict], list[str]]:
    if old == new:
        return [], []
    rc, out, err = _git_bytes(repo, "diff", "--name-status", "--no-renames", "-z", old, new)
    if rc:
        return [], ["committed_diff_failed:" + err.strip()]
    result = []
    bits = out.split(b"\0")
    i = 0
    while i < len(bits) and bits[i]:
        if i + 1 >= len(bits) or not bits[i + 1]:
            return [], ["malformed_committed_diff"]
        result.append({"code": bits[i].decode("utf-8", "surrogateescape"),
                       "path": bits[i + 1].decode("utf-8", "surrogateescape"),
                       "committed": True})
        i += 2
    return result, []


def _index_fingerprint(repo: Path) -> str | None:
    rc, out, err = _git(repo, "rev-parse", "--path-format=absolute", "--git-path", "index")
    if rc:
        return None
    try:
        return __import__("hashlib").sha256(Path(out.strip()).read_bytes()).hexdigest()
    except OSError:
        return None


def inspect(repo: str | os.PathLike[str], expected_head: str,
            scopes: list[str], evidence_root: str, _between_reads=None) -> dict:
    errors: list[str] = []
    classes: set[str] = set()
    try:
        checkout = Path(repo).expanduser().resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        return {"ok": False, "stable": False, "classification": ["invalid_repo"],
                "errors": ["repo_unresolvable:" + str(exc)], "authority": "none"}
    if not checkout.is_dir():
        return {"ok": False, "stable": False, "classification": ["invalid_repo"],
                "errors": ["repo_not_directory"], "authority": "none"}
    if checkout.parent == checkout:
        return {"ok": False, "stable": False, "classification": ["invalid_repo"],
                "errors": ["filesystem_root_is_not_a_checkout"], "authority": "none"}
    rc, top, err = _git(checkout, "rev-parse", "--show-toplevel")
    if rc:
        return {"ok": False, "stable": False, "classification": ["not_git_checkout"],
                "errors": [err.strip() or "rev_parse_failed"], "authority": "none"}
    try:
        actual_top = Path(top.strip()).resolve(strict=True)
    except (OSError, RuntimeError):
        actual_top = Path(top.strip()).resolve()
    if actual_top != checkout:
        return {"ok": False, "stable": False, "classification": ["repo_mismatch"],
                "errors": ["git_top_level_does_not_match_repo"], "authority": "none"}
    if not SHA40.fullmatch(expected_head):
        return {"ok": False, "stable": False, "classification": ["invalid_expected_head"],
                "errors": ["expected_head_must_be_full_lowercase_sha"], "authority": "none"}
    def head() -> str | None:
        rc2, out2, err2 = _git(checkout, "rev-parse", "--verify", "HEAD^{commit}")
        if rc2:
            errors.append("head_read_failed:" + err2.strip())
            return None
        return out2.strip()
    first_head = head()
    if first_head is None:
        classes.add("unstable_read")
    elif _git(checkout, "merge-base", "--is-ancestor", expected_head, first_head)[0] != 0:
        classes.add("divergent_head")
    scope_rel = [_clean_rel(x) for x in scopes]
    evidence_rel = _clean_rel(evidence_root)
    if not scope_rel or any(x is None for x in scope_rel) or evidence_rel is None:
        return {"ok": False, "stable": False, "classification": ["invalid_path_argument"],
                "errors": ["scope_and_evidence_root_must_be_relative_safe_paths"],
                "head": first_head, "expected_head": expected_head, "authority": "none"}
    scope_paths = [checkout / x for x in scope_rel if x is not None]
    evidence_path = checkout / evidence_rel
    index_before = _index_fingerprint(checkout)
    if index_before is None:
        errors.append("index_unreadable")
    committed, committed_errors = _committed(checkout, expected_head, first_head or expected_head)
    errors.extend(committed_errors)
    statuses, status_errors = _status(checkout); errors.extend(status_errors)
    if _between_reads is not None:
        _between_reads()
    paths: list[dict] = []
    for item in committed + statuses:
        for key in ("path", "old_path"):
            if key not in item:
                continue
            raw = item[key]; rel = _clean_rel(raw)
            row = {"path": raw, "code": item["code"], "role": key}
            if rel is None:
                row["classification"] = "path_escape"; classes.add("path_escape")
                paths.append(row); continue
            physical = (checkout / rel).resolve(strict=False)
            if not _inside(physical, checkout):
                row["classification"] = "path_escape"; classes.add("path_escape")
                paths.append(row); continue
            under_evidence = _inside(checkout / rel, evidence_path)
            under_scope = any(_inside(checkout / rel, s) for s in scope_paths)
            code = item["code"]
            added = code == "??" or code == "!!" or "A" in code or "C" in code
            deleted = "D" in code
            if code == "!!" and not item.get("committed"):
                role = "preserved_ignored"
            elif under_evidence and deleted:
                role = "historical_evidence_deleted"
            elif under_evidence and not added:
                role = "historical_evidence_modified"
            elif under_evidence and added:
                role = "evidence_only_added"
            elif not under_scope and not item.get("committed") and code in ("??", "!!"):
                role = "preserved_untracked_outside_scope"
            elif not under_scope:
                role = "outside_task_scope"
            else:
                role = "source_changed_requires_revalidation"
            row["classification"] = role; classes.add(role); paths.append(row)
    second_head = head()
    index_after = _index_fingerprint(checkout)
    if index_after is None:
        errors.append("index_unreadable")
    stable = not errors and first_head == second_head and index_before == index_after
    if not stable:
        classes.add("unstable_read")
    if not classes:
        classes.add("clean")
    blocking = classes - {"clean", "evidence_only_added", "preserved_untracked_outside_scope", "preserved_ignored", "head_advanced"}
    if first_head and first_head != expected_head and "divergent_head" not in classes:
        classes.add("head_advanced")
    return {"ok": not blocking and stable and "divergent_head" not in classes,
            "stable": stable, "authority": "none", "repo": str(checkout),
            "head": first_head, "head_after": second_head,
            "expected_head": expected_head, "classification": sorted(classes),
            "paths": paths, "errors": errors}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", required=True)
    p.add_argument("--expected-head", required=True)
    p.add_argument("--scope", action="append", required=True)
    p.add_argument("--evidence-root", required=True)
    a = p.parse_args(argv)
    result = inspect(a.repo, a.expected_head, a.scope, a.evidence_root)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
