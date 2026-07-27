"""Archive old Mutation nodes to clear gate_node_count_bounded (2015 > 2000).

Moves the oldest ~5% of Mutation-type DNA graph nodes into an archive file,
then saves a trimmed graph so gates pass again. Run once:
    python -m core.archive_old_mutations
"""

import json
from datetime import datetime
from pathlib import Path

# Always resolve from known project root regardless of cwd or invocation method.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent  # E:\PythonChimera\Chimera
DNA_GRAPH_PATH = _PROJECT_ROOT / "docs" / "chimera_dna_graph.json"
ARCHIVE_PATH   = DNA_GRAPH_PATH.parent / f"mutated_nodes_archive_{datetime.utcnow():%Y-%m-%d}.json"


def main():
    print("  Loading DNA graph...")
    with open(DNA_GRAPH_PATH, 'r', encoding='utf-8') as f:
        dna = json.load(f)

    nodes   = dna.get("nodes", [])
    edges   = dna.get("edges", [])
    meta    = dna.get("metadata", {})

    # Identify Mutation-type nodes (oldest first by timestamp / id order).
    mutation_nodes  = [n for n in nodes if n.get("type") == "Mutation"]
    non_mutation     = [n for n in nodes if n.get("type") != "Mutation"]

    print(f"  Total nodes: {len(nodes)} | Mutations: {len(mutation_nodes)} | Others: {len(non_mutation)}")

    # Sort mutations by timestamp (oldest first) and archive the oldest ~5%.
    mutation_nodes.sort(key=lambda n: n.get("timestamp", ""))
    keep_count = int(len(mutation_nodes) * 0.95)          # retain 95 %
    to_archive = mutation_nodes[:len(mutation_nodes) - keep_count]

    print(f"  Archiving {len(to_archive)} oldest Mutation nodes (keeping {keep_count})")

    # Stamp archive metadata on archived entries.
    for n in to_archive:
        n.setdefault("recorded_by", "legacy_pre_provenance")
        n["_archived_at"] = datetime.utcnow().isoformat()
        n["_archive_reason"] = "gate_node_count_bounded - archival"

    # Write archive file.
    with open(ARCHIVE_PATH, 'w', encoding='utf-8') as f:
        json.dump({"nodes": to_archive}, f, indent=2)
    print(f"  Archive written -> {ARCHIVE_PATH}")

    # Save trimmed graph.
    dna["nodes"] = non_mutation + mutation_nodes[len(mutation_nodes) - keep_count:]
    with open(DNA_GRAPH_PATH, 'w', encoding='utf-8') as f:
        json.dump(dna, f, indent=2)
    print(f"  DNA graph trimmed -> {len(dna['nodes'])} nodes")

    # Quick gate check.
    if len(dna["nodes"]) > 2000:
        print("  Warning Gate still fails - more archival needed.")
    else:
        print("  OK Gate passes (<= 2000 nodes). Pipeline can proceed.")


if __name__ == "__main__":
    main()