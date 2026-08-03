# theStar

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

> **chapter 10** of the story  ·  **t = 3.54816e+15 s** since theZero  ·  lasts **9.4671e+14 s**
>
> *The serial is the place in TIME, not in the folder tree. A path says what contains
> what; this says what follows what. Both are published — `timeline_serial` in
> numbers.json and here — so the story and its numbers cannot disagree about when.*


**In plain words —** Squeeze gas hard enough and it catches fire and stops falling. Squeeze too little and it just goes cold and stiff instead — so there is a smallest possible star.

*Chapter 6.*

A cloud that cannot stop falling gets denser, and as it does the Jeans mass falls with it — so the
collapse does not merely proceed, it **fragments**: a million suns breaking into ever smaller
pieces, each piece breaking again. It stops on its own when the gas becomes opaque to its own light
and can no longer dump the heat of compression; then temperature climbs with density instead of
staying flat, the Jeans mass stops falling, and fragmentation halts.

Each surviving fragment now contracts alone and heats, `T ∝ M/R`. But it has a rival that grows
faster. Squeezed electrons cannot share a state, and their crowding pressure rises as

```
E_F ∝ R⁻²        against        kT ∝ R⁻¹
```

so degeneracy always catches up. **Every contracting ball therefore has a maximum temperature it
will ever reach** — set them equal and it comes out

```
T_max ∝ M^{4/3}
```

after which quantum crowding holds the ball up *cold*, and it stops getting hotter forever.

So whether fire ever lights is a statement about **mass alone**. Clear hydrogen's ignition at
~4×10⁶ K and fusion begins; fall short and degeneracy catches the ball first and it never becomes
anything. The threshold comes out at **≈0.07 M☉** — against the measured brown-dwarf limit of
0.075–0.08.

Above it, for the first time since the beginning, **the fall stops** — held up by its own fire, the
heat flowing outward through a surface that glows at the temperature balance demands.

And what did not fall in cannot vanish either: it carries angular momentum, so it flattens and
stays, circling.
