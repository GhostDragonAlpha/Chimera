# Orchestrator Mode — enforcing the Contract at the seams

- Every subtask package must carry: the DSL block or feature node id, the relevant proven
  pathways (MCP_PATHWAYS numbers), grading criteria (`criteria_total` declared up front),
  and the capable-only marking if judgment-heavy.
- Route by state, not habit: human verdicts waiting -> branches A/B first. NEXT list has
  recipes -> C. Empty -> C2 (`python -m core.rehearsal ... --decide`, honor its veto table).
  Nothing else -> D fallback.
- Weak-session routing: items marked `capable sessions only` never go to a local/small-model
  session; split phases into author (capable) + verify (weak) when possible.
- Seam bookends are non-negotiable: preflight before the first subtask, postflight + dream_loop
  after the last, task_progress.md prepend with recipe-carrying NEXT items (handoff invariant).
- Sim evidence (SimPlaytest/SimulationRollout) informs routing but never closes a feature —
  only the human's observation does. human_rejection outranks sim_rejection everywhere.
