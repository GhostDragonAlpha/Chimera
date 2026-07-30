"""theGrip -- mag-boots -- and they break the assumption that down is where gravity points

STUB. Declared from the story, derived from nothing yet. `derive()` returns its own size, its own
duration and `stub: True` -- and NO physics -- so the tree grows, the membrane is visible in
numbers.json, and nobody can mistake an empty chapter for a finished one.

WHAT IT MUST DERIVE, when someone fills it in:
    * adhesion force, and whether it exceeds the body weight it must hold against the normal
    * the gait on a wall: theAnkle's rocker and duty factor with gravity ACROSS the sole
    * the release condition -- what breaks the clamp, and what that does to a body mid-stride
    * power draw, which theSweep showed is the cheap part and the battery is not

WHAT IT CONSUMES from theHuman (all of these are already published and checked):
    * height_m, mass_kg, com_height_m, leg_length_m -- the body
    * g, fall_rate_rad_s, capture_point_at_1ms -- the balance law
    * duration_s (one stride), step_time_s, cadence_steps_s -- its clock
    * gait_cycle (48 samples) -- the pose, so nothing re-derives how to walk

THE STORY'S VERBS THAT LAND HERE:
    * Mag-Boot Adhesion [Left Alt + B] -- clamping a sheer face to walk it like a floor
    * mag-boots crunching frozen slush, in Act I -- adhesion is on by default in the station

THE OPEN QUESTIONS -- what has to be decided before a line of physics is written:
    * does the local UP become the surface normal, which is what a membrane's frame is for?
    * does the whole gait re-derive on a wall, or does the vault simply vanish?
    * what does the ferrous requirement mean -- can it grip aBlueWorld's regolith at all?
"""
from __future__ import annotations


def derive(parent, free):
    if parent is None or "height_m" not in parent:
        raise ValueError("theGrip requires theHuman as its parent")
    h = float(parent["height_m"])
    return {
        # A STUB STATES ITS SCALE AND NOTHING ELSE. `extent_m` is the only honest number available
        # before the physics exists -- it is a size, read off the body, not a claim about behaviour.
        "extent_m": float(parent['height_m']) * 0.15,
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
