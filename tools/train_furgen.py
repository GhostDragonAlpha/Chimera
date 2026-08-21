"""train_furgen.py -- the neural patch generator (operator pick: option 3).

Flow matching over WHOLE patches (2048 x 14 splat records), conditioned on the
patch's own color/pattern averages. The GMM concept model (train_material.py)
rolls dice per splat -- felt, not locks. Locks are agreement BETWEEN splats, so
the unit of generation is the patch. The model learns the joint distribution of
the qualified corpus; rotation augmentation (continuous theta about the membrane
normal, quats conjugated exactly) multiplies 136 real patches into a usable
training set without inventing anything.

Honest limit: 136 patches is thin. Samples will riff on real instances, not
invent new lock families. More donors -> more variety. The gate is the same eye
that qualified the real patches: generated patches must pass "does this look
like teddy bear fur?"

  .venv-gs/Scripts/python.exe tools/train_furgen.py \
      --corpus models/littlebear/corpus/fur_qualified.npz \
      --out models/littlebear/furgen.pt --steps 20000
  # sample:
  .venv-gs/Scripts/python.exe tools/train_furgen.py \
      --corpus models/littlebear/corpus/fur_qualified.npz \
      --ckpt models/littlebear/furgen.pt --sample 8 --sampledir .tmp/furgen
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

DIM = 256
DEPTH = 6
HEADS = 8

# feature layout in a patch row
U, V, H = 0, 1, 2
RGB = slice(3, 6)
ALPHA = 6
LOGS = slice(7, 10)
QUAT = slice(10, 14)


def rotate_patch(p: np.ndarray, theta: float, rng) -> np.ndarray:
    """Rotate (u,v) about the membrane normal; conjugate quats exactly."""
    from extract_genomes import quat_mul
    out = p.copy()
    c, s = math.cos(theta), math.sin(theta)
    u = out[:, U] * c - out[:, V] * s
    v = out[:, U] * s + out[:, V] * c
    out[:, U], out[:, V] = u, v
    qr = np.tile(np.array([math.cos(theta / 2), 0.0, 0.0, math.sin(theta / 2)]), (len(out), 1))
    q = quat_mul(qr, out[:, QUAT].astype(np.float64))
    q[q[:, 0] < 0] *= -1
    out[:, QUAT] = q
    return out


def cond_of(p: np.ndarray) -> np.ndarray:
    """The conditioning vector (operator: color avg + pattern avg)."""
    real = p[p[:, ALPHA] > 0]
    return np.concatenate([
        real[:, RGB].mean(0),                      # color avg (3)
        [real[:, H].mean(), real[:, H].std()],     # relief avg + spread (2)
        real[:, LOGS].mean(0),                     # size avg (3)
        [real[:, ALPHA].mean()],                   # opacity avg (1)
    ])                                             # = 9


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--out", default="models/littlebear/furgen.pt")
    ap.add_argument("--ckpt", default=None, help="resume / load for sampling")
    ap.add_argument("--steps", type=int, default=20000)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--sample", type=int, default=0, help="sample N patches, no training")
    ap.add_argument("--sampledir", default=".tmp/furgen")
    ap.add_argument("--euler", type=int, default=50)
    a = ap.parse_args()

    import torch
    import torch.nn as nn

    d = np.load(a.corpus)
    P = d["patches"].astype(np.float64)          # (N, 2048, 14), padding alpha=0
    W = d["weights"].astype(np.float64) if "weights" in d else np.ones(len(P))
    N, NP, F = P.shape

    # normalization stats over REAL rows only
    real_rows = P[P[:, :, ALPHA] > 0]
    mu = real_rows.mean(0)
    sd = real_rows.std(0) + 1e-6
    mu[QUAT], sd[QUAT] = 0.0, 1.0                # quats: already unit-ish, keep raw
    C = np.stack([cond_of(p) for p in P])
    cmu, csd = C.mean(0), C.std(0) + 1e-6

    class TimeMLP(nn.Module):
        def __init__(self):
            super().__init__()
            self.net = nn.Sequential(nn.Linear(64, DIM), nn.SiLU(), nn.Linear(DIM, DIM))

        def forward(self, t):
            freqs = torch.exp(-math.log(10000) * torch.arange(32, device=t.device) / 31)
            ang = t[:, None] * freqs[None] * 1000
            return self.net(torch.cat([ang.sin(), ang.cos()], -1))

    class FurGen(nn.Module):
        def __init__(self):
            super().__init__()
            self.inp = nn.Linear(F, DIM)
            self.pos = nn.Parameter(torch.randn(1, NP, DIM) * 0.02)
            self.time = TimeMLP()
            self.cond = nn.Sequential(nn.Linear(C.shape[1], DIM), nn.SiLU(), nn.Linear(DIM, DIM))
            layer = nn.TransformerEncoderLayer(DIM, HEADS, DIM * 4, dropout=0.0,
                                               batch_first=True, norm_first=True)
            self.tr = nn.TransformerEncoder(layer, DEPTH)
            self.out = nn.Linear(DIM, F)

        def forward(self, x, t, c):
            h = self.inp(x) + self.pos + self.time(t)[:, None] + self.cond(c)[:, None]
            return self.out(self.tr(h))

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    model = FurGen().to(dev)
    ckpt = a.ckpt or (a.out if Path(a.out).exists() and a.sample else None)
    if ckpt and Path(ckpt).exists():
        model.load_state_dict(torch.load(ckpt, map_location=dev)["model"])
        print(f"loaded {ckpt}")

    tmu = torch.tensor(mu, dtype=torch.float32, device=dev)
    tsd = torch.tensor(sd, dtype=torch.float32, device=dev)
    tC = torch.tensor((C - cmu) / csd, dtype=torch.float32, device=dev)

    if a.sample:
        model.eval()
        out_dir = Path(a.sampledir)
        out_dir.mkdir(parents=True, exist_ok=True)
        rng = np.random.default_rng(0)
        pick = rng.choice(N, size=a.sample)  # conditioning borrowed from real patches
        with torch.no_grad():
            for k, pi in enumerate(pick):
                c = tC[pi:pi + 1]
                x = torch.randn(1, NP, F, device=dev)
                for i in range(a.euler):
                    t = torch.full((1,), i / a.euler, device=dev)
                    x = x + model(x, t, c) / a.euler
                gen = (x[0] * tsd + tmu).cpu().numpy().astype(np.float64)
                # physical cleanup: unit quats, canonical hemisphere, sane ranges
                q = gen[:, QUAT]
                q /= np.linalg.norm(q, axis=1, keepdims=True)
                q[q[:, 0] < 0] *= -1
                gen[:, QUAT] = q
                gen[:, ALPHA] = np.clip(gen[:, ALPHA], 0, 1)
                gen[:, RGB] = np.clip(gen[:, RGB], 0, 1)
                np.save(out_dir / f"gen{k:03d}.npy", gen)
                print(f"gen{k:03d}: cond from patch #{pi} -> {out_dir / f'gen{k:03d}.npy'}")
        return 0

    # ---- train ----
    opt = torch.optim.AdamW(model.parameters(), lr=a.lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, a.steps)
    prob = W / W.sum()
    rng = np.random.default_rng(0)
    model.train()
    for step in range(1, a.steps + 1):
        idx = rng.choice(N, size=a.batch, p=prob)
        batch = np.stack([rotate_patch(P[i], rng.uniform(0, 2 * math.pi), rng) for i in idx])
        x1 = torch.tensor((batch - mu) / sd, dtype=torch.float32, device=dev)
        c = tC[torch.tensor(idx, device=dev)]
        x0 = torch.randn_like(x1)
        t = torch.rand(a.batch, device=dev)
        xt = (1 - t[:, None, None]) * x0 + t[:, None, None] * x1
        loss = nn.functional.mse_loss(model(xt, t, c), x1 - x0)
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
        sched.step()
        if step % 500 == 0:
            print(f"{step}/{a.steps} loss {loss.item():.4f}", flush=True)
        if step % 2000 == 0:
            torch.save({"model": model.state_dict(), "mu": mu, "sd": sd,
                        "cmu": cmu, "csd": csd, "step": step}, a.out)
    torch.save({"model": model.state_dict(), "mu": mu, "sd": sd,
                "cmu": cmu, "csd": csd, "step": a.steps,
                "corpus": a.corpus, "n_patches": int(N)}, a.out)
    json.dump({"corpus": a.corpus, "n_patches": int(N), "steps": a.steps,
               "final_loss": float(loss.item())},
              Path(str(a.out).replace(".pt", ".json")).open("w"))
    print("->", a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
