# aTerrain

**In plain words —** One place on that world, twelve kilometres across — about two hours on foot.
The parent worked in continents; this is the scale where you can see a hill. Nothing here draws a
river: the ground starts as rough noise, water is sent downhill, and every patch is worn down by how
much water crosses it and how steeply it falls. Do that for long enough and valleys are what is
**left over**.

*The first membrane sized for a person.* Everything above it is measured in planets.

## The law that carves it

```
dz/dt  =  −K · A^m · S^n            the stream-power law (Howard & Kerby 1983)
```

`A` is how much land drains through this spot, `S` is how steeply it falls. A river cuts fast where
much water crosses steeply and slowly where little water crosses gently — and that single rule,
applied everywhere at once, is what makes a **branching network**. It is not drawn and it cannot be
faked with noise at any amplitude.

Three things run together:

| | |
|---|---|
| **uplift** | rock is delivered from below. A landscape is a *balance*, never a leftover |
| **stream power** | the rivers cut down |
| **hillslope creep** | what the channels cannot carry, gravity still moves |

## Filling the hollows is not bookkeeping — it is what water does

A cell lower than all eight of its neighbours has nowhere to send its water. Left alone it keeps it,
everything upstream is **cut off from the sea**, and the network never organises.

Water does not do that. It fills the hollow until it overflows the lowest point of the rim, and
carries on. Getting this right is what took one basin from draining **8%** of the patch to draining
**74%** of it.

**And the algorithm matters.** Relaxing each pit up to just above its lowest neighbour looks
equivalent and is not — it moves the fill level one cell per pass, so a wide basin needs as many
passes as it is wide. Measured: 40 passes took 220 pits down to 111 and stalled. Priority-flood
(Barnes, Lehman & Mulla 2014) starts at the rim, always takes the lowest cell reached so far, and
settles every cell once, exactly.

## It passes its own test now, and it did not at first

Real rivers obey **Hack's law** — basin area against longest stream, `L ~ A^0.57`, on every
continent since 1957. It is put into this simulation nowhere, which is exactly why it is the test.

| | |
|---|---|
| **measured here** | **0.564** |
| real rivers | 0.55 – 0.60 |

**It came out 0.19 first** — a fractal wearing valleys. Three things were wrong, all of them mine:

1. **The flow graph was stale.** It was computed before the last round of incision and then read
   after it, so the heights and the drainage directions disagreed. Walking downstream, donors
   arrived *after* their receivers, long chains never accumulated, and the longest-stream length
   came out systematically short for big basins. That alone flattens the exponent.
2. **The hollows were filled by relaxation**, which moves the fill level one cell per pass — 40
   passes took 220 pits to 111 and stalled. Priority-flood settles every cell once.
3. **There was no tectonics.** Uplift was 10⁻³ m per step, so five hundred steps delivered half a
   metre of rock. Nothing to carve — which is why turning the erodibility up 25-fold moved the
   relief by less than one percent. The incision term was doing nothing at all.

### And diffusion is what decides whether there is a network

Incision organises; creep smooths. Too much creep and the branching is erased before it forms:

| creep `D` | 2.0 | 0.5 | 0.1 | 0.05 | 0.02 | **0.008** |
|---|---|---|---|---|---|---|
| Hack | −0.01 | 0.02 | 0.39 | 0.45 | 0.53 | **0.56** |

## Slopes stop at the angle loose rock stands at

They did not before — the 95th percentile stood at **46°** where soil cannot exceed about **33°**,
its friction angle. (The studio measured 40.03° for dry lunar regolith by *growing* a sandpile in
`core/trainables/granular.py`; wet weathered soil is shallower.)

Plain diffusion cannot fix that, because `q = D·S` only smooths — double the slope, double the flux,
and nothing ever stops it. Real hillslopes are **non-linear** (Roering, Kirchner & Dietrich 1999):

```
q_s  =  D·S / (1 − (S/S_c)²)
```

As the slope nears the critical angle the flux runs to **infinity**, so the slope cannot get there:
the hillside sheds material as fast as it is delivered. **That is what an angle of repose is** — not
a clamp applied afterwards, but a transport law that refuses.

It also has to be **sub-stepped**. An explicit diffusion step is stable only while `D·dt/dx² < 0.25`,
and the moment the runaway multiplies `D` by fifty the scheme detonates: relief of 10⁶³ metres and
every slope at 90°, which is not a steep landscape but a numerical explosion wearing one.

**Now: 24.4° at the 95th percentile, under the 33° limit, with 451 m of relief over 12 km.**

## What it does hand on

Height at **true scale** — a few hundred metres of relief over twelve kilometres needs no
exaggeration, which makes this the first membrane in the whole story that can say so. A latitude
(31°, the middle of the temperate band the climate solved for). And the gravity to stand in.

*Contained in `theTerrain`. What it hands on: ground, at the size of a walk.*

## The octaves below the grid  (2026-08-01)

A 128 grid over twelve kilometres puts Nyquist at 93.75 m. Nothing smaller than a football field
could exist here — not by choice, by construction — and that one number explained everything the
patch was accused of. It rendered as a tabletop diorama because at 93.75 m a cell it *was* one.

The law was never wrong. Measured against a generated reference take of this same patch, the clay
render's spectral slope is −3.14 against the take's −3.01: within four percent. What was wrong is
that a scale-free law was being evaluated over one decade of scale.

So the spectrum is continued below the grid, and every part of the continuation is measured rather
than picked:

- **β comes off this membrane's own eroded surface** — 2.54 — so the octaves continue what erosion
  produced instead of decorating it.
- **The falloff follows from β.** Amplitude per octave goes as k^(1−β/2), which is 0.83 here. Not
  the 0.5 the starting canvas uses: erosion steepens the spectrum it was handed.
- **The level comes from the friction angle**, because β < 3 means slope grows without bound as
  wavelength falls and the spectrum therefore *cannot* set it. Bisection finds the largest level at
  which `slopes_below_repose` — a check this membrane has always published — is still true.

That last one turned out to be the finding. The level lands at **0.051**: the spectrum wants about
twenty times more sub-grid relief than the ground can physically stand, and the friction angle cuts
it back. That is not a fudge, it is the threshold-hillslope regime every talus cone sits in — below
some scale, terrain stops being spectrum-limited and becomes friction-limited.

Five octaves reach from 46.9 m down to 2.9 m, where **theGround** takes over at four metres across.
A membrane resolves to its child's extent and stops; asking this one for a pebble is asking the
wrong membrane.
