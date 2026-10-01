# fleet_supervisor -- owned-process launcher + resource broker (phase 1)

Implementation of Astra's round-6 contract, sections 1-3
(`E:/ChimeraWork/lane-archive/astra-round6-answer-20260922.md`), first
implementation slice: the owned-process launcher and the broker's admission
half. Prereg + falsifier receipts:
`tools/science_funnel/validation/fleet_supervisor_20260922/`.

## THE CONTRACT (short form)

- Every execution attempt has a unique session id, owner lane, worktree,
  command, ports, kind, and declared resource requirements.
- The launcher creates the root process SUSPENDED, assigns it to its job,
  then resumes it. Assignment failure means launch failure (no survivor).
- The job: NAMED (`Local\ChimeraFleetJob.<session_id>`, so a restarted
  supervisor re-opens it by name instead of trusting pids), handle
  NON-INHERITABLE, `KILL_ON_JOB_CLOSE` always, declared job+process
  committed-memory limit, active-process limit, priority class for builds.
  Breakaway is prohibited by not setting either breakaway flag.
- Children stay in the job automatically; a `conhost.exe` member joins for
  console roots on this build (counted, contained, killed with the tree).
- Completion = graceful attempt (CTRL_BREAK to the root's process group,
  only when the root's pid+creation-time identity still matches) -> bounded
  wait (10 s default) -> `TerminateJobObject`. Nothing is ever signaled or
  killed by pid/name/port/age/path. There is NO pid-kill code path at all.
- Registry: append-only JSONL (default `E:\ChimeraWork\control\fleet_registry.jsonl`),
  pid + CREATION TIME (raw FILETIME) identity, fold-to-last-event per session.
- Reconcile every 15 s: live jobs verified by handle (or re-opened by name),
  completed jobs reaped, jobs of dead supervisors folded `orphaned_completed`,
  idle sessions expired per kind (browsers/servers 120 s, engine editors 300 s,
  configurable via `fleet_idle_timeouts.json`), and lane-looking processes that
  belong to no fleet job REPORTED and never touched.

## USE

```bash
# the operator's mode switch (bind to a hotkey; prints one line, no UI)
powershell -NoProfile -ExecutionPolicy Bypass -File tools/fleet_supervisor/set_fleet_mode.ps1 gaming

# a lane launches (kill-on-owner-exit: the session dies with your process)
python -m tools.fleet_supervisor.supervisor launch --spec-file spec.json

# a lane that must outlive the launching command runs the supervisor loop
python -m tools.fleet_supervisor.supervisor serve          # reconcile + complete-all on stop
python -m tools.fleet_supervisor.supervisor hold --spec-file spec.json

python -m tools.fleet_supervisor.supervisor complete <session_id>
python -m tools.fleet_supervisor.supervisor status
python -m tools.fleet_supervisor.supervisor reconcile
python -m tools.fleet_supervisor.supervisor touch <session_id>   # idle clock reset
```

Spec:

```json
{"session_id": "mylane-build-001", "owner_lane": "mylane", "worktree": "E:\\path",
 "command": ["python", "build_engine.py"], "ports": [18080], "kind": "build",
 "resources": {"cpu_pct": null, "mem_gib": 16, "max_procs": 64},
 "stdout_file": "E:\\logs\\mylane-build-001.out.log",
 "stderr_file": "E:\\logs\\mylane-build-001.err.log"}
```

Kinds: `engine | server | browser | build | gpu_phase`. Defaults: 8 GiB
session memory, 16 GiB builds; `gpu_phase` must DECLARE measured memory and
requires an exclusive GPU reservation owned by the session. Admission refuses:
gpu/build in gaming mode, gpu_phase without a valid reservation, fleet
declared memory past 48 GiB, free physical RAM under 32 GiB, and port clashes
with active sessions.

## NESTED JOBS (documented; semantics per Microsoft's Job Objects and
## CPU-rate control documentation, as Astra cites)

- A process may belong to a hierarchy of jobs; limits combine, and the most
  restrictive limit wins for memory and active-process counts.
- CPU-rate quotas MULTIPLY down the hierarchy: a child at 50% under a fleet
  parent at 50% gets ~25% of machine CPU. Configure deliberately.
- This lane DOES test nested containment (a child job assigned under a
  parent: members verify membership in both) and does NOT measure the CPU
  multiplication (see F-CPURATE below -- phase 2, with the queue).

## F-CPURATE -- cpu caps refused on this build (measured 2026-09-22)

`resources.cpu_pct` is REFUSED at admission instead of being silently
ignored, because the CPU-rate control primitive could not be pinned on
Win11 build 26200: SET at class 7 "succeeds" and is a measured no-op (a
spinner ran 0.955 of a core under a claimed 10% hard cap); class 14 rejects
every rate value with ERROR_INVALID_PARAMETER (8- and 16-byte structs);
no other class caps a measured spinner (baseline 0.962, all candidates
> 0.9). The class-numbering trap that produced plausible-looking garbage on
readback is pinned in `jobobject.py`; effects, not return values, are the
evidence (`tests_primitives.py`, 15/15).

## GRACEFUL SHUTDOWN -- where applicable

CTRL_BREAK reaches process groups that share the supervisor's console.
Detached roots (CREATE_NO_WINDOW, own hidden console) do NOT receive it --
a documented Windows restriction, covered by the contract's "where
applicable": the deadline + TerminateJobObject remain the guaranteed path.
Lanes with an app-level graceful path should expose it (e.g. a /shutdown
route) and call complete() with a longer deadline while it drains.

## MEASURED TRAPS (all pinned by `tests_primitives.py`)

1. JobObjectInformationClass numbering differs from the classic header enum
   on this build (BasicAndIoAccounting=8, ExtendedLimit=9); the wrong class
   returns struct-shaped garbage that looks plausible. Every limit is
   verified by READBACK and by measured effect.
2. `conhost.exe` joins the job of console roots (one per console). It is a
   real member: counted in limits, killed with the tree, contained.
3. A terminated member whose object is still referenced by SOMEONE (parent,
   console, security software) keeps its (pid, creation time) resolvable --
   an identity check alone over-reports "survivors". Honest liveness =
   identity AND `GetExitCodeProcess` != STILL_ACTIVE (`process_running`).
4. `CreateFileW` signals failure with INVALID_HANDLE_VALUE (non-NULL), and
   OPEN_ALWAYS will not create absent files under the harness sandbox;
   CREATE_ALWAYS does. stdout+stderr sharing one log file must share ONE
   handle (CREATE_ALWAYS truncates between opens otherwise).
5. Undeclared ctypes argtypes truncate 64-bit handle values silently --
   every handle-taking API here has declared argtypes.
6. Held child process handles keep terminated children addressable; the
   launcher closes BOTH child handles immediately after resume. The
   supervisor's ownership instrument is the JOB, never a pid handle.

## PHASE 2 -- the GPU queue, the judge service, the training keeper

Astra section 3 ("GPU arbitration: reservations plus a bounded queue"), implemented
additively by the gpu_broker2_20260922 lane (`Agent: broker2`). Prereg + falsifier
receipts: `tools/science_funnel/validation/gpu_broker2_20260922/`.

- `queue.py` -- the BOUNDED broker queue. A request waiting for the GPU is
  VISIBLY DEFERRED (queryable, queue-worded labels) and is NEVER sent to the
  model while waiting. The three Astra timeout states are distinct terminals:
  `queue_deadline_exceeded` (never admitted) / `model_load_timeout` (admitted,
  load stalled) / `inference_timeout` (ready, inference stalled). Scheduling is
  deadline order with aging (`score = deadline - aging_gain * waited`): measured
  on a synthetic flood, a 120 s-deadline judge under a continuous tighter-deadline
  capture flood waits 59 s aged (the analytic bound) vs 118 s unaged. Judge
  batches amortize model loads under TWO caps (member count + hard wall-clock):
  measured 4.0x amortization, batch wall 0.15 s against a 0.6 s cap.
- `judge.py` -- the fleet judge service around a DEDICATED ollama instance
  (fleet port, never 11434/8127): one loaded model, one parallel request
  (`OLLAMA_MAX_LOADED_MODELS=1`, `OLLAMA_NUM_PARALLEL=1`). Ordering is asserted:
  reservation FIRST -> preload AFTER it -> members -> unload BEFORE release.
  OLLAMA_LOAD_TIMEOUT verified at config level on the installed 0.34.2 binary +
  the v0.34.2 tagged source: default 5 m, a SERVER-SIDE stall timeout for model
  loads, distinct from client HTTP deadlines and proxy timeouts. The real
  `OllamaBackend` ships UNEXERCISED on GPU (the operator games; the no-fleet-GPU
  law outranks lane curiosity) -- the suite drives an ollama-API-shaped
  `FakeBackend` with scripted latencies, labeled as scripted everywhere.
- `keeper.py` -- the DURABLE training keeper: an independent process
  (deliberately NOT in any kill-on-close job), durable record with
  pid+creation-time identity, heartbeats BOTH its record and the phase-1
  reservation file. `reconcile` = reconnect: a restarted broker ADOPTS a live
  keeper (never kills, never launches a duplicate; `ensure` refuses while one is
  live). The reservation's expected-end passing leaves it `expired_pending`
  (STILL OCCUPIED) until completion is verified. A lost heartbeat / dead
  identity = OWNERSHIP UNCERTAIN: the reconcile FLAGS the reservation (a flag
  newer than the heartbeat reads as `uncertain`), alerts the registry, and new
  admissions are refused -- never auto-free; recovery is the keeper's own
  resumed heartbeat (transient stalls) or an audited `admin-release`.
- `broker.py` (additive): a RELEASED reservation may transfer to a new owner
  (the queue's sequential exclusive grant, audited in the file); writes are now
  atomic and reads retry. `jobobject.py` (additive): `affinity_mask` with
  readback -- the measured enforceable substitute where CPU-rate caps are not
  (see F-CPURATE above and the disposition doc in the validation directory).

## VALIDATION

- `python -m tools.fleet_supervisor.tests_primitives`  (15/15 required)
- `python -m tools.fleet_supervisor.supervisor gates`  (broker matrix)
- `python -m tools.fleet_supervisor.tests_gpu_broker`  (phase 2: 8 checks --
  three timeout states + F3 labels, mixed-load overlaps F1 + latency
  percentiles, batch amortization, aging bound, gaming defer/abort, keeper
  reconnect F4 + expired-end, kill/corrupt uncertain F2, measured affinity)
- `python -m tools.fleet_supervisor.validate_ownership` (100 cycles +
  sentinels + pid-reuse + ambiguous + memlimit + assignment-failure;
  receipt in the lane validation directory)
- real-shape smoke: `smoke_real_shape.py` (slice server + engine child +
  bundled-chromium capture through the supervisor)
