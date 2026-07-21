"""
World Model — VAE for 3DGS splat clouds.

Architecture:
  Encoder: PointNet-style → global latent vector (256d)
  Decoder: latent → N×D splat parameters
  Trained on normalized splat clouds from real captures.

Scaling: for N > 100K splats, use patch-based encoding (not yet implemented).
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from pathlib import Path


class SplatEncoder(nn.Module):
    """PointNet-style encoder: per-point MLP → max pool → latent."""

    def __init__(self, point_dim: int = 10, latent_dim: int = 256):
        super().__init__()
        self.point_dim = point_dim
        self.latent_dim = latent_dim

        self.mlp = nn.Sequential(
            nn.Linear(point_dim, 128), nn.ReLU(),
            nn.Linear(128, 256), nn.ReLU(),
            nn.Linear(256, 512), nn.ReLU(),
        )
        self.fc_mu = nn.Linear(512, latent_dim)
        self.fc_logvar = nn.Linear(512, latent_dim)

    def forward(self, x):
        """
        x: (B, N, point_dim) — batch of normalized splat clouds
        Returns: mu (B, latent_dim), logvar (B, latent_dim)
        """
        B, N, D = x.shape
        h = self.mlp(x)         # (B, N, 512)
        h = h.max(dim=1)[0]     # (B, 512) — max pool over points
        mu = self.fc_mu(h)
        logvar = self.fc_logvar(h)
        return mu, logvar


class SplatDecoder(nn.Module):
    """Decode latent vector to a fixed number of splats."""

    def __init__(self, latent_dim: int = 256, num_splats: int = 4096, point_dim: int = 10):
        super().__init__()
        self.num_splats = num_splats
        self.point_dim = point_dim

        self.fc = nn.Sequential(
            nn.Linear(latent_dim, 512), nn.ReLU(),
            nn.Linear(512, 1024), nn.ReLU(),
            nn.Linear(1024, 2048), nn.ReLU(),
            nn.Linear(2048, num_splats * point_dim),
        )

    def forward(self, z):
        """
        z: (B, latent_dim)
        Returns: (B, num_splats, point_dim)
        """
        B = z.shape[0]
        out = self.fc(z)  # (B, N*D)
        out = out.view(B, self.num_splats, self.point_dim)

        # Split into semantics
        # [x, y, z, r, g, b, opacity, sx, sy, sz]
        xyz = out[..., :3]          # positions
        rgb = torch.sigmoid(out[..., 3:6])  # colors in [0,1]
        opa = torch.sigmoid(out[..., 6:7])  # opacity in [0,1]
        scale = torch.exp(out[..., 7:10])   # scales (log → exp)

        return torch.cat([xyz, rgb, opa, scale], dim=-1)


class SplatVAE(nn.Module):
    """Full VAE for splat cloud generation."""

    def __init__(self, num_splats: int = 4096, point_dim: int = 10, latent_dim: int = 256):
        super().__init__()
        self.num_splats = num_splats
        self.point_dim = point_dim
        self.latent_dim = latent_dim
        self.encoder = SplatEncoder(point_dim, latent_dim)
        self.decoder = SplatDecoder(latent_dim, num_splats, point_dim)

    def reparameterize(self, mu, logvar):
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + eps * std

    def forward(self, x):
        mu, logvar = self.encoder(x)
        z = self.reparameterize(mu, logvar)
        recon = self.decoder(z)
        return recon, mu, logvar

    def sample(self, n: int = 1) -> torch.Tensor:
        """Generate n new splat clouds."""
        z = torch.randn(n, self.latent_dim)
        return self.decoder(z)

    def encode(self, x) -> torch.Tensor:
        """Encode a splat cloud to latent vector (no sampling)."""
        mu, _ = self.encoder(x)
        return mu


def splat_cloud_to_tensor(cloud) -> torch.Tensor:
    """Convert a SplatCloud to a fixed-size tensor for training."""
    from WorldModel.splat_io import SplatCloud
    n = cloud.count
    data = np.concatenate([
        cloud.positions,           # 3
        cloud.colors,              # 3
        cloud.opacities[:, None],   # 1
        np.log(cloud.scales + 1e-8), # 3
    ], axis=1).astype(np.float32)
    return torch.tensor(data)


def tensor_to_splat_cloud(tensor: torch.Tensor) -> "SplatCloud":
    """Convert a generated tensor back to a SplatCloud."""
    from WorldModel.splat_io import SplatCloud
    data = tensor.detach().cpu().numpy()
    return SplatCloud(
        positions=data[..., :3].astype(np.float32),
        colors=data[..., 3:6].astype(np.float32),
        opacities=data[..., 6].astype(np.float32),
        scales=np.exp(data[..., 7:10]).astype(np.float32),
        rotations=np.tile(np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32),
                          (len(data), 1)),
    )
