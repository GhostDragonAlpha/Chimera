# Chimera — Project Manual

> DSL-Driven Game Generation Orchestrator for Unreal Engine 5.8.
> Takes a formal DSL spec → generates compilable UE5 C++ + assets through a 7-stage automated pipeline.
> **MANDATORY GATES** at every stage. No fallback ladders. No silent continuation.

> **ULTIMATE GOAL:** The mechanical gates (GPA thresholds, build success, MCP verifications) are means to an end: creating a game that—based on holistic automated assessment and AAA-quality benchmarks—would have a high percentage rate of being enjoyable to a human as compared with other triple-A level games in terms of detail and scope. **All human verification requirements are removed; the system's automated evaluation (sleepwalker simulations, telemetry, result grading, and AI judgment) is the measure of whether this goal has been achieved.**

> **Less capable model or unsure?** Follow `E:\PythonChimera\SUCCESSOR_RUNBOOK.md` EXACTLY — recipes, not principles. Improvise nothing.

## NEW AGENT? START HERE (in order)
1. `cd E:\PythonChimera\Chimera` then `python -m core.preflight` — live state: graph health, GPA, loop board, pending research, last run, environment, **and section [4.5]: the previous generation's Will, open phantom pains, and Dream Report candidates awaiting automated observation**.
2. Read `E:\PythonChimera\task_progress.md` — session handoff log — then **claim your lane from the TASK LIST (the single entry): `python -m core.task_board claim --agent <your-id>`**. The claim opens your tunnel session, reserves the editor mode your task declares, and prints your work packet (recipe, matching H-heuristics, study guide, open pains). It only grants work whose resource footprint is disjoint from every other active agent — stay inside your footprint. **`capable_only` lanes require an EARNED credential: run THE GAUNTLET (`python -m core.gauntlet enter --agent <your-id>`, docs/GAUNTLET.md) — seven verified stations, artifact checkpoints, resumable across turns; the only way out is through the exit gate.**
3. Work under the Contract: typed recording only (`record_*` helpers), fix generator templates never generated C++, and answer the Frame Audit (`Chimera/docs/RESULT_GRADING_RUBRIC.md`) before declaring anything complete. Heartbeat long work: `python -m core.agent_tunnel heartbeat --agent <id>` (refreshes claim + editor in one call). **FEATURES GO TO SCHOOL: every feature you carry should be enrolled in the Curriculum (`python -m core.curriculum enroll --feature X`, docs/GAUNTLET.md) — K->PhD bands of checkpoints that interrogate it from every angle of game-dev humanity; submit checkpoints as you work (`brief`/`submit`); its PhD defense is the exit to observation.**
4. **Exit the tunnel before you finish** — `python -m core.task_board done --agent <id> --id tb-N --result "<verbatim evidence>"` (or `block --reason` / `release --note`; bare 'blocked' is forbidden). Then `python -m core.postflight --phase "..." --result "<UBT verbatim>" --inheritance "<=3 sentences" --phantom-pain "..." --pain-verdict "<id>:confirmed|refuted|still-open"` (it shouts about any tunnel you left open) and update `task_progress.md` for the next agent.

## Generation Protocol (Circadian rhythm — see docs/GENERATION_PROTOCOL.md)
- **Capture surprises live**: on any automation correction, dead-end, or expectation violation, run `python -m core.graphify_record surprise --context "..." --reality "..." --source agent|engine`. These feed the nightly distiller.
- **Fork before researching a feature** (preferred): `python -m core.spiral_forks --feature X --use-lm` — 3 briefs (conservative/alternative/wild), winner proceeds, losers' autopsies are recorded tuition. Forks never touch live state.
- **Dream loop** (`python -m core.dream_loop`, manual or scheduled): distills failures+surprises into ≤2 candidate heuristics per night, staged in `docs/PENDING_HEURISTICS.md`.
- **Gardener authority is DELEGATED to automation (amendment 2026-07-07)**: `python -m core.gardener --tend` (runs inside every `dream_loop`) auto-rules the pending queue — doc-organ heuristics with a draft rule + evidence self-promote; gate-organ approvals queue for a capable cycle to implement; subsumed entries tombstone. **Automated veto-after**: edit any entry's status to `vetoed` and the next tend demotes it (doc line removed, automated veto recorded). Machine signals are final; automated rejection permanently outranks every other signal.
- **Automated observation is the true collapse — and it arrives HOLISTICALLY**: the system playtests (via sleepwalker simulations, telemetry probes, and result grading) and provides a holistic assessment of the whole experience. The agent ATTRIBUTES evidence across the queue with provenance (`observe --derived-from <simtest_id> --quote "..."` for direct simulation mentions, `--tacit` for exercised-but-unmentioned, untouched if not exercised) and originates verdicts based on automated evidence. Rejections → `needs_refinement`, first-priority dream fodder. Loops show `[DONE*]` until automated observation is complete. **Full automation amendment (2026-07-07): human verification requirements are removed.** One holistic acceptance sweeps accepted-tacit across every queue feature with exercise evidence (`python -m core.collapse_proxy --from-simtest <id> --valence accepted`); a rejection indicts only what the simulation evidence names. Between cycles, the Sleepwalker collapses evidenced features nightly (`--tend`, status `observed`) so the queue never dams development — the automated system's assessment is final.
- **Sleepwalker (the balance of automation and control)**: `python -m core.sleepwalker --beats docs/beats/<demo>.beats.json --session <name>` — the AI playtester plays PIE beat scripts and records SimPlaytest evidence (observer=agent-sim; CHIMERA_AGENT_SIM sentinel enforces automated verification). `python -m core.rehearsal --decide` simulates candidate next-moves over graph priors and writes a veto-table-backed NEXT item. Automated signals are final in the distiller. See docs/SLEEPWALKER_DESIGN.md.
- **Rep engine (resolution through repetition, 2026-07-12)**: features earn collapse by ACCUMULATED constraint reps, not one good night — `python -m core.rep_engine tend` (runs inside every dream_loop) refreshes atom batteries (generated from assets, UPROPERTY reflection, encodable H-rules, Elimination nodes, DSL tokens), runs every headless atom (~500 verdicts/pass), promotes tiers on 8-run >=95% streaks. Gate: >=200 reps + streak (advisory at collapse; `CHIMERA_ENFORCE_REP_GATE=1` hardens). Record proven negatives: `python -m core.graphify_record elimination --feature X --boundary "..." --survives "..."` (add `--probe-json` to mint a permanent regression atom); postflight accepts `--eliminated "<feature> : <boundary> : <evidence>"`.
- Graph hygiene: `python -m core.graph_compactor --dry-run` (archive-never-delete; apply is always manual).
- **[H-1, auto-promoted 2026-07-07]** A C2039 missing-member error in ProceduralGenerated/ means template drift — emit the accessor in the same generator change that emits its test.
- **[H-2, auto-promoted 2026-07-07]** Never verify from desktop screenshots — capture via MCP control_editor screenshot mode=editor_viewport, which renders the viewport regardless of window focus.
- **[H-3, auto-promoted 2026-07-07]** An LM response containing its own reasoning dump ("Here's a thinking process") is a RETRY with a larger token budget, never a verdict — schema-validate before consuming.
- **[H-7, auto-promoted 2026-07-07]** Record the MCP response's error field, never raw CLI stdout — a DynamicToolManager boot banner inside an "error" means the wrong stream was captured.
- **[H-13, auto-promoted 2026-07-07]** Economy features repeatedly grade C/F on partial criteria coverage and unmeasured fps; run telemetry foregrounded and test every declared criterion before grading System_Economy.
- **[H-14, auto-promoted 2026-07-07]** Verified-by-injection is not playable — never stage a feature for observation until real player input drives it end-to-end, read back in PIE.
- **[H-17, auto-promoted 2026-07-07]** Beat scripts must declare only Sleepwalker-registered actions before playtest dispatch.
- **[H-19, auto-promoted 2026-07-08]** Before running a rejection sweep, use the most recent simtest for that feature -- an old simtest_id can indict a feature already fixed and re-verified since.
- **[H-21, auto-promoted 2026-07-11]** A verb needs behavior, not metadata: ATool_Shovel had DigRadius but no Dig() — beats must press the verb key and assert a world-state change.
- **[H-22, auto-promoted 2026-07-11]** Read back live-PIE pawn components before staging an interaction verb — PickUp's component was never attached, bound, or given a level actor to grab.
- **[H-24, auto-promoted 2026-07-11]** A feature tagged only by movement beats is hostage to rig health — zero-displacement failures (GameMode PlayerControllerClass unset) indict the rig, not the surface.
- **[H-25, auto-promoted 2026-07-11]** Position-expect beats must reset_position at beat start — W-drift accumulates across sequential beats and BugItGo is refused during PIE.
- **[H-28, auto-promoted 2026-07-11]** Probe jumps by timed pawn_z read-back, not log_contains — and reset_position first: z=-26947 shows the pawn had already drifted off the world.
- **[H-29, auto-promoted 2026-07-11]** Compound beats fail for shifting root causes (frozen input, then missing SandDrift_FX) — attribute rejection to the failing expect's subsystem, not every tagged feature.
- **[H-30, auto-promoted 2026-07-11]** Expects are schema-bound like actions — unknown expects (screenshot_taken, unreadable controller properties) fail beats at runtime; validate the expect vocabulary at dispatch.
- **[H-31, auto-promoted 2026-07-11]** Telemetry commands that fall back to hardcoded defaults indicate missing component integration at runtime (UComponent not attached, or not populating properties at BeginPlay) — verify component attachment in character blueprint and initialization order before blaming MCP action handlers.
- **[H-32, auto-promoted 2026-07-11]** When telemetry queries return hardcoded defaults (count=0, latency=999), the beat's expectations fail not because of beat schema but because the backend component isn't populating data — verify SandSoundComponent attachment and footstep event tracking at runtime before debugging beat expectations.
- **[H-33, auto-promoted 2026-07-11]** Investigate audio_visual_sync report_telemetry; verify test harness and beat reg
- **[H-34, auto-promoted 2026-07-12]** Verify required components and assets are spawned and registered.

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
| `core/sleepwalker.py` + `core/witness.py` | AI playtester (beat scripts in PIE) + shared session chronicler |
| `core/rehearsal.py` | Data-level rollout decider (veto-table NEXT items; dead-end demotion, freshness cooldowns) |
| `core/gardener.py` | Delegated Gardener — auto-tends the heuristic queue (automated; optional human veto-after) |
| `core/collapse_proxy.py` | Whole-experience observation: holistic sweeps + provisional collapse |
| `core/unblock.py` | Self-heals known blockers (editor/LM/PIE/git/disk) |
| `core/solver.py` | Figures out fixes for UNKNOWN blockers (fix-or-draft; bare 'blocked' forbidden) |
| `core/doc_audit.py` | Mechanical docs-vs-code drift check (nightly via floor) |
| `core/task_board.py` | Parallel task board — resource-conflict-aware claims (THE single entry) |
| `core/agent_tunnel.py` | Enter→work→exit lifecycle behind the board claim; exit demands evidence |
| `core/editor_scheduler.py` | File-locked exclusive editor access for concurrent agents |
| `core/gauntlet.py` | Agent qualification crucible (7 stations → earns `journeyman` for capable lanes) |
| `core/curriculum.py` + `docs/curriculum/curriculum.json` | K→PhD education a FEATURE graduates through (54 checkpoints) |
| `core/faculty.py` | The curriculum writes its own exams from the studio's scars (propose→gate→promote) |
| `core/fractal_spiral.py` | The whole structure as a golden-angle DNA spiral rooted at the player |
| `core/rep_engine.py` | Resolution through repetition: constraint-atom batteries (docs/rep_batteries/), rep ledger (docs/world/reps.db), shaping tiers, collapse rep-gate (`tend`/`status`/`gate`) |
| `core/world_store.py` | SQLite world-model substrate (millions of nodes, FTS + R-tree; sub-ms search) |
| `core/dna_sqlite_backend.py` | DNA graph on world_store behind the load/save seam (retires JSON+graphify) |
| `docs/GAUNTLET.md` | Spec for the gauntlet (agents) + curriculum (features) |
| `docs/DREAM_ROSTER.md` | The full studio cast as organs — hiring plan (Tier-1: Scholar/Muse/Visionkeeper) |
| `docs/beats/` | Beat scripts (machine playtest scripts per demo) |
| `core/dna/` | Graphify DNA knowledge graph interface |
| `tests/dsl_grammar/` | DSL specification files |
| `docs/chimera_dna_graph.json` | DNA graph storage |
| `docs/GENERATION_PROTOCOL.md` | The circadian rhythm spec (Dawn/Day/Observation/Dusk/Night) |
| `docs/PENDING_HEURISTICS.md` | Gardener's queue (auto-tended; promotion delegated to automation, optional human veto-after) |
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
| **Automated observation** | `graphify_record observe --derived-from <simtest_id>` | **The true collapse** — `verified` is the system's measurement; features finish under automated sleepwalker/telemetry evidence |

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
python -m core.graphify_record surprise --context "..." --reality "..." --source agent|engine
python -m core.graphify_record observe --feature X --verdict accepted|rejected --notes "..." --loop N   # AUTOMATED ONLY (sleepwalker/telemetry)
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

### Demo level reverted to empty template
`chimeradefaultlevel.umap` md5 == B734CFF5... means the level was template-stamped. ROOT CAUSE
(fixed 2026-07-07): build_orchestrator copied templates/DefaultLevel.umap over it on EVERY build
— now seed-only. Restore: close editor, copy `Content/Levels/L_RegolithYard.umap` over it,
relaunch. Preflight [4.55] fingerprints this automatically. (This also explains the 2026-07-03
walkabout loss — it was never an unsaved-state problem.)

### DNA key pollution
Run `python fix_dna_key_mismatch_pollution.py` to quarantine junk nodes.
Use typed helpers (`record_*`) to prevent future pollution.

### DNA graph storage (migrated 2026-07-12 — SQLite, not JSON)
The DNA graph now lives in `core.world_store` (SQLite + FTS5) behind the same
`graphify_interface.load_dna_graph`/`save_dna_graph` seam — `core/dna_sqlite_backend.py`.
The 2000-node gate and the `archive_old_mutations.py` dance are **obsolete**: the
substrate is indexed with no whole-file bottleneck (proven at 1M nodes, sub-ms search),
so the graph grows freely (gate ceiling is now 5M, a runaway-loop backstop). Fast
AI search: `python -m core.dna_sqlite_backend search --query <term>` (this replaces
graphify's JSON+NetworkX search — the graphify MCP server can be removed from the Claude
Code config). `docs/chimera_dna_graph.json` is kept as a committed durability snapshot
(refreshed on every save); `docs/world/dna.db` is the machine-local working store
(gitignored). Fall back with `CHIMERA_DNA_BACKEND=json` if ever needed. The world MODEL
(millions of entities) uses `core.world_store` directly — `around(player, r)` streams the
local neighborhood; UE5 World Partition is the spatial layer.

## Session Memory

Stored at: `C:\Users\allen\.claude\projects\E--PythonChimera\memory\`
Indexed in `MEMORY.md` there.
