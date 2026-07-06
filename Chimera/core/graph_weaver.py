"""
Graph Weaver — Edge management for the Chimera DNA graph.

Creates edges between related nodes so the graph is actually a graph,
not just a flat list of nodes. Called by the Harness after every
mutation, grade, or verification.

Edge types:
- "professor_grade_for" — ProfessorGrade → FeatureUpdate
- "verified_by" — FeatureUpdate → VisualVerification
- "pathway_for" — pathway_attempt → FeatureUpdate
- "build_for" — Mutation(compilation) → FeatureUpdate
"""

from pathlib import Path
from typing import List, Optional

DNA_GRAPH_PATH = Path("E:/PythonChimera/Chimera/docs/chimera_dna_graph.json")


def _load_graph() -> dict:
    import json
    if DNA_GRAPH_PATH.exists():
        with open(DNA_GRAPH_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"nodes": [], "edges": []}


def _save_graph(graph: dict):
    import json
    with open(DNA_GRAPH_PATH, 'w', encoding='utf-8') as f:
        json.dump(graph, f, indent=2)


def link_nodes(source_id: str, target_id: str, edge_type: str) -> bool:
    """Create an edge between two nodes. Returns True if created, False if exists."""
    graph = _load_graph()
    edges = graph.get("edges", [])

    # Check for duplicate
    for e in edges:
        if e.get("source") == source_id and e.get("target") == target_id and e.get("type") == edge_type:
            return False

    edges.append({
        "source": source_id,
        "target": target_id,
        "type": edge_type,
    })
    _save_graph({"nodes": graph.get("nodes", []), "edges": edges})
    return True


def link_grade_to_feature(grade_id: str, feature_name: str) -> bool:
    """Link a ProfessorGrade node to a FeatureUpdate by feature_name."""
    graph = _load_graph()
    nodes = graph.get("nodes", [])
    for n in nodes:
        if n.get("type") == "FeatureUpdate" and n.get("feature_name") == feature_name:
            return link_nodes(grade_id, n["id"], "professor_grade_for")
    return False


def link_verify_to_feature(verify_id: str, feature_name: str) -> bool:
    """Link a VisualVerification node to a FeatureUpdate by feature_name."""
    graph = _load_graph()
    nodes = graph.get("nodes", [])
    for n in nodes:
        if n.get("type") == "FeatureUpdate" and n.get("feature_name") == feature_name:
            return link_nodes(verify_id, n["id"], "verified_by")
    return False


def link_pathway_to_feature(pathway_id: str, feature_name: str) -> bool:
    """Link a pathway_attempt node to a FeatureUpdate by feature_name."""
    graph = _load_graph()
    nodes = graph.get("nodes", [])
    for n in nodes:
        if n.get("type") == "FeatureUpdate" and n.get("feature_name") == feature_name:
            return link_nodes(pathway_id, n["id"], "pathway_for")
    return False


def get_feature_graph(feature_name: str) -> dict:
    """Return all nodes and edges related to a feature."""
    graph = _load_graph()
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    # Find the feature node
    feature_node = None
    for n in nodes:
        if n.get("type") == "FeatureUpdate" and n.get("feature_name") == feature_name:
            feature_node = n
            break

    if not feature_node:
        return {"feature_node": None, "related_nodes": [], "edges": []}

    # Find all connected nodes
    feature_id = feature_node["id"]
    related_ids = {feature_id}
    connected_edges = []
    for e in edges:
        if e.get("source") == feature_id or e.get("target") == feature_id:
            related_ids.add(e.get("source"))
            related_ids.add(e.get("target"))
            connected_edges.append(e)

    related_nodes = [n for n in nodes if n.get("id") in related_ids]
    return {
        "feature_node": feature_node,
        "related_nodes": related_nodes,
        "edges": connected_edges,
    }


def edge_stats() -> dict:
    """Return edge statistics."""
    graph = _load_graph()
    edges = graph.get("edges", [])
    counts = {}
    for e in edges:
        etype = e.get("type", "unknown")
        counts[etype] = counts.get(etype, 0) + 1
    return {"total_edges": len(edges), "by_type": counts}
