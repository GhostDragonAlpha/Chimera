# theLoad

<!-- CHIMERA-LAW -->
> *Derive before you train — [THE LAW](../../../../../../../../../../../../../../../../../docs/THE_LAW.md). Every number below is derived from the parent's or measured; none is chosen.*
<!-- CHIMERA-LAW -->

> **chapter 34** of the story  ·  **t = 5.75715e+15 s** since theZero  ·  lasts **28800 s**
>
> *The serial is the place in TIME, not in the folder tree. A path says what contains
> what; this says what follows what. Both are published — `timeline_serial` in
> numbers.json and here — so the story and its numbers cannot disagree about when.*


**In plain words —** A body with something on its back is a **different body**: heavier, higher
centred, leaning forward, and burning a third more fuel to go the same distance at the same speed.
Nothing about that is designed. One added mass, at one added height, at one added distance behind the
spine — and everything else on this page is arithmetic done to those three numbers.

*The membrane that turns picking something up into a consequence.* Its film is **eight hours**: one
excursion, a hopper filling the whole time, and the limits crossed in the order the physics puts them
in.

## The one input

`theHuman` walks at 94.50 kg — 84.59 kg of person and **9.91 kg of suit, which is already a load.**
Add cargo of mass `m` at height `h`, standing `x` behind the body's own centre line, and there is
exactly one new centre of mass:

`H_c = (M·H + m·h) / (M + m)`

Everything below is that line, differentiated, inverted, or compared against something somebody
measured.

| | |
|---|---|
| the person | 84.59 kg |
| the suit, already carried | 9.91 kg — **11.7% of body mass before you pick anything up** |
| cargo, at the default 30% | 25.38 kg |
| total on the feet | **119.88 kg** |
| its volume, as broken basalt | 13.6 litres |
| the pack it makes | 41.5 cm wide × 37.8 cm tall × **8.6 cm deep** |
| centre of mass, was | 1.0091 m |
| centre of mass, now | **1.0601 m** (+5.1 cm) |
| forward lean it forces | **1.94°** |

The pack's width, its span and its standoff are **not chosen** — they are ANSUR II medians of this
same 1.755 m man (n = 4,082): shoulders 415 mm apart, iliac crest at 1061 mm, acromion at 1439 mm,
torso 253 mm deep. A pack wider than the shoulders fouls the arms; a pack below the iliac crest has
nothing to sit on.

## The lean is exact, and volume is why it exists

Pivot at the ankle, lean the rigid assembly forward by `φ`, and set the combined centre of mass over
the ankle — which is what standing up *means*:

`tan φ = m·x / (M·H + m·h)`

No small-angle anywhere. Note the denominator: **a load carried high resists the lean it causes**,
because its own height appears in the restoring term.

And this is where **volume** finally earns its place in a chapter about mass. `x` is half the torso's
depth plus half the pack's, and the pack's depth is `V / (width × span)`. So:

| same 25.38 kg, different cargo | density | pack depth | lean |
|---|---:|---:|---:|
| broken basalt | 1871 kg/m³ | 8.6 cm | **1.94°** |
| loose insulation, foam, empty crates | 300 kg/m³ | 53.9 cm | **4.52°** |

**Two loads of the same mass do not cost the same.** The bulky one stands further off your back, and
the lean more than doubles.

## Which stability effect wins — and it is neither of the two you would name

A pack raises the centre of mass, so `ω₀ = √(g/H)` **falls** and the body topples more slowly. That
sounds like a safety margin. It is not one, and the reason is a cancellation:

- time before a lean runs away: `1/ω₀` — grows by **2.50%**
- distance your foot must reach to catch it at speed `v`: `v/ω₀` — grows by **2.50%**

The same `1/ω₀` is in both. **The extra time is exactly the extra ground to cover**, and their ratio
is still `v`. Nothing was bought. The margin moves only because the **foot did not get bigger**.

And that geometric effect is not the main event anyway:

| | unloaded | +25.38 kg | change |
|---|---:|---:|---:|
| topple time | 0.3776 s | 0.3871 s | +2.5% |
| lean limit (centre of pressure reaches the toe) | 9.87° | **9.41°** | **−4.7%** |
| biggest shove you can take standing | 0.4651 m/s | **0.4537 m/s** | **−2.4%** |
| ankle torque demanded at that limit, vs push-off | 1.346× | **1.707×** | **+26.9%** |

**The mass beats the geometry by 5.7 to one.** The lean limit is pure geometry — mass cancels out of
it, because both the toppling moment and the restoring ground reaction are proportional to weight —
so the load's height costs you 5%. The load's *mass* costs the ankle 27%, and the ankle is the thing
that has to do the work.

There is one gravity where that argument changes sides. The toe lever is fixed by the foot; the lever
the ankle's own walking torque can hold is `τ/(Mg)`, and it grows as gravity falls. They are equal at
**4.15 m/s²**. Here, at 7.08, the body is above it and strength is in the argument. On the Moon it
would be below it: balance there is pure geometry and strength is free — which is why lunar falls
were a **balance** problem and not a strength one.

## What it costs

Pandolf, Givoni & Goldman (1977) — the US Army's load-carriage equation, fitted on treadmills, still
the standard:

`M = 1.5W + 2.0(W+L)(L/W)² + η(W+L)(1.5V² + 0.35VG)`   [watts; kg, kg, m/s, % grade]

### The first thing it predicts is something nobody put in it

Climbing at `V` m/s on a grade of `G` percent lifts `(W+L)` kg at `V·G/100` m/s. That is
`0.0981(W+L)VG` watts of **mechanical** power on Earth. Pandolf's **metabolic** coefficient for the
same term is 0.35. The ratio is the efficiency with which muscle turns fuel into height:

`0.0981 / 0.35 = ` **0.2802**

**28.0%.** The measured efficiency of positive muscular work in walking is 25–30%. Nothing was fitted
to that — 0.35 came out of a regression against oxygen uptake — and it is the single fact that
licenses taking this equation to another planet, because it says the grade term is *exactly*
proportional to `g`.

### The cost, at this gravity, on light brush, on the level

| | watts |
|---|---:|
| standing metabolism | 114.8 |
| the load penalty | 30.1 |
| walking | 182.5 |
| **total** | **327.4** |
| the same body carrying nothing at all | 243.6 |
| **what the cargo and suit cost** | **+34.4%** |
| what this body can hold for eight hours | 437.6 |
| **effort, as a share of that ceiling** | **74.8%** |

A 10% grade takes it to **689.9 W** — well past the ceiling. *You can carry this load on the flat all
day and you cannot carry it up a hill.*

## The famous 20–30%, and where it actually is

**It is not a kink in the cost curve, and anybody who says it is has fitted it.** Pandolf's load term
is a polynomial in `L/W`; polynomials do not have knees. Here is the curve, and it is smooth:

| cargo | carried, as a fraction of body mass | metabolic W | **W per kg carried** |
|---:|---:|---:|---:|
| 0 kg | 0.117 | 260.6 | 1.711 |
| 8.46 | 0.217 | 278.6 | 1.904 |
| 16.92 | 0.317 | 300.6 | 2.125 |
| 25.38 | 0.417 | 327.4 | 2.375 |
| 33.84 | 0.517 | 359.7 | 2.655 |
| 42.29 | 0.617 | 398.3 | 2.963 |
| 50.75 | 0.717 | 443.8 | 3.300 |

The knee is in the **marginal** comparison instead. Differentiate the cost with respect to the load,
differentiate it with respect to body mass, and subtract. Every term carrying `η`, `V` or `G`
multiplies `(W+L)` linearly and **cancels identically**, leaving one equation in one unknown:

`2·b·f·(1+f)² = a`     where `f = L/W`, `a` is the rest coefficient and `b` the load coefficient

That is the load fraction above which **one more kilogram in the pack costs more than one more
kilogram of you**. Below it, carrying is a better deal than being heavier; above it, it is a worse
one. With Pandolf's own `a = 1.5` and `b = 2.0` and nothing else, on Earth:

### **f = 0.243.**

The literature band, from soldiers and from Nepalese and African porters, is **20–30%**. It was not
fitted, it was not read off a graph, and no number in this chapter was tuned toward it.

**And it moves with gravity, which nobody has measured.** `a` is chemistry — the split between the
part of standing metabolism that is chemistry and the part that is holding yourself up comes from
NASA CR-1726's own table (lying 290 Btu/hr, standing 440 Btu/hr, same man) — and `b` is weight. Lower
gravity, higher knee:

| world | g | knee, as a fraction of body mass | **cargo this body may carry economically** |
|---|---:|---:|---:|
| Moon | 1.62 | 0.619 | 42.5 kg |
| Mars | 3.71 | 0.399 | 23.8 kg |
| **here** | **7.076** | **0.285** | **14.19 kg** |
| Earth | 9.807 | 0.243 | 10.62 kg |

An Apollo crewman carried more than his own body mass in suit and backpack, and this equation does
not call that extravagant.

**The suit eats 41% of the whole budget before the hopper is opened.** Fourteen kilos of ore is the
economical carry on this world. That is not a design decision; it is what is left after the suit.

## The check that is not ours

NASA TN D-7883 (Waligora *et al.*, March 1975) reports **158.76 hours of Apollo 11–17 lunar surface
EVA**, measured three independent ways — heart rate, oxygen consumption, and liquid-cooled-garment
heat balance — and integrated. Table I's mean, all activities, all missions: **980 kJ/hr = 272 W.**

Run a suited Apollo crewman (75 kg of person, 82 kg of suit and PLSS, 0.9 m/s) through the same four
terms:

| | watts | vs measured |
|---|---:|---:|
| **NASA measured, mean of 158.76 h** | **272** | — |
| Pandolf **with** the gravity scaling, η 1.5–1.8 | **259 – 282** | **brackets it** |
| Pandolf **without** it — the equation as published | 774 | **2.84× too high** |

The report is from 1975. The equation is from 1977. The gravity scaling is derived on this page. It
was never fitted to any of it, and **without the scaling the answer is wrong by a factor of nearly
three** — which is the strongest evidence available that the scaling is physics and not decoration.

## The same load on Earth

One number moved. Nothing about the person changed.

| | here (7.076) | Earth (9.807) |
|---|---:|---:|
| comfortable speed (Froude-similar) | 0.998 m/s | 1.175 m/s |
| metabolic rate, same 35.3 kg carried | **327.4 W** | **466.3 W** |
| within the 8-hour ceiling? | **yes** (75%) | **no** (107%) |
| economical cargo | 14.19 kg | 10.62 kg |
| cargo the lungs allow for 8 h | 49.68 kg | 19.50 kg |
| biggest shove you can take | 0.454 m/s | 0.534 m/s |
| under the boot | 30.7 kPa | 42.5 kPa |

**The same pack that is a normal day's work here is over the line on Earth.** That is the whole
argument for the gravity dial: one law, every world, and it says something different on each.

## What the ground says

`theHuman`'s boot sits at 24.19 kPa against 110.35 kPa of bearing capacity — a margin of 4.56. With
the pack it is 30.69 kPa and a margin of 3.60.

| | cargo | |
|---|---:|---|
| the boot **punches through** — ultimate bearing capacity | **336.6 kg** | never happens |
| the boot **takes a print** — allowable, at the standard factor of safety 3 | **49.2 kg** | happens |

So the stub's own question — *does theGround's bearing capacity ever actually bite, or is the margin
always 5×?* — has an answer, and it is **yes, but only once you stop asking when the ground fails and
start asking when it yields.** No foundation on Earth is designed to its ultimate; the convention is
a third of it, and a third of it lands at 49 kg, inside the range a person actually carries.

And the terrain factor, asked to say something physical, says a depth. If all of `(η−1)` is the work
of compacting ground under the boot, then per step it is `N·z`, the whole mass cancels, and

`z = (η−1)·k_v·v² / (g · cadence)`

| ground | η | boot sinks, per step |
|---|---:|---:|
| blacktop | 1.0 | 0 |
| dirt road | 1.1 | 10.6 mm |
| light brush | 1.2 | 21.2 mm |
| heavy brush | 1.5 | 53.1 mm |
| swampy bog | 1.8 | 85.0 mm |
| **loose sand** | **2.1** | **116.9 mm** |

Boots really do sink about that far in deep sand. Nothing was fitted; the number came out of a
metabolic coefficient.

## What you are looking at

Eight hours. The hopper fills the whole time.

The **shell** of the pack is fixed — shoulder-wide, hip belt to shoulders, and as deep as this cargo's
density forces it to be. The **contents** rise inside it. The bright mark is the **combined centre of
mass**, and it climbs because the contents' own centroid climbs; the pale trail behind it is where it
has been, so the rise is drawn by the thing doing it. The body **leans forward** to put that mark back
over the ankle — the lean is `atan(m·x/(M·H+m·h))`, recomputed at every instant, not keyframed. The
two pale lines from the ankle are the **lean limit**, `atan(toe/H_c)`, and they close as the mark
rises: the gap between them and the leaning trunk *is* the margin. The column at the right is what it
is costing, against a tick at what this body can hold for the eight hours the film runs.

At the default load the film crosses exactly one line, at **4 h 28 m** — the economic knee. The lungs
and the ground would be crossed at 15.7 h and 15.5 h, which is to say: not today.

## What this still gets wrong

- **The terrain factor is in the wrong place.** `η` is a property of the **ground**, and it should
  arrive down the chain from `theGround` through `theHuman`. Neither publishes one, so it is a dial
  here with Soule & Goldman's measured values as its range. This is the one number in this chapter
  that is in the wrong membrane, and it is a *sibling's number typed locally* — the exact failure
  this project has a rule about. Recorded rather than hidden.
- **Nobody has measured a terrain coefficient off Earth,** and holding `η` fixed makes the sinkage
  come out *gravity-invariant* — 116.9 mm in loose sand at Earth and at 7.08 alike. That cannot be
  true: a lighter foot presses less. The invariance is an artifact of the assumption, not a result,
  and the gravity ladder's sinkage column should be read as "if the ground behaved identically",
  which it will not.
- **Three of the four gravity scalings are arguments, not results.** Only the grade term's `g¹` is
  derived (from its own 28% efficiency). The rest term's split is derived from a measurement but the
  interpretation is mine; the load term's `g¹` is asserted because it is weight being stabilised; the
  speed term's `g^0.5` is dynamic similarity — the same Froude argument the rest of this story walks
  on, and no reduced-gravity load-carriage calorimetry exists to check it. The Apollo bracket tests
  all four at once and passes, and that is the only test any of them has had.
- **The lean under-predicts.** 1.94° at 30% of body mass; measured trunk flexion with a loaded pack
  runs 5–7°. Two reasons, both real: this model puts the pack's centre of mass only 17 cm behind the
  body's, and real walkers lean more than statics requires because they are anticipating, not
  balancing. The static law is right and it is not the whole lean.
- **The parent's centre of mass does not know about the suit.** `theHuman` publishes
  `com_height_m = 0.575 × stature`, the bare anthropometric figure, while its `mass_kg` already
  includes 9.91 kg of suit. This chapter's own law, applied to the suit, would raise that by about
  1.5 cm. The parent's number is consumed exactly as published and the discrepancy is named here
  rather than quietly corrected — a child consumes its parent's numbers, not its parent's reasoning.
- **The Apollo body and EMU masses are the only two literals in this chapter that are not in this
  repository.** 75 kg and 82 kg are widely documented but not in a file here, so the comparison is
  published as a bracket with its sensitivity rather than as a point value.
- **The ankle torque is a walking number.** `theHuman` publishes the plantarflexor moment at
  push-off, not a maximum voluntary contraction, so the "ankle demand ratio" above says *how much
  more than a step costs* — not *how close to failure*. A real maximum would be roughly twice it.
- **Heel strike is not in the pressure.** The foot pressure here is over the whole sole. At heel
  strike the contact patch is a fraction of that and the peak pressure is several times higher, and
  nothing in this chapter derives the patch — that needs an elastic contact model and two moduli
  neither membrane has.
- **No spine.** A load has to be carried *through* something, and the compressive load on the lumbar
  spine is the reason 30% of body mass is a doctrinal limit rather than the 24% economics gives. That
  is a different membrane and it does not exist.
- **Downhill is refused, not modelled.** Pandolf has no eccentric-work term and over-predicts on
  descents, so the grade dial is clamped at zero. Going down is a real cost and this chapter cannot
  say what it is.

*Contained in `theHuman`. What it hands on: that a body is what it is carrying, and four different
numbers that stop you — the economics at 14 kg, the lungs at 50, the ground at 49, and the soil
failing at 337, which never happens.*
