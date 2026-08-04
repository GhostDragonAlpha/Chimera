# THE WALK PROGRAM — walking composed over the stand port

> Membrane stated 2026-08-04 in `tools/walk_port.py`'s docstring, before the build. This is the
> verdict. **F4 FIRED.** Falsifier 3 fired by its own letter, and the run says precisely what is
> missing, which is the whole point of naming it in advance.

---

## RULE 0 — the theory, as stated before anything was built

**STATEMENT.** Walking is not a new controller. It is the STAND port's own formula plus ONE
phase-oscillator term, ω = 2π/(2·`step_time_s`) read from theHuman and never chosen. No joint
angle is commanded anywhere: the parser sends a button, the button's formula sends muscle
activations, and the gait is what the body DOES.

**PREDICTION.** speed within 25% of `comfortable_speed_ms` = 0.9924 m/s · periodicity ≥ 0.60 ·
pelvis ≥ 80% of the stand target for the whole run · AND the ablation (oscillator amplitudes
forced to zero) travels under 20% of that speed.

**FALSIFIER.** 1. speed reached but periodicity < 0.60 (it *arrives* without walking).
2. the ablation travels too (the rhythm is decorative). 3. **the body cannot reach 50% of the
derived speed at any trained setting — the composition is insufficient.**

---

## THE VERDICT: FIRED on falsifier 3

`python tools/f4_walk.py` — exit 1. Judged at 6 s; trained at 8 s (train past what you judge —
the rule the stand port earned hours earlier).

| # | measured | bar | verdict |
|---|---|---|---|
| 1 TRAVEL | **+0.158 m/s = 16%** of derived | 75–125% | FAIL |
| 2 PERIODICITY | **0.13**, period 0.88 s vs derived stride 1.17 s | ≥ 0.60 | FAIL |
| 3 UPRIGHT | pelvis MIN 50% of target, **held 2.98 of 6.0 s** | ≥ 80%, full run | FAIL |
| 4 ABLATION | oscillator off: **−0.012 m/s = −1%** | < 20% | **PASS** |

**Falsifier 3 fires: 16% sustained, and the best any trained setting reached while still
upright was ~51% for 2.3 s before falling.** Said plainly rather than patched with a
joint-angle target, which is what the falsifier existed to prevent.

## BUT THE MECHANISM WORKS — and the picture says so where the verdict line cannot

`ChimeraEngine/output/ports/f4_walk.png`. **The body walks for about 2.5 seconds and then falls.**

- **UPRIGHT** — the pelvis holds **0.92–0.98 m, at or ABOVE the 0.9201 m stand target**, from
  t=0 to t≈2.5 s. It is not crouching to move.
- **TRAVEL** — flat to t≈1.4 s, then climbing steadily to ~0.5 m by t=3.0 s: **≈0.31 m/s in that
  segment**, and still accelerating when the body goes down. The ablation trace is flat at zero
  underneath it for the full 6 s.
- **FOOTFALL** — R and L visibly ALTERNATE, ~0.9–1.0 s per cycle against the derived 1.17 s stride.
- **DUTY** — R/L 0.68/0.55 against theHuman's published **0.60**. Neither was trained toward;
  duty is an output here.

**THE BINDING FAILURE IS DURATION, NOT MECHANISM.** Every ingredient of a gait is present and
measurable; none of it survives past ~3 s.

**AN HONEST CAVEAT ON NUMBER 2, which does not excuse it.** `_periodicity` searches lags
0.15–2.0 s, and the run truncates at 3.0 s when the body falls — about 2.5 cycles of a 1.17 s
stride. An autocorrelation cannot resolve a period it sees twice. So 0.13 is a *fell-over*
reading as much as an arrhythmia reading, and the two are not separable until the body stays up.
The failure is still the failure: it fell.

---

## THE DEFECT FOUND AND FIXED EN ROUTE — the port's conclusion is not the port

The first implementation set `phi_r = omega*t`, `phi_l = omega*t + pi`. Two things were wrong
with that, and the second is fatal:

1. **It asserted the `phase_oscillator` port's RESULT instead of running the port.** Port 12
   proves that *coupling* — `dφ/dt = ω + ε·sin(φ_other − φ − π)` — converges to antiphase while
   the uncoupled control does not. Hardcoding antiphase means the validated mechanism is absent
   and only its output is imitated.
2. **It was an open-loop clock.** `ω·t` cannot know whether a foot is loaded, so it commands a
   swing while that leg is still carrying the body. This is a direct violation of the control
   law this project already states — *command the PROCESS and its STOP CONDITION; every atom is
   `apply effort → stop when a sensor says stop`.* A clock has no sensor, therefore no stop.

Replaced by `WalkOscillator`: port 12's coupling law, plus **contact entrainment** — a rising
edge on a foot's plantar sensor is stance onset, and that leg's phase is *pulled* toward 0
(pulled, not snapped, so one noisy contact cannot restart the gait). ε and κ are free numbers,
trained; ω and the antiphase target remain derived.

**MEASURED, open-loop → closed-loop, same 30 turns × pop 32 × 8 s:**

| | open-loop clock | contact-entrained |
|---|---:|---:|
| best score | −4.005 | **−3.674** |
| held before falling | ~3.7 s plateau | **4.5–5.3 s** |
| periodicity | 0.26–0.36 | **0.40–0.49** |
| duty R/L | 0.64 / **0.14** | 0.74 / **0.60** |

The duty row is the one that matters: open-loop, the left foot was on the ground **14%** of the
time — the body was standing on its right leg and waving the left. Closed-loop, the legs share
the load. **The sensory stop condition is what made two legs into a pair.**

## A HYPOTHESIS THAT WAS MEASURED AND REFUTED, recorded so nobody re-derives it

The collapse looked like a missing frontal plane: `OSC_JOINTS` are all sagittal (hip flexion,
knee, ankle), and `stand_port.draw_bones`' own docstring predicts exactly this failure — *"ONE
centre of mass is carried by TWO hips 0.162 m apart… a body that cannot decide which leg is
carrying it is a body that falls over — which is exactly what the walker does at 3.12 s."* Mine
fell at 3.7 s. The story fit perfectly.

**It is wrong.** Measured lateral CoM excursion over 4 s: **1669 mm peak-to-peak against the
~106 mm a step needs — 1582% of requirement.** The body is not failing to shift weight
laterally; it is falling sideways, and the excursion is a *consequence* of the fall. Adding a
hip-adduction oscillator term would have been a fix aimed at a symptom that does not exist.

## WHAT IS ACTUALLY MISSING — the next membrane's question

The body stands (F3 PASS, 102.3% of target, 5 s), and it walks for 2.5 s. What it cannot do is
*keep* walking. Two candidates, and the honest position is that neither has been measured yet:

1. **The stand θ is frozen and was trained to stand STILL.** Its feedback is pelvis height and
   pitch — it has no term for a moving base, and F3 already showed it holds position by hanging
   on joint stops (`subtalar` 60.8%, `mtp` 97.6% of phase 1 past their limits). A posture that
   braces against its own stops is exactly the posture that cannot absorb a step.
2. **There is no swing-terminating stop condition.** Contact entrains the phase, but nothing
   ends a swing when the foot arrives — the same defect one level down.

**Rung 1's leftover is a prerequisite here, not a coincidence.** The joints holding this body up
are the ones with no derived ligament (subtalar, mtp, hip rotation/adduction — theHuman
publishes three sagittal envelopes and nothing else). Standing on stops is survivable; walking
on them is not, because a stop is a rigid constraint and a step needs compliance. **The passive
tissue membrane named at the end of `docs/THE_TRUNK_TISSUE.md` is very likely the missing rung
under this one** — which is a prediction, and it is written down before that work is done so it
can be wrong.

---

# AMENDMENT — two agents in one lane, and the defect that found

Written after `tools/walk_port.py` and `tools/train_walk.py` were taken over mid-run by the
other agent working this list (Kimi Code CLI). Recorded rather than argued, because the finding
it made is correct and the evidence it deferred is measured and would otherwise be lost.

## THE DEFECT IT FOUND IN THIS WORK, and it is real

> *"the trainer drove the ENTRAINED oscillator while the judge drives the CLOCK. Two of the
> eight trained numbers were dead at judgment and the entrained gait was never judged at all."*

**Correct.** When `WalkOscillator` was added to `train_walk.evaluate`, `move_formula_fn` — the
path `f4_walk` reaches through the parser — still computed `phase = omega*t`. So `eps` and
`kappa` were optimised against a plant the judge did not run. It is *"train past what you
judge"* one level deeper than where that rule was earned this morning, and it is the same
species as every other defect on this page: **a number that is alive in one instrument and dead
in the other, with nothing raising.**

Its resolution — make the trainer drive the judge's plant exactly, revert to the clock, and
defer entrainment to its own membrane with its cost stated — is the correct call and stands.
This document does not re-litigate it.

## THE EVIDENCE THE DEFERRAL SHOULD CARRY WITH IT

The deferral is recorded without the number that motivates it, so it is recorded here. Same 30
turns × pop 32 × 8 s, same world, same frozen stand θ — only the phase source differs:

| | open-loop clock | contact-entrained |
|---|---:|---:|
| best score | −4.005 | **−3.674** |
| held before falling | ~3.7 s plateau | **4.5–5.3 s** |
| periodicity | 0.26–0.36 | **0.40–0.49** |
| duty R/L | 0.64 / **0.14** | 0.74 / **0.60** |

**The duty row is the whole argument.** Open-loop, the left foot was on the ground **14%** of
the time: the body stood on its right leg and waved the left. Entrained, the legs share the
load and duty lands on theHuman's published 0.60 without being trained toward it. That is not a
robustness nicety — it is the difference between two legs and a leg plus a pendulum.

**AND THE CAVEAT THAT CUTS THE OTHER WAY, stated so this table cannot be quoted as a verdict:**
those entrained numbers were produced by the trainer alone. By the defect above, *no entrained
gait has ever been judged.* The table is evidence that entrainment moves the mechanism metrics;
it is **not** evidence that an entrained walk passes F4, because that measurement does not exist
yet. Whoever takes the deferred membrane has to make it.

## A MEASUREMENT MADE AND THROWN AWAY, recorded so it is not re-quoted

After the takeover, the 8-number entrained θ was evaluated through the rewritten (clock)
`train_walk.evaluate` and returned −34% travel, held 2.24 s. **That number is meaningless** —
it is a θ trained on one plant scored on another, with two of its numbers silently ignored: the
same mismatch, running in the opposite direction. It is written down only because a plausible
number with no valid comparison behind it is exactly the kind of thing that survives into a
later summary as though it meant something.

## THE SWING INTERLOCK, unjudged and derived

A second structure was built and never judged before the lane changed hands, so it is specified
here rather than claimed. `theHuman` publishes `duty_factor = 0.6027`. A duty above 0.5 is not a
preference — it is what makes a gait a WALK rather than a run: two feet at 60% each is 120% of a
cycle's contact, so at every instant at least one foot is down and **both feet are never
airborne.** The measured failure is exactly the one that arithmetic forbids: the body leaves the
ground and falls at 2.5–4 s.

So: *a leg may not enter swing while the contralateral leg is unloaded* — effort applied until a
sensor says stop, the control law one level below where `WalkOscillator` applies it. Gated on the
**swing half only** (`s > 0`); gating the stance half too would tell a foot in double support to
stop supporting, and the interlock would cause the fall it exists to prevent.

Early signal only, and it is not a result: the interlock reached −3.797 in **4 turns** where the
entrained-only version needed 19 to reach −3.674. It was never carried to a judgment.

---

# THE FOOT MEMBRANE LANDED, AND IT REGRESSED THE STAND PORT (2026-08-04, later)

**A membrane closed its own falsifier and broke a neighbour's.** This is the composition failure
the ladder exists to catch, and neither agent could see it alone: the foot/hip membrane was built
and validated against its own bars, and the regression is only visible from the port above it.

## What the ligaments fixed — exactly what they were derived to fix

The world went from **20 ligaments to 32** (subtalar 333/243, hip_rotation 59/239, hip_adduction
694/444 N·m/rad, both sides). Against F3's offender list before and after:

| joint | before | after |
|---|---|---|
| subtalar_angle_r | 1.16, over 60.8% of phase 1 | **gone from the list** |
| hip_rotation_l | 1.02, over 81.6% | **gone** |
| hip_adduction_l | 1.05, over 91.6% | **gone** |

The derivation did its job. Nothing below is an argument against it.

## What it cost, measured

**`f3_stand` regressed from PASS to FAIL.** Pelvis is untouched (101.9% of target) — the failure
is the CoM term, which had been *fixed* that morning:

| | 20-ligament world | 32-ligament world |
|---|---:|---:|
| CoM excursion, peak | **0.80** | **1.65** |
| CoM outside the BoS box | **0.0%** of phase 1 | **16.8%** (t=1.70–2.52 s) |
| F3, the slice's letter | **PASS** | **FAIL** |

And the cause underneath it — survival, measured on the same θ at four horizons:

| training horizon | survived | pelvis MIN | score |
|---|---:|---:|---:|
| 5.0 s | 4.98 s | 101.9% | **+0.003** |
| 6.0 s | 5.98 s | 85.0% | +0.002 |
| 8.0 s | **6.24 s** | 46.2% | **−3.438** |
| 12.0 s | 6.24 s | 46.2% | −3.958 |

**The body now falls at 6.24 s.** It used to hold past 8. So the 8 s training horizon — correct
by the "train past what you judge" rule — puts *every* candidate past the fall, the −3.0 penalty
saturates, and the search can discriminate only on fall-time, never on posture. Two retrains
(24 and 20 turns) found nothing better than the incumbent. The walk training over the same
foundation plateaued at −3.673 for the same reason: **walking is composed over standing, and
standing regressed.**

## TWO CLAIMS I MADE AND THE MEASUREMENT KILLED — recorded, not quietly dropped

1. **"Grading the policy on the mtp is what blinded the reward."** The mtp is pinned at 1.11
   permanently and its model stop contradicts the published envelope, so excluding it from the
   graded set looked like the principled fix. **Measured: worst joint 1.233 with the mtp and
   1.233 without it** — the actual worst joint is the LUMBAR. The edit would have changed
   nothing and I would have believed it did.
2. **"The reward has gone dark."** Overstated. `stand_reward` is evaluated per sample, so
   `r_joints` is ~1.8e-2 at jf≈1.0, attenuated but not zero. The score is dominated by the
   **fell penalty**, not by a saturated joints term. The distinction matters: the first story
   says fix the reward, the second says the body genuinely cannot stand as long as it used to.

## THE SEARCH DEFECT THIS EXPOSED, and it is fixed

`train_stand`/`train_walk` warm-start by setting `mu` to a known-good θ and then scoring only
`rng.normal(mu, sd)` samples — **the mean itself was never evaluated.** At 870 dimensions every
sample is far from mu, so a warm start could end strictly WORSE than not training at all. It
did: seeded with the θ that stands at 101.9%, a 24-turn warm start opened at 48% and never
recovered, and it overwrote the good θ on disk.

`cand[0] = mu` now carries the incumbent into every generation. This is not a tuning knob — it
is a correctness property of the search (*the best known policy cannot be lost by looking for a
better one*), and it costs one evaluation per turn. With it, the 20-turn retrain returned the
incumbent unchanged instead of a ruin.

## A STALE COMMENT THAT WAS A WRONG NUMBER

`CTRL_EVERY = 20  # 40 ms at the model's 0.002 s timestep` in both `f3_stand.py` and
`train_walk.py`. **Measured `m.opt.timestep` = 0.001** — the control cadence is 50 Hz, not the
25 Hz every docstring asserted. Nothing computed from it was wrong (every consumer multiplies by
`m.opt.timestep` rather than a literal), which is exactly why it survived: a wrong number under a
formula that still reads plausibly is invisible until someone prints it.

## WHAT THIS MEANS FOR THE ORDER OF WORK

The stand port must be re-established in the 32-ligament world before the walk means anything —
walking is composed over standing by construction, so a stale foundation makes every walk number
unattributable. **And the retrain cannot simply be re-run harder:** 44 turns across two attempts
found nothing better than a θ that falls at 6.24 s. Either the postural policy needs a search
that can see past the fell penalty, or the new tissue genuinely made standing harder and the
stand port's own derivation needs revisiting. **That is the next question, and it is not
answered here.**

## WHAT LANDED, and stands on its own

- `tools/walk_port.py` — the port (ω, stride, duty, target speed, all derived; `speed_closure_pct`
  **0.000000** — theHuman's `step_length/step_time` reproduces its published comfortable speed
  exactly, checked rather than assumed), the measured muscle groups (L/R symmetric: 18/22 hip,
  12/10 knee, 3/8 ankle), `WalkOscillator`, and the MOVE formula.
- **MOVE IS NO LONGER A REFUSAL.** `tools/parser.py` registered it as *"no trained formula — its
  atoms are M3 (STEP+PLANT+BALANCE)"*. F4 runs with `parser driver: MOVE`, composed so STAND
  lives *inside* MOVE's formula rather than beside it (the parser's EXCLUSIVE rule would
  otherwise give STAND the parse and MOVE would silently never run).
- `tools/train_walk.py` — CEM over **8 free numbers with the 870-number stand θ FROZEN**. That
  freeze is what makes "composed over standing" a fact about the file rather than a claim in a
  document: if walking required re-training the postural policy, the composition would be a
  fiction and this file could not hide it.
- `tools/f4_walk.py` — the harness, with the ablation as *the same code path* (`gain=0.0` inside
  `walk_formula`), so it cannot drift away from the thing it ablates.
