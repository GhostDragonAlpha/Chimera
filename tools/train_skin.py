"""Train the authored bear's APPEARANCE against SV3D reference frames.

Geometry stays bound to the CAD body: splat positions = authored base +
(offset along the surface normal / strand axis) only. Quats frozen (aligned
to the surface). Trainable: SH color, opacity, scale, small normal offset.
No densification, no pruning — the parts catalog owns where splats live.

Frames: capture/sv3d_eqonly (21 one-pass SV3D views, black bg). Cameras come
from gsplat's Parser (normalized frame); the authored skin is mapped into the
same frame with the inverse of sh_bake.py's unnormalize step.

Run (from tools/gsplat/examples):
  PYTHONPATH="E:\\PythonChimera\\tools\\gsplat\\examples" \
  cmd //c "E:\\PythonChimera\\tools\\laneE_vcvars_run.bat \
  E:\\PythonChimera\\tools\\train_skin.py \
  --skin E:\\PythonChimera\\models\\triposplat\\static\\viewer\\authbear0.splat \
  --data E:\\PythonChimera\\capture\\sv3d_eqonly\\data \
  --norm E:\\PythonChimera\\capture\\sv3d_eqonly\\norm_transform.npy \
  --steps 3000 --out E:\\PythonChimera\\models\\genbear3\\authbear1.splat"
"""
import argparse
import math
import sys

import numpy as np

sys.path.insert(0, r"E:\PythonChimera\ChimeraEngine")
sys.path.insert(0, r"E:\PythonChimera\tools")
import cpp_bridge as cb  # noqa: E402

C0 = 0.28209479177387814


def quat_wxyz_to_mat(q):
    w, x, y, z = q[..., 0], q[..., 1], q[..., 2], q[..., 3]
    m = np.empty(q.shape[:-1] + (3, 3))
    m[..., 0, 0] = 1 - 2 * (y * y + z * z)
    m[..., 0, 1] = 2 * (x * y - z * w)
    m[..., 0, 2] = 2 * (x * z + y * w)
    m[..., 1, 0] = 2 * (x * y + z * w)
    m[..., 1, 1] = 1 - 2 * (x * x + z * z)
    m[..., 1, 2] = 2 * (y * z - x * w)
    m[..., 2, 0] = 2 * (x * z - y * w)
    m[..., 2, 1] = 2 * (y * z + x * w)
    m[..., 2, 2] = 1 - 2 * (x * x + y * y)
    return m


def sh_eval(sh, d):
    """sh (N,K,3), d (N,3) -> rgb (N,3). Degrees 0..2."""
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skin", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--norm", required=True)
    ap.add_argument("--steps", type=int, default=3000)
    ap.add_argument("--sh-degree", type=int, default=2)
    ap.add_argument("--test-every", type=int, default=7)
    ap.add_argument("--out", required=True)
    ap.add_argument("--eval-grid", default=None)
    args = ap.parse_args()

    import torch
    import scipy.spatial.transform as st
    from datasets.colmap import Dataset, Parser
    from gsplat import rasterization
    from torchmetrics.functional import structural_similarity_index_measure as ssim

    parser = Parser(data_dir=args.data, factor=1, normalize=True,
                    test_every=args.test_every)
    trainset = Dataset(parser, split="train")
    valset = Dataset(parser, split="val")
    print(f"views: {len(trainset)} train / {len(valset)} val of "
          f"{len(parser.image_names)} total", flush=True)

    # --- authored skin: display frame -> gsplat normalized world -------------
    buf = cb.load_splat(args.skin).astype(np.float64)
    N = len(buf)
    T = np.load(args.norm).astype(np.float64)
    Rn, tn = T[:3, :3], T[:3, 3]
    sc = float(np.cbrt(abs(np.linalg.det(Rn))))
    Rr = Rn / sc
    mirror = np.linalg.det(Rr) < 0
    D = np.diag([1.0, 1.0, -1.0]) if mirror else np.eye(3)

    pos_d = buf[:, 0:3]
    pos_w = sc * (pos_d @ Rr.T) + tn                       # inverse of sh_bake:199
    scl_w = buf[:, 7:10] * sc                              # inverse of /sc
    W = quat_wxyz_to_mat(buf[:, 10:14])                    # display quats
    Qn = Rr[None] @ W @ D                                  # inverse fold
    quat_w = st.Rotation.from_matrix(Qn).as_quat()[:, [3, 0, 1, 2]]
    # per-splat binding direction = local +z (normal / strand axis), in world
    dir_w = np.einsum("nij,j->ni", W, [0.0, 0.0, 1.0])     # display
    dir_w = dir_w @ Rr.T                                    # world (uniform sc cancels)
    dir_w /= np.linalg.norm(dir_w, axis=1, keepdims=True)

    dev = "cuda"
    means0 = torch.tensor(pos_w, dtype=torch.float32, device=dev)
    dirs = torch.tensor(dir_w, dtype=torch.float32, device=dev)
    quats = torch.tensor(quat_w, dtype=torch.float32, device=dev)
    K = (args.sh_degree + 1) ** 2
    sh0 = torch.tensor((buf[:, 3:6] - 0.5) / C0, dtype=torch.float32,
                       device=dev).unsqueeze(1).requires_grad_()
    shN = torch.zeros(N, K - 1, 3, device=dev).requires_grad_()
    logit_op = torch.logit(torch.tensor(
        np.clip(buf[:, 6], 1e-3, 0.999), dtype=torch.float32,
        device=dev)).requires_grad_()
    log_sc = torch.log(torch.tensor(
        scl_w, dtype=torch.float32, device=dev)).requires_grad_()
    offs = torch.zeros(N, 1, device=dev).requires_grad_()

    opt = torch.optim.Adam([
        {"params": sh0, "lr": 2.5e-3, "name": "sh0"},
        {"params": shN, "lr": 1.25e-4, "name": "shN"},
        {"params": logit_op, "lr": 5e-2, "name": "op"},
        {"params": log_sc, "lr": 5e-3, "name": "sc"},
        {"params": offs, "lr": 1e-3, "name": "off"},
    ])

    def render(camtoworlds, Ks, Wd, Ht, active_deg):
        means = means0 + dirs * offs
        colors = torch.cat([sh0, shN], dim=1)
        rc, ra, _ = rasterization(
            means=means, quats=quats, scales=torch.exp(log_sc),
            opacities=torch.sigmoid(logit_op), colors=colors,
            viewmats=torch.linalg.inv(camtoworlds), Ks=Ks,
            width=Wd, height=Ht, sh_degree=active_deg,
            rasterize_mode="antialiased")
        return rc, ra

    for step in range(args.steps):
        i = np.random.randint(len(trainset))
        data = trainset[i]
        c2w = data["camtoworld"].float()[None].to(dev)
        Ks = data["K"].float()[None].to(dev)
        gt = data["image"].float().to(dev) / 255.0
        Ht, Wd = gt.shape[0], gt.shape[1]
        deg = min(step // 500, args.sh_degree)
        pred, _ = render(c2w, Ks, Wd, Ht, deg)
        pred = pred[0]
        l1 = (pred - gt).abs().mean()
        s = ssim(pred.permute(2, 0, 1)[None], gt.permute(2, 0, 1)[None])
        loss = l1 + 0.2 * (1.0 - s) + 1e-3 * (offs ** 2).mean()
        opt.zero_grad()
        loss.backward()
        opt.step()
        if step % 250 == 0 or step == args.steps - 1:
            with torch.no_grad():
                psnrs = []
                for j in range(len(valset)):
                    vd = valset[j]
                    vc = vd["camtoworld"].float()[None].to(dev)
                    vk = vd["K"].float()[None].to(dev)
                    vg = vd["image"].float().to(dev) / 255.0
                    vp, _ = render(vc, vk, vg.shape[1], vg.shape[0],
                                   args.sh_degree)
                    mse = ((vp[0] - vg) ** 2).mean().item()
                    psnrs.append(-10 * math.log10(max(mse, 1e-10)))
                print(f"step {step:5d} loss {loss.item():.4f} "
                      f"val PSNR {np.mean(psnrs):.2f} dB "
                      f"(n={len(psnrs)})", flush=True)

    # --- eval grid -----------------------------------------------------------
    if args.eval_grid:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        nv = len(valset)
        fig, axs = plt.subplots(2, nv, figsize=(4 * nv, 8))
        with torch.no_grad():
            for j in range(nv):
                vd = valset[j]
                vc = vd["camtoworld"].float()[None].to(dev)
                vk = vd["K"].float()[None].to(dev)
                vg = vd["image"].float().to(dev) / 255.0
                vp, _ = render(vc, vk, vg.shape[1], vg.shape[0], args.sh_degree)
                axs[0, j].imshow(vp[0].cpu().numpy().clip(0, 1))
                axs[1, j].imshow(vg.cpu().numpy().clip(0, 1))
                axs[0, j].set_title(f"render v{j}")
                axs[1, j].set_title("SV3D ref")
        for a in axs.ravel():
            a.axis("off")
        plt.tight_layout()
        plt.savefig(args.eval_grid, dpi=80)
        print(f"wrote {args.eval_grid}", flush=True)

    # --- export: world -> display, bake median SH color ----------------------
    with torch.no_grad():
        means = (means0 + dirs * offs).cpu().numpy().astype(np.float64)
        sh = torch.cat([sh0, shN], dim=1).cpu().numpy().astype(np.float64)
        alpha = torch.sigmoid(logit_op).cpu().numpy()
        scale_w = torch.exp(log_sc).cpu().numpy().astype(np.float64)
    pos_d2 = (means - tn) @ Rr / sc                       # sh_bake:199 forward
    scl_d = scale_w / sc
    Qn2 = quat_wxyz_to_mat(quat_w)                        # (wxyz->mat) world
    M = Rr.T[None] @ Qn2 @ D
    q_out = st.Rotation.from_matrix(M).as_quat()[:, [3, 0, 1, 2]]
    cams_w = parser.camtoworlds[:, :3, 3].astype(np.float64)
    tc = cams_w[None] - means[:, None]
    tc /= np.linalg.norm(tc, axis=2, keepdims=True) + 1e-12
    acc = np.stack([sh_eval(sh, tc[:, j]) for j in range(tc.shape[1])], 1)
    rgb = np.clip(np.median(acc, axis=1), 0, 1)
    out = np.zeros((N, 14))
    out[:, 0:3] = pos_d2
    out[:, 3:6] = rgb
    out[:, 6] = alpha
    out[:, 7:10] = scl_d
    out[:, 10:14] = q_out
    cb.save_splat(args.out, out.astype(np.float32))
    print(f"wrote {args.out}: {N} splats (rgb mean {rgb.mean(0).round(3)})",
          flush=True)


if __name__ == "__main__":
    main()
