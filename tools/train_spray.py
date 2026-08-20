"""Spray-paint trainer: paint a CAD-bound splat skin from REAL photos (CO3D).

Differences from train_skin.py (SV3D lane):
  - dataset = views.json from co3d_to_views.py (c2w OpenCV convention, K,
    foreground mask per frame) — NO gsplat Parser, NO norm transform; the
    skin is authored directly in CO3D world coordinates from fitted_parts.json
  - masked loss: fg pixels |pred-gt|, bg pixels |pred| (positions are bound
    to the CAD surface, so splats cannot chase background — bg loss just
    keeps the silhouette honest)
  - export: CO3D world -> viewer display frame via Rx(180deg) (this world's
    head sits at -y) + uniform scale to CAD height, then save_splat

Run (from tools/gsplat/examples):
  PYTHONPATH=examples cmd //c laneE_vcvars_run.bat E:\\PythonChimera\\tools\\train_spray.py ...
"""
import argparse
import json
import math
import sys

import numpy as np

sys.path.insert(0, r"E:\PythonChimera\tools")
sys.path.insert(0, r"E:\PythonChimera\ChimeraEngine")
import teddy_body as tb  # noqa: E402
import cpp_bridge as cb  # noqa: E402

C0 = 0.28209479177387814
RX180 = np.array([[1.0, 0, 0], [0, -1.0, 0], [0, 0, -1.0]])  # CO3D world head=-y -> y-up


def quat_from_z_to(n):
    n = np.asarray(n, float)
    v = np.cross(np.tile([0.0, 0, 1], (len(n), 1)), n)
    q = np.concatenate([1.0 + n[:, 2:3], v], axis=1)
    bad = np.abs(q).sum(1) < 1e-6
    q[bad] = [0.0, 1.0, 0, 0]
    return q / np.linalg.norm(q, axis=1, keepdims=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parts", default=r"E:/PythonChimera/.tmp/fitted_parts.json")
    ap.add_argument("--views", default=r"E:/PythonChimera/capture/co3d/teddybear/views_34.json")
    ap.add_argument("--steps", type=int, default=4000)
    ap.add_argument("--sh-degree", type=int, default=2)
    ap.add_argument("--test-every", type=int, default=8)
    ap.add_argument("--downscale", type=int, default=2)
    ap.add_argument("--n-per-part", type=int, default=5000)
    ap.add_argument("--out", required=True)
    ap.add_argument("--eval-grid", default=None)
    args = ap.parse_args()

    import imageio.v3 as iio
    import torch
    from gsplat import rasterization
    from torchmetrics.functional import structural_similarity_index_measure as ssim

    # --- dataset (lazy images, preloaded small) -------------------------------
    views = json.load(open(args.views))
    ds = args.downscale
    imgs, masks = [], []
    for v in views:
        im = iio.imread(v["image"])[::ds, ::ds, :3]
        mk = iio.imread(v["mask"])[::ds, ::ds] > 127
        imgs.append(im)
        masks.append(mk)
    H, W = imgs[0].shape[:2]
    c2ws = torch.tensor(np.array([v["c2w"] for v in views]), dtype=torch.float32)
    Ks = torch.tensor(np.array([v["K"] for v in views]), dtype=torch.float32)
    Ks[:, 0, :] /= ds
    Ks[:, 1, :] /= ds
    train_idx = [i for i in range(len(views)) if i % args.test_every != 0]
    val_idx = [i for i in range(len(views)) if i % args.test_every == 0]
    print(f"views: {len(train_idx)} train / {len(val_idx)} val, "
          f"image {W}x{H}", flush=True)

    # --- authored skin in CO3D world ------------------------------------------
    tb.PARTS = json.load(open(args.parts))
    P, Nrm, _ = tb.sample_surface(n_per_part=args.n_per_part, seed=0)
    N = len(P)
    # self-calibrating disc size: mean nearest-neighbor distance
    from scipy.spatial import cKDTree
    d2, _ = cKDTree(P).query(P, k=2)
    disc = float(np.median(d2[:, 1])) * 1.1
    print(f"skin: {N} splats, disc r={disc:.4f}", flush=True)

    dev = "cuda"
    means0 = torch.tensor(P, dtype=torch.float32, device=dev)
    dirs = torch.tensor(Nrm, dtype=torch.float32, device=dev)
    quats = torch.tensor(quat_from_z_to(Nrm), dtype=torch.float32, device=dev)
    K = (args.sh_degree + 1) ** 2
    # init color: median tan of the bear region across frames
    fg = np.concatenate([im[mk] for im, mk in zip(imgs[::20], masks[::20])]) / 255.0
    c0 = np.median(fg, axis=0)
    print(f"init color (median fg): {c0.round(3)}", flush=True)
    sh0 = torch.tensor((c0 - 0.5) / C0, dtype=torch.float32, device=dev)
    sh0 = sh0.repeat(N, 1, 1).requires_grad_()
    shN = torch.zeros(N, K - 1, 3, device=dev).requires_grad_()
    logit_op = torch.full((N,), 2.0, device=dev).requires_grad_()
    log_sc0 = torch.log(torch.tensor(
        np.tile([disc, disc, disc * 0.35], (N, 1)), dtype=torch.float32,
        device=dev))
    dsc = torch.zeros(N, 3, device=dev).requires_grad_()
    # CAD shell: frosting layer OUTSIDE the surface only. off in [dmin, dmax].
    # init sigmoid(-2.0)~0.12 -> starts just off the surface; can never go inside.
    dmin, dmax = 0.0, disc * 2.5
    offs = torch.full((N, 1), -2.0, device=dev).requires_grad_()

    opt = torch.optim.Adam([
        {"params": sh0, "lr": 2.5e-3},
        {"params": shN, "lr": 1.25e-4},
        {"params": logit_op, "lr": 5e-2},
        {"params": dsc, "lr": 5e-3},
        {"params": offs, "lr": 2e-3},
    ])

    imgs_t = [torch.from_numpy(np.ascontiguousarray(im)) for im in imgs]  # uint8 CPU
    masks_t = [torch.from_numpy(mk) for mk in masks]
    c2ws = c2ws.to(dev)
    Ks = Ks.to(dev)

    def render(i, deg):
        means = means0 + dirs * (dmin + (dmax - dmin) * torch.sigmoid(offs))
        colors = torch.cat([sh0, shN], dim=1)
        rc, ra, _ = rasterization(
            means=means, quats=quats,
            scales=torch.exp(log_sc0 + 0.9 * torch.tanh(dsc)),
            opacities=torch.sigmoid(logit_op), colors=colors,
            viewmats=torch.linalg.inv(c2ws[i:i + 1]), Ks=Ks[i:i + 1],
            width=W, height=H, sh_degree=deg, rasterize_mode="antialiased")
        return rc[0]

    for step in range(args.steps):
        i = train_idx[np.random.randint(len(train_idx))]
        gt = imgs_t[i].float().to(dev) / 255.0
        mk = masks_t[i].to(dev)
        deg = min(step // 600, args.sh_degree)
        pred = render(i, deg)
        diff = (pred - gt).abs().mean(-1)
        loss_fg = (diff * mk).sum() / mk.sum().clamp(min=1)
        loss_bg = (pred.mean(-1) * (~mk)).sum() / (~mk).sum().clamp(min=1)
        s = ssim(pred.permute(2, 0, 1)[None], gt.permute(2, 0, 1)[None])
        loss = loss_fg + 0.5 * loss_bg + 0.2 * (1.0 - s)
        opt.zero_grad()
        loss.backward()
        opt.step()
        if step % 500 == 0 or step == args.steps - 1:
            with torch.no_grad():
                psnrs = []
                for j in val_idx[:6]:
                    vg = imgs_t[j].float().to(dev) / 255.0
                    vmk = masks_t[j].to(dev)
                    vp = render(j, args.sh_degree)
                    mse = (((vp - vg) ** 2).mean(-1) * vmk).sum() / vmk.sum()
                    psnrs.append(-10 * math.log10(max(mse.item(), 1e-10)))
                print(f"step {step:5d} loss {loss.item():.4f} "
                      f"val fg-PSNR {np.mean(psnrs):.2f} dB", flush=True)

    if args.eval_grid:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        nv = min(4, len(val_idx))
        fig, axs = plt.subplots(2, nv, figsize=(4 * nv, 9))
        with torch.no_grad():
            for j in range(nv):
                vi = val_idx[j]
                vp = render(vi, args.sh_degree)
                axs[0, j].imshow(vp.cpu().numpy().clip(0, 1))
                axs[1, j].imshow(imgs_t[vi].numpy())
                axs[0, j].set_title(f"spray v{vi}")
                axs[1, j].set_title("real photo")
        for a in axs.ravel():
            a.axis("off")
        plt.tight_layout()
        plt.savefig(args.eval_grid, dpi=80)
        print(f"wrote {args.eval_grid}", flush=True)

    # --- export: CO3D world -> display frame ----------------------------------
    with torch.no_grad():
        means = (means0 + dirs * (dmin + (dmax - dmin) * torch.sigmoid(offs)))
        means = means.cpu().numpy().astype(np.float64)
        sh = torch.cat([sh0, shN], dim=1).cpu().numpy().astype(np.float64)
        alpha = torch.sigmoid(logit_op).cpu().numpy()
        scale = torch.exp(log_sc0 + 0.9 * torch.tanh(dsc)).cpu().numpy().astype(np.float64)
    keep = alpha >= 0.15
    print(f"export prune: {(~keep).sum()} faint splats dropped", flush=True)
    means, sh, scale = means[keep], sh[keep], scale[keep]
    alpha = alpha[keep]
    Nrm_e = Nrm[keep]
    N = int(keep.sum())
    # normalize to CAD height ~1.06 then rotate head-up
    ys = means[:, 1]
    h_world = np.percentile(ys, 99) - np.percentile(ys, 1)
    s_out = 1.06 / h_world
    pos_d = (means * s_out) @ RX180.T
    scl_d = scale * s_out
    Qw = quat_from_z_to(Nrm_e)  # NOTE: quats were frozen; dirs moved only radially
    import scipy.spatial.transform as st
    Rw = st.Rotation.from_quat(Qw[:, [1, 2, 3, 0]]).as_matrix()
    Rd = RX180[None] @ Rw
    q_d = st.Rotation.from_matrix(Rd).as_quat()[:, [3, 0, 1, 2]]
    # bake SH at median camera direction (directions rotate too)
    cams = np.array([v["c2w"] for v in views])[:, :3, 3]
    cams_d = (cams * s_out) @ RX180.T
    tc = cams_d[None] - pos_d[:, None]
    tc /= np.linalg.norm(tc, axis=2, keepdims=True) + 1e-12
    # SH was trained in world frame; evaluate along world-frame dirs
    tc_w = tc @ RX180  # inverse rotation of directions
    acc = np.stack([_sh_eval(sh, tc_w[:, j]) for j in range(tc_w.shape[1])], 1)
    rgb = np.clip(np.median(acc, axis=1), 0, 1)
    out = np.zeros((N, 14))
    out[:, 0:3] = pos_d - pos_d.mean(0) + [0.03, 0.0, 0.0]  # recenter to CAD origin
    out[:, 3:6] = rgb
    out[:, 6] = alpha
    out[:, 7:10] = scl_d
    out[:, 10:14] = q_d
    cb.save_splat(args.out, out.astype(np.float32))
    print(f"wrote {args.out}: {N} splats (rgb mean {rgb.mean(0).round(3)})", flush=True)


def _sh_eval(sh, d):
    x, y, z = d[:, 0:1], d[:, 1:2], d[:, 2:3]
    r = C0 * sh[:, 0]
    if sh.shape[1] > 3:
        r = r - 0.48860251190291987 * (y * sh[:, 1] - z * sh[:, 2] + x * sh[:, 3])
    if sh.shape[1] > 8:
        r = r + 1.0925484305920792 * x * y * sh[:, 4] \
            - 1.0925484305920792 * y * z * sh[:, 5] \
            + 0.31539156525352005 * (2 * z * z - x * x - y * y) * sh[:, 6] \
            - 1.0925484305920792 * x * z * sh[:, 7] \
            + 0.5462742152960396 * (x * x - y * y) * sh[:, 8]
    return r + 0.5


if __name__ == "__main__":
    main()
