# Chimera — Build System Reference

## Canonical Project Structure

```
E:\PythonChimera\Chimera\
├── Chimera.uproject
├── Source\Chimera\
│   ├── Chimera.Build.cs              # Do NOT regenerate
│   ├── Chimera.Target.cs
│   ├── ChimeraEditor.Target.cs
│   └── ProceduralGenerated\          # All generated code
│       ├── Combat\ AI\ Flight\ PCG\
│       ├── Stations\ Missions\ Factions\
│       ├── Save\ GameMode\ Ships\ Scripts\
├── Content\Levels\
├── Config\
└── core\dna\                         # Graphify DNA system
```

**Module**: `Chimera` | **API macro**: `CHIMERA_API` | **Dependencies**: Core, CoreUObject, Engine, InputCore, EnhancedInput, PCG, AIModule, GameplayAbilities, Niagara, NiagaraCore

## The Pipeline (Primary Build Mechanism)

```
cd E:\PythonChimera\Chimera
python run_deep_space_trader_pipeline.py
```

Runs: DSL Parse → Code Generation → Build → Playtest → Report → Visual Verification.
The Pipeline is the authoritative build mechanism. MCP is for discovery when the Pipeline encounters an unknown DSL term. Once MCP discovers how to build something, it records the pathway to the Graph and—where applicable—as a DSL mapping so the Pipeline can build it directly next time.

## Spiral Growth Pattern

Complete all features in Loop N before starting Loop N+1. Each loop's verified output becomes the foundation for the next.

```
Loop 0: The Player (character, suit, lighting)          → The seed
Loop 1: The Ground (sand, rock, metal, footprints)      → Touch
Loop 2: Basic Verbs (look, step, pick up, drop, shovel) → Interaction
Loop 3: The Sky (Earth, Moon, Sun, starfield)           → Scale
Loop 4: Tools (shovel, scanner, weapon)                 → Purpose
Loop 5: Other Dots (NPCs, creatures, trade, conflict)   → Society
Loop 6: Shelter (habitat, station, base)                → Home
Loop 7: Travel (vehicles, ships, quantum jump)          → Freedom
Loop 8: Systems (economy, factions, missions)           → Consequence
Loop 9: The Universe (planets, moons, asteroids)        → Infinity
```

## Feature Ledger (60+ Features)

Tracked in Graphify. Each feature node: name, type, loop, status (`not_started` → `researching` → `verified` → `encoded`), parameters, references, iteration history.

**Full feature list**: See `docs/THE_COMPLETE_CHIMERA_DEVELOPMENT_CYCLE.md` § Feature Ledger.

## The Contract (MANDATORY)

### Pre-Flight
1. `g.query("health")` — project state
2. `g.query("pattern", your_task)` — known patterns
3. `g.query("mutation", your_task)` — past bugs
4. `g.query("gpa", "trend")` — GPA trend
5. Report findings. Only then proceed.

### Post-Flight
1. `g.mutate("phase_complete", result)` — record what happened
2. Report exact UBT output verbatim. Never summarize.
3. Update Feature Ledger. Record all MCP pathway results.
4. If GPA falling, report with corrective action.

## The Ralph Loop (Iterative Verification)

Pick feature → Research → Professor grades → Apply → Screenshot → LM Studio compares → Refine → Repeat until verified.

### Professor Review
Submit research summary to LM Studio before any MCP calls. Grade gates: A/B → proceed. C/F → return to research. Record grade via `g.mutate("professor_grade", {...})`.

### Research Depth Protocol (Gates)
Research is not complete until all gates are passed:

1. **Source Diversity** — minimum 3 source types (primary photography, technical docs, community, video, 3D scans, historical)
2. **Multi-Site Verification** — minimum 3 different domains (not pages on same site)
3. **Cross-Reference Confirmation** — 2 independent sources per parameter. If no second source exists, document absence, mark confidence Low, proceed.
4. **Failure Research** — minimum 1 source on what doesn't work (degradation, edge cases, abandoned designs)
5. **Campus Discovery** — every new source recorded via `g.mutate("research_discovery", {...})`. Uncapped. No limit.
6. **Research Summary** — source inventory, parameter table with citations, discrepancies resolved, confidence rating per parameter

Record metrics to DNA: sources_consulted, websites_visited, parameters_cross_referenced, new_campus_discoveries, failure_sources, research_confidence.

## Graphify Knowledge Graph

| Endpoint | Purpose |
|----------|---------|
| `docs/chimera_dna_graph.json` | Persistent DNA storage |
| `core/graphify_interface.py` | Query/mutate functions (`g.query`, `g.mutate`) |
| `core/dna/pattern_validator.py` | Blocks known-bad patterns before generation |
| `core/dna/auto_fixer.py` | Auto-fix brace errors |
| `core/dna/query_api.py` | FastAPI at `localhost:8766` (/dna/errors, /dna/health) |
| `dna_dashboard.py` | Streamlit dashboard |

**DNA Node Types**: Mutation, Error, Fix, Health, Pathway, FeatureUpdate, VisualVerification, ProfessorGrade, ProfessorGPA, TechnicalDiscovery, ResearchDiscovery

## MCP Pathway Rule

1. **Before any MCP call**: `g.query("pathway", "what_you_want_to_do")`
2. **Pathway exists** → follow exactly. **No pathway** → test simplest approach, record result.
3. **After every MCP call**: record as pathway_attempt mutation.

See `docs/MCP_PATHWAYS.md` for 14 working pathways with exact parameter schemas.

## Subagent Workflow

The Orchestrator compiles a context package and delegates to autonomous subagents:

1. **Context Package**: DSL block + Graph context (pathways, mutations, patterns) + reference images + campus sources + required endpoints
2. **Subagent Autonomy**: Research → Discover → Test → Record. Full authority to try 5+ parameter combinations before reporting blocked.
3. **Report Back**: Feature status update (verified/blocked) + what was discovered + what was recorded to Graph + what DSL mappings were created
4. **Discovery Recording**: Every new MCP pathway, research source, parameter set → recorded to Graph. If applicable → DSL mapping created so Pipeline can build it next time.

## Recursive Self-Improvement

Unknown MCP action → try 5+ parameter combos → record all attempts → spawn technical_research → move to next feature. When solved: record pathway → unblock features → next agent inherits discovery. Never ask for human help. Never mark "requires manual steps."

## Critical Technical Reminders

### Screenshots for Verification
**NEVER use MCP `control_editor.screenshot`.** It captures UI chrome, not the viewport. MCP `editor_viewport` mode captures the full editor window with overlays. MCP `game_viewport` mode uses the default pawn camera (not your placed CameraActor). Both produce small (1048x462) low-resolution images.

**Use `pyautogui.screenshot()` only.** Steps:
1. `powershell "$wshell=New-Object -ComObject wscript.shell; $wshell.AppActivate('Unreal Editor'); Start-Sleep 2"`
2. `python -c "import pyautogui; pyautogui.screenshot('path.png')"`
3. Verify file size > 100000 bytes
4. Send to LM Studio

If the UE5 viewport renders black after MCP operations, reset with:
- `control_editor.set_view_mode("Lit")`
- `control_editor.set_game_view(enabled=False)`
- `control_editor.focus_actor("VerificationItem_Current")`

### Material Parameters via MCP
- `manage_asset.add_vector_parameter` creates **orphaned nodes** — NOT connected to material output pins
- `manage_asset.add_scalar_parameter` also creates **orphaned nodes**
- **Correct approach**: Use `system_control.execute_python` with single-line UE Python.
- The `execute_python` handler crashes on multi-line scripts at line ~22 — ALL code must be single-line semicolon-separated.

### Automatic Research Scheduling
After 2 failed attempts on any feature, automatically create a technical_research task in the Feature Ledger, record pathway_attempt mutations, and move to the next feature. See `Chimera/ORCHESTRATOR_PROMPT.md` § AUTOMATIC RESEARCH SCHEDULING. Future agents must query technical_research tasks before starting work.

## Known Fixed Bugs

| # | Bug | Template | Fix | Category |
|---|-----|----------|-----|----------|
| 1 | Stale directories | build_orchestrator | Single canonical path | module_dependency |
| 2 | DEEPSPACETRADER_API | game_code_generator | CHIMERA_API | macro_error |
| 3 | AIController.h | build_orchestrator | Added AIModule | include_path |
| 4 | NiagaraFunctionLibrary.h | build_orchestrator | Added NiagaraCore | include_path |
| 5 | PCGVolume.h path | game_code_generator | Remove PCG/ prefix | include_path |
| 6 | Missing BeginPlay `}` | game_code_generator | Added closing brace | brace_mismatch |
| 7 | Duplicate code | game_code_generator | Replaced template | brace_mismatch |
| 8 | TickComponent/Tick mismatch | game_code_generator | Fixed to Tick(float) | signature_error |
| 9 | PCGVolumeManager APIs | game_code_generator | Removed runtime calls | module_dependency |
| 10 | GameMode redefinition | game_code_generator | Added scoping braces | signature_error |
| 11 | TEXT() dereference | game_code_generator | Removed stray `*` | macro_error |
| 12 | DockingComponent ctor | game_code_generator | Added empty ctor body | signature_error |

## Key File Paths

| File | Purpose |
|------|---------|
| `docs/THE_COMPLETE_CHIMERA_DEVELOPMENT_CYCLE.md` | Full methodology, 13 schools, phases |
| `docs/chimera_dna_graph.json` | DNA graph (mutations, pathways, features) |
| `docs/MCP_PATHWAYS.md` | Working MCP tool sequences |
| `core/graphify_interface.py` | `g.query()` / `g.mutate()` interface |
| `core/game_generation_orchestrator.py` | Pipeline orchestrator |
| `run_deep_space_trader_pipeline.py` | Pipeline entry point |
