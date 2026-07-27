"""Graph Compactor — the Generation Protocol's distill-and-archive step (WS4).

The tamed version of the Legacy Loop's "clean slate termination": the DNA graph
NEVER forgets (Biology pillar), but success-noise it no longer needs for recall
is moved — never deleted — to docs/dna_graph_archive.json with provenance
stamps, following fix_dna_key_mismatch_pollution.py's quarantine pattern.

A node is archivable only if ALL hold:
  - type is Mutation or pathway_attempt (all other types are protected)
  - error_signature == success_no_error (failures stay: they teach)
  - older than --days (default 30)
  - superseded: a NEWER node exists in the same family
    (pathway_attempt: same tool+action; Mutation: same template_file)
  - not referenced by any edge and not cited as Heuristic evidence

Usage:
    python -m core.graph_compactor --dry-run          (preview, default-safe)
    python -m core.graph_compactor --days 30 --apply
"""
import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    from core.graphify_interface import load_dna_graph, save_dna_graph
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from graphify_interface import load_dna_graph, save_dna_graph

CHIMERA_ROOT = Path(__file__).parent.parent
ARCHIVE_PATH = CHIMERA_ROOT / "docs" / "dna_graph_archive.json"

ARCHIVABLE_TYPES = {"Mutation", "pathway_attempt"}


def _family(n: dict) -> str:
    if n.get("type") == "pathway_attempt":
        return f"pathway:{n.get('tool','?')}:{n.get('action','?')}"
    return f"mutation:{n.get('template_file','?')}"


def find_archivable(graph: dict, days: int) -> list:
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()[:19]

    referenced = set()
    for e in edges:
        for key in ("source", "target", "from", "to"):
            if e.get(key):
                referenced.add(e[key])
    for n in nodes:
        if n.get("type") == "Heuristic":
            referenced.update(x for x in (n.get("evidence_ids") or []) if isinstance(x, str))
        referenced.update(x for x in (n.get("links") or []) if isinstance(x, str))

    newest_in_family = {}
    for n in nodes:
        if n.get("type") in ARCHIVABLE_TYPES:
            fam = _family(n)
            ts = str(n.get("timestamp", ""))
            if ts > newest_in_family.get(fam, ""):
                newest_in_family[fam] = ts

    out = []
    for n in nodes:
        if n.get("type") not in ARCHIVABLE_TYPES:
            continue
        if n.get("error_signature") != "success_no_error":
            continue
        ts = str(n.get("timestamp", ""))[:19]
        if not ts or ts >= cutoff:
            continue
        if n.get("id") in referenced:
            continue
        fam = _family(n)
        if str(n.get("timestamp", "")) >= newest_in_family.get(fam, ""):
            continue  # the newest of a family always stays live
        out.append(n)
    return out


def main():
    parser = argparse.ArgumentParser(description="Archive superseded success-noise from the DNA graph (never deletes)")
    parser.add_argument("--days", type=int, default=30, help="minimum age in days (default 30)")
    parser.add_argument("--apply", action="store_true", help="actually move nodes (default is dry-run)")
    parser.add_argument("--dry-run", action="store_true", help="explicit dry-run (same as omitting --apply)")
    args = parser.parse_args()

    graph = load_dna_graph()
    nodes = graph.get("nodes", [])
    candidates = find_archivable(graph, args.days)

    fams = {}
    for n in candidates:
        fams[_family(n)] = fams.get(_family(n), 0) + 1
    print(f"live nodes: {len(nodes)}  |  archivable (>{args.days}d, superseded, unreferenced): {len(candidates)}")
    for fam, count in sorted(fams.items(), key=lambda kv: -kv[1])[:12]:
        print(f"    {count:>4}x {fam[:80]}")

    if not args.apply:
        print("dry-run: nothing moved. Re-run with --apply to archive.")
        return 0
    if not candidates:
        print("nothing to archive.")
        return 0

    archived_ids = {n["id"] for n in candidates}
    stamp = datetime.now(timezone.utc).isoformat()
    for n in candidates:
        n["archived_at"] = stamp
        n["superseded_by"] = "newer node in family " + _family(n)

    existing = []
    if ARCHIVE_PATH.exists():
        existing = json.loads(ARCHIVE_PATH.read_text(encoding="utf-8")).get("nodes", [])
    ARCHIVE_PATH.write_text(json.dumps(
        {"archived_note": "moved from chimera_dna_graph.json by core.graph_compactor — NEVER deleted",
         "nodes": existing + candidates}, indent=1), encoding="utf-8")

    keep = [n for n in nodes if n["id"] not in archived_ids]
    save_dna_graph({"nodes": keep, "edges": graph.get("edges", [])})
    print(f"archived {len(candidates)} node(s) -> {ARCHIVE_PATH.name} "
          f"(archive total: {len(existing) + len(candidates)})  |  live: {len(keep)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
