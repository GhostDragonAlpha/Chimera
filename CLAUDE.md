# Chimera — Project Manual

> DSL-Driven Game Generation Orchestrator for Unreal Engine 5.8.
> Takes a formal DSL spec → generates compilable UE5 C++ + assets through a 7-stage automated pipeline.
> **MANDATORY GATES** at every stage. No fallback ladders. No silent continuation.

> **Less capable model or unsure?** Follow `E:\PythonChimera\SUCCESSOR_RUNBOOK.md` EXACTLY — recipes, not principles. Improvise nothing.

## NEW AGENT? START HERE (in order)
1. `cd E:\PythonChimera\Chimera` then `python -m core.preflight` — live state: graph health, GPA, loop board, pending research, last run, environment, **and section [4.5]: the previous generation's Will, open phantom pains, and Dream Report candidates awaiting the human**.
2. Read `E:\PythonChimera\task_progress.md` — session handoff log; the top **NEXT** section is your work list.
3. Work under the Contract: typed recording only (`record_*` helpers), fix generator templates never generated C++, and answer the Frame Audit (`Chimera/docs/RESULT_GRADING_RUBRIC.md`) before declaring anything complete.
4. Finish with `python -m core.postflight --phase "..." --result "<UBT verbatim>" --inheritance "<=3 sentences" --phantom-pain "..." --pain-verdict "<id>:confirmed|refuted|still-open"` and update `task_progress.md` for the next agent.

## Generation Protocol (Circadian rhythm — see docs/GENERATION_PROTOCOL.md)
- **Capture surprises live**: on any human correction, dead-end, or expectation violation, run `python -m core.graphify_record surprise --context "..." --reality "..." --source human|agent|engine`. These feed the nightly distiller.
- **Fork before researching a feature** (preferred): `python -m core.spiral_forks --feature X --use-lm` — 3 briefs (conservative/alternative/wild), winner proceeds, losers' autopsies are recorded tuition. Forks never touch live state.
- **Dream loop** (`python -m core.dream_loop`, manual or scheduled): distills failures+surprises into ≤2 candidate heuristics per night, staged in `docs/PENDING_HEURISTICS.md`.
- **The human Gardener approves EVERY heuristic** before promotion (gate / CLAUDE.md rule / MCP_PATHWAYS trap). Pending = inert. Vetoed entries stay as tombstones. Promote approved ones via `python -m core.graphify_record heuristic ...` and set status `promoted`.
- **The human observation is the true collapse**: `verified` is only the system's preliminary measurement. Every system-finalized feature enters the Observation queue (preflight [4.5]) until the human records `observe --verdict accepted|rejected`. Agents NEVER record observations themselves — accepted → `observed` (truly done), rejected → `needs_refinement` with the human's notes as first-priority dream fodder. Loops show `[DONE*]` until observed.
- Graph hygiene: `python -m core.graph_compactor --dry-run` (archive-never-delete; apply is always manual).

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
| `core/result_grader.py` | Rubric-based result grading (zero LM dependency) — the gate |
| `core/telemetry_probe.py` | Crash/fps/soak evidence + `MCPStdioClient` (the MCP tool-call helper) |
| `core/heuristic_distiller.py` | Nightly failure/surprise clustering → PENDING_HEURISTICS.md |
| `core/dream_loop.py` | Circadian consolidation orchestrator (distill + compact preview + Dream Report) |
| `core/spiral_forks.py` | Bounded sacrificial research forks (3, one wild) |
| `core/graph_compactor.py` | Archive-never-delete graph hygiene |
| `core/dna/` | Graphify DNA knowledge graph interface |
| `tests/dsl_grammar/` | DSL specification files |
| `docs/chimera_dna_graph.json` | DNA graph storage |
| `docs/GENERATION_PROTOCOL.md` | The circadian rhythm spec (Dawn/Day/Observation/Dusk/Night) |
| `docs/PENDING_HEURISTICS.md` | Gardener's queue (human approves every constitution change) |
| `docs/DREAM_REPORT.md` | Morning briefing (regenerated nightly) |
| `docs/MCP_PATHWAYS.md` | Proven MCP pathways + TRAPS |
| `Plugins/McpAutomationBridge/` | UE-side MCP plugin |

## Verification & Measurement (current regime — see docs/RESULT_GRADING_RUBRIC.md)

**The gate is the RESULT grade**: `core/result_grader.py` scores measured evidence
(in-engine tests × declared-criteria coverage, telemetry, agent-judged checklist, spec
fidelity) with **zero LM dependency**. A ≥90 · B ≥75 · C ≥60 · F <60; C/F → back to
research with the study guide. Build failure auto-grades F.

Evidence layers (in order of authority):
| Layer | Method | Notes |
|---|---|---|
| Engine state hard facts | MCP queries: read-backs, bounds, transforms, actor lists | Deterministic; the workhorse |
| Telemetry | `python -m core.telemetry_probe --soak 30` | crash-free log, fps vs target, growth — **measure FOREGROUNDED** (background throttle freezes fps AND all Niagara/anim simulation) |
| MCP screenshot | `control_editor screenshot mode=editor_viewport` | Never desktop captures |
| LM text/vision (qwen3.6) | tertiary evidence only, when explicitly requested | `gate_lm_available` applies only to explicitly-requested vision layers |
| **Human observation** | `graphify_record observe` | **The true collapse** — `verified` is the system's preliminary measurement; features finish only under the human's eyes |

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

### Generation Protocol (circadian — full spec: docs/GENERATION_PROTOCOL.md)
```powershell
python -m core.spiral_forks --feature X --use-lm      # 3 research forks, winner proceeds
python -m core.graphify_record surprise --context "..." --reality "..." --source human
python -m core.graphify_record observe --feature X --verdict accepted|rejected --notes "..." --loop N   # HUMAN ONLY
python -m core.dream_loop                             # nightly: distill <=2 candidates + Dream Report
python -m core.heuristic_distiller --dry-run          # inspect clusters without staging
python -m core.graph_compactor --dry-run              # archive preview (apply is manual)
python -m core.result_grader --feature X --evidence ev.json
python -m core.telemetry_probe --out t.json --soak 30
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
