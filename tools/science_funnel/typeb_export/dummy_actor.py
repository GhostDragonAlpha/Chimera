"""TypeB-P3 dummy actor: a 64->128->128->8 dense net with FIXED seeded weights.

Astra's illustrative sizing (lane-archive): 25,600 multiply-accumulates per decision,
103,456 bytes of float32 weights+biases (25,864 parameters). DUMMY policy: the weights
are a frozen seeded sample -- no training has happened and no behavior claim is made.
The export is immutable: sha256 of the npz byte stream is pinned in the manifest.
"""
from __future__ import annotations

import hashlib
import numpy as np

ARCHITECTURE = (64, 128, 128, 8)
ACTIVATION = "tanh"
SEED = 380121  # wave-38 lineage + P3 lane


def param_count(arch=ARCHITECTURE) -> int:
    return int(sum(arch[i] * arch[i + 1] + arch[i + 1] for i in range(len(arch) - 1)))


def mac_count(arch=ARCHITECTURE) -> int:
    return int(sum(arch[i] * arch[i + 1] for i in range(len(arch) - 1)))


def export_dummy_actor(seed: int = SEED, arch=ARCHITECTURE) -> dict[str, np.ndarray]:
    """Fixed-seed weights, float32, C-contiguous. Deterministic given (seed, arch)."""
    rng = np.random.Generator(np.random.PCG64(seed))
    params: dict[str, np.ndarray] = {}
    # Xavier-glorot uniform limits per layer, computed in float64 then cast once.
    for i in range(len(arch) - 1):
        fan_in, fan_out = arch[i], arch[i + 1]
        limit = float(np.sqrt(6.0 / (fan_in + fan_out)))
        w = rng.uniform(-limit, limit, size=(fan_in, fan_out)).astype(np.float32)
        b = rng.uniform(-limit, limit, size=(fan_out,)).astype(np.float32)
        params[f"W{i}"] = np.ascontiguousarray(w)
        params[f"b{i}"] = np.ascontiguousarray(b)
    return params


def weights_bytes(params: dict[str, np.ndarray]) -> bytes:
    """Canonical byte serialization: np.savez to an in-memory buffer."""
    import io
    buf = io.BytesIO()
    np.savez(buf, **params)
    return buf.getvalue()


def weights_sha256(params: dict[str, np.ndarray]) -> str:
    return hashlib.sha256(weights_bytes(params)).hexdigest()
