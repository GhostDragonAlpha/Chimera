# theThrust

**In plain words —** The story drifts Vance across a crater rim on jetpack in low gravity, and stands him in a depressurised hold in zero-G. Every locomotion law in this tree so far needs a foot on something. This one has none, and none of them apply.

*Declared, not built.* This chapter exists because `Chimera/docs/THE_STORY.md` needs it — the verbs
below are in the story and nothing derives them yet. It states its questions and derives no numbers,
which is the honest form of an empty chapter.

## The verbs that land here

- EVA Thrusters / Jetpack (Hold Spacebar)
- Vertical Hop / Zero-G Leap [Spacebar] -- the same key, a different physics
- working in a depressurised cargo hold with the graviton beam

## What it will have to derive

- thrust and specific impulse -- and therefore a propellant budget, which is a MASS
- delta-v for a crater-rim drift, from the gravity aBlueWorld derives
- attitude control: a body with no contact rotates when it pushes off-centre
- the interaction with theLoad -- carried ore is reaction mass you did not want

## What it already has to work with

`theHuman` publishes these and they are checked:

- height_m, mass_kg, com_height_m, leg_length_m -- the body
- g, fall_rate_rad_s, capture_point_at_1ms -- the balance law
- duration_s (one stride), step_time_s, cadence_steps_s -- its clock
- gait_cycle (48 samples) -- the pose, so nothing re-derives how to walk

## What has to be decided first

- is thrust a suit system (a child of aHuman) or a body verb (a child of theHuman)?
- does the gait membrane switch OFF, or does it degrade continuously with contact time?
- does propellant come out of the same budget as theBreath's oxygen?

*Contained in `theHuman`. Hands on: nothing yet.*
