# Chimera — Agent-Developed Game Factory (UE 5.8)

**No humans write code here.** Agents are the only developers. This README is an agent
entry point: a formal DSL spec is compiled into UE5 C++ and assets by a generator
pipeline, measured by automation tests and telemetry, graded against an industry-standard
rubric, and iterated until verified. The workflow below is the project.

## START HERE (every session, any agent)

1. `cd E:\PythonChimera\Chimera` → `python -m core.preflight` — live state: graph health, GPA, spiral loop board, pending research, last run, environment.
2. Read `E:\PythonChimera\task_progress.md` — session handoff; the top **NEXT** section is your work list.
3. Execute THE WORKFLOW below. Nothing else is the process.
4. Finish: `python -m core.postflight --phase "..." --result "<UBT verbatim>"`, update `task_progress.md`, commit + push.

## THE WORKFLOW (authoritative — one full cycle)

```
SELECT → RESEARCH (writes the exam) → APPLY (DSL/generator layer) → BUILD+GATES
      → MEASURE (tests+telemetry) → GRADE THE RESULT → verified | back to research
```

1. **SELECT** — next open feature in the lowest incomplete Spiral loop (the preflight board). Never skip forward.
2. **RESEARCH WRITES THE EXAM** — research the feature (campus sources + web, Research Depth Protocol in `Chimera/docs/THE_COMPLETE_CHIMERA_DEVELOPMENT_CYCLE.md`). The output is the feature's **declared acceptance criteria** — the coverage denominator the grade is computed against — plus buildable parameters. Record everything with the typed helpers (`record_*` / `python -m core.graphify_record`); mis-keyed dicts are rejected.
3. **APPLY AT THE RIGHT LAYER** — game content → the DSL (`Chimera/tests/dsl_grammar/deep_space_trader.chimera`); code shape → generator templates (`Chimera/core/game_code_generator.py`). **Never hand-edit generator-owned C++** (Flight, Ship, GameMode, PCG, Missions, Docking, QuantumTravel, Factions, Economy, Save, Combat suite, PirateAI) — regeneration clobbers it.
4. **BUILD + GATES** — `python run_deep_space_trader_pipeline.py` — regenerates all generator-owned code, UBT-builds, runs mandatory hard gates (exit 1 on violation). Build failure auto-grades **F**. Stale trees under `Source/` fail the build.
5. **MEASURE** — headless, no editor window needed:
   `"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe" Chimera.uproject -ExecCmds="Automation RunTests ChimeraTests;Quit" -unattended -nullrhi -ReportExportPath=Saved/AcceptanceReport`
   plus telemetry via MCP `inspect` (scene stats, runtime report, performance).
6. **GRADE THE RESULT** — `python -m core.result_grader --feature <X> --evidence <evidence.json>` against `Chimera/docs/RESULT_GRADING_RUBRIC.md`. Score = pass_rate × declared-criteria coverage (40) + stability/perf (25) + design checklist (20) + spec fidelity (15). **No LM/model dependency.** A ≥ 90, B ≥ 75, C ≥ 60, F < 60.
7. **GATE** — A/B → `record_feature(..., "verified")`. **C/F → back to step 2** carrying the grader's study guide (lowest-scoring categories) as the research target.
8. **FRAME AUDIT** — mandatory before declaring anything complete: answer the four questions in the rubric (proxy vs target; who judges the judge; artifact vs its generator; what would look good while wrong) in the Post-Flight record.

## FILE MAP

| Need | File |
|---|---|
| Auto-loaded agent briefs | `CLAUDE.md` (Claude Code) / `AGENTS.md` (Roo, Kilo, others) |
| Session handoff + NEXT | `task_progress.md` |
| Grading rubric + frame audit | `Chimera/docs/RESULT_GRADING_RUBRIC.md` |
| Full methodology (Spiral, Contract, Ralph loop) | `Chimera/docs/THE_COMPLETE_CHIMERA_DEVELOPMENT_CYCLE.md` |
| Known-good MCP call sequences | `Chimera/docs/MCP_PATHWAYS.md` |
| DNA knowledge graph interface | `Chimera/core/graphify_interface.py` (`record_*` helpers) |

Everything below is system reference (engine setup, MCP tool inventory, build details —
parts describe the earlier vehicle-simulation framing). The workflow above is authoritative.

---

## 1. Project Overview

| Attribute | Value |
|-----------|-------|
| **Engine** | Unreal Engine 5.8 |
| **Project Type** | Vehicle Game Template (C++) |
| **Physics Scale** | Earth-scale (64-bit double-precision coordinates) |
| **Default Map** | `/Game/VehicleTemplate/Maps/VehicleBasic` |
| **Graphics RHI** | DX12, Ray Tracing enabled, Virtual Textures |
| **Project ID** | `3E9AE102425E690A6986AF96782D589C` |

### Key Design Goals

- **Earth-scale terrain**: Biome-based procedural generation with Ocean, Forest, Desert, Mountain, and Ice regions
- **Spherical gravity**: Gravitational acceleration vectors point toward planet center using inverse-square law
- **Edge wrapping**: Seamless player wrapping at landscape boundaries without pop or visual tearing
- **Celestial transitions**: Smooth interpolation between Earth and Moon gravity via Lagrange transition zones
- **Flight mode**: Vehicle thrust, strafe, pitch/yaw/roll controls for space flight simulation

---

## 2. Core Systems Summary

### Physics & Vehicles
| Component | File | Description |
|-----------|------|-------------|
| `ChimeraSportsCar` / `ChimeraOffroadCar` | `.cpp/.h` | Vehicle pawn classes with Chaos vehicles |
| `ChimeraWheelFront` / `ChimeraWheelRear` | `.cpp/.h` | Sports wheel implementations |
| `ChimeraBreakableComponent` | `Physics/` | Actor destruction and damage system |
| `ChimeraDebrisSpawner` | `Physics/` | Dynamic debris spawning on break events |
| `ChimeraRagdollController` | `Physics/` | Ragdoll activation with impact velocity |

### Flight & Celestial Systems
| Component | File | Description |
|-----------|------|-------------|
| `FlightControlComponent` | `.cpp/.h` | Flight mode toggle, thrust, strafe X/Y/Z, pitch/yaw/roll |
| `ThrustVectoringComponent` | `.cpp/.h` | Thrust nozzle angle control (pitch ±45°, yaw ±30°) |
| `SphericalGravityComponent` | `.cpp/.h` | Earth-scale gravity with 64-bit double precision math |
| `EdgeWrappingComponent` | `.cpp/.h` | Seamless boundary wrapping at landscape edges |
| `LagrangeTransitionZone` | `.cpp/.h` | Earth↔Moon transition with interpolated planet center |

### Procedural Generation & Terrain
| Component | File | Description |
|-----------|------|-------------|
| `LevelGeneratorComponent` | `.cpp/.h` | Biome terrain generation, structure placement, LOD streaming |
| `ProceduralGeneratorComponent` | `.cpp/.h` | General procedural asset generation |
| `ChimeraSculptTool` / `ChimeraPaintTool` | `Terrain/` | Terrain sculpting and painting tools |
| `ChimeraHeightMap` | `Terrain/` | Height map data management |
| `ChimeraPCGFoliage` / `ChimeraPCGSpawner` | `PCG/` | PCG-based foliage placement and spawning |

### Economy & Inventory
| Component | File | Description |
|-----------|------|-------------|
| `ChimeraWallet` | `Economy/` | Player wallet with balance tracking |
| `ChimeraShop` / `ChimeraAuctionHouse` | `Economy/` | Shop and auction systems |
| `ChimeraCurrency` | `Economy/` | Currency definitions and conversion |
| `ChimeraInventoryComponent` | `Inventory/` | Player inventory management |
| `EItemBase` / `EItemInstance` | `Inventory/` | Item definition and instance classes |

### AI & Navigation
| Component | File | Description |
|-----------|------|-------------|
| `ChimeraAIController` | `AI/` | Custom AI controller |
| `ChimeraBehaviorTreeComponent` | `AI/` | Behavior tree integration |
| `ChimeraEQSManager` / `ChimeraPerceptionSystem` | `AI/` | Environment query and perception systems |
| `ChimeraPatrolSystem` | `AI/` | Patrol route management |
| `ChimeraMassAIController` | `Mass/` | MASS AI controller for mass entity simulation |

### Weather, Water & Environment
| Component | File | Description |
|-----------|------|-------------|
| `ChimeraWeatherManager` / `ChimeraClimateSystem` | `Weather/` | Dynamic weather and climate systems |
| `ChimeraDayNightCycle` | `Weather/` | Day/night cycle management |
| `ChimeraWaterBody` / `ChimeraWaterMesh` | `Water/` | Water body definitions and mesh rendering |
| `ChimeraWaterCollision` | `Water/` | Water surface collision detection |

### Game Systems
| Component | File | Description |
|-----------|------|-------------|
| `ChimeraMissionController` / `ChimeraQuest` | `Quests/` | Mission and quest management |
| `ChimeraAchievement` / `ChimeraPrestigeSystem` | `Progression/` | Achievements and player progression |
| `ChimeraRecipeBook` / `ChimeraWorkstation` | `Crafting/` | Crafting recipes and workstations |
| `ChimeraChatSystem` / `ChimeraReputationSystem` | `Social/` | Social features including chat and reputation |
| `ChimeraGarage` / `ChimeraPartSystem` | `Customization/` | Vehicle customization and garage system |

### UI & Sequences
| Component | File | Description |
|-----------|------|-------------|
| `ChimeraHUD` / `D6HudWidget` | `UI/` + `UMG/` | Main HUD with 6DOF widget display |
| `ChimeraCombatHUD` / `ChimeraMinimap` | `UI/` | Combat HUD and minimap |
| `ChimeraCameraDirector` / `ChimeraSequence` | `Sequences/` | Cutscene camera direction and sequence playback |
| `ChimeraDialogueSystem` | `Sequences/` | Dialogue system for narrative sequences |

### Networking & Persistence
| Component | File | Description |
|-----------|------|-------------|
| `ChimeraNetDriver` / `ChimeraGameState` | `Networking/` | Custom network driver and game state replication |
| `ChimeraSaveGame` / `ChimeraCloudSync` | `Persistence/` | Save system with cloud sync support |
| `ChimeraLevelStreamer` / `ChimeraWorldPartition` | `Streaming/` | World partition streaming and LOD management |

---

## 3. MCP Automation Bridge Capabilities

The **McpAutomationBridge** plugin provides a Native HTTP transport layer exposing **37 MCP tools** for AI-driven UE Editor automation.

### Transport Configuration
- **Protocol**: JSON-RPC 2.0 over HTTP POST
- **Endpoint**: `http://localhost:3000/mcp`
- **Server**: Configured in `DefaultGame.ini` under `[McpAutomationBridgeSettings]`
- **LM Studio Endpoint**: `http://localhost:1234` (AI analysis)

### MCP Tool Categories (37 tools)

| Category | Tools | Description |
|----------|-------|-------------|
| **Editor Control** | `control_editor`, `system_control` | Play/stop PIE, screenshots, console commands |
| **Level Management** | `manage_level`, `build_environment`, `manage_geometry` | Level loading, terrain generation, geometry editing |
| **Actor Control** | `control_actor`, `inspect` | Actor manipulation and world state queries |
| **Blueprint & Assets** | `manage_blueprint`, `manage_asset`, `manage_material_authoring`, `manage_texture` | Blueprint creation, asset management, material/texture authoring |
| **Game Framework** | `manage_game_framework`, `manage_character`, `manage_combat`, `manage_gas` | Game framework, character, combat, and GAS tools |
| **AI & Behavior** | `manage_ai`, `manage_behavior_tree`, `manage_skeleton` | AI systems, behavior trees, skeleton management |
| **Environment** | `manage_lighting`, `manage_navigation`, `manage_pcg`, `manage_volume` | Lighting, navigation, PCG, volume tools |
| **UI & Sequences** | `manage_widget_authoring`, `manage_sequence`, `manage_sessions` | Widget authoring, sequence playback, session management |
| **System Tools** | `manage_input`, `manage_inventory`, `manage_networking`, `manage_performance`, `manage_pipeline`, `manage_tools` | Input, inventory, networking, performance profiling, pipeline tools |

### MCP Server Configuration (`.mcp.json`)
```json
{
  "mcpServers": {
    "unreal-engine": {
      "type": "http",
      "url": "http://localhost:3000/mcp"
    }
  },
  "instructions": "Use MCP tools to control UE Editor. Key tools for automated testing:\n- control_editor: play/stop PIE, take screenshots (full_editor_window mode), console commands\n- system_control: execute Python scripts, run profiling, send console commands\n- manage_level: load/save levels\n- inspect: query game world state"
}
```

---

## 4. Python Automation Layer

All Python scripts reside in `Chimera/Python/`. Key modules and their purposes:

### Core Infrastructure
| Script | Purpose |
|--------|---------|
| `config.py` | Central configuration (LM Studio model, paths, ports) |
| `lmstudio_client.py` | Shared LM Studio HTTP client for AI analysis |
| `utils.py` | MetricsCollector, telemetry tracking, JSON export |
| `network_utils.py` | HTTP request helpers and network utilities |

### MCP Automation
| Script | Purpose |
|--------|---------|
| `mcp_automation_client.py` | Core MCP client — session lifecycle, tool calls, batch operations, screenshot capture, AI analysis, TES verification |
| `run_mcp_test.py` | Entry point for MCP-based automated testing |
| `mcp_integration_test_runner.py` | MCP integration test runner |

### Multi-Agent System
| Script | Purpose |
|--------|---------|
| `run_multi_agent.py` | CLI entry point — spawns agents, coordinates tasks, reports results |
| `multi_agent_coordinator.py` | Core coordinator — agent lifecycle, task distribution, dependency resolution (topological sort), sync/async/parallel execution |

### Agent Roles (`Python/agent_roles/`)
| Script | Role | Capabilities |
|--------|------|-------------|
| `base_agent.py` | Base class | MCP session management, message bus communication |
| `level_designer_agent.py` | Level Designer | Terrain generation, structure placement, PCG integration |
| `vehicle_tuner_agent.py` | Vehicle Tuner | Physics tuning, vehicle spawning, flight mode testing |
| `asset_manager_agent.py` | Asset Manager | Material generation, texture creation, asset workflow |

### Testing & Validation
| Script | Purpose |
|--------|---------|
| `flight_simulation.py` / `run_flight_test.py` | Flight physics simulation and test execution |
| `flight_test_suite.py` | Comprehensive flight test suite |
| `play_test.py` | General play testing framework |
| `integration_test.py` | Integration tests across systems |
| `validation_test_suite.py` | Validation test runner |
| `tes_playthrough_script.py` / `tes_validation_reporter.py` | TES (Test Execution Suite) playthrough and reporting |
| `tes_earth_scale_analysis.py` | Earth-scale landscape verification (edge wrapping, flat-to-sphere morph) |

### Screenshot & AI Analysis
| Script | Purpose |
|--------|---------|
| `screenshot_helpers.py` | Screenshot capture and metadata management |
| `screenshot_lmstudio_workflow.py` | Full screenshot → LM Studio analysis pipeline |
| `analyze_screenshot.py` | Quick single-screenshot lift-off verification |
| `run_screenshot_analysis.py` | Flight test screenshot analysis workflow |

### Build & Project Management
| Script | Purpose |
|--------|---------|
| `build_runner.py` / `build_verification.py` | Build execution and post-build validation |
| `cpp_generator.py` | C++ code generation utilities |
| `input_binding_generator.py` | Input binding JSON generation |
| `procedural_game_generator.py` | Procedural game content generation |
| `project_status.py` | Project status reporting |
| `config_diff_utils.py` | Configuration diff utilities |
| `rate_limit_validation.py` | LM Studio rate limit validation |

### Runtime & Editor Automation
| Script | Purpose |
|--------|---------|
| `ue_editor_automation.py` | UE Editor automation scripts |
| `runtime_screenshot_playtest.py` | Runtime screenshot-based playtesting |
| `moon_celestial_automation.py` | Moon/celestial body automation |
| `wpo_material_automation.py` | World Partition material automation |
| `blueprint_controller_automation.py` | Blueprint controller automation |

### Entry Points (root-level)
| Script | Purpose |
|--------|---------|
| `run_flight_physics.py` | Simulates flight physics, generates trajectory plot, sends to LM Studio |
| `demo_6dof_workflow.py` | 6DOF workflow demonstration |
| `test_lm_studio_api.py` | LM Studio API connectivity test |

---

## 5. Multi-Agent Coordination System

### Architecture

```
run_multi_agent.py (CLI entry)
    └── MultiAgentCoordinator
            ├── AgentFactory → LevelDesignerAgent / VehicleTunerAgent / AssetManagerAgent
            ├── AgentMessageBus (inter-agent communication)
            ├── Dependency Resolver (topological sort via Kahn's algorithm)
            └── Execution Modes: sync / async / parallel
```

### Usage

```bash
# Default demo — race track scenario
python Chimera/Python/run_multi_agent.py

# Custom task description
python Chimera/Python/run_multi_agent.py --task "build a city"

# Override agent count
python Chimera/Python/run_multi_agent.py --agents 6

# Async fire-and-forget mode
python Chimera/Python/run_multi_agent.py --async

# Sequential execution (no parallelism)
python Chimera/Python/run_multi_agent.py --sequential
```

### Task Templates

The system includes pre-built task templates:

- **`build_race_track_tasks()`** — 6 subtasks: terrain generation, structure placement, material creation, texture generation, vehicle tuning, test vehicle spawning
- **`build_city_tasks()`** — 4 subtasks: city terrain, building placement, facade materials, traffic vehicles
- **`build_custom_tasks(description)`** — Generic template for any freeform description

### Agent Roles & Capabilities

| Role | MCP Tools Available | Key Capabilities |
|------|---------------------|------------------|
| `LEVEL_DESIGNER` | manage_level, build_environment, manage_geometry | Terrain generation, structure placement, PCG integration |
| `VEHICLE_TUNER` | control_actor, inspect, manage_blueprint | Vehicle tuning, physics testing, spawning |
| `ASSET_MANAGER` | manage_asset, manage_material_authoring, manage_texture | Material generation, texture creation |
| `TEST_ENGINEER` | control_actor, inspect, system_control | Test execution, validation |

### Execution Modes

| Mode | Description | Concurrency |
|------|-------------|-------------|
| **Sync** | Sequential with dependency resolution (topological sort) | 1 |
| **Async** | Fire-and-forget — await task handles separately | Unlimited |
| **Parallel** | Concurrent execution with semaphore limiting | Max 5 (configurable) |

### Progress Callbacks

```python
def on_progress(event):
    print(f"[{event.metadata.get('role', '?')}] {event.content}")

coordinator.register_progress_callback(on_progress)
```

---

## 6. Build Pipeline Instructions

### Quick Commands

```bash
cd Chimera

# Full rebuild (default)
run_build.bat build

# Incremental build (detects changes)
run_build.bat incremental

# Plugins only
run_build.bat plugins

# Post-build validation
run_build.bat validate

# Clean Intermediate, Saved, Binaries
run_build.bat clean

# Show last build status
run_build.bat status
```

### Advanced Options

```bash
# Custom target/platform/config (passed through to PowerShell)
run_build.bat build -Target ChimeraEditor -Platform Win64 -Config Development
```

### Build Pipeline Details

The pipeline is implemented in `build_pipeline.ps1` with supporting scripts:

| Script | Purpose |
|--------|---------|
| `build_pipeline.ps1` | Main pipeline orchestrator — full/incremental/plugin builds, validation, cleanup |
| `BuildScripts/BuildConfig.json` | Build configuration (targets, platforms, configs) |
| `BuildScripts/BuildLogger.ps1` | Structured build logging with JSON output to `E:\PythonChimera\build_logs\` |
| `BuildScripts\DependencyResolver.ps1` | Dependency resolution for incremental builds |

### Build Output

Logs are written to `E:\PythonChimera\build_logs\` as JSON files containing:
- Status (success/failure)
- Timestamp
- Total duration
- Error count

---

## 7. Test & TDD Infrastructure

### Pipeline Stages (7-Stage Process)

The Chimera project implements a comprehensive 7-stage game generation pipeline:

| Stage | Name | Description |
|-------|------|-------------|
| 1 | Parse & Validate DSL | Parses `.chimera` files, validates against JSON schema and ANTLR4 grammar |
| 2 | Asset Generation | Generates placeholder assets (meshes, textures, animations, sounds) via provider pattern |
| 3 | Code Generation | Generates C++ UCLASS/UPROPERTY files, UI widgets, behavior trees, replication rules |
| 4.5 | Automated Playtest | Runs UE automation tests or AI playtests to verify game logic and balance |
| 4 | Integration & Build | Assembles `.uproject`, generates `.Build.cs` and `Target.cs` with proper plugin mappings |
| 6 | Report & Refine | Generates test reports, failure suggestions, and statistical aggregations |

### TDD Test Harness Components

- **Test API** (`TestAPI.h`/`TestAPI.cpp`): Static helper class for actor lifecycle, ability system, attributes, inventory, crafting, status effects, environment, and economy operations
- **Individual Test Files**: UE automation test files using `IMPLEMENT_SIMPLE_AUTOMATION_TEST` macro
- **Test Build CS**: `{ProjectName}Tests.Build.cs` with proper module dependencies (Core, CoreUObject, Engine, AutomationTest)

### Plugin Dependency Mapping

The build orchestrator automatically maps DSL `module_dependencies` to UE plugin declarations:

```python
# Module → Plugin mapping for explicit plugin declarations
module_to_plugin = {
    "PCG": "PCG",
    "PCGGeometryScriptInterop": "PCG",
    "CommonUI": "CommonUI",
    "Niagara": "Niagara",
    "Water": "Water"
}

# Engine modules (no plugin declaration needed)
engine_modules = {
    "GameplayAbilities", "GameplayTags", "GameplayTasks", "EnhancedInput", 
    "UMG", "NetCore", "AIModule", "LevelSequence", "Core", "CoreUObject", "Engine"
}
```

### DSL Test Block Syntax

Tests are defined in the `.chimera` DSL using the `tests` block:

```chimera
tests {
    test "TestName" {
        type = "unit";
        setup {
            action = "spawn_actor"; params { id="player", type="Character" };
        }
        action {
            // Action to execute
        }
        assert {
            expr = "ability_on_cooldown(actor='player', ability='Dash')";
            operator = "=="; expected = "false";
        }
        cleanup {
            action = "destroy_actor"; params { id="player" };
        }
    }
}
```

---

## 10. Directory Structure

```
E:\PythonChimera\
├── Chimera/                          # Main UE project directory
│   ├── .mcp.json                     # MCP server configuration (port 3000)
│   ├── Chimera.uproject              # Unreal project file (UE 5.8)
│   ├── Chimera.sln / .slnx           # Visual Studio solution files
│   ├── run_build.bat                 # Build pipeline launcher
│   ├── build_pipeline.ps1            # PowerShell build orchestrator
│   ├── Config/                       # Engine configuration
│   │   ├── DefaultEngine.ini         # Renderer, graphics RHI, splitscreen settings
│   │   ├── DefaultGame.ini          # Project ID, MCP bridge settings (port 3000)
│   │   └── Backup/                   # Configuration backups
│   ├── Content/                      # Game assets and content
│   │   ├── Vehicles/                 # SportsCar, OffroadCar, PhysicsMaterials
│   │   ├── Celestial/                # Moon celestial body definitions
│   │   ├── Landscape/                # WPO material graph specifications
│   │   ├── ProceduralGenerated/Levels/  # Generated level data
│   │   ├── Blueprints/               # Blueprint assets
│   │   ├── UMG/                      # UI widgets (D6HudWidget)
│   │   └── ...                       # Audio, Characters, Input, Materials, etc.
│   ├── Source\Chimera\               # C++ source code
│   │   ├── Chimera.cpp / .h          # Main module entry point
│   │   ├── ChimeraPawn.cpp           # Player vehicle pawn
│   │   ├── ChimeraGameMode.cpp       # Game mode configuration
│   │   ├── ChimeraUI.cpp / D6HudWidget.cpp  # UI system
│   │   ├── AI/                       # AI controllers, behavior trees, EQS, perception
│   │   ├── Economy/                  # Wallet, shop, auction house, currency
│   │   ├── Physics/                  # Breakable, debris spawner, ragdoll controller
│   │   ├── Terrain/                  # Height maps, sculpt/paint tools
│   │   ├── PCG/                      # PCG foliage and spawning
│   │   ├── Weather/                  # Weather manager, climate, day/night cycle
│   │   ├── Water/                    # Water bodies, meshes, collision
│   │   ├── Quests/                   # Missions, quests, rewards
│   │   ├── Inventory/                # Inventory, items, loot tables
│   │   ├── Progression/              # Achievements, player levels, prestige
│   │   ├── Crafting/                 # Recipes, skills, workstations
│   │   ├── Social/                   # Chat, emotes, friends, reputation
│   │   ├── Combat/                   # Weapons, hitboxes, damage types
│   │   ├── Navigation/               # Radar, route planner, waypoints
│   │   ├── Customization/            # Garage, parts, performance meter
│   │   ├── UI/                       # HUDs, menu system, minimap
│   │   ├── Sequences/                # Camera director, dialogue, sequences
│   │   ├── VFX/                      # Combat and environment visual effects
│   │   ├── Particles/                # Hit effects, trail systems
│   │   ├── Mass/                     # MASS entity system for debris/AI
│   │   ├── StateTree/                # Custom state tree (combat/patrol states)
│   │   ├── Streaming/                # Level streaming, LOD manager, world partition
│   │   ├── Persistence/              # Save game, cloud sync, compression
│   │   ├── Networking/               # Net driver, game state, replication
│   │   ├── Audio/                    # Vehicle audio, ambient, combat audio
│   │   ├── Animation/                # Blend spaces, control rig, IK solver
│   │   ├── VehicleAI/                # Path following, race manager, racing lines
│   │   ├── Debug/                    # Console commands, debugger components
│   │   ├── Input/                    # Input manager and mapping
│   │   ├── Config/                   # Audio settings, game settings, input settings
│   │   ├── McpRuntimeBridgeComponent.cpp  # MCP command registration and execution
│   │   ├── McpPhysicsBridge.cpp      # Physics commands (break, ragdoll, debris, force)
│   │   ├── McpLevelGenerator.cpp     # Level generation via MCP
│   │   ├── McpEconomyBridge.cpp      # Economy commands (buy, sell, auction, currency)
│   │   └── ...                       # 90+ C++ files across all subsystems
│   ├── Plugins\McpAutomationBridge/  # MCP automation plugin
│   │   ├── McpAutomationBridge.uplugin  # Plugin definition (Editor target)
│   │   ├── Source\...Private\MCP\Tools\  # 37 MCP tool implementations
│   │   └── Config\                   # Plugin configuration
│   ├── Python/                       # Python automation layer (40+ scripts)
│   │   ├── agent_roles/              # Specialized AI agent classes
│   │   ├── mcp_automation_client.py  # Core MCP client with batch operations
│   │   ├── multi_agent_coordinator.py # Multi-agent orchestration system
│   │   ├── run_multi_agent.py        # CLI entry point for multi-agent system
│   │   ├── flight_simulation.py      # Flight physics simulation
│   │   └── ...                       # 30+ additional automation scripts
│   ├── Screenshots/                  # Captured screenshots from tests
│   ├── Saved/                        # UE saved data
│   ├── Intermediate/                 # Build intermediates
│   ├── Binaries/                     # Compiled binaries
│   ├── DerivedDataCache/             # DDC cache
│   └── .vs/                          # Visual Studio settings
├── README.md                         # This file
├── run_all_tests.bat                 # Test runner batch script
├── check_models.py                   # LM Studio model availability checker
├── Saved/                            # Top-level saved data
└── Screenshots/                      # Top-level screenshots
```

---

## 11. Quick Start Guide for Developers

### Prerequisites

- **Unreal Engine 5.8** with Visual Studio (C++ development)
- **Python 3.12+** (for automation scripts)
- **LM Studio** running on `http://localhost:1234` (optional, for AI analysis)

### Step 1 — Open the Project

```bash
# From E:\PythonChimera
start Chimera\Chimera.uproject
```

The project will compile automatically. If it fails:

```bash
cd Chimera
run_build.bat build
```

### Step 2 — Verify Build

```bash
cd Chimera
run_build.bat validate
run_build.bat status
```

### Step 3 — Launch Editor & Test

1. Open `Chimera.uproject` in UE Editor
2. Press **Play** to start PIE (default map: `VehicleBasic`)
3. Use the D6 HUD widget for 6DOF controls

### Step 4 — MCP Automation Setup

Ensure LM Studio is running on port 1234, then test MCP connectivity:

```bash
cd Chimera\Python
python run_mcp_test.py
```

The MCP server will listen on `http://localhost:3000/mcp` for JSON-RPC requests.

### Step 5 — Run Automated Tests

```bash
# Flight physics simulation with LM Studio analysis
python Chimera\run_flight_physics.py

# Screenshot-based lift-off verification
python Chimera\analyze_screenshot.py

# Full MCP automated test workflow (PIE → screenshots → AI analysis)
python Chimera\Python\run_mcp_test.py
```

### Step 6 — Multi-Agent Coordination

```bash
cd Chimera\Python

# Default race track scenario
python run_multi_agent.py

# Custom task with parallel execution
python run_multi_agent.py --task "build a desert outpost"

# Sequential mode for debugging
python run_multi_agent.py --sequential
```

### Step 7 — Earth-Scale Landscape Verification

```bash
cd Chimera\Python
python -c "from tes_earth_scale_analysis import run_earth_scale_verification; print(run_earth_scale_verification())"
```

This verifies:
1. Seamless edge wrapping at landscape boundaries
2. Flat-to-sphere morph formula (`apparent_radius = actual_radius / distance`)
3. No pop, stutter, or visual tearing during transitions

---

## Key URLs & Ports

| Service | URL | Purpose |
|---------|-----|---------|
| MCP Server | `http://localhost:3000/mcp` | JSON-RPC 2.0 tool interface (37 tools) |
| LM Studio API | `http://localhost:1234` | AI screenshot analysis and reasoning |

## Configuration Files

| File | Location | Purpose |
|------|----------|---------|
| `.mcp.json` | Project root | MCP client configuration |
| `Config\DefaultEngine.ini` | `Chimera\Config/` | Renderer, graphics, splitscreen settings |
| `Config\DefaultGame.ini` | `Chimera\Config/` | Project ID, MCP bridge port (3000), LM Studio endpoint (1234) |
| `build_pipeline.ps1` | `Chimera/` | Build pipeline configuration |
| `BuildScripts\BuildConfig.json` | `Chimera\BuildScripts/` | Build targets and platforms |
