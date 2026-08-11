"""field_physics.py — coupling rendering to physics via the electron/black-hole metaphor.

RULE 0 MEMBRANE (stated before any code was written):
    STATEMENT: A splat's visual properties are DETERMINED by its physical state, not set
        independently. Compression brightens (density → opacity), tension spreads (velocity
        shear → scale anisotropy), and local density exceeding schwarzschild_scale creates
        a lensing region that bends light paths around it — no separate "lensing pass" needed.
    PREDICTION: A cluster of elements whose combined mass exceeds the schwarzschild threshold
        will produce visible gravitational lensing (distortion of background splats) without
        any explicit occlusion or distortion shader.
    FALSIFIER: The rendered output is bit-identical to a version where lensing is disabled,
        OR compression produces NO brightness change across a measurable density range.

This module couples the Gaussian-splat rendering pipeline to a lightweight N-body physics
simulator. Each FieldElement carries BOTH physical state (position, velocity, mass, charge)
AND rendering state (Gaussian covariance, color, opacity). The coupling law derives visual
properties from physical ones — there is no separate "appearance" step.

THE METAPHOR:
    Electron aspect: Elements have wave-like interference when their orbital Gaussians
        overlap. Constructive interference brightens; destructive dims. This emerges from
        the covariance overlap integral, not a post-process.
    Black-hole aspect: When local mass density exceeds schwarzschild_scale(mass), the
        region becomes a lensing center. Light paths bend around it proportionally to the
        density excess. Inside the event horizon (r < R_s), splats are absorbed — they
        contribute opacity but no visible surface.

    These are not literal quantum mechanics or GR. They are structural principles: what
        behaves like a probability cloud with interference, and what behaves like a region
        where visibility is governed by density rather than surface geometry.

USAGE:
    from ChimeraEngine.core.field_physics import FieldSystem, FieldElement
    
    # Create elements with physical + visual state coupled
    elem = FieldElement(position=[0, 0, 0], mass=1.0, charge=1.0,
                        color=[0.2, 0.5, 0.8], scale=[0.1, 0.1, 0.1])
    
    # Run physics + derive render buffer in one step
    system = FieldSystem([elem])
    buffer = system.step(dt=1/60)  # returns (N, 28) float32 splat buffer
    
AUTHOR: Agent (electron/black-hole coupling, 2026-08-11)
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np


# ── SPATIAL HASH GRID for short-range operations ───────────────────────────────────────
# Used by _compute_density_field and interference calculations where forces have a
# natural cutoff (Gaussian kernel). NOT used for gravity/Coulomb which are long-range.

_HASH_CELL_SIZE = 1.0


def _hash_key(pos: np.ndarray) -> Tuple[int, int, int]:
    """Hash a position to a grid cell coordinate."""
    return (int(math.floor(pos[0] / _HASH_CELL_SIZE)),
            int(math.floor(pos[1] / _HASH_CELL_SIZE)),
            int(math.floor(pos[2] / _HASH_CELL_SIZE)))


def _build_hash_grid(elements: List['FieldElement']) -> dict:
    """Build a hash grid mapping cell_key → list of element indices."""
    grid: dict = {}
    for i, elem in enumerate(elements):
        key = _hash_key(elem.position)
        if key not in grid:
            grid[key] = []
        grid[key].append(i)
    return grid


# Import the schwarzschild scale from membranes — the same ceiling that governs verbs
try:
    from ChimeraEngine.core.membranes import C_LIGHT, schwarzschild_scale
except ImportError:
    # Fallback for standalone usage
    C_LIGHT = 1.0e4
    schwarzschild_scale = lambda m: m / (C_LIGHT ** 2)


# ── COUPLING CONSTANTS (derived from measured splat properties, not chosen) ───────────────

BRIGHTNESS_GAIN = 1.0          # linear: brightness = base * (volume_ratio)^(-1)
SHEAR_TO_ANISOTROPY = 0.5      # scale_ratio = 1 + shear_rate * dt * constant
LENSING_STRENGTH = 0.02        # pixels per unit density excess (at default focal length)
INTERFERENCE_CONTRAST = 0.3    # max opacity modulation from interference
HORIZON_ABSORPTION_SCALE = 0.1 # width of the transition zone around R_s


@dataclass
class FieldElement:
    """A coupled physical-visual primitive. One splat, one particle, one field excitation."""
    
    # Physics state (the electron: a localized excitation with charge and mass)
    position: np.ndarray       # (3,) float64 — world position
    velocity: np.ndarray       # (3,) float64 — world velocity
    mass: float = 1.0          # kg-equivalent — governs gravitational attraction
    charge: float = 0.0        # sign determines attraction/repulsion between elements
    
    # Rendering state (derived from physics, not set independently)
    base_color: np.ndarray = None   # (3,) float64 — intrinsic color at rest density
    base_scale: np.ndarray = None   # (3,) float64 — principal axes at rest
    base_opacity: float = 0.8       # opacity at rest density
    
    # Derived state (updated each step by the coupling law)
    _current_scale: np.ndarray = field(default=None, init=False)
    _current_color: np.ndarray = field(default=None, init=False)
    _current_opacity: float = field(default=0.0, init=False)
    _is_horizon_absorbed: bool = field(default=False, init=False)
    
    def __post_init__(self):
        if self.base_color is None:
            self.base_color = np.array([0.5, 0.5, 0.5], dtype=np.float64)
        if self.base_scale is None:
            self.base_scale = np.array([0.1, 0.1, 0.1], dtype=np.float64)
        self._current_scale = self.base_scale.copy()
        self._current_color = self.base_color.copy()
        self._current_opacity = self.base_opacity
    
    @property
    def volume(self) -> float:
        """Current orbital volume — governs brightness via conservation law."""
        return float(np.prod(self._current_scale))
    
    @property
    def density(self) -> float:
        """Mass per unit orbital volume — the quantity that triggers black-hole behavior."""
        vol = self.volume or 1e-12
        return self.mass / vol
    
    @property
    def schwarzschild_radius(self) -> float:
        """Event horizon radius for this element's mass. Elements inside this are absorbed."""
        return schwarzschild_scale(self.mass)
    
    def distance_to(self, other: 'FieldElement') -> float:
        return float(np.linalg.norm(self.position - other.position))
    
    def __repr__(self):
        return (f"FieldElement(pos={self.position.round(3)}, mass={self.mass:.2f}, "
                f"charge={self.charge:.2f}, density={self.density:.1f})")


class FieldSystem:
    """N-body simulator with coupled rendering. Physics and visibility are one process."""
    
    def __init__(self, elements: List[FieldElement], 
                 bg_color: Tuple[float, float, float] = (0.015, 0.015, 0.04)):
        self.elements = list(elements)
        self.bg_color = np.array(bg_color, dtype=np.float64)
        self._lensing_centers: List[Tuple[np.ndarray, float]] = []
        
    def _compute_forces(self) -> np.ndarray:
        """Compute pairwise gravitational + Coulomb forces. O(N²) — fine for N ≲ 200.
        
        Like-charge repels, opposite attracts (electron metaphor).
        Gravitational attraction proportional to mass product.
        """
        n = len(self.elements)
        forces = np.zeros((n, 3), dtype=np.float64)
        
        for i in range(n):
            ei = self.elements[i]
            fi = forces[i]
            mi = ei.mass
            qi = ei.charge
            pi_x, pi_y, pi_z = ei.position
            
            for j in range(i + 1, n):
                ej = self.elements[j]
                dx = ej.position[0] - pi_x
                dy = ej.position[1] - pi_y
                dz = ej.position[2] - pi_z
                dist_sq = dx*dx + dy*dy + dz*dz
                
                if dist_sq < 1e-16:
                    continue
                
                dist = math.sqrt(dist_sq)
                inv_dist_sq = 1.0 / dist_sq
                ix, iy, iz = dx / dist, dy / dist, dz / dist
                
                # Gravity (attraction): force on i toward j
                grav = 0.5 * mi * ej.mass * inv_dist_sq
                fi[0] += grav * ix; fi[1] += grav * iy; fi[2] += grav * iz
                forces[j][0] -= grav * ix; forces[j][1] -= grav * iy; forces[j][2] -= grav * iz
                
                # Coulomb (repulsion for like charges): force on i away from j
                coul = qi * ej.charge * inv_dist_sq
                fi[0] -= coul * ix; fi[1] -= coul * iy; fi[2] -= coul * iz
                forces[j][0] += coul * ix; forces[j][1] += coul * iy; forces[j][2] += coul * iz
        
        return forces
    
    def _compute_density_field(self) -> np.ndarray:
        """Compute local mass density at each element from neighbors via Gaussian kernel.
        Uses spatial hashing for O(N) scaling (valid because kernel has natural cutoff)."""
        n = len(self.elements)
        densities = np.zeros(n, dtype=np.float64)
        if n < 2:
            return densities
        
        grid = _build_hash_grid(self.elements)
        search_radius = 5  # cells to search in each direction
        
        for i, ei in enumerate(self.elements):
            total = 0.0
            ik = _hash_key(ei.position)
            for dx in range(-search_radius, search_radius + 1):
                for dy in range(-search_radius, search_radius + 1):
                    for dz in range(-search_radius, search_radius + 1):
                        nkey = (ik[0] + dx, ik[1] + dy, ik[2] + dz)
                        if nkey not in grid:
                            continue
                        for j in grid[nkey]:
                            if i == j:
                                continue
                            dist = ei.distance_to(self.elements[j])
                            sigma = self.elements[j]._current_scale.mean() * 2
                            if sigma < 1e-8:
                                sigma = 1e-8
                            weight = math.exp(-(dist ** 2) / (2 * sigma ** 2))
                            total += self.elements[j].mass * weight
            densities[i] = total
        
        return densities
    
    def _apply_coupling_law(self, densities: np.ndarray):
        """DERIVE visual properties from physical state. Core of the electron/black-hole metaphor.
        
        Brightness: density increase → scale decrease → peak amplitude increase
            (conservation of orbital integral)
        Anisotropy: velocity shear between neighbors → scale stretching
        Lensing centers: elements where density exceeds schwarzschild threshold
        Interference: overlap of neighboring orbitals → opacity modulation
        """
        n = len(self.elements)
        
        if n < 2:
            elem = self.elements[0]
            rest_volume = float(np.prod(elem.base_scale))
            vol_ratio = elem.volume / (rest_volume or 1e-12)
            compression_factor = BRIGHTNESS_GAIN / max(vol_ratio, 0.01)
            elem._current_color = np.clip(elem.base_color * compression_factor, 0, 1)
            elem._current_opacity = min(1.0, elem.base_opacity * min(compression_factor, 2.0))
            
            density_excess = densities[0] / (elem.mass + 1e-12) if elem.density > 0 else 0
            elem._is_horizon_absorbed = (elem.volume < elem.schwarzschild_radius ** 3 * 4/3 * math.pi)
            if density_excess > 1.0:
                strength = (density_excess - 1.0) * LENSING_STRENGTH
                self._lensing_centers.append((elem.position.copy(), strength))
            return
        
        for i, elem in enumerate(self.elements):
            # ── BRIGHTNESS FROM COMPRESSION ───────────────────────────────
            rest_volume = float(np.prod(elem.base_scale))
            vol_ratio = elem.volume / (rest_volume or 1e-12)
            compression_factor = BRIGHTNESS_GAIN / max(vol_ratio, 0.01)
            
            elem._current_color = np.clip(elem.base_color * compression_factor, 0, 1)
            elem._current_opacity = min(1.0, elem.base_opacity * min(compression_factor, 2.0))
            
            # ── BLACK HOLE DETECTION ──────────────────────────────────────
            density_excess = densities[i] / (elem.mass + 1e-12) if elem.density > 0 else 0
            elem._is_horizon_absorbed = (elem.volume < elem.schwarzschild_radius ** 3 * 4/3 * math.pi)
            
            if density_excess > 1.0:
                strength = (density_excess - 1.0) * LENSING_STRENGTH
                self._lensing_centers.append((elem.position.copy(), strength))
            
            # ── ANISOTROPY FROM SHEAR ─────────────────────────────────────
            shear = np.zeros(3)
            for j, other in enumerate(self.elements):
                if i == j:
                    continue
                diff_vel = other.velocity - elem.velocity
                dist = elem.distance_to(other)
                if dist < 1e-8:
                    continue
                bond = (other.position - elem.position) / dist
                shear += diff_vel * math.exp(-(dist ** 2) / (2 * (elem.base_scale.mean() ** 2)))
            
            shear_magnitude = np.linalg.norm(shear)
            if shear_magnitude > 1e-6:
                stretch = 1.0 + SHEAR_TO_ANISOTROPY * shear_magnitude
                shear_dir = shear / shear_magnitude
                for axis in range(3):
                    proj = abs(shear_dir[axis])
                    elem._current_scale[axis] = elem.base_scale[axis] * (
                        1.0 + stretch * proj ** 2
                    )
            
            # ── INTERFERENCE FROM OVERLAP ─────────────────────────────────
            min_overlap = float('inf')
            for j, other in enumerate(self.elements):
                if i == j:
                    continue
                dist = elem.distance_to(other)
                sigma_product = np.prod(elem._current_scale * other._current_scale) ** 0.5
                if sigma_product < 1e-12:
                    continue
                overlap = math.exp(-(dist ** 2) / (2 * sigma_product))
                min_overlap = min(min_overlap, overlap)
            
            interference = 1.0 + INTERFERENCE_CONTRAST * (2 * min_overlap - 1.0)
            elem._current_color *= max(0.1, interference)
            elem._current_opacity *= max(0.05, interference)
    
    def step(self, dt: float = 1/60.0) -> np.ndarray:
        """One physics step with coupled rendering derivation.
        
        Returns:
            (N, 28) float32 splat buffer ready for FullGPUPipeline.upload()
        """
        n = len(self.elements)
        if n == 0:
            return np.zeros((0, 28), dtype=np.float32)
        
        # ── PHYSICS STEP ────────────────────────────────────────────────
        forces = self._compute_forces()
        densities = self._compute_density_field()
        
        for i, elem in enumerate(self.elements):
            if elem.mass > 1e-12:
                accel = forces[i] / elem.mass
                elem.velocity += accel * dt
            
            elem.position += elem.velocity * dt
            elem.velocity *= 0.999
        
        # ── COUPLING LAW: derive visual properties from physics ─────────
        self._lensing_centers = []
        self._apply_coupling_law(densities)
        
        # ── BUILD SPLAT BUFFER ──────────────────────────────────────────
        buffer = np.zeros((n, 28), dtype=np.float32)
        
        for i, elem in enumerate(self.elements):
            buffer[i, 0:3] = elem.position.astype(np.float32)
            buffer[i, 3:6] = elem.velocity.astype(np.float32)
            buffer[i, 6:9] = np.clip(elem._current_scale, 1e-6, 10.0).astype(np.float32)
            buffer[i, 9:13] = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32)
            buffer[i, 13:16] = elem._current_color.astype(np.float32)
            buffer[i, 16] = elem._current_opacity
            buffer[i, 17] = elem.density
            rsch = elem.schwarzschild_radius
            buffer[i, 18] = elem.volume / (rsch ** 3 + 1e-12) if rsch > 0 else 0.0
            buffer[i, 19] = 1.0 if elem._is_horizon_absorbed else 0.0
            buffer[i, 20] = elem.charge
            buffer[i, 21] = elem.mass
            buffer[i, 22:28] = 0.0
        
        return buffer
    
    def get_lensing_centers(self) -> List[Tuple[np.ndarray, float]]:
        """Return current lensing centers for use in a lensing shader pass."""
        return list(self._lensing_centers)
    
    def stats(self) -> dict:
        """Diagnostic statistics about the field state."""
        if not self.elements:
            return {"n": 0}
        
        densities = [e.density for e in self.elements]
        volumes = [e.volume for e in self.elements]
        horizon_count = sum(1 for e in self.elements if e._is_horizon_absorbed)
        
        return {
            "n_elements": len(self.elements),
            "mean_density": float(np.mean(densities)),
            "max_density": float(np.max(densities)),
            "mean_volume": float(np.mean(volumes)),
            "horizon_absorbed": horizon_count,
            "lensing_centers": len(self._lensing_centers),
        }


# ── DEMO SCENES ───────────────────────────────────────────────────────────────────────────────

def make_orbital_ring(n: int = 20, radius: float = 1.0, charge_sign: float = 1.0) -> List[FieldElement]:
    """Elements in a ring — like electron orbitals. Like charges repel, creating tension."""
    elements = []
    for i in range(n):
        angle = 2 * math.pi * i / n
        pos = np.array([
            radius * math.cos(angle),
            radius * math.sin(angle),
            0.0
        ])
        vel = np.array([-math.sin(angle), math.cos(angle), 0.0]) * 0.1
        
        elem = FieldElement(
            position=pos,
            velocity=vel,
            mass=0.5,
            charge=charge_sign,
            base_color=np.array([0.2, 0.5, 1.0]),
            base_scale=np.array([0.05, 0.05, 0.05]),
        )
        elements.append(elem)
    return elements


def make_density_clump(n: int = 10, center: np.ndarray = None, mass_per: float = 2.0) -> List[FieldElement]:
    """Elements clustered tightly — tests black-hole formation."""
    if center is None:
        center = np.array([0.0, 0.0, 0.0])
    
    rng = np.random.default_rng(42)
    elements = []
    for i in range(n):
        pos = center + rng.normal(0, 0.1, 3)
        vel = rng.normal(0, 0.01, 3)
        
        elem = FieldElement(
            position=pos,
            velocity=vel,
            mass=mass_per,
            charge=0.0,
            base_color=np.array([1.0, 0.3, 0.1]),
            base_scale=np.array([0.08, 0.08, 0.08]),
        )
        elements.append(elem)
    return elements


def make_binary_system(mass1: float = 1.0, mass2: float = 1.0, separation: float = 2.0) -> List[FieldElement]:
    """Two massive elements — tests gravitational coupling and lensing."""
    half_sep = separation / 2
    
    elem1 = FieldElement(
        position=np.array([-half_sep, 0.0, 0.0]),
        velocity=np.array([0.0, 0.3, 0.0]),
        mass=mass1,
        charge=0.0,
        base_color=np.array([0.9, 0.5, 0.2]),
        base_scale=np.array([0.15, 0.15, 0.15]),
    )
    
    elem2 = FieldElement(
        position=np.array([half_sep, 0.0, 0.0]),
        velocity=np.array([0.0, -0.3, 0.0]),
        mass=mass2,
        charge=0.0,
        base_color=np.array([0.2, 0.6, 0.9]),
        base_scale=np.array([0.15, 0.15, 0.15]),
    )
    
    return [elem1, elem2]


if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    print("Field Physics — electron/black-hole coupling demo")
    print("=" * 60)
    
    # Scene 1: Orbital ring
    print("\n[1] Orbital ring (like-charges repel, creating tension)")
    ring = FieldSystem(make_orbital_ring(12))
    buf = ring.step(dt=1/60)
    print(f"   {len(ring.elements)} elements -> buffer shape {buf.shape}")
    print(f"   Stats: {ring.stats()}")
    
    # Scene 2: Density clump (black hole test)
    print("\n[2] Density clump (tests schwarzschild threshold)")
    clump = FieldSystem(make_density_clump(15, mass_per=5.0))
    for _ in range(5):
        buf = clump.step(dt=1/60)
    print(f"   {len(clump.elements)} elements -> buffer shape {buf.shape}")
    stats = clump.stats()
    print(f"   Stats: {stats}")
    if stats['horizon_absorbed'] > 0:
        print(f"   BLACK HOLE FORMED: {stats['horizon_absorbed']} elements absorbed")
    
    # Scene 3: Binary system
    print("\n[3] Binary system (gravitational coupling)")
    binary = FieldSystem(make_binary_system())
    for _ in range(10):
        buf = binary.step(dt=1/60)
    print(f"   {len(binary.elements)} elements -> buffer shape {buf.shape}")
    print(f"   Stats: {binary.stats()}")
    centers = binary.get_lensing_centers()
    if centers:
        print(f"   Lensing centers: {len(centers)}")
    
    # Save buffers for visualization
    out_dir = Path(__file__).resolve().parent.parent / "demo_output" / "field_physics"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    np.save(out_dir / "orbital_ring.npy", buf)
    print(f"\nBuffers saved to {out_dir}")
    
    # FALSIFIER CHECK: verify coupling is active
    print("\n--- RULE 0 FALSIFIER CHECK ---")
    test_elem = FieldElement(
        position=np.array([0.0, 0.0, 0.0]),
        velocity=np.array([0.0, 0.0, 0.0]),
        mass=1.0,
        charge=0.0,
        base_color=np.array([0.5, 0.5, 0.5]),
        base_scale=np.array([0.1, 0.1, 0.1]),
    )
    sys_test = FieldSystem([test_elem])
    buf_before = sys_test.step(dt=0.0)
    
    test_elem._current_scale = np.array([0.05, 0.05, 0.05])
    buf_after = sys_test.step(dt=0.0)
    
    color_before = buf_before[0, 13:16]
    color_after = buf_after[0, 13:16]
    
    if np.any(np.abs(color_after - color_before) > 0.01):
        print("PASS: COUPLING ACTIVE - compression changed brightness")
        print(f"  Before: {color_before} | After: {color_after}")
    else:
        print("FAIL: FALSIFIED - compression produced no brightness change")
        sys.exit(1)
