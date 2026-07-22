"""The 'tree' construction operator.

Two jobs:
  1. build_skeleton(): grow a physics_tree and walk its branch hierarchy into
     plain nested dicts — a renderer-agnostic skeleton that BOTH backends
     consume (the 3D splatter and the HTML canvas).
  2. pose(): bend that skeleton under a resolved wind state.  DETERMINISTIC in
     (wind, time): same inputs -> same pose, forever (DESIGN §5).  This is the
     4th-dimension fill — the difference between a calm moment and a gale moment
     (DESIGN §4), applied directly rather than left to a simulation.

The wind articulation here is mirrored in JS inside backend_html so the two
backends agree.  They are guarded at the anchors (t=0, t=1) — see DESIGN §6.
"""
from __future__ import annotations
import math

from WorldModel.physics_tree import grow_tree


# ── build ──────────────────────────────────────────────────────────────────

def build_skeleton(seed: int = 7, trunk_height: float = 300.0,
                   trunk_radius: float = 13.0, max_depth: int = 4) -> dict:
    """Grow a physics_tree and walk segments[0]'s hierarchy into nested dicts.

    Caps the beam-mechanics trunk-radius blowup: physics_tree's
    _apply_beam_mechanics inflates the trunk radius to ~100 after growth
    (a real source-side issue — DESIGN §10); we clamp at the nominal radius
    at the construction layer, which is where rendering concerns belong."""
    segs = grow_tree(trunk_height=trunk_height, trunk_radius=trunk_radius,
                     max_depth=max_depth, seed=seed)
    root = segs[0]                       # the trunk PhysicsBranch, with .children
    cap = float(trunk_radius)

    def walk(b) -> dict:
        return {
            "start":  [float(b.start[0]), float(b.start[1]), float(b.start[2])],
            "dir":    [float(b.direction[0]), float(b.direction[1]), float(b.direction[2])],
            "length": float(b.length),
            "radius": min(float(b.radius), cap),
            "depth":  int(b.depth),
            "children": [walk(c) for c in b.children],
        }

    sk = walk(root)
    _annotate(sk)
    return sk


def _annotate(node: dict) -> None:
    """Tag leaves, and give each branch a stable phase so gusts ripple through
    the canopy instead of pulsing in unison."""
    node["is_leaf"] = len(node["children"]) == 0
    node["phase"] = (node["start"][0] * 0.5 + node["start"][2] * 0.3) % (2.0 * math.pi)
    for c in node["children"]:
        _annotate(c)


def max_depth_of(node: dict) -> int:
    if not node["children"]:
        return node["depth"]
    return max(max_depth_of(c) for c in node["children"])


# ── pose (the wind fill) ────────────────────────────────────────────────────

def _rot_y(v, ang):
    """Rotate a 3-vector about +Y.  ang>0 tilts +Z toward +X — wind blows +X."""
    c, s = math.cos(ang), math.sin(ang)
    x, y, z = v
    return [c * x + s * z, y, -s * x + c * z]


def pose(node: dict, wind: dict, time: float, max_depth: int,
         parent_bend: float = 0.0, parent_end=None) -> dict:
    """Return a posed copy of the skeleton.

    Bend accumulates down the hierarchy, so a child inherits its parent's bend
    (they are physically attached) and the tips move most — a cantilever.
    `wind` is a resolved state from Axis.fill(): lean (steady downwind tilt),
    sway (gust amplitude), gust_hz (gust frequency); flutter and sky are read by
    the backends, not here."""
    df = node["depth"] / max(1, max_depth)
    gust = 0.5 + 0.5 * math.sin(2.0 * math.pi * wind.get("gust_hz", 0.6) * time + node["phase"])
    local = (wind.get("lean", 0.0) * 0.12 * (0.4 + df)
             + wind.get("sway", 0.0) * gust * 0.16 * (0.3 + df))
    total = parent_bend + local

    start = list(node["start"]) if parent_end is None else parent_end
    d = _rot_y(node["dir"], total)
    L = node["length"]
    end = [start[0] + d[0] * L, start[1] + d[1] * L, start[2] + d[2] * L]

    return {
        "start": start, "end": end, "radius": node["radius"], "depth": node["depth"],
        "is_leaf": node["is_leaf"], "phase": node["phase"], "bend": total,
        "children": [pose(c, wind, time, max_depth, total, end) for c in node["children"]],
    }
