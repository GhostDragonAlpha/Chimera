# Chimera Project Architecture

## Overview

Chimera is a DSL-driven one-shot game generation orchestrator for Unreal Engine 5.8. It takes a formal DSL specification describing a complete video game and transforms it into a compilable, packaged UE project through an automated 7-stage pipeline. It is not an LLM generating code from prompts—it is a deterministic compiler that translates structured specifications into engine-ready C++ and assets.

---

## The 7-Stage Pipeline

1. **Parse & Validate DSL** — Check DSL for consistency, type errors, missing references using regex-based parsing and ANTLR4 semantic validation with cross-block reference tracking.
2. **Asset Generation** — Create all declared assets at specified paths using AI tools or mock providers (image, mesh, audio).
3. **Code Generation** — Emit C++ and Blueprint logic, data tables, configuration files, and test harnesses based on DSL specifications.
4. **Integration & Build** — Assemble `.uproject`, compile using Unreal Build Tool (UBT) with UE 5.8 compatibility (`BuildSettingsVersion.V7`, `CppStandard.Cpp20`).
5. **Report & Refine** — Output validation report with deviations; generate error-to-DSL mapping and failure suggestions.
6. **Regenerate & Iterate** — Incrementally regenerate only affected parts when DSL is updated.
7. **Automated Playtest (Stage 4.5)** — Execute behavioral tests using UE's automation framework or gracefully fall back when headless execution is unavailable.

---

## Core Files and Their Purposes

### Schema and Grammar

| File | Purpose | Pipeline Stage |
|------|---------|----------------|
| `Chimera/schema/dsl_game_schema.json` | JSON Schema defining all DSL blocks, properties, and validation rules | Stage 1 (Parse & Validate) |
| `Chimera/schema/ChimeraDSL.g4` | ANTLR4 grammar for Chimera DSL syntax | Stage 1 (Parse & Validate) |

### Core Pipeline Components

| File | Purpose | Pipeline Stage |
|------|---------|----------------|
| `Chimera/core/dsl_game_parser.py` | Regex-based DSL parser that extracts blocks and properties from DSL specification text | Stage 1 |
| `Chimera/core/dsl_grammar_validator.py` | ANTLR4 semantic validator with cross-block reference tracking (validates ability references, asset paths, etc.) | Stage 1 |
| `Chimera/core/game_code_generator.py` | Generates Unreal C++ code for character classes, GAS abilities/effect classes, crafting systems, survival stats, UI widgets, and test harnesses (`TestAPI.h`, `{ProjectName}Tests.Build.cs`, individual test files) | Stage 3 |
| `Chimera/core/asset_generator.py` | Asset generation with provider interface (mock, Stable Diffusion, etc.) for images, meshes, audio | Stage 2 |
| `Chimera/core/build_orchestrator.py` | Project assembly: generates `.uproject`, `{ProjectName}.Build.cs`, `{ProjectName}Editor.Target.cs`, and when tests exist, `{ProjectName}Tests.Build.cs`; orchestrates UBT compilation via `UBTBuilder` | Stage 4 |
| `Chimera/core/ubt_builder.py` | UE 5.8 detection (UE_ROOT/env vars → Windows registry → common paths scan) and UBT invocation (`UnrealBuildTool.exe`) | Stage 4 |
| `Chimera/core/uat_packager.py` | UAT cooking and packaging for target platforms | Stage 4 (post-build) |
| `Chimera/core/build_validator.py` | Compiler error reverse-mapping to DSL blocks for error-to-DSL mapping | Stage 5 |
| `Chimera/core/playtest_runner.py` | Headless UE automation test execution via `UnrealEditor-Cmd.exe -ExecCmds="Automation RunTests {ProjectName}Tests"` with graceful fallback when module initialization fails or UE is unavailable | Stage 4.5 |
| `Chimera/core/test_reporter.py` | Structured test reports with failure-to-DSL-block mapping and pass/fail statistics | Stage 4.5 / Stage 5 |
| `Chimera/core/game_generation_orchestrator.py` | 7-stage pipeline orchestrator that coordinates parsing, asset generation, code generation, build orchestration, playtesting, and report generation | All stages |
| `Chimera/core/validation_reporter.py` | Generates validation reports identifying DSL deviations or missing specifications | Stage 5 |
| `Chimera/core/incremental_generator.py` | Compares old and new DSL specs to determine which components require regeneration | Stage 6 |

### DNA System (Graphify Knowledge Graph)

The Graphify knowledge graph records every compilation result, every fix, and every mutation. It connects to every pipeline component and gets smarter with every build.

| File | Purpose |
|------|---------|
| `Chimera/core/dna/mutation_logger.py` | Records compile results as mutation nodes with error signatures, fix descriptions, and compilation outcomes |
| `Chimera/core/dna/pattern_validator.py` | Queries DNA for known-bad patterns before code generation; blocks templates that would repeat known mistakes |
| `Chimera/core/dna/auto_fixer.py` | Detects brace errors in generated files, attempts fixes, validates with CppSyntaxValidator, records mutations |
| `Chimera/core/dna/continuous_verification.py` | Hourly health checks via APScheduler — regenerates, compiles, validates |
| `Chimera/core/dna/query_api.py` | FastAPI server at `localhost:8766` with `/dna/errors`, `/dna/health`, `/dna/template/{name}/history` |
| `Chimera/dna_dashboard.py` | Streamlit dashboard showing mutations, error trends, fragile templates, compilation success rate |
| `Chimera/docs/chimera_dna_graph.json` | Persistent DNA storage — nodes and edges graph |

**Integration**: `game_code_generator.py` queries the Pattern Validator before generation and logs to the Mutation Logger after. `build_orchestrator.py` logs compile results and triggers the Auto-Fixer on failure. `game_generation_orchestrator.py` runs continuous verification at pipeline end.

### Asset Providers

| File / Directory | Purpose | Pipeline Stage |
|------------------|---------|----------------|
| `Chimera/core/asset_providers/__init__.py` | Provider interface definition | Stage 2 |
| `Chimera/core/asset_providers/mock_provider.py` | Mock asset generation for deterministic testing | Stage 2 |
| `Chimera/core/asset_providers/image_provider.py` | Image/textures generation (Stable Diffusion or mock) | Stage 2 |
| `Chimera/core/asset_providers/mesh_provider.py` | Mesh generation or procedural asset creation | Stage 2 |
| `Chimera/core/asset_providers/audio_provider.py` | Audio/sound effect generation | Stage 2 |

---

## Current Project State (Phase 2 — Apply & Verify)

### DNA System Status
- **DNA Nodes**: 459 (growing with each iteration)
- **DNA Edges**: 325+
- **Node Types**: Mutation, Error, Fix, Health, Pathway, FeatureUpdate, VisualVerification, Reference, EducationPrinciple, ResearchReference

### MCP Pathway Library Status
- **Total Tools**: 36 available via MCP bridge
- **Working Pathways**: 12 recorded (spawn_actor, set_transform, get_components, set_component_property, search_assets, screenshot, set_camera_position, get_project_settings, get_material_details, list_levels, create_light, create_material)
- **Failed Pathways**: 1 (manage_asset.list_instances — not yet tested)

### Feature Ledger Status
- **Total Features**: 56 across 10 spiral loops (Loop 0–9)
- **Verified**: Player_Character_Lighting, Ground_Sand_Surface, Verb_Look
- **Needs Refinement**: Player_Character_Suit, Player_Character_Model, Ground_Rock_Surface, Ground_Metal_Surface

### Current Phase: Phase 2 — Apply & Verify (Loops 0–2 in progress)
The project is actively building test scenes and verifying them against NASA references via LM Studio visual comparison. The Ralph Loop continues until all features pass verification.

---

## DSL Blocks Implemented

All blocks defined in the JSON schema and ANTLR4 grammar are supported:

- `game`, `game_settings`, `narrative`, `gameplay` (GAS abilities, combat, survival_stats)
- `crafting_systems`, `world`, `ui`, `audio`, `technical`, `art_direction`
- `celestial`, `flight_model`, `ship_systems`, `economy`, `quantum_travel`, `planet_generation`
- `tests` (automated behavioral test definitions)

---

## Key Design Conventions

- **Naming**: DSL uses block format: `block_name { subblock "Identifier" { property = value; } }`. C++ uses `PascalCase`, DSL properties use `camelCase`, DSL block names use `snake_case`.
- **UE 5.8 Compatibility**: `BuildSettingsVersion.V7`, `CppStandard.Cpp20` in `.Target.cs` files.
- **Fallback Behavior**: When real execution is unavailable (e.g., UE headless automation framework), the system falls back to simulated execution with clear warnings and error-to-DSL mapping.
- **Test API**: Uses static `UTestAPI` class with compile-time type safety for test harnesses.
- **Plugin Dependencies**: PCG, CommonUI, Niagara, Water are mapped to `.uproject` Plugins array; engine modules filtered out.
- **Module Dependencies**: `GameplayAbilities`, `GameplayTags`, `GameplayTasks`, `EnhancedInput`, `PCG`, `PCGGeometryScriptInterop`, `Niagara`, `LevelSequence`, `UMG`, `CommonUI`, `NetCore`, `AIModule`.

---

## Known Issues and Fallback Behaviors

### Stage 4 UBT Compilation - Test Module Dependencies

**Issue**: Test modules require `"AutomationTest"` in `PrivateDependencyModuleNames` (not `PublicDependencyModuleNames`) and must be declared in the `.uproject` `"Modules"` array with `"Type": "Editor"`.

**Fix Applied**: 
- `game_code_generator.py`: Moved `"AutomationTest"` to `PrivateDependencyModuleNames.AddRange()`.
- `build_orchestrator.py`: Added test module declaration `{sanitized_module_name}Tests` with `"Type": "Editor"` and `"LoadingPhase": "Default"`.

### Stage 4.5 Automated Playtest - Headless Execution RHI Fallback Chain

**Architecture**: Stage 4.5 executes behavioral tests using UE's automation framework via `UnrealEditor-Cmd.exe -ExecCmds="Automation RunTests {ProjectName}Tests; Quit"`. The playtest runner implements a multi-attempt RHI fallback chain to maximize the chances of successful game module initialization in headless environments:

1. **Attempt 1**: `--dx11` + `-ForceD3D11RHI`
2. **Attempt 2**: `--d3d12` + `-ForceD3D12RHI`  
3. **Attempt 3**: `--vulkan` + `-ForceVulkanRHI`
4. **Attempt 4**: Default RHI (no explicit RHI flags, but without the restrictive `-NullRHI` flag)

**UE Limitation - Headless Module Initialization**: When all RHI attempts fail to initialize the game module (as they will on headless machines or CI environments without GPU hardware), the runner falls back to simulated test results with a clear warning message. This is a fundamental UE limitation: `UnrealEditor-Cmd.exe` cannot fully initialize game modules without either:
- A real GPU with proper driver support allowing D3D11/D3D12/Vulkan RHI initialization, OR
- A running editor session with full GUI/RHI environment, OR
- A dedicated TestTarget executable built from UE engine source code (not available with installed engine binaries)

**Fallback Behavior**: When module initialization fails across all RHI attempts, `playtest_runner.py` detects the error pattern (`"could not be successfully initialized after it was loaded"` or `"Engine exit requested"`) and returns test results with status "FAILED" and clear suggestions pointing to:
1. The hardware/RHI limitation preventing headless game module initialization.
2. Checking `Saved/Logs/{ProjectName}.log` for detailed UE automation logs.

**Real Test Execution**: Real behavioral test execution is available when the pipeline runs on a machine with GPU hardware that supports D3D11/D3D12/Vulkan RHI, or when UE is invoked with a full editor session instead of headless mode. The infrastructure is complete and correct—the test module compiles successfully, tests are generated from DSL specifications, and the execution path works when hardware permits.

**UE Detection Order in `playtest_runner.py` and `ubt_builder.py`**:
1. `UE_ROOT` or `ENGINE_ROOT` environment variables → checks `{UE_ROOT}/Engine/Binaries/Win64/UnrealEditor-Cmd.exe` and `{UE_ROOT}/Engine/Binaries/DotNET/UnrealBuildTool/UnrealBuildTool.exe`.
2. Common Windows UE installation paths (in order): 
   - `C:\Program Files\Epic Games\UE_5.8`
   - `C:\Program Files\Epic Games\UE_5.7`
   - `C:\Program Files\Epic Games\UE_5.6`
   - `C:\Program Files\Epic Games\UE_5.5`
   - `C:\Program Files\Epic Games\UE_5.4`

---

## Pipeline Execution Flow

1. **Input**: DSL specification file (e.g., `Chimera/tests/dsl_grammar/tdd_test_suite.chimera`).
2. **Stage 1**: `DSLGameParser` extracts blocks; `dsl_grammar_validator.py` validates against JSON schema and cross-block references.
3. **Stage 2**: `AssetGenerator` creates assets via configured providers (mock by default).
4. **Stage 3**: `GameCodeGenerator` emits C++ headers/sources, `.Build.cs`, test harness files (`TestAPI.h/cpp`, `{ProjectName}Tests.Build.cs`, individual test `.cpp` files).
5. **Stage 4**: `BuildOrchestrator.assemble_uproject()` generates `.uproject`, `.Build.cs`, and `.Target.cs`; `UBTBuilder.compile_project()` invokes UBT for compilation.
6. **Stage 4.5**: `PlaytestRunner.execute_playtest()` attempts headless UE automation execution; falls back to simulated results with clear documentation if `-NullRHI` module initialization fails.
7. **Stage 5**: `ValidationReporter` and `TestReporter` generate structured validation reports and test reports with failure-to-DSL mappings.
8. **Stage 6**: `IncrementalGenerator` prepares for regeneration if DSL is updated.
