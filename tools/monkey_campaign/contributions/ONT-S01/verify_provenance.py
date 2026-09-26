#!/usr/bin/env python3
"""Read-only verifier for the ONT-S01 shipped-surface provenance registry (card ONT-S01).

Enforces the done_when "Every shipped asset/model/library has a recorded source and
applicable distribution terms" as a CLOSED-WORLD machine check:

  - every evidence pin resolves in a git object store (commit exists,
    `git rev-parse <commit>:<path>` equals the recorded blob, the blob bytes hash
    to the recorded raw sha256 and byte length, every recorded marker occurs),
  - deep checks re-hash the named MorphoSource agreement PDF, media CSV and the
    render body itself from the object store,
  - on-disk license evidence and banked snapshots re-hash to their recorded values
    and carry their recorded markers,
  - the shipped-surface enumeration (pinned hash receipt + declared extras, each
    marker-tied to a pinned record) is covered EXACTLY by the registry rows in both
    directions: an unregistered shipped artifact is a refusal - existing receipts
    are inputs, not blanket clearance for future assets,
  - every row records a source and terms backed by registered evidence; restricted
    rows must name the operator distribution gate; CLEAR needs evidence.

Read-only everywhere: only `git cat-file`, `git rev-parse` plumbing; no checkout,
no worktree or index mutation; no network.

Usage:
  python -B verify_provenance.py --registry provenance_registry.json [--repo DIR]
      [--expected-criteria SHA256] [--out RECEIPT.json] [--skip-disk]

Exit codes: 0 = PASS, 3 = named refusal, 2 = usage/environment error.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys

EXPECTED_SCOPE_SHA256 = "01ea5cddca8d4795caa096945edf7eadcd1f3eb3e2f084fd2ee36a08cae12ef6"
EXPECTED_TASK_ID = "S01"
EXPECTED_CARD_ID = "ONT-S01"
EXPECTED_CRITERIA_SHA256 = "97b8ad4ec192f3d9900a1d344e4f960365fec49161744a086228f80a247c3112"
OBSERVATION_ENFORCED = "Existing license receipts are inputs, not blanket clearance for future assets"
EXPECTED_PRIMARY_PATHS = 11
ALLOWED_VERDICTS = {
    "CLEAR", "RESTRICTED_RECORDED", "RECORDED", "PENDING_BUILD_IDENTITY",
    "CLEAR_NOT_SHIPPED", "CONFIRMED_EXCLUDED",
}
VERDICTS_REQUIRING_GATE = {"RESTRICTED_RECORDED"}
HEX64 = re.compile(r"^[0-9a-f]{64}$")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
# Line-bounded on purpose: [ \t] cannot cross the newlines that \s would, so a
# match can never swallow the neighboring enumeration line.
SURFACE_LINE = re.compile(r"^[ \t]{2,}(tools/\S+)[ \t]+([0-9a-f]{64})(?:[ \t]+.*)?$", re.M)


class Refusal(Exception):
    """A named, located refusal; never a silent pass."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git(repo: str, *args: str) -> bytes:
    cmd = ["git", "-c", "safe.directory=*", "-C", repo, *args]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        raise Refusal("git_command_failed:" + " ".join(args[:2]) + ":" +
                      proc.stderr.decode("utf-8", "replace").strip()[:200])
    return proc.stdout


def _resolve_repo(explicit: str | None, registry_path: str) -> str:
    if explicit:
        if not (os.path.isdir(os.path.join(explicit, ".git")) or
                os.path.isfile(os.path.join(explicit, ".git"))):
            raise Refusal("repo_not_a_git_worktree:" + explicit)
        return explicit
    env = os.environ.get("PROVENANCE_REGISTRY_REPO")
    if env:
        return env
    cur = os.path.dirname(os.path.abspath(registry_path))
    for _ in range(12):
        if os.path.exists(os.path.join(cur, ".git")):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    raise Refusal("repo_unresolved:pass --repo or set PROVENANCE_REGISTRY_REPO")


def _blob_bytes(repo: str, commit: str, path: str, pin_id: str) -> bytes:
    _git(repo, "cat-file", "-e", commit + "^{commit}")
    actual = _git(repo, "rev-parse", f"{commit}:{path}").decode().strip()
    return _git(repo, "cat-file", "blob", actual), actual


def _check_static(pin: dict, label: str) -> None:
    for name in ("commit", "sha256"):
        val = pin.get(name, "")
        pat = HEX40 if name == "commit" else HEX64
        if not (isinstance(val, str) and pat.match(val)):
            raise Refusal(f"{label}_identity_malformed:{pin.get('id', '?')}:{name}")
    path = pin.get("path", "")
    if not (isinstance(path, str) and path):
        raise Refusal(f"{label}_path_malformed:{pin.get('id', '?')}")


def _resolve_pin(repo: str, pin: dict, label: str = "pin") -> bytes:
    pin_id = pin.get("id", "?")
    _check_static(pin, label)
    commit, path = pin["commit"], pin["path"]
    try:
        raw, actual_blob = _blob_bytes(repo, commit, path, pin_id)
    except Refusal as exc:
        raise Refusal(f"pin_dead:{pin_id}:{exc}") from None
    if HEX40.match(pin.get("blob", "")) and actual_blob != pin["blob"]:
        raise Refusal(f"pin_blob_mismatch:{pin_id}:recorded {pin['blob']} actual {actual_blob}")
    if _sha256(raw) != pin["sha256"]:
        raise Refusal(f"pin_sha256_mismatch:{pin_id}")
    if len(raw) != pin.get("bytes", len(raw)):
        raise Refusal(f"pin_bytes_mismatch:{pin_id}:recorded {pin.get('bytes')} actual {len(raw)}")
    text = raw.decode("utf-8", "replace")
    for marker in pin.get("markers", []):
        if marker not in text:
            raise Refusal(f"pin_marker_missing:{pin_id}:{marker[:60]}")
    return raw


def _parse_primary_paths(receipt_text: str) -> list:
    paths = [m.group(1) for m in SURFACE_LINE.finditer(receipt_text)]
    if len(paths) != EXPECTED_PRIMARY_PATHS:
        raise Refusal(f"surface_enumeration_size:{len(paths)}:expected {EXPECTED_PRIMARY_PATHS}")
    if len(set(paths)) != len(paths):
        raise Refusal("surface_enumeration_duplicate_path")
    return paths


def verify(registry_path: str, repo: str | None = None,
           expected_criteria: str | None = None,
           skip_disk: bool = False,
           disk_root: str | None = None) -> dict:
    repo = _resolve_repo(repo, registry_path)
    try:
        with open(registry_path, "rb") as fh:
            reg = json.loads(fh.read().decode("utf-8"))
    except (OSError, ValueError) as exc:
        raise Refusal(f"registry_unreadable:{exc}") from None

    if reg.get("schema") != "chimera.provenance_registry.v1":
        raise Refusal("schema_mismatch:" + str(reg.get("schema")))
    if reg.get("card_id") != EXPECTED_CARD_ID or reg.get("task_id") != EXPECTED_TASK_ID:
        raise Refusal("card_identity_mismatch")
    if reg.get("scope_sha256") != EXPECTED_SCOPE_SHA256:
        raise Refusal("scope_mismatch")
    want_criteria = expected_criteria or EXPECTED_CRITERIA_SHA256
    if reg.get("criteria_sha256") is not None and reg.get("criteria_sha256") != want_criteria:
        raise Refusal("criteria_mismatch")
    if expected_criteria and expected_criteria != EXPECTED_CRITERIA_SHA256:
        raise Refusal("criteria_mismatch")
    if reg.get("observation_enforced") != OBSERVATION_ENFORCED:
        raise Refusal("observation_dropped")
    closure = reg.get("closure_rule", {})
    if "future asset" not in closure.get("statement", "").lower():
        raise Refusal("closure_rule_missing:not_closed_world")
    if "not clearance" not in closure.get("future_asset_duty", ""):
        raise Refusal("closure_rule_missing:no_future_asset_duty")

    pins = reg.get("pins", [])
    if not (isinstance(pins, list) and pins):
        raise Refusal("pins_missing")
    pin_ids = [p.get("id") for p in pins]
    if len(set(pin_ids)) != len(pin_ids):
        raise Refusal("pin_id_duplicate")
    pin_bytes: dict = {}
    for pin in pins:
        pin_bytes[pin["id"]] = _resolve_pin(repo, pin)

    deep_checks = reg.get("deep_checks", [])
    deep_resolved = 0
    for chk in deep_checks:
        _check_static(chk, "deep")
        try:
            raw, _blob = _blob_bytes(repo, chk["commit"], chk["path"], chk["id"])
        except Refusal as exc:
            raise Refusal(f"deep_dead:{chk['id']}:{exc}") from None
        if _sha256(raw) != chk["sha256"] or len(raw) != chk.get("bytes", len(raw)):
            raise Refusal(f"deep_identity_mismatch:{chk['id']}")
        deep_resolved += 1

    # relative on-disk evidence paths are defined relative to the SHIPPED
    # registry's directory (not the verifier's cwd, and not a mutation copy's)
    disk_registry = disk_root or os.path.dirname(os.path.abspath(registry_path))
    disk_checks_run = 0
    if not skip_disk:
        for item in reg.get("on_disk_evidence", []):
            p = item.get("path", "")
            full = p if os.path.isabs(p) else os.path.join(disk_registry, p)
            if not os.path.isfile(full):
                raise Refusal(f"disk_evidence_missing:{item.get('id', '?')}:{p}")
            with open(full, "rb") as fh:
                raw = fh.read()
            if _sha256(raw) != item.get("sha256"):
                raise Refusal(f"disk_evidence_sha256_mismatch:{item.get('id', '?')}")
            text = raw.decode("utf-8", "replace")
            for marker in item.get("markers", []):
                if marker not in text:
                    raise Refusal(f"disk_evidence_marker_missing:{item.get('id', '?')}:{marker[:60]}")
            disk_checks_run += 1
        meta = reg.get("package_metadata", {})
        import importlib.metadata as _md
        for pkg in ("numpy", "scipy"):
            want = meta.get(pkg, {})
            try:
                version = _md.version(pkg)
            except _md.PackageNotFoundError:
                raise Refusal(f"package_missing:{pkg}") from None
            if version != want.get("version"):
                raise Refusal(f"package_version_drift:{pkg}:{version}!=:{want.get('version')}")
            classifiers = [c for c in _md.metadata(pkg).get_all("Classifier") or []
                           if c == want.get("license_classifier")]
            if not classifiers:
                raise Refusal(f"package_license_classifier_missing:{pkg}")
        cpython = meta.get("cpython", {})
        if f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}" != cpython.get("version"):
            raise Refusal("cpython_version_drift")

    enum = reg.get("surface_enumeration", {})
    primary_raw = pin_bytes.get(enum.get("primary_receipt", ""))
    if primary_raw is None:
        raise Refusal("primary_enumeration_pin_missing")
    primary_paths = _parse_primary_paths(primary_raw.decode("utf-8", "replace"))
    extras = enum.get("declared_extras", [])
    explicit = list(primary_paths)
    for extra in extras:
        path = extra.get("path", "")
        if path in primary_paths:
            raise Refusal("declared_extra_already_enumerated:" + path)
        if path in explicit:
            raise Refusal("declared_extra_duplicate:" + path)
        src = extra.get("marker_source", "")
        if src not in pin_bytes:
            raise Refusal("extra_marker_source_unknown:" + path)
        marker = extra.get("marker", "")
        if marker not in pin_bytes[src].decode("utf-8", "replace"):
            raise Refusal(f"extra_marker_missing:{path}:{marker[:60]}")
        explicit.append(path)
    expected_count = enum.get("expected_explicit_path_count")
    if expected_count is not None and len(explicit) != expected_count:
        raise Refusal(f"surface_size_mismatch:{len(explicit)}!=:{expected_count}")

    rows = reg.get("rows", [])
    if not (isinstance(rows, list) and rows):
        raise Refusal("rows_missing")
    row_ids = [r.get("id") for r in rows]
    if len(set(row_ids)) != len(row_ids):
        raise Refusal("row_id_duplicate")
    evidence_ids = set(pin_ids) | {d.get("id") for d in deep_checks} | \
                   {i.get("id") for i in reg.get("on_disk_evidence", [])}
    covered: dict = {}
    set_rows = 0
    verdicts: dict = {}
    for row in rows:
        rid, verdict = row.get("id", "?"), row.get("verdict", "")
        if not row.get("artifact") or not row.get("source"):
            raise Refusal(f"row_source_or_artifact_missing:{rid}")
        terms = row.get("terms", "")
        if not (isinstance(terms, str) and terms):
            raise Refusal(f"row_terms_missing:{rid}")
        if verdict not in ALLOWED_VERDICTS:
            raise Refusal(f"row_verdict_unknown:{rid}:{verdict}")
        refs = [eid for eid in evidence_ids if eid and eid in terms]
        live_meta_row = any(m.get("row") == rid for m in [reg.get("package_metadata", {}).get("numpy", {}),
                                                          reg.get("package_metadata", {}).get("scipy", {}),
                                                          reg.get("package_metadata", {}).get("cpython", {})]
                            if isinstance(m, dict) and m)
        if verdict != "CONFIRMED_EXCLUDED" and not refs and not live_meta_row:
            raise Refusal(f"row_terms_without_evidence:{rid}")
        if verdict in VERDICTS_REQUIRING_GATE:
            gate = row.get("distribution_gate", "")
            gate_ref = gate.split("(")[0].strip() if gate else ""
            if not gate or not any(eid in gate for eid in pin_ids):
                raise Refusal(f"restricted_row_without_gate:{rid}")
        if verdict == "PENDING_BUILD_IDENTITY" and not row.get("identity_action"):
            raise Refusal(f"pending_identity_without_action:{rid}")
        if verdict == "CLEAR_NOT_SHIPPED" and not row.get("structural_exclusion"):
            raise Refusal(f"not_shipped_without_exclusion:{rid}")
        for path in row.get("covers", []):
            if path in covered:
                raise Refusal(f"coverage_double_claim:{path}:{covered[path]}:{rid}")
            covered[path] = rid
        if row.get("covers_set"):
            set_rows += 1
            manifest_pin = row["covers_set"].get("manifest_pin", "")
            if manifest_pin not in pin_bytes:
                raise Refusal(f"set_coverage_pin_unknown:{rid}:{manifest_pin}")
            manifest = json.loads(pin_bytes[manifest_pin].decode("utf-8"))
            bones = manifest.get("bones", [])
            if len(bones) != row["covers_set"].get("expected_files"):
                raise Refusal(f"set_coverage_count_mismatch:{rid}:{len(bones)}")
        verdicts[verdict] = verdicts.get(verdict, 0) + 1

    expected_rows = enum.get("expected_row_count")
    if expected_rows is not None and len(rows) != expected_rows:
        raise Refusal(f"row_count_mismatch:{len(rows)}!=:{expected_rows}")
    uncovered = [p for p in explicit if p not in covered]
    if uncovered:
        raise Refusal("coverage_hole_unregistered_surface:" + ",".join(uncovered[:5]))
    unenumerated = [p for p in covered if p not in explicit]
    if unenumerated:
        raise Refusal("coverage_extra_unenumerated:" + ",".join(unenumerated[:5]))
    if set_rows < 1:
        raise Refusal("set_coverage_missing")

    return {
        "schema": "chimera.provenance_verification.v1",
        "registry": os.path.abspath(registry_path),
        "repo": os.path.abspath(repo),
        "outcome": "PASS",
        "pins_resolved": len(pins),
        "deep_checks_resolved": deep_resolved,
        "disk_checks_run": disk_checks_run,
        "disk_skipped": bool(skip_disk),
        "rows_checked": len(rows),
        "verdicts": verdicts,
        "restricted_rows": sorted(r["id"] for r in rows
                                  if r.get("verdict") in VERDICTS_REQUIRING_GATE),
        "explicit_surface_paths": len(explicit),
        "set_coverage_rows": set_rows,
        "closure_rule_enforced": True,
    }


def main(argv: list | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--registry", required=True)
    ap.add_argument("--repo")
    ap.add_argument("--expected-criteria", dest="expected_criteria")
    ap.add_argument("--out")
    ap.add_argument("--skip-disk", action="store_true")
    args = ap.parse_args(argv)
    try:
        report = verify(args.registry, repo=args.repo,
                        expected_criteria=args.expected_criteria,
                        skip_disk=args.skip_disk)
    except Refusal as exc:
        print("REFUSAL:", exc, file=sys.stderr)
        return 3
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(report, fh, indent=2, sort_keys=True)
            fh.write("\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as exc:  # usage/environment error, not a records refusal
        print("ERROR:", exc, file=sys.stderr)
        sys.exit(2)
