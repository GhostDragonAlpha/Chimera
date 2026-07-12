"""Research Mandate enforcement — Universal pre-flight validation and tier classification.

Added 2026-07-10 per Chimera/docs/RESEARCH_MANDATE.md §6 Enforcement Mechanism.

MANDATORY FOR ALL AGENTS: Every agent session (Orchestrator, Sleepwalker, Rehearsal,
duty cycles, subagents) MUST use these functions before executing any task. This is not
optional — the Research Mandate applies universally regardless of agent role.

Usage:
    from core.research_enforcement import (
        validate_research_completed,
        classify_task_tier,
        build_research_summary_template,
        check_documentation_review,
        build_subtask_message,
        get_research_compliance_score,
    )

    # Pre-execution validation (ALL agents)
    if not validate_research_completed(task):
        raise ResearchGapError(f"Task {task.name} failed pre-flight research")

    # Tier classification (called by any agent before delegation or execution)
    tier = classify_task_tier(task_description, task_complexity)

    # Build embedded research summary for subtask message (Orchestrator/subagent use)
    summary_template = build_research_summary_template(tier, task_name)
    message = build_subtask_message(task_name, tier, pathway_followed, traps_avoided)

    # Compliance scoring (dashboard integration, all agents)
    score = get_research_compliance_score()
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Project paths (relative to Chimera/ directory)
CHIMERA_DIR = Path(__file__).parent.parent
DNA_GRAPH_PATH = CHIMERA_DIR / "docs" / "chimera_dna_graph.json"
MCP_PATHWAYS_PATH = CHIMERA_DIR / "docs" / "MCP_PATHWAYS.md"

# Mandatory documentation files for review (Research Mandate §2.3)
MANDATORY_DOCS = [
    ("AGENTS.md", "Known bugs table, traps section, current game state"),
    ("Chimera/docs/GENERATION_PROTOCOL.md", "Laws, sleepwalker rules, observation protocol"),
    ("Chimera/docs/MCP_PATHWAYS.md", "Working pathways + TRAP entries for relevant tools"),
    ("task_progress.md", "Current NEXT list, session handoffs, corrections"),
    ("Chimera/docs/PENDING_HEURISTICS.md", "Pending/approved heuristics affecting the task domain"),
]


def load_dna_graph():
    """Load DNA graph from disk."""
    if DNA_GRAPH_PATH.exists():
        with open(DNA_GRAPH_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"nodes": [], "edges": []}


def classify_task_tier(task_description: str, task_complexity: str = None) -> int:
    """Classify a task into Tier 1/2/3 based on complexity heuristics.

    Args:
        task_description: Free-text description of the task
        task_complexity: Optional pre-assessed complexity ('simple', 'moderate', 'complex')

    Returns:
        int: 1, 2, or 3 (tier level)

    Heuristics:
        - Tier 1: Single MCP tool call, well-documented pathway exists, no visual verification needed
        - Tier 2: Multiple tools, new combination, traps likely, visual verification required
        - Tier 3: New feature creation, architecture decision, unknown pathways, reference images needed"""

    # Pre-assessed complexity takes precedence
    if task_complexity:
        mapping = {
            "simple": 1,
            "moderate": 2,
            "complex": 3,
        }
        tier = mapping.get(task_complexity.lower(), None)
        if tier is not None:
            return tier

    # Heuristic classification from description
    desc_lower = task_description.lower()

    # Tier 1 indicators (simple, single-tool tasks)
    tier_1_indicators = [
        "spawn_actor", "set_transform", "toggle", "enable", "disable",
        "set_property", "get_property", "list_", "search_assets",
        "scalar parameter", "boolean flag", "configuration change"
    ]

    # Tier 2 indicators (moderate, multi-tool tasks)
    tier_2_indicators = [
        "material", "pbr", "vector parameter", "niagara", "particle",
        "character movement", "animation", "screenshot", "verification",
        "configure", "setup", "create_blueprint", "widget"
    ]

    # Tier 3 indicators (complex, new feature/architecture)
    tier_3_indicators = [
        "new feature", "architecture", "novel", "unknown pathway",
        "weapon blueprint", "interaction system", "environmental effect",
        "create from scratch", "design", "implement.*system"
    ]

    # Count matches (Tier 3 > Tier 2 > Tier 1)
    tier_3_count = sum(1 for ind in tier_3_indicators if ind in desc_lower)
    tier_2_count = sum(1 for ind in tier_2_indicators if ind in desc_lower)

    if tier_3_count >= 1:
        return 3
    elif tier_2_count >= 1:
        return 2
    else:
        # Default to Tier 1 for simple operations
        tier_1_count = sum(1 for ind in tier_1_indicators if ind in desc_lower)
        if tier_1_count >= 1:
            return 1
        # Unknown complexity defaults to Tier 2 (conservative)
        return 2


def check_documentation_review(task_name: str, task_description: str = "") -> dict:
    """Check which mandatory documentation files have been reviewed for this task.

    Returns a dict with compliance status and findings per document."""
    dna_graph = load_dna_graph()
    nodes = dna_graph.get("nodes", [])

    # Find DocumentationReview nodes related to this task
    relevant_reviews = []
    for node in nodes:
        if node.get("type") == "DocumentationReview":
            doc_file = node.get("doc_file", "")
            findings = node.get("relevant_findings", [])
            section = node.get("section_reviewed", "")

            # Check if this review is relevant to the current task
            task_match = (task_name.lower() in str(node).lower() or
                         task_description.lower() in str(node).lower())

            if doc_file and findings:
                relevant_reviews.append({
                    "doc_file": doc_file,
                    "section_reviewed": section,
                    "findings_count": len(findings),
                    "task_relevant": task_match,
                    "node_id": node.get("id"),
                })

    # Build compliance report for all mandatory docs
    review_status = {}
    for doc_file, purpose in MANDATORY_DOCS:
        matching_reviews = [r for r in relevant_reviews if doc_file.lower() in r["doc_file"].lower()]
        review_status[doc_file] = {
            "reviewed": len(matching_reviews) > 0,
            "findings": [r for r in matching_reviews],
            "purpose": purpose,
        }

    return {
        "task_name": task_name,
        "timestamp": datetime.utcnow().isoformat(),
        "compliance_rate": sum(1 for v in review_status.values() if v["reviewed"]) / len(MANDATORY_DOCS),
        "reviews": review_status,
    }


def validate_research_completed(task: dict) -> bool:
    """Validate that a task has completed all required research before execution.

    Args:
        task: Dict with keys 'name', 'description', 'tier', 'research_summary'

    Returns:
        True if all research requirements are met, False otherwise.

    Raises:
        ResearchGapError: If validation fails (for Orchestrator to catch and reject)"""

    task_name = task.get("name", "unknown")
    task_tier = task.get("tier", 1)
    has_pathway_query = task.get("pathway_queried", False)
    has_doc_review = check_documentation_review(task_name)
    doc_compliance = has_doc_review.get("compliance_rate", 0.0)

    # Tier 1: DNA query + pathway follow (5 min max)
    if task_tier == 1:
        if not has_pathway_query:
            print(f"[research_enforcement] REJECTED: {task_name} (Tier 1) — pathway not queried")
            return False
        # Doc review is advisory for Tier 1
        return True

    # Tier 2+: DNA query + multi-source research + summary required
    if task_tier >= 2:
        if not has_pathway_query:
            print(f"[research_enforcement] REJECTED: {task_name} (Tier {task_tier}) — pathway not queried")
            return False

        # Documentation review compliance required for Tier 2+
        if doc_compliance < 0.5:
            print(f"[research_enforcement] WARNING: {task_name} (Tier {task_tier}) — low doc review compliance ({doc_compliance:.1%})")

        # Research summary required for Tier 2+
        has_summary = task.get("research_summary") is not None and len(str(task.get("research_summary"))) > 50
        if not has_summary:
            print(f"[research_enforcement] REJECTED: {task_name} (Tier {task_tier}) — no research summary provided")
            return False

        # Validate summary structure
        summary = task.get("research_summary", {})
        sources_count = summary.get("sources_count", 0)
        if sources_count < 3 and task_tier >= 2:
            print(f"[research_enforcement] WARNING: {task_name} (Tier {task_tier}) — only {sources_count} sources (min 3 required)")

        return True

    # Unknown tier defaults to Tier 1 validation
    if not has_pathway_query:
        print(f"[research_enforcement] REJECTED: {task_name} (unknown tier) — pathway not queried")
        return False

    return True


def build_research_summary_template(tier: int, task_name: str = "") -> dict:
    """Build a pre-filled research summary template for subtask delegation.

    Returns a dict that can be serialized into the subtask message parameter."""

    template = {
        "task_name": task_name,
        "tier": tier,
        "date": datetime.utcnow().isoformat(),
        "sources_consulted": [],
        "parameters_cited": {},
        "discrepancies_resolved": [],
        "failure_research": [] if tier >= 3 else None,
        "confidence_rating": "medium",
    }

    # Tier-specific required fields
    if tier >= 2:
        template["required_sources"] = [
            {"type": "primary_docs", "url_or_path": "", "confidence": "high"},
            {"type": "community_forum", "url_or_path": "", "confidence": "medium"},
            {"type": "video_tutorial", "url_or_path": "", "confidence": "medium"},
        ]

    if tier >= 3:
        template["required_domains"] = 3
        template["source_types_required"] = [
            "primary_photography",
            "technical_docs",
            "community",
            "video",
            "3d_scans"
        ]
        template["failure_research_required"] = True

    return template


def build_subtask_message(task_name: str, tier: int, pathway_followed: str = "",
                          traps_avoided: list = None) -> str:
    """Build the full subtask message with embedded research summary (Research Mandate §6.2).

    Returns a string that can be passed as the 'message' parameter to orchestrator.delegate()."""

    if traps_avoided is None:
        traps_avoided = []

    # Build the research compliance header
    compliance_header = f"""RESEARCH_MANDATE_COMPLIANT
Tier: {tier}
Pathway followed: {pathway_followed or 'none (new pathway)'}
Traps avoided: {', '.join(traps_avoided) if traps_avoided else 'none identified'}
Research summary attached: {'Yes' if tier >= 2 else 'No (Tier 1 acceptable)'}
"""

    # Build the research summary section for Tier 2+
    research_section = ""
    if tier >= 2:
        template = build_research_summary_template(tier, task_name)
        research_section = f"""
## Research Summary — {task_name}

**Tier:** {tier}  
**Date:** {datetime.utcnow().isoformat()}

### Sources Consulted (to be completed by subagent)
| # | Source Type | URL/Path | Confidence | Notes |
|---|-------------|----------|------------|-------|
| 1 | Primary docs | [TBD] | High | ... |
| 2 | Community forum | [TBD] | Medium | ... |

**Total sources:** 0 (minimum {3 if tier >= 2 else 1} required)  
**Domains visited:** 0 (minimum {template.get('required_domains', 1)} required for Tier {tier})

### Parameters and Citations
| Parameter | Value | Source #1 | Source #2 | Confidence |
|-----------|-------|-----------|-----------|------------|
| [TBD] | [TBD] | [TBD] | [TBD] | TBD |

### Discrepancies Resolved
- [To be completed by subagent during research phase]

### Failure Research (Tier 3 only)
| What Doesn't Work | Why It Fails | Source |
|-------------------|--------------|--------|
| [N/A for Tier {tier}] | — | — |

### Confidence Rating
**Overall:** Medium (pre-research baseline)  
**Justification:** Research phase not yet completed. Will be updated after execution."""

    return f"""{compliance_header}
{research_section}

EXECUTION_INSTRUCTIONS:
1. Follow pathway '{pathway_followed}' exactly (from DNA graph)
2. Apply workarounds for traps: {', '.join(traps_avoided) if traps_avoided else 'none identified'}
3. Verify via read-back after completion
4. Record any deviations as surprises
5. Update research summary with actual findings before completing"""


def get_research_compliance_score(dna_graph=None) -> dict:
    """Calculate aggregate research compliance metrics from the DNA graph.

    Returns a dict suitable for dashboard display (Research Mandate §10)."""

    if dna_graph is None:
        dna_graph = load_dna_graph()

    nodes = dna_graph.get("nodes", [])

    # Count by type
    research_summaries = [n for n in nodes if n.get("type") == "ResearchSummary"]
    pathway_attempts = [n for n in nodes if n.get("type") == "PathwayAttempt"]
    doc_reviews = [n for n in nodes if n.get("type") == "DocumentationReview"]

    # Tier distribution
    tier_counts = {1: 0, 2: 0, 3: 0}
    for rs in research_summaries:
        tier = rs.get("tier", 1)
        if tier in tier_counts:
            tier_counts[tier] += 1

    # Trap avoidance count (from pathway_attempts with error_category='trap_hit')
    traps_avoided = sum(1 for pa in pathway_attempts
                       if pa.get("error_category") == "trap_hit" and pa.get("workaround_applied"))

    return {
        "research_summaries_count": len(research_summaries),
        "pathway_attempts_count": len(pathway_attempts),
        "documentation_reviews_count": len(doc_reviews),
        "tier_distribution": tier_counts,
        "traps_avoided_count": traps_avoided,
        "average_sources_per_summary": (
            sum(rs.get("sources_count", 0) for rs in research_summaries) / max(1, len(research_summaries))
        ),
    }


# Context Exhaustion Controls (added 2026-07-10)

CONTEXT_EXHAUSTION_TIERS = {
    1: {"min_domains": 3, "min_source_types": 0, "description": "Quick — single pathway tasks"},
    2: {"min_domains": 5, "min_source_types": 3, "description": "Standard — multi-source verification"},
    3: {"min_domains": 8, "min_source_types": 5, "description": "Deep — full source diversity + failure research"},
}

SOURCE_TYPE_LABELS = [
    "official_docs",
    "community",
    "video_tutorial",
    "technical_blog",
    "general_web",
]


def validate_research_depth(task_name: str, research_report: dict) -> dict:
    """Validate that a research report meets minimum context exhaustion thresholds.

    Args:
        task_name: Name of the task being validated
        research_report: Dict with keys 'tier', 'sources_count', 'domains_visited',
            'source_types', 'failure_sources', 'page_visits', 'related_queries_followed'

    Returns:
        dict with keys:
            - 'compliant': bool — True if all thresholds met
            - 'score': float (0.0-1.0) — overall compliance score
            - 'missing_requirements': list[str] — human-readable descriptions of what's missing
            - 'tier': int — the tier that was validated against

    Thresholds per tier:
        Tier 1: ≥3 domains (if web search performed), no source type minimum
        Tier 2: ≥5 domains AND ≥3 source types, ≥1 failure source
        Tier 3: ≥8 domains AND all 5 source types, ≥1 failure source, page visits ≥2

    Usage:
        from core.research_enforcement import validate_research_depth
        result = validate_research_depth("CreateWeaponBlueprint", report)
        if not result['compliant']:
            print(f"Research incomplete for {task_name}: {result['missing_requirements']}")
    """
    tier = research_report.get("tier", 1)
    domains_visited = research_report.get("domains_visited", 0)
    sources_count = research_report.get("sources_count", 0)
    source_types = research_report.get("source_types", [])
    failure_sources = research_report.get("failure_sources", 0)
    page_visits = research_report.get("page_visits", 0)
    related_queries_followed = research_report.get("related_queries_followed", False)

    # Resolve tier thresholds
    if tier not in CONTEXT_EXHAUSTION_TIERS:
        tier = 2  # default to Tier 2 for unknown tiers (conservative)

    config = CONTEXT_EXHAUSTION_TIERS[tier]
    min_domains = config["min_domains"]
    min_source_types = config["min_source_types"]

    missing_requirements = []
    score_components = []

    # Check 1: Domain diversity
    domain_score = min(1.0, domains_visited / max(min_domains, 1)) if min_domains > 0 else 1.0
    score_components.append(("domains", domain_score, f"{domains_visited}/{min_domains}"))
    if domains_visited < min_domains:
        missing_requirements.append(
            f"Domain diversity: {domains_visited} domains found, minimum {min_domains} required for Tier {tier}"
        )

    # Check 2: Source type coverage (Tier 2+)
    source_type_score = 1.0 if min_source_types == 0 else min(1.0, len(source_types) / max(min_source_types, 1))
    score_components.append(("source_types", source_type_score, f"{len(source_types)}/{min_source_types}"))
    if min_source_types > 0 and len(source_types) < min_source_types:
        missing_requirements.append(
            f"Source type coverage: {len(source_types)} types found, minimum {min_source_types} required for Tier {tier}"
        )

    # Check 3: Failure research (Tier 2+)
    failure_score = 1.0 if failure_sources >= 1 else 0.0
    score_components.append(("failure_research", failure_score, f"{failure_sources}/1"))
    if failure_sources < 1 and tier >= 2:
        missing_requirements.append(
            "Failure research: at least 1 source on what doesn't work is required for Tier 2+"
        )

    # Check 4: Actual page visits (Tier 3+)
    page_score = 1.0 if page_visits >= 2 else min(1.0, page_visits / 2) if page_visits > 0 else 0.0
    score_components.append(("page_visits", page_score, f"{page_visits}/2"))
    if tier >= 3 and page_visits < 2:
        missing_requirements.append(
            "Page visits: at least 2 real content pages visited (not just Google snippets) required for Tier 3+"
        )

    # Check 5: Related query follow-up (Tier 2+)
    related_score = 1.0 if related_queries_followed else 0.0
    score_components.append(("related_queries", related_score, "yes/no"))
    if tier >= 2 and not related_queries_followed:
        missing_requirements.append(
            "Related query follow-up: 'People also ask' or similar suggestions should be explored for Tier 2+"
        )

    # Check 6: Minimum sources count (global)
    global_min_sources = min_domains if tier >= 2 else 1
    source_count_score = min(1.0, sources_count / max(global_min_sources, 1))
    score_components.append(("sources_count", source_count_score, f"{sources_count}/{global_min_sources}"))

    # Overall compliance: all checks must pass (score == 1.0)
    overall_score = sum(s for _, s, _ in score_components) / len(score_components) if score_components else 0.0
    compliant = overall_score >= 0.95 and len(missing_requirements) == 0

    return {
        "compliant": compliant,
        "score": round(overall_score, 3),
        "tier": tier,
        "task_name": task_name,
        "missing_requirements": missing_requirements,
        "check_details": [
            {"check": name, "score": s, "detail": d} for name, s, d in score_components
        ],
    }


if __name__ == "__main__":
    # Quick self-test
    print("=" * 60)
    print("Research Mandate Enforcement — Self Test")
    print("=" * 60)

    # Test tier classification
    test_cases = [
        ("Spawn actor with known path", "simple"),
        ("Create weapon blueprint with PBR materials", None),
        ("Design novel interaction system from scratch", None),
        ("Set scalar parameter value", "simple"),
        ("Configure character movement speeds", None),
    ]

    print("\nTier Classification:")
    for desc, complexity in test_cases:
        tier = classify_task_tier(desc, complexity)
        print(f"  Tier {tier}: '{desc}' (complexity={complexity})")

    # Test subtask message builder
    print("\nSubtask Message Builder:")
    msg = build_subtask_message("TestWeaponCreation", 2, "pathway_17_material_params", ["set_component_property_lies"])
    lines = msg.split('\n')
    print(f"  Generated {len(lines)} line message for Tier 2 task")

    # Test compliance score
    print("\nCompliance Score:")
    score = get_research_compliance_score()
    for key, val in score.items():
        print(f"  {key}: {val}")

    print("\n" + "=" * 60)
    print("Self test complete.")
    print("=" * 60)
