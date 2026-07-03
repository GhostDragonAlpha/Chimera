# Chimera Project — Build Documentation

## Canonical Project Structure

The Chimera project lives at a single canonical path:

```
E:\PythonChimera\Chimera\
├── Chimera.uproject                          # The one and only uproject
├── Source\Chimera\                           # Module root
│   ├── Chimera.Build.cs                      # Module build file (do NOT regenerate)
│   ├── Chimera.Target.cs                     # Game target
│   ├── ChimeraEditor.Target.cs               # Editor target
│   └── ProceduralGenerated\                  # All generated game code
│       ├── Combat\
│       ├── AI\
│       ├── Flight\
│       ├── PCG\
│       ├── Stations\
│       ├── Missions\
│       ├── Factions\
│       ├── Save\
│       ├── GameMode\
│       ├── Ships\
│       └── Scripts\
├── Content\Levels\                           # Level assets
├── Config\                                   # Engine.ini / Game.ini
└── core\dna\                                 # Graphify DNA system
```

## Stale Directories (DELETED)

These were removed during directory consolidation:
- `GeneratedProject/` — deleted
- `GeneratedProjects_DeepSpaceTrader/` — deleted
- `GeneratedProjects_SpaceTrader/` — deleted
- `GeneratedProjects_TDD/` — deleted
- `generated_projects/` — deleted

## Build Pipeline

Run the full pipeline:
```
cd E:\PythonChimera\Chimera
python run_deep_space_trader_pipeline.py
```

This runs: DSL parse → Code generation → Build → Playtest → Report

## Build Configuration

- **Module name**: `Chimera` (from Chimera.uproject)
- **API macro**: `CHIMERA_API`
- **Private include paths**: All `ProceduralGenerated/*` subdirectories

### Build.cs Dependencies
```
Core, CoreUObject, Engine, InputCore, EnhancedInput, PCG, AIModule,
GameplayAbilities, Niagara, NiagaraCore
```

### Build.cs Include Paths
```
Chimera/ProceduralGenerated/Combat, AI, Flight, PCG, Stations, Missions,
Factions, Save, GameMode, Ships
```

---

## The Complete Development Cycle (Master Workflow)

All agents MUST follow the workflow defined in `docs/THE_COMPLETE_CHIMERA_DEVELOPMENT_CYCLE.md`. This document defines:

- **13 Schools** — Education phase teaching principles from real-world references
- **6 Phases** — Foundation → Research → Apply & Verify → Integration → Polish → Release
- **Spiral Growth Pattern** — Complete Loop N before starting Loop N+1
- **Feature Ledger** — Tracks all features across loops with status, parameters, verification history
- **Ralph Loop** — Iterative build → screenshot → compare → record → refine cycle
- **The Contract** — Pre-flight/post-flight checklist for every MCP call

---

## MCP Pathway Query Rule (MANDATORY)

### Before ANY MCP Call:

1. **Query Graphify**: `g.query("pathway", "what_you_want_to_do")`
   - Examples: `g.query("pathway", "create_material")`, `g.query("pathway", "spawn_point_light")`
   
2. **If pathway exists**: Follow it exactly. Do not deviate. Do not experiment.

3. **If pathway does NOT exist**:
   - Report: "No pathway found for [task]"
   - Use `manage_tools` → `list_tools` to find tools that might work
   - Test the simplest possible approach
   - If it works: record the pathway in Graphify for future use
   - If it fails: record the failure, try next approach

4. **After ANY MCP call**: Record result in DNA graph as a mutation node with pathway name, success/failure status, and error message if any.

See `docs/MCP_PATHWAYS.md` for all 12 working pathways (11 verified + 1 newly discovered).
See `docs/MCP_TOOL_INVENTORY.md` for complete tool reference with parameter schemas.

---

## DNA System (Graphify Knowledge Graph)

The Graphify knowledge graph records every compilation result, every fix, and every mutation. It connects to every pipeline component and gets smarter with each iteration.

### Current State
- **DNA Nodes**: 459 (growing with each iteration)
- **DNA Edges**: 325+
- **MCP Pathways**: 12 working pathways recorded
- **Feature Ledger Entries**: 56 features across 10 spiral loops (Loop 0–9)

### Storage & Components
| File | Purpose |
|------|---------|
| `docs/chimera_dna_graph.json` | Persistent DNA storage — nodes and edges graph |
| `core/graphify_interface.py` | Graphify interface module defining load/save/query/mutate functions |
| `core/dna/mutation_logger.py` | Records compile results as mutation nodes with error signatures |
| `core/dna/pattern_validator.py` | Queries DNA for known-bad patterns before code generation |
| `core/dna/auto_fixer.py` | Detects brace errors, attempts fixes, records mutations |
| `core/dna/continuous_verification.py` | Hourly health checks via APScheduler |
| `core/dna/query_api.py` | FastAPI server at `localhost:8766` with `/dna/errors`, `/dna/health` endpoints |
| `dna_dashboard.py` | Streamlit dashboard showing mutations, error trends, fragile templates |

### DNA Schema
Every entry follows this structure:
- **Mutation Node**: error_signature, template_file, error_category, fix_description, compilation_result
- **Error Node**: error_message, template_file, is_recurring flag
- **Fix Node**: error_id, template_file, fix_description, categories
- **Health Node**: status, details, timestamp
- **Pathway Node**: name, tool, action, params_schema, result, description (NEW — records MCP pathways)
- **FeatureUpdate Node**: feature_name, loop, status, parameters, lm_studio_assessment, iteration_count (NEW — tracks verification progress)
- **VisualVerification Node**: task_name, screenshot_path, focus_area, lm_studio_response, status (NEW — stores LM Studio feedback)

---

## Six Improvements

1. **Static Analysis** — Pre-compilation C++ file analysis for brace matching, paren matching, API macro validation, truncated file detection
2. **Snapshot Testing** — Diff generated output against saved snapshots to detect regressions
3. **Property Tests** — Generative testing of DSL parser for valid/invalid inputs
4. **Template Validation** — Pattern validator checks templates against DNA before generation; blocks known-bad patterns
5. **Differential Testing** — Generated code validated against UE5 reference patterns
6. **Incremental Regeneration** — Knowledge-graph-driven regeneration of only affected components when DSL changes

---

## Known Fixed Bugs and Their Mutations

| # | Bug | Template | Fix | Error Category |
|---|-----|----------|-----|----------------|
| 1 | Stale directories proliferating | build_orchestrator | Consolidated to single canonical path | module_dependency |
| 2 | DEEPSPACETRADER_API vs CHIMERA_API | game_code_generator | Changed all to CHIMERA_API | macro_error |
| 3 | AIController.h not found | build_orchestrator | Added AIModule to Build.cs | include_path |
| 4 | NiagaraFunctionLibrary.h not found | build_orchestrator | Added NiagaraCore to Build.cs | include_path |
| 5 | PCGVolume.h path wrong | game_code_generator | Fixed to PCGVolume.h (no PCG/ prefix) | include_path |
| 6 | Board_Trader_Vessel_Alpha missing BeginPlay `}` | game_code_generator | Added closing brace | brace_mismatch |
| 7 | SystemDamageComponent duplicate code | game_code_generator | Replaced entire template | brace_mismatch |
| 8 | Projectile TickComponent vs Tick mismatch | game_code_generator | Fixed to Tick(float); replaced GetMovementComponent | signature_error |
| 9 | PCGVolumeManager broken PCG runtime APIs | game_code_generator | Removed UPCGRuntime/SetPCGGraph calls | module_dependency |
| 10 | GameMode GraphAsset redefinition | game_code_generator | Added scoping braces | signature_error |
| 11 | *TEXT() format string dereference | game_code_generator | Removed stray `*` from UE_LOG | macro_error |
| 12 | DockingComponent missing constructor | game_code_generator | Added empty constructor body | signature_error |

---

## Current Project State (Phase 2 — Apply & Verify)

### Verified Features (Loops 0–2)
- **Player_Character_Lighting** ✓ — Three-point lighting matches NASA reference
- **Ground_Sand_Surface** ✓ — PBR material with correct color (#8B7D6B), roughness (0.9), metallic (0.05), normal map for micro-topography
- **Verb_Look** ✓ — Camera FOV 90°, pitch 0° (level with eyes), distance ~2m

### Needs Refinement (Loops 0–2)
- **Player_Character_Suit** ⚠ — PBR fabric correct; visor needs layered material (clear polycarbonate substrate + thin gold top layer) for spectral/thin-film shader
- **Player_Character_Model** ⚠ — Still using sports car body placeholder; needs proper astronaut mesh
- **Ground_Rock_Surface** ⚠ — Material applied but cone mesh scale/polygon count needs adjustment
- **Ground_Metal_Surface** ⚠ — Material applied but needs procedural dust-accumulation mask

### Next Steps
1. Complete suit refinement (layered visor material)
2. Replace player placeholder with proper astronaut mesh
3. Adjust rock patch scale and add normal maps
4. Add dust accumulation mask to metal surface
5. Advance to Loop 3 (Sky) research once Loops 0–2 are verified
