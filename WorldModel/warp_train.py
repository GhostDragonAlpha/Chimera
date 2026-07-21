"""GPU-accelerated data generation using Warp. Zero CPU bottlenecks."""
import sys; sys.path.insert(0, r'E:\PythonChimera')
import warp as wp
import numpy as np
import torch

wp.init()

MAX_SPLATS = 4096
SPLATS_PER_TREE = 2048


@wp.kernel
def generate_tree_kernel(
    seeds: wp.array(dtype=wp.int32),
    out_positions: wp.array(dtype=wp.vec3),
    out_colors: wp.array(dtype=wp.vec3),
    out_opacities: wp.array(dtype=wp.float32),
    out_scales: wp.array(dtype=wp.vec3),
    tree_count: wp.int32,
):
    tid = wp.tid()
    if tid >= tree_count:
        return

    seed = seeds[tid]
    state = wp.rand_init(seed)
    base = tid * SPLATS_PER_TREE

    trunk_h = 100.0 + wp.randf(state) * 200.0
    trunk_r = 4.0 + wp.randf(state) * 10.0
    branch_count = 3 + wp.randi(state) % 3
    n_trunk = SPLATS_PER_TREE // 3
    n_br = SPLATS_PER_TREE // (branch_count * 3)
    n_leaves = SPLATS_PER_TREE - n_trunk - branch_count * n_br

    # Trunk
    for i in range(n_trunk):
        t = wp.float32(i) / wp.float32(max(n_trunk - 1, 1))
        y = -150.0 + trunk_h * t
        r = trunk_r * (1.0 - t * 0.7)
        out_positions[base + i] = wp.vec3(wp.randf(state) * r * 0.3, y, wp.randf(state) * r * 0.3)
        out_colors[base + i] = wp.vec3(0.32, 0.16, 0.07)
        out_opacities[base + i] = 0.9
        out_scales[base + i] = wp.vec3(r * 0.6, r * 0.6, r * 0.6)

    # Branches
    for b in range(branch_count):
        angle = wp.float32(b) * 6.28318 / wp.float32(branch_count) + wp.randf(state) * 0.5
        br_len = trunk_h * 0.4
        br_r = trunk_r * 0.4
        split_t = 0.5 + wp.randf(state) * 0.3
        start_y = -150.0 + trunk_h * split_t
        dx = wp.sin(angle) * 0.5
        dz = wp.cos(angle) * 0.5
        br_base = base + n_trunk + b * n_br
        for i in range(n_br):
            t = wp.float32(i) / wp.float32(max(n_br - 1, 1))
            r = br_r * (1.0 - t * 0.5)
            out_positions[br_base + i] = wp.vec3(dx * br_len * t + wp.randf(state) * r * 0.2, start_y + 0.5 * br_len * t, dz * br_len * t + wp.randf(state) * r * 0.2)
            out_colors[br_base + i] = wp.vec3(0.30, 0.15, 0.06)
            out_opacities[br_base + i] = 0.85
            out_scales[br_base + i] = wp.vec3(r * 0.5, r * 0.5, r * 0.5)

    # Leaves
    leaf_base = base + n_trunk + branch_count * n_br
    for i in range(n_leaves):
        lx = wp.randf(state) * 80.0 - 40.0
        ly = -150.0 + trunk_h * 0.6 + wp.randf(state) * trunk_h * 0.6
        lz = wp.randf(state) * 80.0 - 40.0
        out_positions[leaf_base + i] = wp.vec3(lx, ly, lz)
        out_colors[leaf_base + i] = wp.vec3(0.05, 0.4 + wp.randf(state) * 0.4, 0.08)
        out_opacities[leaf_base + i] = 0.7 + wp.randf(state) * 0.25
        s = 1.5 + wp.randf(state) * 3.0
        out_scales[leaf_base + i] = wp.vec3(s, s, s)


def generate_trees_gpu(n_trees: int = 500):
    """Generate N trees entirely on GPU using Warp."""
    print(f"Generating {n_trees} trees on GPU (Warp)...")

    total = n_trees * SPLATS_PER_TREE
    seeds = wp.array(np.random.randint(0, 2**31, n_trees, dtype=np.int32), dtype=wp.int32)
    pos = wp.zeros(total, dtype=wp.vec3)
    col = wp.zeros(total, dtype=wp.vec3)
    opa = wp.zeros(total, dtype=wp.float32)
    sca = wp.zeros(total, dtype=wp.vec3)

    wp.launch(generate_tree_kernel, dim=n_trees,
              inputs=[seeds, pos, col, opa, sca, n_trees])

    # Convert to numpy (still on GPU until this point)
    p = pos.numpy().reshape(n_trees, SPLATS_PER_TREE, 3)
    c = col.numpy().reshape(n_trees, SPLATS_PER_TREE, 3)
    o = opa.numpy().reshape(n_trees, SPLATS_PER_TREE, 1)
    s = sca.numpy().reshape(n_trees, SPLATS_PER_TREE, 3)

    # Normalize each tree
    for i in range(n_trees):
        centroid = p[i].mean(axis=0)
        p[i] -= centroid
        ext = np.linalg.norm(p[i].max(0) - p[i].min(0)) or 1.0
        p[i] /= ext

    # Combine: xyz(3) + rgb(3) + opacity(1) + log_scale(3) = 10
    dataset = np.concatenate([
        p.astype(np.float32),
        c.astype(np.float32),
        o.astype(np.float32),
        np.log(np.maximum(s.astype(np.float32), 1e-8)),
    ], axis=2)

    print(f"Dataset: {dataset.shape} ({dataset.nbytes/1e6:.1f} MB)")
    return dataset


def train_on_gpu(dataset: np.ndarray, epochs: int = 300, latent_dim: int = 64):
    """Train VAE on GPU using PyTorch."""
    from WorldModel.model import SplatVAE
    from WorldModel.splat_io import SplatCloud, save_ply
    from pathlib import Path

    n, sc, d = dataset.shape
    data_t = torch.tensor(dataset).cuda()
    model = SplatVAE(num_splats=sc, point_dim=d, latent_dim=latent_dim).cuda()
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)

    print(f"Training VAE on GPU: {n} trees, {sc} splats, {d}d -> {latent_dim}d, {epochs} epochs")

    for e in range(epochs):
        idx = torch.randperm(n)
        tl = 0
        bs = 16
        nb = n // bs
        for b in range(nb):
            batch = data_t[idx[b*bs:(b+1)*bs]]
            recon, mu, logvar = model(batch)
            rl = torch.nn.functional.mse_loss(recon, batch) * batch.numel()
            kl = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())
            loss = rl + 0.0001 * kl
            opt.zero_grad()
            loss.backward()
            opt.step()
            tl += loss.item()
        if e % 50 == 0:
            print(f"  Epoch {e}: loss={tl/nb:.0f}")

    out = Path("WorldModel/training_data")
    out.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), out / "warp_vae.pt")
    print(f"Saved {out}/warp_vae.pt")

    # Generate samples
    model.eval()
    with torch.no_grad():
        for i in range(5):
            z = torch.randn(1, latent_dim).cuda()
            gen = model.decoder(z).cpu().numpy()[0]
            gen[:, 7:10] = np.exp(gen[:, 7:10])
            gen[:, :3] *= 250

            cloud = SplatCloud(
                positions=gen[:, :3].astype(np.float32),
                colors=np.clip(gen[:, 3:6], 0, 1).astype(np.float32),
                opacities=np.clip(gen[:, 6], 0, 1).astype(np.float32),
                scales=gen[:, 7:10].astype(np.float32),
                rotations=np.tile(np.array([0., 0., 0., 1.], dtype=np.float32), (sc, 1)),
            )
            save_ply(cloud, str(out / f"warp_gen_{i}.ply"))

    print("Done — model trained, trees generated.")
    return model


if __name__ == "__main__":
    import sys
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    dataset = generate_trees_gpu(n)
    train_on_gpu(dataset)
