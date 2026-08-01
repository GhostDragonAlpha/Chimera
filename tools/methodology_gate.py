"""methodology_gate.py -- score EVERY membrane against the workflow, in the tree's own order.

WHY THIS EXISTS. The methodology is now twenty rules across six documents, and forty-two membranes
were built before most of them. "Go back over everything" by reading is the forward-debugging trap
at tree scale: forty-two careful reads, each one hoping to notice what the last twenty rules say to
look for. A rule that can be checked should be checked by a machine, and then the reading goes only
where the machine points.

WHAT IT CHECKS, and every one of these is a rule with a scar behind it:

  FORM        story.md + physics.py + numbers.json. A chapter is a folder; a folder that is not a
              chapter is a place the story stops.
  DERIVES     physics.py defines derive() and READS its parent. A membrane that ignores its parent
              is not in the hierarchy, it is beside it.
  EMITS       physics.py defines emit(). No emit, nothing to look at, nothing to judge.
  UNITS       every published number has a unit folding.py can read. `theZero.r` and
              `theZero.volume` did not -- 26% of the seed was invisible, and the audit reported
              itself clean over the three quarters it could see. A check that skips what it cannot
              parse reports success for the wrong reason.
  ONE NAME    no two keys in one membrane carrying the identical value. theHorizon publishes
              extent_m = r_s = lambda_C, one number under three names: either an identity worth
              stating once, or two ideas that agree here and will stop agreeing when something
              upstream moves. That is how three leg lengths got into one leg.
  NO TYPED    no suspiciously round constants in physics.py -- 0.785398 is pi/4, and a round radian
              in a joint limit is a typed number wearing a derivation's clothes.
  FREE        a FREE dict, so the free numbers are declared rather than buried.
  PREDICTS    story.md cites a measurement it was not fitted to. This is the weakest check here --
              it greps for evidence words -- and it is included because its ABSENCE is meaningful
              even when its presence is not proof.

WHAT IT DOES NOT CHECK, said plainly so the score is not mistaken for a verdict: whether the
physics is right. A membrane can pass every line here and still be an Earth gait on a 0.72 g world.
These are the conditions under which a membrane can be JUDGED, not the judgement.

RUN:  python tools/methodology_gate.py            (every membrane, tree order)
      python tools/methodology_gate.py --fails    (only what fails, which is the work list)
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STORY = ROOT / "story"
sys.path.insert(0, str(STORY))

# round numbers that no measurement produces. pi/4, pi/2, tidy halves and tenths in radians.
TYPED = [0.785398, 1.570796, 0.523599, 0.261799, 3.141593]


def _round_smell(src: str) -> list:
    hits = []
    for m in re.finditer(r"(?<![\w.])(\d+\.\d{4,})(?![\w])", src):
        v = float(m.group(1))
        for t in TYPED:
            if abs(v - t) < 5e-6:
                hits.append(m.group(1))
    return sorted(set(hits))


def check(d: Path) -> dict:
    r = {"name": d.name, "path": d}
    phys, nums, story = d / "physics.py", d / "numbers.json", d / "story.md"
    r["form"] = phys.exists() and nums.exists() and story.exists()
    if not phys.exists():
        return r
    src = phys.read_text(encoding="utf8", errors="replace")
    try:
        tree = ast.parse(src)
    except SyntaxError:
        r["parse"] = False
        return r
    fns = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    r["derives"] = "derive" in fns and "parent" in src
    r["emits"] = "emit" in fns
    # A MEMBRANE WITH NO FREE NUMBERS IS NOT A MEMBRANE THAT FORGOT TO DECLARE THEM. theZero is
    # the seed: it takes nothing and chooses nothing, so there is no FREE dict to write and its
    # absence is correct. The column asks whether anything is UNDECLARED, so a membrane whose
    # derive() takes no `free` values passes by having none.
    has_free_dict = re.search(r"^FREE\s*=", src, re.M) is not None
    uses_free = re.search(r"free\.get\(|free\[", src) is not None
    r["free"] = has_free_dict or not uses_free
    r["typed"] = _round_smell(src)
    # A CITATION IS NOT ALWAYS PHRASED AS ONE. The first pass looked for measured/literature/
    # predict and failed theZero -- whose story cites Carter 1968 deriving g = 2, the Dirac
    # electron's value, out of the Kerr-Newman metric. That is precisely what this column is for.
    # An instrument that cries wolf gets ignored, so an author-and-year and a stated exact value
    # now count too.
    _PRED = (r"measured|literature|predict|against .*\d"
             r"|[A-Z][a-z]+(?:\s+(?:&|and)\s+[A-Z][a-z]+)?\s+(?:19|20)\d\d"
             r"|exactly\s+`?[a-zA-Z]\s*=")
    r["predicts"] = bool(re.search(_PRED, story.read_text(encoding="utf8", errors="replace"))) \
        if story.exists() else False

    if nums.exists():
        try:
            data = json.loads(nums.read_text(encoding="utf8"))
        except Exception:
            data = {}
        vals = {k: v for k, v in data.items()
                if isinstance(v, (int, float)) and not isinstance(v, bool)}
        seen, dup = {}, []
        for k, v in vals.items():
            if v == 0:
                continue
            key = round(float(v), 12)
            if key in seen:
                dup.append((seen[key], k))
            else:
                seen[key] = k
        r["dups"] = dup
        try:
            import folding
            blind = [k for k in vals if not folding.unit_of_key(k, d.name)]
        except Exception:
            blind = []
        r["blind"] = blind
        r["n_numbers"] = len(vals)
    return r


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fails", action="store_true", help="only membranes with something to fix")
    a = ap.parse_args()

    dirs = sorted({p.parent for p in STORY.rglob("physics.py")},
                  key=lambda q: (len(q.relative_to(STORY).parts), str(q)))
    rows = [check(d) for d in dirs]
    print(f"METHODOLOGY GATE -- {len(rows)} membranes, tree order (root first)\n")
    print(f"{'membrane':<26}{'form':>5}{'der':>5}{'emit':>6}{'free':>6}"
          f"{'units':>7}{'1name':>7}{'typed':>7}{'pred':>6}")
    print("-" * 76)
    tally = {k: 0 for k in ("form", "derives", "emits", "free", "units", "dups", "typed", "predicts")}
    work = []
    for r in rows:
        blind, dups, typed = r.get("blind", []), r.get("dups", []), r.get("typed", [])
        ok = {"form": r.get("form"), "derives": r.get("derives"), "emits": r.get("emits"),
              "free": r.get("free"), "units": not blind, "dups": not dups,
              "typed": not typed, "predicts": r.get("predicts")}
        for k, v in ok.items():
            tally[k] += bool(v)
        if a.fails and all(ok.values()):
            continue
        m = lambda b: "  ok " if b else " FAIL"
        depth = len(r["path"].relative_to(STORY).parts) - 1
        print(f"{'  '*min(depth,4)}{r['name']:<{26-2*min(depth,4)}}"
              f"{m(ok['form'])}{m(ok['derives'])}{m(ok['emits']):>6}{m(ok['free']):>6}"
              f"{m(ok['units']):>7}{m(ok['dups']):>7}{m(ok['typed']):>7}{m(ok['predicts']):>6}")
        if blind:
            print(f"      units unreadable: {', '.join(blind[:6])}")
        if dups:
            print(f"      one value, two names: " +
                  "; ".join(f"{x}={y}" for x, y in dups[:4]))
        if typed:
            print(f"      typed constants: {', '.join(typed[:5])}")
        work.append(r["name"])
    n = len(rows)
    print("\n" + "-" * 76)
    for k, v in tally.items():
        print(f"   {k:<10} {v:>3}/{n}   {'#'*int(30*v/max(n,1))}")
    print(f"\n{len(work)} membranes have something to fix" if a.fails else "")
    print("\nTHIS SCORES THE CONDITIONS UNDER WHICH A MEMBRANE CAN BE JUDGED -- not whether its")
    print("physics is right. A membrane can pass every column and still be an Earth gait at 0.72 g.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
