"""policy_gait_eval_directional.py — per-direction gate eval for the 106-dim directional policy.

WHY: tools/policy_gait_eval.py hardcodes the 102-dim obs of the forward-only policies; the
directional policy (tools/train_myobody_directional.py) grew the obs by a 4-dim one-hot command
(order confirmed from ChimeraEngine/output/myobody_walk_directional_meta.npy:
CMDS = ('forward','backward','left','right')). This wrapper reuses EVERYTHING in
policy_gait_eval (contact dyad calibration, strike metrics, envelopes, worst-of-N report) and
patches exactly two things via monkey-patching its rollout:

  1. OBS: the 4-dim one-hot command is appended AFTER the base obs is clamped to +/-20 --
     byte-identical to the trainer's observe().
  2. PROJECTION: distance and speed are measured along the COMMANDED direction, not the spawn
     heading. cmd_dir = spawn heading rotated 0 / 180 / +90 / -90 deg (left = (-y, x),
     right = (y, -x)) -- the same rotation the trainer used, so train/eval agree. Sagittal
     joint angles stay in the BODY-FACING frame (spawn heading), also as in training.

Everything else -- seeds 0..N-1, fall criterion (root z < 0.6 * STAND_Z), report files -- is
unchanged, so numbers are apples-to-apples with the forward-only baseline run through
policy_gait_eval.py. Output files are renamed with an extra __<cmd> suffix so the four
directions do not clobber each other.

Run:  C:\\Python314\\python.exe tools/policy_gait_eval_directional.py --cmd forward
        [--policy output/myobody_walk_directional_policy.pt] [--n 5] [--secs 10]
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
HERE = ROOT / 'ChimeraEngine'
PGE_PATH = Path(__file__).parent / 'policy_gait_eval.py'
# THE COMMAND SET: order matches the trainer's one-hot (meta CMDS, confirmed above).
CMD_IDX = {'forward': 0, 'backward': 1, 'left': 2, 'right': 3}


def load_pge():
    spec = importlib.util.spec_from_file_location('policy_gait_eval', PGE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def make_rollout(pge, cmd, cmd_speeds_m_s):
    """policy_gait_eval.rollout with the two patches from the header. cmd_speeds_m_s is a
    side-channel list: one mean-speed-along-command (m/s, alive portion only) per seed."""

    def rollout(m, d, ac, torch, mujoco, secs, seed):
        links, geoms, floor = pge.foot_sets(m, mujoco)
        nj = m.nq - 7
        mujoco.mj_resetDataKeyframe(m, d, 0)
        d.qpos[7:] += np.random.default_rng(seed).normal(0, 0.03, nj)
        mujoco.mj_forward(m, d)
        q = d.qpos[3:7]
        head = np.array([1 - 2 * (q[2] ** 2 + q[3] ** 2), 2 * (q[1] * q[2] + q[0] * q[3])])
        head /= (np.linalg.norm(head) + 1e-6)
        # cmd_dir: rotate the frozen spawn heading exactly like the trainer (left = (-y, x)).
        cmd_dir = {'forward': head, 'backward': -head,
                   'left': np.array([-head[1], head[0]]),
                   'right': np.array([head[1], -head[0]])}[cmd]
        onehot = np.zeros(len(CMD_IDX), dtype=np.float32)
        onehot[CMD_IDX[cmd]] = 1.0
        start_xy = d.qpos[0:2].copy()
        stand_z = float(m.key_qpos[0][2])

        bid = {role: mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, name)
               for role, name in pge.BODIES.items()}
        steps = int(secs / m.opt.timestep)
        dt_ctrl = m.opt.timestep * pge.CONTROL_EVERY
        truth, lows, bodypos, rootxy, rootz, speed = [], [], [], [], [], []
        fell_at = None
        with torch.no_grad():
            for k in range(0, steps, pge.CONTROL_EVERY):
                base = torch.tensor(np.nan_to_num(np.concatenate(
                    [d.qpos[3:7], d.qvel[3:6], d.qvel[0:3], d.qpos[7:], d.qvel[6:]])),
                    dtype=torch.float32).clamp(-20, 20)
                ob = torch.cat([base, torch.tensor(onehot)]).unsqueeze(0)   # clamp, THEN append
                mean, std, _v = ac(ob)
                a = mean + std * torch.randn_like(std)
                d.ctrl[:] = a.clamp(0.0, 1.0).squeeze(0).numpy()
                for _ in range(pge.CONTROL_EVERY):
                    mujoco.mj_step(m, d)
                touched = set()
                for ci in range(d.ncon):
                    c = d.contact[ci]
                    g1, g2 = int(c.geom1), int(c.geom2)
                    other = g2 if g1 in floor else (g1 if g2 in floor else None)
                    if other is None:
                        continue
                    for name, gl in geoms.items():
                        if other in gl:
                            touched.add(name)
                truth.append([1 if L in touched else 0 for L in links])
                lows.append([min(pge.geom_low(m, d, gi, mujoco) for gi in geoms[L]) for L in links])
                bodypos.append({role: d.xpos[b].copy() for role, b in bid.items()})
                rootxy.append(float(np.dot(d.qpos[0:2] - start_xy, cmd_dir)))   # along COMMAND
                rootz.append(float(d.qpos[2]))
                speed.append(float(np.dot(d.qvel[0:2], cmd_dir)))               # along COMMAND
                if fell_at is None and d.qpos[2] < 0.6 * stand_z:
                    fell_at = k * m.opt.timestep
        dist = float(np.dot(d.qpos[0:2] - start_xy, cmd_dir))
        bp = {role: np.array([b[role] for b in bodypos]) for role in bid}
        ang = pge.angles_from_positions(bp, head)   # sagittal angles stay body-facing
        n_alive = len(speed) if fell_at is None else max(1, int(round(fell_at / dt_ctrl)))
        cmd_speeds_m_s.append(float(np.mean(speed[:n_alive])))
        return {
            'truth': np.array(truth), 'lows': np.array(lows), 'links': links,
            'angles': ang, 'dist': dist, 'fell_at': fell_at, 'dt': dt_ctrl,
            'rootxy': np.array(rootxy), 'rootz': np.array(rootz), 'speed': np.array(speed),
        }

    return rollout


def main() -> int:
    if '--cmd' not in sys.argv:
        print('usage: policy_gait_eval_directional.py --cmd {forward|backward|left|right} '
              '[--policy ...] [--n 5] [--secs 10]')
        return 2
    cmd = sys.argv[sys.argv.index('--cmd') + 1]
    assert cmd in CMD_IDX, f'unknown --cmd {cmd!r}; expected one of {tuple(CMD_IDX)}'
    if '--policy' not in sys.argv:
        sys.argv += ['--policy', 'output/myobody_walk_directional_policy.pt']

    pge = load_pge()
    cmd_speeds_m_s = []
    pge.rollout = make_rollout(pge, cmd, cmd_speeds_m_s)   # THE monkey-patch
    rc = pge.main()
    if rc != 0:
        return rc

    # rename the three report artifacts with an extra __<cmd> suffix (no clobbering).
    pol_name = sys.argv[sys.argv.index('--policy') + 1]
    ppath = Path(pol_name)
    if not ppath.is_absolute():
        ppath = (ROOT / pol_name) if (ROOT / pol_name).exists() else (HERE / pol_name)
    suffix = '' if ppath.stem == 'myobody_walk_policy' else f'__{ppath.stem.replace("_policy", "")}'
    json_dst = None
    for base in (pge.OUT_JSON, pge.OUT_MD, pge.OUT_TRACE):
        src = base.with_name(base.stem + suffix + base.suffix)
        dst = base.with_name(base.stem + suffix + '__' + cmd + base.suffix)
        src.replace(dst)
        if base.suffix == '.json':
            json_dst = dst

    # THE GATE, per direction: sustained --secs on the WORST of N seeds (project rule).
    report = json.loads(json_dst.read_text())
    secs = float(report['secs_per_seed'])
    surv = [r['fell_at_s'] if r['fell_at_s'] is not None else secs for r in report['per_seed']]
    worst = min(surv)
    print(f'\n  GATE[{cmd}]: per-seed survival_s={[round(s, 1) for s in surv]} '
          f'worst={worst:.1f}s of {secs:.0f}s -> {"PASS" if worst >= secs else "FAIL"}')
    print(f'  GATE[{cmd}]: mean speed along command per seed, m/s: '
          f'{[round(s, 3) for s in cmd_speeds_m_s]}')
    print(f'  GATE[{cmd}]: dist along command per seed, m: '
          f'{[r["dist_m"] for r in report["per_seed"]]}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
