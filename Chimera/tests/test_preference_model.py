"""Stage 2 proof — the Bayesian preference model over the physics measure vector.

The comprehensive synthetic recovery + sample-efficiency proof lives in
core.preference.demo() (recovery to the noise ceiling, uncertainty shrinkage,
interpretability). This suite asserts demo() passes and adds the edge cases demo does
not cover: the prior on no data, the pre-fit guard, antisymmetry across many random
pairs, and rank/utility consistency.

Run from E:/PythonChimera/Chimera:
    python tests/test_preference_model.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # the Chimera root

import numpy as np

from core.preference import PreferenceModel, demo, synth_designs, synth_pairs


def _check(label, cond):
    print(f"  [{'ok' if cond else 'XX'}] {label}")
    return bool(cond)


def main():
    ok = True

    # 1. The full synthetic recovery/sample-efficiency proof.
    ok &= _check("core.preference.demo() passes (recovery + sample efficiency)", demo() == 0)

    # 2. No data -> the prior, exactly. w = 0 and weight-std = 1/sqrt(alpha).
    m0 = PreferenceModel(features=["a", "b"], alpha=4.0).fit([])
    ok &= _check("empty fit returns the prior (weights all zero)",
                 all(abs(v) < 1e-12 for v in m0.weights.values()))
    ok &= _check("empty fit posterior std = 1/sqrt(alpha) = 0.5",
                 all(abs(s - 0.5) < 1e-9 for s in m0.weight_std.values()))

    # 3. Used before fit -> a clear error, never a silent zero.
    raised = False
    try:
        PreferenceModel().utility({"a": 1.0})
    except RuntimeError:
        raised = True
    ok &= _check("utility() before fit() raises", raised)

    # 4. Antisymmetry across many random pairs (the property that makes it a preference).
    rng = np.random.default_rng(1)
    feats = ["skill_gap", "punishes_naive", "headroom"]
    designs = synth_designs(rng, feats, 60)
    w_true = np.array([1.8, 0.9, -1.1])
    m = PreferenceModel(alpha=1.0).fit(synth_pairs(rng, feats, designs, w_true, 40))
    anti = max(abs(m.prob(designs[i], designs[j]) + m.prob(designs[j], designs[i]) - 1.0)
               for i, j in [(0, 1), (2, 5), (7, 3), (10, 20), (30, 31)])
    ok &= _check(f"prob(a,b)+prob(b,a)==1 across random pairs (max err {anti:.1e})", anti < 1e-9)

    # 5. rank() is consistent with utility(): the #1-ranked design has the max utility.
    order = m.rank(designs)
    utils = [m.utility(d) for d in designs]
    ok &= _check("rank()[0] is the max-utility design",
                 abs(utils[order[0]] - max(utils)) < 1e-9)
    ok &= _check("rank() is a full permutation", sorted(order) == list(range(len(designs))))

    # 6. Learned taste points the right way: skill_gap weight positive, headroom negative.
    ok &= _check("recovered sign of skill_gap is positive (loves masterable)",
                 m.weights["skill_gap"] > 0)
    ok &= _check("recovered sign of headroom is negative",
                 m.weights["headroom"] < 0)

    print()
    print("PASS — the preference model is honest, sample-efficient, and uncertainty-aware"
          if ok else "FAIL — see the [XX] lines above")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
