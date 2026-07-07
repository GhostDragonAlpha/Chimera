export const meta = {
  name: 'chimera-task-cycling',
  description: 'Cycle through Chimera pending tasks one subagent at a time',
  phases: [
    { title: 'Cycling', detail: 'Process observation queue, heuristics, roster/bridge backlog, live build health in rotation' },
  ],
}

// Context refreshed 2026-07-07 against python -m core.preflight + full docs sweep.
// Prior version's context blob was stale: GPA "0.3" (likely a misread of the +0.3
// per-feature GPA-impact estimate in SAND_SURFACE_TEST_FRAMEWORK.md:562, not the
// global score, which is actually ~2.0/healthy), and "scholar.py needs implementing"
// (core/scholar.py, muse.py, visionkeeper.py all already exist and are substantive —
// only docs/DREAM_ROSTER.md's text is stale). H-15/H-16 are already tombstoned.
const TASK_CONTEXT = {
  observation_queue_processing:
    `14 features await automated observation (the DNA graph's "true collapse" step): ` +
    `Verb_Look, Player_Character_Model_Visor_Apply, Verb_Shovel, Verb_Bend, Verb_PickUp, ` +
    `Verb_Drop, Tool_Weapon_Model, System_Economy, System_SaveLoad, System_Factions, ` +
    `Player_Character_Animation, and 3 more — run "python -m core.preflight" section [4.5] ` +
    `for the exact current list. Per CLAUDE.md's 2026-07-07 full-automation amendment, use ` +
    `"core/collapse_proxy.py --from-simtest <id> --valence accepted|rejected" instead of ` +
    `waiting on a human. Its own rule is narrower than a blanket sweep: "accepted" valence ` +
    `collapses only features EXERCISED by that simtest's evidence; "rejected" valence ` +
    `indicts only what the evidence names. The most recent sleepwalk (audio_sync_test_walk, ` +
    `regolith_yard beats, see preflight [4.6]) reached only 2/5 beats and recorded a failure ` +
    `on walk_metal_to_rock — do not sweep ground-surface-transition features as accepted from ` +
    `that run. Before sweeping any feature, confirm it actually has exercising evidence ` +
    `(graphify_query); leave anything with zero evidence untouched/open rather than guessing. ` +
    `Report exactly which features you swept (and with which valence) versus left open, and why.`,

  pending_heuristics_review:
    `Of the heuristics in docs/PENDING_HEURISTICS.md, only H-12 (grade_CF: Build_Pipeline) is ` +
    `actionable right now — status "approved (implementation pending, capable cycle)". Its ` +
    `draft_rule: "A build-failure grade must carry the failing file:line verbatim — 'no error ` +
    `text captured' makes the F untriageable and wastes the retry." Implement it: find where ` +
    `build/grade failures get recorded (core/result_grader.py and core/build_orchestrator.py ` +
    `are the likely spots) and make sure captured UBT output always includes the verbatim ` +
    `failing file:line:error text rather than a generic placeholder. Do NOT touch H-15 or ` +
    `H-16 — both are already tombstoned (vetoed-auto, subsumed) and need no further review.`,

  roster_and_bridge_progress:
    `First ground this in live data: run "cd E:\\PythonChimera\\Chimera && python -m ` +
    `core.context_package --feature Ground_Sand_Footprints --json" and treat its output ` +
    `as authoritative over any stale claims below (feature status, prior pathway ` +
    `attempts/mutations, campus sources, MCP_PATHWAYS.md endpoints for this feature).\n\n` +
    `docs/DREAM_ROSTER.md still lists Tier-1 organs Scholar, Muse, and Visionkeeper as ` +
    `"EMPTY", but that's stale: core/scholar.py (347 lines), core/muse.py (156 lines), and ` +
    `core/visionkeeper.py (224 lines) all already exist with real implementations (see git ` +
    `log commit "Implement Scholar organ"). First, fix that doc drift: update DREAM_ROSTER.md's ` +
    `Tier-1 entries to reflect they're hired, citing the files as evidence. Second, ` +
    `DREAM_ROSTER.md's own next-in-line gap is Tier-2 #4 BRIDGE ENGINEER: "the ` +
    `McpAutomationBridge NOT_IMPLEMENTED/facade backlog (add_anim_notify, ` +
    `get_anim_sequence_info, Niagara authoring) blocks whole departments (VFX, animation); ` +
    `one failed reverted attempt exists." This is the single most-repeated blocker across ` +
    `recent session handoffs in task_progress.md (it currently blocks Ground_Sand_Footprints). ` +
    `Make one real, evidence-captured step of progress on it. Follow SUCCESSOR_RUNBOOK ` +
    `Directive 6: capture any failure verbatim and stop after two failed attempts rather than ` +
    `improvising a third; record the pathway attempt either way. Be honest about partial ` +
    `progress — task_progress.md's own history records a past incident where a reverted fix ` +
    `got mis-described as "fix in place"; if you don't fully land this, say so plainly.`,

  weight_shift_build_fix:
    `Optional grounding (speculative — no exact Feature Ledger match for this build-diagnostic ` +
    `task): run "cd E:\\PythonChimera\\Chimera && python -m core.context_package --feature ` +
    `Player_Character_Animation --json" — it may surface prior related pathway/mutation ` +
    `history; treat it as supplementary, not authoritative, here.\n\n` +
    `"python -m core.preflight" currently shows 2 of the last 20 builds failing to compile, ` +
    `both citing Source/Chimera/ProceduralGenerated/Tests/WeightShiftAnimationTests.cpp ` +
    `(around lines 6 and 36). I already checked ` +
    `Source/Chimera/ProceduralGenerated/ChimeraMovementComponent.h and confirmed ` +
    `"UpdateWeightShift(float DeltaTime)" and "GetWeightShiftOffset() const" both exist as ` +
    `PUBLIC members — so this is either a stale error from before that header was last ` +
    `edited, or a different mismatch (e.g. the test's component-creation helper, or another ` +
    `symbol/include). ChimeraMovementComponent is a loop-built MANUAL file per CLAUDE.md (no ` +
    `generator template owns it — hand-edits here are safe, unlike the Flight/Ship/Economy/etc ` +
    `generator-owned files). Steps: rebuild fresh via UBT to get the CURRENT verbatim error ` +
    `(apply H-12's capture rule from the previous task), diagnose the real mismatch per ` +
    `heuristic H-1 ("a C2039 missing-member error in ProceduralGenerated/ means drift — fix ` +
    `the interface at its source, not the test"), fix it, rebuild to confirm green, and ` +
    `record the build result to the DNA graph via record_build.`,
}

const CYCLE_TASKS = Object.keys(TASK_CONTEXT)

let cycle_count = 0
// Loop until budget exhausted or max cycles reached
const MAX_CYCLES = 3

while (cycle_count < MAX_CYCLES && (budget.total === null || budget.remaining() > 150_000)) {
  cycle_count++
  log(`Starting workflow cycle ${cycle_count}`)

  for (const task of CYCLE_TASKS) {
    if (budget.total !== null && budget.remaining() <= 150_000) {
      break
    }

    log(`Processing task in cycle ${cycle_count}: ${task}`)

    const result = await agent(
      `Chimera workflow: Process the pending task '${task}'.\n\n${TASK_CONTEXT[task]}\n\n` +
      `Be honest about partial progress — if you don't fully complete this, say so plainly ` +
      `rather than overclaiming (this project's history includes a reverted fix once being ` +
      `mis-described as "fix in place").`,
      {
        phase: 'Cycling',
        label: `task:${task}`,
        effort: 'medium'
      })

    if (result) {
      log(`Task '${task}' result preview: ${String(result).substring(0, 200)}...`)
    } else {
      log(`Task '${task}' had no result or was skipped.`)
    }
  }

  log(`Cycle ${cycle_count} complete. Remaining budget: ${Math.round(budget.remaining()/1000)}k tokens`)
}

log(`Workflow completed ${cycle_count} cycles.`)
return { cycles_completed: cycle_count }
