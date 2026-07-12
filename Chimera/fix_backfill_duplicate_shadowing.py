"""Archive duplicate backfilled nodes that shadow genuine feature statuses.

Root cause (fixed in fix_dna_key_mismatch_pollution.py on 2026-07-11):
- fix_dna_key_mismatch_pollution.py's re_record() was NOT idempotent — every run
  unconditionally re-recorded all LOST_FEATURES (2026-07-05-era statuses) plus the
  Loop-0 LoopComplete with fresh `datetime.now()` timestamps.
- A re-run on 2026-07-11T16:24 duplicated 13 FeatureUpdates + 1 LoopComplete, and
  because preflight/rehearsal pick "latest FeatureUpdate by timestamp", the stale
  statuses shadowed every genuine status recorded since 2026-07-05:
    * Player_Character_Animation showed 'blocked' over a real 'verified' (A 98.5,
      2026-07-06) — pointing the loop board's NEXT at already-finished work;
    * Verb_Shovel showed 'verified' over a real 'needs_refinement' (2026-07-08) —
      hiding work the rehearsal decider treats as its highest-value candidate class.

This script (archive-never-delete, mirroring fix_dna_key_mismatch_pollution.py):
1. Groups backfilled FeatureUpdate nodes by (feature_name, status, repair note) and
   backfilled LoopComplete nodes by (loop, name, status).
2. Keeps the EARLIEST node in each group (the original 2026-07-05 backfill — its
   timestamp is closest to the era of the work it describes); later copies are
   information-free duplicates.
3. Moves the duplicates and their edges to
   docs/dna_graph_quarantine_duplicate_backfills.json.

Default is a DRY RUN. Pass --apply to write. Pass --graph <path> to operate on a
copy (used by tests). Idempotent: a second --apply run archives nothing.
"""
import argparse
import json
import sys
import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))
from graphify_interface import load_dna_graph, save_dna_graph, DNA_GRAPH_PATH


def find_duplicate_backfills(nodes):
    """Return the later-duplicate backfilled nodes (keep-earliest wins).

    Pure function: groups backfilled FeatureUpdate nodes by
    (feature_name, status, parameters.re_recorded) and backfilled LoopComplete
    nodes by (loop, name, status); every node after the earliest in a group is a
    duplicate. Non-backfilled nodes are never candidates.
    """
    groups = defaultdict(list)
    for n in nodes:
        if not n.get("backfilled"):
            continue
        t = n.get("type")
        if t == "FeatureUpdate":
            key = ("FeatureUpdate", n.get("feature_name"), n.get("status"),
                   (n.get("parameters") or {}).get("re_recorded"))
        elif t == "LoopComplete":
            key = ("LoopComplete", n.get("loop"), n.get("name"), n.get("status"))
        else:
            continue
        groups[key].append(n)
    dups = []
    for ns in groups.values():
        if len(ns) < 2:
            continue
        ns.sort(key=lambda n: str(n.get("timestamp", "")))
        dups.extend(ns[1:])
    return dups


def _load(path):
    if Path(path) == DNA_GRAPH_PATH:
        return load_dna_graph()
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _save(path, graph):
    if Path(path) == DNA_GRAPH_PATH:
        save_dna_graph(graph)  # atomic, lock-guarded
    else:
        Path(path).write_text(json.dumps(graph, indent=2), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--graph", default=str(DNA_GRAPH_PATH),
                    help="graph file to repair (default: live DNA graph)")
    ap.add_argument("--apply", action="store_true",
                    help="write changes (default: dry run)")
    args = ap.parse_args()

    graph_path = Path(args.graph)
    quarantine_path = graph_path.parent / "dna_graph_quarantine_duplicate_backfills.json"

    dna = _load(graph_path)
    nodes = dna.get("nodes", [])
    edges = dna.get("edges", [])

    dups = find_duplicate_backfills(nodes)
    dup_ids = {n["id"] for n in dups}
    dropped_edges = [e for e in edges
                     if e.get("source") in dup_ids or e.get("target") in dup_ids]

    print(f"graph: {graph_path}")
    print(f"backfilled duplicates found: {len(dups)} "
          f"(edges referencing them: {len(dropped_edges)})")
    for n in sorted(dups, key=lambda n: (str(n.get('type')), str(n.get('feature_name') or n.get('name')))):
        label = n.get("feature_name") or n.get("name")
        print(f"  {n['type']} {label} status={n.get('status')} "
              f"@ {str(n.get('timestamp', ''))[:19]} ({n['id']})")

    if not dups:
        print("nothing to archive — graph is clean")
        return

    if not args.apply:
        print("dry run: nothing moved. Re-run with --apply to archive.")
        return

    keep_nodes = [n for n in nodes if n["id"] not in dup_ids]
    keep_edges = [e for e in edges
                  if e.get("source") not in dup_ids and e.get("target") not in dup_ids]

    existing_nodes, existing_edges = [], []
    if quarantine_path.exists():
        prior = json.loads(quarantine_path.read_text(encoding="utf-8"))
        existing_nodes = prior.get("nodes", [])
        existing_edges = prior.get("edges", [])
    quarantine_path.write_text(json.dumps({
        "quarantined_at": datetime.now(timezone.utc).isoformat(),
        "reason": "duplicate backfill re-records from non-idempotent "
                  "fix_dna_key_mismatch_pollution.py re-runs; fresh timestamps on "
                  "2026-07-05-era statuses shadowed genuine feature statuses in the "
                  "loop board / rehearsal decider (keep-earliest applied)",
        "nodes": existing_nodes + dups,
        "edges": existing_edges + dropped_edges,
    }, indent=2), encoding="utf-8")
    print(f"quarantine archive: {quarantine_path} "
          f"({len(existing_nodes) + len(dups)} nodes total)")

    dna["nodes"] = keep_nodes
    dna["edges"] = keep_edges
    _save(graph_path, dna)
    print(f"nodes: {len(nodes)} -> {len(keep_nodes)}  "
          f"edges: {len(edges)} -> {len(keep_edges)}")
    print("done")


if __name__ == "__main__":
    main()
