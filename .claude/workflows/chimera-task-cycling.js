export const meta = {
  name: 'chimera-task-cycling',
  description: 'Cycle through Chimera pending tasks one subagent at a time',
  phases: [
    { title: 'Cycling', detail: 'Process observation queue, heuristics, roster/bridge backlog, live build health in rotation' },
  ],
}

// THE ANTI-STALENESS INVARIANT (2026-07-17, fixes confirmed pain
// phase_e0b68063201645ae:P1): a context entry carries a STABLE MISSION plus
// LIVE-GROUNDING COMMANDS, never baked facts. The previous version froze a
// queue snapshot ("14 features await... and 3 more") that arrived unchanged
// across 4+ dispatches while the live queue moved 15->9->13, and told agents
// to chase a WeightShift build failure after the build trend had gone 20/20
// green. If you are tempted to paste a count, a feature list, a heuristic id,
// or a build status in here: paste the COMMAND that prints it instead.
const TASK_CONTEXT = {
  observation_queue_processing:
    `Run "cd E:\\PythonChimera\\Chimera && python -m core.preflight" and read section [4.5] ` +
    `for the CURRENT observation queue (the DNA graph's "true collapse" step) and section ` +
    `[4.6] for the most recent sleepwalk and its failures. Per CLAUDE.md's full-automation ` +
    `amendment, use "python -m core.collapse_proxy --from-simtest <id> --valence ` +
    `accepted|rejected" instead of waiting on a human — with the MOST RECENT simtest for the ` +
    `feature (H-19: an old simtest_id can indict a feature already fixed since). The rule is ` +
    `narrower than a blanket sweep: "accepted" collapses only features EXERCISED by that ` +
    `simtest's evidence; "rejected" indicts only what the evidence names; honor any failed ` +
    `beats by NOT sweeping the features they touch as accepted. Before sweeping any feature, ` +
    `confirm it actually has exercising evidence (graphify_query); leave anything with zero ` +
    `evidence untouched/open rather than guessing. Report exactly which features you swept ` +
    `(and with which valence) versus left open, and why.`,

  pending_heuristics_review:
    `Read docs/PENDING_HEURISTICS.md AS IT IS NOW and act only on what its statuses say ` +
    `TODAY. The Gardener auto-tends this queue nightly (doc-organ entries self-promote; ` +
    `tombstoned/vetoed entries are settled — never touch them). Your lane is entries marked ` +
    `"approved (implementation pending, capable cycle)": gate-organ rules waiting for someone ` +
    `to wire them into code. Pick AT MOST one, implement it where the evidence says (cite ` +
    `file:line in your result), and record the change. If nothing is in that state, say so ` +
    `plainly and stop — an empty lane is a valid, reportable result.`,

  roster_and_bridge_progress:
    `Ground EVERYTHING in live data first: read docs/DREAM_ROSTER.md as it is now, and for ` +
    `whatever feature you end up touching run "cd E:\\PythonChimera\\Chimera && python -m ` +
    `core.context_package --feature <X> --json" — its output is authoritative over any prose ` +
    `claim (including doc drift claims: VERIFY a file is missing/stale before "fixing" it). ` +
    `Then make one real, evidence-captured step on the roster's CURRENT next-in-line gap — ` +
    `cross-check against recent session handoffs in task_progress.md for the most-repeated ` +
    `live blocker. Follow SUCCESSOR_RUNBOOK Directive 6: capture any failure verbatim and ` +
    `stop after two failed attempts rather than improvising a third; record the pathway ` +
    `attempt either way. Be honest about partial progress — task_progress.md's own history ` +
    `records a reverted fix once mis-described as "fix in place".`,

  build_health:
    `Run "cd E:\\PythonChimera\\Chimera && python -m core.preflight" and read the build ` +
    `trend in section [2]. If it shows failures: rebuild fresh via UBT to get the CURRENT ` +
    `verbatim error (a build-failure record must carry the failing file:line verbatim — "no ` +
    `error text captured" is untriageable), diagnose per H-1 (a C2039 missing-member error ` +
    `in ProceduralGenerated/ means template drift — fix the interface at its source, in the ` +
    `generator if the file is generator-owned, never the generated artifact), fix, rebuild ` +
    `to confirm green, and record the result via record_build. If the trend is already ` +
    `clean (e.g. 20/20 pass), REPORT THAT AND STOP — never chase an error message quoted in ` +
    `an old prompt or handoff; only a fresh UBT run is evidence a failure exists.`,
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
