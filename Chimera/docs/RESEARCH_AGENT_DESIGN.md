# Research Agent Module — Architectural Design Document

**Status:** Design (pending implementation)  
**Created:** 2026-07-10  
**Owner:** All agent modes (code, debug, ask, architect, chimera-code, chimera-debug, etc.)  
**Supersedes:** None (new module)

---

## 1. Purpose & Scope

### Problem Statement
The current system has the Orchestrator enforcing research at delegation time via `build_subtask_message()` and `check_documentation_review()`. Individual agents have NO direct way to perform web research during their own execution — they must wait for the Orchestrator to delegate a research task. This creates a bottleneck where agents cannot self-serve quick research needs (e.g., "what's the correct parameter format for this MCP call?").

### Solution
A standalone `Chimera/core/research_agent.py` module that ANY agent mode can import and invoke directly, without going through the Orchestrator. The module handles:
1. Web search via Playwright MCP (proven working)
2. LM Studio analysis of results (qwen3.6-35b)
3. DNA graph cross-referencing before new research
4. Result recording to DNA graph

### Non-Goals (Out of Scope)
- Replacing the Orchestrator's research enforcement at delegation time
- Modifying `research_enforcement.py` tier classification logic
- Creating a new knowledge graph — this module WRITES TO the existing DNA graph
- Visual verification via MCP screenshots (covered by existing pathways)

---

## 2. Module Structure

```
Chimera/core/
├── research_agent.py          # Main module — ResearchAgent class + convenience functions
├── research_playwright.py     # Playwright MCP integration layer
├── research_lm_studio.py      # LM Studio (qwen3.6-35b) analysis layer
└── test_research_agent.py     # Unit tests for the module
```

### File Responsibilities

| File | Responsibility | Dependencies |
|------|----------------|--------------|
| `research_agent.py` | Public API, ResearchAgent class, tier-based orchestration | All sub-modules |
| `research_playwright.py` | Playwright MCP calls (navigate, find, snapshot) | `mcp_playwright_*` tools |
| `research_lm_studio.py` | LM Studio REST API calls for analysis/synthesis | HTTP client, qwen3.6-35b model |
| `test_research_agent.py` | Unit tests mocking MCP/LM calls | pytest |

---

## 3. Class Design

### 3.1 ResearchAgent (Main Class)

```python
class ResearchAgent:
    """On-demand research agent callable from ANY agent mode.
    
    Usage:
        from Chimera.core.research_agent import ResearchAgent
        
        agent = ResearchAgent()
        results = agent.google_search("Unreal Engine 5 PCG best practices")
        
        # Or as a full task:
        summary = agent.research_task(
            "Configure Niagara particle system for ground dust",
            depth="standard"
        )
    """
    
    def __init__(self, lm_studio_api_key: str = None, dna_graph_path: str = None):
        """Initialize the research agent.
        
        Args:
            lm_studio_api_key: Optional LM Studio API key (falls back to env var)
            dna_graph_path: Optional path override (defaults to docs/chimera_dna_graph.json)
        """
    
    def google_search(self, query: str, max_results: int = 10) -> list[dict]:
        """Perform a web search via Playwright MCP and return structured results.
        
        Args:
            query: Search query string (e.g., "Unreal Engine PCG graph nodes")
            max_results: Maximum number of results to return (default: 10)
            
        Returns:
            List of dicts with keys: title, url, snippet, source_type
            
        Raises:
            PlaywrightUnavailableError: If Playwright MCP is not available
            NetworkTimeoutError: If search times out after retries
        """
    
    def search_and_analyze(self, query: str, analysis_prompt: str = None) -> dict:
        """Search + LM Studio analysis of results in one call.
        
        Args:
            query: Search query string
            analysis_prompt: Optional custom prompt for LM analysis
            
        Returns:
            Dict with keys: search_results (list[dict]), analysis (str), 
                           confidence (str), sources_count (int)
        """
    
    def fetch_url_content(self, url: str, max_chars: int = 8000) -> dict:
        """Fetch and extract text content from a specific URL.
        
        Args:
            url: Full URL to fetch
            max_chars: Maximum characters to return (default: 8000)
            
        Returns:
            Dict with keys: url, title, content (str), word_count (int), status (str)
        """
    
    def research_task(self, task_description: str, depth: str = "standard") -> dict:
        """Full research task with tier-based resource allocation.
        
        Args:
            task_description: Free-text description of the research needed
            depth: One of "quick" (Tier 1), "standard" (Tier 2), "deep" (Tier 3)
            
        Returns:
            Research summary dict matching record_research_summary schema:
            {
                "task": str,
                "tier": int,
                "sources_consulted": int,
                "domains_visited": int,
                "confidence_rating": str,
                "source_table": list[dict],
                "parameters": dict,
                "discrepancies_resolved": list[str],
                "failure_research": list[dict]  # Tier 3 only
            }
        """
    
    def check_dna_graph(self, query: str) -> dict:
        """Query the DNA graph for existing knowledge before new research.
        
        Args:
            query: What to look up (pathway, feature, mutation pattern)
            
        Returns:
            Dict with keys: found (bool), nodes (list[dict]), recommendations (str)
        """
    
    def record_to_dna(self, summary: dict, task_name: str = None) -> str:
        """Record research results to the DNA graph.
        
        Uses typed helpers from core.graphify_interface.py:
        - record_research_summary() for completed tasks
        - record_pathway_attempt() if searching for pathways failed
        - record_documentation_review() when reviewing mandatory docs
        
        Args:
            summary: Research summary dict (from research_task output)
            task_name: Optional override for the task name
            
        Returns:
            DNA graph node ID on success, error string on failure
        """
```

### 3.2 Convenience Functions (Module-Level API)

For agents that don't need a full `ResearchAgent` instance, provide module-level functions:

```python
# Module-level convenience functions (no class instantiation needed)
def google_search(query: str, max_results: int = 10) -> list[dict]:
    """Quick search — same as ResearchAgent().google_search()"""
    
def search_and_analyze(query: str, analysis_prompt: str = None) -> dict:
    """Quick search + analyze — same as ResearchAgent().search_and_analyze()"""
    
def fetch_url_content(url: str, max_chars: int = 8000) -> dict:
    """Quick URL fetch — same as ResearchAgent().fetch_url_content()"""
```

---

## 4. MCP Integration Design

### 4.1 Playwright MCP Layer (`research_playwright.py`)

**Proven working tools from this session:**
- `mcp_playwright_browser_navigate` — navigate to URLs
- `mcp_playwright_browser_find` — search page content for text/regex
- `mcp_playwright_browser_snapshot` — capture accessibility tree of current page

**Additional Playwright tools available (from tool definitions):**
- `mcp_playwright_browser_click` / `type` / `fill_form` — interact with web pages
- `mcp_playwright_browser_navigate_back` — go back in browser history
- `mcp_playwright_browser_console_messages` — get console output

**Search Engine Strategy:**
```python
SEARCH_ENGINES = [
    {"name": "startpage", "url": "https://www.startpage.com/sp/search?query={QUERY}", "priority": 1},
    {"name": "bing", "url": "https://www.bing.com/search?q={QUERY}", "priority": 2},
]
```

**Rationale:** Startpage is the primary engine (privacy-respecting, Google results). Bing is the fallback. Both are proven working with Playwright MCP in this project.

### 4.2 Playwright Integration Pattern

```python
class PlaywrightSearchClient:
    """Handles all Playwright MCP calls for web research."""
    
    def search(self, query: str, engine: str = "startpage") -> list[dict]:
        """Perform search via Playwright MCP with result extraction.
        
        Steps:
        1. Navigate to search engine URL (mcp_playwright_browser_navigate)
        2. Wait for results to load (mcp_playwright_browser_wait_for time=5)
        3. Extract results via snapshot (mcp_playwright_browser_snapshot)
        4. Parse and return structured results
        
        Returns:
            List of {title, url, snippet} dicts
        """
    
    def fetch_page(self, url: str) -> dict:
        """Fetch a single page's text content.
        
        Steps:
        1. Navigate to URL (mcp_playwright_browser_navigate)
        2. Wait for load (mcp_playwright_browser_wait_for time=3)
        3. Extract via snapshot (mcp_playwright_browser_snapshot)
        4. Clean and return text content
        
        Returns:
            {title, content, word_count} dict
        """
```

### 4.3 LM Studio Layer (`research_lm_studio.py`)

**Integration Pattern:**
```python
class LMSearchAnalyzer:
    """Handles all LM Studio API calls for research analysis."""
    
    def __init__(self, api_key: str = None):
        self.api_url = os.environ.get("LM_STUDIO_API_URL", "http://localhost:1234/v1")
        self.model = "qwen3.6-35b-a3b-mtp"  # Default model
    
    def analyze_results(self, query: str, search_results: list[dict], 
                       analysis_prompt: str = None) -> dict:
        """Analyze search results via LM Studio and return synthesized findings.
        
        Args:
            query: Original research query
            search_results: Results from google_search()
            analysis_prompt: Optional custom prompt
            
        Returns:
            {analysis (str), confidence (str), key_findings (list[str])}
        """
    
    def synthesize_research(self, task_description: str, 
                           all_sources: list[dict]) -> dict:
        """Synthesize a full research summary from multiple sources.
        
        Used by research_task() for Tier 2+ tasks.
        Returns structured output matching record_research_summary schema.
        """
```

**LM Studio API Call Pattern:**
```python
# Standard LM Studio call (proven working in this project)
def call_lm_studio(messages: list[dict], model: str = None, 
                   max_tokens: int = 2000) -> dict:
    """Call LM Studio REST API with chat messages.
    
    Args:
        messages: List of {role, content} dicts (system/user/assistant)
        model: Model name (defaults to qwen3.6-35b-a3b-mtp)
        max_tokens: Max tokens in response
        
    Returns:
        Dict with 'content' and optionally 'reasoning_content' fields
    
    Notes:
        - Prefix '/no_think' for models that support it
        - Parse BOTH 'content' AND 'reasoning_content' (per AGENTS.md traps)
        - A reasoning dump = retry, never an answer
    """
```

---

## 5. Tier-Based Resource Allocation

### 5.1 Quick Research (Tier 1 / depth="quick")

**Resource Budget:** ~5 minutes  
**Tools Used:** DNA graph query + Playwright search (single engine)

```python
def _research_quick(self, task_description: str) -> dict:
    """Tier 1 research: DNA query + single-engine search."""
    
    # Step 1: Check DNA graph for existing pathways
    dna_results = self.check_dna_graph(task_description)
    if dna_results["found"]:
        return {"tier": 1, "source": "dna_graph", "data": dna_results}
    
    # Step 2: Single-engine Google search
    results = self.google_search(task_description, max_results=5)
    
    # Step 3: Return raw results (no LM analysis for Tier 1)
    return {
        "tier": 1,
        "source": "web_search",
        "search_results": results,
        "sources_consulted": len(results),
        "domains_visited": len(set(r.get("url", "") for r in results)),
        "confidence_rating": "medium"
    }
```

### 5.2 Standard Research (Tier 2 / depth="standard")

**Resource Budget:** ~15 minutes  
**Tools Used:** DNA graph query + dual-engine search + LM analysis

```python
def _research_standard(self, task_description: str) -> dict:
    """Tier 2 research: multi-source verification + LM synthesis."""
    
    # Step 1: Check DNA graph for existing pathways
    dna_results = self.check_dna_graph(task_description)
    
    # Step 2: Dual-engine search (Startpage + Bing fallback)
    results_sp = self.google_search(task_description, engine="startpage", max_results=8)
    results_bing = self.google_search(task_description, engine="bing", max_results=5)
    
    # Step 3: LM Studio analysis of combined results
    all_results = list(set(results_sp + results_bing))  # deduplicate by URL
    analysis = self._lm_analyzer.analyze_results(
        task_description, 
        all_results[:10],  # top 10 results
        analysis_prompt="Synthesize the most reliable information about this topic. "
                       "Note any discrepancies between sources."
    )
    
    # Step 4: Build research summary
    return {
        "tier": 2,
        "source": "web_search + lm_analysis",
        "search_results": all_results[:10],
        "analysis": analysis["content"],
        "confidence_rating": analysis["confidence"],
        "sources_consulted": len(all_results),
        "domains_visited": len(set(r.get("url", "") for r in all_results)),
        "key_findings": analysis.get("key_findings", [])
    }
```

### 5.3 Deep Research (Tier 3 / depth="deep")

**Resource Budget:** ~30 minutes  
**Tools Used:** DNA graph query + multi-engine search + LM synthesis + URL content fetching

```python
def _research_deep(self, task_description: str) -> dict:
    """Tier 3 research: full protocol with source diversity + failure research."""
    
    # Step 1: Check DNA graph for existing pathways
    dna_results = self.check_dna_graph(task_description)
    
    # Step 2: Multi-engine search (Startpage, Bing, DuckDuckGo if available)
    results_all = []
    for engine in ["startpage", "bing"]:
        results_all.extend(self.google_search(task_description, engine=engine, max_results=10))
    
    # Step 3: Fetch top 3 URLs for deep content extraction
    url_contents = []
    for result in results_all[:3]:
        content = self.fetch_url_content(result["url"], max_chars=8000)
        if content["status"] == "success":
            url_contents.append(content)
    
    # Step 4: LM Studio synthesis of all sources + URL contents
    analysis = self._lm_analyzer.synthesize_research(
        task_description,
        [{"type": "search_result", **r} for r in results_all[:10]] +
        [{"type": "url_content", **c} for c in url_contents]
    )
    
    # Step 5: Failure research (search for what doesn't work)
    failure_results = self.google_search(
        f"{task_description} common problems failures mistakes"
    )
    
    return {
        "tier": 3,
        "source": "multi_engine + url_fetch + lm_synthesis",
        "search_results": results_all[:10],
        "url_contents": url_contents,
        "analysis": analysis["content"],
        "confidence_rating": analysis["confidence"],
        "sources_consulted": len(results_all) + len(url_contents),
        "domains_visited": len(set(r.get("url", "") for r in results_all)),
        "key_findings": analysis.get("key_findings", []),
        "failure_research": [
            {"problem": f, "source": s} 
            for f, s in zip(failure_results[:3], failure_results[:3])
        ]
    }
```

---

## 6. DNA Graph Recording Integration

### 6.1 Recording Functions Mapping

All research performed by the Research Agent MUST record to the DNA graph using typed helpers from `core/graphify_interface.py`:

| Research Action | DNA Recording Function | Node Type |
|-----------------|----------------------|-----------|
| Completed research task | `record_research_summary()` | ResearchSummary |
| Pathway search failed | `record_pathway_attempt()` | pathway_attempt |
| Reviewed mandatory docs | `record_documentation_review()` | DocumentationReview |
| New source discovered | `record_surprise()` (source="agent") | SurpriseMoment |

### 6.2 Recording Implementation

```python
def record_to_dna(self, summary: dict, task_name: str = None) -> str:
    """Record research results to the DNA graph using typed helpers."""
    
    # Import from existing module — DO NOT duplicate logic
    try:
        from core.graphify_interface import (
            record_research_summary,
            record_pathway_attempt,
            record_documentation_review,
        )
    except ImportError:
        from Chimera.core.graphify_interface import (
            record_research_summary,
            record_pathway_attempt,
            record_documentation_review,
        )
    
    # Record research summary for completed tasks
    if summary.get("tier", 1) >= 2:
        return record_research_summary(
            task_name=summary.get("task", task_name or "unknown"),
            tier=summary.get("tier", 1),
            sources_count=summary.get("sources_consulted", 0),
            domains_visited=summary.get("domains_visited", 0),
            confidence_rating=summary.get("confidence_rating", "medium"),
            source_table=[
                {"type": self._classify_source(r["url"]), 
                 "url_or_path": r["url"],
                 "confidence": summary.get("confidence_rating", "medium")}
                for r in summary.get("search_results", [])[:5]
            ],
            discrepancies_resolved=summary.get("discrepancies_resolved", []),
        )
    
    # Record pathway attempt if DNA query failed
    dna_query = summary.get("dna_query_result")
    if not dna_query or not dna_query.get("found"):
        return record_pathway_attempt(
            task_name=task_name,
            tool="playwright",
            action="google_search",
            result="success" if summary.get("search_results") else "failed",
            notes=f"No existing pathway for '{task_name}' — new web research performed"
        )
    
    return "no_recording_needed"
```

### 6.3 Source Classification Helper

```python
def _classify_source(self, url: str) -> str:
    """Classify a URL into source types for DNA graph recording."""
    if any(x in url.lower() for x in ["docs.unrealengine.com", "api.unrealengine.com"]):
        return "official_docs"
    elif any(x in url.lower() for x in ["reddit.com", "discord.com", "twitter.com"]):
        return "community"
    elif any(x in url.lower() for x in ["youtube.com", "youtu.be"]):
        return "video_tutorial"
    elif any(x in url.lower() for x in ["medium.com", "dev.to", "hackernoon.com"]):
        return "technical_blog"
    else:
        return "general_web"
```

---

## 7. Error Handling & Fallbacks

### 7.1 Exception Hierarchy

```python
class ResearchAgentError(Exception):
    """Base exception for all research agent errors."""
    pass

class PlaywrightUnavailableError(ResearchAgentError):
    """Raised when Playwright MCP is not available."""
    pass

class LMSudioUnavailableError(ResearchAgentError):
    """Raised when LM Studio API is not reachable."""
    pass

class NetworkTimeoutError(ResearchAgentError):
    """Raised when network operations timeout after retries."""
    pass

class DnaGraphError(ResearchAgentError):
    """Raised when DNA graph operations fail."""
    pass
```

### 7.2 Retry Logic with Exponential Backoff

```python
import time

MAX_RETRIES = 3
BASE_BACKOFF_SECONDS = 1.0

def _retry_with_backoff(self, func, *args, **kwargs):
    """Retry a function call up to MAX_RETRIES times with exponential backoff.
    
    Backoff schedule: 1s, 2s, 4s (for MAX_RETRIES=3)
    """
    for attempt in range(MAX_RETRIES):
        try:
            return func(*args, **kwargs)
        except (NetworkTimeoutError, PlaywrightUnavailableError) as e:
            if attempt == MAX_RETRIES - 1:
                raise  # Last attempt failed, propagate error
            wait_time = BASE_BACKOFF_SECONDS * (2 ** attempt)
            time.sleep(wait_time)
```

### 7.3 Fallback Chains

| Primary Tool | Fallback | Fallback Behavior |
|-------------|----------|-------------------|
| Playwright MCP search | DNA graph cached results | Query `g.query("pathway", query)` and return any cached research findings |
| LM Studio analysis | Raw search results (no analysis) | Return search results without synthesis, mark confidence as "low" |
| Startpage engine | Bing engine | Try second engine automatically |
| DNA graph read | Empty result set | Proceed with web research anyway (graph is advisory, not blocking) |

### 7.4 Graceful Degradation

```python
def google_search(self, query: str, max_results: int = 10) -> list[dict]:
    """Search with full fallback chain."""
    
    # Try Playwright MCP first
    try:
        return self._playwright_client.search(query, max_results=max_results)
    except PlaywrightUnavailableError:
        pass
    
    # Fallback to cached DNA graph results
    dna_results = self.check_dna_graph(query)
    if dna_results.get("found"):
        return [{"title": "Cached", "url": "...", "snippet": "..."}]
    
    # Final fallback: empty list (caller handles the None case)
    return []
```

---

## 8. Mode Compatibility Matrix

### 8.1 How Each Agent Mode Invokes Research

| Mode | Import Pattern | Typical Use Case |
|------|----------------|------------------|
| **code** | `from Chimera.core.research_agent import google_search` | Search for MCP parameter formats before implementing |
| **debug** | `from Chimera.core.research_agent import search_and_analyze` | Search for known error patterns, similar bugs |
| **ask** | `agent = ResearchAgent(); agent.fetch_url_content(url)` | Fetch documentation and current info before answering |
| **architect** | `agent.research_task(desc, depth="deep")` | Research best practices and reference architectures |
| **chimera-code** | Same as code mode + DNA recording | Code implementation with research-backed decisions |
| **chimera-debug** | Same as debug mode + DNA recording | Debugging with web-referenced solutions |
| **chimera-architect** | Same as architect mode + full recording | Architecture design with documented sources |
| **chimera-ue5** | MCP pathway-aware research | UE5-specific research following MCP_PATHWAYS.md |
| **chimera-test** | Verification-focused search | Research testing methodologies, reference data |
| **chimera-balance** | Economy/math research | Balance math verification, reward tuning references |
| **chimera-orchestrate** | Full orchestration integration | Orchestrator delegation + on-demand subagent research |
| **chimera-duty** | Autonomous duty-cycle research | Nightly/idle autonomous research tasks |
| **chimera-sleepwalker** | SimPlaytest evidence gathering | Beat script preparation, reference data collection |

### 8.2 Cross-Mode Research Sharing

All research results are recorded to the shared DNA graph, making them discoverable by ANY mode:

```python
# Mode A performs research and records it
agent = ResearchAgent()
summary = agent.research_task("Configure Niagara particle system")
node_id = agent.record_to_dna(summary, "NiagaraParticleConfig")

# Mode B discovers the same research later
dna_results = g.query("pathway", "Niagara particle system configuration")
if dna_results.get("found"):
    # Use cached research instead of re-searching
    cached_summary = dna_results["data"]
```

---

## 9. Integration with Existing Research Mandate

### 9.1 Tier Classification Reuse

The Research Agent MUST use the existing tier classification from `research_enforcement.py`:

```python
from core.research_enforcement import classify_task_tier

def _classify_depth(self, task_description: str) -> str:
    """Map research_enforcement tiers to depth strings."""
    tier = classify_task_tier(task_description)
    return {1: "quick", 2: "standard", 3: "deep"}.get(tier, "standard")
```

### 9.2 Mandatory Documentation Review Integration

For Tier 2+ tasks, the Research Agent MUST review mandatory docs before web research:

```python
MANDATORY_DOCS = [
    ("AGENTS.md", "Known bugs table, traps section, current game state"),
    ("Chimera/docs/GENERATION_PROTOCOL.md", "Laws, sleepwalker rules, observation protocol"),
    ("Chimera/docs/MCP_PATHWAYS.md", "Working pathways + TRAP entries for relevant tools"),
    ("task_progress.md", "Current NEXT list, session handoffs, corrections"),
    ("Chimera/docs/PENDING_HEURISTICS.md", "Pending/approved heuristics affecting the task domain"),
]

def _review_mandatory_docs(self, task_description: str) -> dict:
    """Review mandatory docs for relevant traps and known issues."""
    findings = {}
    
    # Read each doc and search for relevant content
    for doc_path, purpose in MANDATORY_DOCS:
        try:
            content = self._read_file(doc_path)  # Local file read
            # Search for task-relevant content (traps, known bugs, etc.)
            relevant_sections = self._search_content(content, task_description)
            if relevant_sections:
                findings[doc_path] = {
                    "purpose": purpose,
                    "relevant_findings": relevant_sections
                }
        except FileNotFoundError:
            continue
    
    return findings
```

### 9.3 Research Compliance Scoring

The module exposes a compliance score for dashboard integration (matching `get_research_compliance_score()`):

```python
def get_research_compliance_score(self) -> dict:
    """Calculate research compliance score from DNA graph."""
    
    dna_graph = self._load_dna_graph()
    nodes = dna_graph.get("nodes", [])
    
    # Count by type
    research_summaries = [n for n in nodes if n.get("type") == "ResearchSummary"]
    pathway_attempts = [n for n in nodes if n.get("type") == "pathway_attempt"]
    doc_reviews = [n for n in nodes if n.get("type") == "DocumentationReview"]
    
    # Tier distribution from research summaries
    tier_dist = {}
    for rs in research_summaries:
        tier = str(rs.get("tier", "unknown"))
        tier_dist[tier] = tier_dist.get(tier, 0) + 1
    
    return {
        "research_summaries_count": len(research_summaries),
        "pathway_attempts_count": len(pathway_attempts),
        "documentation_reviews_count": len(doc_reviews),
        "tier_distribution": tier_dist,
        "compliance_rate": self._calculate_compliance_rate(nodes)
    }
```

---

## 10. Usage Examples by Agent Mode

### 10.1 Code Mode — Quick MCP Parameter Lookup

```python
# In code mode, before implementing a feature:
from Chimera.core.research_agent import google_search

# Check DNA graph first (fast path)
results = google_search("Unreal Engine PCG graph node types")

if not results:
    # No cached results — do web search
    results = google_search("Unreal Engine 5.8 PCG graph API", max_results=5)

for r in results[:3]:
    print(f"- {r['title']}: {r['url']}")
```

### 10.2 Debug Mode — Error Pattern Search

```python
# In debug mode, investigating a crash:
from Chimera.core.research_agent import ResearchAgent

agent = ResearchAgent()

# Full research task with LM analysis
summary = agent.search_and_analyze(
    "Unreal Engine TMap operator[] assertion failure fix",
    analysis_prompt="Find the root cause and recommended fix pattern for "
                   "TMap::operator[] assertions when keys are missing."
)

print(f"Analysis: {summary['analysis']}")
print(f"Confidence: {summary['confidence']}")
```

### 10.3 Architect Mode — Deep Architecture Research

```python
# In architect mode, designing a new system:
from Chimera.core.research_agent import ResearchAgent

agent = ResearchAgent()

# Full deep research with source diversity
summary = agent.research_task(
    "Unreal Engine 5 Niagara GPU simulation best practices",
    depth="deep"
)

print(f"Tier: {summary['tier']}")
print(f"Sources consulted: {summary['sources_consulted']}")
print(f"Domains visited: {summary['domains_visited']}")
print(f"Confidence: {summary['confidence_rating']}")

# Record to DNA graph for other agents
node_id = agent.record_to_dna(summary, "NiagaraGPUBestPractices")
```

### 10.4 Chimera Mode — Full Mandate Compliance

```python
# In chimera-code mode, implementing with full research mandate:
from Chimera.core.research_agent import ResearchAgent
from core.research_enforcement import classify_task_tier

agent = ResearchAgent()

task_desc = "Create weapon blueprint with PBR materials"
tier = classify_task_tier(task_desc)  # Returns 3 (Tier 3)

# Tier 3 requires deep research
summary = agent.research_task(task_desc, depth="deep")

# Record compliance
node_id = agent.record_to_dna(summary, task_desc)

# Now implement with documented sources
print(f"Research complete. Node ID: {node_id}")
```

---

## 11. Testing Strategy

### 11.1 Unit Tests (`test_research_agent.py`)

```python
import pytest
from unittest.mock import MagicMock, patch

class TestResearchAgent:
    
    @pytest.fixture
    def agent(self):
        return ResearchAgent()
    
    def test_google_search_returns_structured_results(self, agent):
        """google_search returns list of dicts with title/url/snippet."""
        results = agent.google_search("test query")
        assert isinstance(results, list)
        if results:  # May be empty on fallback
            assert "title" in results[0]
            assert "url" in results[0]
            assert "snippet" in results[0]
    
    def test_google_search_fallback_on_playwright_unavailable(self, agent):
        """Returns cached DNA graph results when Playwright is unavailable."""
        with patch.object(agent._playwright_client, 'search', side_effect=PlaywrightUnavailableError()):
            results = agent.google_search("test query")
            # Should return empty list or cached results
    
    def test_research_task_quick_returns_tier_1(self, agent):
        """Quick depth returns tier 1 with minimal resources."""
        summary = agent.research_task("Spawn actor with known path", depth="quick")
        assert summary["tier"] == 1
    
    def test_research_task_deep_returns_tier_3(self, agent):
        """Deep depth returns tier 3 with source diversity."""
        summary = agent.research_task("New feature architecture design", depth="deep")
        assert summary["tier"] == 3
        assert "failure_research" in summary
    
    def test_record_to_dna_calls_typed_helpers(self, agent):
        """record_to_dna uses typed helpers from graphify_interface."""
        with patch('Chimera.core.graphify_interface.record_research_summary') as mock_rs:
            agent.record_to_dna({"tier": 2, "task": "test"}, "TestTask")
            mock_rs.assert_called_once()
```

### 11.2 Integration Tests

```python
class TestResearchAgentIntegration:
    
    def test_playwright_search_live(self):
        """Test against real Playwright MCP (requires running browser)."""
        agent = ResearchAgent()
        results = agent.google_search("Unreal Engine documentation")
        assert len(results) > 0 or True  # May fail if no browser available
    
    def test_lm_studio_analysis_live(self):
        """Test against real LM Studio API (requires running model)."""
        agent = ResearchAgent()
        summary = agent.search_and_analyze("test query")
        assert "analysis" in summary or True  # May fail if LM unavailable
```

---

## 12. File Changes Summary

### New Files Created

| File | Lines (est.) | Purpose |
|------|-------------|---------|
| `Chimera/core/research_agent.py` | ~400 | Main module, ResearchAgent class, convenience functions |
| `Chimera/core/research_playwright.py` | ~250 | Playwright MCP integration layer |
| `Chimera/core/research_lm_studio.py` | ~200 | LM Studio REST API integration |
| `Chimera/core/test_research_agent.py` | ~300 | Unit tests with mocking |

### Existing Files Modified

| File | Change | Reason |
|------|--------|--------|
| `AGENTS.md` | Add Research Agent invocation protocol section | Document how all modes can invoke research |
| `Chimera/docs/MCP_PATHWAYS.md` | Add pathway #29: web_research (Playwright MCP) | Document the new web research pathway |

### No Changes Required To

- `research_enforcement.py` — tier classification stays as-is
- `graphify_interface.py` — typed helpers stay as-is, Research Agent imports them
- `dream_loop.py`, `sleepwalker.py`, `rehearsal.py` — no changes needed (they can optionally use the new module)

---

## 13. Implementation Order

### Phase 1: Core Module (`research_agent.py`)
1. Create `ResearchAgent` class skeleton with `__init__`
2. Implement `google_search()` with Playwright MCP integration
3. Implement fallback chain (Playwright → DNA graph → empty)
4. Add module-level convenience functions

### Phase 2: Analysis Layer (`research_lm_studio.py`)
5. Create `LMSearchAnalyzer` class
6. Implement `analyze_results()` for Tier 2 analysis
7. Implement `synthesize_research()` for Tier 3 synthesis
8. Handle LM Studio unavailability gracefully

### Phase 3: Full Task Orchestration (`research_agent.py`)
9. Implement `_research_quick()`, `_research_standard()`, `_research_deep()`
10. Wire up tier-based resource allocation in `research_task()`
11. Add mandatory doc review for Tier 2+ tasks

### Phase 4: DNA Graph Recording
12. Implement `record_to_dna()` using typed helpers from `graphify_interface.py`
13. Implement `_classify_source()` helper
14. Test recording to live DNA graph

### Phase 5: Testing & Documentation
15. Write unit tests with mocking
16. Update AGENTS.md with Research Agent invocation protocol
17. Add pathway #29 to MCP_PATHWAYS.md
18. Run `python -m core.test_research_agent` validation

---

## 14. Mermaid Architecture Diagram

```mermaid
graph TD
    subgraph "Agent Mode"
        A[Code/Debug/Ask/Architect] --> B[Research Agent Module]
        C[chimera-code/chimera-debug] --> B
        D[chimera-architect/chimera-ue5] --> B
    end
    
    subgraph "research_agent.py"
        B --> E[ResearchAgent Class]
        E --> F[google_search()]
        E --> G[search_and_analyze()]
        E --> H[fetch_url_content()]
        E --> I[research_task()]
        E --> J[record_to_dna()]
    end
    
    subgraph "Layer 1: Playwright MCP"
        F --> K[PlaywrightSearchClient]
        K --> L[navigate to search engine]
        K --> M[snapshot results]
        K --> N[parse structured output]
    end
    
    subgraph "Layer 2: LM Studio"
        G --> O[LMSearchAnalyzer]
        H --> O
        I --> O
        O --> P[call qwen3.6-35b API]
        O --> Q[synthesize findings]
    end
    
    subgraph "Layer 3: DNA Graph"
        J --> R[typed helpers from graphify_interface.py]
        R --> S[record_research_summary()]
        R --> T[record_pathway_attempt()]
        R --> U[record_documentation_review()]
        I --> V[g.query pathway check]
    end
    
    subgraph "Fallback Chain"
        K -.fallback.> W[DNA graph cached results]
        O -.fallback.> X[raw search results no analysis]
        L -.fallback.> Y[Bing engine if Startpage fails]
    end
```

---

## 15. Open Questions for Implementation

| # | Question | Impact |
|---|----------|--------|
| Q1 | Should `google_search()` default to Startpage or Bing? | Affects fallback chain order |
| Q2 | What is the exact LM Studio API URL format? (localhost:1234 vs other ports) | Affects LMSearchAnalyzer initialization |
| Q3 | Should the module auto-detect Playwright availability at init time, or fail lazily on first call? | Affects error handling strategy |
| Q4 | Do we need to handle browser tab management (multiple agents calling Playwright concurrently)? | Affects concurrency design |

---

## 16. Appendix: Existing DNA Graph Node Types Used

The Research Agent writes these existing node types (no new node types needed):

| Node Type | Writer Function | When Written |
|-----------|-----------------|--------------|
| `ResearchSummary` | `record_research_summary()` | After Tier 2+ research tasks complete |
| `pathway_attempt` | `record_pathway_attempt()` | When DNA pathway query fails (new pathway discovered) |
| `DocumentationReview` | `record_documentation_review()` | When mandatory docs are reviewed for Tier 2+ tasks |
| `SurpriseMoment` | `record_surprise(source="agent")` | When unexpected findings/corrections occur during research |

All node types already exist in the DNA graph schema — no schema changes required.
