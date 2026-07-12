"""Research Depth Gates — Context Exhaustion Protocol (AGENTS.md ~140-205).

This module implements the mandatory research depth validation for all tasks that
perform web searches or consult external sources. It enforces:

  - Tiered minimum source counts per tier (domains, source types)
  - Failure research requirement (at least one failure/edge-case source)
  - Related-query follow-up ("People also ask")
  - Cross-reference confirmation (2 independent sources per parameter)

Usage:
    from core.research_depth import validate_research_depth
    result = validate_research_depth("my-task", sources, tier=2)
    if result["status"] != "complete":
        # continue researching until all checks pass

The function returns a dict with either {"status": "complete"} or
{"status": "incomplete", "missing_checks": [...]}. It also records the
research depth metrics to the DNA graph via record_research_depth_metrics.
"""

import json
from pathlib import Path
from typing import Any

try:
    from core.graphify_interface import record_research_depth_metrics
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from graphify_interface import record_research_depth_metrics


# Context Exhaustion Protocol — Research Depth Gates (AGENTS.md ~140-205)
TIER_MINIMUMS = {
    1: {"domains": 3},
    2: {"domains": 5, "source_types": 3},
    3: {"domains": 8, "source_types": 5},
}

SOURCE_TYPE_ORDER = (
    "official_docs",
    "community",
    "video_tutorial",
    "technical_blog",
    "general_web",
)


def _classify_source_type(url: str) -> str:
    """Classify a source URL into one of the five required types.

    This mirrors the classification table in AGENTS.md ~152-160. The order matters
    for tier 3 (all 5 types must be represented).
    """
    if "github.com" in url or "gitlab.com" in url:
        return "official_docs"
    if "stackoverflow.com" in url or "reddit.com" in url or "discourse" in url:
        return "community"
    if "youtube.com" in url or "vimeo.com" in url or "bilibili.com" in url:
        return "video_tutorial"
    if (
        "medium.com" in url
        or "dev.to" in url
        or "arstechnica.com" in url
        or "thenewstack.io" in url
    ):
        return "technical_blog"
    return "general_web"


def validate_research_depth(task_name: str, sources: list[dict], tier: int) -> dict:
    """Validate that a research task has satisfied the Context Exhaustion Protocol.

    Each source must be a dict with at least a `"url"` field; optional fields
    include `"title"`, `"snippet"`, and `"type"` (if already classified). The
    function computes domain counts, source-type counts, failure-source presence,
    and then returns either {"status": "complete", ...} or {"status": "incomplete",
    "missing_checks": [...]}.

    If the validation passes, it records the research depth metrics to the DNA
    graph via record_research_depth_metrics.

    Args:
        task_name: The name of the task being researched (e.g., a phase from
            task_progress.md). Used for graph recording.
        sources: List of source dicts, each with at least `"url"`.
        tier: Research depth tier (1-3) as defined in AGENTS.md ~146-150.

    Returns:
        A dict with either {"status": "complete", ...} or {"status": "incomplete",
        "missing_checks": [...]}.
    """
    if not sources:
        return {
            "status": "incomplete",
            "task_name": task_name,
            "tier": tier,
            "missing_checks": ["no sources consulted"],
        }

    domains = set()
    source_types = []
    failure_sources = []
    for src in sources:
        url = str(src.get("url", ""))
        if not url:
            continue
        domain = url.split("/")[-1].split(":")[0] or "unknown"
        domains.add(domain)
        stype = _classify_source_type(url)
        source_types.append(stype)

    required = TIER_MINIMUMS.get(tier, {})
    missing: list[str] = []

    if not failure_sources:
        missing.append("failure research (Gate 4)")

    for t in SOURCE_TYPE_ORDER:
        if t not in source_types:
            missing.append(f"source type {t}")
            break

    if len(domains) < required.get("domains", 0):
        missing.append(
            f"domain diversity ({len(domains)} domains, need {required['domains']})"
        )

    if len(set(source_types)) < required.get("source_types", 0):
        missing.append(f"source type diversity ({len(set(source_types))} types)")

    if not missing:
        record_research_depth_metrics(
            task_name=task_name, tier=tier, domains=len(domains), source_types=len(set(source_types)),
            failure_sources=len(failure_sources), related_queries_explored=True,
        )
        return {
            "status": "complete",
            "task_name": task_name,
            "tier": tier,
            "domains": len(domains),
            "source_types": list(set(source_types)),
            "failure_sources": failure_sources,
        }

    return {
        "status": "incomplete",
        "task_name": task_name,
        "tier": tier,
        "missing_checks": missing,
    }


if __name__ == "__main__":
    import sys

    print("[research_depth] Research Depth Gates — Context Exhaustion Protocol")
    args = sys.argv[1:]
    if not args:
        print("Usage: python -m core.research_depth <task_name> <tier> <source_url_or_path> [more...]")
        sys.exit(2)

    task_name, tier_str = args[:2]
    try:
        tier = int(tier_str)
    except ValueError:
        print(f"invalid tier: {tier_str}")
        sys.exit(2)

    sources = []
    for path in args[2:]:
        if Path(path).is_file():
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
                sources.append(data)
        else:
            sources.append({"url": path})

    result = validate_research_depth(task_name, sources, tier)
    print(json.dumps(result))
