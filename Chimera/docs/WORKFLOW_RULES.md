> **DEPRECATED** — This document describes the old approach.
> Read `AGENT_ONBOARDING.md`, `DECISION_METHOD.md`, and `EMERGENT_WORKFLOW.md` instead.
> The thought chain is at `docs/THOUGHT_CHAIN.md`.

# Chimera — Complete Workflow Rules & Requirements

> Every rule and requirement of the project workflow, in one place. Source of
> truth is CLAUDE.md + the enforcement code (core/gates.py, the postflight gate
> stack, the task board). This is the consolidated reference.

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

## 1. Onboarding — do these in order, every session
1. **Circadian tick:** `python -m core.circadian tick --run` (runs the night iff due).
2. **Preflight:** `python -m core.preflight` — reads live state; OPENS with the
   CAPCOM operator channel. `python -m core.capcom brief` is the agent-agnostic read.
3. **Read the handoff:** `E:\PythonChimera\task_progress.md`.
4. **Claim your lane:** `python -m core.task_board claim --agent <your-id>` (the
   single entry point; a claim opens your tunnel + reserves your editor mode).
5. **`capable_only` lanes require an EARNED credential:** run THE GAUNTLET
   (`python -m core.gauntlet enter --agent <id>`) — 7 verified stations.

## 2. The Contract (how you work)
- **Typed recording ONLY.** Never hand-write mutation detail dicts — use the
  `record_*` helpers (`record_feature`/`record_pathway`/`record_loop`/
  `record_phase`/`record_grade`/`record_build`). Wrong keys silently write
  `unknown_*` junk.
- **Fix generator TEMPLATES, never generated C++.** Development flows top-down:
  game content → the DSL spec (`tests/dsl_grammar/*.chimera`); code shape →
  `core/game_code_generator.py`; the pipeline regenerates the C++.
- **Answer the Frame Audit** (`docs/RESULT_GRADING_RUBRIC.md`) before declaring
  anything complete: proxy-vs-target, author-as-judge, artifact-vs-generator.
- **Heartbeat long work:** `python -m core.agent_tunnel heartbeat --agent <id>`.
- **Exit before you finish:** `python -m core.task_board done --agent <id> --id
  tb-N --result "<verbatim evidence>"` (or `block --reason` / `release --note`;
  **bare 'blocked' is forbidden** — give evidence or a reasoned waiver, never a
  silent skip). Then run **postflight** and update `task_progress.md`.

## 3. Mandatory Hard Gates (core/gates.py — BLOCKERs)
Exit code 1 on violation; pipeline halts.

| Gate | Enforces |
|---|---|
| `gate_no_junk_nodes` | Zero `unknown_*` junk in the graph |
| `gate_gpa_not_critically_falling` | Cumulative GPA ≥ 1.0 |
| `gate_provenance_complete` | Every mutation carries provenance |
| `gate_node_count_bounded` | Graph under the 5M runaway-backstop ceiling |
| `gate_lm_available` | LM Studio reachable with SOME model resident (adopted, never auto-loaded) |
| `gate_no_stale_trees` | Only `Chimera/` under `Source/` |
| `gate_build_succeeded` | UBT must return 0 |
| `gate_auto_fixer_attempted` | Build failures must have been auto-fix-attempted |
| `gate_playtest_no_failures` | Zero test failures before Stage 7 |
| `gate_git_clean` | No unexpected dirty tree at gate points |
| `gate_envelope` | No MEASURED breach of a Malcolm container wall |
| `stage_7_visual` | All 4 scene-verification layers pass |

## 4. The Postflight Enforcement Stack (feature verify/observe)
Fires when recording a feature `verified`/`observed`/`observed_provisional`, in
this order. Each has a `CHIMERA_*_GATE=warn` softener; each refuses unless
satisfied or given a reasoned waiver.

1. **Research Gate** (`CHIMERA_RESEARCH_GATE`) — cite `--researched` sources or a
   `--research-waiver`. Covers TECHNICAL/INFRASTRUCTURE decisions, not just assets.
2. **Generator Guard** (`CHIMERA_GENERATOR_GUARD`) — LM-judged block on hand-edits
   to generator-owned C++ (silently clobbered on regen); `--generator-waiver`.
3. **Witness Gate** (`CHIMERA_WITNESS_GATE`) — needs a SimPlaytest/telemetry/
   observation node this session, `--witnessed`, or `--witness-waiver` (a compile
   is not proof).
4. **Visual Gate** (`CHIMERA_VISUAL_GATE`) — needs a recorded LM screenshot
   analysis, `--visual-analysis`, or `--visual-waiver`. The model must have LOOKED.
5. **Training Gate** (`CHIMERA_TRAINING_GATE`) — `verified` needs curriculum
   ENROLLMENT + reps begun; `observed`/collapse needs the FULL rep gate
   (≥200 reps + 8-run ≥95% streak). `--training-waiver`.
6. **The Coin** (`CHIMERA_COIN_GATE`) — HEADS = the claim, TAILS = the evidence;
   the LM judges BOTH directions (evidence proves claim / claim honest to
   evidence). Not the same coin → refused.

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
- **TRAIN it, don't hand-tune it.** If a feature is DATA (prices, damage, yields,
  morphology, layouts, spawn tables), EVOLVE it: write a domain
  (`core/trainables/<f>.py`), an objective (`docs/objectives/<f>.json`, ≥1
  `maximize` term), train inside a membrane, read the PINNED walls. **Iterate the
  objective, never the artifact.** The LLM writes the CONSTRAINTS; it never turns
  the crank (~20 edits/hr vs ~30,000 evals/sec). **You CANNOT train CODE** (a UBT
  build ≈ 6 min/eval).
- **Evaluate honestly or you train LUCK.** One rollout from one start is a coin
  toss — score N randomized restarts, keep the WORST (`robustness`). Audit
  inherited physics constants.
- **GPU for the population, CPU for development.** `mujoco-warp` batches the whole
  population in one kernel; NOTHING reads back from the GPU inside the rollout
  loop. Morphology is NOT GPU-trainable (batches N copies of ONE model).
- **Features go to school (curriculum).** Enrollment auto-mints a tier-0 starter
  rep battery. Submit K→PhD checkpoints as you work; the PhD defense is the exit
  to observation.
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
- **Never hand-edit `AGENTS.md`** (repo root — NOT `docs/AGENTS.md`, which does not exist and never did) without the user raising it (finalized). The wrong path is why its stale "human Gardener approves EVERY heuristic" line sat protected and unrepaired: a rule aimed at a file that isn't there guards nothing and hides everything.

## 7. Task Board & Resource Rules
- **Claims are resource-conflict-aware:** a task is granted only if its footprint
  is DISJOINT from every active claim. Stay strictly inside your footprint.
- **Three real shared resources:** `pie` (the one PIE session — only PIE-driving
  lanes take it), `generator` (`game_code_generator.py` — generator-owned fixes
  share it), and file globs (same-subtree serializes). Headless work never claims
  `pie`.
- **The board cannot run dry** while the seed is unrealized — the WELLSPRING
  refills it (red atoms → observation queue → helm gap).
- **The board is CAPPED at Malcolm's `open_board_tasks` wall** — the wellspring
  seeds only up to headroom; **tasks are DISPOSABLE** (`task_board trim` culls the
  lowest-priority excess to ABANDONED, re-seedable later).
- **Stale/ghost tasks auto-close at claim time:** pain-verdict tasks whose pain is
  already dispositioned, and "Fix red atom" tasks whose feature is already green.
- **Claims auto-reap** past the heartbeat TTL (2h); you cannot force-release
  another agent's lane.

## 8. Verification & Evidence Rules
- **The gate is the RESULT grade** (`core/result_grader.py`, zero LM dependency):
  A ≥90 · B ≥75 · C ≥60 · F <60. C/F → back to research. Build failure auto-grades F.
- **Evidence hierarchy (by authority):** engine-state hard facts (MCP queries) >
  telemetry (measure FOREGROUNDED — background throttle freezes fps AND sim) >
  MCP screenshot (`control_editor screenshot mode=editor_viewport`, NEVER desktop
  captures) > LM text/vision (tertiary) > **automated observation** (the true
  collapse).
- **VERIFY, don't trust** — every sub-agent/self report is a CLAIM to check with
  the studio's own instruments (git diff, rep re-measure, compile-plausibility).
  A green rep atom on broken code is FICTION and gets reverted.
- **Verified-by-injection is not playable** (H-14) — real player input must drive
  it end-to-end, read back in PIE, before staging for observation.
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
- **The LM call sites are NOT read-only** — `solver`/`critic`/`coin_verifier`
  mutate `task_progress.md` and the DNA graph; `--no-execute` stops solver
  EXECUTING, not WRITING. Never drive them with fabricated input against live state.

## 11. LM Studio Rules
- **The model is ADOPTED, never pinned and never loaded.** `resolve_model()` reads
  whatever LM Studio has resident. If nothing is loaded it raises `NoModelLoaded`
  — it does NOT fall back and JIT-load. The operator decides what runs.
- **Never re-pin a model id; never make the request path load or evict** — the box
  shares one GPU with other clients.
- **Never gate on LM Studio's `llm`/`vlm`/`capabilities.vision` flags** — they are
  WRONG for these builds.
- All generation routes through `core.lm_gateway.lm_urlopen` (a fair FIFO queue).
  Give LM-dependent commands a long timeout (≥300s) and WAIT; batch N items into
  ONE call behind a deterministic pre-filter + fallback.

## 12. Git / GitHub Rules (delegated ownership)
- **Commit directly to master. NEVER open feature branches** (a branch the user
  can't see reads as lost work). Archive-tag stray branches before deleting.
- **Commit + push without asking each time**; surface only destructive actions.
- **State the exact branch + commit SHA on every push.**
- **Commit BY-PATH; exclude `DefaultEngine.ini`.**
- **Keep the tree clean, maintain `.gitignore`.**
- **Never skip hooks / bypass signing** unless the user explicitly asks.

## 13. CAPCOM (operator channel)
- The studio is mostly PULL; CAPCOM is the PUSH inverse. Subsystems + the human
  drop signals; the operating agent reads ONE brief. Agent-agnostic (not
  Claude-Code-reliant).
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
- **0** — pipeline complete, all gates passed.
- **1** — gate violation; pipeline blocked, cannot proceed.
- **2** — unexpected error.

## 16. Standing Operating Principles
- **Full fixes, not partial** — do complete fixes even when large; don't disable
  or shim around root causes. Verify "installed" by INVOKING it, not by a file's
  existence.
- **Verify-first, then execute fully** — verify ambiguity/big actions before
  running; once aligned, execute decisively and don't re-ask.
- **Prove it, don't assert it** — report outcomes faithfully; if tests fail, say
  so with the output; state done-and-verified plainly, without hedging.
- **No fabrication, ever** — if work doesn't exist or you're blocked, say so.
