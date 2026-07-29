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

## ⚠ It fails its own test, and that is recorded rather than tuned away

Real rivers obey **Hack's law** — measure a basin's area against the length of its longest stream and
`L ~ A^0.57`, on every continent, since 1957. It is not put into this simulation anywhere, which is
exactly why it is the test worth running.

| | |
|---|---|
| measured here | **0.19** |
| required | 0.50 – 0.65 |

**So by this membrane's own standard, what it makes is not yet a drainage network.** It is not noise
either — the incision is real, the water reaches the sea, and the valleys are carved rather than
drawn. But the branching is not organising the way running water organises, and I have not found
why. The strongest suspect is the **flats**: filling a hollow leaves a surface with no gradient, and
508 cells still have nowhere downhill to send their water.

Slopes fail too: the 95th percentile stands at 46° where loose rock cannot exceed about **33°**, its
friction angle. (The studio measured 40.03° for dry lunar regolith by *growing* a sandpile, in
`core/trainables/granular.py`; wet weathered soil is shallower.) The hillslope term is too weak to
hold the limit.

Both are left failing in `measure()`. Widening a tolerance until the check passes is the one move
this project forbids, and a membrane that fails its own test honestly is worth more than one that
passes a weakened one.

## What it does hand on

Height at **true scale** — a few hundred metres of relief over twelve kilometres needs no
exaggeration, which makes this the first membrane in the whole story that can say so. A latitude
(31°, the middle of the temperate band the climate solved for). And the gravity to stand in.

*Contained in `theTerrain`. What it hands on: ground, at the size of a walk.*
