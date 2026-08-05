# THE LOCOMOTION OBJECTIVE — what `stand_reward` measures, and what it does not

> **This is the design document for any future objective work in this lane.** It records what was
> measured about `stand_port.stand_reward`, in which regime, with what uncertainty — so that the
> next objective is derived against facts rather than against a summary of a summary.
>
> Written 2026-08-04, from `agent_logs/objective_survival.json` (200 policies) and
> `agent_logs/objective_matrix.json`. Companion to `docs/LOCOMOTION_POLICY_DESIGN.md`, which does
> the same job for the *policy class*. That document says what the controller IS; this one says
> what the number ranking it MEANS.
>
> **The headline, in one line:** the objective ranks a broken policy against a working one
> perfectly (r = 1.000) and cannot rank two working policies at all (r = −0.162, CI includes
> zero) — and the reason is not that its components are uninformative. **Near the incumbent every
> component is informative, and one of them is informative with the WRONG SIGN.**

---

## 0. THE PREMISE THIS DOCUMENT CORRECTS, before anything is built on it

The task that commissioned this work stated:

> *"The component matrix shows `support` is the only factor that tracks survival (r = +0.891).
> Height and joints are anti-correlated at −0.943 and neither relates to survival (r = −0.042 and
> −0.057)."*

Those three numbers are real and they are in `agent_logs/objective_matrix.json`. **They are
WITHIN-RUNG MEDIANS — a median over ten perturbation rungs, eight of which contain nothing but
wreckage.** The median is dominated by the broken regime, and the broken regime is not where any
warm-started search operates.

Restricted to the two rungs nearest the incumbent — the regime `tools/search_landscape.py`
independently measured the basin to sit in, so the split is not slicing until something appears —
the same 200-policy population says something different:

| component | within-rung MEDIAN (the premise) | **near the incumbent, n = 40** | 95% CI |
|---|---:|---:|---|
| height | −0.042 | **+0.495** | [+0.216, +0.699] |
| support | +0.891 | **+0.391** | [+0.090, +0.626] |
| joints | −0.057 | **−0.530** | [−0.722, −0.262] |
| effort | −0.251 | **+0.484** | [+0.203, +0.691] |

**Every one of the four is significantly correlated with survival where the search lives, and
none of them has the value the premise quotes.** `support` is not the only informative factor;
`joints` is the *strongest* one and it points the wrong way. This is the rule CLAUDE.md already
states — *a task's premise can be the artifact* — applied to a premise this repo itself produced
one commit earlier. Measure the number a spec quotes before you build on it.

---

## 1. THE OBJECTIVE, as it is actually composed

`stand_port.stand_reward`, per control sample, then averaged over the rollout, then penalised at
the rollout level (`train_stand.evaluate` / `policy_classes.rollout_score`):

```
per sample   r = height × support × joints        − 0.01 · effort
             height  = exp(−(z_err / 0.05)²)                    z_err = |z − 0.9201| / 0.9201
             support = exp(−max(|Δx|/hl, |Δy|/hw)²)             the CoM in the base of support
             joints  = 1 / (1 + Σⱼ max(0, fⱼ − 0.8) / 0.1)      the hinge sum, repaired 2026-08-04

per rollout  score = mean(r) − 3·fell − 2·(1 − frac_run)
```

**Survival time appears nowhere in it.** It integrates a per-sample quality and pays two
penalties; the quantity every judge in this lane reports is not a term.

---

## 2. THE CORRELATION MATRIX — three regimes, and they disagree

Population: 200 policies on a scale ladder around the incumbent (`tools/objective_survival.py`),
because thetas drawn uniformly over the trainer's bounds all fall in under a second and a
correlation over them measures nothing. Objective = `train_stand.score_theta`, the trainer's own
number, 12 s, worst of seeds 0–2. Survival = median over **held-out** seeds 3–9 at 20 s.

### 2a. NEAR THE INCUMBENT — scale ≤ 3e-5, n = 40, survival spread 6.36–7.02 s

|  | height | support | joints | effort | **survival** |
|---|---:|---:|---:|---:|---:|
| **height** | 1.000 | +0.872 | **−0.902** | +0.752 | **+0.495** |
| **support** | +0.872 | 1.000 | −0.643 | +0.399 | **+0.391** |
| **joints** | −0.902 | −0.643 | 1.000 | **−0.958** | **−0.530** |
| **effort** | +0.752 | +0.399 | −0.958 | 1.000 | **+0.484** |

**objective vs survival: r = −0.162, 95% CI [−0.451, +0.157] — the interval contains zero.**
The honest statement is *uninformative*, not *negatively correlated*: at n = 40 this measurement
cannot distinguish a mild negative relationship from none at all. Either way it is not a ranking.

### 2b. BROKEN POLICIES — scale ≥ 3e-4, n = 140, survival spread 1.50–6.60 s

|  | height | support | joints | effort | **survival** |
|---|---:|---:|---:|---:|---:|
| **height** | 1.000 | +0.357 | −0.430 | −0.023 | +0.277 |
| **support** | +0.357 | 1.000 | −0.177 | −0.527 | **+0.944** |
| **joints** | −0.430 | −0.177 | 1.000 | −0.181 | −0.183 |
| **effort** | −0.023 | −0.527 | −0.181 | 1.000 | −0.520 |

**objective vs survival: r = +1.000.** Perfect. This is where the pooled number comes from.

### 2c. POOLED — all 200

**objective vs survival: r = +0.990.** `support` +0.950, `height` +0.330, `joints` −0.374,
`effort` −0.525.

---

## 3. WHY THE POOLED NUMBER IS MISLEADING

The population is a **scale ladder**: objective and survival both fall monotonically as the
perturbation grows. A strong pooled correlation can therefore be manufactured entirely by that
common cause, without the two quantities being related at fixed scale at all. This is the same
species the experimental method already names — *never threshold on a quantile of the population
you measure* — a structure in the **sampling** masquerading as a structure in the **body**.

Per rung, with the confound held constant:

| rung (× the trainer's warm sd) | n | objective spread | survival spread | **r** |
|---|---:|---:|---:|---:|
| 1e-5 | 20 | 0.220 | 0.38 s | **−0.280** |
| 3e-5 | 20 | 0.197 | 0.60 s | **−0.069** |
| 1e-4 | 20 | 0.181 | 1.36 s | +0.600 |
| 3e-4 | 20 | 0.178 | 1.06 s | +0.981 |
| 1e-3 … 1.0 | 120 | ~0.24 | ~1.4 s | **+0.996 … +1.000** |

**The correlation is a function of how broken the population is.** 140 of the 200 policies are
wreckage; they carry the pooled 0.990. `search_landscape.py` measured the incumbent's basin at
**1e-4 × the trainer's step** (70% of samples beat it there, 10% at 3e-4, 0% beyond) — so the two
rungs where the objective is uninformative are exactly the two rungs inside the basin.

**And the within-rung MEDIAN inherits the same defect.** `objective_matrix.py` reports a
within-rung median r of 0.998, which is a median over ten rungs of which eight are wreckage. A
control that removes the ladder confound does not remove a regime imbalance. **The split by
regime is the control that works**, and its boundary was set by an independent measurement of the
basin, not by looking for a place the answer changes.

> **THE RULE THIS ESTABLISHES.** A correlation reported over a spanning population is a statement
> about the population. Any objective claim in this lane must state its regime, its n, and its
> confidence interval, or it is not a measurement.

---

## 4. THE MULTIPLICATIVE STRUCTURE'S FAILURE MODE — measured, not argued

A product assumes its factors are independently achievable *and* that they agree about what
"better" means. Near the incumbent, neither holds.

**They are not independently achievable.** `height` and `joints` correlate at **−0.902** and
`joints` and `effort` at **−0.958**. A policy that lifts the pelvis to its target does it by
driving joints toward their stops; the body cannot deliver both. The objective asks for both and
multiplies the answer.

**And they disagree about "better".** `height` predicts survival at **+0.495** and `joints` at
**−0.530**. Being *further off the stops* — the thing `joints` rewards — predicts a **shorter**
stand. That is not a paradox: passive tissue is stiffness, and an under-actuated body with 290
muscles and no rate feedback is partly held up by its own ligaments. The term was written as a
penalty for hanging on passive tissue, and passive tissue is load-bearing.

**So the product inherits the wrong sign.** Measured directly on the same 40 policies:

| quantity | r with survival | 95% CI |
|---|---:|---|
| `height` alone | +0.495 | [+0.216, +0.699] |
| `support` alone | +0.391 | [+0.090, +0.626] |
| `joints` alone | −0.530 | [−0.722, −0.262] |
| `height × joints` | −0.523 | [−0.718, −0.252] |
| `support × joints` | −0.490 | [−0.695, −0.210] |
| `height × support` | +0.446 | [+0.156, +0.665] |
| **`height × support × joints` — the objective's own product** | **−0.441** | **[−0.661, −0.150]** |

**Maximising the per-sample product near the incumbent selects for a SHORTER stand, significantly.**
Every pair containing `joints` goes negative; the only pair without it stays positive. The
full objective's −0.162 is *milder* than −0.441 because the rollout-level `−3·fell` and
`−2·(1 − frac_run)` penalties pull back toward survival — **the two terms that are not part of the
product are the only ones defending the goal.**

On the broken population the same product reads **+0.880**, which is why nothing caught this: the
structure is correct where the differences are large and inverted where they are small.

**Pareto, on the pooled population:** the best-objective policy survives **6.72 s**; the best
survivor lasts **7.48 s** and sits at the **26th percentile** of the objective's own ranking
(#53 of 200). The objective leaves **0.76 s — 11% — on the table** and cannot see it.

---

## 5. THE SUPPORT-ONLY HYPOTHESIS, and exactly what justifies it

`stand_reward_v2`: **`score = mean(support) − 3·fell − 2·(1 − frac_run)`.**

**What the matrix justifies.** Of the three multiplied factors, `support` is the only one whose
correlation with survival is positive in **both** regimes (+0.391 near, +0.944 broken, +0.950
pooled). Removing `joints` removes the factor whose sign is inverted where the search operates and
which drags every product containing it negative. Removing `height` removes the factor most
strongly anti-correlated with `joints` (−0.902), so the remaining objective is no longer asking
for two things the body must trade against each other.

**What it does NOT justify, stated so the result can be read honestly.** Near the incumbent
`support` is +0.391, not +0.891 — the premise's number is the wreckage-dominated median. A
correlation of 0.391 explains ~15% of the variance in survival, so support-only is expected to be
*less wrong*, not *right*. If it wins, it wins by a margin the matrix predicts to be small.

**Why the duration penalty stays.** T6 names height, joints and effort — the per-sample terms — as
what to remove. `−2·(1 − frac_run)` is a rollout-level term and is what stops an early fall
outscoring a late one: `mean(support)` over the first second, when the keyframe still has the CoM
centred, is HIGHER than over twelve. Dropping it would introduce a defect nobody asked for.
`policy_classes.rollout_score` is shared by both arms, so the objective is the single variable.

**Why `effort` is dropped despite being significant.** It is +0.484 near the incumbent — higher
effort predicts *longer* survival — and it enters the objective as **`−0.01 · effort`**, a
subtraction. The sign is inverted there too. It is removed rather than flipped, because flipping
it would be choosing a coefficient and no membrane publishes one (rule 1).

---

## 6. THE RULE — binding, and it is not a preference

> ### NO POLICY-CLASS EXPERIMENT MAY BE RANKED BY THIS OBJECTIVE.
>
> Near the incumbent — the only regime in which two candidate policy classes are ever compared —
> the objective's correlation with held-out survival is **r = −0.162, CI [−0.451, +0.157]**. A
> statement of the form *"class A beats class B on the objective"* is a statement about a number
> that does not track standing where the comparison happens.
>
> **Every policy-class comparison is judged on HELD-OUT SURVIVAL directly.** That is affordable —
> it is what `tools/stand_survival.py` already does — and `tools/benchmark_policies.py` refuses
> `--judge` anything else rather than making it the default.

Three corollaries, each of which follows without another measurement:

1. **The seeds are split and stay split.** The trainer selects on 0–2, the judge reads 3–9. The
   train/test gap on the incumbent is **+0.88 s** and grew to **+1.08 s** under a better search. A
   benchmark reporting all-10 medians ranks the class that overfits its three seeds best.
2. **A "capability ceiling" is not a ranking.** `benchmark_policies` records the best held-out
   survival seen at *any* turn. That number is selected on the judge, is biased upward, and exists
   only to separate *"this class cannot stand longer"* from *"it can, and the objective cannot find
   it"* — which, given §4, is the failure to expect.
3. **The objective is a diagnostic and is printed as one.** It is still worth reading: it is the
   quantity the search is climbing, and a class whose objective rises while its survival falls has
   told you something specific about §4.

---

## 7. WHAT A REPLACEMENT OBJECTIVE HAS TO SATISFY — the checklist for the next one

Written as requirements, because the next objective should be derived against them rather than
assembled and then correlated after the fact.

1. **STATE THE REGIME.** Report r with n and a confidence interval, near the incumbent and on the
   broken population separately. A pooled number on a scale ladder is a property of the ladder.
2. **CHECK EVERY FACTOR'S SIGN IN THE REGIME THAT MATTERS.** `joints` was written as a penalty for
   a real physical fact (weight on passive tissue) and measured **−0.530** against survival where
   the search operates. A term can be physically well-motivated and still be pointed the wrong way
   for the goal.
3. **DO NOT MULTIPLY FACTORS THAT ARE ANTI-CORRELATED ACROSS REACHABLE POLICIES.** −0.902 between
   `height` and `joints` means the product is a constraint the body cannot satisfy. Measure the
   pairwise matrix on a spanning population *before* composing, not after.
4. **CHECK THE PRODUCT, NOT ONLY THE PARTS.** Three individually-significant factors composed into
   a product that correlates at −0.441 is the whole finding of §4, and no inspection of the parts
   predicts it.
5. **THE OBJECTIVE MUST DISCRIMINATE AT THE SCALE OF THE BASIN.** The basin is **1e-4 × the
   trainer's warm step**; inside it the survival spread is **0.38–0.60 s**. An objective that
   cannot resolve half a second of standing cannot rank anything a warm-started search proposes.
6. **NAME WHAT IT DOES NOT MEASURE.** `stand_reward` never contained survival time. Whatever
   replaces it should say plainly which quantity it is a proxy *for*, and be plotted against that
   quantity on a spanning population before it ranks anything.

---

## 8. PROVENANCE — every number above, and the instrument that produced it

| number | source |
|---|---|
| the 200-policy population, objective and held-out survival | `tools/objective_survival.py` → `agent_logs/objective_survival.json` |
| the pooled and within-rung component matrices | `tools/objective_matrix.py` → `agent_logs/objective_matrix.json` |
| the regime split, the CIs, and the product correlations of §4 | computed from the same JSON; the split boundary is the basin edge measured by `tools/search_landscape.py` |
| the basin at 1e-4 × the trainer's step | `agent_logs/search_landscape_stand_theta.json` |
| the +0.88 s train/test gap | `tools/stand_survival.py --trained-seeds 3` |
| the policy class the objective was ranking | `docs/LOCOMOTION_POLICY_DESIGN.md` |
| the runner that enforces §6 | `tools/benchmark_policies.py` (`--judge` refuses anything but `held_out`) |

Confidence intervals are Fisher-z at 95%. No number in this document was re-drawn on a second
population: comparing two measurements of the same question on two different populations is the
defect `objective_matrix.py` was written to avoid, and it applies to this document too.
