# THE LOCOMOTION LANE — ten tasks, each a theory, 2026-08-04

The operator set ten tasks in one lane, each with a **STATEMENT**, a **PREDICTION** and a
**FALSIFIER** named before the run, in the order **1 → 3 → 6 → 2 → 5 → 9 → 4 → 7 → 8 → 10**.
This document is the lane's ledger. A falsifier that fires is a result, not a failure, and every
one that fired is recorded here with the number that fired it.

**THE HEADLINE, AND IT IS NOT WHAT THE LANE EXPECTED.** Four of the first six tasks turned out to
be about **instruments rather than about the body**: two measures were saturated (the joints
penalty, the periodicity), one number was a window's edge reported as a cadence (0.14 s), and one
class of number was the luckiest sample of a distribution (every published stand survival). The
body did not move in any of them. That is the lane's actual finding so far — *the locomotion
work has been reading four broken gauges*, and three of the four had produced published claims.

---

## TASK 1 — THE SATURATED JOINTS PENALTY · falsifier **FIRES**

**STATEMENT.** `stand_reward`'s joints factor is `exp(-(max(0, jmax − 0.8)/0.1)²)` where `jmax`
is the MAXIMUM over 29 graded joints. The max discards 28 of 29; the gaussian is flat at both
ends. Once one joint (`L4_L5_FE` ≈ 1.18) is through its stop the factor is ~0 with ~0 slope, and
it MULTIPLIES the height and support terms, annihilating them too.

**PREDICTION.** Replacing max-then-gaussian with a per-joint hinge summed over joints gives
10-seed median stand survival **> 8 s** and mtp over-stop **< 50%** with no range change.

**FALSIFIER.** Median still ≈ 7 s, or a new joint pinned > 90%.

### The statement is CONFIRMED, and it was measured before anything was changed

`tools/joints_gradient.py`, incumbent policy, 400 control samples, 29 graded joints:

| | retired: max → gaussian | hinge: sum → Lorentzian |
|---|---:|---:|
| joints carrying ANY slope, per sample | **0.99 of 29** | **3.84 of 29** |
| median per-joint slope where `f > 0.8` | **exactly 0** | 1.22e-1 |
| of those joint-samples, slope exactly zero | **74.1%** | 0.0% |
| the factor itself: median / min | 6.6e-3 / **4.2e-7** | 1.11e-1 / 5.8e-2 |

On average **3.1 of the 29 joints are past their stop at any instant** and the retired form could
see one of them. A factor at 4.2e-7 multiplying height and support means every candidate in the
population scored the same ≈ 0: the reward had stopped being a reward.

**The replacement is derived, not chosen.** A joint past its range is resting on capsule and
ligament — the body is held by PASSIVE TISSUE instead of muscle — and strain energy is
**extensive**, so the aggregate over joints is a SUM. The max was a lossy projection of it.
Both constants are unmoved (0.8 where it goes cold, 0.1 the width), so the SHAPE is the single
variable:

```
E   = Σ_j max(0, f_j − 0.8)          extensive, over every graded joint
r_j = 1 / (1 + E / 0.1)              bounded (0,1], never reaching 0
```

`d r_j/d f_j = −(1/w)·r_j²` for every joint past the threshold — the same magnitude for each, so
29 joints carry gradient where one did.

### The prediction FAILED, and the mechanism is upstream of the reward

A/B, both arms warm-started from the incumbent, identical budget / seeds / window / RNG,
differing only in `--joints hinge|retired`:

| | hinge | retired (control) | incumbent |
|---|---:|---:|---:|
| 10-seed median survival | **7.01 s** | **7.01 s** | 7.01 s |
| min / max / spread | 6.30 / 9.08 / 2.78 s | 6.30 / 9.08 / 2.78 s | identical |
| saved θ vs incumbent | **bit-identical** | **bit-identical** | — |

**Neither arm ever beat its own warm start.** Turn 0's best is `cand[0] = mu` — the incumbent —
at −3.864 (hinge) and −3.907 (retired), and across **2,160 evaluations each** (30 turns × 24
candidates × 3 seeds) **not one turn produced anything better**: the best score after turn 0 was
−3.918 and −3.943 respectively. `best_ever` therefore saved the incumbent, and the two arms
handed back the same file they started from.

> **SO THE JOINTS TERM'S SHAPE NEVER GOT TO DECIDE ANYTHING.** The wall is the SEARCH.
> At 1160 dimensions with `sd = 0.075`, every sample of `normal(mu, sd)` is worse than `mu`, so
> the elite mean — four samples, all worse — walks the search's centre *downhill from the
> incumbent on turn 0* and never returns. `cand[0] = mu` (added earlier, for exactly this
> reason) preserves the ARTIFACT but not the SEARCH: it guarantees the best policy cannot be
> lost, and does nothing to stop the distribution it is sampled from being destroyed.
>
> **Every warm-started run in this project is therefore measuring "is the incumbent preserved",
> not "can this be improved".** `agent_logs/elitism_audit.json` checks `has_incumbent` and would
> pass all six trainers; it does not check whether `mu` survives its own first turn.

### The cold A/B — where the search DOES move, and the shape still does not rescue it

A warm A/B cannot test a reward whose search never leaves its start, so the same two arms were
run **cold** (no `--init`), identical budget, identical seeds and RNG:

| | cold hinge | cold retired (control) |
|---|---:|---:|
| 10-seed median survival | **5.06 s** | 4.95 s |
| min / max / spread | 5.00 / 5.12 / **0.12 s** | 4.84 / 5.20 / 0.36 s |
| falls | forward ×7, lateral ×3 | backward ×9, lateral ×1 |
| trainer's own best score | −3.542 | −4.114 |

The control **reproduces the earlier cold run exactly** (`stand_theta_roll_A`: median 4.95,
spread 0.360, backward ×9, lateral ×1 — the same digits), which is what licenses the comparison.

**And the effect is +0.11 s, or +2.2%.** The hinge arm's seed spread is 3× tighter, which is the
kind of thing the derivation predicts, and one training run each is nowhere near enough to call
2.2% a result. Against a prediction of **> 8 s**, both arms are at 5 s.

> **THE JOINTS REPAIR IS KEPT AND IS NOT CLAIMED TO IMPROVE STANDING.** Two separate facts, both
> measured: the retired form was saturated (0.99 of 29 joints, median slope exactly zero) and
> the repaired form does not produce a better stand (7.01 → 7.01 warm, 4.95 → 5.06 cold). The
> derivation stands on its own terms — an extensive quantity aggregated as a sum, with gradient
> where there was none — and the falsifier fired on the prediction. Both sentences are true.

---

## TASK 3 — MULTI-SEED JUDGING BECOMES THE GATE · falsifier **FIRES**, and the reason is the finding

**STATEMENT.** Single-rollout numbers overstate by ~30%, so F3/F4 must headline median-of-10.
**FALSIFIER.** Median-of-10 within 5% of seed 0 on both judges.

Both judges now run ten 1e-6-nudged seeds and headline the median with the min and spread beside
it. And the falsifier **fires on both**:

| judge | quantity | seed 0 | median of 10 | deviation |
|---|---|---:|---:|---:|
| F3 | upright s | 5.00 | 5.00 | 0.0% |
| F3 | pelvis min % | 102.9 | 102.9 | 0.0% |
| F3 | CoM peak | 0.49 | 0.49 | 0.0% |
| F4 | speed | 0.5310 | 0.5311 | 0.0% |
| F4 | periodicity | 0.539 | 0.539 | 0.0% |
| F4 | pelvis min | 0.4024 | 0.4019 | 0.1% |

**WHY: BOTH JUDGES' WINDOWS ARE SHORTER THAN THE DIVERGENCE TIMESCALE.** F3's phase 1 closes at
**5.0 s** and this body does not reach the fall bar until ~7 s, so all ten seeds report `5.00 s`
*because the window ended* — a censored column, measuring the harness and not the body. F4's walk
falls at **1.62 s**, earlier still. The 2.78 s spread `stand_survival.py` measures over 20 s is
real, and it lives past both windows.

> So **F3's and F4's headline numbers were never the ones the coin toss was inflating** — and
> `stand_survival.py`'s 20 s survival was. Measure at the scale the thing lives at (rule 13).
> F3 now detects and names the censoring rather than printing a verdict on a censored column.

**What the ten seeds DID change: the published record.** Every stand survival figure in this
repo was seed 0, and seed 0 is the LUCKIEST of ten — 9.08 s reported against a 7.01 s median,
**+29.5%**. Amended in `CLAUDE_PROMPT_RUNG9.md`, `THE_WALK_PROGRAM.md`, `THE_STEP.md`,
`THE_GRAB.md`, `THE_SLICE.md`; no run withdrawn, every number relabelled as the sample it is.
**And the cold roll A/B reverses under the median**: roll 4.95 s vs no-roll 5.67 s, where single
rollouts had roll ahead.

---

## TASK 6 — RE-MEASURE MTP AFTER TASK 1 · falsifier **FIRES**, and it is answered

**PREDICTION.** Controlled over-stop drops 95–98% → < 50% at unchanged ±30° range.
**FALSIFIER.** Still > 90% → **name which stand-formula term drives it** before further work.

θ came back bit-identical (task 1), so `mtp_angle_l` is unchanged: **peak 1.097, past its stop
97.6% of phase 1**. The falsifier fires, and it obliges the naming. `tools/mtp_drive.py` answers
it with **two independent messengers**, and they agree.

Four muscles have a nonzero moment arm about this DOF — `edl_l`, `ehl_l`, `fdl_l`, `fhl_l`, read
from the model's own moment arms and never from a name match.

**Messenger 1 — the activation ledger** (mean |contribution| over those four muscles):

| block | contribution |
|---|---:|
| **`a0`** (baseline activation) | **0.20233** |
| `kp` · pitch | 0.07641 |
| `kh` · (tgt − z) | 0.02667 |
| `kr` · roll | 0.02392 |

**Messenger 2 — the ablation** (one block zeroed, every other number identical):

| dropped | peak | past stop | Δ | held |
|---|---:|---:|---:|---:|
| (none) | 1.097 | 97.6% | — | 4.98 s |
| **`a0`** | 1.032 | **31.7%** | **−65.9** | 1.62 s |
| `kr` | 1.099 | 74.4% | −23.2 | 2.32 s |
| `kp` | 1.068 | 82.8% | −14.8 | 1.26 s |
| `kh` | 1.093 | 93.3% | −4.3 | 2.08 s |

**BOTH NAME `a0`.** The falsifier for the attribution does not fire: one block drops the
over-stop by more than half and no other moves it by a quarter.

**And the answer carries its own cost, stated rather than hidden.** Removing `a0` also drops
survival from 4.98 s to 1.62 s — the same constant baseline activation is holding the body up
*and* crushing the toe. The torque ledger on the DOF says the muscle supplies 51% of the mean
torque magnitude and the joint's own constraint supplies the reaction (+1.03 N·m mean, 5.60 peak):
nothing else is catching this joint, because `derive_ligaments` refuses an mtp ligament —
theHuman's `gait_envelope_deg` publishes no toe curve. **29% of raw muscle commands are below
zero and clipped away**, which is where a term that wanted to *release* the toe would have to live.

---

## TASK 2 — STRIDE, NOT SHUFFLE · the premise was an instrument artifact

**STATEMENT (as set).** All walk arms show 0.14 s footfall against a 1.17 s derived stride.

**AND 0.14 s IS THE INSTRUMENT'S OWN FLOOR.** `chimera_gait._periodicity` searches lags in
[0.15 s, 2.0 s] and this harness samples at dt = 0.02 s, so its smallest admissible lag is
`max(2, int(0.15/0.02)) · dt` = **0.140 s exactly**. `tools/footfall_spectrum.py` plots the
autocorrelation the measure consumes:

```
lag s   autocorr
 0.02      0.876  #################################
 0.06      0.777  ##############################
 0.10      0.678  ##########################
 0.14      0.579  ######################    <- WINDOW FLOOR, and the reported "period"
 0.20      0.431  ################
 0.30      0.183  #######
 0.38     -0.015
```

It **decays monotonically out of lag 0** — no peak anywhere — which is what a body that falls
over ONCE looks like, and `argmax` over a decaying function always returns the leftmost
admissible lag. So the measure was reporting *"strength 0.579 at a 0.14 s cadence"* for a body
with **no rhythm at all**, and 0.579 reads as 0.021 short of the 0.60 bar.

> **A monotone decay is not a slow rhythm. It is the absence of one.**

`_periodicity` now requires a genuine **interior local maximum** and returns `(0, 0)` when there
is none. No bar moved, no window changed. Verified against known subjects pushed through the
whole instrument: a 0.5865 s metronome returns 0.58 s at strength 0.86, a 1.173 s metronome
returns 1.18 s at 0.78, and a single fall returns **0.0** where it returned 0.579.

**Numbers this retires:** `walk_theta_mult` periodicity **0.54 → 0.00**. The entrained arm's
**0.59 was the same artifact** and was never 0.01 short of anything — which is task 5's premise,
and task 5 inherits this correction.

**So the cadence term is built on touchdown EVENTS, not on the spectrum.**
`walk_port.footfall_interval_s` is the mean time between successive touchdowns of the same foot —
countable from two events, with gradient where a spectral estimate has none — and
`cadence_factor` prices it against the derived floor `0.60 × step_time_s = 0.3519 s`, clipped
(the same shape `walk_reward`'s speed term was rebuilt into, for the same reason: a gaussian is
flat at the bottom). It multiplies into `score_walk_mult` behind `--cadence`, and is **refused**
with `--score sub`, where a factor in [0,1] would make a worse gait score *better*.

**First reading, and it is worse than "a shuffle":** the mult arm's footfall interval is
**0.000 s** — *no foot is planted twice* before the body falls at 1.62 s. The body does not
complete one step cycle. The cadence term is measured on every arm and scored on none by
default, so the control arm reports it too.

---

## TASK 5 — THE ENTRAINED OSCILLATOR, ONE BOUNDED ATTEMPT · falsifier **FIRES**

**PREDICTION.** Periodicity ≥ 0.60 **and** held ≥ 3 s.
**FALSIFIER (either fails).** Record as the measured bound; no objective iteration without a
plant change.

**The premise was the artifact.** Task 5 was set against *"0.59 vs the 0.60 bar"* — one
hundredth short. Under the repaired `_periodicity` the entrained arm's number is **0.39**: not a
hundredth short, a third short. The 0.59 was the monotone decay of a body falling over once.

Retrained once, worst-of-3 randomized starts (`train_walk` gained `--seeds` for this — the walk
trainer had never had the worst-of-N rule the stand trainer got, so the walk was still selecting
initial conditions after the stand had stopped), judged at F4 median-of-10:

| | measured | bar |
|---|---:|---:|
| periodicity | **0.39** | ≥ 0.60 |
| held | **1.52 s** | ≥ 3 s |
| travel | 0.5562 m/s = 56% of derived | 75–125% |

**Both clauses fail, so the falsifier fires and this is the measured bound.** No further
objective iteration on the entrained oscillator without a plant change — recorded as the task
required.

---

## TASK 9 — RE-RUN THE THREE WALK ARMS · the ranking **CHANGED**, and not for the stated reason

**PREDICTION.** The `b288800` ranking (mult 54% > entrained 35% > sub 12%) changes, **or** the
winner's held crosses 3 s.
**FALSIFIER.** Unchanged within noise → the penalty was never walking's constraint.

Four arms, identical budgets (30 turns × 24 pop × 8.0 s, worst-of-3), judged F4 median-of-10:

| arm | travel | periodicity | footfall interval | held | verdict |
|---|---:|---:|---:|---:|---|
| **entrained + mult** | **56%** | **0.39** | 0.000 s | 1.52 s | FAIL |
| mult + cadence | 52% | 0.19 | 1.160 s | 1.78 s | FAIL |
| mult (control) | 51% | 0.17 | 0.570 s | 1.76 s | FAIL |
| sub | 7% | 0.11 | 1.205 s | **2.86 s** | FAIL |

**The ranking changed** — entrained went from last (35%) to first (56%) and now leads
periodicity by more than 2×. The prediction holds and the falsifier does not fire. (`sub`
collapses from 12% to 7% travel while holding the longest of the four at 2.86 s, which is the
subtractive rule doing exactly what `score_walk_mult`'s own Rule 0 said it does: standing still
is a local optimum when the penalties dominate the signal.)

**BUT THE CAUSE IS NOT TASK 1, AND SAYING SO IS THE POINT.** The stand θ came back
bit-identical, so the joints repair changed *nothing* about the walk — it cannot have moved this
ranking. What moved it is the **periodicity repair**: `score_walk_mult` multiplies by
periodicity, and the arms were previously being scored on a number that rewarded a monotone
decay. The entrained arm gains most because it is the only one that establishes anything like a
cycle. Three things changed between `b288800` and this table — the periodicity measure,
worst-of-3 scoring, and the RNG path — and only the first is large enough to explain it. Named
as a confound rather than claimed as a clean attribution.

**Every arm still fails every bar.** The body does not walk. Travel is stuck near half the
derived speed, periodicity is a third of its bar, and nothing survives 2 s.

---

## TASK 2 (continued) — THE CADENCE ARM · the prediction holds, and the term did not earn it

**PREDICTION.** Footfall > 0.4 s. **FALSIFIER.** Stays < 0.3 s → the shuffle is in the plant.

| | footfall interval | % of theHuman's step_time |
|---|---:|---:|
| mult **control** (term off) | **0.570 s** | 97% |
| mult **+ cadence** (term on) | **1.160 s** | **198%** |

**The prediction holds — on BOTH arms, including the one without the term.** The control alone
reaches 0.570 s, within 3% of theHuman's own 0.5865 s step time, so > 0.4 s was not the cadence
term's doing and the term cannot claim it.

**And the term is one-sided, so the search rode it.** `cadence_factor` prices *too fast* and says
nothing about *too slow* — a hole named in its own docstring before the run — and the arm that
optimised it landed at **198% of the derived step time**, nearly two steps' worth of time between
footfalls, while its periodicity (0.19) and travel (52%) stayed level with the control. The
optimiser audited the spec and found the hole, exactly as this studio's trainer notes predict.
The exploit is the product: a cadence term for this port has to be **two-sided about theHuman's
published step time**, not a floor.

**The original premise is retired.** There was never a 0.14 s shuffle to penalise — that number
was `_periodicity`'s window floor, and the real intervals were 0.5–1.2 s all along.

---

## TASK 7 — GUARD THETA-SHAPE DRIFT · prediction **HOLDS**

**PREDICTION.** Saving a 3-block theta trips a loud shape check. **FALSIFIER.** It doesn't.

`parser.py` now DECLARES the contract instead of implying it with `theta.size >= n*nu`:
`STAND_BLOCKS = (a0, kh, kp, kr, kw)` and `STAND_CHECKPOINT_BLOCKS = 4` (`kw` is the *carry*
formula's tendon-organ block, trained by `train_carry`, so a stand checkpoint carrying five
would be claiming a sense it was never trained with). `check_theta_shape(theta, nu, ...)` takes
`nu` **from the model** and refuses a mismatch, naming the terms that would be zero-filled.

**It sits at the SAVE, not only at the load,** because the tolerance is correct in one direction
and wrong in the other: a 3-block theta *read* reproduces the pre-roll formula bit-identically
and that is deliberate; a 3-block theta *written* mints an artifact every future consumer
silently completes. `train_stand` now calls it before `np.save`, so the trainer's pad and the
parser's contract are two parties that must agree before a file leaves.

Wired into the regression sweep as **falsifier 0**, exercised on a synthetic 3-block theta
(never by writing a bad file — an instrument that must create the defect on disk to detect it is
one crash away from leaving it there):

```
[PASS] falsifier 0: the shape guard trips on a 3-block theta: ... theta holds 3 blocks of 290
       = 870 numbers; the parser formula applies 4 (a0, kh, kp, kr)
[PASS] falsifier 0b: the guard accepts the real checkpoint: 4 blocks x 290 = 1160
[PASS] falsifier 1: parser stand == the 4-block formula, bit-identical: 0.000e+00 over 405 samples
```

Falsifier 1 — the parser's headline claim — **runs again**, over 405 samples. It had been
un-runnable since the roll block landed.

---

## TASK 8 — STANCE-PICK DECISION SUPPORT · the unjustified pick is **CORRECT**

`stand_port.py:83` picks `together_half_width_m` (0.1020 m) over `natural` (0.1565) and `braced`
(0.3932) with no stated reason. Measured: one set of ten 20 s rollouts, scored five ways (the
stance is a **judging landmark** — it changes nothing in the plant, so survival is identical
across every row by construction and is printed once rather than five times pretending to
compare).

Survival, common to every row: median 7.01 s, min 6.30, max 9.08, spread 2.78 s.

| base of support | half-width m | CoM peak | % outside |
|---|---:|---:|---:|
| **together (the pick)** | **0.1020** | 8.16 | 15.2% |
| natural | 0.1565 | 5.32 | 12.4% |
| braced | 0.3932 | 2.12 | 6.2% |
| foot-origin spread *(measured)* | 0.0967 | 10.21 | 15.5% |
| **CONTACT polygon** *(measured)* | **0.1015** | 28.31 | 15.8% |

> **THE MEASURED CONTACT POLYGON IS 0.1015 m AND `together` IS 0.1020 m — A GAP OF 0.5 mm.**
> theStance's own grain is one foot breadth (0.1020 m, the number every stance width it
> publishes is built from), so the falsifier fires: `together` **is** the measurement, and the
> pick was right. Every landmark also returns the same in/out verdict on every seed, so nothing
> measurable was ever at stake between them.

**RECOMMENDATION for the operator to sign.** Keep `together_half_width_m`, and record it as
**measured** rather than picked: the contact polygon this body actually stands on matches it to
0.5%. State the reason at `stand_port.py:83` so the next reader does not re-open it. *(Do not
adopt the foot-origin spread: those four points are body FRAMES inside the feet and know nothing
about how wide a foot is, so they understate the polygon by construction — it is in the table
only because `f3_stand` prints it today.)*

The CoM-peak column is inflated for the measured rows by the post-fall period, when contacts
shrink toward a point and the denominator collapses; the half-width medians are unaffected
because they are dominated by the standing phase. Named rather than trimmed.

---

## TASK 4 — MEASURE THE BACKWARD FALL · prediction **HOLDS**, 9/10

**STATEMENT.** `kp·pitch` overcorrects once the lateral escape is gone.
**PREDICTION.** CoM exits the posterior edge in ≥ 7/10. **FALSIFIER.** Exits distributed.

Arm A (`stand_theta_roll_A`), ten seeds, exit edge read against the **contact polygon**:

| edge | seeds |
|---|---:|
| **posterior** | **9/10** |
| left | 1/10 |

Pitch at exit: median **−14.1°** (leaning back), range −14.3…−13.9° across the nine — a tightly
clustered mechanism, not a scatter. The single outlier is seed 8, which `classify_fall`
independently labels *lateral*. **The falsifier does not fire**: the exit has one mechanism and
`kp·pitch` driving the body out the back is the reading the measurement supports.

### And the instrument had to be repaired twice to say that

**First: the exit is not the fall.** The CoM leaves at median **3.85 s** and the pelvis crosses
the fall bar at **4.95 s** — 1.10 s of toppling *after the outcome was decided*. An edge read at
the fall bar reads the landing.

**Second, and this one reverses the sign:** pitch at the fall bar is **+15.2°** — *forward* —
while pitch at the exit is **−14.0°**, backward. The body leaves backward and rotates forward as
it collapses. **Any measurement taken at the fall instant would have named the wrong mechanism**,
with a confident number and the wrong sign.

**Third: the FIRST exit is not the fall either.** It lands at t = 0.02 s, the first control tick,
on every single seed — because only the **heels** are loaded at the keyframe, so the polygon's
front edge *is* the heel line and a CoM 4.9 cm ahead of it reads "outside". `f3_stand` already
carries this finding from the other direction. The measurement therefore reads the **committed**
exit: the last inside→outside crossing never recovered from. Everything before it was recovered
from, by definition, and a body that recovers has not fallen out of anything.

---

## TASK 10 — THE GRAB LOAD PATH · falsifier **does NOT fire**, and two of three clauses fail

Task 10 was conditional on locomotion stalling. **It has stalled**: every walk arm fails every
bar, and no stand search improves on its own warm start. So the load path is live.

**PREDICTION.** (a) sag LINEAR in carried mass, r² ≥ 0.90; (b) `k_eff` calibrated on a known
vertical PELVIS force predicts the welded stone's sag out of sample within 2×; (c) 10-seed
median stand survival is shorter loaded than unloaded.
**FALSIFIER.** No measurable load effect → the load path is decorative.

The stone is **59.49 kg → 420.97 N, 72.5% of the 82.04 kg body.** Grab at 2.0 s over the port's
own 0.5 s arrival window, release at 5.0 s, 10 seeds.

### The falsifier does NOT fire — the load path is real

| | value |
|---|---:|
| unloaded pelvis, settled window | 0.95992 m |
| unloaded seed-to-seed jitter | **0.05 mm** |
| loaded sag vs that control | **2.57 mm** (min 2.53, max 2.60) |
| ratio to the jitter | **50×** |
| weld load over the carry | **+0.886** of the stone's weight |
| survival, unloaded → loaded | **7.01 s → 3.44 s** |

The body feels 89% of the stone's weight through the weld, sags 50× its own jitter, and loses
half its stand. **Clause (c) holds.** Nothing decorative about it.

### And clauses (a) and (b) both fail, for one coherent reason

**The calibration is clean and the stone is not:**

| pelvis force N | sag mm | k N/m |
|---:|---:|---:|
| 105.24 | 5.53 | 19,037 |
| 210.48 | 14.77 | 14,255 |
| 420.97 | 39.77 | 10,586 |

| carried stone kg | weight N | sag mm | weld load |
|---:|---:|---:|---:|
| 14.87 | 105.24 | 2.60 | 0.937 |
| 29.75 | 210.48 | 4.73 | 0.823 |
| 44.62 | 315.72 | 3.29 | 0.934 |
| 59.49 | 420.97 | 2.57 | 0.886 |

> **A vertical force at the pelvis sags the body in proportion to itself. A stone of the same
> weight, welded to the torso, does not.** The sag is FLAT across a 4× mass range — r² **0.038**,
> slope faintly *negative* — and `k_eff` over-predicts the stone's sag by **11×** (29.53 mm
> predicted, 2.57 mm measured, 0.09×).

**PUBLISHED, NOT RECONCILED (rule 17).** The two failures are one fact: **the stone's load is
not a vertical load.** It hangs 0.40 m forward of the torso, so it arrives as a PITCHING MOMENT,
and the body answers it in the channel that has a moment to give — `kp·pitch` — not in the
height channel the sag measures. Pelvis sag is therefore the wrong observable for carried mass;
it reports the small vertical residual and says nothing about the load that is actually
toppling the body. That is why survival halves while the sag barely moves.

**And the calibration refutes the derivation's own premise on the way past.** `k` falls
19,037 → 14,255 → 10,586 N/m as the probe grows: the stand's height channel is a **softening**
spring, not the proportional one the statement assumed. `dz = W/k_eff` was never going to hold
even in the direction it was calibrated.

### Two instrument defects had to be fixed before any of this could be said

1. **The window ran past the fall.** At full mass the body falls *during* the carry (0/10 seeds
   reach the release), so a mean over `[grab+ramp, release]` averaged a collapse and called it a
   sag — the first run reported 109.86 mm, which is the body going down, not a spring. The
   measurement now takes the first 0.20 s after arrival and returns `nan` rather than a number
   when the body was not there for it.
2. **`mj_setConst` overwrote the state.** It recomputes model constants *for the qpos0
   configuration* and uses `d` as scratch. Called after the keyframe reset, the stone spawn and
   `seat_in_limits`, it silently threw all three away and started the body from qpos0 —
   unseated, outside its own joint limits. **Caught by a control, not by reading:**
   `mass_scale=1.0` — the *same* mass the unscaled path uses — survived 1.64 s where
   `mass_scale=None` survived 3.44 s. Identical physics, different survival, so the difference
   was in the call. Every mass-response row was `nan` until it was moved before the reset.

---

## THE LANE'S CLOSING NOTE

**Ten tasks; four falsifiers fired, four predictions held, and the falsifiers were the
informative half.**

| task | verdict |
|---|---|
| 1 joints penalty | statement CONFIRMED, prediction **FIRES** — and the wall is the search, not the reward |
| 3 multi-seed judging | **FIRES** — both judges' windows are shorter than the divergence timescale |
| 6 MTP re-measure | **FIRES**, and the naming it obliges is answered: `a0`, by two agreeing messengers |
| 2 stride-not-shuffle | premise was an instrument artifact; prediction holds on the *control* too, and the term is exploitable |
| 5 entrained oscillator | **FIRES** — 0.39 and 1.52 s against 0.60 and 3 s. The measured bound. |
| 9 three walk arms | ranking CHANGED (entrained 35% → 56%) — but the cause is the periodicity repair, not task 1 |
| 4 backward fall | **HOLDS** 9/10 posterior, −14.1° exit pitch |
| 7 theta-shape guard | **HOLDS** — trips on a 3-block theta, and falsifier 1 runs again after being dead |
| 8 stance pick | the unjustified pick is **CORRECT** to 0.5 mm |
| 10 GRAB load path | falsifier does NOT fire; (a) and (b) fail on one coherent fact — the load is a moment, not a weight |

**WHAT THE LANE ACTUALLY FOUND.** Not one of the ten tasks moved the body. Six of them moved an
*instrument*, and three of those instruments had already produced published claims: a survival
figure that was the luckiest of ten, a periodicity that rewarded a body falling over once, and a
cadence that was a search window's floor. **The locomotion work has been reading broken gauges,
and the gauges all read optimistic.**

**THE ONE OPEN THING THAT BLOCKS THE REST.** `train_stand`'s warm-started CEM cannot improve on
its own start at 1160 dimensions — 2,160 evaluations, zero improvements, a bit-identical file
back. `cand[0] = mu` guarantees the incumbent survives; nothing guarantees the *distribution*
does, and the elite mean walks off the incumbent on turn 0. Until that is fixed, **no warm-start
experiment in this repo can test anything**, because the answer is "the incumbent was preserved"
whatever the change was. `agent_logs/elitism_audit.json` checks `has_incumbent` and would pass
all six trainers. That is the next Rule 0 to write, and it is a SEARCH membrane, not a reward one.
