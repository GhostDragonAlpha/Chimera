# PREREGISTRATION — fleet-orient-continuation-02 (fresh-system re-verification)

- Agent: subagent-worker-04 (slot 3, generation 1, lead glm53-lead-02 epoch 5)
- Task: fleet-orient-continuation-02 · branch `astra/tasks/fleet-orient-continuation-02`
- Date: 2026-09-11
- Inherited work: origin/astra/tasks/fleet-orient-continuation-01 @ 6a03ae91 (4 commits:
  route / refine / finalize + gen3 logs), merged into this branch, then reconciled to
  tip c1a1ec5a. Gen1–gen3 artifacts under this directory are PRESERVED — this run only
  ever adds NEW-named files (`*-20260911-fresh.*`), never overwrites.

## STATEMENT (disagreeable claim)

The inherited orientation/continuation surfaces behave truthfully on a fresh system:
a completed local term hierarchy remains truthful bounded state (it is NOT completion
of the canonical Master project); the CLI/JSON/MCP completion surfaces supply the
canonical continuation route (resume owned milestones first, or claim eligible READY
work via an authenticated claim on the agent's own provisioned session); they never
fabricate live ownership or readiness (owner and eligible_tasks stay null — unclaimed),
and read-only orientation never writes the store.

## PREDICTION (not yet measured on this fresh checkout)

1. The 9 inherited tests in `tools.test_orient_continuation` pass fresh from the repo
   root of this worktree with no modification and no weakening.
2. `orient --json` bound to an ephemeral completed store returns
   `continuation.hierarchy_complete == true`, `route == "canonical_master_controller"`,
   `action == CONTINUATION_ACTION`, `owner == null`, `eligible_tasks == null`, and the
   store bytes are hash-unchanged after the run.
3. Missing / malformed / synthetic-store orientations refuse without writes: missing
   store is not created (exit 3), malformed store bytes unchanged (exit 4), synthetic
   mode creates no store file; each reports `owner == null`, `eligible_tasks == null`.
4. The three normalized-LF sha256 pins in the test module
   (engine_state.py `c1a5f578…`, mcp_server.py `d9944a02…`, orient.py `3d899219…`)
   hold unchanged on this fresh checkout — no re-pinning, no weakened assertion.
5. Related suites are green on this branch: `tools.test_orient_store`,
   `ChimeraEngine.tests.test_engine_gates`, and the fleet discover suite
   (`python -m unittest discover -s tools/agent_fleet -p 'test_*.py'`) with 0 failures
   (expected single Windows-symlink skip).

## FALSIFIER (named before the run)

- Any fabricated live ownership or readiness (owner / eligible_tasks populated from
  anything but the agent's own authenticated claim path).
- Any write to a store during read-only orientation (store bytes change where the
  prediction says hash-unchanged), including the live MCP store.
- Any weakened assertion, skipped test, or re-pinned source hash without cause.
- Any overwrite of inherited gen1–gen3 evidence files in this directory.
- A stale hierarchy-complete stop instruction surviving on any completion surface.

If any of these fire, the routing fix does NOT survive fresh-system re-verification
and this branch must be reported as failing, not fixed post hoc.

## Method

Fresh merges only (no source edits): merge 6a03ae91 (fast-forward from base 6e240af1),
then merge tip c1a1ec5a (scoped files verified byte-identical base↔tip before merge).
Then run the suites verbatim from the worktree root and record raw outputs verbatim in
new-named evidence files. No measured actuals appear above this section.
