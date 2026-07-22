"""THE NOUN CONSTRUCTOR — a photo-authorable 2D seed -> a 3D noun.

construct() is the whole decode: build a skeleton, flatten it to the 2D picture,
lift by the winning golden rule, and shape the crown.  Every argument is a knob
the AI sets by LOOKING at a reference photo (see REFERENCE_TO_NOUN.md):

    seed          which specific branch pattern (vary if the silhouette is off)
    trunk_height  overall size / how high the trunk forks
    trunk_radius  trunk stoutness  (small = sapling, large = old oak)
    max_depth     branch density / canopy fullness
    droop         crown shape: 0 = flat umbrella, ~1.2 = drooping oak dome
    spread        canopy width
    lift_amount   how much 3rd dimension is filled (1.0 = full volume)
    rule          the construction rule (golden won the bake-off)

The result composes with any verb (e.g. Construction/tree.pose for wind):
    blow(construct(picture)).
"""
from __future__ import annotations

from Construction import tree as T
from Construction import lift as L


def construct(seed: int = 42, trunk_height: float = 280, trunk_radius: float = 26,
              max_depth: int = 5, droop: float = 0.0, spread: float = 0.0,
              lift_amount: float = 1.0, rule=L.golden_rule) -> dict:
    """Author -> 3D noun.  Deterministic in every argument."""
    sk = T.build_skeleton(seed=seed, trunk_height=trunk_height,
                          trunk_radius=trunk_radius, max_depth=max_depth)
    noun = L.lift(L.flatten(sk, rule), lift_amount)
    if droop or spread:
        noun = L.shape_crown(noun, droop=droop, spread=spread,
                             max_depth=T.max_depth_of(noun))
    return noun
