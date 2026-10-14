# RULE 0 PREREG — gpu_broker2_20260922 (BROKER-2 lane, Astra round 6 section 3, phase 2)

- Committed BEFORE any code in tools/fleet_supervisor/ (this file + receipt.json are the first
  commit of the lane).
- Governing spec: `E:/ChimeraWork/lane-archive/astra-round6-answer-20260922.md` **section 3**
  ("GPU arbitration: reservations plus a bounded queue").
- Base: 248704d8 (the landed phase-1 supervisor tip, lane/fleet-supervisor-20260922).
  Branch: lane/gpu-broker2-20260922. Trailer: `Agent: broker2`.
- Phase 1 (already landed, my foundation): owned-process launcher, broker admission
  (mode file, GPU reservation states, memory gates), registry with pid+creation-time identity,
  reconcile. F-CPURATE already measured there: CPU-rate hard caps are unenforceable on this build
  (Win11 26200) and the launcher REFUSES cpu_pct instead of pretending.

## STATEMENT (Astra's section-3 contract, verbatim-cited)

> "Use a single GPU broker with exclusive ownership of fleet GPU execution."
> "1. Gaming mode: admit no fleet GPU work; unload fleet-owned judge models."
> "2. Reserved training: exclusive allocation for the run."
> "3. Interactive fleet work: schedule captures and judge requests by deadline, with aging to
>    prevent starvation."
> "4. Throughput measurements: exclusive quiet windows."
> "5. Batch a few judge requests to amortize model loading, but cap batch duration so captures
>    cannot starve."
> "A training reservation cannot simply expire into 'GPU free.' If its expected end passes, it
> remains occupied until completion is verified. Likewise, a lost heartbeat means ownership
> uncertain, not permission to start a competing job."
> "Because training must not be preempted, place it under a dedicated durable worker/keeper whose
> lifetime is independent of the dispatch service. A broker restart must reconnect to that worker,
> not kill it or launch a duplicate."
> "Do not send requests to Ollama while waiting for the GPU. Maintain the queue in your broker.
> Distinguish: Queue deadline. Model-load timeout after admission. Inference timeout after
> readiness. This makes a deferred request visibly deferred instead of repeatedly 'failing
> inference.'"
> "Start the dedicated fleet Ollama instance with one loaded model and one parallel request.
> Preload after obtaining the reservation; retain it during a bounded judging batch; unload before
> releasing the reservation."
> OLLAMA_LOAD_TIMEOUT: "current Ollama source exposes OLLAMA_LOAD_TIMEOUT, defaulting to five
> minutes, for stalled model loading. Verify the installed version and distinguish this from
> client/proxy deadlines."

Astra's own preregistered rejection condition for this lane (verbatim):

> "GPU broker | Mixed capture/judge workload plus simulated reservation loss | Overlapping
> exclusive reservations; a lost heartbeat grants a second owner; queue wait mislabeled as model
> failure"

## OPERATOR CONTEXT THIS LANE HONORS (measured at prereg time, 2026-09-22)

`nvidia-smi` at prereg time shows `WardogsClient-Win64-Shipping.exe` (a game) on the GPU and the
operator's own Ollama/LM Studio instances resident. The hard law stands: **no fleet GPU work while
the operator games, zero popups, never touch his processes.** Therefore:

- Every scheduling decision, timeout state, aging rule, batch cap, reservation fault, and keeper
  reconnect in the falsifier suite is exercised against an **INJECTED judge backend** (an HTTP
  ollama-API-shaped fake with scripted latencies) and **timer-based capture stubs** — the things
  Astra's rejection conditions test are the BROKER'S DECISIONS, and they are fully falsifiable
  without a loaded model.
- The REAL `OllamaBackend` ships in judge.py but loads no model and touches no GPU this lane; it
  is exercised only in config/refusal paths (mode gate, no-reservation gate). Real model-load
  latency on the 4090 is NAMED-UNMEASURED (below) for exactly this reason.
- The suite binds only ephemeral loopback ports (never 8127, never 11434, never the operator's
  instances), starts no windows, touches no operator process.

## THE BUILD (phase 2, additive to tools/fleet_supervisor/)

- `queue.py` — the bounded broker queue: requests carry kind (capture|judge|train), owner lane,
  absolute deadline; THREE DISTINCT terminal-timeout states per Astra (queue_deadline_exceeded for
  never-admitted waits, model_load_timeout for admitted-but-stalled loads, inference_timeout for
  ready-but-slow inference); a waiting request is VISIBLY DEFERRED (queryable status journal,
  JSONL) and its label can never read as an inference/model failure; deadline ordering with an
  aging term (score = deadline - aging_gain * waited) so neither captures nor judges can starve;
  judge batches with a CAPPED batch duration and capped batch size.
- `judge.py` — the fleet judge service around a dedicated ollama instance (OLLAMA_HOST on a fleet
  port, OLLAMA_MAX_LOADED_MODELS=1, OLLAMA_NUM_PARALLEL=1, OLLAMA_KEEP_ALIVE = batch cap):
  reservation FIRST, preload AFTER the reservation, retain through one bounded batch, unload
  BEFORE release; three-phase timeouts distinct (load phase honors OLLAMA_LOAD_TIMEOUT=5m default,
  verified below, with the client load deadline set beyond it and labeled separately);
  gaming-mode check each pass: unload + release, never admit.
- `keeper.py` — the durable training keeper: an INDEPENDENT process (deliberately NOT inside a
  kill-on-close job — that is the exception Astra's contract names for the training keeper);
  durable keeper record (pid + creation-time identity + heartbeat), heartbeats the phase-1
  RESERVATION FILE; reconnect = a restarted broker scans records, verifies (pid, creation_time),
  adopts the live keeper — never kills, never duplicates (a second keeper for a live run is
  refused); expected-end passing keeps the reservation occupied (expired_pending) until the
  keeper verifies completion; lost heartbeat = OWNERSHIP UNCERTAIN: new admissions refused,
  registry alert appended, never auto-granted; only an explicit audited admin release (or the
  keeper's own verified-completion release) frees the GPU.
- `tests_gpu_broker.py` — the falsifier suite (injected faults; measurements below).

## PREDICTIONS (pre-named, none measured yet)

- P-NOVERLAP: under the mixed capture/judge workload with all injected faults, the grant ledger's
  exclusive intervals are pairwise disjoint — zero overlapping exclusive reservations, ever.
- P-DEFERLABEL: 100% of requests that never reach admission carry terminal state
  queue_deadline_exceeded (or refused/cancelled) with queue-worded labels; no request's status
  ever reads as a model/inference failure unless it was actually admitted to the model phase.
- P-KEEPERRECONNECT: after a REAL broker kill + restart, the live keeper's (pid, creation_time)
  identity is unchanged, the new broker adopts exactly once, and no second keeper process exists.
- P-UNCERTAIN: a killed keeper mid-run and a corrupted heartbeat each leave the reservation in
  state uncertain; a competing admission attempt is REFUSED while uncertain; a registry alert is
  appended; the GPU is never auto-granted; recovery requires the audited admin release.
- P-EXPIRED: an expected_end in the past with a live, fresh-heartbeat keeper leaves the
  reservation expired_pending (STILL OCCUPIED) until the keeper verifies completion and releases.
- P-AGING: under a continuous capture flood with tighter deadlines, the judge is NOT starved — its
  measured wait is bounded (aging gain 1.0 predicts ≈ half the flood's per-request slack as the
  worst case, ≈59 s in the suite's configuration) and the unaged ordering would starve it
  indefinitely (measured both ways).
- P-BATCH: batching amortizes model loads — loads per judge request falls from 1.0 unbatched to
  ≈1/batch_size batched (scripted load latencies); batch wall time never exceeds the cap even
  with judges arriving mid-batch; a capture arriving mid-batch waits no more than the remaining
  batch cap.
- P-TIMEOUTS: the three states are distinguishable end-to-end: a scripted stall during load fires
  model_load_timeout (not inference timeout, not queue deadline); a scripted slow inference fires
  inference_timeout; a queue that cannot admit before the deadline fires queue_deadline_exceeded —
  each with the correct label, and never cross-labeled.
- P-CPUAFFINITY: job-object AFFINITY (not cpu-rate) is a working, enforceable CPU alternative on
  this build: a multi-threaded spinner pinned to k of N logical processors measures ≈k/N total
  machine CPU (±10%); carried forward as the honest substitute where F-CPURATE left a hole.

## FALSIFIERS (Astra's rejection conditions + this lane's measurements; any firing = lane fails)

- F1 (Astra): any two exclusive grants in the ledger overlap in time.
- F2 (Astra): any admission of a second owner while the reservation is uncertain (killed keeper or
  corrupted heartbeat), or any auto-free of an uncertain/expired_pending reservation.
- F3 (Astra): any queue wait mislabeled as a model failure — a non-admitted request whose terminal
  state/label references model loading or inference, or a status query that cannot report a
  queued request as deferred.
- F4 (Astra): a broker restart that kills the live keeper (identity change, or exit while broker
  restarting), spawns a duplicate keeper for a live run, or adopts zero/multiple times.
- M1 (measurement): queue latency percentiles (p50/p95/max by kind) under the mixed load —
  recorded either way; a falsifier fires only if the AGING GUARANTEE breaks (a request starves
  past its deadline while the GPU was repeatedly granted to lower-scored work).
- M2 (measurement): model-load latency distribution + batch amortization (loads/request batched
  vs unbatched). Scripted-backend numbers are LABELED AS SCRIPTED; no GPU number is claimed.
- All falsifiers can fire honestly: F1/F2 by construction bugs in the grant/admission logic,
  F3 by label wording bugs, F4 by lifecycle bugs (a broker that exits its children, or a reconnect
  scan that launches when it should adopt).

## NAMED-UNMEASURED (honestly out of scope this lane, with cause)

- Real GPU model-load latency, real ollama judge latency/quality, and CPU-judge offload
  (Astra's Judge-offload lane): NOT MEASURED — the operator is gaming (Wardogs on GPU at prereg
  and suite time); the no-fleet-GPU law outranks this lane's curiosity. OllamaBackend ships
  unexercised on GPU; its config knobs (OLLAMA_LOAD_TIMEOUT/NUM_PARALLEL/MAX_LOADED_MODELS/
  KEEP_ALIVE) are verified at the installed-binary + tagged-source level only.
- Gaming-mode frame-time effect (Astra's Gaming lane).
- The fleet-wide `serve` integration (queue hosted inside the live supervisor loop) is built and
  unit-tested against injected backends; hosting it on the REAL machine-wide control dir under
  gaming is left to the first gaming-free window.

## OLLAMA_LOAD_TIMEOUT — verification instrument (config-level, no model load)

- Installed binary: `C:\Users\allen\AppData\Local\Programs\Ollama\ollama.exe`, reported version
  `ollama version is 0.34.2`; binary grep finds the literal `OLLAMA_LOAD_TIMEOUT` (and
  OLLAMA_NUM_PARALLEL, OLLAMA_MAX_LOADED_MODELS, OLLAMA_KEEP_ALIVE, OLLAMA_MAX_QUEUED).
- Tagged source v0.34.2 `envconfig/config.go`: `LoadTimeout()` default `5 * time.Minute`, env
  `OLLAMA_LOAD_TIMEOUT`, described as "How long to allow model loads to STALL before giving up" —
  a server-side scheduler stall timeout, distinct from any client HTTP deadline and any proxy
  timeout; `<= 0` = infinite. judge.py therefore separates: queue deadline (broker-side),
  load-stall timeout (server, 5m default) and the judge client's own load-phase deadline (set
  > 5m, labeled load_client_deadline), then the per-request inference timeout.

## METHOD NOTES

- Results land in this directory: `suite_results.json` (raw per-check records) + `receipt.json`
  (final verdicts). RED results are kept verbatim (the stranger-lane pattern).
- The suite kills only processes it launched itself, via the process handle obtained at launch
  (launch-established ownership), and only to SIMULATE faults the contract names (keeper death,
  broker death). The identity check guards every such kill.
- Nothing in this lane touches: other lanes' worktrees, finish-agent's GPU reservations (the
  reservation file is read before any GPU decision and no GPU work is scheduled this lane at
  all), port 8127, the janitor, master, or the operator's processes.
