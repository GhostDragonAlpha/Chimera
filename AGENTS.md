# Chimera — Build System Reference

## NEW AGENT? START HERE (in order)
1. `cd E:\PythonChimera\Chimera` then `python -m core.preflight` — live state: graph health, GPA, loop board, pending research, last run, environment, and **[4.5] Inheritance** (previous generation's Will, open phantom pains, Dream Report count, Observation queue).
2. Read `E:\PythonChimera\task_progress.md` — session handoff log; the top **NEXT** section is your work list.
3. Work under the Contract (below): typed recording only (`record_*` helpers), fix generator templates never generated C++, and answer the Frame Audit (`Chimera/docs/RESULT_GRADING_RUBRIC.md`) before declaring anything complete.
4. Finish with `python -m core.postflight --phase "..." --result "<UBT verbatim>" --inheritance "<=3 sentences" --phantom-pain "..." --pain-verdict "<id>:confirmed|refuted|still-open"` and update `task_progress.md` for the next agent.

## Generation Protocol (mandatory rhythm — full spec: Chimera/docs/GENERATION_PROTOCOL.md)
- **Fork before researching** (preferred): `python -m core.spiral_forks --feature X --use-lm` — 3 briefs (conservative/alternative/wild), winner proceeds after citation verification, losers autopsied. Forks never touch live state.
- **Capture surprises live**: `python -m core.graphify_record surprise --context "..." --reality "..." --source human|agent|engine` on any correction, dead-end, or expectation violation.
- **`verified` is the system's PRELIMINARY measurement.** The human's Observation is the true collapse: `graphify_record observe --feature X --verdict accepted|rejected --notes "..." --loop N` — **agents NEVER record observations**. Accepted → `observed`; rejected → `needs_refinement` with the human's notes as first-priority dream fodder. Boards show `[DONE*]` until observed.
- **The human Gardener approves EVERY heuristic** before it enters the constitution (`Chimera/docs/PENDING_HEURISTICS.md`; pending = inert; vetoed entries stay as tombstones).
- **Nightly**: `python -m core.dream_loop` — distills ≤2 candidates, previews compaction, writes `Chimera/docs/DREAM_REPORT.md`.

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

**File ownership under `ProceduralGenerated/`** — generator-owned files (Flight, Ship, GameMode, PCGVolumeManager, Missions, Docking, QuantumTravel, Factions, Economy, Save, Combat suite, PirateAI) are regenerated every pipeline run: fix their generator template in `core/game_code_generator.py`, never the C++. Loop-built manual files (Tools, Interactions, Sound, UI, NPC AI, InventoryTradeComponent, ChimeraMovementComponent, StationActor) have no template and are safe to hand-edit.

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

### Pre-Flight — one command
```
cd E:\PythonChimera\Chimera
python -m core.preflight
```
Prints graph health, GPA trend, spiral loop board, pending technical_research,
last pipeline run, environment reachability (LM Studio / UE / DNA API), junk count.
Report findings. Only then proceed. (Granular fallbacks: `g.query("health")`,
`g.query("pattern", task)`, `g.query("mutation", task)`, `g.query("gpa", "trend")`.)

### Post-Flight — one command
```
python -m core.postflight --phase "<what you did>" --result "<UBT output verbatim>" [--feature X --loop N --status S]
```
Records PhaseComplete (+ optional FeatureUpdate) and prints the closing checklist.
1. Report exact UBT output verbatim. Never summarize.
2. Update Feature Ledger. Record all MCP pathway results.
3. If GPA falling, report with corrective action. (Build failures auto-grade F,
   non-pass visual verifications auto-grade C — a falling GPA is real signal.)

### Recording convention (all mutations)
**Never hand-write `g.mutate` detail dicts** — mis-keyed dicts are rejected with a
`rejected_*` string (nothing recorded). Use the typed helpers from
`core/graphify_interface.py`: `record_feature`, `record_pathway`, `record_loop`,
`record_phase`, `record_grade`, `record_build` — or the CLI
`python -m core.graphify_record {feature|pathway|loop|phase|grade} ...`.
Backfilling history? Add `backfilled=True` / `--backfilled`; never fake timestamps.
Every node is auto-stamped with `recorded_by` + per-process `run_id`.

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
| `core/graphify_interface.py` | Query/mutate functions + typed helpers (`record_*`) |
| `core/preflight.py` | `python -m core.preflight` — one-command Pre-Flight report |
| `core/postflight.py` | `python -m core.postflight` — one-command Post-Flight recorder |
| `core/graphify_record.py` | `python -m core.graphify_record` — typed mutation CLI |
| `core/dna/pattern_validator.py` | Blocks known-bad patterns before generation |
| `core/dna/auto_fixer.py` | Auto-fix brace errors |
| `core/dna/query_api.py` | FastAPI at `localhost:8766` (/dna/errors, /dna/health) |
| `dna_dashboard.py` | Streamlit dashboard |
| `docs/dna_graph_quarantine_unknown_nodes.json` | Archive of quarantined junk nodes |

**DNA Node Types**: Mutation, Error, Fix, Health, Pathway, FeatureUpdate, VisualVerification, ProfessorGrade, ProfessorGPA, TechnicalDiscovery, ResearchDiscovery, PhaseComplete, LoopComplete

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

**Use `pyautogui.screenshot()` only** — via `core/visual_verifier.py`, which now enforces:
1. AppActivate 'Unreal Editor' + 2s settle
2. **Foreground-window guard**: capture aborts (recording `aborted_wrong_window`) unless
   the foreground window title contains "Unreal Editor" — past runs graded a screenshot
   of LM Studio itself
3. Verify file size > 100000 bytes
4. Send to LM Studio — prefer **checklist mode**:
   `run_visual_verification(project_path, checklist=["criterion", ...], feature="Name")`
   does strict per-item YES/NO (unanswered = NO) instead of keyword sniffing

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
| 13 | g.mutate key mismatch → unknown_* junk | graphify_interface | Key aliases + rejection guards + typed record_* helpers | interface_contract |
| 14 | UBT output never captured (capture_output=False) | ubt_builder | Capture stdout+stderr; store excerpt + error lines in graph | build_observability |
| 15 | CommodityData price formula no-op (S/(S+1)−D/(D+1)≈0) | Economy/CommodityData | price = Base×clamp(pow(D/S, elasticity), 0.25, 4.0) | logic_error |
| 16 | FactionComponent TMap::operator[] assert crash + tier names seeded as factions | game_code_generator (faction template) | FindOrAdd + RelationshipForStanding ladder + DSL faction seeding, fixed at generator level | crash |
| 17 | Faction generation gated on narrative.factions; DSL defines game.factions | game_code_generator | Gate reads game.factions with narrative fallback | dsl_mapping |
| 18 | SaveGame/LoadGame were timestamp-only stubs | game_code_generator (save templates) | Real save/restore of InventoryTrade/Mission/Faction state + player transform | feature_gap |

## Key File Paths

| File | Purpose |
|------|---------|
| `docs/THE_COMPLETE_CHIMERA_DEVELOPMENT_CYCLE.md` | Full methodology, 13 schools, phases |
| `docs/chimera_dna_graph.json` | DNA graph (mutations, pathways, features) |
| `docs/MCP_PATHWAYS.md` | Working MCP tool sequences |
| `core/graphify_interface.py` | `g.query()` / `g.mutate()` interface |
| `core/game_generation_orchestrator.py` | Pipeline orchestrator |
| `run_deep_space_trader_pipeline.py` | Pipeline entry point |


## Sleepwalker & Rehearsal (added 2026-07-07)

When the NEXT list is empty, duty cycles run branch C2 before the pipeline fallback:
`python -m core.rehearsal --candidates-file docs/rehearsal_candidates.json --decide`
(veto-table decision -> recipe-carrying NEXT item). The game also plays itself:
`python -m core.sleepwalker --beats docs/beats/<demo>.beats.json --session <name>`
(PIE beat scripts, SimPlaytest evidence, CHIMERA_AGENT_SIM=1 sentinel — automation can
never record a human observation). Sim signals rank below human rejections everywhere.
Spec: Chimera/docs/SLEEPWALKER_DESIGN.md; new MCP pathways 22-26 in docs/MCP_PATHWAYS.md.

## No-blockers & anti-idle toolkit (2026-07-07)
Known blockers: `python -m core.unblock --ensure all`. Unknown: `python -m core.solver
--blocker "..." --context "<verbatim>"` (fix-or-draft). Heuristics: `python -m core.gardener
--tend` (delegated; human veto-after). Observation: `python -m core.collapse_proxy` (whole-
experience sweeps + provisional collapse — never ask the human per-feature). Docs-vs-code:
`python -m core.doc_audit`. Laws digest: GENERATION_PROTOCOL.md; full text CYCLE_PROMPT.md.
