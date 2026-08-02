# theAtmosphere

<!-- CHIMERA-LAW -->
> *Derive before you train — [THE LAW](../../../../../../../../../../../../../docs/THE_LAW.md). Every number below is derived from the parent's or measured; none is chosen.*
<!-- CHIMERA-LAW -->

> **chapter 15** of the story  ·  **t = 5.75715e+15 s** since theZero  ·  lasts **86400 s**
>
> *The serial is the place in TIME, not in the folder tree. A path says what contains
> what; this says what follows what. Both are published — `timeline_serial` in
> numbers.json and here — so the story and its numbers cannot disagree about when.*


**In plain words —** An atmosphere is gas that gravity keeps. Everything else about any air —
its weight, its colour, its weather, and the way it fades instead of ending — is that one fact
consequences chasing it down.

*The law of air, above any world that can hold one. The instance of it here is `aNitrogenAtmosphere`.*

## Keeping: a world's air is selected, not given

A gas stays if its molecules cannot reach escape speed thermally. The ratio of escape energy to
thermal energy is the Jeans parameter, and below about **6** the gas is gone over geological time.
So a world's air is a *selection*: light gases leave, heavy ones stay. This world's ledger shows it
working — hydrogen (3.0) and helium (4.2) are gone; methane (8.4), nitrogen, oxygen, carbon dioxide
and water all cleared the bar and stayed.

## Weighing: pressure is weight, and air has no edge

Kept gas weighs something, so the pressure at the ground IS the column's weight — and because gas
compresses under its own weight, the density falls as `e^{-z/H}` with `H = kT/μg`. That is why an
atmosphere has **no edge**: it does not stop, it fades. Any picture of air with a hard boundary is
drawn wrong.

## Colouring: the sky is forced

The column scatters short light most (`λ⁻⁴`), so any atmosphere over any star has a coloured sky —
blue where the path is short, red where it is long. The colour is set by the column mass and the
star's spectrum. It is never chosen.

## Weathering: clouds are condensation, not decoration

Air lifted cools at `g/c_p`; water falls out at the dewpoint. So clouds sit where the temperature
and humidity put them, and all of it stops at the tropopause, where the cooling stops.

## The classification

An atmosphere is its **dominant gas** — and the mean molecule is *measurable* from the scale
height: `μ = kT/Hg`. The classes, by molar mass: hydrogen, helium, methane, nitrogen, oxygen,
carbon dioxide. An instance is named by the class its own μ lands in, and `measure()` checks the
name still matches — rename it wrongly and the check fails, exactly like the star's colour class.

## What an instance inherits

The kept gases and their Jeans ratios, the pressure, the scale height, the temperature, the spin,
the wind — and the retention verdict. What an instance must derive for itself: its molecule, its
lapse rate, its sky's colours, its clouds, its top edge, its class and therefore its name.

*Contained in `aBlueWorld`, sibling to `theTerrain`. Contains `aNitrogenAtmosphere` — the air that
actually formed here.*

## What it predicted that it was never given

`scale_height_m` = **11,312 m** — the height over which this air thins by a factor of e.

    H = RT / (M_air g)  =  8.314 x 279.2 / (0.0288 x 7.076)  =  11,390 m      0.7% from the
    published value, and the difference is the membrane's own mean molar mass rather than my
    round 28.8 g/mol.

The comparison that matters is against a world we can stand on: **Earth's scale height is 8,500 m**.
This atmosphere is a third deeper, and every term says why — the surface is slightly cooler, which
would thin it, and gravity is 0.72 g, which more than makes up the difference. A planet that pulls
less holds its air further out.
