# fleet-client-instance-01 preregistration (2026-09-11, lead lane)

Task: `fleet-client-instance-01` generation 1, slot 1 (integration kind),
worktree `E:\ChimeraWork\slot-01`, recorded base `9022d669…` reconciled to
integration tip `c1a1ec5a` by merge (never force).

**Proven baseline (feedback `4a1e631e`, reproduced against deployed
control.py):** two ThreadPool clients sharing one bearer can both checkpoint
the same task (saved=true at consecutive revisions); the audit records only
the actor, dropping the client instance. Shared Git config authorship is not
identity. The operator explicitly asked the workflow to identify/coordinate
many active agents without mapping windows by hand.

- **STATEMENT** (task packet): authorized independent clients have distinct
  durable instance identities and only the current bound instance/generation
  may mutate its claimed task; duplicated legacy credentials cannot silently
  establish a second writer; the audit identifies the admitted instance;
  restart preserves bindings; recovery requires actual drain/preservation.
- **DESIGN (derived, task-centric fence with staged migration):**
  1. The trusted launcher (`enroll_agent.py`) mints a per-enrollment instance
     (`instance_id` + `instance_secret`) into the session file; the enroll op
     records only the secret's sha256 fingerprint under the agent record.
     Identity is a secret, never a PID (PID reuse cannot authorize a writer).
  2. `client.py` sends `X-Chimera-Instance: <id>:<secret>` on every call when
     the session carries instance fields; the service parses it into the
     request context (malformed → named refusal `invalid_instance_header`).
  3. `claim` binds the claiming instance to the task
     (`owner_instance`); every task-mutating op (checkpoint, submit_review,
     resource_*, integration_request) requires the caller's instance to
     match when the task is bound — a second instance of the SAME agent is
     refused `instance_not_bound`. Tasks claimed by legacy (instance-less)
     sessions stay unfenced until re-enrollment: compatibility is explicit
     and auditable (`instance: legacy-unfenced` in events), never silent.
  4. Registry flag `instance_fencing`: `compat` (default; new bound claims
     are fenced, legacy claims auditable-unfenced) → `enforced` (rejects
     instance-less claims; flipped only through a reviewed controlled
     transition after per-client migration — not executed in this PR).
  5. Events carry the instance id (never the secret). Restart persists
     everything (state doc). The same-OS-account shell boundary stays
     explicit: bearer+instance fencing is cooperative capability, not a
     sandbox.
- **PREDICTION**: (a) baseline reproduction — two instance-less clients
  sharing a bearer both checkpoint (compat, legacy task) and the audit lacks
  instance identity (retained as the falsifier's before-picture); (b) with
  instance-bearing enrollment, instance B checkpointing instance A's claimed
  task is refused `instance_not_bound` while A succeeds; (c) events identify
  the admitted instance and never contain the instance secret (scanned);
  (d) a stop/start cycle on the same store preserves bindings and the fence;
  (e) a malformed instance header is refused by name at the transport layer;
  (f) the full fleet suite stays green with the new regressions.
- **FALSIFIER**: simultaneous same-claim writers accepted in enforced/bound
  mode; a forged or absent binding treated as proof; PID-derived
  authorization; instance secrets in any snapshot/event/status/log surface;
  lost claims/bindings across restart; silently permissive compatibility
  claimed fixed; or any existing gate weakened.

Existing live sessions (lead + workers, legacy format) continue working in
compat mode; their migration is a later controlled transition with per-client
acknowledgements. No live-service mutation from this branch; the deployment
follows review+merge through the documented transition.
