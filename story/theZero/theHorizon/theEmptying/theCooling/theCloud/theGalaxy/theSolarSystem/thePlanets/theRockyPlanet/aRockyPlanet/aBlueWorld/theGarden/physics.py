"""theGarden -- PLACEHOLDER GEOMETRY. This membrane draws; it does not yet DERIVE.

    Declared in terms_data.py; placed under aBlueWorld.

RULE 0, AND IT IS A WEAK THEORY ON PURPOSE RATHER THAN A MISSING ONE.

  STATEMENT   This chapter has no law yet. What it claims is only about its own EXTENT: a
              placeholder must be framed like its neighbours, so its extent is read from the
              PARENT's published `extent_m` and scaled by one declared factor. It claims nothing
              about what theGarden IS.
  PREDICTION  Move the parent's extent and this membrane's extent moves with it, by exactly
              `EXTENT_FRAC`. Its grain count is `grains_for` at that extent, like every other
              membrane's, so it costs what a body of its size costs.
  FALSIFIER   The extent does not track the parent (the slider test fails), or any number here is
              cited as a fact about theGarden. `placeholder: true` is published in numbers.json so
              nothing downstream can mistake this for derived matter.

WHY A STUB AT ALL. `docs/TERM_INVENTORY.md` measured 46 terms declared in the engine's vocabulary
with no emit() anywhere; the viewer cannot show them and the tree does not contain them. This is
one of five built so the gap has a floor to stand on -- NOT so it can be counted as closed.

    A PLACEHOLDER THAT ANNOUNCES ITSELF IS HONEST. ONE THAT DOES NOT IS THE SPECIFICATION
    CITED AS PROOF.

The parent named in `terms_data.py` is not a node of this tree, so the substitution above is
declared here rather than made silently.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[12]))
import matter as M

EXTENT_FRAC = 0.3      # this placeholder's size as a fraction of its parent's extent
RGB = (0.32, 0.62, 0.26)
N_GRAINS = 3000


def derive(parent, free):
    if parent is None:
        raise ValueError("theGarden requires a parent membrane")
    ext = float(parent.get("extent_m", 1.0)) * EXTENT_FRAC
    return {
        "extent_m": ext,
        "duration_s": float(parent.get("duration_s", 1.0)),
        "placeholder": True,
        "placeholder_reason": "declared in terms_data.py, no law written yet",
        "parent_substituted": 'aPlanet -> aBlueWorld (the lush place is on the habitable world)',
        "n_grains": N_GRAINS,
        "g": float(parent.get("g", 0.0)),
    }


def emit(nums, t=1.0):
    """A Fibonacci shell at the derived extent. The DISTRIBUTION is a placeholder; the SIZE is not.

    `fibonacci_sphere` is the tree's own even-coverage helper and `surface_grain` sets the splat
    size from the count so the shell tiles rather than speckles -- the same law every real
    membrane's emit uses. What is missing is any reason for the shape to be a shell.
    """
    n = int(nums.get("n_grains", N_GRAINS))
    b = M.blank(n)
    b[:, 0:3] = M.fibonacci_sphere(n, jitter=0.15, seed=7)
    return M.paint(b, RGB, 0.9, M.surface_grain(n, 1.0))
