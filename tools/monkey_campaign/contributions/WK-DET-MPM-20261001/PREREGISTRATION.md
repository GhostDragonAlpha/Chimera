# PREREG DRAFT (not yet committed) — MPM-path whole-run determinism, lane det-mpm

- lane: `det-mpm` (worker wk-det-mpm)
- status: DRAFT for Lieutenant commit; gated execution starts ONLY after the
  Lieutenant commits this draft and hands back the commit pin (sha).
- correction implemented: "XPBD determinism does not qualify MPM. Exercise the
  MPM path under contention and in separate processes before claiming it meets
  the campaign's determinism requirement. Derive acceptance from whole-run
  evidence on that path."
- authority: Captain correction tasking, prereg-first; NO_WORKTREES.md
  (no worktrees; CPU via task_package.py seal|run; GPU only via the existing
  queue at E:/ChimeraWork/gpu-queue/ per PROTOCOL.md). Graph identity at time
  of drafting: creature_graph.json hash
  cd9098622f95647acddfb30b7f3bc8d3ddc6cd7be20def6fc5ad0eafc28df18a.

## 1. Distinct evidence subject (boundary statement)

There are four separate evidence subjects: (1) XPBD whole-run determinism —
lane `determinism-proof/`, pin d4e6b5d1 — NOT extended or imported by this
lane; (2) atomic microbenchmarks; (3) runtime-combine; (4) MPM-path determinism
— THIS lane only. This lane speaks ONLY for the MPM path
(newton `SolverImplicitMPM`) on the scene, environment and hardware declared
below. It makes no engine-wide claim, no XPBD claim, and no claim about other
scenes, particle counts, GPU models or drivers. Nothing here re-opens,
re-interprets or relies on any other lane's receipts.

## 2. Availability verification (done, from the pinned executables; NOT gated evidence)

Environment (recorded from my executables, 2026-09-29):

- Pinned env: `E:/ChimeraWork/envs/newton/Scripts/python.exe`
  (venv, Python 3.13.5). `newton.__version__ == "1.6.0"`,
  `warp.__version__ == "1.17.0"`.
- Determinism ladder verified in-env: `warp.DeterministicMode` (defined
  `warp/config.py` line 102) = {NOT_GUARANTEED=0, RUN_TO_RUN=1, GPU_TO_GPU=2};
  `warp.config.deterministic` defaults to NOT_GUARANTEED; per warp docs the
  value must be set before module creation/import to apply broadly (existing
  modules accept a per-module "deterministic" option).
- Atomic inventory on the MPM path (from the pinned env's installed files, not
  from any graph projection). Float `wp.atomic_add` sites — library-level
  ordering risk:
  - `newton/_src/solvers/implicit_mpm/solver_implicit_mpm.py` lines 4011,
    4015, 4019 (`_harvest_mpm_proxy_particle_forces_kernel`) and 4096
    (`_harvest_mpm_proxy_wrenches_kernel`) — the four sites named by the
    correction; these fire on the proxy-body mesh-contact coupling path.
  - ADDITIONALLY (found during this verification, same package):
    `implicit_mpm_solver_kernels.py` lines 358, 359, 360
    (`advect_particles` warp.fem integrand — the per-frame
    particle<->grid advection scatter: pos, vel, vel_grad) and lines 422,
    423, 424 (`update_particle_strains`: particle_Jp, particle_stress,
    elastic_strain). These fire EVERY frame for every particle and are the
    dominant atomic surface on this path.
  - `rasterized_collisions.py` line 333 (`collider_volumes_kernel`) — fires
    only with rasterized colliders (not exercised by this scene).
  - Order-insensitive by construction (min/max commute exactly in IEEE-754):
    `implicit_mpm_solver_kernels.py` lines 875-876 (`compute_bounds`,
    atomic_min/atomic_max). Not treated as a divergence source.
  - `solve_rheology.py` line ~992 documents an "atomic velocity scatter" in
    the batched Gauss-Seidel rheology solver; no direct `wp.atomic_*` call
    site found by grep in that module — noted as an open code-reading item,
    covered regardless by whole-run arms.
- Warp's own deterministic tests (`warp/tests/deterministic/`) cover plain
  `@wp.kernel` scatter-add under RUN_TO_RUN; they do NOT cover warp.fem
  integrand scatter-adds — the exact pattern `advect_particles` uses. Whether
  RUN_TO_RUN fixes the MPM path is therefore an open empirical question; the
  mode ladder below measures it.
- CPU feasibility probe (GPU-free, run with CUDA_VISIBLE_DEVICES=""):
  `probe_cpu_support.py` constructed SolverImplicitMPM on `device="cpu"` and
  stepped 2 frames; exit 0, `CPU_PROBE_RESULT=OK`. The CPU control arm is
  SUPPORTED and will run.

## 3. Scene (whole-run specimen, fixed)

Name `mpm-multi-spec`. Structure copied from the pinned
`newton/examples/mpm/example_mpm_multi_material.py` (headless; no viewer):

- Builder: `SolverImplicitMPM.register_custom_attributes(builder)` first; four
  particle blocks via `add_particle_grid` (particles_per_cell=3):
  kinematic boundary block (density 0.0 -> infinite-mass BC) bounds
  (-0.5,-0.5,0.0)-(0.5,0.5,0.25); sand (2500.0) (-0.5,0.25,0.5)-(0.5,0.75,0.75);
  snow (300.0) (-0.5,-0.75,0.5)-(0.5,-0.25,0.75); mud (1000.0)
  (-0.25,-0.5,1.0)-(0.25,0.5,1.5). `builder.add_ground_plane()`.
  Expected total ~178.6k particles; the exact count is recorded per run.
- Materials exactly as the example defaults: snow yield_pressure 2.0e4,
  tensile_yield_ratio 0.2, friction 0.1, hardening 10.0, dilatancy 1.0; mud
  yield_pressure 1.0e10, yield_stress 3.0e2, tensile_yield_ratio 1.0,
  friction 0.0, viscosity 100.0; sand defaults.
- Solver config: voxel_size 0.05, tolerance 1.0e-6, max_iterations 250,
  enable_timers=False. Stepper: per frame `clear_forces`, `solver.step`,
  `solver.project_outside`, state swap; frame_dt=1/60, substeps=1.
- Fixed run length N=120 frames (2.0 simulated seconds).
- Initial conditions are process-reproducible by construction: the builder's
  jitter uses `np.random.default_rng(42 + len(particle_q))` (verified in
  `_src/sim/builder.py` add_particle_grid). Independent IC check: sha256 of
  builder positions AND of `model.state()` arrays at frame 0 recorded per run
  and compared across all arms. IC mismatch = harness bug; blocks all
  interpretation.
- This scene is distinct from any XPBD scene (different lane, different solver,
  different evidence subject).

## 4. Harness (code bound to this prereg)

- `E:/ChimeraWork/monkey-coordination/det-mpm/run_mpm_arm.py` — one process
  per invocation, one arm per invocation. Sets
  `wp.config.deterministic = wp.DeterministicMode[<arm mode>]` immediately
  after `import warp` and BEFORE `import newton` (applies at module-load
  time); asserts the readback at set, at solver construction, and at run end,
  and records all three in the receipt. CPU arms additionally set
  `CUDA_VISIBLE_DEVICES=""` before importing warp, making GPU contact
  impossible.
- Hash protocol (per run):
  - IC hash at frame 0 (all `wp.array` attributes of `model.state()`,
    name-sorted, per-array sha256 + combined hash).
  - Per frame: after `wp.synchronize()`, per-array sha256 + combined state
    hash; every frame appended to `frame_hashes.csv`; a rolling
    whole-run hash = sha256 over the stream of
    `"{frame:06d}:{frame_hash}\n"` records binds the entire trajectory, not
    only checkpoints.
  - Checkpoints every 20 frames + final frame: state hash + rolling hash +
    saved `state_f####.npz` (particle_q, particle_qd) for refinement.
  - "No divergence" means bit-exact byte equality of the whole-run rolling
    hash and every checkpoint hash within an arm pair.
- Contention workload (declared precisely): in-arm, second CUDA stream
  (`wp.Stream`), N launches (arm parameter, default 800) queued BEFORE frame 1
  so the entire run is contended. Kernel: dim 32768 threads, block_dim 256,
  each thread performs 8192 `wp.atomic_add(float32)` ops into a shared
  4096-element float32 window => 268,435,456 atomic adds per launch,
  ~2.1e11 at N=800, saturating the atomic units. The kernel writes only its
  own array; it cannot alter MPM inputs — it competes for GPU resources.
  Drain: after the scene, `wp.synchronize()`; if the contention stream already
  drained (drain wait ~0), the receipt records `contention_underflow=true` and
  the arm is reported WEAK (never upgraded silently).
- Per-frame timing boundary (exact): `perf_counter` around
  clear_forces + step + project_outside + `wp.synchronize()`, per frame.
  Hashing and npz writes happen AFTER the timing stop, outside the measured
  window. Reported: frame 1 separately (includes residual lazy loads), then
  mean/p50/p95/max over frames 2..N, plus total run time. Scope: THIS scene,
  THIS hardware (receipt nvidia-smi), THIS env (newton 1.6.0/warp 1.17.0,
  Python 3.13.5). NO engine generalization, no per-particle or per-voxel
  extrapolation, no other-scene claim — the correction forbids it. Contended
  cost is reported separately and labeled as contended.

## 5. Arms and job manifest (execution AFTER pin; each job = one separate process)

GPU arms go through the existing queue at `E:/ChimeraWork/gpu-queue/` per
PROTOCOL.md (requester det-mpm, priority 5, timeout_seconds 600, outputs
declared). CPU arms go through the CPU runner
(`python -B E:/PythonChimera/tools/monkey_campaign/task_package.py seal|run`)
as required by NO_WORKTREES.md. Queue receipts (done/<id>.result.json with
output sha256s) are the execution records; lane copies in
`E:/ChimeraWork/monkey-coordination/det-mpm/runs/<arm>/`.

Job list (order: warm-cache, clean pairs, contention pairs, CPU pilot, CPU pairs):

| id | arm | mode | device | contention | frames | runner |
|---|---|---|---|---|---|---|
| det-mpm-warm0 | warmup (non-evidence) | not_guaranteed | cuda:0 | 0 | 2 | queue |
| det-mpm-ng-clean-a | ng_clean_a | not_guaranteed | cuda:0 | 0 | 120 | queue |
| det-mpm-ng-clean-b | ng_clean_b | not_guaranteed | cuda:0 | 0 | 120 | queue |
| det-mpm-r2r-clean-a | r2r_clean_a | run_to_run | cuda:0 | 0 | 120 | queue |
| det-mpm-r2r-clean-b | r2r_clean_b | run_to_run | cuda:0 | 0 | 120 | queue |
| det-mpm-ng-cont-a | ng_cont_a | not_guaranteed | cuda:0 | 800 | 120 | queue |
| det-mpm-ng-cont-b | ng_cont_b | not_guaranteed | cuda:0 | 800 | 120 | queue |
| det-mpm-r2r-cont-a | r2r_cont_a | run_to_run | cuda:0 | 800 | 120 | queue |
| det-mpm-r2r-cont-b | r2r_cont_b | run_to_run | cuda:0 | 800 | 120 | queue |
| det-mpm-cpu-pilot | cpu_pilot | not_guaranteed | cpu | 0 | 10 | task_package |
| det-mpm-cpu-ng-a/b | cpu pair | not_guaranteed | cpu | 0 | R (rule below) | task_package |
| det-mpm-cpu-r2r-a/b | cpu pair | run_to_run | cpu | 0 | R (rule below) | task_package |

- Warm-cache job J=det-mpm-warm0 populates GPU kernel caches; its artifacts
  are kept and labeled NON-EVIDENCE (it is not a pair member).
- Separate processes: every arm invocation is an independent queue/job
  invocation (separate OS processes; GPU arms are separate queue jobs).
- GPU_TO_GPU mode: NOT RUNNABLE on this host — single RTX 4090 (single
  physical GPU; expected cc 8.9, driver 616.92; the exact live identity is
  recorded from job receipts in Phase B). Declared excluded with this reason;
  not a silent omission.
- Contention rounds rule (fixed now): N=800. If a contention pair shows
  `contention_underflow=true`, ONE re-run pair at N=3200 is permitted
  (pre-declared adjustment; job ids `*-cont2-a/b`); both the weak and the
  strengthened runs are kept and reported.
- CPU frame-count rule (fixed now): the cpu_pilot (10 frames, timing only)
  measures per-frame CPU cost T. CPU pair length R =
  min(120, max(10, floor(0.8 * 480 s / T))) frames, identical for both CPU
  pairs, recorded in receipts. No other adjustment is permitted.
- CPU-mode control: SUPPORTED (verified probe, section 2); runs as declared
  above. If any later state change broke it, the failure would be recorded
  and the control declared unavailable in the report — not skipped silently.
- Two-process contention (MPM and load in separate OS processes) is NOT used
  because PROTOCOL.md forbids a job spawning further GPU processes; the
  two-stream same-process design achieves GPU-level contention within the
  protocol. Flagged for the Lieutenant: if the Captain rules two-process
  contention permissible, an amendment would be required before any such run.

## 6. Prereg predictions (declared before any gated run)

- P0 (IC): all arms in all modes have identical IC hashes. Falsified => harness
  bug; stop, fix, re-prereg. Not a solver finding.
- P1 (not_guaranteed, clean, separate processes): divergence at some frame is
  the EXPECTED outcome (unconstrained float atomic ordering on the every-frame
  P2G/strain scatter). If the pair is nonetheless bit-exact, that is recorded
  as an observation of THIS scene/hardware/env and explicitly does NOT
  establish any guarantee (order may be stable-by-accident under this
  scheduler/kernel mix; the NG label stays).
- P2 (run_to_run, clean): genuinely uncertain, stated as such. Warp documents
  atomic determinism support for plain @wp.kernel scatter-adds; coverage of
  warp.fem integrand scatter-adds (the pattern this path actually uses) is not
  demonstrated anywhere in the installed package. Both outcomes are
  informative. Divergence here is a recorded finding that BLOCKS any MPM
  determinism claim — this lane's acceptance is the whole-run evidence,
  whichever way it points; a clean negative (divergence) is a valid,
  valuable result.
- P3 (contention, both modes): divergence is expected to be at least as
  likely as in the corresponding clean arm. Clean-pass/contention-diverge
  blocks the claim too. Clean-diverge does not exempt contention arms: they
  still run (the correction requires them).
- P4 (CPU control): warp CPU launches are host-side; prediction is bit-exact
  pairs in BOTH modes. If CPU pairs diverge, that indicates scene- or
  library-level state dependence beyond GPU scheduling (e.g., uninitialized
  or reduction-order effects on host path) — recorded as a serious finding,
  claim blocked in ALL modes.
- P5 (cost): per-frame cost is reported with the exact boundary of section 4
  for THIS specimen only. No prediction of absolute cost is registered (it is
  a measurement, not a falsifiable physics claim); the registered obligation
  is that the report states scene-specific numbers with hardware identity and
  never generalizes.

## 7. Decision matrix (what each outcome licenses)

- "MPM path meets the campaign's whole-run determinism requirement" is
  claimable ONLY if ALL of: R2R clean pair bit-exact; R2R contention pair
  bit-exact (no underflow, or underflow handled by the pre-declared N=3200
  rule with a bit-exact strengthened pair); CPU control bit-exact and sane;
  IC equality everywhere. Any divergence in any arm => claim BLOCKED, finding
  recorded with first divergent frame and refinement data. NG arms are
  descriptive context and are never sufficient for a claim.
- Sergeant/Flash review of picture-type outputs does not apply here (no
  images); independent review still required for the receipts before any
  graph evidence record is created. This lane does not self-approve.

## 8. Failure preservation and refinement checks

- Any job failure (timeout, exception, underflow) preserves partial artifacts
  (frame_hashes.csv, receipt.json with `status=FAILED` and error) — the
  runner writes them in a finally block. Failed jobs are kept under
  `runs/<arm>-failed-N/`; reruns get fresh ids; nothing is overwritten.
- On any pair divergence, declared refinement sequence (receipt/hash
  analysis only, no GPU needed): (1) re-run that pair ONCE with fresh
  processes to distinguish stable divergence from transient (both kept);
  (2) first divergent frame index and the first state array that differs;
  (3) per-material localization using the recorded group ranges (kinematic /
  sand / snow / mud) on the checkpoint npz files; (4) difference statistics
  (differing element count, max abs diff, max rel diff, affected arrays q vs
  qd); (5) cross-mode comparison (NG run A vs R2R run A) recorded as context
  only.
- Evidence anchoring: lane receipts and the analysis summary go through the
  existing anchor.py into the sealed evidence store BEFORE any registry
  reference or retirement claim; queue receipts (done/*.result.json with
  output sha256s) are preserved verbatim.
- Every load-bearing artifact in this lane is recorded with sha256 in
  `E:/ChimeraWork/monkey-coordination/det-mpm/EVIDENCE.md` (updated as
  artifacts appear; the Phase A version is hashed at first chain stop).

## 9. Amendment policy

Any change to scene, arm set, mode application, hash protocol, timing
boundary, contention workload, or decision matrix after the Lieutenant's
commit requires a committed amendment BEFORE affected runs; results from a
superseded prereg stay valid only for the prereg revision they were run
under. Harness bug fixes (P0 class) require re-prereg with the bug and fix
documented.

## 10. Explicit not-yet-run statement (Phase A state)

As of this draft: NO gated arm has run. No GPU job has been submitted by this
lane. No determinism, contention, cost or CPU-control result exists. The only
executions so far are read-only availability verification and the GPU-free
CPU feasibility probe (section 2), which are not determinism evidence.
Phase B (queue execution, receipts, EVIDENCE.md updates, per-standing-format
report) starts only after the Lieutenant commits this prereg and hands the
pin.
