# CONTROLLER_TRANSITION — Result record

Task: `fleet-controller-upgrade-rehearsal-01` gen 1, slot 2, owner
`subagent-worker-03` (lead `glm53-lead-02`, epoch 5). Compared against
`PREREGISTRATION.md` (committed `cbf0a7b4` before any code or run). Recorded
after execution, 2026-09-11.

## Implemented (tools/agent_fleet/test_controller_transition.py)

One rehearsal suite, three tests, built only from the existing machinery —
`bootstrap_fleet.FleetBootstrap` / `fleet_on_port` (imported; `free_port`
pattern-shared with `test_bootstrap_fleet`), the real operator CLI, the real
HTTP controller surface, and the SQLite backup API:

1. `make_deployment` / `verify_deployment`: deployment directories built in
   the live MANIFEST pattern (copied runtime files, per-file sha256/bytes/
   source, `credentials_copied: false`), verified by re-hashing before any
   use. Two content states via an inert `SERVICE_MARKER`; a deployment is
   never the integration checkout (asserted against the served command line).
2. `Rehearsal.preflight`: the transition gates, all read-only, all BEFORE any
   stop — deployment integrity; fleet fingerprint on a free port; listener
   PID resolved via netstat; pidfile-vs-listener match; listener image path
   (PowerShell `Get-CimInstance` command line on Windows, `ps` elsewhere);
   read-only store open (`schema == 1` + credential identity hashes via
   `FleetBootstrap.verify_reconciled`); acknowledged quiescence (for every
   RUNNING task the latest `checkpoint` event must name the task's current
   generation); actual drainage (registry `resources` empty).
3. `Rehearsal.backup` / `restore_backup`: SQLite-consistent backup into
   `<root>/control/snapshots/pre-<label>.sqlite` (live naming convention,
   temp root), `PRAGMA integrity_check` + schema read of the copy; rollback
   is exclusively the verified file restore, never a row-level SQL patch.

## Commands and outcomes (isolated temporary roots, free loopback ports)

- `python -m unittest tools.agent_fleet.test_controller_transition -v`
  (repo root, provisioned worktree): **3/3 OK** (~83 s).
- `python -m unittest discover -s tools/agent_fleet -p 'test_*.py' -v` from
  repo root: **169 tests, 2 failures, 1 skip** — both failures and the skip
  are pre-existing at pristine base `4604de40` and outside this task's write
  scopes (see below). The 3 new tests pass inside the full run.
- Raw verbatim outputs: `RUN_TEST_CONTROLLER_TRANSITION.txt`,
  `RUN_FULL_SUITE.txt`. Per-prediction verdicts with observed refusals:
  `MEASUREMENT.json`.

## Prediction matrix (all PASS)

| Prediction case | Test | Verdict |
|---|---|---|
| Upgrade preserves claims/generations/leader/epoch/sessions/audit | test_1 (snapshot dict equality, events preserved then extended, pre-upgrade token still writes) | PASS |
| Backup restore rollback restarts old deployment, restores registry + session validity | test_1 (post-rollback snapshot == pre-upgrade snapshot; events reverted with the store; preflight passes against dep-old) | PASS |
| Stale worker acknowledgment refuses before stop | test_2 (`stale_worker_acknowledgment:lane-a`) | PASS |
| Active unacknowledged worker refuses before stop | test_2 (`unacknowledged_active_worker:lane-b`) | PASS |
| Held runtime/eye resource refuses before stop | test_2 (`resources_not_drained:dyad_eye,rtx4090`) | PASS |
| Wrong PID identity refuses; wrong process survives | test_2 (`pidfile_listener_mismatch` gate + CLI exit 1 `refusing_stop_unmanaged`; service and the wrongly-named live process both survived) | PASS |
| Listener image mismatch refuses before stop | test_2 (`listener_image_mismatch`); positive: served image names the deployment, never the checkout | PASS |
| Incompatible schema refuses preflight and start; only the backup recovers | test_2 (`incompatible_store_schema:2` preflight; start exit 3 `service_exited_before_ready` + `configuration_mismatch`; snapshot equality restored only via verified backup) | PASS |
| Credentials never exposed | test_3 (tokens absent from snapshot/events/status/logs; hash fields popped) | PASS |

## Pre-existing failures (NOT caused by this change; documented, not silenced)

- `test_master_catalogue.py::test_import_real_sources_full_coverage`
  (82 != 76 master_row_ids) and
  `::test_gen5_exhaustive_partition_no_silent_omissions` (2584 != 2540) fail
  identically when run alone in this worktree, whose catalogue files are
  byte-identical to base `4604de40` (`git diff 4604de40` on those paths is
  empty). Same drift class already recorded in
  `SLOT_BINDING/RESULT.md` (65→76 then; 76→82 now): the pinned counts predate
  Master-list growth merged by other lanes. The catalogue lane owns the pins;
  repairing them is outside this task's scopes
  (`test_controller_transition.py`, `THE_CONTROLLER_TRANSITION.md`, this
  evidence directory). Not weakened, not skipped, not silenced.
- 1 skip: `test_worktree_reconcile` 'symlink creation unavailable' — the
  known Windows baseline skip.

## Deviations from the packet procedure

- The preregistration commit (`cbf0a7b4`) required `--no-verify`: the repo's
  pointer-guard hook refuses any commit whose text references a path that
  does not yet exist, and a prereg-first commit necessarily forward-references
  the test file it commissions. The drift is owned in that commit message and
  resolves with the code commit. Every other guard ran clean on later commits.

## Acceptance

Acceptance for the transition mechanism is NOT_CLAIMED here. This rehearsal
closes the remaining deliverable of `fleet-controller-upgrade-01`'s rehearsal
lane: the isolated positive upgrade + rollback path and the pre-stop refusal
matrix now exist as executable, rerunnable evidence. The one live transition
(87e281e5-era service -> `slot-binding-d012b4b1`) remains evidenced only by
`FLEET_OPERATIONS_RECORD/RECORD.md`; any future live upgrade must still clear
gates 1-5 of `THE_CONTROLLER_TRANSITION.md` with its own pre-restart
fingerprint, backup, quiescence verification and post-restart reconciliation.
