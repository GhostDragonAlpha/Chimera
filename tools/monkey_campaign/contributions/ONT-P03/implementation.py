"""implementation.py -- ONT-P03: reconcile current work and receipts into the
existing ledger, read-only.

Tables EVERY card in the live campaign registry with the four ledger
identities the card demands -- owner, source revision, scoped verdict,
receipt -- and names any missing identity explicitly. Reuses prior completed
work as recorded (merged winners, recorded reviews, publication requests);
re-derives nothing and writes nothing (Registry opened read-only).

Exit 0 = reconciliation tabled (this is the deliverable; gaps, if any, are
FINDINGS printed in the table, never silent). Exit 1 = structural failure to
read the registry.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

MODULES = pathlib.Path("E:/PythonChimera/tools/monkey_campaign")
sys.path.insert(0, str(MODULES))

from agent_slots import Registry  # noqa: E402

REQUIRED_ATTEMPT_FIELDS = ("id", "agent_id", "state", "workspace",
                           "criteria_sha256")
SCHEMA = "ont-p03.ledger_reconciliation.v1"


def reconcile_card(card) -> dict:
    row = {"id": card.get("id"), "lane": card.get("lane"),
           "state": card.get("state"), "missing": []}
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


def reconcile(registry_root) -> dict:
    registry = Registry(str(registry_root))
    state = registry.readonly()
    board = state.get("kanban", {})
    cards = board.get("cards", {})
    rows = [reconcile_card(c) for c in sorted(cards.values(),
                                              key=lambda c: c.get("slot") or 99)]
    gaps = [r for r in rows if not r["ledger_complete"]]
    return {
        "schema": SCHEMA,
        "registry_root": str(registry_root),
        "card_count": len(rows),
        "done_with_winner": sum(1 for r in rows
                                if r["state"] == "DONE"
                                and r["source_revision"]["winner_head"]),
        "cards_awaiting_lead_publication": sum(
            1 for r in rows if r.get("awaiting") == "lead_publication"),
        "cards_awaiting_review_or_merge": sum(
            1 for r in rows if r.get("awaiting") == "review_or_merge"),
        "cards_with_missing_identities": len(gaps),
        "missing_detail": [{"id": r["id"], "missing": r["missing"]}
                           for r in gaps],
        "rows": rows,
        "all_identities_present": not gaps,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry", default="E:/ChimeraWork/monkey-coordination")
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)
    result = reconcile(args.registry)
    text = json.dumps(result, indent=1, ensure_ascii=False)
    if args.out:
        out = pathlib.Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8", newline="\n")
    summary_keys = ("card_count", "done_with_winner",
                    "cards_awaiting_lead_publication",
                    "cards_awaiting_review_or_merge",
                    "cards_with_missing_identities", "all_identities_present")
    print(json.dumps({k: result[k] for k in summary_keys}, indent=1))
    for gap in result["missing_detail"]:
        print("GAP", gap["id"], gap["missing"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
