# RULE 0 PREREG — fleet_supervisor_20260922 (SUPERVISOR lane, Astra round 6 first implementation)

- Committed BEFORE any code in tools/fleet_supervisor/ (this file + receipt.json are the first commit).
- Governing spec: E:/ChimeraWork/lane-archive/astra-round6-answer-20260922.md (Astra's answer, sections 1-3).
- Base: origin master 88da85bc. Lane: lane/fleet-supervisor-20260922. Trailer: `Agent: supervisor`.
- Machine constraints honored: installed Chrome cannot navigate (MACHINE_FINDINGS 2026-09-20) so the
  smoke capture uses Playwright's BUNDLED chromium; the notepad GUI sentinel is replaced by a
  windowless dummy (a GUI sentinel would put a window on the operator's desktop — the operator plays
  games on this machine; zero popups is a hard law). The deviation is recorded in the receipt.

## STATEMENT (Astra's contract, verbatim-cited)

From astra-round6-answer-20260922.md:

> "Every execution attempt has a unique ID, owner lane, worktree, command, ports, browser profile,
> and declared resource requirements."
> "The launcher creates the root process suspended, assigns it to its job, then resumes it.
> Assignment failure means launch failure."
> "Children remain contained; prohibit breakaway."
> "Completion triggers graceful shutdown, then job termination after a short deadline."
> "Keep job handles non-inheritable. An accidentally inherited handle can defeat cleanup on
> supervisor death."
> "Never authorize termination by executable name, age, port number, or location alone. Kill only
> processes whose fleet ownership is established through the launch mechanism. PID records need
> creation time because PIDs are reused. Ambiguous processes are reported and left alone."
> "Reconcile live jobs frequently; retain the two-hour janitor as an audit and disk-retention
> mechanism."

Ownership rejection condition (Astra's own lane, verbatim):

> "Ownership | 100 execution cycles, including cancellation and launcher crashes; unrelated sentinel
> processes present | Any sentinel affected, or disposable descendants survive over 30 seconds after
> cleanup"

Broker phase 1 rules implemented this lane (from the same spec):
- mode file (gaming|fleet|training, default fleet); gaming refuses GPU work and new builds.
- GPU reservation file: "If its expected end passes, it remains occupied until completion is
  verified. Likewise, a lost heartbeat means ownership uncertain, not permission to start a
  competing job."
- Fleet memory: 48 GiB aggregate committed ceiling; per execution session 8 GiB default, build 16 GiB;
  "refuse admission if free physical memory falls below an initial 32 GiB reserve".
- gpu_phase kind requires an exclusive GPU reservation held by the launching session.

## THE BUILD (phase 1 only)

tools/fleet_supervisor/: jobobject.py (ctypes Windows primitives, no new dependencies),
registry.py (JSONL, pid+creation-time identity), broker.py (mode/reservation/admission),
launcher.py (suspended->assign->resume; JSONL ownership record appended after resume),
lifecycle.py (complete = graceful-then-TerminateJobObject after deadline, default 10 s; idle expiry
per kind: browsers/servers 120 s, engine editors 300 s, configurable; reconcile every 15 s:
job-handle liveness, completed-job reaping, AMBIGUOUS/UNOWNED lane-looking processes REPORTED and
never touched), supervisor.py (CLI), set_fleet_mode.ps1 (one-line operator hotkey target).

## PREDICTIONS (pre-named, none measured yet)

- P-CYCLES: 100/100 execution cycles clean — every launched root and every disposable descendant
  (depth >= 3 trees, spawned grandchildren included) is dead at cleanup, across normal-exit cycles,
  cancellation-mid-run cycles, and launcher-kill cycles (the supervisor process itself TerminateProcess'd
  mid-cycle; KILL_ON_JOB_CLOSE must finish the job).
- P-SENTINELS: both sentinels (a windowless dummy cmd process and a dummy python server whose command
  line deliberately matches the legacy orphan-sweep pattern "slice_server", neither launched through
  the supervisor) are untouched — alive at suite end by exact (pid, creation-time) identity.
- P-MEMLIMIT: a child that tries to allocate beyond its job's declared limit fails ITS OWN allocation
  (MemoryError / nonzero exit), while machine free physical RAM does not dip (measured before/after).
- P-PIDREUSE: the registry fold cannot false-match a reused PID — matching requires (pid AND creation
  time); a synthetic record with a live pid and wrong creation time is never treated as ours, and
  complete() on such a record never signals the innocent live process.
- P-GATES: the broker refuses: gpu_phase with no reservation; gpu_phase or build in gaming mode;
  admission pushing the fleet past 48 GiB declared; admission when free physical RAM < 32 GiB
  (the RAM gate is exercised with injected readings; real readings are used at real admission).
- P-SMOKE: a real slice server + real engine child + one bundled-chromium headless capture, launched
  through the supervisor end-to-end and completed, leaves zero survivors (verified by exact identity,
  then by name-class census as a second opinion) and a coherent registry (one status trail per session,
  fold-to-last consistent).
- P-AMBIGUOUS: processes that look lane-ish but are not registry-owned are reported by reconcile and
  left running (the suite plants one deliberately and checks reconcile REPORTS it and its exit-code
  proves it was not signaled).

## FALSIFIERS (any one firing = the lane fails; all can fire honestly)

- F1 (Astra ownership): any sentinel affected — dead, restarted, signaled, or otherwise touched at any
  point during the suite. Measured by identity checks during and after.
- F2 (Astra ownership): any disposable descendant of a launched job alive more than 30 s after its
  cycle's cleanup completed.
- F3 (Astra law): a PID-reuse false match — the registry/reconcile treats a process as fleet-owned
  because of a reused pid without a creation-time match, or complete() signals an innocent process.
- F4 (resource contract): a job's declared memory limit fails to constrain — the child allocates past
  its declared limit, or the machine's free RAM dips while it tries.
- F5 (launch contract): assignment failure leaves a live process — a simulated AssignProcessToJobObject
  failure on a suspended root must end with no surviving process.
- F6 (launcher-kill): the supervisor process killed mid-cycle leaves any job member alive > 30 s.
- F7 (smoke conditions): after the real-shape smoke completes, any survivor exists or the registry
  fold is incoherent (contradictory statuses, a session that never ran, a record with no identity).
- F8 (broker): any admission gate passes work it must refuse (the P-GATES matrix, injected inputs).

## NAMED-UNMEASURED (honestly out of scope this lane)

- Nested-job CPU-rate multiplication (~25% for 50%-in-50%): semantics DOCUMENTED this lane
  (per Microsoft CPU-rate control docs, as Astra cites), MEASUREMENT deferred to phase 2 with the
  queue; containment of nested jobs IS tested (child job members are in both parent and child jobs).
- Ollama/GPU judge paths: the broker MANAGES reservations only; it consumes no GPU this lane.
- The gaming-mode frame-time effect: not this lane (Astra's Gaming lane).

## METHOD NOTES

- All cycle counts, per-cycle events, sentinel checks and verdicts land in cycle_results.json +
  receipt.json in this directory. RED results are kept verbatim (the stranger-lane pattern).
- Survivors are checked by exact (pid, creation-time) identity recorded while the tree was live;
  a second-opinion census by process class runs after the suite.
- The suite never kills anything by name/age/port/location. Only supervisor-launched jobs are
  terminated, by job handle, by session id.
