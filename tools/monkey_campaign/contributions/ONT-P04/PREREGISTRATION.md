# PREREGISTRATION - ONT-P04 correction: GPU-A handoff authority/state machine (records profile)

Attempt: 4f4df57ef3d54c0996cf969e8a599d1b (branch-6)
Arrival: arrival-0074d33c896e4039a01dc67fc628a8bf
Pinned attempt head: c525b82c7c3ce0128565424764293a3c85811ab3
Card criteria hash: 6191e11ce3098cf90190c88a658267676e01163106dadaf883b0c48b7dc072db
Scope hash: 01ea5cddca8d4795caa096945edf7eadcd1f3eb3e2f084fd2ee36a08cae12ef6
Profile: records (offline). This correction is frozen before any probe below runs.
It answers the operational-lead CHANGES_REQUESTED ruling (evidence
E:/ChimeraWork/monkey-coordination/lead-verify-20260926/ONT-P04.json): clause 2
requires the handoff mechanism to EXIST and be verified, so the missing GPU-A
authority/state machine is implemented and probed numerically; the verified
clauses 1/3 records work of attempt fccb0a3f4fc74a29a7189453b6f91ced carries
forward unchanged. No live GPU work, no model unload/reload, no game
interruption, no training launch, no process preemption, no process launches
beyond `python -B` tests. All writes stay inside this attempt workspace (plus
the scoped sparse checkout path tools/monkey_campaign/contributions/ONT-P04/ of
this attempt's own checkout); E:/PythonChimera receives zero writes; the pinned
sources are extracted read-only via `git archive` at the attempt head.

## Frozen statement

The GPU-A handoff mechanism exists at this correction as `gpu_handoff.py`
defining `HandoffControl`, a subclass of the pinned `tools/agent_fleet/control.py`
`Control` (sha256 39ff01dc8a4192e04606ee9d87386780739e89c8a1774da48501a9545792f6b3).
It extends the native controller under its EXISTING authentication and atomicity:
one SQLite registry, every transition inside the controller's
`BEGIN IMMEDIATE` transaction, actor resolution through `Control._actor`,
task/generation identity through `Control._task`, GPU admission/release/clear
through the controller's own queue promotion, evidenced release and
supervisor-only clear laws. It adds an additive `handoff` plane
(`s.setdefault('handoff', ...)`, schema-1 compatible) and audit journal, visible
through the existing controller snapshot.

### Frozen states

Per handoff request, exactly: REQUESTED, DRAINING, READY, TRAINING, RESTORING,
AVAILABLE, plus RECOVERY_HOLD. Legal edges (each exercised by probes):
REQUESTED->DRAINING, DRAINING->READY, READY->TRAINING, TRAINING->RESTORING,
RESTORING->AVAILABLE, and ANY->RECOVERY_HOLD. Machine initial phase for a fresh
request is REQUESTED; AVAILABLE is terminal for that request (a new training
cycle is a new request). Every non-listed edge is refused by name.

### Frozen operations, guards and refusal names (exact strings)

- `handoff_request` (owner of a RUNNING task at the live generation; brief must
  carry derivation_gate_receipt, vram_required_mb>0, expected_duration_minutes>0,
  evidence; the training task must already hold an ADMITTED (queued, unserved)
  rtx4090 request in the controller resource queue): creates the handoff record
  in phase REQUESTED and enqueues it in ARRIVAL ORDER. Refusals:
  `stale_or_foreign_claim` (via _task), `invalid_handoff_brief`,
  `training_request_not_admitted`. IDEMPOTENT: an identical re-request (same
  task+generation, request still live) returns the SAME request id, adds no
  queue entry, bumps no journal entry, changes no phase. While a protected run
  is TRAINING, a new request records a waiting follower; it never preempts.
- `handoff_admit`: REQUESTED->DRAINING. Guards: actor owns the request task at
  the live generation; the request is the EARLIEST open request
  (`handoff_queue_jump_refused` - priority is recorded metadata, never a
  scheduling weight); no protected run is TRAINING (`protected_run_active`).
  From other phases: `handoff_not_requested`.
- `handoff_gate_close`: legal in DRAINING (`handoff_not_draining` otherwise);
  records inference_admission_closed with a deadline. Idempotent while closed.
  Closed gate behavior: `handoff_infer_wait` returns status RESOURCE_WAIT (the
  request waits; no model-load timeout consumption, no fallthrough);
  `handoff_reload_attempt` (JIT/retry bypass) refused `inference_admission_closed`;
  `handoff_gate_check` after the deadline returns GATE_TIMEOUT and the gate
  REMAINS CLOSED (`gate_timeout_gate_stays_closed`); `handoff_gate_open` refused
  `inference_gate_open_not_allowed` until the RESTORING->AVAILABLE restore path.
- `handoff_checkpoint_preserved` (DRAINING only, else `handoff_not_draining`):
  worker/session preservation evidence required (`preservation_evidence_required`).
- `handoff_model_unload` (DRAINING only): per NAMED instance id with restoration
  config (artifact, context, offload, worker associations). Refusals:
  `model_unload_all_refused` (no unnamed/--all unload), `restoration_config_required`,
  `instance_already_unloaded`.
- `handoff_game_release` (DRAINING only): registered game identity
  (executable path, pid, start_time) + graceful save/quit evidence + observed
  free VRAM number. Refusals: `unregistered_game_identity`, `game_identity_mismatch`,
  `graceful_release_required`. `handoff_force_kill` is NOT a legal operation in
  any phase and is always refused `force_kill_refused` (a failed graceful release
  must enter RECOVERY_HOLD via `handoff_hold`, never escalate to a kill).
- `handoff_ready`: DRAINING->READY (`handoff_not_draining` otherwise). Requires
  ALL: admission gate closed; checkpoint preserved; every registered instance
  unloaded with restoration config; registered game (if any) gracefully released;
  observed free VRAM >= requested (`insufficient_vram_evidence`; zero-total-VRAM
  is NOT required); and the controller registry shows rtx4090 held by nobody or
  by the training task itself (`protected_holder_present` otherwise - the
  gaming holder must complete the evidenced release first). Missing pieces are
  refused by the specific missing-piece name (`inference_gate_open`,
  `preservation_evidence_required`, `model_instances_still_loaded`,
  `game_not_released`).
- `handoff_launch`: READY->TRAINING (`handoff_not_ready` otherwise - this is the
  never-fabricate-READY gate: DRAINING/REQUESTED/RECOVERY_HOLD cannot launch).
  Requires the registry to show rtx4090 held BY the training task at the live
  generation (`gpu_not_held_by_training_task` - the grant is committed through
  the controller's own atomic promotion, never fabricated). Issues a durable
  run id exactly once; any later launch attempt (including after restart) is
  refused `already_launched`.
- `handoff_cessation`: TRAINING->RESTORING (`handoff_not_training` otherwise).
  Requires OBSERVED process/child cessation (evidence with observed=True;
  timer/lease/silence is refused `release_requires_observed_cessation`) and
  receipts/checkpoints preserved BEFORE release
  (`preservation_required_before_release`).
- `handoff_restore`: RESTORING->AVAILABLE (`handoff_not_restoring` otherwise).
  Reloads ONLY the captured restoration configs, per instance, with health
  evidence (`restoration_config_mismatch`, `unknown_instance`); resumes each
  preserved worker at most once (`worker_already_resumed`); all preserved
  workers resumed + health recorded, else `restore_incomplete`. There is no
  game auto-relaunch operation and no test-prompt operation.
- `handoff_hold`: ANY phase -> RECOVERY_HOLD with reason+evidence
  (`hold_evidence_required`). Any uncertain/failing transition lands here; the
  machine never fabricates READY.
- `handoff_recover`: SUPERVISOR ONLY (`supervisor_only`). Cross-checks the
  persisted phase against registry reality and the journal: TRAINING with the
  grant still held by the training task at the recorded generation reconstructs
  back to TRAINING (protection survives restart); TRAINING whose grant is gone
  reconstructs to RESTORING only with observed cessation evidence, otherwise
  stays RECOVERY_HOLD; READY with a foreign holder stays RECOVERY_HOLD
  (`resources_still_held`); an unknown/corrupt phase stays RECOVERY_HOLD and
  further transitions are refused `unknown_state_stays_recovery_hold`; demanding
  a specific resume state without the supporting evidence is refused
  `cannot_fabricate_ready` (READY/TRAINING) or `recovery_evidence_insufficient`.
  Restart never authorizes replaying a launch (`already_launched`).
- `handoff_state`: read-only visibility (any authenticated actor): phase,
  owner/task/generation, run id, evidence references, queue with arrival order,
  next action, journal tail. The additive plane is carried in the controller
  snapshot (transitions/owner/identity/evidence/next action visible through the
  existing controller, per COORDINATION.md).

### Frozen supervisor-only invariants

1. Graceful release before preemption: a registered game leaves the GPU only
   through evidenced graceful release; force-kill does not exist
   (`force_kill_refused`); failure enters RECOVERY_HOLD.
2. Never force-kill a protected run: while TRAINING, the holder keeps the
   resource against every later request (`protected_run_active`); the supervisor's
   own `resource_clear` still requires actual process-drain evidence
   (`actual_process_drained_evidence`, pinned controller law); timer/lease/silence
   never releases (`release_requires_observed_cessation`).
3. Recovery is supervisor-only and never fabricates READY.

### Frozen consistency-defect corrections (carried by this attempt)

- Draft qualification_receipt.json of attempt fccb0a3f4fc74a29a7189453b6f91ced
  set done_when_verified=true while clause 2 was unverified: OVERSTATED. The
  replacement receipt in this attempt sets done_when_verified=true only if all
  three clauses are actually verified by executed probes, and states each
  clause's verification basis. Live GPU qualification remains an open,
  separately-owned gate and is not claimed.
- Preserved-first-run-failure counts are inconsistent across the prior
  deliverables (checkpoint text: 5; report.md: 4; receipt.json enumerates 7
  items). The authoritative reconciliation frozen here: the receipt.json itemized
  enumeration (stale_generation->stale_or_foreign_claim x2;
  foreign_resource->stale_or_foreign_claim x1; over-broad admitted_mb assertion
  after queued auto-promotion; task-id charset train_a->train-a; broker
  supervisor token; wrapped-markdown record match) = 7 individual expectation
  fixes is the authoritative count; report.md's 4 counts only the
  refusal-name/memory subset (3 refusal-name + 1 memory), omitting the task-id
  charset, broker-token and markdown-match fixes; the checkpoint's 5 is also an
  undercount of the same 7-item list. No evidence was contradictory - the two
  smaller numbers were stale summaries of the same list. This correction's OWN
  probe first-run failures are archived as output files under
  first_run_failures/ (file per failing run) so the preservation claim is
  verifiable from artifacts, not session history.

## Frozen prediction

1. Pinned suites at head c525b82c pass CPU-only: test_resources (12),
   test_resource_lifecycle (12), test_review_handoff (13),
   test_review_handoff_claim (12), test_run_queue (8).
2. Carried-forward prior probes pass unchanged against the pinned extraction:
   test_p04_contract.py (17), test_p04_records.py (6) - including its probe
   asserting the six-state machine is absent from PINNED control.py, which
   stays true because HandoffControl is a scoped additive subclass contribution,
   not a mutation of the pinned controller.
3. New GPU-A probes (test_gpu_handoff.py) pass: the five legal edges of the
   six-state sequence execute in order with the registry showing the actual
   grant/hold/release at each step; every frozen illegal transition is refused
   by its exact name; re-request is idempotent; a restarted authority
   reconstructs state from the journal + registry and keeps a protected run
   protected; unknown state stays RECOVERY_HOLD; the inference gate stays
   closed on timeout and blocks bypass attempts.
4. New correction-records probes (test_correction_records.py) pass: the 7-item
   failure enumeration reconciles the 4/5/7 defect as frozen above; the
   implemented module is byte-identical between this workspace and the scoped
   checkout sparse path; the replacement qualification receipt is honest.
5. Total battery exits 0, CPU-only, `python -B`.

## Frozen falsifier

Any of: a claimed pass unsupported by executed records; a probe failure
suppressed; a double grant or a priority queue jump observed; a state skipped
or an illegal transition accepted; RECOVERY_HOLD ever yielding READY/TRAINING
without the frozen evidence; a force-kill path existing or succeeding; a
protected run displaced; a gate opening on timeout; an un-evidenced launch;
a live GPU/handoff/training claim; any write outside the attempt workspace and
its scoped checkout sparse path; a receipt flag not matching verified clauses.
Missing identities or a claimed pass unsupported by records fails.

## Frozen probes (exact, executed after this freeze)

- R0 Extract from the attempt checkout commit c525b82c (git archive, read-only)
  into `<workspace>/pinned/`: `tools/agent_fleet/*.py`,
  `tools/monkey_campaign/COORDINATION.md`,
  `tools/monkey_campaign/GPU_HANDOFF_PREREGISTRATION.md`,
  `tools/monkey_campaign/monkey_completion_map.json`; copy the untracked
  working-tree record GPU_HANDOFF_PUBLICATION_RECEIPT.json as
  `GPU_HANDOFF_PUBLICATION_RECEIPT.untracked.json`. Record sha256 of every
  extracted file in pinned_file_hashes.json; identity bound to the commit by
  archive construction and `git rev-parse HEAD`.
- P1 Run the five pinned suites CPU-only with `python -B -m unittest` (isolated
  temporary registries; loopback-only fixtures inside the pinned suites).
- P2 Carried forward: prior test_p04_contract.py + test_p04_records.py, byte
  -identical to the hash-verified prior attempt copies, run against the pinned
  extraction.
- P3 New `gpu_handoff.py` (implementation, written after this freeze but before
  any run; mirrored byte-identically into the checkout sparse path
  tools/monkey_campaign/contributions/ONT-P04/) and `test_gpu_handoff.py`
  (written before any run): the frozen state/transition/refusal matrix above,
  with these probe groups and minimum counts - H1 legal chain (6 edges),
  H2 illegal-transition refusal matrix (every non-legal op from every phase,
  exact names), H3 idempotent re-request, H4 crash-recovery reconstruction
  (restart during TRAINING/READY, corrupt state, launch replay),
  H5 supervisor-only invariants, H6 inference admission gate (RESOURCE_WAIT,
  timeout stays closed, bypass refused, open only on restore).
- P4 New `test_correction_records.py` (written before any run): the frozen
  failure-count reconciliation (reads the preserved prior artifacts read-only),
  implementation byte-identity between workspace and checkout sparse path,
  receipt honesty cross-check (done_when_verified true iff all three clause
  entries are VERIFIED), and pinned-extraction hash parity with the prior
  attempt's pinned_file_hashes.json for all common files.
- Views: none (records profile; nonvisual). Camera fields: none required.
  Numerical evidence: exact pass/fail counts, refusal names and file hashes
  recorded in probe_run_results.json, report.md and the receipts.

## Applicability boundary

This implements and verifies the GPU-A authority/state machine as records:
CPU-only state transitions over isolated temporary registries. It does not
execute or certify a live GPU handoff, model unload/reload, game interruption,
training launch or process preemption; GPU-B/C/D adapters and live
qualification remain governed by their owning records in COORDINATION.md.
Fixture results are labeled fixtures; the live registry is never written.
