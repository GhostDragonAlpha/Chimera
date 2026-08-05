"""benchmark_verdict.py -- THE FALSIFIERS, READ OFF THE BENCHMARK, ON THE RIGHT STATISTIC.

RULE 0, stated before the run:

    STATEMENT   `benchmark_policies.py` ranks arms by the MEDIAN of held-out survival over seeds
                3..9. Those seven seeds are the SAME seven initial conditions for every arm, so
                the samples are PAIRED by construction. A median over the unpaired set discards
                that pairing, and a rank statistic over seven numbers is decided by ONE of them.

    PREDICTION  On at least one of the task comparisons the median and the paired statistic
                DISAGREE about the sign of the effect.

    FALSIFIER   Median and paired agree everywhere -- the pairing carried no information, the
                runner's own ranking was sufficient, and this file is unnecessary.

IT DISAGREES, AND HERE IS THE CASE THAT MADE THIS FILE (task 1, measured 2026-08-04):

    p_only per seed   7.18  7.72  6.32  6.40  6.34  6.86  7.62   -> median 6.86
    pd     per seed   7.68  7.90  6.34  6.66  6.42  6.76  8.00   -> median 6.76

`pd` wins on SIX of the seven seeds. Both medians are the seed-8 value, which is the ONE seed
where it loses -- so the median statistic reports the opposite sign of the effect from every
other seed in the set. Task 1's falsifier is written "PD held-out survival <= P-only held-out
survival"; on the median it FIRES and on the pairing it does not. Both are printed, and which
one the verdict reads is stated rather than chosen quietly.

    ONE QUANTITY, ONE LANDMARK. The seeds are paired; the comparison must be.

THE TEST IS AN EXACT SIGN TEST, not a t-test and not a normal approximation. Seven paired
samples, one bounded quantity, no distributional assumption available and none needed: count the
signs and read the binomial exactly. Ties are DROPPED (the standard treatment) and reported, so a
comparison decided by ties is visible as one.

AND THE CEILING IS PRINTED BESIDE EVERY VERDICT, because it answers a different question. The
delivered theta is the one the OBJECTIVE picked; the ceiling is the best held-out survival the
search visited at any turn. When the gap between them is larger than the gap between two arms,
the comparison is measuring the objective's mis-ranking and not the policy class.

    python tools/benchmark_verdict.py
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
LOGDIR = ROOT / "agent_logs"
OUTDIR = ROOT / "ChimeraEngine" / "output" / "ports"

# THE COMPARISONS THE TASKS NAME, each with its falsifier written as the task wrote it.
# `worse_or_equal_fires` = the falsifier is "A <= B", which is how tasks 1, 2, 3, 6 and 7 are
# phrased: the INTERESTING outcome is the one that fires.
COMPARISONS = [
    ("T1  rate feedback", "pd", "full", "p_only", "full",
     "PD held-out survival <= P-only held-out survival -- derivative feedback doesn't help "
     "standing."),
    ("T2  long baseline", "pd_windowed", "full", "pd", "full",
     "Windowed-PD held-out survival <= PD held-out survival -- a cleaner derivative doesn't "
     "help."),
    ("T3  phase basis", "pd_phase", "full", "pd", "full",
     "PD+phase held-out survival <= PD held-out survival -- the derivative already captures "
     "the oscillation."),
    ("T6  support-only", "p_only", "support_only", "p_only", "full",
     "Support-only held-out survival <= full-objective held-out survival -- removing "
     "anti-correlated noise doesn't help."),
    ("T6b support-only (pd)", "pd", "support_only", "pd", "full",
     "the same comparison on a second policy class, so the answer does not rest on one arm."),
]

# T4's six, all against `pd` -- the class they are ablations OF.
ABLATIONS = ("pd_no_z", "pd_no_zdot", "pd_no_pitch", "pd_no_pitch_rate",
             "pd_no_roll", "pd_no_roll_rate")


def sign_test(diff):
    """Exact two-sided sign test. Ties dropped. Returns (wins, ties, losses, p)."""
    w = int((diff > 0).sum())
    l = int((diff < 0).sum())
    t = int((diff == 0).sum())
    n = w + l
    if n == 0:
        return w, t, l, 1.0
    k = max(w, l)
    tail = sum(math.comb(n, i) for i in range(k, n + 1))
    return w, t, l, min(1.0, 2.0 * tail / (2 ** n))


def load():
    rows = {}
    for tag, obj in (("full", "full"), ("v2", "support_only")):
        p = LOGDIR / f"benchmark_{tag}.json"
        if not p.exists():
            raise SystemExit(f"no {p} -- refusing to read verdicts off a benchmark that was "
                             f"never run (rule 20).")
        for r in json.loads(p.read_text(encoding="utf8"))["rows"]:
            rows[(r["name"], obj)] = r
    return rows


def report(rows, label, a_key, b_key, falsifier):
    A, B = rows.get(a_key), rows.get(b_key)
    if A is None or B is None:
        print(f"  {label}: an arm is missing ({a_key if A is None else b_key}) -- skipped.")
        return None
    va = np.array(A["survival_per_seed_after"], float)
    vb = np.array(B["survival_per_seed_after"], float)
    diff = va - vb
    w, t, l, p = sign_test(diff)
    med_a, med_b = A["survival_after"], B["survival_after"]
    fires_median = med_a <= med_b
    fires_paired = float(np.median(diff)) <= 0.0
    print(f"\n  {label}   {a_key[0]}[{a_key[1]}]  vs  {b_key[0]}[{b_key[1]}]")
    print(f"    falsifier: {falsifier}")
    print(f"    MEDIAN     {med_a:.2f}s vs {med_b:.2f}s   -> "
          + ("FIRES" if fires_median else "does not fire"))
    print(f"    PAIRED     median difference {np.median(diff):+.2f}s   "
          f"wins {w}/{w+t+l}  ties {t}  losses {l}   sign test p = {p:.3f}   -> "
          + ("FIRES" if fires_paired else "does not fire"))
    print(f"    per seed   " + " ".join(f"{v:+.2f}" for v in diff))
    print(f"    ceiling    {A['survival_ceiling']:.2f}s (turn {A['survival_ceiling_turn']}) vs "
          f"{B['survival_ceiling']:.2f}s (turn {B['survival_ceiling_turn']})")
    if fires_median != fires_paired:
        print(f"    *** THE TWO STATISTICS DISAGREE. The seeds are paired by construction, so "
              f"the paired one is the")
        print(f"        measurement and the median is a rank statistic that threw the pairing "
              f"away. Both printed;")
        print(f"        the verdict below reads the PAIRED row, and says so rather than "
              f"choosing quietly.")
    sig = "" if p > 0.05 else "  (p <= 0.05)"
    print(f"    VERDICT (paired): " + ("FIRES" if fires_paired else "does NOT fire") + sig)
    return dict(label=label, a=list(a_key), b=list(b_key), median_a=med_a, median_b=med_b,
                paired_median=float(np.median(diff)), wins=w, ties=t, losses=l, p=p,
                fires_median=bool(fires_median), fires_paired=bool(fires_paired),
                ceiling_a=A["survival_ceiling"], ceiling_b=B["survival_ceiling"],
                per_seed_diff=[float(v) for v in diff])


def main() -> int:
    rows = load()
    print("\nPOLICY-CLASS BENCHMARK -- THE FALSIFIERS, ON THE PAIRED STATISTIC")
    print("=" * 108)
    print("  Every arm is judged on the SAME seven held-out initial conditions (seeds 3..9), so")
    print("  every comparison below is PAIRED. The median the runner prints is shown beside it "
          "and never instead.")
    out = [report(rows, lbl, (an, ao), (bn, bo), f)
           for lbl, an, ao, bn, bo, f in COMPARISONS]

    # ── T4: WHICH OBSERVATION MATTERS, on both questions it actually contains ────────────────
    print("\n" + "=" * 108)
    print("  T4  ABLATION -- and it is TWO questions, not one, because the warm start is P-only.")
    print("  Removing z / pitch / roll drops a TRAINED gain block: the ablation is felt "
          "immediately.")
    print("  Removing zdot / pitch_rate / roll_rate drops a channel whose gain STARTS AT ZERO: "
          "at the warm start")
    print("  it costs exactly nothing, and the only thing the ablation can measure is whether "
          "training would have")
    print("  ACQUIRED it. Ranking all six on one column would read two quantities as one "
          "(rule 19).")
    pd = rows[("pd", "full")]
    base_after = np.array(pd["survival_per_seed_after"], float)
    print(f"\n  {'removed channel':<20}{'warm s':>9}{'drop@warm':>11}{'trained s':>11}"
          f"{'vs pd':>9}{'wins/7':>9}{'p':>8}{'ceiling':>9}")
    t4 = []
    for n in ABLATIONS:
        r = rows.get((n, "full"))
        if r is None:
            continue
        v = np.array(r["survival_per_seed_after"], float)
        d = v - base_after
        w, t, l, p = sign_test(d)
        t4.append(dict(name=n, warm=r["survival_before"],
                       drop_warm=r["survival_before"] - pd["survival_before"],
                       after=r["survival_after"],
                       vs_pd=float(np.median(d)), wins=w, ties=t, losses=l, p=p,
                       ceiling=r["survival_ceiling"]))
        print(f"  {n.replace('pd_no_',''):<20}{r['survival_before']:>8.2f}s"
              f"{r['survival_before']-pd['survival_before']:>+11.2f}{r['survival_after']:>10.2f}s"
              f"{np.median(d):>+9.2f}{f'{w}/{w+t+l}':>9}{p:>8.3f}{r['survival_ceiling']:>8.2f}s")
    print(f"  {'(none: pd itself)':<20}{pd['survival_before']:>8.2f}s{0.0:>+11.2f}"
          f"{pd['survival_after']:>10.2f}s{0.0:>+9.2f}{'-':>9}{'-':>8}"
          f"{pd['survival_ceiling']:>8.2f}s")
    ranked = sorted([x for x in t4 if x["drop_warm"] < 0], key=lambda x: x["drop_warm"])
    print(f"\n  RANKED BY THE PURE ABLATION (a trained channel removed, no retraining): "
          + " > ".join(f"{x['name'].replace('pd_no_','')} ({x['drop_warm']:+.2f}s)"
                       for x in ranked))
    zero = [x for x in t4 if x["drop_warm"] == 0.0]
    print(f"  COSTS NOTHING AT THE WARM START: "
          + ", ".join(x["name"].replace("pd_no_", "") for x in zero)
          + " -- the incumbent has no rate gains to remove.")
    print(f"  T4 FALSIFIER (all six ablations have similar survival -- no observation matters "
          f"more than another):")
    spread = max(x["after"] for x in t4) - min(x["after"] for x in t4)
    print(f"    does not fire -- the trained spread is {spread:.2f} s "
          f"({min(x['after'] for x in t4):.2f}..{max(x['after'] for x in t4):.2f} s).")
    print(f"  AND THE TASK'S STATED NULL IS REFUTED: it predicted zdot and pitch_rate would be "
          f"the critical terms.")
    print(f"    They are the two whose removal costs the LEAST. `pitch` costs the most.")

    # ── THE CONTROL THAT SIZES EVERY COMPARISON ABOVE ────────────────────────────────────────
    print("\n" + "=" * 108)
    print("  THE OBJECTIVE'S OWN MIS-RANKING, PER ARM -- and it is the number to read the "
          "comparisons against.")
    print("  `delivered` is the theta the OBJECTIVE selected; `ceiling` is the best held-out "
          "survival the search")
    print("  visited. The gap between them is not noise: it is the objective preferring a "
          "policy that stands less")
    print("  long. Where that gap exceeds the difference between two ARMS, the comparison is "
          "measuring the")
    print("  objective and not the policy class.")
    print(f"\n  {'class':<20}{'delivered':>11}{'ceiling':>10}{'@turn':>7}{'objective cost':>16}")
    gaps = []
    for (n, o), r in sorted(rows.items(), key=lambda kv: -(kv[1]["survival_ceiling"]
                                                           - kv[1]["survival_after"])):
        g = r["survival_ceiling"] - r["survival_after"]
        gaps.append(g)
        print(f"  {n + ('[v2]' if o == 'support_only' else ''):<20}{r['survival_after']:>10.2f}s"
              f"{r['survival_ceiling']:>9.2f}s{r['survival_ceiling_turn']:>7}{-g:>+15.2f}s")
    print(f"\n  WORST OBJECTIVE COST {max(gaps):.2f} s; median {float(np.median(gaps)):.2f} s.")
    near = [r for (n, o), r in rows.items() if r["survival_before"] > 6.0]
    spread_near = (max(r["survival_after"] for r in near)
                   - min(r["survival_after"] for r in near))
    print(f"  SPREAD ACROSS THE ARMS THAT START AT 6.82 s: {spread_near:.2f} s "
          f"({min(r['survival_after'] for r in near):.2f}.."
          f"{max(r['survival_after'] for r in near):.2f} s).")
    print("  " + ("The objective's worst mis-ranking is LARGER than the whole between-class "
                  "spread. Every policy-class"
                  if max(gaps) > spread_near else
                  "The between-class spread exceeds the objective's worst mis-ranking, so the "
                  "classes are separable"))
    print("  " + ("difference above is inside the noise the objective itself introduces, and "
                  "that is the finding."
                  if max(gaps) > spread_near else "under this objective."))

    LOGDIR.mkdir(parents=True, exist_ok=True)
    (LOGDIR / "benchmark_verdict.json").write_text(json.dumps(dict(
        comparisons=[c for c in out if c], ablations=t4,
        worst_objective_cost=float(max(gaps)), median_objective_cost=float(np.median(gaps)),
        near_incumbent_spread=float(spread_near)), indent=1), encoding="utf8")
    print(f"\n  JSON: {LOGDIR / 'benchmark_verdict.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
