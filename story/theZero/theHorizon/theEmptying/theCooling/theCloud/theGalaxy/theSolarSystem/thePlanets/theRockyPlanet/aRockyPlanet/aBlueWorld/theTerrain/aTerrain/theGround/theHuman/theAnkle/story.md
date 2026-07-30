# theAnkle

**In plain words —** The joint that makes walking cheap, and the only one that touches the ground.
The parent's gait was a **sled**: both feet 4.2% of stature off the floor at mid-stride, duty factor
near 1.0 on each, no double support. Two faults caused it, and the second is this chapter — the knee
bent on the wrong leg, **and the foot had no joint.**

*The smallest membrane about a body.* Thirty-six centimetres, heel to toe, and its film is one stance
phase.

## A rigid foot cannot walk

A foot welded to a swinging shank has two options and both are wrong: plough its toe, or lift its
heel. It cannot keep a sole on the ground, because the sole's height is then a rigid function of the
leg's angle. That was the residual contact-plane travel the parent could not remove by fixing the
knee alone.

## The foot is worth 30% of the vault

Hansen, Childress & Knox measured the **roll-over shape** — the locus the effective contact point
traces during stance, in a shank frame — and found a circular arc of radius about **0.30 of leg
length**, near-independent of walking speed. That independence is what makes it a property of the
limb rather than of the gait.

A rocker of radius `R` rolls with its hub at *constant* height, so only the leg above the hub swings:

| | |
|---|---|
| rocker radius | **0.283 m** (0.30 of a 0.943 m leg) |
| a point foot vaults | 8.2 cm |
| **a rocker foot vaults** | **5.7 cm** |
| **the foot is worth** | **30% of the rise** |

That is a large part of why walking costs so little: **a third of the pole-vaulting is deleted by
having feet.**

## But the arc is not a wheel — and that trap cost a rebuild

I modelled it as a literal wheel first. The hip rose correctly and **the sole left the ground**,
because a wheel has nowhere to put a foot: measured, duty factor fell to **0.12**, worse than the
sled it replaced.

The arc is an **effective** description of three rockers in sequence, with an ankle pitching the foot
between them:

| rocker | share of stance | what is happening |
|---|---:|---|
| **heel** | 15% | toe up, rolling forward over the heel |
| **ankle** | 50% | sole flat and still; the shank rotates over it |
| **forefoot** | 35% | heel rising, rolling off the ball |

**Model the joint and the arc emerges. Model the arc and the joint disappears.** The three fractions
are measured kinematics and they partition stance exactly — `measure()` checks they sum to one.

## What it pushes with, and the check nobody fitted

At toe-off the ground reaction acts on the forefoot lever. Both numbers come from above: a body
weight this chain derived, a peak ground reaction measured in body weights, and a lever measured off
a cadaver.

`τ = 1.2 · mg · 0.10h` → **122.7 N·m**

Divide by the body mass and it is **1.51 N·m/kg**. **The measured peak ankle moment in human walking
is ~1.5 N·m/kg.** Nothing here was tuned toward that — it is three inherited numbers multiplied
together, and it lands on the literature to within 1%.

| | |
|---|---|
| push-off work | **55 J** per step |
| mean power over a step | 86 W |
| work to lift the vault, per stride | 96 J |
| **the ankle's share of positive work** | **45.6%** |

**That last row is a second check that was not fitted.** The literature puts the ankle at 45–50% of
the positive work in walking; this chain gives **45.6%**, from a torque it derived and a vault it
derived, agreeing to within 4%. I had written 37% here from an earlier, cruder vault measurement, and
the chapter's own `measure()` corrected me — which is the arrangement working.

## What it fixed, measured

| | sled | wheel | **the joint** | a real walk |
|---|---:|---:|---:|---|
| contact-plane travel | 4.2% | 3.9% | **1.2%** | 0 |
| duty factor, each foot | ~1.0 | 0.12 | **0.58 / 0.60** | 0.55–0.65 |
| double support | 0% | 0% | **17–21%** | ~20% |
| swing-foot clearance | ~0 | — | **9.7%** | 8–15% |

The footfall diagram is the alternating Hildebrand pattern the studio's gait witness looks for, with
the overlap that makes it a walk rather than two abutting hops.

**And one structural thing had to change to get there.** The hip angle was `swing·sin(φ)`, which puts
each foot down for *exactly* half the cycle — so the two stances abut and never overlap, and without
overlap there is no leg pushing off while the other reaches. **A sine cannot produce a walk.** The
cycle is now parameterised by duty factor directly, with 0.60 as a measured input, and the 0.2 of
overlap that buys is where double support comes from.

## What you are looking at

One foot, heel strike to toe off, on a line that is the ground.

The bright mark is **the centre of pressure** — where the ground is pushing, now. It starts under the
heel, sweeps forward along the sole, and ends under the ball of the foot. The pale trail behind it is
where the pressure has already been, so **the roll-over shape draws itself**, by the thing that makes
it, rather than by a curve fitted over the top.

**And it took a correction to get right.** The first version asked the *geometry* where the foot
touched — the lowest point of the sole. But **a flat foot has no lowest point**: while the sole is
flat every part of it is equally low, so the mark sat on the heel through half of stance and then
*teleported* to the toe the instant the pitch went negative. The sweep this page describes is real,
but it is not caused by the pitch: the centre of pressure advances **because the body advances over
it.** That is measured CoP behaviour, and it is what turns three rockers into one continuous arc.

## What is honestly still missing

- **The vault is still too tall** — 4.7% of stature against a human ~2.5%. The remaining cause is a
  fully *locked* stance knee; real walking flattens the path with a stance-knee flexion wave of about
  15° at mid-stance. "Near straight" is not "locked". The mechanism is named rather than the number
  scaled, because scaling it would be tuning the answer.
- **The peak of the hip path is at push-off, not mid-stance.** A real hip is highest in the middle of
  stance; here 26° of plantarflexion lifts the ankle nearly 10% of stature and over-supports the end.
  The plantarflexion range is measured, so the error is in treating the foot as rigid about a single
  pitch rather than as a deforming arch.
- **No arch, no toes, no heel pad.** A foot stores and returns elastic energy in its plantar fascia
  (~8–17% of the stride's work) and none of that is here.
- **`swing = 0.42` rad is still the one number in this gait neither derived nor measured**, and the
  vault, the CoP travel and the stride all inherit that.

*Contained in `theHuman`. What it hands on: the reason a walk is cheap, and a sole that stays down.*
