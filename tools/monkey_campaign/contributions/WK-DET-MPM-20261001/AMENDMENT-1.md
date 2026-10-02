# AMENDMENT-1 — lane det-mpm (prereg 32e485e07a5c1df6a1d244c6893c5b6549358d8d, blob 8d445279)

Status: DRAFT for Lieutenant commit; contention arms are gated on this commit.
Submitted by wk-det-mpm, 2026-10-02.

## P0 harness bug (found before any contention run)

`run_mpm_arm.py` line 115 used `if acc == float("inf"):` inside the warp
kernel `contention_kernel`. Warp 1.17.0 codegen cannot parse `float(<str>)`:
`WarpCodegenError: Couldn't find function overload for 'float' that matched
inputs with types: [builtins.str]`. Every contention arm would have failed at
first kernel launch. Found by a CPU-only compile/launch test with CUDA hidden
before any contention job was submitted; no GPU job touched the bug.

## Fix (one line; nothing else changes)

- line 115: `if acc == float("inf"):` -> `if acc != acc:`
  (NaN guard; same dead-code-insurance role; float comparison is supported).
- `acc = float(0.0)` on line 112 is RETAINED: warp codegen requires the
  `float(<number>)` idiom to declare a mutable variable inside a dynamic loop
  (a plain `acc = 0.0` is rejected as "mutating a constant inside a dynamic
  loop" — tested and confirmed during diagnosis).

Fixed file: `run_mpm_arm_v2.py`
sha256: 9ed56c19a3cacb8c9e75377105795542be922808951197971597e7452c314494
diff vs pinned v1 (136be90a423e72247e4bc0507c5ad4ea44be1b208ee5d1fac16c09aacef4f674):
exactly the one line above.

Fix verification (CPU-only, CUDA hidden): kernel compiles, launches with
dim 32768/block 256, and lands exactly 32768x8192 = 268435456 atomic adds
(array sum = 268435456.0 exact).

## Effect scope (prereg section 9 applied)

- AFFECTED, gated on this commit: the four GPU contention arms
  (det-mpm-ng-cont-a/b, det-mpm-r2r-cont-a/b). They will execute ONLY
  run_mpm_arm_v2.py with the sha above, recorded per job in receipts notes.
- NOT AFFECTED, proceed under the original pin without re-run: warm0,
  ng-clean-a/b, r2r-clean-a/b (GPU) and cpu_pilot, cpu_ng_a/b, cpu_r2r_a/b
  (CPU). None of these reference or compile `contention_kernel` (warp compiles
  kernels lazily at first launch per device), and all completed/completes under
  harness sha 136be90a. Per prereg section 9 their results stay valid under
  the prereg revision they ran with. No other prereg term changes: scene, arm
  set, mode application, hash protocol, timing boundary, contention workload
  parameters, decision matrix are unchanged.

## Requested commit

Add to the WK-DET-MPM-20261001 contribution directory, as one commit on top of
the current branch tip:
1. AMENDMENT-1.md (this file, bytes as staged by wk-det-mpm)
2. run_mpm_arm_v2.py (bytes as staged by wk-det-mpm)
