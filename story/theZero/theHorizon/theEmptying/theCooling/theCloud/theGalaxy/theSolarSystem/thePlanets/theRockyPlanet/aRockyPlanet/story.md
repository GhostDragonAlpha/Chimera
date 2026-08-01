# aRockyPlanet

> **chapter 13** of the story  ·  **t = 5.75715e+15 s** since theZero  ·  lasts **3.31094e+07 s**
>
> *The serial is the place in TIME, not in the folder tree. A path says what contains
> what; this says what follows what. Both are published — `timeline_serial` in
> numbers.json and here — so the story and its numbers cannot disagree about when.*


**In plain words —** This is the same world as the last chapter, seen from the inside. Because it was
once molten, it sorted itself: the iron sank and made a core, the lighter rock floated on top. How
big that core is, how hard it is squeezed, how far out of round the spin pushes the whole thing, and
— the one that matters — **whether the core is still moving.** A moving iron core makes a magnetic
field, and a magnetic field is what stops the star from blowing the air away.

*The chapter that answers the question the last one had to leave open.*

## It sorted itself, and the density says how far

Nobody places a core. A molten body separates by weight, and the only thing that decides where the
boundary lands is how much iron there was — which the **bulk density already tells you**:

```
ρ_bulk  =  f · ρ_iron  +  (1 − f) · ρ_silicate          f = the core's share of the volume
```

| | this world | Earth (through the same law) | Earth measured |
|---|---|---|---|
| core reaches | **0.42** of the radius | 0.584 | 0.546 |
| pressure at the centre | **179 GPa** | 345 GPa | 364 GPa |
| moment of inertia `C/MR²` | **0.372** | 0.347 | 0.3307 |

Two densities and one equation get the inside of Earth right to **7%**. That moment-of-inertia
number is worth pausing on: 0.4 is a uniform ball and anything lower means the mass is piled inward.
Measuring 0.3307 is *how anyone knew Earth had a core at all*, long before they could say what it
was made of.

## Out of round

A turning body throws its own equator outward. The driving ratio is `q = ω²R³/GM`, and the
flattening is a multiple of it — a multiple that depends on **how the mass is arranged**, because a
body with a heavy middle resists. This world is less dense than Earth and turns just as fast, so it
is more out of round: **1/224** against Earth's 1/298.

## The core is still moving, and that is why there is still air

Heat is made by radioactivity in the rock, so it scales with **mass**; it escapes through the
surface, so it is diluted by **area**. `Q/A ~ M/R²` — and that ratio is why small worlds die young.

| | heat out | core |
|---|---|---|
| Earth | 92 mW/m² | **stirring** |
| **this world** | **66 mW/m²** | **stirring** — 23 TW total |
| Mars | 35 mW/m² (measured ~25) | **dead** |

Once the mantle can no longer carry the core's heat away, convection stops, the field switches off,
and **it does not come back.**

### This is the answer to the problem the last chapter left open

`theRockyPlanet`'s escape law says Mars should still be holding its CO₂ and most of its nitrogen.
Mars is not, and that chapter said so and stopped, because one inequality about *thermal* escape
cannot explain it.

The rest is not thermal. **Mars' core went quiet, its magnetic field went with it, and the solar wind
took the atmosphere** — a process that does not care in the slightest how heavy the molecules are.
So a planet keeps its air by **being warm inside**, which is a claim about the middle of a world made
from nothing but its mass and its radius.

This world is warm inside. Its air is shielded. That is why the next chapter gets to have weather.

## Its name

Left to itself the physics would classify a rocky body by what is in charge of its interior —
whether the core still convects — and this one comes out **Magnetised**. The folder is named
`aRockyPlanet` because the operator named it; `measure()` reports the derived class alongside, so it
can be renamed if the story ever wants that.

*Contained in `theRockyPlanet`. What it hands on: a shielded atmosphere, an interior, and the
gravity to stand in.*
