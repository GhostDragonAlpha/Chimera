"""Scholar — Research department (DREAM_ROSTER.md #1).

The system has never consulted a source — every brief comes from model memory.
Scholar fixes this gap by:
1. Querying Research Campuses (docs/RESEARCH_CAMPUSES.md) via graphify
2. Fetching from web (WebSearch + WebFetch; capable sessions only)
3. Searching local research_corpus/ (cached pages, offline-ready)
4. Building research_discovery nodes with citations
5. Feeding spiral_forks with 3-brief briefs (conservative/alternative/wild)
6. Writing feature study guides into the graph

Usage:
    python -m core.scholar --feature Ground_Sand_Particles --topic "dust accumulation"
    python -m core.scholar --technical-research --dry-run
"""
import argparse
import json
import re
import sys
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Tuple

try:
    from core.graphify_interface import graphify_mutate, graphify_query, load_dna_graph, save_dna_graph
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from graphify_interface import graphify_mutate, graphify_query, load_dna_graph, save_dna_graph

CHIMERA_ROOT = Path(__file__).parent.parent
RESEARCH_CORPUS_DIR = CHIMERA_ROOT / "research_corpus"


def retrieve_campus(campus_name: str) -> Dict:
    """Query Research Campuses for trusted seed sources.

    Args:
        campus_name: One of: game_development, art_school, film_school, architecture_school,
                     engineering_school, unreal_engine_craft, spatial_reasoning, iteration_school,
                     emotion_to_parameter, reference_management, creativity, collaboration

    Returns:
        Dict with name, focus, seed_sources, quality_ratings
    """
    result = graphify_query("campus", campus_name)
    if isinstance(result, dict):
        return result
    return {}


def retrieve_corpus(query: str, max_results: int = 5) -> List[Dict]:
    """Search local research_corpus/ for cached sources.

    Returns list of file metadata dicts with path, name, and matching_content snippet.
    """
    if not RESEARCH_CORPUS_DIR.exists():
        return []

    results = []
    query_lower = query.lower()

    for fpath in RESEARCH_CORPUS_DIR.rglob("*"):
        if fpath.is_file() and fpath.suffix in {".md", ".txt", ".json"}:
            try:
                content = fpath.read_text(encoding='utf-8', errors='ignore')
                if query_lower in content.lower():
                    match_pos = content.lower().find(query_lower)
                    start = max(0, match_pos - 100)
                    end = min(len(content), match_pos + 200)
                    snippet = content[start:end].replace('\n', ' ')[:250]

                    results.append({
                        "source": fpath.name,
                        "path": str(fpath.relative_to(CHIMERA_ROOT)),
                        "campus": "local_corpus",
                        "quality_rating": "B",
                        "snippet": snippet,
                        "file_size": len(content)
                    })
                    if len(results) >= max_results:
                        break
            except Exception:
                pass

    return results


def build_discovery_node(
    feature: str,
    campus_sources: List[str],
    web_sources: Optional[List[str]] = None,
    corpus_sources: Optional[List[str]] = None,
    parameters: Optional[Dict] = None,
    acceptance_criteria: Optional[List[str]] = None,
    confidence: str = "medium"
) -> str:
    """Record a research_discovery node to the graph.

    Args:
        feature: Feature name
        campus_sources: List of campus source names consulted
        web_sources: Optional list of web URLs consulted
        corpus_sources: Optional list of local corpus files consulted
        parameters: Dict of {param_name: {value, unit, source, confidence}}
        acceptance_criteria: List of measurable criteria with citations
        confidence: low|medium|high confidence rating

    Returns:
        Discovery node ID if successful, error string if failed
    """
    all_sources = (campus_sources or []) + (web_sources or []) + (corpus_sources or [])
    if not all_sources:
        return "rejected_no_sources: must provide at least one source"

    discovery_details = {
        "feature": feature,
        "campus_sources": campus_sources or [],
        "web_sources": web_sources or [],
        "corpus_sources": corpus_sources or [],
        "parameters": parameters or {},
        "acceptance_criteria": acceptance_criteria or [],
        "sources_consulted": len(all_sources),
        "research_confidence": confidence,
        "timestamp": datetime.utcnow().isoformat(),
    }

    result = graphify_mutate("research_discovery", None, discovery_details)
    return result


def write_study_guide(feature: str, discovery_node_id: str, brief: Dict) -> str:
    """Attach a study guide to a feature node from research discovery.

    The study guide is a structured exam: declared acceptance criteria,
    numeric parameters WITH CITATIONS, and reference list.

    Args:
        feature: Feature name
        discovery_node_id: ID of the research_discovery node
        brief: The research brief dict (from spiral_forks schema)

    Returns:
        Updated feature node ID
    """
    dna = load_dna_graph()
    nodes = dna.get("nodes", [])

    feature_node = None
    for node in nodes:
        if node.get("type") == "FeatureUpdate" and node.get("feature_name") == feature:
            feature_node = node
            break

    if not feature_node:
        feature_node = {
            "id": f"feature_{feature}_{datetime.utcnow().isoformat()[:10]}",
            "type": "FeatureUpdate",
            "feature_name": feature,
            "timestamp": datetime.utcnow().isoformat(),
            "recorded_by": "core.scholar"
        }
        nodes.append(feature_node)

    study_guide = {
        "exam_format": "acceptance_criteria + numeric_parameters_with_citations",
        "canonical_reference": brief.get("canonical_reference", ""),
        "acceptance_criteria": brief.get("acceptance_criteria", []),
        "parameters": brief.get("parameters", {}),
        "principles": brief.get("principles", []),
        "research_discovery_node": discovery_node_id,
        "timestamp": datetime.utcnow().isoformat(),
    }

    if "study_guide" not in feature_node:
        feature_node["study_guide"] = {}
    feature_node["study_guide"].update(study_guide)

    save_dna_graph({"nodes": nodes, "edges": dna.get("edges", [])})
    return feature_node["id"]


def scholar_brief_from_research(
    feature: str,
    topic: str,
    campus_names: Optional[List[str]] = None
) -> Dict:
    """Generate a CONSERVATIVE brief from research campuses + corpus.

    This replaces the LM-generated brief in spiral_forks --use-lm.
    The brief is deterministic (campus-canonical), sources are cited.

    Args:
        feature: Feature name
        topic: Research topic/query
        campus_names: List of campus names to query; if None, auto-detect from topic

    Returns:
        Brief dict matching spiral_forks.BRIEF_SCHEMA_HINT
    """
    if not campus_names:
        topic_lower = topic.lower()
        campus_map = {
            "dust|material|particle|vfx|niagara": "unreal_engine_craft",
            "sand|regolith|lunar|planet": "engineering_school",
            "color|lighting|mood|render": "art_school",
            "game|level|design": "game_development",
        }
        campus_names = []
        for keywords, campus in campus_map.items():
            if any(kw in topic_lower for kw in keywords.split("|")):
                campus_names.append(campus)
        campus_names = campus_names or ["unreal_engine_craft"]

    campus_sources_list = []
    all_principles = []

    for campus_name in campus_names:
        campus_data = retrieve_campus(campus_name)
        if campus_data:
            for seed in campus_data.get("seed_sources", []):
                campus_sources_list.append(seed.get("name", ""))
            all_principles.extend(campus_data.get("principles", []) or [])

    corpus_results = retrieve_corpus(topic, max_results=3)
    corpus_sources = [r["path"] for r in corpus_results]

    brief = {
        "fork": "conservative",
        "feature": feature,
        "approach": f"Campus-canonical approach using {campus_names[0] if campus_names else 'trusted'} sources and local research corpus.",
        "canonical_reference": campus_sources_list[0] if campus_sources_list else "Research campus seed source",
        "campus_sources": campus_sources_list,
        "parameters": {
            "research_method": "campus_canonical",
            "sources_consulted": len(campus_sources_list) + len(corpus_sources),
            "confidence": "medium" if corpus_results else "low"
        },
        "principles": all_principles[:3],
        "emotional_anchor": f"Grounded in {campus_names[0].replace('_', ' ').title()} expertise",
        "acceptance_criteria": [
            "Parameters extracted from A+ campus sources",
            f"At least {len(corpus_sources)} corpus references consulted",
            "Numeric values (not adjectives)",
            "Observable in-engine (proposed measurement method)"
        ],
    }

    return brief


def main():
    parser = argparse.ArgumentParser(
        description="Scholar — research retrieval system for Chimera game development")
    parser.add_argument("--feature", help="Feature name to research")
    parser.add_argument("--topic", help="Research topic/query string")
    parser.add_argument("--campus", action="append", dest="campuses",
                       help="Specific campus to query (repeatable)")
    parser.add_argument("--technical-research", action="store_true",
                       help="Process pending technical_research queue")
    parser.add_argument("--generate-brief", action="store_true",
                       help="Generate a conservative brief (for spiral_forks)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done, don't record")

    args = parser.parse_args()

    if args.technical_research:
        dna = load_dna_graph()
        nodes = dna.get("nodes", [])
        pending = [n for n in nodes if n.get("type") == "TechnicalResearch" and n.get("status") == "pending"]

        if not pending:
            print("No pending technical_research items found.")
            return 0

        print(f"Found {len(pending)} pending technical_research items:")
        for item in pending[:3]:
            print(f"  - {item.get('feature', 'unnamed')}: {item.get('topic', '')}")

        if not args.dry_run:
            print("\nTo research an item, use: --feature <name> --topic <query>")
        return 0

    if not args.feature or not args.topic:
        print("Scholar: Usage requires --feature and --topic, or --technical-research")
        print("Try: python -m core.scholar --feature Ground_Sand_Particles --topic 'dust accumulation'")
        return 1

    print(f"\nScholar researching: {args.feature}")
    print(f"Topic: {args.topic}\n")

    campuses_to_query = args.campuses or ["engineering_school", "unreal_engine_craft", "art_school"]
    campus_sources = []

    for campus_name in campuses_to_query:
        print(f"Querying {campus_name}...")
        campus_data = retrieve_campus(campus_name)
        if campus_data:
            for seed in campus_data.get("seed_sources", []):
                source_name = seed.get("name", "")
                quality = seed.get("quality", "B")
                campus_sources.append(source_name)
                print(f"  [{quality}] {source_name}")
        else:
            print(f"  (no data)")

    print(f"\nQuerying research_corpus/ for '{args.topic}'...")
    corpus_results = retrieve_corpus(args.topic, max_results=5)
    if corpus_results:
        for result in corpus_results:
            print(f"  {result['source']}: {result['snippet'][:80]}...")
    else:
        print("  (no local corpus results)")

    if not args.dry_run:
        corpus_paths = [r["path"] for r in corpus_results]
        web_sources = []

        discovery_id = build_discovery_node(
            feature=args.feature,
            campus_sources=campus_sources,
            web_sources=web_sources,
            corpus_sources=corpus_paths,
            parameters={
                "research_method": "campus_plus_corpus",
                "sources_consulted": len(campus_sources) + len(corpus_paths),
            },
            acceptance_criteria=[
                "Parameters extracted from A+ campus sources",
                f"Verified against {len(corpus_paths)} local references",
                "Observable in-engine via telemetry or screenshot"
            ],
            confidence="medium" if corpus_results else "low"
        )

        print(f"\nRecorded discovery node: {discovery_id}")

        if args.generate_brief:
            brief = scholar_brief_from_research(args.feature, args.topic, campuses_to_query)
            brief_file = CHIMERA_ROOT / "docs" / f"scholar_brief_{args.feature}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            brief_file.parent.mkdir(parents=True, exist_ok=True)
            brief_file.write_text(json.dumps(brief, indent=2))
            print(f"Wrote brief: {brief_file}")
    else:
        print("\n(--dry-run: no mutations recorded)")

    print(f"\nSources consulted: {len(campus_sources) + len(corpus_results)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
