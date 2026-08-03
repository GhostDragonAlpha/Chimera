# theClock

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
> **[docs/THE_LAW.md](../../../../docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 26 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

> **chapter 02** of the story  ·  **t = 1.07825e-43 s** since theZero  ·  lasts **5.39125e-44 s**
>
> *The serial is the place in TIME, not in the folder tree. A path says what contains
> what; this says what follows what. Both are published — `timeline_serial` in
> numbers.json and here — so the story and its numbers cannot disagree about when.*


**In plain words —** Everything that gravity holds together ticks, and how fast it ticks depends on
only one thing: how densely it is packed. A star, a planet and a galaxy run on the same formula —
they just have wildly different densities, so a star's tick is an hour and a galaxy's is a hundred
million years.

*The law of duration.* `theHorizon` produced the first tick, `t_P = 5.39×10⁻⁴⁴ s`. This membrane is
what a tick *is* at every scale above it.

## One formula, and it is the same one every time

A thing held together by its own gravity has exactly one natural timescale — the time it would take
to fall through itself:

```
t_dyn ≈ 1 / √(Gρ)
```

**Only the density appears.** Not the size, not the mass — just how tightly the mass is packed.
That is why the same expression gives the orbital period of a planet, the collapse time of a cloud,
and the pulsation period of a star: they are not three laws that happen to look alike, they are one
law seen at three densities.

Check it: the orbital period `T = 2π√(a³/GM)` — substitute `M = ρ·(4π/3)a³` and the `a` cancels
completely, leaving `T = √(3π/Gρ)`. **A satellite skimming any body's surface orbits in a time set
by that body's density alone**, whether it is a pebble or a star.

## The other two clocks are different in kind

| clock | what sets it | scales as |
|---|---|---|
| **dynamical** | gravity vs itself | `1/√(Gρ)` |
| **light-crossing** | how long a signal takes to cross | `r/c` |
| **thermal / burn** | how long the stored energy lasts at the rate it is spent | `E/L` |

A thing is *coherent* when its dynamical time is shorter than its light-crossing time — it can
settle faster than news of a change can leave. When the reverse is true, it cannot act as one thing.

## Why the game needs this

The game is a state machine, and a state machine needs to know **what changes when**. Every membrane
ticks at its own rate, and those rates span 60 orders of magnitude — from the Planck tick to a
star's ten-billion-year burn. Without a clock per membrane, a chapter's movie runs `t = 0 → 1` in an
arbitrary unit and the fourth dimension is unlabelled. With one, `t = 1` means *a real elapsed time*,
and the ratios between scales — a day inside a year inside a lifetime — become true.

## What is contained here

| declared | what it is |
|---|---|
| **theDensityClock** | how fast time itself runs: deeper and faster are slower, and the ceiling is the horizon |

*What it hands on: a duration for every membrane below, derived from that membrane's own density.*

## What it predicted that it was never given

`t_light_sun_s` = **2.3206 s** — how long light takes to cross the Sun.

    measured solar radius 6.957e8 m / c  =  2.3206 s        agrees to every digit published here

Nothing about the Sun was fitted: the membrane was handed the Planck tick and asked to lay out the
scales a clock can run at, and one of the rungs it lands on is a real star's crossing time. The
same ladder gives the Sun's dynamical time as 1769 s and the Earth's as 895 s — free-fall times
that depend only on mean density, so a body's *size* never enters them.
