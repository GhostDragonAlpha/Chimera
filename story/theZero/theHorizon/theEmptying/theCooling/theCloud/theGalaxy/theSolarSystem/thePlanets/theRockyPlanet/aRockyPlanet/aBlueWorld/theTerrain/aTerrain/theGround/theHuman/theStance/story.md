# theStance

**In plain words —** Standing is one posture out of six the story uses, and the other five are missing. Each changes the contact patch, the centre of mass height, and therefore the whole balance problem `theHuman` solved once for standing.

*Declared, not built.* This chapter exists because `Chimera/docs/THE_STORY.md` needs it — the verbs
below are in the story and nothing derives them yet. It states its questions and derives no numbers,
which is the honest form of an empty chapter.

## The verbs that land here

- Low Profile Stance [Left Ctrl] -- crouch
- Prone Stance [X] -- crawling under thermal motion grids
- Combat Slide [Left Ctrl while sprinting]
- Corner Peeking Left / Right [Q / E] -- leaning past cover
- Mantle / Vault [Spacebar at a ledge]

## What it will have to derive

- CoM height per posture, which re-runs the inverted pendulum: fall_rate = sqrt(g/H)
- contact area and bearing pressure per posture -- prone spreads a body over ~5x the area
- the transition COST: how long standing-to-prone takes, and it is not free
- a lean's limit: how far the CoM can go outside the feet before the capture point is unreachable

## What it already has to work with

`theHuman` publishes these and they are checked:

- height_m, mass_kg, com_height_m, leg_length_m -- the body
- g, fall_rate_rad_s, capture_point_at_1ms -- the balance law
- duration_s (one stride), step_time_s, cadence_steps_s -- its clock
- gait_cycle (48 samples) -- the pose, so nothing re-derives how to walk

## What has to be decided first

- is prone a posture or a different LOCOMOTION (crawling is not walking)?
- does a slide need friction from theGround, and does the regolith's repose angle bound it?
- does mantling need theHand -- can you vault a ledge with a rifle in both hands?

*Contained in `theHuman`. Hands on: nothing yet.*
