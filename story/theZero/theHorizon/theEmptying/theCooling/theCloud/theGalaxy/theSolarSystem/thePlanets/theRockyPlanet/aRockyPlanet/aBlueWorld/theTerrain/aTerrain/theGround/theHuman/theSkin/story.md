# theSkin

**In plain words —** The suit's insulation is derived in `aHuman` and the body's heat is derived in `theSweep`, and now the surface between them is derived too: skin is a 60-micron melanin filter crossed twice, over blood-bearing collagen that diffuses light — red furthest, which is why a finger glows red against a torch. What happens when something goes THROUGH it is still open: the story's only injury is a laser graze and a coagulant.

*Optics and area built 2026-07-31 (F1).* The light model is `story/skin_optics.py` — Jacques'
measured epidermis/dermis formulas over Prahl's archived hemoglobin table, reproduced against the
article's own worked examples within 3%. The area is DuBois on the ANSUR-median body (2.01 m², not
the typed 1.83 of the 70 kg "standard man"). Both arrive through the parent, which derives the skin
once for both children.

## The verbs that land here (still open)

- Administer Bio-Patch [C] -- local coagulants after a laser graze
- the suit breach the story implies but never spells out

## What it still has to derive

- damage as an ENERGY, not a hit point: joules deposited, over what area, in what time
- what a breach costs -- theBreath's loop pressure is what leaks, and it derived that
- healing as a rate, so time is the currency rather than a potion

## What it already has to work with

`theHuman` publishes these and they are checked:

- height_m, mass_kg, com_height_m, leg_length_m -- the body
- melanin_fraction, skin_albedo_rgb, skin_sss_mfp_mm, skin_area_m2 -- the boundary itself
- g, fall_rate_rad_s, capture_point_at_1ms -- the balance law
- duration_s (one stride), step_time_s, cadence_steps_s -- its clock
- gait_cycle (48 samples) -- the pose, so nothing re-derives how to walk

## What has to be decided first

- is damage a state of theSkin or a separate membrane?
- does a breach couple to theBreath, ending the excursion the way the numbers already say?
- is there a body temperature to lose, and does aHuman's insulation defend it?

*Contained in `theHuman`. Hands on: nothing yet.*
