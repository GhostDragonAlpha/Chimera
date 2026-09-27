#!/usr/bin/env python3
"""Verifier for the MAT2-P02 prototype-recovery + lineage-reconciliation claim.

Re-verifies, read-only, against a git object store and this directory's frozen
reproduction receipts:

  - identity binding: card criteria, active scope, archived scope, planning id,
    attempt id, and the frozen PREREGISTRATION.md bytes (full-hash equality),
  - every pin (commit, path, blob, raw sha256, byte length, markers) resolves
    through `git rev-parse` / `git cat-file` plumbing only,
  - every frozen prediction receipt (P1-P5) matches its exact anchors,
  - the five-item lineage clause is carried by the merged ONT-P02 map and its
    independent re-verification receipt is PASS with the frozen counts,
  - the named standing gaps are present and UNRESOLVED (a "resolved" gap, a
    trained-policy claim, or a playable-walk claim is a refusal).

Exit codes: 0 = PASS, 1 = IDENTITY_MISMATCH, 3 = named refusal,
2 = usage/environment error.

Usage:
  python -B verify_prototype_recovery.py --pr prototype_recovery.json
         [--repo DIR] [--receipts-dir DIR] [--prereg PREREGISTRATION.md]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys

CARD_TASK_ID = "MAT2-P02"
PLANNING_ID = "P02"
CRITERIA_SHA256 = "28148c96061a42ae49753b622876f9ed1337aadb8f814b34204fb13fc7023c0d"
ACTIVE_SCOPE_SHA256 = "cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097"
ARCHIVED_SCOPE_SHA256 = "01ea5cddca8d4795caa096945edf7eadcd1f3eb3e2f084fd2ee36a08cae12ef6"
ONTP02_CRITERIA_SHA256 = "5c0720b4451b8b9ea22360575461968667496000220c8cba645e1d3e28f252ef"

ANCHOR_SCENE = "f6844eeae3dc87170a572ccdeedf326a6cac4f73d1448941808bd8b25a8db342"
ANCHOR_STDOUT = "8c537cdb7cb8c43cf9423cb50056787bcc31ee487d70d3c2a1e73ed5d60b06cc"
ANCHOR_STDERR = "c6f9b6c00a1d549a4bc709724d2f62f8f28b37823696de4689e1950651c37481"
ANCHOR_DUMP = "b47b709c43a021d24bfee13bb2fe4592167cf205ee0abf9971de462319389c93"
ANCHOR_MOVIE = "2e2982f1e98204a3682b71f70bb6be542ae6b3edeceec9f2ad09f96dcd84699a"

REQUIRED_GAPS = (
    "trained_walking_policy",
    "interactive_playable_walk",
    "judge_stride_phase_verdict",
    "ct_distribution_clearance",
    "cot_denominator_correction",
)

REQUIRED_FIVE_ITEMS = (
    "ct_monkey",
    "source_msk_model",
    "forearm_paddle_assets",
    "training_body",
    "runtime_body",
)


class Refusal(Exception):
    pass


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _git(repo: str | None, *args: str) -> bytes:
    cmd = ["git"]
    if repo:
        cmd += ["-C", repo]
    cmd += list(args)
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        raise Refusal("git_failed:" + " ".join(args) + ":" + r.stderr.decode("utf-8", "replace").strip()[:200])
    return r.stdout


def _require(cond: bool, name: str) -> None:
    if not cond:
        raise Refusal(name)


def _full_hex(value: str, name: str) -> str:
    v = (value or "").strip().lower()
    _require(len(v) == 64 and all(c in "0123456789abcdef" for c in v), "identity_not_full_sha256:" + name)
    return v


def verify(pr_path: str, repo: str | None, receipts_dir: str | None, prereg_path: str | None) -> dict:
    here = os.path.dirname(os.path.abspath(pr_path))
    receipts_dir = receipts_dir or os.path.join(here, "reproduction")
    pr = json.loads(open(pr_path, encoding="utf-8").read())

    # ---- identity binding (full hashes, F1/F3 guard) ----
    _require(pr.get("schema") == "chimera.mat2_p02.prototype_recovery.v1", "schema_mismatch")
    _require(pr.get("task_id") == CARD_TASK_ID, "identity_task_id")
    _require(pr.get("planning_id") == PLANNING_ID, "identity_planning_id")
    _require(_full_hex(pr.get("criteria_sha256", ""), "criteria") == CRITERIA_SHA256, "identity_criteria")
    _require(_full_hex(pr.get("active_scope_sha256", ""), "scope") == ACTIVE_SCOPE_SHA256, "identity_scope")
    _require(_full_hex(pr.get("archived_scope_sha256", ""), "archived_scope") == ARCHIVED_SCOPE_SHA256, "identity_archived_scope")
    _require(pr.get("attempt_id") == "b6607daeeed549aeb865302efd24eb9a", "identity_attempt")
    prereg_path = prereg_path or os.path.join(here, "PREREGISTRATION.md")
    _require(_full_hex(pr.get("preregistration_sha256", ""), "prereg") == _sha(open(prereg_path, "rb").read()),
             "identity_preregistration_bytes")

    # ---- pin resolution (read-only plumbing) ----
    for pin in pr.get("pins", []):
        got = _git(repo, "rev-parse", "%s:%s" % (pin["rev"], pin["path"])).decode().strip()
        _require(got == pin["blob"], "pin_blob_mismatch:" + pin["name"])
        data = _git(repo, "cat-file", "blob", pin["blob"])
        if "sha256" in pin:
            _require(_sha(data) == pin["sha256"], "pin_sha_mismatch:" + pin["name"])
        if "bytes" in pin:
            _require(len(data) == pin["bytes"], "pin_bytes_mismatch:" + pin["name"])
        for marker in pin.get("markers", []):
            _require(marker.encode("utf-8") in data, "pin_marker_missing:" + pin["name"] + ":" + marker[:40])

    # ---- frozen prediction receipts (exact anchors) ----
    def load_receipt(name: str) -> dict:
        p = os.path.join(receipts_dir, name)
        _require(os.path.isfile(p), "receipt_missing:" + name)
        return json.loads(open(p, encoding="utf-8").read())

    p1 = load_receipt("scene_regeneration.json")
    _require(p1.get("scene_sha256") == ANCHOR_SCENE, "P1_scene_anchor")
    _require(p1.get("prediction") == "P1", "P1_label")

    p2 = load_receipt("dump_run_record.json")
    _require(p2.get("scene_sha256") == ANCHOR_SCENE, "P2_scene")
    _require(p2.get("stdout_sha256") == ANCHOR_STDOUT, "P2_stdout_anchor")
    _require(p2.get("stderr_sha256") == ANCHOR_STDERR, "P2_stderr_anchor")
    _require(p2.get("dump1_sha256") == ANCHOR_DUMP, "P2_dump_anchor")
    _require(p2.get("dumps_bit_identical") is True, "P2_dump_determinism")
    _require(p2.get("n_ticks") == 302, "P2_ticks")
    _require(p2.get("base_dx") == 0.9131056683968011, "P2_base_dx")

    p3 = load_receipt("walk_numbers.json")
    _require(p3.get("worst_ledger_J") == 30.970714, "P3_ledger")
    _require(p3.get("ticks_covered") == 302, "P3_ticks")
    _require(p3.get("engine_base_dx_m") == 0.9131, "P3_base_dx")

    p4 = load_receipt("behavior_bytes.json")
    _require(p4.get("movie_sha256") == ANCHOR_MOVIE, "P4_movie_anchor")
    _require(p4.get("movie_bytes") == 1570836, "P4_movie_bytes")
    _require(p4.get("dump_reproduced_equals_intree") is True, "P4_dump_identity")
    _require(p4.get("arithmetic_consistent") is True, "P4_frame_plan")

    p5 = load_receipt("lineage_reverification.json")
    _require(p5.get("outcome") == "PASS", "P5_outcome")
    _require(p5.get("checks_passed") == 152, "P5_checks")
    _require(p5.get("pins_resolved") == 23, "P5_pins")
    _require(p5.get("falsifier_suite") == "23/23 OK", "P5_suite")
    _require(_full_hex(p5.get("criteria_sha256", ""), "ontp02_criteria") == ONTP02_CRITERIA_SHA256, "P5_criteria")

    # ---- five-item clause carried, not re-implemented ----
    carried = pr.get("five_item_clause", {})
    mc = (carried.get("merged_commit") or "").strip().lower()
    _require(len(mc) == 40 and all(c in "0123456789abcdef" for c in mc), "merged_commit_not_full_git_sha")
    _require(mc == "51eaa010177b71d7728234c8b2883ef6547fa3a4", "carried_merged_commit")
    items = carried.get("items", {})
    for name in REQUIRED_FIVE_ITEMS:
        entry = items.get(name, {})
        _require(entry.get("relation") in ("related", "kept_separate"), "clause_relation:" + name)
        _require(entry.get("carried_by") == "ONT-P02 merged map (PR #157)", "clause_carried_by:" + name)

    # ---- gaps: present, honest, unresolved (F3) ----
    gaps = pr.get("gaps", {})
    for name in REQUIRED_GAPS:
        gap = gaps.get(name, {})
        _require(gap.get("status") == "UNRESOLVED", "gap_not_unresolved:" + name)
        _require(len((gap.get("detail") or "").strip()) >= 20, "gap_detail_missing:" + name)

    return {
        "outcome": "PASS",
        "pr": os.path.abspath(pr_path),
        "repo": repo,
        "pins_resolved": len(pr.get("pins", [])),
        "receipts_verified": 5,
        "gaps_recorded": len(gaps),
        "criteria_sha256": CRITERIA_SHA256,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pr", required=True)
    ap.add_argument("--repo", default=None)
    ap.add_argument("--receipts-dir", default=None)
    ap.add_argument("--prereg", default=None)
    args = ap.parse_args(argv)
    repo = args.repo or os.environ.get("MAT2P02_REPO")
    try:
        report = verify(args.pr, repo, args.receipts_dir, args.prereg)
    except Refusal as r:
        print(json.dumps({"outcome": "REFUSED", "refusal": str(r)}, indent=1))
        return 3
    print(json.dumps(report, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
