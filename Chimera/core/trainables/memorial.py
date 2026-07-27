"""memorial — the star brightness curve, as a trainable domain.

CWM rung 1 (docs/THE_COMPOSITIONAL_WORLD_MODEL.md §4, the UStarMemorialSubsystem row).
Design Law 2, stated as perceptual physics: "the bad ending is a costless life...
taught only through consequence." That consequence has to be SEEN, so this module
trains the two data tables that decide whether a player can see it:

    STAR = dict(brightness_k=..., bright_lights_yard=...)   the 1-exp(-w/k) curve
    SACRIFICE_WEIGHTS = {8 kinds -> weight}                 what each sacrifice costs

Both are grepped verbatim from CHIMERA_VISION.py (lines ~3141, ~3153, ~3760, ~3816) —
never invented. The curve itself:

    brightness(w) = 1 - exp(-w / brightness_k)
    ending        = COSTLESS_LIFE if w <= 0
                    else BRIGHT_STAR if brightness(w) >= bright_lights_yard
                    else QUIET_STAR
    NightLightLevel = min(0.5, sum(brightness of stars >= bright_lights_yard) * 0.18)

THIS MODULE REPORTS FACTS, NOT OPINIONS. It never says a costless life SHOULD be
dim — it measures whether, under the genome it was handed, a costless life IS dim,
whether distinct playstyles produce discriminable stars, and whether the night-light
budget behaves. What GOOD means lives in docs/objectives/memorial.json, written by
the LLM from Law 2 as a physics statement, never a target weight.

THE SIMULATED PLAYER: not one scripted life — an honest SPREAD of three archetypes,
named directly from CWM §4's own language for this row: COSTLESS (plays the
self-interested, profitable option and almost never sacrifices), QUIET (sacrifices
sometimes, mostly the smaller acts), GENEROUS (sacrifices often, including the
costly acts). Each life is a stochastic process over decision points, not a fixed
script — one life is a coin toss (TRAINING_PROTOCOL.md §3.5: "one rollout is a coin
toss, not a measurement"); a POPULATION of them, fixed-seeded for determinism
(creature.py / attunement.py convention: EVAL_SEED so genome -> measurement is not
simulator noise), is what turns that coin toss into a measurement.
"""

from __future__ import annotations

import bisect
import copy
import math
import random

# --- sim settings (NOT genome: these are the test conditions, not the game) ----
DECISIONS_PER_LIFE = 16        # sacrifice-shaped opportunities across one generation
POP_PER_TIER = 200              # lives sampled per playstyle archetype -> tier stats
N_LINEAGES = 80                 # independent star-memorial yards (Monte Carlo over lineages)
GENERATIONS_PER_LINEAGE = 16     # heirs per lineage before reading NightLightLevel
EVAL_SEED = 11                   # fixed: genome -> measurement must be deterministic

KINDS = ("REFUSED_PROFIT", "GAVE_CARGO", "GAVE_O2", "SPENT_TIME_UNPAYABLE",
         "TOOK_RISK_FOR_OTHER", "BURIED_STRANGER", "WEAPON_NEVER_FIRED",
         "HEIRLOOM_GIVEN")

# Per-decision firing probability of EACH kind, by archetype (NOT genome — these are
# the test conditions, i.e. how "generous" plays, not what a sacrifice IS worth).
# Not firing = the profitable / self-interested choice, which is why COSTLESS is
# almost entirely zero, by construction of the archetype, not the curve.
_RATES = {
    "costless": {"REFUSED_PROFIT": 0.010, "GAVE_CARGO": 0.004, "GAVE_O2": 0.000,
                 "SPENT_TIME_UNPAYABLE": 0.003, "TOOK_RISK_FOR_OTHER": 0.000,
                 "BURIED_STRANGER": 0.000, "WEAPON_NEVER_FIRED": 0.002,
                 "HEIRLOOM_GIVEN": 0.000},
    "quiet":    {"REFUSED_PROFIT": 0.160, "GAVE_CARGO": 0.090, "GAVE_O2": 0.020,
                 "SPENT_TIME_UNPAYABLE": 0.070, "TOOK_RISK_FOR_OTHER": 0.030,
                 "BURIED_STRANGER": 0.015, "WEAPON_NEVER_FIRED": 0.060,
                 "HEIRLOOM_GIVEN": 0.000},
    "generous": {"REFUSED_PROFIT": 0.150, "GAVE_CARGO": 0.120, "GAVE_O2": 0.065,
                 "SPENT_TIME_UNPAYABLE": 0.100, "TOOK_RISK_FOR_OTHER": 0.080,
                 "BURIED_STRANGER": 0.042, "WEAPON_NEVER_FIRED": 0.075,
                 "HEIRLOOM_GIVEN": 0.016},
}
TIERS = ("costless", "quiet", "generous")

# cumulative thresholds per tier, precomputed once — bisect turns each decision's
# categorical draw into O(log 8) instead of a linear scan.
_CUM = {}
for _tier, _rates in _RATES.items():
    _acc, _c = 0.0, []
    for _kind in KINDS:
        _acc += _rates[_kind]
        _c.append(_acc)
    assert _acc <= 1.0 + 1e-9, f"{_tier} per-decision rates sum > 1.0"
    _CUM[_tier] = _c

# the honest POPULATION mix behind one memorial lineage — a design fact about how
# many players land where (this studio would tune it from telemetry, not guess);
# it is NOT a taste claim about what any single weight should be.
_POPULATION_MIX = {"costless": 0.20, "quiet": 0.50, "generous": 0.30}
_MIX_CUM = []
_acc = 0.0
for _tier in TIERS:
    _acc += _POPULATION_MIX[_tier]
    _MIX_CUM.append(_acc)


def seed() -> dict:
    """The live values, verbatim from CHIMERA_VISION.py:
    STAR = dict(brightness_k=6.0, bright_lights_yard=0.75)         (line 3153)
    SACRIFICE_WEIGHTS = {...8 kinds...}                            (line 3141)
    """
    return {
        "brightness_k": 6.0,
        "bright_lights_yard": 0.75,
        "weights": {
            "REFUSED_PROFIT": 1.0, "GAVE_CARGO": 1.5, "GAVE_O2": 3.0,
            "SPENT_TIME_UNPAYABLE": 2.0, "TOOK_RISK_FOR_OTHER": 2.5,
            "BURIED_STRANGER": 3.5, "WEAPON_NEVER_FIRED": 2.0, "HEIRLOOM_GIVEN": 5.0,
        },
    }


def mutate(g: dict, rng: random.Random) -> dict:
    """Every locus jittered UNCONDITIONALLY, every call — no dead genes
    (TRAINING_PROTOCOL.md §6: a locus mutation cannot reach is a locus that does
    not exist; the seg_taper trap was 'only jitter if already > 0' on a zero seed).
    All ten loci here start non-zero, so plain multiplicative jitter reaches
    every one of them from generation zero."""
    d = copy.deepcopy(g)

    def jit(v, frac, lo, hi):
        return max(lo, min(hi, v * (1.0 + rng.uniform(-frac, frac))))

    # curve steepness. Too small -> even a trivial sacrifice saturates near max
    # brightness (nothing stays dim); too large -> even HEIRLOOM_GIVEN alone can
    # never cross bright_lights_yard (nothing ever shines). Bounds are generous
    # on both sides so the optimiser can find the failure, not just avoid it.
    d["brightness_k"] = jit(d["brightness_k"], 0.25, 1.0, 20.0)

    # the visibility threshold. Clamped off both rails: >=1 is unreachable (never
    # bright), <=0 is free (always bright) — either would erase Law 2's
    # distinction by construction, not by evidence, so neither is in the search
    # space as an achievable "solution".
    d["bright_lights_yard"] = jit(d["bright_lights_yard"], 0.20, 0.05, 0.95)

    # every sacrifice weight, unconditionally — a sacrifice must cost something
    # positive or it is not a sacrifice; the upper bound keeps one act from
    # swallowing the whole scale (the lollipop's shape, one locus up).
    for k in d["weights"]:
        d["weights"][k] = jit(d["weights"][k], 0.25, 0.1, 12.0)

    return d


def _brightness(w: float, k: float) -> float:
    return 1.0 - math.exp(-max(0.0, w) / max(k, 1e-6))


def _life_weight(tier: str, weights: dict, rng: random.Random) -> float:
    """One simulated life of one playstyle archetype: DECISIONS_PER_LIFE independent
    opportunities, each either passed over (the profitable, self-interested choice)
    or spent on exactly one sacrifice kind, drawn from the archetype's own rates.
    TOTAL: a bounded `for`, never a `while` — no genome can hang the trainer."""
    cum = _CUM[tier]
    w = 0.0
    for _ in range(DECISIONS_PER_LIFE):
        idx = bisect.bisect_right(cum, rng.random())
        if idx < len(KINDS):
            w += weights[KINDS[idx]]
    return w


def _draw_tier(rng: random.Random) -> str:
    idx = bisect.bisect_right(_MIX_CUM, rng.random())
    return TIERS[min(idx, len(TIERS) - 1)]


def measure(g: dict) -> dict:
    """FACTS about the trained curve + weight table, from an honest population of
    simulated lives — never one scripted playthrough (TRAINING_PROTOCOL.md §3.5).
    Fixed EVAL_SEED makes genome -> measurement deterministic, so the trainer
    climbs the objective, not the simulator's own noise."""
    rng = random.Random(EVAL_SEED)
    k = g["brightness_k"]
    yard = g["bright_lights_yard"]
    weights = g["weights"]

    # --- 1) tier statistics: costless / quiet / generous -----------------------
    all_pairs = []          # (weight, brightness) across every simulated life
    tier_mean_b, tier_dim_frac, tier_bright_frac = {}, {}, {}
    for tier in TIERS:
        bs = []
        for _ in range(POP_PER_TIER):
            w = _life_weight(tier, weights, rng)
            b = _brightness(w, k)
            bs.append(b)
            all_pairs.append((w, b))
        n = len(bs)
        tier_mean_b[tier] = sum(bs) / n
        tier_dim_frac[tier] = sum(1 for b in bs if b < yard) / n
        tier_bright_frac[tier] = sum(1 for b in bs if b >= yard) / n

    sep_cq = tier_mean_b["quiet"] - tier_mean_b["costless"]
    sep_qg = tier_mean_b["generous"] - tier_mean_b["quiet"]
    min_tier_separation = min(sep_cq, sep_qg)

    # --- 2) per-kind discriminability: 8 distinct weights, isolated ------------
    kind_b = sorted(_brightness(weights[kd], k) for kd in KINDS)
    uniq = sorted({round(x, 9) for x in kind_b})
    min_kind_gap = min((b2 - b1 for b1, b2 in zip(uniq, uniq[1:])), default=0.0)

    # --- 3) monotonicity: more sacrifice must never read as a DIMMER star ------
    all_pairs.sort(key=lambda p: p[0])
    violations = sum(1 for (w1, b1), (w2, b2) in zip(all_pairs, all_pairs[1:])
                     if w2 > w1 + 1e-9 and b2 < b1 - 1e-9)

    # --- 4) NightLightLevel vs its 0.5 cap, over independent lineages ----------
    finals = []
    zero_ct = at_cap_ct = 0
    for _ in range(N_LINEAGES):
        stars = []
        for _ in range(GENERATIONS_PER_LINEAGE):
            tier = _draw_tier(rng)
            w = _life_weight(tier, weights, rng)
            stars.append(_brightness(w, k))
        level = min(0.5, sum(b for b in stars if b >= yard) * 0.18)
        finals.append(level)
        if level <= 1e-9:
            zero_ct += 1
        if level >= 0.5 - 1e-6:
            at_cap_ct += 1
    n_lin = len(finals)

    return {
        "min_tier_separation": min_tier_separation,
        "min_kind_gap": min_kind_gap,
        "frac_dim_costless": tier_dim_frac["costless"],
        "frac_bright_generous": tier_bright_frac["generous"],
        "monotonicity_violations": float(violations),
        "night_light_final_mean": sum(finals) / n_lin,
        "night_light_zero_frac": zero_ct / n_lin,
        "night_light_at_cap_frac": at_cap_ct / n_lin,
        # reported so a winner can be READ, never optimised against
        "brightness_k": float(k),
        "bright_lights_yard": float(yard),
        "mean_costless_brightness": tier_mean_b["costless"],
        "mean_quiet_brightness": tier_mean_b["quiet"],
        "mean_generous_brightness": tier_mean_b["generous"],
    }
