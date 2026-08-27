"""theStance -- the inverted-pendulum standing clock, not a splat membrane.

This membrane publishes the standing physics that downstream ports derive
against. It has no emit(): it is a law about balance, not a drawable scene.
"""
from __future__ import annotations

import json
from pathlib import Path

_HERE = Path(__file__).resolve().parent
NUMBERS_PATH = _HERE / "numbers.json"


def derive(parent_nums=None, free=None):
    """Derived size and clock from the published stance ledger.

    extent_m: the standing body's vertical reach is its centre-of-mass height.
    duration_s: the inverted-pendulum time_to_fall_s is the stance's own clock.
    ground_friction_mu: the contact ledger must publish the floor's own friction --
    read from the loaded body model (geom_friction), the same measurement
    tools/action_tests.py's PUSH/PULL refusals reason against. It lives in the
    MJCF, not in any hand ledger, so it is measured here at derive time.
    """
    nums = json.loads(NUMBERS_PATH.read_text(encoding="utf8"))
    nums["extent_m"] = float(nums["com_height_m"])
    nums["duration_s"] = float(nums["time_to_fall_s"])
    import sys
    root = NUMBERS_PATH.resolve().parents[2]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    import mujoco
    from tools.world import load_body                 # noqa: E402 -- path set above
    sys.path.insert(0, str(root / "tools"))           # port_registry lives beside world.py
    from port_registry import MYOBODY                 # noqa: E402
    m, _g = load_body(MYOBODY, mujoco)
    nums["ground_friction_mu"] = float(m.geom_friction[0][0])
    return nums


def derive_commit():
    d = derive()
    NUMBERS_PATH.write_text(json.dumps(d, indent=1) + "\n", encoding="utf8")
    return d


if __name__ == "__main__":
    derive_commit()
