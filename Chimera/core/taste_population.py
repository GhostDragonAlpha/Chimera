"""taste_population — taste is a class genome. Which parts of fun are CULTURAL vs PERSONAL.

THE SOCIOLOGY HIRE (2026-07-24, backlog T3, the operator's insight). The spine closed this
session with every term terminating at PHYSICS and none at THE HUMAN -- the vocabulary scored
CUTSCENE against its own emotion test. The fix the operator named: "fun can be defined by
characteristics and preferences of groups... a sampling that predicts what is fun for someone
in China vs America." Sociology is the first hire that makes the human terminal MEASURABLE.

And it is the SAME machinery the studio already runs on matter, applied to taste:

    matter                          taste
    ------                          -----
    a specimen (one scan)           an individual (one person's preferences)
    a population (a material class)  a group (a culture / demographic)
    a trait (size, aniso)           a taste AXIS (skill_gap, punishes_naive, ...)
    heritability h2 = V_between /    the fraction of taste that is CULTURAL: predictable from
      (V_between + V_within)          which group you are in, vs PERSONAL: varying as much
                                       inside a country as between countries

    h2 HIGH on an axis  ->  cultural. Design it per market; a group sample predicts it.
    h2 LOW  on an axis  ->  personal. No amount of sociology predicts it; you must ask the
                            individual. This is exactly the boundary the preference loop
                            (core/preference.py, the HUMAN terminal) exists to cross.

Most arguments about "what players want" are that distinction, unmade. This makes it a number.

HONEST DATA STATUS: there is no real cross-cultural preference corpus yet, so the demo below
is CLEARLY SYNTHETIC -- two groups constructed with a known cultural/personal split, to show
the machinery RECOVERS which axis is which. When the operator elicits real group preferences
(core/preference_elicit.py, per group), this layer computes the real split unchanged. The
machinery is real; the demo data is labeled synthetic, the same authored-awaiting-measured
pattern as the emissive/fluid/atmosphere genomes.
"""
from __future__ import annotations

import numpy as np

# The taste axes are the physics measure vector the preference model already scores over
# (core/preference.py). Taste is weights over THESE -- never over raw pixels.
DEFAULT_AXES = ('skill_gap', 'punishes_naive', 'learnability', 'headroom')


def heritability_split(groups: dict, axes=DEFAULT_AXES) -> dict:
    """Per axis: V_between, V_within, and h2 = cultural fraction of taste variation.

    groups: {group_name: [individual_weight_dict, ...]} -- each individual's taste weights over
    the axes (e.g. from a per-person PreferenceModel.weights()). Needs >=2 groups and >=2
    individuals per group for the split to be defined, the same minimum a class genome needs.
    """
    names = list(groups)
    if len(names) < 2:
        raise ValueError('cultural heritability needs >= 2 groups (one group cannot vary '
                         'BETWEEN groups) -- the same reason a class genome needs >= 2 scans')
    for g in names:
        if len(groups[g]) < 2:
            raise ValueError(f'group {g!r} has < 2 individuals; V_within is undefined')

    out = {}
    for ax in axes:
        group_means, within_vars = [], []
        for g in names:
            w = np.array([ind[ax] for ind in groups[g]], dtype=np.float64)
            group_means.append(w.mean())
            within_vars.append(w.var(ddof=1))          # variance among individuals in this group
        v_between = float(np.var(group_means, ddof=1)) # variance of the group means
        v_within = float(np.mean(within_vars))         # typical within-group variance
        denom = v_between + v_within
        h2 = float(v_between / denom) if denom > 1e-12 else 0.0
        out[ax] = {
            'v_between': round(v_between, 5), 'v_within': round(v_within, 5),
            'h2': round(h2, 3),
            'verdict': ('CULTURAL -- a group sample predicts it; design per market'
                        if h2 >= 0.6 else
                        'PERSONAL -- ask the individual; sociology will not predict it'
                        if h2 <= 0.3 else
                        'MIXED -- partly group, partly individual'),
        }
    return out


def fit_individual(pairs, axes=DEFAULT_AXES) -> dict:
    """One person's taste weights from their pairwise comparisons, via the real model.

    pairs: [(phi_winner: dict, phi_loser: dict), ...] -- two designs' physics vectors, winner
    first. Returns {axis: weight}. Thin wrapper over core.preference.PreferenceModel so the
    population layer uses the SAME Bradley-Terry taste model as the single-operator loop.
    """
    from core.preference import PreferenceModel
    m = PreferenceModel()
    m.fit([(a, b) for a, b in pairs])       # fit wants (winner, loser) tuples
    w = m.weights          # @property, not a method
    return {ax: float(w.get(ax, 0.0)) for ax in axes}


def report(groups: dict, axes=DEFAULT_AXES) -> str:
    split = heritability_split(groups, axes)
    lines = [f"  {'axis':16} {'h2':>6}  {'V_between':>10} {'V_within':>10}  verdict"]
    for ax, d in sorted(split.items(), key=lambda kv: -kv[1]['h2']):
        lines.append(f"  {ax:16} {d['h2']:>6.3f}  {d['v_between']:>10.4f} {d['v_within']:>10.4f}"
                     f"  {d['verdict']}")
    return '\n'.join(lines)


def _synthetic_demo(seed: int = 0) -> dict:
    """TWO SYNTHETIC GROUPS with a KNOWN split, to show the machinery recovers it.

    Constructed so:
      punishes_naive  is CULTURAL   -- the two groups have very different group means, tight
                                       within-group spread (group A loves difficulty, B hates it)
      learnability    is PERSONAL   -- same group means, wide within-group spread (everyone
                                       differs, regardless of group)
      skill_gap, headroom  MIXED    -- moderate on both
    A correct implementation must return punishes_naive high-h2, learnability low-h2.
    """
    rng = np.random.default_rng(seed)
    groups = {}
    # (group_mean, within_sd) per axis, per group
    spec = {
        'A': {'punishes_naive': (1.6, 0.10), 'learnability': (0.5, 0.90),
              'skill_gap': (0.8, 0.40), 'headroom': (0.6, 0.45)},
        'B': {'punishes_naive': (-1.2, 0.10), 'learnability': (0.5, 0.90),
              'skill_gap': (0.2, 0.40), 'headroom': (0.9, 0.45)},
    }
    for g, axspec in spec.items():
        inds = []
        for _ in range(12):                            # 12 people per group
            inds.append({ax: float(rng.normal(mu, sd)) for ax, (mu, sd) in axspec.items()})
        groups[g] = inds
    return groups


def _main() -> int:
    import sys
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    print("  TASTE AS A CLASS GENOME -- cultural vs personal, from a SYNTHETIC 2-group demo")
    print("  (built so punishes_naive is CULTURAL and learnability is PERSONAL by construction;")
    print("   a correct split must recover that):\n")
    groups = _synthetic_demo(0)
    print(report(groups))
    print("\n  The machinery is real (reused core.preference + the heritability formula);")
    print("  the DATA is synthetic until real group preferences are elicited per market.")
    return 0


if __name__ == '__main__':
    raise SystemExit(_main())
