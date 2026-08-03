# theDisk

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
> **[docs/THE_LAW.md](../../../../../../../../../docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 26 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

> **chapter 11** of the story  ·  **t = 5.75715e+15 s** since theZero  ·  lasts **3.1557e+15 s**
>
> *The serial is the place in TIME, not in the folder tree. A path says what contains
> what; this says what follows what. Both are published — `timeline_serial` in
> numbers.json and here — so the story and its numbers cannot disagree about when.*


**In plain words —** Near the star it is too warm for ice, so only rock survives and you get small worlds. Farther out ice survives too, and there is four times more of it — enough to build giants.

*Chapter 7.*

What missed the star cannot leave — angular momentum has nowhere to go — so it settles into a disk
lit from its own centre. And a disk lit from its centre has a temperature that falls with distance:

```
T(r) = (L / 16πσr²)^{1/4}     ∝ r^{-1/2}
```

That gradient **sorts the material without anyone sorting it.** Every substance condenses at its own
temperature: metal and rock freeze out close in, while water stays vapour until ~170 K and only
becomes solid beyond the radius where the star's light has dimmed that far.

**That line is not placed, it is computed: 2.7 AU** — which is where the asteroid belt is.

And it matters out of all proportion, because water is roughly four times more abundant than rock,
so the moment you cross the line the amount of *solid* material jumps fourfold:

```
inside  0.4 – 2.7 AU :  ~3 Earth masses of rock       -> small worlds, and nothing more
outside 2.7 – 30 AU  : ~54 Earth masses of solids     -> cores past the ~10-Earth threshold
```

Past ten Earth masses a core's own gravity pulls gas in faster than the disk can resupply it, and
growth **runs away** into something enormous.

So the architecture of a system is not designed: **small rocky worlds inside a line, giants outside
it** — and the line's position is set by nothing but the brightness of the star it orbits. Move the
star's luminosity and the whole layout moves with it.

What is handed on is a rocky world, close in, made of what could condense where it formed.

## What it predicted that it was never given

`snow_line_au` = **2.80 AU** — where water ice can first survive.

    the Solar System's snow line sits at ~2.7 AU, the inner edge of the asteroid belt

The membrane was given a star's luminosity and the temperature ice condenses at, and nothing else.
It was not told where our own asteroid belt is. That the line falls just inside Jupiter is the
reason the inner planets are rock and the outer ones are gas, and this chapter derives the boundary
rather than placing it.
