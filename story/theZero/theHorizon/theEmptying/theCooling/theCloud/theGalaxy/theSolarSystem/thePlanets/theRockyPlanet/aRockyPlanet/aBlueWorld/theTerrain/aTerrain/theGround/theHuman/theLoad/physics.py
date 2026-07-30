"""theLoad -- what the body carries, and what carrying it costs

STUB. Declared from the story, derived from nothing yet. `derive()` returns its own size, its own
duration and `stub: True` -- and NO physics -- so the tree grows, the membrane is visible in
numbers.json, and nobody can mistake an empty chapter for a finished one.

WHAT IT MUST DERIVE, when someone fills it in:
    * carried mass -> cadence, via the swing period theHuman already derives from mass
    * carried mass -> foot pressure -> the margin against theGround's bearing capacity
    * VOLUME as well as mass: a hopper has a size and ore has a density
    * where the load sits: a back pack moves the CoM and the whole balance problem with it

WHAT IT CONSUMES from theHuman (all of these are already published and checked):
    * height_m, mass_kg, com_height_m, leg_length_m -- the body
    * g, fall_rate_rad_s, capture_point_at_1ms -- the balance law
    * duration_s (one stride), step_time_s, cadence_steps_s -- its clock
    * gait_cycle (48 samples) -- the pose, so nothing re-derives how to walk

THE STORY'S VERBS THAT LAND HERE:
    * Open Suit Storage [I]
    * Vacuum-Collect Ore (Hold F) -- the hopper fills
    * Jettison Tailings / Eject Unstable Payload [Left Alt + J]
    * Cargo Manifest [M]

THE OPEN QUESTIONS -- what has to be decided before a line of physics is written:
    * is the inventory a volume, a mass, or a list -- and does the answer change the gait?
    * does theGround's bearing capacity ever actually bite, or is the margin always 5x?
    * does an off-centre load force a lean, which is theBalance?
"""
from __future__ import annotations


def derive(parent, free):
    if parent is None or "height_m" not in parent:
        raise ValueError("theLoad requires theHuman as its parent")
    h = float(parent["height_m"])
    return {
        # A STUB STATES ITS SCALE AND NOTHING ELSE. `extent_m` is the only honest number available
        # before the physics exists -- it is a size, read off the body, not a claim about behaviour.
        "extent_m": float(parent['height_m']) * 0.5,
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
