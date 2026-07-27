"""body.py — THE HUMAN BODY, from published anthropometry.

Not a shape someone drew. Every segment mass and length here is Winter's standard table
(*Biomechanics and Motor Control of Human Movement*), expressed as a fraction of total mass and of
standing height, so `humanoid(height=1.75, mass=70)` gives a body with the right proportions and
the right inertia — and `humanoid(1.90, 95)` gives a different real person, not a scaled toy.

The peak joint torques are likewise measured values from the biomechanics literature, and they are
what SIZE THE MUSCLES: a muscle's max tension is set so the pair can produce the torque a human
actually produces at that joint, given the moment arm the geometry actually has. Nothing here is
a number I chose because it felt right.

    STRUCTURE. 18 hinges, because the engine's Link is a 1-DOF hinge and a real hip is not. A
    multi-DOF joint is built the standard way -- stacked hinges with a near-massless intermediate
    body between them. Six of the eighteen links are those intermediates; the other twelve plus the
    pelvis are the fourteen real segments.

    WHY MUSCLES AND NOT TORQUES (settled by the operator, 2026-07-26). A torque model cannot tell
    "applying nothing" from "braced" -- both read as zero. Antagonists can: activate both and the
    joint goes STIFF WITHOUT MOVING. That is what you do landing from a fall and bracing in EVA,
    and with torques it would be a hand-tuned PD gain, which is an aesthetic pass wearing control
    theory as a hat.

    THE FROZEN SPACES. `OBSERVATION` and `ACTION` at the bottom are the contract from
    THE_BODY.md §3.1-3.2. Changing either invalidates every trained policy, so they include things
    not used yet -- gravity strength above all, which costs one input now and saves retraining
    everything the day the Moon arrives.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field as dfield
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nervous import attach_antagonist                                        # noqa: E402
from physics_articulated import Link                                         # noqa: E402
from physics_floating import FloatingTree                                    # noqa: E402


# ── Winter's anthropometric table ────────────────────────────────────────────────────────────
# mass as a fraction of TOTAL BODY MASS; length as a fraction of STANDING HEIGHT.
# The mass fractions sum to exactly 1.000, which is the first thing to check when editing them.
MASS_FRAC = {
    'pelvis': 0.142, 'chest': 0.355, 'head': 0.081,
    'upperarm': 0.028, 'forearm': 0.022,          # forearm 0.016 + hand 0.006, carried together
    'thigh': 0.100, 'shin': 0.0465, 'foot': 0.0145,
}
LEN_FRAC = {
    'pelvis': 0.096, 'chest': 0.288, 'head': 0.130,
    'upperarm': 0.186, 'forearm': 0.254,          # forearm + hand
    'thigh': 0.245, 'shin': 0.246, 'foot': 0.152,
    'hip_width': 0.191, 'shoulder_width': 0.259,
}

# Peak isometric joint torques, N.m for a ~70 kg adult (biomechanics literature, order-of-magnitude
# agreed across sources). These SIZE THE MUSCLES -- see `humanoid()`.
PEAK_TORQUE = {
    'waist': 200.0, 'neck': 30.0,
    'shoulder_pitch': 70.0, 'shoulder_roll': 55.0, 'elbow': 70.0,
    'hip_pitch': 200.0, 'hip_roll': 130.0, 'knee': 250.0,
    'ankle_pitch': 150.0, 'ankle_roll': 45.0,
}

_MASSLESS = 5.0e-4          # fraction of body mass given to an intermediate link. NOT zero: a
                            # genuinely massless body makes the mass matrix singular and the solve
                            # fails in a way that looks like a physics bug. Small and honest beats
                            # zero and broken -- and body_witness B2 measures the conditioning.


def _seg(name, mass, length, anchor, axis, parent, radius=None):
    """A capsule-ish segment hinged at one end, extending along -Z in its own frame."""
    r = radius if radius is not None else max(length * 0.12, 1e-3)
    ixx = mass * (3.0 * r * r + length * length) / 12.0
    return Link(name=name, mass=mass, inertia=np.diag([ixx, ixx, 0.5 * mass * r * r]),
                com=np.array([0.0, 0.0, -length / 2.0]), anchor=np.asarray(anchor, float),
                axis=np.asarray(axis, float), parent=parent)


def _hub(name, mass, anchor, axis, parent):
    """A near-massless intermediate: how a multi-DOF joint is built out of 1-DOF hinges."""
    return Link(name=name, mass=mass, inertia=np.eye(3) * (mass * 4e-4),
                com=np.zeros(3), anchor=np.asarray(anchor, float),
                axis=np.asarray(axis, float), parent=parent)


X, Y, Z = (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)


@dataclass
class Humanoid:
    """The assembled body plus the maps a controller needs to talk about it."""
    tree: FloatingTree
    height: float
    mass: float
    joint: dict = dfield(default_factory=dict)        # name -> link/joint index
    pairs: dict = dfield(default_factory=dict)        # name -> Antagonist
    feet: list = dfield(default_factory=list)         # link indices that can bear load
    hands: list = dfield(default_factory=list)

    def n_joints(self) -> int:
        return len(self.tree.links)

    def n_actuators(self) -> int:
        return len(self.tree.muscles)

    def contact_links(self) -> list:
        """Every link that may become a contact -- the planner's candidate set. Feet and hands
        first, then the parts you land on: knees, elbows, pelvis, chest."""
        return self.feet + self.hands + [self.joint[n] for n in
                                         ('shinL', 'shinR', 'forearmL', 'forearmR', 'chest')] + [-1]

    def describe(self) -> str:
        t = self.tree
        real = [L for L in t.links if L.mass > self.mass * _MASSLESS * 2]
        return (f"{self.height:.2f} m, {self.mass:.1f} kg | {len(t.links)} hinges "
                f"({len(real)} real segments + pelvis, {len(t.links)-len(real)} joint hubs) | "
                f"{len(t.muscles)} muscles in {len(self.pairs)} antagonist pairs | "
                f"nv = {t.nv} ({t.n} joints + 6 base)")


def humanoid(height: float = 1.75, mass: float = 70.0,
             gravity=(0.0, 0.0, -9.80665), base_pos=(0.0, 0.0, 0.0)) -> Humanoid:
    """Build the body. Parents must precede children, so the order below IS the tree."""
    m = lambda k: MASS_FRAC[k] * mass
    L = lambda k: LEN_FRAC[k] * height
    hub_m = mass * _MASSLESS
    N_HUBS = 6                       # 2 shoulders, 2 hips, 2 ankles
    # The hubs' mass comes OUT of the pelvis, not on top of the person. Adding it made a 70 kg
    # body weigh 70.84 -- 1.2% of invented matter in a model whose whole claim is anthropometric
    # accuracy. Carve it out and the total is exact.
    hw, sw = L('hip_width') * 0.5, L('shoulder_width') * 0.5
    links, idx = [], {}

    def add(link) -> int:
        links.append(link)
        idx[link.name] = len(links) - 1
        return len(links) - 1

    # trunk and head -- the base IS the pelvis, so `parent=-1` means "hinged to the pelvis"
    i_chest = add(_seg('chest', m('chest'), L('chest'), (0, 0, L('pelvis')), Y, -1))
    add(_seg('head', m('head'), L('head'), (0, 0, L('chest')), Y, i_chest))

    for side, sgn in (('L', 1.0), ('R', -1.0)):
        h = add(_hub(f'shoulder{side}', hub_m, (0.0, sgn * sw, L('chest')), Y, i_chest))
        ua = add(_seg(f'upperarm{side}', m('upperarm'), L('upperarm'), (0, 0, 0), X, h))
        add(_seg(f'forearm{side}', m('forearm'), L('forearm'), (0, 0, -L('upperarm')), Y, ua))

    for side, sgn in (('L', 1.0), ('R', -1.0)):
        h = add(_hub(f'hip{side}', hub_m, (0.0, sgn * hw, 0.0), Y, -1))
        th = add(_seg(f'thigh{side}', m('thigh'), L('thigh'), (0, 0, 0), X, h))
        sh = add(_seg(f'shin{side}', m('shin'), L('shin'), (0, 0, -L('thigh')), Y, th))
        ah = add(_hub(f'ankle{side}', hub_m, (0.0, 0.0, -L('shin')), Y, sh))
        add(_seg(f'foot{side}', m('foot'), L('foot'), (0, 0, 0), X, ah,
                 radius=L('foot') * 0.25))

    # the pelvis is the FLOATING BASE, not a link: a body standing on the ground is not hinged to it
    pelvis_r = L('hip_width') * 0.5
    I_pelvis = np.diag([m('pelvis') * (3 * pelvis_r ** 2 + L('pelvis') ** 2) / 12.0] * 2 +
                       [0.5 * m('pelvis') * pelvis_r ** 2])
    tree = FloatingTree(base_mass=m('pelvis') - N_HUBS * hub_m, base_inertia=I_pelvis,
                        base_com=(0.0, 0.0, L('pelvis') * 0.5), links=links,
                        gravity=gravity, base_pos=base_pos)

    # ── MUSCLES ──────────────────────────────────────────────────────────────────────────────
    # max_tension is DERIVED: the pair must make the published peak torque at the moment arm the
    # geometry actually gives, so tension = torque / arm. Nothing is chosen by feel.
    pairs, _TORQUE_OF = {}, {}

    def pair(joint_name, torque_key, parent_link, offset, along, axis_perp):
        _TORQUE_OF[joint_name] = torque_key
        j = idx[joint_name]
        arm_guess = max(offset, 1e-3)
        p = attach_antagonist(tree, j, parent_link, j, offset=offset, along=along,
                              max_tension=PEAK_TORQUE[torque_key] / arm_guess,
                              name=joint_name, offset_axis=axis_perp)
        pairs[joint_name] = p
        return p

    o = height * 0.030                       # a moment arm of ~5 cm on a 1.75 m body
    pair('chest', 'waist', -1, o * 1.4, L('pelvis') * 0.5, X)
    pair('head', 'neck', i_chest, o * 0.7, L('chest') * 0.25, X)
    for side in ('L', 'R'):
        pair(f'shoulder{side}', 'shoulder_pitch', i_chest, o, L('chest') * 0.25, X)
        pair(f'upperarm{side}', 'shoulder_roll', idx[f'shoulder{side}'], o, o, Y)
        pair(f'forearm{side}', 'elbow', idx[f'upperarm{side}'], o * 0.7, L('upperarm') * 0.3, X)
        pair(f'hip{side}', 'hip_pitch', -1, o * 1.2, L('pelvis') * 0.4, X)
        pair(f'thigh{side}', 'hip_roll', idx[f'hip{side}'], o, o, Y)
        pair(f'shin{side}', 'knee', idx[f'thigh{side}'], o, L('thigh') * 0.3, X)
        pair(f'ankle{side}', 'ankle_pitch', idx[f'shin{side}'], o * 0.8, L('shin') * 0.3, X)
        pair(f'foot{side}', 'ankle_roll', idx[f'ankle{side}'], o * 0.5, o, Y)

    # SIZE THE MUSCLES AGAINST THE ARM THEY ACTUALLY HAVE, not the one I assumed. `offset` is where
    # the attachment sits; the resulting moment arm is a geometric consequence and differs from it.
    # Guessing would have made every peak torque wrong by an unknown factor -- so measure, then
    # rescale. tension = torque / arm, with the arm read off the built body at its neutral pose.
    for jname, p in pairs.items():
        j = idx[jname]
        for msc in (p.flexor, p.extensor):
            arm = abs(tree.moment_arm(msc, j))
            if arm > 1e-6:
                msc.max_tension = PEAK_TORQUE[_TORQUE_OF[jname]] / arm

    # THE FORCE-LENGTH CURVE IS WHAT MAKES CO-CONTRACTION STIFFEN ANYTHING. `rest_length = 0`
    # DISABLES it, tension goes constant, and bracing becomes purely DESTABILISING -- the muscle
    # model's own docstring says so, and body_witness B5 measured -1666 N.m/rad before this line
    # existed. Optimal length is the length in the build pose: the body is strongest around the
    # posture it is built for, which is what an organism's geometry does.
    tree.set_rest_lengths()

    return Humanoid(tree=tree, height=height, mass=mass, joint=idx, pairs=pairs,
                    feet=[idx['footL'], idx['footR']],
                    hands=[idx['forearmL'], idx['forearmR']])


# ══════════════════════════════════════════════════════════════════════════════════════════════
#  THE FROZEN SPACES (THE_BODY.md §3.1-3.2) — change these and every trained policy is invalid
# ══════════════════════════════════════════════════════════════════════════════════════════════
OBSERVATION = [
    # (name, width, why it is in even before anything uses it)
    ('gravity_up',        3, 'local up. There is no global up on a sphere.'),
    ('gravity_strength',  1, 'THE ONE THAT MATTERS. Conditioning on g is what makes ONE policy '
                             'work from an asteroid to a super-Earth. One input now; retraining '
                             'everything later if it is left out.'),
    ('base_lin_vel',      3, 'vestibular -- falling is detected here first'),
    ('base_ang_vel',      3, 'vestibular'),
    ('base_tilt',         1, 'angle from LOCAL up'),
    ('joint_q',          18, 'proprioception: where your limbs are with your eyes shut'),
    ('joint_qd',         18, 'proprioception'),
    ('contact_normal_f',  9, 'per candidate contact link: load. Getting up is a contact problem.'),
    ('muscle_activation', 36, 'what you are already doing -- co-contraction is state, not just output'),
    ('command',           4, 'what is being ASKED for: desired velocity (3) + a mode scalar'),
]
ACTION = [('muscle_activation', 36, 'one activation per muscle, in [0, 1]. Muscles PULL only, '
                                    'which is why they come in pairs and why co-contraction '
                                    '(both on) is a legal and useful action.')]

OBS_DIM = sum(w for _, w, _ in OBSERVATION)
ACT_DIM = sum(w for _, w, _ in ACTION)


def spec() -> str:
    out = [f'OBSERVATION  {OBS_DIM} numbers', '-' * 78]
    for n, w, why in OBSERVATION:
        out.append(f'  {n:<18} {w:>3}   {why}')
    out += ['', f'ACTION       {ACT_DIM} numbers', '-' * 78]
    for n, w, why in ACTION:
        out.append(f'  {n:<18} {w:>3}   {why}')
    return '\n'.join(out)


if __name__ == '__main__':
    h = humanoid()
    print(h.describe())
    print()
    print(spec())
