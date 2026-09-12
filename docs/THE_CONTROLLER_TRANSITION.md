# Controller source transition: requirements before deployment

Read-only audit at integration `8d72c4f36f5565aa33edf04da86d9f2d86347dc0`.
The operating source for the live service must be independently inspected;
integrated PR #11 and a future catalogue PR are not evidence of deployment.

## Existing mechanism

`tools/agent_fleet/bootstrap_fleet.py` provides trusted `stop`, `start`,
`restart`, and `status` operations. `restart` composes stop and start. Start
reuses the durable database and private session/secret files. Stop checks the
listener against the PID record and waits for port drainage. Read the current
implementation before use; the PID record alone does not establish executable
image identity or ownership after PID reuse.

`tools/agent_fleet/control.py` supplies per-claim resource release and
supervisor slot release. It has no controller-wide quiescence barrier. A slot
release requires an integrated task and no held resources. It cannot honestly
be used to clear the stale binding of an unfinished GOV task by pretending that
task is integrated. `fleet-slot-binding-01` owns the necessary isolated repair
after the catalogue source change integrates.

## Required transition gates

STATEMENT: an approved source upgrade can preserve current claims, generations,
leadership epoch, reservations and evidence while rejecting unsafe lifecycle
actions. PREDICTION: an isolated rehearsal using the same durable-store format
survives upgrade and rollback, and rejects mismatched process identity or an
unacknowledged active worker/resource. FALSIFIER: lost or overwritten claims,
invented leadership, wrong process stopped, credentials exposed, stale binding
accepted, or successful deployment claimed without a post-restart snapshot.

Before a live transition, the lead must establish:

1. Exact reviewed source revision, supported store schema, private backup and
   rollback procedure. Keep credentials and database contents out of public
   evidence. Never delete a catalogue key directly as a routine rollback.
2. Worker checkpoints and acknowledged quiescence, plus actual runtime/eye
   drainage. Silence or an old "done" report is insufficient.
3. Listener PID, executable/command ownership, start identity, port and trusted
   launch record. Do not terminate a process solely because a stale PID file
   names it.
4. Isolated same-store upgrade/restart/rollback evidence before deployment.
   Preserve old session validity where the existing contract requires it.
5. Post-restart comparison of leader/epoch, claims/generations, slots/resources,
   checkpoints and source identity. Reopen dispatch only after reconciliation.

There is no implemented automatic pause/drain/source-rollback orchestrator at
this inspected revision. These are explicit remaining engineering requirements,
not instructions to improvise a direct database mutation. They extend the
existing fleet rather than replace its ledger or controller.

## Isolated transition rehearsal suite (2026-09-11, fleet-controller-upgrade-rehearsal-01)

`tools/agent_fleet/test_controller_transition.py` closes gate 4 ("isolated
same-store upgrade/restart/rollback evidence") as a rerunnable rehearsal. It
does not perform or claim any live deployment; the one live transition
(87e281e5-era service -> `slot-binding-d012b4b1`) remains evidenced only by
`evidence/agent_fleet/FLEET_OPERATIONS_RECORD/RECORD.md`.

How it works, entirely on temporary roots under the gitignored worktree
scratch and free loopback ports:

- Two deployment directories per test are built in the MANIFEST pattern of
  the live deployment (copied `tools/agent_fleet` runtime files, per-file
  sha256 manifest, `credentials_copied: false`), verified by re-hashing
  before use, and differentiated by an inert `SERVICE_MARKER`. Services are
  spawned only from these directories through the real `bootstrap_fleet.py`
  CLI — never from the integration checkout, which the served command line
  is explicitly asserted against.
- `Rehearsal.preflight` composes the required gates, read-only and strictly
  before any stop: deployment integrity; listener PID (netstat) vs pidfile
  consent record; listener executable-image path (process command line);
  store schema and credential identity hashes via a read-only open;
  acknowledged quiescence (for every RUNNING task, the latest `checkpoint`
  audit event must name the task's current generation — silence or an old
  "done" report is insufficient); actual runtime/eye drainage (registry
  resources empty).
- Backup/rollback use the SQLite backup API into
  `<root>/control/snapshots/pre-<label>.sqlite` plus `PRAGMA
  integrity_check`; rollback is exclusively the verified file restore over
  the same store. A row-level SQL patch is never a rollback path; the one
  crafted incompatible-schema store in the suite exists only to be refused
  (preflight `incompatible_store_schema`, then the controller constructor's
  `configuration_mismatch` at start), and only the backup restores service.

Measured at base `4604de40` (evidence:
`evidence/agent_fleet/CONTROLLER_TRANSITION/`, preregistration committed
before the code): 3/3 suite tests pass — upgrade and backup-restore rollback
both preserve the registry byte-for-byte (leader/epoch, claims, generations,
checkpoints, slots, audit events) and keep pre-upgrade session tokens valid
in both directions; stale acknowledgment, unacknowledged active worker, held
runtime/eye resource, tampered pidfile, image mismatch and incompatible
schema each refuse BEFORE any stop or mutation, leaving the old service
answering with an unchanged revision; credentials never appear in snapshot,
events, status or service logs. Full-suite context: the two
`test_master_catalogue.py` count-drift failures and the one Windows symlink
skip pre-exist at this base and belong to the catalogue lane.

Any future live transition must still clear gates 1-5 above with its own
pre-restart fingerprint, backup, quiescence verification and post-restart
reconciliation; this suite proves the procedure, not a deployment.

## Transport body cap (2026-09-11, fleet-transport-body-limit-01)

The first full catalogue import (GOV-01 clause-4 milestone) was refused by
the live transport: `MAX_BODY` 64 KB versus the canonical payload
1,518,593 B measured at tip `95f25b33`. The cap is transport policy ("not a
physics constant", per its own comment) and is now the derived 2**24
(16 MiB): measured payload, corpus-doubling headroom (×8), power-of-two
convention. `test_controller_transition.py::test_4` pins the boundary both
ways (under-cap served; over-cap refused `request_size` — note the refusal
may surface client-side as a mid-upload connection abort because the server
decides from the Content-Length header before reading the body). The change
deploys only through the controlled transition above; the live import retry
follows the transition and is recorded separately.
