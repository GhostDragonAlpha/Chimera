# theGrip

**In plain words —** The story has Vance clamp to a sheer rock face and walk it like a floor. That is not a movement mode, it is a DIFFERENT CONTACT LAW: everything `theAnkle` derived assumes the support force opposes gravity, and here it opposes an arbitrary surface normal.

*Declared, not built.* This chapter exists because `Chimera/docs/THE_STORY.md` needs it — the verbs
below are in the story and nothing derives them yet. It states its questions and derives no numbers,
which is the honest form of an empty chapter.

## The verbs that land here

- Mag-Boot Adhesion [Left Alt + B] -- clamping a sheer face to walk it like a floor
- mag-boots crunching frozen slush, in Act I -- adhesion is on by default in the station

## What it will have to derive

- adhesion force, and whether it exceeds the body weight it must hold against the normal
- the gait on a wall: theAnkle's rocker and duty factor with gravity ACROSS the sole
- the release condition -- what breaks the clamp, and what that does to a body mid-stride
- power draw, which theSweep showed is the cheap part and the battery is not

## What it already has to work with

`theHuman` publishes these and they are checked:

- height_m, mass_kg, com_height_m, leg_length_m -- the body
- g, fall_rate_rad_s, capture_point_at_1ms -- the balance law
- duration_s (one stride), step_time_s, cadence_steps_s -- its clock
- gait_cycle (48 samples) -- the pose, so nothing re-derives how to walk

## What has to be decided first

- does the local UP become the surface normal, which is what a membrane's frame is for?
- does the whole gait re-derive on a wall, or does the vault simply vanish?
- what does the ferrous requirement mean -- can it grip aBlueWorld's regolith at all?

*Contained in `theHuman`. Hands on: nothing yet.*
