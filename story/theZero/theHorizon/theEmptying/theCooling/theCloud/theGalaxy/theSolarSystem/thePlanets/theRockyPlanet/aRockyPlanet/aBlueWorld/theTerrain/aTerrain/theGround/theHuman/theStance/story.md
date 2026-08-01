# theStance

**In plain words —** Standing still is not a thing a body is, it is a thing a body keeps doing. The
feet mark out a patch of ground, the body falls very slowly in one direction or another inside it,
and something catches it before it runs out of patch. How much patch there is, how fast it is
running out, and what it costs to make the patch bigger — that is this chapter.

---

## Why standing is a process

Put a broom upright on your palm and you know within a second that "balanced" is not a position. It
is a chase. A standing human is the same object: a mass up at chest height over a small contact
patch, held up by nothing but continuous correction. Stop correcting and it falls, and the time it
takes to fall is not long.

The parent chapter already derived the rate of that fall: `fall_rate = √(g/H)`, an inverted
pendulum with the centre of mass at height H. What it never asked was **how much room the fall has
before it stops being recoverable.** That room is the base of support, and the amount of it left at
any instant is the *margin of stability*.

The one idea that makes the whole chapter work is Hof's (2005): **you are not stable because your
centre of mass is inside your feet — you are stable because where it is GOING is inside your feet.**

```
XcoM  =  com  +  v / ω₀
```

A body leaning 5 cm and dead still is fine; it will come back. The same body at 5 cm and moving at
0.2 m/s is already gone. The difference is `v/ω₀` — how much further an inverted pendulum will
travel before it can be stopped. So the margin is a length that depends on a **velocity**, which
means it cannot be known once and stored. It has to be measured continuously. That is what makes
standing a process rather than a state, and it is why the verb behind it is *hold*, not *be*.

---

## What the force plates said about the parent's number

The parent's `fall_rate_rad_s` treats the body as a **point mass** at the CoM height. A real body
is not a point. It has rotational inertia about its own centre, and that inertia slows the topple.

This chapter measured how much, from 261 quiet-standing force-plate trials in the balance database
already sitting in this repo (HBEDB / BDS — Santos & Duarte 2016, PeerJ 4:e2648, CC BY 4.0; young
adults, eyes open, firm surface, 60 s each at 100 Hz). The measurement uses **no anthropometry at
all**: the plate gives the horizontal force, so `a_com = F/m` by Newton; it gives the centre of
pressure from the moments; and the CoM position follows from the acceleration with no model
whatever, since acceleration *is* the second derivative. That leaves ω₀ as the only unknown in

```
a_com  =  ω₀² (com − cop)
```

and it is a one-parameter fit. Ten fits — five frequency bands × two plate axes:

| band | axis 1 | axis 2 |
|---|---:|---:|
| 0.3 – 1.0 Hz | 2.817 | 2.918 |
| 0.5 – 2.0 Hz | 2.971 | 2.984 |
| 0.8 – 3.0 Hz | 3.063 | 2.988 |
| 0.3 – 3.0 Hz | 2.900 | 2.941 |
| 1.0 – 4.0 Hz | 3.146 | 2.979 |
| **mean** | **2.971 rad/s** | ±5.5% |

A point mass at those subjects' CoM height would give **3.199 rad/s**. So the real body falls at
**0.929** of the point-mass rate. And two idealisations bracket that number, both computed from
nothing but geometry, neither fitted to anything:

| body | correction |
|---|---:|
| a point mass at the CoM | 1.000 |
| **a standing human, measured** | **0.929** |
| a uniform rod standing on its end | 0.866 ( = √3⁄2 ) |

It lands between them, nearer the point mass, which is what you would expect of a shape whose mass
is concentrated in a trunk sitting close to its own centre. The implied whole-body radius of
gyration is **0.230 of stature**, giving **15.4 kg·m²** for this 94.5 kg body — the right order for
an adult's whole-body sagittal inertia, and if anything a little high, which means the correction is
a little conservative rather than flattering.

The correction is **dimensionless**. It describes how a body's mass is arranged, not how hard its
world pulls, which is why a measurement made at 9.807 m/s² is allowed to travel to a world at
7.076.

**On this world, then:** ω₀ = 2.459 rad/s, and the time constant of the fall is **0.407 s**, not
the 0.378 s the point-mass form gives.

---

## The base of support

The support polygon is the convex hull of what touches the ground: as long as a foot, as wide as
the feet are apart. The foot comes from ANSUR II (4,082 males) — length 0.271 m, breadth 0.102 m at
this stature — and multiplying them gives 0.027642 m², which is the `foot_area_m2` the parent
published from its own read of the same survey, to twelve decimal places. Two paths, one number.

The hips come from the musculoskeletal model this studio already walks on (MyoSuite `myo_sim`,
which places the femurs ±0.07726 m either side of the pelvis). That matters because it fixes the
stance that costs the hips *nothing* — feet directly under the hip joints — without assuming it.

| stance | foot centres apart | outer width | area | hip abduction | hip torque | friction needed |
|---|---:|---:|---:|---:|---:|---:|
| **together** | 0.102 m | 0.204 m | 0.055 m² | −2.1° (adducted) | 10.6 N·m | 0.034 |
| **natural** (the walk's own step width) | 0.212 m | 0.314 m | 0.085 m² | +1.5° | 7.8 N·m | 0.025 |
| **braced** | 0.688 m | 0.790 m | 0.214 m² | +17.6° | 87.3 N·m | 0.293 |

The braced stance is not chosen. It is **the widest stance the hips will hold for the same torque
the ankles already spend pushing off** — 87.3 N·m, the parent's own `ankle_torque_Nm`. Turn the
`brace_effort` dial and the width follows; leave it at 1 and the body braces to the width where
standing wide costs what walking already costs.

Note the two rightmost columns are alternatives, not both. A leg held out sideways can be paid for
by the **hip** (a moment, with the ground pushing straight up) or by the **ground** (friction, with
the leg loaded along its own axis like a strut). Real stances sit between. This chapter cannot see
the ground's coefficient — no membrane above it publishes one — so it publishes the *requirement*
and lets the ground decide, which is this project's rule about commanding a process and never a
position.

**The hip's own limit is unreachable.** The model's hip abducts 50°, which would put the feet
1.588 m apart — but a stance that wide needs a friction coefficient of **1.06**, and there is no
ordinary ground that gives that. The hip stops at almost exactly the width where the ground gives
out first. Stated as an observation with its two numbers, not as a claim that one caused the other.

---

## What a shove costs

Set the extrapolated CoM at the boundary and solve. `v_max = b·ω₀` is the fastest the CoM may be
travelling and still be stoppable without moving a foot.

| stance | sideways | from in front |
|---|---:|---:|
| together | 0.251 m/s | 0.333 m/s |
| natural | 0.386 m/s | 0.333 m/s |
| braced | **0.971 m/s** | 0.333 m/s |
| *allowed to take one step* | — | **1.788 m/s** |

Two things fall out of that table and both are worth having in a game.

**Bracing wide does nothing at all for a push from the front.** The fore-aft margin is half a foot
length, and no amount of standing wide changes a foot's length. A braced stance is 3.9× harder to
shove sideways and *exactly as easy* to shove over forwards.

**Taking a step is worth more than any stance.** One step extends the reachable base by a step
length, and the survivable shove goes to 1.79 m/s — 1.8× the body's own comfortable walking speed,
and 4.6× what the same body survives with its feet planted. Which is the honest answer to why
nobody stands braced all the time.

---

## The cost of holding

A wide stance has to be paid for in **time**, and the payment is derivable. To lift a foot the body
must first get its centre of mass over the *other* one — it does that by pushing the centre of
pressure to the far side and letting itself fall the right way. With the CoP a distance `c` away,
the pendulum gives `com(t) = c(cosh ω₀t − 1)`, so crossing a distance `a` takes

```
t  =  arccosh(1 + a/c) / ω₀
```

| stance | time before a foot can leave the ground |
|---|---:|
| together | 0.391 s |
| natural | 0.449 s |
| braced | 0.504 s |

So the trade, both halves in one line: **bracing multiplies the sideways margin by 3.87 and adds
0.112 s — 19% of a step time — to how long it takes to react by moving.** It is a good trade against
a push and a bad one against anything that requires going somewhere, which is exactly the choice the
`[Y]` key should feel like.

---

## The sway

A standing human is never still. The centre of pressure wanders continuously, and the same 261
trials measure the wander: **4.62 mm RMS**, mean path velocity **8.80 mm/s**, median power frequency
**0.195 Hz** on one axis and **0.253 Hz** on the other.

What transfers between bodies is not the distance but the **angle**: a lean of θ puts the CoM `L·θ`
off centre, so a taller body sways further for the same lean. Dividing the measured sway by the
subjects' own CoM height gives **4.82 mrad = 0.276°**, and that is the invariant. What transfers
across gravity is ω₀, because the body has no other clock — no spring, no resonance, nothing tuned.

| | Earth (measured) | this world (derived) |
|---|---:|---:|
| sway RMS | 4.62 mm | **4.87 mm** |
| sway velocity | 8.80 mm/s | **7.67 mm/s** |
| fore-aft frequency | 0.195 Hz | **0.162 Hz** |
| lateral frequency | 0.253 Hz | **0.210 Hz** |
| ω₀ / 2π | 0.473 Hz | 0.391 Hz |

### The check this was not fitted to

If the body carries no clock of its own, sway must run at O(ω₀) — there is nothing else for it to
run at. Dividing the measured frequencies by the measured pendulum frequency:

```
fore-aft   0.413 × (ω₀/2π)
lateral    0.535 × (ω₀/2π)
```

Both are O(1), and both are about **half** the pendulum's own frequency. Nothing was fitted: the
frequencies came off the plates and ω₀ came off the same plates by a completely different route
(force and centre of pressure, no spectrum involved). A body standing still oscillates at half the
rate at which it would topple. The commonly quoted sway band for quiet standing is 0.3–1 Hz, and
0.195–0.253 Hz sits *below* it — which is what the median-power-frequency measure gives, since most
of the power in a stabilogram is at the low end. The band and this measurement are the same signal
read two ways, and the ratio above is the part that is a prediction.

### And a second one, from geometry alone

Put the centre of mass at the **fore-aft middle of the foot**. That is the position which maximises
the smaller of the two sagittal margins — a pure optimisation, with nothing about human physiology
in it. It lands **47.8 mm ahead of the ankle joint**. Quiet standing is measured to put the centre
of mass 40–60 mm anterior to the ankles.

---

## What gravity does to standing

`ω₀ = √(g/H)`, so at g = 7.076 against Earth's 9.807 every part of standing runs at **0.849×** the
rate. That cuts two ways and only one of them is comfort:

- **Balance is slower.** The time constant of a fall goes from 0.345 s to 0.407 s — 18% more time
  to notice and react. The sway is 15% slower. Everything about holding a position is more
  forgiving.
- **Balance is more fragile.** `v_max = b·ω₀`, and ω₀ is *smaller*. The same feet in the same
  natural stance survive 0.386 m/s here against 0.454 m/s on Earth — **15% less**. A trip that a
  person shrugs off on Earth puts them down here.

That is the Apollo result, and it is why the footage looks the way it does. On the Moon
(g = 1.625) the same body's time constant is 1.18 s — three times Earth's, all the time in the
world to react — while its velocity margin is a third of Earth's, so the smallest catch of a boot
was unrecoverable. Astronauts did not fall over because they were clumsy or because the suits were
stiff. They fell over because low gravity gives you a long time to fail to fix a problem you were
never able to absorb.

---

## The movie

Looking straight down at the ground. The stance opens from feet-together to the derived braced
stance while the body sways at the two frequencies above, so two clocks run at once and the trace
never closes — which is why a real stabilogram wanders instead of orbiting.

Two marks, and the gap between them is the whole idea: the dim one is the centre of mass, the
bright one is the **extrapolated** centre of mass, ahead of it by `v/ω₀`. It leads furthest when the
CoM is moving fastest, which is in the middle of a sway and not at its ends. The red segment runs
from the extrapolated CoM to the nearest edge of the base: its length *is* the margin. Watch which
edge it points at — early on it reaches sideways, and as the stance opens the nearest edge flips to
the front, because the sideways margin has overtaken the fore-aft one that never grew.

The sway is drawn eight times life size, declared in `sway_drawn_factor` and published with the
numbers. It scales something derived; nothing here is invented. The soles are coloured with the
parent's own measured skin albedo. Everything else is a diagram colour and is said to be one — a
base of support is a geometric region, it has no spectrum, and pretending otherwise would be the
aesthetic pass this project does not take.

---

## What this still gets wrong

**The whole base of support is treated as load-bearing, and it is not.** A real foot touches the
ground at the heel, the lateral border, the ball and the toes; the arch does not touch at all. The
functional base is smaller than the sole's outline and a different shape. Every margin here is
therefore slightly optimistic, and the fore-aft one — the small one that matters — most of all.

**The plate axes are not labelled.** The distributed files carry `COPx` and `COPy` with no key. The
assignment used here is from the signature — the larger, slower axis taken to be anteroposterior,
the smaller, faster one mediolateral — and if it is backwards, two labels swap and no derived
number moves, because the amplitude law uses the resultant and the movie uses both frequencies.

**Two anthropometric sources disagree about feet by 11%.** ANSUR II gives foot length at 0.154 of
stature; the HBEDB subjects' recorded foot length averages 0.138 of theirs. Different populations,
possibly different measurement conventions. ANSUR is used, because it is the source the parent
already uses and because its product matches the parent's published foot area exactly — but the
disagreement is real and it moves the fore-aft margin by 11%.

**The margins are all measured from the centre of the base.** A body standing anywhere else has an
asymmetric pair of margins, and a body already leaning has a small one and a large one. The
numbers here are the *at-rest* margins; the movie shows the instantaneous ones, and only the movie
is honest about that.

**The natural stance width is the walk's step width, and it should not have to be.** The step width
comes from the parent's gait measurement (0.212 m between foot centres), while the hip joints
derived here are 0.166 m apart. The 23 mm difference per side is why the natural stance costs 7.8
N·m of hip torque instead of nothing. That may be real — people do stand slightly wider than their
hips — or it may be that a treadmill step width is not a standing stance width. Nothing here can
tell which.

**Sway amplitude is imported, not derived.** The 4.82 mrad lean is a measurement carried across; it
is not predicted from anything. Predicting it needs a sensory threshold and a loop delay, and this
chapter has neither from a source. The sway *rate* is derived (it is ω₀'s), the sway *size* is not,
and the two are not the same claim.

**One number trips the physics catalog and the trip is kept.** `whole_body_inertia_kgm2` docks into
H1.02 / H1.04, whose symbol is `I_segment` and whose regime is a segment's (≤ 10 kg·m²) — because
the signature's key fragment is the bare word "inertia", so a whole body fits a thigh's socket. The
number is right and the socket is too wide. Two other notes for whoever maintains that machinery:
`sway_speed_ms` was renamed to `sway_velocity_ms` because it was binding into a cost-of-transport
law's *walking* speed at 7.7 mm/s; and `folding.py membrane <name>` does not pass the membrane name
down to `undeclared()`, so the three `_hz` keys declared in `story/data/units.json` read as
undeclared in that view while the tree-wide audit sees them correctly.

**The other five postures are still not written.** Crouch, prone, the combat slide, the corner lean
and the mantle each change the contact patch and the CoM height, which re-runs every equation above
with different numbers. None of it is done. This chapter is standing, and standing only.

---

## The verbs

| verb | what this chapter gives it |
|---|---|
| **Deploy Bipod / Brace [Y]** | 0.790 m stance, 3.87× the sideways margin, 87.3 N·m of hip torque, µ ≥ 0.293 from the ground, and 0.112 s added to every reaction |
| **Steady Aim [Left Shift]** | the sway the aim is fighting: 4.87 mm at 0.16 and 0.21 Hz, on two axes that never quite line up |
| *the shove* | 0.386 m/s standing naturally, 0.971 m/s braced, 1.788 m/s if a step is allowed |

*Contained in `theHuman`. Hands on: nothing yet.*
