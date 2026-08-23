# SESSION LOG 2026-08-23 -- F2-c round 2: honest retrain result + harness diagnosis

Continuing the kernel-native bear (docs/SESSION_LOG_2026-08-22.md, "RUN 34
RESULT + ERRATUM"). Fork-2 official proof (F2-c) in flight. Provenance note:
the LM Studio context limit forced chat restarts this week; every restarted
session re-verifies state from disk first (git log, npz content, .tmp logs)
before writing anything -- the log chain is the durable record across restarts.

## RUN 35 RESULT (honest retrain) + F2-c round-2 referee + diagnosis

**Retrain (RUN 35)** -- done per the pre-authorized RUN 33 procedure
(E=lam=20, mu=10, n_par=152, H=2.0 s, budget 6.0 h; log .tmp/run35_train.log,
gens=55). Best sample reward +0.999878 @ gen 38 (frozen min gap 0.0068 mm),
saved to models/cad_bear/policy_run33.npz with an HONEST label -- the npz's
'reward' is that sample's own measured reward, not a population mean. Eval mode
confirms: "measured reward=+0.9999 (frozen min gap 0.01 mm) vs npz label
+0.9999 (gen 38) -- label verified" (.tmp/run35_eval.log). Provenance preserved:
the mislabeled artifact kept as policy_run33_gen39_mean_mislabeled.npz (copied
before overwrite, 2026-08-22 20:24); npz written 2026-08-22 23:32.

**F2-c round 2 (reference replay of the honest theta)** -- first replay
(.tmp/run35_f2c.log): min gap 2.2 mm @ t=0.55 s, tilt max 59.6 deg, FELL at
t=0.68 s -> FALSIFIER FIRED as written (tilt/no-fall criteria).

**Diagnosis -- the pre-registered successor path ("diagnose the obs channel
mapping FIRST; never retrain to fit")**, .tmp/run35_diag.log + this session:

1. Port-side tick-by-tick of the honest theta: a knife-edge sweep. com_x 59.1 ->
   8.527 mm (t=0.50 s, tilt 17.186 deg -- still inside the corridor) -> 1.993 mm
   (t=0.55 s, tilt 24.366 deg, fallen flag), min gap 0.0068 mm recorded on the
   SAME tick as the corridor violation. The best policy passes X_R exactly as it
   breaches the corridor -- ON THE PORT ITSELF.
2. One real harness bug found and fixed: the reference injection fed the policy
   the CURRENT-tick Fn channels; port BatchBear.obs() sees the PREVIOUS physics
   tick's floor normals (zero at episode start). The pre-registration required obs
   "channel-for-channel as kernel_batch.BatchBear.obs() defines it" -- so this is
   a harness fix, not fitting. Fixed in tools/kernel_walk.py with a lagged Fn_obs
   shadow (zeroed at build, advanced after the policy reads it).
3. Rerun after the fix (.tmp/run35b_f2c.log): reference tracks port row-for-row
   over the whole sweep -- com_x within ~0.1 mm at every 50 ms tick t=0..0.55 s;
   min gap printed 0.0 mm (port: 0.0068 mm); corridor-breach tick t=0.55 s on BOTH
   harnesses; physical fall t=0.72 s. Harness equivalence under control HOLDS --
   no chaotic divergence.

**Verdict.** FALSIFIER FIRED as written (tilt max 63.4 deg > 17.2, fallen=True) --
but its stated interpretation ("port verification does not extend to control") is
REFUTED by measurement: what fired is a bound-calibration artifact. The
pre-registered "trunk tilt <= 17.2 deg over the entire horizon, no fall" was
miscalibrated for this policy class -- the reward (min-gap with freeze on corridor
violation) is gameable by sweep-then-fall, and CMA-ES found exactly such a policy
(+0.999878). That bound can never pass for this theta even with perfect harness
equivalence; transfer itself holds to sub-mm.

**Successor proposal F2-c' (needs pre-registration + operator sign-off -- NOT run):**
corrected referee semantics = harness equivalence under control: reference min gap
within 1 mm of port min gap AND corridor-breach tick equal to the port's fallen-flag
tick. This replay already meets both (0.0 vs 0.0068 mm; t=0.55 s on both). FALSIFIER
for F2-c': gap delta > 1 mm or a different breach tick -> equivalence fails; next
suspect is the remaining channel-for-channel obs diff, never retraining to fit.

**Dyad pending (operator verdict is the gate):** M1 .tmp/packet_bear.png +
M2 .tmp/kernel_stand.png + M3 gait filmstrips (.tmp/kernel_walk_gait.png /
_kernel_walk_gait_side.png, regenerated from the corrected replay) -- the numbers
above are the aligned terms.

## OPERATOR VERDICT (2026-08-23): M3 = FAIL

M3 dyad presented 2026-08-23. Operator verdict: **FAIL** -- "I believe you that it
fell ... that's a fail." The walking milestone does NOT advance on this evidence.
Harness equivalence under control stands proven to sub-mm (that part is solid and is
not re-litigated); what failed is the BEHAVIOR itself: the bear fell. Two distinct
problems are now visible, and they are not the same:
1. Reward v1 is gameable -- min-gap is recorded BEFORE freeze-on-corridor-violation,
   so sweep-then-fall scores +1; falling costs nothing in the objective.
2. Upright transfer is NOT yet proven physically achievable: the hand-designed FSM
   gait (RUN 30/31) ALSO fell (.tmp/run30_gait.log, .tmp/run31_gait.log).
Consequence: next step is NOT "retrain harder" (forbidden retraining-to-fit). Order:
achievability diagnosis as one Rule-0 claim before any training; then reward v2
pre-registration (falling unprofitable), conditional on operator sign-off.

## SUCCESSOR SESSION (2026-08-23): orientation findings + achievability membrane

**Step 1 already landed -- no duplicate append.** The handoff was written at HEAD
b6d000a; disk now carries fe72a89 (the handoff doc itself) and 8599a35, which appended
exactly the required operator-verdict entry above. Verified against disk per protocol;
nothing re-recorded.

**Reconciliation finding (engine store vs git narrative).** `engine_state.json` is a
gitignored RUNTIME ledger (`ChimeraEngine/MCP_ENGINE.md` states this) -- it has no
commit history by design, so "store vs HEAD" is not corruption but two lanes. The
kernel-bear lane NEVER entered the engine store: no term has records except theSeed
(proven via MCP vision proxy, its own graphics lane), `current=theSeed ->
theDeterminism` is where the ENGINE's story lane stands, untouched. Per
`terms_data.py` declarations the walking work maps to **theGait > theStand** ("rest
equilibrium: paws planted" = M2, falsifier record PASSED, operator eyes still
pending) and **theGait > theWalk** ("the stride" = M3, operator verdict FAIL). V61/V62
belong to the grain-rendering lane -- left alone as instructed. Action taken:
this entry IS the reconciliation record. The shared store is not mutated mid-failure;
whether/when the bear chain enters the engine gates (frame() theStand/theWalk) is an
operator call -- the natural moment is when M2 gets operator eyes.

**STEP 3 -- ACHIEVABILITY MEMBRANE (Rule 0, stated before any run).**

Sources read in full: .tmp/run30_gait.log, .tmp/run31_gait.log,
tools/kernel_walk.py docstring (RUN 25--31 pre-registrations + results),
physics prints in both logs.

STATEMENT: An upright transfer IS physically achievable with this physics +
geometry -- but ONLY as a deliberate RELEASE-AND-CATCH dynamic transfer, not the
quasi-static weight shift every failing controller attempted. All three falls share
one structural cause, derived BEFORE any run and confirmed by both control families:
the ankle-centroid channel (lambda = 0.40 rad/s measured, RUN 30) cannot regulate a
MOVING COM (u_ss = D_c - v/lambda dies above v ~ 2.6 mm/s), so holding the transfer
static guarantees the topple the hold is trying to prevent. The FSM died of it
(RUN 30/31 identical traces; RUN 31's PI hold windup-capped at ~10% of need, brake
trigger unreachable on approach / out of scope in the fall); the learned policy died
of the same edge differently (RUN 35 knife-edge sweep, breach tick = pass tick).

THE DYNAMIC BUDGET CLOSES (all numbers from measured constants, closed form):
release at the left sole's inner edge (com_x = 39.5 mm; soles L [39.5, 76.5],
R [-16.5, 20.5], gap 19 mm, x_L=58/x_R=2/hx=18.5 measured) and let the pendulum run.
Transit to the R sole's outer edge: theta = asin(19/157) = 6.95 deg, arrival
v_arr = omega_n*h*sin(theta)/(1-cos... ) closed form = 150.5 mm/s (omega_n = 7.90
rad/s -- matches the build's measured print). The RUN 31 hip brake (a_brake = 1.14
m/s^2 derived, reaction 0.45 N.m vs W*l_fore = 0.50 N.m drain) stops it in
v^2/2a = 9.9 mm -> stop point com_x ~ 10.6 mm: INSIDE the R sole, 27 mm from the far
edge, 4 mm short of com_xt[R] = 14.5 (undershoot side, clause-(b) territory if it
even materializes). Peak tilt through the whole maneuver ~10.6 deg < the 17.2 deg
catchable corridor with ~6.6 deg margin. The hip bandwidth (omega_hr = 20.6 rad/s)
exceeds everything the catch asks. THE KEY UNLOCK: RUN 31's brake never engaged
because its trigger presupposed an arrival speed the lambda-capped channel could
never develop on the approach -- release-and-catch GENERATES that speed deliberately,
so the original speed-dependent trigger becomes reachable IN SCOPE. RUN 31's own
derivation said it first: "the transfer IS a controlled fall"; "THE HIP IS THE
CATCH." The tree died one step short of acting on it.

PREDICTION: a controller implementing release-and-catch (hold upright -> stop
resisting the inward tip at inner-edge crossing -> fire the hip brake + load the far
foot under the speed trigger evaluated EVERY TICK WHILE THE XFER WINDOW IS OPEN)
crosses the first transfer with tilt_T max <= 17.2 deg, majority exit CONTROLLED
(both Fn > 0 within 25% of W), com settling near com_xt[R] +- basin margin.

FALSIFIER (named before any run): if a deliberate-release transfer breaches the
corridor (tilt_T > 17.2 deg) BEFORE majority contact, or overshoots the basin
(com_x past -16.5 mm), or arrives at > 2x the closed-form v_arr (channel dynamics
not following pendulum energy), the dynamic budget above is wrong BY MEASUREMENT and
upright transfer is NOT achievable at THIS geometry. Successor then = gait DESIGN
(build-level FOOT_SEP re-derivation: bigger basin / narrower gap) or physics params
-- NOT reward shaping, NOT policy retraining.

Note the convergence: RUN 35's optimizer independently rode the same boundary --
without a survival incentive it had no reason to CATCH. Reward v2 (survival gate:
zero/negative on ANY corridor violation in horizon, so +1 requires passing X_R AND
staying upright) aligns the objective with the physics this membrane states. The two
fixes compose; neither substitutes for the other.

PENDING OPERATOR SIGN-OFF (gate before any run): (A) proceed to reward-v2
pre-registration + RUN 36 policy training as pre-planned; (B) first spend ONE cheap
hand-authored release-and-catch probe through the existing harness (no training --
minutes, direct falsifier test, reopens the superseded hand lane for one run only);
(C) reject the membrane. Choice recorded here when made.
