"""parse_physics_catalog.py -- turn the physics markdown into something a membrane can bind to.

THE PROBLEM. `research_references/PHYSICS_OF_EVERYTHING.md` holds 120 sourced rows of physics and
`PHYSICS_OF_THE_HUMAN.md` holds 45 more. They are good rows -- real equations, named sources. But
NOTHING READS THEM. Measured: zero Python files parse or import any of the catalogs, there is no
machine-readable index, and `MEMBRANE_PHYSICS_MAP.md` resolves membranes against fourteen SECTIONS
rather than the individual rows -- so the project's own ruling that "a membrane ignoring a governing
row is incomplete by construction" is checked at eight times too coarse a grain, by prose, by hand.

A bibliography is not a system. This makes the index.

WHAT IS PARSED AND WHAT IS NOT -- the line matters. This reads the TABLE STRUCTURE: the branch, the
name, the equation as written, the source as written, the stated relevance. That is reading, not
inference. It does NOT try to extract a law's variables or units out of the equation text, because
that would be a guessing machine, and the whole point of the catalog is that nothing in it is a
guess. Signatures are DECLARED (see story/folding.py) and this file reports how many rows still
lack one, so the gap is a number rather than an impression.

IDS. `E<section>.<row>` for the everything-tree, `H<section>.<row>` for the human tree -- matching
the `E§n` / `H§n` notation MEMBRANE_PHYSICS_MAP.md already uses, so the existing prose map and the
new index refer to the same things.

RUN:  python tools/parse_physics_catalog.py
      python tools/parse_physics_catalog.py --check     (re-derive and diff, write nothing)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "story" / "data" / "physics_catalog.json"

SOURCES = [
    ("E", ROOT / "research_references" / "PHYSICS_OF_EVERYTHING.md",
     "humanity's physics tree, minus the forbidden branches"),
    ("H", ROOT / "research_references" / "human" / "PHYSICS_OF_THE_HUMAN.md",
     "the human body's own physics"),
    # THE MATHEMATICS, and it was never indexed at all. 97 rows across 12 sections -- the
    # simulator's-eye view: what every physics engine, renderer and solver actually computes.
    # `MEMBRANE_PHYSICS_MAP.md` already cites it as `S§n`, so the prefix matches what the prose
    # map has been pointing at all along.
    ("S", ROOT / "research_references" / "PHYSICS_SOFTWARE_MATH.md",
     "the math every simulator encompasses -- equations are facts, code is not"),
]

# Sections that are prose rather than catalogue -- they carry no rows to bind.
SKIP_SECTIONS = ("THE FORBIDDEN", "HOW THIS TREE", "WHAT THIS", "THE PROOF", "NOTES")


def _cells(line: str) -> list:
    """Split a markdown table row into its cells."""
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


# THE TWO CATALOGS DO NOT SHARE A COLUMN LAYOUT, and assuming they did produced rows whose `name`
# was "1.1" -- a section number sitting where a law's name belongs. So the header row is READ and
# the columns mapped by what they call themselves. That also means a column added later is picked
# up rather than silently shifting everything one to the left.
COLUMN_ALIASES = {
    "physics": "name", "law / equation": "equation", "law/equation": "equation",
    "concept": "name", "the math": "equation", "chimera consumer": "relevance",
    "canonical source": "source",
    "equation": "equation", "official source": "source", "source": "source",
    "chimera relevance": "relevance", "relevance": "relevance",
    "membrane": "membrane", "status": "status", "proof": "proof",
    "measured data (repo)": "data", "measured data": "data", "#": "n",
}


def parse(prefix: str, path: Path) -> list:
    if not path.exists():
        return []
    rows, section, sec_n, row_n = [], None, 0, 0
    cols = None
    for raw in path.read_text(encoding="utf8", errors="replace").splitlines():
        line = raw.rstrip()
        m = re.match(r"^##\s+(?:(\d+)\.\s*)?(.+)$", line)
        if m:
            num, title = m.group(1), m.group(2).strip()
            if any(title.upper().startswith(s) for s in SKIP_SECTIONS):
                section = None
                continue
            sec_n = int(num) if num else sec_n + 1
            section, row_n, cols = title, 0, None
            continue
        if not line.startswith("|") or section is None:
            continue
        c = _cells(line)
        if len(c) < 3 or set("".join(c)) <= set("-: "):
            continue
        if cols is None:                            # the first table row names the columns
            cols = [COLUMN_ALIASES.get(x.strip().lower()) for x in c]
            continue
        row_n += 1
        rec = {"id": f"{prefix}{sec_n}.{row_n:02d}", "branch": section,
               "name": "", "equation": "", "source": "", "relevance": ""}
        for key, val in zip(cols, c):
            if key and key != "n":
                rec[key] = val
        # `#` columns carry the catalog's own numbering (e.g. "1.1") -- keep it as an alias so a
        # reader coming from the markdown can find the row it is looking at.
        if "n" in (cols or []):
            rec["catalog_ref"] = c[cols.index("n")]
        # DECLARED LATER, NEVER INFERRED. Null here is honest: it says "nobody has stated what
        # this law consumes and produces yet", which is a fact, unlike a parsed guess.
        rec["signature"] = None
        rows.append(rec)
    return rows


def build() -> dict:
    out = {
        "what": ("the physics catalogs as an index a membrane can bind against. Rows are READ from "
                 "the markdown; signatures are declared in story/folding.py, never inferred."),
        "catalogs": [],
        "rows": [],
    }
    for prefix, path, what in SOURCES:
        rows = parse(prefix, path)
        out["catalogs"].append({"prefix": prefix, "file": str(path.relative_to(ROOT)),
                                "what": what, "rows": len(rows)})
        out["rows"].extend(rows)
        print(f"  {path.name}: {len(rows)} rows as {prefix}*")
    # a branch index, so "which rows are in classical mechanics" is one lookup
    br = {}
    for r in out["rows"]:
        br.setdefault(r["branch"], []).append(r["id"])
    out["branches"] = br
    out["n_rows"] = len(out["rows"])
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="re-derive and diff, writing nothing")
    a = ap.parse_args()

    print("parsing the physics catalogs")
    data = build()
    blob = json.dumps(data, ensure_ascii=False, indent=1)
    print(f"  {data['n_rows']} rows across {len(data['branches'])} branches")

    if a.check:
        if not OUT.exists():
            print("  nothing committed to check against")
            return 1
        same = OUT.read_text(encoding="utf8") == blob
        print(f"  {'MATCHES' if same else 'DIFFERS FROM'} {OUT.relative_to(ROOT)}")
        return 0 if same else 2

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(blob, encoding="utf8")
    print(f"  wrote {OUT.relative_to(ROOT)} ({len(blob):,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
