"""splat_types — catalog of every Gaussian splat shape the system can emit.

Each splat type is a different point in the covariance parameter space.
The GPU rasterizer handles ALL of them — it reads the full 3x3 anisotropic
covariance matrix. No kernel change needed for shape.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable
import numpy as np


@dataclass
class SplatType:
    """Definition of one splat shape family."""
    name: str
    description: str
    covariance_shape: str  # how the 3x3 cov is constructed
    default_params: dict = field(default_factory=dict)
    blend_mode: str = 'alpha'  # alpha | additive | subtract
    
    def make_cov(self, normal: np.ndarray, params: dict = None) -> np.ndarray:
        """Build a 3x3 covariance matrix for this splat type.
        
        normal: (N, 3) array of unit normals
        params: override defaults
        Returns: (N, 3, 3) covariance matrices
        """
        raise NotImplementedError


# ─── SURFACE SPLAT ───────────────────────────────────────────────────────
# Flat disk aligned to surface. Thin along normal, wide in tangent plane.
# Use: ground terrain, skin, shelter walls, any surface

def emit_surface(normal, tangent_scale=1.15, normal_scale=0.35):
    """Surface splat: thin along normal, circular in tangent plane."""
    N = len(normal)
    # Build orthonormal frame
    up = np.where(np.abs(normal[:, 2:3]) < 0.9,
                  np.array([0., 0., 1.]), np.array([1., 0., 0.]))
    t1 = np.cross(up, normal)
    t1 /= np.clip(np.linalg.norm(t1, axis=1, keepdims=True), 1e-9, None)
    t2 = np.cross(normal, t1)
    
    # Covariance: flat disk
    R = np.zeros((N, 3, 3))
    R[:, :, 0] = t1 * tangent_scale
    R[:, :, 1] = t2 * tangent_scale
    R[:, :, 2] = normal * normal_scale
    return R @ R.transpose(0, 2, 1)


# ─── FIBER SPLAT ─────────────────────────────────────────────────────────
# Needle-like, elongated along fiber direction.
# Use: muscle, grass, hair, cables

def emit_fiber(normal, tangent_scale=1.15, normal_scale=0.35, 
               fiber_dir=None, elongation=3.0):
    """Fiber splat: elongated along fiber_dir in the tangent plane."""
    N = len(normal)
    up = np.where(np.abs(normal[:, 2:3]) < 0.9,
                  np.array([0., 0., 1.]), np.array([1., 0., 0.]))
    t1 = np.cross(up, normal)
    t1 /= np.clip(np.linalg.norm(t1, axis=1, keepdims=True), 1e-9, None)
    t2 = np.cross(normal, t1)
    
    if fiber_dir is not None:
        # Project fiber_dir into tangent plane
        fd = fiber_dir - np.einsum('ni,ni->n', fiber_dir, normal)[:, None] * normal
        flen = np.linalg.norm(fd, axis=1, keepdims=True)
        good = flen[:, 0] > 1e-3
        fd = np.where(good[:, None], fd / np.clip(flen, 1e-6, None), t1)
        # Align major axis to fiber direction
        t1 = fd
        t2 = np.cross(normal, t1)
        r_major = tangent_scale * elongation
        r_minor = tangent_scale / elongation  # area-preserving
    else:
        r_major = tangent_scale
        r_minor = tangent_scale
    
    R = np.zeros((N, 3, 3))
    R[:, :, 0] = t1 * r_major
    R[:, :, 1] = t2 * r_minor
    R[:, :, 2] = normal * normal_scale
    return R @ R.transpose(0, 2, 1)


# ─── POINT SPLAT ─────────────────────────────────────────────────────────
# Isotropic sphere. No orientation.
# Use: dust, particles, distant objects, fog

def emit_point(positions, radius=1.0):
    """Point splat: isotropic sphere."""
    N = len(positions)
    cov = np.zeros((N, 3, 3))
    cov[:, 0, 0] = radius ** 2
    cov[:, 1, 1] = radius ** 2
    cov[:, 2, 2] = radius ** 2
    return cov


# ─── BEAM SPLAT ─────────────────────────────────────────────────────────
# Long along one axis, thin in others.
# Use: beacon signal, light rays, laser

def emit_beam(direction, length=10.0, thickness=0.5):
    """Beam splat: long along direction, thin perpendicular."""
    N = len(direction)
    norm = np.linalg.norm(direction, axis=1, keepdims=True)
    d = direction / np.clip(norm, 1e-6, None)
    
    # Build frame where d is the long axis
    up = np.where(np.abs(d[:, 2:3]) < 0.9,
                  np.array([0., 0., 1.]), np.array([1., 0., 0.]))
    t1 = np.cross(up, d)
    t1 /= np.clip(np.linalg.norm(t1, axis=1, keepdims=True), 1e-9, None)
    t2 = np.cross(d, t1)
    
    R = np.zeros((N, 3, 3))
    R[:, :, 0] = d * length       # long
    R[:, :, 1] = t1 * thickness   # thin
    R[:, :, 2] = t2 * thickness   # thin
    return R @ R.transpose(0, 2, 1)


# ─── CLOUD SPLAT ─────────────────────────────────────────────────────────
# Large, soft, isotropic. Low alpha.
# Use: atmosphere, fog banks, gas clouds

def emit_cloud(positions, radius=100.0, alpha=0.1):
    """Cloud splat: large soft sphere with low alpha."""
    N = len(positions)
    cov = np.zeros((N, 3, 3))
    cov[:, 0, 0] = radius ** 2
    cov[:, 1, 1] = radius ** 2
    cov[:, 2, 2] = radius ** 2
    return cov


# ─── GLOW SPLAT ─────────────────────────────────────────────────────────
# Same as point but uses additive blending.
# NOTE: Requires renderer change (alpha composite -> additive).
# For now, uses high-alpha point with emissive color.

def emit_glow(positions, radius=5.0):
    """Glow splat: bright point with high alpha."""
    return emit_point(positions, radius)


# ─── SHELL SPLAT ─────────────────────────────────────────────────────────
# Hollow ellipsoid: thin shell at a distance from center.
# Use: thin walls, membranes

def emit_shell(positions, normal, thickness=0.2, spread=1.0):
    """Shell splat: surface disk but even thinner along normal."""
    return emit_surface(normal, tangent_scale=spread, normal_scale=thickness)


# ─── CATALOG ─────────────────────────────────────────────────────────────

SPLAT_TYPES = {
    'surface': {
        'name': 'Surface',
        'description': 'Flat disk aligned to surface normal',
        'build_cov': emit_surface,
        'default_params': {'tangent_scale': 1.15, 'normal_scale': 0.35},
        'blend': 'alpha',
        'uses': 'terrain, walls, skin, shelter, ground',
    },
    'fiber': {
        'name': 'Fiber',
        'description': 'Needle elongated along fiber direction',
        'build_cov': emit_fiber,
        'default_params': {'tangent_scale': 1.15, 'normal_scale': 0.35, 'elongation': 3.0},
        'blend': 'alpha',
        'uses': 'muscle, grass, hair, cables, cloth',
    },
    'point': {
        'name': 'Point',
        'description': 'Isotropic sphere, no orientation',
        'build_cov': emit_point,
        'default_params': {'radius': 1.0},
        'blend': 'alpha',
        'uses': 'dust, particles, debris, distant LOD',
    },
    'beam': {
        'name': 'Beam',
        'description': 'Long and thin along one axis',
        'build_cov': emit_beam,
        'default_params': {'length': 10.0, 'thickness': 0.5},
        'blend': 'alpha',
        'uses': 'beacon signal, light rays, lasers, trails',
    },
    'cloud': {
        'name': 'Cloud',
        'description': 'Large soft sphere, low alpha',
        'build_cov': emit_cloud,
        'default_params': {'radius': 100.0, 'alpha': 0.1},
        'blend': 'alpha',
        'uses': 'atmosphere, fog, gas clouds, nebula',
    },
    'glow': {
        'name': 'Glow',
        'description': 'Additive blend bright point',
        'build_cov': emit_glow,
        'default_params': {'radius': 5.0},
        'blend': 'additive',  # renderer needs additive path
        'uses': 'sun, lights, beacon, emissive VFX',
    },
    'shell': {
        'name': 'Shell',
        'description': 'Very thin surface disk',
        'build_cov': emit_shell,
        'default_params': {'thickness': 0.2, 'spread': 1.0},
        'blend': 'alpha',
        'uses': 'thin walls, membranes, skin overlay',
    },
}


if __name__ == '__main__':
    print('=== SPLAT TYPE CATALOG ===')
    print()
    for name, info in SPLAT_TYPES.items():
        print(f'  {name}')
        print(f'    {info["description"]}')
        print(f'    blend: {info["blend"]}')
        print(f'    uses:  {info["uses"]}')
        print(f'    params: {info["default_params"]}')
        print()
    
    # Smoke test: build each type
    rng = np.random.RandomState(42)
    n_test = 100
    normals = np.zeros((n_test, 3))
    normals[:, 2] = 1.0
    positions = rng.randn(n_test, 3) * 10
    
    print('=== SMOKE TEST ===')
    for name, info in SPLAT_TYPES.items():
        try:
            if name in ('point', 'cloud', 'glow'):
                cov = info['build_cov'](positions, **info['default_params'])
            elif name in ('beam',):
                dirs = np.zeros((n_test, 3))
                dirs[:, 0] = 1.0
                cov = info['build_cov'](dirs, **info['default_params'])
            elif name in ('shell',):
                cov = info['build_cov'](positions, normals, **info['default_params'])
            else:
                cov = info['build_cov'](normals, **info['default_params'])
            print(f'  {name}: cov shape {cov.shape}, trace={np.trace(cov, axis1=1, axis2=2).mean():.2f}')
        except Exception as e:
            print(f'  {name}: FAILED - {e}')
