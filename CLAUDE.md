# Chimera — Project Manual

> DSL-Driven Game Generation Orchestrator for Unreal Engine 5.8.
> Takes a formal DSL spec → generates compilable UE5 C++ + assets through a 7-stage automated pipeline.
> **MANDATORY GATES** at every stage. No fallback ladders. No silent continuation.

> **ULTIMATE GOAL:** The mechanical gates (GPA thresholds, build success, MCP verifications) are means to an end: creating a game that—based on holistic automated assessment and AAA-quality benchmarks—would have a high percentage rate of being enjoyable to a human as compared with other triple-A level games in terms of detail and scope. **All human verification requirements are removed; the system's automated evaluation (sleepwalker simulations, telemetry, result grading, and AI judgment) is the measure of whether this goal has been achieved.**

> **Less capable model or unsure?** Follow `E:\PythonChimera\SUCCESSOR_RUNBOOK.md` EXACTLY — recipes, not principles. Improvise nothing.

## NEW AGENT? START HERE (in order)
0. **The studio steers itself toward the seed.** Preflight [0] reads system time -> circadian PHASE (Dawn wake / Day build / Dusk Will / Night dream; call `python -m core.circadian tick --run` each cycle — runs the night IFF due, else a no-op). Preflight [0.7] is the HELM (`core/helm.py`): it ast-parses `CHIMERA_VISION.py` (the SEED / true north) into the vision's systems, measures how far each is realized in the live project, and turns seed−state into this cycle's HEADING — Contain / Fix / Graduate / Build (the vision gap) / Verify / Polish / Consolidate. Work the recommended focus unless you have a sharper reason; see the ranked gap with `python -m core.helm targets`.
1. `cd E:\PythonChimera\Chimera` then `python -m core.preflight` — live state: graph health, GPA, loop board, pending research, last run, environment, **and section [4.5]: the previous generation's Will, open phantom pains, and Dream Report candidates awaiting automated observation**. The brief now OPENS with the **CAPCOM operator channel** — unread signals pushed by subsystems and by you (`python -m core.capcom tell "..."`, or just edit `docs/OPERATOR_INBOX.md`). `python -m core.capcom brief` is the standalone read any agent or harness can run — it is not Claude-Code-dependent.
2. Read `E:\PythonChimera\task_progress.md` — session handoff log — then **claim your lane from the TASK LIST (the single entry): `python -m core.task_board claim --agent <your-id>`**. The claim opens your tunnel session, reserves the editor mode your task declares, and prints your work packet (recipe, matching H-heuristics, study guide, open pains). It only grants work whose resource footprint is disjoint from every other active agent — stay inside your footprint. **`capable_only` lanes require an EARNED credential: run THE GAUNTLET (`python -m core.gauntlet enter --agent <your-id>`, docs/GAUNTLET.md) — seven verified stations, artifact checkpoints, resumable across turns; the only way out is through the exit gate.**
3. Work under the Contract: typed recording only (`record_*` helpers), fix generator templates never generated C++, and answer the Frame Audit (`Chimera/docs/RESULT_GRADING_RUBRIC.md`) before declaring anything complete. Heartbeat long work: `python -m core.agent_tunnel heartbeat --agent <id>` (refreshes claim + editor in one call). **FEATURES GO TO SCHOOL: every feature you carry should be enrolled in the Curriculum (`python -m core.curriculum enroll --feature X`, docs/GAUNTLET.md) — K->PhD bands of checkpoints that interrogate it from every angle of game-dev humanity; submit checkpoints as you work (`brief`/`submit`); its PhD defense is the exit to observation.**
4. **Exit the tunnel before you finish** — `python -m core.task_board done --agent <id> --id tb-N --result "<verbatim evidence>"` (or `block --reason` / `release --note`; bare 'blocked' is forbidden). Then `python -m core.postflight --phase "..." --result "<UBT verbatim>" --inheritance "<=3 sentences" --phantom-pain "..." --pain-verdict "<id>:confirmed|refuted|still-open"` (it shouts about any tunnel you left open, and now REFUSES a research-less session — cite what you looked up with `--researched "..."` or record a reasoned `--research-waiver "..."`; the Research Depth Protocol covers TECHNICAL/INFRASTRUCTURE decisions too, not just game assets) and update `task_progress.md` for the next agent.

## Generation Protocol (Circadian rhythm — see docs/GENERATION_PROTOCOL.md)
- **TRAIN it, don't hand-tune it** (2026-07-14; full spec: `docs/TRAINING_PROTOCOL.md`). If a feature is **DATA** (prices, damage, yields, morphology, layouts, spawn tables), do NOT tune it by reasoning — an LLM manages ~20 edits/hour and `core/trainer.py` does ~30,000 evals/sec. Write a **domain** (`core/trainables/<f>.py` — `seed`/`mutate`/`measure`, reporting FACTS only), write an **objective** (`docs/objectives/<f>.json` — what GOOD means, in physics not taste, **with at least one `maximize` term or you get a satisficer**), then train it **inside a membrane** and read the **PINNED** walls. A degenerate winner is not a failure — it is the optimiser auditing your spec at 35kHz and finding the hole you would have defended in review. **Iterate the objective, never the artifact.** If a feature is **CODE** (needs a UBT build to evaluate: ~6 min/eval), it is NOT trainable — author it, one at a time.
- **EVALUATE IT HONESTLY, or you are training LUCK** (2026-07-14; the hardest lesson this studio has learned). **One rollout from one initial condition is not a measurement — it is a coin toss.** Proven: the celebrated 13.52-body-length walker had `periodicity 0.25` (no repeating cycle at all) and lost 5.5 body lengths to a **one-micron** nudge of its start height. That is Lyapunov divergence: no attractor → no limit cycle → **no gait**. The GA had spent 80,000 evaluations selecting lucky dice, and under honest physics that champion scores **worse than an untrained brain**. THE RULE: score every genome from **N randomized starts and keep the WORST** (report `robustness` = worst/mean; a real limit cycle is ~1.0, a fraud is ~0). It costs Nx compute — **that is what the GPU is for**. And check the physics you inherited: `TORQUE=22 N·m` on a 0.622 kg creature is **35 N·m/kg** (a human hip is 3) and flung the body **3.4 km** into the air; pybullet's constraint servo merely *contained* that violence instead of NaN-ing, which is *why* there was never a limit cycle to find. **A body permanently in flight has no contact to build a gait out of.**
- **GPU for the population, CPU for development** (2026-07-14). `core/trainables/brain_gpu.py` + `core/mjcf.py` run the **whole population × every restart in ONE `mujoco-warp` kernel**: measured **2,358 evals/sec at 16,384 worlds (6.95 s, 1.5 of 24 GiB, GPU at 39 °C)** vs pybullet's **70 evals/sec with 8 P-cores pinned at thermal limit** — 33.7×, and the P-cores go idle. The trainer picks the backend automatically (`measure_batch` present → GPU, Pool unused). **THE ONE RULE: nothing reads back from the GPU inside the rollout loop** — the previous attempt did 1,575 CPU↔GPU syncs per batch and ran **300× SLOWER than the CPU**. **pybullet can never do this**: Bullet has promised OpenCL physics on its own forums since **2006**, and the 2022 Quickstart Guide still says *"We **will** expose Bullet 3.x running on GPU"* — future tense, sixteen years on. Caveat: **`mujoco-warp` batches N copies of ONE model, so morphology is NOT GPU-trainable** — evolve bodies on CPU MuJoCo, brains on GPU.
- **Probing infrastructure? Put it in a MEMBRANE.** `python -m core.membrane run --burn -- <cmd>` runs it in a sealed copy and proves it touched nothing live. The LM call sites are NOT read-only: `solver`/`critic`/`coin_verifier` mutate task_progress.md and the DNA graph, and `--no-execute` stops solver *executing* its plan, not *writing* it. Never drive them with fabricated input against the live studio.
- **Capture surprises live**: on any automation correction, dead-end, or expectation violation, run `python -m core.graphify_record surprise --context "..." --reality "..." --source agent|engine`. These feed the nightly distiller.
- **Fork before researching a feature** (preferred): `python -m core.spiral_forks --feature X --use-lm` — 3 briefs (conservative/alternative/wild), winner proceeds, losers' autopsies are recorded tuition. Forks never touch live state.
- **Dream loop** (`python -m core.dream_loop`, manual or scheduled): distills failures+surprises into ≤2 candidate heuristics per night, staged in `docs/PENDING_HEURISTICS.md`.
- **Gardener authority is DELEGATED to automation (amendment 2026-07-07)**: `python -m core.gardener --tend` (runs inside every `dream_loop`) auto-rules the pending queue — doc-organ heuristics with a draft rule + evidence self-promote; gate-organ approvals queue for a capable cycle to implement; subsumed entries tombstone. **Automated veto-after**: edit any entry's status to `vetoed` and the next tend demotes it (doc line removed, automated veto recorded). Machine signals are final; automated rejection permanently outranks every other signal.
- **Automated observation is the true collapse — and it arrives HOLISTICALLY**: the system playtests (via sleepwalker simulations, telemetry probes, and result grading) and provides a holistic assessment of the whole experience. The agent ATTRIBUTES evidence across the queue with provenance (`observe --derived-from <simtest_id> --quote "..."` for direct simulation mentions, `--tacit` for exercised-but-unmentioned, untouched if not exercised) and originates verdicts based on automated evidence. Rejections → `needs_refinement`, first-priority dream fodder. Loops show `[DONE*]` until automated observation is complete. **Full automation amendment (2026-07-07): human verification requirements are removed.** One holistic acceptance sweeps accepted-tacit across every queue feature with exercise evidence (`python -m core.collapse_proxy --from-simtest <id> --valence accepted`); a rejection indicts only what the simulation evidence names. Between cycles, the Sleepwalker collapses evidenced features nightly (`--tend`, status `observed`) so the queue never dams development — the automated system's assessment is final.
- **Sleepwalker (the balance of automation and control)**: `python -m core.sleepwalker --beats docs/beats/<demo>.beats.json --session <name>` — the AI playtester plays PIE beat scripts and records SimPlaytest evidence (observer=agent-sim; CHIMERA_AGENT_SIM sentinel enforces automated verification). `python -m core.rehearsal --decide` simulates candidate next-moves over graph priors and writes a veto-table-backed NEXT item. Automated signals are final in the distiller. See docs/SLEEPWALKER_DESIGN.md.
- **Rep engine (resolution through repetition, 2026-07-12)**: features earn collapse by ACCUMULATED constraint reps, not one good night — `python -m core.rep_engine tend` (runs inside every dream_loop) refreshes atom batteries (generated from assets, UPROPERTY reflection, encodable H-rules, Elimination nodes, DSL tokens), runs every headless atom (~500 verdicts/pass), promotes tiers on 8-run >=95% streaks. Gate: >=200 reps + streak (advisory at collapse; `CHIMERA_ENFORCE_REP_GATE=1` hardens). Record proven negatives: `python -m core.graphify_record elimination --feature X --boundary "..." --survives "..."` (add `--probe-json` to mint a permanent regression atom); postflight accepts `--eliminated "<feature> : <boundary> : <evidence>"`.
- **Decomposition Process (2026-07-12)**: when evidence indicts something COMPOUND, do not work it as a blob and do not decide the fix out-of-band — run `python -m core.decomposer run --target X --kind <template> --evidence <simtest/elim ids>`. It breaks the target into parts via docs/decomposition_templates.json (grow the JSON, never the engine), seeds one board task per part (footprint, deps, not_scope siblings), mints a rep atom per part, blocks any bare-parent task (the parts get processed, never the system), and records a Decomposition node. Parts then ride the normal conveyor: claim -> tunnel -> work -> reps -> beats -> collapse.
- Graph hygiene: `python -m core.graph_compactor --dry-run` (archive-never-delete; apply is always manual).
- **[H-1, auto-promoted 2026-07-07]** A C2039 missing-member error in ProceduralGenerated/ means template drift — emit the accessor in the same generator change that emits its test.
- **[H-2, auto-promoted 2026-07-07; amended 2026-07-13]** Never verify from desktop screenshots — capture via MCP control_editor screenshot mode=editor_viewport, which renders the viewport regardless of window focus, and (since the 2026-07-13 Slate-widget capture fix, McpAutomationBridge_ControlHandlers.cpp/McpAutomationBridge_UiHandlers.cpp) now also includes composited UMG/Slate HUDs during PIE, cropped to just the viewport — full_editor_window is only needed for whole-editor-chrome captures now, not to see a HUD (docs/MCP_PATHWAYS.md #32).
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
- **[H-35, auto-promoted 2026-07-12]** Investigate elimination_audio_visual_sync telemetry_accessors; verify test harne
- **[H-36, auto-promoted 2026-07-13]** Implement missing input bindings and verify actor registration.
- **[H-37, auto-promoted 2026-07-13]** Verify beat spawn location distances and pawn navigation constraints.
- **[H-38, auto-promoted 2026-07-14]** Investigate correction feature; verify test harness and beat registration.
- **[H-40, auto-promoted 2026-07-15]** Investigate actors bp_verb_; verify test harness and beat registration.
- **[H-41, auto-promoted 2026-07-15]** Investigate bad costless; verify test harness and beat registration.
- **[H-42, auto-promoted 2026-07-15]** Investigate blocker draft; verify test harness and beat registration.
- **[H-43, auto-promoted 2026-07-15]** Investigate chaos chaos_organ; verify test harness and beat registration.
- **[H-44, auto-promoted 2026-07-15]** Investigate fixes generationsubsystem; verify test harness and beat registration
- **[H-45, auto-promoted 2026-07-15]** Investigate bridge dsl; verify test harness and beat registration.

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
| `core/rep_engine.py` | Resolution through repetition: constraint-atom batteries (docs/rep_batteries/), rep ledger (docs/world/reps.db), shaping tiers, collapse rep-gate (`tend`/`status`/`gate`/`prune`) |
| `core/history_book.py` + `docs/HISTORY_BOOK.md` | THE BOOK: everything learned, 8 chapters (constitution/eliminations/surprises/verdicts/wills/rep-milestones/drift/breakdowns), FTS-searchable: `python -m core.history_book search --query X` — rewritten nightly by dream_loop |
| `core/decomposer.py` + `docs/decomposition_templates.json` | THE BREAKDOWN PROCESS: evidence-indicted compound targets become board-processed PARTS (one task+footprint+not_scope+rep atom each, dependency-edged; monolith guard blocks the bare parent). `python -m core.decomposer run --target X --kind input_rig --evidence <ids>` — the parts get processed, never the system |
| `core/malcolm.py` + `docs/envelope.json` | THE CONTAINER (edge-of-chaos regulator): 15 walls in bands [min,max] (hardware/systemic/experience) with provenance (researched/measured/design/existing/provisional), emergence reserves, admission control (`admit`), gate_envelope BLOCKER, envelope rep atoms, and the nightly BREATH (`tune`: engine-surprise gauge vs band -> pending wall proposals, never self-applied). `python -m core.malcolm status\|check\|admit\|tune\|fit` |
| `core/lm_gateway.py` | The single LM Studio endpoint arbitrated across PROCESSES: a fair FIFO file-queue (docs/world/lm_queue/) so concurrent agents wait their turn instead of dogpiling into timeouts. All generation call sites (critic/solver/spiral_forks/ralph_loop/coin_verifier/generator_guard) route through `lm_urlopen`. Serializes by default (kills the timeout); `CHIMERA_LM_CONCURRENCY=N` raises in-flight slots if LM Studio is configured for parallel/batching. **THE MODEL IS ADOPTED, NEVER PINNED AND NEVER LOADED (2026-07-14): `resolve_model()` reads whatever LM Studio currently has resident and retargets the outgoing body at it** — so changing the model for the whole operation is just "load a different model in LM Studio", no config/env/code. **If nothing is loaded it raises `NoModelLoaded` — it does NOT fall back to a default and JIT-load it.** A "fallback" is a pinned model wearing a hat: it means silently pulling a multi-GB model the operator never asked for. The operator decides what runs; the studio only adopts. Never re-pin a model id and never make the request path load or evict: the box shares ONE GPU with other clients (a `pi` agent harness), and two clients each forcing a different model evict each other mid-load and BOTH die with "Engine protocol startup was aborted". Vision-capability is the operator's responsibility — **never gate on LM Studio's `llm`/`vlm` or `capabilities.vision` flags, they are WRONG for these builds** (vision was added after the fact); `Python/lmstudio_client.py` used to reroute screenshots to a different "vision-capable" model on that bad flag — removed. `python -m core.lm_gateway status` prints which model will be used; `evict` manually frees VRAM (never automatic). |
| `core/membrane.py` | **THE MEMBRANE** (2026-07-14, the human's insight) — run ANY command in a sealed copy of the studio, then PROVE it touched nothing outside. `python -m core.membrane run -- python -m core.solver --blocker "X"`. A boundary is what makes a cause ATTRIBUTABLE: in biology the vesicle is what lets a replicator keep what it makes (no inside/outside → no individual → nothing for selection to act on); in engineering the same boundary is what lets you attribute an outcome to a change rather than to the world. **Seals a git worktree of your CURRENT tree (uncommitted changes included, via `git stash create`) PLUS a copy of `docs/world/` — which is gitignored, so a worktree ALONE would leave the DNA graph, rep ledger, history and CAPCOM stores SHARED WITH LIVE.** That is the difference between a membrane and a costume. Then it re-fingerprints the live side and shouts if anything moved — it MEASURES its containment instead of asserting it (it caught `pi` writing to the live graph on its first run). Also a discovery tool: it tells you what a command actually WRITES. **Use it to probe infrastructure — `solver`/`critic`/`coin_verifier` are NOT read-only, and `--no-execute` stops solver EXECUTING its plan, not WRITING it** (2026-07-14: a fabricated blocker reached task_progress.md, got auto-pushed, and `pi` began working the phantom). Does not isolate the network — a cell wall, not a Faraday cage. `run [--burn]` · `list` · `diff` · `apply` · `burn` |
| `core/trainer.py` + `core/trainables/` + `docs/objectives/` | **THE TRAINER — build features by EVOLVING them, not authoring them** (2026-07-14; full spec: `docs/TRAINING_PROTOCOL.md`). **The LLM writes the CONSTRAINTS; it never turns the crank.** SCENARIO → [LLM] writes `docs/objectives/<f>.json` → [TRAINER] 26,000–37,000 evals/sec MEASURED, no LLM in the loop → WINNER + **PINNED WALLS** → [LLM] repairs the objective → repeat. The LLM sits at the TOP and the BOTTOM, never the middle (it manages ~20 edits/hour; the trainer does ~30,000/sec — six orders of magnitude). THREE-PART SPLIT: a **domain** (`core/trainables/<f>.py`: `seed`/`mutate`/`measure`) reports **FACTS, never opinions**; an **objective** (LLM-authored JSON) says which facts are GOOD; the **trainer** is generic and knows what neither an economy nor a creature *is*. **YOU CAN TRAIN DATA; YOU CANNOT TRAIN CODE** — a C++ system costs ~6 min/eval (LLM + UBT + PIE) vs 1.5 ms for morphology: seven orders of magnitude, so push the game OUT of code and INTO data. **THE DSL IS THE GENOME** — this studio built a genotype→phenotype pipeline before it knew that is what it was. **THE EXPLOIT IS THE PRODUCT**: a degenerate winner is the optimiser auditing your spec at 35kHz; `pinned()` names the walls it is riding. **Never encode taste — encode PHYSICS.** The creature objective never mentions legs; legs are the ANSWER. `python -m core.trainer --domain core.trainables.economy --objective docs/objectives/economy.json` |
| `core/trainables/brain_gpu.py` + `core/mjcf.py` | **THE GPU BACKEND — and it is a CORRECTNESS fix, not a speed one** (2026-07-14). The trainer auto-selects it (`measure_batch` present → whole population in one kernel, Pool unused). `mjcf.from_bones()` turns a bone tree into MJCF — **XML nesting IS the kinematic tree**, which deletes most of the six bugs that killed the Newton attempt (no add_body/add_link, inertia from geom density, a solver that doesn't explode in free fall; when the tree was malformed MuJoCo **refused to load and named the missing joint**, where pybullet silently dropped 19 of 20 links). `brain_gpu.measure_batch()` runs **population × N_RESTARTS worlds in ONE kernel**, brain included (3 Warp kernels — **ZERO CPU↔GPU syncs in the rollout**, the previous attempt did 1,575/batch and ran 300× SLOWER than CPU). Contact is derived **geometrically** from capsule pose (`z − |axis_z|·halflen − r`), which yields per-bone **footfall for free** — so `periodicity` and `duty_factor` are first-class GPU measures. THREE LOAD-BEARING SETTINGS, each measured: **self-collision OFF** (pybullet parity — with it on, 65 contacts on a flat plane), **`integrator="implicitfast"`** (Euler NaN'd at t=3.74 s), **`armature=0.001`** (rotor inertia: without it, z-max **3,433 m**; with it, 0.66 m). `njmax`/`nconmax` are **PER WORLD** (192/64 here — measured max 48/9; passing `nworld*192` asks for 750× too much and OOMs 24 GiB). **Morphology is NOT GPU-trainable** — mujoco-warp batches N copies of ONE model. |
| `core/gait.py` | **DOES IT WALK, OR DOES IT JUST ARRIVE?** `python -m core.gait --trained docs/objectives/brain.trained.json [--png ...]`. A distance is a receipt; the trainer hands you the same receipt for a walk, a bound, and a seizure that drifts downfield. This prints the **Hildebrand footfall diagram** + duty factor + suspension + **PERIODICITY** (autocorrelation of the footfall signal: 1.0 = a metronome, 0.0 = a seizure) and classifies the gait. **A foot is DISCOVERED, never declared** — nothing ever told this creature it has feet, so a foot is defined behaviourally as *a link that touches the ground SOME of the time*; that definition hands you both failure modes free, as the two ends of the range (duty ~1.0 = a **SLED**, duty ~0 = cargo). It is what caught the fraud: the champion scored **periodicity 0.25**. |
| `docs/THE_EVOLUTION_ENGINE.md` | **WHAT THE WHOLE MACHINE CAN NOW BUILD** — the capstone. The trainer + terrarium + membrane + GPU backend + gait witness assembled into one thing: *a general engine for evolving game content against machine-checkable objectives.* Read it for the POSSIBILITIES (a bestiary grown overnight, co-evolution, terrain curricula, the whole game as evolvable data), the two substrates (CPU for morphology, GPU for control — and why both), and the LIMITS stated as plainly as the frontier (you can't train CODE, bodies aren't GPU-batchable, one rollout is a coin toss, open-ended evolution is unsolved). Every claim is grounded in a measured result. |
| `core/matter.py` + `core/limb.py` + `core/rig.py` + `core/bake.py` + `core/bake_to_ue5.py` + `docs/THE_MATTER_MODEL.md` | **THE MATTER MODEL — grown anatomy RENDERS IN UE5 and MOVES BY ITS BRAIN (rungs 0–2 + headless spine, 2026-07-14); in-editor animation onward is design.** `core/rig.py` is THE SPINE (from the system audit): the real evolved body is fleshed, auto-skinned to the terrarium bones, and posed by the TRAINED BRAIN's own gait (`--mode walk`, FK + linear blend skinning) — the skeleton is one shared object across physics/flesh/render, so the creature that learned to walk is the creature you see move. Closed the audit's two biggest gaps (real body #2, brain-drives-flesh #1). `core/bake.py` marching-cubes each tissue's occupancy into three watertight nested meshes (skin/muscle/bone) → a UE5-importable GLB; `core/bake_to_ue5.py` drives the LIVE editor over the MCP bridge (import → `nanite_rebuild_mesh` → spawn → screenshot) and grown flesh rendered+shadowed as native Nanite geometry, witnessed in-editor. The substrate *beneath* the evolution engine: what everything is made OF. A universal library of typed "bricks" (muscle/bone/skin/wood/stone/water), each carrying only the game-relevant variables, assembled bottom-up and **baked** into native UE5 (the human's LEGO metaphor, made precise). **Built & proven:** `core/matter.py` — differential adhesion (Cellular Potts) self-sorts scrambled bricks into a layered limb, 2D (`--mode cross2d`) and 3D with a typed tendon connector (`--mode limb3d`), each against a failing uniform control. `core/limb.py` — the INTEGRATION: voxelizes the terrarium's L-system skeleton as a **frozen** bone axis and lets adhesion wrap the flesh → the first CONTINUOUS limb (skeleton = AXIS, adhesion = RADIAL TISSUE; neither alone — adhesion pinches a free rod via Rayleigh-Plateau). **Design (rung 2+):** generate-then-bake (bricks = GENOTYPE, Nanite/Chaos-Flesh = PHENOTYPE); three budgets never conflated (**LOOK** Nanite / **MOVE** coarse rig / **BEHAVE** local agents); adaptive granularity by **coalesce/fracture**; §12 = the expansion (the human player character, and a world). |
| `core/terrarium.py` + `core/evolve.py` + `docs/TERRARIUM_DESIGN.md` | **THE TERRARIUM** — a grown organism, sealed in glass. A genome (a bounded parametric L-system) → skeleton → mesh (`tubes` = generalised cylinders; `blob` = capsule SDFs + smooth-min + marching cubes). 447 bytes → 238 bones in 1.2 ms → 3,808 triangles. **Rule 2 TOTALITY**: `grow()` is a `for` loop with a hard symbol cap — no `while`, no recursion, and no genome (valid, malformed, or adversarial) can make it fail to terminate; runaway growth is not guarded against, it is **unrepresentable**. **Rule 3 DETERMINISM**: pure function, byte-identical output. **Rule 1 MEMBRANE**: imports NOTHING from the studio (ast-asserted). **A TREE IS A RECURSION; A CREATURE IS A CASCADE** — `A -> ...A` is self-similar and can only ever be a plant; an animal is a finite staged program where each symbol fires once and hands off to a *different* one (Hox: positional identity). `( )` = bilateral mirror. |
| `core/world_store.py` | SQLite world-model substrate (millions of nodes, FTS + R-tree; sub-ms search) |
| `core/capcom.py` + `docs/OPERATOR_INBOX.md` | **CAPCOM — the operator channel** (agent-agnostic, NOT Claude-Code-reliant; 2026-07-13). The studio is mostly PULL — state reaches the operating agent only if it remembers to run preflight/git/helm. CAPCOM is the PUSH inverse: subsystems + the human drop signals, any operating agent reads ONE situational brief. `python -m core.capcom brief` (unread signals + live git/editor/phase/heading/board snapshot) · `tell "..."` OR edit `docs/OPERATOR_INBOX.md` to reach the operator (no tool needed) · `post`/`post_safe` for subsystems · `ack`/`search`/`log`/`prune`. Signals live append-only in world_store (`docs/world/capcom.db`, FTS-searchable). Led into `preflight`; `postflight` + `task_board` claim/done post to it. |
| `core/research_gate.py` | **Research Gate** (2026-07-13) — makes the workflow's mandated research non-skippable: postflight REFUSES a research-less session unless it cites `--researched` sources or records a reasoned `--research-waiver` (both auditable; waivers feed the distiller). Explicitly covers TECHNICAL/INFRASTRUCTURE decisions, not just game assets (Gate 1's Technical-Documentation source type). Surfaced by preflight's `[research]` pulse. `CHIMERA_RESEARCH_GATE=warn` softens block→warn. |
| `core/generator_guard.py` | **Generator Guard** (2026-07-13) — LM-judged (via `lm_gateway`, H-3) block on hand-edits to generator-owned C++ (silently clobbered on regen). Deterministic pre-filter (only when a `ProceduralGenerated/` file is dirty AND the generator wasn't) + ONE batched LM call + stem-match fallback. preflight LM-free heads-up; postflight refuses unless `--generator-waiver`. `CHIMERA_GENERATOR_GUARD=warn` softens. |
| `core/witness_gate.py` | **Witness Gate** (2026-07-13) — a feature can't be recorded `verified`/`observed` without a SimPlaytest/telemetry/observation node this session, `--witnessed "<obs+id>"`, or `--witness-waiver` (H-14: a compile is not proof). `CHIMERA_WITNESS_GATE=warn` softens. |
| `core/visual_gate.py` | **Visual Gate** (2026-07-14) — a verified/observed feature additionally requires a recorded **LM screenshot analysis** (`visual_verification/*` node via `core/visual_verifier.py`), `--visual-analysis`, or `--visual-waiver`. The local model must have LOOKED at it. `CHIMERA_VISUAL_GATE=warn` softens. |
| `core/training_gate.py` | **Training Gate** (2026-07-14, the human's goal: "train everything, one piece at a time") — training is FORCED at the ledger transition: `verified` requires curriculum ENROLLMENT + a rep battery with reps begun; `observed`/collapse requires the FULL rep gate (>=200 reps + 8-run >=95% streak, `rep_engine.rep_gate`). Un-enrolled verification is refused even with research/witness/visual satisfied; `--training-waiver` records honest exceptions. Wellspring build lanes say ENROLL FIRST. `CHIMERA_TRAINING_GATE=warn` softens. |
| `core/coin_verifier.py` | **THE COIN** (2026-07-14, the human's design) — the semantic top layer above the existence gates: every verification has two faces, **HEADS = the claim, TAILS = the evidence**; pre-programmed prompts feed both to the LM Studio agent, which judges **both directions** (evidence proves claim / claim honest to evidence). Not the same coin -> postflight refused. Proven live: catches overclaims (compile+unit-tests ≠ "playtested and seen"), passes honest claims. CLI: `python -m core.coin_verifier --claim ... --evidence ...` or `--feature X` (auto-assembles faces). `CHIMERA_COIN_GATE=warn` softens. |
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
| LM text/vision (whatever model you have loaded) | tertiary evidence only, when explicitly requested | the model is **adopted** from LM Studio at call time (`core.lm_gateway.resolve_model`) — never pinned; load a different model to change it everywhere. `gate_lm_available` only requires that *some* model is loaded |
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
| `gate_lm_available` | LM Studio reachable with SOME model RESIDENT (any id — it gets adopted; nothing is auto-loaded) | BLOCKER |
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
