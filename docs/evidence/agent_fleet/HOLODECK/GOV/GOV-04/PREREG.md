# PREREG — holodeck-gov-04 (gen 1)

- Agent: subagent-worker-03. Slot 10, worktree E:\ChimeraWork\slot-10, branch
  astra/tasks/holodeck-gov-04, base 62b8e35757c71e31d621c26b32a7c52558905b02
  (verified HEAD==base, clean, index 6050 entries, before any work).
- Realizes catalogue card GOV-04 "Agent packet generation" (admitted from draft
  DRAFT-holodeck-gov-04, PR #67; catalogue digest b9d32319, content_sha256
  48fcff17bb260ae1e406e97e338c268e59564f4284687cc16232cc69a69e3fff), following
  the integrated GOV-01 pattern (PR #77).
- SOURCE-ONLY lane: the DEPLOYED contract is studied from the source text at
  base (tools/agent_fleet/control.py 839 lines sha256
  7cee259b35a21ebe689feb5d77c8f2bb10b7125cd1ea9c3ac06e1cb6254bfa30;
  tools/agent_fleet/review_handoff.py 227 lines sha256
  ad3674bd2e1f1a60a3762e44cd26578150b2c475b064af042a40bace30b51811 — both
  re-hashed and recorded in RESULT.md). The live service at 127.0.0.1:8099 is
  NEVER contacted. DYAD: NOT_APPLICABLE — source-only scope records no executed
  visible behavior; reason recorded in RESULT.md per the card's DYAD policy.
- This commit contains the PREREG ONLY. No reference model, no controls, no
  results.

## CARD MEMBRANE (quoted from the card / task packet)

- CARD STATEMENT: Self-contained assignments from ready tasks and preserved
  active scopes.
- CARD PREDICTION: Packets include dependencies, actual evidence, write scope
  and finish criteria.
- CARD FALSIFIER (named BEFORE the run, for both the reference model and the
  source trace): **A blocked or already claimed task is silently reassigned.**
- CARD MATHEMATICS: topological scheduling; critical paths; resource
  constraints.
- CARD THRESHOLD POLICY: fixture-specific bounds are derived and stated below,
  before implementation tests; existing frozen gates are preserved (this lane
  writes evidence only — no production gate is touched).

## REFERENCE MODEL CONTRACT (fixed before implementation)

A self-contained stdlib-only module (`reference/gov04_reference_model.py`,
inside this evidence scope) implementing the INTENDED base contract of packet
generation and admission — create_task validation, catalogue admission gates,
claim admission of generated packets, and packet content — as read at base
62b8e357, NOT the interceptor deviation:

- `create_task(leader, ...)` mirrors control.py:503-524: lead-only
  (`_lead`, control.py:113); id regex `[a-z0-9][a-z0-9-]{0,63}` + no duplicate
  (506); scopes non-empty list, each through `path_scope` (41-49: relative
  POSIX-style, no `:`/`.`/`..`/empty parts, no `.git` part casefold,
  protected `chimeraengine/engine/build` refused in BOTH overlap directions);
  dependencies must EXIST at create time (508); capabilities list of str;
  kind in {worker, integration}; base = 40-hex; branch derived
  `astra/tasks/<id>`; packet text required (521); record born
  READY/owner=None/generation=0.
- `generate_packet(task)` (the card's deliverable 1): emits a self-contained
  assignment dict with EXACTLY these measured-required elements —
  `dependencies` (verbatim from the record), `evidence` (actual record state:
  checkpoint/head/review/integration fields as stored, plus resource and slot
  provenance when present), `write_scope` (the record's scopes verbatim),
  `finish_criteria` (the record's packet text + the contract's finish states
  REVIEW→INTEGRATED). The CARD PREDICTION is measured as: every generated
  packet contains all four elements, non-empty where the record demands it.
- `admit_packet(packet)` → `claim(actor, task_id)`: the gate chain mirrors
  control.py:520-540 — qualified → READY (`task_not_ready` otherwise) →
  integration-kind lead-only → MASTER_LIST scope lead-only → capability
  subset → capacity (active RUNNING/BLOCKED/REVIEW/RECOVERY_HOLD <
  max_tasks) → all dependencies INTEGRATED (`dependencies_not_integrated`) →
  write-scope overlap refusal vs every active task (casefold prefix,
  `overlaps` 51-53) → slot of matching kind free (auto-spawn under
  SLOT_GUARD with the stale-provision recovery guard, 534-540). Success:
  owner=actor, state=RUNNING, generation+=1, slot bound, and — INTENDED
  contract — `owner_instance` bound to the claiming instance (control.py:554).
- Catalogue plane: `catalogue_import` (digest-stamped payload),
  `catalogue_next` mirrors control.py:804-826 — candidates are cards with
  status PROPOSED, id not live (live = not INTEGRATED and not ABANDONED,
  casefold match) and every dependency casefold-satisfied by INTEGRATED-only;
  sorted output; planning-data note. `catalogue_read` returns the record by
  plane+id.
- Scheduler (CARD MATHEMATICS): topological order of the task DAG over
  dependencies (INTEGRATED satisfies); critical path = maximum dependency-edge
  chain to any node; resource constraint = concurrent claims bounded by free
  slots of the record's kind.

## PREREGISTERED NUMBERS / THRESHOLDS (stated before ANY implementation test)

Verdict rule: each R row must reach its full N/N; any miss = the card
falsifier fired for that row and the miss is REPORTED, never patched around.
For the reference model a fired falsifier means the MODEL (or my reading of
the semantics) is wrong — the model gets fixed and the correction is disclosed
in RESULT.md with the fired run retained; DEPLOYED-source findings are never
edited.

- **R1 positive controls (model must ACCEPT): N=8/8** —
  (a) lead create_task with legal id/scope/dep;
  (b) claim of READY task with dep INTEGRATED;
  (c) generated packet for a READY task contains all 4 required elements
  (dependencies, evidence, write_scope, finish_criteria) — 4/4 per packet;
  (d) second legal task admitted while first is RUNNING (disjoint scopes);
  (e) catalogue_next offers an eligible card ONLY after its dependency is
  INTEGRATED (before: absent; after: present, sorted);
  (f) topological order of the fixture DAG is a valid topo order
  (every edge points forward);
  (g) capacity boundary: 2nd claim of max_tasks=2 accepted;
  (h) instance-bound mutation accepted from the binding instance.
- **R2 card falsifier clause 1 — blocked/claimed tasks are NOT silently
  reassigned (model must REJECT): N=6/6**, each with the refusal verbatim and
  post-state assertions (owner, generation, state, slot, packet bytes
  unchanged):
  (a) claim with dependency NOT INTEGRATED → `dependencies_not_integrated`;
  (b) claim of an already-RUNNING task → `task_not_ready`, owner unchanged;
  (c) second agent claim overlapping an active task's scope →
  `write_scope_conflict`;
  (d) claim of a BLOCKED-state task → `task_not_ready`;
  (e) create_task duplicate id → `invalid_or_duplicate_task` and the existing
  record's packet survives byte-identical (no silent overwrite);
  (f) claim of a REVIEW-state task → `task_not_ready`.
- **R3 packet-admission integrity (create_task validation, model must
  REJECT): N=6/6** —
  (a) dependency that does not exist → `dependencies_must_exist`;
  (b) absolute scope → `invalid_scope`;
  (c) `..` scope → `invalid_scope`;
  (d) scope under `chimeraengine/engine/build` → `protected_build_scope`;
  (e) scope whose PARENT would be the protected path (both-direction rule) →
  `protected_build_scope`;
  (f) scope with a `.git` part → `git_metadata_scope`.
  (Non-worker creating a task is additionally refused lead-only — recorded in
  R5 trace.)
- **R4 scheduling mathematics (CARD MATHEMATICS): N=4/4** —
  (a) fixture DAG (7 tasks, edges chosen below) yields a topological order
  that satisfies every edge;
  (b) critical path length == 4 nodes on the fixture (chain
  t_a→t_c→t_e→t_g), derived not tuned;
  (c) resource constraint: with 2 worker slots, the schedule's concurrent
  RUNNING set never exceeds 2 (measured over the whole simulation);
  (d) packet generation over all READY tasks in topo order: 7/7 packets, each
  4/4 required elements.
  Fixture DAG edges (fixed here): t_a; t_b; t_c←{t_a}; t_d←{t_b}; t_e←{t_c};
  t_f←{t_c,t_d}; t_g←{t_e,t_f}.
- **R5 deployed-source trace (PREDICTION judged against the DEPLOYED text at
  base 62b8e357): 6/6 semantics present with exact file:line quotes** —
  id regex + duplicate refusal (control.py:506); path_scope rules (41-49);
  dependencies_must_exist (508); claim refuses blocked/claimed
  (521 `task_not_ready`; 526 `dependencies_not_integrated`; 531-532
  `write_scope_conflict`); catalogue_next eligibility — PROPOSED + casefold
  live/done + INTEGRATED-only deps (822-825); lead-only create
  (_lead 113, applied 504).
- **R6 measured deviation (recorded finding, NOT adopted as the model's
  truth)**: the interceptor claim path (review_handoff.py:55-93, serving
  claims when active) binds {owner, slot, state, generation} at rh.py:90-91
  and performs NO instance-binding check, while the base claim binds
  owner_instance at control.py:554 and `_task` enforces it at 121-123.
  Predicted textual delta at base: `owner_instance` occurrences ==
  0 in review_handoff.py and == 8 in control.py (121,122,123,323,499,501,554,697).
  Consequence (recorded): for interceptor-claimed tasks owner_instance stays
  None, so the intended per-instance fencing is inert on the live claim path.
  Matches feedback c4212657; fix in flight as PR #80 (in review at this base).
  If the delta measures differently at this base, that is reported as a
  surprise finding, never silently reconciled.

## METHOD

1. Write the reference model (evidence-scoped, stdlib-only, <400 lines).
2. `controls/run_controls.py` executes R1-R4 against the model in one process
   and writes `checks/r1_positive.txt`, `checks/r2_falsifier_reassignment.txt`,
   `checks/r3_admission_integrity.txt`, `checks/r4_scheduling.txt` (refusals
   verbatim, post-state assertions listed, packet contents printed).
3. R5/R6 measured from the source text at base by a read-only script:
   `checks/r5_source_trace.txt` (quoted lines), `checks/r6_owner_instance_delta.txt`
   (occurrence counts + quoted bind sites).
4. RESULT.md: scoreboard, reproduction commands, source identity (git sha +
   file sha256), limitations, DYAD NOT_APPLICABLE record, integration contract
   and handoff (card deliverable 4).
5. Commit chain on astra/tasks/holodeck-gov-04 (trailer `Agent:
   subagent-worker-03`), push no-force, PR into astra/gait-capture,
   submit_review with exact HEAD.
