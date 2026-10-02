# AMENDMENT-3 — lane det-mpm (prereg 32e485e0; amendments a7dc1f1a, bb81ce60)

Status: DRAFT for Lieutenant commit; the four contention arms are gated on
this commit. Submitted by wk-det-mpm, 2026-10-02.

## Library-boundary finding (new evidence, preserved)

Both r2r-cont arms (det-mpm-r2r-cont-a/b, N=73805, 24 frames) FAILED at the
first contention launch, exit 1, job walls 6.0/6.1 s, receipts + partial CSVs
preserved under runs/r2r-cont-a/ and runs/r2r-cont-b/:

    WarpCodegenError: Error while parsing function "contention_kernel" ...
    Deterministic mode currently supports consumed-return counter atomics only
    for int32 counter arrays.

Reproduced CPU-side with CUDA hidden: the v3 kernel under
warp.config.deterministic = RUN_TO_RUN raises the identical WarpCodegenError.
This is a direct empirical statement of warp 1.17.0's determinism-ladder
coverage boundary on this stack: under RUN_TO_RUN, a float32 wp.atomic_add
whose return value is CONSUMED is rejected at codegen; only int32 counter
atomics may consume their return. The MPM solver's own atomic_add sites all
DISCARD the return value (verified: implicit_mpm_solver_kernels.py 358-360,
422-424; solver_implicit_mpm.py 4011-4019, 4096; rasterized_collisions.py 333),
which is consistent with the R2R clean pair completing and being bit-exact.
The v3 contention kernel CONSUMED the return (acc accumulation for a
dead-code guard) — my design error; it tested a pattern the MPM path does not
use. The ng-cont arms ran the same kernel fine under NOT_GUARANTEED (no such
restriction) and are preserved as context.

## Fix

run_mpm_arm_v4.py
sha256 d42e269cd8e9b0cdc0638c57940b8fd07ad3a1bbd165767eb69db64ee90c961d
(diff vs v3: contention_kernel no longer consumes the atomic_add return; the
atomic traffic is IDENTICAL to the registered workload — dim 32768,
block_dim 256, runtime iters called with 8192, 4096-float window, same
per-thread index sequence, same 268,435,456 adds per launch; the removed
consumed-return adds were scalar bookkeeping on the return values only).
Verified CPU-side under RUN_TO_RUN with CUDA hidden: kernel compiles, one
launch lands exactly 268,435,456 adds (array sum 268435456.0 exact).

cont_cal.py updated to import v4 (no duplicated kernel source):
sha256 ac7d0e697e26498870dc3562d4259e069c0c8b8ef9492b2d2363c7b5410f0bf1

## Changes

C6. Recalibration: det-mpm-cont-cal2 (NON-EVIDENCE, same standing) reruns the
    calibration with the v4 kernel — removing the consumed-return chain can
    change solo launch duration, so the C3 sizing inputs must be re-measured.
    Output runs/cont-cal2/calibration.json.
C7. Re-derivation by the UNCHANGED C3 formula (same clamp, same clean-receipt
    means 0.105388/0.076297 and 4.170550/4.320911, same guards) using the
    cont-cal2 median. Derived N recorded in job notes and EVIDENCE.md before
    submission.
C8. Re-run ALL FOUR contention arms under v4 (ng pair 120 frames, r2r pair
    24 frames) so both cells share one contention identity. The completed
    v3 ng-cont runs are preserved as historical context only (they are not
    pair members of the final evidence set; their observations — 7.8-11x
    contended slowdown, whole-run bit-identical to clean — are reported as
    such).
C9. C5 validity rule unchanged (contended iff contention_drain_wait_s
    >= 1.0 s, else recorded WEAK; no re-runs). Nothing else in the prereg
    changes.

## Execution order after this commit

det-mpm-cont-cal2 -> derive N_ng, N_r2r -> submit ng-cont2-a/b and
r2r-cont2-a/b under v4. (Fresh job ids; the failed r2r-cont-a/b and completed
v3 ng-cont-a/b stay preserved under their ids.)

## Requested commit

Add to tools/monkey_campaign/contributions/WK-DET-MPM-20261001/ as ONE commit:
1. AMENDMENT-3.md (this file as staged)
2. run_mpm_arm_v4.py (as staged)
3. cont_cal.py (updated, as staged)
