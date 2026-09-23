"""report_first_skill_checkpoint.py -- the one-command 21:00 evidence scaffold.

Given a trainer checkpoint (ckpt_dir/eval_*.pt or iter_*.pt), runs its actor on
the frozen eval seed set (deterministic mean actions) in FirstSkillGoalEnv and
reduces the episode records through the FROZEN acceptance module
(tools/science_funnel/first_skill/acceptance.py: episode_bars / run_bars /
cot_band_ok) -- the hard conditions + CoT band machinery, unmodified.

HONESTY LABEL (printed and written into the output): this measures on the GPU
training env named by --dll. The manifest's acceptance (RUNBOOK Step 5) is the
CPU-exact engine; a GPU-env measurement is TRAINING-TIME EVIDENCE, not
acceptance. The JSON carries the engine identity (dll sha256) and the label so
the 21:00 report cannot blur the two.

Usage:
  python tools/report_first_skill_checkpoint.py --manifest <run_manifest.json> \
      --ckpt <path/to/eval_02_dec0024576.pt> [--dll <walker_env_co8.dll>] [--out <json>]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys

import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
TYPEB_GPU_DIR = os.path.join(HERE, "science_funnel", "typeb_gpu")
TYPEB_EXPORT_DIR = os.path.join(HERE, "science_funnel", "typeb_export")
FIRST_SKILL_DIR = os.path.join(HERE, "science_funnel", "first_skill")
for p in (TYPEB_GPU_DIR, TYPEB_EXPORT_DIR, FIRST_SKILL_DIR, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

import acceptance as acceptance_mod      # FROZEN hard conditions
import walker_env_host                   # UNTOUCHED host
from train_first_skill import (ActorCritic, FirstSkillGoalEnv, MANIFEST_SHA_FROZEN,
                               TICK_NORM, HOLD_TICKS, _rebind_dll_image)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--dll", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--queue-wait-s", type=float, default=1800.0)
    args = ap.parse_args()

    with open(args.manifest, "rb") as f:
        man = json.loads(f.read().decode("utf-8"))
    man_sha = hashlib.sha256(open(args.manifest, "rb").read()).hexdigest()
    assert man_sha == MANIFEST_SHA_FROZEN, "the manifest is not the frozen prereg"
    eval_seeds = [int(s) for s in man["seeds"]["eval_set"]]

    with open(args.ckpt, "rb") as f:
        ck = torch.load(f, weights_only=False)
    dll_sha = ck.get("dll_sha256", "unbound")
    print(f"[report] ckpt {args.ckpt}")
    print(f"[report] ckpt dll_sha256 {dll_sha}  decision_count {ck.get('decision_count')}"
          f"  iteration {ck.get('iteration')}  seed {ck.get('seed')}")

    if args.dll:
        with open(args.dll, "rb") as f:
            dll_sha_now = hashlib.sha256(f.read()).hexdigest()
        print(f"[report] --dll sha256  {dll_sha_now}"
              f"  {'MATCHES ckpt' if dll_sha_now == dll_sha else 'DIFFERS FROM CKPT (labeled)'}")
        _rebind_dll_image(args.dll)

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    hidden = [int(h) for h in man["algorithm"]["actor_hidden"]]
    policy = ActorCritic(FirstSkillGoalEnv.OBS_DIM,
                         FirstSkillGoalEnv.OBS_DIM + 3, hidden,
                         FirstSkillGoalEnv.ACT_DIM).to(dev)
    policy.actor.load_state_dict(ck["actor"])
    policy.eval()

    env = FirstSkillGoalEnv(len(eval_seeds), seed_tags=list(eval_seeds),
                            device=dev, queue_wait_s=args.queue_wait_s)
    env.seed_tags = list(eval_seeds)
    obs = env.reset()
    rets = torch.zeros(env.E, dtype=torch.float64, device=dev)
    with torch.no_grad():
        for _ in range(int(TICK_NORM // HOLD_TICKS)):
            a_norm = torch.tanh(policy.actor(obs))
            obs, rew, _done, info = env.step(a_norm.cpu().numpy())
            valid = torch.from_numpy(info["valid"]).to(dev)
            rets = rets + torch.from_numpy(rew).to(dev) * valid.double()
            if env._ended.all():
                break
    records = []
    for i in range(env.E):
        rec = env._records[i] or env._episode_record(i, env._st)
        rec["seed"] = int(eval_seeds[i])
        records.append(rec)

    run = acceptance_mod.run_bars(records)
    verdict = {
        "label": ("TRAINING-ENV MEASUREMENT (GPU), NOT ACCEPTANCE -- the manifest's "
                  "acceptance is the CPU-exact engine (RUNBOOK Step 5); this is the "
                  "21:00 evidence scaffold over the frozen acceptance.py machinery"),
        "checkpoint": os.path.abspath(args.ckpt),
        "checkpoint_decision_count": ck.get("decision_count"),
        "checkpoint_iteration": ck.get("iteration"),
        "checkpoint_seed": ck.get("seed"),
        "manifest_sha256": man_sha,
        "engine_dll_sha256": dll_sha_now if args.dll else dll_sha,
        "engine_matches_checkpoint_dll": (dll_sha_now == dll_sha) if args.dll else None,
        "mean_eval_return": float(rets.mean().item()),
        "per_episode_records": records,
        "acceptance_run_bars": run,
        "hard_conditions_note": ("no_fall = no engine refusal before tick "
                                 f"{acceptance_mod.EVAL_WINDOW_TICKS}; reach window "
                                 f"[{acceptance_mod.REACH_START_TICK}, "
                                 f"{acceptance_mod.EVAL_WINDOW_TICKS}]; CoT = "
                                 "work_J/(13824.5 kg x distance)"),
    }
    out = args.out or os.path.splitext(args.ckpt)[0] + ".acceptance.json"
    with open(out, "w") as f:
        json.dump(verdict, f, indent=1)
    print(f"[report] reach_rate {run['reach_rate']:.2f}  no_fall_rate "
          f"{run['no_fall_rate']:.2f}  median_ttw {run['median_time_to_waypoint']}"
          f"  cot_median {run['cot_median']}")
    print(f"[report] -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
