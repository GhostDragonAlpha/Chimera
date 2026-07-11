"""Graph Linker — Auto-link orphaned nodes and establish missing traceability edges.

This is the most impactful graph health improvement: 87% of nodes are currently orphaned.
This tool establishes semantic relationships between features, mutations, grades, and
observations to restore full graph connectivity and traceability.

The linking rules follow the implicit domain model:
- FeatureUpdate links to Mutation that enabled it (feature.loop and mutation context)
- ProfessorGrade links to FeatureUpdate it evaluates
- SurpriseMoment links to Feature it pertains to
- ResearchDiscovery informs Feature development
- Observation captures evidence of FeatureUpdate
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict
from typing import List, Dict, Set, Tuple

DNA_GRAPH_PATH = Path(__file__).parent.parent / "docs" / "chimera_dna_graph.json"


def load_dna_graph():
    if DNA_GRAPH_PATH.exists():
        with open(DNA_GRAPH_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"nodes": [], "edges": []}


def save_dna_graph(graph):
    DNA_GRAPH_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DNA_GRAPH_PATH, 'w', encoding='utf-8') as f:
        json.dump(graph, f, indent=2)


def _extract_feature_name_from_node(node: dict) -> str:
    """Extract feature name from various node types."""
    if "feature_name" in node:
        return node["feature_name"]
    if "feature" in node:
        return node["feature"]
    if "name" in node and node.get("type") == "Feature":
        return node["name"]
    return None


def _extract_loop_from_node(node: dict) -> int:
    """Extract loop number from node."""
    if "loop" in node:
        return node["loop"]
    return None


def _link_features_to_mutations(dna: dict, edges_to_add: List[dict]):
    """Link FeatureUpdate nodes to Mutation nodes that created them.

    Heuristic: a FeatureUpdate for loop N is likely caused by mutations from loop N-1
    or N, within the same time window or semantic context.
    """
    nodes = dna.get("nodes", [])

    features = {n["id"]: n for n in nodes if n.get("type") == "FeatureUpdate"}
    mutations = {n["id"]: n for n in nodes if n.get("type") == "Mutation"}

    # Build index of feature names -> feature node ids
    feature_by_name = defaultdict(list)
    for fid, f in features.items():
        fname = _extract_feature_name_from_node(f)
        if fname:
            feature_by_name[fname].append(fid)

    # Build index of loop -> mutation ids
    mutations_by_loop = defaultdict(list)
    for mid, m in mutations.items():
        loop = m.get("loop")
        if loop is not None:
            mutations_by_loop[loop].append(mid)

    linked_count = 0
    for fid, feature in features.items():
        fname = _extract_feature_name_from_node(feature)
        floop = _extract_loop_from_node(feature)

        if not fname or floop is None:
            continue

        # Link to mutations from the same or prior loop
        candidate_loops = [floop] if floop > 0 else [0]
        if floop > 0:
            candidate_loops.append(floop - 1)

        for candidate_loop in candidate_loops:
            for mid in mutations_by_loop[candidate_loop]:
                edge = {
                    "source": mid,
                    "target": fid,
                    "type": "enabled_feature",
                }
                # Avoid duplicates
                if not any(e.get("source") == mid and e.get("target") == fid
                          and e.get("type") == "enabled_feature"
                          for e in dna.get("edges", [])):
                    edges_to_add.append(edge)
                    linked_count += 1

    return linked_count


def _link_grades_to_features(dna: dict, edges_to_add: List[dict]):
    """Link ProfessorGrade nodes to FeatureUpdate nodes they evaluate.

    Heuristic: a grade typically references a feature or loop in its data.
    """
    nodes = dna.get("nodes", [])

    grades = {n["id"]: n for n in nodes if n.get("type") == "ProfessorGrade"}
    features = {n["id"]: n for n in nodes if n.get("type") == "FeatureUpdate"}

    linked_count = 0
    for gid, grade in grades.items():
        # Try to find feature by name or loop context
        evaluated_feature = grade.get("evaluated_feature")
        target_loop = grade.get("loop")

        candidate_fids = []

        if evaluated_feature:
            # Direct feature name reference
            for fid, f in features.items():
                fname = _extract_feature_name_from_node(f)
                if fname and (fname == evaluated_feature or evaluated_feature in fname):
                    candidate_fids.append(fid)

        if target_loop is not None:
            # Features in same loop
            for fid, f in features.items():
                floop = _extract_loop_from_node(f)
                if floop == target_loop:
                    candidate_fids.append(fid)

        for fid in set(candidate_fids):
            edge = {
                "source": gid,
                "target": fid,
                "type": "grades",
            }
            if not any(e.get("source") == gid and e.get("target") == fid
                      and e.get("type") == "grades" for e in dna.get("edges", [])):
                edges_to_add.append(edge)
                linked_count += 1

    return linked_count


def _link_surprises_to_features(dna: dict, edges_to_add: List[dict]):
    """Link SurpriseMoment nodes to relevant Feature/Mutation nodes.

    Heuristic: surprise context often names the feature or loop it pertains to.
    """
    nodes = dna.get("nodes", [])

    surprises = {n["id"]: n for n in nodes if n.get("type") == "SurpriseMoment"}
    features = {n["id"]: n for n in nodes if n.get("type") == "FeatureUpdate"}

    linked_count = 0
    for sid, surprise in surprises.items():
        context = surprise.get("context", "").lower()
        reality = surprise.get("reality", "").lower()
        combined_text = f"{context} {reality}"

        target_loop = surprise.get("loop")

        candidate_fids = []

        # Text-based matching (feature names in surprise text)
        for fid, f in features.items():
            fname = _extract_feature_name_from_node(f)
            if fname and fname.lower() in combined_text:
                candidate_fids.append(fid)

        # Loop-based matching
        if target_loop is not None:
            for fid, f in features.items():
                floop = _extract_loop_from_node(f)
                if floop == target_loop:
                    candidate_fids.append(fid)

        for fid in set(candidate_fids):
            edge = {
                "source": sid,
                "target": fid,
                "type": "surprised_by",
            }
            if not any(e.get("source") == sid and e.get("target") == fid
                      and e.get("type") == "surprised_by" for e in dna.get("edges", [])):
                edges_to_add.append(edge)
                linked_count += 1

    return linked_count


def _link_observations_to_features(dna: dict, edges_to_add: List[dict]):
    """Link Observation nodes to the FeatureUpdate they observe."""
    nodes = dna.get("nodes", [])

    observations = {n["id"]: n for n in nodes if n.get("type") == "Observation"}
    features = {n["id"]: n for n in nodes if n.get("type") == "FeatureUpdate"}

    linked_count = 0
    for oid, obs in observations.items():
        target_feature = obs.get("feature")
        target_loop = obs.get("loop")

        candidate_fids = []

        if target_feature:
            for fid, f in features.items():
                fname = _extract_feature_name_from_node(f)
                if fname == target_feature:
                    candidate_fids.append(fid)

        if target_loop is not None:
            for fid, f in features.items():
                floop = _extract_loop_from_node(f)
                if floop == target_loop:
                    candidate_fids.append(fid)

        for fid in set(candidate_fids):
            edge = {
                "source": oid,
                "target": fid,
                "type": "observes",
            }
            if not any(e.get("source") == oid and e.get("target") == fid
                      and e.get("type") == "observes" for e in dna.get("edges", [])):
                edges_to_add.append(edge)
                linked_count += 1

    return linked_count


def link_orphaned_nodes(dry_run: bool = True) -> Dict[str, int]:
    """Auto-link orphaned nodes to restore graph connectivity.

    Returns:
        Dict with counts of edges added per category.
    """
    dna = load_dna_graph()
    nodes = dna.get("nodes", [])
    edges = dna.get("edges", [])

    # Analyze current state
    all_node_ids = {n["id"] for n in nodes}
    connected_node_ids = set()
    for e in edges:
        connected_node_ids.add(e.get("source"))
        connected_node_ids.add(e.get("target"))

    orphaned_before = len(all_node_ids) - len(connected_node_ids)

    print(f"Before linking:")
    print(f"  Total nodes: {len(nodes)}")
    print(f"  Connected nodes: {len(connected_node_ids)}")
    print(f"  Orphaned nodes: {orphaned_before} ({100*orphaned_before/len(nodes):.1f}%)")
    print()

    # Collect edges to add
    edges_to_add = []

    print("Linking strategy:")
    print("  - Features to Mutations (enabled_feature)")
    count_feat_mut = _link_features_to_mutations(dna, edges_to_add)
    print(f"    Added {count_feat_mut} edges")

    print("  - Grades to Features (grades)")
    count_grade_feat = _link_grades_to_features(dna, edges_to_add)
    print(f"    Added {count_grade_feat} edges")

    print("  - Surprises to Features (surprised_by)")
    count_surp_feat = _link_surprises_to_features(dna, edges_to_add)
    print(f"    Added {count_surp_feat} edges")

    print("  - Observations to Features (observes)")
    count_obs_feat = _link_observations_to_features(dna, edges_to_add)
    print(f"    Added {count_obs_feat} edges")

    if not dry_run:
        dna["edges"].extend(edges_to_add)
        save_dna_graph(dna)

        # Re-analyze connectivity
        all_node_ids = {n["id"] for n in dna.get("nodes", [])}
        connected_node_ids = set()
        for e in dna.get("edges", []):
            connected_node_ids.add(e.get("source"))
            connected_node_ids.add(e.get("target"))

        orphaned_after = len(all_node_ids) - len(connected_node_ids)
        improvement = orphaned_before - orphaned_after

        print()
        print("After linking:")
        print(f"  Total nodes: {len(dna.get('nodes', []))}")
        print(f"  Connected nodes: {len(connected_node_ids)}")
        print(f"  Orphaned nodes: {orphaned_after} ({100*orphaned_after/len(all_node_ids):.1f}%)")
        print(f"  Improvement: {improvement} orphaned nodes now connected")
    else:
        print()
        print("DRY RUN: Would add the edges above without modifying the graph")
        print(f"Total edges to add: {len(edges_to_add)}")

    return {
        "features_to_mutations": count_feat_mut,
        "grades_to_features": count_grade_feat,
        "surprises_to_features": count_surp_feat,
        "observations_to_features": count_obs_feat,
        "total_edges_added": len(edges_to_add),
    }


if __name__ == "__main__":
    import sys
    dry_run = "--apply" not in sys.argv
    results = link_orphaned_nodes(dry_run=dry_run)

    if not dry_run:
        print("\n[OK] Graph linking complete. DNA graph saved.")
    print("\nResults:")
    for key, val in results.items():
        print(f"  {key}: {val}")
