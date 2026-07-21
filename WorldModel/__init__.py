"""
World Model — generative model trained on real 3DGS captures.

Architecture:
  Real 3DGS captures (.ply) → SplatDataset → VAE/Diffusion → Generated splats
                                                                      │
                                           Chimera Engine (GPU render) │
                                                                      ▼
                                                              Rendered scene

Phase 1: Data ingestion — load standard 3DGS .ply files, normalize, store
Phase 2: Training — VAE learns latent space of real splat distributions
Phase 3: Generation — sample latent vectors → new objects
Phase 4: Composition — place generated objects into Chimera Engine scenes
"""

__version__ = "0.1.0"
