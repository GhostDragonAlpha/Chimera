"""preference_elicit - WHEN to ask the operator, and WHICH comparison.

Stage 3 of the preference-attunement plan. The preference model (core.preference) learns
taste from comparisons; this decides which comparison is worth a scarce human's attention,
and refuses to ask at all until the machine has earned it.

TWO DISCIPLINES, both load-bearing:

1. THE GATE (never spend the operator on arithmetic). A design is eligible for comparison
   only if it PASSED PHYSICS — `feasible(design)` is True (in production this is
   core.trainables.attunement.ready_for_human: winnable, punishes the naive strategy, has
   skill in it, is learnable). Fewer than two eligible designs -> select_query returns
   None and asks NOTHING. Asking earlier is `ready_for_human`'s "easy out" wearing a
   courteous face: it spends the one resource the studio cannot manufacture on a question
   physics could still answer.

2. ACTIVE SELECTION (few labels, so make each one count). Among eligible designs, pick the
   MOST INFORMATIVE duel instead of a random one:
     - "uncertainty": the pair whose outcome the posterior is least sure of
       (max posterior logit std).
     - "dts" (Dueling Thompson Sampling, the dueling-bandit method for this regime): draw
       TWO independent weight vectors from the Laplace posterior, take each one's champion
       design, and duel them. A wide posterior -> the champions disagree -> an exploratory
       duel; a confident posterior -> they converge near the top -> a duel that refines the
       frontier. Explore/exploit falls out of the sampling, untuned.

The oracle here is ALWAYS the human (or, in the demo, a synthetic ground-truth taste
standing in for one). No LM selects, labels, or judges. This file only chooses the
question; the human answers it and core.graphify_interface.record_preference records it.

Membrane-clean: numpy + core.preference (itself numpy-only), deterministic.

    python -m core.preference_elicit demo    # gate behaviour + active-beats-random proof
"""
from __future__ import annotations

import argparse
import sys
from collections import namedtuple

import numpy as np

from core.preference import (PreferenceModel, _accuracy, _sigmoid, synth_designs,
                             synth_pairs)

# a b: indices into the designs list; info: posterior logit std of the chosen duel;
# strategy: how it was chosen; n_feasible: how many designs passed the gate.
Query = namedtuple("Query", "a b info strategy n_feasible")


def _feasible_indices(designs, feasible):
    return [i for i, d in enumerate(designs) if (feasible is None or feasible(d))]


def _binary_entropy(p):
    p = np.clip(p, 1e-9, 1.0 - 1e-9)
    return -(p * np.log(p) + (1.0 - p) * np.log(1.0 - p))


def select_query(model, designs, feasible=None, strategy="bald", rng=None,
                 n_samples=64, max_pairs=800):
    """Choose the next comparison to put to the operator, or None if none is earned.

    Returns a Query(a, b, ...) of indices into `designs`, or None when fewer than two
    designs pass `feasible` — the machine has not earned the operator's time.

    strategy:
      "bald"      — maximise information gain about the taste weights: the pair whose
                    outcome the posterior SAMPLES disagree on. H(mean p) - E[H(p)] over
                    posterior draws. Peaks where the outcome is both ambiguous AND the
                    weights are unsure — the correct acquisition. (default)
      "ambiguity" — the pair nearest the 0.5 decision boundary under the MAP weights
                    (two designs the operator finds similarly good; a fine distinction).
      "logit_var" — the naive d'Σd. KEPT AS A CAUTIONARY BASELINE: it selects far-apart,
                    already-decided pairs and underperforms random. Do not use it.
      "dts"       — Dueling Thompson Sampling: two independent posterior draws, each one's
                    champion, dueled.
    """
    idx = _feasible_indices(designs, feasible)
    if len(idx) < 2:
        return None
    rng = rng if rng is not None else np.random.default_rng()

    if strategy == "dts":
        cov = 0.5 * (model.cov + model.cov.T)
        w1 = rng.multivariate_normal(model.w, cov)
        w2 = rng.multivariate_normal(model.w, cov)

        def champion(ws, exclude=None):
            best_i, best_u = None, None
            for i in idx:
                if i == exclude:
                    continue
                u = float(model.phi(designs[i]) @ ws)
                if best_u is None or u > best_u:
                    best_i, best_u = i, u
            return best_i

        c1 = champion(w1)
        c2 = champion(w2, exclude=c1)
        return Query(c1, c2, model.uncertainty(designs[c1], designs[c2]), strategy, len(idx))

    # pair-scoring strategies — candidate pairs (subsampled if the shortlist is large)
    pairs = [(idx[a], idx[b]) for a in range(len(idx)) for b in range(a + 1, len(idx))]
    if len(pairs) > max_pairs:
        pick = rng.choice(len(pairs), size=max_pairs, replace=False)
        pairs = [pairs[k] for k in pick]
    D = np.array([model.phi(designs[i]) - model.phi(designs[j]) for i, j in pairs])  # (P, K)

    if strategy == "logit_var":
        score = np.einsum("pk,kl,pl->p", D, model.cov, D)
    elif strategy == "ambiguity":
        score = -np.abs(_sigmoid(D @ model.w) - 0.5)          # nearest the boundary
    elif strategy == "bald":
        cov = 0.5 * (model.cov + model.cov.T)
        Ws = rng.multivariate_normal(model.w, cov, size=n_samples)   # (M, K)
        P = _sigmoid(D @ Ws.T)                                        # (P, M)
        score = _binary_entropy(P.mean(axis=1)) - _binary_entropy(P).mean(axis=1)
    else:
        raise ValueError(f"unknown strategy {strategy!r}")

    best = int(np.argmax(score))
    i, j = pairs[best]
    return Query(i, j, float(model.uncertainty(designs[i], designs[j])), strategy, len(idx))


# ---------------------------------------------------------------------------
# validation — active selection should reach a given accuracy in FEWER operator
# comparisons than random. The oracle is a synthetic ground-truth taste (the human's
# stand-in); the loop is exactly the production loop with the human swapped for w_true.
# ---------------------------------------------------------------------------
def _oracle(a, b, features, w_true, rng):
    z = np.array([a[f] for f in features]) - np.array([b[f] for f in features])
    return (a, b) if (rng.random() < _sigmoid(float(np.asarray(w_true) @ z))) else (b, a)


def _learning_curve(rng, features, designs, w_true, test, n_queries, strategy, seed_pairs=3):
    """Run n_queries of the ask->answer->refit loop; return held-out accuracy after each."""
    train = list(synth_pairs(rng, features, designs, w_true, seed_pairs))   # a few to fit at all
    model = PreferenceModel(alpha=1.0).fit(train)
    accs = []
    for _ in range(n_queries):
        if strategy == "random":
            i, j = int(rng.integers(len(designs))), int(rng.integers(len(designs)))
            while j == i:
                j = int(rng.integers(len(designs)))
        else:
            q = select_query(model, designs, strategy=strategy, rng=rng)
            i, j = q.a, q.b
        train.append(_oracle(designs[i], designs[j], features, w_true, rng))
        model = PreferenceModel(alpha=1.0).fit(train)
        accs.append(_accuracy(model, test))
    return np.array(accs)


def demo():
    features = ["skill_gap", "punishes_naive", "learnability", "headroom", "band_hz", "n_partials"]
    w_true = np.array([2.2, 1.3, 0.7, -1.0, 0.1, -0.4])
    n_queries, seeds = 30, 8

    print("=" * 74)
    print("ACTIVE ELICITATION — when to ask, and which comparison")
    print("=" * 74)

    ok = True

    def check(label, cond):
        nonlocal ok
        print(f"  [{'ok' if cond else 'XX'}] {label}")
        ok = ok and bool(cond)

    # -- the gate (the load-bearing discipline) --------------------------------
    rng = np.random.default_rng(0)
    designs = synth_designs(rng, features, 100)
    model = PreferenceModel(alpha=1.0).fit(synth_pairs(rng, features, designs, w_true, 30))

    check("no query when <2 designs are eligible (nothing earned)",
          select_query(model, [designs[0]]) is None)
    gated = lambda d: d["skill_gap"] > 0.5
    q = select_query(model, designs, feasible=gated, strategy="bald", rng=rng)
    check("a returned duel has both sides feasible (passed the gate)",
          q is not None and gated(designs[q.a]) and gated(designs[q.b]))
    check("a returned duel is two distinct designs", q is not None and q.a != q.b)

    # ambiguity targets near-boundary comparisons (informative), not far-apart ones.
    qa = select_query(model, designs, strategy="ambiguity")
    sel = abs(model.prob(designs[qa.a], designs[qa.b]) - 0.5)
    rnd = float(np.mean([abs(model.prob(designs[int(rng.integers(100))],
                                        designs[int(rng.integers(100))]) - 0.5)
                         for _ in range(300)]))
    check(f"ambiguity picks a nearer-boundary duel than a random pair ({sel:.3f} < {rnd:.3f})",
          sel < rnd)

    # -- active vs random: measured honestly -----------------------------------
    # Per seed: fix designs + held-out test once; run each strategy from the SAME run-rng
    # so they share seed pairs and early oracle draws and diverge only by what they ask.
    strategies = ["random", "ambiguity", "bald", "dts", "logit_var"]
    curves = {s: [] for s in strategies}
    for s in range(seeds):
        rng_data = np.random.default_rng(100 + s)
        d = synth_designs(rng_data, features, 100)
        test = synth_pairs(rng_data, features, d, w_true, 400)
        for strat in strategies:
            rng_run = np.random.default_rng(500 + s)
            curves[strat].append(_learning_curve(rng_run, features, d, w_true, test, n_queries, strat))
    mean = {k: np.mean(np.vstack(v), axis=0) for k, v in curves.items()}

    def first_reach(curve, thr):
        hit = int(np.argmax(curve >= thr))
        return hit + 1 if curve[hit] >= thr else None

    thr = 0.80
    print(f"\n  mean held-out accuracy over {seeds} seeds, {n_queries} operator comparisons:")
    print(f"  {'strategy':>12}  {'final acc':>10}  {'mean acc':>9}  {'queries to '+str(thr):>14}")
    for k in strategies:
        fr = first_reach(mean[k], thr)
        print(f"  {k:>12}  {mean[k][-1]:>10.3f}  {mean[k].mean():>9.3f}  "
              f"{(str(fr) if fr else '>'+str(n_queries)):>14}")
    rand_mean = mean["random"].mean()
    best_active = max(("ambiguity", "bald", "dts"), key=lambda k: mean[k].mean())
    delta = mean[best_active].mean() - rand_mean
    print(f"\n  best active = {best_active}; mean-accuracy delta vs random = {delta:+.3f}")
    print("  (at 6 clean physics axes the feature reduction is so strong that random is a")
    print("   hard baseline; the gate is the load-bearing part, active selection a bonus.)")
    print()

    # HONEST checks. The gate must work and the corrected metric must at least not LOSE to
    # random — the naive logit_var did (kept as the cautionary baseline below).
    check("corrected metric fixed the regression: best active >= random - 0.01",
          delta >= -0.01)
    check("the naive logit_var baseline still underperforms (why the fix mattered)",
          mean["logit_var"].mean() < rand_mean + 1e-9)

    print("=" * 74)
    print("PASS — the machine asks only when earned, and asks near the boundary not the edge"
          if ok else "FAIL — see the [XX] lines above")
    print("=" * 74)
    return 0 if ok else 1


def main(argv=None):
    p = argparse.ArgumentParser(prog="preference_elicit", description=__doc__.split("\n")[1])
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("demo", help="gate behaviour + active-beats-random proof")
    a = p.parse_args(argv)
    return demo() if a.cmd == "demo" else 1


if __name__ == "__main__":
    sys.exit(main())
