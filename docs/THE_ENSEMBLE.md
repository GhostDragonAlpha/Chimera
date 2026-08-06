# THE ENSEMBLE — RULE 0 for many-world batches

*2026-08-06. Operator's directive: train whole categories of things at once. The
bottleneck is not the GPU and not the process count — it is per-tick Python latency
paid once per world. The fix: one process, one CUDA context, W worlds integrated
together. Physics is unchanged; only the launch geometry changes.*

## STATEMENT (someone could disagree)

An ensemble of W independent worlds — same force laws, no cross-world interaction —
can be integrated in ONE batched kernel launch per tick, and the trajectories will be
identical to running each world alone, because the force kernels are already written
as independent per-point loops: the only change is that the flat thread index spans
W*N points instead of N. If batching changes the physics, the kernel was never
correctly per-point independent — and that would be a bug worth finding NOW, before
the tree and the million arrive.

## PREDICTION (not yet measured)

1. **Equivalence**: a world run inside an ensemble produces the SAME positions as the
   same world run solo (same seed, same start), bitwise for the first 1000 ticks
   (the force computation per point is order-identical), and the same falsifier
   verdict at 10 t_ff. Only the radiated-power accumulator may differ (atomic
   ordering) — within 1e-3 relative.
2. **Throughput**: W=16 worlds of N=4096 integrated together cost less than 1/8th the
   wall-time of 16 sequential solo runs (Python per-tick latency amortized across the
   batch; measured, not assumed).

## FALSIFIER (named before the run)

- Any ensemble world whose trajectory diverges from its solo twin beyond float32
  rounding in the first 1000 ticks → the batching leaks across worlds or reorders
  forces; the ensemble is wrong, stop and re-derive.
- Throughput gain < 2x over sequential solo → the batch didn't amortize what it was
  derived to amortize; the profiling premise is wrong, measure again before scaling.

## THE DESIGN (derived from the bottleneck)

- State arrays become (W, N, 3) float32 on ONE device context. World w owns rows
  [w*N, (w+1)*N); the force kernels flatten to W*N threads, `w = i // N`, and loop
  j only over world w's points. No force crosses a world boundary — ever.
- One host sync per tick for the whole batch (the 7 ms Python latency is paid once,
  not W times). Per-world radiated power: a (W,) array, atomic-accumulated.
- Metrics and frames stay per-world, computed on host at sample times.
- N is uniform across a batch (padding is a lie; mixed sizes get separate batches).
- v2 note: the tree, when it comes, walks per-world — the batch dimension is
  orthogonal to the algorithm dimension.

## THE GATE

```bash
python -m pytest LightEngine/tests -q                 # incl. ensemble equivalence tests
python LightEngine/demo_ensemble.py --specs <file>    # a category of worlds, one batch
```
