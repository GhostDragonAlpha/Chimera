# theSkin

**In plain words —** The suit's insulation is derived in `aHuman` and the body's heat is derived in `theSweep`, but nothing derives the surface between them — or what happens when something goes through it. The story's only injury is a laser graze and a coagulant.

*Declared, not built.* This chapter exists because `Chimera/docs/THE_STORY.md` needs it — the verbs
below are in the story and nothing derives them yet. It states its questions and derives no numbers,
which is the honest form of an empty chapter.

## The verbs that land here

- Administer Bio-Patch [C] -- local coagulants after a laser graze
- the suit breach the story implies but never spells out

## What it will have to derive

- skin area from stature and mass (DuBois) -- theSweep already assumes 1.83 m2 and should read it
- damage as an ENERGY, not a hit point: joules deposited, over what area, in what time
- what a breach costs -- theBreath's loop pressure is what leaks, and it derived that
- healing as a rate, so time is the currency rather than a potion

## What it already has to work with

`theHuman` publishes these and they are checked:

- height_m, mass_kg, com_height_m, leg_length_m -- the body
- g, fall_rate_rad_s, capture_point_at_1ms -- the balance law
- duration_s (one stride), step_time_s, cadence_steps_s -- its clock
- gait_cycle (48 samples) -- the pose, so nothing re-derives how to walk

## What has to be decided first

- is damage a state of theSkin or a separate membrane?
- does a breach couple to theBreath, ending the excursion the way the numbers already say?
- is there a body temperature to lose, and does aHuman's 11.9 mm of insulation defend it?

*Contained in `theHuman`. Hands on: nothing yet.*
