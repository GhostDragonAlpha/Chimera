"""core/rig.py — THE SPINE: one skeleton for physics, flesh, and render.

The system audit (2026-07-14) found the skeleton was a FORK, not a spine: the brain moved
capsules in physics, the flesh was a static sculpture in UE5, and the two never met. This
binds them. The SAME evolved skeleton the brain learned to actuate is voxel-scaffolded,
wrapped in flesh by adhesion, meshed, and SKINNED — so posing the skeleton deforms the
flesh. Drive that skeleton with the brain's own gait, and the creature that learned to walk
is the creature you see walking.

Proven headless first (the studio's discipline), on the REAL evolved body from
walker.trained.json — closing the audit's GAP #2: the flesh pipeline had been standing on a
toy 3-bone limb, not the 17-bone creature the brain actually trained on.

    grow (evolved skeleton) -> voxel scaffold -> adhesion flesh -> mesh -> SKIN to skeleton
                                                                              -> pose by the brain
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from core import bake, matter
from core.matter import BONE, MEDIUM, MUSCLE, SKIN
from core.trainables.brain_cpu import _bones as _evolved_bones


def evolved_skeleton():
    """The real 17-bone body from walker.trained.json — the one the brain trained on."""
    bones, size = _evolved_bones()
    return bones, size


def voxelize_skeleton(bones, target_len=84, flesh_cells=5.0, bone_min=1.6,
                      fractions=(0.5, 0.5), seed=0, pad=4):
    """Evolved skeleton -> a 3D lattice. A cell is BONE within its local bone radius of any
    segment (floored at bone_min so the thin evolved bones survive voxelisation), FLESH in
    the sheath out to flesh_cells beyond that, medium otherwise. The flesh is a scrambled
    muscle/skin pepper for adhesion to sort. Returns (grid, shape, targets, scale, offset).

    The sheath thickness is in CELLS, not proportional to the (tiny) bone radius — the flesh
    is what you see, and it should not vanish just because the evolved limbs are threads."""
    rng = np.random.RandomState(seed)
    segs = [(np.asarray(b.p0, float), np.asarray(b.p1, float),
             max(b.r0, b.r1)) for b in bones]
    pts = np.array([q for a, b, _ in segs for q in (a, b)])
    lo, hi = pts.min(0), pts.max(0)
    scale = target_len / max((hi - lo).max(), 1e-6)

    reach = flesh_cells + max(s[2] * scale for s in segs) + pad
    offset = -lo * scale + reach
    A = [a * scale + offset for a, _, _ in segs]
    B = [b * scale + offset for _, b, _ in segs]
    R = [max(r * scale, bone_min) for _, _, r in segs]
    D = tuple(int(x) for x in np.ceil((hi - lo) * scale + 2 * reach).astype(int) + 1)

    zz, yy, xx = np.mgrid[0:D[0], 0:D[1], 0:D[2]]
    P = np.stack([zz, yy, xx], -1).reshape(-1, 3).astype(np.float32)
    sd = np.full(len(P), np.inf, np.float32)                 # signed distance to bone surface
    for a, b, r in zip(A, B, R):
        ab = b - a
        t = np.clip((P - a) @ ab / (ab @ ab + 1e-9), 0, 1)
        d = np.linalg.norm(P - (a + t[:, None] * ab), axis=1) - r
        sd = np.minimum(sd, d)

    g = np.full(len(P), MEDIUM, np.int16)
    flesh = (sd > 0) & (sd <= flesh_cells)
    g[flesh] = rng.choice((MUSCLE, SKIN), size=int(flesh.sum()),
                          p=np.asarray(fractions) / sum(fractions)).astype(np.int16)
    g[sd <= 0] = BONE
    g = g.reshape(D)
    targets = {t: int((g == t).sum()) for t in (BONE, MUSCLE, SKIN)}
    return g, D, targets, scale, offset


def flesh_the_body(bones, sweeps=60, seed=0, **kw):
    """Voxelize the evolved skeleton and wrap it in flesh by differential adhesion, the
    bone frozen (the spine holds the axis). Returns (fleshed_grid, shape, scale, offset)."""
    grid, shape, targets, scale, offset = voxelize_skeleton(bones, seed=seed, **kw)
    fleshed = matter.assemble_3d(grid, shape, targets, matter.J_DIFFERENTIAL_3D,
                                 sweeps=sweeps, seed=seed, frozen_type=BONE)
    return fleshed, shape, scale, offset


def skin_surface(grid, sigma=0.9):
    """The outer skin surface (tissue vs medium) as a smooth mesh — the visible creature."""
    out = bake._surface(grid != MEDIUM, sigma)
    if out is None:
        return None
    v, f = out
    return v.astype(np.float32), f.astype(np.int32)


# --- the spine: bind the flesh to the skeleton, then pose it -------------------
# Standard skeletal animation. Each bone has a REST bind frame; posing applies a rotation
# at each joint and forward-kinematics accumulates it down the hierarchy; linear blend
# skinning moves each vertex by its bones' weighted transforms. The joint axes are the same
# flexion axes the MJCF physics body uses (cross of parent and own direction), so a pose
# from the brain's sim maps onto this mesh without a coordinate-frame fight.

def _rot3(axis, ang):
    a = axis / (np.linalg.norm(axis) + 1e-9)
    x, y, z = a
    c, s, C = np.cos(ang), np.sin(ang), 1 - np.cos(ang)
    return np.array([[c + x*x*C, x*y*C - z*s, x*z*C + y*s],
                     [y*x*C + z*s, c + y*y*C, y*z*C - x*s],
                     [z*x*C - y*s, z*y*C + x*s, c + z*z*C]])


def _frame(origin, d):
    z = d / (np.linalg.norm(d) + 1e-9)
    up = np.array([0, 0, 1.0]) if abs(z[2]) < 0.9 else np.array([1.0, 0, 0])
    x = np.cross(up, z); x /= np.linalg.norm(x) + 1e-9
    M = np.eye(4)
    M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = x, np.cross(z, x), z, origin
    return M


def skeleton_frames(bones, scale, offset):
    """Rest bind frames (lattice space), parents, local joint axes, and each bone's local
    rest transform relative to its parent — everything forward kinematics needs."""
    n = len(bones)
    raw = [(-1 if i == 0 else (b.parent if 0 <= b.parent < i else 0)) for i, b in enumerate(bones)]
    par = [(-1 if i == 0 else (raw[i] if raw[i] >= 1 else 0)) for i in range(n)]
    p0 = [np.asarray(b.p0) * scale + offset for b in bones]
    p1 = [np.asarray(b.p1) * scale + offset for b in bones]
    d = [(p1[i] - p0[i]) for i in range(n)]
    B = [_frame(p0[i], d[i]) for i in range(n)]
    info = []
    for i in range(n):
        pj = par[i]
        Lrest = np.linalg.inv(B[pj]) @ B[i] if pj >= 0 else B[i].copy()
        if pj >= 0:
            ax = np.cross(d[pj], d[i])
            ax = ax / (np.linalg.norm(ax) + 1e-9) if np.linalg.norm(ax) > 1e-6 else np.array([0, 1.0, 0])
        else:
            ax = np.array([0, 1.0, 0])
        ax_local = B[i][:3, :3].T @ ax
        info.append({"parent": pj, "B": B[i], "Binv": np.linalg.inv(B[i]),
                     "Lrest": Lrest, "axis_local": ax_local})
    return info


def skin_weights(verts, bones, scale, offset, k=4):
    """Per-vertex bone weights: the k nearest bone segments, inverse-square distance,
    normalised. This is auto-skinning — no hand-painted weights."""
    segs = [(np.asarray(b.p0) * scale + offset, np.asarray(b.p1) * scale + offset)
            for b in bones]
    dists = np.empty((len(segs), len(verts)), np.float32)
    for i, (a, bb) in enumerate(segs):
        ab = bb - a
        t = np.clip((verts - a) @ ab / (ab @ ab + 1e-9), 0, 1)
        dists[i] = np.linalg.norm(verts - (a + t[:, None] * ab), axis=1)
    idx = np.argsort(dists, axis=0)[:k].T                    # (N, k) nearest bone indices
    dk = np.take_along_axis(dists.T, idx, axis=1)            # (N, k)
    w = 1.0 / (dk ** 2 + 1e-4)
    w /= w.sum(axis=1, keepdims=True)
    return idx.astype(np.int32), w.astype(np.float32)


def fk(info, dtheta):
    """Forward kinematics -> per-bone skinning matrix M_b = Posed_b @ Rest_b^{-1}."""
    n = len(info)
    P = [None] * n
    M = np.empty((n, 4, 4), np.float32)
    for b in range(n):
        s = info[b]
        if s["parent"] < 0:
            P[b] = s["B"]
        else:
            anim = np.eye(4)
            anim[:3, :3] = _rot3(s["axis_local"], dtheta[b])
            P[b] = P[s["parent"]] @ s["Lrest"] @ anim
        M[b] = P[b] @ s["Binv"]
    return M


def pose_mesh(verts, widx, ww, M):
    """Linear blend skinning: each vertex moved by its bones' weighted transforms."""
    vh = np.concatenate([verts, np.ones((len(verts), 1), np.float32)], axis=1)  # (N,4)
    Mv = M[widx]                                             # (N,k,4,4)
    moved = np.einsum("nkij,nj->nki", Mv, vh)[..., :3]       # (N,k,3)
    return (ww[..., None] * moved).sum(axis=1)               # (N,3)


def gait_angles(bones, trained="brain_gpu.trained.json", n_frames=6):
    """Run the TRAINED brain on the evolved body in MuJoCo and record its joint angles
    across the gait. These are the same hinge angles the mesh's forward kinematics consumes
    (mjcf and skeleton_frames build the joint axes identically), so the brain that learned
    to walk now poses the flesh — the two halves, joined."""
    import json
    import math
    import mujoco

    from core import mjcf as MJ
    from core.gait_mj import _mlp
    from core.trainables.brain_cpu import N_HID, TARGET_AMP, shape as brain_shape
    from core.trainables.walker import DT, SETTLE_STEPS, SIM_STEPS

    root = Path(__file__).resolve().parents[1]
    w = json.loads((root / "docs" / "objectives" / trained).read_text(encoding="utf-8"))["genome"]["w"]
    zmin = min(min(b.p0[2], b.p1[2]) for b in bones)
    mjm = mujoco.MjModel.from_xml_string(MJ.from_bones(bones, lift=-zmin + 0.05, dt=DT))
    mjd = mujoco.MjData(mjm)
    nj, n_in = mjm.nu, brain_shape()[0]
    W1, b1, W2, b2 = _mlp(w, n_in, nj)

    for _ in range(SETTLE_STEPS):
        mujoco.mj_step(mjm, mjd)
    grab = {int(k * (SIM_STEPS - 1) / (n_frames - 1)) for k in range(n_frames)}
    obs, frames = np.empty(n_in), []
    for step in range(SIM_STEPS):
        obs[:nj] = mjd.qpos[7:7 + nj]
        obs[nj:2 * nj] = mjd.qvel[6:6 + nj] * 0.1
        obs[2 * nj:2 * nj + 3] = mjd.xmat[1].reshape(3, 3)[:, 2]
        t = step * DT
        obs[2 * nj + 3] = math.sin(6.2831853 * t)
        obs[2 * nj + 4] = math.cos(6.2831853 * t)
        mjd.ctrl[:] = np.tanh(W2 @ np.tanh(W1 @ obs + b1) + b2) * TARGET_AMP
        mujoco.mj_step(mjm, mjd)
        if step in grab:
            frames.append(mjd.qpos[7:7 + nj].copy())
    return np.asarray(frames)                                # (n_frames, nj)


def render_mesh(views, path: Path, elev=18):
    """A headless 3D render of the fleshed creature from a few angles (matplotlib Agg —
    no display needed). A number is not proof (H-14); you must see the body."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    fig = plt.figure(figsize=(5 * len(views), 5), facecolor="#0c0c0e")
    for i, (label, verts, faces, azim) in enumerate(views, 1):
        ax = fig.add_subplot(1, len(views), i, projection="3d", facecolor="#0c0c0e")
        tri = Poly3DCollection(verts[faces], alpha=1.0)
        tri.set_facecolor((0.80, 0.62, 0.47))
        tri.set_edgecolor((0.5, 0.38, 0.29, 0.15))
        ax.add_collection3d(tri)
        lo, hi = verts.min(0), verts.max(0)
        c, r = (lo + hi) / 2, (hi - lo).max() / 2
        for setlim, m in ((ax.set_xlim, 0), (ax.set_ylim, 1), (ax.set_zlim, 2)):
            setlim(c[m] - r, c[m] + r)
        ax.set_axis_off()
        ax.view_init(elev=elev, azim=azim)
        ax.set_title(label, color="#dddddd", fontsize=10)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=90, facecolor="#0c0c0e", bbox_inches="tight")
    plt.close(fig)
    return path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--mode", choices=["flesh", "flex", "walk"], default="flesh",
                    help="flesh = fleshed body; flex = synthetic pose; walk = brain's gait")
    ap.add_argument("--frames", type=int, default=6)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--sweeps", type=int, default=60)
    ap.add_argument("--png", default=None)
    a = ap.parse_args()

    bones, size = evolved_skeleton()
    print(f"\nSPINE — the REAL evolved body: {len(bones)} bones, size {size:.3f}")
    fleshed, shape, scale, offset = flesh_the_body(bones, sweeps=a.sweeps, seed=a.seed)
    surf = skin_surface(fleshed)
    if surf is None:
        print("  FAILED: no skin surface — flesh too thin?")
        return 1
    verts, faces = surf
    print(f"  lattice {shape}, skin surface {len(faces):,} tris")

    if a.mode == "flesh":
        views = [("evolved creature, fleshed", verts, faces, -60),
                 ("other side", verts, faces, 120)]
        tail = "The REAL evolved body is fleshed."
    elif a.mode == "flex":
        info = skeleton_frames(bones, scale, offset)
        widx, ww = skin_weights(verts, bones, scale, offset)
        # SYNTHETIC pose: bend every joint the same way. If the flesh follows the bones,
        # the skinning is sound and we can trust it with the brain's real gait next.
        dtheta = np.array([0.0] + [0.8] * (len(bones) - 1), np.float32)
        posed = pose_mesh(verts, widx, ww, fk(info, dtheta))
        moved = float(np.linalg.norm(posed - verts, axis=1).mean())
        print(f"  skinned to {len(bones)} bones (k=4); synthetic flex moved verts "
              f"{moved:.1f} cells")
        views = [("rest", verts, faces, -60), ("skeleton flexed 0.8 rad", posed, faces, -60)]
        tail = "The flesh follows the skeleton. Next: drive it with the brain's gait."
    else:  # walk — the payoff: the fleshed evolved body performs its evolved gait
        info = skeleton_frames(bones, scale, offset)
        widx, ww = skin_weights(verts, bones, scale, offset)
        angles = gait_angles(bones, n_frames=a.frames)
        print(f"  skinned to {len(bones)} bones; driving with the brain's gait "
              f"({len(angles)} frames)")
        views = []
        for i, ja in enumerate(angles):
            dtheta = np.concatenate([[0.0], ja]).astype(np.float32)   # bone0 root, rest = joints
            posed = pose_mesh(verts, widx, ww, fk(info, dtheta))
            views.append((f"gait {i + 1}/{len(angles)}", posed, faces, -60))
        tail = "THE SPINE IS JOINED. The brain that learned to walk now moves the flesh."

    if a.png:
        print(f"\n  -> {render_mesh(views, Path(a.png))}")
    print(f"\n  {tail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
