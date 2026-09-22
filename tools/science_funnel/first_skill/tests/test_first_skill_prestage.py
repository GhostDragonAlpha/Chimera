"""First-skill prestage tests. Every test names the falsifier or frozen clause
it guards (Rule 0: a test that names no falsifier is not registered).

Falsifier linkage:
  test_manifest_*        -> the run manifest's frozen fields (Rule 0 prereg:
                            no field may drift before the first tick lands)
  test_reward_*          -> the shaping stays normalized O(1) and subordinate
                            (the contradictory-reward disease; training_gate)
  test_baseline_*        -> the baseline is the BANKED schedule, action-interface
                            identical to the policy (F-FIRST-SKILL's comparison
                            is only honest if the interface matches)
  test_acceptance_*      -> hard conditions enforced independently + the frozen
                            ranking (F-ACCEPTANCE-EXACT / F-FIRST-SKILL)
  test_p3_manifest_*     -> the skill-1 manifest shape validates through P3's
                            frozen loader with ZERO amendments (F-EXPORT-VALID)
"""
import copy
import json
import math
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1]          # .../tools/science_funnel/first_skill
SF_DIR = HERE.parent                                 # .../tools/science_funnel
ROOT = SF_DIR.parent.parent                          # repo root
sys.path.insert(0, str(SF_DIR))
sys.path.insert(0, str(HERE))

import acceptance  # noqa: E402
import baseline_controller  # noqa: E402
import reward  # noqa: E402

MANIFEST_PATH = ROOT / "tools/science_funnel/validation/first_skill_prestage_20260922/run_manifest.json"


def _manifest():
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- manifest ---
def test_manifest_frozen_fields_present():
    m = _manifest()
    assert m["algorithm"]["name"] == "PPO"
    assert m["algorithm"]["num_envs"] == 4096
    assert m["seeds"]["training"] == [20260922, 20260923, 20260924]
    assert len(m["seeds"]["eval_set"]) == 5
    assert m["curriculum"].startswith("NONE")
    for f in ("F-FIRST-SKILL", "F-EXPORT-VALID", "F-ACCEPTANCE-EXACT"):
        assert f in m["rule_0"]["falsifiers_declared_before_any_training_exists"]
    sel = m["checkpoint_selection_frozen_now"]
    assert "every 25,000 decisions" in sel["eval_cadence"]
    assert "LAST 10%" in sel["selection_rule"] and "EARLIEST" in sel["selection_rule"]


def test_manifest_budget_arithmetic_closes():
    m = _manifest()
    alg = m["algorithm"]
    assert alg["num_envs"] * alg["steps_per_env"] == alg["decisions_per_iteration"]
    assert alg["decisions_per_iteration"] * alg["iterations"] == alg["budget_decisions_per_seed"]
    assert alg["budget_decisions_per_seed"] <= 1_000_000
    clk = m["timing_and_clock"]
    assert clk["policy_hz"] * clk["hold_ticks"] == clk["physics_hz"] == 300


def test_manifest_frozen_numbers_match_banked_receipts():
    m = _manifest()
    assert m["hard_conditions"]["cot_within_band"]["definition"]  # mass/denominator declared
    assert "13824.5" in m["hard_conditions"]["cot_within_band"]["definition"]
    wp = m["task"]["waypoint"]
    assert abs(wp["d_wp_m"] - 0.5) < 1e-12
    # reach disc == one decision of seed-speed travel
    assert abs(m["task"]["reach_disc_radius_m"] - reward.PROGRESS_QUANTUM) < 1e-9
    assert abs(reward.PROGRESS_QUANTUM - reward.V_SEED * reward.T_DECISION) < 1e-12


def test_manifest_hard_conditions_absent_from_reward():
    """The reward module defines exactly the two shaping terms and nothing else:
    no alive/terminal/effort function exists to call."""
    m = _manifest()
    assert "NO terminal success/failure term" in m["reward_frozen"]["excluded"][1]
    assert "NO alive bonus" in m["reward_frozen"]["excluded"][0]
    expected = ["derived_w_head", "progress_quantum", "r_heading", "r_progress",
                "shaping", "subordination_ok"]
    public = [n for n in dir(reward) if not n.startswith("_")
              and callable(getattr(reward, n))
              and getattr(getattr(reward, n), "__module__", "") == reward.__name__]
    assert sorted(public) == expected, public


# ------------------------------------------------------------------ reward ---
def test_reward_normalized_o1_at_seed_speed():
    """At the banked seed speed the progress term reads exactly +1/decision."""
    step = reward.V_SEED * reward.T_DECISION
    assert reward.r_progress(0.0, step) == pytest.approx(1.0, abs=1e-12)
    for d in (-3.0, -0.5, 0.5, 3.0):  # clip holds for any displacement
        assert -1.0 <= reward.r_progress(0.0, d * step) <= 1.0


def test_reward_heading_bounds_and_alignment():
    assert reward.r_heading(1.0, 0.0) == 0.0                    # dead aligned
    lo, hi = -2.0 * reward.W_HEAD, 0.0
    for vx, vy in [(1.0, 1.0), (0.0, 1.0), (-1.0, 0.0), (1.0, -2.0)]:
        assert lo - 1e-12 <= reward.r_heading(vx, vy) <= hi + 1e-12
    assert reward.r_heading(0.0, 0.0) == 0.0                    # stopped: aligned by convention


def test_reward_subordination_inequality_derived():
    """W_HEAD is the largest declared candidate that cannot outweigh reaching."""
    assert reward.derived_w_head() == 0.1 == reward.W_HEAD
    assert reward.subordination_ok(0.1)
    assert not reward.subordination_ok(0.2)
    # the inequality's own arithmetic, spelled out
    assert 2 * 0.1 * 20 <= (1 / 3) * (0.5 / reward.PROGRESS_QUANTUM)
    assert 2 * 0.2 * 20 > (1 / 3) * (0.5 / reward.PROGRESS_QUANTUM)


def test_reward_is_exactly_the_two_terms():
    r = reward.shaping(0.0, reward.PROGRESS_QUANTUM / 2, 1.0, 1.0)
    assert r == pytest.approx(reward.r_progress(0.0, reward.PROGRESS_QUANTUM / 2)
                              + reward.r_heading(1.0, 1.0), abs=1e-15)


# ---------------------------------------------------------------- baseline ---
def test_baseline_is_the_banked_fixed_schedule():
    c = baseline_controller.BaselineController()
    assert c.schedule_fingerprint == "baseline_constant_hold_v=0.600000@tick0"
    assert baseline_controller.V_HOLD == 0.60  # the banked R2 value
    first = c.decide(0)
    assert first == {"commanded_target_velocity_x": 0.60}
    for t in (15, 150, 285):                   # ZOH: identical payload every decision
        assert c.decide(t) == first


def test_baseline_reads_nothing_and_interface_matches_policy():
    """Action-interface identity: the baseline emits the same single adapter
    channel the policy's mapping emits -- the comparison isolates learning."""
    c = baseline_controller.BaselineController()
    obs = [0.123] * 82
    goal = {"dist": 0.4}
    assert c.decide(0, obs=obs, goal=goal) == c.decide(0)
    c.reset()
    assert c._issued is False and c.decide(0)["commanded_target_velocity_x"] == 0.60


def test_baseline_value_inside_measured_envelope():
    assert 0.0 <= baseline_controller.V_HOLD <= reward.V_SEED  # banked [0, 0.7636] envelope


# --------------------------------------------------------------- acceptance --
def _ep(seed=1, refusal=None, reach=None, dist=0.4, work=2e5):
    return {"seed": seed, "refusal_tick": refusal, "reach_tick": reach,
            "distance_m": dist, "work_J": work}


def test_acceptance_fall_classification():
    assert acceptance.episode_bars(_ep(refusal=269))["fall"] is True
    assert acceptance.episode_bars(_ep(refusal=270))["fall"] is False  # boundary: 270 is alive
    assert acceptance.episode_bars(_ep(refusal=None))["fall"] is False


def test_acceptance_reach_window_boundaries():
    assert acceptance.episode_bars(_ep(reach=60))["reached"] is True
    assert acceptance.episode_bars(_ep(reach=270))["reached"] is True
    assert acceptance.episode_bars(_ep(reach=59))["reached"] is False
    assert acceptance.episode_bars(_ep(reach=271))["reached"] is False
    assert acceptance.episode_bars(_ep(reach=None))["time_to_waypoint"] == acceptance.INF


def test_acceptance_cot_computation():
    b = acceptance.episode_bars(_ep(dist=0.4, work=2e5))
    assert b["cot"] == pytest.approx(2e5 / (acceptance.M_BODY_KG * 0.4), rel=1e-12)
    assert acceptance.episode_bars(_ep(dist=0.0, work=2e5))["cot"] == acceptance.INF


def _runs(baseline_cot=10.0, policy_cot=10.0, spread=0.0,
          base_reach=0.8, pol_reach=1.0, base_t=250.0, pol_t=240.0,
          pol_nofall=1.0, n=5):
    def run(reach_rate, t, cot, nofall):
        k = round(reach_rate * n)
        eps = []
        for i in range(n):
            reached = i < k
            fell = i >= round(nofall * n)   # no_fall_rate == nofall by construction
            eps.append({"seed": i, "fall": fell, "reached": reached,
                        "time_to_waypoint": t if reached else acceptance.INF,
                        "cot": cot})
        return {"n": n, "reach_rate": reach_rate,
                "no_fall_rate": sum(0 if e["fall"] else 1 for e in eps) / n,
                "median_time_to_waypoint": t if k else acceptance.INF,
                "cot_median": cot, "cot_max": cot + spread,
                "per_episode": eps}
    return run(base_reach, base_t, baseline_cot, 1.0), run(pol_reach, pol_t, policy_cot, pol_nofall)


def test_acceptance_ranking_all_clauses():
    base, pol = _runs()
    v = acceptance.first_skill_ranking(pol, base)
    assert v == {"reach_rate_strictly_greater": True,
                 "median_time_strictly_less_paired": True,
                 "no_fall_rate_is_one": True,
                 "cot_within_measured_band": True, "all": True}


def test_acceptance_ranking_each_clause_can_fail():
    cases = [
        (_runs(pol_reach=0.8)[1], "reach_rate_strictly_greater"),
        (_runs(pol_t=250.0)[1], "median_time_strictly_less_paired"),
        (_runs(pol_nofall=0.6)[1], "no_fall_rate_is_one"),
        (_runs(policy_cot=10.5, spread=0.0)[1], "cot_within_measured_band"),
    ]
    for pol, failing in cases:
        base, _ = _runs()
        v = acceptance.first_skill_ranking(pol, base)
        assert v[failing] is False and v["all"] is False, failing


def test_acceptance_cot_band_is_measured_not_assumed():
    base, pol = _runs(baseline_cot=10.0, policy_cot=11.0, spread=2.0)
    assert acceptance.cot_band_ok(pol, base) is True   # inside the measured band
    base2, pol2 = _runs(baseline_cot=10.0, policy_cot=13.0, spread=2.0)
    assert acceptance.cot_band_ok(pol2, base2) is False  # above the baseline's worst
    assert acceptance.cot_band_ok(pol, {"cot_median": acceptance.INF}) is False  # no band, no pass


def test_acceptance_paired_comparison_excludes_double_inf():
    base, pol = _runs(base_reach=0.0, pol_reach=0.0)
    v = acceptance.first_skill_ranking(pol, base)
    assert v["median_time_strictly_less_paired"] is False  # nobody reached: no win


# ----------------------------------------------------------- P3 compatibility ---
def test_p3_manifest_validator_accepts_skill1_shape_zero_amendments():
    """F-EXPORT-VALID prerequisite: the skill-1 manifest shape passes P3's frozen
    validator (1b6d7749 harness) with zero amendments."""
    sys.path.insert(0, str(SF_DIR / "typeb_export"))
    import policy_manifest as pm
    from observation_schema import FIELDS, OBS_DIM

    assert OBS_DIM == 80
    order = [f["name"] for f in FIELDS] + ["goal_dist_norm", "goal_closing_speed_norm"]
    assert len(order) == 82 and len(set(order)) == 82
    assert all(f["privileged"] is False for f in FIELDS)
    arch = [82, 128, 128, 1]
    manifest = {
        "manifest_version": pm.MANIFEST_VERSION,
        "kind": "typeb_policy_manifest",
        "claim": "first-skill flat-ground goal tracking",
        "named_falsifiers": ["F-CPU-POLICY-BYTES", "F-INFERENCE-BUDGET",
                             "F-FIRST-SKILL", "F-EXPORT-VALID", "F-ACCEPTANCE-EXACT"],
        "cpu_reference": {"commit": "73f3a860"},
        "horizon_and_ticks": {"physics_hz": 300, "episode_cap_ticks": 300},
        "scene_and_receipts": {"scene": "first_skill flat ground"},
        "body": {"digest": "BOUND_AT_EXPORT"},
        "reflex_set": {"version": "wave38-banked-reflex/1.0.0"},
        "physics_version": "BOUND_AT_EXPORT",
        "observation": {
            "dim": 82, "order": order, "privileged_forbidden": True,
            "per_field": {n: {"privileged": False} for n in order},
        },
        "normalization": {"mean": [], "std": [1.0] * 82},
        "action": {
            "dim": 1, "bounds_lo": [0.0],
            "bounds_hi": [reward.V_SEED], "scale": [reward.V_SEED / 2.0],
            "center": [reward.V_SEED / 2.0],
            "clock": {"policy_hz": 20, "hold_ticks": 15, "physics_hz": 300},
        },
        "policy": {
            "architecture": arch, "activation": "tanh", "weights_format": "npz",
            "weights_sha256": "0" * 64, "param_count": 82 * 128 + 128 + 128 * 128 + 128 + 128 + 1,
            "mac_count": 82 * 128 + 128 * 128 + 128, "seed": 20260922,
            "training_backend": "rsl_rl PPO (staged; BOUND_AT_EXPORT)",
        },
        "inference": {"recipe": "numpy float32"},
        "reset": {"semantics": "seed entry state"},
        "evaluation": {"eval_seeds": [20260922, 20260923, 20260924, 20260925, 20260926]},
        "receipts": [],
    }
    errs = pm.validate_manifest(manifest, weights_bytes=None)
    assert errs == [], errs


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
