"""The INK membrane's falsifier judge: two blind_read runs, one table.

Usage: python tools/ink_ab.py <before_readings.json> <after_readings.json>

The membrane (docs/THE_RECORDED_SESSION_2.md, INK): the object beats (beat01..beat07) mean align
must rise from 0.22 to >= 0.50 after the density step, same eye, same prompts, same expected
terms. Below 0.35 the falsifier FIRES: splat count was not the binding constraint. Between 0.35
and 0.50 the membrane neither holds nor fires -- partial, and the residue is named, not hidden.
"""

from __future__ import annotations

import json
import sys

OBJECT_BEATS = ["beat01", "beat02", "beat03", "beat04", "beat05", "beat06", "beat07"]


def load(path: str) -> dict:
    return {r["item"]: r for r in json.load(open(path, encoding="utf8"))}


def main() -> int:
    before, after = load(sys.argv[1]), load(sys.argv[2])
    rows, deltas = [], []
    print(f"{'item':18s} {'before':>7s} {'after':>7s} {'delta':>7s}")
    for item in OBJECT_BEATS + ["beat00", "beat08", "beat09", "sheet_master"]:
        b = (before.get(item) or {}).get("align")
        a = (after.get(item) or {}).get("align")
        d = (a - b) if (a is not None and b is not None) else None
        if item in OBJECT_BEATS and d is not None:
            deltas.append(d)
        fmt = lambda v: "  None" if v is None else f"{v:6.2f}"
        print(f"{item:18s} {fmt(b)} {fmt(a)} {fmt(d)}")
    if not deltas:
        print("no comparable object beats")
        return 1
    mb = sum((before[i])["align"] for i in OBJECT_BEATS) / len(OBJECT_BEATS)
    ma = sum((after[i])["align"] for i in OBJECT_BEATS) / len(OBJECT_BEATS)
    print(f"\nobject-beat mean: {mb:.3f} -> {ma:.3f}")
    if ma >= 0.50:
        print("PREDICTION HOLDS (>= 0.50): density was the binding constraint.")
    elif ma < 0.35:
        print("FALSIFIER FIRES (< 0.35): splat count was NOT the binding constraint.")
    else:
        print("PARTIAL (0.35-0.50): density moved the needle but was not the whole gap.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
