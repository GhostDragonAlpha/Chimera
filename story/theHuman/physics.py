"""theHuman -- the MuJoCo dynamics body, not a splat membrane.

This membrane publishes the measured body and gait ledger that downstream
ports (stand, step, walk) derive against. It has no emit(): it does not draw
matter in the Gaussian viewer; it is a body law, not a scene.
"""
from __future__ import annotations

import json
from pathlib import Path

_HERE = Path(__file__).resolve().parent
NUMBERS_PATH = _HERE / "numbers.json"


def derive(parent_nums=None, free=None):
    """Derived size and clock from the published body ledger.

    extent_m: the body's vertical stature (height_m) is its natural size.
    duration_s: one full stride is two steps; step_time_s is one step.
    """
    nums = json.loads(NUMBERS_PATH.read_text(encoding="utf8"))
    nums["extent_m"] = float(nums["height_m"])
    nums["duration_s"] = 2.0 * float(nums["step_time_s"])
    return nums


def derive_commit():
    d = derive()
    NUMBERS_PATH.write_text(json.dumps(d, indent=1) + "\n", encoding="utf8")
    return d


if __name__ == "__main__":
    derive_commit()
