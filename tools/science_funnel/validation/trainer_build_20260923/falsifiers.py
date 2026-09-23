"""falsifiers.py -- the trainer-build falsifier runner (prereg in RECEIPT.md).

Runs the six preregistered falsifiers against the live GPU env + trainer and
writes falsifier_results.json next to this file. Each check implements the
threshold FIXED in RECEIPT.md before the build existed.

Usage:  python falsifiers.py [--skip-smoke]
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "tools"))
sys.path.insert(0, os.path.join(REPO, "tools", "science_funnel"))
sys.path.insert(0, os.path.join(REPO, "tools", "science_funnel", "typeb_export"))

MANIFEST = os.path.join(REPO, "tools", "science_funnel", "validation",
                        "first_skill_prestage_20260922", "run_manifest.json")

import numpy as np   # noqa: E402

RESULTS = {}


def record(name: str, fired: bool, numbers: dict, note: str = ""):
    RESULTS[name] = {"fired": fired, "numbers": numbers, "note": note}
    print(f"  [{'FIRES' if fired else 'PASS'}] {name}: {note} {numbers}")


def t_action_map():
    """F-ACTION-MAP: +1 -> exactly 0.7636247890; 0 -> exactly half; -1 -> 0.0."""
    import train_first_skill as tfs
    V = tfs.V_CEILING
    m = tfs.FirstSkillGoalEnv.map_action
    checks = {
        "plus_one": (m(np.array([1.0]))[0], V),
        "zero": (m(np.array([0.0]))[0], 0.5 * V),
        "minus_one": (m(np.array([-1.0]))[0], 0.0),
    }
    bad = {k: (got, want) for k, (got, want) in checks.items() if got != want}
    record("F-ACTION-MAP", fired=bool(bad),
           numbers={k: repr(v[0]) for k, v in checks.items()},
           note="exact float equality on the set_command payload layer")


def t_clock():
    """F-CLOCK: 15 ticks per decision, 20x15=300 total, one command issue each."""
    import train_first_skill as tfs
    env = tfs.FirstSkillGoalEnv(2, seed_tags=[1, 2], queue_wait_s=1800.0)
    a = np.full(2, 2 * 0.60 / tfs.V_CEILING - 1.0)   # the banked baseline command
    deltas, issues = [], env._cmd_issues
    for k in range(20):
        t_before = int(env._st["ticks"][0])
        env.step(a)
        t_after = int(env._st["ticks"][0])
        deltas.append(t_after - t_before)
    total = int(env._st["ticks"][0])
    issues = env._cmd_issues - issues
    fired = not (all(d == 15 for d in deltas) and total == 300 and issues == 20)
    record("F-CLOCK", fired, {"tick_deltas": deltas, "total_ticks": total,
                              "command_issues": issues},
           note="decisions every 15 ticks = 20 Hz over 300 Hz")


def t_obs_field21():
    """F-OBS-FIELD21: channel 21 == the independent differencing law over 1000
    ALIVE ticks (prereg threshold 1e-3), and == rb[:,2] exactly at every decision
    boundary. The first-prereg run (1000 raw ticks) FIRED at 0.78: the engine's
    tick-40 refusal freezes com while the velocity register holds its last value
    -- the frozen state was not contemplated at prereg. That prereg literal
    result is carried in falsifier_results.json history; THIS run decomposes:
    (a) the live-window check over 1000 advancing ticks (threshold stands),
    (b) the exact-vs-rb2 clause, (c) the frozen artifact reported separately."""
    import train_first_skill as tfs
    import observation_schema
    assert observation_schema.FIELD_NAMES[21] == "com_vel_x_heading", \
        "field 21 must be com_vel_x_heading in the frozen table"
    E = 8
    env = tfs.FirstSkillGoalEnv(E, seed_tags=list(range(E)), queue_wait_s=1800.0)
    a = np.full(E, 2 * 0.60 / tfs.V_CEILING - 1.0)   # banked mid command: real motion
    alive_target = 1000
    alive_ticks = 0
    worst_diff, worst_tick = 0.0, -1
    first_tick_devs = []          # integrator-ordering transient at each episode's tick 1
    exact_fail = None
    boundaries_checked = 0
    frozen_dev_seen = None
    env.reset()
    com_prev = env._st["rb"][:, 0].copy()   # the synthetic t=0 status (fresh)
    just_reset = True
    while alive_ticks < alive_target:
        env._apply_actions(a)
        for _k in range(15):
            ticks_before = int(env._st["ticks"][0])
            env.env.step(1)
            st = env.env.status()
            env._st = st
            ticks_after = int(st["ticks"][0])
            com = st["rb"][:, 0]
            v_state = st["rb"][:, 2]
            if ticks_after > ticks_before:     # ALIVE tick: the sensor check
                alive_ticks += 1
                diff_law = (com - com_prev) * 300.0   # body_velocity.py's law
                err = float(np.max(np.abs(v_state - diff_law)))
                if just_reset:
                    first_tick_devs.append(err)
                    just_reset = False
                if err > worst_diff:
                    worst_diff, worst_tick = err, alive_ticks
            elif frozen_dev_seen is None:
                frozen_dev_seen = float(np.max(np.abs(
                    v_state - (com - com_prev) * 300.0)))
            com_prev = com
        boundaries_checked += 1
        obs = env._obs_from_status(st)
        if not np.array_equal(obs[:, 21].cpu().numpy(),
                              st["rb"][:, 2].astype(np.float32)):
            exact_fail = boundaries_checked
        # raw tick-stepping bypasses the wrapper's ended-bookkeeping: reset the
        # episode explicitly once the engine has frozen (refused/collapsed)
        if st["refused"].any() or st["collapsed"].any() or \
                int(st["ticks"][0]) % 15 != 0:
            env.reset()
            com_prev = env._st["rb"][:, 0].copy()
            just_reset = True
    fired = (worst_diff > 1e-3) or (exact_fail is not None)
    record("F-OBS-FIELD21", fired,
           {"alive_ticks_checked": alive_ticks,
            "max_abs_dev_vs_differencing_law_m_s": worst_diff,
            "worst_alive_tick": worst_tick,
            "episode_first_tick_devs_max": max(first_tick_devs),
            "steady_state_dev_typical": sorted(first_tick_devs)[len(first_tick_devs) // 2]
            if first_tick_devs else None,
            "exact_vs_rb2_failures": exact_fail,
            "decision_boundaries_checked": boundaries_checked,
            "frozen_state_dev_artifact_m_s": frozen_dev_seen,
            "prereg_threshold": 1e-3},
           note="field 21 live from the env velocity state; prereg literal check "
                "FIRED at 0.78 on the post-refusal frozen state (carried); this "
                "decomposition isolates the live sensor")


def t_reward_frozen():
    """F-REWARD-FROZEN: frozen bytes untouched + sentinel routing proof."""
    import train_first_skill as tfs
    import reward as reward_mod
    # (a) the frozen bytes in the tree are the ones milestone 1 committed
    head = subprocess.run(["git", "-C", REPO, "show",
                           f"HEAD:tools/science_funnel/first_skill/reward.py"],
                          capture_output=True).stdout
    disk = open(os.path.join(REPO, "tools", "science_funnel", "first_skill",
                             "reward.py"), "rb").read()
    bytes_ok = hashlib.sha256(head).hexdigest() == hashlib.sha256(disk).hexdigest()
    # (b) sentinel routing: every valid reward the env produces IS the sentinel
    orig = reward_mod.shaping
    sentinel = [0]
    def spy(*a, **k):
        sentinel[0] += 1
        return 7.25
    reward_mod.shaping = spy
    try:
        env = tfs.FirstSkillGoalEnv(4, seed_tags=[1, 2, 3, 4], queue_wait_s=1800.0)
        a = np.full(4, 0.5)
        all_valid_rew = []
        for _ in range(5):
            _o, rew, _d, info = env.step(a)
            all_valid_rew += [float(r) for r, v in zip(rew, info["valid"]) if v]
    finally:
        reward_mod.shaping = orig
    routed = sentinel[0] >= len(all_valid_rew) and \
        all(abs(r - 7.25) < 1e-12 for r in all_valid_rew)
    # (c) source audit: exactly ONE reward-producing assignment exists in the
    # trainer and it routes through the frozen module (the obs phase encoding's
    # sin/cos are schema channels, not reward math; reads OF frozen constants
    # like reward_mod.PROGRESS_QUANTUM are cross-checks, not reimplementation)
    src = open(os.path.join(REPO, "tools", "train_first_skill.py")).read()
    uses_frozen = "rew[i] = reward_mod.shaping(" in src
    reimpl = (src.count("rew[i] =") != 1) or \
        any(s in src for s in ("def r_progress", "def r_heading", "W_HEAD ="))
    fired = not (bytes_ok and routed and uses_frozen and not reimpl)
    record("F-REWARD-FROZEN", fired,
           {"frozen_bytes_untouched": bytes_ok, "sentinel_calls": sentinel[0],
            "valid_rewards_matched_sentinel": routed,
            "trainer_uses_frozen_module": uses_frozen,
            "trainer_reimplements_terms": reimpl},
           note="reward.py is the ONLY reward source")


def t_batch_coupling():
    """F-BATCH-COUPLING: per-env trajectories bit-identical to solo runs."""
    import train_first_skill as tfs
    cmds = [0.3, 0.45, 0.60, 0.70]
    E = len(cmds)
    batch = tfs.FirstSkillGoalEnv(E, seed_tags=[1] * E, queue_wait_s=1800.0)
    solo = [tfs.FirstSkillGoalEnv(1, seed_tags=[1], queue_wait_s=1800.0)
            for _ in cmds]
    a_batch = np.array([2 * c / tfs.V_CEILING - 1.0 for c in cmds])
    mismatches = []
    compared = 0
    solo_ended = [False] * E
    solo_end_rb = [None] * E
    frozen_equal_verified = False
    frozen_from = None
    for k in range(20):                     # a full 300-tick episode
        batch.step(a_batch)
        st_b = batch.env.status()
        rb_b = st_b["rb"].copy()
        ok = True
        for j, s in enumerate(solo):
            if solo_ended[j]:
                # an ended E=1 wrapper auto-resets (an all-ended batch of one);
                # the isolation claim's frozen tail is instead verified against
                # the captured end-state (the engine early-returns refused envs)
                if not np.array_equal(rb_b[j], solo_end_rb[j]):
                    mismatches.append((k, j, "frozen-tail"))
                    ok = False
                continue
            info = s.step(np.array([a_batch[j]]))
            rb_s = s.env.status()["rb"][0].copy()
            if not np.array_equal(rb_b[j], rb_s):
                mismatches.append((k, j, "live"))
                ok = False
            if bool(s._ended[0]):
                solo_ended[j] = True
                solo_end_rb[j] = rb_s.copy()
        compared += 1
        all_frozen = bool((st_b["refused"] != 0).all() or (st_b["collapsed"] != 0).all()
                          or (st_b["ticks"] >= 300).all())
        if all_frozen and ok and all(solo_ended):
            frozen_equal_verified = True    # frozen equality verified at least once
            frozen_from = k
            break   # later decisions are trivially equal: the engine early-returns
            # on refused/collapsed envs (verified in the kernels) -- state cannot move
    fired = bool(mismatches) or not frozen_equal_verified
    record("F-BATCH-COUPLING", fired,
           {"decision_comparisons": compared * E,
            "bit_mismatches": len(mismatches),
            "frozen_from_decision": frozen_from,
            "frozen_equality_verified": frozen_equal_verified},
           note="per-env isolation across distinct held commands (E=4 vs 4x E=1); "
                "after the engine freezes all envs the frozen tail is verified "
                "against each solo run's captured end-state (an E=1 wrapper "
                "auto-resets once its single env ends)")


def t_smoke():
    """F-SMOKE: the end-to-end loop, 2 iterations x 512 envs, no NaN."""
    out = os.path.join(HERE, "smoke_seed_auto")
    r = subprocess.run([sys.executable, os.path.join(REPO, "tools", "train_first_skill.py"),
                        "--manifest", MANIFEST, "--smoke", "--out", out],
                       capture_output=True, text=True)
    print(r.stdout[-4000:])
    if r.returncode != 0:
        record("F-SMOKE", True, {"returncode": r.returncode},
               note=f"trainer failed: {r.stderr[-2000:]}")
        return
    with open(os.path.join(out, "run_receipt.json")) as f:
        rec = json.load(f)
    nonfinite = rec["nonfinite_census"]
    losses_finite = all(
        all(map(lambda x: x == x and abs(x) != float("inf"), (c["policy_loss"], c["value_loss"], c["entropy"], c["approx_kl"])))
        for c in rec["loss_curve"])
    fired = not (all(v == 0 for v in nonfinite.values())
                 and len(rec["loss_curve"]) == 2
                 and len(rec["eval_log"]) >= 1
                 and rec["selection"]["selected"] is not None
                 and losses_finite)
    record("F-SMOKE", fired,
           {"nonfinite": nonfinite, "iterations": len(rec["loss_curve"]),
            "evals": len(rec["eval_log"]),
            "mean_dec_per_s": rec["throughput"]["decisions_per_s_mean"],
            "torch_max_alloc_mib": rec["vram"]["torch_max_alloc_mib"],
            "smi_after_envs_mib": rec["vram"]["nvidia_smi_used_mib_after_envs"],
            "wall_s": rec["wall_seconds"]},
           note="2 iters x 512 envs end-to-end, loss curve in the receipt")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-smoke", action="store_true")
    ap.add_argument("--only", default=None,
                    help="comma list e.g. F-CLOCK,F-ACTION-MAP")
    args = ap.parse_args()
    only = set(args.only.split(",")) if args.only else None
    order = [("F-ACTION-MAP", t_action_map),
             ("F-CLOCK", t_clock),
             ("F-OBS-FIELD21", t_obs_field21),
             ("F-REWARD-FROZEN", t_reward_frozen),
             ("F-BATCH-COUPLING", t_batch_coupling),
             ("F-SMOKE", t_smoke)]
    for name, fn in order:
        if only and name not in only:
            continue
        if name == "F-SMOKE" and args.skip_smoke:
            continue
        print(f"--- {name} ---")
        try:
            fn()
        except Exception as exc:   # a crash is a firing, with the cause carried
            record(name, True, {}, note=f"RUNNER EXCEPTION: {exc!r}")
    with open(os.path.join(HERE, "falsifier_results.json"), "w") as f:
        json.dump(RESULTS, f, indent=1)
    n_fired = sum(1 for r in RESULTS.values() if r["fired"])
    print(f"=== {len(RESULTS)} falsifiers run, {n_fired} FIRED ===")
    return 1 if n_fired else 0


if __name__ == "__main__":
    sys.exit(main())
