# Chimera — Project Manual

> DSL-Driven Game Generation Orchestrator for Unreal Engine 5.8.
> Takes a formal DSL spec → generates compilable UE5 C++ + assets through a 7-stage automated pipeline.
> **MANDATORY GATES** at every stage. No fallback ladders. No silent continuation.

## Architecture Overview

```
DSL Spec → Parse → Asset Gen → Code Gen → Build → Playtest → Scene Verify → Record
                          ↕                          ↕
                    Graphify Knowledge Graph    MCP (chiR24 + Unreal)
```

**Hard gates at every transition.** If a gate fails, exit code 1. Pipeline halts.

## Key Concepts

- **Spiral Loop** — Iterative development: Research → Design → Implement → Test → Verify → Record
- **Contract** — Master workflow at `docs/THE_COMPLETE_CHIMERA_DEVELOPMENT_CYCLE.md`
- **DNA Graph** — Persistent graph at `docs/chimera_dna_graph.json`; records every mutation, build, verification
- **ProfessorGPA** — Quality metric (0.0–4.0). Auto-grades F on build failure, C on verification failure
- **Pre-Flight / Post-Flight** — `python -m core.preflight` and `python -m core.postflight`
- **Scene Verification** — 4 mandatory layers (see below)

## Key Paths

| Path | Purpose |
|---|---|
| `Chimera.uproject` | UE5 project (Engine 5.8) |
| `Source/Chimera/ProceduralGenerated/` | All generated game code (do NOT hand-edit) |
| `core/` | Pipeline components (Python) |
| `core/gates.py` | Mandatory hard gate definitions |
| `core/scene_verifier.py` | 4-layer vision-free scene verification via MCP |
| `core/dna/` | Graphify DNA knowledge graph interface |
| `core/mcp_client.py` | MCP tool call helper |
| `tests/dsl_grammar/` | DSL specification files |
| `docs/chimera_dna_graph.json` | DNA graph storage |
| `Plugins/McpAutomationBridge/` | UE-side MCP plugin |

## Mandatory Scene Verification (4 Layers)

Stage 7 of the pipeline runs 4 mandatory layers. ALL must pass. NO fallback.

| Layer | Method | What it checks | Model |
|---|---|---|---|
| 1 | Engine state hard facts | World loaded, ≥5 actors, lights, viewport >100px, screenshot >100KB | Deterministic |
| 2 | MCP screenshot capture | UE viewport render saved to disk | `control_editor screenshot` |
| 3 | LM text reasoning | qwen3.6 analyzes structured engine data | `qwen3.6-35b-a3b-mtp@iq2_m` |
| 4 | LM vision analysis | qwen3.6 analyzes screenshot via multimodal vision | `qwen3.6-35b-a3b-mtp@iq2_m` |

All four are mandatory. No layer can be skipped or timed out to a lesser substitute. The pipeline blocks until all four return PASS or the wall clock expires.

## Pipeline Commands

### Full pipeline
```powershell
cd E:\PythonChimera\Chimera
python run_deep_space_trader_pipeline.py
```

### Pre-Flight / Post-Flight
```powershell
python -m core.preflight       # Prints health, GPA, loop board, build trend
python -m core.postflight --phase "..." --result "..."
```

### Individual stages
```powershell
python core/dsl_game_parser.py
python core/asset_generator.py
python core/game_code_generator.py
python core/build_orchestrator.py
python core/playtest_runner.py
```

### DNA / Graphify
```powershell
python -m core.graphify_record feature --name X --loop 8 --status verified
python fix_dna_key_mismatch_pollution.py
cd core/dna && uvicorn query_api:app --host localhost --port 8766
```

### Build with UBT directly
```powershell
& "C:/Program Files/Epic Games/UE_5.8/Engine/Build/BatchFiles/Build.bat" ChimeraEditor Win64 Development "E:\PythonChimera\Chimera\Chimera.uproject" -waitmutex
```

## MCP Tools

| Server | Type | Purpose |
|---|---|---|
| `chiR24-unreal-mcp` | stdio | UE editor control, actor queries, screenshots |
| `graphify` | stdio | Knowledge graph queries/mutations |
| `playwright` | HTTP (port 8342) | Browser automation |

Key tools:
- `control_editor screenshot mode=editor_viewport filename=...` — viewport render
- `inspect` action=`get_scene_stats`, `get_viewport_info`, `runtime_report`, `get_performance_stats`
- `control_actor` action=`find_by_class` — query actors by UE class name

## Mandatory Gates (core/gates.py)

| Gate | Enforces | Severity |
|---|---|---|
| `gate_no_junk_nodes` | Zero unknown_* junk in graph | BLOCKER |
| `gate_gpa_not_critically_falling` | Cumulative GPA ≥ 1.0 | BLOCKER |
| `gate_no_stale_trees` | Only Chimera/ under Source/ | BLOCKER |
| `gate_build_succeeded` | UBT must return 0 | BLOCKER |
| `gate_playtest_no_failures` | Zero test failures before Stage 7 | BLOCKER |
| `gate_lm_available` | qwen3.6 must be loaded | BLOCKER |
| `stage_7_visual` | All 4 scene verification layers must pass | BLOCKER |

### Exit code contract
- **0**: Pipeline complete, all gates passed
- **1**: Gate violation — pipeline blocked, cannot proceed
- **2**: Unexpected error

## Agent Modes Available

| Mode | Command | Purpose |
|---|---|---|
| Code | `skill code` | Full-access software engineering |
| Debug | `skill debug` | Systematic troubleshooting |
| Architect | `skill architect` | System design & planning |
| UE5 | `skill ue5` | UE5 C++ component development |
| Ask | `skill ask` | Read-only research |
| Orchestrate | `skill orchestrate` | Multi-agent workflow coordination |

## Project Conventions

- **C++**: UE 5.8, C++20, `CHIMERA_API` macro, Visual Studio 2022
- **Development flows top-down**: game content changes go in the DSL spec (`tests/dsl_grammar/deep_space_trader.chimera`); code-shape changes go in the generator (`core/game_code_generator.py`); the pipeline regenerates the C++.
- **Generator-owned files** (regenerated every pipeline run — hand-edits WILL be clobbered; fix the generator template instead): Flight, Ship, GameMode, PCGVolumeManager, MissionData/MissionComponent, Docking, QuantumTravel, FactionComponent, Economy (CommodityData/EconomyManager/StationTradingData), DeepSpaceTraderSaveGame/SaveGameComponent, Weapon/Projectile/Shield/Damage/SystemDamage/CombatTarget, PirateAIController + behavior tree.
- **Loop-built manual files** also live under `ProceduralGenerated/` (Tools, Interactions, Sound, UI, NPC AI, ChimeraMovementComponent, StationActor): no template exists, hand-edits are safe. When touching one substantively, migrate it under generator ownership (add a `generate_*` method) first.
- **Do NOT edit** `Chimera.Build.cs` — regenerate instead
- **Always record build results** to DNA graph (success AND failure with UBT output)
- **Pre-Flight** before running pipeline: `python -m core.preflight`
- **Post-Flight** after pipeline: `python -m core.postflight`
- **Never write mutation detail dicts by hand** — use `record_feature`/`record_pathway`/`record_loop`/`record_phase`/`record_grade`/`record_build` helpers

## Common Troubleshooting

### Pipeline blocked by gate
Run `python -m core.preflight` to see current state. Check which gate is failing. Fix the condition, re-run.

### Build fails — DLL locked
The pipeline auto-detects running UE Editor, closes it, builds, then restarts UE. If this fails, close UE manually and re-run.

### Scene verification fails
Layer 1 (engine hard facts): the level may be empty or missing required actors.
Layer 4 (vision): the rendered viewport may show a greybox/empty level — spawn required actors before verification.
All layers are mandatory and non-skippable.

### DNA key pollution
Run `python fix_dna_key_mismatch_pollution.py` to quarantine junk nodes.
Use typed helpers (`record_*`) to prevent future pollution.

## Session Memory

Stored at: `C:\Users\allen\.claude\projects\E--PythonChimera\memory\`
Indexed in `MEMORY.md` there.
