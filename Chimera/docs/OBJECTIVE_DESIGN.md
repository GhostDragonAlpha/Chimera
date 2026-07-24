# OBJECTIVE DESIGN — the method for writing a trainer objective the optimiser won't exploit

> Recorded 2026-07-24 as a **completely solved category**: the most efficient method for one
> goal — *an objective that trains the thing you meant, not the hole in your spec.* Every rule
> here was paid for by a worked failure, most of them in a single session, each costing a
> retrain cycle. The method exists so those cycles are never spent again.
>
> Enforced, not just documented: `python -m core.objective_lint <objective.json>` checks the
> statically-checkable rules, and the pre-commit hook runs it. A doc can be ignored; a lint
> cannot. That is what makes a method *stay* solved.
>
> Sibling reading: `docs/TRAINING_PROTOCOL.md` (the protocol), `CLAUDE.md` (train-don't-tune),
> `core/trainer.py` (the crank), the memory `objective-reachability-and-margin`.

---

## The one-paragraph version

The optimiser does ~30,000 evaluations a second and has no taste. It will satisfy your
objective by the **cheapest** path it can find, and the cheapest path is almost never the one
you pictured. **A degenerate winner is not a failure — it is the optimiser auditing your spec
and finding the hole you would have defended in review.** So you do not fix the winner; you
fix the spec, and you front-load the seven checks below so the hole is closed before the
first run instead of after the fourth.

**Iterate the objective, never the artifact.**

---

## The seven rules, each with the failure that proved it

### 1. Probe reachability before setting a hard gate
A hard gate scores **zero** on violation. If the initial population cannot reach it, *every*
genome scores zero, there is no gradient, and the trainer does a **random walk at full speed**
— the fitness curve is flat and you read it as "the domain can't do this" when the truth is
"the spec has no slope."

> **Proved:** a hard floor of `clustering >= 4.5` when **0 of 140 random genomes** reached it.
> Worse, the one corner that *did* reach reality had `robustness 0.45`, so a second hard gate
> at `robustness >= 0.55` would have killed exactly the genomes that reached the target — two
> gates, mutually unsatisfiable in the reachable space.

**Do:** measure what N random genomes actually reach for every gated field first. A hard gate
is safe only where the population can already satisfy it, or where nothing is near it yet (an
overshoot guard, e.g. `clustering <= 12`). *A gate you cannot reach is not strict, it is blind.*

### 2. Every band target needs a margin term
A constraint asks *"are you inside?"*, which the **cheapest boundary point answers as well as
the centre.** So the winner parks *on* a band edge — inside reality by exactly nothing — and
its children fall out of reality with the slightest variation.

> **Proved:** round 1 satisfied every constraint with `verticality 0.476` against a `0.476`
> ceiling. Per-object jitter left the measured band **62% of the time at 1% of range.** Adding
> `band_margin` (distance from the nearest edge) as a maximize took child survival **38% → 81%.**

**Do:** maximize a **margin** (distance from the edge), not mere insideness. Margin is physics,
not taste: *a genome with room on all sides has children that are still real matter.*

### 3. A weighted-mean maximize needs a floor on its minimum component
Weighting terms by importance is correct — but a weighted mean **has no floor.** The optimiser
will zero a low-weight term entirely to buy a high-weight one, abandoning a dimension you
still care about.

> **Proved:** `seen_margin` weighted each fact by how visible it is (aspect 77.6%, verticality
> 6.1%). The optimiser drove verticality's margin to **0.045** — abandoning a fact that is 2.1
> JNDs wide and therefore *visible* — because at 6.1% weight it cost almost nothing. Fixed with
> a hard floor on `band_margin` (the min over all facts).

**Do:** if you maximize a weighted mean, floor the minimum component. Priority is not licence
to abandon.

### 4. Hard-gate SURVIVAL, not just presence
A soft constraint (a penalty, a low λ) can be **overwhelmed**. If nothing *hard* requires a
thing to survive, the optimiser will let it drain away when that buys score elsewhere — and
the loss is **invisible in every aggregate number.**

> **Proved:** `frac_muscle` had a genome floor of 0.10, but the volume constraint was soft
> (λ=0.9). The winner came out **3,143 bone / 14 muscle / 543 skin** — muscle drained to 0.4%.
> A single-tissue blob still has an aspect, a clustering and a robustness, so nothing else
> flagged it. Fixed with a hard `min_tissue_frac >= 0.06` gate.

**Do:** if a component must exist in the result, hard-gate its survival. Partial failure hides
in means.

### 5. Maximize physics that never saturates — never the band quantity itself
A quantity that is a **band** in reality (it has a natural range) must not be a `maximize`
term. Maximizing it drives the winner to reality's *extreme* rather than its *typical*, and a
maximize that saturates is, in the trainer's own words, *a band wearing a maximize's clothes.*

> **Standing rule** (`core/trainer.py`, CLAUDE.md). Clustering is a band (4.7–8.2); maximizing
> it would chase the most extreme region of the truck. The honest maximize is **robustness** —
> it never saturates, it is physics not taste, and it asks the only question that separates a
> rule from an accident: *does the same genome produce the same result from a different seed?*

**Do:** make band quantities into band-errors (distance outside, normalised by band width).
Maximize robustness, margin, or another never-saturating physical fact.

### 6. At least one maximize or a target — unless it is a feasibility check
An OPTIMISATION objective with only bounds **stops the moment the constraints are met** —
almost never where you wanted it. **Do:** carry at least one `maximize`, or a `target` to fit.

**The exception, verified against 47 objects:** a **feasibility** objective — "does a
configuration SATISFY these constraints?" — is legitimately maximize-free, because the first
feasible point *is* the answer. The `auto_decomposer` generates exactly these ("satisfy the
parent's walls in composition"). R6 is about optimisation goals; feasibility is a different,
valid category. `objective_lint` exempts an objective whose provenance is auto-decomposed or
whose every constraint carries a `wall`. (The "47 satisficers" the lint first reported were
all of this kind — not bugs.)

### 7. Score N randomised restarts and keep the WORST
One rollout from one initial condition is a **coin toss, not a measurement.** A chaotic sim
lets the optimiser select **luck** — a genome that looks good once and cannot repeat.

> **Proved (the founding lesson):** a celebrated 13.52-body-length walker had `periodicity
> 0.25` and lost 5.5 body lengths to a **one-micron** nudge. Under honest physics it scored
> *worse than an untrained brain* after 80,000 evaluations of selecting lucky dice.

**Do:** every fact is worst-cased over N randomised restarts; report `robustness = worst/mean`.
It costs Nx compute — that is what the GPU is for.

---

## Normalisation is load-bearing (the quiet rule)

When you sum errors across facts, **normalise each by its own scale**, or one fact silently
dominates. Clustering spans ~3.5 and alignment spans ~0.06; a raw sum weights clustering ~58×
for no physical reason, and the winner matches density while getting orientation completely
wrong. Divide each band-error by its band width.

---

## The efficiency claim, made concrete

Each rule above is **one retrain cycle** you do not spend. This session spent four
rediscovering rules 1–4 the hard way (~5 minutes of training plus analysis each, plus the
objective edits). The method front-loads all seven checks into the ~2 minutes of writing the
objective. That is the "most efficient method for the goal result": the goal is a working
objective, and the efficient path is to close the holes before the optimiser finds them, not
after.

---

## What the lint can and cannot check

`core/objective_lint.py` enforces the **statically-checkable** rules:
- **R6** — at least one `maximize` (fully checkable).
- **R5** — no known band-quantity in `maximize` (checkable against a small known-bands list).
- **R2** — if the objective has band-error minimize terms, it should also maximize a margin
  (checkable by term-name convention).
- **R3** — flagged heuristically when a maximize looks like a weighted mean with no floor.

Rules **R1 (reachability), R4 (survival), R7 (restarts)** need the domain to *run* and cannot
be linted statically — the lint prints them as a **reminder checklist** so they are never
silently skipped. The lint is a floor, not a ceiling: passing it means you did not make the
four mechanical mistakes, not that your physics is right.
