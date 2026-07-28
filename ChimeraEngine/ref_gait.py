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
MYOBODY = HERE.parent / 'vendor' / 'myo_sim' / 'body' / 'myobody_simpleupper.xml'  # WITH ARMS

STRIDE_S = 1.506          # the derived stride period (swing/): one full L+R cycle
DUTY = 0.60               # stance fraction -- THE musical division: stance 60% / swing 40% (not 50/50)
# The operator's "first musical division problem": the sub-goals are RIGHT, but they must land on the
# right BEATS of the timeline. The gait cycle is a measure; each keyframe below is a sub-goal on its
# beat; linked by interpolation they ARE the reference walk. Phase in [0,1) of ONE leg:
#   stance 0.00-0.60 (heel-strike -> toe-off),  swing 0.60-1.00.  Legs offset 0.5 -> double support
#   at 0.0-0.1 and 0.5-0.6 (the two downbeats where BOTH feet are planted).
#          phase    hip    knee   ankle
GAIT_KF = [(0.00,  0.35,  0.05,  0.10),   # heel-strike: leg reaches FORWARD, knee near-straight
           (0.15,  0.15,  0.18,  0.00),   # loading:     a small knee flex absorbs the landing
           (0.35, -0.05,  0.08, -0.05),   # mid-stance:  CoM vaults over the planted foot
           (0.55, -0.22,  0.12, -0.22),   # terminal stance: hip EXTENDS back, ankle pushes off
           (0.65, -0.12,  0.45, -0.05),   # toe-off:     knee breaks, the leg leaves the ground
           (0.80,  0.12,  1.00,  0.15),   # mid-swing:   knee at MAX flex, foot tucked up to clear
           (0.95,  0.35,  0.25,  0.10),   # terminal swing: knee EXTENDS to reach for heel-strike
           (1.00,  0.35,  0.05,  0.10)]   # = heel-strike (the cycle closes)

LEG_JOINTS = ['hip_flexion_r', 'hip_flexion_l', 'knee_angle_r', 'knee_angle_l',
              'ankle_angle_r', 'ankle_angle_l']
ARM_AMP = 0.40            # shoulder swing amplitude -- arms COUNTER the legs (keeps whole-body L ~ 0)
ELBOW_FLEX = 0.40         # elbows carried slightly bent, as in a natural walk
ARM_JOINTS = ['arm_flex_r', 'arm_flex_l', 'elbow_flex_r', 'elbow_flex_l']


def leg_addr(m, mujoco):
    """qpos address + [lo, hi] limit for each DRIVEN joint (legs + arms)."""
    info = {}
    for nm in LEG_JOINTS + ARM_JOINTS:
        jid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, nm)
        info[nm] = (int(m.jnt_qposadr[jid]), float(m.jnt_range[jid][0]), float(m.jnt_range[jid][1]))
    return info


def _interp(ph01):
    """The leg pose (hip, knee, ankle) at cycle phase ph01 in [0,1), linear between beat-keyframes."""
    ph01 = ph01 % 1.0
    for i in range(len(GAIT_KF) - 1):
        p0, p1 = GAIT_KF[i][0], GAIT_KF[i + 1][0]
        if p0 <= ph01 <= p1:
            f = (ph01 - p0) / (p1 - p0 + 1e-9)
            return [GAIT_KF[i][j] + f * (GAIT_KF[i + 1][j] - GAIT_KF[i][j]) for j in (1, 2, 3)]
    return list(GAIT_KF[-1][1:])


def reference(qkey, phase, info):
    """q_ref for a gait phase (rad, 2pi = one stride). Legs run the beat-cycle (offset half a stride);
    each ARM swings CONTRALATERAL -- antiphase to its SAME-side leg -- so whole-body angular momentum
    stays ~ 0 (why a walk needs arms). Every driven DOF clamped to its real joint limit."""
    q = qkey.copy()
    ph01 = (phase / (2 * np.pi)) % 1.0
    for side, p in (('r', ph01), ('l', (ph01 + 0.5) % 1.0)):
        hip, knee, ankle = _interp(p)
        arm = -ARM_AMP * np.cos(2 * np.pi * p)          # shoulder back when this leg is forward (p=0)
        for nm, val in ((f'hip_flexion_{side}', hip), (f'knee_angle_{side}', knee),
                        (f'ankle_angle_{side}', ankle),
                        (f'arm_flex_{side}', arm), (f'elbow_flex_{side}', ELBOW_FLEX)):
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
    cam.distance, cam.elevation, cam.azimuth = 3.4, -6.0, 180.0   # look along X = the body's SAGITTAL plane (it faces -Y)
    rend = mujoco.Renderer(m, height=720, width=520)
    NPC = 30                                  # frames per stride
    cam.lookat[:] = [float(qkey[0]), float(qkey[1]), 0.9]    # FIXED camera -- no fake translation (the cheat)
    frames = []
    for i in range(int(cycles * NPC)):
        t = i * STRIDE_S / NPC
        ph = 2 * np.pi * (t / STRIDE_S)
        q = reference(qkey, ph, info)
        q[2] = root_z; q[3:7] = quat                        # root PINNED in place; only the configuration cycles
        d.qpos[:] = q; mujoco.mj_forward(m, d)
        rend.update_scene(d, cam)
        img = Image.fromarray(rend.render()); dr = ImageDraw.Draw(img)
        dr.rectangle([0, 0, 520, 58], fill=(8, 10, 18))
        dr.text((12, 8), 'REFERENCE configuration -- IN PLACE (no fake translation)', fill=(210, 220, 240))
        dr.text((12, 32), 'legs alternate (one stance / one swing) -- real motion comes from PHYSICS',
                fill=(150, 200, 240))
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
    print(f'  stride {STRIDE_S:.3f} s   musical division: stance {DUTY*100:.0f}% / swing {(1-DUTY)*100:.0f}%'
          f'   {len(GAIT_KF)-1} beat-keyframes')

    N = 24
    foot_fwd, foot_up, viol = [], [], 0
    print(f"\n  {'phase':>6}{'hipR':>7}{'kneeR':>7}{'footX(rel pelvis)':>18}{'footZ':>8}")
    for i in range(N):
        ph = 2 * np.pi * i / N
        q = reference(qkey, ph, info)
        # limit check
        for nm in LEG_JOINTS + ARM_JOINTS:
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
    print(f'  joint-limit violations: {viol}/{N*(len(LEG_JOINTS)+len(ARM_JOINTS))}')
    walk_like = fwd_range > 0.15 and lift_range > 0.03 and viol == 0
    print(f'\n  VERDICT: {"walking-like reference — forward swing + foot lift, all joints legal" if walk_like else "NOT walking-like — needs the operator eye / amplitude fix"}')
    print('  (next: render this kinematically for the operator to confirm, THEN train PPO to imitate it)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
