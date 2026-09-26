# ONT-P04 correction report - GPU-A handoff authority/state machine (records)

Attempt `4f4df57ef3d54c0996cf969e8a599d1b` (branch-6), arrival
`arrival-0074d33c896e4039a01dc67fc628a8bf`. Pinned attempt head
`c525b82c7c3ce0128565424764293a3c85811ab3`. Card criteria
`6191e11ce3098cf90190c88a658267676e01163106dadaf883b0c48b7dc072db`. Scope
`01ea5cddca8d4795caa096945edf7eadcd1f3eb3e2f084fd2ee36a08cae12ef6`. Profile:
records (offline). Dependency ONT-P03 DONE (winner PR #140, head `e1443d45`,
merged) - unchanged.

## What this correction answers

Operational-lead CHANGES_REQUESTED on publication
`publication-3a6a3e498a0740efad08936e19c831df` (evidence
`E:/ChimeraWork/monkey-coordination/lead-verify-20260926/ONT-P04.json`):
clause 2 requires the handoff mechanism to EXIST and be verified; at the
pinned head it did not (contract records only). Delta taken: **implement the
GPU-A authority/state machine at the qualified head with records-profile
numerical transition probes**. Clauses 1 and 3 findings are carried forward
without rework (byte-identical probe copies, hash-checked). Two consistency
defects are also corrected (below). No live GPU work, no model unload/reload,
no game interruption, no training launch, no process preemption was performed
or claimed; E:/PythonChimera received zero writes; all writes stayed inside
this attempt workspace plus its own checkout sparse path
`tools/monkey_campaign/contributions/ONT-P04/`.

## The implemented mechanism (GPU-A)

`gpu_handoff.py` defines `HandoffControl`, an additive subclass of the pinned
`tools/agent_fleet/control.py` `Control` (sha256 `39ff01dc...`, unchanged at
the pinned head - the pinned COORDINATION.md statement that control.py "does
not implement the model/game handoff above" stays true of control.py itself;
the machine extends it under its existing authentication). No rival GPU
authority: one SQLite registry, every transition inside the controller's
`BEGIN IMMEDIATE` transaction, actor resolution through `Control._actor`,
task/generation identity through `Control._task`, and the actual GPU
grant/release/clear through the controller's own queue promotion, evidenced
release and supervisor-only clear laws. The machine adds a schema-1-compatible
`handoff` plane (`setdefault`) with an audit journal, visible through the
existing controller snapshot and `handoff_state`.

States: `REQUESTED -> DRAINING -> READY -> TRAINING -> RESTORING -> AVAILABLE`
plus `RECOVERY_HOLD` (any uncertain/failing transition; it never fabricates
READY). Semantics follow the COORDINATION.md handoff section:

- **Request and validate**: brief (derivation/gate receipt, VRAM, duration,
  requester identity, existing training owner), the training task must hold an
  ADMITTED (queued, unserved) `rtx4090` request in the controller queue;
  arrival-order serialization, idempotent re-request (same record, no drain
  restart, no journal entry).
- **Drain**: inference-admission gate (`RESOURCE_WAIT` tickets; requests wait
  without a model-load timeout or fallthrough; timeout leaves the gate CLOSED;
  JIT/reload bypass refused `inference_admission_closed`; the gate opens only
  on the restore path), worker checkpoint preservation, named model unloads
  with restoration configs (no `--all`), graceful game release bound to a
  registered identity (executable+pid+start_time) with observed free-VRAM
  numbers. `handoff_force_kill` is refused `force_kill_refused` in every
  phase, for every actor: a failed graceful release enters RECOVERY_HOLD.
- **Ready**: all drain pieces by name (`inference_gate_open`,
  `preservation_evidence_required`, `model_instances_still_loaded`,
  `game_not_released`, `insufficient_vram_evidence`), and no foreign holder on
  `rtx4090` (`protected_holder_present`) - zero-total-VRAM is not required.
- **Grant and launch once**: the grant is committed through the controller's
  own promotion (gamer's evidenced release auto-promotes the trainer's queued
  request); `handoff_launch` verifies the registry hold (`gpu_not_held_by_
  training_task` - never fabricated) and issues a durable run id exactly once;
  any replay, including across a restart, is `already_launched`.
- **Release and restore**: `handoff_cessation` requires OBSERVED cessation
  (`release_requires_observed_cessation` for timer/lease/silence) and
  preservation BEFORE release (`preservation_required_before_release`); the
  hold itself still releases only through the owner's evidenced
  `resource_release` (C3 law, `release_dyad_first`/`release_engine_first`
  intact); `handoff_restore` reloads only captured configs
  (`restoration_config_mismatch`, `unknown_instance`), resumes each preserved
  worker at most once (`worker_already_resumed`), opens the gate, reaches
  AVAILABLE. Games are not auto-relaunched (no such op).
- **Recovery**: supervisor-only `handoff_recover` (`supervisor_only`)
  reconstructs from journal + registry reality: TRAINING with a live grant
  resumes TRAINING (protection survives restart, run id preserved); TRAINING
  whose grant vanished resumes RESTORING only with observed cessation
  evidence, else stays RECOVERY_HOLD (`recovery_evidence_insufficient`);
  READY with a foreign holder refuses `resources_still_held`; corrupt/unknown
  phase stays RECOVERY_HOLD and blocks transitions
  (`unknown_state_stays_recovery_hold`); demanding READY from a hold is
  `cannot_fabricate_ready`.

## Executed verification (frozen probes; all CPU-only, `python -B`)

Extraction: `git archive` from the attempt checkout commit `c525b82c` into
`pinned/` (52 files; per-file sha256 in `pinned_file_hashes.json`; all common
files hash-identical to the prior verified extraction; the untracked working
-tree record is labeled `GPU_HANDOFF_PUBLICATION_RECEIPT.untracked.json`).
Fixtures are isolated temporary registries; loopback-only servers exist only
inside the pinned suites.

| Suite | Result |
|---|---|
| pinned test_resources.py | 12/12 OK |
| pinned test_resource_lifecycle.py | 12/12 OK |
| pinned test_review_handoff.py | 13/13 OK |
| pinned test_review_handoff_claim.py | 12/12 OK |
| pinned test_run_queue.py | 8/8 OK |
| probe test_p04_contract.py (carried forward) | 17/17 OK |
| probe test_p04_records.py (carried forward) | 6/6 OK |
| probe test_gpu_handoff.py (new) | 28/28 OK |
| probe test_correction_records.py (new) | 10/10 OK |

Total 118/118 OK, exit 0. Exact commands, exit codes, durations, hashes and
the carried-forward byte-identity check: `probe_run_results.json`. New-probe
coverage: 6 legal edges with registry facts at each (grant transfer via
controller promotion; hold persisting through observed cessation until the
owner's evidenced release); the illegal-transition refusal matrix with exact
frozen names from every phase; idempotent re-request and arrival-order (not
priority) admission; crash recovery across a supervisor restart (protected run
stays protected, replay refused), READY-with-foreign-holder, corrupt phase,
hold-then-recover; supervisor-only invariants; the inference admission gate
(RESOURCE_WAIT accumulation, timeout stays closed, bypass refused, open only
on restore).

First-run failures of THIS attempt's new probes are preserved as files in
`first_run_failures/` (see its INDEX.md for the complete sequence). Summary:
`test_gpu_handoff.py` run1 (4 errors + 1 failure), run2 (1 error + 1 failure),
run3 green - all five were probe-fixture/expectation defects (a missing
`handoff_admit` step in an H6 helper x3; a new-cycle probe that needed a newly
admitted, genuinely contended controller request; one expectation that
contradicted the frozen semantics - with the grant still live, recover
correctly resumes TRAINING, and the probe now asserts the stronger
`already_launched` replay guard). The battery stage then surfaced: an
extraction-layout mismatch for the untracked receipt against the byte-identical
carried `test_p04_records.py` (fixed by aligning to the prior verified
`pinned/`-root layout), two wrapped-markdown assertion defects in
`test_correction_records.py` (fixed by whitespace normalization - the same
defect class as the prior attempt's recorded "wrapped-markdown record match"
first-run fix), and a runner bug that checked this attempt's own prereg
against the PRIOR attempt's prereg hash (removed; this attempt's prereg,
sha256 `124c3acf...`, is unchanged since its freeze BEFORE any probe ran).
No failure was a defect in the frozen semantics or the implementation's
decision logic. Nothing suppressed.

## Consistency-defect corrections

- **Draft receipt overstatement**: the prior draft
  `qualification_receipt.json` set `done_when_verified=true` while clause 2
  was unverified - OVERSTATED (lead anomaly). The replacement receipt in this
  attempt sets the flag from the clause map (true only because all three
  clauses now verify at the records profile) and names the live gate as
  remaining. A records probe enforces the flag-matches-clause-map property.
- **First-run-failure count mismatch (4 report / 5 checkpoint / 7 receipt)**:
  the authoritative count is the prior receipt.json itemized enumeration =
  **7** individual expectation fixes (stale_generation->stale_or_foreign_claim
  x2; foreign_resource->stale_or_foreign_claim x1; over-broad admitted_mb
  assertion after queued auto-promotion; task-id charset train_a->train-a;
  broker supervisor token; wrapped-markdown record match). report.md's 4
  counted only the refusal-name+memory subset (3+1) and omitted the task-id
  charset, broker-token and markdown-match fixes; the checkpoint's 5 was
  likewise an undercount of the same single list. No contradictory evidence
  existed - both smaller numbers were stale summaries of one pool, all
  disclosed, none suppressed. Records probes verify the arithmetic (4+3=7)
  against the preserved prior artifacts read-only. Going forward, this
  attempt archives its own failing-run outputs as files, so preservation is
  verifiable from artifacts rather than session history (the lead's anomaly).

## Honest limits

- No live GPU handoff, no Bionic/LM Studio unload, no game release, no
  training job: GPU-B/C/D and live qualification remain open with their
  owning records and are NOT satisfied by this card. All "drained"/"graceful"
  evidence in fixtures is recorded strings, not real process state.
- The machine is a scoped contribution (new additive module in
  `contributions/ONT-P04/`), not a mutation of pinned control.py at
  c525b82c; publication through the lead's review/PR lane remains the trusted
  path for controller changes (COORDINATION.md implementation-queue rule).
- Historical fleet demonstrations do not establish what is running now; no
  claim is made about the live `E:/ChimeraWork/control` service state.

## Next step for the lead

Publish the correction artifacts to `review/ONT-P04`, run the non-author
review, pin the replacement qualification receipt (numerical + source +
independent_review) with head_sha re-bound to the published PR head. The
verified clauses-1/3 records work carries forward unchanged.
