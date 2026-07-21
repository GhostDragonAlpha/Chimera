"""Parallel tree generator — uses all CPU cores for training data."""
import sys; sys.path.insert(0, r'E:\PythonChimera')
import torch, numpy as np, math
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import multiprocessing as mp

def generate_one_tree(seed: int) -> np.ndarray:
    """Generate a single physics-informed tree. Runs per-worker."""
    import sys, os
    sys.path.insert(0, r'E:\PythonChimera')
    os.chdir(r'E:\PythonChimera')
    from WorldModel.physics_tree import grow_tree, segments_to_splats
    np.random.seed(seed)
    segs = grow_tree(
        trunk_height=200 + np.random.uniform(-50, 80),
        trunk_radius=8 + np.random.uniform(-2, 4),
        max_depth=np.random.randint(2, 4),
        seed=seed,
    )
    data = segments_to_splats(segs, target_count=2048)
    p = data['positions'] - data['positions'].mean(axis=0)
    ext = np.linalg.norm(p.max(0) - p.min(0)) or 1
    p /= ext
    return np.concatenate([
        p, data['colors'], data['opacities'][:, None],
        np.log(data['scales'] + 1e-8)
    ], axis=1)[:2048].astype(np.float32)


def generate_dataset(n: int = 500, workers: int = None) -> np.ndarray:
    """Generate N trees using all CPU cores."""
    workers = workers or max(1, mp.cpu_count() - 2)
    print(f"Generating {n} trees using {workers} workers...")

    trees = []
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for i, tree in enumerate(pool.map(generate_one_tree, range(n))):
            trees.append(tree)
            if i % 50 == 0:
                print(f"  {i}/{n}")

    dataset = np.stack(trees)
    print(f"Dataset: {dataset.shape} ({dataset.nbytes / 1e6:.1f} MB)")
    return dataset


def train_and_save(dataset: np.ndarray, out_dir: str = "WorldModel/training_data",
                   epochs: int = 200, latent_dim: int = 32, batch_size: int = 16):
    """Train SplatVAE on GPU, save model, generate samples."""
    from WorldModel.model import SplatVAE
    from WorldModel.splat_io import SplatCloud, save_ply

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    n, splat_count, dim = dataset.shape
    data_t = torch.tensor(dataset).cuda()
    model = SplatVAE(num_splats=splat_count, point_dim=dim, latent_dim=latent_dim).cuda()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

    print(f"\nTraining VAE on GPU ({n} samples, {splat_count} splats, {dim}d -> {latent_dim}d)")

    for epoch in range(epochs):
        idx = torch.randperm(n)
        total_loss = 0
        n_batches = n // batch_size

        for b in range(n_batches):
            batch = data_t[idx[b * batch_size:(b + 1) * batch_size]]
            recon, mu, logvar = model(batch)
            r_loss = torch.nn.functional.mse_loss(recon, batch) * batch.numel()
            kl = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())
            loss = r_loss + 0.0001 * kl
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        if epoch % 40 == 0:
            print(f"  Epoch {epoch}: loss={total_loss / n_batches:.0f}")

    torch.save(model.state_dict(), out / "physics_vae.pt")
    print(f"Saved {out}/physics_vae.pt")

    # Generate samples
    print("\nGenerating 5 new trees...")
    model.eval()
    with torch.no_grad():
        for i in range(5):
            z = torch.randn(1, latent_dim).cuda()
            gen = model.decoder(z).cpu().numpy()[0]
            gen[:, 7:10] = np.exp(gen[:, 7:10])
            gen[:, :3] *= 200

            cloud = SplatCloud(
                positions=gen[:, :3].astype(np.float32),
                colors=np.clip(gen[:, 3:6], 0, 1).astype(np.float32),
                opacities=np.clip(gen[:, 6], 0, 1).astype(np.float32),
                scales=gen[:, 7:10].astype(np.float32),
                rotations=np.tile(np.array([0., 0., 0., 1.], dtype=np.float32), (splat_count, 1)),
            )
            fname = out / f"gen_tree_{i}.ply"
            save_ply(cloud, str(fname))
            extent = np.linalg.norm(cloud.positions.max(0) - cloud.positions.min(0))
            print(f"  {fname.name} ({cloud.count} splats, extent={extent:.0f})")

    print("Done — VAE trained, trees generated.")


if __name__ == "__main__":
    import sys
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    dataset = generate_dataset(n)
    train_and_save(dataset)
