"""Synthetic fixtures: minimal rig + a counts-matched whole-body chimanoid twin.

Facts the fixtures must satisfy (DERIVATION.md §2):
  - synth_chimanoid() reproduces the REAL source's counts and NAMES (19 bodies / 39
    coordinate names / 468 path sites / 120 tendons / 121 muscles) so the SAME
    correspondence object fits both the real XML intake and the synthetic source;
  - synth target landmarks are generated from a parameterised limb-length table
    (longer femur, shorter tibia, wider thorax) so F6 scaling and F2 frame
    invariance are exercised with real geometry values.
"""
from __future__ import annotations

import numpy as np

from schema import (
    SourceAnatomy,
    SourceBody,
    SourceJoint,
    SourceMuscle,
    SourceSite,
    SourceTendon,
    Correspondence,
    CorrespondenceSegment,
)
from correspondence import Refusal
from intake import load_source, global_site_positions

REAL_XML = r"E:\PythonChimera\.tmp\chimanoid.xml"

TREE_ORDER = [
    "pelvis",
    "femur_r", "tibia_r", "talus_r", "toes_r",
    "femur_l", "tibia_l", "talus_l", "toes_l",
    "thorax_dummy", "thorax", "humerus", "ulna", "radius", "hand_r",
    "humerus_l", "ulna_l", "radius_l", "hand_l",
]


def chain_child(ana: SourceAnatomy, body: str) -> str | None:
    for b in ana.bodies:
        if b.parent == body:
            return b.name
    return None


def _pick_roll_site(ana: SourceAnatomy, b: SourceBody, site_world: dict[str, np.ndarray]) -> str | None:
    """Choose a roll-reference site guaranteed off the bone axis: among the body's own
    sites, its parent's and its first child's, pick the one with the largest
    perpendicular distance to the proximal->distal bone line."""
    child = chain_child(ana, b.name)
    if child is not None:
        D = ana.body_by_name[child].pos_global
    else:
        own_ref = [s for s in ana.sites if s.body == b.name and s.referenced_by]
        D = max((site_world[s.name] for s in own_ref), key=lambda p: np.linalg.norm(p - b.pos_global), default=b.pos_global + np.array([0.0, -0.1, 0.0]))
    A = b.pos_global
    a = D - A
    nn = np.linalg.norm(a)
    if nn < 1e-12:
        return None
    a = a / nn
    candidates: list[str] = []
    for body in [b.name, b.parent, child]:
        if body is None:
            continue
        candidates += [s.name for s in ana.sites if s.body == body]
    best, best_perp = None, -1.0
    for sn in candidates:
        d = (site_world[sn] - A)
        perp = np.linalg.norm(d - a * (a @ d))
        if perp > best_perp:
            best, best_perp = sn, perp
    return best if best_perp > 1e-6 else None


# ------------------------------------------------------------------- synth rig
def synth_rig() -> SourceAnatomy:
    pelvis = SourceBody(
        name="pelvis", parent=None, pos_global=np.array([0.0, 0.0, 0.0]),
        quat=np.array([1.0, 0.0, 0.0, 0.0]),
        joint_names=["pelvis_tz", "pelvis_ty", "pelvis_tx", "pelvis_tilt", "pelvis_list", "pelvis_rotation"],
        site_names=["biart_1"],
        mass=8.0, com_local=np.array([0.0, 0.05, 0.0]), inertia_local=np.diag([0.4, 0.3, 0.35]),
    )
    femur = SourceBody(
        name="femur", parent="pelvis", pos_global=np.array([0.0, -0.35, 0.25]),
        quat=np.array([1.0, 0.0, 0.0, 0.0]),
        joint_names=["hip_flex", "hip_rot"],
        site_names=["biart_2", "mono_1"],
        mass=6.0, com_local=np.array([0.0, -0.12, 0.0]), inertia_local=np.diag([0.1, 0.03, 0.11]),
    )
    tibia = SourceBody(
        name="tibia", parent="femur", pos_global=np.array([0.0, -0.7, 0.28]),
        quat=np.array([1.0, 0.0, 0.0, 0.0]),
        joint_names=["knee"],
        site_names=["biart_3", "mono_2", "ankle_site"],
        mass=3.0, com_local=np.array([0.0, -0.18, 0.0]), inertia_local=np.diag([0.04, 0.006, 0.042]),
    )
    coils = [
        ("z", np.array([0.0, 0.0, 1.0])), ("y", np.array([0.0, 1.0, 0.0])), ("x", np.array([1.0, 0.0, 0.0])),
    ]
    joints = [
        SourceJoint("pelvis_tz", "pelvis", "slide", coils[0][1], coils[0][1], False, [-3.0, 3.0], np.zeros(3)),
        SourceJoint("pelvis_ty", "pelvis", "slide", coils[1][1], coils[1][1], False, [-1.0, 2.0], np.zeros(3)),
        SourceJoint("pelvis_tx", "pelvis", "slide", coils[2][1], coils[2][1], False, [-10.0, 10.0], np.zeros(3)),
        SourceJoint("pelvis_tilt", "pelvis", "hinge", coils[0][1], coils[0][1], True, [-1.5708, 1.5708], np.zeros(3)),
        SourceJoint("pelvis_list", "pelvis", "hinge", coils[2][1], coils[2][1], True, [-1.5708, 1.5708], np.zeros(3)),
        SourceJoint("pelvis_rotation", "pelvis", "hinge", coils[1][1], coils[1][1], False, [-3.14, 3.14], np.zeros(3)),
        SourceJoint("hip_flex", "femur", "hinge", coils[0][1], coils[0][1], True, [-2.0944, 2.0944], np.zeros(3)),
        SourceJoint("hip_rot", "femur", "hinge", coils[1][1], coils[1][1], True, [-2.0944, 2.0944], np.zeros(3)),
        SourceJoint("knee", "tibia", "hinge", coils[0][1], coils[0][1], True, [-2.0944, 0.174533], np.zeros(3)),
    ]
    sites = [
        SourceSite("biart_1", "pelvis", np.array([0.0, 0.05, 0.35])),
        SourceSite("biart_2", "femur", np.array([0.03, 0.0, 0.05])),
        SourceSite("biart_3", "tibia", np.array([0.02, 0.0, 0.03])),
        SourceSite("mono_1", "femur", np.array([-0.02, -0.05, 0.04])),
        SourceSite("mono_2", "tibia", np.array([0.0, -0.05, 0.02])),
        SourceSite("ankle_site", "tibia", np.array([0.0, -0.30, 0.02])),
    ]
    tendons = [
        SourceTendon("biart_tendon", ["biart_1", "biart_2", "biart_3"]),
        SourceTendon("mono_tendon", ["mono_1", "mono_2"]),
    ]
    muscles = [
        SourceMuscle("biart", "biart_tendon", "100", "0.01 0.04", "0.4 0.6", True, "0 1"),
        SourceMuscle("mono", "mono_tendon", "80", "0.01 0.04", "0.3 0.5", True, "0 1"),
    ]
    ana = SourceAnatomy(
        meta={"source_file": "synth_rig", "revision": "synthetic", "sha256": "", "root_body": "pelvis"},
        bodies=[pelvis, femur, tibia],
        joints=joints,
        sites=sites,
        tendons=tendons,
        muscles=muscles,
    )
    ana.index()
    return ana


def rig_correspondence() -> Correspondence:
    src_lm = {
        "root": "body_origin:pelvis",
        "femur.prox": "body_origin:pelvis",
        "femur.dist": "body_origin:tibia",
        "femur.roll": "site:biart_2",
        "tibia.prox": "body_origin:tibia",
        "tibia.dist": "site:ankle_site",
        "tibia.roll": "site:mono_2",
    }
    land = {
        "root": np.array([0.0, 0.9, 0.0]),
        "femur.prox": np.array([0.0, 0.9, 0.0]),
        "femur.dist": np.array([0.0, 0.0, 0.6]),
        "femur.roll": np.array([0.3, 0.9, 0.0]),
        "tibia.prox": np.array([0.0, 0.0, 0.6]),
        "tibia.dist": np.array([0.0, -0.45, 0.7]),
        "tibia.roll": np.array([0.28, 0.05, 0.6]),
    }
    return Correspondence(
        frame_up=np.array([0.0, 1.0, 0.0]),
        frame_anterior=np.array([1.0, 0.0, 0.0]),
        frame_right=np.array([0.0, 0.0, 1.0]),
        global_scale=1.0,
        handedness="preserve",
        landmarks=land,
        source_landmarks=src_lm,
        root_landmark="root",
        segments=[
            CorrespondenceSegment("femur", "pelvis", "femur.prox", "femur.dist", "femur.roll", ["hip_flex", "hip_rot"]),
            CorrespondenceSegment("tibia", "femur", "tibia.prox", "tibia.dist", "tibia.roll", ["knee"]),
        ],
    )


# ------------------------------------------------------------------- synth whole body
def synth_chimanoid(proportions: dict[str, float] | None = None) -> SourceAnatomy:
    """Counts- and names-matched synthetic twin of the real chimanoid.xml.

    Each body is displaced around its origin by `proportions[name]`; names,
    adjacency, coordinate ownership and tendon paths are preserved exactly.
    """
    props = proportions or {
        "femur_r": 1.12, "tibia_r": 0.92, "talus_r": 1.05, "toes_r": 0.9,
        "femur_l": 1.12, "tibia_l": 0.92, "talus_l": 1.05, "toes_l": 0.9,
        "thorax_dummy": 1.08, "thorax": 1.25,
        "humerus": 1.1, "ulna": 1.05, "radius": 1.0, "hand_r": 0.98,
        "humerus_l": 1.1, "ulna_l": 1.05, "radius_l": 1.0, "hand_l": 0.98,
    }
    real = load_source(REAL_XML)

    new_origin: dict[str, np.ndarray] = {}
    for name in TREE_ORDER:
        b = real.body_by_name[name]
        if b.parent is None:
            new_origin[name] = b.pos_global.copy()
        else:
            par = real.body_by_name[b.parent]
            new_origin[name] = new_origin[b.parent] + props.get(name, 1.0) * (b.pos_global - par.pos_global)

    new_bodies: list[SourceBody] = []
    new_sites: list[SourceSite] = []
    for name in TREE_ORDER:
        b = real.body_by_name[name]
        f = props.get(name, 1.0)
        new_sites += [
            SourceSite(name=s.name, body=b.name, pos_local=f * s.pos_local)
            for s in real.sites
            if s.body == b.name
        ]
        mi = None
        if b.mass is not None:
            mi = (b.mass * f**3, b.com_local * f if b.com_local is not None else None,
                  b.inertia_local * f**5 if b.inertia_local is not None else None)
        new_bodies.append(
            SourceBody(
                name=name,
                parent=b.parent,
                pos_global=new_origin[name],
                quat=b.quat.copy(),
                joint_names=list(b.joint_names),
                site_names=[s.name for s in new_sites if s.body == name],
                mass=mi[0] if mi else None,
                com_local=mi[1] if mi else None,
                inertia_local=mi[2] if mi else None,
            )
        )

    new_joints = [
        SourceJoint(
            name=j.name, body=j.body, joint_type=j.joint_type,
            axis=j.axis.copy(), axis_global=j.axis.copy(),  # quat identity preserved
            limited=j.limited, range=list(j.range), pos_local=j.pos_local.copy(),
        )
        for j in real.joints
    ]

    ana = SourceAnatomy(
        meta={"source_file": "synth_chimanoid", "revision": "synthetic_twin", "sha256": "", "root_body": real.meta["root_body"]},
        bodies=new_bodies,
        joints=new_joints,
        sites=new_sites,
        tendons=[SourceTendon(t.name, list(t.site_names)) for t in real.tendons],
        muscles=[SourceMuscle(m.name, m.tendon, m.force, m.timeconst, m.lengthrange, m.ctrllimited, m.ctrlrange) for m in real.muscles],
    )
    ana.index()
    assert len(ana.bodies) == 19 and len(ana.joints) == 39
    assert len([s for s in ana.sites if s.referenced_by]) == 468
    assert len(ana.tendons) == 120 and len(ana.muscles) == 120
    return ana


# ------------------------------------------------------------------- target landmarks
def generate_target_landmarks(ana: SourceAnatomy, lens: dict[str, float], radials=None, origin=(0.0, 0.0, 0.0)) -> dict[str, np.ndarray]:
    """Generate target landmarks by walking the source tree with per-body bone
    lengths (lens). Roll points are placed off the fitted bone axis (never
    axis-parallel). Leaf bodies extend a tip along their source bone direction.
    """
    radials = radials or {}
    L: dict[str, np.ndarray] = {"root": np.array(origin, dtype=np.float64)}
    P_body: dict[str, np.ndarray] = {ana.root.name: np.array(origin, dtype=np.float64)}
    site_world = global_site_positions(ana)

    bone_info: dict[str, dict] = {}
    for b in ana.bodies:
        src_A = b.pos_global
        child = chain_child(ana, b.name)
        if child is not None:
            src_D = ana.body_by_name[child].pos_global
        else:
            sts = [site_world[s.name] for s in ana.sites if s.body == b.name and s.referenced_by]
            if not sts:
                sts = [b.pos_global + np.array([0.0, -0.05, 0.0])]
            src_D = max(sts, key=lambda p: np.linalg.norm(p - src_A))
        n = src_D - src_A
        nn = np.linalg.norm(n)
        roll_site = _pick_roll_site(ana, b, site_world)
        q_ref = site_world[roll_site] if roll_site is not None else src_A + n / 2.0
        bone_info[b.name] = {
            "A": src_A, "D": src_D,
            "dir": (n / nn) if nn > 1e-12 else np.array([0.0, -1.0, 0.0]),
            "len": nn, "q": q_ref,
        }

    def prox_id(b: str) -> str:
        return f"{b}.prox"

    def dist_id(b: str) -> str:
        return f"{b}.dist"

    def roll_id(b: str) -> str:
        return f"{b}.roll"

    # seed direct children of root (their origin == root origin point)
    for child in [b.name for b in ana.bodies if b.parent == ana.root.name]:
        info = bone_info[child]
        P_body[child] = P_body[ana.root.name] + lens.get(child, info["len"]) * info["dir"]

    def place(body: str) -> None:
        P_here = P_body[body]
        ln = lens.get(body, bone_info[body]["len"])
        child = chain_child(ana, body)
        for c in [b.name for b in ana.bodies if b.parent == body]:
            ci = bone_info[c]
            P_body[c] = P_here + lens.get(c, ci["len"]) * ci["dir"]
        if child is not None:
            P_child = P_body[child]
            dst = P_child
            a_tgt = (P_child - P_here) / max(np.linalg.norm(P_child - P_here), 1e-12)
        else:
            dst = P_here + ln * bone_info[body]["dir"]
            a_tgt = (dst - P_here) / max(np.linalg.norm(dst - P_here), 1e-12)
        L[prox_id(body)] = P_here
        L[dist_id(body)] = dst
        info = bone_info[body]
        ref = np.array([0.0, 0.0, 1.0]) if abs(a_tgt @ np.array([0.0, 1.0, 0.0])) > 0.98 else np.array([0.0, 1.0, 0.0])
        bvec = np.cross(ref, a_tgt)
        bn = np.linalg.norm(bvec)
        bvec = (bvec / bn) if bn > 1e-9 else np.array([1.0, 0.0, 0.0])
        q_src = info["q"] - info["A"]
        ax = q_src @ info["dir"]
        perp = np.linalg.norm(q_src - ax * info["dir"])
        radial = radials.get(body, 1.0)
        L[roll_id(body)] = P_here + a_tgt * ax + bvec * (perp * radial)

    for name in TREE_ORDER:
        if name != ana.root.name:
            place(name)
    return L


def make_full_body_correspondence(ana: SourceAnatomy, lens, radials=None, origin=(0.0, 0.0, 0.0), rot=None) -> Correspondence:
    """One correspondence object; works against BOTH the real intake and the
    synthetic twin because every source resolution is by NAME, and the fixtures
    share names."""
    rot = np.eye(3) if rot is None else np.asarray(rot, dtype=np.float64)
    L0 = generate_target_landmarks(ana, lens, radials, origin)
    L = {k: v.copy() for k, v in L0.items()}
    if not np.all(rot == np.eye(3)):
        L = {k: rot @ v for k, v in L0.items()}
        up = rot @ np.array([0.0, 1.0, 0.0])
        ant = rot @ np.array([1.0, 0.0, 0.0])
        rgt = rot @ np.array([0.0, 0.0, 1.0])
    else:
        up, ant, rgt = np.array([0.0, 1.0, 0.0]), np.array([1.0, 0.0, 0.0]), np.array([0.0, 0.0, 1.0])

    site_world = global_site_positions(ana)
    src_lm: dict[str, str] = {"root": f"body_origin:{ana.root.name}"}
    segments: list[CorrespondenceSegment] = []
    for b in ana.bodies:
        if b.parent is None:
            continue
        child = chain_child(ana, b.name)
        prox_rid, dist_rid, roll_rid = f"{b.name}.prox", f"{b.name}.dist", f"{b.name}.roll"
        src_lm[prox_rid] = f"body_origin:{b.name}"
        if child is not None:
            src_lm[dist_rid] = f"body_origin:{child}"
        else:
            own = [s for s in ana.sites if s.body == b.name and s.referenced_by]
            if not own:
                raise Refusal("unresolvable_leaf", f"leaf body {b.name} has no referencing sites for a distal landmark")
            farthest = max(own, key=lambda s: np.linalg.norm(site_world[s.name] - b.pos_global))
            src_lm[dist_rid] = f"site:{farthest.name}"
        roll_site = _pick_roll_site(ana, b, site_world)
        if roll_site is None:
            raise Refusal("unresolvable_roll", f"body {b.name} has no off-axis roll site")
        src_lm[roll_rid] = f"site:{roll_site}"
        segments.append(
            CorrespondenceSegment(
                source_body=b.name,
                parent=b.parent,
                proximal_landmark=prox_rid,
                distal_landmark=dist_rid,
                roll_ref=roll_rid,
                coords=list(ana.body_by_name[b.name].joint_names),
            )
        )

    return Correspondence(
        frame_up=up,
        frame_anterior=ant,
        frame_right=rgt,
        global_scale=1.0,
        handedness="preserve",
        landmarks=L,
        source_landmarks=src_lm,
        root_landmark="root",
        segments=segments,
        note="generated by synthetic_fixtures.make_full_body_correspondence",
    )


TARGET_LENS = {
    "femur_r": 0.52, "femur_l": 0.52,
    "tibia_r": 0.26, "tibia_l": 0.26,
    "talus_r": 0.34, "talus_l": 0.34,
    "toes_r": 0.16, "toes_l": 0.16,
    "thorax_dummy": 0.16,
    "thorax": 0.40,
    "humerus": 0.30, "humerus_l": 0.30,
    "ulna": 0.35, "ulna_l": 0.35,
    "radius": 0.06, "radius_l": 0.06,
    "hand_r": 0.30, "hand_l": 0.30,
    "pelvis": 0.0,
}
TARGET_RADIALS = {"thorax": 1.35, "pelvis": 1.2}
SYNTH_SOURCE_PROPORTIONS = {
    "femur_r": 1.12, "femur_l": 1.12, "tibia_r": 0.94, "tibia_l": 0.94,
    "thorax_dummy": 1.06, "thorax": 1.22, "humerus": 1.10, "humerus_l": 1.10,
}


def load_real() -> SourceAnatomy:
    return load_source(REAL_XML)