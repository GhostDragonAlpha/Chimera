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

**2076, at 09:00 local.** Fifty years on from the day this chapter was written: far enough that the
world is not a documentary about the present, near enough that the person standing in it is
recognisably us.

The hour is not taste. `aTerrain`'s whole claim is a carved drainage network, and **a valley is only
visible in raking light** - at local noon the sun stands at 59 degrees and the relief that 500
erosion steps earned goes flat. At 09:00 the sun is at **37.4 degrees**, low enough to cast the
valleys and high enough to see by.

And **the clock runs 1:1**. Every membrane above this one is geared - an aeon of collapse compressed
into a movie you can sit through - because nothing else is watchable otherwise. Here that would be a
lie: the person is standing in it. So one second is one second, and the sun crosses the sky at
exactly the rate this planet's own rotation says it does. That is what the bottom rung of
`theHumanClock` means: there is no gearing left to apply.

| | |
|---|---|
| sunrise | **06:00**, due east |
| noon | 59.2 degrees - which is 90 minus the 30.77 latitude, exactly |
| sunset | **18:00**, due west |
| seasons | **none** |

That last row is not a design choice, it is an admission: **no membrane in this chain derives an
axial tilt.** With no obliquity there is no solar declination, so every day of the year is the
equinox and the sun rises due east whatever the date. Put a tilt in `aBlueWorld` and the seasons
appear here for free. Until then this world has none, and the render must not imply otherwise.

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

*Contained in `theGround`. What it hands on: a body that can be stood up, and everything the planet
underneath decides about how it moves.*
