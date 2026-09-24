# TIE2 RUN PLAN — FROZEN (preregistered before execution)

Agent: M-tie2. Date: 2026-09-24. This plan is written BEFORE any battery run.
It executes ONLY the frozen prereg's cases. No new tolerances, no tuning, no
anchor choice. Failures are results, preserved verbatim.

## THE FROZEN PREREG (quoting)

Receipt: `agents/P02P03/receipts/prereg_tie_v2_9376c3d8.txt` (= git 9376c3d8,
committed BEFORE any v2 run; full text `PREREG_RESIDUAL_TIE_V2.md` @ a62b286e):

> "the contact residual tie bound = kTouch (1e-5 m, the pad's own position
> resolution) converted to the row's velocity units (kTouch/dt_ = 3e-3 m/s);
> the tie rule (a floor-check violation within the bound is exactly-satisfied;
> tol_k = max(1e-9 relative, kTouch/dt_)); one-sided (only the satisfaction
> test widens; the multipliers/cone/tier law untouched)"

Falsifier table (PREREG_RESIDUAL_TIE_V2.md, verbatim names):
1. EDGE-CLASS-SPLIT: "at the kTouch/dt_ boundary (violations at 3e-3 exact,
   +-1 ulp) host/GPU must agree on the accept/reject decision."
2. FALSE-FEASIBILITY: "the accepted mask's one-tick pad motion must stay
   within kTouch (checked: violation bound * dt_ <= kTouch)."
3. ANCHOR-DRIFT: "the v1 anchors (the pre-band trace) and the v1-band anchor
   (the 6-entry walk) are preserved in the registry; the v2 anchors are the
   v2 build's own first-run shas, recorded at the qualification run."
4. OUTSIDE-BAND-DRIFT: "projections with any violation > kTouch/dt_ decide
   identically to the pre-v2 behavior (the tolerance widening is inactive
   above the bound)."
5. REPLAY-DIVERGENCE: "the v2 build must walk PAST tick 41 (the continue
   outcome) on host and GPU from the tick-41 fixture state, and hold
   host-vs-GPU FULL-state parity as far as the run reaches."

Absorbed-fact clause (binding on expectations): "the post-projection velocity
difference (up to ~1e-3 m/s on the affected row) is REPORTED SEPARATELY per
Astra's ruling and is expected to re-separate the trajectories after tick 41
-- byte parity past 41 is NOT claimed."

## THE FROZEN IMPLEMENTATION STATE (verified before planning)

- The tie patch at the freeze (git diff 9376c3d8..a62b286e) touches ONLY the
  two tol expressions + the signature + the two call sites in
  `walker_numba_split.py` and its regenerated `walker_kernels.cuh`:
  `tol = max(1e-9*(1+|floors[k]|), tol_band)`,
  `tol_band = cst[CF_k_touch]/cst[CF_dt]` (CF_k_touch=4, CF_dt=2).
- GAP RECORDED (not fixed here): the C++ reference + instrument
  (gait_controller_ref.hpp / gait_controller_instr.hpp) do NOT carry the tie
  at the freeze, though the convention clause names "all three paths". The
  falsifier table's named legs (host/GPU) are both served by
  walker_kernels.cuh: it compiles the GPU DLL (nvcc -> walker_env_v2.dll,
  built 14:10 2026-09-23) AND the CPU host replay (cl via host_shim ->
  host_loop.exe, rebuilt 14:00 2026-09-23). Recorded as a v2-completeness
  gap for the owner; no code authored.
- Frozen run state on disk: `E:/ChimeraWork/finish-agent` byte-verified equal
  to a62b286e for walker_numba_split.py, walker_kernels.cuh, walker_env.cu,
  co8_v2walk.py. Binaries present: walker_env_v2.dll, host_loop.exe.
- Frozen constants (host_shim/cst.txt): cst[2]=3.333333333333333547e-03 (dt_),
  cst[4]=1.000000000000000082e-05 (kTouch). The implemented bound
  cst[4]/cst[2] = 0.003 (double).

## RESOURCE DISCIPLINE (measured 2026-09-24 before planning)

nvidia-smi: RTX 4090, util 20%, 23092/24564 MiB used; desktop, Steam,
Battle.net, Bigscreen, lmstudio llama-server attached — operator-session
signs present. Per the campaign law ("no fleet GPU during gaming") and the
brief: ALL GPU-touching runs are QUEUED-BEHIND-BROKER (exact commands
recorded, never executed here). CPU-side cases run now. No existing process
touched.

## EXECUTION ORDER (= the prereg's table order)

### CASE 1 — EDGE-CLASS-SPLIT (the kTouch/dt_ boundary ±1 ulp)
- CPU leg NOW: `tie_boundary_probe` (a pure HARNESS — zero physics authored:
  it #includes the FROZEN walker_kernels.cuh via the host_loop.cxx shim
  pattern and calls the FROZEN project_rows). Registered inputs: R=1,
  floors[0]=0.0, one unit row, identity inv, initial = -viol*e0, with
  viol in {tb, nextafter(tb,-inf), nextafter(tb,+inf)} where
  tb = cst[CF_k_touch]/cst[CF_dt] computed in-harness from the frozen cst
  (the kernel call sites' own expression). Observables: return value
  (0=enumeration failed), p_out==initial? (empty-mask accept = no repair),
  multipliers (repair applied?). The pre-v2 decision on the SAME frozen code
  = the same call with tol_band=0.0 (the max() then selects the exact pre-v2
  tolerance; tol_band is a parameter of the frozen signature — this is the
  registered OUTSIDE-BAND-DRIFT instrument, not a code change).
- EXPECTED (per the registered convention): viol=tb and viol=tb-1ulp ->
  v2 accepts with NO repair (exactly-satisfied tie; <= is inclusive) where
  pre-v2 repairs; viol=tb+1ulp -> repair on both v2 and pre-v2 (identical).
- GPU leg: the same probe under nvcc + device run -> QUEUED-BEHIND-BROKER.
  PASS requires both legs measured and agreeing; the CPU leg alone records
  the host decision only.

### CASE 2 — FALSE-FEASIBILITY (violation bound * dt_ <= kTouch)
- CPU NOW (same probe): for every ACCEPTED case print viol, viol*dt_, and
  the comparison vs cst[CF_k_touch]. Expected: PASS, equality at the
  boundary ((kTouch/dt_)*dt_ == kTouch exactly in the frozen doubles).
- The replay legs carry the integration-level form (every accepted mask).

### CASE 3 — OUTSIDE-BAND-DRIFT
- CPU NOW (same probe): above-band cases {tb+1ulp, 1e-2, 1.0}: v2 decision
  must EQUAL the tol_band=0.0 decision on every observable. Plus the frozen
  diff audit (already recorded: only the two tol expressions changed;
  multipliers/cone/tier untouched).
- Expected: PASS (identical above-band decisions).

### CASE 4 — ANCHOR-DRIFT (the registry record — NO choice made)
- v1-preserved: verify + sha256 the co8_t41_fixture files (state_t40_host/
  state_t40_gpu/state_t39_cpp/scene_sha256/host_drill_t41/device_drill_t41 +
  README) at a62b286e — the pre-v1 anchor retained in the fixture.
- v1-band anchor: co8_csub310 BAND_ENTRIES=6 record verified.
- v2-recorded: sha256 of the v2 build's own first runs as preserved
  (co8_hl_v2.out, co8_dll_v2_120.txt, co8_dll_v2b_120.txt, co8_cp_v2_120.txt)
  + the v2 binaries (walker_env_v2.dll, host_loop.exe) + the v2-era drill
  lines. Both anchor versions' behavior recorded where the cases touch them;
  the A/B decision stays Astra's (PENDING), untouched here.

### CASE 5 — REPLAY-DIVERGENCE (walk PAST tick 41, host and GPU)
- HOST leg NOW (CPU): `HL_FULL=1 ./host_loop.exe` (the tie-patched CPU build
  of the frozen walker_kernels.cuh) in the frozen finish-agent/typeb_gpu,
  stdout redirected to TIE2/receipts/. Decision: does the rc=5 class 5
  adv=2 ticks=40 refusal at tick 41 fire under the tie on the host leg, or
  does the walk continue past 41?
- GPU leg: `python co8_v2walk.py` (walker_env_v2.dll) -> QUEUED-BEHIND-BROKER
  (exact command recorded). PRESERVED evidence recorded: co8_dll_v2b_120.txt
  (14:18, post-rebuild v2 build): no REFUSED line, t=41 shows the resolved
  impact, walk continues through t=43 (the preserved capture's end);
  co8_dll_v2_120.txt (14:06, the FIRST v2 build): still refused at 41 with
  the signature — the rebuild is part of the frozen history and is recorded,
  not re-judged. The live GPU re-run remains the qualification duty.

## VERDICT FORM
Each case: PASS / FAIL / PARTIAL (one leg measured, other queued) / QUEUED,
with verbatim numbers. No threshold is chosen here: the registered decisions
themselves are the bars.

## WRITES
Only `tools/monkey_campaign/agents/TIE2/**` (this plan, brief.md, report.md,
receipts/, run/ workspace with the probe harness + its outputs). Reads from
the frozen finish-agent state; nothing there is modified.
