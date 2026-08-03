# theMining

<!-- CHIMERA-LAW -->
> **RULE 0 — EVERY MEMBRANE IS A THEORY. STATE IT BEFORE YOU BUILD IT.** Three parts, all three
> required: a **STATEMENT** someone could disagree with · a **PREDICTION** you have not measured
> yet · a **FALSIFIER** named *before* the run. **A description survives any result; a theory can
> lose.** No falsifier, no build.
>
> **RULE 1 — DERIVE IT BEFORE YOU TRAIN IT.** A parameter sweep is an admission the derivation was
> not done. Before any run, any sweep, any "let's try N variants": trace the variables and show the
> equations close. If you are choosing a number, you broke the chain and substituted taste for a
> law. Ask what QUESTION each variant answers — if the answer is "which number is best", STOP.
>
> **RULE 0 IS ENFORCED AT S-1 VALIDATE** — every port tested alone, and `port_test()` REFUSES to
> register a test that names no falsifier. The model it feeds: `docs/THE_COMPILER.md` — ports →
> primitives → programs → parser → runtime → calibration.
>
> **[docs/THE_LAW.md](../../../../../../../../../../../../../../docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 26 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

> **chapter 38** of the story  ·  **t = 1.47764e+17 s** since theZero  ·  lasts **6.31152e+08 s**
>
> *The serial is the place in TIME, not in the folder tree. A path says what contains
> what; this says what follows what. Both are published — `timeline_serial` in
> numbers.json and here — so the story and its numbers cannot disagree about when.*


**In plain words —** An ore is a concentration: the interior's elements sit in the crust at
trace fractions, and a mine is the place geology piled them up past the grade where taking them
pays. Everything else — the method, the energy, the deepest hole — is that fact meeting physics.

*The law of taking matter to the surface. The instance of it here is `aTerraceMine`.*

## The cutoff is energy, not taste

Separating below a grade costs more than the metal is worth. The cutoff grade is where the
energy to dig, crush, smelt and refine a tonne crosses the metal the tonne yields — computed,
never chosen.

## The method is the stripping ratio

Above ground or below it: waste over ore decides. Past a few-to-one (measured band 5–10) the
pit closes and the shaft opens. An instance is named by the method the ratio computes —
`aTerraceMine` or `aShaftMine` — and `measure()` checks.

## Comminution is where the power goes

Freeing metal means breaking rock, and the energy follows Bond's law (measured, 1952): the
finer you grind, the steeper the cost. A mine's power bill is mostly its grinders.

## The limits are the planet's

Depth is heat (the gradient — here 22 K/km), water (inflow), and pressure (the rock closing
back). The deepest workable hole is set by the planet, not by will.

*Contained in `theInterior`. Contains `aTerraceMine` — the hole this world actually digs.*
