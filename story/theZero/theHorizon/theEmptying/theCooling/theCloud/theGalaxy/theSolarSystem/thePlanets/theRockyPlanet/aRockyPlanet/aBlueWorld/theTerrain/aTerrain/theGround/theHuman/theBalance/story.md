# theBalance

**In plain words —** Every motion in the gait so far is sagittal — fore-aft and up. A real walking body also moves SIDEWAYS over each stance foot, because if it did not it would fall. That missing axis is most of what makes a figure look alive rather than railed.

*Declared, not built.* This chapter exists because `Chimera/docs/THE_STORY.md` needs it — the verbs
below are in the story and nothing derives them yet. It states its questions and derives no numbers,
which is the honest form of an empty chapter.

## The verbs that land here

- Deploy Bipod / Brace [Y]
- Steady Aim [Left Shift] -- and the sway IS theBreath, already derived at 15.7/min
- the weight shift under every step, which no key presses and every eye sees

## What it will have to derive

- lateral CoM excursion per step, from the frontal-plane inverted pendulum theHuman has
- pelvic list and rotation -- what lengthens a stride without lengthening a leg
- trunk counter-rotation and head stabilisation: the head stays still while all below moves
- reticle sway as a function of breath phase, heart rate and stance -- braced vs standing

## What it already has to work with

`theHuman` publishes these and they are checked:

- height_m, mass_kg, com_height_m, leg_length_m -- the body
- g, fall_rate_rad_s, capture_point_at_1ms -- the balance law
- duration_s (one stride), step_time_s, cadence_steps_s -- its clock
- gait_cycle (48 samples) -- the pose, so nothing re-derives how to walk

## What has to be decided first

- does bracing consume theHand, theStance, or both?
- is holding a breath a theBreath state with a CO2 cost, closing that loop?
- does the derived 4.7% vault (against a human 2.5%) get fixed here or in theAnkle?

*Contained in `theHuman`. Hands on: nothing yet.*
