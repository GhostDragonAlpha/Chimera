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
