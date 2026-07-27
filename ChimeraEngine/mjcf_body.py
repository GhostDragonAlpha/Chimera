"""mjcf_body.py — export the humanoid to MJCF, so two engines can be asked the same question.

THE_BODY.md §3.4 calls this the most expensive available mistake: training needs mujoco-warp
(2,358 evals/sec against our measured 50.7 ms/step), but a policy trained in MuJoCo and run in our
engine was trained on a DIFFERENT WORLD -- and a policy exploits exactly the details that differ.

So before any training: prove the two agree. This is a `dyadAnalysis` at the engine seam.

    WHAT IS COMPARED, and what deliberately is not. Passive dynamics only -- gravity, inertia, the
    kinematic tree. MuJoCo has no primitive for our muscle transmission (r(q) = r0 + r1 cos(q-qp)),
    so actuation is a separate seam and is NOT claimed here. If the passive bodies disagree,
    nothing built on top can be trusted; if they agree, the muscle layer is the only thing left to
    check, which is a much smaller question.

    TWO CONVENTION TRAPS, both real and both silent if you get them wrong:
      * quaternions -- ours is (x, y, z, w), MuJoCo's qpos is (w, x, y, z)
      * a free joint's angular velocity -- MuJoCo's qvel[3:6] is in the BODY frame; our `w_base` is
        in the WORLD frame. That exact distinction was a real bug in this engine (S8), found only
        because its error was dt-INDEPENDENT.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from body import Humanoid, humanoid
from physics import quat_to_mat                                          # noqa: E402


def _fmt(v) -> str:
    return ' '.join(f'{float(x):.10g}' for x in np.asarray(v, float).ravel())


def to_mjcf(h: Humanoid, dt: float = 1e-3, gravity=(0.0, 0.0, -9.80665),
            visual: bool = False, floor: bool = False) -> str:
    """Our Link tree as MJCF. Every number is carried across, nothing is re-derived."""
    t = h.tree
    kids = {i: [] for i in range(-1, len(t.links))}
    for i, L in enumerate(t.links):
        kids[L.parent].append(i)

    def emit(i: int, depth: int) -> list:
        L = t.links[i]
        pad = '  ' * depth
        I = np.asarray(L.inertia, float)
        # VISUAL-ONLY GEOMS. contype/conaffinity 0 means they never collide, and the compiler is
        # set inertiafromgeom="false" with an explicit <inertial> on every body -- so adding these
        # cannot touch mass, inertia or contact. The physics stays bit-identical to the model
        # mjcf_witness measured agreeing to 1e-13 m; these exist purely so a human can SEE it.
        vis = ''
        if visual:
            # ANATOMICAL radii, not inertial ones. Deriving the radius from I_zz gave a thin rod
            # for every segment, so a correctly-assembled body rendered as a bundle of sticks and
            # nothing about its proportions was checkable by eye. These are visual-only geoms, so
            # thickness is free -- and being able to SEE the body is what caught the torso bug.
            dz = float(L.com[2])
            ln = abs(2.0 * dz) if abs(dz) > 1e-6 else 0.05
            far = 2.0 * dz if abs(dz) > 1e-6 else -0.05
            key = L.name.rstrip('LR')
            frac = {'chest': .085, 'head': .050, 'upperarm': .028, 'forearm': .024,
                    'thigh': .048, 'shin': .034, 'foot': .030}.get(key, .022)
            r = frac * float(getattr(h, 'height', 1.75))
            col = '0.80 0.83 0.90' if key in ('chest', 'head') else '0.68 0.72 0.82'
            vis = (f'{pad}  <geom type="capsule" fromto="0 0 0 0 0 {far:.4f}" size="{r:.4f}" '
                   f'contype="{1 if floor else 0}" conaffinity="0" rgba="{col} 1"/>')
        out = [f'{pad}<body name="{L.name}" pos="{_fmt(L.anchor)}">']
        if vis:
            out.append(vis)
        out += [
               f'{pad}  <joint name="{L.name}" type="hinge" axis="{_fmt(L.axis)}" '
               f'pos="0 0 0" limited="false" damping="{0.2 if floor else 0}" '
               f'armature="{0.02 if floor else 0}" stiffness="0"/>',
               f'{pad}  <inertial pos="{_fmt(L.com)}" mass="{L.mass:.10g}" '
               f'diaginertia="{I[0,0]:.10g} {I[1,1]:.10g} {I[2,2]:.10g}"/>']
        for c in kids[i]:
            out += emit(c, depth + 1)
        out.append(f'{pad}</body>')
        return out

    Ib = np.asarray(t.base_inertia, float)
    head = []
    if visual or floor:
        head += ['  <visual><global offwidth="900" offheight="700"/></visual>']
    if floor:
        head += ['  <asset><texture name="grid" type="2d" builtin="checker" '
                 'rgb1="0.16 0.18 0.24" rgb2="0.10 0.11 0.15" width="300" height="300"/>'
                 '<material name="grid" texture="grid" texrepeat="8 8" reflectance="0.1"/></asset>',
                 '  <worldbody><geom name="floor" type="plane" size="6 6 0.1" pos="0 0 0" '
                 'contype="0" conaffinity="1" material="grid" condim="3" friction="0.9 0.1 0.1"/>'
                 '<light pos="2 -2 4" dir="-0.5 0.5 -1" diffuse="1 1 1"/></worldbody>']
    if visual and not floor:
        head += ['  <asset>',
                '    <texture name="sky" type="skybox" builtin="gradient" rgb1="0.10 0.12 0.20" '
                'rgb2="0.02 0.03 0.06" width="64" height="64"/>',
                '  </asset>',
                '  <worldbody><light pos="1.2 -1.2 2.2" dir="-0.4 0.4 -1" diffuse="1 1 1"/>'
                '</worldbody>']
    lines = ['<mujoco model="chimera_humanoid">'] + head + [
             # armature/damping ZERO and NO geoms: our engine has neither rotor inertia nor
             # collision, so anything MuJoCo adds here would be a difference we introduced
             # ourselves and then measured as disagreement.
             f'  <option timestep="{dt:.10g}" gravity="{_fmt(gravity)}" integrator="Euler" '
             f'iterations="100" tolerance="1e-12"/>',
             '  <compiler angle="radian" inertiafromgeom="false"/>',
             '  <worldbody>',]
    lines += [
             f'    <body name="pelvis" pos="{_fmt(t.base_pos)}">',
             '      <freejoint name="root"/>',
             f'      <inertial pos="{_fmt(t.base_com)}" mass="{t.base_mass:.10g}" '
             f'diaginertia="{Ib[0,0]:.10g} {Ib[1,1]:.10g} {Ib[2,2]:.10g}"/>']
    for c in kids[-1]:
        lines += emit(c, 4)
    lines += ['    </body>', '  </worldbody>']
    # ONE TORQUE MOTOR PER JOINT. MuJoCo has tendon wrapping and its own muscle model, but our
    # transmission is a MEASURED r(q) TABLE -- a curve sampled off MyoSuite geometry and published
    # in-vivo data -- and no MuJoCo primitive takes a table. Re-fitting it to tendon geometry would
    # mean training against an APPROXIMATION of the levers the game actually runs, which is the
    # sim-to-sim mistake §3.4 exists to prevent, one layer down.
    #
    # So the seam closes the other way round: the muscle model stays OURS (it is the measured part)
    # and MuJoCo supplies only the dynamics (the fast part). tau = T(a, L) * r(q) is computed by
    # muscle_torques() and handed over as ctrl. Same torque, same body, nothing re-derived.
    lines.append('  <actuator>')
    for L in t.links:
        lines.append(f'    <motor name="m_{L.name}" joint="{L.name}" gear="1" ctrllimited="false"/>')
    lines += ['  </actuator>', '</mujoco>']
    return '\n'.join(lines)


def push_state(h: Humanoid, mjd) -> None:
    """Copy OUR state into MuJoCo's, converting both conventions explicitly."""
    t = h.tree
    q = np.asarray(t.base_quat, float)                      # ours is (x, y, z, w)
    mjd.qpos[0:3] = t.base_pos
    mjd.qpos[3:7] = [q[3], q[0], q[1], q[2]]                # MuJoCo wants (w, x, y, z)
    mjd.qpos[7:] = t.q
    mjd.qvel[0:3] = t.v_base
    mjd.qvel[3:6] = t.base_rot.T @ t.w_base                 # world -> BODY frame
    mjd.qvel[6:] = t.qd


def pull_state(mjd):
    """MuJoCo's state in OUR conventions."""
    w, x, y, z = mjd.qpos[3:7]
    return {'pos': np.array(mjd.qpos[0:3]), 'quat': np.array([x, y, z, w]),
            'q': np.array(mjd.qpos[7:]), 'v': np.array(mjd.qvel[0:3]),
            'qd': np.array(mjd.qvel[6:])}


def build(h: Humanoid = None, dt: float = 1e-3, gravity=(0.0, 0.0, -9.80665)):
    """(model, data, xml) for the given body -- or the default one."""
    import mujoco
    h = h or humanoid()
    xml = to_mjcf(h, dt=dt, gravity=gravity)
    m = mujoco.MjModel.from_xml_string(xml)
    return m, mujoco.MjData(m), xml


if __name__ == '__main__':
    import mujoco
    hh = humanoid()
    m, d, xml = build(hh)
    print(xml[:600] + '\n...')
    print(f'\nMuJoCo model: nq {m.nq}, nv {m.nv}, nbody {m.nbody}, njnt {m.njnt}')
    print(f'ours:         nq {hh.tree.n + 7}, nv {hh.tree.nv}, links {len(hh.tree.links)} + base')
    print(f'total mass:   MuJoCo {m.body_mass.sum():.6f} kg   ours {hh.tree.total_mass():.6f} kg')


class FastBody:
    """THE GAME'S PHYSICS PATH. Same body, stepped in C instead of in numpy.

    Our FloatingTree builds a 24x24 mass matrix by 24 unit-acceleration RNEA passes every tick --
    96% of a 51 ms step. MuJoCo uses O(n) articulated-body dynamics and never forms the matrix.
    Same model, same answer: mjcf_witness measured the two agreeing to 1e-13 m, which is ROUNDOFF,
    so this is not an approximation of our engine -- it IS our engine, compiled.

    The numpy tree keeps its job: readable enough to trust as the second messenger that proved this
    one correct. That is why it stays, and why it is allowed to stay slow.
    """

    def __init__(self, h, dt: float = 1e-3, gravity=(0.0, 0.0, -9.80665)):
        import mujoco
        self.h = h
        self.dt = dt
        self.m, self.d, self.xml = build(h, dt=dt, gravity=gravity)
        self._mj = mujoco
        push_state(h, self.d)
        mujoco.mj_forward(self.m, self.d)

    def step(self, n: int = 1, actuated: bool = True, control_every: int = 1) -> None:
        """One tick. With `actuated`, OUR muscle model computes the joint torques and MuJoCo
        integrates them -- the measured half and the fast half, each doing its own job."""
        # CONTROL IS DECIMATED, and that is physiology rather than a shortcut: neural drive to a
        # muscle runs at ~50-100 Hz, not at the 500 Hz a 2 ms physics tick would imply. Recomputing
        # tau every tick was both 36x slower AND less honest than the body it models.
        for k in range(n):
            if actuated and self.h.tree.muscles and (k % control_every == 0):
                self.sync_to_tree()                  # muscle torque depends on q and qd
                self.d.ctrl[:] = self.h.tree.muscle_torques()
            self._mj.mj_step(self.m, self.d)

    def sync_to_tree(self) -> None:
        """Write MuJoCo's state back into the numpy tree, so anything reading the tree -- the
        witnesses, the renderer, sense() -- sees the stepped body without knowing who stepped it."""
        s = pull_state(self.d)
        t = self.h.tree
        t.base_pos[:] = s['pos']
        t.base_quat[:] = s['quat']
        t.base_rot = quat_to_mat(t.base_quat)
        t.q[:] = s['q']
        t.qd[:] = s['qd']
        t.v_base[:] = s['v']
        t.w_base[:] = t.base_rot @ np.array(self.d.qvel[3:6])   # body -> world, our convention
