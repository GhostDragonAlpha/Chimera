# Research Mandate — Universal Research Requirement Policy

**Effective:** 2026-07-10  
**Status:** Design (pending implementation)  
**Owner:** Orchestrator / All Subagents  
**Supersedes:** None (new policy)

---

## 1. Purpose

Every task in the Chimera system — regardless of size, complexity, or perceived simplicity — MUST complete a research phase before execution begins. This mandate eliminates assumptions and ensures all decisions are evidence-based.

**Rationale:** The Verb_Bend capsule bug (2026-07-10) demonstrated that unverified "verified" claims from sleepwalker simulations can be catastrophically wrong. A crouch fix that never called `SetCrouchedHalfHeight()` was recorded as verified against its own recording — the self-report failure this mandate exists to prevent.

---

## 2. Universal Research Requirement (URR)

### 2.1 Scope

The URR applies to:
- **All subagent tasks** delegated by the Orchestrator
- **Sleepwalker beat scripts** (`core/sleepwalker.py`)
- **Rehearsal decisions** (`core/rehearsal.py`)
- **Pipeline builds** (the `run_deep_space_trader_pipeline.py` entry point)
- **Any task appearing in `task_progress.md` NEXT list**

No exceptions. No shortcuts. No "this is too simple to research."

### 2.2 Research Phase Checklist

Before ANY execution begins, the agent MUST complete all applicable checklist items:

```markdown
## Pre-Execution Research Checklist — [Task Name]

### Required (All Tasks)
- [ ] DNA graph query: `g.query("pathway", "<task_description>")`
- [ ] DNA graph query: `g.query("feature", "<related_feature_name>")`
- [ ] Review relevant documentation files (see §2.3)
- [ ] Record research findings to DNA graph (`record_pathway` or `record_surprise`)

### Complexity-Specific (see §3 for tier assignment)
- [ ] Tier 1: Google search via Playwright MCP (proven working)
- [ ] Tier 2: Multi-source verification + pathway cross-reference
- [ ] Tier 3: Full research protocol with source diversity, failure research
```

### 2.3 Mandatory Documentation Review

Every task MUST check these files before execution:

| File | What to Check | Why |
|------|---------------|-----|
| `AGENTS.md` (workspace root) | Known bugs table, traps section, current game state | Prevents repeating documented failures |
| `Chimera/docs/GENERATION_PROTOCOL.md` | Laws, sleepwalker rules, observation protocol | Ensures protocol compliance |
| `Chimera/docs/MCP_PATHWAYS.md` | Working pathways + TRAP entries for relevant tools | Avoids known MCP traps |
| `task_progress.md` (workspace root) | Current NEXT list, session handoffs, corrections | Prevents duplicate work, catches false claims |
| `Chimera/docs/PENDING_HEURISTICS.md` | Pending/approved heuristics affecting the task domain | Ensures constitutional compliance |

**Search pattern:** Before executing any MCP call, search MCP_PATHWAYS.md for the tool/action. If a TRAP entry exists for that combination, follow the documented workaround — do NOT assume success from `success: true`.

---

## 3. Research Depth Tiers

Tasks are classified into one of three tiers based on complexity. The Orchestrator assigns the tier during task delegation.

### Tier 1 — Simple (Quick Research)

**Applies to:** Tasks involving a single, well-documented MCP pathway with no known traps; parameter tuning within established ranges; configuration changes using existing templates.

**Research requirements:**
1. DNA graph query for pathway: `g.query("pathway", "<task>")`
2. If pathway exists → follow exactly (no additional research needed)
3. If pathway does NOT exist → test simplest approach, record result as `record_pathway`
4. Review AGENTS.md known bugs table for relevant category

**Time budget:** 5 minutes max per task  
**Example tasks:** Setting a scalar parameter value, spawning an actor with known path, toggling a boolean property

### Tier 2 — Moderate (Multi-Source Verification)

**Applies to:** Tasks involving new MCP tool combinations; modifying existing systems; visual verification requirements; any task where the pathway is partially documented or has known traps.

**Research requirements:**
1. All Tier 1 requirements
2. **Google search via Playwright MCP** — minimum 3 sources:
   - Primary source (official documentation, manufacturer specs)
   - Secondary source (community forums, technical blogs)
   - Tertiary source (video tutorials, comparative reviews)
3. **Cross-reference verification** — at least 2 independent sources per parameter
4. Review MCP_PATHWAYS.md for ALL tools used in the task
5. Record all findings: `record_pathway` for successful combinations, `record_surprise` for corrections/dead-ends

**Time budget:** 15 minutes max per task  
**Example tasks:** Creating a new material with PBR parameters, configuring character movement speeds, setting up Niagara particle effects

### Tier 3 — Complex (Full Research Protocol)

**Applies to:** New feature creation; architecture decisions; any task involving unknown MCP pathways; tasks where expectations may be violated; features requiring visual verification against reference images.

**Research requirements:**
1. All Tier 2 requirements
2. **Source diversity** — minimum source types:
   - Primary photography/reference images (from `research_references/` or web)
   - Technical documentation/specs
   - Community sources (forums, Discord, Reddit)
   - Video content (tutorials, reviews, comparisons)
   - 3D scans/models (if applicable)
3. **Multi-site verification** — minimum 3 different domains (not pages on same site)
4. **Cross-reference confirmation** — 2 independent sources per parameter; if no second source exists, document absence and mark confidence as Low
5. **Failure research** — minimum 1 source on what doesn't work (degradation patterns, edge cases, abandoned designs)
6. **Campus discovery** — every new source recorded via `g.mutate("research_discovery", {...})` or `record_surprise --source agent`
7. **Research summary** — structured output (see §5 for template)

**Time budget:** 30 minutes max per task  
**Example tasks:** Creating a new weapon blueprint, designing a complete interaction system, implementing novel environmental effects

---

## 4. Resource Allocation

### 4.1 Playwright MCP (Web Research)

**Capabilities:**
- `mcp_playwright_browser_navigate` — navigate to URLs
- `mcp_playwright_browser_find` — search page content for text/regex
- `mcp_playwright_browser_snapshot` — capture accessibility tree of current page
- `mcp_playwright_browser_click` / `type` / `fill_form` — interact with web pages

**Proven workflow:** Google search via Playwright MCP (documented as "proven working" in task_progress.md). Use Startpage as primary engine, Bing as fallback.

**Resource limits:** Unlimited queries per task. No rate limiting enforced by this mandate.

### 4.2 LM Studio (qwen3.6-35b)

**Capabilities:**
- Analysis and synthesis of research findings
- Professor review/grading via REST API
- Visual verification when explicitly requested (checklist mode preferred over keyword sniffing)

**Resource limits:** Unlimited calls per task. Each call should include full context package from DNA graph + relevant documentation excerpts.

### 4.3 DNA Graph Tools

**Capabilities:**
- `g.query("pathway", "...")` — check existing pathways
- `g.query("feature", "...")` — review related features
- `g.query("campus", "...")` — access research campus sources
- `record_pathway`, `record_surprise`, `record_feature` — document findings

**Resource limits:** Unlimited queries. Graph size bounded by compaction (30-day archive policy per GENERATION_PROTOCOL.md).

### 4.4 Visual Verification via MCP

**Capabilities:**
- `control_editor screenshot mode=editor_viewport` — viewport captures
- `control_editor screenshot mode=game_viewport` — PIE-specific captures
- `inspect.get_property`, `get_component_property` — read-back verification

**Resource limits:** Unlimited screenshots per task. Always verify file size > 100000 bytes before trusting capture.

---

## 5. Research Summary Template

Every Tier 2+ task MUST produce a research summary in this format:

```markdown
## Research Summary — [Task Name]

**Tier:** [1/2/3]  
**Date:** [ISO 8601 timestamp]  
**Researcher:** [agent name / human operator]

### Sources Consulted
| # | Source Type | URL/Path | Confidence | Notes |
|---|-------------|----------|------------|-------|
| 1 | Primary docs | https://... | High | ... |
| 2 | Community forum | https://... | Medium | ... |

**Total sources:** N  
**Domains visited:** M (minimum 3 required for Tier 3)

### Parameters and Citations
| Parameter | Value | Source #1 | Source #2 | Confidence |
|-----------|-------|-----------|-----------|------------|
| param_a | 42.0 | [1] | [2] | High |
| param_b | "foo" | [1] | (none) | Low — no second source |

### Discrepancies Resolved
- Parameter X: Source [1] says A, Source [2] says B → resolved to A because...
- Parameter Y: All sources agree on C → no resolution needed

### Failure Research (Tier 3 only)
| What Doesn't Work | Why It Fails | Source |
|-------------------|--------------|--------|
| Approach Z | Causes crash due to... | [3] |

### New Discoveries Recorded
- `record_surprise --context "..." --reality "..." --source agent` — node_id: <id>
- `record_pathway --name "..." --pathway "..."` — node_id: <id>

### Confidence Rating
**Overall:** [High/Medium/Low]  
**Justification:** ...
```

---

## 6. Enforcement Mechanism

### 6.1 Orchestrator Pre-Flight Checklist

The Orchestrator MUST enforce research completion before delegating any subtask:

```python
# Pseudocode for orchestrator enforcement
def validate_research_completed(task):
    """Returns True if task has completed all required research."""
    
    # Check DNA graph for pathway query
    pathways = g.query("pathway", task.description)
    if not pathways:
        raise ResearchGapError(f"No pathway found for {task.name}")
    
    # Check documentation review
    doc_review = check_documentation_review(task)
    if not doc_review.completed:
        raise DocumentationReviewMissingError(
            f"Task {task.name} has not reviewed mandatory docs"
        )
    
    # Check research summary exists for Tier 2+
    if task.tier >= 2:
        if not task.research_summary or not validate_research_summary(task.research_summary):
            raise ResearchSummaryMissingError(
                f"Task {task.name} requires a research summary (Tier {task.tier})"
            )
    
    return True
```

### 6.2 Subtask Message Parameter Requirement

Every subtask delegation MUST include the research summary in the `message` parameter:

```python
# Orchestrator delegates with embedded research
subtask = orchestrator.delegate(
    name="CreateWeaponBlueprint",
    message="""RESEARCH_SUMMARY_START
[Full research summary from §5 template]
RESEARCH_SUMMARY_END

EXECUTION_INSTRUCTIONS:
1. Follow pathway X exactly (from DNA graph)
2. Apply workaround Y for trap Z (from MCP_PATHWAYS.md)
3. Verify via read-back after completion
""",
    tier=2,
    research_verified=True
)
```

### 6.3 Post-Task Verification

After task execution, the agent MUST:

1. **Read-back verification** — verify all changes using appropriate MCP read-backs (see MCP_PATHWAYS.md §18)
2. **Compare against research findings** — did execution match research predictions? Record any deviations as `record_surprise`
3. **Update DNA graph** — record pathway if new, update existing pathway with corrections

### 6.4 Enforcement Checkpoints

| Checkpoint | Who | What | Consequence of Failure |
|------------|-----|------|------------------------|
| Pre-delegation | Orchestrator | Validates research checklist complete | Task rejected, returns to queue |
| During execution | Subagent | Follows pathway exactly, records surprises | `pathway_attempt` recorded with failure category |
| Post-execution | Subagent | Read-back verification + DNA update | Auto-grade F if verification fails |
| Session close | Any agent | Postflight includes research compliance note | Cannot declare phase complete without it |

---

## 6.5 Context Exhaustion Controls (added 2026-07-10)

The Research Agent MUST NOT stop researching until it has exhausted all available context for the query. This prevents shallow research (one search, report back) and forces thorough investigation.

### Minimum Source Requirements Per Tier

| Tier | Minimum Domains | Minimum Source Types | Failure Sources Required |
|------|-----------------|---------------------|-------------------------|
| **Tier 1** (Quick) | 3 domains (if web search performed) | N/A (single-domain pathway tasks exempt) | Not required |
| **Tier 2** (Standard) | 5 different domains | 3 of: official_docs, community, video_tutorial, technical_blog, general_web | ≥1 |
| **Tier 3** (Deep) | 8 different domains | All 5 source types represented | ≥1 |

A "domain" is a distinct top-level provider — not multiple pages on the same site. `stackoverflow.com`, `reddit.com`, and `github.com` each count as one domain. Three pages from stackoverflow.com counts as ONE domain.

### Context Exhaustion Checklist (Mandatory)

Before reporting results, the Research Agent MUST verify ALL checks pass:

```markdown
## Context Exhaustion Verification

- [ ] Have I visited actual content pages (not just Google snippets)? → Must visit ≥2 real pages
- [ ] Do I have multiple source types? → Must have ≥3 different domains from different providers
- [ ] Have I searched for what doesn't work? → Must find at least 1 failure/edge case source
- [ ] Are there related queries I haven't explored? → Must check "People also ask" and follow up

VERDICT: PASS / FAIL (if FAIL, continue researching)
```

**No premature termination:** The agent MUST NOT report results until ALL of the above checks pass. If any check fails, continue researching. Do not declare research complete with partial findings.

### Orchestrator Validation

The orchestrator validates returned reports against these thresholds before accepting them as complete:

- Tier 1: ≥3 domains (if web search was performed)
- Tier 2: ≥5 domains AND ≥3 source types AND ≥1 failure source
- Tier 3: ≥8 domains AND all 5 source types AND ≥1 failure source AND ≥2 page visits

If a report fails validation, the orchestrator re-delegates to the Research Agent with explicit instructions to dig deeper, citing which thresholds were not met. See [`Chimera/core/research_enforcement.py:validate_research_depth()`](Chimera/core/research_enforcement.py) for programmatic enforcement.

### Anti-Patterns (Shallow Research Detection)

The following patterns indicate premature termination and MUST be avoided:

- ❌ "One search, 3 snippets, report back" — Tier 1+ tasks require actual page visits
- ❌ "All sources from same domain" — e.g., 5 stackoverflow.com pages = 1 domain
- ❌ "No failure research conducted" — Every task must find at least 1 source on what doesn't work (Tier 2+)
- ❌ "No related query follow-up" — Google's "People also ask" ignored
- ❌ "Confidence High with only 1 source per parameter" — Must be marked Low if no cross-reference exists

---

## 7. Integration Points

### 7.1 AGENTS.md Update

Add a new section to `AGENTS.md` after "The Contract (MANDATORY)":

```markdown
## Research Mandate (2026-07-10)

**Every task requires research before execution.** Full policy: `Chimera/docs/RESEARCH_MANDATE.md`.

### Quick Reference
1. **Before any MCP call:** Query DNA graph + check MCP_PATHWAYS.md for traps
2. **Tier 1 tasks:** DNA query → follow pathway (5 min max)
3. **Tier 2+ tasks:** Complete research summary (§5 template), multi-source verification
4. **Post-execution:** Read-back verify, record deviations as surprises

### Enforcement
- Orchestrator validates research checklist before delegation
- Subtask `message` parameter MUST include embedded research summary for Tier 2+
- Postflight cannot declare phase complete without research compliance note
```

### 7.2 task_progress.md Handoff Format Update

Add a new section to the handoff format:

```markdown
## Research Compliance (NEW — 2026-07-10)

All NEXT items MUST include:
- **Tier:** [1/2/3]
- **Research summary attached:** Yes/No (Yes for Tier 2+, No acceptable for Tier 1)
- **Pathway followed:** <pathway_name_or_none>
- **Traps avoided:** <trap_names_from_MCP_PATHWAYS>

Example:
1. **Verb_Bend** — Tier 2, research attached, pathway: character_configure_movement, traps: possess_fake_success
```

### 7.3 DNA Graph Integration

New mutation types for research tracking:

| Node Type | Purpose | Fields |
|-----------|---------|--------|
| `ResearchSummary` | Documents completed research phase | task_name, tier, sources_count, confidence_rating, node_ids_referenced |
| `PathwayAttempt` | Records failed pathway discovery | task_name, attempted_pathway, error_category, workaround_applied |
| `DocumentationReview` | Confirms mandatory docs were checked | doc_file, section_reviewed, relevant_findings |

---

## 8. Implementation Plan

### Phase 1: Documentation (this design)
- [x] Create `Chimera/docs/RESEARCH_MANDATE.md` (§ this file)
- [ ] Update `AGENTS.md` with Research Mandate quick reference section
- [ ] Update `task_progress.md` handoff format template

### Phase 2: Orchestrator Enforcement (code changes)
- [ ] Add `validate_research_completed()` function to orchestrator module
- [ ] Modify subtask delegation to embed research summary in message parameter
- [ ] Add Tier classification logic based on task complexity heuristics
- [ ] Update preflight/postflight to include research compliance checks

### Phase 3: DNA Graph Integration (code changes)
- [ ] Add `ResearchSummary`, `PathwayAttempt`, `DocumentationReview` mutation types to `graphify_interface.py`
- [ ] Create `record_research_summary()` typed helper
- [ ] Update dream_loop to process research compliance metrics

### Phase 4: Validation and Testing
- [ ] Dry-run existing NEXT items through new enforcement pipeline
- [ ] Verify no regression in task throughput (should be neutral or positive)
- [ ] Run `python -m core.doc_audit` — must return CLEAN

---

## 9. Known Constraints and Edge Cases

### 9.1 Sleepwalker Limitations

The sleepwalker (`core/sleepwalker.py`) runs under `CHIMERA_AGENT_SIM=1` and cannot record direct observations. Research mandate compliance for sleepwalker tasks:
- Pre-flight research is done by the orchestrator before beat script execution
- Sleepwalker records `SimPlaytest` evidence + surprises (not research summaries)
- Research summary validation happens at delegation time, not during sleepwalk

### 9.2 Rehearsal Decisions

Rehearsal (`core/rehearsal.py`) produces candidate next-moves with veto tables:
- Each rehearsal decision MUST include a Tier classification for the proposed move
- If tier >= 2, the research summary is generated by the orchestrator during delegation
- Human veto overrides any research finding (one sentence, recorded as `surprise --source human`)

### 9.3 Pipeline Builds

The pipeline (`run_deep_space_trader_pipeline.py`) has implicit research built into its DSL parse → code generation → build cycle:
- DSL terms without pathways trigger MCP discovery (existing behavior)
- Research mandate adds explicit documentation review step before each pipeline run
- Build failures auto-grade F regardless of research compliance (existing policy, unchanged)

### 9.4 Resource Exhaustion

While the mandate specifies "unlimited resources," practical limits apply:
- Tier 1 tasks: 5 minutes max per task
- Tier 2 tasks: 15 minutes max per task  
- Tier 3 tasks: 30 minutes max per task
- If research time is exhausted without completion, record as `pathway_attempt` with category `research_timeout`, move to next candidate

---

## 10. Metrics and Compliance Tracking

### 10.1 Research Compliance Score

Track per-agent (per-session):
```python
compliance_score = {
    "tasks_delegated": N,
    "research_completed": M,
    "tier_2_plus_with_summary": K,
    "pathway_followed_exact": P,
    "traps_avoided": T,
    "surprises_recorded": S
}
# compliance_rate = research_completed / tasks_delegated (target: 1.0)
```

### 10.2 Integration with GPA System

Research compliance feeds into the existing GPA calculation:
- Tasks completed without required research summary → GPA penalty
- Surprises recorded during execution → neutral (expected learning)
- Pathway followed exactly + read-back verified → GPA bonus
- Traps avoided via prior pathway knowledge → GPA bonus

### 10.3 Dashboard Display

The DNA dashboard (`dna_dashboard.py`) should display:
- Research compliance rate per session
- Most common trap categories encountered
- Tier distribution of tasks this loop
- Average research time per tier

---

## Appendix A: Quick Reference Card

```
┌─────────────────────────────────────────────────────┐
│           RESEARCH MANDATE — QUICK REFERENCE        │
├─────────────────────────────────────────────────────┤
│                                                     │
│  BEFORE ANY TASK:                                   │
│  1. g.query("pathway", "<task>")                    │
│  2. Check MCP_PATHWAYS.md for traps                 │
│  3. Review AGENTS.md known bugs                     │
│  4. Assign tier (1/2/3)                             │
│                                                     │
│  TIER 1 (Simple):                                   │
│  - DNA query → follow pathway                       │
│  - 5 min max                                        │
│                                                     │
│  TIER 2 (Moderate):                                 │
│  - All Tier 1 + Google search (3 sources)           │
│  - Cross-reference verification                     │
│  - Research summary (§5 template)                   │
│  - 15 min max                                       │
│                                                     │
│  TIER 3 (Complex):                                  │
│  - All Tier 2 + source diversity                    │
│  - Multi-site verification (3 domains)              │
│  - Failure research (1 source)                      │
│  - Campus discovery (record all new sources)        │
│  - 30 min max                                       │
│                                                     │
│  AFTER EXECUTION:                                   │
│  1. Read-back verify via MCP                        │
│  2. Compare against research predictions            │
│  3. Record deviations as surprises                  │
│  4. Update DNA graph                                │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## Appendix B: Trap Cross-Reference Matrix

| MCP Tool/Action | Known Traps (from MCP_PATHWAYS.md) | Research Requirement |
|-----------------|-------------------------------------|----------------------|
| `spawn_actor` | `.BP_Y_C` class form fails; use `/Game/X/BP_Y.BP_Y` asset form | Tier 1 pathway check mandatory |
| `set_component_property {material}` | Lies — reports success but writes nothing | Tier 2: must verify via read-back |
| `control_editor possess` | Fakes success in PIE | Tier 1: use AutoPossessPlayer=Player0 instead |
| `simulate_input` | Drives wrong pawn when DefaultPawn exists | Tier 2: check level has no DefaultPawn |
| `create_niagara_system` | Facade — renders nothing | Tier 3: must use spawn_niagara with engine templates |
| `get_actor_bounds` (DynamicMeshActor) | Stale cache after post-creation moves | Tier 2: use inspect get_actor_details instead |
| `BugItGo` during PIE | Hard-rejected, not silent no-op | Tier 1: never use mid-PIE |
| `set_material` on DynamicMeshComponent | Reports success but OverrideMaterials read-back empty | Tier 2: verify visually or trust error-free response |

---

*Document created: 2026-07-10T17:30Z*  
*Next step: Implementation by code mode — see §8 Implementation Plan*
