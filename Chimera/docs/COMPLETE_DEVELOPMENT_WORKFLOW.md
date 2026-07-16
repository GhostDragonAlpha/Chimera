# COMPLETE DEVELOPMENT WORKFLOW: Research-Informed Game Development via Hire_Scholar_organ

## OVERVIEW
This workflow integrates all concepts from the Claude code system / AGENTS.md documentation into a single, executable development pipeline. It ensures research informs all game development questions, unknown actions are tried and recorded as discoveries, mapped to DSL for direct Pipeline building, and the Graph deepens with each iteration through the orchestrator loop with MCP servers providing execution mechanisms for UE5 game development operations.

---

## PHASE 1: PRE-FLIGHT & STATE VERIFICATION

**Objective**: Verify graph health, GPA trend, spiral loop board, pending technical_research tasks, and environment reachability.

**Commands**:
```bash
cd e:\PythonChimera\Chimera
python -m core.preflight
```

**Expected Output**:
- Graph health status (healthy/degraded)
- GPA trend (last 20 cycles: pass/fail ratio)
- Spiral loop board (current Loop N status)
- Pending technical_research queue count
- Environment reachability (Vision/Testing Model / UE / DNA API)

---

## PHASE 2: HIRE_SCHOLAR_ORGAN EXECUTION (Research Infrastructure)

**Objective**: Query campus sources for dust-accumulation research, search local research corpus, build discovery node with citations, and generate study guide.

### Step 2.1: Query Campus Sources
Campus mapping from `core/scholar.py`:
- `unreal_engine_craft` → Niagara/Particle VFX expertise, dust accumulation materials
- `engineering_school` → lunar/regolith physics, vacuum ballistics (dust arcs vs billows)
- `art_school` → color/lighting/mood/render, ground-surface visual fidelity

### Step 2.2: Search Local Research Corpus
Query `Chimera/research_corpus/` for cached sources matching "dust accumulation", "vertex normal blending", "noise functions".

### Step 2.3: Build Discovery Node with Citations
Via `build_discovery_node()` function in `core/scholar.py`:
```python
discovery_id = build_discovery_node(
    feature="Ground_Sand_Particles",
    campus_sources=["unreal_engine_craft", "engineering_school", "art_school"],
    corpus_sources=["research_corpus/dust_accumulation_reference.md", ...],
    parameters={
        "research_method": "campus_plus_corpus",
        "sources_consulted": N,
        "noise_functions": true,
        "vertex_normal_blending": true
    },
    acceptance_criteria=[
        "Parameters extracted from A+ campus sources",
        "Verified against local references",
        "Observable in-engine via telemetry or screenshot"
    ],
    confidence="medium"
)
```

### Step 2.4: Generate Study Guide
Via `write_study_guide()` function:
- Exam format: acceptance_criteria + numeric_parameters_with_citations
- Canonical reference from campus seed sources
- Research_discovery_node reference attached to feature node

---

## PHASE 3: SPIRAL GROWTH PATTERN EXECUTION

**Objective**: Complete all features in Loop N before starting Loop N+1.

**Loop Sequence**:
- **Loop 0**: The Player (character, suit, lighting) → The seed
- **Loop 1**: The Ground (sand, rock, metal, footprints) → Touch
- **Loop 2**: Basic Verbs (look, step, pick up, drop, shovel) → Interaction
- **Loop 3**: The Sky (Earth, Moon, Sun, starfield) → Scale
- **Loop 4**: Tools (shovel, scanner, weapon) → Purpose
- **Loop 5**: Other Dots (NPCs, creatures, trade, conflict) → Society
- **Loop 6**: Shelter (habitat, station, base) → Home
- **Loop 7**: Travel (vehicles, ships, quantum jump) → Freedom
- **Loop 8**: Systems (economy, factions, missions) → Consequence
- **Loop 9**: The Universe (planets, moons, asteroids) → Infinity

**Rule**: Complete all features in Loop N before starting Loop N+1. Each loop's verified output is the foundation for the next.

---

## PHASE 4: RALPH LOOP VERIFICATION CYCLE (Per Feature)

**Objective**: Iterative verification for each feature using the Ralph Loop pattern.

**Cycle Steps**:
1. **Select feature** → Read DSL specification
2. **Query Graph** → `graphify_query("pathway", feature)` to check if known
3. **If known**: Feed to Pipeline (`run_deep_space_trader_pipeline.py`)
4. **If unknown**: Compile context package + spawn subagent with full autonomy (5+ parameter combinations)
5. **Apply & Verify**: Vision/Testing Model compares → Refine → Repeat until verified

**Subagent Mandate**: Full autonomy to research, discover, test, and record. Must try 5+ parameter combinations before reporting blocked. Returns SUBAGENT REPORT format: status, what was built, discoveries, DSL mappings, graph nodes, screenshot path, LM Studio response.

---

## PHASE 5: AAA QUALITY GATES

**Objective**: Enforce quality standards using the Result Grader (`core/result_grader.py`) — 100-point rubric, zero LM dependency.
(result_grader_aaa_expanded was DELETED 2026-07-16: it graded the agent's own adjectives against a benchmark it never read — docs/MASTER_DEVELOPMENT_DASHBOARD.md)

**Tier Breakdown**:
- **Tier 1**: Technical Correctness, Stability, Design Checklist, Spec Fidelity (100 pts foundation)
- **Tier 2**: Player Immersion, Gameplay Flow, Systems Depth (120 pts experience — the critical "feel")
- **Tier 3**: Visual Fidelity, Audio Design, Polish & Juiciness (95 pts production quality)
- **Tier 4**: Narrative & World Building, Accessibility & Inclusivity (50 pts game design)

**Minimum Targets**:
- Loop 0 avg AAA enjoyment: 85%+
- Loop 1 avg AAA enjoyment: 80%+
- All features ≥75% AAA-benchmark enjoyment percentile

---

## PHASE 6: CONTINUOUS INTEGRATION VIA PIPELINE

**Objective**: Execute the authoritative build mechanism that compiles DSL specifications.

**Pipeline Commands**:
```bash
cd e:\PythonChimera\Chimera
python run_deep_space_trader_pipeline.py
```

**Pipeline Stages**:
1. DSL Parse
2. Code Generation (`core/game_code_generator.py`)
3. Build (UBT)
4. Playtest
5. Report
6. Visual Verification

**Post-Flight Recording**:
```bash
python -m core.postflight --phase "<what you did>" --result "<UBT output verbatim>" [--feature X --loop N --status S]
```

---

## PHASE 7: RECURSIVE SELF-IMPROVEMENT

**Objective**: Ensure unknown actions are tried, recorded as discoveries, mapped to DSL so the Pipeline can build them directly next time, and the Graph deepens with each iteration.

**Failure Recovery Protocol**:
Any failure after 2 attempts must automatically:
1. Create a `technical_research` task in the Feature Ledger with failed parameters
2. Record pathway_attempt mutations
3. Move to the next feature

Future agents query technical_research tasks before starting work, trying something different based on history.

---

## MCP SERVER INTEGRATION REFERENCE

| MCP Server | Purpose | Key Tools |
|------------|---------|-----------|
| `graphify` | Knowledge graph operations | `query_graph`, `get_node`, `shortest_path`, `list_prs`, `triage_prs` |
| `chiR24-unreal-mcp` | Unreal Engine 5 asset/blueprint/actor management | `manage_asset`, `manage_blueprint`, `control_actor`, `control_editor`, `build_environment` |
| `playwright` | Browser automation for UI testing/validation | `browser_navigate`, `browser_click`, `browser_snapshot`, `browser_take_screenshot` |
| `git` | Version control operations | `git_status`, `git_commit`, `git_push_to_origin`, etc. |

---

## EXECUTION SUMMARY

This complete workflow ensures:
1. Research informs all game development questions
2. Unknown actions are tried and recorded as discoveries
3. Discoveries are mapped to DSL so the Pipeline can build them directly next time
4. The Graph deepens with each iteration through the orchestrator loop with MCP servers providing execution mechanisms for UE5 game development operations

All concepts from the Claude code system / AGENTS.md documentation are fully integrated into this workflow.