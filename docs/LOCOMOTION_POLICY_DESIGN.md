# THE LOCOMOTION POLICY CLASS — what it is, what it assumes, and what nobody has measured

> **This is the document every subsequent locomotion experiment cites.** It records what the
> policy class IS, what it ASSUMES, what has been MEASURED, and what is UNTESTED — so the next
> Rule 0 is stated against facts rather than against a summary of a summary.
>
> Written 2026-08-04, at the point where the search wall closed. The lane before it
> (`docs/THE_LOCOMOTION_LANE.md`) eliminated two of three explanations for *"the stand cannot be
> improved"*: the reward was saturated (repaired, no effect) and the search could not move
> (repaired in three places, **+1.2% on held-out survival**). **The policy class and the
> objective are what is left.**

---

## 0. FOUR CORRECTIONS FIRST, because this document exists to stop them recurring

Every one of these was in circulation as a premise for new work, and every one is wrong against
the code. They are listed before anything else because a design document that inherits them is
worse than no document.

| claimed | actual | why it matters |
|---|---|---|
| *"the policy is `u = θ·[h, ḣ, θ, θ̇]`"* | **there is no `ḣ` and no `θ̇`** — the obs is `{z, pitch, roll}` and nothing else | the policy is **purely proportional**. It has *no derivative feedback at all*, which is a more basic gap than the absence of phase or memory |
| *"four scalars"* | **1160 numbers** — 4 blocks × 290 muscles, one gain *per muscle per channel* | an experiment that "extends theta from 4 to 6" would actually be 1160 → 1740; the search-cost and basin arguments all scale with this |
| *the judge lives in `tools/stand_port.py`* | `stand_port.py` derives the target and draws the bones. The judge is **`tools/stand_survival.py`**; F3 is `tools/f3_stand.py` | — |
| *an "MTP-widened theta" exists to re-judge* | **it does not.** `agent_logs/mtp_ab.txt` is a log of an A/B; no such artifact was saved | any task asking to re-judge it has nothing to load |

Two more path facts: this repo's gait code is **`tools/chimera_gait.py`** (there is no
`core/gait.py`), and the elitism audit is **`tools/elitism_audit.py`** (not `core/trainables/`).

---

## 1. WHAT THE POLICY CLASS IS

One function, and this is all of it (`tools/parser.py`, `stand_formula_fn`):

```python
u = clip(a0 + kh·(tgt − z) + kp·pitch + kr·roll [+ kw·F], 0, 1)
```

| | |
|---|---|
| **inputs** | `z` (pelvis height, m), `pitch` (sagittal lean, rad), `roll` (frontal lean, rad). **Three scalars.** `kw·F` is the *carry* formula's weld-load block, trained by `train_carry`, absent from a stand checkpoint |
| **parameters** | `a0`, `kh`, `kp`, `kr` — each a **290-vector**, one gain per muscle. **1160 numbers.** |
| **output** | 290 muscle activations, clipped to [0, 1] |
| **state** | none. `u_t` is a function of the instantaneous observation only |
| **cadence** | 50 Hz (`CTRL_EVERY = 20` × 1 ms timestep) |

**It is a static, memoryless, proportional map from three scalars to 290 activations.** The
declared block contract is `parser.STAND_BLOCKS` / `STAND_CHECKPOINT_BLOCKS = 4`, enforced at
save by `parser.check_theta_shape` and in the regression sweep by `parser_tests` falsifiers 0,
0b and 0c.

---

## 2. WHAT IT ASSUMES

Each of these is a real commitment the form makes. None has been tested.

1. **That standing is a linear function of three instantaneous scalars.** No `ż`, no `pitch̊`,
   no `roll̊` — so the controller cannot distinguish *"leaning forward and returning"* from
   *"leaning forward and accelerating"*. It sees position and answers with force; a body already
   moving gets the same command as one at rest in the same pose. **This is a proportional
   controller with the D term missing**, and the standard reason a P-only controller on a second
   order plant oscillates and eventually diverges is exactly that.
2. **That one gain per muscle per channel is the right factorisation.** 290 muscles are known to
   live on ~16 synergies for this body (`ChimeraEngine/synergy.py`: 8 dims = 91% of movement,
   16 = 96%), so 1160 free numbers may be describing a ~64-dimensional thing with 18× redundancy
   — which is also the direct cause of the basin being 10⁴ times narrower than a naive step.
3. **That the clip is harmless.** Measured: **29% of raw muscle commands are below zero and
   clipped away** at the toe (`tools/mtp_drive.py`). Nearly a third of the command vector is
   being discarded, and any term that wanted to *release* a muscle has nowhere to live.
4. **That `a0` is a baseline and the gains do the work.** Measured, at the toe: `a0` contributes
   0.202 mean |activation| against `kp` 0.076, `kh` 0.027, `kr` 0.024, and ablating `a0` drops
   the over-stop from 97.6% to 31.7% *and* survival from 4.98 s to 1.62 s. **The constant is
   doing the standing.** The feedback is a correction on top of a posture held open-loop.

---

## 3. WHAT THE OBJECTIVE WAS INTENDED TO MEASURE

`stand_port.stand_reward`, per control sample, then averaged over the rollout:

```
r = height × support × joints − 3·fell − 0.01·effort
```

| term | intended to measure | form |
|---|---|---|
| **height** | is the pelvis at its derived target 0.9201 m | `exp(−(z_err/0.05)²)` |
| **support** | is the CoM inside the base of support | `exp(−max(mx,my)²)` |
| **joints** | is the body off its own stops (not hanging on passive tissue) | `1/(1 + Σⱼ max(0, fⱼ−0.8)/0.1)` — repaired 2026-08-04 |
| **fell** | terminal | −3.0 |
| **effort** | metabolic cost | −0.01·mean\|u\| |

Plus, at the rollout level: `score = mean(r) − 3·fell − 2·(1 − frac_run)`.

**Note what is NOT in it: survival time.** The reward integrates a per-sample quality and pays
duration penalties; it never measures the quantity every judge reports. **Whether it predicts
survival at all is unmeasured** — see §5.

---

## 4. WHAT HAS BEEN MEASURED

All of the following are numbers with instruments behind them, not readings of the code.

### The instruments were the problem more often than the body

Seven gauges were repaired in one lane, three of which had already produced published claims:

| gauge | defect | consequence |
|---|---|---|
| joints penalty | max-then-gaussian over 29 joints | saw **0.99 of 29** joints/sample; median per-joint slope **exactly 0**; factor at 4.2e-7 annihilated height and support |
| `_periodicity` | argmax over a window whose floor is 0.140 s | reported **strength 0.579 at "a 0.14 s cadence"** for a body with no cycle at all |
| stand survival | one rollout | **9.08 s published; 7.01 s median of ten**, and seed 0 is the luckiest |
| `step_port` | reimplemented the stand formula with an open slice | crashed `f5_step`/`train_step` outright for a day |
| CEM elite mean | moves the centre downhill | turn 0: incumbent −3.864, elite mean **−4.504** |
| CEM step size | 10⁴ too large for the basin | **0/10** samples beat the incumbent at the trainer's own scale |
| CEM spread floor | `+1e-3` absolute where a fraction belonged | **133×** larger than the derived step |

### The search wall, opened

| | value |
|---|---|
| improvements exist at | **1e-4 × the trainer's step** — 70% of samples beat the incumbent there |
| the basin, in ‖Δθ‖ | ~1e-3 over 1160 numbers |
| effect of repairing all three search defects | **+1.2% held-out survival** (6.82 → 6.90 s) |
| trainer score over the same run | −3.864 → −3.637 |

**The trainer's score moved 0.227 and held-out survival moved 0.08 s.** That gap is the single
most important number in this document.

### The train/test gap is real

`stand_survival --trained-seeds 3` on the incumbent: all-10 median **7.01 s**, trained seeds 0–2
**7.70 s**, held-out seeds 3–9 **6.82 s** — a **+0.88 s gap**. On the derived-step arm the gap
*grew* to +1.08 s. Any headline that averages across the training seeds is inflated.

### The stand itself

Pelvis holds **102.9% of target** for F3's 5 s on 10/10 seeds; the CoM stays inside the base of
support (measured contact polygon 0.1015 m half-width, matching theStance's published
`together_half_width_m` 0.1020 m to 0.5 mm). It then falls at a **median 7.01 s**, and the fall
is **posterior in 9/10 seeds** at an exit pitch of **−14.1°** — leaning back — while the pitch at
the fall bar is **+15.2°**, forward. The CoM leaves its base at 3.85 s and the pelvis crosses the
fall bar at 4.95 s: **1.10 s of toppling after the outcome is decided.**

---

## 5. WHAT IS UNTESTED — the live questions, in the order the evidence recommends

Each is written as a claim someone could disagree with, because that is what makes it a
membrane rather than a backlog item.

**Q1. Does the objective predict survival at all?**
It is a *proxy*, and no one has plotted it against the thing it proxies. The one datum available
is discouraging: a 0.227 improvement in objective bought 0.08 s of held-out survival. If the
correlation is weak, every training run in this lane optimised a number that does not mean what
its name says, and no policy class will rescue that. **This is first because it is cheap and
because a negative answer invalidates the others.**
*Design note:* thetas sampled uniformly over the trainer's bounds will all fall at ~0.5 s and
give a degenerate population with no variance to correlate. A spanning population must be drawn
the way `tools/search_landscape.py` draws one — a scale ladder around a known-good point.

**Q2. Does the missing derivative matter more than the missing phase?**
The policy has no `ż` and no `pitch̊`. A P-only controller on an inverted pendulum is the
textbook case for oscillation and divergence, and the measured fall is exactly that shape:
committed exit at −14° backward, arrival at +15° forward — one overshoot. **Adding D is a
smaller, better-motivated change than adding a phase basis, and it should be tested first**, or
a phase result cannot be attributed.

**Q3. Does phase help?**
`ω₀ = √(g/H)` is derived and a standing CoM does oscillate. But a phase basis on a body with no
rate feedback adds an oscillator to a controller that cannot yet sense oscillation.

**Q4. Does memory help?**
A finite-impulse window is a way of *approximating* the derivative Q2 asks for directly. If Q2
answers yes, part of Q4's answer is already known.

**Q5. Does the policy transfer across gravity?**
A policy that stands at 9.81 m/s² as well as at 7.076 is a policy; one that only stands where it
was trained is a fit. Given the +0.88 s train/test gap on *seeds*, the prior is not encouraging.
*Design note:* this does **not** require regrowing the story at a different `g`. `world.load_body`
overrides the model's gravity from theHuman; a transfer test sets `m.opt.gravity` directly and
leaves every membrane and every other lane's shared state untouched.

**Q6. Is 1160 free numbers the right size?**
`synergy.py` measured 8 dims = 91% and 16 dims = 96% of this body's movement. A policy in synergy
space would be ~64 numbers instead of 1160, and the A/B already run on the walk found that the
16-dim arm *climbed monotonically where the 290-dim control thrashed*. The basin measurement
(10⁴ narrower than a naive step) is what over-parameterisation looks like from the search's side.

---

## 6. THE RULE FOR WHAT COMES NEXT

**No policy-class experiment is interpretable until Q1 is answered.** If the objective does not
predict survival, then "policy class A beats policy class B on the objective" is a statement
about the proxy and not about standing, and the whole comparison has to be judged on held-out
survival directly — which is affordable and should probably be the rule regardless.

**And every comparison is on held-out seeds.** The judge scores seeds 0–9; the trainer selects on
0–2. The gap is +0.88 s on the incumbent and grew to +1.08 s under a better search. A policy-class
benchmark that reports all-10 medians will rank the class that overfits its three seeds best.
