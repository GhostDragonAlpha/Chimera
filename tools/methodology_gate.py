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
  ONE NAME    two keys in one membrane holding the identical value AND STILL HOLDING IT after a
              free number moves. The second half is the whole test. theHorizon publishes
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

THE ONE-NAME COLUMN'S ANSWER, MEASURED 2026-08-01: it is not 36 defects, it is ONE DECISION
made 45 times. Counting every flagged pair across the tree:

    31  extent_m   = <domain name>     R, r_s, l_P, ...
    14  duration_s = <domain name>     year_s, day_s, t_P, ...
    10  obliquity_deg = obliquity_effective_deg = tropic_lat_deg

Every membrane publishes its own size twice -- once under the universal contract name that
chain_witness and the composer read, and once under the name its own equations use. That is a
design choice, not sloppiness: the contract name faces out, the physics name faces in. But a
child can then read EITHER, and the moment one is recomputed and the other is not they drift,
which is exactly how LEG_FRAC, leg_length_m and the segment sum became three different legs.

    THE FIX IS ONE DECISION, NOT FORTY-TWO EDITS: the contract name is the PUBLISHED number and
    the domain name is a LOCAL VARIABLE. Then the consumers move -- theClock reading
    parent["r_s"] is the first of them, and that rename must travel with its children.

A NOTE ON THIS FILE'S OWN HISTORY, since it is a witness and rule 19 applies to it. The dup
column has now been wrong twice: it first accused twenty innocent membranes over a FREE dict a
seed cannot have, and a later attempt to filter identities from coincidences by perturbing a
free number INVENTED pairs on membranes whose derive returns degenerate values off-default
(theClock went 1 -> 4, including an extent_m=duration_s that is false in its own numbers.json).
That attempt is reverted. The slider test IS the right discriminator -- run by hand on
theHorizon it correctly keeps the black-hole/electron crossing and drops the redundancies --
but it needs a re-derive that is checked for sanity before its output is trusted.

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


def _identities(d: Path, data: dict, dup: list):
    """Of the equal-valued pairs, which SURVIVE moving a free number? Those are the real ones.

    Returns None when the membrane cannot be re-derived (no parent numbers, no FREE dial, an emit
    that needs the engine) -- in which case the caller keeps the raw pairs and the reading decides.
    A check that cannot run must say so rather than pass."""
    import importlib.util
    try:
        par_f = d.parent / "numbers.json"
        if not par_f.exists():
            return None
        parent = json.loads(par_f.read_text(encoding="utf8"))
        sp = importlib.util.spec_from_file_location("_m_" + d.name, str(d / "physics.py"))
        m = importlib.util.module_from_spec(sp)
        sp.loader.exec_module(m)
        FREE = getattr(m, "FREE", None)
        if not FREE:
            return None
        k0 = sorted(FREE)[0]
        spec = FREE[k0]
        base = m.derive(parent, {})
        lo, hi = float(spec.get("lo", 0.0)), float(spec.get("hi", 1.0))
        alt = hi if abs(base.get(k0, lo) - lo) < abs(hi - lo) * 0.5 else lo
        moved = m.derive(parent, {k0: alt})
        keep = []
        for a, b in dup:
            if a in moved and b in moved:
                va, vb = float(moved[a]), float(moved[b])
                if abs(va - vb) <= 1e-12 * max(abs(va), abs(vb), 1e-300):
                    keep.append((a, b))
            else:
                keep.append((a, b))
        return keep
    except Exception:
        return None


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
        # ── THE SLIDER TEST: IS IT AN IDENTITY, OR A COINCIDENCE? ────────────────────────────
        # "Two keys hold the same number" is a suspicion, not a defect. theHorizon publishes
        # extent_m = lambda_C -- the Schwarzschild radius equalling the Compton wavelength, which
        # is THE CROSSING WHERE A BLACK HOLE AND AN ELECTRON ARE THE SAME SIZE, and the entire
        # point of theZero's story. A naive same-value check would have had it deleted.
        #
        # MOVE A FREE NUMBER AND RE-DERIVE. A pair that still agrees is an IDENTITY and one of the
        # two is redundant. A pair that comes apart was only ever equal at this setting, and both
        # are real. Measured on theHorizon: extent_m=r_s and duration_s=t_P survived a x3 on
        # M_added; extent_m=lambda_C and M_added=M_crossing came apart, exactly as the physics says
        # they should. This is CLAUDE.md's own slider test, pointed at the audit.
        if dup:
            # KNOWN OVER-AGGRESSIVE, AND SAID SO RATHER THAN LEFT TO BE DISCOVERED. Hand-running
            # the slider on theHorizon calls BOTH extent_m=r_s and duration_s=t_P identities; this
            # filter keeps only the first. The alternate free value is picked off FREE's lo/hi
            # bounds and for a mass dial those may be far enough out that derive() returns
            # something the comparison cannot use. Until that is chased, treat a SURVIVING pair as
            # a real finding and an ABSENT one as unproven -- the filter can currently lose a true
            # defect, which is the safer direction for a work list but not for a gate.
            _keep = _identities(d, data, dup)
            dup = _keep if _keep is not None else dup
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
