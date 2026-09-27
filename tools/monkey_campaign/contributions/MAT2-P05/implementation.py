"""implementation.py -- MAT2-P05: retain milestone recovery and artifact
identity, READ-ONLY reconciliation at the current revision.

Card done_when: "Recoverable commits, run manifests, training checkpoints,
raw/blob/canonical hash labels, and retry rules exist". Profile `records`
(offline, nonvisual); falsifier: "Missing identities or a claimed pass
unsupported by records fails; a screenshot is not a substitute."

RECONCILE-FIRST (see PREREGISTRATION.md, frozen before this file existed):
the legacy card ONT-P05 delivered a known-good five-clause identity audit
(merged via PR #174, merge 78f3b524; source bytes raw SHA-256 e45d837d…,
probe bytes 30f33924… — both bound in its winner receipt). This module does
NOT re-implement those oracles. It materializes (or reads in-tree) the merged
verifier bytes, byte-verifies them against the winner-receipt hashes, and
reuses its parameterized clause functions, binding them to THIS attempt's
identity and to the CURRENT human-pinned scope anchor. On top it adds only
the MAT2-specific layer:

  1. own-identity binding to this attempt (startup receipt
     8daed2f6…, checkout_identity.json head c525b82c… branch-6);
  2. winner-merge resolvability extended to the MAT2 merges
     (MAT2-P01 97993cbe…, MAT2-P03 13a94391…, MAT2-F01 b0108a36…);
  3. preservation verification that the merged prior evidence is still
     byte-identical in the integration branch;
  4. checkpoint-store hash equality against the merged report's frozen
     table (store drift named, never silent);
  5. the governing crosswalk row extracted from the merged MAT2-P03
     artifact with the no-promotion invariant enforced;
  6. dependency verdicts from a read-only registry read;
  7. a labeled live-refresh run of the unmodified merged verifier at its
     own frozen identity/anchor (expected old-anchor drift is a predicted
     finding, not a repair).

All probes are read-only over the live registry and record trees; the only
writes are outputs inside this attempt workspace. CPU-only, stdlib +
the repository's own `integrity`/`agent_slots` modules. Exit 0 = the
reconciliation tabled (findings, if any, are the work product). Exit 2 =
structural failure to read a named record root or to byte-verify the merged
verifier (never a silent pass).
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import pathlib
import re
import subprocess
import sys

CAMPAIGN = pathlib.Path("E:/PythonChimera/tools/monkey_campaign")
if str(CAMPAIGN) not in sys.path:
    sys.path.insert(0, str(CAMPAIGN))

SCHEMA = "mat2-p05.milestone_identity_reconciliation.v1"
ALGORITHM = "sha256-chimera-json-v1"
HEX64 = re.compile(r"[0-9a-f]{64}")
HEX40 = re.compile(r"[0-9a-f]{40}")

# --- own identity (this attempt; frozen from worker_start onboarding) ------
OWN = {
    "arrival_id": "arrival-961a6f78a19c4eb58cafb2c7e1fcbcb1",
    "attempt_id": "01ce64f40de34bcb82782d566ddfed39",
    "task_id": "MAT2-P05",
    "criteria_sha256": "0fbecb6247f21492706fbfe94c2ac0af81060e26a667bb52c91e6b4d89ea4953",
    "receipt_stem": "8daed2f64bc4d3b316da5fdd4d70e7f2de0d6da0e016ec7258b56310abbf1220",
    "base_sha256": "c525b82c7c3ce0128565424764293a3c85811ab3",
    "branch": "branch-6",
    "scope_sha256": "cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097",
}

# --- merged prior evidence (winner receipts bound these hashes) ------------
MERGE_ONT_P05 = "78f3b5248dc5503526fefb763ff3195dc769d957"
MERGE_MAT2_P03 = "13a943911da711a4dd24a450055ba0d1b1fe1d04"
MERGED_MODULE_REL = "tools/monkey_campaign/contributions/ONT-P05/implementation.py"
MERGED_MODULE_RAW = "e45d837d8a32de28449e851b8ec3452141c861f729406177c0987782db6b3cd2"
PRIOR_EVIDENCE = [
    {
        "task": "ONT-P05",
        "pr_url": "https://github.com/GhostDragonAlpha/Chimera/pull/174",
        "head_sha256": "52dbc2ce35857fd442fc2b0ea20b67a58071233e",
        "merge_sha256": MERGE_ONT_P05,
        "rel_path": MERGED_MODULE_REL,
        "expected_raw_sha256": MERGED_MODULE_RAW,
        "role": "source (merged audit verifier)",
    },
    {
        "task": "ONT-P05",
        "pr_url": "https://github.com/GhostDragonAlpha/Chimera/pull/174",
        "head_sha256": "52dbc2ce35857fd442fc2b0ea20b67a58071233e",
        "merge_sha256": MERGE_ONT_P05,
        "rel_path": "tools/monkey_campaign/contributions/ONT-P05/identity_audit.json",
        "expected_raw_sha256": "30f339244dd683cd2ea9bebf0223ffccee860ad9ee3891e489cf846459489d9e",
        "role": "numerical (official probe)",
    },
    {
        "task": "MAT2-P03",
        "pr_url": "https://github.com/GhostDragonAlpha/Chimera/pull/194",
        "head_sha256": "250d6b243947eceb0abd93c6ffadea099a612bd7",
        "merge_sha256": MERGE_MAT2_P03,
        "rel_path": "tools/monkey_campaign/contributions/MAT2-P03/reconciliation.json",
        "expected_raw_sha256": "2ea458a294009c16ce8258e3b364af0df31a57d52468a2b9cf5d7f7e1b205b4f",
        "role": "numerical (governing crosswalk artifact)",
    },
]

# --- winner merges that must resolve as commits (recovery identity) --------
WINNER_MERGES = {
    "ONT-P01": "391f0ede0ebc2f4072c62c3386827b1b4eefc88e",
    "ONT-P03": "736d12cca04964c333410a41ac31ced4bd004344",
    "ONT-X01": "7a3d11eab2d19c04d70b62e1559eca8d97886658",
    "MAT2-P01": "97993cbefaf00380803d8e67652ac51d50c37d06",
    "MAT2-P03": "13a943911da711a4dd24a450055ba0d1b1fe1d04",
    "MAT2-F01": "b0108a364a560909c6c396bd916ec15369c27d7e",
}
# merges the reused merged verifier already resolves itself (its own frozen
# constants); this module adds the MAT2 ones so the two sets never drift.
MERGED_TOOL_MERGES = ("ONT-P01", "ONT-P03", "ONT-X01")
MAT2_MERGES = ("MAT2-P01", "MAT2-P03", "MAT2-F01")

# --- current MAT2 scope anchor and the archived (legacy) anchor ------------
SCOPE_ANCHOR_MAT2 = OWN["scope_sha256"]
SCOPE_ANCHOR_LEGACY = "01ea5cddca8d4795caa096945edf7eadcd1f3eb3e2f084fd2ee36a08cae12ef6"

# --- identified training-checkpoint store (merged report's frozen table) ---
CHECKPOINT_STORE_DIR = "E:/PythonChimera/ChimeraEngine/output/ports"
CHECKPOINT_STORE_EXPECTED = {
    "walk_theta_entrained.npy":
        "8f5dd3a68ec4d430a9883f267112b6f7b043ec1432dba6a59d131e87d2a9af92",
    "walk_theta_mult.npy":
        "ad8ed9a9451f1c943bf535a98f2a7cf2fb38b5e36388b636177c3087854d8e90",
    "stand_theta.npy":
        "684f1eaab29f683ef7c803180c32e9d4f1e5ddd64656d103ac5391fc79e851b7",
    "step_theta.npy":
        "db943f46b29422dc45053c0d9541a0be537cfc93149660a0d8a7cc9cac6e2a3c",
}
CHECKPOINT_STORE_ROLES = [
    ("walk_theta_entrained.npy", "walk policy checkpoint (entrained width)"),
    ("walk_theta_mult.npy", "walk policy checkpoint (plain width)"),
    ("stand_theta.npy", "stand substrate policy checkpoint"),
    ("step_theta.npy", "step policy checkpoint"),
]
RUN_RECORD_REL = "agent_logs/f4_walk_walk_theta_entrained.json"
RUN_RECORD_SHA = "9cd272ea65bd30305d122b9c8b1e5b64b7265d3e60278d74db9b01b5746873aa"

# --- live roots (same record stores the merged verifier pins) --------------
COORD_ROOT = pathlib.Path("E:/ChimeraWork/monkey-coordination")
RECEIPTS_DIR = COORD_ROOT / "startup-receipts"
REPO_ROOT = pathlib.Path("E:/PythonChimera")


def raw_sha256(path) -> str:
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def run_git(checkout, *args):
    proc = subprocess.run(["git", "-C", str(checkout), *args],
                          capture_output=True, text=True)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def git_show_bytes(checkout, rev, rel_path):
    """Exact blob bytes (no text decoding, no whitespace stripping)."""
    proc = subprocess.run(
        ["git", "-C", str(checkout), "show", f"{rev}:{rel_path}"],
        capture_output=True)
    return proc.returncode, proc.stdout, proc.stderr.decode("utf-8",
                                                            "replace").strip()


# ---------------------------------------------------------------- seams ----
def resolve_winner_merges(checkout, merges):
    """git cat-file -t each merge; unresolvable identities are named."""
    rows = []
    for task, sha in sorted(merges.items()):
        row_findings = []
        ok = False
        if HEX40.fullmatch(str(sha)):
            code, out, _ = run_git(checkout, "cat-file", "-t", sha)
            ok = code == 0 and out == "commit"
        else:
            row_findings.append(f"winner_merge_sha_malformed:{task}")
        if not ok:
            row_findings.append(f"winner_merge_unresolvable:{task}:{sha}")
        rows.append({"task": task, "merge_sha256": sha,
                     "resolvable_commit": ok,
                     "findings": row_findings})
    return rows


def check_checkout_head(checkout, identity_path):
    """checkout_identity.json head must be a 40-hex resolvable commit."""
    findings = []
    try:
        ident = json.loads(pathlib.Path(identity_path).read_text(
            encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        return [f"checkout_identity_unreadable:{exc}"]
    head = str(ident.get("head_sha", ""))
    code, out, _ = run_git(checkout, "cat-file", "-t", head)
    if not (HEX40.fullmatch(head) and code == 0 and out == "commit"):
        findings.append(f"checkout_head_unresolvable:{head}")
    branch = ident.get("branch", "")
    if branch != OWN["branch"]:
        findings.append(f"checkout_branch_mismatch:{branch!r}")
    return findings


def verify_preservation(checkout, rows):
    """Recompute raw SHA-256 of merged prior-evidence bytes from git."""
    out = []
    for row in rows:
        rel = row["rel_path"].replace("\\", "/")
        rev = row.get("merge_sha256") or row.get("merge_hint")
        code, data, err = git_show_bytes(checkout, rev, rel)
        findings = []
        match = False
        if code != 0:
            findings.append(f"prior_evidence_absent:{row['task']}:{rel}"
                            f":{err[-120:]}")
        else:
            digest = hashlib.sha256(data).hexdigest()
            if digest != row["expected_raw_sha256"]:
                findings.append(f"prior_evidence_hash_mismatch:{row['task']}:"
                                f"{rel}:{digest}")
            else:
                match = True
        out.append(dict(row, match=match, findings=findings))
    return out


def load_merged_module(path, expected_raw_sha256):
    """Import the merged ONT-P05 verifier ONLY after byte verification."""
    path = pathlib.Path(path)
    if not path.is_file():
        raise ValueError(f"merged_module_absent:{path}")
    digest = raw_sha256(path)
    if digest != expected_raw_sha256:
        raise ValueError(f"merged_module_bytes_unverified:{digest}")
    spec = importlib.util.spec_from_file_location(
        "ont_p05_merged_implementation", str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def extract_crosswalk_row(path, archived_id, mat2_id):
    """Extract the governing crosswalk row; promotion is refused by law."""
    doc = json.loads(pathlib.Path(path).read_text(encoding="utf-8-sig"))
    rows = (doc.get("crosswalk") or {}).get("rows") or []
    for row in rows:
        if row.get("archived_id") == archived_id and \
                row.get("mat2_id") == mat2_id:
            if row.get("promoted_to_acceptance") is not False:
                raise ValueError(
                    f"crosswalk_promotion_illegal:{archived_id}->{mat2_id}")
            return row
    raise KeyError(f"crosswalk_row_absent:{archived_id}->{mat2_id}")


def dependency_verdict(repo, task, card):
    """Dependency verdict from a live (read-only) registry card record."""
    findings = []
    state = card.get("state")
    criteria = card.get("criteria_sha256")
    winner = card.get("winner") or {}
    merge = winner.get("merge_commit_sha")
    merge_ok = False
    if merge:
        code, out, _ = run_git(repo, "cat-file", "-t", merge)
        merge_ok = code == 0 and out == "commit"
        if not merge_ok:
            findings.append(f"dependency_merge_unresolvable:{task}:{merge}")
    else:
        findings.append(f"dependency_winner_absent:{task}")
    if not criteria:
        findings.append(f"dependency_criteria_absent:{task}")
    wcriteria = winner.get("criteria_sha256")
    if criteria and wcriteria and criteria != wcriteria:
        findings.append(f"dependency_criteria_mismatch:{task}")
    satisfied = (state == "DONE" and merge_ok and bool(criteria)
                 and not [f for f in findings
                          if not f.startswith("dependency_criteria_mismatch")])
    if state != "DONE":
        findings.append(f"dependency_not_done:{task}:{state}")
    return {"task": task, "state": state,
            "criteria_sha256": criteria,
            "winner_pr": winner.get("pr_url"),
            "winner_merge": merge,
            "merge_resolvable": merge_ok,
            "satisfied": satisfied,
            "findings": findings}


def verify_store_hashes(store, named, expected_map):
    """Live store files must equal the merged report's frozen table."""
    store = pathlib.Path(store)
    rows = []
    for name, role in named:
        path = store / name
        findings = []
        if not path.is_file():
            findings.append(f"store_file_absent:{name}")
            rows.append({"name": name, "role": role, "present": False,
                         "raw_sha256": None, "match": False,
                         "findings": findings})
            continue
        digest = raw_sha256(path)
        expect = expected_map.get(name)
        if expect is None:
            findings.append(f"store_entry_unlabeled:{name}")
        elif digest != expect:
            findings.append(f"store_hash_mismatch:{name}:{digest}")
        rows.append({"name": name, "role": role, "present": True,
                     "raw_sha256": digest,
                     "match": not findings, "findings": findings})
    return rows


def read_registry_state(root):
    """Read-only registry read; gaps are named, never silent."""
    findings = []
    path = pathlib.Path(root) / "agent_slots.sqlite3"
    if not path.is_file():
        return {"available": False, "revision": None, "state": None,
                "findings": [f"registry_unavailable:{path}"]}
    try:
        from agent_slots import Registry  # noqa: E402
        state = Registry(str(root)).readonly()
    except Exception as exc:  # noqa: BLE001 - any failure is a named finding
        return {"available": False, "revision": None, "state": None,
                "findings": [f"registry_unreadable:{exc}"]}
    return {"available": True, "revision": state.get("revision"),
            "state": state, "findings": findings}


def ensure_within(path, root):
    """Refuse any output path outside the attempt workspace."""
    path = os.path.abspath(str(path))
    root = os.path.abspath(str(root))
    if os.path.commonpath([path, root]).lower() != root.lower():
        raise ValueError(f"write_outside_workspace_refused:{path}")
    return True


def first_unmet_clause(clauses):
    for row in clauses:
        if not row.get("satisfied"):
            return row.get("clause")
    return None


def clause_from_tool(clause, tool_output):
    """Wrap a reused verifier clause output; findings are never dropped."""
    findings = list(tool_output.get("findings") or [])
    satisfied = bool(tool_output.get("satisfied"))
    if not satisfied:
        verdict = "unmet"
    elif findings:
        verdict = "findings_present"
    else:
        verdict = "pass"
    return {"clause": clause, "verdict": verdict, "satisfied": satisfied,
            "findings": findings, "tool_output": tool_output}


# ------------------------------------------------------------- assembly ----
def locate_repo_root(checkout):
    code, out, err = run_git(checkout, "rev-parse", "--show-toplevel")
    if code != 0:
        raise RuntimeError(f"repo_root_unresolvable:{err}")
    return pathlib.Path(out)


def materialize_merged_module(checkout, workspace):
    """Prefer the in-tree merged verifier; else extract from the merge.

    Both paths byte-verify against the winner receipt's raw SHA-256 before
    import; a mismatch is a structural failure (exit 2), never a pass.
    """
    ref_dir = pathlib.Path(workspace) / "reference" / "ONT-P05"
    in_tree = locate_repo_root(checkout) / MERGED_MODULE_REL
    if in_tree.is_file():
        module = load_merged_module(in_tree, MERGED_MODULE_RAW)
        return module, {"path": str(in_tree), "provenance": "in_tree",
                        "raw_sha256": MERGED_MODULE_RAW}
    ref_dir.mkdir(parents=True, exist_ok=True)
    target = ref_dir / "implementation.py"
    code, data, err = git_show_bytes(checkout, MERGE_ONT_P05,
                                     MERGED_MODULE_REL)
    if code != 0:
        raise RuntimeError(f"merged_module_extraction_failed:{err}")
    target.write_bytes(data)
    module = load_merged_module(target, MERGED_MODULE_RAW)
    return module, {"path": str(target),
                    "provenance": f"git show {MERGE_ONT_P05}:{MERGED_MODULE_REL}",
                    "raw_sha256": MERGED_MODULE_RAW}


def audit(checkout, workspace, merged=None, provenance=None,
          battery_runner=None):
    """Assemble the MAT2-P05 reconciliation (read-only; own-identity)."""
    checkout = pathlib.Path(checkout)
    workspace = pathlib.Path(workspace)
    if merged is None:
        merged, provenance = materialize_merged_module(checkout, workspace)

    # Shared record paths: the merged verifier's pinned defaults, with the
    # checkout overridden to THIS attempt's checkout (own identity).
    paths = dict(merged.DEFAULT_PATHS)
    paths["checkout"] = str(checkout)

    clause_rows = []

    # 1. recoverable commits — reused clause with THIS attempt's identity.
    tool = merged.audit_recoverable_commits(
        paths["checkout"], paths["receipts_dir"], expected=OWN)
    extra_findings = []
    merges = {k: v for k, v in WINNER_MERGES.items()
              if k in MAT2_MERGES}
    merge_rows = resolve_winner_merges(checkout, merges)
    extra_findings.extend(f for r in merge_rows for f in r["findings"])
    ident_findings = check_checkout_head(
        checkout, pathlib.Path(paths["checkout"]).parent /
        "checkout_identity.json")
    extra_findings.extend(ident_findings)
    tool = dict(tool)
    tool["findings"] = list(tool.get("findings") or []) + extra_findings
    tool["satisfied"] = bool(tool.get("satisfied")) and not extra_findings
    tool["mat2_winner_merges"] = [
        {k: v for k, v in r.items() if k != "findings"} for r in merge_rows]
    row = clause_from_tool("recoverable_commits", tool)
    row["tool"] = "merged ONT-P05 verifier clause (reuse), identity=THIS attempt"
    clause_rows.append(row)

    # 2. run manifests — reused clause unchanged (F1/F2 findings preserved).
    tool = merged.audit_run_manifests(
        paths["fleet_manifest"], paths["walk_manifest"],
        paths["manifest_schema_sources"],
        generation_repo=paths.get("generation_repo"))
    row = clause_from_tool("run_manifests", tool)
    row["tool"] = "merged ONT-P05 verifier clause (reuse)"
    clause_rows.append(row)

    # 3. training checkpoints — reused clause + store-table equality.
    tool = merged.audit_training_checkpoints(
        paths["curriculum"], paths["training_receipts"],
        paths["checkpoint_law_sources"],
        checkpoint_store=paths.get("checkpoint_store"),
        run_record_sites=paths.get("run_record_sites"),
        trainer_law_sources=paths.get("trainer_law_sources"))
    store_rows = verify_store_hashes(
        paths.get("checkpoint_store") or CHECKPOINT_STORE_DIR,
        CHECKPOINT_STORE_ROLES, CHECKPOINT_STORE_EXPECTED)
    store_findings = [f for r in store_rows for f in r["findings"]]
    tool = dict(tool)
    tool["findings"] = list(tool.get("findings") or []) + store_findings
    tool["satisfied"] = bool(tool.get("satisfied")) and not store_findings
    row = clause_from_tool("training_checkpoints", tool)
    row["tool"] = "merged ONT-P05 verifier clause (reuse) + store-table equality"
    row["store_table"] = store_rows
    clause_rows.append(row)

    # 4. hash labels — reused clause under the CURRENT human-pinned anchor.
    tool = merged.audit_hash_labels(paths["map"], paths["scope_lock"],
                                    paths["checkout"],
                                    anchor=SCOPE_ANCHOR_MAT2)
    row = clause_from_tool("raw_blob_canonical_hash_labels", tool)
    row["tool"] = ("merged ONT-P05 verifier clause (reuse), anchor=cb5475f8…"
                   " (current MAT2 scope)")
    clause_rows.append(row)

    # 5. retry rules — reused clause, batteries re-executed by it.
    tool = merged.audit_retry_rules(
        paths["campaign_dir"], paths["merge_receipts_dir"],
        battery_runner=battery_runner or merged.run_battery)
    row = clause_from_tool("retry_rules", tool)
    row["tool"] = "merged ONT-P05 verifier clause (reuse)"
    clause_rows.append(row)

    # Preservation + crosswalk + registry + dependency (MAT2 layer).
    preservation = verify_preservation(checkout, PRIOR_EVIDENCE)

    code, recon_bytes, err = git_show_bytes(
        checkout, MERGE_MAT2_P03,
        "tools/monkey_campaign/contributions/MAT2-P03/reconciliation.json")
    crosswalk = {"row": None, "findings": []}
    if code != 0:
        crosswalk["findings"].append(f"crosswalk_artifact_unreadable:{err}")
    else:
        ref = workspace / "reference" / "MAT2-P03" / "reconciliation.json"
        ref.parent.mkdir(parents=True, exist_ok=True)
        ref.write_bytes(recon_bytes)
        digest = raw_sha256(ref)
        if digest != PRIOR_EVIDENCE[2]["expected_raw_sha256"]:
            crosswalk["findings"].append(
                f"crosswalk_artifact_hash_mismatch:{digest}")
        else:
            try:
                crosswalk["row"] = extract_crosswalk_row(
                    ref, "ONT-P05", "MAT2-P05")
            except (KeyError, ValueError) as exc:
                crosswalk["findings"].append(f"crosswalk_row_invalid:{exc}")

    registry = read_registry_state(COORD_ROOT)
    dependency = None
    if registry["available"]:
        cards = (registry["state"].get("kanban") or {}).get("cards") or {}
        card = cards.get("MAT2-P03")
        if card is None:
            dependency = {"task": "MAT2-P03", "satisfied": False,
                          "findings": ["dependency_card_absent:MAT2-P03"]}
        else:
            dependency = dependency_verdict(checkout, "MAT2-P03", card)
        own_card = cards.get("MAT2-P05") or {}
        own_attempt = (own_card.get("attempts") or {}).get(
            OWN["attempt_id"]) or {}
    else:
        dependency = {"task": "MAT2-P03", "satisfied": False,
                      "findings": list(registry["findings"])}
        own_card, own_attempt = {}, {}

    result = {
        "schema": SCHEMA,
        "task_id": OWN["task_id"],
        "attempt_id": OWN["attempt_id"],
        "agent_id": OWN["arrival_id"],
        "criteria_sha256": OWN["criteria_sha256"],
        "scope_sha256": OWN["scope_sha256"],
        "base_sha256": OWN["base_sha256"],
        "branch": OWN["branch"],
        "checkout": str(checkout),
        "workspace": str(workspace),
        "merged_verifier": provenance,
        "clause_map": clause_rows,
        "prior_evidence_preservation": preservation,
        "crosswalk": crosswalk,
        "registry": {"available": registry["available"],
                     "revision": registry["revision"],
                     "findings": registry["findings"]},
        "dependency_verdicts": [dependency],
        "own_card": {"state": own_card.get("state"),
                     "attempt_state": own_attempt.get("state")},
        "first_unmet_clause": first_unmet_clause(clause_rows),
    }
    return result


def main(argv=None) -> int:
    here = pathlib.Path(__file__).resolve().parent
    checkout = here.parents[3]  # .../<attempt>/checkout
    workspace = checkout.parent
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(here / "reconciliation.json"),
                    help="write the reconciliation JSON here (attempt "
                         "workspace only)")
    ap.add_argument("--skip-refresh", action="store_true",
                    help="skip the labeled live-refresh run of the unmodified "
                         "merged verifier")
    args = ap.parse_args(argv)
    try:
        ensure_within(args.out, workspace)
        result = audit(checkout, workspace)
    except (RuntimeError, ValueError) as exc:
        print(f"structural_failure:{exc}", file=sys.stderr)
        return 2

    # Labeled live-refresh: the unmodified merged verifier at ITS frozen
    # identity/anchor (predicted old-anchor drift is a named finding).
    if not args.skip_refresh:
        ref = (workspace / "reference" / "ONT-P05")
        module_path = pathlib.Path(result["merged_verifier"]["path"])
        refresh_out = workspace / "refresh_identity_audit.json"
        argv_ = [sys.executable, "-B", str(module_path), "--out",
                 str(refresh_out)]
        try:
            proc = subprocess.run(argv_, cwd=str(here), capture_output=True,
                                  text=True, timeout=1800)
            (here / "refresh_stdout.log").write_text(
                proc.stdout or "", encoding="utf-8")
            (here / "refresh_stderr.log").write_text(
                proc.stderr or "", encoding="utf-8")
            refresh = {"command": " ".join(argv_), "exit_code":
                       proc.returncode,
                       "raw_sha256": raw_sha256(refresh_out)
                       if refresh_out.is_file() else None}
            if refresh_out.is_file():
                try:
                    doc = json.loads(refresh_out.read_text(
                        encoding="utf-8-sig"))
                    refresh["task_id"] = doc.get("task_id")
                    refresh["attempt_id"] = doc.get("attempt_id")
                    refresh["clauses"] = [
                        {"clause": c.get("clause"),
                         "satisfied": c.get("satisfied"),
                         "finding_count": len(c.get("findings") or [])}
                        for c in doc.get("clauses") or []]
                except ValueError as exc:
                    refresh["parse_error"] = str(exc)
            if proc.returncode != 0:
                refresh["findings"] = ["refresh_nonzero_exit:"
                                       f"{proc.returncode}"]
            result["refresh"] = refresh
        except subprocess.TimeoutExpired:
            result["refresh"] = {"findings": ["refresh_timeout"]}
        except OSError as exc:
            result["refresh"] = {"findings": [f"refresh_failed:{exc}"]}

    text = json.dumps(result, indent=1, ensure_ascii=False)
    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text + "\n", encoding="utf-8")
    summary = {row["clause"]: row["verdict"] for row in result["clause_map"]}
    print(json.dumps({"schema": SCHEMA,
                      "clause_verdicts": summary,
                      "first_unmet_clause": result["first_unmet_clause"],
                      "registry_revision": result["registry"]["revision"],
                      "out": str(out)}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
