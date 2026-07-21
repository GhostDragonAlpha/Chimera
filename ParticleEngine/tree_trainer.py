"""
Tree training data generator + simple VAE for oak tree generation.

Generates procedural oak tree parameter sets, converts them to
particle point clouds, and trains a VAE to generate new realistic trees.

Usage:
  python -m ParticleEngine.tree_trainer generate  # Generate training data
  python -m ParticleEngine.tree_trainer train      # Train VAE
  python -m ParticleEngine.tree_trainer sample     # Generate new trees
"""

import sys, json, math, numpy as np
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class TreeParams:
    """All parameters needed to generate an oak tree."""
    trunk_height: float = 280.0
    trunk_radius: float = 12.0
    trunk_gnarl: float = 0.15
    num_main_branches: int = 4
    branch_length: float = 120.0
    branch_angle_min: float = 0.4
    branch_angle_max: float = 0.9
    branch_depth: int = 3
    branch_spread: float = 0.5
    leaf_density: int = 30
    leaf_size_min: float = 3.0
    leaf_size_max: float = 8.0
    acorn_density: int = 8
    root_count: int = 500
    moss_count: int = 3000
    atmosphere_count: int = 2000
    seed: int = 0

    def vectorize(self) -> np.ndarray:
        """Convert to a fixed-length float32 vector for ML."""
        return np.array([
            self.trunk_height, self.trunk_radius, self.trunk_gnarl,
            self.num_main_branches, self.branch_length,
            self.branch_angle_min, self.branch_angle_max,
            self.branch_depth, self.branch_spread,
            self.leaf_density, self.leaf_size_min, self.leaf_size_max,
            self.acorn_density, self.root_count, self.moss_count,
            self.atmosphere_count, self.seed,
        ], dtype=np.float32)

    @classmethod
    def from_vector(cls, v: np.ndarray) -> "TreeParams":
        return cls(
            trunk_height=v[0], trunk_radius=v[1], trunk_gnarl=v[2],
            num_main_branches=int(v[3]), branch_length=v[4],
            branch_angle_min=v[5], branch_angle_max=v[6],
            branch_depth=int(v[7]), branch_spread=v[8],
            leaf_density=int(v[9]), leaf_size_min=v[10], leaf_size_max=v[11],
            acorn_density=int(v[12]), root_count=int(v[13]),
            moss_count=int(v[14]), atmosphere_count=int(v[15]),
            seed=int(v[16]),
        )

    @classmethod
    def random(cls) -> "TreeParams":
        """Generate random realistic oak parameters."""
        return cls(
            trunk_height=np.random.uniform(200, 400),
            trunk_radius=np.random.uniform(8, 18),
            trunk_gnarl=np.random.uniform(0.05, 0.3),
            num_main_branches=np.random.randint(3, 6),
            branch_length=np.random.uniform(80, 180),
            branch_angle_min=np.random.uniform(0.3, 0.6),
            branch_angle_max=np.random.uniform(0.7, 1.2),
            branch_depth=np.random.randint(2, 4),
            branch_spread=np.random.uniform(0.3, 0.7),
            leaf_density=np.random.randint(15, 50),
            leaf_size_min=np.random.uniform(2.0, 5.0),
            leaf_size_max=np.random.uniform(5.0, 12.0),
            acorn_density=np.random.randint(3, 15),
            root_count=np.random.randint(200, 800),
            moss_count=np.random.randint(1000, 5000),
            atmosphere_count=np.random.randint(500, 3000),
            seed=np.random.randint(0, 2**31),
        )


def generate_dataset(n_samples: int = 1000, out_dir: str = "ParticleEngine/training_data"):
    """Generate N random oak tree parameter sets and save them."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    params_list = []
    for i in range(n_samples):
        tp = TreeParams.random()
        params_list.append(tp.vectorize().tolist())
        if i % 100 == 0:
            print(f"  Generated {i}/{n_samples}")

    data = np.array(params_list, dtype=np.float32)
    np.save(out / "tree_params.npy", data)

    # Also save a JSON metadata file
    meta = {
        "n_samples": n_samples,
        "vector_size": len(TreeParams().vectorize()),
        "feature_names": [
            "trunk_height", "trunk_radius", "trunk_gnarl",
            "num_main_branches", "branch_length",
            "branch_angle_min", "branch_angle_max",
            "branch_depth", "branch_spread",
            "leaf_density", "leaf_size_min", "leaf_size_max",
            "acorn_density", "root_count", "moss_count",
            "atmosphere_count", "seed",
        ],
    }
    (out / "metadata.json").write_text(json.dumps(meta, indent=2))
    print(f"  Saved {n_samples} samples to {out}/")


def train_vae(data_path: str = "ParticleEngine/training_data/tree_params.npy",
              latent_dim: int = 8, epochs: int = 200, batch_size: int = 64):
    """Train a simple VAE on tree parameter vectors."""
    import torch
    import torch.nn as nn
    import torch.optim as optim

    data = np.load(data_path)
    data = (data - data.mean(axis=0)) / (data.std(axis=0) + 1e-8)
    data = torch.tensor(data, dtype=torch.float32)
    input_dim = data.shape[1]

    class TreeVAE(nn.Module):
        def __init__(self):
            super().__init__()
            self.encoder = nn.Sequential(
                nn.Linear(input_dim, 32), nn.ReLU(),
                nn.Linear(32, 16), nn.ReLU(),
            )
            self.mu = nn.Linear(16, latent_dim)
            self.logvar = nn.Linear(16, latent_dim)
            self.decoder = nn.Sequential(
                nn.Linear(latent_dim, 16), nn.ReLU(),
                nn.Linear(16, 32), nn.ReLU(),
                nn.Linear(32, input_dim),
            )

        def encode(self, x):
            h = self.encoder(x)
            return self.mu(h), self.logvar(h)

        def reparameterize(self, mu, logvar):
            std = torch.exp(0.5 * logvar)
            eps = torch.randn_like(std)
            return mu + eps * std

        def forward(self, x):
            mu, logvar = self.encode(x)
            z = self.reparameterize(mu, logvar)
            return self.decoder(z), mu, logvar

    model = TreeVAE()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    n_batches = len(data) // batch_size

    print(f"Training VAE: {input_dim}d -> {latent_dim}d latent, {epochs} epochs")
    for epoch in range(epochs):
        total_loss = 0
        idx = torch.randperm(len(data))
        for b in range(n_batches):
            batch = data[idx[b*batch_size:(b+1)*batch_size]]
            recon, mu, logvar = model(batch)
            recon_loss = nn.functional.mse_loss(recon, batch, reduction='sum')
            kl_loss = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())
            loss = recon_loss + 0.001 * kl_loss
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        if epoch % 20 == 0:
            print(f"  Epoch {epoch}: loss={total_loss/n_batches:.4f}")

    out = Path("ParticleEngine/training_data")
    torch.save(model.state_dict(), out / "tree_vae.pt")
    print(f"  Saved model to {out}/tree_vae.pt")


def sample_trees(n: int = 5):
    """Generate new tree parameters from the trained VAE."""
    import torch
    import torch.nn as nn

    data = np.load("ParticleEngine/training_data/tree_params.npy")
    mean = data.mean(axis=0)
    std = data.std(axis=0) + 1e-8
    input_dim = data.shape[1]

    class TreeVAE(nn.Module):
        def __init__(self):
            super().__init__()
            self.encoder = nn.Sequential(nn.Linear(input_dim,32),nn.ReLU(),nn.Linear(32,16),nn.ReLU())
            self.mu = nn.Linear(16, 8)
            self.logvar = nn.Linear(16, 8)
            self.decoder = nn.Sequential(nn.Linear(8,16),nn.ReLU(),nn.Linear(16,32),nn.ReLU(),nn.Linear(32,input_dim))

    model = TreeVAE()
    model.load_state_dict(torch.load("ParticleEngine/training_data/tree_vae.pt"))
    model.eval()

    trees = []
    with torch.no_grad():
        for _ in range(n):
            z = torch.randn(1, 8)
            v = model.decoder(z).numpy()[0]
            v = v * std + mean  # denormalize
            params = TreeParams.from_vector(v)
            trees.append(params)

    return trees


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m ParticleEngine.tree_trainer [generate|train|sample]")
        return 1

    cmd = sys.argv[1]
    if cmd == "generate":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
        generate_dataset(n)
    elif cmd == "train":
        train_vae()
    elif cmd == "sample":
        trees = sample_trees(5)
        for i, t in enumerate(trees):
            print(f"Tree {i}: height={t.trunk_height:.0f} radius={t.trunk_radius:.1f} "
                  f"branches={t.num_main_branches} depth={t.branch_depth} "
                  f"leaf_density={t.leaf_density}")
    else:
        print(f"Unknown command: {cmd}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
