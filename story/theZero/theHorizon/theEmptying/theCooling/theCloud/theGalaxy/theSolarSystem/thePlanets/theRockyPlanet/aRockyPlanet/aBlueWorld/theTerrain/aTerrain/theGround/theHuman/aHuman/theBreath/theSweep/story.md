# theSweep

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
> **[docs/THE_LAW.md](../../../../../../../../../../../../../../../../../../../docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 25 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

> **chapter 33** of the story  ·  **t = 5.75715e+15 s** since theZero  ·  lasts **13.2437 s**
>
> *The serial is the place in TIME, not in the folder tree. A path says what contains
> what; this says what follows what. Both are published — `timeline_serial` in
> numbers.json and here — so the story and its numbers cannot disagree about when.*


**In plain words —** The draught across the inside of the faceplate. The parent proved a fan has to
exist and then refused to size it; this sizes it. And the answer is decided not by the lungs but by
**the one part of the suit that cannot be insulated, because you have to see through it.**

*The smallest membrane in the story.* Thirty-one centimetres of plate, and its film is a fogged
visor clearing.

## Why a faceplate is the weak point

Every other part of this suit wears the 12 mm of batting `aHuman` solved for. The visor wears none.
So it is a **cold bridge by construction**, and its inner surface sits where a series resistance puts
it — the sweep's film inside, 3 mm of polycarbonate, the weather outside:

| | |
|---|---|
| loop | 22 °C |
| **inner face of the visor** | **13.4 °C** |
| weather | 6.0 °C |
| U through the plate | 6.50 W/m²K |

Nine degrees below the gas it faces. And a person is breathing 30 grams of water an hour into that
gas. **Saturation at 13.4 °C is 0.0153 bar**, and the moment the loop's vapour pressure passes it,
the plate is wet — which is not a cosmetic problem, because condensate *scatters*. Fog does not darken
a view, it whites it out.

## Two ceilings, and they nearly coincide — which is luck, not law

There are two independent reasons to keep gas moving, and both reduce to the same algebra: a
well-mixed loop with a perfect scrubber downstream settles at concentration `c = production / Q`, so
a partial-pressure ceiling *is* a minimum flow.

| what sets it | ceiling | flow it demands |
|---|---|---:|
| the lungs — CO₂ under 0.010 bar | physiology | **21.1 L/min** |
| the visor — vapour under saturation at 13.4 °C | thermodynamics | **21.1 L/min** |

**Those agree to 0.2%, and I want to be blunt: that is a coincidence of this world's numbers, not a
principle.** It happens because the ratio of what a body exhales (water to CO₂, 1.53) lands on the
ratio of the two ceilings (0.0153 to 0.010, also 1.53). Nothing connects them. Cool the weather and
the visor gets colder, saturation drops, and the visor wins outright; warm it and the lungs take over.
The code returns `agreement_is_coincidence: True` so nobody later mistakes it for a result.

Here, marginally, **the visor binds.** The flow is then flown with margin — 2.5× the floor, which is
the one judgement in this chapter rather than a consequence — giving **52.8 L/min**.

## The fan is almost free, and that is the surprise

The thing that *must* exist turns out to cost nothing worth carrying:

| | |
|---|---|
| pressure drop round the loop | 800 Pa |
| **fan power** | **2.0 W** |
| over an eight-hour day | 16 Wh |
| **battery to run it** | **65 g** |

Sixty-five grams, against **770 g of lithium hydroxide** and **1.15 kg of oxygen bottle**. The fan is
**8%** of the scrubber's mass and it is the component without which none of the rest works. Worth
knowing when something has to be cut.

## One identity, and this one is real

At the minimum flow, the time for the visor to fog with the fan **off** equals the time for the loop
to turn over **once**. Not approximately — identically, because both quantities are

`V · p_sat / (water rate · P)`

and that is the same expression written twice. Both come out **34 seconds**.

**That is the cleanest possible statement of what a sweep is for:** the fan's entire job is to be
faster than fogging, and the floor is exactly the speed where it draws level. At the 2.5× margin it
clears in 13.6 s against a 34 s fog — **2.5× faster than the plate can go blind**, which is the same
2.5 and not a second one.

It also means the failure mode is knowable to the second. **Lose the fan and you have half a minute
of sight.**

## It audits its grandparent

`aHuman` solved its coat thickness by putting the *whole* metabolic output through insulation of one
conductivity. It cannot: some of that heat leaves through the faceplate, which has none.

The visor leaks **7.8 W** — **4.7%** of a 166 W budget. So the insulation is slightly thin: it should
be **12.5 mm**, not 11.9. That is a small correction and it is reported as one, not dressed up: a
5% error in a coat is not a scandal. But it is a real one, and it is the *second* time a child has
found a number wrong in a parent — the first cost a factor of 2.6.

## What you are looking at

The plate from inside, at the moment the fan starts. At **t = 0** it is fully condensed — what you get
34 seconds after the fan quits. The sweep enters at the top and the **clearing front travels down**,
reaching the bottom exactly as one transit elapses, so the film ends settled and clear and **its
length is not chosen: it is V/Q.**

The front is soft rather than a hard line, because a flow has a boundary layer — a plate clears over
about a finger's width. And the corners keep a rime longest, because that is where the flow
separates; anyone who has worn a mask in the cold has seen exactly that.

## What is honestly still missing

- **The condensate does not run.** Real fog beads, coalesces and trickles, and a droplet on a
  faceplate refracts rather than scatters — a different and worse problem than an even haze.
- **The visor temperature assumes a still 6 °C.** Wind would drive `h_outside` up and the plate
  colder, which is exactly the direction that makes the visor bind harder. Nothing upstream derives
  wind.
- **No anti-fog coating and no heated plate**, both of which are how the problem is actually solved
  in the field. Either would change the flow requirement, and neither is derived.
- **The 800 Pa loop drop is a stated engineering figure, not a derivation.** A packed LiOH bed's
  pressure drop follows from its grain size and depth, and this chapter does not do that work.

*Contained in `theBreath`. What it hands on: how fast the loop must run, what that costs, and how
long you can see after it stops.*
