"""world.py -- load a body into THE WORLD IT LIVES IN, never MuJoCo's default.

FOUND BY THE PRE-FLIGHT, 2026-08-02, and it had been true since the body arrived.

`external/myo_sim/body/myobody.xml` declares no `<option gravity>`. MuJoCo therefore applies its
built-in default of **-9.81**, and not one of the eight places in this repo that build a myobody
model ever overrode it. Every training run, every gait evaluation and every render has simulated
this walker ON EARTH -- while the membranes underneath it derived `g = 7.076 m/s^2` and the
documentation argued about which target speed to ask for.

    THE TARGET BUG AND THE WORLD BUG ARE THE SAME BUG, AND THE WORLD ONE IS WORSE.
    Earth sim + Earth target was at least SELF-CONSISTENT. Earth sim + this-world target --
    which is what deriving the target alone produces -- is strictly worse than what it replaced.
    Half a fix here is a regression.

-9.81 is also not Earth. Standard gravity is 9.80665. The default was never a decision anybody
made; it is what you get when nobody decides.

WHY THIS IS ONE MODULE AND NOT EIGHT EDITS. `EXPERIMENTAL_METHOD.md`'s remake procedure: *a
systematic pattern is ONE decision, not N edits.* Eight call sites each setting gravity is eight
chances to drift, and rule 20 is explicit that an instrument must move with the membrane and keep
no private copy of it. So the world is read from the ledger, in one place, by everything.

    from world import load_body
    m, g = load_body(MYOBODY)     # g is this world's, and the model already has it

There is NO fallback. If the ledger cannot be read, this raises -- because a default here is
exactly the thing that produced the bug.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEDGER_MEMBRANE = "theHuman"


class WorldUnknown(RuntimeError):
    """The world will not say what its gravity is. There is no sensible default; that is the point."""


def gravity() -> float:
    """This world's g, in m/s^2, read from the membrane that owns the body."""
    hits = [p for p in (ROOT / "story").rglob("numbers.json")
            if p.parent.name == LEDGER_MEMBRANE]
    if not hits:
        raise WorldUnknown(
            f"no {LEDGER_MEMBRANE}/numbers.json under story/ -- run `python story/grow.py`. "
            f"Refusing to assume Earth.")
    led = json.loads(hits[0].read_text(encoding="utf8"))
    if "g" not in led:
        raise WorldUnknown(
            f"{LEDGER_MEMBRANE} publishes no `g`. The number belongs to the membrane; if it is "
            f"absent the membrane must derive it. Refusing to assume Earth.")
    g = float(led["g"])
    if not (g > 0.0):
        raise WorldUnknown(f"{LEDGER_MEMBRANE} publishes g={g!r}, which is not a gravity.")
    return g


def load_body(xml_path, mujoco=None):
    """Load an MJCF and put it in this world. Returns `(model, g)`.

    Prints what it changed, because a silent world change is how the original defect survived:
    nothing in the logs ever said which gravity a run had used, so nothing could contradict it.
    """
    if mujoco is None:
        import mujoco  # local import: this module is useful without it (see `gravity()`)
    g = gravity()
    m = mujoco.MjModel.from_xml_path(str(xml_path))
    before = float(m.opt.gravity[2])
    m.opt.gravity[2] = -g
    if abs(before + g) > 1e-9:
        print(f"[world] gravity {before:+.5f} -> {-g:+.6f} m/s^2  "
              f"({g / 9.80665:.4f} of Earth, from {LEDGER_MEMBRANE})")
    assert abs(float(m.opt.gravity[2]) + g) < 1e-12, "gravity did not take"
    return m, g


if __name__ == "__main__":
    print(f"this world's gravity: {gravity():.6f} m/s^2")
