"""Teddy parts catalog — the membrane library.

Every body slot has multiple STYLE variants. A bear is an assembly: pick one
style per slot, get a parts list for teddy_body.py (SDF union, analytic mass,
surface sampling). Limbs are SEGMENTED: arm = upper_arm + forearm (+paw),
leg = thigh + shin (+foot) — every segment has its own joint pivot and axis,
which is what makes posing (and later, gravity) well-defined.

Base numbers measured from models/genbear3/eqonly_med.splat
(.tmp/eqonly_measure.json, cluster PCA), symmetrized about SPINE_X, then
slimmed per operator direction. Styles vary proportions around that base.
"""
import copy

SPINE_X = 0.03

# ---------------------------------------------------------------------------
# CATALOG: slot -> style -> param dict.
# prims: ellipsoid(c, r), sphere(c, r), capsule(a, b, r).
# Every part also gets parent / pivot / axis at assembly time (see JOINTS).
# ---------------------------------------------------------------------------
CATALOG = {
    "torso": {
        "slim":     dict(prim="ellipsoid", c=[0.03, -0.10, 0.00], r=[0.245, 0.26, 0.23]),
        "classic":  dict(prim="ellipsoid", c=[0.03, -0.10, 0.00], r=[0.28, 0.27, 0.26]),
        "potbelly": dict(prim="ellipsoid", c=[0.03, -0.11, 0.03], r=[0.29, 0.26, 0.30]),
    },
    "head": {
        "round": dict(prim="ellipsoid", c=[0.03, 0.33, 0.02], r=[0.185, 0.165, 0.165]),
        "wide":  dict(prim="ellipsoid", c=[0.03, 0.33, 0.02], r=[0.21, 0.155, 0.16]),
        "baby":  dict(prim="ellipsoid", c=[0.03, 0.345, 0.02], r=[0.225, 0.20, 0.195]),
    },
    "muzzle": {
        "small":   dict(prim="ellipsoid", c=[0.03, 0.27, 0.185], r=[0.075, 0.06, 0.085]),
        "classic": dict(prim="ellipsoid", c=[0.03, 0.27, 0.20], r=[0.09, 0.07, 0.10]),
        "long":    dict(prim="ellipsoid", c=[0.03, 0.265, 0.225], r=[0.085, 0.065, 0.125]),
    },
    "ear_L": {
        "round_small": dict(prim="sphere", c=[-0.175, 0.44, -0.02], r=[0.062, 0.062, 0.062]),
        "round_big":   dict(prim="sphere", c=[-0.19, 0.445, -0.02], r=[0.082, 0.082, 0.082]),
        "floppy":      dict(prim="capsule", a=[-0.16, 0.46, -0.02], b=[-0.25, 0.36, -0.02], r=[0.05, 0.05, 0.05]),
    },
    "ear_R": {
        "round_small": dict(prim="sphere", c=[0.235, 0.44, -0.02], r=[0.062, 0.062, 0.062]),
        "round_big":   dict(prim="sphere", c=[0.25, 0.445, -0.02], r=[0.082, 0.082, 0.082]),
        "floppy":      dict(prim="capsule", a=[0.22, 0.46, -0.02], b=[0.31, 0.36, -0.02], r=[0.05, 0.05, 0.05]),
    },
    # bead eyes: derived from head geometry — at x=0.03±0.07, y=0.355 the head
    # surface is z=0.171; centers at z=0.185 leave half the bead proud.
    "eye_L": {
        "bead": dict(prim="sphere", c=[-0.04, 0.355, 0.185], r=[0.025, 0.025, 0.025]),
    },
    "eye_R": {
        "bead": dict(prim="sphere", c=[0.10, 0.355, 0.185], r=[0.025, 0.025, 0.025]),
    },
    # segmented arm: shoulder -> elbow -> paw. ARMS OUT (operator 2026-08-20:
    # limbs must not touch torso/legs or the coat mixes at the contact).
    # A-pose; elbow ~0.12 clear of the torso surface, paws clear of thighs.
    "upper_arm_L": {
        "slim":    dict(prim="capsule", a=[-0.205, 0.05, 0.02], b=[-0.337, -0.001, 0.057], r=[0.052, 0.052, 0.052]),
        "classic": dict(prim="capsule", a=[-0.205, 0.05, 0.02], b=[-0.337, -0.001, 0.057], r=[0.068, 0.068, 0.068]),
        "chunky":  dict(prim="capsule", a=[-0.205, 0.05, 0.02], b=[-0.337, -0.001, 0.057], r=[0.085, 0.085, 0.085]),
    },
    "forearm_L": {
        "slim":    dict(prim="capsule", a=[-0.337, -0.001, 0.057], b=[-0.470, -0.059, 0.138], r=[0.047, 0.047, 0.047]),
        "classic": dict(prim="capsule", a=[-0.337, -0.001, 0.057], b=[-0.470, -0.059, 0.138], r=[0.06, 0.06, 0.06]),
        "chunky":  dict(prim="capsule", a=[-0.337, -0.001, 0.057], b=[-0.470, -0.059, 0.138], r=[0.075, 0.075, 0.075]),
    },
    "upper_arm_R": {
        "slim":    dict(prim="capsule", a=[0.265, 0.05, 0.02], b=[0.397, -0.001, 0.057], r=[0.052, 0.052, 0.052]),
        "classic": dict(prim="capsule", a=[0.265, 0.05, 0.02], b=[0.397, -0.001, 0.057], r=[0.068, 0.068, 0.068]),
        "chunky":  dict(prim="capsule", a=[0.265, 0.05, 0.02], b=[0.397, -0.001, 0.057], r=[0.085, 0.085, 0.085]),
    },
    "forearm_R": {
        "slim":    dict(prim="capsule", a=[0.397, -0.001, 0.057], b=[0.530, -0.059, 0.138], r=[0.047, 0.047, 0.047]),
        "classic": dict(prim="capsule", a=[0.397, -0.001, 0.057], b=[0.530, -0.059, 0.138], r=[0.06, 0.06, 0.06]),
        "chunky":  dict(prim="capsule", a=[0.397, -0.001, 0.057], b=[0.530, -0.059, 0.138], r=[0.075, 0.075, 0.075]),
    },
    # segmented leg: hip -> knee -> foot (sitting pose: forward-down)
    "thigh_L": {
        "slim":    dict(prim="capsule", a=[-0.15, -0.17, 0.04], b=[-0.21, -0.29, 0.17], r=[0.072, 0.072, 0.072]),
        "classic": dict(prim="capsule", a=[-0.17, -0.18, 0.05], b=[-0.23, -0.30, 0.17], r=[0.095, 0.095, 0.095]),
    },
    "shin_L": {
        "slim":    dict(prim="capsule", a=[-0.21, -0.29, 0.17], b=[-0.25, -0.40, 0.30], r=[0.062, 0.062, 0.062]),
        "classic": dict(prim="capsule", a=[-0.23, -0.30, 0.17], b=[-0.27, -0.40, 0.30], r=[0.085, 0.085, 0.085]),
    },
    "thigh_R": {
        "slim":    dict(prim="capsule", a=[0.21, -0.17, 0.04], b=[0.27, -0.29, 0.17], r=[0.072, 0.072, 0.072]),
        "classic": dict(prim="capsule", a=[0.23, -0.18, 0.05], b=[0.29, -0.30, 0.17], r=[0.095, 0.095, 0.095]),
    },
    "shin_R": {
        "slim":    dict(prim="capsule", a=[0.27, -0.29, 0.17], b=[0.31, -0.40, 0.30], r=[0.062, 0.062, 0.062]),
        "classic": dict(prim="capsule", a=[0.29, -0.30, 0.17], b=[0.33, -0.40, 0.30], r=[0.085, 0.085, 0.085]),
    },
}

# JOINTS: slot -> (parent_slot, pivot, axis). Pivot = where the segment rotates.
# Swing axes are world-frame at rest pose; x-axis = pitch forward/back,
# z-axis = spread sideways, y-axis = twist.
JOINTS = {
    "torso":       (None, [0, 0, 0], [0, 1, 0]),
    "head":        ("torso", [SPINE_X, 0.15, 0.00], [1, 0, 0]),       # neck nod
    "muzzle":      ("head", [SPINE_X, 0.27, 0.12], [1, 0, 0]),
    "ear_L":       ("head", [-0.16, 0.42, -0.02], [0, 0, 1]),
    "ear_R":       ("head", [0.22, 0.42, -0.02], [0, 0, 1]),
    "eye_L":       ("head", [-0.04, 0.355, 0.185], [0, 0, 1]),
    "eye_R":       ("head", [0.10, 0.355, 0.185], [0, 0, 1]),
    "upper_arm_L": ("torso", [-0.205, 0.05, 0.02], [1, 0, 0]),        # shoulder
    "forearm_L":   ("upper_arm_L", [-0.337, -0.001, 0.057], [1, 0, 0]), # elbow
    "upper_arm_R": ("torso", [0.265, 0.05, 0.02], [1, 0, 0]),
    "forearm_R":   ("upper_arm_R", [0.397, -0.001, 0.057], [1, 0, 0]),
    "thigh_L":     ("torso", [-0.15, -0.17, 0.04], [1, 0, 0]),        # hip
    "shin_L":      ("thigh_L", [-0.21, -0.29, 0.17], [1, 0, 0]),      # knee
    "thigh_R":     ("torso", [0.21, -0.17, 0.04], [1, 0, 0]),
    "shin_R":      ("thigh_R", [0.27, -0.29, 0.17], [1, 0, 0]),
}

DEFAULT_STYLE = {
    "torso": "slim", "head": "round", "muzzle": "long",
    "ear_L": "round_small", "ear_R": "round_small",
    "eye_L": "bead", "eye_R": "bead",
    "upper_arm_L": "slim", "forearm_L": "slim",
    "upper_arm_R": "slim", "forearm_R": "slim",
    "thigh_L": "slim", "shin_L": "slim", "thigh_R": "slim", "shin_R": "slim",
}


def assemble(style_map=None):
    """style_map: {slot: style_name}. Returns the teddy_body.py PARTS list."""
    style_map = {**DEFAULT_STYLE, **(style_map or {})}
    parts = []
    for slot, (parent, pivot, axis) in JOINTS.items():
        if slot not in style_map:
            continue
        style = style_map[slot]
        if style not in CATALOG[slot]:
            raise KeyError(f"{slot}: no style '{style}' (have {list(CATALOG[slot])})")
        p = copy.deepcopy(CATALOG[slot][style])
        p["name"] = slot
        p["style"] = style
        p["parent"] = parent
        p["pivot"] = list(pivot)
        p["axis"] = list(axis)
        parts.append(p)
    return parts


if __name__ == "__main__":
    import sys
    sm = None
    if len(sys.argv) > 1:  # e.g. python teddy_catalog.py torso=potbelly head=baby
        sm = dict(kv.split("=") for kv in sys.argv[1:])
    parts = assemble(sm)
    print(f"assembled {len(parts)} parts:")
    for p in parts:
        print(f"  {p['name']:12s} style={p['style']:12s} parent={str(p['parent']):12s} {p['prim']}")
