"""collect_release_states.py -- v14 THE RETURN: record the REAL post-release states.

Runs the full carry cycle under the proven carry theta (carry_theta.npy) exactly as
train_carry's evaluate does -- keyframe reset, stone on the floor, SNAP at 1.0 s, set-down
taper 4.0-4.5 s, weld release at 4.5 s -- and saves FULLPHYSICS state snapshots (time,
qpos, qvel, act -- muscle activations included, or the reset would be an artificial state)
plus eq_active and xfrc_applied, every SNAP_DT s from the release for SPAN_S.

These are the states the recovery must stand FROM. Deterministic: one theta, one reset,
one trajectory -- the snapshots ARE the trajectory the full cycle produces.

    python tools/collect_release_states.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from world import load_body
from stand_port import derive_stand_port, MYOBODY
from train_stand import joint_ids, seat_in_limits
from grab_port import (derive_grab_port, stone_xml, spawn_stone, snap_stone_to_carry,
                       support_stone_weight, weld_load, RAMP_S, T_DROP, WELD_NAME)

OUTDIR = ROOT / "ChimeraEngine" / "output" / "ports"
CARRY_THETA = OUTDIR / "carry_theta.npy"
STATES_NPZ = OUTDIR / "release_states.npz"
T_SNAP = 1.0
SECS = 7.5          # release at 4.5, snapshots to 6.0, margin past the last one
SNAP_DT = 0.1       # 16 states over release .. release+1.5 -- the collapse trajectory itself
SPAN_S = 1.5


def main() -> int:
    import mujoco
    if not CARRY_THETA.exists():
        raise SystemExit(f"no {CARRY_THETA} -- the carry must be proven before its return.")
    P = derive_stand_port()
    G = derive_grab_port()
    path = stone_xml(MYOBODY, G)
    m, _g = load_body(path, mujoco)
    d = mujoco.MjData(m)
    eq = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_EQUALITY, WELD_NAME)
    nu = m.nu
    theta = np.load(CARRY_THETA)
    if theta.size == 4 * nu:
        theta = np.concatenate([theta, np.zeros(nu)])
    a0, kh, kp = theta[:nu], theta[nu:2 * nu], theta[2 * nu:3 * nu]
    kr = theta[3 * nu:4 * nu]
    kw = theta[4 * nu:5 * nu]

    jids = joint_ids(m, mujoco)
    mujoco.mj_resetDataKeyframe(m, d, 0)
    mujoco.mj_forward(m, d)
    seat_in_limits(m, d, mujoco, jids)
    spawn_stone(m, d, mujoco, G)
    support_stone_weight(m, d, mujoco, 1.0)

    tgt = P["OUT pelvis_target_m"]
    steps = int(SECS / m.opt.timestep)
    snap_k = int(T_SNAP / m.opt.timestep)
    ramp_steps = int(RAMP_S / m.opt.timestep)
    drop_k = int(T_DROP / m.opt.timestep)
    release_k = drop_k + ramp_steps
    spec = mujoco.mjtState.mjSTATE_FULLPHYSICS
    snaps_at = {release_k + int(dt / m.opt.timestep)
                for dt in np.arange(0.0, SPAN_S + 1e-9, SNAP_DT)}
    states, times = [], []
    for k in range(steps):
        if k == snap_k:
            snap_stone_to_carry(m, d, mujoco)
            d.eq_active[eq] = 1
        if snap_k <= k < drop_k:
            support_stone_weight(m, d, mujoco, min(1.0, (k - snap_k + 1) / ramp_steps))
        elif drop_k <= k < release_k:
            support_stone_weight(m, d, mujoco, 1.0 - min(1.0, (k - drop_k + 1) / ramp_steps))
        elif k == release_k:
            d.eq_active[eq] = 0
            support_stone_weight(m, d, mujoco, 1.0)
        if k % 20 == 0:
            z = float(d.qpos[2])
            q = d.qpos[3:7]
            pitch = float(np.arctan2(2 * (q[0] * q[2] - q[3] * q[1]),
                                     1 - 2 * (q[1] ** 2 + q[2] ** 2)))
            roll = float(np.arctan2(2 * (q[0] * q[1] + q[2] * q[3]),
                                    1 - 2 * (q[1] ** 2 + q[2] ** 2)))
            d.ctrl[:] = np.clip(a0 + kh * (tgt - z) + kp * pitch + kr * roll
                                + kw * weld_load(m, d, mujoco), 0.0, 1.0)
        mujoco.mj_step(m, d)
        if k in snaps_at:
            st = np.empty(mujoco.mj_stateSize(m, spec))
            mujoco.mj_getState(m, d, st, spec)
            states.append(st.copy())
            times.append(float(d.time))
            print(f"snapshot at t={d.time:.2f} s  pelvis {float(d.qpos[2]):.3f} m")
    if not states:
        raise SystemExit("no snapshots collected -- refusing to write an empty curriculum.")
    np.savez_compressed(STATES_NPZ,
                        states=np.stack(states), times=np.array(times),
                        spec=int(spec))
    print(f"\nsaved {len(states)} states to {STATES_NPZ}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
