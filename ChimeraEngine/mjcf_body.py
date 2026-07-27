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


def to_mjcf(h: Humanoid, dt: float = 1e-3, gravity=(0.0, 0.0, -9.80665)) -> str:
    """Our Link tree as MJCF. Every number is carried across, nothing is re-derived."""
    t = h.tree
    kids = {i: [] for i in range(-1, len(t.links))}
    for i, L in enumerate(t.links):
        kids[L.parent].append(i)

    def emit(i: int, depth: int) -> list:
        L = t.links[i]
        pad = '  ' * depth
        I = np.asarray(L.inertia, float)
        out = [f'{pad}<body name="{L.name}" pos="{_fmt(L.anchor)}">',
               f'{pad}  <joint name="{L.name}" type="hinge" axis="{_fmt(L.axis)}" '
               f'pos="0 0 0" limited="false" damping="0" armature="0" stiffness="0"/>',
               f'{pad}  <inertial pos="{_fmt(L.com)}" mass="{L.mass:.10g}" '
               f'diaginertia="{I[0,0]:.10g} {I[1,1]:.10g} {I[2,2]:.10g}"/>']
        for c in kids[i]:
            out += emit(c, depth + 1)
        out.append(f'{pad}</body>')
        return out

    Ib = np.asarray(t.base_inertia, float)
    lines = ['<mujoco model="chimera_humanoid">',
             # armature/damping ZERO and NO geoms: our engine has neither rotor inertia nor
             # collision, so anything MuJoCo adds here would be a difference we introduced
             # ourselves and then measured as disagreement.
             f'  <option timestep="{dt:.10g}" gravity="{_fmt(gravity)}" integrator="Euler" '
             f'iterations="100" tolerance="1e-12"/>',
             '  <compiler angle="radian" inertiafromgeom="false"/>',
             '  <worldbody>',
             f'    <body name="pelvis" pos="{_fmt(t.base_pos)}">',
             '      <freejoint name="root"/>',
             f'      <inertial pos="{_fmt(t.base_com)}" mass="{t.base_mass:.10g}" '
             f'diaginertia="{Ib[0,0]:.10g} {Ib[1,1]:.10g} {Ib[2,2]:.10g}"/>']
    for c in kids[-1]:
        lines += emit(c, 4)
    lines += ['    </body>', '  </worldbody>', '</mujoco>']
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

    def step(self, n: int = 1) -> None:
        for _ in range(n):
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
