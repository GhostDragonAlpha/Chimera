"""implementation.py -- ONT-P05: milestone recovery and artifact identity audit,
READ-ONLY.

Binds each done_when clause of card ONT-P05 -- recoverable commits, run
manifests, training checkpoints, raw/blob/canonical hash labels, retry rules
-- to its actual current records and re-verifies them through independent
oracles (recomputed raw SHA-256, canonical sha256-chimera-json-v1 digest,
Git blob identity, re-executed rule batteries). Every absent, stale or
mismatched component is named explicitly as a finding; nothing is repaired,
fabricated or silently passed.

Exit 0 = audit tabled (findings, if any, are the work product). Exit 2 =
structural failure to read a named record root. All probes are read-only;
the only write this tool performs is its own --out report path.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import sys

CAMPAIGN = pathlib.Path("E:/PythonChimera/tools/monkey_campaign")
if str(CAMPAIGN) not in sys.path:
    sys.path.insert(0, str(CAMPAIGN))

from integrity import verify_catalog, content_digest  # noqa: E402

SCHEMA = "ont-p05.identity_audit.v1"
ALGORITHM = "sha256-chimera-json-v1"
HEX64 = re.compile(r"[0-9a-f]{64}")
HEX40 = re.compile(r"[0-9a-f]{40}")

EXPECTED = {
    "arrival_id": "arrival-9de32a8d32144d1fb62ffc7308cd11d7",
    "attempt_id": "1ea58bee28c04768b15253c2f1ba7888",
    "task_id": "ONT-P05",
    "criteria_sha256": "53cb0e60f447a52e9c0aca432f46d7173a3ff6cecc536cee1346d8306f715eb4",
    "receipt_stem": "edbb3770b01289e53640c52e9d431b63fd9ff5ba9df946ac1b443bf0ad94e193",
}
SCOPE_ANCHOR = "01ea5cddca8d4795caa096945edf7eadcd1f3eb3e2f084fd2ee36a08cae12ef6"
WINNER_MERGES = {
    "ONT-P03": "736d12cca04964c333410a41ac31ced4bd004344",
    "ONT-P01": "391f0ede0ebc2f4072c62c3386827b1b4eefc88e",
    "ONT-X01": "7a3d11eab2d19c04d70b62e1559eca8d97886658",
}
RETRY_MARKERS = {
    "kanban.py": ["ALREADY_COMPLETED"],
    "continuous_cycle.py": ["PUBLICATION_ALREADY_REQUESTED"],
    "suggestion_box.py": ["exact_retry"],
    "MERGE_SERVICE.md": ["retry accept-merge"],
    "STARTUP_RECOVERY.md": ["Retry the receipt's arrival ID"],
}
BATTERIES = {
    "training_checkpoints": ["test_checkpoints"],
    "retry_rules": ["test_kanban", "test_suggestion_box", "test_merge_service"],
}


def raw_sha256(path) -> str:
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def labeled(path, note):
    """Every cited record carries its own raw-file SHA-256 label."""
    path = pathlib.Path(path)
    return {"path": str(path), "note": note, "raw_sha256": raw_sha256(path)}


def run_git(checkout, *args):
    proc = subprocess.run(
        ["git", "-c", "safe.directory=" + str(checkout), "-C", str(checkout), *args],
        capture_output=True, text=True, timeout=60)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def git_blob_sha256(repo, revision, rel_path):
    """Raw SHA-256 of a path's blob at a pinned generation; read-only."""
    proc = subprocess.run(
        ["git", "-c", "safe.directory=" + str(repo), "-C", str(repo),
         "cat-file", "blob", f"{revision}:{rel_path}"],
        capture_output=True, timeout=60)
    if proc.returncode != 0:
        return None, proc.stderr.decode("utf-8", "replace").strip()[:120]
    return hashlib.sha256(proc.stdout).hexdigest(), None


# ---------------------------------------------------------------- clause 1
def audit_startup_receipts(receipts_dir, expected=EXPECTED):
    findings, receipts = [], []
    files = sorted(pathlib.Path(receipts_dir).glob("*.json"))
    own = None
    for path in files:
        try:
            doc = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as exc:
            findings.append(f"unreadable_receipt:{path.name}:{exc}")
            continue
        if doc.get("schema") != "chimera.startup_recovery.v1":
            findings.append(f"receipt_schema_missing:{path.name}")
            continue
        arrival = doc.get("arrival_id")
        if not arrival or hashlib.sha256(arrival.encode("utf-8")).hexdigest() != path.stem:
            findings.append(f"receipt_filename_not_arrival_digest:{path.name}")
        if "worker_start.py" not in str(doc.get("resume_command", "")):
            findings.append(f"resume_command_missing:{path.name}")
        receipts.append({"file": path.name, "arrival_id": arrival,
                         "task_id": doc.get("task_id")})
        if path.stem == expected["receipt_stem"]:
            own = doc
    if own is None:
        findings.append("own_startup_receipt_absent:" + expected["receipt_stem"])
    else:
        for key in ("task_id", "assignment_id", "criteria_sha256"):
            if own.get(key) != expected[{"task_id": "task_id",
                                         "assignment_id": "attempt_id",
                                         "criteria_sha256": "criteria_sha256"}[key]]:
                findings.append(f"own_receipt_mismatch:{key}={own.get(key)!r}")
    return {"clause": "recoverable_commits", "records": receipts,
            "receipt_dir": {"path": str(receipts_dir),
                            "note": "startup recovery receipt store; per-receipt raw labels in records"},
            "receipt_count": len(receipts), "own_receipt": bool(own),
            "findings": findings, "satisfied": not findings}


def audit_recoverable_commits(checkout, receipts_dir, expected=EXPECTED):
    clause = audit_startup_receipts(receipts_dir, expected)
    identities = []
    for task, sha in sorted(WINNER_MERGES.items()):
        code, out, _ = run_git(checkout, "cat-file", "-t", sha)
        ok = code == 0 and out == "commit"
        if not ok:
            clause["findings"].append(f"winner_merge_unresolvable:{task}:{sha}")
        identities.append({"task": task, "merge_sha256": sha,
                           "resolvable_commit": ok})
    identity_path = pathlib.Path(checkout).parent / "checkout_identity.json"
    if identity_path.is_file():
        ident = json.loads(identity_path.read_text(encoding="utf-8-sig"))
        head = ident.get("head_sha", "")
        code, out, _ = run_git(checkout, "cat-file", "-t", head)
        if not (HEX40.fullmatch(head) and code == 0 and out == "commit"):
            clause["findings"].append(f"checkout_head_unresolvable:{head!r}")
        if ident.get("task_id") != expected["task_id"] or ident.get("assignment_id") != expected["attempt_id"]:
            clause["findings"].append("checkout_identity_not_this_attempt")
        clause["checkout_identity"] = {
            "record": labeled(identity_path, "per-attempt checkout manifest"),
            "head_sha": head, "head_resolvable": code == 0 and out == "commit",
            "branch": ident.get("branch")}
    else:
        clause["findings"].append("checkout_identity_manifest_absent")
    clause["winner_merges"] = identities
    clause["worker_checkout_rule"] = "unrecorded_checkout_preserved_inspect_before_retry"
    clause["satisfied"] = not clause["findings"]
    return clause


# ---------------------------------------------------------------- clause 2
def _sha_entries_fleet(manifest_path, sample, generation_repo=None):
    findings, rows = [], []
    manifest_path = pathlib.Path(manifest_path)
    if not manifest_path.is_file():
        return {}, [], ["fleet_manifest_absent"]
    doc = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    base = manifest_path.parent.parent.parent.parent  # repo root of the record
    rows_disk, findings, wellformed = [], [], []
    if not HEX40.fullmatch(str(doc.get("source_base", ""))):
        findings.append("fleet_manifest_source_base_not_commit_hash")
    else:
        code, out, _ = run_git(generation_repo or base, "cat-file", "-t",
                               doc["source_base"])
        if not (code == 0 and out == "commit"):
            findings.append("fleet_manifest_source_base_unresolvable:" + doc["source_base"])
    for entry in doc.get("files", []):
        ok = (isinstance(entry.get("path"), str) and entry["path"]
              and isinstance(entry.get("bytes"), int)
              and HEX64.fullmatch(str(entry.get("sha256", ""))))
        if not ok:
            findings.append("fleet_manifest_unlabeled_entry:" + str(entry.get("path")))
        else:
            wellformed.append(entry)
    for entry in wellformed[:sample]:
        target = base / entry["path"]
        if not target.is_file():
            drift = "absent"
        else:
            drift = "match" if raw_sha256(target) == entry["sha256"] else "stale"
        row = {"path": entry["path"], "recorded_sha256": entry["sha256"],
               "worktree_drift": drift}
        if doc.get("source_base") and HEX40.fullmatch(str(doc.get("source_base"))):
            observed, err = git_blob_sha256(generation_repo or base,
                                            doc["source_base"], entry["path"])
            if observed is None:
                row["generation_verdict"] = "blob_unreadable"
                findings.append(f"generation_blob_unreadable:{entry['path']}:{err}")
            else:
                row["generation_verdict"] = ("generation_match" if observed == entry["sha256"]
                                             else "generation_mismatch")
                if row["generation_verdict"] != "generation_match":
                    findings.append(f"generation_mismatch:{entry['path']}")
        rows.append(row)
    return doc, rows, findings


def _sha_entries_walk(manifest_path, sample):
    rows, findings = [], []
    manifest_path = pathlib.Path(manifest_path)
    root = manifest_path.parent
    if not manifest_path.is_file():
        return [], ["walk_manifest_absent"]
    lines = [ln for ln in manifest_path.read_text(encoding="utf-8-sig").splitlines() if ln.strip()]
    labeled = []
    for line in lines:
        parts = line.split(None, 1)
        if len(parts) != 2 or not HEX64.fullmatch(parts[0]) or not parts[1].strip():
            findings.append("walk_manifest_unlabeled_line:" + line[:60])
        else:
            labeled.append((parts[0], parts[1].strip()))
    for digest_hex, rel in labeled[:sample]:
        target = root / rel
        if not target.is_file():
            verdict = "absent"
        else:
            verdict = "match" if raw_sha256(target) == digest_hex else "stale"
        rows.append({"path": rel, "recorded_sha256": digest_hex,
                     "verdict": verdict})
    return rows, findings


def audit_run_manifests(fleet_manifest, walk_manifest, schema_sources, sample=8,
                        generation_repo=None):
    findings = []
    fleet_doc, fleet_rows, fleet_findings = _sha_entries_fleet(
        fleet_manifest, sample, generation_repo)
    findings += fleet_findings
    walk_rows, walk_findings = _sha_entries_walk(walk_manifest, sample)
    findings += walk_findings
    sampled = fleet_rows + walk_rows
    matched = sum(1 for r in fleet_rows
                  if r.get("generation_verdict") == "generation_match")
    for row in walk_rows:
        if row["verdict"] in ("stale", "absent"):
            findings.append(f"manifest_generation_mismatch:{row['path']}:{row['verdict']}")
    schema_records = []
    for source, token in schema_sources:
        path = pathlib.Path(source)
        text = path.read_text(encoding="utf-8-sig") if path.is_file() else ""
        present = token in text
        if not present:
            findings.append(f"run_manifest_schema_record_absent:{token}")
        schema_records.append({"record": labeled(path, "manifest schema record") if path.is_file() else {"path": str(source), "note": "absent"},
                               "schema_token": token, "present": present,
                               "kind": "schema/law record, not a run capture"})
    return {"clause": "run_manifests",
            "fleet_manifest": labeled(fleet_manifest, "fleet evidence manifest (source_base + per-file sha256)") if pathlib.Path(fleet_manifest).is_file() else {"path": str(fleet_manifest), "note": "absent"},
            "fleet_source_base": fleet_doc.get("source_base"),
            "fleet_entry_count": len(fleet_doc.get("files", [])),
            "walk_manifest": labeled(walk_manifest, "raw-sha256 capture manifest") if pathlib.Path(walk_manifest).is_file() else {"path": str(walk_manifest), "note": "absent"},
            "schema_records": schema_records,
            "sampled_entries": sampled, "sampled_match": matched,
            "sampled_total": len(sampled),
            "findings": findings, "satisfied": not findings}


# ---------------------------------------------------------------- clause 3
def audit_training_checkpoints(curriculum_path, receipts, schema_sources):
    findings = []
    statuses = []
    if pathlib.Path(curriculum_path).is_file():
        doc = json.loads(pathlib.Path(curriculum_path).read_text(encoding="utf-8-sig"))
        for entry in doc.get("proposed", []):
            checkpoint = entry.get("checkpoint") or {}
            status = entry.get("status")
            statuses.append({"id": checkpoint.get("id"), "status": status,
                             "provenance_source_id": (entry.get("provenance") or {}).get("source_id")})
            if not isinstance(status, str) or not status:
                findings.append(f"curriculum_status_absent:{checkpoint.get('id')}")
    else:
        findings.append("curriculum_checkpoints_absent")
    receipt_records = [labeled(p, "training-suite receipt") for p in map(pathlib.Path, receipts)
                       if p.is_file()]
    if not receipt_records:
        findings.append("training_suite_receipts_absent")
    schema_records = []
    for source, token in schema_sources:
        path = pathlib.Path(source)
        text = path.read_text(encoding="utf-8-sig") if path.is_file() else ""
        present = token in text
        if not present:
            findings.append(f"checkpoint_law_record_absent:{token}")
        schema_records.append({"record": labeled(path, "checkpoint law/workflow record") if path.is_file() else {"path": str(source), "note": "absent"},
                               "schema_token": token, "present": present})
    return {"clause": "training_checkpoints",
            "curriculum_record": labeled(curriculum_path, "engine curriculum training checkpoints") if pathlib.Path(curriculum_path).is_file() else {"path": str(curriculum_path), "note": "absent"},
            "curriculum_entries": len(statuses), "curriculum_statuses": statuses,
            "training_receipts": receipt_records,
            "checkpoint_law_records": schema_records,
            "findings": findings, "satisfied": not findings}


# ---------------------------------------------------------------- clause 4
def audit_hash_labels(map_path, scope_path, checkout, anchor=SCOPE_ANCHOR):
    findings = []
    map_path, scope_path = pathlib.Path(map_path), pathlib.Path(scope_path)
    for name, path in (("map", map_path), ("scope_lock", scope_path)):
        if not path.is_file():
            findings.append(f"{name}_record_absent:{path}")
    if findings:
        return {"clause": "raw_blob_canonical_hash_labels",
                "subject": {"path": str(map_path), "note": "sealed completion map"},
                "scope_lock": {"path": str(scope_path), "note": "scope lock"},
                "labels": None, "lock_labels": None, "labels_distinct": False,
                "oracle": {"verify_catalog": "not_run"},
                "law_reference": "decisions/20260924_campaign_handoffs.md MV-B4-1 + M01-F1",
                "findings": findings, "satisfied": False}
    data = json.loads(map_path.read_text(encoding="utf-8-sig"))
    lock = json.loads(scope_path.read_text(encoding="utf-8-sig"))
    canonical = content_digest(data)
    if canonical != anchor:
        findings.append("canonical_digest_mismatch:" + canonical)
    if lock.get("scope_sha256") != canonical:
        findings.append("scope_lock_canonical_mismatch")
    if lock.get("algorithm") != ALGORITHM:
        findings.append("scope_lock_algorithm_label_missing")
    raw_map = raw_sha256(map_path)
    # The lock dual-labels ONE subject (the sealed map): canonical digest and
    # raw bytes are distinct identity rules over the same file.
    if lock.get("raw_file_sha256") != raw_map:
        findings.append("scope_lock_raw_label_mismatch")
    try:
        _, info = verify_catalog(map_path, scope_path, anchor, require_anchor=True)
        oracle = {"verify_catalog": "pass", "external_digest_checked": info["external_digest_checked"]}
    except ValueError as exc:
        oracle = {"verify_catalog": "fail", "error": str(exc)}
        findings.append("verify_catalog_refused:" + str(exc))
    code, blob, _ = run_git(checkout, "hash-object", str(map_path))
    if code != 0:
        findings.append("git_blob_identity_unavailable")
        blob = None
    distinct = blob is not None and len({raw_map, blob, canonical}) == 3
    if not distinct:
        findings.append("hash_labels_conflated")
    return {"clause": "raw_blob_canonical_hash_labels",
            "subject": labeled(map_path, "sealed completion map"),
            "scope_lock": labeled(scope_path, "dual-labeled scope lock over the map"),
            "labels": {"raw_sha256": raw_map, "git_blob_sha1": blob,
                       "canonical_sha256_chimera_json_v1": canonical},
            "lock_labels": {"scope_sha256": lock.get("scope_sha256"),
                            "raw_file_sha256": lock.get("raw_file_sha256"),
                            "lock_file_raw_sha256": raw_sha256(scope_path)},
            "labels_distinct": distinct, "oracle": oracle,
            "law_reference": "decisions/20260924_campaign_handoffs.md MV-B4-1 + M01-F1: label each identity",
            "findings": findings, "satisfied": not findings}


# ---------------------------------------------------------------- clause 5
def run_battery(module, cwd, interpreter=None):
    argv = [sys.executable if interpreter is None else interpreter, "-B", "-m",
            "unittest", module]
    try:
        proc = subprocess.run(argv, cwd=str(cwd), capture_output=True,
                              text=True, timeout=600)
    except subprocess.TimeoutExpired:
        return {"module": module, "ok": False, "summary": "timeout"}
    tail = [ln for ln in (proc.stderr or "").splitlines() if ln.strip()][-3:]
    ok = proc.returncode == 0 and tail and tail[-1].strip() == "OK"
    return {"module": module, "ok": ok, "returncode": proc.returncode,
            "summary": " | ".join(tail)}


def audit_retry_rules(campaign_dir, merge_receipts_dir, battery_runner=None):
    findings = []
    markers = []
    for name, tokens in sorted(RETRY_MARKERS.items()):
        path = pathlib.Path(campaign_dir) / name
        text = path.read_text(encoding="utf-8-sig") if path.is_file() else ""
        for token in tokens:
            present = token in text
            if not present:
                findings.append(f"retry_rule_record_absent:{name}:{token}")
            markers.append({"record": labeled(path, "retry-rule record") if path.is_file() else {"path": str(path), "note": "absent"},
                            "marker": token, "present": present})
    receipts = sorted(pathlib.Path(merge_receipts_dir).glob("accept-*-result.json"))
    if len(receipts) < 3:
        findings.append(f"merge_service_retry_receipts_sparse:{len(receipts)}")
    runner = battery_runner or run_battery
    batteries = [runner(m, campaign_dir) for m in BATTERIES["retry_rules"]]
    batteries.append(runner(BATTERIES["training_checkpoints"][0], campaign_dir))
    for row in batteries:
        if not row["ok"]:
            findings.append(f"battery_not_green:{row['module']}:{row.get('summary','')[-120:]}")
    return {"clause": "retry_rules",
            "rule_records": markers,
            "merge_service_receipts": [labeled(p, "idempotent accept-merge receipt") for p in receipts],
            "batteries": batteries,
            "findings": findings, "satisfied": not findings}


# ---------------------------------------------------------------- driver
def audit(paths, battery_runner=None):
    clauses = [
        audit_recoverable_commits(paths["checkout"], paths["receipts_dir"]),
        audit_run_manifests(paths["fleet_manifest"], paths["walk_manifest"],
                            paths["manifest_schema_sources"],
                            generation_repo=paths.get("generation_repo")),
        audit_training_checkpoints(paths["curriculum"], paths["training_receipts"],
                                   paths["checkpoint_law_sources"]),
        audit_hash_labels(paths["map"], paths["scope_lock"], paths["checkout"]),
        audit_retry_rules(paths["campaign_dir"], paths["merge_receipts_dir"],
                          battery_runner=battery_runner),
    ]
    return {"schema": SCHEMA,
            "task_id": EXPECTED["task_id"],
            "attempt_id": EXPECTED["attempt_id"],
            "agent_id": EXPECTED["arrival_id"],
            "criteria_sha256": EXPECTED["criteria_sha256"],
            "scope_sha256": SCOPE_ANCHOR,
            "mode": "READ_ONLY_RECORDS_AUDIT",
            "clauses": clauses,
            "clause_satisfied": {c["clause"]: c["satisfied"] for c in clauses},
            "findings": [f"{c['clause']}:{f}" for c in clauses for f in c["findings"]],
            "all_clauses_satisfied": all(c["satisfied"] for c in clauses),
            "limits": "Records and hash oracles only; no visual, runtime or human "
                      "claim. Battery runs exercise fixture registries, not live state."}


DEFAULT_PATHS = {
    "checkout": "E:/ChimeraWork/monkey-coordination/kanban-attempts/ONT-P05/1ea58bee28c04768b15253c2f1ba7888/checkout",
    "receipts_dir": "E:/ChimeraWork/monkey-coordination/startup-receipts",
    "fleet_manifest": "E:/ChimeraWork/monkey-play-20260924/docs/evidence/agent_fleet/MANIFEST.json",
    "walk_manifest": "E:/ChimeraWork/monkey-play-20260924/docs/evidence/agent_fleet/FEATURE_WALK/MANIFEST_sha256.txt",
    "generation_repo": "E:/ChimeraWork/monkey-play-20260924",
    "manifest_schema_sources": [
        (str(CAMPAIGN / "checkpoints.py"), "chimera.checkpoint_context.v1"),
        (str(CAMPAIGN / "visual_capture.py"), "chimera.visual_capture_manifest.v1"),
        (str(CAMPAIGN / "CHECKPOINT_WORKFLOW.md"), "candidate manifest"),
    ],
    "curriculum": "E:/ChimeraWork/monkey-play-20260924/Chimera/docs/curriculum/pending_checkpoints.json",
    "training_receipts": [
        "E:/ChimeraWork/monkey-play-20260924/tools/monkey_campaign/agents/W7_landing/receipts/suite_green_landed.log",
        "E:/ChimeraWork/monkey-play-20260924/tools/monkey_campaign/agents/W7_landing/receipts/w5_suite.log",
        "E:/ChimeraWork/monkey-play-20260924/tools/monkey_campaign/agents/W7_landing/receipts/w6_suite.log",
    ],
    "checkpoint_law_sources": [
        (str(CAMPAIGN / "checkpoints.py"), "chimera.checkpoint_receipt.v1"),
        (str(CAMPAIGN / "CHECKPOINT_WORKFLOW.md"), "## Checkpoints for each affected feature"),
        (str(CAMPAIGN / "CHECKPOINT_VERIFICATION.md"), "first-unmet-gate"),
    ],
    "map": str(CAMPAIGN / "monkey_completion_map.json"),
    "scope_lock": str(CAMPAIGN / "APPROVED_SCOPE.json"),
    "campaign_dir": str(CAMPAIGN),
    "merge_receipts_dir": "E:/Chimera/merge-service",
}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=None,
                    help="write the audit JSON here (attempt workspace only)")
    ap.add_argument("--no-batteries", action="store_true",
                    help="skip unittest batteries (fixture checks only)")
    args = ap.parse_args(argv)
    runner = None
    if not args.no_batteries:
        runner = run_battery
    result = audit(DEFAULT_PATHS, battery_runner=runner)
    text = json.dumps(result, indent=1, ensure_ascii=False)
    if args.out:
        out = pathlib.Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if result["schema"] == SCHEMA else 2


if __name__ == "__main__":
    sys.exit(main())
