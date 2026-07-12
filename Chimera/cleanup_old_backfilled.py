"""Clean up old backfilled entries that have been superseded by newer LIVE entries.

This prevents the DNA graph from accumulating stale backfilled entries while
keeping the idempotency flag intact so fix_dna_key_mismatch_pollution.py
never re-records the same repair twice.

Strategy:
1. Find all BACKFILLED FeatureUpdate entries older than today
2. For each, check if a newer LIVE FeatureUpdate exists for the same feature
3. If yes, move the backfilled entry to quarantine
4. Archive the quarantine to docs/dna_graph_quarantine_old_backfilled.json
"""
import json
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))
from graphify_interface import load_dna_graph, save_dna_graph, DNA_GRAPH_PATH

QUARANTINE_PATH = DNA_GRAPH_PATH.parent / "dna_graph_quarantine_old_backfilled.json"
TODAY = "2026-07-11"  # Fix to today's date


def find_latest_live_timestamp_per_feature(nodes):
    """Return dict of {feature_name: latest_live_timestamp} for LIVE FeatureUpdates."""
    latest_live = {}
    for n in nodes:
        if n.get("type") != "FeatureUpdate":
            continue
        if n.get("backfilled"):  # Skip backfilled
            continue
        fname = n.get("feature_name")
        if not fname or fname == "unknown_feature":
            continue
        ts = n.get("timestamp", "")
        if fname not in latest_live or ts > latest_live[fname]:
            latest_live[fname] = ts
    return latest_live


def cleanup():
    dna = load_dna_graph()
    nodes = dna.get("nodes", [])
    edges = dna.get("edges", [])

    # Find latest LIVE timestamp per feature
    latest_live = find_latest_live_timestamp_per_feature(nodes)

    # Find OLD backfilled entries to archive
    # (Keep today's backfilled entries in case fixer needs to re-run)
    old_backfilled = []
    keep = []
    for n in nodes:
        if n.get("type") != "FeatureUpdate":
            keep.append(n)
            continue
        if not n.get("backfilled"):
            keep.append(n)
            continue
        # Is it from today?
        ts = n.get("timestamp", "")
        if ts.startswith(TODAY):
            keep.append(n)  # Keep today's backfilled entries
            continue
        # Is there a newer LIVE entry for this feature?
        fname = n.get("feature_name")
        if fname in latest_live and latest_live[fname] > ts:
            old_backfilled.append(n)  # Archive it
        else:
            keep.append(n)  # Keep it (no newer LIVE entry exists)

    # Remove edges to archived nodes
    archived_ids = {n["id"] for n in old_backfilled}
    kept_edges = [e for e in edges
                  if e.get("source") not in archived_ids and e.get("target") not in archived_ids]

    print(f"nodes: {len(nodes)} -> {len(keep)} (archived {len(old_backfilled)})")
    print(f"edges: {len(edges)} -> {len(kept_edges)} (dropped {len(edges) - len(kept_edges)})")

    # Append to quarantine archive
    existing = []
    if QUARANTINE_PATH.exists():
        existing = json.loads(QUARANTINE_PATH.read_text(encoding="utf-8")).get("nodes", [])
    QUARANTINE_PATH.write_text(json.dumps({
        "cleaned_up_at": datetime.now(timezone.utc).isoformat(),
        "reason": "old backfilled entries superseded by newer LIVE entries (retained today's for idempotency)",
        "nodes": existing + old_backfilled,
    }, indent=2), encoding="utf-8")
    print(f"quarantine archive: {QUARANTINE_PATH} ({len(existing) + len(old_backfilled)} nodes total)")

    dna["nodes"] = keep
    dna["edges"] = kept_edges
    save_dna_graph(dna)
    return len(old_backfilled)


if __name__ == "__main__":
    removed = cleanup()
    dna = load_dna_graph()
    print(f"final node count: {len(dna.get('nodes', []))}")
    print("done")
