"""ref_gait.py — the imitation REFERENCE, generated from the derived sub-goals (not mocap).

The operator's synthesis: the imitation framework's reference IS the linked sub-goals (the membranes).
So we DERIVE q_ref(t) from the physics we already closed, rather than borrow a motion-capture clip:

    stride period  T = 1.506 s          (swing/ : compound pendulum, sets the cadence)
    hips swing antiphase                 (rhythm/ : left/right alternation, Δφ = π)
    knee flexes during swing             (contact/ : lift the foot to clear the ground, then plant)

Each keyframe of the reference is a sub-goal ("hierarchy point"); linked in time and cycled at the
cadence, they ARE the reference walk. The body then IMITATES this with the dense per-joint reward
exp(-|q-q_ref|), which is the strong gradient each sub-goal needs. Rhythm is not a hand-coded
oscillator in the loop (that failed) -- it is the PERIODICITY OF THE REFERENCE, tracked.

This module only GENERATES and SELF-CHECKS the reference (no training, no GPU). The check is kinematic:
drive the body through q_ref(phase) with the root pinned and confirm the foot traces a walking arc
(forward+up in swing, back+down in stance) with every joint inside its real limit. A garbage reference
(wrong sign/amplitude) would train the body into a garbage pose -- so it is verified BEFORE any GPU.

Run:  python ChimeraEngine/ref_gait.py [--cycles 2]
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
MYOBODY = HERE.parent / 'vendor' / 'myo_sim' / 'body' / 'myobody.xml'

STRIDE_S = 1.506          # the derived stride period (swing/): one full L+R cycle
HIP_MEAN = -0.10          # small extension bias (within [-0.52, 2.09])
HIP_AMP = 0.35            # hip flexion swing amplitude (~20 deg), stays in range
KNEE_FLEX = 0.90          # peak knee flex during swing (~50 deg), always >= 0
ANKLE_AMP = 0.15          # gentle ankle oscillation

LEG_JOINTS = ['hip_flexion_r', 'hip_flexion_l', 'knee_angle_r', 'knee_angle_l',
              'ankle_angle_r', 'ankle_angle_l']


def leg_addr(m, mujoco):
    """qpos address + [lo, hi] limit for each leg joint we drive."""
    info = {}
    for nm in LEG_JOINTS:
        jid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, nm)
        info[nm] = (int(m.jnt_qposadr[jid]), float(m.jnt_range[jid][0]), float(m.jnt_range[jid][1]))
    return info


def reference(qkey, phase, info):
    """q_ref for a gait phase (rad). Root untouched; only the six leg DOFs are driven, each clamped
    to its real joint limit so the reference is always a pose the body can actually hold."""
    q = qkey.copy()
    for side, ph in (('r', phase), ('l', phase + np.pi)):          # left lags right by pi (antiphase)
        hip = HIP_MEAN + HIP_AMP * np.sin(ph)                        # forward at sin>0, back at sin<0
        # knee flexes through the SWING half (leg lifting/clearing), straight for stance.
        # swing ~ the quarter around max forward velocity; peak flex a bit before max hip flexion.
        knee = KNEE_FLEX * max(0.0, np.sin(ph + 0.6)) ** 2
        ankle = -ANKLE_AMP * np.cos(ph)
        for nm, val in ((f'hip_flexion_{side}', hip), (f'knee_angle_{side}', knee),
                        (f'ankle_angle_{side}', ankle)):
            a, lo, hi = info[nm]
            q[a] = float(np.clip(val, lo, hi))
    return q


def render_reference(cycles):
    """Kinematic playback (no physics): drive the body through q_ref, translate the root forward at a
    walking speed for the eye, render to a gif. Feet slide (no contact) -- the operator judges the LEG
    COORDINATION: does this read as a walk? We do not train PPO to imitate it until it does."""
    import mujoco
    from PIL import Image, ImageDraw
    m = mujoco.MjModel.from_xml_path(str(MYOBODY))
    m.vis.global_.offheight = 720; m.vis.global_.offwidth = 520
    d = mujoco.MjData(m)
    qkey = m.key_qpos[0].copy(); info = leg_addr(m, mujoco)
    root_z = float(qkey[2]); quat = qkey[3:7].copy()
    cam = mujoco.MjvCamera(); mujoco.mjv_defaultCamera(cam)
    cam.distance, cam.elevation, cam.azimuth = 3.8, -6.0, 120.0
    rend = mujoco.Renderer(m, height=720, width=520)
    V, NPC = 0.8, 30                          # cosmetic forward speed (m/s), frames per stride
    frames = []
    for i in range(int(cycles * NPC)):
        t = i * STRIDE_S / NPC
        ph = 2 * np.pi * (t / STRIDE_S)
        q = reference(qkey, ph, info)
        q[0] = V * t; q[2] = root_z; q[3:7] = quat
        d.qpos[:] = q; mujoco.mj_forward(m, d)
        cam.lookat[:] = [V * t, 0.0, 0.9]
        rend.update_scene(d, cam)
        img = Image.fromarray(rend.render()); dr = ImageDraw.Draw(img)
        dr.rectangle([0, 0, 520, 58], fill=(8, 10, 18))
        dr.text((12, 8), 'REFERENCE gait (kinematic, no physics) -- derived from the sub-goals', fill=(210, 220, 240))
        dr.text((12, 32), f't={t:4.2f}s  phase={ph:4.2f}  hipR={q[info["hip_flexion_r"][0]]:+.2f} '
                          f'kneeR={q[info["knee_angle_r"][0]]:.2f}', fill=(150, 200, 240))
        frames.append(img)
    gif = HERE.parent / 'ref_gait.gif'
    frames[0].save(gif, save_all=True, append_images=frames[1:], duration=60, loop=0)
    png = HERE.parent / 'ref_gait.png'
    grid = Image.new('RGB', (520 * 4, 720), (8, 10, 18))
    for idx, fi in enumerate(np.linspace(0, len(frames) - 1, 4).astype(int)):
        grid.paste(frames[fi], (520 * idx, 0))
    grid.save(png)
    print(f'  wrote {gif.name} and {png.name}  ({len(frames)} frames, {cycles} strides)')
    return 0


def main() -> int:
    import mujoco
    cycles = int(sys.argv[sys.argv.index('--cycles') + 1]) if '--cycles' in sys.argv else 2
    if '--render' in sys.argv:
        return render_reference(cycles)
    m = mujoco.MjModel.from_xml_path(str(MYOBODY))
    d = mujoco.MjData(m)
    qkey = m.key_qpos[0].copy()
    info = leg_addr(m, mujoco)
    toes_r = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, 'toes_r')
    pelvis = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, 'pelvis')

    print('\nREFERENCE GAIT — derived from the sub-goals, self-check (kinematic, no physics)\n' + '=' * 76)
    print(f'  stride {STRIDE_S:.3f} s   hip {HIP_MEAN:+.2f}{HIP_AMP:+.2f}*sin   knee {KNEE_FLEX:.2f}*swing   '
          f'ankle {ANKLE_AMP:.2f}')

    N = 24
    foot_fwd, foot_up, viol = [], [], 0
    print(f"\n  {'phase':>6}{'hipR':>7}{'kneeR':>7}{'footX(rel pelvis)':>18}{'footZ':>8}")
    for i in range(N):
        ph = 2 * np.pi * i / N
        q = reference(qkey, ph, info)
        # limit check
        for nm in LEG_JOINTS:
            a, lo, hi = info[nm]
            if q[a] < lo - 1e-6 or q[a] > hi + 1e-6:
                viol += 1
        d.qpos[:] = q
        mujoco.mj_forward(m, d)
        fx = float(d.xpos[toes_r][0] - d.xpos[pelvis][0])   # foot forward relative to pelvis
        fz = float(d.xpos[toes_r][2])                       # foot height (world)
        foot_fwd.append(fx); foot_up.append(fz)
        if i % 3 == 0:
            print(f'  {ph:6.2f}{q[info["hip_flexion_r"][0]]:7.2f}{q[info["knee_angle_r"][0]]:7.2f}'
                  f'{fx:18.3f}{fz:8.3f}')

    fwd_range = max(foot_fwd) - min(foot_fwd)
    lift_range = max(foot_up) - min(foot_up)
    print('\n  ' + '-' * 72)
    print(f'  foot forward travel (rel pelvis): {fwd_range:.3f} m   vertical lift: {lift_range:.3f} m')
    print(f'  joint-limit violations: {viol}/{N*len(LEG_JOINTS)}')
    walk_like = fwd_range > 0.15 and lift_range > 0.03 and viol == 0
    print(f'\n  VERDICT: {"walking-like reference — forward swing + foot lift, all joints legal" if walk_like else "NOT walking-like — needs the operator eye / amplitude fix"}')
    print('  (next: render this kinematically for the operator to confirm, THEN train PPO to imitate it)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
