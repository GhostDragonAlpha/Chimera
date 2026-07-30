# theEye

**In plain words —** What the person can see. This is the only unbuilt port that changes what the SCREEN shows — right now the camera is a free-floating lens that owes nothing to the body it sits inside, so a derived visor, a derived sun altitude and a polar night all render identically.

*Declared, not built.* This chapter exists because `Chimera/docs/THE_STORY.md` needs it — the verbs
below are in the story and nothing derives them yet. It states its questions and derives no numbers,
which is the honest form of an empty chapter.

## The verbs that land here

- Cycle Visor Optics [N] -- standard / thermal / low-light amplification
- Visor HUD Elements Toggle [F12]
- Clear Visor Condensation [Left Alt + X] -- and theSweep already derives WHY it fogs
- Helmet Torch [T]
- Optic Sights View / ADS [Right Mouse]

## What it will have to derive

- field of view, from eye separation and the visor's own aperture (aHuman derives its radius)
- dark adaptation as a TIME CONSTANT -- how long a polar night takes to become visible
- acuity: the angular size at which a grain stops being resolvable, which bounds the render
- what the visor costs -- transmission, and the IR rejection that makes it dark
- thermal optics as an actual band, not a colour filter: what emits at aBlueWorld's temperatures

## What it already has to work with

`theHuman` publishes these and they are checked:

- height_m, mass_kg, com_height_m, leg_length_m -- the body
- g, fall_rate_rad_s, capture_point_at_1ms -- the balance law
- duration_s (one stride), step_time_s, cadence_steps_s -- its clock
- gait_cycle (48 samples) -- the pose, so nothing re-derives how to walk

## What has to be decided first

- is the camera INSIDE the helmet (visor edge visible, fogging in frame) or at the eye?
- does acuity bound the clipmap's grain size, closing the loop with walker.py's _STEP0?
- is thermal a second render pass over the same matter, or a different measure of it?

*Contained in `theHuman`. Hands on: nothing yet.*
