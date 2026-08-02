# theDensityClock

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
> **[docs/THE_LAW.md](../../../../../docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 25 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

> **chapter 03** of the story  ·  **t = 1.84069e-43 s** since theZero  ·  lasts **7.62437e-44 s**
>
> *The serial is the place in TIME, not in the folder tree. A path says what contains
> what; this says what follows what. Both are published — `timeline_serial` in
> numbers.json and here — so the story and its numbers cannot disagree about when.*


**In plain words —** Time runs slower when you are deep in gravity or moving fast. Your clock is really a readout of how much mass is packed around you.

**time leans with mass and speed**

Time is not a backdrop the world happens in front of. It is a **local rate**, and two things bend it:
how deep in a gravity well you are, and how fast you are moving.

```
deeper  →  slower :   dτ/dt = √(1 − 2GM/rc²)
faster  →  slower :   dτ/dt = √(1 − v²/c²)
```

Both are the same statement — **density of mass-energy leans the clock** — which is why one name
covers them.

## It closes the loop back to Chapter 2

Look at what happens when the first term reaches one:

```
2GM/rc² = 1        →        r = 2GM/c²  =  r_s
```

**The clock's ceiling is the fence.** `theHorizon` was never a separate object with its own rule —
it is the radius where this clock stops. The place you cannot divide by is the place where time
runs out. That is the same turtle, seen from the other end of the story.

## The proof is in your pocket

The prediction is not subtle and it is not optional: **GPS**.

| effect | rate |
|---|---|
| satellites sit higher in the well → their clocks run **fast** | **+45.7 μs/day** |
| satellites move at 3.9 km/s → their clocks run **slow** | **−7.2 μs/day** |
| **net** | **+38.5 μs/day** |

Measured value: **38.6 μs/day.** Uncorrected, that is **11.5 km of position error per day** — the
system would be useless inside an hour. Every phone on Earth is a running experiment confirming
that time leans.

*Contained in `theSolarSystem`. What it hands on: that "when" is a place, that going fast or falling
deep costs you time, and that there is a depth from which no time is left to come back with.*
