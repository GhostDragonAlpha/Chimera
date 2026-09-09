# Five-slot control-plane preregistration

Written before implementation/testing. This is development orchestration,
not the engine's physical runtime. Python is not added to a simulation frame.

## Scope

A standard-library transactional control core and local HTTP adapter; five
fixed task slots; task branch/PR contracts; multiple claims per agent session;
qualified-lead selection after corroborated failure; generation fencing;
read-only disk/worktree inspection; a universal onboarding prompt.

The first version does not launch third-party model sessions, provision Alan's
Windows worktrees, execute GitHub merges, or grant/restrict OS filesystem access.
Those integration boundaries must remain explicit and fail closed. The lead
can prepare integration requests; only an external trusted publisher can execute
GitHub operations. Failover cannot revoke a token held directly by another
process; production activation requires credentials and publication exclusively
through a fencing-aware broker. No claim of that deployment is made here.

## Preregistered structural predictions and falsifiers

1. Capacity: at most five simultaneous occupied/reserved slots; slot 1 is the
   integration slot. A sixth conflicting claim refuses without state mutation.
2. Atomicity: simultaneous clients cannot acquire the same slot/task/scope.
3. Multi-task: one session can own separate tasks up to its approved capacity;
   every update needs task ID and current claim generation. Cross-task updates
   and stale generations refuse without changing the task.
4. Failover: silence/suspicion alone never changes the leader. A trusted
   failure event or explicit yield selects one qualified available successor
   deterministically and increments leadership epoch. An old lead cannot issue
   accepted control-plane integration requests afterward.
5. Recovery: failed-worker tasks remain held for inspection; they are not
   erased or assigned to another writer. Recovery requires a trusted preserved-
   work attestation and a new generation. Failure without a qualified successor
   leaves leadership vacant rather than inventing an owner.
6. Evidence: reported completion enters review, not acceptance. Integration
   requires the current task branch, head, expected base and recorded review;
   dependencies unblock only after trusted integration acknowledgement.
7. Resources: GPU/DYAD reservations are exclusive and explicit; control-plane
   failure never implicitly frees resources that may still be in use.
8. Restart: durable task, claim, resource and leader records survive a new
   controller instance; no time-based reassignment occurs.
9. Branches: one task -> unique astra/tasks/<id> branch; PR base is always
   astra/gait-capture, never master. No reuse of old task branches for new work.
10. Inventory: read-only directory scans skip symlinks, report partial errors,
    and distinguish logical bytes from disk free capacity; no cleanup runs.

For each item, the opposite behavior is a named falsifier. Tests exercise real
SQLite transactions and real HTTP requests locally; offline controller tests
are not Windows deployment, live model failover or GitHub merge certification.
Policy choices (five slots, max claims, qualification ranks) are declared
operator/coordinator settings, not physical constants or intelligence scores.

## Amendment E1 — one engine per slot (before the layout test)

STATEMENT: each of the five source slots owns a distinct engine build, runtime
CWD and evidence root. Task claims return those same locations.
PREDICTION: all five sets of paths are disjoint and inside their own slot,
none enters the protected build path, and candidate ports are distinct.
FALSIFIER: any overlap, cross-slot path, protected path, inconsistent claim
metadata or assertion that an unreserved candidate port is available.
LIMIT: this tests the planned configuration, not real processes, file writes,
port ownership, GPU isolation or Windows engine behavior.

## Amendment H1-H4 — human criticism intake (2026-09-09, before code)

STATEMENT: criticism is retained with attributed origin, categories, evidence
and task links; interpretation never silently replaces the original.
PREDICTION: human input requires the trusted human adapter (supervisor in this
reference); ordinary agents cannot impersonate it. Dispositions append in
order, require current leadership epoch, and never integrate a task or prove
a physical claim. Original record remains byte-for-byte unchanged.
FALSIFIER: forged human source admitted; invalid category/task accepted; old
record overwritten; stale leader dispositions accepted; task acceptance
changes merely because feedback is filed/dispositioned.
LIMIT: no UI intake, language classifier, screenshot viewer or stop executor
is implemented. The supervisor supplies attribution and routing; it must
execute human commands through the appropriate existing authority path.
