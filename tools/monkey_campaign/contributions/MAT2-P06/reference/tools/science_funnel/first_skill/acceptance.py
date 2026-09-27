"""First-skill acceptance: the hard conditions + the frozen ranking.

RULE-0 STATUS: the executable half of run_manifest.json's hard_conditions and
ranking_rule_frozen_now sections. These functions are the ONLY place the hard
conditions live. The reward (reward.py) never reads them; no blended score
exists anywhere in this lane -- each condition is enforced independently, then
the ranking is applied, in that order.

The CoT band is MEASURED, not assumed: the baseline runs first on the identical
protocol, its per-episode CoTs are frozen into the acceptance ledger
(baseline_band), and only then is any policy compared.
"""
from __future__ import annotations

import math

# --- frozen constants (manifest: timing_and_clock, hard_conditions) ---
M_BODY_KG = 13824.5       # the measured membrane inventory at water density
EPISODE_CAP_TICKS = 300   # the walk's own banked end-of-life region
EVAL_WINDOW_TICKS = 270   # 18 x 15; refusals before here are falls
REACH_START_TICK = 60     # the banked entry/settle era ends
INF = float("inf")


def episode_bars(record: dict) -> dict:
    """Reduce one episode record to the frozen bars.

    record fields (the env wrapper's contract):
      seed           eval seed
      refusal_tick   int tick of the engine's own refusal class, or None
      reach_tick     int first tick in the reach window with CoM x past the
                     disc, or None
      distance_m     along-heading CoM displacement achieved by episode end
      work_J         the engine's cumulative mechanical-work ledger at end
    """
    refusal = record.get("refusal_tick")
    fell = refusal is not None and refusal < EVAL_WINDOW_TICKS
    reach = record.get("reach_tick")
    reached = reach is not None and REACH_START_TICK <= reach <= EVAL_WINDOW_TICKS
    t_reach = float(reach) if reached else INF
    dist = float(record.get("distance_m", 0.0))
    work = float(record.get("work_J", 0.0))
    cot = work / (M_BODY_KG * dist) if dist > 0.0 else INF
    return {"seed": record.get("seed"), "fall": fell, "reached": reached,
            "time_to_waypoint": t_reach, "cot": cot}


def run_bars(records: list) -> dict:
    """Aggregate per-episode bars over one eval run (the fixed eval seed set)."""
    bars = [episode_bars(r) for r in records]
    reached_times = [b["time_to_waypoint"] for b in bars if b["reached"]]
    cots = [b["cot"] for b in bars if math.isfinite(b["cot"])]
    return {
        "n": len(bars),
        "reach_rate": sum(1 for b in bars if b["reached"]) / len(bars) if bars else 0.0,
        "no_fall_rate": sum(1 for b in bars if not b["fall"]) / len(bars) if bars else 0.0,
        "median_time_to_waypoint": _median(reached_times) if reached_times else INF,
        "cot_median": _median(cots) if cots else INF,
        "cot_max": max(cots) if cots else INF,
        "per_episode": bars,
    }


def cot_band_ok(policy_run: dict, baseline_run: dict) -> bool:
    """THE FROZEN CoT BAND RULE.

    The band is the baseline's own measured distribution: a policy passes iff
    median(CoT_policy) <= median(CoT_baseline) + (max(CoT_baseline) -
    median(CoT_baseline)) -- not above the baseline's worst measured efficiency.
    With a deterministic engine the spread term may be 0: the bar is then exact
    parity with the baseline's efficiency. Every term measured; none invented.
    """
    if not math.isfinite(baseline_run["cot_median"]):
        return False  # no measured band exists; acceptance cannot proceed
    band_top = (baseline_run["cot_median"]
                + (baseline_run["cot_max"] - baseline_run["cot_median"]))
    return math.isfinite(policy_run["cot_median"]) and policy_run["cot_median"] <= band_top


def first_skill_ranking(policy_run: dict, baseline_run: dict) -> dict:
    """THE FROZEN RANKING (worst training seed's eval run vs the baseline).

    Returns the per-clause verdicts; F-FIRST-SKILL / F-ACCEPTANCE-EXACT pass
    only when every clause holds. Order is always: hard conditions first,
    ranking second -- never blended.
    """
    paired = _paired_times(policy_run, baseline_run)
    clauses = {
        "reach_rate_strictly_greater":
            policy_run["reach_rate"] > baseline_run["reach_rate"],
        "median_time_strictly_less_paired": paired,
        "no_fall_rate_is_one": policy_run["no_fall_rate"] == 1.0,
        "cot_within_measured_band": cot_band_ok(policy_run, baseline_run),
    }
    clauses["all"] = all(clauses.values())
    return clauses


def _paired_times(policy_run: dict, baseline_run: dict) -> bool:
    """Paired time-to-waypoint comparison by eval seed.

    Policy median over reached episodes must be strictly below the baseline's
    median over the same paired episodes; both-INF pairs are excluded; an INF
    (no reach) on the policy side can never win a pair.
    """
    p = {b["seed"]: b["time_to_waypoint"] for b in policy_run["per_episode"]}
    b = {b["seed"]: b["time_to_waypoint"] for b in baseline_run["per_episode"]}
    pairs = [(p[s], b[s]) for s in sorted(set(p) & set(b))]
    decided = [(pt, bt) for pt, bt in pairs if math.isfinite(pt) or math.isfinite(bt)]
    if not decided:
        return False
    p_times = sorted(pt for pt, _ in decided if math.isfinite(pt))
    b_times = sorted(bt for _, bt in decided if math.isfinite(bt))
    if not p_times or not b_times:
        return False
    return _median(p_times) < _median(b_times)


def _median(xs: list) -> float:
    xs = sorted(xs)
    n = len(xs)
    if n == 0:
        return INF
    mid = n // 2
    return xs[mid] if n % 2 else 0.5 * (xs[mid - 1] + xs[mid])
