# CONTROLLER_TRANSITION — Preregistration (before any code or run)

Task: `fleet-controller-upgrade-rehearsal-01` (gen 1, slot 2, owner
subagent-worker-03, lead glm53-lead-02 epoch 5).
Base: `4604de40bd6cdd02d3cc277019f8bac5030c2dbe` (= recorded integration tip at
claim time; no stale-base merge needed).
Recorded: 2026-09-11, BEFORE implementing
`tools/agent_fleet/test_controller_transition.py` and before any run.
Deliverable closes `fleet-controller-upgrade-01`'s remaining rehearsal lane; the
one live transition (87e281e5-era service -> `slot-binding-d012b4b1`) is already
separately evidenced in `docs/evidence/agent_fleet/FLEET_OPERATIONS_RECORD/RECORD.md`
and is NOT re-claimed here.

## STATEMENT

Current-generation acknowledged quiescence, verified process identity,
SQLite-consistent backup and same-store restart/rollback can upgrade controller
source without stale authority or data loss, rehearsed end-to-end in isolation
on temporary roots.

## PREDICTION

1. Positive upgrade: starting the service from deployment A, accumulating live
   state (leader/epoch, a RUNNING claim with a current-generation checkpoint, a
   REVIEW claim, an INTEGRATED request, audit events), then controlled
   stop -> start from deployment B over the SAME store preserves claims,
   generations, leader, epoch, session tokens and audit history.
2. Rollback: stop -> restore the pre-upgrade SQLite-consistent backup ->
   start from deployment A over the same store restores exactly the pre-upgrade
   registry and the pre-upgrade session tokens remain valid.
3. Each of the following refuses BEFORE any stop or mutation, leaving the old
   service answering on the port with an unchanged registry revision:
   a. stale worker acknowledgment (latest checkpoint event at a generation
      below the task's current generation),
   b. active unacknowledged worker (RUNNING claim with no checkpoint event),
   c. held runtime/eye resource (`dyad_eye`/`rtx4090` registry holds),
   d. wrong PID identity (pidfile naming a live but different process than the
      port listener; the bootstrap must refuse the stop, and the named wrong
      process must survive),
   e. listener image mismatch (served executable path not the expected
      deployment's `service.py`),
   f. incompatible store schema (registry whose `schema` is not 1 refuses
      preflight while running, and refuses `start` at the controller
      constructor).

## FALSIFIER (named before the run)

- A refusal path that stops or kills a process (in particular the process named
  by the tampered pidfile) instead of refusing.
- A stale-generation acknowledgment admitted as quiescence.
- A claim, generation, checkpoint, leader/epoch or audit event lost across the
  upgrade or the rollback (or a rollback that silently drops state the backup
  was supposed to preserve).
- Any supervisor/enrollment/session token appearing in snapshot output, events,
  status reports or service logs (exposed credentials).
- A direct SQL patch to the store treated as the rollback path. The rollback
  under rehearsal is exclusively the verified consistent backup restore; the
  incompatible-schema store is a hand-crafted FIXTURE whose only legal role is
  to be refused.
- Starting a service from the integration checkout and calling that a
  deployment: every service spawn in this suite must come from an explicitly
  built deployment directory (copied files + hash MANIFEST, verified before
  use), never from the worktree source, and the served command line must name
  the deployment path, not the checkout.

## Method (fixed before implementation)

- Suite: `tools/agent_fleet/test_controller_transition.py`, `python -m unittest`
  from the repo root of the provisioned worktree; services on free loopback
  ports; every spawned service stopped in `tearDown`; all scratch under the
  worktree's gitignored `.tmp/` (never committed).
- Deployments: `make_deployment()` copies the runtime `tools/agent_fleet` files
  into two temp directories (`dep-old`, `dep-new`), writes a `MANIFEST.json`
  (sha256 + bytes + source revision per file, `credentials_copied: false`) in
  the pattern of the live deployment `slot-binding-d012b4b1`, and marks the
  generational difference with an inert `SERVICE_MARKER` constant in
  `service.py`. `verify_deployment()` re-hashes every file before any use.
- Lifecycle through the real operator CLI (`python <dep>/bootstrap_fleet.py
  start|stop --root <tmp> --port <free> [--json]`), matching
  `test_bootstrap_fleet.py`; state building through the real HTTP surface
  (`client.call`), matching the existing suites.
- Transition gates (`preflight`), all read-only, all BEFORE any stop:
  deployment integrity; fleet fingerprint on the port; listener PID resolved
  via netstat (reusing `bootstrap_fleet` machinery); pidfile-vs-listener
  match; listener image path check (PowerShell `Get-CimInstance` process
  command line on Windows, `ps` elsewhere); read-only store open asserting
  `schema == 1` and credential identity hashes (reusing
  `FleetBootstrap.verify_reconciled`); acknowledged quiescence = for every
  RUNNING task the latest `checkpoint` event names the task's current
  generation (silence or an old "done" is insufficient); actual drainage =
  registry `resources` empty.
- Backup: SQLite backup API into `<root>/control/snapshots/pre-<label>.sqlite`
  (inside the temp root, mirroring the live convention), then
  `PRAGMA integrity_check` and a schema read of the copy.
- No live control-plane mutation: the real `E:\ChimeraWork\control\` store and
  service are never touched; no supervisor operations; no GPU/model use.

## Acceptance planned (to be measured after implementation)

Run `python -m unittest tools.agent_fleet.test_controller_transition -v` and
the full `python -m unittest discover -s tools/agent_fleet -p 'test_*.py'` from
the repo root. Baseline to preserve: the suite must end 0 failures without
weakening any existing test (known platform skip: 1 Windows-symlink skip).
Raw verbatim outputs land in this directory; `MEASUREMENT.json` embeds the
producing commands; `RESULT.md` records the per-prediction verdict table.

## NOT_CLAIMED (fixed in advance)

- No live deployment identity, acceptance or source integration is claimed by
  this rehearsal: the live transition remains evidenced only by the existing
  operations record.
- No new controller source is authored here; this lane delivers the rehearsal
  suite only.
- No claim about dual-generation (schema-2) forward compatibility: the suite
  only proves refusal of an incompatible store, never interoperability.
