# TIE2 REPORT — the frozen tie-v2 falsifier battery, executed

Agent: M-tie2 · 2026-09-24 · worktree E:/ChimeraWork/monkey-play-20260924
Frozen prereg: `agents/P02P03/receipts/prereg_tie_v2_9376c3d8.txt` (git 9376c3d8,
"PREREG_COMMITTED_BEFORE_ANY_V2_RUN") + full text `PREREG_RESIDUAL_TIE_V2.md` @
a62b286e. Run plan (frozen before execution): `run_plan.md`. This battery ran
what was preregistered; nothing authored new physics, no tolerance tuned, no
anchor choice made.

## THE FROZEN STATE THE BATTERY RAN AGAINST

- The tie patch at the freeze: `walker_numba_split.py` + its regenerated
  `walker_kernels.cuh` — `tol = max(1e-9*(1+|floors[k]|), tol_band)`,
  `tol_band = cst[CF_k_touch]/cst[CF_dt]`, at both decision sites of
  `project_rows` (the empty-mask satisfaction test AND the mask-recheck),
  both call sites (`rate` -> return 5, `impact` -> rc[0]=5). Git diff
  9376c3d8..a62b286e touches ONLY these lines (+ the d41 drill instruments).
- The frozen build state survives byte-verified on disk at
  `E:/ChimeraWork/finish-agent` (== a62b286e; checked
  walker_numba_split.py, walker_kernels.cuh, walker_env.cu, co8_v2walk.py).
  `walker_env_v2.dll` (nvcc, 14:10 2026-09-23) and `host_loop.exe` (cl via
  host_shim FROM THE SAME walker_kernels.cuh, 14:00) — the host replay leg
  IS the tie-patched kernels on CPU.
- Frozen constants (host_shim/cst.txt): dt = 0.0033333333333333335,
  kTouch = 1.0000000000000001e-05; the implemented bound kTouch/dt =
  0.0030000000000000001.

## PER-CASE VERDICTS (the prereg's table order)

### 1. EDGE-CLASS-SPLIT (the kTouch/dt_ boundary ±1 ulp) — PARTIAL (host measured; GPU leg QUEUED, Q2)
Harness: `run/tie_boundary_probe.cxx` (pure harness — includes the FROZEN
walker_kernels.cuh via the host_loop shim pattern, calls the FROZEN
project_rows with R=1, floor=0, unit row, identity inv; the pre-v2 decision
measured on the SAME frozen code via tol_band=0.0, the registered signature's
own parameter). Receipt: `receipts/case123_tie_boundary_host.out`.

Measured on the host leg (verbatim decisions):
- viol = 0.0030000000000000001 (tb exact): v2 = ACCEPT-norepair (the tie:
  empty-mask accept, p_out=0, multipliers=0); pre-v2 = ACCEPT-repair.
- viol = 0.0029999999999999996 (tb - 1 ulp): v2 = ACCEPT-norepair; pre-v2 =
  ACCEPT-repair.
- viol = 0.0030000000000000005 (tb + 1 ulp): v2 = ACCEPT-repair; pre-v2 =
  ACCEPT-repair — identical, the widening inactive above the bound.

The boundary class-split lands EXACTLY on the ulp, inclusive at tb, as
registered. Honest shape note: in the R=1 unit shape both legs end rc=1
(the single-row repair is always cone-valid), so the registered
"accept/reject decision" observable here is the empty-mask decision
(repair vs exactly-satisfied-no-repair) — the decision the tie rule owns.
Also recorded (case A7, verbatim): the fixture's g0 = 6.9388939039072284e-18
residual is absorbed by BOTH pre-v2 and v2 (identical decisions) — the g0
residual was never beyond the pre-v2 1e-9 tolerance; the tick-41 rescue
class is residuals in (1e-9, 3e-3] (the frozen drill's
got=-1.3446626414778118e-3 PROROW chk line; g2=2.0861058498689022e-07),
which pre-v2 treated as violations and v2 absorbs.

### 2. FALSE-FEASIBILITY (violation bound * dt_ <= kTouch) — PASS (host leg)
Same receipt. The registered identity on the frozen doubles:
(kTouch/dt)*dt = 1.0000000000000001e-05 <= kTouch = 1.0000000000000001e-05 —
YES, with EXACT equality: the tie-admissible residual over one tick moves
the pad at most kTouch = 1e-5 m, the pad's own resolution. Every
tie-accepted case: viol*dt <= kTouch YES (tb-exact case: 1e-05 == 1e-05;
tb-1ulp: 9.9999999999999991e-06). Every repair case repairs to EXACTLY the
floor (got_after = 0). The integration-level form rides the replay legs.

### 3. OUTSIDE-BAND-DRIFT — PASS (host leg)
Above-band cases (tb+1ulp, 1e-2, 1.0): the v2 leg and the tol_band=0.0 leg
are IDENTICAL on every observable (rc, p_out, multipliers, got_after — the
output lines are byte-identical). Backed by the frozen diff audit: the only
decision-code change at the freeze is the two tol expressions; the
multipliers, cone validity (lam >= -1e-10), mask order, and tier law are
untouched, exactly per the one-sidedness clause.

### 4. ANCHOR-DRIFT (the registry record) — RECORDED (no choice made)
Receipt: `receipts/case4_anchor_registry.txt` (sha256s). v1-preserved: the
co8_t41_fixture (state_t40_host/gpu, state_t39_cpp, scene_sha256 =
f6844eeae3dc87170a572ccdeedf326a6cac4f73d1448941808bd8b25a8db342, the drill
pairs, README). v1-band anchor verified: `co8_csub310.err` line 6626 reads
"BAND_ENTRIES 6" (the 6-entry walk). Pre-v2 tolerance record:
co8_ksub_prorow3.out's "PROROW chk ... tol=1.0000000000000001e-09" lines.
v2-recorded: the v2 build's own first runs (co8_hl_v2.out, co8_dll_v2_120.txt,
co8_dll_v2b_120.txt, co8_cp_v2_120.txt) + the v2 binaries
(walker_env_v2.dll, host_loop.exe). The A/B (scope-the-band vs version-bump)
decision remains Astra's, PENDING — both versions' behavior recorded where
the cases touch them: the pre-v2-vs-v2 host walk comparison (below).

### 5. REPLAY-DIVERGENCE (walk PAST tick 41, host and GPU) — HOST LEG PASS; GPU LEG preserved + QUEUED (Q1)
HOST LEG (measured now, CPU): `HL_FULL=1 ./host_loop.exe` (the tie-patched
CPU build) — receipt `receipts/case5_replay_host_v2.out`: the walk proceeds
PAST tick 41 and runs to t=100 with "tick 100: y=0.215657301 vx=0.664807
rc=0 adv=7 refused=0 ticks=100". The refusal signature rc=5 class 5
adv=2 ticks=40 DOES NOT FIRE on the host under the tie. Bit-identical to the
preserved co8_hl_v2.out (reproducibility confirmed).
HOST pre-v2 vs v2 (the v1-preserved/v2-recorded comparison):
`co8_hl_full6.out` (pre-v2) vs this run — bit-identical t=1..40; FIRST
divergence at exactly t=41; 60 FULL lines differ (t=41..100).
HOST-vs-GPU PARITY under v2: the preserved GPU v2b capture
(co8_dll_v2b_120.txt, walker_env_v2.dll 14:18) is BIT-IDENTICAL to the host
v2 walk on EVERY FULL state t=1..43 (0 differing ticks after stripping the
file's \r\r\n capture artifact on line-final tokens) — stronger than the
prereg claimed (it claimed no byte parity past 41; parity measured holds
through the capture end).
GPU LEG: the preserved v2b run shows the continue outcome (NO refusal; t=41
carries the resolved impact; capture reaches t=43). The live GPU re-run is
QUEUED-BEHIND-BROKER with the exact command
(`receipts/gpu_leg_queued_broker.txt`, Q1) — resource evidence recorded
(18:33: 20% util, 23092/24564 MiB; 18:40: 0% util, 23067/24564 MiB,
steam.exe pid 17472 live; operator-session signs; nothing launched, nothing
touched).

## HONEST ANOMALIES (preserved verbatim, not smoothed)

1. The FIRST v2 build still refused at 41: `co8_dll_v2_120.txt` (14:06)
   ends "REFUSED at tick 41 rc=5 refused=1 adv=2 ticks=40"; the DLL was
   rebuilt at 14:10 and v2b (14:18) walked past. No frozen receipt names the
   rebuild's cause. Recorded as-is; the queued live qualification run (Q1)
   supersedes both preserved captures.
2. The convention clause names "all three paths (C++ reference +
   instrument, host kernels, GPU kernels)"; at the freeze the C++ reference
   + instrument (gait_controller_ref.hpp / gait_controller_instr.hpp) do NOT
   carry the tie (verified: git diff shows no change there;
   `tol=1e-9*(1.+std::abs(floors[k]))` unchanged). The falsifier table's
   named legs (host/GPU) are both served by walker_kernels.cuh. GAP
   RECORDED for the owner; not fixed here (no physics authored).
3. Post-41 re-separation (the absorbed partial-application fact, "expected
   to re-separate the trajectories after tick 41"): NOT observed in the
   preserved window — host and GPU v2 are bit-identical through t=43. What
   happens beyond 43 is unmeasured without the GPU (queued with Q1).

## RESOURCE DISCIPLINE

CPU ran now: the boundary probe (compile + run), the host replay leg, all
sha/anchor work. GPU: ZERO work launched — the two GPU-touching legs are
QUEUED with exact commands (`receipts/gpu_leg_queued_broker.txt`). No
existing process touched or killed; the only build was CPU-side (cl) into my
own dir. The GPU probe harness was authored CPU-side and left unbuilt/unrun.

## INTEGRITY

Writes confined to `tools/monkey_campaign/agents/TIE2/**`:
brief.md, run_plan.md, report.md, run/ (probe harnesses + build scripts +
exe/obj), receipts/ (case123_tie_boundary_host.out, case4_anchor_registry.txt,
case5_replay_host_v2.out, gpu_leg_queued_broker.txt). Reads from the frozen
finish-agent state only; nothing there modified.

## WHAT THIS LEAVES FOR W03

1. Broker clearance -> run Q1 (live GPU replay leg; the qualification run
   whose first-run shas become the v2 anchors per the registry clause) and
   Q2 (the GPU boundary leg that completes EDGE-CLASS-SPLIT's
   host/GPU-agreement verdict).
2. W03's own C3 duty: the clean-window re-measure (Q3 command recorded;
   closeout-8's C3 was 3-way-contention-depressed).
3. The Astra anchor-version A/B decision stays PENDING — this battery's
   anchor record (case 4) supplies both versions' data for it; the choice is
   not TIE2's.
4. Owner decisions recorded as gaps: the C++-reference leg of the tie
   (all-three-paths clause) and the first-v2-build refusal history.
5. The C3-adjacent need from the brief ("the C3 re-measure"): unchanged in
   law — bars thresholds untouched, seeds unchanged; only a clean GPU window
   is missing, now queued with its exact command.
