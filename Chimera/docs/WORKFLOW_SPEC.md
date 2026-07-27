# Chimera — Full System Technical Specification

> Complete spec sheet for the Chimera DSL-driven game-generation studio.
> Authoritative sources: CLAUDE.md, `core/*.py` (148 modules), `docs/world/*.db`,
> `docs/envelope.json`. UE 5.8 / C++20 / Python orchestration on Win64.

---

## 1. SYSTEM OVERVIEW

### 1.1 Purpose
A closed-loop pipeline that takes a formal DSL spec and produces compilable UE5
C++ + assets, verifies them by automated evaluation, and iterates toward a seed
vision (`CHIMERA_VISION.py`). Human verification is removed; the measure of done
is the system's own automated assessment (sleepwalker sims, telemetry, result
grading, LM judgment).

### 1.2 Top-level data flow
```
DSL Spec → Parse → Asset Gen → Code Gen → Build → Playtest → Scene Verify → Record
                        ↕                              ↕
                  DNA Graph (world_store)      MCP (chiR24 + Unreal bridge)
```
Hard gates at every transition; a gate failure exits non-zero and halts.

### 1.3 Control planes (four steering organs, read every cycle)
| Organ | Module | Function |
|---|---|---|
| HELM | `core/helm.py` | ast-parses the seed → measures per-system realization → sets HEADING (Contain/Fix/Graduate/Build/Verify/Polish/Consolidate) |
| CAPCOM | `core/capcom.py` | push channel: subsystems + human drop signals → one operator brief |
| MALCOLM | `core/malcolm.py` | edge-of-chaos regulator: 15 walls with provenance + admission control |
| CIRCADIAN | `core/circadian.py` | system time → PHASE (Dawn/Day/Dusk/Night); gates the nightly run |

---

## 2. DATA STORES & SCHEMAS

### 2.1 SQLite substrate (`core/world_store.py`) — `docs/world/*.db` (gitignored, machine-local)
All graph DBs share the schema: `node`, `edge`, `node_fts` (FTS5 full-text),
`node_rtree` (R-tree spatial). Proven at 1M nodes, sub-ms search.

| DB | Holds |
|---|---|
| `dna.db` | THE DNA GRAPH — every mutation/build/verification (behind `graphify_interface.load/save_dna_graph`; `core/dna_sqlite_backend.py`) |
| `world.db` | the world MODEL (millions of entities; `around(player, r)` streams the local neighborhood) |
| `capcom.db` | CAPCOM signals (append-only) + `capcom_meta` (watermark) + `capcom_inbox_seen` (hash-idempotent inbox ingest) |
| `reps.db` | rep ledger — `reps(id, ts, run_id, feature, atom_id, passed, evidence)` + `promotions(feature, tier, ts, note)` |
| `history.db` | THE BOOK — 8 chapters, FTS-searchable (`book` table) |

### 2.2 Committed snapshots (in git)
- `docs/chimera_dna_graph.json` — durability snapshot of the DNA graph, refreshed on every save.
- `docs/envelope.json` — Malcolm's 15 walls (`axes`) + `rules` + `pending_adjustments`.
- `docs/rep_batteries/*.json` — per-feature constraint-atom batteries.
- `docs/objectives/*.json` — trainer objective functions.
- `docs/beats/*.beats.json` — machine playtest scripts.
- `docs/curriculum/curriculum.json` — the K→PhD checkpoint program.
- `docs/decomposition_templates.json` — breakdown templates.

### 2.3 Fallback
`CHIMERA_DNA_BACKEND=json` reverts the DNA graph to JSON+NetworkX. Default is SQLite.

---

## 3. THE PIPELINE (7 stages)

Entry: `python run_deep_space_trader_pipeline.py`. Stage modules:

| # | Stage | Module | Output |
|---|---|---|---|
| 1 | Parse | `core/dsl_game_parser.py` (+ `dsl_grammar_validator.py`) | parsed spec AST |
| 2 | Asset Gen | `core/asset_generator.py` (+ `asset_config.py`, `audio_sourcer.py`) | UE assets |
| 3 | Code Gen | `core/game_code_generator.py` (+ `incremental_generator.py`) | ProceduralGenerated/*.h/.cpp |
| 4 | Build | `core/build_orchestrator.py` (+ `ubt_builder.py`, `build_validator.py`) | UBT result (must == 0) |
| 5 | Playtest | `core/playtest_runner.py` (+ `sleepwalker.py`, `witness_runner.py`) | SimPlaytest evidence |
| 6 | Scene Verify | 4 mandatory layers (engine facts / telemetry / screenshot / vision) | verification nodes |
| 7 | Record | `core/graphify_record.py` (typed helpers) | DNA graph mutations |

### 3.1 DSL specs (`tests/dsl_grammar/*.chimera`)
`deep_space_trader` (primary), `space_trader`, `ship_classes`, `flight_components`,
`quantum_travel`, `economy_data`, `celestial_bodies`, `planet_generation`,
`starcitizen_scale`, `valid_game_spec`, `valid_gameplay_combat`, `tdd_test_suite`,
`invalid_syntax` (negative test).

### 3.2 Generator ownership contract
- **Generator-owned** (regenerated every run; hand-edits clobbered — fix
  `core/game_code_generator.py`): Flight, Ship, GameMode, PCGVolumeManager,
  MissionData/MissionComponent, Docking, QuantumTravel, FactionComponent, Economy
  (CommodityData/EconomyManager/StationTradingData), DeepSpaceTraderSaveGame/
  SaveGameComponent, Weapon/Projectile/Shield/Damage/SystemDamage/CombatTarget,
  PirateAIController + behavior tree.
- **Guarded seed-only** (written `if not exists`, then hand-editable): GameMode
  header/source, module files, CombatTargetComponent — editing the template does
  NOT overwrite an existing file without a full regen.
- **Loop-built** (no template; hand-edits safe): Tools, Interactions, Sound, UI,
  NPC AI, ChimeraMovementComponent, StationActor.
- **Never edit** `Chimera.Build.cs`.

---

## 4. GATE SYSTEM

### 4.1 Mandatory hard gates (`core/gates.py`) — `GateViolation(severity="blocker")` → exit 1
| Gate | Predicate |
|---|---|
| `gate_no_junk_nodes` | zero `unknown_*` nodes in the graph |
| `gate_gpa_not_critically_falling` | cumulative GPA ≥ 1.0 |
| `gate_provenance_complete` | every mutation carries provenance |
| `gate_node_count_bounded` | graph_nodes < 5,000,000 |
| `gate_lm_available` | LM Studio reachable, SOME model resident (adopted, not loaded) |
| `gate_lm_studio_online` | LM Studio endpoint responds |
| `gate_unreal_editor_running` | editor process present when required |
| `gate_build_succeeded` | UBT return code == 0 |
| `gate_auto_fixer_attempted` | build failure was auto-fix-attempted first |
| `gate_no_stale_trees` | only `Chimera/` under `Source/` |
| `gate_playtest_no_failures` | zero test failures before Stage 7 |
| `gate_git_clean` | no unexpected dirty tree at gate points |
| `gate_envelope` | no MEASURED breach of a Malcolm wall (`core.malcolm`) |
| `stage_7_visual` | all 4 scene-verification layers pass |

### 4.2 Postflight enforcement stack (`core/postflight.py`)
Fires inside `if args.feature and args.status in {verified, observed,
observed_provisional}`. Order + satisfy/waiver flags + env softener:

| # | Gate | Module | Requires | Waiver flag | Softener |
|---|---|---|---|---|---|
| 1 | Research | `research_gate.py` | `--researched` sources or node | `--research-waiver` | `CHIMERA_RESEARCH_GATE=warn` |
| 2 | Generator Guard | `generator_guard.py` | no dirty generator-owned C++ (LM-judged, H-3) | `--generator-waiver` | `CHIMERA_GENERATOR_GUARD=warn` |
| 3 | Witness | `witness_gate.py` | SimPlaytest/telemetry/observation node or `--witnessed` | `--witness-waiver` | `CHIMERA_WITNESS_GATE=warn` |
| 4 | Visual | `visual_gate.py` | recorded `visual_verification/*` node or `--visual-analysis` | `--visual-waiver` | `CHIMERA_VISUAL_GATE=warn` |
| 5 | Training | `training_gate.py` | verified: enroll + reps begun; observed: full rep gate | `--training-waiver` | `CHIMERA_TRAINING_GATE=warn` |
| 6 | The Coin | `coin_verifier.py` | LM judges HEADS(claim)↔TAILS(evidence) both directions | (n/a) | `CHIMERA_COIN_GATE=warn` |

Postflight arg surface: `--phase --result --notes --feature --loop --status
--phantom-pain --inheritance --pain-verdict --eliminated --researched
--research-waiver --generator-waiver --witnessed --witness-waiver
--visual-analysis --visual-waiver --training-waiver --short`.

### 4.3 Task-closure training gate (`agent_tunnel.exit_tunnel` / `task_board done`)
Separate from 4.2. `training_gate.classify_task` → {game, infra, research,
witness}; `check_task` → {n/a, evidence, waived, missing};
`enforce_task_or_raise` raises ValueError (→ REFUSED) on missing+enforced and
posts the outcome to CAPCOM (`training` channel). Domain-appropriate:
- **game** (footprint touches Source/ | generator | DSL): subject enrolled + ≥1 rep.
- **infra**: proof-of-work (tests + verbatim exit evidence) — no game artifact to atomize.
- **research**: the research gate.
- **witness**: it runs the training-evaluation.

### 4.4 Result grade (`core/result_grader.py`, zero LM dependency)
Scores measured evidence (in-engine tests × declared-criteria coverage, telemetry,
agent-judged checklist, spec fidelity). A ≥90 · B ≥75 · C ≥60 · F <60. C/F → back
to research with the study guide. Build failure auto-grades F.

There is no "expanded AAA rubric". `result_grader_aaa_expanded.py` was DELETED
2026-07-16 and nothing replaces it: it accepted `benchmark_titles`, defaulted them to
`[]`, copied them into its output and **never read them** — so its "85th percentile vs
AAA titles" was computed against nothing — and 45 of its scoring branches were
string-equality checks against the agent's own evidence file (write
`"moment_to_moment_feel_quality": "AAA"` about your own work, score 12/12). Nothing
imported it; its numbers reached the operator only through dashboards.
**No reference, no verdict** — see `docs/MASTER_DEVELOPMENT_DASHBOARD.md`.

### 4.5 Exit-code contract
`0` all gates passed · `1` gate violation (blocked) · `2` unexpected error.

---

## 5. TASK BOARD & AGENT LIFECYCLE (`core/task_board.py`, `core/agent_tunnel.py`)

### 5.1 Task record
`{id: tb-N, title, feature, recipe, priority, capable_only, depends_on,
resources:{files[], editor, exclusive[]}, status, claimed_by, claimed_at,
heartbeat, created_at/by, notes[], result}`. Statuses: `open|claimed|done|
blocked|abandoned`.

### 5.2 Footprint / conflict model (`tasks_conflict`)
Two tasks conflict iff: same `feature`, OR shared `exclusive` token, OR editor
mode clash (`closed` vs non-none), OR file-glob overlap. **Three real shared
resources:**
- `pie` — the single Play-In-Editor session; only PIE-driving lanes (witness,
  telemetry soaks) take it. Headless code-fix NEVER claims pie.
- `generator` — `core/game_code_generator.py`; every generator-owned fix shares it.
- file globs — same-subtree edits serialize; different subtrees run parallel.
Scope resolver `_scope_for(name)` classifies: PIE families / envelope (docs) /
loop-built subtree / generator-owned (generator token) / default.
`rescope_nondone_tasks()` self-heals footprints on every claim.

### 5.3 Claim algorithm (`_claimable` / `parallel_frontier`)
Grant an OPEN task iff: not `capable_only` (unless credentialed), deps DONE,
and disjoint from every ACTIVE claim, highest priority first. `parallel_frontier`
= greedy maximal simultaneously-claimable set. On empty frontier, the CLI prints
`_print_no_claim` (names the blocking claim, resource, reap ETA).

### 5.4 Lifecycle chokepoints
- claim = tunnel `enter` (reserves editor mode, prints work packet) → posts CAPCOM `board`.
- `agent_tunnel exit --outcome done|blocked|release` — the exit contract:
  `done` demands `--result` verbatim evidence; **bare 'blocked' forbidden**.
  Routes `done`→`complete_task` after the closure training gate.
- Stale reap: `_reap_stale` reopens claims past `CLAIM_TTL` (default 7200s,
  `CHIMERA_TASK_CLAIM_TTL`).

### 5.5 The Wellspring (`core/wellspring.py`) — board can't run dry
On empty-frontier claim, `replenish()` seeds from steering organs (priority):
red rep atoms (1.2) → observation queue (0.9) → helm vision gap (0.5+gap/2).
`seed_board` dedups against non-done+non-abandoned titles.

### 5.6 Board ceiling
`board_ceiling()` = Malcolm `open_board_tasks.max` (24) − margin (4) = 20.
`_apply_seed` seeds only up to headroom, highest-value first (never breaches the
wall). `trim_board_to_ceiling` abandons lowest-priority excess (ABANDONED =
disposable, re-seedable). Wired into claim + `task_board trim` CLI.

### 5.7 Auto-reconcilers (run at claim)
- `reconcile_stale_pain_tasks` — closes pain-verdict tasks whose pain is dispositioned.
- `reconcile_stale_rep_tasks` — closes "Fix N red rep atom(s): X" whose feature is
  0-red in the latest run (ghost tasks).
These call `complete_task` directly and are NOT training-gated (system auto-closes).

### 5.8 Concurrency / editor
`core/editor_scheduler.py` — file-locked exclusive editor access (`get_editor_state`,
`_read/_write_state`). Board mutations are `@_locked` under a file lock.

---

## 6. TRAINING SUBSYSTEM

### 6.1 Curriculum (`core/curriculum.py`, `docs/curriculum/curriculum.json`)
A feature graduates K→PhD (7 bands, 54+ checkpoints). `enroll(feature)` creates
`docs/gauntlet/features/<slug>/transcript.json` AND mints a tier-0 starter rep
battery (via `rep_engine.build`). `brief`/`submit` checkpoints; PhD defense =
exit to observation. `core/faculty.py` writes new exams from the studio's scars
(propose→gate→promote).

### 6.2 Rep engine (`core/rep_engine.py`) — resolution through repetition
- **Atom** = `{id, feature, tier, kind, probe:{type, ...spec}, desc, provenance}`.
  `_atom_id` = hash(feature, probe_type, spec).
- **10 probe types** (`PROBES`): `glob_nonempty`, `file_contains`, `tree_contains`
  (multi-root: searches Source/ AND `core/game_code_generator.py` — credits the
  generator), `tree_lacks`, `json_valid`, `file_md5_not`, `beats_registered`,
  `graph_status`, `envelope_axis`, `feel_metric`.
- **8 generators** (`GENERATORS`): `gen_assets`, `gen_code_reflection` (UPROPERTY
  used-in-cpp + UCLASS component spawned, H-21/H-34), `gen_h_rules`,
  `gen_eliminations`, `gen_dsl_fidelity`, `gen_envelope`, `gen_feel`,
  `gen_curriculum` (enrollment → identity atoms).
- **Tiers** (`TIER_NAMES`): 0 exists · 1 behaves · 2 measures · 3 perceptual ·
  4 comparative. Promotion (`PROMOTE`): 8-run ≥95% streak, ≥100 reps/tier.
- **Collapse rep gate** (`REP_GATE`): eligible iff ≥ min(200, atoms×25) reps AND
  the last 8 runs each ≥95%. Advisory unless `CHIMERA_ENFORCE_REP_GATE=1`; the
  training gate hardens it at collapse.
- Commands: `tend` (refresh + run all atoms, ~500+ verdicts/pass, promote),
  `build`, `status`, `gate --feature X`, `prune` (`prune_to_current` drops stale
  atoms). Ledger: `docs/world/reps.db`.

### 6.3 The Trainer (`core/trainer.py`, `core/trainables/`, `docs/objectives/`)
Evolve DATA features; never author them. Three-part split:
- **domain** (`core/trainables/<f>.py`: `seed`/`mutate`/`measure` → FACTS only):
  `economy`, `creature`, `brain`, `brain_cpu`, `brain_gpu`, `walker`, `walker_gpu`.
- **objective** (`docs/objectives/<f>.json`, LLM-authored, ≥1 `maximize` term):
  `economy`, `creature`, `brain`, `brain_gpu`, `walker` (+ `*.trained.json` winners).
- **trainer** (generic; 26k–37k evals/sec CPU). Backend auto-select: `measure_batch`
  present → GPU (`brain_gpu` + `core/mjcf.py`, mujoco-warp, whole pop × N restarts
  in one kernel, ZERO in-rollout CPU syncs, 2,358 evals/s @ 16,384 worlds).
- **Laws:** iterate the objective never the artifact; you CANNOT train CODE (UBT ≈
  6 min/eval); score N randomized restarts keep the WORST (`robustness`);
  morphology is NOT GPU-batchable; the exploit IS the product (`pinned()` names the
  ridden walls). Gait witness: `core/gait.py` (Hildebrand footfall + periodicity).

### 6.4 Matter model (grown anatomy → UE5)
`core/matter.py` (Cellular-Potts adhesion) · `core/limb.py` (skeleton axis +
radial tissue) · `core/rig.py` (THE SPINE: brain-driven flesh) · `core/terrarium.py`
+ `evolve.py` (bounded L-system genome→skeleton→mesh) · `core/bake.py` /
`bake_to_ue5.py` (marching-cubes → GLB → live editor Nanite via MCP).

---

## 7. VERIFICATION & EVIDENCE

### 7.1 Evidence hierarchy (descending authority)
1. Engine hard facts — MCP queries (read-backs, bounds, transforms, actor lists).
2. Telemetry — `core/telemetry_probe.py --soak 30` (crash/fps/growth; measure
   FOREGROUNDED — background throttle freezes fps + all Niagara/anim sim).
3. MCP screenshot — `control_editor screenshot mode=editor_viewport` (never desktop;
   now includes composited UMG/Slate HUDs cropped to the viewport).
4. LM text/vision — tertiary; the adopted model (`lm_gateway.resolve_model`).
5. Automated observation — the TRUE collapse (`graphify_record observe
   --derived-from <simtest_id>`).

### 7.2 MCP transport
Working client: `telemetry_probe.MCPStdioClient` (node CLI → bridge WebSocket
127.0.0.1:8090/8091). `core/mcp_client.py` HTTP:3000 is a stale door (docstring
corrected). Pathways/traps: `docs/MCP_PATHWAYS.md`. Plugin: `Plugins/McpAutomationBridge/`.

### 7.3 Automated playtest
`core/sleepwalker.py` + `core/witness.py` play PIE beat scripts (`docs/beats/`);
observer=agent-sim (CHIMERA_AGENT_SIM sentinel). `core/collapse_proxy.py`:
MODE B `--tend` (nightly, `observed_provisional`) / `sweep` (holistic accept).
`core/rehearsal.py` decides the next move over graph priors (ALREADY-DONE demotion
+ dead-end veto table). Both consult the training gate before collapse.

### 7.4 Anti-fiction discipline (verify-don't-trust)
A subagent/self "success" is a CLAIM. Verify with: `git diff` (additive +
internally consistent), `rep_engine tend` (green for the RIGHT reason),
compile-plausibility by analogy. The COIN formalizes it: claim↔evidence both ways.
Verified-by-injection is not playable (H-14).

---

## 8. CAPCOM & THE LEAD/SUBAGENT MODEL

### 8.1 CAPCOM (`core/capcom.py`, `docs/OPERATOR_INBOX.md`)
Push channel over `capcom.db` (append-only signals + watermark + hash-idempotent
inbox). `brief` (unread + live git/board/phase/heading) · `tell` / edit inbox
(reach operator) · `post`/`post_safe` (subsystems, retry-on-SQLITE_BUSY) ·
`ack`/`search`/`log`/`prune`. Posters: preflight (reads), postflight, task_board
claim/done, training gate. Agent-agnostic (not Claude-Code-reliant).

### 8.2 Pi orchestration model (the `LEAD_AGENT_PROMPT` / `SUBAGENT_PROMPT` docs were removed 2026-07-25; current onboarding: `ChimeraEngine/ONBOARDING.md`)
Pi calls ONE **lead agent** = the CAPCOM operator. The lead dispatches **focused
subagents** (one task = one trained piece), watches the lifecycle via CAPCOM
(claim → training block/waiver → completion), VERIFIES each completion
independently, integrates only what survives, commits verified work. Subagent
lifecycle is fully surfaced to the lead through CAPCOM signals.

---

## 9. MALCOLM — THE CONTAINER (`core/malcolm.py`, `docs/envelope.json`)

Edge-of-chaos regulator: 15 walls in bands `[min, max]` with provenance
(researched/measured/design/existing/provisional).

| Axis | Family | Band | Unit |
|---|---|---|---|
| frame_time_ms | hardware | [·, 16.6] | ms |
| vram_gb | hardware | [·, 12.0] | GB |
| system_memory_gb | hardware | [·, 12.0] | GB |
| audio_voices | hardware | [·, 32] | concurrent |
| open_board_tasks | systemic | [3, 24] | tasks |
| atoms_per_battery | systemic | [1, 400] | atoms |
| decomposition_depth | systemic | [1, 3] | levels |
| coupling_degree_k | systemic | [1, 4] | systems |
| generated_loc | systemic | [·, 19100] | lines |
| generated_files | systemic | [·, 230] | files |
| graph_nodes | systemic | [·, 5,000,000] | nodes |
| heuristics_per_night | systemic | [·, 2] | candidates |
| interacting_systems_per_slice | experience | [3, 7] | systems |
| active_dots | experience | [2, 24] | NPCs |
| engine_surprise_rate_per_week | experience | [2, 20] | surprises/wk |

CLI: `status | check | admit | tune | fit`. `gate_envelope` BLOCKS on a MEASURED
breach. Nightly BREATH (`tune`) proposes wall changes (never self-applied) into
`pending_adjustments`. Admission control (`admit`) pre-checks a delta.

---

## 10. CIRCADIAN / DREAM / GARDENER / DECOMPOSITION

- **Circadian** (`core/circadian.py`): Dawn wake / Day build / Dusk Will / Night
  dream. `tick --run` runs the night iff due.
- **Dream loop** (`core/dream_loop.py`): nightly orchestrator — distills failures +
  surprises (`core/heuristic_distiller.py`) into ≤2 candidate heuristics →
  `docs/PENDING_HEURISTICS.md`; runs `rep_engine tend`, `rep_engine`/gardener tends,
  history-book rewrite, Dream Report (`docs/DREAM_REPORT.md`).
- **Gardener** (`core/gardener.py`): DELEGATED to automation — auto-rules the
  pending queue (doc-organ self-promote, gate-organ queue, subsumed tombstone).
  Automated veto-after outranks all; machine signals final.
- **Decomposition** (`core/decomposer.py`, `docs/decomposition_templates.json`):
  evidence-indicted compound target → parts (one board task + footprint + not_scope
  + rep atom each, dependency-edged); monolith guard blocks the bare parent.
- **Graph hygiene** (`core/graph_compactor.py`): archive-never-delete; apply manual.
- **Surprise capture**: `graphify_record surprise --context --reality --source`.
- **Spiral forks** (`core/spiral_forks.py`): 3 sacrificial research briefs
  (conservative/alternative/wild); winner proceeds, losers' autopsies recorded.

---

## 11. LM STUDIO INTEGRATION (`core/lm_gateway.py`)

Single endpoint arbitrated across PROCESSES via a fair FIFO file-queue
(`docs/world/lm_queue/`). All generation call sites route through `lm_urlopen`
(critic/solver/spiral_forks/ralph_loop/coin_verifier/generator_guard).
- **Model is ADOPTED, never pinned/loaded**: `resolve_model()` reads whatever LM
  Studio has resident and retargets the request. `NoModelLoaded` if none — NO JIT
  fallback (a fallback = a pinned model in a hat; evicts other GPU clients).
- Serializes by default; `CHIMERA_LM_CONCURRENCY=N` raises in-flight slots.
- **Never gate on `llm`/`vlm`/`capabilities.vision`** (wrong for these builds).
- `status` (which model) · `evict` (manual VRAM free, never automatic).
- Vision (`Python/lmstudio_client.py`): images go to the RESIDENT model — no
  reroute, no vision-model var. (The old `CHIMERA_VISION_MODEL` reroute JIT-loaded
  a second multi-GB model next to the resident one; removed 2026-07-17. Loading a
  sighted model is the operator's job.) Token budget
  `CHIMERA_LM_MAX_TOKENS` (default 32768, cap 131072), ×2 on reasoning-dump retry
  (H-3), timeout 600s. Latency ~20 tok/s — batch behind a deterministic pre-filter.

---

## 12. THE MEMBRANE (`core/membrane.py`)

Runs any command in a sealed git worktree (uncommitted changes via `git stash
create`) PLUS a copy of gitignored `docs/world/`, then re-fingerprints live and
proves nothing leaked (MEASURES containment). `run [--burn] | list | diff | apply
| burn`. Use to probe infra — `solver`/`critic`/`coin_verifier` MUTATE live
(`--no-execute` stops executing, not writing). Not a network isolation (cell wall,
not Faraday cage).

---

## 13. AGENT QUALIFICATION (`core/gauntlet.py`, `docs/GAUNTLET.md`)

7 verified stations → earns `journeyman` (required for `capable_only` lanes).
Artifact checkpoints (orientation.md, research.md, …), resumable across turns.
Check labels are self-teaching (carry a live example id). `credentials.json`
holds roles; `_capable_authorized` reads it directly (no gauntlet import).

---

## 14. MODULE INVENTORY (143 in `core/`)

**Pipeline:** dsl_game_parser, dsl_grammar_validator, dsl_mcp_bridge,
asset_generator, asset_config, audio_sourcer, game_code_generator,
incremental_generator, build_orchestrator, ubt_builder, build_validator,
playtest_runner, generate_antlr_parser, interpreter, pathway_to_dsl.
**Gates/verify:** gates, postflight, preflight, result_grader,
research_gate, generator_guard, witness_gate,
visual_gate, training_gate, coin_verifier, research_enforcement,
research_auth, cpp_lint, validator, validation_reporter, build_validator.
**Board/agents:** task_board, agent_tunnel, editor_scheduler, wellspring,
gauntlet, curriculum, faculty.
**Training:** rep_engine, trainer, trainables/*, mjcf, gait, gait_mj, evolve,
terrarium, matter, limb, rig, bake, bake_to_ue5, creature/brain/walker domains.
**Graph/data:** world_store, dna_sqlite_backend, graphify_interface,
graphify_record, graphify_query_cli, graph_compactor, graph_linker, graph_weaver,
history_book, roadmap, horizon.
**Steering:** helm, capcom, malcolm, circadian, rehearsal, ripener, decomposer,
dream_loop, heuristic_distiller, gardener, collapse_proxy, sleepwalker, witness,
witness_runner, spiral_forks, fractal_spiral.
**Verify/telemetry:** telemetry_probe, sand_surface_telemetry, radiometry_probe,
mcp_client, visual_verifier, bloodhound, regression, metronome.
**LM/infra:** lm_gateway, membrane, unblock, solver, critic, context_package,
doc_audit, groundskeeping_floor.
**Cast/orchestration:** muse, scholar, visionkeeper, herald, trailer,
perpetual_orchestrator, game_generation_orchestrator, dsl_workflow_orchestrator,
code_generation_orchestrator, ralph_loop_harness, backlog_burn, fix_stalled,
chaos, ether, lumen_rig, uat_packager, testkit, restore_deleted_files,
archive_old_mutations, *_demo. **Tests:** test_*.py (25+).

---

## 15. ENVIRONMENT VARIABLES

| Var | Effect |
|---|---|
| `CHIMERA_RESEARCH_GATE` / `_WITNESS_GATE` / `_VISUAL_GATE` / `_TRAINING_GATE` / `_COIN_GATE` | `warn` softens block→warn |
| `CHIMERA_GENERATOR_GUARD` | `warn` softens the generator guard |
| `CHIMERA_ENFORCE_REP_GATE` | `1` hardens the advisory rep gate |
| `CHIMERA_TASK_CLAIM_TTL` | stale-claim reap seconds (default 7200) |
| `CHIMERA_LM_MODEL` | legacy pin — normally ignored: the gateway adopts the resident model |
| `CHIMERA_LM_MAX_TOKENS` / `CHIMERA_LM_CONCURRENCY` | LM token budget / in-flight slots |
| `CHIMERA_DNA_BACKEND` | `json` reverts DNA graph off SQLite |
| `CHIMERA_AGENT_SIM` | sleepwalker automated-verification sentinel |

---

## 16. INVARIANTS & LAWS

1. **No fallback ladders.** A gate failure exits non-zero; never substitute a fake
   default or continue silently.
2. **Typed recording only** (`record_*`); wrong keys → `unknown_*` junk (blocked).
3. **Fix the generator, never generated C++;** development flows top-down.
4. **Bare 'blocked' forbidden** — evidence or a reasoned waiver, always.
5. **Train the piece you worked** — enforced at task closure, domain-appropriate.
6. **Train DATA (evolve), author CODE** — you cannot train what needs a UBT build.
7. **Evaluate honestly** — N randomized restarts, keep the worst.
8. **Verify, don't trust** — every self-report is a claim; a green atom on broken
   code is fiction, reverted.
9. **The generator is the source of truth** — rep atoms credit it.
10. **The board can't run dry** (wellspring) and **can't exceed the wall** (ceiling);
    tasks are disposable.
11. **Automated observation is the true collapse;** human verification is removed.
12. **The model is adopted, never pinned/loaded;** the operator decides what runs.
13. **Probe infra in a membrane** — LM call sites mutate live state.
14. **Git:** master only, by-path, state the SHA; never feature branches; exclude
    `DefaultEngine.ini`.
15. **Machine signals are final** — automated rejection outranks every other signal.
