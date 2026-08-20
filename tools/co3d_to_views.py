"""CO3D sequence -> view list (c2w OpenCV/COLMAP convention) + validation.

CO3D frame_annotations give PyTorch3D cameras: X_cam = X_world @ R + T,
camera axes +x left / +y up / +z forward, focal in NDC units where the
shorter image side spans [-1, 1]. We convert to OpenCV convention
(+x right, +y down, +z forward) via D = diag(-1,-1,1):

    R_c = D @ R.T      t_c = D @ T        (c2w = [R_c.T | -R_c.T @ t_c])
    f_px = f_ndc * min(H, W) / 2
    cx = W/2 + pp_x * min(H,W)/2 ... (pp ~ 0 in this data)

VALIDATION (Rule 0): the sequence's pointcloud.ply is a real COLMAP
reconstruction in the same world frame. Project it through the converted
cameras: if the conversion is right, projected points land inside the
foreground mask. Statement: "the conversion above is correct."
Prediction: mask-hit-rate > 0.85 on frame 1. Falsifier: below that ->
axis convention wrong, re-derive before any training.
"""
import argparse
import gzip
import json
import os

import numpy as np


def load_sequence(meta_jgz, images_root, seq):
    fa = json.load(gzip.open(meta_jgz, "rt"))
    frames = [f for f in fa if f["sequence_name"] == seq]
    frames.sort(key=lambda f: int(f["frame_number"]))
    views = []
    D = np.diag([-1.0, -1.0, 1.0])
    for f in frames:
        vp = f["viewpoint"]
        R = np.array(vp["R"], dtype=np.float64)
        T = np.array(vp["T"], dtype=np.float64)
        H, W = f["image"]["size"]  # CO3D stores [H, W]
        f_ndc = float(np.mean(vp["focal_length"]))
        s = min(H, W) / 2.0
        R_c = D @ R.T
        t_c = D @ T
        c2w = np.eye(4)
        c2w[:3, :3] = R_c.T
        c2w[:3, 3] = -R_c.T @ t_c
        K = np.array([[f_ndc * s, 0, W / 2.0 - vp["principal_point"][0] * s],
                      [0, f_ndc * s, H / 2.0 - vp["principal_point"][1] * s],
                      [0, 0, 1.0]])
        views.append(dict(
            frame=int(f["frame_number"]),
            image=os.path.join(images_root, f["image"]["path"]),
            mask=os.path.join(images_root, f["mask"]["path"]),
            H=H, W=W, K=K.tolist(), c2w=c2w.tolist()))
    return views


def load_ply_points(path):
    """Minimal ASCII/binary PLY reader: xyz of vertices."""
    with open(path, "rb") as fh:
        header = b""
        while not header.endswith(b"end_header\n"):
            header += fh.read(1)
        htxt = header.decode("ascii", "replace")
        n = int([l.split()[2] for l in htxt.splitlines()
                 if l.startswith("element vertex")][0])
        props = [l.split()[2] for l in htxt.splitlines()
                 if l.startswith("property")]
        buf = fh.read()
    # binary little-endian, mixed types (float x/y/z + uchar rgb)
    dtmap = {"float": "<f4", "uchar": "u1", "double": "<f8"}
    dt = np.dtype([(p, dtmap[t.split()[1]]) for p, t in
                   zip(props, [l for l in htxt.splitlines() if l.startswith("property")])])
    if len(buf) >= n * dt.itemsize:
        arr = np.frombuffer(buf[: n * dt.itemsize], dtype=dt)
        return np.stack([arr["x"], arr["y"], arr["z"]], axis=1).astype(np.float64)
    raise ValueError("unsupported PLY layout")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--meta", default="capture/co3d/meta/teddybear/frame_annotations.jgz")
    ap.add_argument("--root", default="capture/co3d")
    ap.add_argument("--seq", default="34_1479_4753")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    views = load_sequence(args.meta, args.root, args.seq)
    print(f"sequence {args.seq}: {len(views)} views, "
          f"image {views[0]['W']}x{views[0]['H']}, "
          f"f_px {views[0]['K'][0][0]:.1f}")

    # --- validation: project the real pointcloud through view 0 ---------------
    import imageio.v3 as iio
    ply = os.path.join(args.root, "teddybear", args.seq, "pointcloud.ply")
    P = load_ply_points(ply)
    v = views[0]
    c2w = np.array(v["c2w"])
    w2c = np.linalg.inv(c2w)
    Pc = (w2c[:3, :3] @ P.T).T + w2c[:3, 3]
    infront = Pc[:, 2] > 0.1
    Pc = Pc[infront]
    K = np.array(v["K"])
    uv = (K @ (Pc / Pc[:, 2:3]).T).T
    u = np.clip(uv[:, 0].astype(int), 0, v["W"] - 1)
    vv = np.clip(uv[:, 1].astype(int), 0, v["H"] - 1)
    mask = iio.imread(v["mask"]) > 127
    hits = mask[vv, u].mean()
    print(f"VALIDATION frame {v['frame']}: {len(Pc)} cloud points in front, "
          f"mask hit rate {hits:.3f} (target > 0.85)")

    if args.out:
        with open(args.out, "w") as fh:
            json.dump(views, fh)
        print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
