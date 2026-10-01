# MIGRATION NOTE -- the name-based orphan sweep degrades to REPORT-ONLY

(Lane: fleet-supervisor-20260922. Written at the request of the round-6
spec, before any lane has cut over. This note changes NOTHING today: the
live `E:\ChimeraWork\tools\orphan_process_sweep.ps1` keeps its current
behavior until the cutover rule below is triggered, and the worktree janitor
cron stays as audit and disk-retention exactly as Astra directed.)

## The rule

Once lanes launch their execution sessions through the fleet supervisor,
`orphan_process_sweep.ps1` MUST degrade to report-only. Its kill authority
narrows to exactly one class:

> **The sweep may kill only REGISTRY-IDENTIFIED orphans**: a process whose
> (pid AND creation-time) identity matches a record in
> `E:\ChimeraWork\control\fleet_registry.jsonl` whose folded status is
> terminal (completed / terminated / orphaned_completed) and which is still
> RUNNING past its cleanup -- i.e. a leak the supervisor itself would have
> reaped, identified through the launch mechanism's own records, never by
> name, age, port, or location.

Everything else -- every process that merely LOOKS like a lane process
(same exe name, same cmdline substring, same port, same worktree) -- is
REPORTED, with its pid, image, and command line, and LEFT ALONE. Ambiguity
is resolved by humans or by the supervisor's job handles, never by the
sweep's heuristics.

## Why the current sweep cannot survive the cutover

The sweep kills `chimera_engine.exe` and python servers matching
`slice_server|lesson_shell|thin_client|...` by NAME + worktree-quietness.
Under a supervisor regime that logic becomes actively dangerous:

1. A session the supervisor owns and is still using can sit in a QUIET
   worktree (a lane thinking/editing for twenty minutes) -- exactly the
   session Astra's model says must NOT be restarted. The sweep kills it.
2. Name patterns cannot distinguish a fleet browser profile from the
   operator's browser, or one lane's capture from another's evidence run.
3. Age and quietness are properties of WORKTREES; ownership is a property
   of PROCESSES. Only the launch mechanism knows the second thing.

The supervisor's reconcile loop already does the sweep's real job better:
it verifies every live job by handle every 15 s, reaps completed jobs, and
REPORTS unowned lane-looking processes without touching them (measured:
the ambiguous-report falsifier in this lane's receipt).

## The census keeps its job

`fleet_process_census.ps1` remains useful as a read-only class census and
as the supervisor's second opinion after suites (its aggressive
"sweep headless browsers to 2 newest" behavior must NOT be used once fleet
browsers are supervisor-owned: those are someone's evidence runs, not
leaks, until the registry says otherwise).

## Cutover condition (when this note ACTIVATES)

When the number of lane execution sessions launched through the supervisor
exceeds the number launched by hand for one full working day, flip
`orphan_process_sweep.ps1` to report-only with the registry-identified-orphan
kill class above. Until then the sweep's current conservative behavior
stays, and the supervisor's reconcile reports accumulate as the evidence
base for the flip.
