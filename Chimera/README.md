# Chimera — DSL-Driven Game Generation Orchestrator for UE 5.8

Chimera takes a formal DSL specification describing a complete video game and transforms it into a compilable, packaged Unreal Engine 5 project through an automated 7-stage pipeline. It is a deterministic compiler that translates structured specifications into engine-ready C++ and assets.

## Current Status

**Build: Zero errors. 38 generated files compiled successfully.**

- Module: `Chimera` (API macro: `CHIMERA_API`)
- UE 5.8, C++20, Visual Studio 2022
- All template bugs fixed, includes resolved, dependencies satisfied
- DNA knowledge graph recording all mutations and fixes

## Quick Start

### Full Pipeline

```powershell
cd E:\PythonChimera\Chimera
python run_deep_space_trader_pipeline.py
```

Runs: DSL parse → Asset generation → Code generation → Build → Playtest → Report

### DNA System

```powershell
# Dashboard
streamlit run E:\PythonChimera\Chimera\dna_dashboard.py

# Query API
cd E:\PythonChimera\Chimera\core\dna
uvicorn query_api:app --host localhost --port 8766
```

## Key Paths

| Path | Purpose |
|---|---|
| `Chimera.uproject` | The one and only uproject |
| `Source\Chimera\` | Module root |
| `Source\Chimera\ProceduralGenerated\` | All generated game code |
| `Source\Chimera\Chimera.Build.cs` | Do NOT regenerate |
| `core\` | Pipeline components |
| `core\dna\` | Graphify DNA knowledge graph |
| `tests\dsl_grammar\` | DSL specification files |
| `docs\chimera_dna_graph.json` | Persistent DNA storage |

## Architecture

### 7-Stage Pipeline

1. **Parse & Validate** — DSL grammar parsing, ANTLR4 validation, cross-block reference tracking
2. **Asset Generation** — Images, meshes, audio via provider interface
3. **Code Generation** — C++ headers/sources, data tables, config files
4. **Integration & Build** — UBT compilation, static analysis, auto-fixing
5. **Automated Playtest** — UE automation framework behavioral tests
6. **Report & Refine** — Validation reports, DSL patch generation
7. **Regenerate & Iterate** — Incremental regeneration from knowledge graph

### DNA System (Graphify)

The Graphify knowledge graph records every compilation result, every fix, and every mutation. It gets smarter with every build:

- **Mutation Logger** — Records template fixes as mutation nodes with error signatures
- **Pattern Validator** — Queries DNA for known-bad patterns before generation
- **Auto-Fixer** — Detects and fixes brace errors, records mutations
- **Continuous Verification** — Hourly health checks via APScheduler
- **Query API** — FastAPI server at `localhost:8766`
- **Dashboard** — Streamlit web app showing mutation history and health

### DSL Blocks Supported

`game`, `game_settings`, `narrative`, `gameplay`, `crafting_systems`, `world`, `ui`, `audio`, `technical`, `art_direction`, `celestial`, `flight_model`, `ship_systems`, `economy`, `quantum_travel`, `planet_generation`, `tests`

## Dependencies

Build.cs modules: `Core`, `CoreUObject`, `Engine`, `InputCore`, `EnhancedInput`, `PCG`, `AIModule`, `GameplayAbilities`, `Niagara`, `NiagaraCore`
