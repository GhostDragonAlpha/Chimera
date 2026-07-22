"""preference - the operator's taste as a model over the PHYSICS MEASURE VECTOR.

Stage 2 of the preference-attunement plan. Given pairwise comparisons between designs
(each design already reduced to a handful of honest physical facts by a domain's
measure()), learn a utility u(x) = w . phi(x) such that

    P(A preferred over B) = sigmoid( w . (phi(A) - phi(B)) )       <- Bradley-Terry

and report BOTH the weights (what the operator's taste values, per physical axis) and
the UNCERTAINTY on any comparison (what Stage 3 spends the operator on).

WHY THIS IS TRACTABLE AT SINGLE-OPERATOR SCALE. A neural reward model over raw artifacts
needs thousands of labels. Here phi is ~6 interpretable physics axes (skill_gap,
punishes_naive, learnability, headroom, ...), so the model is ~6 weights and a Gaussian
prior fits it from a DOZEN comparisons. The studio's physics feature-reduction is exactly
what makes preference learning cheap: you are not learning taste over pixels, you are
learning which region of an already-meaningful measure-space the human prefers.

WHAT KEEPS IT HONEST (the constitution, not decoration):
- No intercept -> exactly antisymmetric: P(A>B) + P(B>A) = 1. A model that could prefer A
  over B AND B over A is not a preference.
- A Gaussian prior (alpha) + Laplace posterior -> finite weights even on perfectly
  separable data (a handful of unanimous labels cannot send a weight to infinity), and a
  covariance that says how sure it is. Few labels => wide posterior => Stage 3 asks.
- This model NEVER judges. It consumes recorded HUMAN preferences (PreferenceObservation
  nodes, core/graphify_interface.record_preference) and physics FACTS (measure()). The LM
  is nowhere in it. It cannot manufacture a preference; it can only fit ones a person gave.

Membrane-clean: numpy only, no studio imports, deterministic. Stage 4 is the glue that
reads PreferenceObservation nodes into fit(); this file only does the math.

    python -m core.preference demo        # synthetic recovery + sample-efficiency proof
"""
from __future__ import annotations

import argparse
import math
import sys

import numpy as np


def _sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -30.0, 30.0)))


def _is_number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


class PreferenceModel:
    """Bayesian Bradley-Terry over a design's physics measure vector.

    fit(pairs) where pairs is [(measures_winner, measures_loser), ...] and each measures
    is a dict of physical facts (a domain's measure() output, or a PreferenceObservation
    node's measures_winner/measures_loser). The label is implicit: the first of each pair
    was preferred.
    """

    def __init__(self, features=None, alpha=1.0, newton_iters=50, tol=1e-9):
        # features: explicit feature names to use; None -> inferred (keys common to every
        #   design in the pairs). alpha: Gaussian prior precision (regularisation strength;
        #   higher = more shrinkage toward "taste is flat"). The prior is what tames few
        #   labels and separable data.
        self.features = list(features) if features else None
        self.alpha = float(alpha)
        self.newton_iters = int(newton_iters)
        self.tol = float(tol)
        self.w = None          # MAP weights in STANDARDISED space, shape (K,)
        self.cov = None        # Laplace posterior covariance, shape (K, K)
        self.mu = None         # per-feature mean  (standardisation)
        self.sd = None         # per-feature std   (standardisation)
        self.n_pairs = 0

    # -- feature plumbing -----------------------------------------------------
    def _infer_features(self, pairs):
        if self.features:
            return list(self.features)
        common = None
        for w, l in pairs:
            for d in (w, l):
                keys = {k for k, v in d.items() if _is_number(v)}
                common = keys if common is None else (common & keys)
        return sorted(common or [])

    def _vec(self, d):
        return np.array([float(d.get(f, 0.0)) for f in self.features], dtype=float)

    def _std(self, x):
        return (x - self.mu) / self.sd

    def _require_fit(self):
        if self.w is None:
            raise RuntimeError("PreferenceModel used before fit() — nothing learned yet")

    # -- fit ------------------------------------------------------------------
    def fit(self, pairs):
        pairs = [(w, l) for w, l in pairs]
        self.n_pairs = len(pairs)
        self.features = self._infer_features(pairs)
        K = len(self.features)
        if K == 0:
            raise ValueError("no shared numeric features across the preference pairs — "
                             "the designs share no physics axis to learn taste over")

        W = np.array([self._vec(w) for w, l in pairs]) if pairs else np.zeros((0, K))
        L = np.array([self._vec(l) for w, l in pairs]) if pairs else np.zeros((0, K))

        # Standardise over the POOLED designs (winners and losers together) so a weight's
        # magnitude is comparable across axes — "taste weights skill_gap more than headroom"
        # only means something if both are on the same scale.
        pool = np.vstack([W, L]) if pairs else np.zeros((1, K))
        self.mu = pool.mean(axis=0)
        self.sd = pool.std(axis=0)
        self.sd[self.sd < 1e-9] = 1.0     # a constant axis carries no taste signal; centring zeroes it

        D = (self._std(W) - self._std(L)) if pairs else np.zeros((0, K))

        # Newton's method on the (strongly, because alpha>0) convex negative log-posterior:
        #   L(w) = -sum log sigmoid(w . d_i) + (alpha/2)||w||^2
        w = np.zeros(K)
        aI = self.alpha * np.eye(K)
        for _ in range(self.newton_iters):
            p = _sigmoid(D @ w)                       # P(winner preferred) under current w
            grad = -(D.T @ (1.0 - p)) + self.alpha * w
            s = p * (1.0 - p)
            H = (D.T * s) @ D + aI                     # PD for alpha>0
            try:
                step = np.linalg.solve(H, grad)
            except np.linalg.LinAlgError:
                step = np.linalg.lstsq(H, grad, rcond=None)[0]
            w = w - step
            if np.max(np.abs(step)) < self.tol:
                break
        self.w = w

        # Laplace: posterior ~ N(w_MAP, H^-1) at the MAP. The covariance is the uncertainty
        # Stage 3 reads to decide which comparison is worth the operator's attention.
        p = _sigmoid(D @ w)
        s = p * (1.0 - p)
        H = (D.T * s) @ D + aI
        self.cov = np.linalg.inv(H)
        return self

    # -- predict / read out ---------------------------------------------------
    def phi(self, measures):
        """The standardised physics-feature vector for a design (numpy array) — the space
        the weights live in. Public so an active selector can score a design under a
        SAMPLED weight vector (Dueling Thompson Sampling), not just the MAP."""
        self._require_fit()
        return self._std(self._vec(measures))

    def utility(self, measures) -> float:
        """The taste score of a single design. Higher = more preferred."""
        self._require_fit()
        return float(self.phi(measures) @ self.w)

    def prob(self, a, b) -> float:
        """P(operator prefers design a over design b). Exactly 1 - prob(b, a)."""
        self._require_fit()
        d = self._std(self._vec(a)) - self._std(self._vec(b))
        return float(_sigmoid(d @ self.w))

    def uncertainty(self, a, b) -> float:
        """Posterior std of the a-vs-b logit — how unsure the model is about this
        comparison. Stage 3's active selector spends the operator on the MOST uncertain
        (feasible) pair."""
        self._require_fit()
        d = self._std(self._vec(a)) - self._std(self._vec(b))
        return math.sqrt(max(float(d @ self.cov @ d), 0.0))

    def rank(self, designs) -> list:
        """Indices of `designs` best-first by learned taste."""
        self._require_fit()
        u = [self.utility(d) for d in designs]
        return sorted(range(len(designs)), key=lambda i: u[i], reverse=True)

    @property
    def weights(self) -> dict:
        """{feature: weight} in standardised space — what the operator's taste values,
        per physical axis, on a comparable scale. Sign says direction, magnitude says
        how much this axis moves the preference."""
        if self.w is None:
            return {}
        return {f: float(wi) for f, wi in zip(self.features, self.w)}

    @property
    def weight_std(self) -> dict:
        """Per-feature posterior std (sqrt of the covariance diagonal) — the honesty
        channel: a big std next to a weight means 'not enough comparisons to trust this'."""
        if self.cov is None:
            return {}
        sd = np.sqrt(np.clip(np.diag(self.cov), 0.0, None))
        return {f: float(s) for f, s in zip(self.features, sd)}


# ---------------------------------------------------------------------------
# synthetic ground truth — shared by demo() and the test, so the estimator is proved
# against a taste we KNOW before it is ever pointed at a real operator.
# ---------------------------------------------------------------------------
def synth_designs(rng, features, n):
    """n designs with i.i.d. ~N(0,1) facts, so the model's standardisation is ~identity
    and a recovered weight can be read directly against the ground truth."""
    return [{f: float(rng.normal()) for f in features} for _ in range(n)]


def synth_pairs(rng, features, designs, w_true, n, noise=True):
    """n comparisons labelled by the Bradley-Terry model under w_true. noise=True flips
    the label with the model's own probability (a real operator is not deterministic);
    noise=False is the separable stress case."""
    w_true = np.asarray(w_true, dtype=float)

    def z(d):
        return np.array([d[f] for f in features])

    pairs = []
    m = len(designs)
    for _ in range(n):
        i = int(rng.integers(m))
        j = int(rng.integers(m))
        while j == i:
            j = int(rng.integers(m))
        a, b = designs[i], designs[j]
        du = float(w_true @ (z(a) - z(b)))
        a_wins = (rng.random() < _sigmoid(du)) if noise else (du > 0)
        pairs.append((a, b) if a_wins else (b, a))
    return pairs


def _accuracy(model, pairs):
    return float(np.mean([model.prob(w, l) > 0.5 for w, l in pairs])) if pairs else 0.0


def _ceiling(features, designs, w_true, pairs):
    """The best any model could do on THESE noisy labels: predict by the true utility."""
    w_true = np.asarray(w_true, dtype=float)

    def z(d):
        return np.array([d[f] for f in features])

    return float(np.mean([(w_true @ (z(w) - z(l))) > 0 for w, l in pairs]))


def demo():
    rng = np.random.default_rng(0)
    features = ["skill_gap", "punishes_naive", "learnability", "headroom", "band_hz", "n_partials"]
    w_true = np.array([2.2, 1.3, 0.7, -1.0, 0.1, -0.4])   # a taste that loves masterable, punishing designs

    designs = synth_designs(rng, features, 400)
    test = synth_pairs(rng, features, designs, w_true, 400)
    ceiling = _ceiling(features, designs, w_true, test)

    print("=" * 74)
    print("PREFERENCE MODEL — taste learned over the PHYSICS MEASURE VECTOR")
    print("  ground-truth taste weights (standardised):")
    print("    " + "  ".join(f"{f}={v:+.1f}" for f, v in zip(features, w_true)))
    print(f"  noise ceiling on held-out pairs (best possible) = {ceiling:.3f}")
    print("=" * 74)
    print(f"  {'n_pairs':>8}  {'held-out acc':>12}  {'mean weight-std':>15}  top axis")

    results = {}
    for n in (8, 15, 30, 80, 200):
        train = synth_pairs(rng, features, designs, w_true, n)
        m = PreferenceModel(alpha=1.0).fit(train)
        acc = _accuracy(m, test)
        wstd = float(np.mean(list(m.weight_std.values())))
        top = max(m.weights, key=lambda k: abs(m.weights[k]))
        results[n] = (acc, wstd, top, m)
        print(f"  {n:>8}  {acc:>12.3f}  {wstd:>15.3f}  {top}")

    print("-" * 74)
    ok = True

    def check(label, cond):
        nonlocal ok
        print(f"  [{'ok' if cond else 'XX'}] {label}")
        ok = ok and bool(cond)

    acc15 = results[15][0]
    acc200 = results[200][0]
    check(f"sample-efficient: 15 comparisons over 6 axes already beat 0.70 ({acc15:.3f})",
          acc15 > 0.70)
    check(f"recovers the taste: 200 comparisons reach >=0.92 of the noise ceiling "
          f"({acc200:.3f} vs {ceiling:.3f})", acc200 >= 0.92 * ceiling)
    check("uncertainty shrinks with evidence (weight-std 8 > 200)",
          results[8][1] > results[200][1])
    check("interpretable: the dominant learned axis is skill_gap",
          results[200][2] == "skill_gap")

    m200 = results[200][3]
    a, b = designs[0], designs[1]
    check("antisymmetric: prob(a,b) + prob(b,a) == 1",
          abs(m200.prob(a, b) + m200.prob(b, a) - 1.0) < 1e-9)

    sep = synth_pairs(rng, features, designs, w_true, 40, noise=False)
    ms = PreferenceModel(alpha=1.0).fit(sep)
    finite = np.all(np.isfinite(list(ms.weights.values())))
    p = ms.prob(designs[2], designs[3])
    check("separable data stays finite (prior regularises; no blow-up)",
          finite and 0.0 < p < 1.0)

    print("=" * 74)
    print("PASS — taste is learnable from few comparisons over the physics axes"
          if ok else "FAIL — see the [XX] lines above")
    print("=" * 74)
    return 0 if ok else 1


def main(argv=None):
    p = argparse.ArgumentParser(prog="preference", description=__doc__.split("\n")[1])
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("demo", help="synthetic recovery + sample-efficiency proof")
    a = p.parse_args(argv)
    return demo() if a.cmd == "demo" else 1


if __name__ == "__main__":
    sys.exit(main())
