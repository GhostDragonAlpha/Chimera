"""gsplat_fit — per-splat 3D-Gaussian-Splatting fit against the actual pixels.

The honest endgame (the nine-descriptor trainer could match colour but never look
like the photo; this optimizes the splats to the IMAGE itself). A differentiable
2D Gaussian splatter in PyTorch: N Gaussians (position, anisotropic scale,
rotation, colour, opacity) rendered by a differentiable normalized-accumulation
splat; the loss is pixel error vs the reference photo; Adam on the GPU moves every
splat's parameters down the gradient. Then the fitted splats are lifted to 3D
(depth field) so the reconstruction is an orbitable noun.

Run:  python Construction/gsplat_fit.py    (fits Construction/renders/reference_oak.jpg)
"""
from __future__ import annotations
import math, os
import numpy as np
import torch
from PIL import Image

DEV = torch.device("cuda" if torch.cuda.is_available() else "cpu")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "renders")


def load(path, scale=1.0):
    im = Image.open(path).convert("RGB")
    if scale != 1.0:
        im = im.resize((int(im.width*scale), int(im.height*scale)), Image.LANCZOS)
    return torch.tensor(np.asarray(im, np.float32)/255.0, device=DEV)   # (H,W,3)


def _render(mu, log_scale, theta, color_logit, opa_logit, H, W, K, ox, oy):
    color = torch.sigmoid(color_logit)                       # (N,3)
    alpha = torch.sigmoid(opa_logit)                         # (N,)
    sx = torch.exp(log_scale[:, 0]).clamp(0.6, 9.0)
    sy = torch.exp(log_scale[:, 1]).clamp(0.6, 9.0)
    ct, st = torch.cos(theta), torch.sin(theta)
    cxr = mu[:, 0].round().long(); cyr = mu[:, 1].round().long()
    px = cxr[:, None] + ox[None, :]; py = cyr[:, None] + oy[None, :]   # (N,KK)
    valid = ((px >= 0) & (px < W) & (py >= 0) & (py < H)).float()
    ddx = px.float() - mu[:, 0:1]; ddy = py.float() - mu[:, 1:2]
    rx = ct[:, None]*ddx + st[:, None]*ddy
    ry = -st[:, None]*ddx + ct[:, None]*ddy
    g = torch.exp(-0.5*((rx/sx[:, None])**2 + (ry/sy[:, None])**2))
    w = alpha[:, None] * g * valid                           # (N,KK)
    idx = (py.clamp(0, H-1)*W + px.clamp(0, W-1)).reshape(-1)
    wsum = torch.zeros(H*W, device=DEV).index_add_(0, idx, w.reshape(-1))
    csum = torch.zeros(H*W, 3, device=DEV).index_add_(0, idx, (w[:, :, None]*color[:, None, :]).reshape(-1, 3))
    img = (csum/(wsum[:, None] + 1e-5)).reshape(H, W, 3)
    return img, wsum.reshape(H, W)


def fit(target, N=16000, iters=700, K=13):
    H, W, _ = target.shape
    # jittered-grid init so the splats tile the image, coloured from the photo
    cols_n = max(1, int(round(math.sqrt(N*W/H)))); rows_n = max(1, N//cols_n)
    ys = torch.linspace(2, H-3, rows_n, device=DEV); xs = torch.linspace(2, W-3, cols_n, device=DEV)
    gy, gx = torch.meshgrid(ys, xs, indexing="ij")
    mu = torch.stack([gx.reshape(-1), gy.reshape(-1)], 1)
    if mu.shape[0] < N:
        extra = torch.rand(N-mu.shape[0], 2, device=DEV)*torch.tensor([W, H], device=DEV)
        mu = torch.cat([mu, extra], 0)
    mu = (mu[:N] + torch.randn(N, 2, device=DEV)*1.4)
    xi = mu[:, 0].long().clamp(0, W-1); yi = mu[:, 1].long().clamp(0, H-1)
    c0 = target[yi, xi].clamp(1e-3, 1-1e-3)
    log_scale = torch.full((N, 2), math.log(2.1), device=DEV)
    theta = torch.zeros(N, device=DEV)
    color_logit = torch.log(c0/(1-c0))
    opa_logit = torch.full((N,), 1.2, device=DEV)
    for p in (mu, log_scale, theta, color_logit, opa_logit): p.requires_grad_(True)
    opt = torch.optim.Adam([
        {"params": [mu], "lr": 0.7}, {"params": [log_scale], "lr": 0.025},
        {"params": [theta], "lr": 0.02}, {"params": [color_logit], "lr": 0.05},
        {"params": [opa_logit], "lr": 0.05}])
    off = torch.arange(-(K//2), K//2+1, device=DEV)
    oy, ox = torch.meshgrid(off, off, indexing="ij"); ox = ox.reshape(-1); oy = oy.reshape(-1)
    for it in range(iters):
        opt.zero_grad()
        img, _ = _render(mu, log_scale, theta, color_logit, opa_logit, H, W, K, ox, oy)
        loss = (img-target).abs().mean() + ((img-target)**2).mean()
        loss.backward(); opt.step()
        with torch.no_grad(): mu.clamp_(-K, torch.tensor([W+K, H+K], device=DEV).max())
        if it % 100 == 0 or it == iters-1:
            print(f"  iter {it:4d}  L1+L2 {loss.item():.4f}")
    with torch.no_grad():
        img, wsum = _render(mu, log_scale, theta, color_logit, opa_logit, H, W, K, ox, oy)
    return {"mu": mu.detach(), "scale": torch.exp(log_scale).detach(), "theta": theta.detach(),
            "color": torch.sigmoid(color_logit).detach(), "opacity": torch.sigmoid(opa_logit).detach(),
            "H": H, "W": W}, img.detach(), wsum.detach()


def main():
    target = load(os.path.join(OUT, "reference_oak.jpg"), scale=0.9)
    print(f"fitting {target.shape[1]}x{target.shape[0]} on {DEV} ...")
    P, recon, wsum = fit(target, N=18000, iters=800, K=13)
    Image.fromarray((recon.clamp(0, 1).cpu().numpy()*255).astype(np.uint8)).save(os.path.join(OUT, "gsplat_recon.png"))
    np.savez(os.path.join(OUT, "gsplat_params.npz"),
             **{k: (v.cpu().numpy() if torch.is_tensor(v) else v) for k, v in P.items()})
    print("saved gsplat_recon.png + gsplat_params.npz  |  splats:", P["mu"].shape[0])


if __name__ == "__main__":
    main()
