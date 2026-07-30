# theLoad

**In plain words —** A suit hopper full of ore is mass, and mass is already load-bearing in this tree — `theHuman` computes its cadence and foot pressure from the SUITED mass. Everything picked up should move those numbers, and right now nothing does.

*Declared, not built.* This chapter exists because `Chimera/docs/THE_STORY.md` needs it — the verbs
below are in the story and nothing derives them yet. It states its questions and derives no numbers,
which is the honest form of an empty chapter.

## The verbs that land here

- Open Suit Storage [I]
- Vacuum-Collect Ore (Hold F) -- the hopper fills
- Jettison Tailings / Eject Unstable Payload [Left Alt + J]
- Cargo Manifest [M]

## What it will have to derive

- carried mass -> cadence, via the swing period theHuman already derives from mass
- carried mass -> foot pressure -> the margin against theGround's bearing capacity
- VOLUME as well as mass: a hopper has a size and ore has a density
- where the load sits: a back pack moves the CoM and the whole balance problem with it

## What it already has to work with

`theHuman` publishes these and they are checked:

- height_m, mass_kg, com_height_m, leg_length_m -- the body
- g, fall_rate_rad_s, capture_point_at_1ms -- the balance law
- duration_s (one stride), step_time_s, cadence_steps_s -- its clock
- gait_cycle (48 samples) -- the pose, so nothing re-derives how to walk

## What has to be decided first

- is the inventory a volume, a mass, or a list -- and does the answer change the gait?
- does theGround's bearing capacity ever actually bite, or is the margin always 5x?
- does an off-centre load force a lean, which is theBalance?

*Contained in `theHuman`. Hands on: nothing yet.*
