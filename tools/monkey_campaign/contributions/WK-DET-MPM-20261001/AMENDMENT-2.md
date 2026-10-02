# AMENDMENT-2 — lane det-mpm (prereg 32e485e0; amendment-1 a7dc1f1a)

Status: DRAFT for Lieutenant commit; the four contention arms are gated on
this commit. Submitted by wk-det-mpm, 2026-10-02. All clean-cell and CPU
results already collected remain valid under their existing identities
(pin 32e485e0, harness 136be90a; amendment-1 v2 9ed56c19 for nothing yet —
v2 was never executed and is superseded by v3 before any use).

## Why (measured, from completed clean receipts)

1. Contention coverage: the registered N=800 (and the 3200 fallback) cannot
   cover the measured scene durations. The contention kernel executes
   268,435,456 atomic adds per launch against a 4096-float window; per-address
   serialization bounds one launch to ~0.1-1 ms even on a fast GPU, so
   N=800 covers well under 1 s while the ng scene runs ~10.9 s (measured:
   frames_2_to_N_mean_s 0.1054 s ng-clean-a / 0.0763 s ng-clean-b; 120
   frames). The arms would have reported contention_underflow and been WEAK.
2. R2R infeasibility at 120 frames: measured R2R mode cost is 4.1706 s/frame
   (r2r-clean-a) and 4.3209 s/frame (r2r-clean-b) => 120-frame scene ~509 s,
   job wall 558.5 s / 529.1 s — already at the 600 s queue cap WITHOUT any
   contention stream. A contended 120-frame R2R arm cannot fit the cap.
3. Host queue depth: a multi-million-launch unbounded pre-queue (v2 design)
   risks exhausting host launch queues; v3 feeds the budget per frame instead.

## Changes (nothing else changes)

C1. Harness v3: run_mpm_arm_v3.py
    sha256 db201be87e5a6aa51ce71da386d35111486eb308ce7918120e950c03f48363b5
    (diff vs v2: (a) contention_kernel takes runtime `iters: int`; the call
    site passes CONTENTION_ITERS=8192, so the per-launch atomic workload is
    byte-identical to the registered one — dim 32768, block 256, 8192
    atomic_adds/thread into the same 4096-float window; (b) the launch budget
    N is distributed evenly across frames (share = N div frames, remainder to
    the first frames) and queued just before each frame's timed window, so the
    contention stream executes concurrently with every scene frame; per-frame
    pending depth is bounded by the share; N < frames raises instead of
    silently under-covering). Fix verified CPU-only with CUDA hidden:
    kernel compiles with runtime iters, sum 268435456.0 exact.
    The four contention arms execute ONLY v3 under this sha.

C2. Calibration job det-mpm-cont-cal (NON-EVIDENCE mechanics check, same
    standing as warm0): cont_cal.py
    sha256 45ed8cbee0282dc1376502e7ba21736bfca463de231711ef54b2c49692bb657d
    imports the kernel from v3 (no duplicated source), runs on cuda:0:
    2 warmups, then 5 timed solo launches (launch -> synchronize_stream ->
    stop), writes runs/cont-cal/calibration.json with all five timings,
    the median T_launch_solo_ms, workload parameters and nvidia-smi identity.

C3. Sizing rule (mechanical; inputs are the calibration median and the
    already-collected clean receipts; derived N recorded in each job's notes
    and in EVIDENCE.md before submission):
    scene_ng_s   = 120 * mean(0.1054, 0.0763)      = 10.902 s   (measured)
    scene_r2r24_s = 24 * mean(4.1706, 4.3209)       = 101.898 s  (measured)
    N_ng   = clamp(ceil(3.0 * scene_ng_s   / T_launch_s), 800, 2000000)
    N_r2r  = clamp(ceil(3.0 * scene_r2r24_s / T_launch_s), 800, 2000000)
    Budget guard (holds by construction here, stated for completeness):
    job_est = 60 (construction) + max(scene_est, N*T_launch_s) + 30
    (hash/npz overhead) must be <= 570 s; else N is reduced to
    floor((570 - 90 - scene_est) / T_launch_s), floor 800.

C4. r2r contention arms run at FRAMES=24 instead of 120 (same scene, same
    ICs, shorter registered whole-run length). Justification: measured R2R
    cost (item 2). ng contention arms stay at 120 frames.

C5. Contention-validity interpretation (replaces the "one re-run pair at
    N=3200" rule, which is superseded and will not be used): an arm counts as
    CONTENDED-THROUGH-FINAL-FRAME iff its receipt contention_drain_wait_s
    >= 1.0 s (the contention stream still had queued work when the last scene
    frame completed). Otherwise the arm is recorded WEAK (underflow) — kept,
    reported, never silently upgraded, and insufficient for the campaign
    determinism claim by itself. No re-runs are authorized by this amendment.

## Execution order after this commit

det-mpm-cont-cal -> derive N_ng, N_r2r from calibration.json + the frozen
formula -> submit det-mpm-ng-cont-a/b (120 frames) and det-mpm-r2r-cont-a/b
(24 frames) with the derived N in notes. Pair comparisons and the decision
matrix of prereg section 7 are unchanged.

## Requested commit

Add to tools/monkey_campaign/contributions/WK-DET-MPM-20261001/ as ONE commit:
1. AMENDMENT-2.md (this file as staged)
2. run_mpm_arm_v3.py (as staged)
3. cont_cal.py (as staged)
