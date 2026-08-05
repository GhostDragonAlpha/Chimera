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

> ## ANSWERED 2026-08-04 — Q1 and Q5 are closed, and both answers are bad
>
> **Q1. The objective ranks wreckage and cannot rank policies.** 200 policies on a scale ladder
> around the incumbent, objective = the trainer's own `score_theta`, survival = held-out median:
>
> | regime | n | Pearson r |
> |---|---:|---:|
> | **broken policies** (scale ≥ 3e-4) | 140 | **1.000** |
> | **near the incumbent** (scale ≤ 3e-5) | 40 | **−0.162** |
> | pooled | 200 | 0.990 |
>
> The pooled 0.990 passes the stated bar **and passes it because 70% of the population is
> wreckage.** Where a warm-started search actually lives the correlation is *negative*. **The
> objective can tell a broken policy from a working one and cannot tell two working policies
> apart — which is the only comparison a search makes near a good solution.** This is exactly
> why repairing the search moved the objective 0.227 and held-out survival 0.08 s.
>
> **And the components fight each other.** Within-rung (scale held constant, so the ladder
> cannot manufacture it):
>
> | | height | support | joints | effort | **survival** |
> |---|---:|---:|---:|---:|---:|
> | height | 1.000 | 0.311 | **−0.943** | 0.924 | **−0.042** |
> | support | 0.311 | 1.000 | −0.335 | 0.109 | **+0.891** |
> | joints | −0.943 | −0.335 | 1.000 | −0.959 | **−0.057** |
>
> **`support` is the only component that predicts survival.** `height` and `joints` are almost
> perfectly anti-correlated (−0.943) and *neither* relates to survival. The objective MULTIPLIES
> all three: one informative factor times two mutually-exclusive uninformative ones. The
> optimiser has been asked for something the body cannot deliver, in exchange for something the
> bar does not measure.
>
> **Pareto:** the best-objective policy survives 6.72 s; the best survivor lasts 7.48 s and sits
> at the **26th percentile** of the objective's own ranking.
>
> **Q5. The policy does not transfer.** Held-out survival at Earth gravity vs this world's:
> **6.82 s → 1.60 s, ratio 0.23**, identically for all three thetas — inside the task's OVERFIT
> band. And the mechanism is already on record: ablating `a0` gives **1.62 s**. *The body at the
> wrong gravity performs like a body with no baseline activation at all*, because `a0` is a
> constant activation producing a fixed force to balance a fixed weight. **A constant baseline
> IS a memorised gravity** — an arithmetic identity, not a metaphor.

**Q1. Does the objective predict survival at all?**
It is a *proxy*, and no one has plotted it against the thing it proxies. The one datum available
is discouraging: a 0.227 improvement in objective bought 0.08 s of held-out survival. If the
correlation is weak, every training run in this lane optimised a number that does not mean what
its name says, and no policy class will rescue that. **This is first because it is cheap and
because a negative answer invalidates the others.**
*Design note:* thetas sampled uniformly over the trainer's bounds will all fall at ~0.5 s and
give a degenerate population with no variance to correlate. A spanning population must be drawn
the way `tools/search_landscape.py` draws one — a scale ladder around a known-good point.

> ## ANSWERED 2026-08-04, SECOND PASS — Q2, Q3 and Q4 are closed, and the control closes them all
>
> Thirteen arms, `tools/benchmark_policies.py`, all warm-started from **one point** (the incumbent,
> matched by channel name, every added channel at zero gain — so a PD policy at the warm start IS
> the P-only policy, measured bit-identically by `--selftest`). Identical budget 24×30, worst-of-3
> starts × 12 s, identical RNG seed, derive-step + elite-guard on every arm. Judged on the same
> seven held-out seeds. Verdicts: `tools/benchmark_verdict.py`.
>
> **READ THE PAIRED STATISTIC, NOT THE MEDIAN.** Every arm is judged on the *same* seven initial
> conditions, so the samples are paired by construction and a median over the unpaired set throws
> that away. It is not a nicety — the two disagree:
>
> | | seed 3 | 4 | 5 | 6 | 7 | 8 | 9 | median |
> |---|---:|---:|---:|---:|---:|---:|---:|---:|
> | `p_only` | 7.18 | 7.72 | 6.32 | 6.40 | 6.34 | **6.86** | 7.62 | 6.86 |
> | `pd` | 7.68 | 7.90 | 6.34 | 6.66 | 6.42 | **6.76** | 8.00 | 6.76 |
>
> `pd` wins on **six of seven** seeds; both medians are the seed-8 value, the one seed where it
> loses. The median reports the opposite sign from every other seed in the set.
>
> | question | comparison | paired median | wins | sign test p | verdict |
> |---|---|---:|---:|---:|---|
> | **Q2** derivative | `pd` vs `p_only` | +0.18 s | 6/7 | 0.125 | **superseded — see below** |
> | **Q4** longer baseline | `pd_windowed` vs `pd` | **−0.04 s** | 2/7 | 0.688 | **no help** |
> | **Q3** phase basis | `pd_phase` vs `pd` | **+0.00 s** | 3/7 (1 tie) | 1.000 | **adds nothing over PD** |
> | objective v2 | `p_only`[support-only] vs [full] | **+0.20 s** | 6/7 | 0.125 | positive, not significant |
> | objective v2 | `pd`[support-only] vs [full] | −0.02 s | 2/7 | 0.688 | no help |
>
> ### Q2 CORRECTED AT n = 24 — the direction survives, the magnitude does not
>
> The n = 7 reading above was **underpowered, and that is a fact about the design before it is a
> fact about the body**: at n = 7 the *only* outcome reaching p ≤ 0.05 is a perfect 7/7
> (p = 0.0156), so the experiment had exactly one significant result available to it. Held-out
> seeds are cheap — a rollout ends when the body falls — so nothing was retrained, no theta moved,
> the same two arms and the same `survive`; only **n went 7 → 24** (seeds 3–26).
>
> | | wins | ties | losses | win rate | paired median | paired mean | sign test p |
> |---|---:|---:|---:|---:|---:|---:|---:|
> | **`pd` vs `p_only`, n = 24** | **18** | 0 | 6 | 0.75 | **+0.040 s** | +0.054 s | **0.0227** |
>
> **RATE FEEDBACK IS REAL AND SIGNIFICANT, AND IT IS WORTH 0.04 s.** The direction held; the
> effect size fell by a factor of four, because the first seven seeds happened to hold the larger
> differences. Independently replicated (`agent_logs/t1_replication_n24.json`) — the two
> measurements agree to the digit, and both reproduce the original seven seeds exactly, which is
> the control that says one instrument is not measuring something adjacent to the other's.
>
> **AND IT SHARPENS THE HEADLINE RATHER THAN SOFTENING IT.** A statistically real +0.04 s sits
> against an objective whose own worst mis-ranking is **0.78 s** — twenty times larger. The
> policy class is not the wall, and now that is true with a significant effect measured rather
> than an insignificant one assumed.
>
> **AND THE CONTROL SIZES ALL OF IT.** The theta each run *delivers* is the best-**objective** one;
> the *ceiling* is the best held-out survival the search visited at any turn. `p_only` delivered
> **6.86 s** having visited **7.64 s at turn 1** — the objective preferred a policy that stands
> **0.78 s less**. The entire spread across the seven arms that start at 6.82 s is **0.76 s**.
>
> > **The objective's own worst mis-ranking is larger than the whole between-class spread.** Every
> > policy-class difference measured here sits inside the noise the objective introduces. This is
> > `docs/LOCOMOTION_OBJECTIVE_DIAGNOSIS.md` §4 arriving exactly where it predicted.
>
> **WHICH OBSERVATION MATTERS (Q7, new).** The ablation is **two questions**, because the warm
> start is P-only: removing `z`/`pitch`/`roll` drops a *trained* gain block, while removing
> `ż`/`pitch̊`/`roll̊` drops a channel whose gain *starts at zero* and therefore costs exactly
> nothing until training acquires it.
>
> | removed | held-out at the warm start | drop | after training | vs `pd`, paired | p |
> |---|---:|---:|---:|---:|---:|
> | `pitch` | 1.26 s | **−5.56** | 2.26 s | −4.50 s (0/7) | 0.016 |
> | `a0` | 1.62 s | −5.20 | 4.46 s | — | — |
> | `z` | 2.08 s | −4.74 | 6.18 s | −0.88 s (0/7) | 0.016 |
> | `roll` | 2.32 s | −4.50 | 5.70 s | −1.06 s (0/7) | 0.016 |
> | `ż` | 6.82 s | **0.00** | 6.78 s | +0.00 (2/7) | 1.000 |
> | `pitch̊` | 6.82 s | **0.00** | 6.76 s | −0.02 (2/7) | 0.688 |
> | `roll̊` | 6.82 s | **0.00** | 7.52 s | +0.00 (3/7) | 1.000 |
>
> **The stated null — that `ż` and `pitch̊` are the critical terms — is refuted.** They are the two
> whose removal costs the least. `pitch` is the load-bearing channel by a factor of five.
>
> **Q5 EXTENDED, and the ratio was hiding the answer.** Earth-gravity held-out survival:
> incumbent **1.60 s**, `p_only` **1.60 s**, `pd` **1.60 s**, `pd_phase` **1.60 s**, `pd_no_a0`
> **1.64 s** — two control ticks apart across every policy class tried. `pd_no_a0`'s transfer
> *ratio* rises 0.23 → 0.37 only because its home survival collapsed 6.82 → 4.46 s. **The
> denominator moved; the quantity the ratio is about did not.** No policy class in this family
> transfers, and removing the baseline does not buy transfer — it buys a smaller home number.

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

**Q1 IS ANSWERED AND THE ANSWER IS BINDING: no policy-class experiment may be ranked by the
objective.** Near the incumbent the objective's correlation with survival is **−0.162**, so
*"policy class A beats policy class B on the objective"* is a statement about a number that does
not track standing in the regime where the comparison happens. **Every policy-class comparison is
judged on held-out survival directly.** That is affordable — it is what `stand_survival` already
does — and it is now mandatory rather than preferable.

**Three consequences that follow immediately, none of which needs another measurement:**

1. **`height` and `joints` should not both be multiplied.** They are anti-correlated at −0.943
   within-rung and neither predicts survival. A product of them is a constraint the body cannot
   satisfy, priced against a goal neither serves. `support` — the only component that tracks
   survival (+0.891) — is being multiplied by their conflict.
2. **`a0` is a memorised gravity, and any policy class that keeps a constant baseline inherits
   that.** A phase basis or a time window added *on top of* `a0` will still collapse at a
   different `g`. If transfer is wanted, the baseline has to become a function of something the
   body can sense.
3. **The missing derivative outranks the missing phase.** The policy is P-only on an inverted
   pendulum; the measured fall is one overshoot (exit −14° backward, arrival +15° forward). Add
   rate feedback before adding an oscillator, or a phase result cannot be attributed.

**And every comparison is on held-out seeds.** The judge scores seeds 0–9; the trainer selects on
0–2. The gap is +0.88 s on the incumbent and grew to +1.08 s under a better search. A policy-class
benchmark that reports all-10 medians will rank the class that overfits its three seeds best.

---

## 7. WHAT THE SECOND PASS ADDS TO THE RULE (2026-08-04)

Three rules, each earned by a measurement above rather than reasoned to.

1. **PAIRED SEEDS DEMAND A PAIRED STATISTIC.** Every arm is judged on the same seven initial
   conditions. A median over the unpaired set is a rank statistic decided by one seed, and it
   reported the opposite sign from the other six on Q2 *and* on Q3 — in opposite directions.
   `tools/benchmark_verdict.py` prints both and reads the paired one, out loud.
   **A comparison that discards structure the design already had is not a cheaper measurement,
   it is a different one.**
2. **THE SEARCH'S CEILING IS THE CONTROL FOR THE OBJECTIVE, AND IT IS NOT A RANKING.** Recording
   the best held-out survival visited at any turn costs seven rollouts per turn and separates
   *"this class cannot stand longer"* from *"the objective cannot find it"*. On these thirteen
   arms it is always the second. The number is selected on the judge, so it is biased upward and
   must never rank an arm — it exists to size the objective's error, and the error is **0.78 s
   against a 0.76 s between-class spread**.
3. **AN INSTRUMENT MUST RESOLVE ITS OWN CRITERION.** `derive_step` selects the largest ladder rung
   where ≥ `elite/pop` = 4/24 = 16.7% of samples beat the incumbent, and it sampled `k = 6` — so
   the finest fraction it could measure *was* the criterion, and one sample chose a rung. Measured:
   the same basin reads **1e-4** at 10 samples, **3e-4** at 12, and **1e-4** at 24. `k` is now the
   search's own population. Same species as *never threshold on a quantile of the population you
   measure*.

## 8. THE WALK AND THE LANDSCAPE (2026-08-04) — the derivative does not transfer, and it narrows the basin

**THE WALK.** Two arms, identical in everything but the frozen stand substrate: the walk's eight
oscillator numbers warm-started from `walk_theta_entrained`, trained 24×30 worst-of-3 × 8 s with
derive-step and elite-guard, judged by `f4_walk` on held-out seeds 3–9.

| walk arm | travel | **periodicity** | pelvis min | held |
|---|---:|---:|---:|---:|
| baseline (`walk_theta_entrained`, incumbent substrate) | 0.4603 m/s | **0.173** | 0.4121 m | 2.20 s |
| **P-only substrate**, retrained | 0.4963 m/s | **0.245** | 0.4330 m | 2.08 s |
| **PD substrate**, retrained | 0.4758 m/s | **0.188** | 0.4559 m | 2.18 s |

Paired over the seven held-out seeds:

| comparison | paired median periodicity | wins | p |
|---|---:|---:|---:|
| PD vs P-only | **−0.061** | 2/7 | 0.453 |
| PD vs baseline | +0.015 | **7/7** | **0.016** |
| P-only vs baseline | **+0.073** | **7/7** | **0.016** |

**Task 7's falsifier fires on both statistics: the PD walk's periodicity is *lower* than the
P-only walk's.** The derivative does not transfer from standing to walking. What *did* move is
the search and the judge: both retrained arms beat the repaired baseline on 7/7 seeds
(p = 0.016), and the larger gain belongs to the P-only substrate. **Every arm still fails all
three F4 bars** — 0/7 seeds on travel, periodicity and upright. This is a better failure, not a
walk.

> **The baseline it is measured against had to be repaired first, twice.** The quoted prior best
> — *"entrained+mult, periodicity 0.59, held 2.06 s"* — was scored at a **period of 0.14 s**, the
> `_periodicity` window-floor artifact this document already records. Re-judged with the repaired
> gauge it is **0.173**. And `f4_walk` was building its parser obs as `{z, pitch, t}` while
> `move_formula_fn` read `obs.get("roll", 0.0)`, so **290 of the frozen stand policy's 1160
> numbers were multiplied by zero at judgment** while `train_walk` trained against them —
> travel 0.3495 → 0.4603 m/s, **+32%**, on the exact quantity falsifier 1 reads.
> `tools/walk_roll_probe.py` measured it; the formula now refuses a lean-less obs.

**THE LANDSCAPE.** `tools/search_landscape.py --class`, 24 samples per rung (the search's own
population), ladder extended to 1e-6 so the answer is inside the measured curve:

| perturbation × the trainer's warm step | `p_only` (1160 numbers) | `pd` (2030 numbers) |
|---|---:|---:|
| 1e-6 | 58.3% | **0.0%** |
| 1e-5 | 75.0% | **0.0%** |
| 3e-5 | 87.5% | **0.0%** |
| 1e-4 | 16.7% | 0.0% |
| 3e-4 | 16.7% | 0.0% |
| ≥ 1e-3 | 0.0% | 0.0% |
| **basin at the elite criterion (4/24)** | **1e-4 … 3e-4** | **below 1e-6** |

**The PD basin is at least two decades narrower than the P-only one — the opposite of task 10's
hypothesis.** Adding 870 parameters did not widen the landscape the search navigates; it made
every perturbation, down to a step of ~1e-5 in ‖Δθ‖, strictly worse. Read `p_only`'s 58.3% at
1e-6 for what it says: the incumbent is *not* at a local optimum, and a random tiny step is a
coin toss. `pd`'s 0/24 at the same scale says it *is* at one.

*Honest limit:* `p_only`'s qualifying rung sits exactly at the criterion — 16.7% **is** 4/24 — so
which of 1e-4 and 3e-4 is "the" basin flips with the RNG realisation (12.5% = 3/24 on a different
draw). The robust statement is the range, not a single rung. The PD result needs no such caveat:
it is 0/24 everywhere.

---

**AND THE STANDING QUESTION IS NOW Q6, ALONE.** Q2, Q3 and Q4 are answered and all three answers
are *"the policy class is not the wall"*. Nothing in the family — a derivative, a longer baseline,
an oscillator basis, six ablations, a second objective — moved held-out survival by more than the
objective's own mis-ranking. `pitch` carries the stand (−5.56 s when removed) and `a0` carries the
gravity (Earth-g survival is 1.60 s for every class tried). What has *not* been tried is the one
§5 already named: **the 1160 free numbers are describing a ~16-dimensional body**
(`ChimeraEngine/synergy.py`: 8 dims = 91%, 16 = 96%), and the basin being 10⁴ narrower than a naive
step is what over-parameterisation looks like from the search's side.
