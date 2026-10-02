# AMENDMENT-5 — lane det-mpm (prereg 32e485e0; amendments a7dc1f1a, bb81ce60, 09dd5a8b, 966a44d8)

Status: DRAFT for Lieutenant commit; the r2r contention cell remains gated.
Submitted by wk-det-mpm, 2026-10-02. Executes the Lieutenant's pre-ruling
("first try the iters=1024 variant, N x8, same formula") after the cal3
failure below. Also records the Captain-directed transfer-boundary follow-up
arms as the lane's declared next assignment (not executed in this chain).

## Third library-boundary finding (preserved failure)

det-mpm-cont-cal3 (NON-EVIDENCE, v5) FAILED on the GPU R2R solo launch, exit 1
after 2.8 s. The NG-phase measurements never ran to output. Failure (from the
warp sources involved: warp/_src/deterministic.py launch_deterministic ->
run_sort_reduce -> warp.empty):

    ValueError: Array shapes must not exceed the maximum representable value
    of a signed 32-bit integer, got 10871935487 in dimension 0.

Interpretation: with deterministic_max_records = 8192 and 32768 threads, one
launch produces 268,435,456 scatter records; the R2R sort-reduce workspace
alone is 10,871,935,487 bytes (~10.9 GB, ~40.5 B/record), and warp arrays
cannot represent shapes above 2^31 — so a 268M-record launch can NEVER
allocate on this stack, regardless of GPU memory. This is a hard, named
boundary of warp 1.17.0's deterministic mode at scale, alongside the two
already recorded (consumed-return int32-only; per-thread static record
bounds).

## Fix: the pre-ruled iters=1024 variant

run_mpm_arm_v6.py
sha256 f173e815ad87bede99f14e044a8427cd6df1cbfcb960c86831a884a2d7101b01
(diff vs v5: (a) new optional `--contention-iters` argument, DEFAULT 8192 =
the registered per-launch workload, so every prior arm's identity is
unaffected; (b) `deterministic_max_records` is now COUPLED to the effective
iters instead of fixed at 8192 — the workspace is sized from the bound, so an
8192-bound with 1024 visits would still allocate the oversized workspace).
At iters=1024: 32,768 x 1024 = 33,554,432 records/launch (~1.36 GB workspace,
shape within int32; record buffer ~0.5 GB). Validated CPU-side with CUDA
hidden under RUN_TO_RUN: exact 33,554,432 adds landed.

cont_cal.py updated for v6 + optional argv iters:
sha256 50599edfbdc475c49ac8210006c95312340f009ee08fbdd6b439b6b7746e2cd8
(cal4 measures BOTH modes at the requested iters; per-launch R2R cost at
iters=1024 includes recording + ordering of 33.5M records.)

## Changes

C14. r2r contention cell workload: per-launch iters = 1024 (8x fewer per
     launch than the registered 8192), N re-derived by the UNCHANGED C12
     formula using the cal4 R2R median at iters=1024 — coverage-based sizing
     (3x scene duration) is preserved; total atomic traffic per frame is
     within the same order (N scales inversely with per-launch cost). The ng
     cell of record remains ng-cont2 (v4, per-launch 8192, bit-exact).
C15. r2r cell jobs: det-mpm-r2r-cont4-a/b (v6, 24 frames, --contention-iters
     1024, N from cal4, guards as in C12). The failed r2r-cont2-a/b (buffer
     overflow) and the cal3 failure stay preserved under their ids.
C16. Validity rule C5 unchanged. No other prereg term changes.

## Transfer-boundary follow-up arms (Captain direction; declared NEXT ASSIGNMENT, not executed in this chain)

Before any transfer of this lane's result to new consumers, two
representative workload variants must be tested on this path:

T1. mpm-multi-spec-changing-contact: the same specimen with an evolving
    contact topology during the run (e.g., a kinematic collider sweeping the
    sand/snow/mud blocks so contact sets change every frame), same mode ladder
    (NG/R2R), clean + contention pairs, same hash protocol. Target: does
    bit-exactness survive changing contact-set sizes/orderings?
T2. mpm-multi-spec-scatter-heavy: the same specimen with a declared
    scatter-heavy stressor on the same atomic surface (P2G/strain scatter)
    rather than the synthetic window kernel — e.g., increased
    particles-per-cell density variant with proportional voxel sizing, or a
    second MPM model stepped in the same process; sized so per-thread record
    counts stay within the R2R record budget measured in cal4.

Both run only after a committed amendment of their own (scene definitions,
arms, predictions) if the Lieutenant dispatches them; otherwise this section
is the recorded next assignment for the lane.

## Execution order after this commit

det-mpm-cont-cal4 (argv iters=1024) -> derive N_r2r -> det-mpm-r2r-cont4-a/b
-> pair comparison + C5 validity -> full final report with provenance table.

## Requested commit

Add to tools/monkey_campaign/contributions/WK-DET-MPM-20261001/ as ONE commit:
1. AMENDMENT-5.md (this file as staged)
2. run_mpm_arm_v6.py (as staged)
3. cont_cal.py (as staged)
