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
    """F-OBS-FIELD21: channel 21 == the independent differencing law (<=1e-3)
    at every one of 1000 ticks, and == rb[:,2] exactly at every decision."""
    import train_first_skill as tfs
    import observation_schema
    assert observation_schema.FIELD_NAMES[21] == "com_vel_x_heading", \
        "field 21 must be com_vel_x_heading in the frozen table"
    E = 8
    env = tfs.FirstSkillGoalEnv(E, seed_tags=list(range(E)), queue_wait_s=1800.0)
    a = np.full(E, 2 * 0.60 / tfs.V_CEILING - 1.0)   # banked mid command: real motion
    env.step(a)                                       # settle onto the decision grid
    worst_diff = 0.0
    worst_tick = -1
    exact_fail = None
    decisions_checked = 0
    com_prev = env.env.status()["rb"][:, 0].copy()
    for tick in range(1, 1001):                       # THE 1000-step check
        env.env.step(1)                               # one physics tick, all envs
        st = env.env.status()
        com = st["rb"][:, 0]
        diff_law = (com - com_prev) * 300.0           # body_velocity.py's law
        v_state = st["rb"][:, 2]
        err = float(np.max(np.abs(v_state - diff_law)))
        if err > worst_diff:
            worst_diff, worst_tick = err, tick
        if tick % 15 == 0:                            # a decision boundary
            decisions_checked += 1
            obs = env._obs_from_status(st)
            if not np.array_equal(obs[:, 21].cpu().numpy(),
                                  v_state.astype(np.float32)):
                exact_fail = tick
        com_prev = com
    fired = (worst_diff > 1e-3) or (exact_fail is not None)
    record("F-OBS-FIELD21", fired,
           {"max_abs_dev_vs_differencing_law_m_s": worst_diff,
            "worst_tick": worst_tick, "ticks": 1000,
            "decision_boundaries_checked": decisions_checked,
            "exact_vs_rb2_failures": exact_fail},
           note="field 21 live from the env velocity state (threshold 1e-3, prereg)")


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
    # (c) source audit: the trainer references the frozen module's shaping and
    # never re-derives reward terms locally
    src = open(os.path.join(REPO, "tools", "train_first_skill.py")).read()
    uses_frozen = "reward_mod.shaping(" in src
    reimpl = any(s in src for s in ("r_progress(", "r_heading(", "W_HEAD", "PROGRESS_QUANTUM"))
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
    for k in range(20):                     # a full 300-tick episode
        batch.step(a_batch)
        rb_b = batch.env.status()["rb"].copy()
        for j, s in enumerate(solo):
            s.step(np.array([a_batch[j]]))
            rb_s = s.env.status()["rb"][0].copy()
            if not np.array_equal(rb_b[j], rb_s):
                mismatches.append((k, j))
    fired = bool(mismatches)
    record("F-BATCH-COUPLING", fired,
           {"decision_comparisons": 20 * E, "bit_mismatches": len(mismatches)},
           note="per-env isolation across distinct held commands (E=4 vs 4x E=1)")


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
