"""rate_feedback_power.py -- DOES RATE FEEDBACK HELP, OR IS 6/7 A COIN THAT LANDED SIX TIMES?

RULE 0, stated before the run:

    STATEMENT   The T1 benchmark measured PD beating P-only on 6 of 7 held-out seeds by a paired
                median of +0.18 s, and reported it as "does NOT fire, not significant". That is
                the correct reading of an exact sign test at n = 7, where 6/7 gives p = 0.125 and
                even a PERFECT 7/7 gives p = 0.0156. **The experiment could not have produced a
                significant result at that sample size no matter what the body did**, so its
                verdict is a statement about the seed count and not yet about rate feedback.

    PREDICTION  Held-out seeds are cheap -- a rollout ends when the body falls, ~7 s of sim -- so
                extending the SAME paired comparison to 24 held-out seeds resolves it. If the
                +0.18 s is real, the win rate stays near 6/7 and p falls below 0.05.

    FALSIFIER   The win rate collapses toward 1/2 as seeds are added -- the 6/7 was the small
                sample, rate feedback does not help this body, and T1's verdict stands for a
                better reason than the one originally given.

WHY THIS IS NOT RE-RUNNING A SETTLED QUESTION. Nothing is retrained and no theta moves: the two
arms `bench_full_pd` and `bench_full_p_only` are judged exactly as the benchmark judged them,
through the benchmark's OWN `survive`, on MORE of the same kind of seed. The only variable is n.

PAIRED, ALWAYS. Both arms see the identical seed on every row, so each row is a difference under
one initial condition and the test is over those differences. The benchmark already established
why this matters: the UNPAIRED median reports pd LOSING by 0.10 s while pd wins on six of seven
seeds, because both medians land on the single seed where it loses.

    python tools/rate_feedback_power.py [--seeds 24] [--secs 20]
"""
from __future__ import annotations

import json
import sys
from math import comb
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from world import load_body                                       # noqa: E402
from stand_port import derive_stand_port, MYOBODY                 # noqa: E402
from train_stand import joint_ids                                 # noqa: E402
import policy_classes as PC                                       # noqa: E402
import benchmark_policies as BP                                   # noqa: E402

OUTDIR = ROOT / "ChimeraEngine" / "output" / "ports"
LOGDIR = ROOT / "agent_logs"
TRAINED_SEEDS = (0, 1, 2)
ARMS = (("pd", "bench_full_pd"), ("p_only", "bench_full_p_only"))


def sign_p(wins, losses):
    """Exact two-sided sign test. Ties are dropped, which is the standard convention and is
    stated because dropping them changes n and therefore the p it is compared against."""
    n = wins + losses
    if n == 0:
        return 1.0
    k = min(wins, losses)
    return min(1.0, 2.0 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)


def main() -> int:
    import mujoco
    a = sys.argv
    nseeds = int(a[a.index("--seeds") + 1]) if "--seeds" in a else 24
    secs = float(a[a.index("--secs") + 1]) if "--secs" in a else 20.0
    P = derive_stand_port()
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    jids = joint_ids(m, mujoco)
    held = [i for i in range(3, 3 + nseeds)]

    print(f"\nRATE FEEDBACK -- IS 6/7 REAL? paired over {len(held)} held-out seeds "
          f"({held[0]}..{held[-1]}), {secs:.0f} s")
    print("=" * 96)
    print(f"  n = 7 COULD NOT HAVE ANSWERED THIS. An exact two-sided sign test gives p = 0.125 "
          f"at 6/7 and")
    print(f"  p = {sign_p(7,0):.4f} at a perfect 7/7 -- so the benchmark's 'not significant' was "
          f"a fact about the")
    print(f"  seed count before it was a fact about the body. Nothing is retrained here; only n "
          f"moves.")
    print("-" * 96)
    res = {}
    for label, fname in ARMS:
        p = OUTDIR / f"{fname}.npy"
        if not p.exists():
            raise SystemExit(f"no {p} -- refusing to re-judge an arm that is not on disk "
                             f"(rule 20).")
        th = np.load(p)
        pc = PC.get(label)
        pc.decode_theta(th, m.nu)
        _, per = BP.survive(mujoco, m, d, jids, P, pc, th, secs, held)
        res[label] = np.array(per, dtype=float)
        print(f"  {label:8} median {float(np.median(res[label])):.2f} s   "
              f"min {res[label].min():.2f}   max {res[label].max():.2f}")
    diff = res["pd"] - res["p_only"]
    wins = int((diff > 1e-9).sum())
    losses = int((diff < -1e-9).sum())
    ties = int(len(diff) - wins - losses)
    pval = sign_p(wins, losses)
    print("-" * 96)
    print(f"  PAIRED (pd - p_only), per seed:")
    for i in range(0, len(held), 12):
        print("    " + "  ".join(f"{v:+.2f}" for v in diff[i:i + 12]))
    print(f"  wins {wins}  ties {ties}  losses {losses}   paired median "
          f"{float(np.median(diff)):+.3f} s   mean {float(diff.mean()):+.3f} s")
    print(f"  exact two-sided sign test (ties dropped, n = {wins+losses}): p = {pval:.4f}")
    print(f"  UNPAIRED medians would say: pd {float(np.median(res['pd'])):.2f} vs p_only "
          f"{float(np.median(res['p_only'])):.2f} = "
          f"{float(np.median(res['pd']) - np.median(res['p_only'])):+.2f} s")
    print("=" * 96)
    rate = wins / max(wins + losses, 1)
    fires = rate < 0.65 or pval >= 0.05
    print(f"  FALSIFIER (the win rate collapses toward 1/2, or p stays >= 0.05): "
          + (f"FIRES -- win rate {rate:.2f}, p = {pval:.4f}.\n    The 6/7 does not survive more "
             f"seeds at this effect size. Rate feedback is not established for this body,\n"
             f"    and T1's verdict stands for a better reason than the one first given."
             if fires else
             f"does not fire -- win rate {rate:.2f} held over {wins+losses} seeds at "
             f"p = {pval:.4f}.\n    Rate feedback DOES help, by a paired median of "
             f"{float(np.median(diff)):+.3f} s. The original 'not significant' was the\n"
             f"    sample size, not the body."))
    print(f"  AND THE SIZE IS THE POINT EITHER WAY: {float(np.median(diff)):+.3f} s against a "
          f"between-class spread of 0.76 s")
    print(f"  and an objective mis-ranking cost of 0.78 s. Even a real effect here is smaller "
          f"than what the")
    print(f"  proxy throws away choosing which theta to deliver.")

    LOGDIR.mkdir(parents=True, exist_ok=True)
    out = LOGDIR / "rate_feedback_power.json"
    out.write_text(json.dumps(dict(
        seeds=held, secs=secs, pd=res["pd"].tolist(), p_only=res["p_only"].tolist(),
        diff=diff.tolist(), wins=wins, ties=ties, losses=losses,
        paired_median=float(np.median(diff)), paired_mean=float(diff.mean()),
        p_value=pval, win_rate=rate, falsifier_fires=bool(fires)), indent=1), encoding="utf8")
    print(f"  JSON: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
