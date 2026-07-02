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

## DNA System (Graphify)

The Graphify knowledge graph records every compilation result, every fix, and every mutation. It gets smarter with every build.

### Modules
- **Storage**: `E:\PythonChimera\Chimera\docs\chimera_dna_graph.json`
- **Modules**: `E:\PythonChimera\Chimera\core\dna\`
- **Dashboard**: `E:\PythonChimera\Chimera\dna_dashboard.py`
- **API**: FastAPI at `localhost:8766`

### Components
- `mutation_logger.py` — Records every compilation result as a mutation node with error signatures
- `pattern_validator.py` — Queries DNA for known-bad patterns before code generation; blocks known bugs from repeating
- `auto_fixer.py` — Detects and fixes brace errors in generated files, records mutations
- `continuous_verification.py` — Hourly health checks via APScheduler
- `query_api.py` — FastAPI endpoints: `/dna/errors`, `/dna/health`, `/dna/template/{name}/history`
- `dashboard.py` — Streamlit web app: mutations, error trends, fragile templates, graph visualization

### DNA Schema
Every entry follows this structure:
- **Mutation Node**: error_signature, template_file, error_category, fix_description, compilation_result
- **Error Node**: error_message, template_file, is_recurring flag
- **Fix Node**: error_id, template_file, fix_description, categories
- **Health Node**: status, details, timestamp

## Six Improvements

1. **Static Analysis** — Pre-compilation C++ file analysis for brace matching, paren matching, API macro validation, truncated file detection
2. **Snapshot Testing** — Diff generated output against saved snapshots to detect regressions
3. **Property Tests** — Generative testing of DSL parser for valid/invalid inputs
4. **Template Validation** — Pattern validator checks templates against DNA before generation; blocks known-bad patterns
5. **Differential Testing** — Generated code validated against UE5 reference patterns
6. **Incremental Regeneration** — Knowledge-graph-driven regeneration of only affected components when DSL changes

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
