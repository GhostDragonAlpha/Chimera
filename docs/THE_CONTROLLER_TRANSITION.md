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
