"""hierarchical_verifier.py — Prove each level of SDF hierarchy.

LEVEL 1: Voxel (trilinear sampling accuracy)
LEVEL 2: Surface Voxels (collision candidates)
LEVEL 3: Contact Pair (two bodies interacting)
LEVEL 4: SDFBody (single membrane with dynamics)
LEVEL 5: SDFWorld (multiple bodies)
LEVEL 6: Rendered World (physics + splats)

TARGET: RTX 4090, 128GB RAM, 13900 CPU
PERFORMANCE FIRST: GPU parallelism, minimal host-GPU sync, batch operations
"""
from __future__ import annotations

import time
import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass, field

# Import core SDF components
import sys
sys.path.insert(0, 'ChimeraEngine')
from core.sdf_grid import SDFGrid, VoxelKey, sphere_sdf, box_sdf, capsule_sdf
from core.sdf_gpu import GpuSdfSolver, GpuVolume

@dataclass
class Verdict:
    """Record a falsifier test result."""
    level: int
    claim: str
    passed: bool
    metric: float = 0.0
    unit: str = ''
    detail: str = ''
    
    def __str__(self):
        status = 'PASS' if self.passed else 'FAIL'
        return f'[{status}] L{self.level}: {self.claim} ({self.metric:.6g}{self.unit}) {self.detail}'


class HierarchicalVerifier:
    """Prove each level of the SDF hierarchy with falsifier tests."""
    
    def __init__(self):
        self.verdicts: List[Verdict] = []
        self.timings: dict = {}
        
    def record(self, level: int, claim: str, passed: bool, metric: float = 0.0, 
               unit: str = '', detail: str = '') -> Verdict:
        v = Verdict(level, claim, passed, metric, unit, detail)
        self.verdicts.append(v)
        print(str(v))
        return v
    
    def time(self, name: str):
        """Context manager for timing."""
        import contextlib
        @contextlib.contextmanager
        def _timer():
            start = time.perf_counter()
            yield
            self.timings[name] = time.perf_counter() - start
        return _timer()
    
    # =====================================================
    # LEVEL 1: VOXEL (Trilinear Sampling Accuracy)
    # =====================================================
    def test_level_1_voxel(self) -> List[Verdict]:
        """Prove trilinear sampling is accurate within tolerance."""
        print('\n=== LEVEL 1: VOXEL ACCURACY ===')
        
        voxel_size = 0.1
        grid = SDFGrid(voxel_size=voxel_size)
        
        extent = 10
        for x in range(-extent, extent+1):
            for y in range(-extent, extent+1):
                for z in range(-extent, extent+1):
                    pos = np.array([x*voxel_size, y*voxel_size, z*voxel_size])
                    sdf = sphere_sdf(pos, np.array([0.0, 0.0, 0.0]), 5.0)
                    key = VoxelKey(x, y, z)
                    grid.set(key, sdf)
        
        tests = [
            (0.0, 0.0, 0.0, -5.0),
            (3.0, 4.0, 0.0, -5.0),
            (5.0, 0.0, 0.0, -5.0),
            (10.0, 0.0, 0.0, 5.0),
        ]
        
        passed = True
        for px, py, pz, expected in tests:
            pos = np.array([px, py, pz])
            sdf_val, _ = grid.sample_trilinear(pos)
            error = abs(sdf_val - expected)
            ok = error < 0.1 * voxel_size
            passed = passed and ok
            self.record(1, f'Sample at ({px},{py},{pz}) = {sdf_val:.4f} (expected {expected:.4f})', 
                       ok, error, '', f'error < tol={0.1*voxel_size}')
        
        return [Verdict(1, 'Trilinear sampling accurate', passed)]
    
    # =====================================================
    # LEVEL 2: SURFACE VOXELES (Collision Candidates)
    # =====================================================
    def test_level_2_surface(self) -> List[Verdict]:
        """Prove surface voxel extraction identifies contact candidates."""
        print('\n=== LEVEL 2: SURFACE VOXELS ===')
        
        voxel_size = 0.1
        grid = SDFGrid(voxel_size=voxel_size)
        
        extent = 10
        for x in range(-extent, extent+1):
            for y in range(-extent, extent+1):
                for z in range(-extent, extent+1):
                    pos = np.array([x*voxel_size, y*voxel_size, z*voxel_size])
                    sdf = sphere_sdf(pos, np.array([0.0, 0.0, 0.0]), 5.0)
                    grid.set(VoxelKey(x, y, z), sdf)
        
        surface = grid.surface_voxels()
        
        ok = len(surface) > 1000
        self.record(2, f'Surface voxels extracted: {len(surface)}', ok, len(surface), 'voxels')
        
        max_sdf = max(abs(s) for _, s, _ in surface) if surface else 0
        ok = ok and max_sdf < grid.band
        self.record(2, f'Max |SDF| on surface: {max_sdf:.4f}', ok and max_sdf < grid.band, 
                   max_sdf, '', 'should be < band')
        
        return [Verdict(2, 'Surface extraction correct', ok)]
    
    # =====================================================
    # LEVEL 3: CONTACT PAIR (Two Bodies Interacting)
    # =====================================================
    def test_level_3_contact(self) -> List[Verdict]:
        """Prove GPU contact solver matches CPU oracle."""
        print('\n=== LEVEL 3: CONTACT PAIR ===')
        
        try:
            import cupy as cp
        except ImportError:
            return [Verdict(3, 'GPU contact skipped (no cupy)', False)]
        
        voxel_size = 0.05
        grid1 = SDFGrid(voxel_size=voxel_size)
        grid2 = SDFGrid(voxel_size=voxel_size)
        
        extent = 20
        for x in range(-extent, extent+1):
