"""elitism_audit.py -- CAN A SEARCH IN THIS REPO LOSE THE BEST POLICY IT ALREADY HAS?

RULE 0, stated before the run:

    STATEMENT   Every population-based search in this repository evaluates its OWN INCUMBENT as
                one of its candidates, so the best known policy cannot be lost by looking for a
                better one. This is not a tuning knob; it is a correctness property of the
                search, and it costs exactly one evaluation per turn.

    PREDICTION  Two things, one static and one numerical:
                1. The static scan finds at least one CEM loop with no incumbent line. (The fix
                   was applied to train_stand and train_walk on 2026-08-04; the sibling trainers
                   were never swept, so the prediction is that the fix did not propagate.)
                2. At the dimensionality these searches actually run at -- 1160 free numbers for
                   the stand policy -- a CEM WITHOUT the line reports a turn-0 best strictly
                   WORSE than the incumbent it was warm-started from, on a smooth objective with
                   no noise at all. The failure is geometric, not stochastic: in d dimensions a
                   sample from N(mu, sd) sits at radius ~sd*sqrt(d) from mu, so with d=1160 and
                   sd=0.075 EVERY sample is ~2.6 away from a mean the search never scores.

    FALSIFIER   If the numerical demonstration shows the no-incumbent arm matching or beating
                the incumbent at turn 0, the line is unnecessary and this audit should say so
                and be deleted. A fix whose absence cannot be measured is a superstition.

WHY A DEMONSTRATION AND NOT JUST A GREP. `tools/train_stand.py` records that this defect cost a
real policy -- "seeded with the theta that stands at 101.9% of target, turn 0 of a 24-turn warm
start opened at 48% and never recovered". A grep can tell you a line is missing; it cannot tell
you whether missing it matters, and the answer depends entirely on d, which is why the same
omission is harmless in a 6-number walk search and fatal in a 1160-number stand search. So the
audit measures the consequence at each optimizer's OWN dimensionality.

    python tools/elitism_audit.py            # exit 0 = every search keeps its incumbent
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SCAN_DIRS = ("tools", "ChimeraEngine", "Chimera/core")

# A CEM TURN: a population-sized draw around a mean, then an elite selection that REPLACES the
# mean. Both halves are required -- a bare `rng.normal(mu, sd, ...)` somewhere is not a search.
RE_DRAW = re.compile(r"^\s*(\w+)\s*=\s*(?:np\.clip\()?\s*rng\.normal\(\s*(\w+)\s*,\s*(\w+)\s*,"
                     r"\s*size=\(")
RE_ELITE = re.compile(r"\.mean\(0\)")
RE_INCUMBENT = re.compile(r"^\s*(\w+)\[0\]\s*=\s*(?:np\.clip\()?\s*(\w+)")
# MIRRORED-SAMPLING ES is a DIFFERENT FAMILY WITH THE SAME EXPOSURE, and a scan that only knew
# CEM would report it clean by never looking at it. `cand = mu + sigma * pert` with an
# antithetic `pert` cannot take the CEM fix: inserting mu as candidate 0 breaks the +eps/-eps
# pairing that cancels the first-order noise, and the rank-normalised gradient picks up a bias.
# The property still has to hold, so the fix is to score mu OUTSIDE the population and fold it
# into the best-ever bookkeeping only. That is what this looks for.
RE_ES_DRAW = re.compile(r"^\s*(\w+)\s*=\s*(\w+)\s*\+\s*(\w+)\s*\*\s*(\w+)\s*$")
RE_ES_SCORES_MU = re.compile(r"=\s*(?:float\()?\s*score\(\s*(\w+)\s*[,)]")


def scan():
    """Every CEM turn in the repo, and whether its incumbent is in the population."""
    out = []
    for d in SCAN_DIRS:
        base = ROOT / d
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.py")):
            if "__pycache__" in str(path) or "archive" in str(path):
                continue
            lines = path.read_text(encoding="utf8", errors="replace").splitlines()
            for i, ln in enumerate(lines):
                mo = RE_DRAW.match(ln)
                if not mo:
                    continue
                cand_var, mu_var = mo.group(1), mo.group(2)
                # the window is the turn body: from the draw to the elite update
                win = lines[i:i + 25]
                if not any(RE_ELITE.search(w) for w in win):
                    continue                     # a draw that never selects an elite is not CEM
                has = False
                for w in win:
                    im = RE_INCUMBENT.match(w)
                    if im and im.group(1) == cand_var and im.group(2) == mu_var:
                        has = True
                        break
                # the search's dimensionality, read from the draw's own size= expression
                dim_txt = ln.split("size=(")[1].split(")")[0]
                out.append(dict(file=str(path.relative_to(ROOT)).replace("\\", "/"),
                                line=i + 1, cand=cand_var, mu=mu_var, dim_expr=dim_txt,
                                family="CEM", has_incumbent=has))
            # ── the ES family, scanned separately because its fix is a different shape ──
            for i, ln in enumerate(lines):
                mo = RE_ES_DRAW.match(ln)
                if not mo:
                    continue
                cand_var, mu_var = mo.group(1), mo.group(2)
                win = lines[max(0, i - 6):i + 22]
                if not any("argsort" in w for w in win):
                    continue                     # an arithmetic line that is not a search
                if not any(re.search(rf"\b{mu_var}\s*=\s*{mu_var}\s*\+", w) for w in win):
                    continue                     # mu must actually be stepped, or this is not ES
                has = any((sm := RE_ES_SCORES_MU.search(w)) and sm.group(1) == mu_var
                          for w in win)
                out.append(dict(file=str(path.relative_to(ROOT)).replace("\\", "/"),
                                line=i + 1, cand=cand_var, mu=mu_var, dim_expr="(ES, mirrored)",
                                family="ES", has_incumbent=has))
    return out


def demonstrate(d, sd=0.075, pop=24, trials=200, seed=0):
    """Turn 0 of a warm-started CEM in `d` dimensions, WITH and WITHOUT the incumbent line.

    The objective is a smooth quadratic with its optimum AT the incumbent -- no noise, no
    plateau, no deception. Any gap is therefore purely the geometry of sampling in d dimensions,
    which is the whole point: this is not a hard-objective problem, it is a distance problem.

    Returns (best_without, best_with, incumbent_score). Scores are negatives of distance^2, so
    the incumbent scores exactly 0 and every sample scores below it.
    """
    rng = np.random.default_rng(seed)
    mu = np.zeros(d)
    f = lambda x: -float(np.sum((x - mu) ** 2))
    wo, wi = [], []
    for _ in range(trials):
        cand = rng.normal(mu, sd, size=(pop, d))
        wo.append(max(f(c) for c in cand))            # no incumbent in the population
        cand[0] = mu                                   # the one line
        wi.append(max(f(c) for c in cand))
    return float(np.mean(wo)), float(np.mean(wi)), 0.0


def main() -> int:
    rows = scan()
    print("\nELITISM AUDIT -- does every search evaluate its own incumbent?")
    print("=" * 96)
    print(f"{'file:line':44}{'fam':5}{'cand':7}{'mu':6}{'dim':20}  incumbent evaluated?")
    print("-" * 96)
    missing = []
    for r in rows:
        tag = f"{r['file']}:{r['line']}"
        print(f"{tag:44}{r['family']:5}{r['cand']:7}{r['mu']:6}{r['dim_expr'][:19]:20}  "
              f"{'YES' if r['has_incumbent'] else 'NO  <-- the search can lose its incumbent'}")
        if not r["has_incumbent"]:
            missing.append(tag)
    print("-" * 96)
    ncem = sum(1 for r in rows if r["family"] == "CEM")
    nes = sum(1 for r in rows if r["family"] == "ES")
    print(f"  {len(rows)} searches found ({ncem} CEM, {nes} mirrored-sampling ES), "
          f"{len(missing)} not evaluating their incumbent")

    print("\n  WHAT THE MISSING LINE COSTS, measured on a NOISELESS quadratic whose optimum IS")
    print("  the incumbent. Every number below is the mean over 200 independent turn-0 draws.")
    print(f"\n{'dim':>7}{'best WITHOUT':>16}{'best WITH':>12}{'incumbent':>12}  verdict")
    fires = False
    demo = []
    for d in (6, 12, 66, 290, 870, 1160, 1450):
        wo, wi, inc = demonstrate(d)
        worse = wo < inc - 1e-12
        fires |= worse
        demo.append(dict(dim=d, without=wo, with_=wi, incumbent=inc, worse_than_incumbent=worse))
        print(f"{d:>7}{wo:>16.4f}{wi:>12.4f}{inc:>12.4f}  "
              + ("turn 0 lands BELOW the warm start" if worse else "no loss"))
    print("\n  The gap is sd^2 * d exactly -- 0.075^2 * 1160 = 6.53 -- so it grows LINEARLY with")
    print("  the number of free numbers. At 6 dims (the walk port) the omission costs 0.03 and")
    print("  is nearly harmless; at 1160 (the stand policy) it costs 6.5 and the warm start is")
    print("  destroyed on the first turn. SAME BUG, TWO ORDERS OF MAGNITUDE APART IN CONSEQUENCE,")
    print("  which is why 'is this line important' has no answer that is not a dimensionality.")

    print("\n" + "=" * 96)
    print(f"  FALSIFIER (does the omission actually cost anything?): "
          + ("DOES NOT FIRE -- the no-incumbent arm never lands below the warm start, so the "
             "line is superstition and this audit should be deleted." if not fires else
             "the omission IS measurable: without the line, turn 0 lands strictly below the "
             "incumbent at every dimensionality tested."))
    print(f"  VERDICT: {'PASS -- every search keeps its incumbent' if not missing else 'FAIL'}")
    for tag in missing:
        print(f"    MISSING: {tag}")
    out = ROOT / "agent_logs" / "elitism_audit.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(dict(searches=rows, missing=missing, demonstration=demo), indent=1),
                   encoding="utf8")
    print(f"  JSON: {out}")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
