"""THE CONSTRUCTION ALGORITHM: a flat 2D picture -> a 3D form (DESIGN §3, §4).

This is the piece the wind demo skipped.  There, the tree was born 3D.  Here the
tree is AUTHORED FLAT — a 2D picture in the XZ plane, carrying no depth at all —
and the construction FILLS IN the third dimension deterministically by a design
principle (golden-angle phyllotaxis): each branch's outward reach is rotated
about the vertical axis by an accumulated azimuth.

    amount = 0.0   ->   the flat 2D picture (every branch in the drawing plane)
    amount = 1.0   ->   the full 3D volume (branches fanned around the trunk)

This is CONSTRUCTION, not extraction.  The depth is not recovered from the input
(the input has none) — it is INVENTED by the rule.  And it is DIRECT, not
emergent: `lift(flat, amount)` is a pure function; same inputs -> same 3D form,
forever.  `amount` is a dial you can turn, or drive from game state.

The JS mirror of flatten()/lift() lives in Construction/viewer3d.py so the
orbitable dev viewer and this Python renderer construct the same geometry.
"""
from __future__ import annotations
import math

GOLDEN = math.pi * (3.0 - math.sqrt(5.0))   # ~137.5°, the phyllotactic angle


def _flat_dir(d):
    """Collapse a 3D direction to the XZ drawing plane: keep how UP-vs-OUT the
    branch is (vertical dz, total horizontal reach), throw away its compass
    direction (which way it pointed in Y).  Signed by X so the flat picture is
    two-sided, not a one-way fan."""
    dx, dy, dz = d
    hs = math.copysign(math.hypot(dx, dy), dx if dx != 0.0 else 1.0)  # signed horizontal reach
    m = math.sqrt(hs * hs + dz * dz) or 1e-9
    return [hs / m, 0.0, dz / m]


# ── the construction rules to bake off (each assigns a branch its azimuth) ──
# The rule IS the "dynamics" that fills the third dimension.  Try them all;
# Construction/measure.py scores which reconstructs the best 3D noun.
def golden_rule(idx, nsib, depth):  return GOLDEN * idx                 # phyllotaxis
def radial_rule(idx, nsib, depth):  return 2.0 * math.pi * idx / max(1, nsib)  # even fan
def mirror_rule(idx, nsib, depth):  return math.pi / 2 if idx % 2 == 0 else 3 * math.pi / 2  # bilateral ±Y
def flat_rule(idx, nsib, depth):    return 0.0                          # no depth (control)
def random_rule(idx, nsib, depth):                                      # scrambled (control)
    h = ((idx * 73856093) ^ ((depth + 1) * 19349663)) & 0xFFFF
    return (h / 0xFFFF) * 2.0 * math.pi

RULES = {"flat": flat_rule, "mirror": mirror_rule, "radial": radial_rule,
         "random": random_rule, "golden": golden_rule}


def flatten(skeleton: dict, rule=golden_rule) -> dict:
    """Project a 3D skeleton onto the XZ plane -> a genuine 2D picture, and tag
    each branch with an azimuth from `rule` for the lift to fill depth with."""
    def walk(n: dict, idx: int, nsib: int) -> dict:
        kids = n["children"]
        return {
            "len": n["length"],
            "radius": n["radius"],
            "depth": n["depth"],
            "is_leaf": n["is_leaf"],
            "phase": n.get("phase", 0.0),
            "dir2": _flat_dir(n["dir"]),     # [signed_horizontal, 0, vertical], unit
            "azi": rule(idx, nsib, n["depth"]),   # sibling fan; accumulated in lift()
            "children": [walk(c, i, len(kids)) for i, c in enumerate(kids)],
        }
    flat = walk(skeleton, 0, 1)
    flat["start2"] = [float(skeleton["start"][0]), 0.0, float(skeleton["start"][2])]
    return flat


def lift(flat: dict, amount: float, start=None, parent_azi: float = 0.0) -> dict:
    """Fill in the third dimension.  Rotate each branch's horizontal reach about
    the vertical (Z) axis by (accumulated azimuth × amount); children inherit the
    parent's azimuth so whole limbs twist into depth coherently.  Returns a 3D
    skeleton with the same node shape the renderers expect
    (start/end/dir/radius/depth/is_leaf/children)."""
    azi = parent_azi + flat["azi"]
    phi = azi * amount
    hx, _, dz = flat["dir2"]
    d = [hx * math.cos(phi), hx * math.sin(phi), dz]
    m = math.sqrt(d[0] * d[0] + d[1] * d[1] + d[2] * d[2]) or 1e-9
    d = [d[0] / m, d[1] / m, d[2] / m]

    s = list(flat.get("start2", [0.0, 0.0, 0.0])) if start is None else start
    L = flat["len"]
    e = [s[0] + d[0] * L, s[1] + d[1] * L, s[2] + d[2] * L]

    return {
        "start": s, "end": e, "dir": d, "length": L, "phase": flat.get("phase", 0.0),
        "radius": flat["radius"], "depth": flat["depth"], "is_leaf": flat["is_leaf"],
        "children": [lift(c, amount, e, azi) for c in flat["children"]],
    }


def y_spread(node: dict) -> float:
    """Max |Y| anywhere in a lifted skeleton — 0 means still flat, >0 means depth
    was filled in.  A cheap witness that the construction actually did something."""
    m = abs(node["end"][1])
    for c in node["children"]:
        m = max(m, y_spread(c))
    return m
