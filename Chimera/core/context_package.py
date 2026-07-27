"""Context Package assembler (AGENTS.md ~146-153; CHIMERA_AGENT_BRIEF.md ~511-578;
ORCHESTRATOR_PROMPT.md ~15-24).

CHIMERA_AGENT_BRIEF.md documents the Context Package as human-mediated today (a human
writes subagent_prompts/{feature}_context.md by hand and pastes it into a new agent
window) with its own note: "Future automation: the Orchestrator will write the prompt
file... programmatically." This module is that automation. It merges the 5 fields by
calling ONLY existing query primitives -- it does not reinvent pathway/pattern/mutation
querying or campus lookup:

  1. dsl_block         -> graphify_query("feature", name)  [graphify_interface.py]
     Note: the .chimera DSL grammar has no per-feature "Feature: X { ... }" block syntax
     today (verified: zero matches in tests/dsl_grammar/*.chimera) -- the FeatureUpdate
     node in the DNA graph is the real per-feature source of truth, so this field is
     synthesized from that node instead of a DSL block that doesn't exist.
  2. graph_context      -> graphify_query("pathway"/"mutation"/"pattern", ...)
  3. campus_sources     -> core.scholar.retrieve_campus(...)
  4. reference_images   -> best-effort from the feature's study_guide; NO live lookup
                           primitive exists anywhere in this codebase today (honest gap,
                           not faked)
  5. required_endpoints -> ralph_loop_harness.MCPPathways().find(feature_type)

No MCPStdioClient / live editor connection required -- every field reads the DNA graph
(docs/chimera_dna_graph.json) or static docs. Safe to call with no Unreal Editor running.

NOTE: importing core.ralph_loop_harness (for MCPPathways / FEATURE_TO_SCHOOL /
_detect_feature_type) runs that module's _setup_logging() once per process, creating one
timestamped file under Chimera's log directory. This is a pre-existing cost
core/spiral_forks.py already accepts today (it imports HARNESS_CONFIG from the same
module) -- not new here.

Usage:
    python -m core.context_package --feature Ground_Sand_Footprints --json
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

try:
    from core.graphify_interface import graphify_query
    from core.scholar import retrieve_campus
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from graphify_interface import graphify_query
    from scholar import retrieve_campus

# graphify_query("pattern", ...) only recognizes these 4 keys (falls back to AActor/
# UActorComponent for other A*/U* names, else raises ValueError) -- verified at
# graphify_interface.py:212-250. Hint substrings are matched against the feature NAME.
_PATTERN_KEY_HINTS = {
    "UActorComponent": ("component", "_system", "_trade", "_inventory"),
    "AGameModeBase": ("gamemode",),
    "UGameInstance": ("gameinstance",),
}


def _guess_pattern_key(feature_name: str) -> str:
    name_lower = feature_name.lower()
    for key, hints in _PATTERN_KEY_HINTS.items():
        if any(h in name_lower for h in hints):
            return key
    return "AActor"


def _feature_type_and_endpoints(feature_name: str):
    """Feature-type detection + MCP_PATHWAYS.md lookup live only on
    ralph_loop_harness.py today (RalphLoopHarness._detect_feature_type is a @staticmethod,
    callable with no instantiation; MCPPathways does its own file parsing, no MCP
    connection). Reused directly rather than re-derived."""
    from core.ralph_loop_harness import RalphLoopHarness, MCPPathways
    feature_type = RalphLoopHarness._detect_feature_type(feature_name)
    endpoints = MCPPathways().find(feature_type)
    return feature_type, endpoints


def _schools_for_type(feature_type: str) -> List[str]:
    """Reuses ralph_loop_harness.FEATURE_TO_SCHOOL -- the only existing feature-type ->
    campus mapping -- with the same safe fallback the harness itself uses
    (ralph_loop_harness.py:913: .get(feature_type, FEATURE_TO_SCHOOL.get("Model", }]}))."""
    from core.ralph_loop_harness import FEATURE_TO_SCHOOL
    return FEATURE_TO_SCHOOL.get(feature_type, FEATURE_TO_SCHOOL.get("Model", []))


def assemble_context_package(feature_name: str, campus_names: Optional[List[str]] = None) -> dict:
    """Merge the 5 Context Package fields for one feature. Never raises -- every
    sub-query is best-effort and degrades to an empty value + a note."""
    package = {"feature_name": feature_name, "generated_by": "core.context_package"}

    # 1. DSL block -- synthesized from the FeatureUpdate node (see module docstring for
    # why: no per-feature block exists in the .chimera DSL grammar today).
    try:
        matches = graphify_query("feature", feature_name)
    except Exception as exc:
        matches = [{"error": str(exc)}]
    feature_node = None
    if isinstance(matches, list):
        for m in matches:
            if m.get("feature_name") == feature_name:
                feature_node = m
                break
    package["dsl_block"] = {
        "source": "FeatureUpdate node (graphify_query('feature', ...)) -- no per-feature "
                   "block exists in the .chimera DSL grammar today",
        "loop": feature_node.get("loop") if feature_node else None,
        "status": feature_node.get("status") if feature_node else "not_found",
        "parameters": feature_node.get("parameters", {}) if feature_node else {},
        "study_guide": feature_node.get("study_guide", {}) if feature_node else {},
    }

    # 2. Graph context: pathways + mutations + patterns
    try:
        feature_type, endpoints = _feature_type_and_endpoints(feature_name)
    except Exception as exc:
        feature_type, endpoints = "Model", [{"error": str(exc)}]
    pattern_key = _guess_pattern_key(feature_name)
    try:
        pattern_data = graphify_query("pattern", pattern_key)
    except ValueError:
        pattern_data = {}
    try:
        prior_pathways = graphify_query("pathway", feature_name)
    except Exception as exc:
        prior_pathways = [{"error": str(exc)}]
    try:
        prior_mutations = graphify_query("mutation", feature_name)
    except Exception as exc:
        prior_mutations = [{"error": str(exc)}]
    package["graph_context"] = {
        "feature_type": feature_type,
        "prior_pathway_attempts": prior_pathways,
        "prior_mutations": prior_mutations,
        "code_pattern": {"pattern_key": pattern_key, **pattern_data},
    }

    # 3. Campus sources -- reuse scholar.retrieve_campus() (itself a thin wrapper over
    # graphify_query("campus", ...)); same FEATURE_TO_SCHOOL-style mapping
    # ralph_loop_harness.research_feature() already uses.
    schools = campus_names or _schools_for_type(feature_type)
    campuses = {}
    for school in schools:
        try:
            campuses[school] = retrieve_campus(school)
        except ValueError as exc:
            campuses[school] = {"error": str(exc)}
    package["campus_sources"] = campuses

    # 4. Reference images -- NO live lookup primitive exists anywhere in the codebase
    # today. Best-effort from the feature's own study_guide; say so honestly.
    study_guide = package["dsl_block"]["study_guide"]
    package["reference_images"] = {
        "canonical_reference": study_guide.get("canonical_reference", ""),
        "status": "from_study_guide" if study_guide else "no_lookup_primitive_exists",
    }

    # 5. Required endpoints -- MCP_PATHWAYS.md hints for this feature's type
    package["required_endpoints"] = endpoints
    return package


def main() -> int:
    parser = argparse.ArgumentParser(description="Assemble a Context Package for one feature")
    parser.add_argument("--feature", required=True)
    parser.add_argument("--campus", action="append", dest="campuses")
    parser.add_argument("--json", action="store_true", help="machine-readable output (for the .js workflow bridge)")
    args = parser.parse_args()
    package = assemble_context_package(args.feature, campus_names=args.campuses)
    if args.json:
        print(json.dumps(package, indent=2, default=str))
    else:
        print(f"Context Package: {args.feature}  (type={package['graph_context']['feature_type']})")
        print(json.dumps(package, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
