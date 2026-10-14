# Independent-state batch experiment, 2026-10-02 UTC

The first sealed CPU run (`53cabdae5ea04e49a422a6478c1e83c5`) passed exact
baseline parity and all executor checks. Diagnostic total probe elapsed time was
approximately 1.96 seconds baseline, 2.13 candidate serial, 4.30 two workers and
5.45-5.53 four workers for seven 300-tick configurations. These are single-run
diagnostics, not an isolated evaluation benchmark or a qualified speedup result.

Before implementing the additional API: test coarse batching of independent
configuration evaluations on the same immutable Model. Each task evaluates one
whole configuration serially, sharing the persistent executor with other tasks.
No RK stage, coupled iteration, or consecutive physical timestep is treated as
independent. No automatic switch to parallel execution is introduced.

Prediction: 256 requests cycling existing pinned reference configurations will
give bitwise-identical mass/gravity/bias/potential/frames across serial, 1/2/4-worker
batch evaluation. A malformed request refuses the batch after workers finish,
without returning partial results; a subsequent valid batch succeeds. Empty input
returns an empty result. Independent requests own separate outputs.

Record warmup plus five timing samples and median per execution mode only as a
diagnostic of this CPU/model/workload. No speed threshold is selected from results.
Contradiction: any mismatched output bit, leaked partial successful batch,
non-repeatable failure, failure to recover, or nested parallel worker use. Original
physical/reference tolerances and byte-equality requirements remain unchanged.
