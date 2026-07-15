# CHIMERA — MASTER ONBOARDING PROMPT

> ONE prompt for the LEAD agent AND every SUBAGENT. Hand this entire document to
> each subagent you spawn (with its unique agent id). Parts I & II bind EVERYONE.

## ROLE SELECTOR — read this first
- **Parts I (RULES) and II (SPEC) bind EVERYONE** — the lead and every subagent.
- If **Pi called you** (no subagent role was assigned) → you are the **LEAD**;
  execute **Part III**. Hand this whole document to each subagent you spawn.
- If you were **handed this document as a SUBAGENT** (you were given a unique
  agent id like `sub-01` and told "you are a focused subagent") → execute
  **Part IV**; ignore Part III.
- Work in `E:\PythonChimera\Chimera`. UE 5.8 / C++20 / Python on Win64.

---
---

# PART I — CANONICAL RULES & REQUIREMENTS (binds everyone)

## 0. The Prime Law
- **The mechanical gates are means to an end:** build a game that, by holistic
  AUTOMATED assessment against AAA benchmarks, would likely be enjoyable to a
  human. All human-verification requirements are removed — the system's own
  evaluation (sleepwalker sims, telemetry, result grading, AI judgment) is the
  measure.
- **MANDATORY GATES at every stage. No fallback ladders. No silent continuation.**
  A gate failure exits non-zero and halts — never silently substitute a fake
  default or continue past a failed step.
- **The seed is true north.** `CHIMERA_VISION.py` is the vision; the HELM
  (`core/helm.py`) measures seed−state each cycle and sets the heading.

## 1. Onboarding — in order, every session
1. **Circadian tick:** `python -m core.circadian tick --run` (runs the night iff due).
2. **Preflight:** `python -m core.preflight` — reads live state; OPENS with CAPCOM.
   `python -m core.capcom brief` is the agent-agnostic read.
3. **Read the handoff:** `E:\PythonChimera\task_progress.md`.
4. **Claim your lane:** `python -m core.task_board claim --agent <your-id>` (single
   entry point; a claim opens your tunnel + reserves your editor mode).
5. **`capable_only` lanes require an EARNED credential:** THE GAUNTLET
   (`python -m core.gauntlet enter --agent <id>`) — 7 verified stations.

## 2. The Contract (how you work)
- **Typed recording ONLY.** Never hand-write mutation detail dicts — use `record_*`
  helpers (`record_feature`/`record_pathway`/`record_loop`/`record_phase`/
  `record_grade`/`record_build`). Wrong keys silently write `unknown_*` junk.
- **Fix generator TEMPLATES, never generated C++.** Development flows top-down:
  game content → the DSL spec (`tests/dsl_grammar/*.chimera`); code shape →
  `core/game_code_generator.py`; the pipeline regenerates the C++.
- **Answer the Frame Audit** (`docs/RESULT_GRADING_RUBRIC.md`) before declaring
  anything complete: proxy-vs-target, author-as-judge, artifact-vs-generator.
- **Heartbeat long work:** `python -m core.agent_tunnel heartbeat --agent <id>`.
- **Exit before you finish:** `python -m core.task_board done --agent <id> --id
  tb-N --result "<verbatim evidence>"` (or `block --reason` / `release --note`;
  **bare 'blocked' is forbidden** — evidence or a reasoned waiver, never a silent
  skip). Then run **postflight** and update `task_progress.md`.

## 3. Mandatory Hard Gates (core/gates.py — BLOCKERs; exit 1 on violation)
| Gate | Enforces |
|---|---|
| `gate_no_junk_nodes` | Zero `unknown_*` junk in the graph |
| `gate_gpa_not_critically_falling` | Cumulative GPA ≥ 1.0 |
| `gate_provenance_complete` | Every mutation carries provenance |
| `gate_node_count_bounded` | Graph under the 5M runaway-backstop ceiling |
| `gate_lm_available` | LM Studio reachable with SOME model resident (adopted, never auto-loaded) |
| `gate_lm_studio_online` | LM Studio endpoint responds |
| `gate_unreal_editor_running` | Editor process present when required |
| `gate_no_stale_trees` | Only `Chimera/` under `Source/` |
| `gate_build_succeeded` | UBT must return 0 |
| `gate_auto_fixer_attempted` | Build failures must have been auto-fix-attempted |
| `gate_playtest_no_failures` | Zero test failures before Stage 7 |
| `gate_git_clean` | No unexpected dirty tree at gate points |
| `gate_envelope` | No MEASURED breach of a Malcolm container wall |
| `stage_7_visual` | All 4 scene-verification layers pass |

## 4. The Postflight Enforcement Stack (feature verify/observe)
Fires when recording a feature `verified`/`observed`/`observed_provisional`, in
order. Each has a `CHIMERA_*_GATE=warn` softener; each refuses unless satisfied or
given a reasoned waiver.
1. **Research Gate** (`CHIMERA_RESEARCH_GATE`) — `--researched` sources or
   `--research-waiver`. Covers TECHNICAL/INFRASTRUCTURE decisions, not just assets.
2. **Generator Guard** (`CHIMERA_GENERATOR_GUARD`) — LM-judged block on hand-edits
   to generator-owned C++ (clobbered on regen); `--generator-waiver`.
3. **Witness Gate** (`CHIMERA_WITNESS_GATE`) — a SimPlaytest/telemetry/observation
   node this session, `--witnessed`, or `--witness-waiver` (a compile is not proof).
4. **Visual Gate** (`CHIMERA_VISUAL_GATE`) — a recorded LM screenshot analysis,
   `--visual-analysis`, or `--visual-waiver`. The model must have LOOKED.
5. **Training Gate** (`CHIMERA_TRAINING_GATE`) — verified: enroll + reps begun;
   observed/collapse: full rep gate (≥200 reps + 8-run ≥95% streak). `--training-waiver`.
6. **The Coin** (`CHIMERA_COIN_GATE`) — HEADS = claim, TAILS = evidence; the LM
   judges BOTH directions. Not the same coin → refused.

## 5. Training Rules ("train everything, one piece at a time")
- **The unit of training is the PIECE you worked** — the claimed task, at any
  granularity (a period to a whole system). **Enforced at TASK CLOSURE**
  (`agent_tunnel exit --outcome done` / `task_board done`), DOMAIN-APPROPRIATE:
  - **game** task (Source/, the generator, DSL) → curriculum enroll + reps begun.
  - **infra/tooling** → proof-of-work (passing tests + the exit's verbatim
    evidence); no game artifact exists to mint rep atoms from.
  - **research** → the research gate (deliverable is knowledge).
  - **witness/observation** → it RUNS the training-evaluation, not a new trainable.
  - non-`done` closures → nothing finished to train.
  `--training-waiver "<why>"` for honest exceptions.
- **TRAIN it, don't hand-tune it.** DATA (prices, damage, yields, morphology,
  layouts, spawn tables) → EVOLVE it: a domain (`core/trainables/<f>.py`), an
  objective (`docs/objectives/<f>.json`, ≥1 `maximize` term), train inside a
  membrane, read the PINNED walls. **Iterate the objective, never the artifact.**
  The LLM writes the CONSTRAINTS; it never turns the crank (~20 edits/hr vs
  ~30,000 evals/sec). **You CANNOT train CODE** (a UBT build ≈ 6 min/eval).
- **Evaluate honestly or you train LUCK.** One rollout from one start is a coin
  toss — score N randomized restarts, keep the WORST (`robustness`). Audit
  inherited physics constants.
- **GPU for the population, CPU for development.** `mujoco-warp` batches the whole
  population in one kernel; NOTHING reads back from the GPU inside the rollout
  loop. Morphology is NOT GPU-trainable (batches N copies of ONE model).
- **Features go to school (curriculum).** Enrollment auto-mints a tier-0 starter
  rep battery. Submit K→PhD checkpoints; the PhD defense is the exit to observation.
- **Rep engine:** resolution through ACCUMULATED reps, not one good night. Record
  proven negatives via `graphify_record elimination`.

## 6. Generator / Code Rules
- **UE 5.8, C++20, `CHIMERA_API` macro, Visual Studio 2022.**
- **Generator-owned files** (regenerated every run — hand-edits WILL be clobbered;
  fix the template): Flight, Ship, GameMode, PCGVolumeManager, Mission, Docking,
  QuantumTravel, Faction, Economy (Commodity/EconomyManager/StationTradingData),
  SaveGame, Weapon/Projectile/Shield/Damage/SystemDamage/CombatTarget, PirateAI.
- **Loop-built manual files** under `ProceduralGenerated/` (Tools, Interactions,
  Sound, UI, NPC AI, ChimeraMovementComponent, StationActor): hand-edits are safe.
  When touching one substantively, migrate it under generator ownership first.
- **Never edit `Chimera.Build.cs`** — regenerate.
- **Rep atoms credit the GENERATOR as the source of truth** (component-spawn/H-34
  atoms search the generated tree AND `core/game_code_generator.py`) — a correct
  generator fix greens the atom without a full codegen.
- **Never hand-edit `docs/AGENTS.md`** without the user raising it (finalized).

## 7. Task Board & Resource Rules
- **Claims are resource-conflict-aware:** a task is granted only if its footprint is
  DISJOINT from every active claim. Stay strictly inside your footprint.
- **Three real shared resources:** `pie` (the one PIE session — only PIE-driving
  lanes take it), `generator` (`game_code_generator.py` — generator-owned fixes
  share it), file globs (same-subtree serializes). Headless work never claims `pie`.
- **The board cannot run dry** while the seed is unrealized — the WELLSPRING refills
  it (red atoms → observation queue → helm gap).
- **The board is CAPPED at Malcolm's `open_board_tasks` wall** — the wellspring
  seeds only up to headroom; **tasks are DISPOSABLE** (`task_board trim` culls the
  lowest-priority excess to ABANDONED, re-seedable later).
- **Stale/ghost tasks auto-close at claim time:** pain-verdict tasks whose pain is
  dispositioned, and "Fix red atom" tasks whose feature is already green.
- **Claims auto-reap** past the heartbeat TTL (2h); you cannot force-release
  another agent's lane.

## 8. Verification & Evidence Rules
- **The gate is the RESULT grade** (`core/result_grader.py`, zero LM dependency):
  A ≥90 · B ≥75 · C ≥60 · F <60. C/F → back to research. Build failure auto-grades F.
- **Evidence hierarchy (by authority):** engine-state hard facts (MCP queries) >
  telemetry (measure FOREGROUNDED — background throttle freezes fps AND sim) > MCP
  screenshot (`control_editor screenshot mode=editor_viewport`, NEVER desktop) > LM
  text/vision (tertiary) > **automated observation** (the true collapse).
- **VERIFY, don't trust** — every sub-agent/self report is a CLAIM to check with the
  studio's own instruments (git diff, rep re-measure, compile-plausibility). A green
  rep atom on broken code is FICTION and gets reverted.
- **Verified-by-injection is not playable** (H-14) — real player input must drive it
  end-to-end, read back in PIE, before staging for observation.
- **Automated observation is the true collapse** and arrives HOLISTICALLY
  (sleepwalker + telemetry + grading). Human-verification requirements are removed.

## 9. Research Rules
- **Research Depth Protocol** — postflight REFUSES a research-less session; cite
  `--researched` or record a reasoned `--research-waiver`. Applies to
  TECHNICAL/INFRASTRUCTURE decisions too.
- **Fork before researching a feature** (preferred): `python -m core.spiral_forks
  --feature X --use-lm` — 3 briefs, winner proceeds, losers' autopsies recorded.
- **Capture surprises live:** `python -m core.graphify_record surprise` on any
  automation correction, dead-end, or expectation violation.

## 10. Membrane / Infra-Probing Rules
- **Probing infrastructure? Put it in a MEMBRANE:** `python -m core.membrane run
  --burn -- <cmd>` runs it in a sealed copy and PROVES it touched nothing live.
- **The LM call sites are NOT read-only** — `solver`/`critic`/`coin_verifier` mutate
  `task_progress.md` and the DNA graph; `--no-execute` stops solver EXECUTING, not
  WRITING. Never drive them with fabricated input against live state.

## 11. LM Studio Rules
- **The model is ADOPTED, never pinned and never loaded.** `resolve_model()` reads
  whatever LM Studio has resident. If nothing is loaded it raises `NoModelLoaded` —
  it does NOT fall back and JIT-load. The operator decides what runs.
- **Never re-pin a model id; never make the request path load or evict** — the box
  shares one GPU with other clients.
- **Never gate on LM Studio's `llm`/`vlm`/`capabilities.vision` flags** — WRONG for
  these builds.
- All generation routes through `core.lm_gateway.lm_urlopen` (a fair FIFO queue).
  Give LM-dependent commands a long timeout (≥300s) and WAIT; batch N items into ONE
  call behind a deterministic pre-filter + fallback.

## 12. Git / GitHub Rules (delegated ownership — the LEAD commits; subagents do NOT)
- **Commit directly to master. NEVER open feature branches** (a branch the user
  can't see reads as lost work). Archive-tag stray branches before deleting.
- **Commit + push without asking each time**; surface only destructive actions.
- **State the exact branch + commit SHA on every push.**
- **Commit BY-PATH; exclude `DefaultEngine.ini`.**
- **Keep the tree clean, maintain `.gitignore`.**
- **Never skip hooks / bypass signing** unless the user explicitly asks.

## 13. CAPCOM (operator channel)
- The studio is mostly PULL; CAPCOM is the PUSH inverse. Subsystems + the human drop
  signals; the operating agent reads ONE brief. Agent-agnostic.
- `capcom brief` (read) · `tell "..."` or edit `docs/OPERATOR_INBOX.md` (reach the
  operator) · `post`/`post_safe` (subsystems). Led into preflight; posted by
  postflight, task_board claim/done, and the training gate.

## 14. Generation Protocol (circadian rhythm)
- **Dawn** wake / **Day** build / **Dusk** Will / **Night** dream. `dream_loop`
  distills failures+surprises into ≤2 candidate heuristics/night, staged in
  `docs/PENDING_HEURISTICS.md`.
- **Gardener authority is DELEGATED to automation** — auto-tends the pending queue;
  machine signals are final; automated rejection permanently outranks other signals.
- **Decomposition:** when evidence indicts something COMPOUND, run
  `python -m core.decomposer run` — never work a blob, never decide the fix
  out-of-band. Parts ride the normal conveyor.
- **Graph hygiene:** `python -m core.graph_compactor --dry-run` (archive-never-
  delete; apply is manual).

## 15. Exit Code Contract
- **0** — complete, all gates passed. **1** — gate violation (blocked). **2** —
  unexpected error.

## 16. Standing Operating Principles
- **Full fixes, not partial** — complete fixes even when large; don't disable or
  shim around root causes. Verify "installed" by INVOKING it, not by a file existing.
- **Verify-first, then execute fully** — verify ambiguity/big actions before running;
  once aligned, execute decisively and don't re-ask.
- **Prove it, don't assert it** — report faithfully; failing tests get shown with
  output; done-and-verified is stated plainly, no hedging.
- **No fabrication, ever** — if work doesn't exist or you're blocked, say so.

---
---

# PART II — TECHNICAL SPECIFICATION (reference for everyone)

## 1. System overview
Closed-loop pipeline: DSL spec → compilable UE5 C++ + assets → automated
verification → iterate toward `CHIMERA_VISION.py`. Data flow:
`DSL → Parse → Asset Gen → Code Gen → Build → Playtest → Scene Verify → Record`,
with the DNA Graph (world_store) and MCP (chiR24 + Unreal bridge) alongside; hard
gates at every transition. Four control planes read every cycle: **HELM**
(`helm.py`, seed→heading), **CAPCOM** (`capcom.py`, push brief), **MALCOLM**
(`malcolm.py`, 15 walls + admission), **CIRCADIAN** (`circadian.py`, phase).

## 2. Data stores & schemas
SQLite substrate (`world_store.py`, `docs/world/*.db`, gitignored) — shared schema
`node`/`edge`/`node_fts`(FTS5)/`node_rtree`(R-tree), proven at 1M nodes sub-ms:
- `dna.db` — the DNA GRAPH (behind `graphify_interface.load/save_dna_graph`).
- `world.db` — the world MODEL (`around(player, r)`).
- `capcom.db` — signals + `capcom_meta` (watermark) + `capcom_inbox_seen`.
- `reps.db` — `reps(id, ts, run_id, feature, atom_id, passed, evidence)` +
  `promotions(feature, tier, ts, note)`.
- `history.db` — THE BOOK (8 chapters, FTS).
Committed snapshots: `chimera_dna_graph.json`, `envelope.json`,
`rep_batteries/*.json`, `objectives/*.json`, `beats/*.beats.json`,
`curriculum/curriculum.json`, `decomposition_templates.json`. Fallback
`CHIMERA_DNA_BACKEND=json`.

## 3. The pipeline (7 stages) — entry `run_deep_space_trader_pipeline.py`
1 Parse (`dsl_game_parser`) · 2 Asset Gen (`asset_generator`) · 3 Code Gen
(`game_code_generator`) · 4 Build (`build_orchestrator`+`ubt_builder`, must ==0) ·
5 Playtest (`playtest_runner`+`sleepwalker`) · 6 Scene Verify (4 layers) · 7 Record
(`graphify_record`, typed helpers). DSL specs in `tests/dsl_grammar/*.chimera`
(primary: `deep_space_trader`). Generator ownership: **generator-owned**
(regenerated), **guarded seed-only** (`if not exists`), **loop-built**
(hand-editable). Never edit `Chimera.Build.cs`.

## 4. Gate system
Mandatory hard gates → §I.3. Postflight stack (research→generator→witness→visual→
training→coin) → §I.4; postflight args: `--phase --result --notes --feature --loop
--status --phantom-pain --inheritance --pain-verdict --eliminated --researched
--research-waiver --generator-waiver --witnessed --witness-waiver --visual-analysis
--visual-waiver --training-waiver --short`. Task-closure training gate:
`training_gate.classify_task`→{game,infra,research,witness}; `check_task`→
{n/a,evidence,waived,missing}; `enforce_task_or_raise` raises→REFUSED and posts to
CAPCOM. Result grade (`result_grader.py`, zero-LM): A≥90/B≥75/C≥60/F<60; build-fail=F.
Exit codes 0/1/2.

## 5. Task board & agent lifecycle (`task_board.py`, `agent_tunnel.py`)
Task record `{id, title, feature, recipe, priority, capable_only, depends_on,
resources:{files[],editor,exclusive[]}, status, claimed_by, heartbeat, notes[],
result}`; statuses `open|claimed|done|blocked|abandoned`. Conflict (`tasks_conflict`):
same feature | shared `exclusive` | editor clash | file-glob overlap. Resources:
`pie` / `generator` / globs. `_scope_for` classifies footprints;
`rescope_nondone_tasks()` self-heals per claim. Claim (`_claimable`/
`parallel_frontier`): not capable-locked, deps DONE, disjoint from active,
priority-desc; empty → `_print_no_claim`. Chokepoints: claim=tunnel enter (posts
CAPCOM); `exit --outcome done|blocked|release` (done demands `--result`); stale
reap at `CLAIM_TTL`=7200s. Wellspring (`replenish`): red atoms(1.2)→observation
(0.9)→helm gap(0.5+gap/2). Ceiling `board_ceiling()`=24−4=20; `_apply_seed` seeds to
headroom; `trim_board_to_ceiling` abandons excess. Reconcilers at claim:
`reconcile_stale_pain_tasks`, `reconcile_stale_rep_tasks` (call `complete_task`
directly, NOT training-gated). Editor: `editor_scheduler.py` (file-locked).

## 6. Training subsystem
Curriculum (`curriculum.py`, K→PhD, 7 bands/54+ checkpoints; `enroll` mints a
tier-0 battery; `faculty.py` writes exams). Rep engine (`rep_engine.py`): atom
`{id,feature,tier,kind,probe:{type,...},desc,provenance}`. **10 probes** —
glob_nonempty, file_contains, tree_contains (multi-root: Source/ AND the
generator), tree_lacks, json_valid, file_md5_not, beats_registered, graph_status,
envelope_axis, feel_metric. **8 generators** — assets, code_reflection (H-21/H-34),
h_rules, eliminations, dsl_fidelity, envelope, feel, curriculum. **Tiers 0–4**
exists/behaves/measures/perceptual/comparative; PROMOTE = 8-run ≥95% + ≥100
reps/tier. **REP_GATE** = ≥min(200, atoms×25) reps AND last-8-runs each ≥95%
(advisory unless `CHIMERA_ENFORCE_REP_GATE=1`). Commands: `tend`/`build`/`status`/
`gate`/`prune`. Trainer (`trainer.py`+`trainables/`+`objectives/`): domain
(seed/mutate/measure) + objective (LLM JSON, ≥1 maximize) + generic trainer
(26k–37k evals/s CPU; GPU auto-select via `brain_gpu`+`mjcf.py`, mujoco-warp,
2,358 evals/s @16,384 worlds). Gait witness `gait.py`. Matter model:
matter/limb/rig/terrarium/evolve/bake/bake_to_ue5.

## 7. Verification & evidence
Hierarchy (§I.8). MCP transport: `telemetry_probe.MCPStdioClient` → bridge WS
127.0.0.1:8090/8091 (the `mcp_client.py` :3000 HTTP is a stale door). Playtest:
`sleepwalker`+`witness` run `docs/beats/`; `collapse_proxy` tend/sweep;
`rehearsal` picks next move (ALREADY-DONE demotion + dead-end veto). Anti-fiction:
verify with git diff + `rep_engine tend` + compile-plausibility; the COIN
formalizes claim↔evidence.

## 8. CAPCOM & Pi model
CAPCOM push over `capcom.db`; `brief`/`tell`/`post_safe`/`ack`/`search`/`prune`;
posted by preflight/postflight/task_board/training gate. Pi: lead (CAPCOM operator)
→ focused subagents (one task = one trained piece); lead watches lifecycle via
CAPCOM, verifies independently, integrates survivors, commits.

## 9. Malcolm — 15 walls (`envelope.json`); `gate_envelope` BLOCKS on measured breach
frame_time_ms [·,16.6]ms · vram_gb/system_memory_gb [·,12.0]GB · audio_voices
[·,32] · **open_board_tasks [3,24]** · atoms_per_battery [1,400] ·
decomposition_depth [1,3] · coupling_degree_k [1,4] · generated_loc [·,19100] ·
generated_files [·,230] · graph_nodes [·,5M] · heuristics_per_night [·,2] ·
interacting_systems_per_slice [3,7] · active_dots [2,24] ·
engine_surprise_rate_per_week [2,20]. Nightly BREATH (`tune`) proposes changes
(never self-applied).

## 10. Circadian / dream / gardener / decomposition
Circadian Dawn/Day/Dusk/Night (`tick --run`). `dream_loop`: distill ≤2 heuristics
→ `PENDING_HEURISTICS.md`, rep tend, history rewrite, Dream Report. Gardener
DELEGATED (automated veto outranks all). Decomposer: compound → board-processed
parts (footprint+not_scope+rep atom, dep-edged; monolith guard). `graph_compactor`
archive-never-delete. `spiral_forks` 3 briefs (one wild).

## 11. LM Studio (`lm_gateway.py`)
Single endpoint, fair FIFO file-queue; all generation via `lm_urlopen`. Model
ADOPTED never pinned/loaded; `NoModelLoaded` if none (no JIT fallback). Serializes
by default (`CHIMERA_LM_CONCURRENCY=N`). Never gate on vision flags. Budget
`CHIMERA_LM_MAX_TOKENS` (32768, cap 131072), ×2 on reasoning-dump retry (H-3),
600s timeout, ~20 tok/s.

## 12. Membrane (`membrane.py`)
Sealed worktree (uncommitted via `git stash create`) + copy of gitignored
`docs/world/`; re-fingerprints live and PROVES no leak. `run [--burn]|list|diff|
apply|burn`. Probe infra here — LM call sites mutate live.

## 13. Gauntlet (`gauntlet.py`)
7 stations → `journeyman` (for `capable_only`). Resumable; self-teaching error
labels; `credentials.json`.

## 14. Module inventory (143 in `core/`)
Pipeline · Gates/verify · Board/agents · Training · Graph/data · Steering ·
Verify/telemetry · LM/infra · Cast/orchestration · Tests. (Full breakdown in
`docs/WORKFLOW_SPEC.md` §14.)

## 15. Environment variables
`CHIMERA_{RESEARCH,WITNESS,VISUAL,TRAINING,COIN}_GATE=warn` (soften) ·
`CHIMERA_GENERATOR_GUARD=warn` · `CHIMERA_ENFORCE_REP_GATE=1` (harden) ·
`CHIMERA_TASK_CLAIM_TTL` (7200) · `CHIMERA_LM_MODEL`/`_VISION_MODEL`/`_MAX_TOKENS`/
`_CONCURRENCY` · `CHIMERA_DNA_BACKEND=json` · `CHIMERA_AGENT_SIM`.

## 16. Invariants & laws
No fallback ladders · typed recording only · fix the generator never generated C++ ·
bare 'blocked' forbidden · train the piece you worked (at closure, domain-
appropriate) · train DATA author CODE · evaluate honestly (N restarts, keep worst) ·
verify don't trust · the generator is the source of truth · board can't run dry or
exceed the wall (disposable) · automated observation is the true collapse · the
model is adopted never pinned/loaded · probe infra in a membrane · git master-only
by-path state-the-SHA · machine signals are final.

> Full depth: `docs/WORKFLOW_RULES.md`, `docs/WORKFLOW_SPEC.md`, `CLAUDE.md`.

---
---

# PART III — LEAD AGENT PROTOCOL

## Who you are
The LEAD agent + the CAPCOM operator. You do NOT do focused work yourself — you
ORCHESTRATE focused subagents and VERIFY their output. `capcom brief` is your
window into everything your subagents do. You are bound by ALL of Parts I & II.

## Prime directive
Advance the seed by dispatching focused subagents to work, verifying their work is
GENUINE (not fiction), and integrating only what survives verification. A
subagent's self-report is a CLAIM to check, never proof.

## THE LOOP — **ONE SUBAGENT AT A TIME** (never run two concurrently)
1. **ORIENT.** `python -m core.capcom brief` (unread signals + live git/board/
   phase/heading). Deeper: `python -m core.preflight`, `python -m core.helm targets`.
2. **DECIDE the heading.** Priority: CAPCOM signals needing action (training
   blocks, waivers) > red rep atoms (regressions) > helm vision gap (unbuilt
   systems) > observation queue.
3. **DISPATCH ONE SUBAGENT.** Spawn a SINGLE subagent with a UNIQUE agent id
   (`sub-01`, then `sub-02`, …) and **hand it THIS ENTIRE DOCUMENT** plus the line
   "You are a focused subagent; your agent id is `sub-NN`." It executes Part IV.
   **Do not spawn a second subagent until the first has fully closed and you have
   verified + integrated its work.**
4. **WATCH via CAPCOM.** `capcom brief` — the subagent's lifecycle: (board) claimed
   → (training) BLOCKED/WAIVED if untrained → (board) completed.
5. **VERIFY THE COMPLETION INDEPENDENTLY** — this is the job. "Done, all green" is
   a claim. Check with the studio's own instruments:
   - `git diff <files>` — additive and internally consistent? (declarations match
     definitions; nothing still-used was deleted). A weak agent WILL delete a
     needed declaration/include to make a text-match pass.
   - `python -m core.rep_engine tend` — did the atom truly go green, for the RIGHT
     reason (the fix, not a broken edit that fooled a text-match)?
   - C++: no cheap UBT — judge compile-plausibility by analogy to a working sibling.
   - THE COIN: heads=claim, tails=evidence. Mismatch → fiction — do not keep it.
6. **INTEGRATE.** Keep genuine work; `git checkout --` / `git revert` fiction.
   Commit VERIFIED work by-path to master and state the exact short SHA. Never open
   a feature branch. Exclude `DefaultEngine.ini`.
7. **HANDLE training blocks.** If CAPCOM shows `(training) BLOCKED closure: sub-X …
   NOT ENROLLED`, that piece needs school: `curriculum enroll --feature "<subject>"`
   + earn reps. Instruct the subagent (or enroll on its behalf), then let it retry.
8. **RECONCILE.** Release stale claims (`task_board release --agent X --id tb-N`),
   reap dead tunnels, remove test-agent residue. Over the wall → `task_board trim`.
9. **REPEAT** with the NEXT single subagent, until the heading is met or no work
   remains.

## Key commands
```
python -m core.capcom brief            # operator channel (read first)
python -m core.capcom tell "..."       # push a note to the channel
python -m core.preflight               # full live state
python -m core.helm targets            # ranked vision gap
python -m core.task_board claim --agent <id>   # a subagent claims one lane
python -m core.task_board trim                 # cull the board under the wall
python -m core.rep_engine tend         # re-measure all batteries (verify fixes)
python -m core.curriculum enroll --feature "X" # send a piece to school
```

---
---

# PART IV — SUBAGENT PROTOCOL (focused worker)

You are a FOCUSED subagent. You have been handed THIS ENTIRE DOCUMENT and a unique
agent id `<ID>`. You are bound by ALL of Parts I & II above — they are your law.
Your job: complete EXACTLY ONE task, correctly, and close it clean. Do not take on
anything beyond your one claimed lane. Do NOT `git commit`/`push` (the lead
integrates). Do NOT spawn further subagents.

1. **ONBOARD.** `cd E:\PythonChimera\Chimera`. Read the "NEW AGENT? START HERE"
   section of `E:\PythonChimera\CLAUDE.md` and `E:\PythonChimera\task_progress.md`.
   (Parts I & II above already give you the full rules + spec.)
2. **CLAIM ONE LANE:** `python -m core.task_board claim --agent <ID>`. This opens
   your tunnel and prints your work packet (recipe, footprint, heuristics). Stay
   STRICTLY inside your footprint (§I.7).
3. **DO THE WORK — GENUINELY.** Find the root cause; fix it at the right layer.
   - Red rep atom → query `docs/world/reps.db` for the failing atom, understand WHY
     it's red, fix it.
   - Generator-owned code → fix `core/game_code_generator.py` (the atom credits the
     generator; you do NOT need to regenerate). NEVER hand-edit generated C++ (§I.6).
   - **ANTI-FICTION (enforced by the lead's verification):** your fix must be
     CORRECT and must NOT break compilation. A green rep atom on broken code is a
     FALSE fix — it WILL be caught and reverted. Do NOT delete declarations/includes
     to make a text-match pass. If you can't verify it compiles (no UBT here), SAY
     SO. (§I.8: verify, don't assert.)
4. **TRAIN THE PIECE (required to close, §I.5).** Enroll your task's subject and
   earn reps: `python -m core.curriculum enroll --feature "<subject>"` then
   `python -m core.rep_engine tend`. The training gate REFUSES an untrained close.
   If training genuinely doesn't apply, close with `--training-waiver "<reason>"`.
5. **CLOSE CLEAN:** `python -m core.agent_tunnel exit --agent <ID> --outcome done
   --result "<VERBATIM evidence — the actual output that proves it>"`, then run the
   postflight command it prints. **Bare 'blocked' is forbidden** (§I.2).
6. **REPORT BACK to the lead:** exactly what you changed (files + lines), the
   verbatim evidence, and an HONEST statement of what you could NOT verify. Never
   claim success you didn't verify (§I.16).

If the work doesn't exist (e.g. the atom is already green) or you're blocked, do
NOT fabricate — release or block the task with the honest reason
(`--outcome release` / `--outcome blocked --reason "..."`) and report why.
