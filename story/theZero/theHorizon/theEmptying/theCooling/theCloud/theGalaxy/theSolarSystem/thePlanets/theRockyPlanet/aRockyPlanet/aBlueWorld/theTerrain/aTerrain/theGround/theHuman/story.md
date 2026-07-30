# theHuman

**In plain words —** A person, standing on that ground. Everything above this chapter exists so this
one can stand up: the seed emptied, the sea cooled, a cloud shattered until its pieces were the size
of stars, one of them lit, a rock swept up the leftovers, its core stayed warm enough to keep the
air, water fell and cut the rock, and the rock broke down into something that bears weight. **All of
it to arrive at 7.08 m/s² and a surface that carries 110 kPa.** This chapter is what those two
numbers do to a body.

*The bottom of the ladder.* Fourteen membranes from the seed, and the only thing chosen here is how
tall the person is.

## One free number, and the rest follows

Height is not derivable from a planet — it is a fact about a body. Everything else on this page comes
from that height and from `g`:

| | |
|---|---|
| mass | **71.3 kg** (`BMI · h²` — mass goes as height *squared*, not cubed) |
| centre of mass | 1.02 m up |
| leg | 0.94 m |
| **how fast you fall over** | **2.63 rad/s** — 0.38 s to do something about it |
| step time | 0.65 s |
| **walk → run** | **1.83 m/s** |
| stride | 0.65 m |
| **jump** | **0.37 m** |
| femur, running | 4.6 MPa against 150 — **33× safety** |
| foot on the ground | 19 kPa against the 110 the ground carries — **it holds, 5.8×** |

## When

Height was the only free number here until the game needed somewhere to begin. A date is not a fact
about a planet - it is a count from a convention, and this is the only chapter in the story with
anyone in it to keep a calendar. So the epoch is **free here, and it is a human decision**, declared
rather than typed under a comment pretending it was inherited.

**2076, day 96, at 09:00 local.** Fifty years on from the day this chapter was written: far enough
that the world is not a documentary about the present, near enough that the person standing in it is
recognisably us. Day 96 of 383 is this world's **summer solstice** - and that is not a preference
either. On an equinox a tilted world and a straight one make the same picture, so opening there
would hide the thing the chapter above just gained.

The hour is not taste. `aTerrain`'s whole claim is a carved drainage network, and **a valley is only
visible in raking light** - at local noon the sun stands at 59 degrees and the relief that 500
erosion steps earned goes flat. At 09:00 the sun is at **37.4 degrees**, low enough to cast the
valleys and high enough to see by.

And **the clock runs 1:1**. Every membrane above this one is geared - an aeon of collapse compressed
into a movie you can sit through - because nothing else is watchable otherwise. Here that would be a
lie: the person is standing in it. So one second is one second, and the sun crosses the sky at
exactly the rate this planet's own rotation says it does. That is what the bottom rung of
`theHumanClock` means: there is no gearing left to apply.

## And now there are seasons

That table used to end with **seasons: none**, written as an admission - nothing in the chain
derived an axial tilt, so declination was zero, every day was the equinox, and the date could only
advance a calendar. `theRockyPlanet` now derives one, and everything below it moved.

**The tilt is not chosen; the distribution it is drawn from is.** A collision big enough to change
how fast a world spins also changes which way its axis points, so the tilt sits beside the day
length as the same event's other consequence. The spin vector that stochastic giant impacts leave
points **isotropically** (Kokubo & Ida 2007), so `P(tilt)` goes as `sin(tilt)` - a distribution with
no free parameters at all, which says something blunt: **most worlds are steeply tilted, and Earth's
23.4 degrees is a fourth-percentile outcome.** A mild seasonal world is the strange one.

And the default is not ours. Above **53.90 degrees** a world turns inside out - the poles receive
more sunlight over a year than the equator, and the cold place and the hot place swap. That number
is pure geometry, no mass and no distance in it, so this membrane can state it unprompted; the
literature it was never fitted to puts the crossover at ~54. The tilt used here is the **median
among worlds on the ordinary side of that line** - the typical member of the regime rather than a
copy of ours - and it comes out at **37.38 degrees**.

| | |
|---|---|
| tilt | **37.38 degrees** |
| the tropics | **37.38 degrees** - and this terrain sits at 30.77 |
| polar circles | 52.62 degrees |
| longest day | **15.61 h** |
| shortest day | **8.39 h** |
| noon at midsummer | 83.4 degrees |
| noon at midwinter | 21.8 degrees |
| a season | 96 days |

**Read the second row again.** The sun can only stand directly overhead inside the tropics, and the
tropics *are* the tilt. This terrain is at 30.77 degrees, and the tilt is 37.38 - so **the sun passes
through the zenith here, twice a year, on days 61 and 130.** Nobody arranged that. `aTerrain` picked
a latitude for reasons of its own and an impact distribution picked an angle, and the comparison
between them decides a fact you can go outside and check. On Earth, at this latitude, it never
happens.

It has a second signature, and the render shows it: **noon is not highest at midsummer.** The sun
crosses overhead on the way to the solstice and has started back down by the time it arrives, so
midsummer noon is 83.4 degrees while the peak, weeks earlier, is 90. Calling the solstice value "the
highest" would have been wrong by 6.6 degrees for exactly that reason.

Everything else follows from one line - `sin(declination) = sin(tilt) x sin(where it has got to in
its orbit)`. At the equinoxes that is zero and the day is **12.02 hours** with the sun rising due
east at **89.8 degrees**; at midsummer the sunrise has swung to **45 degrees**, northeast, and at
midwinter to **135**. None of those were fitted; they are the same equation read on different days.

And it is visible rather than merely recorded. At 06:12 the sun is **20 degrees up in summer and 16
degrees below the horizon in winter** - same clock, same hillside. Over a whole year the lit ground
tracks `sin(sun altitude)` at **r = 0.9986**, which is Lambert's cosine law turning up in a renderer
that was never told seasons exist. It only ever knew where the sun was.

## Standing is not a state, it is a process

A body balanced above its feet is an **inverted pendulum**, and it topples at `ω₀ = √(g/H)`. On Earth
that is 3.2 rad/s — about a third of a second between losing balance and needing to have done
something. Which is why balance feels effortless and is not.

And it says **where the foot must land**: the capture point, `x = v/ω₀` (Hof 2008). Not aimed at —
it is where the physics requires the foot to go, and a walk is a controlled series of these.

## A leg is a pendulum, but a walk is not passive

Left to hang, the leg's natural period is **1.61 s** on Earth. A free swing is half a cycle — 0.80 s
— which would give 1.24 steps per second. People walk at about **1.8**.

That gap is not an error in the pendulum. **The hip flexors drive the swing**, about half again
faster than gravity alone would carry it. It is stated here as the measured factor it is, because
pretending the pendulum alone predicts cadence would be a fit wearing a derivation's clothes.

What the pendulum *does* give — and this is what makes it a law rather than a fit — is the
**scaling**. The period goes as `1/√g` whatever the drive. So the same body on a lighter world *must*
walk more slowly, and the law says by exactly how much.

## The same body, three worlds

| | g | walk → run | cadence | jump |
|---|---|---|---|---|
| Moon | 1.63 | **0.88 m/s** | 0.74 /s | 1.60 m |
| **here** | 7.08 | 1.83 m/s | 1.55 /s | 0.37 m |
| Earth | 9.81 | 2.15 m/s | 1.82 /s | 0.27 m |

**Look at the Moon row.** Walking gives out at 0.88 m/s — slower than a comfortable stroll on Earth.
There is no speed at which walking is available and useful, so you have to do something else. That
is precisely why the Apollo crews bunny-hopped, and it was never fitted to: it falls out of `Fr = 0.5`
and a gravity.

## What the render shows, and what it deliberately does not

A stick figure. The mass, the segment lengths, the moments of inertia and every timing are derived —
**the flesh is not**, and drawing flesh would be claiming a body this chapter has not built.

The legs swing at the period the compound pendulum gives, the stance knee stays near straight (which
is what makes walking cheap — the leg is a strut, not a spring), the centre of mass rises at
mid-stance as the body vaults over the planted foot, and the arms counter-swing because whole-body
angular momentum stays near zero. None of it is animated: every part's phase is a function of the
same `t`.

**All of that was written before it was true.** The code bent the knee on the *stance* leg — the
condition `-cos(phase + ph) > 0` is precisely the definition of stance — so the stance knee folded
while the swing knee locked straight, and a straight swing leg is a *long* leg whose foot never left
the floor. Worse, the hip was nailed at a fixed height, so nothing vaulted over anything and the
promised centre-of-mass rise was supplied by a hand-written `0.018·cos(2φ)`: a **simulation of the
consequence, sitting where the consequence should have been.**

Measured, the two faults together lifted **both feet 4.2% of stature off the ground at mid-stride**
and set them down at the extremes. Duty factor near 1.0 on both feet. By this project's own gait
doctrine that is **a sled, not a gait** — and the page above was describing a walk.

The repair is one line of physics: *the stance foot is on the ground, so the hip height is whatever
the stance leg's geometry puts it at.* Nothing else is added.

| | before | after | a real walk |
|---|---:|---:|---|
| contact plane travel | 4.2% | **1.6%** | 0 |
| swing-foot clearance | ~0 | **9.7%** | 8–15% |
| centre-of-mass rise | hand-written 1.8% | **emergent 4.3%** | ~2.5% |
| **duty factor, each foot** | **~1.0 (a sled)** | **0.65** | 0.55–0.65 |

And **double support falls out unasked** — both feet down through the transition, 30% of the cycle,
which is what a slow walk has. The footfall diagram is now the alternating Hildebrand pattern instead
of two solid bars.

**And its movie is 1.3 seconds long.** Every other membrane in this story runs a film measured in
years or aeons and has to be geared down to be seen at all. This one is inside the band a person can
feel — the bottom of `theHumanClock`'s ladder, finally reached.

## And you can stand up in it

This is the chapter you can enter. `ChimeraEngine/walker.py` puts the eye at **0.94 of stature** and
hands the keyboard the four verbs a body has - and every speed in it is a number off this page:
walking is `comfortable_speed_ms`, running is the Froude limit `walk_run_ms`, the jump is
`sqrt(2g x jump_height_m)`, and what the feet are on is `aTerrain`'s carved surface. **There is
nothing to tune, because there is no movement setting anywhere in it.** Change the star's mass and
the planet moves, gravity changes, and the walk changes with it.

The ground you see is the same derivation read at the resolution a body needs: **shape** from
`aTerrain`, **grain** from `theGround`, in eight nested rings each double the spacing of the one
inside it - so a grain subtends about 1.9 degrees wherever it is, and the level of detail has no
seam to show. The rings are anchored to the world, not to the player, which is why walking slides
them over stationary ground instead of dragging the whole landscape along with you.

And the sky is not a backdrop. `aBlueWorld` derived half an atmosphere; this draws it - Rayleigh
scattering with the optical depth scaled by that pressure and coloured by one-over-lambda-to-the-
fourth. **Nobody wrote that sunrise should be red.** It comes out red because at 06:00 the beam
crosses 38 airmasses and the blue is scattered out of it before it arrives.

## The sine is gone. 246 people walk here now.

The hip angle was `swing·sin(φ)` with `swing = 0.42` rad, and this page used to call that out as
*"the one amplitude here that is neither derived nor measured."* It is now read from
**246 healthy adults aged 18–91**, walking at three self-selected speeds, every joint angle
recorded at every percent of the gait cycle and grouped by sex and decade of age.

**A better amplitude is not the point.** A sine could never have carried three things a real hip has:

| | a sine | 246 adults |
|---|---|---|
| shape | symmetric by construction | **asymmetric** — steep through swing, slow through stance |
| the knee | one peak, in swing | **two** — and the small one is an ~18° wave during *stance* |
| the foot | a model with hand-placed phases | **falls out**, by geometry, from the other three |

That stance-knee wave is the exact mechanism this page named as the reason the vault was too tall,
with the note that *"the mechanism is named rather than the number scaled, because scaling it would
be tuning the answer."* It arrived as data, and the number moved on its own:

| | before | now | a real walk |
|---|---:|---:|---:|
| **vault, at Earth gravity** | 4.3% of stature | **2.36%** | ~2.5% |
| hip path peaks at | push-off | **29% of the cycle** | mid-stance, ~30% |
| duty factor | 0.60, chosen | **0.6027, measured** | 0.55–0.65 |
| double support | 0% with a sine | **21.1%** | ~20% |

**And speed became a dial.** The study measured three of them, so the Froude law derives a
comfortable speed, that speed *selects the curve shape*, and walking faster really does reach
further — because 246 people were measured reaching further. The vault runs 1.30% → 4.71% of stature
across the range, monotonically, which is what every study of it reports and none of it is a gain.

## Two errors of opposite sign, cancelling

This page claimed the ankle torque was an unfitted check: `τ = 1.2·mg·0.10h` → **1.51 N·m/kg**
against a literature peak of ~1.5. The same 246 adults measure **1.51 N·m/kg**. The result was right.

The inputs were not. The measured peak ground reaction is **1.10** body weights, not 1.2 — and the
product only landed because the forefoot lever is longer than 0.10 of stature. Worse, `1.2·g·0.10·h`
gives 1.51 only at **this planet's 7.08 m/s²**; run it at Earth's 9.81 and it gives **2.09**, 39%
above the measurement it was being congratulated for matching.

**A check that passes for a compensating reason is not a check**, and nothing about it looked wrong
from the inside. The torque is now the measurement.

## The foot pivots on the ball, and that was worth 3.6 cm

`ankle_height` rolled the foot about the **toe tip** — the whole 0.152 of stature. A real foot rolls
over the metatarsal heads and the toes go along for the ride. Moving the pivot cut the two legs'
disagreement about where the pelvis is from 5.73% of stature to 2.10%.

**The lever was not chosen to do that.** It is what the measured ankle *moment* divided by the
measured ground *reaction* independently says it must be — `r = τ/F` — **0.071 of stature**, from a
different sheet of the same study. A kinematic check and a kinetic check on the same millimetre.

## What the gait still gets wrong

- **In single support it is exact and in double support it is not.** One leg carrying everything
  fixes the pelvis completely: sole error **0.000%**, contact plane **dead still**. With both feet
  down, the two legs each demand a pelvis height from their own joint angles and disagree by
  **2.02% of stature** — and the more heavily loaded foot is always the one nearly right (0.44% off
  while bearing 0.97 body weights; the foot barely touching is the one 2% out).
- **About 40% of that residual is the frontal plane, which this chapter does not have.** The pelvis
  *lists* — measured obliquity 8.5° peak to peak at this speed — so the two hips are not at one
  height, and a sagittal model puts them there by construction. At this body's hip width that is
  **0.81% of stature** of the 2.02%. It is not fixable here; it is `theBalance`'s job.
- **No segment length can close the rest.** Measured: the sensitivity of the disagreement to the
  thigh fraction is 0.096 per unit, so closing 2% would take a change of 0.26 of stature — the whole
  thigh. So this is not the unsourced-segment gap, and saying so is worth more than assuming it.
- **Leg length is still the repo's 0.530 of stature, not the measured 0.5246.** They agree to 1.1%,
  and the study's definition of "leg length" is not certainly the same as this chapter's, so it was
  left alone rather than changed in the same pass as the gait. One change at a time.
- **`stride_m` was a step length wearing a stride's name** — `speed/cadence` with cadence in *steps*.
  Caught only because the measured stride was there to compare against, and 0.60 against 1.13 is not
  a 47% error in a derivation, it is a factor of two in a label.

*Contained in `theGround`. What it hands on: a body that can be stood up, a walk measured on 246
people, and everything the planet underneath decides about how it moves.*
