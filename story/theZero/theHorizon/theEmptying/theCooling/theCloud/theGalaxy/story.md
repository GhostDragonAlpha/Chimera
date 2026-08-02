# theGalaxy

<!-- CHIMERA-LAW -->
> *Derive before you train — [THE LAW](../../../../../../../docs/THE_LAW.md). Every number below is derived from the parent's or measured; none is chosen.*
<!-- CHIMERA-LAW -->

> **chapter 08** of the story  ·  **t = 2.41211e+15 s** since theZero  ·  lasts **2.33681e+15 s**
>
> *The serial is the place in TIME, not in the folder tree. A path says what contains
> what; this says what follows what. Both are published — `timeline_serial` in
> numbers.json and here — so the story and its numbers cannot disagree about when.*


**In plain words —** The clumps of gas keep falling into each other and pile up into one enormous
spinning island of stars. It has to spin, because it cannot fall straight in — and that spin is what
makes the spiral arms, which are not solid things but traffic jams that stars drift through.

*Chapter 7.* — **where stars are actually made**

`theCloud` handed down bound clumps of ~6×10⁵ M☉ that cannot stop falling. **They do not become
solar systems on their own.** They fall into each other first, and what they build is a galaxy — so
this membrane sits between them, and it is a level we skipped once and put back.

## Why it is flat, and why it is not

The same law as before: **angular momentum survives the collapse.** Gas can radiate away its heat
and settle into a disk, but it cannot radiate away its spin, so it flattens. Stars, once formed,
cannot radiate anything away at all — so the *old* stars keep the round shape they collapsed with,
and only the *gas* becomes a thin disk. A galaxy is therefore both at once: a **bulge** that
remembers, and a **disk** that settled.

## The arms are not objects

A disk of stars cannot rotate rigidly — inner orbits are faster, so any solid pattern would wind
itself shut within a few turns (the **winding problem**). The arms survive because they are not
material at all: they are a **density wave**, a slow-moving compression that stars and gas drift
*through*. Gas entering an arm is squeezed, and squeezed gas is what crosses the Jeans threshold —
so **the arms are bright because that is where stars are being made**, not because more stars live
there.

## What holds it together

The orbital speed of a disk should fall off with distance, like the planets do. **It does not** — it
flattens out, which is only possible if far more mass is present than the light shows. That is the
rotation-curve fact, and it is measured, not assumed.

## What is contained here

| declared | what it is |
|---|---|
| **theMolecularCloud** | the cold dense gas inside an arm, where a system actually forms |
| **theSolarSystem** | one system, grown from one such cloud |

*What it hands on: a place in a spiral arm, an orbital period around the centre, and gas already
enriched by the stars that lived and died before ours.*

## Why a star weighs about a sun

The chapter above builds an island of stars out of clouds of **615,000 suns**. Nothing so far has
explained why the things that form *inside* those clouds weigh **one**.

The answer is that a cloud does not collapse. **It shatters — repeatedly.**

```
M_J  =  (5kT / G μ mH)^(3/2) · (3 / 4πρ)^(1/2)
```

That's the same Jeans mass the parent chapter used, but the important thing is what it does *during*
a collapse. As long as the gas can radiate away the heat of its own squeezing it stays **cold**, so
`T` is fixed and the fragment mass falls as `ρ^-1/2`: every hundredfold gain in density cuts the
piece tenfold. So the pieces keep getting smaller, all the way down:

| where | temperature | density | fragment |
|---|---|---|---|
| recombination | 3,760 K | 10⁻³ cm⁻³ | **124,000,000 M☉** |
| a warm atomic cloud | 100 K | 10² | 1,700 M☉ |
| a cold molecular cloud | 10 K | 10⁴ | 5.4 M☉ |
| **a dense core** | **10 K** | **10⁵** | **1.7 M☉** |

Eight orders of magnitude of shattering, and it lands **in the stellar range**.

### What stops it

Fragmentation ends when a piece becomes **opaque to its own cooling light**. It can no longer dump
the heat of compression, so it warms, `M_J` stops falling, and that piece is the last one. The floor
is about **0.01 M☉** (Low & Lynden-Bell 1976; Rees 1976).

Multiply the core Jeans mass by the **measured** core-to-star efficiency — a core loses roughly
two-thirds of itself to outflow — and the characteristic stellar mass is **0.56 M☉**. The observed
value is 0.2–0.3. Right decade, from no fitting at all.

### The Sun is a heavy star

Reading the resulting mass function: **1 M☉ sits at the 93rd percentile.** Nine stars in ten are
lighter than the Sun. "An ordinary star" is already an unusual one.

## The dial that reaches all the way down: enrichment

Cooling needs **coolants**. Metal-free gas has only molecular hydrogen, which is a poor radiator, so
the first cores could not get below ~200 K. Once a few generations have made carbon, oxygen and
dust, CO and grain emission take over and a core settles at 10 K.

Since `M_J ∝ T^1.5`, that is a factor of **90 in fragment mass**:

| enrichment | core temperature | fragment |
|---|---|---|
| 10⁻⁵ Z☉ | 198 K | **150 M☉** |
| 10⁻³ Z☉ | 105 K | 58 M☉ |
| 10⁻² Z☉ | 27 K | 7.7 M☉ |
| **1 Z☉** | **10.2 K** | **1.7 M☉** |

**This law was not built from it and returns it anyway: the first stars were hundreds of solar
masses.** That is the accepted picture of Population III, and here it is a consequence of one
temperature in one equation.

### And one dial that deliberately does *not* reach down

`clouds merged` sets how much **galaxy** there is — its rotation curve, its dark ratio. It has no
bearing on how cold a core can get, so it does not touch stellar mass. That claim is written into
the dial itself (`"local": ...`) rather than left as a silence, because a silent non-propagation is
indistinguishable from a bug. Manufacturing a link would have made a nicer audit report and a worse
model.

