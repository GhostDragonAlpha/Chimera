# theHand

<!-- CHIMERA-LAW -->
> *Derive before you train — [THE LAW](../../../../../../../../../../../../../../../../../docs/THE_LAW.md). Every number below is derived from the parent's or measured; none is chosen.*
<!-- CHIMERA-LAW -->

> **chapter 24** of the story  ·  **t = 5.75715e+15 s** since theZero  ·  lasts **0.594644 s**
>
> *The serial is the place in TIME, not in the folder tree. A path says what contains
> what; this says what follows what. Both are published — `timeline_serial` in
> numbers.json and here — so the story and its numbers cannot disagree about when.*


**In plain words —** What the person can do to things. The manual's own control law lives here: COMMAND THE PROCESS, NOT THE POSITION — the hand closes until it cannot, and the OBJECT decides where the fingers land. One GRAB serves a pin and a bowling ball.

*Declared, not built.* This chapter exists because `Chimera/docs/THE_STORY.md` needs it — the verbs
below are in the story and nothing derives them yet. It states its questions and derives no numbers,
which is the honest form of an empty chapter.

## The verbs that land here

- Neural Direct-Interact (Hold F) / Direct Action (Tap F)
- Arm Sidearm / Primary A / Primary B [1 / 2 / 3], Injector [4], Utility Core [5]
- Equip Scanner [6], Excavation Tool [7], Cultivation Kit [8]
- Melee Strike [B] / Weapon Bash (Hold B)
- Activate Graviton Beam + Torque Payload (Hold R + mouse)
- Bore / Excavate, Till, Plant, Harvest, Prune

## What it will have to derive

- grip force from forearm cross-section -- what mass can be held, and for how long
- the work envelope: where a hand can reach, from segment lengths theHuman already has
- what a tool's mass does to that envelope and to the shoulder torque
- the stop condition for each atom -- GRIP ends on contact force, not on a position

## What it already has to work with

`theHuman` publishes these and they are checked:

- height_m, mass_kg, com_height_m, leg_length_m -- the body
- g, fall_rate_rad_s, capture_point_at_1ms -- the balance law
- duration_s (one stride), step_time_s, cadence_steps_s -- its clock
- gait_cycle (48 samples) -- the pose, so nothing re-derives how to walk

## What has to be decided first

- is a tool a child membrane of theHand, or an object the world hands it?
- does the same GRIP law serve a rifle, a drill and a seedling, as the story implies?
- one hand or two -- does a braced rifle need both, and does that lock out the torch?

*Contained in `theHuman`. Hands on: nothing yet.*

## What it predicted that it was never given

`hand_over_stature_ratio` = **0.1103** — hand length as a fraction of standing height.

    ANSUR II, 6,068 adults, median 0.10996          this chapter derives 0.11030

Drillis & Contini's classical figure for the same ratio is 0.108. The hand here is not measured
from a hand: it is derived from the body the story already grew, and it lands inside a spread
measured on six thousand people, 0.3% from their median.

The spread is the sharper claim. This ratio's coefficient of variation across those adults is
**3.83%** — hands vary less, proportionally, than almost anything else about a person, which is why
one number can stand for a hand at all, and why a glove size predicts a grip.
