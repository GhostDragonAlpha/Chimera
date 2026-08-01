"""visual_hull.py -- compare generated geometry to a membrane's own, in THREE dimensions.

WHY THE EARLIER CHECKS ALL FAILED. Five silhouette metrics were tried against a generated take and
every one of them was degenerate: a terrain outline scored 0.900 against an astronaut video, as
well as the astronaut's own outline did. The cause is not a bad threshold, it is the method.

    A SILHOUETTE IS A PROJECTION, AND PROJECTION DISCARDS EXACTLY WHAT IS BEING CHECKED.

Two very different solids can share an outline from any single view. Comparing one view to one view
therefore cannot decide whether a shape survived, no matter how carefully the masks are made.

BUT MANY SILHOUETTES, CARVED JOINTLY, ARE A RECONSTRUCTION. That is the visual hull -- the oldest
shape-from-silhouette method there is. Start with a solid block of voxels, and for every camera,
delete every voxel that projects outside that view's mask. What survives is the tightest solid
consistent with ALL the outlines at once. It is not a perfect reconstruction (it can never see a
concavity that no silhouette reveals) and it does not need to be: it is a bound, and comparing two
bounds computed the same way from the same cameras is a fair test.

WHAT THIS NEEDS, AND ALL OF IT ALREADY EXISTS: exact masks (capture mode's black void gives them),
the camera poses (clay_export writes them down for exactly this reason), and the source geometry
(the membrane's own emit). No GPU, no 3DGS, no neural anything -- a voxel grid and a loop.

WHAT IT REPORTS: the IoU of the two carved volumes, in 3D. And a control, because the whole reason
this file exists is that the previous five metrics passed a control they should have failed.

RUN:  python tools/visual_hull.py clay_exports/capture_aHuman --membrane aHuman
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "story"))
sys.path.insert(0, str(ROOT / "tools"))


def project(pts, cam, width, height, fov):
    """World points -> pixel coordinates, using the same convention the engine's camera uses.

    The camera looks along +X at yaw 0 with +Z up; yaw rotates about Z and pitch tilts. Anything
    behind the camera is marked invalid rather than wrapped, because a point behind the lens that
    projects onto the image is how a carve quietly deletes the wrong voxels."""
    import numpy as np
    pos = np.array(cam["position"], dtype=np.float64)
    yaw, pitch = float(cam["yaw"]), float(cam["pitch"])
    d = pts - pos[None, :]
    cy, sy = math.cos(-yaw), math.sin(-yaw)
    x = d[:, 0] * cy - d[:, 1] * sy
    y = d[:, 0] * sy + d[:, 1] * cy
    z = d[:, 2]
    cp, sp = math.cos(-pitch), math.sin(-pitch)
    fwd = x * cp - z * sp
    up = x * sp + z * cp
    valid = fwd > 1e-6
    f = (0.5 * width) / math.tan(0.5 * float(fov))
    u = 0.5 * width - f * (y / np.where(valid, fwd, 1.0))
    v = 0.5 * height - f * (up / np.where(valid, fwd, 1.0))
    return u, v, valid


def carve(masks, cams, bound, n=96, keep_frac=0.92):
    """The visual hull: every voxel that projects inside (almost) every mask.

    `keep_frac` is not a fudge. A carve that demands EVERY view is destroyed by one bad mask, and a
    generated take will have one. Requiring a voxel to survive 92% of views tolerates a single
    frame going wrong without opening the hull to anything. Stated, so it can be argued with."""
    import numpy as np
    g = np.linspace(-bound, bound, n)
    X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
    pts = np.stack([X.ravel(), Y.ravel(), Z.ravel()], axis=1)
    votes = np.zeros(len(pts), dtype=np.int32)
    for m, c in zip(masks, cams):
        h, w = m.shape
        u, v, valid = project(pts, c, w, h, c["fov"])
        ui = np.clip(u.astype(np.int64), 0, w - 1)
        vi = np.clip(v.astype(np.int64), 0, h - 1)
        inside = valid & (u >= 0) & (u < w) & (v >= 0) & (v < h) & m[vi, ui]
        votes += inside.astype(np.int32)
    need = int(math.ceil(keep_frac * len(masks)))
    return (votes >= need).reshape(n, n, n)


def hull_iou(a, b):
    import numpy as np
    inter = float(np.logical_and(a, b).sum())
    union = float(np.logical_or(a, b).sum())
    return inter / max(union, 1.0)


def main():
    import numpy as np
    import cv2
    from PIL import Image

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("take_dir", help="a probe output dir: clay.mp4 + generated.mp4 + cameras")
    ap.add_argument("--membrane", required=True)
    ap.add_argument("--tol", type=float, default=0.22, help="black-void mask threshold")
    ap.add_argument("--grid", type=int, default=96)
    ap.add_argument("--control", default="aTerrain",
                    help="a DIFFERENT membrane, carved from the same generated masks. If it scores "
                         "as well as the real one, this metric is degenerate like the last five.")
    a = ap.parse_args()
    take = Path(a.take_dir)

    from clay_export import clay, key_for, orbit_camera
    from ChimeraEngine import splat_appearance as SA
    from ParticleEngine.gpu_pipeline import FullGPUPipeline
    from ParticleEngine.camera import FirstPersonCamera
    from matter import PX, PZ

    req = json.loads((take / "request.json").read_text(encoding="utf8"))
    frames_n, arc, elev, dist, size = 24, 90.0, 16.0, 2.6, 480

    def clay_masks_and_cams(term):
        src = SA.membrane_buffer(term, 1.0)
        ext = float(np.linalg.norm(np.asarray(src)[:, PX:PZ + 1], axis=1).max()) or 1.0
        pipe = FullGPUPipeline(bg=(0.5, 0.5, 0.5))
        ms, cs = [], []
        for i in range(frames_n):
            pos, yaw, pitch = orbit_camera(ext, i, frames_n, arc, elev, dist)
            cam = FirstPersonCamera(pos, yaw=yaw, pitch=pitch)
            p = cam.params(size, size)
            pipe.upload(clay(src, key_for(yaw, pitch)))
            im = np.asarray(Image.fromarray(pipe.render_from_gpu(cam, p)).convert("L"),
                            dtype=np.float32) / 255.0
            ms.append(np.abs(im - 0.5) > 0.02)
            cs.append({"position": list(pos), "yaw": yaw, "pitch": pitch, "fov": float(p.fov)})
        return ms, cs, ext

    src_masks, cams, extent = clay_masks_and_cams(a.membrane)
    ctl_masks, _, _ = clay_masks_and_cams(a.control)

    cap = cv2.VideoCapture(str(take / "generated.mp4"))
    gen = []
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        gen.append(fr[:, :, ::-1])
    cap.release()

    gen_masks = []
    for i in range(frames_n):
        g = cv2.resize(gen[int(i * (len(gen) - 1) / (frames_n - 1))], (size, size))
        m = ((np.asarray(g, np.float32) / 255.0).max(axis=2) > a.tol).astype(np.uint8)
        n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
        if n > 1:
            m = (lab == (1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA])))).astype(np.uint8)
        gen_masks.append(m.astype(bool))

    bound = extent * 1.15
    print(f"carving {a.grid}^3 voxels over +/-{bound:.4g} local, from {frames_n} views")
    h_src = carve(src_masks, cams, bound, a.grid)
    h_gen = carve(gen_masks, cams, bound, a.grid)
    h_ctl = carve(ctl_masks, cams, bound, a.grid)

    occ = lambda h: 100.0 * h.mean()
    print(f"   source clay hull   {occ(h_src):6.2f}% of the box")
    print(f"   generated hull     {occ(h_gen):6.2f}%")
    print(f"   control clay hull  {occ(h_ctl):6.2f}%  ({a.control})")
    print()
    matched = hull_iou(h_src, h_gen)
    control = hull_iou(h_ctl, h_gen)
    print(f"3D HULL IoU")
    print(f"   MATCHED  {a.membrane} clay vs generated   {matched:.4f}")
    print(f"   CONTROL  {a.control} clay vs generated    {control:.4f}")
    print(f"   separation {matched - control:+.4f}")
    print()
    if matched - control < 0.10:
        print("DEGENERATE, like the five before it -- this metric cannot tell the shapes apart.")
    elif matched >= 0.60:
        print("THE SHAPE SURVIVED. The generated volume agrees with the membrane's own geometry, "
              "and disagrees with a different membrane's, which is what a real check looks like.")
    else:
        print("THE SHAPE DID NOT SURVIVE, and the control confirms the metric can tell -- so this "
              "is a fact about the generator, not about the measurement.")
    (take / "hull.json").write_text(json.dumps(
        {"membrane": a.membrane, "control": a.control, "grid": a.grid,
         "matched_iou": matched, "control_iou": control,
         "occupancy": {"source": occ(h_src), "generated": occ(h_gen), "control": occ(h_ctl)}},
        indent=1), encoding="utf8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
