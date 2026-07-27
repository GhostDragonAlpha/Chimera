"""Stage 3 proof — active elicitation + the ask gate.

The measured active-beats-random comparison lives in core.preference_elicit.demo(). This
suite asserts demo() passes and pins the discrete behaviours: the gate returns None until
two designs are eligible, a returned duel is feasible and distinct, ambiguity/BALD target
informative (near-boundary) pairs rather than the naive far-apart ones, and an unknown
strategy is refused.

Run from E:/PythonChimera/Chimera:
    python tests/test_preference_elicit.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # the Chimera root

import numpy as np

from core.preference import PreferenceModel, synth_designs, synth_pairs
from core.preference_elicit import demo, select_query


def _check(label, cond):
    print(f"  [{'ok' if cond else 'XX'}] {label}")
    return bool(cond)


def main():
    ok = True

    features = ["skill_gap", "punishes_naive", "learnability", "headroom"]
    w_true = np.array([2.0, 1.1, 0.6, -1.0])
    rng = np.random.default_rng(3)
    designs = synth_designs(rng, features, 80)
    model = PreferenceModel(alpha=1.0).fit(synth_pairs(rng, features, designs, w_true, 40))

    # 1. The gate.
    ok &= _check("None when 0 designs eligible", select_query(model, designs, feasible=lambda d: False) is None)
    ok &= _check("None when only 1 design eligible",
                 select_query(model, [designs[0]]) is None)
    gated = lambda d: d["skill_gap"] > 0.0
    q = select_query(model, designs, feasible=gated, strategy="bald", rng=rng)
    ok &= _check("returned duel: both sides passed the gate",
                 q is not None and gated(designs[q.a]) and gated(designs[q.b]))
    ok &= _check("returned duel: two distinct designs", q is not None and q.a != q.b)
    ok &= _check("Query reports how many designs were feasible",
                 q is not None and q.n_feasible == sum(1 for d in designs if gated(d)))

    # 2. Informative-not-extreme: ambiguity's chosen pair is nearer prob 0.5 than average.
    qa = select_query(model, designs, strategy="ambiguity")
    sel = abs(model.prob(designs[qa.a], designs[qa.b]) - 0.5)
    avg = float(np.mean([abs(model.prob(designs[int(rng.integers(80))],
                                        designs[int(rng.integers(80))]) - 0.5) for _ in range(300)]))
    ok &= _check(f"ambiguity picks a near-boundary duel ({sel:.3f} < {avg:.3f})", sel < avg)

    # 3. All strategies return a valid, feasible, distinct duel.
    for strat in ("bald", "ambiguity", "dts", "logit_var"):
        q = select_query(model, designs, feasible=gated, strategy=strat, rng=np.random.default_rng(7))
        good = q is not None and q.a != q.b and gated(designs[q.a]) and gated(designs[q.b])
        ok &= _check(f"strategy '{strat}' returns a valid feasible duel", good)

    # 4. An unknown strategy is refused, not silently guessed.
    raised = False
    try:
        select_query(model, designs, strategy="magic")
    except ValueError:
        raised = True
    ok &= _check("unknown strategy raises ValueError", raised)

    # 5. The full measured proof (active beats random via the corrected metric).
    ok &= _check("core.preference_elicit.demo() passes", demo() == 0)

    print()
    print("PASS — asks only when earned, and asks where the answer is informative"
          if ok else "FAIL — see the [XX] lines above")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
