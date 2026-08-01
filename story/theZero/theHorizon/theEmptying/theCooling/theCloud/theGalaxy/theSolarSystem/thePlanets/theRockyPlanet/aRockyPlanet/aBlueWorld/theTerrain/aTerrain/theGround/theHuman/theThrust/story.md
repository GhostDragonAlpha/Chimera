# theThrust

> **chapter 26** of the story  ·  **t = 5.75715e+15 s** since theZero  ·  lasts **1.5718 s**
>
> *The serial is the place in TIME, not in the folder tree. A path says what contains
> what; this says what follows what. Both are published — `timeline_serial` in
> numbers.json and here — so the story and its numbers cannot disagree about when.*


**In plain words —** The body as an engine. Every time a person jumps, starts, stops, climbs or
shoves, they are turning muscle work into momentum against this planet's gravity — and the floor has
to be able to take it. It cannot always take it.

*The chapter behind the verb.* Its film is one jump: crouch, drive, flight, land, in 1.65 seconds.

## A walk is polite. Nothing else is.

The parent walks, and a walk is a fall that keeps being caught — it never asks the ground for much
more than one body weight. Everything else the legs do asks for **two and a half to six and a half**,
and it asks through a contact patch that **shrinks by a factor of 3.6** at the moment the heel leaves
the floor. Whether those two facts collide is not a matter of opinion. The parent published every
number needed to find out.

## What a jump is, and the thing gravity is not in

The parent publishes `jump_height_m` and `g`, so the specific muscle work comes straight back out of
them — `w = g·h = 2.6 J/kg` — and this chapter holds **no muscle constant of its own** to drift out
of step with the one above it.

All of that work is kinetic at the instant the feet leave, so

    v = √(2w) = 2.2804 m/s

and **there is no `g` in it.** The same legs leave the ground at the same speed on every world in the
universe. What gravity sets is only how long they stay up, and therefore how high they get. *A person
on the Moon does not leave the ground faster; they leave it for longer.*

## How far the push goes — two joints, in series

Work happens over a **distance**, and the distance is the body's own geometry.

| | | |
|---|---:|---|
| the knee and hip fold | **0.2524 m** | `L(1 − cos 45°)` on a 0.8617 m hip-to-ankle line |
| the heel comes up | **0.1041 m** | the foot rotates about the **ball**, on a 0.1756 m lever |
| **the push-off** | **0.3565 m** | measured countermovement jumps: 0.30–0.45 m |

**The ankle is 29% of it**, and leaving it out is not a rounding error: the *driving* force goes as
1/distance for fixed work, so a knee-only jump reports a net drive **41%** too high and a peak ground
reaction **25%** too high (the weight, which is the rest of it, does not care). The heel-rise term carries a
correction most treatments drop — the ankle sits 6.8 cm *above* the pivot, which costs 16% of the
naive `d·sin α` back. Sixteen per cent of a small number, deciding a 2% margin.

Then the contact time needs no assumption at all about the shape of the force:

    T = 2s/v = 0.3127 s        (any time-symmetric profile gives the same T)

## The peak force — and the peak pressure, which is a different question

    F_peak = mg + (π/2)·m·v²/(2s) = 1751 N = 2.62 body weights

The weight term is the *smaller* one, by a factor of two and a half. **A jump is not a weight; it is
several.** But the force is not what breaks ground — pressure is, and the two peak at different
moments:

| | when | force | area | pressure |
|---|---|---:|---:|---:|
| force peak | mid-drive, soles flat | **2.62 BW** | 553 cm² | 31.7 kPa |
| **heel lift** | **85% of the drive** | 1.73 BW | **155 cm²** | **74.7 kPa** |
| touchdown | forefeet first | 1.00 BW | 155 cm² | 43.3 kPa |
| heel down | 15% of the landing | 1.73 BW | 553 cm² | 20.9 kPa |

The ground's bearing capacity is **110.4 kPa**. So the take-off's worst instant runs at **68% of
it — margin 1.48.**

**When the heel lifts is derived, not chosen.** The ankle owns the *last* 0.1041 m of the push-off's
distance (proximal-to-distal: hip, then knee, then ankle), and integrating the half-sine acceleration
twice says what fraction of the *time* that distance is: **85%.** By then the force has already
fallen back from its peak, and that lateness is the entire reason the floor survives.

## Whether the ground holds it — bounded, not asserted

| | pressure | margin | |
|---|---:|---:|---|
| take-off, heel lifting where the sequence says | 74.7 kPa | **1.48** | holds |
| take-off, **if the heel lifted at the force peak** | 113.1 kPa | **0.975** | **fails by 2.5%** |
| take-off, worst case with the parent's *other* foot length | 124 kPa | **0.889** | fails by 11% |
| landing, giving the full push-off range | 74.7 kPa | 1.48 | holds |
| **landing stiff — on the toes, legs locked** | **282.6 kPa** | **0.39** | **fails by 2.6×** |

**The honest answer is that the take-off sits on the line and which side depends on the joint
sequence.** The derived timing clears it comfortably; the worst case — everything happening at once —
misses by two and a half per cent. Both are published (`takeoff_margin`, `takeoff_worst_margin`) and
neither is hidden behind the other.

### The rule this world imposes on landing

Solve for the least a landing may give before the floor lets go:

| | |
|---|---|
| a landing must travel at least | **0.241 m** — 54% of the push-off range |
| below that | the forefoot window catches the force peak and the ground yields |
| a **flat, stiff** landing survives a fall of | **0.539 m** |

So: **land through your legs, or land flat.** A toes-first landing with locked legs puts 283 kPa into
regolith rated at 110 — the foot goes in. That is not a rule anyone wrote; it is this planet's
bearing capacity meeting this body's mass, and it is why a ledge above about half a metre is a
decision rather than a step.

**And it is never the skeleton that fails.** The same stiff landing puts 13.3 MPa through the femur
against 150 MPa of cortical bone — a margin of **11.3**. The bone is eleven times safer than the
floor. On this world the limiting member of a jump is the *ground*.

## Friction is the ceiling on everything horizontal

You cannot push harder than `μN`, so on the flat

    a_max = μ·g = 4.387 m/s²        — and the mass falls out entirely

A heavy person and a light one accelerate identically, which is why a sprint start is technique
rather than size.

| | here | Earth | |
|---|---:|---:|---|
| maximum acceleration | **4.39 m/s²** | 6.08 m/s² | **72.2%** of Earth's |
| to reach walking speed (1.00 m/s) | 0.227 s | | over 0.113 m |
| to reach the walk–run speed (1.81 m/s) | 0.413 s | | over 0.375 m |
| shortest stop from the walk–run speed | **0.375 m** | 0.271 m | **38.6% longer** |
| longest standing leap | 0.658 m | | 10% short of the unlimited 0.735 m |

**But the lean has no gravity in it either.** The ground reaction must stay inside the friction cone,
so the most a body can lean from vertical is `arctan(μ) = 31.8°` — the same on Earth, here, and on
the Moon. *Only what the lean buys changes.* And because the projectile optimum is 45° from
horizontal, **a standing leap cannot be taken at its best angle unless μ ≥ 1**; below that, friction
picks the angle. It costs only 10% of the distance, because `sin 2α` is flat near its maximum —
less than you would guess.

If μ came from where it should come from — the ground's own angle of repose — this says something
neater still: **a body may accelerate up to exactly the slope the ground would stand at on its own.**

## The power, and the check nobody fitted

| | |
|---|---|
| peak centre-of-mass power | **2806 W** = **29.7 W/kg** |
| mean over the push | 1548 W = 16.4 W/kg |
| **measured band for countermovement jumps** | **20–50 W/kg** |

Nothing here was aimed at that band. The power is `N·v` read off the *same* half-sine that produced
the force, sampled through a push-off whose distance came from the body's own bone lengths and whose
duration came from `2s/v`. It lands in the middle.

## Gravity is a dial, and this is where you can see it

| | this world | Earth | the Moon |
|---|---:|---:|---:|
| gravity | 7.076 m/s² | 9.807 | 1.625 |
| **take-off speed** | **2.280 m/s** | **2.280** | **2.280** |
| jump height, the parent's law | **0.367 m** | 0.265 m | 1.600 m |
| jump height, corrected (below) | **0.505 m** | 0.265 m | 3.395 m |
| time in the air | 0.645 s | 0.465 s | 2.807 s |

One row does not move. That is the law.

### The Apollo comparison, honestly

Neither column predicts Apollo. Astronauts on the Moon managed vertical jumps of roughly **0.4–0.5
metres**, against 1.60 m from the parent's law and 3.40 m from the corrected one — a factor of
**three to seven** out.

Two corrections are available, and chained at their most generous they still fall short:

| | |
|---|---:|
| total leg work, Earth-calibrated | 6.096 J/kg |
| **a pressurised suit resists joint flexion, so the crouch nearly vanishes** — the work is done over the ankle's 0.104 m instead of 0.357 m | × 0.292 → 1.781 J/kg |
| **the suit is dead mass** — the parent's own `bare_mass_kg` over `mass_kg` | × 0.895 |
| Moon, less the push-off distance | **= 0.877 m** |
| **still, against what was seen** | **≈ 2×** |

**This chapter does not close that gap and does not pretend to.** What it will say is that the
residue is *the suit* rather than the gravity — the take-off-speed row of the table above is not in
dispute, and neither is `1/g`. The rest is a spacesuit and a man who could not afford to fall.

## What this chapter found in its parent

`jump_height(g) = w/g` leaves out the lift the legs do **before the feet leave the ground.** They
raise the centre of mass through `s = 0.3565 m` during the push-off, and that costs `g·s` J/kg on top
of the flight energy.

Calibrate the total where the parent's constant was measured — Earth — and it comes to

    w_total = 2.6 + 9.807 × 0.3565 = 6.10 J/kg

**which is where the measured total concentric work of a countermovement jump actually sits (5–8
J/kg).** That check was never aimed at: it is the parent's own jump height plus a push-off distance
this chapter derived from bone lengths, added together. Landing inside the measured band is the
evidence that the missing term is real rather than an argument.

The consequence is that the parent understates a low-gravity jump. Here, **0.505 m rather than 0.367
— 37% more.** On Earth the two agree *exactly*, by construction, which is why the omission was
invisible from above.

**The parent's number is still used as THE jump everywhere in this chapter.** A child consumes its
parent's numbers; it does not overrule them. The correction is published beside it as
`jump_height_full_work_m` and handed up.

## The thing a jump cannot do

**0.645 seconds of every jump — 39% of it — is spent with no contact and therefore no thrust of any
kind.** No amount of muscle changes a trajectory once the feet are gone. That is the derived reason
the stub this chapter replaced was reaching for jetpacks: *a thruster is the machine that deletes
that interval.* Those numbers are not here, because a jetpack is equipment and belongs under `aHuman`
with the suit. What belongs here is the reason it has to exist.

## What you are looking at

One jump, from the side, on a line that is the ground. Everything drawn is a derived quantity.

**The body** is posed by the same crouch angle and plantarflexion the forces came from. The knee juts
forward because a squat is a two-bar linkage with the hip held over the foot — which is what keeps
the centre of mass over the base, and why the hip drops by `L(1 − cos φ)`. **The foot is two segments
hinged at the ball**, because that is where a foot actually bends: the heel section rotates, the
forefoot stays flat, and so the patch you can see *is* the area the pressure is divided by.

**The white bar** is the ground reaction in body weights. **It goes to zero twice**, and both zeroes
are physics: once in the first half of the countermovement, because the fastest possible descent is a
free fall and the feet genuinely carry nothing; and once in flight, because a body with no contact
cannot push on anything. **The red tick across it** is what the ground can take *right now* — bearing
capacity times the contact area at this instant — and it drops by 3.6× the moment the heel lifts.

**To the left, two curves against time**: the centre of mass's height, and the **pressure**, scaled so
the bearing capacity sits on a fixed red line. Those are graphs, not paths — the horizontal axis is
time — and they share the ground line as their zero. They exist because **heel-lift lasts about one
frame in forty-eight**, and a still taken a moment later shows nothing at all. The dangerous instant
of a jump is very short, which is itself the finding.

## What this still gets wrong

- **Two literature checks MISS, and they are left failing.** Peak take-off ground reaction comes to
  **2.62 BW against a band of 2.0–2.6** — over by 0.7%. Peak stiff-landing reaction comes to **6.54
  BW against 4.0–6.0** — over by 9.0%. Both misses are in the same direction and both have the same
  shape of cause: the push-off distance is a little short, and a half sine is a poor model of a
  *landing*, where the real trace is a sharp impact transient riding a broader wave. Widening a band
  after seeing a number is the one thing that would make these checks worthless, so they stand.
- **The first miss is worth 1.2% of a length, and it has a name.** The ankle is **dorsiflexed** at
  the bottom of a real countermovement and plantarflexes through that range too, so the true
  excursion is nearer 65–70° than the 45° counted here. A push-off just **1.2% longer** — 0.3607 m
  instead of 0.3565 — puts the take-off force back inside its band, and the missing dorsiflexion is
  worth far more than that. It is left out because doing it properly needs a two-dimensional linkage
  rather than a scalar, and inventing one to close a 0.7% gap would be fitting.
- **The parent disagrees with itself about how long a foot is** — and it moves this chapter's central
  answer across the line. `forefoot_lever_m` implies a foot **0.208 of stature**; `foot_area_m2` is
  built from ANSUR's **0.1544**. That is a 35% disagreement. Taking the short foot, the worst-case
  take-off margin falls from 0.975 to **0.889**. Both are published; neither is chosen.
- **`μ = 0.62` is a free number and should not be.** Friction should come from the ground's own angle
  of repose — a surface cannot resist a shear steeper than the slope it will itself stand at — and
  `theGround` derives and publishes `repose_deg`. **`theHuman` does not carry it**, and a membrane
  may only read its parent. The moment theHuman republishes it, the free entry is deleted and the
  line becomes `μ = tan(radians(parent["repose_deg"]))`. Until then this is the one number in the
  chapter reaching outside the chain.
- **Two constants are literature central values, not derivations**, and are listed rather than
  buried: take-off plantarflexion **45°** (reported range 40–55°) and the ball of the foot at **0.72**
  of foot length (shoe lasting). The first moves the ankle's whole contribution; the second sets the
  contact area the pressure is divided by. Neither is traced to a single paper.
- **The overlap of the joint sequence is a modelling choice**, and it is the assumption the pressure
  result is most sensitive to. The ankle is treated as owning the *last* 0.1041 m of the push-off
  outright; in reality the knee is still extending while the ankle finishes, which lifts the heel
  earlier and raises the pressure. That is precisely why the worst case is published alongside.
- **Arm swing is not here.** A countermovement jump with arms is about 10% higher than without, and
  the arms in the film swing without contributing a joule. Whether the parent's 2.6 J/kg was measured
  with arms is not recorded anywhere in this chain.
- **The ground does not answer back.** When the pressure exceeds the bearing capacity this chapter
  says *it fails* and stops. How far the foot sinks, how much energy the sinkage absorbs, and whether
  it costs you the jump are all real questions. `theGround` publishes `sinkage_m`; theHuman does not
  carry that either, so the same missing bridge blocks both halves of the ground's reply.
- **Horizontal thrust is derived but not drawn.** The friction ceiling, the leans, the stopping
  distances and the leap are all in `numbers.json` and none of them is in the film, because one
  chapter gets one movie and the movie is the jump.

*Contained in `theHuman`. What it hands on: what the body can do to the floor, and what the floor
will take.*
