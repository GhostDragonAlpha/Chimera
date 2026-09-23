"""train_first_skill.py -- the skill-1 trainer (RUNBOOK Step 1 env + Step 2 PPO).

THE ONE NEW FILE of the GPU-env lane (first_skill_prestage_20260922 RUNBOOK).
Everything numeric comes from the FROZEN manifest
(tools/science_funnel/validation/first_skill_prestage_20260922/run_manifest.json,
sha256 c85ba5c43aa7cf12969caf8df732dc77025bb1f50ab23ab87ed42685fe3ef39a) and the
frozen modules it names -- this file invents NO number:

  reward      -> tools/science_funnel/first_skill/reward.py (reward.shaping ONLY;
                 F-REWARD-FROZEN)
  obs         -> tools/science_funnel/typeb_export/observation_schema.py's frozen
                 80-field v2 table + 2 declared goal channels
                 [goal_dist_norm = dist_to_wp/d_wp, goal_closing_speed_norm =
                 com_vel_x_heading/v_seed] (manifest algorithm.actor_input)
  field 21    -> com_vel_x_heading delivered LIVE from the env's velocity state
                 (rb[:,2] = v[3]), the body_velocity.py landed law's quantity,
                 equality-gated by F-OBS-FIELD21 (1e-3 m/s vs the independent
                 first-difference of com_east x 300)
  action      -> (tanh(u)+1)/2 * V_CEILING (reward.V_SEED = 0.7636247890) into
                 commanded_target_velocity_x via the DLL's per-env flat command
                 API (F-ACTION-MAP: +1 -> exactly V_CEILING, 0 -> exactly half)
  clock       -> decisions every reward.HOLD_TICKS=15 ticks at
                 reward.PHYSICS_HZ=300 (F-CLOCK); episode cap 300 ticks =
                 manifest timing_and_clock; termination = the engine's own
                 refusal classes (refused budget rc / collapsed height floor),
                 never an env-invented failure
  PPO         -> the manifest's frozen algorithm block verbatim (4096x24, 10
                 iters, gamma 0.99, lam 0.95, clip 0.2, value coef 1.0, entropy
                 0.01, adaptive lr 1e-3 KL 0.01, 4 minibatches, 5 epochs, actor
                 [128,128] tanh, critic actor-input + privileged {true CoM pose,
                 waypoint world coord} = 85) with eval every 25,000 decisions on
                 the frozen eval seed set (deterministic mean actions, return =
                 the frozen shaping sum) and the frozen checkpoint-selection rule
                 (best mean return among evals at 900000..975000 decisions, ties
                 to the EARLIEST).

IMPLEMENTATION NOTE (recorded, per the brief): rsl_rl is not installed in this
Python (3.14). The manifest says "RSL-RL-style config" -- THE CONFIG IS THE LAW,
NOT THE PACKAGE -- so PPO is implemented here from scratch, hyperparameter for
hyperparameter from the manifest, with the two published-default shapes the
manifest cites (Gaussian over the pre-map action u with state-independent
learnable log std init 1.0; adaptive-lr rule lr/1.5 if KL>2x target, lr*1.5 if
KL<target/2, clamped [1e-5, 1e-2]). The env applies the declared tanh bound; the
Gaussian owns u (the bound is env-side by the manifest's action_space.mapping).

Batch-reset mechanics (the DLL resets all envs together): an env ends at its
own refusal/collapse or the 300-tick cap; ended envs are command-dead
(live=0), contribute zero reward, and their buffer transitions are invalid;
when the LAST env ends, the whole batch resets. Dead transitions never enter
the PPO loss (valid mask); GAE bootstraps zero at true terminations and
V(end-state) at cap truncations (time-limit convention).

Usage:
  python tools/train_first_skill.py --manifest <run_manifest.json> --seed 20260922
  python tools/train_first_skill.py --manifest <run_manifest.json> --smoke

--smoke: 2 iterations x 512 envs on ONE seed (the runbook's declared smoke
shape; a loop proof, not a tuning run) + a forced final eval so the eval path
executes inside the smoke.
"""
from __future__ import annotations

import argparse
import ast
import ctypes
import hashlib
import inspect
import json
import math
import os
import subprocess
import sys
import time

import numpy as np
import torch
import torch.nn as nn
from torch.distributions import Normal

HERE = os.path.dirname(os.path.abspath(__file__))
TYPEB_GPU_DIR = os.path.join(HERE, "science_funnel", "typeb_gpu")
TYPEB_EXPORT_DIR = os.path.join(HERE, "science_funnel", "typeb_export")
FIRST_SKILL_DIR = os.path.join(HERE, "science_funnel", "first_skill")
SCIENCE_DIR = os.path.join(HERE, "science_funnel")
for p in (TYPEB_GPU_DIR, TYPEB_EXPORT_DIR, FIRST_SKILL_DIR, SCIENCE_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

import reward as reward_mod           # tools/science_funnel/first_skill/reward.py (FROZEN)
import acceptance as acceptance_mod   # tools/science_funnel/first_skill/acceptance.py (FROZEN)
import observation_schema             # tools/science_funnel/typeb_export (FROZEN 80-field table)
import walker_env_host                # the batched GPU env host (UNTOUCHED, wrapped only)

# The DLL binding: walker_env_host loads ITS OWN walker_env.dll at import; the
# trainer can rebind that module attribute to a QUALIFIED build (the lane's
# _dll patch pattern -- walker_env_host.py's bytes untouched) via --dll. All
# engine calls (create/reset/step/status/sync AND the per-env flat command API)
# resolve walker_env_host._dll at CALL time, so handle and image always agree.
def _dll():
    return walker_env_host._dll


def _rebind_dll_image(dll_path: str):
    """Point walker_env_host._dll at a qualified image and replay the host's OWN
    restype/argtype configuration statements onto it (parsed with ast from
    walker_env_host's source so the two can never drift; handles the multi-line
    argtypes lists). A fresh CDLL carries no configuration -- the MEASURED
    failure mode (env_create 'argument 13' TypeError) -- so this replay is
    mandatory on every rebind."""
    new_dll = ctypes.CDLL(os.path.abspath(dll_path))
    tree = ast.parse(inspect.getsource(walker_env_host))

    def _root_name(node):
        while isinstance(node, ast.Attribute):
            node = node.value
        return node.id if isinstance(node, ast.Name) else None

    stmts = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and \
                isinstance(node.targets[0], ast.Attribute) and \
                _root_name(node.targets[0]) == "_dll":
            stmts.append(ast.unparse(node).replace("_dll.", "new_dll.", 1))
    env = {"ctypes": ctypes, "new_dll": new_dll}
    for stmt in stmts:
        exec(compile(stmt, "<dll-config-replay>", "exec"), env)
    walker_env_host._dll = new_dll
    return new_dll


def _bind_flat_api(dll):
    """One-time argtypes/restype binding for the per-env flat command API on
    whatever image walker_env_host._dll currently names."""
    dll.env_set_command_flat.restype = ctypes.c_int
    dll.env_set_command_flat.argtypes = [ctypes.c_void_p,
                                         ctypes.POINTER(ctypes.c_double),
                                         ctypes.POINTER(ctypes.c_int)]


MANIFEST_SHA_FROZEN = "c85ba5c43aa7cf12969caf8df732dc77025bb1f50ab23ab87ed42685fe3ef39a"

# ======================================================================================
# Step 1 -- FirstSkillGoalEnv (manifest gpu_env_contract)
# ======================================================================================

V_CEILING = reward_mod.V_SEED          # 0.7636247890 m/s (frozen reward module)
D_WP = reward_mod.D_WP                 # 0.5 m (frozen reward module)
HOLD_TICKS = reward_mod.HOLD_TICKS     # 15 (frozen reward module)
PHYSICS_HZ = reward_mod.PHYSICS_HZ     # 300 (frozen reward module)
REACH_DISC_R = 0.0381812394            # manifest task.reach_disc_radius_m (= V_SEED*15/300)
GOAL_DIM = 2                           # [goal_dist_norm, goal_closing_speed_norm]
TICK_NORM = 300.0                      # manifest timing_and_clock.episode_cap_ticks


class FirstSkillGoalEnv:
    """Batched gait_unit bodies + the Type-A command adapter channel + waypoint
    bookkeeping, exactly per run_manifest.json § gpu_env_contract.

    obs = the frozen v2 field table's 80 channels (fields the engine status
    determines are delivered LIVE; the rest are DECLARED UNAVAILABLE -- mask 0,
    mean-fill 0.0, the schema's own convention; the mask is itself observed via
    fields 58/59) + 2 goal channels -> 82, torch float32 on the GPU.
    action = 1 normalized value in [-1, 1] per env -> the adapter channel.
    """

    NAME = "FirstSkillGoalEnv"
    OBS_DIM = observation_schema.OBS_DIM + GOAL_DIM   # 82
    ACT_DIM = 1

    def __init__(self, n_envs: int, seed_tags=None, block: int = 32,
                 device: str = "cuda", queue_wait_s: float = 2700.0,
                 log=print):
        self.E = int(n_envs)
        self.device = device
        self.log = log
        self.spec = walker_env_host.load_spec()
        self.env = self._create_queued(block, queue_wait_s)
        self._cmd = np.zeros(self.E, np.float64)
        self._live = np.ones(self.E, np.int32)
        self._cmd_issues = 0          # F-CLOCK: one issue per decision
        self.seed_tags = [int(s) for s in seed_tags] if seed_tags is not None \
            else [0] * self.E
        self._st = None               # cached last status (no re-readbacks)
        # per-episode bookkeeping
        self._x0 = None
        self._x_wp = None
        self._work0 = None
        self._prev_com = None
        self._ended = None
        self._ended_kind = None
        self._refusal_tick = None
        self._collapse_tick = None
        self._reach_tick = None
        self._ticks_since_intv = None
        self._episode_decisions = None
        self._records = None
        self.reset()

    # ---- construction with polite GPU queueing (the GPU may be busy with the
    # lead's bars run or another lane's drill; wait/retry, never preempt) ----
    def _create_queued(self, block: int, queue_wait_s: float):
        waited = 0.0
        attempt = 0
        while True:
            attempt += 1
            try:
                env = walker_env_host.WalkerEnvDLL(self.spec, n_envs=self.E,
                                                   block=block)
                env.reset()
                st = env.status()   # probe: a real reset + status round-trip
                if st["ticks"].shape[0] != self.E:
                    raise RuntimeError("status width mismatch")
                self.log(f"[{self.NAME}] GPU env up: E={self.E} "
                         f"(attempt {attempt}, waited {waited:.0f}s)")
                return env
            except Exception as exc:  # CUDA busy/OOM/context race -> queue
                if waited >= queue_wait_s:
                    raise RuntimeError(
                        f"[{self.NAME}] BLOCKED with cause: GPU env create failed "
                        f"{attempt} attempts over {waited:.0f}s; last: {exc!r}") from exc
                self.log(f"[{self.NAME}] GPU busy or env create failed "
                         f"({exc!r}); queuing behind it (retry in 30s, "
                         f"{queue_wait_s - waited:.0f}s budget left)")
                time.sleep(30.0)
                waited += 30.0

    # ---- episodes ----
    def reset(self):
        # MEASURED 2026-09-23 (F-OBS-FIELD21 probe): reset_kernel re-initializes
        # neither the rb readback NOR the a_battery work ledger. The pre-reset
        # rb[5] IS the ledger carry-in, so capture it BEFORE env.reset; episode
        # work_J = rb_end[5] - carry_in is then the honest ledger delta.
        work_carry_in = self.env.status()["rb"][:, 5].copy()
        q, v, _phi = self.spec.reset_state()
        q0 = np.tile(np.asarray(q, np.float64), self.E)
        v0 = np.tile(np.asarray(v, np.float64), self.E)
        self.env.reset(q0=q0, v0=v0, touching0=None)
        st = self._synthetic_reset_status(q0, v0)
        st["rb"][:, 5] = work_carry_in
        self._st = st
        self._x0 = st["rb"][:, 0].copy()                       # com east at entry
        self._x_wp = self._x0 + D_WP                           # waypoint dead ahead
        self._work0 = work_carry_in                            # ledger carry-in
        self._prev_com = self._x0.copy()
        self._ended = np.zeros(self.E, bool)
        self._ended_kind = np.array([""] * self.E, dtype=object)
        self._refusal_tick = np.full(self.E, -1, np.int64)
        self._collapse_tick = np.full(self.E, -1, np.int64)
        self._reach_tick = np.full(self.E, -1, np.int64)
        self._ticks_since_intv = np.zeros(self.E, np.float64)
        self._episode_decisions = 0
        self._records = [None] * self.E
        self._cmd_issues = 0
        return self._obs_from_status(st)

    def _ensure_batch_alive(self):
        """All-batch reset when every env has ended (the DLL resets all E)."""
        if self._ended.all():
            self.reset()

    def _synthetic_reset_status(self, q0: np.ndarray, v0: np.ndarray) -> dict:
        """The t=0 status, synthesized from the reset arrays this wrapper just
        uploaded. MEASURED 2026-09-23 (the F-OBS-FIELD21 probe): walker_env.dll's
        reset_kernel rewrites the scalar state (ticks, refused, cmd -- verified
        zeroed) but NOT the rb/rbi readback arrays, so the first status readback
        after any reset carries the PREVIOUS episode's last tick (stale com,
        v3, phi, battery). Reading it would corrupt every episode's t=0
        observation (previous episode's frozen state) and the episode
        bookkeeping (phantom first-decision reward, misanchored waypoint).
        Every field here is the array the wrapper itself wrote -- zero invented
        numbers; from tick 1 onward the tick kernels rewrite rb every tick."""
        E = q0.size // 18
        qf = np.ascontiguousarray(q0, np.float64).reshape(E, 18)
        vf = np.ascontiguousarray(v0, np.float64).reshape(E, 18)
        rb = np.zeros((E, 6), np.float64)
        rb[:, 0] = qf[:, 3]                    # com east (the entry x)
        rb[:, 1] = qf[:, 4]                    # height
        rb[:, 2] = vf[:, 3]                    # com vx (the seed entry speed)
        rb[:, 3] = float(self.spec.start_phase_left)    # the gait clock entry
        rb[:, 4] = float(self.spec.start_phase_right)
        rb[:, 5] = 0.0                         # the work ledger, zeroed at reset
        return {"rb": rb,
                "rbi": np.zeros((E, 6), np.int32),
                "refused": np.zeros(E, np.int32),
                "refused_class": np.zeros(E, np.int32),
                "collapsed": np.zeros(E, np.int32),
                "ticks": np.zeros(E, np.int64),
                "cmd_fires": np.zeros(E, np.int32),
                "cmd_first_tick": np.zeros(E, np.int64),
                "hind_tds": np.zeros((E, 2), np.int32),
                "fore_td_count": np.zeros((E, 2), np.int32)}

    # ---- the action-map layer (F-ACTION-MAP) ----
    @staticmethod
    def map_action(a_norm: np.ndarray) -> np.ndarray:
        """a_norm in [-1,1] -> the commanded_target_velocity_x payload.
        (a+1)/2 * V_CEILING: +1 -> exactly V_CEILING; 0 -> exactly half."""
        return (np.asarray(a_norm, np.float64).reshape(-1) + 1.0) * 0.5 * V_CEILING

    def _apply_actions(self, a_norm):
        self._cmd[:] = self.map_action(a_norm)
        self._live[:] = (~self._ended).astype(np.int32)   # ended envs: command-dead
        dll = _dll()
        _bind_flat_api(dll)
        ok = dll.env_set_command_flat(
            ctypes.c_void_p(self.env._h),
            self._cmd.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            self._live.ctypes.data_as(ctypes.POINTER(ctypes.c_int)))
        if not ok:
            raise RuntimeError("env_set_command_flat failed")
        self._cmd_issues += 1

    def step(self, a_norm):
        """One decision: ZOH the command, HOLD_TICKS physics ticks, return
        (obs, reward, done, info). The engine's own refusal classes terminate."""
        self._ensure_batch_alive()
        self._apply_actions(a_norm)
        self.env.step(HOLD_TICKS)
        st = self.env.status()
        self._st = st
        rb = st["rb"]
        com = rb[:, 0]
        vx = rb[:, 2]
        ticks = st["ticks"].astype(np.int64)
        newly_refused = (~self._ended) & (st["refused"] != 0)
        newly_collapsed = (~self._ended) & (st["collapsed"] != 0) & ~newly_refused
        self._refusal_tick[newly_refused] = ticks[newly_refused]
        self._collapse_tick[newly_collapsed] = ticks[newly_collapsed]
        engine_end = (st["refused"] != 0) | (st["collapsed"] != 0)
        cap_end = ticks >= int(TICK_NORM)
        newly_end = (~self._ended) & (engine_end | cap_end)
        # THE frozen reward, and ONLY the frozen reward (F-REWARD-FROZEN):
        # shaping(prev_com_x_along, com_x_along, com_vel_x_heading, com_vel_y_heading).
        # com_vel_y_heading is the declared-unavailable channel (mean-fill 0.0).
        # Computed for every env ALIVE ENTERING this decision -- the ending
        # transition included (it earned its shaping; F-REWARD-FROZEN's sentinel
        # probe caught the dropped-terminal-reward bug at first measurement).
        rew = np.zeros(self.E, np.float64)
        for i in np.nonzero(~self._ended)[0]:
            rew[i] = reward_mod.shaping(self._prev_com[i], com[i], vx[i], 0.0)
        for i in np.nonzero(newly_end)[0]:
            self._ended_kind[i] = ("refused" if engine_end[i] else "cap")
            self._records[i] = self._episode_record(int(i), st)
        self._ended |= newly_end
        # reach census on the decision grid (the acceptance window, frozen in
        # acceptance.py; no window constant is invented here)
        in_window = (ticks >= acceptance_mod.REACH_START_TICK) & \
                    (ticks <= acceptance_mod.EVAL_WINDOW_TICKS)
        reached = in_window & (com >= self._x_wp - REACH_DISC_R) & (self._reach_tick < 0)
        self._reach_tick[reached] = ticks[reached]
        # intervention census (fields 50/51/54): the engine's own refusal state
        intv_now = newly_end & engine_end
        self._ticks_since_intv = np.where(intv_now, 0.0,
                                          np.minimum(self._ticks_since_intv + HOLD_TICKS, TICK_NORM))
        self._prev_com = com.copy()
        self._episode_decisions += 1
        obs = self._obs_from_status(st, intv_refusal_now=intv_now)
        info = {
            # a transition is real iff the env was alive entering this decision
            # (its ending decision included); dead-after-end transitions are not
            "valid": (~self._ended) | newly_end,
            "kind": np.where(newly_end, np.where(engine_end, 1, 2), 0).astype(np.int64),
            "ticks": ticks,
            "records": {int(i): self._records[i] for i in np.nonzero(newly_end)[0]},
        }
        return obs, rew, self._ended.copy(), info

    def _episode_record(self, i: int, st: dict) -> dict:
        return {
            "seed": self.seed_tags[i],
            "env": int(i),
            "refusal_tick": (int(self._refusal_tick[i])
                             if self._refusal_tick[i] >= 0 else None),
            "collapse_tick": (int(self._collapse_tick[i])
                              if self._collapse_tick[i] >= 0 else None),
            "reach_tick": (int(self._reach_tick[i])
                           if self._reach_tick[i] >= 0 else None),
            "distance_m": float(st["rb"][i, 0] - self._x0[i]),
            "work_J": float(st["rb"][i, 5] - self._work0[i]),
            "work_J_absolute": float(st["rb"][i, 5]),
            "work_carry_in_J": float(self._work0[i]),
            "ended_kind": self._ended_kind[i],
            "ticks": int(st["ticks"][i]),
        }

    # ---- the privileged training-only block (critic; never the actor) ----
    def privileged_block(self) -> torch.Tensor:
        """True CoM pose (east, height) + waypoint world coord (east) from the
        cached status. Planar engine: no further coords exist to append."""
        rb = self._st["rb"]
        blk = np.stack([rb[:, 0], rb[:, 1], self._x_wp], axis=1).astype(np.float32)
        return torch.from_numpy(blk).to(self.device)

    # ---- the 82-channel observation (frozen v2 table + 2 goal channels) ----
    def _obs_from_status(self, st, intv_refusal_now=None) -> torch.Tensor:
        rb = st["rb"]
        E = self.E
        obs = np.zeros((E, observation_schema.OBS_DIM + GOAL_DIM), np.float32)
        mask = np.zeros((E, observation_schema.OBS_DIM), np.float32)
        two_pi = 2.0 * math.pi
        # gait_phase (fields 0-3): sin/cos of the gait clock phases, LIVE
        phi_l, phi_r = rb[:, 3], rb[:, 4]
        obs[:, 0] = np.sin(two_pi * phi_l); mask[:, 0] = 1.0
        obs[:, 1] = np.cos(two_pi * phi_l); mask[:, 1] = 1.0
        obs[:, 2] = np.sin(two_pi * phi_r); mask[:, 2] = 1.0
        obs[:, 3] = np.cos(two_pi * phi_r); mask[:, 3] = 1.0
        # fields 4 (gait_phase_frac), 5-8 (contact_aggregate), 9-14 (per-foot
        # contacts), 15-20 (foot forces): the DLL status does not determine
        # them -- DECLARED UNAVAILABLE (mask 0, fill 0.0; the per-foot slots'
        # non-delivery is body_velocity.py's banked ruling on this body).
        # body_velocity (fields 21-25): field 21 delivered LIVE from the env's
        # velocity state (the G2.5 gate; equality-gated by F-OBS-FIELD21).
        # 22-25 are NOT delivered (body_velocity.py's declared decree).
        obs[:, 21] = rb[:, 2]; mask[:, 21] = 1.0
        # prev_requested/applied_cmd + limiter_saturation (26-49): not in the
        # status readback -> unavailable. intervention (50-54): the engine's own
        # refusal/collapse state IS the refusal class; ledger_breach and
        # falsifier_red are monitor-side classes the env never determines.
        obs[:, 50] = 1.0; mask[:, 50] = 1.0
        obs[:, 51] = 0.0; mask[:, 51] = 1.0
        obs[:, 54] = self._ticks_since_intv / TICK_NORM; mask[:, 54] = 1.0
        if intv_refusal_now is not None:
            obs[:, 50] = (~intv_refusal_now).astype(np.float32)
            obs[:, 51] = intv_refusal_now.astype(np.float32)
        # command_clock (55-57): the wrapper's own ZOH clock state, LIVE
        obs[:, 55] = 0.0; mask[:, 55] = 1.0   # hold_tick_frac: fresh hold at a decision
        obs[:, 56] = 1.0; mask[:, 56] = 1.0   # policy_gate: this IS a decision tick
        # freq_scale (57): not in the readback -> unavailable
        # phase_dynamics (60-63): census fields unavailable; the clock field
        # LIVE (tick_norm by the manifest's own episode cap)
        obs[:, 63] = np.minimum(st["ticks"].astype(np.float64), TICK_NORM) / TICK_NORM
        mask[:, 63] = 1.0
        # pad_split (64-79): pad gaps not in the readback -> unavailable
        # sensor_health (58-59) observe the mask itself (the schema's rule)
        obs[:, 58] = mask.mean(axis=1)
        obs[:, 59] = (mask > 0).mean(axis=1)
        mask[:, 58] = 1.0
        mask[:, 59] = 1.0
        # the 2 declared goal channels (manifest algorithm.actor_input.composition)
        obs[:, observation_schema.OBS_DIM + 0] = (self._x_wp - rb[:, 0]) / D_WP
        obs[:, observation_schema.OBS_DIM + 1] = rb[:, 2] / V_CEILING
        self._last_mask = mask
        return torch.from_numpy(obs).to(self.device)


# ======================================================================================
# Step 2 -- PPO (the manifest's frozen config, implemented from scratch)
# ======================================================================================

class ActorCritic(nn.Module):
    def __init__(self, obs_dim: int, critic_dim: int, hidden, act_dim: int,
                 init_noise_std: float = 1.0):
        super().__init__()
        assert len(hidden) == 2
        self.actor = nn.Sequential(
            nn.Linear(obs_dim, hidden[0]), nn.Tanh(),
            nn.Linear(hidden[0], hidden[1]), nn.Tanh(),
            nn.Linear(hidden[1], act_dim))
        self.critic = nn.Sequential(
            nn.Linear(critic_dim, hidden[0]), nn.Tanh(),
            nn.Linear(hidden[0], hidden[1]), nn.Tanh(),
            nn.Linear(hidden[1], 1))
        self.log_std = nn.Parameter(torch.log(torch.tensor(float(init_noise_std))))

    def value(self, obs82: torch.Tensor, priv: torch.Tensor) -> torch.Tensor:
        return self.critic(torch.cat([obs82, priv], dim=-1)).squeeze(-1)

    def dist(self, obs82: torch.Tensor) -> Normal:
        mu = self.actor(obs82)                                   # (N, 1)
        return Normal(mu, torch.exp(self.log_std).expand_as(mu))


def adaptive_lr(lr: float, kl: float, kl_target: float) -> float:
    """The cited RSL-RL published adaptive-lr rule (clamped [1e-5, 1e-2])."""
    if kl > kl_target * 2.0:
        return max(lr / 1.5, 1e-5)
    if kl < kl_target * 0.5:
        return min(lr * 1.5, 1e-2)
    return lr


@torch.no_grad()
def run_eval(policy: ActorCritic, env: FirstSkillGoalEnv, eval_seeds, device) -> dict:
    """One eval pass: the frozen eval seed set (one batch slot per seed),
    deterministic mean actions, return = the frozen shaping sum per episode
    (the checkpoint-selection metric). Episodes run to the engine's own end or
    the 300-tick cap; the batch never resets mid-eval (the loop stops when the
    last env ends, so no fresh-episode reward can pollute the returns)."""
    assert env.E == len(eval_seeds), "one batch slot per eval seed"
    obs = env.reset()
    env.seed_tags = [int(s) for s in eval_seeds]
    rets = torch.zeros(env.E, dtype=torch.float64, device=device)
    for _ in range(int(TICK_NORM // HOLD_TICKS)):   # <= 20 decisions = the cap
        a_norm = torch.tanh(policy.actor(obs))
        obs, rew, _done, info = env.step(a_norm.cpu().numpy())
        valid = torch.from_numpy(info["valid"]).to(device)
        rets = rets + torch.from_numpy(rew).to(device) * valid.double()
        if env._ended.all():
            break
    records = []
    for i in range(env.E):
        rec = env._records[i] or env._episode_record(i, env._st)
        rec["seed"] = int(eval_seeds[i])
        records.append(rec)
    return {"mean_return": float(rets.mean().item()),
            "returns": [float(x) for x in rets.tolist()],
            "records": records}


def gae(rew, v, v_next, valid, kind, gamma, lam):
    """Per-env GAE over the dense rollout with the valid mask; zero bootstrap at
    true terminations (kind 1), V(end-state) bootstrap at cap truncations and at
    the rollout boundary for still-alive envs (time-limit convention)."""
    T, E = rew.shape
    adv = np.zeros((T, E), np.float64)
    lastgaelam = np.zeros(E, np.float64)
    for t in range(T - 1, -1, -1):
        seg_end = ~valid[t + 1] if t + 1 < T else np.ones(E, bool)
        boot = np.where(kind[t] == 1, 0.0, v_next[t])
        if t + 1 < T:
            # np.where evaluates both branches eagerly: guard the v[t+1] index
            nextv = np.where(valid[t] & ~seg_end, v[t + 1], boot)
        else:
            nextv = boot
        delta = rew[t] + gamma * nextv - v[t]
        adv[t] = np.where(valid[t], delta + gamma * lam * lastgaelam, 0.0)
        lastgaelam = np.where(valid[t], adv[t], 0.0)
    return adv


def _nvidia_smi_used_mib() -> int:
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=20)
        return int(out.stdout.strip().splitlines()[0])
    except Exception:
        return -1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--out", default=None)
    ap.add_argument("--queue-wait-s", type=float, default=2700.0)
    ap.add_argument("--dll", default=None,
                    help="path to the qualified walker_env DLL image to bind "
                         "(the lane's _dll patch pattern; default: "
                         "typeb_gpu/walker_env.dll). Its sha256 is recorded in "
                         "the run log and hash-bound into every checkpoint.")
    args = ap.parse_args()

    with open(args.manifest, "rb") as f:
        man_bytes = f.read()
    manifest = json.loads(man_bytes.decode("utf-8"))
    manifest_sha = hashlib.sha256(man_bytes).hexdigest()
    if manifest_sha != MANIFEST_SHA_FROZEN:
        raise SystemExit(
            f"[trainer] manifest sha {manifest_sha} != the frozen prereg sha "
            f"{MANIFEST_SHA_FROZEN} -- a NEW registration is required, refusing")
    alg = manifest["algorithm"]
    tim = manifest["timing_and_clock"]
    seeds_cfg = manifest["seeds"]

    # cross-check the frozen modules against the manifest (drift = stop)
    assert abs(reward_mod.V_SEED - 0.7636247890) < 1e-12
    assert abs(reward_mod.PROGRESS_QUANTUM - V_CEILING * HOLD_TICKS / PHYSICS_HZ) < 1e-15
    assert int(tim["physics_hz"]) == PHYSICS_HZ and int(tim["hold_ticks"]) == HOLD_TICKS
    assert int(tim["episode_cap_ticks"]) == acceptance_mod.EPISODE_CAP_TICKS == int(TICK_NORM)
    assert abs(manifest["task"]["reach_disc_radius_m"] - REACH_DISC_R) < 1e-12

    # the frozen config, read from the manifest (never hardcoded here)
    num_envs = int(alg["num_envs"])
    steps_per_env = int(alg["steps_per_env"])
    iterations = int(alg["iterations"])
    gamma = float(alg["gamma"])
    gae_lam = float(alg["gae_lambda"])
    clip = float(alg["clip_param"])
    v_coef = float(alg["value_loss_coef"])
    ent_coef = float(alg["entropy_coef"])
    lr = 1.0e-3                       # alg.learning_rate: "adaptive, init 1.0e-3"
    kl_target = 0.01                  # alg.learning_rate: "KL target 0.01"
    n_mb = int(alg["num_mini_batches"])
    n_epochs = int(alg["num_learning_epochs"])
    hidden = [int(h) for h in alg["actor_hidden"]]
    train_seeds = [int(s) for s in seeds_cfg["training"]]
    eval_seeds = [int(s) for s in seeds_cfg["eval_set"]]
    budget = int(alg["budget_decisions_per_seed"])
    eval_cadence = 25000              # checkpoint_selection_frozen_now.eval_cadence
    eval_grid = list(range(0, budget, eval_cadence))       # 0, 25k, .., 975k (40 evals)
    select_lo = 900000                # the frozen window: evals at 900000..975000

    smoke = args.smoke
    if smoke:
        num_envs, iterations = 512, 2     # the runbook's DECLARED smoke shape
    seed = args.seed if args.seed is not None else train_seeds[0]

    run_name = ("smoke_" if smoke else "") + f"seed{seed}"
    out_dir = args.out or os.path.join(
        SCIENCE_DIR, "validation", "trainer_build_20260923", run_name)
    ckpt_dir = os.path.join(out_dir, "ckpt")
    os.makedirs(ckpt_dir, exist_ok=True)

    log = print
    dll_sha = "unbound"
    if args.dll:
        with open(args.dll, "rb") as f:
            dll_bytes = f.read()
        dll_sha = hashlib.sha256(dll_bytes).hexdigest()
        _rebind_dll_image(args.dll)
        log(f"[trainer] DLL BOUND: {os.path.abspath(args.dll)}")
    log(f"[trainer] DLL sha256 {dll_sha}")
    log(f"[trainer] manifest sha {manifest_sha[:16]}... (frozen prereg verified)")
    log("[trainer] rsl_rl not installed for this Python; PPO implemented from "
        "scratch per the manifest's frozen config -- the config is the law, "
        "not the package (recorded per the brief)")
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    torch.manual_seed(seed)
    np.random.seed(seed)

    vram0 = _nvidia_smi_used_mib()
    t_start = time.perf_counter()
    env = FirstSkillGoalEnv(num_envs, seed_tags=[seed] * num_envs, device=dev,
                            queue_wait_s=args.queue_wait_s, log=log)
    eval_env = FirstSkillGoalEnv(len(eval_seeds), seed_tags=list(eval_seeds),
                                 device=dev, queue_wait_s=args.queue_wait_s, log=log)
    vram1 = _nvidia_smi_used_mib()

    policy = ActorCritic(FirstSkillGoalEnv.OBS_DIM,
                         FirstSkillGoalEnv.OBS_DIM + 3, hidden,
                         FirstSkillGoalEnv.ACT_DIM).to(dev)
    opt = torch.optim.Adam(policy.parameters(), lr=lr)

    T, E = steps_per_env, num_envs
    obs_buf = torch.zeros((T, E, FirstSkillGoalEnv.OBS_DIM), device=dev)
    priv_buf = torch.zeros((T, E, 3), device=dev)
    u_buf = torch.zeros((T, E), device=dev)
    logp_buf = torch.zeros((T, E), device=dev)
    v_buf = torch.zeros((T, E), device=dev)
    v_next_buf = torch.zeros((T, E), device=dev)
    rew_buf = np.zeros((T, E), np.float64)
    valid_buf = np.zeros((T, E), bool)
    kind_buf = np.zeros((T, E), np.int64)

    decision_counter = 0
    eval_fired = set()
    eval_log = []
    train_log = []
    nonfinite = {"obs": 0, "act": 0, "rew": 0, "loss": 0}   # F-SMOKE census
    obs = env.reset()

    def maybe_eval(force=False):
        due = [d for d in eval_grid if d <= decision_counter and d not in eval_fired]
        if force and not due:
            due = ["final"]     # the smoke's declared final eval
        for d in due:
            res = run_eval(policy, eval_env, eval_seeds, dev)
            res["decision_count"] = decision_counter
            res["tag"] = str(d)
            eval_log.append(res)
            eval_fired.add(d)
            ck = os.path.join(ckpt_dir, f"eval_{len(eval_log):02d}_dec{decision_counter:07d}.pt")
            torch.save({"actor": policy.actor.state_dict(),
                        "critic": policy.critic.state_dict(),
                        "log_std": policy.log_std.detach().cpu(),
                        "decision_count": decision_counter,
                        "iteration": len(train_log),
                        "eval": res,
                        "manifest_sha": manifest_sha,
                        "dll_sha256": dll_sha,
                        "seed": seed}, ck)
            log(f"[trainer] EVAL {len(eval_log):02d} @dec {decision_counter}: "
                f"mean_return {res['mean_return']:.6f} -> {os.path.basename(ck)}")

    maybe_eval()   # the frozen grid's decision-0 eval

    for it in range(iterations):
        t0 = time.perf_counter()
        # ---- rollout (24 decisions x E envs; evals fire mid-rollout on the grid) ----
        for t in range(T):
            priv = env.privileged_block()          # the state obs was built from
            with torch.no_grad():
                dist = policy.dist(obs)
                u = dist.sample()                                  # (E, 1)
                logp = dist.log_prob(u).squeeze(-1)
                v = policy.value(obs, priv)
            a_norm = torch.tanh(u)
            if not torch.isfinite(obs).all():
                nonfinite["obs"] += int((~torch.isfinite(obs)).sum().item())
            if not torch.isfinite(a_norm).all():
                nonfinite["act"] += int((~torch.isfinite(a_norm)).sum().item())
            next_obs, rew, _done, info = env.step(a_norm.cpu().numpy())
            if not np.isfinite(rew).all():
                nonfinite["rew"] += int((~np.isfinite(rew)).sum())
            next_priv = env.privileged_block()     # the state next_obs was built from
            with torch.no_grad():
                v_next = policy.value(next_obs, next_priv)
            obs_buf[t] = obs
            priv_buf[t] = priv
            u_buf[t] = u.squeeze(-1)
            logp_buf[t] = logp
            v_buf[t] = v
            v_next_buf[t] = v_next
            rew_buf[t] = rew
            valid_buf[t] = info["valid"]
            kind_buf[t] = info["kind"]
            obs = next_obs
            decision_counter += E
        maybe_eval()   # the frozen 25k decision grid fires mid-iteration too

        # ---- GAE over valid transitions ----
        adv = gae(rew_buf, v_buf.cpu().numpy(), v_next_buf.cpu().numpy(),
                  valid_buf, kind_buf, gamma, gae_lam)
        ret = adv + v_buf.cpu().numpy()
        valid_t = torch.from_numpy(valid_buf).to(dev)
        adv_t = torch.from_numpy(adv).to(dev)[valid_t]
        adv_t = (adv_t - adv_t.mean()) / (adv_t.std() + 1e-8)
        ret_t = torch.from_numpy(ret).to(dev)[valid_t]
        o_t = obs_buf[valid_t]
        p_t = priv_buf[valid_t]
        u_t = u_buf[valid_t]
        lp_t = logp_buf[valid_t]
        n_valid = int(valid_t.sum().item())

        # ---- PPO update (the frozen epochs/minibatches/clip/coefficients) ----
        mb_size = math.ceil(n_valid / n_mb)
        it_stats = {"policy_loss": [], "value_loss": [], "entropy": [], "kl": []}
        for _ep in range(n_epochs):
            perm = torch.randperm(n_valid, device=dev)
            for mb in range(n_mb):
                mi = perm[mb * mb_size:(mb + 1) * mb_size]
                dist = policy.dist(o_t[mi])
                logp = dist.log_prob(u_t[mi].unsqueeze(-1)).squeeze(-1)
                ratio = torch.exp(logp - lp_t[mi])
                a = adv_t[mi]
                surr = -torch.min(ratio * a,
                                  torch.clamp(ratio, 1.0 - clip, 1.0 + clip) * a).mean()
                v_pred = policy.value(o_t[mi], p_t[mi])
                v_loss = ((v_pred - ret_t[mi]) ** 2).mean()
                entropy = dist.entropy().mean()
                loss = surr + v_coef * v_loss - ent_coef * entropy
                opt.zero_grad(set_to_none=True)
                loss.backward()
                nn.utils.clip_grad_norm_(policy.parameters(), 1.0)
                opt.step()
                with torch.no_grad():
                    it_stats["policy_loss"].append(float(surr.item()))
                    it_stats["value_loss"].append(float(v_loss.item()))
                    it_stats["entropy"].append(float(entropy.item()))
                    it_stats["kl"].append(float((lp_t[mi] - logp).mean().item()))
        if not all(math.isfinite(x) for xs in it_stats.values() for x in xs):
            nonfinite["loss"] += 1
        mean_kl = float(np.mean(it_stats["kl"]))
        lr = adaptive_lr(lr, mean_kl, kl_target)
        for g in opt.param_groups:
            g["lr"] = lr
        dt = time.perf_counter() - t0
        train_log.append({
            "iteration": it + 1,
            "decisions": decision_counter,
            "valid_transitions": n_valid,
            "policy_loss": float(np.mean(it_stats["policy_loss"])),
            "value_loss": float(np.mean(it_stats["value_loss"])),
            "entropy": float(np.mean(it_stats["entropy"])),
            "approx_kl": mean_kl,
            "lr": lr,
            "mean_reward_alive": float(rew_buf[valid_buf].mean()),
            "seconds": dt,
            "decisions_per_s": (T * E) / dt,
            "env_steps_per_s": (T * E * HOLD_TICKS) / dt,
        })
        tl = train_log[-1]
        log(f"[trainer] iter {it + 1}/{iterations}: pi_loss {tl['policy_loss']:+.5f} "
            f"v_loss {tl['value_loss']:.5f} ent {tl['entropy']:.4f} kl {mean_kl:.5f} "
            f"lr {lr:.2e} r_mean {tl['mean_reward_alive']:+.4f} "
            f"| {tl['decisions_per_s']:.0f} dec/s {tl['env_steps_per_s']:.0f} steps/s "
            f"{dt:.1f}s")
        # per-iteration checkpoint (the restart-is-one-command requirement):
        torch.save({"actor": policy.actor.state_dict(),
                    "critic": policy.critic.state_dict(),
                    "log_std": policy.log_std.detach().cpu(),
                    "decision_count": decision_counter,
                    "iteration": it + 1,
                    "manifest_sha": manifest_sha,
                    "dll_sha256": dll_sha,
                    "seed": seed,
                    "train_log_tail": train_log[-1]},
                   os.path.join(ckpt_dir, f"iter_{it + 1:02d}.pt"))
    maybe_eval(force=smoke)   # the smoke's declared final eval (loop proof)

    # ---- the frozen checkpoint-selection rule ----
    pool = [e for e in eval_log
            if (isinstance(e["decision_count"], int) and e["decision_count"] >= select_lo)]
    pool_fallback = False
    if not pool:
        if smoke:
            pool = list(eval_log)   # smoke: prove the rule's machinery on what exists
            pool_fallback = True
        else:
            raise SystemExit("[trainer] the frozen selection window "
                             "(decision counts >= 900000) is empty in a full run -- "
                             "the eval grid wiring is broken; refusing to select")
    best = None
    for e in pool:              # ties break to the EARLIEST (strictly-greater replaces)
        if best is None or e["mean_return"] > best["mean_return"]:
            best = e
    selection = {
        "rule": "best mean eval return among the LAST 10% of evals "
                "(decision counts 900000..975000); ties to the EARLIEST (frozen)",
        "pool_fallback_smoke_only": pool_fallback,
        "pool": [{"tag": e["tag"], "decision_count": e["decision_count"],
                  "mean_return": e["mean_return"]} for e in pool],
        "selected": ({"tag": best["tag"], "decision_count": best["decision_count"],
                      "mean_return": best["mean_return"]} if best else None),
        "selection_is_not_acceptance": True,
    }
    with open(os.path.join(out_dir, "selection.json"), "w") as f:
        json.dump(selection, f, indent=1)

    wall = time.perf_counter() - t_start
    receipt = {
        "lane": "TRAINER-BUILD (Agent: trainer)",
        "run": run_name,
        "smoke": smoke,
        "seed": seed,
        "manifest_sha256_restated": manifest_sha,
        "dll_sha256": dll_sha,
        "env_class": FirstSkillGoalEnv.NAME,
        "obs_dim": FirstSkillGoalEnv.OBS_DIM,
        "action_map": "(tanh(u)+1)/2 * 0.7636247890 -> commanded_target_velocity_x",
        "ppo": {"implementation": "from-scratch (rsl_rl absent for py3.14); the "
                                  "manifest's frozen config verbatim",
                "config": {k: alg[k] for k in
                           ("num_envs", "steps_per_env", "iterations", "gamma",
                            "gae_lambda", "clip_param", "value_loss_coef",
                            "entropy_coef", "num_mini_batches",
                            "num_learning_epochs", "actor_hidden")}},
        "nonfinite_census": nonfinite,   # F-SMOKE: must be all zeros
        "loss_curve": [{"iteration": t["iteration"],
                        "policy_loss": t["policy_loss"],
                        "value_loss": t["value_loss"],
                        "entropy": t["entropy"],
                        "approx_kl": t["approx_kl"]} for t in train_log],
        "throughput": {"decisions_per_s_mean":
                       float(np.mean([t["decisions_per_s"] for t in train_log])),
                       "env_steps_per_s_mean":
                       float(np.mean([t["env_steps_per_s"] for t in train_log]))},
        "vram": {"nvidia_smi_used_mib_before": vram0,
                 "nvidia_smi_used_mib_after_envs": vram1,
                 "torch_max_alloc_mib":
                 round(torch.cuda.max_memory_allocated() / 2 ** 20, 1)
                 if dev == "cuda" else None},
        "wall_seconds": wall,
        "train_log": train_log,
        "eval_log": [{"tag": e["tag"], "decision_count": e["decision_count"],
                      "mean_return": e["mean_return"],
                      "records": e["records"]} for e in eval_log],
        "selection": selection,
    }
    with open(os.path.join(out_dir, "run_receipt.json"), "w") as f:
        json.dump(receipt, f, indent=1)
    log(f"[trainer] receipt -> {os.path.join(out_dir, 'run_receipt.json')}")
    if smoke:
        ok = (all(v == 0 for v in nonfinite.values())
              and len(train_log) == iterations
              and len(eval_log) >= 1 and selection["selected"] is not None)
        log(f"[trainer] F-SMOKE: {'PASS' if ok else 'FIRED'} "
            f"(nonfinite={nonfinite}, iters={len(train_log)}, "
            f"evals={len(eval_log)}, selected={selection['selected'] is not None})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
