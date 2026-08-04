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

## THE SEATING WAS NOT THE CAUSE — measured, and it corroborates the other agent independently

The foot commit changed **two** things: it added ligaments AND it moved the keyframe, seating
`hip_rotation_r` from **−35.18° to −8.00°**. A 27° change to the starting pose is a large enough
perturbation to explain a survival regression on its own, and the stand θ was fitted to the old
pose — so "one change at a time" says separate them before blaming the tissue.

Survival with the current θ, sweeping only the `hip_rotation_r` start (its legal range is
[−40°, +40°], so every value below is a pose the body may legally hold):

| start | survived | pelvis MIN |
|---:|---:|---:|
| **−8.0° (the new seat)** | **6.24 s** | 46.2% |
| −12.0° | 3.76 s | 47.0% |
| −16.0° | 3.10 s | 45.2% |
| −20.0° | 2.76 s | 46.3% |
| −24.0° | 2.60 s | 48.2% |
| −28.0° | 2.50 s | 44.7% |
| −30.0° | 2.46 s | 49.0% |

**The re-seating HELPED.** Survival is best exactly at the new seat and degrades monotonically
toward the old pose. The hypothesis is refuted: the regression is attributable to the ligaments'
own dynamics, not to the pose change bundled with them.

**AND IT INDEPENDENTLY CORROBORATES THE OTHER AGENT.** That −8° seat is not a range clamp — the
keyframe's −35.18° is *inside* [−40°, +40°], so the range-clamp never saw it. It is the foot
membrane's **off-sagittal deadband**, added when its own falsifier 2 fired: *"a keyframe inside
the range but PAST a ligament's engagement edge starts the body with the spring taut… 113 N·m of
phantom torque at t=0, the 689 N·m defect one level subtler."* This sweep reaches the same
conclusion from the opposite direction — by measuring what the body *does* rather than what the
spring holds — and lands on the same value. Two agents, two methods, one number.

## CORRECTION — "the ligaments' own dynamics" is ALSO wrong. Every new group is load-bearing.

The section above concludes the regression is "attributable to the ligaments' own dynamics, not
the pose change." **A bisect refutes that too.** Dropping ligament groups (by patching only
`derive_ligaments`, so every other line of `load_body` — seating included — runs unchanged) and
measuring survival with the same θ:

| world | tendons | survived |
|---|---:|---:|
| **all 32 ligaments (current)** | 322 | **6.24 s** |
| minus subtalar (4) | 318 | 2.62 s |
| minus hip_rotation (4) | 318 | 2.06 s |
| minus hip_adduction (4) | 318 | 2.00 s |
| minus all 12 new | 310 | 2.44 s |

**Removing tissue makes it far worse. Every new group is load-bearing.** The ligaments are not
the regression; they are holding the body up.

**AND THAT LAST ROW IS NOT THE OLD WORLD**, which is the point worth keeping. It reads 2.44 s
where the *real* 20-ligament world gave >8 s this morning on this same θ — because `load_body`'s
off-sagittal deadband still seats `hip_rotation` to −8° whether or not the ligament exists. So
that row is *the new seat without its spring*: a joint parked at a ligament's engagement edge
with no ligament there. **Seat and tissue are COUPLED and were introduced together; neither is
separable, and a bisect that moves only one of them is measuring a world that never existed.**

The honest statement, with all three hypotheses dead: the world changed as one coupled unit
(tissue + seat), each piece is load-bearing, and the old θ is simply **mismatched to the
combination**. Nothing is broken. The policy is stale, and it is stale in a way no single-factor
story explains.

## FOUR PLAUSIBLE CAUSES, FOUR MEASUREMENTS, FOUR DEAD — the pattern is the finding

1. *"No frontal-plane weight shift"* — refuted: lateral CoM excursion **1582% of requirement**.
   The body was falling sideways, not failing to shift.
2. *"The frozen stand θ pins pitch and forbids the forward lean"* — refuted: pitch runs
   **−18° to −27° mean, reaching −85°**. Nothing was being pinned.
3. *"Grading on the mtp blinded the reward"* — refuted: worst joint **1.233 with the mtp and
   1.233 without**. The lumbar was the offender all along.
4. *"The re-seating broke it"* / *"the ligaments broke it"* — both refuted above, in opposite
   directions, by the sweep and the bisect.

Every one of these was a *good* story that fit the symptom, and every one was wrong. This
membrane has produced more plausible causal narratives than any other on this ladder, and the
only thing that has ever settled one is a number. **Recorded as the finding, because the next
agent here will generate a fifth story and it will also feel right.**

## THE FIFTH HYPOTHESIS, AND IT SURVIVES: the CoM term is judged against the wrong landmark

A 60-turn protected retrain found a genuinely better θ (score −3.438 → −3.098, survival
6.24 → 7.00 s, pelvis 101.9 → 102.4%). **F3's CoM reading did not move: 1.65 peak, outside
16.8% of phase 1, the same window to ±0.02 s.** A policy change that leaves a measurement
identical means the measurement is not about the policy.

`f3_stand` computes the CoM relative to the mean of `calcn_r/l` + `toes_r/l`, then scores it
against `theStance`'s published `bos_half_lat_m` / `bos_half_fore_m`. Measured at reset:

| | actual foot polygon | theStance publishes | ratio |
|---|---:|---:|---:|
| lateral half-extent | 0.1939 m | 0.1020 m | **1.90×** |
| fore/aft half-extent | 0.1109 m | 0.1355 m | 0.82× |

**And the stance is not symmetric.** `calcn_r` (+0.175, +0.059), `calcn_l` (−0.046, −0.165),
`toes_r` (+0.108, **+0.223**), `toes_l` (−0.041, +0.013): the heels are 22 cm apart fore/aft and
the right foot is splayed laterally. The body is standing **twisted and split**, and the
published box describes feet *together* — a different stance entirely.

**THE BAR IS NOT MOVED AND THIS IS NOT A PASS.** Two things are now separable and both are real:

1. *The instrument is comparing a measured CoM to a nominal box that does not describe this
   body's base of support.* At 1.90× lateral disagreement the 1.65 reading cannot be taken at
   face value in either direction — the CoM may be inside the real polygon or outside it, and
   this measurement does not say which. Published as the disagreement it is (rule 17), not
   reconciled by picking whichever number passes.
2. *The body genuinely stands in a twisted, split stance.* That is a finding about the keyframe
   and the seating, not about the policy, and it is the more interesting half: a stand port whose
   feet are 22 cm apart fore/aft is not standing the way `theStance` describes standing.

**What this does NOT license:** swapping the published box for the measured polygon so the term
passes. The measured polygon is *this pose's* footprint — grading a body against its own current
stance is grading it against itself, and the term would then be unfalsifiable by construction.
The right fix is to establish which stance the port is actually meant to hold, and that is a
question for `theStance`, not for this harness.

## CORRECTION TO THE ABOVE, and the resolution: 1.90x was a RESET-ONLY number

The 1.90× lateral disagreement is measured **at reset**, in the twisted keyframe pose. Measured
*over phase 1*, the polygon's mean half-width is **0.1073 m against the published 0.1020 —
1.05×.** The stance normalises within the first samples. The table above is not wrong, but it is
a snapshot of the worst instant quoted as if it described the run, which is the same
peak-vs-sustained error this document has now caught three times in three different places.

With both landmarks measured every sample and printed side by side:

| CoM judged against | peak | outside the support |
|---|---:|---:|
| `theStance.together_*` (published, nominal) | **1.65** | 16.8% of phase 1 |
| the polygon the feet actually make | **0.76** | **0.0%** of phase 1 |

**The body never leaves the base of support its own feet make.** It is physically stable in the
only sense that word has — the CoM projects inside the contact hull at every instant. What it is
*not* doing is standing in the feet-together stance the port's published numbers describe.

**Both are true and they answer different questions**, which is why `f3_stand` now prints both
and `ok_com` still reads the published box. The bar is unmoved. But the open question is now
sharp and small: **`stand_port.py:83` selects `together_half_width_m` out of three stances
`theStance` publishes (`together_` 0.1020, `natural_` 0.1565, `braced_` 0.3932) with no comment
and no stated reason**, in a function where every other line names the membrane it came from.
F3's own falsifier says "the base of support **the feet make**". Those are two different
instruments and the port never said which one it meant.

That is a one-line decision with a real consequence, and it belongs to `theStance`.

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
