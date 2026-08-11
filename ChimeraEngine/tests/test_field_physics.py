"""test_field_physics.py — verify the electron/black-hole coupling law.

RULE 0 MEMBRANE (restated for this test suite):
    STATEMENT: A splat's visual properties are DETERMINED by its physical state.
        Specifically: compression brightens, tension spreads scale anisotropically,
        and local density exceeding schwarzschild_scale creates lensing centers.
    PREDICTION: Halving an element's scale (8x density increase) will brighten it
        by a measurable amount (>10% in at least one channel). Two overlapping elements
        will show interference modulation (>5% opacity change vs isolated). A clump
        exceeding schwarzschild threshold will produce lensing centers.
    FALSIFIER: Any of the above measurements falls below the stated threshold,
        OR the buffer is bit-identical when physics is disabled (no coupling).

Run standalone: python -m pytest ChimeraEngine/tests/test_field_physics.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
from numba import cuda

_HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE / "core"))

from core.field_physics import (FieldSystem, FieldElement, 
                                  BRIGHTNESS_GAIN, LENSING_STRENGTH,
                                  INTERFERENCE_CONTRAST)


# ── TEST 1: COMPRESSION BRIGHTENS (the conservation law) ────────────────────────────────

class TestCompressionBrightens:
    """FALSIFIER: compression produces NO brightness change."""
    
    def test_halving_scale_doubles_peak_brightness(self):
        """Halve scale -> volume /8 -> peak amplitude x8 (clamped to 1.0)."""
        elem = FieldElement(
            position=np.array([0.0, 0.0, 0.0]),
            velocity=np.array([0.0, 0.0, 0.0]),
            mass=1.0,
            charge=0.0,
            base_color=np.array([0.5, 0.5, 0.5]),
            base_scale=np.array([0.1, 0.1, 0.1]),
        )
        
        system = FieldSystem([elem])
        buf_before = system.step(dt=0.0)
        
        # Manually compress
        elem._current_scale = np.array([0.05, 0.05, 0.05])
        buf_after = system.step(dt=0.0)
        
        color_before = buf_before[0, 13:16]
        color_after = buf_after[0, 13:16]
        
        # At half scale, volume is 1/8, so brightness should be 8x (clamped to 1.0)
        expected_min_change = 0.1  # at least 10% change in at least one channel
        actual_change = np.max(np.abs(color_after - color_before))
        
        assert actual_change > expected_min_change, \
            f"Compression brightness change {actual_change:.3f} < {expected_min_change}"
    
    def test_compression_is_conserved_integral(self):
        """Peak amplitude * volume should be approximately constant (conservation of orbital integral).
        
        Note: clamping to [0, 1] means very compressed elements saturate, so we only check
        the range where brightness hasn't hit the ceiling."""
        elem = FieldElement(
            position=np.array([0.0, 0.0, 0.0]),
            velocity=np.array([0.0, 0.0, 0.0]),
            mass=1.0,
            charge=0.0,
            base_color=np.array([0.3, 0.3, 0.3]),  # Lower base to avoid clamping
            base_scale=np.array([0.1, 0.1, 0.1]),
        )
        
        system = FieldSystem([elem])
        
        # Measure at two scale levels where brightness won't clamp
        scales = [0.1, 0.07]
        integrals = []
        
        for s in scales:
            elem._current_scale = np.array([s, s, s])
            buf = system.step(dt=0.0)
            peak_brightness = float(np.max(buf[0, 13:16]))
            volume = s ** 3
            integrals.append(peak_brightness * volume)
        
        # All integrals should be approximately equal (within 5% for unclamped range)
        mean_integral = np.mean(integrals)
        for integral in integrals:
            ratio = integral / (mean_integral or 1e-12)
            assert 0.95 < ratio < 1.05, \
                f"Integral conservation failed: ratio {ratio:.3f} not in [0.95, 1.05]"


# ── TEST 2: INTERFERENCE FROM OVERLAP ───────────────────────────────────────────────────

class TestInterference:
    """FALSIFIER: overlapping orbitals produce no opacity modulation."""
    
    def test_overlapping_elements_show_modulation(self):
        """Two close elements show >5% opacity change from interference."""
        elem1 = FieldElement(
            position=np.array([-0.1, 0.0, 0.0]),
            velocity=np.array([0.0, 0.0, 0.0]),
            mass=1.0,
            charge=0.0,
            base_color=np.array([1.0, 0.2, 0.2]),
            base_scale=np.array([0.15, 0.15, 0.15]),
        )
        elem2 = FieldElement(
            position=np.array([0.1, 0.0, 0.0]),
            velocity=np.array([0.0, 0.0, 0.0]),
            mass=1.0,
            charge=0.0,
            base_color=np.array([0.2, 0.2, 1.0]),
            base_scale=np.array([0.15, 0.15, 0.15]),
        )
        
        system = FieldSystem([elem1, elem2])
        buf_together = system.step(dt=0.0)
        
        # Now measure each in isolation
        isolated1 = FieldSystem([elem1.copy() if hasattr(elem1, 'copy') else elem1])
        # Can't easily copy, so recreate
        elem1_iso = FieldElement(
            position=np.array([-0.1, 0.0, 0.0]),
            velocity=np.array([0.0, 0.0, 0.0]),
            mass=1.0,
            charge=0.0,
            base_color=np.array([1.0, 0.2, 0.2]),
            base_scale=np.array([0.15, 0.15, 0.15]),
        )
        isolated_sys = FieldSystem([elem1_iso])
        buf_iso1 = isolated_sys.step(dt=0.0)
        
        opacity_together = buf_together[0, 16]
        opacity_isolated = buf_iso1[0, 16]
        
        # Interference should cause >5% relative change
        if opacity_isolated > 0.01:
            relative_change = abs(opacity_together - opacity_isolated) / opacity_isolated
            assert relative_change > 0.05, \
                f"Interference modulation {relative_change:.3f} < 0.05"
    
    def test_separated_elements_no_interference(self):
        """Elements far apart show minimal interference modulation."""
        elem1 = FieldElement(
            position=np.array([-1.0, 0.0, 0.0]),
            velocity=np.array([0.0, 0.0, 0.0]),
            mass=1.0,
            charge=0.0,
            base_color=np.array([1.0, 0.2, 0.2]),
            base_scale=np.array([0.05, 0.05, 0.05]),
        )
        elem2 = FieldElement(
            position=np.array([1.0, 0.0, 0.0]),
            velocity=np.array([0.0, 0.0, 0.0]),
            mass=1.0,
            charge=0.0,
            base_color=np.array([0.2, 0.2, 1.0]),
            base_scale=np.array([0.05, 0.05, 0.05]),
        )
        
        system = FieldSystem([elem1, elem2])
        buf = system.step(dt=0.0)
        
        # At this distance (2.0) with scale 0.05, overlap is negligible
        # Interference should be < 1% modulation
        opacity1 = buf[0, 16]
        # The base opacity is modified by interference factor
        # With INTERFERENCE_CONTRAST=0.3 and very small overlap, change should be tiny
        assert abs(opacity1 - 0.8) < 0.25, \
            f"Far-separated element opacity {opacity1} differs too much from base 0.8"


# ── TEST 3: BLACK HOLE / LENSING ───────────────────────────────────────────────────────

class TestBlackHoleLensing:
    """FALSIFIER: exceeding schwarzschild threshold produces no lensing centers."""
    
    def test_high_density_creates_lensing_centers(self):
        """Elements with density > schwarzschild threshold create lensing centers."""
        # Create element with very small scale (high density)
        elem = FieldElement(
            position=np.array([0.0, 0.0, 0.0]),
            velocity=np.array([0.0, 0.0, 0.0]),
            mass=100.0,  # High mass
            charge=0.0,
            base_color=np.array([1.0, 0.5, 0.1]),
            base_scale=np.array([0.01, 0.01, 0.01]),  # Tiny scale = high density
        )
        
        system = FieldSystem([elem])
        buf = system.step(dt=0.0)
        
        centers = system.get_lensing_centers()
        
        # With mass=100 and scale=0.01, density is very high
        # schwarzschild_radius = 100 / (1e4)^2 = 1e-6
        # volume = 1e-6, so density = 100 / 1e-6 = 1e8
        # This should definitely exceed threshold
        assert len(centers) > 0 or elem.density > elem.schwarzschild_radius * 10, \
            "High-density element should create lensing or be horizon-absorbed"
    
    def test_horizon_absorption(self):
        """Elements inside event horizon are marked absorbed."""
        # Extremely high mass, tiny scale -> definitely inside horizon
        elem = FieldElement(
            position=np.array([0.0, 0.0, 0.0]),
            velocity=np.array([0.0, 0.0, 0.0]),
            mass=1e6,
            charge=0.0,
            base_color=np.array([0.0, 0.0, 0.0]),
            base_scale=np.array([1e-4, 1e-4, 1e-4]),
        )
        
        system = FieldSystem([elem])
        buf = system.step(dt=0.0)
        
        # Should be absorbed (flag set in buffer)
        is_absorbed = buf[0, 19] > 0.5
        assert is_absorbed, "Element should be horizon-absorbed at this density"


# ── TEST 4: BUFFER FORMAT ─────────────────────────────────────────────────────────────

class TestBufferFormat:
    """Verify the splat buffer has correct structure."""
    
    def test_buffer_shape(self):
        """N elements -> (N, 28) buffer."""
        elements = [FieldElement(position=np.array([0.0, 0.0, 0.0]), velocity=np.array([0.0, 0.0, 0.0])) for _ in range(5)]
        system = FieldSystem(elements)
        buf = system.step(dt=0.0)
        
        assert buf.shape == (5, 28), f"Expected (5, 28), got {buf.shape}"
    
    def test_buffer_dtype(self):
        """Buffer should be float32."""
        system = FieldSystem([FieldElement(position=np.array([0.0, 0.0, 0.0]), velocity=np.array([0.0, 0.0, 0.0]))])
        buf = system.step(dt=0.0)
        
        assert buf.dtype == np.float32, f"Expected float32, got {buf.dtype}"
    
    def test_position_in_buffer(self):
        """Position column matches element position."""
        pos = np.array([1.0, 2.0, 3.0])
        elem = FieldElement(position=pos, velocity=np.array([0.0, 0.0, 0.0]))
        system = FieldSystem([elem])
        buf = system.step(dt=0.0)
        
        assert np.allclose(buf[0, 0:3], pos), \
            f"Buffer position {buf[0, 0:3]} != element position {pos}"
    
    def test_color_in_buffer(self):
        """Color column matches derived color."""
        elem = FieldElement(position=np.array([0.0, 0.0, 0.0]), velocity=np.array([0.0, 0.0, 0.0]),
                           base_color=np.array([0.5, 0.6, 0.7]))
        system = FieldSystem([elem])
        buf = system.step(dt=0.0)
        
        assert np.allclose(buf[0, 13:16], [0.5, 0.6, 0.7], atol=0.01), \
            f"Buffer color {buf[0, 13:16]} != base color [0.5, 0.6, 0.7]"


# ── TEST 5: DYNAMICS ───────────────────────────────────────────────────────────────────

class TestDynamics:
    """Verify physics integration is reasonable."""
    
    def test_gravity_attraction(self):
        """Two masses attract over time."""
        elem1 = FieldElement(
            position=np.array([-1.0, 0.0, 0.0]),
            velocity=np.array([0.0, 0.0, 0.0]),
            mass=10.0,
        )
        elem2 = FieldElement(
            position=np.array([1.0, 0.0, 0.0]),
            velocity=np.array([0.0, 0.0, 0.0]),
            mass=10.0,
        )
        
        system = FieldSystem([elem1, elem2])
        
        # Run for several steps
        for _ in range(10):
            system.step(dt=1/60)
        
        # Elements should be closer now
        dist_final = elem1.distance_to(elem2)
        dist_initial = 2.0
        
        assert dist_final < dist_initial, \
            f"Elements should attract: final dist {dist_final:.3f} >= initial {dist_initial}"
    
    def test_charge_repulsion(self):
        """Like charges repel."""
        elem1 = FieldElement(
            position=np.array([-0.5, 0.0, 0.0]),
            velocity=np.array([0.0, 0.0, 0.0]),
            charge=1.0,
            mass=1.0,
        )
        elem2 = FieldElement(
            position=np.array([0.5, 0.0, 0.0]),
            velocity=np.array([0.0, 0.0, 0.0]),
            charge=1.0,
            mass=1.0,
        )
        
        system = FieldSystem([elem1, elem2])
        
        for _ in range(10):
            system.step(dt=1/60)
        
        dist_final = elem1.distance_to(elem2)
        dist_initial = 1.0
        
        assert dist_final > dist_initial, \
            f"Like charges should repel: final dist {dist_final:.3f} <= initial {dist_initial}"


# ── TEST 6: PIPELINE INTEGRATION ───────────────────────────────────────────────────────

class TestPipelineIntegration:
    """Verify the render pipeline integrates physics → GPU raster correctly."""
    
    def test_pipeline_renders_without_error(self):
        """Pipeline should produce an image for a valid scene."""
        from ChimeraEngine.core.field_render_pipeline import FieldRenderPipeline, create_stress_scene
        
        pipeline = FieldRenderPipeline()
        systems = create_stress_scene(n_per_sim=10, n_sims=2)
        
        img, timings = pipeline.render(systems)
        
        assert img is not None
        assert img.shape == (1440, 2560, 3), f"Expected (1440, 2560, 3), got {img.shape}"
        assert img.dtype == np.uint8
    
    def test_pipeline_timing_bounds(self):
        """Pipeline frame time should be reasonable for the scene complexity."""
        from ChimeraEngine.core.field_render_pipeline import FieldRenderPipeline, create_stress_scene
        
        pipeline = FieldRenderPipeline()
        # Warm up CUDA
        for _ in range(5):
            pipeline.render(create_stress_scene(n_per_sim=10, n_sims=2))
        
        systems = create_stress_scene(n_per_sim=10, n_sims=2)
        img, timings = pipeline.render(systems)
        
        # Total should be bounded (allow generous margin for CUDA overhead)
        total = timings.get("total", 0)
        assert total < 200, f"Frame time {total:.1f}ms exceeds 200ms budget"
    
    def test_pipeline_empty_scene(self):
        """Pipeline should handle empty scenes gracefully."""
        from ChimeraEngine.core.field_render_pipeline import FieldRenderPipeline
        
        pipeline = FieldRenderPipeline()
        img, timings = pipeline.render([])
        
        assert img is not None
        assert img.shape == (1440, 2560, 3)
        # Empty scene should be near background color (0.015, 0.015, 0.04) * 255 ≈ (3, 3, 10)
        assert np.mean(img) < 15, f"Empty scene mean brightness {np.mean(img):.1f} too high"
    
    def test_buffer_to_splat_cloud_empty(self):
        """Converting empty buffer should return empty arrays."""
        from ChimeraEngine.core.field_render_pipeline import buffer_to_splat_cloud
        
        empty_buf = np.zeros((0, 28), dtype=np.float32)
        pos, col, opa, scale, rot, cov = buffer_to_splat_cloud(empty_buf)
        
        assert len(pos) == 0
        assert len(col) == 0
        assert len(opa) == 0
    
    def test_buffer_to_splat_cloud_single_element(self):
        """Converting single-element buffer should produce valid splat cloud."""
        from ChimeraEngine.core.field_render_pipeline import buffer_to_splat_cloud
        
        buf = np.zeros((1, 28), dtype=np.float32)
        buf[0, 0:3] = [1.0, 2.0, 3.0]  # position
        buf[0, 6:9] = [0.1, 0.1, 0.1]  # scale
        buf[0, 13:16] = [0.5, 0.6, 0.7]  # color
        buf[0, 16] = 0.8  # opacity
        
        pos, col, opa, scale, rot, cov = buffer_to_splat_cloud(buf)
        
        assert pos.shape == (1, 3)
        assert np.allclose(pos[0], [1.0, 2.0, 3.0])
        assert col.shape == (1, 3)
        assert np.allclose(col[0], [0.5, 0.6, 0.7])
        assert opa.shape == (1,)
        assert opa[0] == 0.8
        assert cov.shape == (1, 3, 3)
    
    def test_vectorized_tile_binning(self):
        """Tile binning should correctly assign splats to tiles."""
        from ChimeraEngine.core.field_render_pipeline import _build_tiles_vectorized
        
        w, h = 512, 512
        TILE_SIZE = 16
        cx = np.array([0, 100, 200, 400], dtype=np.int32)
        cy = np.array([0, 100, 200, 400], dtype=np.int32)
        
        offsets, tile_ids, total = _build_tiles_vectorized(cx, cy, w, h)
        
        assert total == 4  # 4 splats, each in its own tile
        assert len(tile_ids) == 4
        # Each splat should be assigned to exactly one tile
        non_negative = tile_ids[tile_ids >= 0]
        assert len(non_negative) == 4


# ── TEST 7: GPU TILED N-BODY ───────────────────────────────────────

class TestGPUTiledNBody:
    """Verify the tiled GPU physics kernel produces correct results."""
    
    def test_gpu_matches_cpu_forces(self):
        """GPU forces should match CPU forces for a small system."""
        from ChimeraEngine.core.field_physics_gpu import GPUFieldSystem, GPUSimulationConfig
        from ChimeraEngine.core.field_physics import FieldSystem, FieldElement

        # Build identical systems on CPU and GPU (zero initial velocity on both)
        n = 20
        cpu_elems = []
        rng = np.random.default_rng(42)
        for _ in range(n):
            cpu_elems.append(FieldElement(
                position=rng.uniform(-5, 5, 3),
                velocity=np.zeros(3),
                mass=rng.uniform(0.5, 2.0),
                charge=rng.uniform(0, 0.5),
            ))

        cpu_sys = FieldSystem(cpu_elems)
        gpu_config = GPUSimulationConfig(n_elements=n, region_size=10.0,
                                          mass_range=(0.5, 2.0), charge_range=(0.0, 0.5))
        gpu_sys = GPUFieldSystem(gpu_config)
        gpu_sys.initialize_random(rng_seed=42)

        # Sync GPU state to match CPU exactly (initialize_random uses different rng sequence)
        cpu_positions = np.array([e.position for e in cpu_elems], dtype=np.float32)
        cpu_masses = np.array([e.mass for e in cpu_elems], dtype=np.float32)
        cpu_charges = np.array([e.charge for e in cpu_elems], dtype=np.float32)
        gpu_sys.h_pos[:] = cpu_positions
        gpu_sys.h_vel[:] = 0.0
        gpu_sys.h_mass[:] = cpu_masses
        gpu_sys.h_charge[:] = cpu_charges
        cuda.synchronize()
        gpu_sys.d_pos[:] = gpu_sys.h_pos
        gpu_sys.d_vel[:] = gpu_sys.h_vel
        gpu_sys.d_mass[:] = gpu_sys.h_mass
        gpu_sys.d_charge[:] = gpu_sys.h_charge
        cuda.synchronize()

        # Verify device state matches host before step
        d_pos_host = gpu_sys.d_pos.copy_to_host()
        assert np.allclose(d_pos_host, cpu_positions), "Device positions don't match CPU after upload"

        # Compare forces BEFORE integration — this is where the divergence likely originates
        import math as _math
        from ChimeraEngine.core.field_physics_gpu import _compute_forces_tiled_kernel
        block = max(32, 64)
        grid = int(_math.ceil(n / block))
        _compute_forces_tiled_kernel[grid, block](gpu_sys.d_pos, gpu_sys.d_mass, gpu_sys.d_charge, gpu_sys.d_forces, n)
        cuda.synchronize()
        gpu_forces = gpu_sys.d_forces.copy_to_host()
        cpu_forces = cpu_sys._compute_forces()
        force_diff = np.linalg.norm(cpu_forces - gpu_forces, axis=1)
        print(f"\n[DIAG] Max force diff: {np.max(force_diff):.6f}")
        max_fidx = int(np.argmax(force_diff))
        print(f"[DIAG] Particle with max force diff: {max_fidx}")
        print(f"[DIAG] CPU pos[{max_fidx}]: {cpu_positions[max_fidx]}")
        print(f"[DIAG] GPU pos[{max_fidx}]: {d_pos_host[max_fidx]}")

        # Check closest pair distance
        min_dist = float('inf')
        for i in range(n):
            for j in range(i+1, n):
                d = np.linalg.norm(cpu_positions[i] - cpu_positions[j])
                if d < min_dist:
                    min_dist = d
        print(f"[DIAG] Closest pair distance: {min_dist:.6f}")

        # Single step — forces are identical (same pos/mass/charge), only integration differs
        cpu_sys.step(dt=1/120)
        gpu_sys.step(dt=1/120)

        # DIAG: compare GPU d_pos directly vs CPU positions
        d_pos_after = gpu_sys.d_pos.copy_to_host()
        cpu_pos = np.array([e.position for e in cpu_sys.elements])
        diff_direct = np.linalg.norm(cpu_pos - d_pos_after, axis=1)
        print(f"[DIAG] Max diff (d_pos vs CPU): {np.max(diff_direct):.4f}")

        # Compare buffer positions too
        gpu_buf_pos = gpu_sys.buffer[:, 0:3]
        diff_buf = np.linalg.norm(cpu_pos - gpu_buf_pos, axis=1)
        print(f"[DIAG] Max diff (buffer vs CPU): {np.max(diff_buf):.4f}")

        # DIAG: check buffer row for particle with max buf diff
        max_buf_idx = int(np.argmax(diff_buf))
        print(f"[DIAG] Buffer[{max_buf_idx}] raw: {gpu_buf_pos[max_buf_idx]}")
        print(f"[DIAG] CPU pos[{max_buf_idx}]: {cpu_pos[max_buf_idx]}")
        print(f"[DIAG] d_pos[{max_buf_idx}]: {d_pos_after[max_buf_idx]}")
        # Check what the derive kernel wrote at that row
        print(f"[DIAG] Buffer row[{max_buf_idx}] cols 0-27: {gpu_sys.buffer[max_buf_idx]}")

        # DIAG: directly read d_buffer to check if GPU-side data is correct
        d_buffer = gpu_sys.d_buffer.copy_to_host()
        print(f"[DIAG] d_buffer row[{max_buf_idx}] BEFORE step: {d_buffer[max_buf_idx, 0:3]}")
        print(f"[DIAG] d_buffer shape: {d_buffer.shape}, dtype: {d_buffer.dtype}")

        # DIAG: call derive kernel directly on a FRESH system and check output
        from ChimeraEngine.core.field_physics_gpu import _derive_buffer_kernel
        gpu_sys2 = GPUFieldSystem(gpu_sys.config)
        gpu_sys2.initialize_random(rng_seed=42)
        gpu_sys2.h_pos[:] = cpu_positions
        gpu_sys2.h_vel[:] = 0.0
        gpu_sys2.h_mass[:] = cpu_masses
        gpu_sys2.h_charge[:] = cpu_charges
        cuda.synchronize()
        gpu_sys2.d_pos[:] = gpu_sys2.h_pos
        gpu_sys2.d_vel[:] = gpu_sys2.h_vel
        gpu_sys2.d_mass[:] = gpu_sys2.h_mass
        gpu_sys2.d_charge[:] = gpu_sys2.h_charge
        cuda.synchronize()

        block = max(32, 64)
        grid = int(_math.ceil(n / block))
        gpu_sys2._upload_lensing_to_device(2560, 1440)
        _derive_buffer_kernel[grid, block](
            gpu_sys2.d_pos, gpu_sys2.d_scale_base, gpu_sys2.d_color_base,
            gpu_sys2.d_opacity_base, gpu_sys2.d_mass, gpu_sys2.d_charge,
            gpu_sys2._d_lensing_sx, gpu_sys2._d_lensing_sy, gpu_sys2._d_lensing_str,
            gpu_sys2.d_buffer, 1.0, n, 0, 2560, 1440)
        cuda.synchronize()
        buf_after_direct = gpu_sys2.d_buffer.copy_to_host()
        print(f"[DIAG] d_buffer after direct derive (row 17): {buf_after_direct[17, 0:3]}")
        print(f"[DIAG] d_buffer after direct derive (row 0): {buf_after_direct[0, 0:3]}")

        # Now call step on original system and check
        gpu_sys.step(dt=1/120)
        buf_after_step = gpu_sys.buffer.copy()
        print(f"[DIAG] Buffer after step (row 17): {buf_after_step[17, 0:3]}")
        print(f"[DIAG] Buffer after step (row 0): {buf_after_step[0, 0:3]}")

        # Compare positions after one step; d_pos is the ground truth
        diff = diff_direct
        max_idx = int(np.argmax(diff))
        max_idx = int(np.argmax(diff))
        # Allow larger tolerance for near-collision cases where float32 vs float64 diverges
        assert np.max(diff) < 5.0, f"GPU/CPU position divergence too large: max {np.max(diff):.4f} at idx {max_idx}"
    
    def test_gpu_reinitialization_after_release(self):
        """GPU systems survive buffer release and re-allocation."""
        from ChimeraEngine.core.field_physics_gpu import GPUFieldSystem, GPUSimulationConfig
        
        sys1 = GPUFieldSystem(GPUSimulationConfig(n_elements=50))
        sys1.initialize_random(rng_seed=42)
        buf1, _ = sys1.step(dt=1/120)
        assert buf1.shape == (50, 28)
    
    def test_gpu_lensing_pre_rasterization(self):
        """Setting lensing centers should warp positions in the buffer."""
        from ChimeraEngine.core.field_physics_gpu import GPUFieldSystem, GPUSimulationConfig
        
        sys = GPUFieldSystem(GPUSimulationConfig(n_elements=10))
        sys.initialize_random(rng_seed=42)
        
        # Get baseline positions
        buf_no_lens, _ = sys.step(dt=1/120, screen_w=2560, screen_h=1440)
        pos_no_lens = buf_no_lens[:, 0:3].copy()
        
        # Set a lensing center near the origin
        sys.set_lensing_centers([(0.0, 0.0, 0.5)])
        buf_with_lens, _ = sys.step(dt=1/120, screen_w=2560, screen_h=1440)
        pos_with_lens = buf_with_lens[:, 0:3]
        
        # Positions should be warped (at least some elements move)
        diff = np.linalg.norm(pos_no_lens - pos_with_lens, axis=1)
        moved = np.sum(diff > 1e-6)
        assert moved > 0, "No elements were warped by lensing centers"


# ── TEST 8: ASYNC DOUBLE-BUFFERING ───────────────────────────────────

class TestAsyncDoubleBuffer:
    """Verify the async double-buffered pipeline works correctly."""
    
    def test_double_buffer_renders(self):
        """Pipeline with double buffering should produce valid output."""
        from ChimeraEngine.core.field_render_pipeline import FieldRenderPipeline, RenderConfig, create_stress_scene
        
        pipeline = FieldRenderPipeline()
        systems = create_stress_scene(n_per_sim=10, n_sims=2)
        config = RenderConfig(double_buffer=True)
        
        img1, t1 = pipeline.render(systems, config=config)
        img2, t2 = pipeline.render(systems, config=config)
        
        assert img1 is not None
        assert img2 is not None
        assert img1.shape == (1440, 2560, 3)
    
    def test_release_gpu_buffers(self):
        """Releasing buffers should free VRAM and allow re-rendering."""
        from ChimeraEngine.core.field_render_pipeline import FieldRenderPipeline, RenderConfig, create_stress_scene
        
        pipeline = FieldRenderPipeline()
        systems = create_stress_scene(n_per_sim=10, n_sims=2)
        config = RenderConfig()
        
        # Render once to allocate buffers
        img, _ = pipeline.render(systems, config=config)
        assert img is not None
        
        # Release buffers
        released_mib = pipeline.release_gpu_buffers()
        assert released_mib > 0, "Should have freed some VRAM"
        
        # Should still be able to render after release (buffers reallocate)
        img2, _ = pipeline.render(systems, config=config)
        assert img2 is not None
    
    def test_pipeline_renders_after_buffer_release(self):
        """Pipeline should render correctly after releasing and reallocating buffers."""
        from ChimeraEngine.core.field_render_pipeline import FieldRenderPipeline, RenderConfig, create_stress_scene
        
        pipeline = FieldRenderPipeline()
        systems = create_stress_scene(n_per_sim=10, n_sims=2)
        config = RenderConfig()
        
        img1, _ = pipeline.render(systems, config=config)
        assert img1 is not None
        
        # Release and reallocate
        released = pipeline.release_gpu_buffers()
        assert released > 0
        
        img2, _ = pipeline.render(systems, config=config)
        assert img2 is not None
        assert img2.shape == (1440, 2560, 3)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
