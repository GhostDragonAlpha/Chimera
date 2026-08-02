# aSaltOcean

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
> **[docs/THE_LAW.md](../../../../../../../../../../../../../../docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 25 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

> **chapter 19** of the story  ·  **t = 5.75715e+15 s** since theZero  ·  lasts **86400 s**
>
> *The serial is the place in TIME, not in the folder tree. A path says what contains
> what; this says what follows what. Both are published — `timeline_serial` in
> numbers.json and here — so the story and its numbers cannot disagree about when.*


**In plain words —** The water that actually fills this world's basins: 2,861 metres of it on
average, dark navy where it is deep, frozen past 43° latitude, with waves a metre and a half tall
and a tide that never changes — 21 centimetres from the star alone, twice a day, forever.

*An instance of `theOcean`, named by the class its own dissolved load puts it in.*

## Two paths to the same depth

Volume over area gives **2,861 m**. The Terrain membrane's sea-level solver — a different road,
through the basin's own shape — gave 2,914 m. Two paths within 2% of each other, and neither bent
toward the other. Earth's own volume over area gives 3,690 m against a measured 3,688.

## The colour is measured, not chosen

From Pope & Fry's absorption coefficients (1997): red dies ~25× faster than blue, so the deep
water returns only navy — attenuation length **57 m** for blue, **3 m** for red. The light that
gets anywhere is blue, and it gets down **165 m** (the photic zone, 1% light); at 100 m **6%**
remains. The sun's glint is Fresnel's measured 2.1% at normal incidence, concentrated by
wave slopes — the bright point in every ocean photograph from space.

## Cold, salty, and slow

At 35 g/kg (Earth's own salinity, the free dial), the surface sits at **1,027 kg/m³** and freezes
at **−1.9 °C**; the deep water rests at **+1.1 °C**, three degrees off the floor, as Earth's does.
Sound crosses the surface layer at **1,475 m/s**. The wind (7.3 m/s) drags the surface at
**0.22 m/s**, raises **1.5 m** seas, and spins two gyres, one per hemisphere.

## The tide that never changes

No moon was ever derived in this story, so the star is the whole tide. Its pull: h =
(3/2)(M★/M_p)(R/a)³R = **21 centimetres** — Earth's own sun raises 0.25 m by the same formula.
But there is no lunar tide to add to it, no spring-neap cycle, no king tide: the water rises a
hand-span **twice a day, every day, the same, forever**. Every coast here is shaped by a tide
that never varies — a fact any creature living on one would take for granted as the way worlds
are.

## The free dial

`salinity_g_kg` (35) — how much salt the rock weathered into the water over this world's history.
Turn it below 30 and the name must change to `aBrackishOcean`; `measure()` checks.

*Contained in `theOcean`. What it hands on: depth, density, freezing point, currents, wave
climate, ice edge, and the light's reach — everything a swimmer, a sailor, or a root needs.*
