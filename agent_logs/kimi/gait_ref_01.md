# H7 Stage 1 — Gait CPG CPU Reference: Construction Report

**Agent:** kimi-code (k3-256k)
**Run date:** 2026-08-29
**Spec:** `agent_logs/hy3/gait_packet_01.md` (accepted Rule-0 membrane) + `agent_logs/hy3/physics_packet_02.md` R5
**Constraints honoured:** CPU-only (`.venv-hy3d/Scripts/python.exe`, numpy); zero posts to the live engine on :8090; scratch in `.tmp` (uncommitted); `tools/gsplat` untouched.

## What was built

The packet's reference CPG, exactly as specced, as the golden CPU run for the later engine port:

- **Source:** `.tmp/gait_ref.py` (subcommands `bands|sweep|meta|energy`)
- **Outputs:** `.tmp/gait_ref_out/{bands,sweep,meta,energy}.json`
- **This report:** `agent_logs/kimi/gait_ref_01.md`

**Dynamics** (8 oscillators, packet's crouch set O = {LF,RF,LH,RH}×{hip,knee}):

```
φ̇_i = ω − σ·N_i·cosφ_i  +  w·Σ_(i,j)∈G_c sin(φ_j − φ_i − α_ij)      (Owaki eq 1 + Sakaguchi graph coupling)
θ_i = θ_mid + θ_amp·sinφ_i                                          (G1, measured joints only)
```

- **Coupling graph** per packet G2: ipsilateral hip–knee ×4 (α=0, placeholder), contralateral knees ×2 (α=π), diagonal knees ×2 (α=+π/2). α = canonical lateral-sequence walk lags (footfall LF→RH→RF→LH quarter-cycle), per R5 "use the canonical quadruped set as band centers" — UNVERIFIED for our creature, flagged, not re-derived.
- **Schedule (determinism tier):** float64, fixed dt = 1e-3 s, fixed-order RK4, fixed edge iteration order, no fast-math, `default_rng(seed)` initial phases. The packet (line 118) does **not** pin integer/fixed-point phase updates: *"Integer phase not required; the float schedule is deterministic under R2c pinning."* Tier documented = reproducible float schedule.

## H6 landed mid-task — new ROM adopted

The packet's knee ROM was measured about the ill-conditioned tilted axes. **H6's corrected-axis re-sweep landed 2026-08-29 (commit `a9a37048`, probe15)** and supersedes it; per the task brief the new measured numbers are used everywhere below:

| joint | ROM (H6, measured) | θ_mid | θ_amp | old (retired) |
|---|---|---|---|---|
| L (hind) knee | −1.56° … +145.39° | **71.915°** | **73.475°** | 71.22 / 73.72 |
| R (hind) knee | −2.33° … +140.75° | **69.210°** | **71.540°** | 55.60 / 59.22 |

θ_mid/θ_amp derived per G1: mid=(max+min)/2, amp=(max−min)/2. Note the H6 re-sweep **shrunk the L/R asymmetry** (flexion stops 145.39 vs 140.75 — the old 144.94 vs 114.82 gap was mostly axis tilt).

**Placeholder slots (stated, not hidden):** the four hips and the two fore "knees" (the elbow slots) are full phase oscillators in the coupling graph — the tetrapod topology needs them — but carry **no θ map** (θ_amp = 0, no measured ROM exists). They contribute to phase coordination only and nothing to angle/energy outputs. No numbers invented for them.

## G3 stand-in (flagged): shared-weight load surrogate

G3's real load (sole-polygon normal impulse λ from the deterministic contact solve) does not exist in CPU — it is the next stage's dependency. To keep the Owaki term alive rather than amputated, the reference uses a **surrogate**: `N_i = N0·s_i/Σs`, `s_i = max(0, −sinφ_i)` (stance-depth proxy; total support distributes over planted limbs — Owaki's physical-communication channel expressed in phase variables). **N0 is derived, not chosen:** full single-limb support must be able to stall the phase (φ̇=0 reachable, the Owaki entrainment regime): `σ·N0·max_stance(−sinφ·cosφ) = σ·N0/2 ≥ ω_ref` ⇒ `N0 = 2·ω_ref/σ = 10π`. Bands will be **re-measured** when the real estimator lands; the surrogate is recorded here, not silently dropped.

## G2 — measured per-pair bands (ω_ref = 2.5π, σ = 0.5, w = 1, burn-in 5 s, window 20 s, seed 20260829)

| directed edge | target α (cyc) | settled Δ̄ (cyc) | σ_natural (rad) | **δ_band = ±2σ (rad)** | half-split drift (rad) | coherence R |
|---|---|---|---|---|---|---|
| LF_hip→LF_knee | 0 | −0.0024 | 0.03604 | **±0.07209** | 1.9e-4 | ≈1 |
| RF_hip→RF_knee | 0 | −0.0023 | 0.03610 | **±0.07220** | 1.2e-4 | ≈1 |
| LH_hip→LH_knee | 0 | −0.0028 | 0.04373 | **±0.08746** | 1.3e-3 | ≈1 |
| RH_hip→RH_knee | 0 | −0.0029 | 0.04384 | **±0.08768** | 1.2e-3 | ≈1 |
| LF_knee→RF_knee | 0.5 | +0.4999 | 0.20263 | **±0.40526** | 1.3e-3 | 0.98 |
| LH_knee→RH_knee | 0.5 | −0.4997 | 0.25807 | **±0.51614** | 6.7e-4 | 0.97 |
| LF_knee→RH_knee | 0.25 | +0.2520 | 0.19866 | **±0.39732** | 2.2e-4 | 0.98 |
| RF_knee→LH_knee | 0.25 | +0.2518 | 0.19869 | **±0.39738** | 8.4e-4 | 0.98 |

All eight pairs **lock** (half-split drift ≤ 1.3e-3 rad over the 20 s window) and settle on the canonical walk lags to within 0.002 cycles. σ_natural is nonzero because the surrogate load brakes each oscillator phase-dependently — the locked lag breathes within each stride; the band is that measured breath, per pair, read out never chosen (δ_band = 2σ_natural, σ_band = σ_natural). Machine JSON: `.tmp/gait_ref_out/bands.json`.

**The named w experiment — and what the math did to it.** Packet: "pick w that minimizes the footfall-direction variance." Footfall *direction* is undefined without a world/substrate, so the CPU proxy is band tightness (Σσ_natural) plus lock:

| w | Σσ_natural (rad) | max half-split drift (rad) |
|---|---|---|
| 0.5 | 1.0891 | 3.47e-2 (lock degrading) |
| **1.0** | 1.0178 | 1.3e-3 |
| 2.0 | 0.9482 | 1.3e-3 |
| 4.0 | 0.8461 | 1.4e-3 |

Σσ_natural **decreases monotonically with w — the criterion has no interior optimum** (stronger coupling trivially freezes the lags, and w→∞ would also strangle the Owaki load term the transitions are supposed to come from). The packet's named selection rule is **degenerate at this tier**; the proposed w = 1 is adopted, the losers recorded above, and the real experiment (footfall-direction variance from real contacts) is deferred to the engine stage where footfalls exist.

## G4 — ω-sweep: the transition prediction is FALSIFIED at this tier

Protocol exactly per packet: ω ∈ [π, 4π], Δω = π/8 (25 dwells), T_dwell = 10 s, state carried between dwells, up-sweep then down-sweep, lag vector measured over the last 5 s of each dwell. Jump threshold = 3·max(σ_band) = 0.774 rad. Because a contralateral lag locked at α = π sits **on** the circular-mean branch cut (±π flips are the same physical state), the analysis is done on branch-safe `dist_from_target` and coherence R — the naive mean/std formula the packet writes literally would hallucinate a 2π "range" here (see Contradictions).

**Result:** no discontinuity anywhere, in either direction.

- Max step-to-step lag-vector jump: **0.115 rad** (up), **0.117 rad** (down) — 7× under threshold; zero crossings.
- Per-edge dist-from-target range across the whole up-sweep: **≤ 0.167 rad** (contralateral pairs ≤ 0.059 rad).
- Per-edge minimum coherence across the sweep: **R ≥ 0.836** (every pair locked at every ω).
- **Δω_h = 0.** τ_trans: undefined (no ω* exists to cross).
- The packet's FAIL condition — "Δ̄(ω) constant within σ_band across [π, 4π]" — is **TRIGGERED**: the lag graph is the *same walk* at every ω.

**Verdict, stated plainly:** the gait self-organizes (locks to the canonical walk, two-seed robust) but it does **not** transition. The prediction `Δω_h > 0` is **FALSIFIED at the CPU tier**. The packet's own causal story names why: Owaki transitions are a *load-feedback* phenomenon — the load must carry the body's state (CoM over the support polygon, other limbs' off-loading through real contact). The stance-depth surrogate brakes each oscillator but carries no body state, so nothing destabilizes the walk as ω rises. **This is not a waived failure:** the ω-sweep must be re-run engine-side with G3's real λ; if Δω_h = 0 there too, the membrane fails there. Machine JSON: `.tmp/gait_ref_out/sweep.json` (full 25×2 dwell curves).

## Metamorphic + determinism

- **Bit-identity (packet's hard gate):** two same-seed reference runs ⇒ φ series over the full 20 s window **0 ULP apart** (bit-identical). PASS. Tier: float64 reproducible schedule (integer phase not required, packet line 118).
- **Two-seed lock:** seed 20260829 vs seed 7 settle to lag graphs differing by ≤ 0.0042 rad on every edge — inside δ_band everywhere. PASS (the bands absorb IC variation, as designed).
- **Rotate-world (ψ = 90°):** at this tier the dynamics contain **no world-frame term at all** (gravity enters only through G3's real λ), so the rotated run is the identical computation: lag graph ULP-identical (0 ULP, same series as the bit-identity gate), and world-frame footfall directions rotate by exactly ψ (max direction error 0.0 — by construction). **PASS at this tier, honestly labelled "by construction":** the non-trivial gate is the engine stage, where the rotated contact solve must reproduce the rotated λ field. Footfall pattern first cycle: **LF → RH → RF → LH** — the canonical lateral-sequence walk emerges from the coupling, 24 stance onsets per oscillator per 20 s window (1.2 Hz). Machine JSON: `.tmp/gait_ref_out/meta.json`.

## G5 — energy honesty

Torque is unavailable in CPU (no hinge solve), so the packet's own direct proxy is used: `W_proxy = Σ_i |θ_amp_i|·∮|ċ_i|dt`, `c_i = sinφ_i`, over one stride (hind-knee footfall interval).

- Measured stride period **0.830 s** (1.205 Hz vs ω_ref/2π = 1.250 Hz — the surrogate load brakes cadence by 3.6%; a real, expected Owaki effect).
- **W_proxy = 579.41°/stride** vs the analytic limit-cycle value 4·Σ|θ_amp| = 580.06° — 0.1% agreement (sanity: the gait is a clean limit cycle).
- **No-pump falsifier:** `E_mech = Σ ½I_iθ̇_i²` (I = 1 normalized — CHOSEN-UNVERIFIED, experiment = limb inertia from mesh; the verdict is I-independent for any positive I): first-half mean 48.677 → second-half mean 48.488, i.e. **no monotonic growth — PASS**. θ is bounded by ROM by construction (sinusoid), so boundedness is structural at this tier; the non-trivial energy gate is engine-side where hinge torque feeds back into the solve.
- **COT anchor:** not runnable in CPU (needs mass and stride distance). Per the packet, W_stride is **reported, not pass/failed against a guessed number**. Named experiment stands: match the crouched-primate COT curve, margin 2× proposal, engine stage.

## Falsifier table (every verdict, honest)

| # | Falsifier | Verdict |
|---|---|---|
| G1 | θ map from measured ROM, bounded in ROM | **PASS** (H6 ROM adopted; placeholders carry no map, stated) |
| G2 | per-pair bands measured, lags lock, L/R asymmetry inside band by construction | **PASS** (bands above; all pairs lock; two-seed robust) |
| G2-w | w picked by footfall-direction variance | **CRITERION DEGENERATE at CPU tier** — monotone in w; w = 1 (proposal) adopted, real experiment deferred to engine footfalls |
| G3 | load from substrate contact | **BLOCKED — next stage's dependency** (surrogate used and flagged; estimator A-vs-B experiment runs engine-side) |
| G4 | ω-sweep: discontinuous transition, Δω_h > 0, finite τ_trans | **FALSIFIED at CPU tier** — Δ̄ constant, Δω_h = 0, τ_trans undefined; re-run engine-side is mandatory |
| G4 | FAIL condition "Δ̄ never changes" | **TRIGGERED** (same walk at all 25 ω, both directions) |
| Meta | rotate-world: lag graph identical, footfalls rotate by ψ | **PASS — by construction at this tier** (0 ULP lag graph, 0.0 direction error); real gate engine-side |
| Meta | two same-seed runs ⇒ φ series ≤ 1 ULP | **PASS — 0 ULP** (float64 pinned schedule tier) |
| G5 | no energy pump: E_mech bounded | **PASS** (structural at this tier) |
| G5 | COT-anchored "reasonable" W_stride | **REPORTED, not judged** (579.41°/stride; anchor experiment engine-side) |

## What the math contradicted in the packet

1. **w-selection rule** ("minimize footfall-direction variance") is degenerate: band tightness improves monotonically with w; only the real-footfall version of the experiment can have an interior optimum.
2. **η_lock as literally defined** (R5: "2σ_natural of the warm-up transient") measures **6.065 rad ≈ a full circle** — the burn-in transient is dominated by IC convergence, so the literal threshold cannot discriminate lock from non-lock. The operative stationarity number used instead: in-window half-split drift ≤ 1.3e-3 rad.
3. **The packet's literal `mean_t/std_t` lag formula** is branch-cut-blind: a contralateral pair locked exactly at π reports σ ≈ huge from ±π flips alone. Circular statistics were used; the first sweep pass "detected" a spurious 2π contralateral range that was entirely the artifact.
4. **G2's claim that the band "absorbs the L/R asymmetry"** is untestable at this tier: φ dynamics never see θ (bands before/after the H6 ROM update are identical to the last digit). The asymmetry enters only through real contact geometry — engine stage. (And H6 shrank the asymmetry itself: 145.39 vs 140.75 flexion stops.)

## Ready for the engine port / blocked

**Ready:**
- G1 phase→angle map with H6-measured ROM for both hind knees (`θ_mid/θ_amp` above).
- The coupling graph, canonical walk targets, and the measured per-pair bands as the port's acceptance bands.
- `.tmp/gait_ref.py` as the **golden CPU run**: the engine port's bit-exactness gate should reproduce this φ series under the pinned schedule (fixed dt = 1e-3, fixed RK4 order, fixed edge order, seeded ICs) — the same pattern as the B15 water gate.
- Surrogate load as a clearly-labelled placeholder until G3 lands.

**Blocked (next stage's dependencies):**
- **G3 real load** — sole-polygon normal impulse λ from the deterministic contact solve; the estimator A-vs-B experiment (impulse vs penetration proxy) runs there, then bands are re-measured.
- **G4 transition/hysteresis re-run** with real λ — the membrane's walk→trot prediction lives or dies there.
- **COT anchor + W_stride judgement** — needs mass, stride distance, hinge torque.
- **w's real experiment** — footfall-direction variance from real contacts.

---

# H7 Stage 2 — Engine Port: the march becomes a walk (2026-08-29, kimi-code k3-256k)

**Spec:** H7 stage-2 brief — port the stage-1 golden run (`.tmp/gait_ref.py`) to the
engine bit-exactly, drive the knees from it, B15-style gate, one time-stream.

## Step 0 — which component was driving the pose

TWO time-streams were live (the duplicate-driver fight the brief warned about):

1. **The engine's `hinge.comp` kernel** — engaged at engine boot via
   `.tmp/hinge_setup.py` (`Hinge engaged: 18459 verts, period 4.0s, ROM L 144.9
   R 114.8 deg` in `engine_v12.log` — note the **stale pre-H6 ROM**; the hinge
   kernel rewrites every vertex each frame *after* any driver write, so it owned
   the visible pose).
2. **`.tmp/leg_move_v2.py` (driver_v15)** — posting `/mesh_bin` vertex updates at
   84/s that were clobbered every frame by (1): pure waste, plus the fight risk.

Both were killed for the restart; after the rebuild the ONLY time-stream is the
engine's (hinge engaged with the current H6 ROM 145.39/140.75, gait driving it).

## The transcendental problem — and its solution

The pinned schedule (fixed dt = 1e-3, fixed-order RK4, fixed edge order, seeded
ICs, pairwise-sum tree measured `((s0+s1)+(s2+s3))+((s4+s5)+(s6+s7))`) is
correctly-rounded-op replication — the B15 pattern. The one hard wall: `sin`/`cos`
are **not** correctly rounded by anyone. Measured on this box:

- `np.sin` ≡ `math.sin`, `np.cos` ≡ `math.cos` (0 mismatches / 200k) — one
  implementation: **ucrtbase.dll's**, and it is **not correctly rounded**
  (~3% of inputs 1 ULP off mpmath-CR) and **not fdlibm** (~3.4% off musl's
  kernel). A correctly-rounded or fdlibm shader loses the gate by construction.
- The DLL ships no source, but the machine code is the spec. `sin @0xaba70`,
  `cos @0xa7730`, reduction `@0xab910`: an ISA-flag branch (runtime value 3)
  selects an **FMA path** — Cody-Waite reduction (magic-number rounding,
  3-word π/2, exact error terms) + degree-6 FMA Horner polynomials. Transcribed
  op-for-op: Python twin `.tmp/ucrt_trig.py` validated **0 mismatches over
  2,000,010 values** across every code path (tiny/small/med/big/edges, |x| to
  1e6) against the live DLL, then ported to GLSL f64 (`fma()`, `precise`,
  constants uploaded as raw f64 bits). Boundary named: the [2e7, ∞) Payne-Hanek
  path is not ported — φ passes 2e7 rad only after ~30 days of continuous gait
  at ω = 2.5π.

## What was built

- **`ChimeraEngine/engine/shaders/gait.comp`** — the CPG as a CA-field kernel:
  one workgroup × 8 invocations = one RK4 step (barrier-synced stages), Owaki
  surrogate load + Sakaguchi coupling in fixed edge order, phase ring record +
  θ mirror out. The UCRT trig above.
- **Engine integration** (`engine.cpp/.hpp`, `main.cpp`): the **gait clock** on
  the water clock's pattern — `/gait_bin` (constants + seeded φ₀, bit-exact
  upload), POST `/gait {on, omega, steps}` (omega parsed as **double** — a
  32-bit round would break the gate), GET `/gait`, GET `/gait_state` (16 MiB
  ring readback). Steps recorded into the frame's command buffer before the
  hinge dispatch; `hinge.comp` gained a theta mode (`flags&1`: pose from
  θ_L/θ_R instead of the open-loop cosine — the gait replaces the hinge's
  phase source; CPU fallback `pose_hinge` same). Hips/elbows placeholder-inert
  per stage 1.
- **`.tmp/gait_setup.py`** (constants + ICs upload) and **`.tmp/gait_verify.py`**
  (the gate + walk captures).

## The gate (B15-style)

Engine gait, fresh from the golden seed, ω = 2.5π, N = 25,000 steps (25 s,
~30 strides) vs `.tmp/gait_ref.py` run for the same N/seed/ω:

**max ULP over 25,000 × 8 phases = 0 — PASS, bit-identical.** Machine JSON:
`.tmp/gait_ref_out/engine_gate.json`.

## The walk

- θ series over a stride (engine status reads): **θ_L 2.2…130.0°, θ_R 0.4…124.7°,
  antiphase** — the canonical lateral-sequence walk in the two measured hind
  knees, no gallop, no in-phase march.
- `/frame` captures (`.tmp/gait_walk/walk_00…09.png`, operator's camera
  untouched — tight on the legs): the visible leg cycles full extension
  (foot planted) → deep flexion (heel-to-butt) over the stride; the antiphase
  alternation is the numeric series above.
- **FPS 299–300 at the cap, ft avg 0.26 ms** with the gait stepping 3 steps/frame
  — identical to the pre-port baseline (the frost GT batch was running
  concurrently throughout; brief FPS dips only during the 16 MiB gate readback).

## Honest status of G3 (load feedback) — still BLOCKED, named

Unchanged from stage 1, and now the membrane's critical path: G3's real
`N_i` = sole-polygon normal impulse λ from the **deterministic contact solve
does not exist yet**. The stance-depth surrogate (`N_i = N0·s_i/Σs`,
`N0 = 2ω_ref/σ` derived) still stands in, flagged. Waiting on it: the estimator
A-vs-B experiment (impulse vs penetration proxy), band re-measurement, the
mandatory G4 ω-sweep re-run (stage-1 falsification of Δω_h > 0 was at the CPU
tier with the surrogate — the walk→trot prediction lives or dies on real λ),
the w-selection experiment with real footfalls, and the COT anchor.

## Contradictions / notices found this stage

1. **The live engine marched on stale pre-H6 ROM** (144.9/114.8 engaged at boot)
   while H6's corrected 145.39/140.75 was the law — fixed by the re-engage;
   noted because any visual judgment of "the march" before today was of the old
   ROM.
2. **UCRT's sin/cos are ~1 ULP implementations that are neither correctly
   rounded nor fdlibm** — any "use a good libm in the shader" plan would have
   silently failed the 0-ULP gate; the disassembly was the only honest path.
3. **The dead-code trap in reverse engineering:** UCRT's tiny-|x| path computes
   `x·(1−2⁻⁵³)+1.0` into xmm1 purely to raise FP flags — the return value
   (xmm0) is just `x`. Reading the flags-only computation as the result would
   have produced a "sin(1e-9) = 1.0" port.
4. **`cos` takes its big path at |x| > π/4 (strict) while `sin` uses ≥** — a
   one-bit boundary asymmetry that matters exactly at π/4.
5. The gate's naive (branch-cut-blind) hind-knee lag statistic reads
   −0.0075 ± 2.9 rad on a π-locked pair — the same artifact stage 1 documented;
   circular stats give the true −0.4997 cyc. Not re-litigated.
