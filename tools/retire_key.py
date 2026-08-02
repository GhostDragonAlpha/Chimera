"""retire_key.py -- remove a published key from a membrane's derive(), using the AST, not a regex.

WHY THIS FILE EXISTS. Retiring a duplicate key from a physics.py was attempted three times with
regular expressions and broke the tree three different ways:

  1. A WHOLE-LINE MATCH ate a sibling. aBlueWorld writes `"R": R, "M": M,` on one line, so
     retiring R silently deleted M, and theInterior died on KeyError('M') eight membranes
     downstream -- while chain_witness reported 42 working, because it was reading the last good
     numbers.json on disk.
  2. A BACKREFERENCE IN THE REPLACEMENT wrote U+0001 into four files and every one stopped parsing.
  3. A FRAGMENT MATCH broke a multi-LINE value: `"day_s": float(parent.get("day_s",` and `86400.0)),`
     are one key spanning two lines, and removing the first left the second orphaned.

Three attempts, three distinct failure modes, one cause: **a regex sees text and a key-value pair
is a TREE**. Its extent has nothing to do with line breaks, and Python source is not a line-oriented
format. So this walks the AST, asks the key-value node where it BEGINS and ENDS, and splices exactly
that span out of the source text -- which keeps every comment, every blank line and every other key
untouched, because nothing else is touched.

    python tools/retire_key.py <membrane> <key> [--note "..."] [--dry]
    python tools/retire_key.py --all-dups        (every extent_m/duration_s twin in the tree)
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

STORY = Path(__file__).resolve().parent.parent / "story"


def _find_membrane(name: str):
    hits = [p.parent for p in STORY.rglob("physics.py") if p.parent.name == name]
    return hits[0] if hits else None


def retire(path: Path, key: str, note: str, dry=False):
    """Splice one key out of every dict literal in the file. Returns True if anything moved."""
    src = path.read_text(encoding="utf8")
    tree = ast.parse(src)
    lines = src.splitlines(keepends=True)

    def offset(lineno, col):
        return sum(len(l) for l in lines[:lineno - 1]) + col

    cuts = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        for i, k in enumerate(node.keys):
            if not (isinstance(k, ast.Constant) and k.value == key):
                continue
            v = node.values[i]
            a = offset(k.lineno, k.col_offset)
            b = offset(v.end_lineno, v.end_col_offset)
            # take the trailing comma and the newline with it, so no orphan punctuation is left
            while b < len(src) and src[b] in ", ":
                b += 1
            if b < len(src) and src[b] == "\n":
                b += 1
            # and the indentation that led up to it, if the key started its own line
            ls = src.rfind("\n", 0, a) + 1
            lead = src[ls:a]
            if lead.strip() == "":
                a = ls
                cuts.append((a, b, lead))
            else:
                cuts.append((a, b, None))
    if not cuts:
        return False
    for a, b, lead in sorted(cuts, reverse=True):
        rep = f"{lead}# `{key}` RETIRED: {note}\n" if lead is not None else ""
        src = src[:a] + rep + src[b:]
    ast.parse(src)          # REFUSE TO WRITE SOMETHING THAT DOES NOT PARSE
    if not dry:
        path.write_text(src, encoding="utf8")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("membrane", nargs="?")
    ap.add_argument("key", nargs="?")
    ap.add_argument("--note", default="the contract name above is the same number.")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--all-dups", action="store_true",
                    help="retire every key whose value equals this membrane's extent_m or duration_s")
    a = ap.parse_args()

    # ONLY GENUINE RESTATEMENTS BELONG HERE, and the first version of this list got it wrong.
    # `day_s`, `year_s` and `height_m` were in it because they hold the same NUMBER as duration_s
    # or extent_m -- and they are not the same QUANTITY. duration_s is how long this membrane's
    # movie runs; day_s is the length of a day. They coincide because the membrane chose to show
    # exactly one day, and showing two would double one and not the other. height_m is a person's
    # stature, extent_m is the membrane's extent. Thirty-five consumers read those three, so
    # retiring them would have destroyed real meaning across the tree to satisfy a column.
    #
    # The slider test separates them in one run: an IDENTITY survives moving a free number, a
    # COINCIDENCE comes apart. R and r_s survive -- they are extent_m computed a second time.
    TWINS = {"extent_m": ("R", "r_s"), "duration_s": ("t_P", "t_evap")}
    NOTE = ("{c} above is the same number under the contract name every child and the composer "
            "already read. One quantity, one name.")

    if a.all_dups:
        done = []
        for phys in STORY.rglob("physics.py"):
            nums = phys.parent / "numbers.json"
            if not nums.exists():
                continue
            d = json.loads(nums.read_text(encoding="utf8"))
            for contract, twins in TWINS.items():
                base = d.get(contract)
                if not isinstance(base, (int, float)) or base == 0:
                    continue
                for t in twins:
                    if d.get(t) == base and retire(phys, t, NOTE.format(c=contract), a.dry):
                        done.append(f"{phys.parent.name}.{t}")
        print(f"{'would retire' if a.dry else 'retired'} {len(done)}")
        for x in done:
            print("   ", x)
        return 0

    d = _find_membrane(a.membrane)
    if d is None:
        print(f"no membrane {a.membrane!r}")
        return 1
    ok = retire(d / "physics.py", a.key, a.note, a.dry)
    print(("would retire " if a.dry else "retired ") + f"{a.membrane}.{a.key}" if ok else "key not found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
