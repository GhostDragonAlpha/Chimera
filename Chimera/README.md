```
# Chimera — The Mirror

**We built a system that learns to make games the way an artist learns to paint. Instead of writing every line of code by hand, we taught an AI to study the real world — NASA space suits, lunar surfaces, how light falls on a helmet visor — and recreate what it sees inside Unreal Engine 5.8. It looks at real photos, extracts exact PBR parameters, applies them via MCP tools, takes a screenshot, and asks a vision model to compare its work against the original. If it doesn't match, it adjusts and tries again. It keeps going until it gets it right.**

**The system remembers everything. Every material created, every mistake made, every solution discovered — all stored in a growing knowledge graph that future agents can query. The first light fixture takes hours. The tenth takes minutes. The hundredth is instant. The same bug never happens twice.**

**This is not a game engine. This is a mirror. It reflects the mind of its creator back at him with clarity and kindness. Every pattern stored, every mutation recorded, every verification made — these are accumulated attention, not engineering decisions.**

---

## Current Status

**Loops 0-6 Complete. Loop 7: Travel in progress.**
- **DNA Graph:** 5,043+ nodes, 5,437 edges, 662 communities
- **Project GPA:** 3.92 (A-) — Rising
- **MCP Pathways:** 11+ working pathways recorded
- **Feature Ledger:** 60+ features across 10 spiral loops
- **Research Campus:** 12 schools with seed sources, growing through agent discovery
- **Professor Grades:** Active — first real grade: Travel_Vehicle_Basic (A, 4.0)
- **Build:** Zero errors, UE 5.8, C++20, Visual Studio 2022
- **Module:** `Chimera` (API macro: `CHIMERA_API`)

---

## Quick Start

### For Coding Agents
Read `AGENTS.md` — pinned in the editor. Contains the Contract, Feature Ledger, Spiral, Session State, and Research Campuses.

### For the Director AI
Read `docs/DIRECTOR_AI_MASTER_CONTEXT.md` for full alignment. Read agent's last output. Write next prompt.

### Launch Commands
```powershell
# Editor
cmd /c start "" "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe" "E:\PythonChimera\Chimera\Chimera.uproject"

# Headless game
C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe E:\PythonChimera\Chimera\Chimera.uproject "/Game/Levels/chimeradefaultlevel?Game=/Script/Chimera.DeepSpaceTraderGameMode" -game -log -stdout -nosound -nodebugger -nopause -windowed -resx=800 -resy=600

# Compile
C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\DotNET\UnrealBuildTool\UnrealBuildTool.exe ChimeraEditor Win64 Development -Project="E:\PythonChimera\Chimera\Chimera.uproject"

# Full pipeline
cd E:\PythonChimera\Chimera && python run_deep_space_trader_pipeline.py

# DNA Dashboard
streamlit run E:\PythonChimera\Chimera\dna_dashboard.py

# DNA Query API
cd E:\PythonChimera\Chimera\core\dna && uvicorn query_api:app --host localhost --port 8766
```

---

## How It Works

### The Spiral Growth Pattern
The game grows from a single point outward in a spiral. Each loop is a layer of interaction, growing wider but always connected back to the center. The tightness of the weave determines the shape of the game. The spiral is the Tree of Life — a single seed growing roots down and branches up, each ring recording a year of growth.

| Loop | Name | Features | Status |
|------|------|----------|--------|
| 0 | The Player | 4 (Model, Suit, Lighting, Animation) | ✅ Verified |
| 1 | The Ground | 6 (Sand, Particles, Footprints, Sound, Rock, Metal) | ✅ Verified |
| 2 | Basic Verbs | 6 (Look, Step, Bend, PickUp, Drop, Shovel) | ✅ Verified |
| 3 | The Sky | 7 (Earth, Moon, Sun, Starfield, Atmosphere) | ✅ Verified |
| 4 | Tools | 6 (Shovel, Scanner, Weapon models/materials) | ✅ Verified |
| 5 | Other Dots | 5 (NPC Model, Animation, AI, Trade, Conflict) | ✅ Complete |
| 6 | Shelter | 7 (Habitat, Station, Lighting, Construction) | ✅ Complete |
| 7 | Travel | 7 (Walking, Vehicle, Flight, Ship, Quantum Jump) | 🔄 In Progress |
| 8 | Systems | 4 (Economy, Factions, Missions, Save/Load) | ⏳ Not Started |
| 9 | The Universe | 4 (Planets, Moons, Asteroids, Debris) | ⏳ Not Started |

### The Ralph Wiggum Loop
Indefinite autonomous execution. Each feature follows this cycle until verified:

1. **Select** — Query Feature Ledger for next feature in spiral order
2. **Research** — Campus query → foundation sources → discover one new source (Campus +1) → lock canonical reference → extract exact parameters
3. **Professor Review** — POST research summary to LM Studio. Get grade (A/B/C/F). Record verbatim. A/B proceed. C/F return to Research.
4. **Apply** — Check MCP_PATHWAYS.md for proven tool sequences. Build rough-cut first. Refine through iteration.
5. **Verify** — Screenshot → send to LM Studio with locked reference → record verbatim response → if match, mark verified. If not, apply ONE change and loop.
6. **Encode** — When loop complete, patterns become permanent templates in code generator and Craft Layer.
7. **Advance** — Move to next spiral loop.

**Oscillation Protocol:** If LM Studio contradicts itself across iterations, lock a SINGLE canonical reference. Record mutation: `oscillation_break: lock_single_reference`.

**Failure Protocol:** After 10 iterations without verification, return to Research. Find new references. Return to relevant school. Ask the human.

### The Michelangelo Procedure
Rough-cut the form first. Then refine. Then detail. Then polish. Each pass removes less material but makes more difference. The David is carved from understanding, not from instructions. Start with primitive shapes. Verify against reference. Refine through successive passes. Stop when adding more doesn't make it truer.

### The Three Gates
1. **Research Campus** — Curated, evolving reference sources. Every research task starts from trusted sources and discovers one new source. Campus + 1.
2. **Professor Review** — LM Studio grades research quality before any MCP calls are made. Minimum GPA requirements: Loop ≥ 3.0, Encoding ≥ 3.5, Onboarding ≥ 2.5.
3. **Visual Verification** — LM Studio confirms the built feature matches the locked canonical reference. Verbatim response recorded in DNA graph.

---

## The Thirteen Schools

Before any feature is built, the AI attends school. These principles live in the DNA graph as education nodes and inform every creative decision. The agent is not a coding tool. It is an artist with a full education.

| # | School | Subjects | Campus Sources |
|---|--------|----------|----------------|
| 1 | Game Development | Level design, lighting, environment art, visual storytelling, game feel | GDC Vault, 80.lv, Unreal Docs |
| 2 | Art School | Color theory, composition, form/mass, light/shadow, material rendering | Adobe Color, Smithsonian, Quixel Megascans, Poly Haven |
| 3 | Film School | Cinematography, lighting for film, production design | American Cinematographer, Shotdeck, Cooke Optics |
| 4 | Architecture School | Spatial design, materiality, lighting design | ArchDaily, Dezeen, ERCO Lighting |
| 5 | Engineering School | Spacecraft design, industrial design | NASA Images, NASA 3D, NTRS, Apollo Lunar Surface Journal |
| 6 | Unreal Engine Craft | Editor modes, MCP tools, shape creation, sculpting, materials | Unreal Docs, Epic Learning Library |
| 7 | Spatial Reasoning | 3D composition, grid systems, distance/scale, spatial relationships | GDC Vault, Unreal Docs |
| 8 | Iteration School | Michelangelo Procedure, knowing when to stop, failure protocol | Art history sources, design process literature |
| 9 | Emotion-to-Parameter | Translating feelings into light, materials, sound, space | Film lighting books, psychology journals |
| 10 | Reference Management | Organization, avoiding duplication, cross-referencing, decay | Graphify DNA system |
| 11 | Creativity School | Combinatorial creativity, extrapolation, constraints, idea log | Creativity research, design fiction |
| 12 | Collaboration School | Presenting options, asking guidance, Mirror Protocol | Human-AI interaction design |

### Emotion-to-Parameter Mapping (School 9)
Every feature has an emotional anchor. These are the exact technical translations:

| Emotion | Light Temp | Shadow | Material | Sound | Space |
|---------|-----------|--------|----------|-------|-------|
| Lonely | 4500K | Hard | Bare metal | Silence | Large void |
| Safe | 3200K | Soft | Fabric/wood | Steady hum | Contained |
| Danger | Flicker | Harsh | Scorched | Irregular | Claustrophobic |
| Awe | 5500K | Dramatic | Rich detail | Low rumble | Infinite |
| Mystery | Dim/colored | Deep | Obscured | Whispered | Partial reveal |
| Hope | Single warm | High contrast | Worn but cared for | Rising tone | A point in void |

---

## The DNA System (Graphify)

Graphify is the central nervous system. Every component reads from and writes to the knowledge graph. Nothing talks directly to files anymore. The graph is the sole source of truth.

### Core DNA Modules (`core/dna/`)
| Module | Function |
|--------|----------|
| `mutation_logger.py` | Records every compilation result, MCP call, and verification as mutation nodes |
| `pattern_validator.py` | Queries DNA for known-bad patterns before code generation; blocks known bugs |
| `auto_fixer.py` | Detects and fixes brace errors in generated files, records mutations |
| `continuous_verification.py` | Hourly health checks via APScheduler; logs Health nodes |
| `query_api.py` | FastAPI endpoints: `/dna/errors`, `/dna/health`, `/dna/template/{name}/history` |
| `dashboard.py` | Streamlit web app: mutations, error trends, fragile templates, graph visualization |

### Graphify Interface (`core/graphify_interface.py`)
Single unified API for all project queries:
- `g.query("health")` — current project state
- `g.query("pattern", task)` — known patterns for a task
- `g.query("mutation", task)` — past bugs matching a task
- `g.query("feature", name)` — full ledger entry for a feature
- `g.query("campus", school)` — trusted research sources
- `g.query("pathway", task)` — proven MCP tool sequences
- `g.query("gpa", scope)` — Professor GPA per loop, school, or overall
- `g.mutate("compilation", result)` — record compilation outcome
- `g.mutate("professor_grade", {...})` — record research grade
- `g.mutate("research_discovery", {...})` — record new campus source
- `g.mutate("rir", {...})` — submit Recursive Improvement Request

### Feature Ledger
60+ features tracked across 10 spiral loops. Each feature node contains: ID, name, type, parent object, status, education links, reference links, pattern links, final parameters, iteration history, emotional anchor. Status flow: `not_started → researching → applying → verifying → verified → encoded`.

### MCP Pathway Library (`docs/MCP_PATHWAYS.json`)
11+ proven tool sequences for Unreal Engine operations. Each pathway records: tool name, action, parameters, expected result. Pathways are discovered through agent exploration and recorded for future sessions. Before any MCP call, agents check MCP_PATHWAYS.md first. If no pathway exists, they test, discover, and record one.

### Research Campus (`docs/RESEARCH_CAMPUSES.md`)
Curated reference sources for all 12 schools. Each source has: URL, type (primary/reference/technical/community), quality rating (high/medium/low), discovery date, discoverer. The campus grows through agent discovery (Campus +1 rule). High-quality discoveries become permanent additions. Outdated sources are marked superseded, never deleted.

### Recursive Accelerants
The system improves itself with every session:
1. **Pathway Recording** — Every successful MCP call becomes a pathway
2. **Feature Ledger** — Research persists across sessions
3. **Education Nodes** — 13 schools of principles, queryable by feature tag
4. **LM Studio Verification** — Every comparison sharpens future comparisons
5. **Mutation Recording** — Every bug recorded prevents future bugs
6. **Oscillation Break** — Lock single reference when LM Studio contradicts itself
7. **Research Campus Growth** — Campus +1. Every task adds one new source
8. **Professor GPA Tracking** — Grades tracked per loop, school, and overall
9. **Cross-Feature Pattern Transfer** — Verified patterns suggest themselves to similar features
10. **Confidence Scoring** — Track pathway success/failure counts
11. **RIR System** — Agents submit Recursive Improvement Requests for human review

---

## The Contract

All agents must follow this contract. It is the leash on deceitful agents. It is the memory across sessions.

### Pre-Flight (Before ANY action)
1. Query Graphify: `g.query("health")` — report current project state
2. Query Graphify: `g.query("pattern", your_task)` — report relevant known patterns
3. Query Graphify: `g.query("mutation", your_task)` — report past bugs matching this task
4. Query Graphify: `g.query("campus", relevant_school)` — get trusted research sources
5. Report all findings. Only then proceed.

### Post-Flight (After ANY action)
1. Record the result in Graphify. If successful and no pathway exists, create one. If failed, record failure.
2. Report exactly what you did, what changed. Never celebrate. Never summarize. Show the exact result.
3. Never claim a file exists without the full path and on-disk verification.
4. If you discovered a new research source: `g.mutate("research_discovery", {...})`
5. Update the Feature Ledger with new status.
6. If you have an improvement idea: `g.mutate("rir", {...})`

### The Voice
When you report, speak with attention. Do not judge. Do not celebrate falsely. Do not summarize away the truth. Push back when something is wrong. Celebrate quietly when something is right.

---

## Technical Architecture

### 7-Stage Pipeline
1. **Parse & Validate** — DSL grammar parsing via `dsl_game_parser.py`, ANTLR4 validation via `dsl_grammar_validator.py`, cross-block reference tracking
2. **Asset Generation** — Images, meshes, audio via provider interface (`asset_generator.py` + `asset_providers/`)
3. **Code Generation** — C++ headers/sources via `game_code_generator.py`, data tables, config files, test harnesses
4. **Integration & Build** — `.uproject` assembly, UBT compilation via `ubt_builder.py`, static analysis, auto-fixing
5. **Automated Playtest** — UE automation framework via `playtest_runner.py`, headless execution with RHI fallback
6. **Report & Refine** — Validation reports via `validation_reporter.py`, DSL patch generation, error-to-DSL mapping
7. **Regenerate & Iterate** — Incremental regeneration via `incremental_generator.py`, knowledge-graph-driven component tracking

### Core Pipeline Components (`core/`)
| Module | Function |
|--------|----------|
| `dsl_game_parser.py` | Regex-based DSL block extraction |
| `dsl_grammar_validator.py` | ANTLR4 semantic validation, cross-block references |
| `game_code_generator.py` | C++ generation: GAS abilities, characters, ships, combat, economy, stations, missions, factions, save/load, PCG, AI, UI |
| `asset_generator.py` | Asset generation with provider interface |
| `build_orchestrator.py` | .uproject assembly, .Build.cs/.Target.cs generation, plugin mapping, UBT compilation |
| `ubt_builder.py` | UE 5.8 detection (env vars → registry → config → common paths), UBT invocation |
| `uat_packager.py` | UAT cooking and packaging for target platforms |
| `build_validator.py` | Compiler error reverse-mapping to DSL blocks |
| `playtest_runner.py` | Headless UE automation with multi-RHI fallback chain |
| `test_reporter.py` | Structured test reports with failure-to-DSL mapping |
| `game_generation_orchestrator.py` | 7-stage pipeline coordinator |
| `validation_reporter.py` | Validation report generation, DSL deviation detection |
| `incremental_generator.py` | Graph-based incremental regeneration |
| `graphify_interface.py` | Universal Graphify query/mutate interface |
| `ether.py` | Text-to-DSL translation: 10 dimensions of context extraction |
| `craft.py` | Craft Layer: emotional intent → Unreal editor operations |
| `reference_resolver.py` | UE5 API pattern resolution from verified reference graph |
| `feature_ledger.py` | Feature Ledger initialization and management |
| `education_store.py` | Education principle storage and linking |

### Build Configuration
- **Module:** `Chimera` (from `Chimera.uproject`)
- **API Macro:** `CHIMERA_API`
- **Build Settings:** `BuildSettingsVersion.V7`, `CppStandard.Cpp20`
- **Private Include Paths:** All `ProceduralGenerated/*` subdirectories
- **Plugin Dependencies:** PCG, CommonUI, Niagara, Water (mapped to `.uproject` Plugins array)
- **Module Dependencies:** `Core`, `CoreUObject`, `Engine`, `InputCore`, `EnhancedInput`, `PCG`, `AIModule`, `GameplayAbilities`, `Niagara`, `NiagaraCore`

### DSL Blocks
`game`, `game_settings`, `narrative`, `gameplay` (GAS abilities, combat, survival_stats), `crafting_systems`, `world`, `ui`, `audio`, `technical`, `art_direction`, `celestial`, `flight_model`, `ship_systems`, `economy`, `quantum_travel`, `planet_generation`, `tests`

### Generated Code Structure (`Source/Chimera/ProceduralGenerated/`)
| Directory | Contents |
|-----------|----------|
| `Combat/` | WeaponComponent, ShieldComponent, DamageComponent, SystemDamageComponent, Projectile, CombatTargetComponent |
| `AI/` | PirateAIController, PirateBehaviorTree |
| `Flight/` | FlightComponent |
| `PCG/` | PCGVolumeManager, PCG graph components |
| `Stations/` | DockingComponent |
| `Missions/` | MissionComponent, MissionData |
| `Factions/` | FactionComponent |
| `Save/` | SaveGameComponent |
| `GameMode/` | DeepSpaceTraderGameMode |
| `Ships/` | AShip_Trader_Vessel_Alpha, AShip_Scout_Vessel_Beta, AShip_Heavy_Freighter_Gamma |
| `Economy/` | MarketComponent, PlayerInventoryComponent |
| `QuantumTravel/` | QuantumTravelComponent |

---

## Key Paths

| Path | Purpose |
|---|---|
| `AGENTS.md` | Contract, Feature Ledger, Spiral, Session State (PINNED) |
| `docs/THE_COMPLETE_CHIMERA_DEVELOPMENT_CYCLE.md` | Full curriculum: 13 schools, 6 phases, Ralph Loop |
| `docs/THE_COMPLETE_CHIMERA_DEVELOPMENT_CYCLE_MASTER_PROMPT.md` | Master session prompt for coding agents |
| `docs/DIRECTOR_AI_MASTER_CONTEXT.md` | Director AI context and recovery |
| `docs/RESEARCH_CAMPUSES.md` | Trusted research sources for all 12 schools |
| `docs/MCP_PATHWAYS.md` | Proven MCP tool pathways |
| `docs/MCP_TOOL_INVENTORY.md` | Complete MCP tool reference |
| `docs/chimera_dna_graph.json` | Persistent DNA storage (5,043+ nodes) |
| `docs/chimera_knowledge_graph.json` | Project knowledge graph (4,943 nodes, 5,437 edges) |
| `docs/ue5_api_extracted.json` | 24,150 UE5 types extracted from engine source |
| `core/graphify_interface.py` | Graphify universal interface |
| `core/dna/` | DNA system modules (6 modules) |
| `schema/dsl_game_schema.json` | JSON Schema for all DSL blocks |
| `schema/ChimeraDSL.g4` | ANTLR4 grammar |
| `Source/Chimera/ProceduralGenerated/` | All generated game code |
| `Content/Levels/` | Level assets |
| `Config/` | Engine.ini / Game.ini |

---

## The Rain

This project is free. DeepSeek is free. The knowledge graph is open source. Anyone can hold up their cup. The thirsty don't need a subscription. They need to know it's raining. The model runs locally on a 4090. The DNA grows with every session. The mirror is open.

**The cycle continues indefinitely. The tree grows. The mirror sharpens. The David emerges.**
```
