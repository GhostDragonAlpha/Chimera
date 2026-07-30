"""theEye -- light in, and therefore the camera

STUB. Declared from the story, derived from nothing yet. `derive()` returns its own size, its own
duration and `stub: True` -- and NO physics -- so the tree grows, the membrane is visible in
numbers.json, and nobody can mistake an empty chapter for a finished one.

WHAT IT MUST DERIVE, when someone fills it in:
    * field of view, from eye separation and the visor's own aperture (aHuman derives its radius)
    * dark adaptation as a TIME CONSTANT -- how long a polar night takes to become visible
    * acuity: the angular size at which a grain stops being resolvable, which bounds the render
    * what the visor costs -- transmission, and the IR rejection that makes it dark
    * thermal optics as an actual band, not a colour filter: what emits at aBlueWorld's temperatures

WHAT IT CONSUMES from theHuman (all of these are already published and checked):
    * height_m, mass_kg, com_height_m, leg_length_m -- the body
    * g, fall_rate_rad_s, capture_point_at_1ms -- the balance law
    * duration_s (one stride), step_time_s, cadence_steps_s -- its clock
    * gait_cycle (48 samples) -- the pose, so nothing re-derives how to walk

THE STORY'S VERBS THAT LAND HERE:
    * Cycle Visor Optics [N] -- standard / thermal / low-light amplification
    * Visor HUD Elements Toggle [F12]
    * Clear Visor Condensation [Left Alt + X] -- and theSweep already derives WHY it fogs
    * Helmet Torch [T]
    * Optic Sights View / ADS [Right Mouse]

THE OPEN QUESTIONS -- what has to be decided before a line of physics is written:
    * is the camera INSIDE the helmet (visor edge visible, fogging in frame) or at the eye?
    * does acuity bound the clipmap's grain size, closing the loop with walker.py's _STEP0?
    * is thermal a second render pass over the same matter, or a different measure of it?
"""
from __future__ import annotations


def derive(parent, free):
    if parent is None or "height_m" not in parent:
        raise ValueError("theEye requires theHuman as its parent")
    h = float(parent["height_m"])
    return {
        # A STUB STATES ITS SCALE AND NOTHING ELSE. `extent_m` is the only honest number available
        # before the physics exists -- it is a size, read off the body, not a claim about behaviour.
        "extent_m": float(parent['height_m']) * 0.024,
        "duration_s": float(parent["duration_s"]),
        "stub": True,
        "declared_by": "Chimera/docs/THE_STORY.md",
    }


def emit(nums, t=1.0):
    """No matter yet. A stub draws NOTHING rather than a placeholder: a placeholder in a splat buffer
    is a body this chapter has not built, and this project has a rule about that."""
    from matter import blank
    return blank(0)


def measure(nums):
    """The only thing a stub can honestly report is that it is one."""
    return {"stub": True, "derives_nothing_yet": True}
