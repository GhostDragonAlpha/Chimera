"""timeline.py -- every membrane's SERIAL is its place in time, not just its place in the tree.

THE OPERATOR'S CORRECTION, and it fixes something that had been costing order all day. A
membrane's address is its PATH, and a path encodes CONTAINMENT: what is inside what. The story,
though, is told in TIME -- theZero at the seed, theHorizon at the Planck tick, theCooling at
recombination, a footprint on a planet thirteen billion years later. Containment and chronology
agree all the way down the cosmological spine and then stop agreeing the moment the tree branches:
theStar and thePlanets are siblings in the tree and are not simultaneous, and nothing written down
anywhere said which came first.

    A HIERARCHY SAYS WHAT CONTAINS WHAT. A TIMELINE SAYS WHAT FOLLOWS WHAT.
    The fourth dimension is the second one, and it was never recorded.

THE EPOCH IS DERIVED, NOT DECLARED. Every membrane already publishes `duration_s` -- its own span,
the length of its own movie -- and those are real: theCooling's 1.199e13 s IS the 380,000 years to
recombination, theAtmosphere's 86,400 s IS one day. Summing them down the path from the seed gives
the time at which each membrane's own process COMPLETES, measured in the seed's own seconds:

    t_end(m) = t_end(parent) + duration_s(m)

Nothing is invented, nothing is chosen, and the ordering it produces is monotonic down every
branch by construction -- a child cannot finish before the parent it lives inside.

HONEST ABOUT WHAT IT IS NOT. This is a sum of PROCESS durations, not of the gaps between them, so
the total is far short of the universe's age -- the story does not yet publish the waiting. That
makes t_end an ORDERING, exact in sequence and approximate in absolute epoch, and it is labelled
so. When a membrane one day publishes the interval it waits before starting, this same sum becomes
the real clock without changing shape.

WHAT IT IS FOR, beyond order for its own sake:
  * a canonical WORK ORDER -- the sequence the story happens in is the sequence to build and audit
    in, and "start at the beginning" stops being ambiguous;
  * a SERIAL that is a number and not a folder path, so a membrane can be cited, sorted and
    compared without walking a directory;
  * the fourth dimension made explicit, so a scene knows not merely where it sits but when.

RUN:  python story/timeline.py              (the timeline, in order)
      python story/timeline.py --write      (publish t_since_seed_s + serial into numbers.json)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

STORY = Path(__file__).resolve().parent


def walk():
    """Every membrane with its parent chain, deepest-last, so a parent is always seen first."""
    out = []
    for f in STORY.rglob("numbers.json"):
        rel = f.parent.relative_to(STORY)
        out.append((len(rel.parts), rel, f))
    out.sort()
    return out


def timeline():
    """t_end for every membrane: the seed's own seconds at which its process completes."""
    t_end, rows = {}, []
    for depth, rel, f in walk():
        try:
            d = json.loads(f.read_text(encoding="utf8"))
        except Exception:
            continue
        dur = d.get("duration_s")
        dur = float(dur) if isinstance(dur, (int, float)) else 0.0
        parent = rel.parent
        base = t_end.get(str(parent), 0.0)
        t = base + dur
        t_end[str(rel)] = t
        rows.append({"name": rel.parts[-1], "rel": rel, "depth": depth,
                     "duration_s": dur, "t_end_s": t, "file": f})
    # THE SERIAL IS THE RANK IN TIME. Ties broken by depth then path, so it is deterministic --
    # two membranes that complete at the same instant still get a stable, reproducible order.
    rows.sort(key=lambda r: (r["t_end_s"], r["depth"], str(r["rel"])))
    for i, r in enumerate(rows):
        r["serial"] = i
    return rows


NOTE = ("sum of duration_s down the path from theZero: exact as an ORDERING, approximate as an "
        "absolute epoch, because the story publishes process spans and not yet the waiting "
        "between them")


def stamp(rows=None) -> int:
    """Publish the epoch into every numbers.json. Called by `--write` AND by grow.py's own tail.

    WHY grow.py CALLS THIS. `grow` rebuilds each numbers.json from `derive()`, which knows nothing
    about the timeline, so for a while every `python story/grow.py` silently STRIPPED these two keys
    off all 42 membranes -- and nothing complained. The numbers stayed right, chain_witness passed,
    the methodology gate scored 42/42, and the story's chapter order quietly lost its consumer.
    Two writers to one file, and the generator wins (`docs/THE_ORDER.md`'s one-writer rule).

    `indent=2` MATTERS: grow writes at indent 2, and this used to write at indent 1, so a re-stamp
    that changed no value still rewrote all 42 files and showed up as a diff. A formatting
    disagreement between two writers is a permanently dirty tree, which is how a real stray change
    becomes invisible.
    """
    rows = rows if rows is not None else timeline()
    for r in rows:
        d = json.loads(r["file"].read_text(encoding="utf8"))
        d["timeline_serial"] = r["serial"]
        d["t_since_seed_s"] = r["t_end_s"]
        d["t_since_seed_note"] = NOTE
        r["file"].write_text(json.dumps(d, indent=2), encoding="utf8")
    return len(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true",
                    help="publish t_since_seed_s and timeline_serial into each numbers.json")
    a = ap.parse_args()
    rows = timeline()

    print(f"THE TIMELINE -- {len(rows)} membranes, in the order the story happens\n")
    print(f"{'serial':>6}  {'t since seed (s)':>18}  {'own duration (s)':>18}  membrane")
    print("-" * 78)
    for r in rows:
        print(f"{r['serial']:>6}  {r['t_end_s']:>18.6g}  {r['duration_s']:>18.6g}  "
              f"{'  ' * (r['depth'] - 1)}{r['name']}")

    if a.write:
        n = stamp()
        print(f"\npublished timeline_serial + t_since_seed_s into {n} membranes")
    else:
        print("\n(--write to publish these into numbers.json)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
