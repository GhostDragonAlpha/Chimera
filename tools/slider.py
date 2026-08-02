"""slider.py -- move a free number at the top of the world and see what fails to move.

THE PROJECT'S OWN TEST, MADE RUNNABLE. CLAUDE.md states it plainly: *move a free number at the top
and every consequence must move; whatever does not move is typed.* It was written after a render
minted a moon that no membrane had derived, and after `thePlanets` typed `T_star_surface = 5772.0`
under a comment claiming the value was carried from the system -- so changing the star's mass moved
the snow line and left the sunlight the same colour forever.

Nothing had ever run it across the whole tree.

HOW IT WORKS. Grow the story twice: once with every free number at its default, once with ONE dial
moved. Then compare every published number in all 42 membranes.

    MOVED      the number is downstream of the dial. This is what a derivation looks like.
    UNMOVED    the number is independent of it -- which is either correct or a defect, and the
               difference is the whole point of reading the output rather than counting it.

WHAT AN HONEST UNMOVED NUMBER LOOKS LIKE. Constants of nature (`l_P`, the Planck mass) must not
move -- they are true in an empty universe. Measured anthropometry must not move: ANSUR II's
thigh fraction is a fact about 4,082 people and does not care what mass fell into the seed.
A membrane on a different BRANCH must not move either: nothing about the star's mass reaches the
Planck-scale clocks that ran before it existed.

WHAT A DISHONEST ONE LOOKS LIKE. A number that SHOULD depend on the dial and does not, sitting in
a membrane whose ancestors all moved. That is a typed constant wearing a derivation's clothes, and
it is invisible to every other check in this repo -- folding sees its unit is fine, the gate sees
it has a name and a value, the witness sees the membrane emits. Only moving the world finds it.

    python tools/slider.py                      # move theHorizon's M_added, report the tree
    python tools/slider.py --dial theStar:M_frac --factor 1.5
    python tools/slider.py --unmoved-below aBlueWorld   # only the subtree that should have moved
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

STORY = Path(__file__).resolve().parent.parent / "story"
sys.path.insert(0, str(STORY))


def _load(d: Path):
    sp = importlib.util.spec_from_file_location("_sl_" + d.name, str(d / "physics.py"))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def grow(dial_membrane=None, dial_key=None, factor=1.0):
    """Derive the whole tree, optionally with one free number multiplied. Returns {path: numbers}."""
    out = {}

    def walk(d: Path, parent):
        try:
            m = _load(d)
        except Exception as e:
            out[str(d.relative_to(STORY))] = {"_error": repr(e)}
            return
        free = {}
        if d.name == dial_membrane and dial_key:
            FREE = getattr(m, "FREE", {}) or {}
            spec = FREE.get(dial_key, {})
            base = spec.get("default")
            if base is None:
                try:
                    base = float(m.derive(parent, {}).get(dial_key, 1.0))
                except Exception:
                    base = 1.0
            lo, hi = spec.get("lo", -1e300), spec.get("hi", 1e300)
            free[dial_key] = min(max(float(base) * factor, lo), hi)
        try:
            nums = m.derive(parent, free)
        except Exception as e:
            out[str(d.relative_to(STORY))] = {"_error": repr(e)}
            return
        out[str(d.relative_to(STORY))] = nums
        for child in sorted(p for p in d.iterdir() if (p / "physics.py").exists()):
            walk(child, nums)

    walk(STORY / "theZero", None)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dial", default="theHorizon:M_added",
                    help="membrane:free_key to move (default: the mass added to the seed)")
    ap.add_argument("--factor", type=float, default=3.0)
    ap.add_argument("--unmoved-below", default=None,
                    help="only report membranes at or below this one -- the subtree that SHOULD move")
    ap.add_argument("--rel", type=float, default=1e-12, help="relative change counted as movement")
    a = ap.parse_args()
    mem, key = a.dial.split(":", 1)

    base = grow()
    moved = grow(mem, key, a.factor)
    print(f"SLIDER: {mem}.{key} x{a.factor}\n")

    rows = []
    for path in sorted(base):
        b, v = base[path], moved.get(path, {})
        if "_error" in b or "_error" in v:
            rows.append((path, -1, -1, b.get("_error") or v.get("_error")))
            continue
        keys = [k for k, x in b.items()
                if isinstance(x, (int, float)) and not isinstance(x, bool)
                and k not in ("timeline_serial", "t_since_seed_s")]
        mv = 0
        still = []
        for k in keys:
            x, y = float(b[k]), float(v.get(k, b[k]))
            if abs(y - x) > a.rel * max(abs(x), abs(y), 1e-300):
                mv += 1
            else:
                still.append(k)
        rows.append((path, mv, len(keys), still))

    sub = a.unmoved_below
    hit = False
    for path, mv, tot, extra in rows:
        name = path.split("\\")[-1].split("/")[-1]
        if sub:
            if name == sub:
                hit = True
            if not hit:
                continue
        if mv < 0:
            print(f"  {name:24} ERROR {extra}")
            continue
        depth = len(Path(path).parts) - 1
        bar = "#" * int(20 * mv / max(tot, 1))
        flag = "" if mv else "   <-- NOTHING MOVED"
        print(f"{'  ' * min(depth, 5)}{name:<{26 - 2 * min(depth, 5)}}"
              f"{mv:>3}/{tot:<3} moved {bar:<20}{flag}")
        if mv and extra and len(extra) <= 8:
            print(f"{'  ' * min(depth, 5)}      still: {', '.join(extra)}")
    print("\nA number that does not move is not automatically wrong: constants of nature, measured")
    print("anthropometry and membranes on other branches all SHOULD sit still. What is wrong is a")
    print("number that should be downstream of the dial and is not -- read, do not count.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
