"""skin.py — the SKIN membrane: from rigid parts to a POSABLE splat teddy.

THEORY (Rule 0 — stated before the build, per docs/research/rigging_static_objects_reference.md):
  STATEMENT  — the rigid nearest-bone partition cracks at the joints under rotation (rigid
               skinning is for mechanisms; a plush toy is not one). A SMOOTH LBS band at
               each joint — two influences, exp falloff, band width = 0.8 x the limb's
               MEASURED cross-section radius at the joint (the seam a bend opens is
               ~r*theta), weights normalized to 1 — articulates the teddy without visible
               seam cracks, and transporting each Gaussian's ROTATION by the weighted
               quaternion average of its influencing bones (Moverse: blending rotation
               matrices is not a valid rotation) keeps splat orientation glued to the
               surface.
  PREDICTION — a posed orbit (e.g. shoulder 30 deg + elbow 60 deg) renders with continuous
               fur across the band: no background showing through the joint, no candy-
               wrapper collapse, no visibly rotated-flat splats.
  FALSIFIER  — if the posed orbit shows a crack/gap at a joint band or volume collapse,
               LBS-with-band is falsified for this asset -> escalate to DQS (Kavan 2008).
               Band too wide/narrow is a derivation fix, not a falsification.

WHAT IS TRANSFORMED (the 3DGS skinning consensus, see the research note):
  mean      <- LBS with the smooth weights (2 influences)
  rotation  <- premultiplied by the weighted, sign-aligned, normalized quaternion blend
  scale, opacity, color <- UNTOUCHED (rotation-invariant; scale rides with the mean)

STAGES:
  weights  skeleton + part_assignment -> per-splat (bone0, w0, bone1, w1)  -> skin_weights.npz
  pose     apply a pose spec (FK over the bone tree) -> posed buffer -> orbit frames
           -> <dir>/pose_<name>/fNN.png  (the eye judges in section.py style)

Usage (from the repo root):
  python ChimeraEngine/native/skin.py weights models/imagegen/tpose2_640.splat \
      --dir models/imagegen/tpose2_640_section --skeleton models/imagegen/tpose2_640_rig/skeleton_sym.json
  python ChimeraEngine/native/skin.py pose models/imagegen/tpose2_640.splat \
      --dir models/imagegen/tpose2_640_section --skeleton ... --spec pose_wave.json

Pose spec JSON: {"name": "wave", "rotations": {"elbow_right": {"deg": 60},
  "shoulder_right": {"deg": 30, "axis": [0,0,1]}}}
  axis = rest-world rotation axis at the joint; OMITTED -> the derived hinge axis
  (stickfigure.hinge_axes: bone_dir x up, fallback bone_dir x front).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_CHIMERA_ENGINE = _HERE.parent
if str(_CHIMERA_ENGINE) not in sys.path:
    sys.path.insert(0, str(_CHIMERA_ENGINE))

import cpp_bridge as cb                     # noqa: E402
from section import SKEL_BONES, SKEL_TIPS, RING_PARTS, _body_mask, _orbit, _upload  # noqa: E402
from stickfigure import hinge_axes          # noqa: E402

# ── the bone tree (FK) ---------------------------------------------------------------
# bone -> (pivot joint, end joint, parent bone). Root = torso, pivot = hip_center.
BONE_TREE = {
    "torso": ("hip_center", "neck", None),
    "head": ("neck", "head_center", "torso"),
    "uparm_left": ("shoulder_left", "elbow_left", "torso"),
    "farm_left": ("elbow_left", "hand_left", "uparm_left"),
    "uparm_right": ("shoulder_right", "elbow_right", "torso"),
    "farm_right": ("elbow_right", "hand_right", "uparm_right"),
    "thigh_left": ("hip_center", "knee_left", "torso"),
    "shin_left": ("knee_left", "foot_left", "thigh_left"),
    "thigh_right": ("hip_center", "knee_right", "torso"),
    "shin_right": ("knee_right", "foot_right", "thigh_right"),
}
BONES = [b[0] for b in SKEL_BONES]                    # section.py's order = bone indices
# which bone each part label skins to (tips ride their parent limb bone; face rides the head)
PART_TO_BONE = {p: p for p in BONES}
for bone, (_j, tip) in SKEL_TIPS.items():
    PART_TO_BONE[tip] = bone
for rp in RING_PARTS:
    PART_TO_BONE[rp] = "head"
# joint -> the two bones that meet there (the blend pair across the joint)
JOINT_BONES = {
    "neck": ["head", "torso"],
    "shoulder_left": ["uparm_left", "torso"],       # clavicle is rigid with the torso
    "shoulder_right": ["uparm_right", "torso"],
    "elbow_left": ["farm_left", "uparm_left"], "elbow_right": ["farm_right", "uparm_right"],
    "knee_left": ["shin_left", "thigh_left"], "knee_right": ["shin_right", "thigh_right"],
    # hip_center (torso + both thighs) stays a rigid hub: the plush crotch has no hinge
}
BIPED_FK_ORDER = ["torso", "head", "uparm_left", "farm_left", "uparm_right", "farm_right",
                  "thigh_left", "shin_left", "thigh_right", "shin_right"]

# QUADRUPED (koala = instance #2, stickfigure_quad.py joints; spine horizontal along z).
# Root = torso pivoting at the pelvis; the chest/pelvis hub stays rigid (no waist hinge).
QUAD_BONE_TREE = {
    "torso": ("pelvis", "neck", None),
    "head": ("neck", "head_center", "torso"),
    "thigh_f_left": ("shoulder_f_left", "elbow_f_left", "torso"),
    "shin_f_left": ("elbow_f_left", "foot_f_left", "thigh_f_left"),
    "thigh_f_right": ("shoulder_f_right", "elbow_f_right", "torso"),
    "shin_f_right": ("elbow_f_right", "foot_f_right", "thigh_f_right"),
    "thigh_b_left": ("hip_b_left", "knee_b_left", "torso"),
    "shin_b_left": ("knee_b_left", "foot_b_left", "thigh_b_left"),
    "thigh_b_right": ("hip_b_right", "knee_b_right", "torso"),
    "shin_b_right": ("knee_b_right", "foot_b_right", "thigh_b_right"),
}
QUAD_FK_ORDER = ["torso", "head",
                 "thigh_f_left", "thigh_f_right", "thigh_b_left", "thigh_b_right",
                 "shin_f_left", "shin_f_right", "shin_b_left", "shin_b_right"]
QUAD_JOINT_BONES = {
    "neck": ["head", "torso"],
    "shoulder_f_left": ["thigh_f_left", "torso"], "shoulder_f_right": ["thigh_f_right", "torso"],
    "elbow_f_left": ["shin_f_left", "thigh_f_left"], "elbow_f_right": ["shin_f_right", "thigh_f_right"],
    "hip_b_left": ["thigh_b_left", "torso"], "hip_b_right": ["thigh_b_right", "torso"],
    "knee_b_left": ["shin_b_left", "thigh_b_left"], "knee_b_right": ["shin_b_right", "thigh_b_right"],
}


def _skin_spec(skel: dict) -> dict:
    """Species-parameterized skinning tables, selected from the skeleton JSON's `species`."""
    if skel.get("species", "biped") == "quadruped":
        from section import QUAD_SKEL_BONES, QUAD_SKEL_TIPS
        bones = [b[0] for b in QUAD_SKEL_BONES]
        tree, order, joints, tips = QUAD_BONE_TREE, QUAD_FK_ORDER, QUAD_JOINT_BONES, QUAD_SKEL_TIPS
    else:
        bones, tree, order, joints, tips = BONES, BONE_TREE, BIPED_FK_ORDER, JOINT_BONES, SKEL_TIPS
    part_to_bone = {p: p for p in bones}
    for bone, (_j, tip) in tips.items():
        part_to_bone[tip] = bone
    for rp in RING_PARTS:
        part_to_bone[rp] = "head"
    return {"bones": bones, "tree": tree, "order": order, "joints": joints,
            "part_to_bone": part_to_bone, "species": skel.get("species", "biped")}


def _quad_hinge_axes(J: dict, tree: dict) -> dict:
    """stickfigure.hinge_axes' rule (axis = bone_dir x up, fallback bone_dir x front) over
    the quadruped tree — its module BONES list is biped-only."""
    up = np.array([0.0, 1.0, 0.0])
    front = np.array([0.0, 0.0, 1.0])
    touch = {}
    for _b, (piv, end, _p) in tree.items():
        if piv in J and end in J:
            d = np.array(J[end]) - np.array(J[piv])
            n = float(np.linalg.norm(d))
            if n > 1e-9:
                touch.setdefault(piv, (d / n, n))
                touch.setdefault(end, (d / n, n))
    axes = {}
    for j, (d, ln) in touch.items():
        ax = np.cross(d, up)
        if np.linalg.norm(ax) < 1e-6:
            ax = np.cross(d, front)
        n = float(np.linalg.norm(ax))
        if n < 1e-9:
            continue
        axes[j] = (np.array(J[j]), ax / n, 0.4 * ln)
    return axes


# ── quaternion helpers ([w,x,y,z], vectorized) ----------------------------------------

def _qmul(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    aw, ax, ay, az = np.moveaxis(a, -1, 0)
    bw, bx, by, bz = np.moveaxis(b, -1, 0)
    return np.stack([aw * bw - ax * bx - ay * by - az * bz,
                     aw * bx + ax * bw + ay * bz - az * by,
                     aw * by - ax * bz + ay * bw + az * bx,
                     aw * bz + ax * by - ay * bx + az * bw], axis=-1)


def _qrot(q: np.ndarray, p: np.ndarray) -> np.ndarray:
    """Rotate points p (...,3) by quaternion q (...,4)."""
    u, w = q[..., 1:], q[..., :1]
    return p + 2.0 * np.cross(u, np.cross(u, p) + w * p)


def _axis_angle(axis: np.ndarray, deg: float) -> np.ndarray:
    axis = axis / np.linalg.norm(axis)
    h = np.deg2rad(deg) / 2.0
    return np.array([np.cos(h), *(np.sin(h) * axis)])


# ── STAGE: weights --------------------------------------------------------------------

def stage_weights(splat_path: str, workdir: Path, skeleton_path: str):
    skel = json.loads(Path(skeleton_path).read_text(encoding="utf-8"))
    J = {k: np.array(v, dtype=np.float64) for k, v in skel["joints"].items()}
    spec = _skin_spec(skel)
    bones, tree, joints, part_to_bone = spec["bones"], spec["tree"], spec["joints"], spec["part_to_bone"]
    print(f"  species: {spec['species']} ({len(bones)} bones)")
    buf = cb.load_splat(splat_path)
    pos = buf[:, 0:3].astype(np.float64)
    n = len(pos)
    label = np.load(workdir / "part_assignment.npy")
    parts = json.loads((workdir / "parts.json").read_text(encoding="utf-8"))["parts"]
    part_of = {nm: i for i, nm in enumerate(parts)}

    # primary bone: the part's bone (labels); giant fillers / unlabeled -> nearest segment
    bidx = np.full(n, -1, dtype=np.int32)
    for nm, i in part_of.items():
        if nm in part_to_bone:
            bidx[label == i] = bones.index(part_to_bone[nm])
    A = np.array([J[tree[b][0]] for b in bones])
    Bv = np.array([J[tree[b][1]] for b in bones])
    V = Bv - A
    L2 = (V * V).sum(1)
    W = pos[:, None, :] - A[None]
    t = np.clip(np.einsum("nbk,bk->nb", W, V) / L2[None], 0.0, 1.0)   # (n, bones) projection
    dseg = np.linalg.norm(W - t[:, :, None] * V[None], axis=2)
    miss = bidx < 0
    bidx[miss] = np.argmin(dseg[miss], axis=1)
    print(f"  primary: {int((~miss).sum())} from parts, {int(miss.sum())} nearest-segment")

    # secondary influence inside the joint band. DERIVATION (Rule 1, not taste): the seam a
    # rotation theta opens at a joint is ~ r_limb * theta, so the blend band ALONG the bone
    # must be comparable to the limb's cross-section radius AT the joint — MEASURED as the
    # median perpendicular distance of the joint-side third of each adjacent bone's splats
    # (the SMALLER side governs: the neck, not the head ball). band = 0.8 * r_joint (covers
    # bends to ~1 rad), distance = |along-bone distance from the joint plane| —
    # distance-to-joint-POINT was wrong (the joint is buried a limb-radius under the skin;
    # measured 2026-08-19: 1 splat in the band).
    rad = {bi: np.linalg.norm(W[:, bi, :] - t[:, bi, None] * V[None, bi, :], axis=1)
           for bi in range(len(bones))}
    w1 = np.zeros(n, dtype=np.float32)
    b2 = np.full(n, -1, dtype=np.int32)
    for joint, pair in joints.items():
        b0, b1 = (bones.index(pair[0]), bones.index(pair[1]))
        # radius AT the joint, per bone: median radial distance of the splats in the third
        # of the bone nearest the joint; the band scales with the SMALLER side (the neck,
        # not the head ball; the arm, not the torso)
        rs = []
        for me in (b0, b1):
            u = V[me] / float(np.sqrt(L2[me]))
            d_along = np.abs((pos - J[joint]) @ u)
            near = (bidx == me) & (d_along < 0.3 * float(np.sqrt(L2[me])))
            rs.append(float(np.median(rad[me][near])) if near.any() else np.inf)
        band = 0.8 * min(rs)
        for me, other in ((b0, b1), (b1, b0)):
            u = V[me] / float(np.sqrt(L2[me]))
            d = np.abs((pos - J[joint]) @ u)            # along-bone distance to the joint plane
            dp = np.linalg.norm(pos - J[joint], axis=1)  # lateral gate: the joint REGION only
            sel = (bidx == me) & (d < band) & (dp < 2.0 * band)
            w = 0.5 * np.exp(-3.0 * d[sel] / band)      # 0.5 AT the joint -> ~0.02 at band edge
            upd = w > w1[sel]
            idx = np.flatnonzero(sel)[upd]
            w1[idx] = w[upd]
            b2[idx] = other
        print(f"  band {joint}: {int((np.isin(bidx, [b0, b1]) & (w1 > 0)).sum())} splats "
              f"(band={band:.4f})")

    w0 = 1.0 - w1
    np.savez(workdir / "skin_weights.npz",
             bone0=bidx, w0=w0.astype(np.float32),
             bone1=b2.astype(np.int32), w1=w1.astype(np.float32),
             bones=np.array(bones))
    print(f"weights -> {workdir / 'skin_weights.npz'} "
          f"({int((w1 > 0).sum())} blended, {int((w1 == 0).sum())} rigid)")


# ── STAGE: pose -----------------------------------------------------------------------

def _fk(J: dict, rotations: dict, spec: dict) -> dict:
    """Pose spec -> per-bone delta transform (quat, offset): p' = Q.p + t, world frame."""
    tree, order = spec["tree"], spec["order"]
    axes = hinge_axes(J) if spec["species"] == "biped" else _quad_hinge_axes(J, tree)
    Q, T = {}, {}

    def posed_joint(j: str, home: str) -> np.ndarray:
        return _qrot(Q[home], J[j]) + T[home]

    for bone in order:
        piv, _end, parent = tree[bone]
        rot = rotations.get(piv, {})
        if rot:
            axis = np.array(rot["axis"]) if "axis" in rot else axes[piv][1]
            q = _axis_angle(axis, float(rot.get("deg", 0.0)))
        else:
            q = np.array([1.0, 0.0, 0.0, 0.0])
        if parent is None:
            Q[bone] = q
            T[bone] = J[piv] - _qrot(q, J[piv])
        else:
            Q[bone] = _qmul(Q[parent], q)
            pp = posed_joint(piv, parent)
            T[bone] = pp - _qrot(Q[bone], J[piv])
    return {b: (Q[b], T[b]) for b in order}


def apply_pose(buf: np.ndarray, J: dict, wz: np.ndarray, rotations: dict, spec: dict) -> np.ndarray:
    D = _fk(J, rotations, spec)
    pos = buf[:, 0:3].astype(np.float64)
    rot = buf[:, 10:14].astype(np.float64)
    out = buf.copy()
    p_new = np.zeros_like(pos)
    q_delta = np.zeros((len(pos), 4))
    q_ref = np.array([1.0, 0.0, 0.0, 0.0])            # sign-align every contribution to bone0's quat
    aligned_ref = np.tile(q_ref, (len(pos), 1))
    have_ref = np.zeros(len(pos), dtype=bool)
    for bi, bone in enumerate(spec["bones"]):
        q, tt = D[bone]
        for col_b, col_w in (("bone0", "w0"), ("bone1", "w1")):
            sel = wz[col_b] == bi
            if not sel.any():
                continue
            if col_b == "bone0":
                aligned_ref[sel] = q
                have_ref[sel] = True
                s = 1.0
            else:
                s = np.sign(aligned_ref[sel] @ q)
                s[s == 0.0] = 1.0
            p_new[sel] += wz[col_w][sel, None] * (_qrot(q, pos[sel]) + tt)
            q_delta[sel] += (wz[col_w][sel] * s)[:, None] * q
    q_delta[~have_ref] = q_ref                        # splats with no weights row (shouldn't happen)
    q_delta = q_delta / np.maximum(np.linalg.norm(q_delta, axis=1, keepdims=True), 1e-12)
    out[:, 0:3] = p_new.astype(np.float32)
    out[:, 10:14] = _qmul(q_delta, rot).astype(np.float32)
    return out


def stage_pose(splat_path: str, workdir: Path, skeleton_path: str, spec_path: str):
    pose_spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    name = pose_spec.get("name", "pose")
    skel = json.loads(Path(skeleton_path).read_text(encoding="utf-8"))
    J = {k: np.array(v, dtype=np.float64) for k, v in skel["joints"].items()}
    spec = _skin_spec(skel)
    wz = np.load(workdir / "skin_weights.npz")
    buf = cb.load_splat(splat_path)
    posed = apply_pose(buf, J, wz, pose_spec.get("rotations", {}), spec)
    # the 314 giant low-alpha filler splats are generator junk, not surface (section.py
    # _body_mask); static they are invisible haze, but POSED they streak (measured
    # 2026-08-19: a mag-0.30 filler bound to the head painted a line across the frame).
    # Hide them in posed renders only — the rest pose is untouched.
    hidden = ~_body_mask(buf)
    posed[hidden, 6] = 0.0
    print(f"  hidden {int(hidden.sum())} giant filler splats in the posed render")
    np.save(workdir / f"pose_{name}.npy", posed)
    _upload(posed)
    frames = _orbit(workdir, f"pose_{name}", tag=True)
    print(f"pose {name} -> {workdir / ('pose_' + name)} ({len(frames)} frames)")


# ── CLI --------------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("stage", choices=["weights", "pose"])
    ap.add_argument("target", help="path to the ORIGINAL .splat")
    ap.add_argument("--dir", required=True, help="section workdir (parts.json, part_assignment.npy)")
    ap.add_argument("--skeleton", required=True, help="skeleton JSON (stickfigure.py build)")
    ap.add_argument("--spec", default=None, help="pose: pose spec JSON")
    a = ap.parse_args()
    workdir = Path(a.dir)
    if a.stage == "weights":
        stage_weights(a.target, workdir, a.skeleton)
    else:
        if not a.spec:
            raise SystemExit("pose needs --spec")
        stage_pose(a.target, workdir, a.skeleton, a.spec)


if __name__ == "__main__":
    main()
