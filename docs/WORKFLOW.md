# Workflow - the current operating method

Status: written 2026-10-01 by worker wk-docsync from the Captain's documentation-sync
order; every command and path below was verified to exist on this host on that date,
and the flag/prose claims were re-verified against the worker-toolchain tree
216f5a767f26cd99d8bef62159a3797744f86314 (PR #304) at re-seal. Observed scheduler
state: registry revision 1676, scheduler serving enabled by the Lieutenant
2026-10-01. This file is navigation and method summary. It grants no authority; the
authoritative sources are the files it links.

A new worker or agent reads THIS file and
[E:/PythonChimera/tools/monkey_campaign/NO_WORKTREES.md](../tools/monkey_campaign/NO_WORKTREES.md)
first, then the linked authority for its role. Older workflow prose elsewhere in the
repository predates the file-package era (2026-09-30 and earlier) and is historical
context unless this file or NO_WORKTREES.md links it as current.

## 1. Authority chain in one paragraph

The human Captain sets the goal and holds final authority. The Lieutenant
(astra-codex label) dispatches ZCode agents, owns publication/merge/acceptance and
runs the resume discipline (section 7). The kanban registry
(`E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3`) is the single work
authority: cards, attempts, winners and events live there in transactions; workers
acquire work ONLY through the registry join/claim path. [DELIVERY.md](../tools/monkey_campaign/DELIVERY.md)
governs priority and reporting. The scheduler (section 3) watches the registry and
advises; it never replaces any of the above.

## 2. The file-package method (worker path)

Operator-authorized default since 2026-10-01: new task attempts use pinned file
packages, never Git clones or worktrees. The full contract is NO_WORKTREES.md; the
short form:

1. Start canonically with your existing arrival ID:
   `python -B E:/PythonChimera/tools/monkey_campaign/worker_start.py --arrival-id YOUR_ID`.
   An executable Kanban allocation invokes `worker_checkout.prepare` and returns
   `working_directory` under the attempt's package/files directory. The allocation's
   `base_sha` (or review `head_sha`) pins the input; a cached named publication ref
   is resolved and recorded, and is not a claim of remote freshness.
2. Edit the package files. Never run experiments directly in the editing package:
   `python -B E:/PythonChimera/tools/monkey_campaign/task_package.py seal ABSOLUTE_PACKAGE_DIRECTORY`
   then
   `python -B E:/PythonChimera/tools/monkey_campaign/task_package.py run --sealed SEALED_DIRECTORY --keep outputs/result.json -- PYTHON_EXECUTABLE -B RELATIVE_TEST.py`.
   Each seal returns a manifest hash, base SHA, changed-file list and a binary patch.
   Each run executes in one of four fixed CPU slots (auto-selected; `--slot 0..3`
   pins one). All slots busy returns state BUSY and CLI exit 75: wait and retry with
   backoff, never allocate another directory. Declare every needed evidence file
   with `--keep`; required missing outputs fail the job.
3. Send the sealed manifest hash, patch, base SHA and run receipts to the
   publication owner. The owner serializes Git mutations and may stage the package
   with `task_package.py apply --sealed SEALED_DIRECTORY --target SHARED_PUBLICATION_CHECKOUT`
   (requires a clean target at exactly the recorded base; stages only; commit,
   review, push, acceptance and merge authority stay with the existing owners).

Laws that ride on this method:

- Prereg pin: a prereg or amendment that requires a prior Git commit gets that
  commit published by the one publication owner BEFORE the gated experiment; the
  package is then pinned to the published prereg commit SHA. A seal never replaces
  a required commit. The unsquashed-lineage law stays in force.
- Publisher creates first dispatch refs: a card's `review/<CARD>` ref is seeded
  local AND remote at the integrated tip BEFORE its first dispatch, so a joining
  worker can pin a base. The scheduler's `named_ref_observation` reports a MISSING
  ref with the directive that the publisher must refresh it (section 3).
- Record accuracy (the W08 lessons, recorded in
  `E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-W08/source/DEV_RUN_REFUSALS.md`):
  every named development-run refusal is recorded under its refusal code in the
  frozen prereg or in a DEV_RUN_REFUSALS.md beside it; receipts report MEASURED
  values beside nominal values with deviation flags; reports carry no format
  placeholders (placeholder lint shipped with the W08 card's `lint_report_numbers.py`).
- Only a run receipt that says PASSED with `cleanup_verified: true` counts as a
  passing run, and that alone never qualifies physics or implies campaign acceptance.

Host profile: `E:/PythonChimera/tools/monkey_campaign/runner_profile.json`
(i9-13900K, 4 CPU slots, 16 GiB Windows Job limit per job, 4 threads per job,
agent target 12 / ceiling 15 including descendants, 1 publication writer).
Explaining unused agent capacity in every progress report is a permanent operator
rule (top section of NO_WORKTREES.md; CARD_STARTER v6): report observed-at time,
confirmed productive workers against the target, blocked/idle/unknown agents, and
concrete limiting reasons - occupied CPU slots alone do not prove capacity is
exhausted. GPU experiments still use the GPU queue at `E:/ChimeraWork/gpu-queue/`
per its PROTOCOL.md; the CPU package runner does not certify GPU work.

## 3. The continuous scheduler (serving since 2026-10-01)

Tool: `E:/ChimeraWork/monkey-coordination/compiler-scheduler/scheduler.py`.
A single poll-based process that watches the authoritative registry read-only,
PROJECTS the plan lifecycle vocabulary over registry states, and EMITS dispatch
directives. It is not a board and not a dispatcher: the Lieutenant remains the
dispatcher of ZCode agents; the queue it writes is `ADVISORY_QUEUE_LT_CONSUMES`.

- Modes: `--dry-run` (one read-only pass, default), `--serve --interval 60`
  (persistent loop; REFUSED unless the Lieutenant validated a dry-run and created
  `SERVE-ENABLED.txt` in the lane directory - enabled 2026-10-01),
  `--execute` (off by default; only code-owned lane-local steps: packet preview
  builds and stale-row reports), `--self-test`.
- Lifecycle as projection: WAITING, READY, DISPATCHED, RUNNING, VERIFYING, REVIEW,
  INTEGRATION, ACCEPTED, plus BLOCKED, CORRECTION_REQUIRED, SUPERSEDED. The
  registry's own state vocabulary is NOT extended; there is no FAILED state -
  failing rounds project as CORRECTION_REQUIRED with a failure signature.
- Idempotency: dispatch keys are `(task_id, criteria_sha256, kind [, head/failure
  signature])`. An IMPLEMENT directive is consumed exactly when the registry shows
  an attempt at the same criteria; a failing task is never redispatched without new
  information (changed failure signature); re-polls never duplicate open directives.
- Binding contract R1-R5 (in the module docstring): capacity truth is per-card
  registry attempts, never the vestigial ten-slot ledger or prompt rosters; the
  scheduler never writes cards; capacity domains stay separate (API agents per
  runner_profile.json, 4 CPU slots with BUSY exit 75 backoff, GPU mailbox untouched,
  1 publication writer).
- Artifacts (all in the lane directory): `next-dispatch-queue.json` (open/closed
  directives, capacity, stale rows, named-ref observation, pending acceptance-chain
  packets), `projection.json`, `dispatch-ledger.json`, `transitions.jsonl`,
  `LATEST-RUN.json`.
- The Lieutenant still owns: dispatching agents, accept/merge, publication, ref
  refresh, materialization at refill, retiring parked/stale rows, and the serve
  gate. The scheduler emits these as `LEAD_*` directives; it never executes them.

## 4. The acceptance chain

Authored-card path: each MAT2 card is a versioned specification-as-contract
(criteria sha-pinned; the 95-card catalog is
`E:/PythonChimera/tools/monkey_campaign/monkey_completion_map.json`, wave briefs in
`E:/ChimeraWork/monkey-coordination/gap-analysis/wave-*.md`). A candidate composes
against CARD_STARTER v6 (cite the version you compose against; v6 adds the
permanent capacity-reporting rule atop the v5 package-method and host-tuning
amendments: `E:/ChimeraWork/monkey-coordination/CARD_STARTER.md`), the house standards
(`E:/ChimeraWork/monkey-coordination/house-standards/IMPLEMENTER_CHECKLIST.md`,
`.../TOOLKIT.md`) and the card kit (`E:/ChimeraWork/monkey-coordination/card-kit/`,
including `batch_gates.py`, the one-process 12-gate pre-GPU pass).

Mechanical acceptance is tool-owned:
`E:/ChimeraWork/monkey-coordination/acceptance-chain/acceptance_packet.py` with
`build / approve / execute / resume / status / report / lifecycle / verify`
(full contracts in `E:/ChimeraWork/monkey-coordination/acceptance-chain/ACCEPTANCE_CHAIN.md`).
Packets are content-addressed; `approve` by a recorded authority is the judgment
checkpoint; `execute` runs four reconciled steps with an append-only oplog and
named refusals classified RESOLVED/EXECUTE/RETRIEVE/ASK/BLOCKED. The tool asserts
observed and checked facts only; it never chooses scientific claims or grants
acceptance itself.

Gates include capture conformance: visual evidence follows
`E:/ChimeraWork/monkey-coordination/format-spec/FORMAT_SPEC.md` and the FFV1 codec
standard in `E:/ChimeraWork/monkey-coordination/codec-benchmark/CODEC_STANDARD.md`;
evidence reaches the store only through
`E:/ChimeraWork/monkey-coordination/evidence-store/anchor.py add <file> --card MAT2-XX`
(one path, one sha; verify with `verify_store.py`); references are store paths, not
prose. Reviewer preflight packets live in
`E:/ChimeraWork/monkey-coordination/reviewer-preflight/`; findings-to-regression
proposals in `E:/ChimeraWork/monkey-coordination/findings-pipeline/propose_check.py`.

Correction loop: a CHANGES_REQUIRED verdict reopens scoped correction work on the
same card; the scheduler emits IMPLEMENT_CORRECTION only when the failure signature
changed (new review body/head/round); non-physics changes take delta reviews, physics
claims always take full independent review. Worker PASS is a recommendation, never
approval; only the Lieutenant records ACCEPTED and the verified merge.

Closeout at accept (worktree elimination policy): task acceptance and storage
release are one lifecycle observed by `lifecycle --packet`:
Accepted -> Evidence preserved -> Writers stopped -> Workspace released ->
Cleanup verified. The canonical manager is
`E:/ChimeraWork/tools/workspace_lifecycle.py` (its WORKSPACE_LIFECYCLE.md is
superseded for NEW workspace creation by the package method; legacy owners finish
and release their own checkouts). Evidence must already be anchored in the
evidence-store before anything disposable is removed.

## 5. The compiler stack

- Capability inventory: `E:/ChimeraWork/monkey-coordination/compiler-inventory/`
  (`README.md` human summary, `CAPABILITY_INVENTORY.json` authority). The
  single-authority map assigns one owning tool per responsibility and names the
  missing-function candidates MF-01..MF-10 (MF-01 is the scheduler above).
- Declaration format: `E:/ChimeraWork/monkey-coordination/compiler-declare/`
  (`membrane_schema.v1.json` + the hand-ground pair declaration
  `hand_ground_declaration.v1.json`). Four evidence classes on every parameter
  (MEASURED / AUTHORED_DECLARED / NAMED_PLACEHOLDER with debt owner / ABSENT with
  verbatim provenance); the pair run is honestly `declared_not_run`.
- Bindings: `E:/ChimeraWork/monkey-coordination/compiler-bind/`
  (`binding_extension.v1.json`, `bind_resolution.v1.json`,
  `scheduler_blocker_packet.v1.json`). 14 bindings resolve declared interactions to
  exact kernel implementations, state owners and verification classes: 8 BOUND,
  6 BLOCKED; 4 PERSISTENT connections vs 10 GENERATED contact instances. The 8
  named blockers NB-01..NB-08 (measured friction pins, x_press, x_share, x_reach,
  tendon waypoints/inputs, TC-3 drive re-declaration) each name their exact missing
  fact and debt owner.
- Newton adoption: `E:/ChimeraWork/monkey-coordination/newton-adoption/`.
  `INSTALL_BASELINE.md` pins the env (Python 3.13 venv at `E:/ChimeraWork/envs/newton`,
  newton 1.6.0, warp-lang 1.17.0, numpy 2.5.3, hash-verified wheels) and the
  baseline receipts: rigid-body capabilities PASS with exact identities (b1 warp
  context/CUDA graphs, b2 articulation/actuation, b3 contact/friction); the particle
  deformation path FAILS on this host (b4 divergence, b5 machine-readable repro) and
  is recorded, not hidden. SOFA/Chrono/Taichi adoption is DEFERRED; the lean is to
  adopt Newton only as a declared, separately-qualified backend while the sealed
  M06/M07/M08 line remains the mechanism of record. `ADAPTER_MAP.md` is the
  read-only binding map (24 concept rows; byte identity is a within-backend claim
  only; cross-backend numbers need separately-declared tolerances).

## 6. Disk doctrine

- The 150G free-disk floor is a standing law recorded in the Lieutenant resume
  (section 7): when free disk crosses the floor, no new card dispatch (G07-class
  holds) and the Captain is escalated with a reclaim directive; reclaim is
  lawful under the floor directive only.
- Runner-owned budgets (NO_WORKTREES.md): 256 MiB selected source per package,
  ~1 GiB retained package history, 2 GiB scratch per job, 256 MiB declared outputs
  per job, 1 MiB log tail, 20 GiB results admission threshold. Cleanup is in code:
  the runner stops the owned process tree, hash-verifies declared outputs, writes
  receipts and removes scratch; after a crash the slot recovery preserves unknown
  data rather than guessing.
- Legacy scratch budgets (100 GiB scratch / 100 GiB free) belong to
  `workspace_lifecycle.py` and its registered owners; new clones through it are
  disabled.
- Storage lifecycle table (authoritative form in ACCEPTANCE_CHAIN.md section 5 and
  WORKSPACE_LIFECYCLE.md): Accepted -> Evidence preserved -> Writers stopped ->
  Workspace released -> Cleanup verified. Documents that describe storage should
  cross-reference this table instead of inventing their own.
- Evidence-safe reclamation: `E:/ChimeraWork/monkey-coordination/retention/retention.py`
  deletes SCRATCH, never EVIDENCE; its anchor set (S1-S7 in `retention/README.md`)
  is rebuilt fresh every run from the registry, review verdicts, the failure museum
  (`E:/ChimeraWork/monkey-coordination/failure-museum/`) and manifest pins. The
  standing cleanup record lives in `E:/ChimeraWork/monkey-coordination/retention/ledgers/`.

## 7. Memory and resume discipline

- The registry is the durable work record; receipts are the durable run record.
  Prompt-side rosters are advisory only.
- The Lieutenant's operational state store is
  `E:/ChimeraWork/monkey-coordination/LIEUTENANT_RESUME_v2.json` (identity,
  authority, board state, acceptance-chain procedure, dated gotcha ledgers). A
  replacement Lieutenant resumes from it, not from conversation memory.
- Per-task durable lessons are separate files under
  `E:/ChimeraWork/monkey-coordination/memory/` (one file per task/lesson, e.g.
  worker lesson records and lane notes); `STATUS.json` carries the current lane
  summary. Workers append their own lesson files; nobody rewrites another agent's.
- The scheduler's lane artifacts (section 3) are the durable dispatch/projection
  history; `LATEST-RUN.json` is the last pass.

## 8. Command quick reference (all verified on this host)

    python -B E:/PythonChimera/tools/monkey_campaign/worker_start.py --arrival-id ID
    python -B E:/PythonChimera/tools/monkey_campaign/worker_start.py --arrival-id ID --task MAT2-XX
    python -B E:/PythonChimera/tools/monkey_campaign/worker_start.py --arrival-id ID --finish FILE     # + --take-next deals the next card
    python -B E:/PythonChimera/tools/monkey_campaign/worker_start.py --arrival-id ID --submit-pr FILE  # + --take-next
    python -B E:/PythonChimera/tools/monkey_campaign/worker_start.py --arrival-id ID --review-result FILE  # + --take-next
    python -B E:/PythonChimera/tools/monkey_campaign/worker_start.py --arrival-id ID --checkpoint FILE | --park FILE
    python -B E:/PythonChimera/tools/monkey_campaign/task_package.py seal PACKAGE_DIRECTORY
    python -B E:/PythonChimera/tools/monkey_campaign/task_package.py run --sealed SEALED --keep outputs/result.json -- PYTHON -B RELATIVE_TEST.py
    python -B E:/PythonChimera/tools/monkey_campaign/task_package.py apply --sealed SEALED --target PUBLICATION_CHECKOUT   # publication owner only
    C:/Python314/python.exe -B E:/ChimeraWork/monkey-coordination/compiler-scheduler/scheduler.py --dry-run
    C:/Python314/python.exe -B E:/ChimeraWork/monkey-coordination/compiler-scheduler/scheduler.py --self-test
    C:/Python314/python.exe -B E:/ChimeraWork/monkey-coordination/compiler-scheduler/scheduler.py --serve --interval 60   # gated by SERVE-ENABLED.txt
    python -B E:/ChimeraWork/monkey-coordination/acceptance-chain/acceptance_packet.py build|approve|execute|resume|status|report|lifecycle|verify ...
    python -B E:/ChimeraWork/monkey-coordination/evidence-store/anchor.py add FILE --card MAT2-XX
    python -B E:/ChimeraWork/monkey-coordination/evidence-store/verify_store.py

Handoff flags --finish/--submit-pr/--review-result record their JSON and then deal
the next card ONLY with the explicit `--take-next` flag; --checkpoint and --park
never re-deal. Keep the same arrival ID across all of them.

## 9. Document map (which file owns what)

| Topic | Authority |
| --- | --- |
| Package method, slots, cleanup, budgets | `tools/monkey_campaign/NO_WORKTREES.md` + `runner_profile.json` |
| Card composition, gates, GPU banking, versions | `E:/ChimeraWork/monkey-coordination/CARD_STARTER.md` (cite the version you compose against; v6 current) |
| Priority, delivery direction | `tools/monkey_campaign/DELIVERY.md`, `MATERIAL_PLAN_ADOPTION.md` |
| Continuous cycle, handoffs, review verdicts | `tools/monkey_campaign/CONTINUOUS_CYCLE.md`, `REVIEW_LANE.md`, `MERGE_SERVICE.md` |
| Dispatch queue, projection, lifecycle | `E:/ChimeraWork/monkey-coordination/compiler-scheduler/scheduler.py` + lane artifacts |
| Acceptance packets, oplog, storage stages | `E:/ChimeraWork/monkey-coordination/acceptance-chain/ACCEPTANCE_CHAIN.md` |
| Worker onboarding, Lieutenant onboarding | `tools/monkey_campaign/WORKER_ONBOARDING.md`, `LIEUTENANT_ONBOARDING.md` (current-method sections at top; older prose below is historical) |
| Older role/state navigation | `docs/WORKFLOW_INDEX.md`, `docs/FLEET_WORKFLOW.md`, `docs/MONKEY_RUN.md` |
| Compiler inventory/declare/bind/newton | the four lane directories under `E:/ChimeraWork/monkey-coordination/` (section 5) |

Publication note for this file: the documentation package that adds this file also
adds tools/monkey_campaign/NO_WORKTREES.md and tools/monkey_campaign/runner_profile.json,
copied byte-exact from the operational working tree (2026-10-01), so the links above
resolve in a fresh clone. tools/monkey_campaign/task_package.py is already carried by
the worker-toolchain import-closure fix in this tree; this package verifies its bytes
identical and changes nothing in it. The coordination lane directories under
E:/ChimeraWork/monkey-coordination/ remain host-operational state, intentionally not
Git-tracked; their links are valid on this host.
