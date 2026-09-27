"""implementation.py -- MAT2-P03: reconcile current work and receipts into the
existing ledger, read-only, with the material-first additions.

Reuses the accepted ONT-P03 ledger design (PR #140, head e1443d45: four ledger
identities per live card -- owner, source revision, scoped verdict, receipt --
with every missing identity named, never silent; registry opened read-only via
``Registry(...).readonly()``) and extends it with the two material-first clause
additions:

1. CROSSWALK: every card in the archived pre-adoption board
   (``scope_archives["01ea5cdd…"]["board"]``, scope
   01ea5cddca8d4795caa096945edf7eadcd1f3eb3e2f084fd2ee36a08cae12ef6) is mapped
   to its revised MAT2 requirement id (``ONT-<XX>`` -> ``MAT2-<XX>``) or, for
   campaign-workflow cards (``D-*``, ``I-*``, ``R5-*``), classified as a
   workflow receipt with no catalog target. Every crosswalk row is recorded as
   HISTORICAL EVIDENCE ONLY: ``promoted_to_acceptance`` is always false -- an
   old DONE verdict never satisfies a MAT2 clause.
2. MATERIAL SEARCH: a frozen, bounded probe list over the existing repository
   records what material-graph/code artifacts exist (with true sha256) and
   which catalog-referenced paths are absent (explicit UNAVAILABLE entries,
   never fabricated), so later tasks search the existing graph before adding
   work.

Exit 0 = reconciliation tabled (gaps, if any, are FINDINGS in the output,
never silent). Exit 1 = structural failure to read the registry.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

MODULES = pathlib.Path("E:/PythonChimera/tools/monkey_campaign")
sys.path.insert(0, str(MODULES))

from agent_slots import Registry  # noqa: E402

REPO_ROOT = pathlib.Path("E:/PythonChimera")
REQUIRED_ATTEMPT_FIELDS = ("id", "agent_id", "state", "workspace",
                           "criteria_sha256")
SCHEMA = "mat2-p03.ledger_reconciliation.v1"
OLD_SCOPE_SHA256 = ("01ea5cddca8d4795caa096945edf7eadcd1f3eb3e2f084fd2ee36a"
                    "08cae12ef6")
NEW_SCOPE_SHA256 = ("cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aa"
                    "e57996097")
# Frozen probe list, identical to PREREGISTRATION.md Probe C (order matters).
FROZEN_PROBE_PATHS = (
    "tools/monkey_campaign/monkey_completion_map.json",
    "tools/monkey_campaign/APPROVED_SCOPE.json",
    "docs/MONKEY_RUN.md",
    "docs/THE_MASTER_LIST.md",
    "docs/THE_HOLODECK_BLUEPRINT.md",
    "docs/roadmap/holodeck_tasks.json",
    "docs/architecture/CREATURE_ARCHITECTURE_REBASE_2026-09-15.md",
    "agent_logs/local_buffy_qwen/assembly_handoff_02.md",
    "forearm_package/ANATOMICAL_DECISION_TABLE.md",
    "planning_inventory.json",
    "plans/material-first-v2",
    "Chimera/core/membranes.py",
    "Chimera/core/membrane_shapes.py",
    "Chimera/core/matter_derive.py",
)


def reconcile_card(card) -> dict:
    """Four ledger identities for one live card (ONT-P03 design, reused)."""
    row = {"id": card.get("id"), "lane": card.get("lane"),
           "state": card.get("state"),
           "criteria_sha256_present": bool(card.get("criteria_sha256")),
           "missing": []}
    if not card.get("criteria_sha256"):
        row["missing"].append("criteria_sha256")

    attempts = card.get("attempts") or {}
    row["owners"] = sorted({a.get("agent_id") for a in attempts.values()
                            if a.get("agent_id")})
    for aid, a in attempts.items():
        for field in REQUIRED_ATTEMPT_FIELDS:
            if not a.get(field):
                row["missing"].append(f"attempt:{aid}:{field}")

    winner = card.get("winner")
    row["source_revision"] = {
        "winner_head": (winner or {}).get("head_sha"),
        "winner_merge": (winner or {}).get("merge_commit_sha"),
        "winner_pr": (winner or {}).get("pr_url"),
    }
    row["receipts"] = {
        "prs": sorted((card.get("prs") or {}).keys()
                      if isinstance(card.get("prs"), dict)
                      else (card.get("prs") or [])),
        "publication_requests": [
            {"id": r.get("id"), "status": r.get("status"),
             "artifacts": len(r.get("artifacts") or [])}
            for r in (card.get("publication_requests") or [])],
        "winner_merge_sha": (winner or {}).get("merge_commit_sha"),
    }
    verdicts = []
    for review in (card.get("worker_reviews") or []):
        verdicts.append({"reviewer": review.get("agent_id"),
                         "pr": review.get("pr_url"),
                         "head": review.get("head_sha"),
                         "state": review.get("state"),
                         "verdict": ((card.get("prs") or {}).get(
                             review.get("pr_url"), {}).get("review", {})
                             or {}).get("verdict")})
    row["scoped_verdicts"] = verdicts

    if card.get("state") != "DONE" and not attempts:
        row["missing"].append("owner:no_active_attempt")
    if card.get("prs") and not winner and card.get("state") != "DONE":
        row["awaiting"] = "review_or_merge"
    pending = [r for r in (card.get("publication_requests") or [])
               if r.get("status") == "PENDING"]
    if pending:
        row["awaiting"] = "lead_publication"
    row["ledger_complete"] = not row["missing"]
    return row


def classify_clause(old, new):
    """Relation between an archived objective and its MAT2 successor."""
    if old is None or new is None:
        return None
    if old == new:
        return "unchanged"
    if new.startswith(old):
        return ("extended_material_first" if "Material-first" in new
                else "extended")
    return "divergent"


def material_search(root, relpaths=FROZEN_PROBE_PATHS) -> dict:
    """Frozen bounded probe: FOUND entries carry true hashes; absent paths
    become explicit UNAVAILABLE entries. Never fabricates."""
    found, unavailable = [], []
    for rel in relpaths:
        p = pathlib.Path(root) / rel
        if p.is_file():
            import hashlib
            data = p.read_bytes()
            found.append({"path": rel, "status": "FOUND", "kind": "file",
                          "size_bytes": len(data),
                          "sha256": hashlib.sha256(data).hexdigest()})
        elif p.is_dir():
            found.append({"path": rel, "status": "FOUND", "kind": "directory",
                          "size_bytes": None, "sha256": None})
        else:
            unavailable.append({"path": rel, "status": "UNAVAILABLE"})
    return {"root": str(root), "probe_count": len(relpaths),
            "found": found, "unavailable": unavailable}


def crosswalk(archive, live_board) -> dict:
    """Archived old-scope receipts -> MAT2 requirements, evidence only.

    Every row carries promoted_to_acceptance=False; an old DONE verdict is
    never recorded as satisfying a MAT2 clause.
    """
    board = archive.get("board") or {}
    cards = board.get("cards") or {}
    live_cards = live_board.get("cards") or {}
    backlog = {b.get("id"): b for b in (live_board.get("backlog") or [])}
    rows = []
    mapped = 0
    for cid in sorted(cards):
        c = cards[cid]
        winner = c.get("winner") or {}
        accepted = sum(1 for p in (c.get("prs") or {}).values()
                       if isinstance(p, dict)
                       and (p.get("review") or {}).get("verdict") == "ACCEPTED")
        row = {"archived_id": cid,
               "archived_state": c.get("state"),
               "archived_criteria_sha256": c.get("criteria_sha256"),
               "archived_scope_sha256": OLD_SCOPE_SHA256,
               "archived_receipt": {
                   "winner_pr": winner.get("pr_url"),
                   "winner_head": winner.get("head_sha"),
                   "winner_merge": winner.get("merge_commit_sha"),
                   "accepted_review_count": accepted},
               "mat2_id": None, "target_kind": None,
               "target_criteria_sha256": None, "clause_relation": None,
               "promoted_to_acceptance": False,
               "historical_evidence_only": True}
        suffix = cid[4:] if cid.startswith("ONT-") else None
        if (suffix and len(suffix) == 3 and suffix[0].isalpha()
                and suffix[1:].isdigit()):
            row["mat2_id"] = "MAT2-" + suffix
        if row["mat2_id"] is None:
            row["target_kind"] = "workflow"
        else:
            new_obj = None
            if row["mat2_id"] in live_cards:
                target = live_cards[row["mat2_id"]]
                row["target_kind"] = "card"
                row["target_criteria_sha256"] = target.get("criteria_sha256")
                new_obj = (target.get("spec") or {}).get("objective")
            elif row["mat2_id"] in backlog:
                target = backlog[row["mat2_id"]]
                row["target_kind"] = "backlog"
                # criteria_sha256 is minted when the backlog item becomes a
                # card; until then it is honestly unavailable.
                new_obj = target.get("objective")
            else:
                row["target_kind"] = "missing_target"
            old_obj = (c.get("spec") or {}).get("objective")
            row["clause_relation"] = classify_clause(old_obj, new_obj)
            if row["target_kind"] in ("card", "backlog"):
                mapped += 1
        rows.append(row)
    workflow = sum(1 for r in rows if r["target_kind"] == "workflow")
    mapped_ids = {r["mat2_id"] for r in rows if r["mat2_id"]}
    catalog_ids = set(live_cards) | set(backlog)
    fresh = sorted(catalog_ids - mapped_ids)
    return {"archived_scope_sha256": OLD_SCOPE_SHA256,
            "archived_board_sha256": archive.get("board_sha256"),
            "archive_reason": archive.get("reason"),
            "archived_card_count": len(cards),
            "rows": rows,
            "mapped_to_catalog": mapped,
            "workflow_card_count": workflow,
            "promoted_to_acceptance_count": 0,
            "catalog_task_count": len(catalog_ids),
            "catalog_ids_without_archived_counterpart": fresh,
            "catalog_ids_without_archived_counterpart_count": len(fresh)}


def reconcile(registry_root, repo_root=REPO_ROOT) -> dict:
    registry = Registry(str(registry_root))
    state = registry.readonly()
    board = state.get("kanban", {})
    cards = board.get("cards", {})
    rows = [reconcile_card(c) for c in sorted(cards.values(),
                                              key=lambda c: c.get("slot") or 99)]
    gaps = [r for r in rows if not r["ledger_complete"]]

    archives = state.get("scope_archives") or {}
    archive = archives.get(OLD_SCOPE_SHA256)
    if archive is not None:
        crosswalk_section = crosswalk(archive, board)
    else:
        crosswalk_section = {"archived_scope_sha256": OLD_SCOPE_SHA256,
                             "available": False,
                             "promoted_to_acceptance_count": 0}
        gaps_entry = {"id": f"scope_archive:{OLD_SCOPE_SHA256}",
                      "missing": ["scope_archives"]}
        missing_detail = [{"id": r["id"], "missing": r["missing"]}
                          for r in gaps] + [gaps_entry]
    if archive is not None:
        missing_detail = [{"id": r["id"], "missing": r["missing"]}
                          for r in gaps]

    backlog_scope = next((b.get("ontology_qualification", {}).get(
        "scope_sha256") for b in (board.get("backlog") or [])
        if b.get("id") == "MAT2-P03"), None)

    return {
        "schema": SCHEMA,
        "registry_root": str(registry_root),
        "registry_revision": state.get("revision"),
        "old_scope_sha256": OLD_SCOPE_SHA256,
        "active_scope_sha256": backlog_scope or NEW_SCOPE_SHA256,
        "active_scope_source": ("kanban.backlog[MAT2-P03].ontology_qualification"
                                ".scope_sha256" if backlog_scope else
                                "preregistration constant"),
        "card_count": len(rows),
        "done_with_winner": sum(1 for r in rows
                                if r["state"] == "DONE"
                                and r["source_revision"]["winner_head"]),
        "cards_awaiting_lead_publication": sum(
            1 for r in rows if r.get("awaiting") == "lead_publication"),
        "cards_awaiting_review_or_merge": sum(
            1 for r in rows if r.get("awaiting") == "review_or_merge"),
        "cards_with_missing_identities": len(gaps),
        "missing_detail": missing_detail,
        "rows": rows,
        "all_identities_present": not gaps,
        "crosswalk": crosswalk_section,
        "material_search": material_search(repo_root),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry", default="E:/ChimeraWork/monkey-coordination")
    ap.add_argument("--repo-root", default=str(REPO_ROOT))
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)
    result = reconcile(args.registry, pathlib.Path(args.repo_root))
    text = json.dumps(result, indent=1, ensure_ascii=False)
    if args.out:
        out = pathlib.Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8", newline="\n")
    cw = result["crosswalk"]
    summary = {"card_count": result["card_count"],
               "done_with_winner": result["done_with_winner"],
               "cards_awaiting_lead_publication":
                   result["cards_awaiting_lead_publication"],
               "cards_awaiting_review_or_merge":
                   result["cards_awaiting_review_or_merge"],
               "cards_with_missing_identities":
                   result["cards_with_missing_identities"],
               "all_identities_present": result["all_identities_present"],
               "registry_revision": result["registry_revision"],
               "crosswalk_archived_cards": cw.get("archived_card_count"),
               "crosswalk_mapped": cw.get("mapped_to_catalog"),
               "crosswalk_workflow": cw.get("workflow_card_count"),
               "promoted_to_acceptance": cw.get(
                   "promoted_to_acceptance_count"),
               "material_found": len(result["material_search"]["found"]),
               "material_unavailable":
                   len(result["material_search"]["unavailable"])}
    print(json.dumps(summary, indent=1))
    for gap in result["missing_detail"]:
        print("GAP", gap["id"], gap["missing"])
    for u in result["material_search"]["unavailable"]:
        print("UNAVAILABLE", u["path"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
