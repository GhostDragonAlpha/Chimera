# theGrip

> **chapter 23** of the story  ·  **t = 5.75715e+15 s** since theZero  ·  lasts **0.644 s**
>
> *The serial is the place in TIME, not in the folder tree. A path says what contains
> what; this says what follows what. Both are published — `timeline_serial` in
> numbers.json and here — so the story and its numbers cannot disagree about when.*


**In plain words —** The hand does not aim its fingers at a place. It **closes until it cannot**, and
whatever it ran into decides where the fingers stopped and how hard they now have to squeeze. So there
is one GRAB, and a pin and a bowling ball are the *same command* with different answers.

*The chapter with no poses in it.* One inequality, six objects, and 0.64 seconds.

## Whether it holds is friction, not strength

An object pinched between two pads does not fall while

`n · μ · F_grip  ≥  m · g`

— `n` opposing surfaces, each returning `μ` times the force pressed into it, against the weight hanging
off them. Read it once and the whole chapter is implied.

- **The squeeze scales with the object's mass, and inversely with its surface.** So *a slippery light
  thing is harder than a grippy heavy one*, which is not what "strength" suggests at all.
- **Nothing in it mentions a finger, a pose, or a hand.** Positions are outputs. There is no place in
  this file where a grasp position is computed, because none is needed.
- **The only body-side term is the ceiling on `F_grip`.** Which is why *"can I hold this"* has an
  answer before any geometry exists.

## One command, six objects — the table is the proof

Same law, same body, same world. Every mass is sourced or derived; nothing on this list was invented
to make the point come out. The surface varies as hard as the mass does, and that is the argument.

| object | mass | surface | μ | slip threshold | with a 25% margin | grip it forces |
|---|---:|---|---:|---:|---:|---|
| a steel pin | 0.067 g | polished steel | 0.60 | **0.19 mN** | 0.23 mN | tip pinch |
| a one-kilogram hand tool | 1.000 kg | silicone grip | 0.61 | 7.56 N | 9.45 N | tip pinch |
| a full water ration | 1.915 kg | bare aluminium | 0.60 | 14.71 N | 18.39 N | tip pinch |
| **the same ration, soaped** | **1.915 kg** | soaped aluminium | **0.15** | **58.84 N** | 73.55 N | tip pinch |
| a regulation bowling ball | 7.258 kg | polished coverstock | 0.37 | 90.42 N | 113.03 N | **key pinch** |
| the pressure suit itself | 9.915 kg | suit fabric | 0.46 | 99.36 N | 124.20 N | **power grip** |

**Rows three and four are the chapter.** Same object, same mass, same planet, one of them soaped —
and the squeeze it needs goes up **exactly four-fold**, because 0.60/0.15 is four. Nothing about the
body changed. *"Can I hold it" is a fact about the surface.*

And the last column was never designed. The **force** law picks the weakest grip whose measured
ceiling covers the job, and that alone reproduces the controller map's *"pin → pinch; ball → two-hand"*
from a friction coefficient and a dynamometer table. **The masses span 148,898 : 1 and the required
squeeze spans 531,411 : 1** — the answer spreads *wider* than the objects do.

## The ceiling, and what it forbids

Maximum voluntary force, **Mathiowetz 1985**, men aged
30–34, dominant hand. That cell and not another: theHuman's body **is** the ANSUR-II male median, and
ANSUR-II's male mean age is 30.2 years. The demographic is matched, not chosen.

| grip | max | what it can hold here |
|---|---:|---:|
| tip pinch (thumb–index) | **78.3 N** | 8.4 kg |
| palmar pinch (three-jaw) | 109.9 N | 11.8 kg |
| key pinch (lateral) | 117.4 N | 12.6 kg |
| **power grip (whole hand)** | **541.8 N** | **58.3 kg** |
| two-handed power grip | 1083.6 N | 116.6 kg |

Your hand squeezes with **81% of your own body weight**. And the consequence is already in the table
above: at 113 N the bowling ball is **not holdable in a fingertip pinch** — it needs a key pinch or
better. That is a real rule of play derived from a friction coefficient and a 1985 dynamometer, rather
than authored as a difficulty setting.

> ### The check nobody fitted — a different instrument, a different population, a different decade
>
> Mathiowetz measured 310 men in Milwaukee in 1985. **NHANES** measured **14,984 people** aged 6 to 80,
> both sexes, in 2011–2014, with a different protocol. An adult male's best hand ought to land near the
> **95th percentile** of that mixed population.
>
> NHANES p95 = **545.7 N**. Mathiowetz men-30-34 = **541.8 N**. **Ratio 0.993.**
>
> Two cycles of NHANES agree with each other to 0.4% (545.7 and 547.2 N), which is what says the
> instrument is real and not a coincidence. Neither number was adjusted toward the other.

## μ is not a constant, and that is the second half

**Carré 2017** fitted **every** finger-surface condition it
tested with a power law, `COF = a · N^b`, and Zhang & Mak found the same sign independently. It is not
a fit looking for a reason — it falls out of contact mechanics:

> a soft pad on a flat makes a Hertzian contact of area `A ~ N^(2/3)`; adhesive friction is a shear
> strength times that area; so `μ = τA/N ~ N^(−1/3)`.

The exponent is **derived**. Put it back into the inequality and the required grip stops being linear
in the load:

`F_min = [ W / (n·μ_ref) ]^(3/2) / √F_ref`   → **three halves.** Twice the weight needs **2.83×** the
squeeze.

**It also eats the safety margin.** Capacity goes as `F^(2/3)`, so squeezing 25% harder buys only
**16.0%** more friction — **36% of the margin you asked for evaporates into the μ you destroyed by
asking for it.** *The margin you feel is not the margin you get.*

### …and the honest scope of all that

μ only *slides* between its two clamps. Converted into mass on this world, the superlinear regime is:

| | |
|---|---:|
| below | 0.042 kg — μ is pinned at its measured ceiling, 1.26 |
| **the three-halves law rules between** | **0.042 kg and 0.292 kg** |
| above | 0.292 kg — the pad has flattened, μ is pinned at 0.476, and the schoolbook linear law returns |

**Zero of the six objects above are in that band.** The 3/2 law is real, derived, and it governs a
pen, a switch, a sample vial — the light end, where friction sensing matters most. Everything on this
chapter's own table is heavier than 292 g, so the linear law is what actually runs on it. Worked at the
middle of the band (110 g): **0.504 N** by the real law against **0.629 N** if μ were held constant —
a 20% error, in the direction of *needing less*, because at that squeeze μ is higher than its reference.

**The clamps are not tidying-up.** Unclamped, the power law hands a dressmaker's pin — held with about
0.19 mN — a coefficient of friction of **thirty**. Extrapolating a power law past its data is how you
get a number that is dimensionally legal and physically absurd.

## Gravity is a dial, and only some things move

Everything in the law scales with `g`. **μ does not** — it is a property of two surfaces. **The
ceiling does not** — it is a property of a body. So each object has a gravity at which the force it
needs crosses the force the hand has, and the number is a fact about the *pair*.

| object | needs here (7.076) | needs on Earth (9.807) | drops from a pinch above | drops from a power grip above |
|---|---:|---:|---:|---:|
| a steel pin | 0.19 mN | 0.26 mN | — never in range | — never in range |
| a one-kilogram hand tool | 7.56 N | 10.47 N | 58.6 m/s² | 405.8 m/s² |
| a full water ration | 14.71 N | 20.39 N | 30.1 m/s² | 208.5 m/s² |
| the same ration, soaped | 58.84 N | 81.54 N | **7.53 m/s²** | 52.1 m/s² |
| a regulation bowling ball | 90.42 N | 125.32 N | **4.90 m/s²** | 33.9 m/s² |
| the pressure suit itself | 99.36 N | 137.70 N | 4.46 m/s² | 30.9 m/s² |

Two predictions this was never fitted to:

- **The soaped ration drops from a fingertip pinch above 7.53 m/s².** This world is 7.076. It is held
  here by a margin of 6%, and **on Earth the same wet canteen falls out of the same pinch.** Move the
  planet and the object changes hands.
- **A bowling ball leaves a pinch above 4.90 m/s²** — so it is a two-finger object on the Moon and a
  whole-hand object everywhere warmer. That is the controller map's contextual variant, derived.

Everything on Earth costs **1.386×** what it costs here — `9.807/7.076` exactly, because in the
flat-μ regime the law is linear and the ratio has to be the gravity ratio. It is a small check that the
plumbing is real: change `g` at the top and every force below moves, in proportion.

## The clock is neural, and it does not move with gravity

| | |
|---|---:|
| slip onset → motor correction | **74 ± 9 ms** (Johansson & Westling 1987) |
| contact detected | 74 ms |
| preload phase | ~100 ms |
| load phase, to lift-off | ~100 ms |
| slip check and up-rate | 74 ms |
| **the grasp itself** | **0.348 s — 4.7 tactile loops** |
| approach (free; 4 loops) | 0.296 s |
| **one whole grasp** | **0.644 s** |

**Double the planet's gravity and this table does not change by a millisecond.** Every force above
doubles; the clock is set by an afferent nerve and a synapse. A membrane whose duration moves with `g`
would be wrong, and this one is checked for it.

### The stop condition is too slow to close the hand — so the approach cannot be feedback

A grasp is a *stop-condition* process, so ask what it would cost to run the **closing** that way. To
stop within the pad's own compliant travel — about a millimetre — the pads may not move more than a
millimetre per decision. Closing a 0.302 m aperture that way is **302 decisions at 74 ms = 22.4
seconds.**

Real grasps take **0.64 s**. Thirty-five times too fast.

**Therefore the approach is feed-forward and the tactile loop only corrects.** That is exactly what the
Johansson school found from the other end — sensorimotor memory, and the famous result that the *first*
lift of an object whose weight was secretly changed is clumsy and the second is not. This chapter
arrives at it from a latency and a millimetre, having been told neither.

## The mag-boot is the same inequality with the object set to the body

The stub that stood here asked whether mag-boot adhesion beats the body weight it holds against a
sheer face. It does not need its own physics. On a wall, gravity runs **along** the sole instead of
into it, the sole is **one** contact instead of two, and the object being held is **you**:

`1 · μ · F_clamp ≥ m · g` → `F_clamp = m·g/μ`

Body weight here is **668.7 N**, so:

| boot-sole μ | clamp force | in body weights |
|---:|---:|---:|
| 0.37 | 1807 N | 2.70× |
| 0.46 | 1454 N | 2.17× |
| 0.62 | 1079 N | 1.61× |

**The answer to the stub's question is: the clamp must press with roughly two to three times body
weight**, and *"can it grip regolith at all"* is now a question about a single number rather than about
a mechanism. **This is a parameterisation, not a prediction** — boot-sole-on-rock μ is the one friction
number this chapter could not source (see below), so the row is given across a range on purpose.

## What you are looking at

Five grasps running at once, on **one command**. Left to right in order of the squeeze each needs.

The pads close at **the same rate at every station.** Nothing tells them where to stop. They stop where
the *object* is — so the bowling ball halts them at 11% of the approach and the pin not until 46%, and
those five contact moments are five different times inside one movie produced by one instruction. That
is the operator's law, drawn: **the stop comes from the object's size, never from a keyframe.**

Then the force rises and each pad presses *into* its object by an amount read straight from
`grip_applied_N / tip_pinch_max_N`. The pin barely dimples. The soaped ration is crushed.

Under each station are **two bars against one yellow ceiling line** — the slip threshold and the force
actually applied. **The gap between them is the safety margin**, drawn rather than described. When the
taller bar overtops the ceiling, that object is about to be on the floor, and the bowling ball duly
leaves the pinch and falls — at 7.076 m/s², not at a rate anyone picked.

**The objects' colours are their friction.** Slick is pale and cold, grippy is dark and warm. That is a
measurement of μ, not a decision about how a bowling ball ought to look.

**One declared exaggeration, and it scales what exists rather than minting anything.** The real
diameters span 360 : 1 — a pin beside a bowling ball is a third of a pixel. The drawn radii are on a
**log remap** of that true range, so the ordering and every contact moment are real and only the ratio
is compressed. Every circle on screen is a row of the published table.

## What this still gets wrong

- **Grip endurance is not traced at all.** Everything here is maximum *voluntary* force — a one-off
  squeeze against a dynamometer. How long it can be held is not modelled, and *a grip you cannot
  sustain is a grip you do not have.* The bowling ball at 113 N of a 117 N key pinch is "holdable" in
  this chapter and would be on the floor in about ten seconds in life. **This is the largest hole.**
- **The safety margin's 10–40% band is second-hand.** Johansson & Westling define the margin and
  measure it per subject, but their abstract states no percentage and the full text was not reachable
  from here. So the margin is carried as a **free** number over that band rather than typed as a
  constant — which is the honest place for a figure like that, and it means the number is trainable
  the moment a real distribution turns up.
- **Boot-sole-on-rock μ is not sourced.** Elkington 2024 is downloaded and is about precisely this, but
  its coefficients live in tables the local copy does not contain. Hence the range above.
- **The fingerpad's ~1 mm compliance is an order of magnitude, not a measurement.** It appears only in
  the feed-forward argument, which survives a factor of several either way — 22 s could be 5 s or 90 s
  and the conclusion would be identical. Said out loud anyway.
- **Everything is bare skin.** theHuman's suit is sealed but **not pressurised** — `P_surface` is above
  the Armstrong limit, so no pressure shell is needed and the glove is a thin one. That branch is read
  from the parent rather than assumed. But Carré's gloved-finger coefficients are figure-only in the
  local PDF, so even the thin-glove correction is not applied; and if the planet's pressure ever fell
  below the Armstrong limit, **the pressurised-glove penalty is untraced and the whole table would be
  wrong.**
- **Friction here is one number per pair of surfaces.** Real skin friction moves with hydration, with
  sweat, with temperature and with time-in-contact; Zhang & Mak's own palm figure is 0.62 ± 0.22, which
  is a ±35% band this chapter reports and then ignores. Every force above should be read with it.
- **Only static friction, and only a hanging weight.** No torque about the grip axis, no shear from
  acceleration, no tangential loads from swinging the thing — all of which a real hold has to survive
  and all of which raise the required force.
- **A hook is not a grip.** Hanging from a bar by the fingers is *form* closure, not friction, and this
  law says nothing about it. It will say something wrong if asked.
- **The grip ladder's lower bound only.** Force says which grips are strong enough; **geometry says
  which ones fit**, and geometry is theHand's, unread. The force law alone claims a fingertip pinch
  could hold 8.4 kg, which at the density of water is a **25 cm sphere** — larger than a bowling ball,
  and impossible to span. That absurdity is left standing on purpose: it is the exact shape of the seam
  between two sibling membranes, and it says plainly that neither can answer alone.

*Contained in `theHuman`. What it hands on: one GRAB, and the object's own answer to it.*
