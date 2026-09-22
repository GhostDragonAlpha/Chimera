# PREREG — tick-0 hang diagnostic (continuation lane, 2026-09-22)

Rule 0 preregistration, written BEFORE any diagnostic run. Branch
`agent/typeb-gpu-fullport2-20260922` @ `0763d27` (the first lane's pushed tip).
Baseline: receipt `tools/science_funnel/validation/typeb_gpu_fullport_20260921/receipt.md`
(UNMEASURED state: tick-0 never returned at E=2, 20+ min; GPU busy 87-91% on a
shared box; all whiles audited bounded; hang reproduces with contact=0/power=0).
The frozen Phase-A/B/C falsifiers of PREREG_FULLPORT.md remain binding and
unmeasured; nothing here re-tunes them.

## STATEMENT (disagreeable)

The tick-0 hang has ONE dominant cause among the three below, and the tests
ordered here discriminate them on this machine in under 30 minutes of wall
time without waiting out the 20+ min hang except once.

## HYPOTHESES (named, with their discriminating tests and falsifiers)

- H1 COMPILE-COST: the first `tick_kernel[E,1]` call blocks the HOST in
  LLVM/NVVM/ptxas codegen of the 5606-line fully-inlined monolith; the "GPU
  busy" was the shared box; the kernel never ran. Discriminator T1: during
  the in-flight first launch, python.exe must sit at ~100% of one core with
  NO kernel resident in `nvidia-smi`; a second identical launch in the same
  process then returns in <1 s. FALSIFIER F-H1: host idle (<5% CPU) while
  `nvidia-smi` shows this process holding a context with SM activity, or a
  second launch not returning in <1 s — H1 dead.
- H2 LOCAL-MEMORY WORKING SET: the kernel executes but the inlined
  ~25-100 KB/thread local-memory set at block=1-thread-per-block makes each
  tick pathologically slow (latency-bound serial spill traffic, 2 threads on
  128 SMs). Discriminator T2: PTX `.local` byte census + `ptxas -v` spill
  stats for the compiled kernel (predicted 40 KB..128 KB/thread), and the
  same tick relaunched at block>=32 (the semantic no-op relaunch — the
  kernel has zero cross-env state) must change the wall time by >10x.
  FALSIFIER F-H2: local bytes/thread < 32 KB AND block>=32 relaunch shows
  <10x speedup while tick still fails to return in 120 s — H2 dead.
- H3 UNBOUNDED DEVICE LOOP: a loop the mechanical audit missed spins forever
  (NaN-guarded convergence, float-counted stepper). Discriminator T3: a
  heartbeat (mapped host array the kernel writes at entry / per substep /
  at exit) read live from the host — frozen at a checkpoint forever = the
  spin sits between that checkpoint and the next; monotone advance to DONE
  = no hang (H3 dead along with the hang itself).
- H0 (null, carried): the hang is machine- or box-specific (shared GPU,
  WDDM/TDR). Discriminated for free by T1's nvidia-smi attribution.

## ORDER (cheapest decisive first)

T1 (seconds..minutes, no 20-min wait needed for the verdict): host-CPU +
nvidia-smi sampling during first launch, then the double-launch timer.
T2 (needs H1's compile to finish): PTX/ptxas local census + block>=32
relaunch (E=1 tiny grid first, then the real E ladder).
T3 (needs a heartbeat-patched kernel copy `walker_numba_diag.py`; only if
T1 proves execution): bracket the freeze point.

## FROZEN VERDICT RULE

The cause is the first hypothesis whose discriminator FIRED; the others are
reported with their numbers as not-fired. If T1 proves compile (H1), T2/T3
run anyway on the compiled kernel — compile and locals can BOTH be true and
the fix (split + smaller units) serves both. If the block>=32 relaunch or
the split makes tick-0 return, the phase-split becomes the deliverable and
the preregistered bars (survival >=100 ticks in >=80% of 64 seeds; >=968
eps at batch 1024) take their FIRST measurement — a miss is reported red,
not tuned.

Trailer Agent: GLM 5.3.
