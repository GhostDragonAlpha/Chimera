# theOcean

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
> **[docs/THE_LAW.md](../../../../../../../../../../../../../docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 25 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

> **chapter 16** of the story  ·  **t = 5.75715e+15 s** since theZero  ·  lasts **86400 s**
>
> *The serial is the place in TIME, not in the folder tree. A path says what contains
> what; this says what follows what. Both are published — `timeline_serial` in
> numbers.json and here — so the story and its numbers cannot disagree about when.*


**In plain words —** An ocean is a liquid that gravity holds in a world's basins. Everything else
about every ocean — its depth, its colour, its currents, its tides — is that one fact's
consequences chasing it down.

*The law of oceans. The instance of it here is `aSaltOcean`.*

## Phase: the water must be liquid at all

Between freezing and boiling, at the world's pressure, or there is no ocean to speak of. This
world sits at 279 K and 0.52 bar — deep inside the liquid band, which is why the parent's climate
said `water_state: liquid` before this membrane ever asked.

## Weight: depth is volume over area

The ocean's mean depth is its volume over its area — nothing more. The basin's *shape* (coasts,
shelves, trenches) is theTerrain's business, never this membrane's: **theOcean owns the water.**

## Light: the colour is the absorption spectrum

Red light dies about 25× faster than blue in pure water (measured: Pope & Fry 1997), so deep
water returns only blue. The colour is a measurement, never a palette. And the sun's glint is the
*measured reflection* — Fresnel off the surface at n=1.34, about 2% at normal incidence,
concentrated by wave slopes into the bright point every ocean photo from space shows.

## Motion: wind drags, spin bends, and only the star pulls

The wind drags the surface (~3% of its speed, measured), the spin bends it (Coriolis), and the
star raises the only tide there is — **no moon was ever derived here.**

## The classification

An ocean is its **dissolved load**: fresh (<0.5 g/kg), brackish (0.5–30), salt (30–50), brine
(>50) — measured bands. An instance is named by the class its own salinity lands in, and
`measure()` checks the name still matches, exactly like the star's colour class.

*Contained in `aBlueWorld`, sibling to `theTerrain` and `theAtmosphere`. Contains `aSaltOcean` —
the water that actually fills this world's basins.*
