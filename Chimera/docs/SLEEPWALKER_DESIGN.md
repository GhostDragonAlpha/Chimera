# The Sleepwalker System — AI playtester + rehearsal engine that advances the game

> **IMPLEMENTED 2026-07-07** (grade A 98.5): M1+M2+M3 shipped — core/witness.py,
> core/sleepwalker.py, core/rehearsal.py, beats/regolith_yard (5/5 clean walk after one
> honest find->fix->verify loop on the jump probe), SimPlaytest/SimulationRollout node
> types, distiller sim_rejection tier, preflight [4.6], constitution amendments live.
> M4 ARMED 2026-07-07 (ChimeraUnblock 00:45 / ChimeraSleepwalk 01:00 / ChimeraDream 02:15; PIE-collision guard + editor self-heal live)
> (pain phase_34195900a1671e58:P1). GUARD FINDING: observe was honor-system only;
> CHIMERA_AGENT_SIM=1 sentinel now technically blocks agent-sim direct observations
> (surprise_1451fd0fc19c66f3 — stronger universal rule is the Gardener's call).
>
> Approved by the Gardener 2026-07-06. Milestones M1-M4 are duty-cycle-sized; M1/M2 capable sessions only.
> Constitution amendment authorized: sim_verified tier, Step-2 branch C-half, nightly sleepwalk rhythm.

## Context

The Gardener wants the primary engine of development to become **an AI playtester that informs what to build next**, with human input as an additive/steering signal — "a balance of automation and control." Today the protocol is human-gated: features stall at `[DONE*]` until the human observes; when queues are empty, duty cycles fall back to pipeline health checks. Tonight proved the seed works: the agent simulated a W-keypress in PIE and measured a 1333uu walk — a playtest without a player. This plan turns that seed into a system with two staged layers (user-confirmed: staged-both; outputs land both in the NEXT list and as graph evidence; full design).

Naming follows the protocol's circadian register: the **Sleepwalker** plays the game at night; the **Rehearsal** engine simulates generations as data to decide what deserves real cycles; both feed the existing **Dream** (distiller). Human observation remains the supreme override — the sim advances work, the human's one sentence can reverse anything (the reversibility pattern already proven in the attribution table).

## What exists to reuse (verified by exploration)

- `core/telemetry_probe.py` `MCPStdioClient` — proven PIE control: `control_editor play/stop_pie`, `simulate_input key_down/key_up` (drives AutoPossess pawns — pathway_attempt_06941e7d0619e72d), `runtime_report`, `get_component_property`, screenshots, BugItGo.
- `[DEMOBEAT]` log convention (Demo/DemoPlayerController.cpp) + the unbuilt `demo_witness` design (DEMO_ARCHITECTURE.md §5 P2 item 4) — beat-timeline JSON from log tail + runtime polls.
- `core/spiral_forks.py` — the candidate→deterministic-rubric→winner-proceeds→loser-autopsy pattern (spiral_forks.py:68–102 scoring; :224–230 autopsy recording). Rehearsal generalizes this from research briefs to development actions.
- `core/heuristic_distiller.py` — clusters Observation/SurpriseMoment/pathway_attempt/grade failures; `human_rejection` ranked first (keep that supremacy).
- `core/graphify_interface.py` provenance guards — `playtest` is human-only (:1307–1310); `observe` requires human provenance or `--derived-from <playtest_id>` (:1364–1370). **Keep these guards untouched** — they are the control half of the balance. Sim gets NEW node types instead.
- `run_deep_space_trader_pipeline.py` stage 6 / `core/playtest_runner.py` — headless automation tests (unit-level); unchanged, complementary.
- Windows Task Scheduler pattern documented in dream_loop.py:20–22.

## Architecture

```
              (steering: one-line vetoes, temperatures, heuristic approvals)
   HUMAN ─────────────────────────────┐ overrides anything below
                                      ▼
   REHEARSAL (data)  ──ranked NEXT──► DUTY CYCLE executes ──build──► SLEEPWALKER (engine)
   rollouts over graph priors         (existing machinery)           plays beat scripts in PIE
        ▲      │ SimulationRollout nodes          SimPlaytest nodes │      │
        │      └──────────────► DNA GRAPH ◄─────────────────────────┘      │
        └────────── priors (grades, pathway failure rates, facade map) ◄───┘
                                      │
                              DREAM LOOP (existing) — sim surprises are fodder,
                              human rejections stay ranked above sim signals
```

### 1. `core/witness.py` — shared witness (NEW, absorbs the demo_witness Phase-2 item)
Beat-timeline recorder used by BOTH human sessions and sleepwalks: tails `Saved/Logs/Chimera.log` for `[DEMOBEAT]`, polls `inspect runtime_report` (pawn position, possessed class) every N s, emits `Saved/SessionChronicles/<session>.json` (beat, t, evidence). CLI: `python -m core.witness --session <name> --out <path>`.

### 2. `core/sleepwalker.py` — the in-engine AI playtester (NEW)
- **Beat scripts**: JSON per demo at `Chimera/docs/beats/<demo>.beats.json`. Schema: `{beat, goal, actions[], expect[]}` where actions are proven-pathway MCP calls (`simulate_input` sequences, waits) and expects are read-backs (`runtime_report` position within radius, component property equals, log line present, screenshot taken). First script: `regolith_yard.beats.json` transcribed from DEMO_ARCHITECTURE.md §2 beats 1–8.
- **Executor**: foreground-independent (throttle already disabled); play → run beats → stop_pie. Per beat: attempt, read back, classify `reached | failed | blocked`. Never trusts success:true.
- **Emits**: witness timeline; `record_simtest(...)` → new `SimPlaytest` node (observer=`agent-sim`, beats, outcomes, timeline path, screenshots ≤2, synthetic temperature ≤3 sentences, clearly sim-labeled); `surprise --source agent` per dead-end; `pathway` per novel MCP sequence; per-feature sim-evidence links.
- **Grading**: beat outcomes become ev.json criteria → `result_grader` stays the only gate. A feature passing its beats records `feature --status sim_verified`.
- **Hard rule**: sleepwalker NEVER calls `graphify_record playtest` or human-provenance `observe`. The existing guards already reject it; add a test asserting they do.

### 3. `core/rehearsal.py` — data-level generational rollouts → next-move decision (NEW)
- **Candidates**: enumerate from loop board (not_started / needs_refinement), DEMO_ARCHITECTURE phases, open phantom pains, (later: cinematic-resonance extracted material).
- **Rollout**: for each candidate simulate K virtual generations as data using graph priors — per-tool pathway failure rates, facade map (Niagara authoring, add_anim_notify…), grade history per template, asset availability (Content scan), declared capable-only fraction. Produce: expected grade, build risk, queue-closure value, human-minutes cost, surprise potential.
- **Policy**: deterministic score = expected_value × queue_value ÷ cost, plus an exploration bonus for high-uncertainty candidates (bandit-style, seeded like spiral_forks; NO wall-clock/random in workflow contexts). LM pass optional (`--use-lm`, LM Studio `/no_think` discipline) for narrative rationale only — never for the score.
- **Output**: (a) `SimulationRollout` node per decision (candidates, scores, chosen, rationale, run_id); (b) prepends a **recipe-carrying NEXT item** to task_progress.md (handoff invariant: exact commands or feature node with study guide, skip-condition, capable-only marking); (c) prints a **decision table** for the human to veto with one line — same reversibility pattern as the attribution table.

### 4. Protocol amendment — the balance of automation and control
- New feature status **`sim_verified`** between `verified` and observed. Loop board renders `[DONE~]`. **Dependent work may proceed on sim_verified**; human observation remains the true collapse — a later human rejection reopens `needs_refinement` at top priority (existing behavior).
- Duty-cycle Step 2 gains branch **C-half**: "no human verdicts and NEXT empty of executable items → run `python -m core.rehearsal --decide` and execute the item it writes." Fallback pipeline health check drops to last.
- Distiller: ingest SimPlaytest failures as kind=`sim_rejection`, ranked strictly BELOW `human_rejection` in staging order.
- Nightly rhythm: Sleepwalker 01:00 → dream_loop 02:00 (schtasks, same pattern dream_loop documents). The game plays itself, then dreams about it.
- Amendment text lands in `docs/GENERATION_PROTOCOL.md` (new "Sleepwalking" section) + CLAUDE.md protocol block + CYCLE_PROMPT.md branch list. These constitution edits are what this plan's approval authorizes.

## Files

| Action | Path |
|---|---|
| NEW | `Chimera/core/witness.py`, `Chimera/core/sleepwalker.py`, `Chimera/core/rehearsal.py` |
| NEW | `Chimera/docs/beats/regolith_yard.beats.json` (from DEMO_ARCHITECTURE §2 beats 1–8) |
| MOD | `Chimera/core/graphify_interface.py` — `record_rollout`, `record_simtest`, allowlist `sim_verified`, SimPlaytest/SimulationRollout node types (typed helpers only; provenance guards untouched) |
| MOD | `Chimera/core/graphify_record.py` — CLI subcommands `rollout`, `simtest` |
| MOD | `Chimera/core/heuristic_distiller.py` — sim_rejection cluster kind below human_rejection |
| MOD | `Chimera/core/preflight.py` — §[4.6]: last sleepwalk result, last rehearsal decision, `[DONE~]` tier on loop board |
| MOD | `docs/GENERATION_PROTOCOL.md`, `CLAUDE.md`, `CYCLE_PROMPT.md` — amendment |

## Milestones (each = one duty cycle, graded via result_grader)

1. **M1 Sleepwalker walking skeleton** *(capable)*: witness.py + sleepwalker.py + regolith beats 1–4 (spawn-check, walk three pads, orbit pedestal via yaw read-back). Criteria: beats executed with read-backs, timeline JSON exists, SimPlaytest node recorded, provenance-guard test passes. Known risks probed here: mouse-axis simulation unproven (WASD-first beats; camera via control-rotation set_property fallback — declared unknown), background input injection unproven (test with editor unfocused; if it needs focus, schedule sleepwalks when idle + AppActivate).
2. **M2 Rehearsal decider** *(capable)*: candidate enumeration + priors from graph + deterministic policy + one real decision written to NEXT + SimulationRollout node + veto table printed. Criterion: its top choice for tomorrow is defensible against the live queue state.
3. **M3 Protocol integration** *(mixed)*: sim_verified tier end-to-end (record → loop board → preflight), distiller sim_rejection, docs amendment. Weak-OK except doc wording.
4. **M4 Rhythm + steering** *(weak-OK)*: schtasks 01:00 sleepwalk / 02:00 dream; veto-table intake path documented in CYCLE_PROMPT branch A′ (human one-liners against sim decisions).

## Verification (end-to-end)
Run `python -m core.sleepwalker --beats docs/beats/regolith_yard.beats.json --session sim_smoke` with the editor open: expect PIE start/stop, ≥4 beats with read-back evidence, timeline JSON, SimPlaytest node in graph (`grep SimPlaytest docs/chimera_dna_graph.json`), and `python -m core.preflight` showing the sleepwalk under [4.6]. Then `python -m core.rehearsal --decide --dry-run` → decision table with ≥3 candidates and a recipe-carrying item. Negative test: sleepwalker attempting `graphify_record playtest` must be rejected by the existing human-provenance guard. Grade both via ev.json (declared criteria) — C/F routes back per the rubric.

## Risks / honest unknowns
- `simulate_input` mouse axes + background-window injection: unproven (M1 probes; fallbacks named above).
- Rehearsal priors may be thin (graph has 1300 nodes but uneven coverage) — policy must expose its confidence, and low-confidence decisions get an exploration flag rather than false certainty.
- Constitution drift risk: sim signals slowly displacing human authority — mitigated structurally (separate node types, guarded human-only surfaces, human_rejection permanently outranks sim_rejection, veto table on every decision).
- Cost: sleepwalks are local (MCP + optional LM Studio) — near-zero API usage; rehearsal LM pass optional.
