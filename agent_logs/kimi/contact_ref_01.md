# G3 — The Substrate Contact/Load Reference Solve: Construction Report

**Agent:** kimi-code (k3-256k)
**Run date:** 2026-08-29
**Spec:** `agent_logs/hy3/gait_packet_01.md` §G3 + the G3 stage brief (H7's missing dependency; H10's impact source)
**Constraints honoured:** CPU-only (`.venv-hy3d/Scripts/python.exe`, numpy/scipy/trimesh); zero posts to the live engine; no GPU batch jobs (H12 render running untouched); scratch in `.tmp` (uncommitted); `tools/gsplat` untouched.

## The membrane (Rule 0, stated before the build)

- **STATEMENT:** the load the gait's Owaki term needs is the normal contact impulse λ on each
  hind leg's sole-polygon set, produced by a deterministic Baumgarte-stabilized unilateral
  contact solve that is a **pure function of the posed state** (θ_L, θ_R, θ̇_L, θ̇_R) —
  same state in ⇒ bit-identical λ out. On this substrate the sole rows' load path is the
  **ground plane the birth pose stands on** (the toes do not touch the forelimbs — measured,
  see Contradiction 1).
- **PREDICTION:** (i) two independent evaluations of the solve on the same state give 0-ULP
  identical λ; (ii) over a reference stride, λ_i(t) is zero in swing and pulses in stance,
  L/R antiphase-symmetric; (iii) λ responds to pose (θ) and to drive speed (θ̇∝ω);
  (iv) the packet's A-vs-B experiment (impulse sum vs penetration proxy) has a measurable
  winner by band tightness + stance correlation.
- **FALSIFIER:** (i) any ULP difference in a double run; (ii) λ ≡ 0 or constant across the
  stride (no pose state — the surrogate's own failure mode); (iii) λ identical across an
  ω-ladder (no speed state); (iv) Σσ_natural or stance correlation ties → no estimator
  verdict. Verdicts as measured: (i) **PASS** (0 ULP both gates); (ii) **PASS** (contact
  windows track θ exactly, zero in swing); (iii) **FIRED** — λ is ω-insensitive at this
  drive (the Baumgarte clamp saturates at 5.8× slop press depth; named for the gait
  line, see the stride section); (iv) **PASS with a confound named** (B adopted; both
  estimators stall-trap the reference gait at the surrogate-derived normalization).

## What was built

- **Source:** `.tmp/contact_ref.py` (subcommands `precompute|stride|estimator|all`)
- **Geometry cache:** `.tmp/contact_ref_geom.npz` (candidate pairs, intervals, sole sets)
- **Outputs:** `.tmp/contact_ref_out/{stride.json, stride_curves.npz, estimator.json,
  gait_contact_A.npz, gait_contact_B.npz, *.log}` + two evidence renders
  (`full_sets.png`, `lower_sets.png`)

**The pose law:** the H6 blend deform (`.tmp/leg_move_v2.py` header, exec'd like
`fold_validate.py` does): per-vertex Rodrigues about the corrected inter-knee axis
(n = [0.9997, −0.0244, 0]) through the measured joint centers, weights `w_v` on the welded
dual graph. The substrate is SALLY_body_0 (`8955…_birth.glb`): **36,630 tris / 18,459
verts** (the brief's 34,538 is the water cell count of the same mesh family — noted, not an
error), outward winding (signed volume +13.83).

**The solve (per macro-step, per leg):**
1. *Broad phase:* swept-ROM candidate pairs (union over a 21-pose grid per leg, exact
   vertex-distance filter with per-pair triangle radii, per-pair active θ-interval) +
   per-step AABB cull. **Completeness falsifier:** off-grid poses searched exhaustively —
   **0 missed pairs both legs**. Cross-leg (L↔R) near-pairs over 9 ROM corners: **0**.
2. *Narrow phase:* exact vertex-face both directions (signed gap, barycentric inside test,
   blend weight interpolated on the face), plus analytic **ground-plane rows**
   (y < Y_G + slop, normal +y). Plane-crossing pairs that yield no vertex row are **counted
   per step** (missed-contact instrumentation), not silently dropped.
3. *Impulse solve:* projected Gauss–Seidel over canonically sorted rows (integer-key
   lexsort), **K_PGS = 8 fixed sweeps**, Baumgarte bias = `min(depth, slop)/dt` (β = 1, the
   atlas's verbatim term). Per-row effective mass = series of two derived paths: hinge
   moment (`ℓ²/I_eff`, exactly coupled through `S_h = Σℓλ`) and structural/compression
   (`1/m_leg`, diagonal-lumped — the standard effective-mass bound: a contact's effective
   mass never exceeds the leg's moving mass). `I_eff = Σ m_v w_v² d_v²` about the hinge
   axis, `m_leg = Σ m_v w_v²`, `m_v` = ⅓ incident triangle areas (ρ_s = 1,
   CHOSEN-UNVERIFIED — one global scale constant, absorbed by the stall normalization).

**Derived constants (nothing swept):** slop = E_MED = 0.06839 (median mesh edge);
Y_G = −0.01951 (deepest sole vertex at rest — the birth pose *stands on* the plane);
broad-phase margin = max inter-pose vertex displacement + slop; I_eff L = 16.033 /
R = 15.281; m_leg L/R (same w² weighting); β = 1 (atlas verbatim); dt = 1e-3 (the gait
macro-step; λ is per-macro-step impulse). Sole-polygon sets: the measured **plantar slab**
of each rotating set — core tris with rest centroid y ≤ Y_G + 2·slop: **927 tris / 553
verts per leg**.

## Contradiction 1 — the brief's load-path premise is wrong (measured)

The brief: *"the crouched monkey's soles/toes touch the forelimbs (the rest pose has
measured contacts — the probe chain found toe↔forelimb contacts at extension stops). There
is no ground plane yet — the crouch's self-contact IS the load path."*

Measured on the substrate:

1. **The birth pose is a STANDING monkey with free-hanging arms** (`full_sets.png`): arms
   hang at the sides, hands ending at y ≥ 2.49 (nothing outside the leg sets exists below
   that); the feet stand at y ≈ −0.02. There is no crouch in the mesh — "the crouch" is the
   *gait's* θ_mid ≈ 70° knee angle, not the birth pose.
2. **probe15's "toe↔forelimb" extension-stop contacts are an artifact of its own rotating-set
   cut.** probe15 selected rotating rods by `z < 0.39`; its "stationary partners" at the
   extension stops (L: [−0.728, 0.260, 0.572]; R: [0.987, 0.286, 0.468]) sit at z > 0.39 —
   but the skin's measured rotating sets span z −0.20 … +1.44 (the long toes). **100% of
   skin vertices within 0.3 of either partner position are inside the leg's own rot_set** —
   the partners are the foot's own distal toes, which the actual deform law rotates rigidly
   with the leg. Intra-rigid-set contacts can never develop impulse from knee motion.
3. Consequently the sole rows' real load path is the **ground plane** (JOINT_ATLAS sole
   rows were floor contacts; Owaki's N_i is by definition the ground reaction). The ground
   is not a "later case" — it was always the packet's load; the stage brief's self-contact
   premise is falsified by measurement. **Follow-up for the H6 line:** H6's *extension*
   stops (−1.56°/−2.33°) rest on the same artifact and should be re-measured (the toe's
   ground contact is the candidate limiter); the *flexion* stops are confirmed real on the
   skin (shank↔thigh, gap 0.031 at 145.39°). G3 used the H6 ROM as-is (it is the gait's
   law); the load curves inherit whatever error the extension-stop numbers carry.

## Contradiction 2 — naive hinge-priced impulses diverge (measured, fixed)

The first solve priced every row through the hinge alone (`m_eff = I_eff/ℓ²`). Ground rows
on sole vertices near the knee axis have lever ℓ ≈ 0 (the contact normal is along the
bone-compression line), so `m_eff → ∞`: peak "impulses" of **7.4e11**, non-monotone in ω —
pure lever noise. Diagnosis: legs are compression structures; ground reaction generically
travels the structural path, not the hinge moment. Fix (derived, standard): per-row
effective mass bounded by the leg's moving mass (`A_rr = ℓ²/I_eff + 1/m_leg`). After the
fix: bounded, monotone, L/R-symmetric loads (below). Estimator A = the solver's λ **with
this mass model**; estimator B = the packet's penetration proxy verbatim.

## Determinism (the load-bearing requirement)

- **Double-run of the stride pass: max ULP = 0 over every recorded series** (N_A, N_B,
  nonsole λ, depth — full 800-step stride at ω_ref, two independent evaluations).
- **Double-run of the full gait with contact in the loop (estimator A): φ series ULP and N
  series ULP — see the estimator table below.**
- Mechanism: fixed canonical order everywhere (candidate pairs sorted once; per-step rows
  lex-sorted by integer keys; PGS fixed order + fixed sweep count), float64, no fast-math,
  no RNG anywhere (seeded ICs only, same `default_rng(seed)` as the golden run). The solve
  is a pure function of (θ_L, θ_R, θ̇_L, θ̇_R); N_i is recomputed from state each macro-step
  (no accumulation — the packet's drift clause).
- Broad-phase completeness: 0 missed pairs at 5 off-grid poses per leg. PGS convergence:
  final-sweep max |Δλ| reported per run (never assumed); KKT violation (residual constraint
  approach velocity) max 8.95 vs bias 68 during the deepest press (666 rows) — 1.3% worst
  step, ~0 in swing/stance-typical steps.

## The load curve over a reference stride (ω_ref = 2.5π, canonical settled hind-knee lag from bands.json)

Sampled N_B_L every 1/16 stride (raw, penetration-proxy units; N_A_L in solver-impulse
units, κ-normalized versions feed the CPG):

```
phase (cyc): 0    .06   .13   .19   .25   .31   .38   .44   .50   .56   .62   .69   .75   .81   .88   .94
N_B_L:       0    0     0     0     0     0     0     0     0     22.0k 26.9k 4.7k  0     4.7k  26.9k 22.0k
N_A_L:       0    0     0     0     0     0     0     0     96    6.8k  19.7k 0.9k  0     1.0k  20.3k 6.2k
```

- **Shape: a double-peak stance with a liftoff at maximum extension** (phase 0.75 =
  φ = 3π/2). Mechanism, measured: the long forward toes (z-lever +1.15 about the knee)
  trace an arc that dips below the birth ground level for θ ∈ [0.4°, 68.4°] (static sweep,
  peak dip −0.40 at θ ≈ 38°) and lifts above it both at deep flexion AND at full extension
  (toe at +0.012 at θ = −1.56°). The "stance" of this drive is a toe-press through the
  knee-flexing half of the cycle, with a genuine unload at maximum extension. Duty:
  L 0.46 / R 0.47 (N_A), 0.42 / 0.43 (N_B). Swing: exactly zero load.
- **Symmetry:** peak ratio L/R = 0.992 (N_A), 0.991 (N_B); half-cycle-shifted correlation
  0.904 (N_A), 0.980 (N_B); peaks antiphase (L at 0.598 cyc, R at 0.409 cyc — the measured
  δ ≈ −π hind-knee lag). The H6 L/R asymmetry (145.39 vs 140.75 flexion stops) enters the
  curve as different press windows per side — real geometry in the load, as required.
- **θ response (falsifier ii — pose state): PASS.** Static θ-sweep: sole load confined to
  θ ∈ [0.44°, 68.44°], zero outside; contact windows track the pose exactly. The
  surrogate's "no body state" failure IS fixed for pose: the load now reads the substrate.
- **ω response (falsifier iii — speed state): essentially ABSENT at this drive.**
  ω-ladder [π … 4π]: mean N_A varies < 0.1%, peak < 0.3%, duty < 0.5%. Mechanism,
  measured: the kinematic drive plunges the toe 0.39 = **5.8× slop** into the ground, so
  the Baumgarte term `min(depth, slop)/dt` saturates on **83% of contact steps**; the
  approach-velocity term (θ̇ ≈ ±10 vs bias 68) contributes ~1.5% (static vs extending
  mid-press: 14,219.9 vs 14,437.0) and cancels across the two windows. λ carries **pose**
  state strongly and **speed** state only through a saturated channel. Whether the ω-sweep
  (G4) revives depends on whether Owaki transitions need pose-dependent load (now real) or
  speed-dependent load (weak at this slop/drive regime — named for the gait line: the
  press depth 5.8× slop is the drive's own amplitude, and a re-derived contact band or a
  body-mounted drive would un-saturate it). **G4 was NOT re-run** — that is the gait
  line's next stage now that real λ exists.
- **Non-sole contact load (reported, not in N_i):** the flexion-stop wedge (shank core vs
  thigh/butt skin) peaks at 31.3k (L) / 33.6k (R) impulse near θ_max — the H6 flexion stop
  is a real mechanical event in the gait envelope. It loads the leg but not the sole set,
  so it stays out of the estimators (packet: C_i = sole rows) and is recorded here.

## The estimator experiment (the packet's named A-vs-B)

Protocol: golden CPG (8 oscillators, packet's G_c, ω_ref = 2.5π, σ = 0.5, w = 1, seed
20260829, burn-in 5 s, window 20 s) with N_i read from the contact solve **at the top of
each macro-step** (packet: recomputed from state each step). θ̇ for the approach velocity
uses the load-free derivative (one fixed-point pass — stated). Only the two hind knees
have sole sets; the six other oscillators carry N = 0 (no fore contacts exist at this
tier — stated, the fore limbs are the support). Stall normalization per estimator:
κ_e = N0 / (raw peak over the reference stride), N0 = 2ω_ref/σ = 31.416 — the surrogate's
own derived stall load, so the comparison is about information content, not scale
(κ_A = 1.735e-4, κ_B = 1.144e-3; raw peaks A = 181,080, B = 27,466).

**Results (machine JSON: `.tmp/contact_ref_out/estimator.json`):**

| estimator | Σσ_natural (rad) | max half-split drift | min coherence R | hind-knee pair | cadence LHK/RHK | stance corr |
|---|---|---|---|---|---|---|
| A (impulse sum) | 9.7451 | 0.5716 | 0.0547 | lag −0.006 cyc, R 0.9997 | **0.000 / 0.000 Hz** | −0.9991 |
| B (penetration proxy) | 9.5313 | 0.8157 | 0.0489 | lag −0.002 cyc, R 0.9965 | **0.000 / 0.000 Hz** | −0.9884 |

**Literal verdict per the packet rule: B** (tighter Σσ_natural AND stronger stance
correlation; A recorded as the loser). **Determinism gate with contact in the loop:
φ series 0 ULP, N series 0 ULP across two independent 25 s runs.**

**But the experiment is confounded, and the confound is the real finding.** Under BOTH
estimators the hind knees **stall to a dead stop** — 0.00 phase cycles over the 20 s
window (free-run: 25). Mechanism, measured: the real load curve is nearly binary in the
press window (the Baumgarte clamp saturates — 83% of contact steps), so the press
*plateau* sits at ≈ 0.98 of the κ-normalized peak = N0 = the stall load; σ·N·|cosφ| ≥ ω
holds for the whole plateau, φ̇ → 0, the foot never lifts (N duty 1.000), and both knees
park **in-phase** (R ≥ 0.996 at lag ≈ 0) at sinφ ≈ −0.6…−0.8 (θ ≈ 13–28°, mid-press).
The fore chain stays locked (R ≈ 0.99); every pair involving a hind knee de-locks
(R ≈ 0.05–0.09) because the hips free-run while the knees stand still. This is textbook
Owaki mechanics — load feedback halting the limb — overshot into a fixed point: the
stall normalization κ = N0/peak was derived for the surrogate's shared, momentary-peaked
channel (N0 reached only by one limb, only instantaneously), and the real per-leg channel
holds near-stall for ~46% of the cycle. The packet's stance-correlation criterion
presupposes a locking gait; with the phase parked it reads −0.99 for both estimators
(N tracks planting by construction — the phase proxy is what decorrelated).

So: **B is adopted** — on the packet's literal rule, and independently on curve quality
(B's stride curve is the cleaner channel: half-cycle-shifted corr 0.980 vs A's 0.904;
A's impulse additionally needs the structural effective-mass bound to exist at all —
Contradiction 2) — **and the operating point is named as the gait line's next
re-derivation**: σ and κ must be re-set for the real channel before bands are
re-measured and G4 is re-run. The κ probe below (run as due diligence on MY OWN
normalization, not a G4 re-run) shows the trap is the operating point, not the channel:

**κ probe (estimator B, same protocol, gain scaled — due diligence on my own
normalization, NOT a G4 re-run; machine log `.tmp/contact_ref_out/kappa_probe.log`):**

| κ scale | Σσ_natural (rad) | min R | cadence LHK/RHK | hind-knee lag | stance corr |
|---|---|---|---|---|---|
| ×0.25 | **0.7699** | 0.9756 | 1.239 / 1.239 Hz | −0.4991 cyc (canonical antiphase) | +0.557 / +0.530 |
| ×0.5 | 1.9340 | 0.8359 | 1.208 / 1.204 Hz | −0.4921 cyc | +0.564 / +0.540 |
| ×1.0 (the run above) | 9.5313 | 0.0489 | **0.000 / 0.000 Hz** | −0.002 cyc (parked in-phase) | −0.988 |

Read: at ×0.25 the walk returns with bands **tighter than the surrogate's own**
(0.770 vs 1.018 rad) and a realistic Owaki cadence brake (0.9% vs free-run, growing to
3.4% at ×0.5 — the surrogate's was 3.6%); the stall boundary sits between ×0.5 and ×1.0.
The load channel does exactly what Owaki's equation says it should — it brakes stance
limbs, locks the canonical walk at moderate gain, and halts them outright past the
boundary. The trap in the main experiment is the operating point, not the substrate.
**What the gait line owns next:** re-derive κ (or σ) for the real channel (the ×0.25
point is measured and works), re-measure the G2 bands there, then the G4 ω-sweep — which
now has both things it needs: a load that re-patterns the gait when strong (measured
here: walk → in-phase park across the gain boundary) and a locked walk to start from.
The surrogate's failure mode IS fixed: λ responds to θ (contact windows, L/R asymmetry,
double-peak), it feeds back through the CPG (cadence brake monotone in gain), and the
gait's pattern genuinely depends on it. The one channel that stays weak at this drive is
speed-in-the-load (ω-ladder flat, falsifier iii) — named, with its mechanism.

## Honest gaps

1. **1-DOF + lumped-structural mechanics.** The leg is one hinge DOF with a diagonal
   structural path; the torso is a fixed support; the driver is kinematic. λ is the
   impulse with the leg's own derived inertia (ρ_s = 1, one global scale constant —
   shape and distribution are ρ-free; the gait line re-measures bands with κ-normalized
   N, and σ is CHOSEN-UNVERIFIED anyway).
2. **Saturation.** 83% of contact steps sit at the `min(depth, slop)` clamp because the
   drive presses 5.8× slop deep. The load curve's fine structure in the press windows is
   row-count/lever driven, not depth driven. A re-derived band (or a drive that doesn't
   plunge) un-saturates it — gait line's call, not hidden here.
3. **Edge-crossing contacts.** Plane-crossing pairs with no vertex-face row: 13,201 over
   the 800-step stride (~16/step, concentrated at the deep-press rim and the flexion
   fold). Their bias would clamp at slop anyway; counted, not solved.
4. **The fore oscillators carry N = 0** — no fore contacts exist (no ground interaction
   modeled for the hands, which hang at y ≥ 2.49 and never approach anything). If the
   creature is ever posed quadrupedally (hands down), the same machinery prices their
   rows with zero changes.
5. **H6 extension stops inherited.** See Contradiction 1, item 3.
6. **The walk direction.** The gait drives flexion = foot-posterior about the inter-knee
   axis; with a fixed torso the soles press on the flexing half-cycle. What that means for
   a self-propelling creature is the gait line's question, not G3's.
