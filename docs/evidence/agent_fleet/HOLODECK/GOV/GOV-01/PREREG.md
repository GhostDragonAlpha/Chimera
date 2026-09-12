# PREREG — holodeck-gov-01 (gen 1)

- Agent: subagent-worker-10. Slot 4, worktree E:\ChimeraWork\slot-04, branch
  astra/tasks/holodeck-gov-01, base d59518b9d9dc002cba43d071495576a236b9d498
  (verified HEAD==base, clean, index 5984 entries, before any work).
- Admitted from my own draft DRAFT-holodeck-gov-01 (PR #67; catalogue card GOV-01,
  digest b9d32319, content_sha256 b0919b86e7b71402...).
- SOURCE-ONLY lane: the DEPLOYED contract is studied from the source text at base
  (tools/agent_fleet/control.py 839 lines, tools/agent_fleet/review_handoff.py 227
  lines, sha256 recorded in RESULT.md). The live service at 127.0.0.1:8099 is NEVER
  contacted. DYAD: NOT_APPLICABLE — source-only scope records no executed behavior;
  reason recorded in RESULT.md per the card's DYAD policy.
- This commit contains the prereg ONLY. No reference model, no controls, no results.

## CARD MEMBRANE (quoted from the card / task packet)

- CARD STATEMENT: Canonical task IDs, claims, owners and publication queue.
- CARD PREDICTION: Conflicting claims are rejected and active assignments survive restart.
- CARD FALSIFIER (named BEFORE the run, both for the reference model and the source trace):
  **Two agents own the same write scope or stale state replaces a newer claim.**

## REFERENCE MODEL CONTRACT (fixed before implementation)

A self-contained stdlib-only python module (`reference/gov01_reference_model.py`, inside
this evidence scope) implementing the INTENDED base contract (control.py claim + `_task`
CAS + committed-state persistence), NOT the interceptor deviation:

- state: agents{id: caps, max_tasks, qualified}, tasks{id: state, owner, generation,
  scopes, caps, deps, kind}, slots{no: task, kind}; revision counter.
- `claim(actor, token, task_id)` gate chain mirrors control.py:520-532: qualified →
  READY → capability subset → capacity (active < max_tasks) → deps INTEGRATED →
  write-scope overlap refusal (casefold prefix semantics, control.py:51-53) → slot
  allocation. On success: owner=actor, state=RUNNING, generation+=1 (CAS bind).
- `mutate(actor, generation, task_id, payload)` mirrors `_task` (control.py:116-124):
  owner AND generation AND active-state must all match → apply; else refuse
  `stale_or_foreign_claim`. INTENDED instance binding modeled as a 4th CAS field
  (`owner_instance`): when bound, a mutation must present the same instance or refuse
  `instance_not_bound`.
- `save()/load()`: whole-registry JSON to a scratch file (models the committed state
  blob; control.py:65-66, 351). Restart = new instance + load.

## PREREGISTERED NUMBERS / THRESHOLDS (stated before ANY implementation test)

Verdict rule: each R row must reach its full N/N; any miss = falsifier fired for that row
and the miss is REPORTED, not patched around. For the reference model a fired card
falsifier means the MODEL (or my reading of the semantics) is wrong — the model gets
fixed and the correction is disclosed in RESULT.md with the fired-run retained; the
DEPLOYED-source findings are never edited.

- R1 positive controls (model must ACCEPT): N=6/6 legal operations —
  (a) qualified claim of READY task; (b) second agent claims scope-disjoint task;
  (c) checkpoint mutate with exact current generation; (d) save→new-instance→load→
  mutate with pre-restart generation; (e) capacity boundary claim (2nd of max_tasks=2);
  (f) scope-suffix/parent-child NON-overlap handled per casefold-prefix semantics
  (distinct dirs `a/b` vs `a/bc` must NOT conflict).
- R2 conflicting claims (card falsifier clause 1 — model must REJECT): N=5/5 refusals
  with the refusal recorded verbatim —
  (a) equal scope, 2 agents; (b) parent/child scope overlap; (c) child/parent overlap;
  (d) case-insensitive (casefold) duplicate scope; (e) same TASK claimed twice by a
  second agent (refusal `task_not_ready`, because state left READY).
  Post-state assertions in every case: owner unchanged, generation unchanged (0),
  state still READY/RUNNING as applicable, slot binding unchanged.
- R3 stale-state mutation (card falsifier clause 2 — model must REJECT): N=4/4 —
  (a) mutate with generation < current (`stale_or_foreign_claim` semantics recorded);
  (b) mutate by a foreign actor with the owner's generation;
  (c) mutate unknown task; (d) after owner change (claim→release→re-claim by B),
  A's old generation refused.
- R4 restart persistence (card prediction clause 2 — model must PRESERVE): N=2 tasks ×
  5 fields (owner, generation, state, slot binding, checkpoint payload) identical after
  save→load; plus post-reload stale mutation still refused (1/1) and post-reload legal
  mutation accepted (1/1).
- R5 deployed-source trace (the card prediction judged against the DEPLOYED text at
  base): each of the 3 negative controls maps to a named deployed refusal/property with
  exact file:line at d59518b9 —
  write_scope_conflict → control.py:530-532 (and interceptor copy review_handoff.py:74-77);
  stale_or_foreign_claim → control.py:119 (CAS owner+generation, active-state 120);
  serialization/persistence → control.py:308 (BEGIN IMMEDIATE), 344 (revision bump),
  351 (state committed), 65-66 (state+events tables), 359 (ROLLBACK on refusal).
  Threshold: 3/3 semantics present in the deployed text with the quoted lines.
- R6 measured deviation (recorded finding, NOT adopted as the model's truth): the
  interceptor claim (review_handoff.py:54-93, serving ALL claims when active) binds
  {owner, slot, state, generation} at rh.py:90-91 while the base claim binds those PLUS
  owner_instance at control.py:553-554, and performs no `instance_binding_required`
  check (contrast control.py:550-551). Predicted textual delta: owner_instance
  occurrences in review_handoff.py == 0; in control.py == 4 (claim bind 554, _task
  check 121-123 x2 lines, yield guard 497-501, setdefault 323 — exact count measured
  and reported). Consequence recorded: for interceptor-claimed tasks owner_instance
  stays None so the `_task` binding check (control.py:122-123) is skipped, i.e. the
  INTENDED per-instance fencing is inert on the live claim path while
  instance_fencing=='compat'. Matches feedback c4212657; fix in flight as
  fleet-review-handoff-claim-delegation-01. If the delta measures differently at this
  base, that is reported as a surprise finding, never silently reconciled.

## METHOD

1. Write the reference model (evidence-scoped, stdlib-only, <300 lines).
2. `controls/run_controls.py` executes R1-R4 against the model in one process and
   writes `checks/r1_positive.txt`, `checks/r2_conflicting_claims.txt`,
   `checks/r3_stale_generation.txt`, `checks/r4_restart_persistence.txt` (each refusal
   verbatim, each post-state assertion listed).
3. R5/R6 measured from the source text at base by a read-only script:
   `checks/r5_source_trace.txt` (quoted lines), `checks/r6_owner_instance_delta.txt`
   (occurrence counts + quoted bind sites).
4. RESULT.md: scoreboard, reproduction commands, source identity (git sha + file
   sha256), limitations, DYAD NOT_APPLICABLE record.
5. Commit chain on astra/tasks/holodeck-gov-01 (trailer `Agent: subagent-worker-10`),
   push no-force, PR into astra/gait-capture, submit_review with exact HEAD.
