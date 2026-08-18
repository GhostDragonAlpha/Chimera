"""demo_field_physics.py — visualize coupled field elements as splat images.

Demonstrates the electron/black-hole metaphor:
    - Orbital ring: like-charges repel, creating tension-driven anisotropy
    - Density clump: tests schwarzschild threshold (black hole formation)
    - Binary system: gravitational coupling with lensing centers

Run standalone: python ChimeraEngine/demo_field_physics.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE / "core"))

from core.field_physics import (FieldSystem, FieldElement, 
                                  make_orbital_ring, make_density_clump, 
                                  make_binary_system)


# ── SIMPLE SPLAT RASTERIZER (CPU-only, for visualization) ─────────────────────────────
# A minimal EWA-style rasterizer to turn splat buffers into images.
# This is NOT the production renderer; it's a witness tool.

def _project_splat(pos, scale, rot, cam_pos, cam_target, cam_up, w, h, fov):
    """Project one splat to 2D screen space. Returns (cx, cy, major, minor, alpha)."""
    # Simple orthographic-ish projection for demo
    to_obj = cam_target - cam_pos
    to_obj = to_obj / (np.linalg.norm(to_obj) + 1e-8)
    
    right = np.cross(cam_up, to_obj)
    right = right / (np.linalg.norm(right) + 1e-8)
    up = np.cross(to_obj, right)
    
    # Position in camera space
    offset = pos - cam_pos
    x = float(np.dot(offset, right))
    y = float(np.dot(offset, up))
    z = float(np.dot(offset, to_obj))
    
    if z < 0.1:
        return None
    
    focal = h / (2 * np.tan(fov / 2))
    cx = w / 2 + x * focal / z
    cy = h / 2 - y * focal / z
    
    # Scale projection (simplified)
    scale_z = scale[2] * focal / z
    scale_x = scale[0] * focal / z
    scale_y = scale[1] * focal / z
    
    return (cx, cy, max(scale_x, 0.1), max(scale_y, 0.1), z)


def render_splats_to_image(buffer: np.ndarray, 
                           w: int = 960, h: int = 540,
                           fov: float = 1.047,
                           bg_color: tuple = (0.015, 0.015, 0.04)) -> np.ndarray:
    """Render a splat buffer to an RGB image using simple depth-sorted compositing."""
    img = np.ones((h, w, 3), dtype=np.float32) * np.array(bg_color, dtype=np.float32)
    
    n = buffer.shape[0]
    if n == 0:
        return (img * 255).astype(np.uint8)
    
    # Collect all splat projections
    splats = []
    for i in range(n):
        pos = buffer[i, 0:3]
        scale = buffer[i, 6:9]
        color = buffer[i, 13:16]
        alpha = buffer[i, 16]
        
        # Skip horizon-absorbed elements (they don't render)
        if buffer[i, 19] > 0.5:
            continue
        
        proj = _project_splat(pos, scale, None, 
                              np.array([0, 0, -3]), np.array([0, 0, 0]), 
                              np.array([0, 1, 0]), w, h, fov)
        if proj:
            cx, cy, sx, sy, z = proj
            splats.append((cx, cy, sx, sy, color, alpha, z))
    
    # Sort by depth (far to near for front-to-back compositing)
    splats.sort(key=lambda s: -s[6])
    
    # Composite
    for cx, cy, sx, sy, color, alpha, z in splats:
        if alpha < 0.01:
            continue
        
        # Draw ellipse approximation (circle for simplicity)
        r = max(sx, sy)
        x0, y0 = int(cx - r), int(cy - r)
        x1, y1 = int(cx + r), int(cy + r)
        
        for py in range(max(0, y0), min(h, y1)):
            for px in range(max(0, x0), min(w, x1)):
                dx = (px - cx) / sx
                dy = (py - cy) / sy
                dist2 = dx*dx + dy*dy
                
                if dist2 > 1.0:
                    continue
                
                # Gaussian falloff
                wgt = np.exp(-0.5 * dist2 * 3.0)
                c = alpha * wgt
                
                img[py, px] = img[py, px] * (1 - c) + color * c
    
    return (np.clip(img, 0, 1) * 255).astype(np.uint8)


# ── DEMO SCENES WITH VISUALIZATION ─────────────────────────────────────────────────────

def demo_orbital_ring():
    """Like-charges repel, creating visible tension anisotropy."""
    print("\n[ORBITAL RING] Like-charges repel -> tension-driven stretching")
    
    system = FieldSystem(make_orbital_ring(16, radius=1.0, charge_sign=1.0))
    
    # Run for several steps to let tension build
    for _ in range(30):
        buf = system.step(dt=1/60)
    
    img = render_splats_to_image(buf)
    out_path = Path(__file__).resolve().parent / "demo_output" / "field_physics" / "orbital_ring.png"
    Image.fromarray(img).save(out_path)
    
    stats = system.stats()
    print(f"   {stats['n_elements']} elements, mean density: {stats['mean_density']:.1f}")
    print(f"   -> saved to {out_path}")
    return buf


def demo_density_clump():
    """Test schwarzschild threshold — black hole formation."""
    print("\n[DENSITY CLUMP] Testing schwarzschild threshold")
    
    # Start with moderate density, watch what happens
    system = FieldSystem(make_density_clump(20, mass_per=10.0))
    
    for step in range(20):
        buf = system.step(dt=1/60)
        stats = system.stats()
        if stats['horizon_absorbed'] > 0:
            print(f"   Step {step}: BLACK HOLE FORMED - {stats['horizon_absorbed']} elements absorbed")
            break
    
    img = render_splats_to_image(buf)
    out_path = Path(__file__).resolve().parent / "demo_output" / "field_physics" / "density_clump.png"
    Image.fromarray(img).save(out_path)
    
    stats = system.stats()
    print(f"   {stats['n_elements']} elements, max density: {stats['max_density']:.1f}")
    print(f"   -> saved to {out_path}")
    return buf


def demo_binary_system():
    """Gravitational coupling with lensing center detection."""
    print("\n[BINARY SYSTEM] Gravitational binding + lensing centers")
    
    system = FieldSystem(make_binary_system(mass1=5.0, mass2=5.0, separation=3.0))
    
    for _ in range(50):
        buf = system.step(dt=1/60)
    
    img = render_splats_to_image(buf)
    out_path = Path(__file__).resolve().parent / "demo_output" / "field_physics" / "binary_system.png"
    Image.fromarray(img).save(out_path)
    
    stats = system.stats()
    centers = system.get_lensing_centers()
    print(f"   {stats['n_elements']} elements, lensing centers: {len(centers)}")
    print(f"   -> saved to {out_path}")
    return buf


def demo_interference():
    """Show wave-like interference from overlapping orbitals."""
    print("\n[INTERFERENCE] Overlapping orbitals -> constructive/destructive patterns")
    
    # Two close elements with opposite phase (one bright, one dim baseline)
    elem1 = FieldElement(
        position=np.array([-0.3, 0.0, 0.0]),
        velocity=np.array([0.0, 0.05, 0.0]),
        mass=1.0,
        charge=0.0,
        base_color=np.array([1.0, 0.2, 0.2]),
        base_scale=np.array([0.15, 0.15, 0.15]),
    )
    elem2 = FieldElement(
        position=np.array([0.3, 0.0, 0.0]),
        velocity=np.array([0.0, -0.05, 0.0]),
        mass=1.0,
        charge=0.0,
        base_color=np.array([0.2, 0.2, 1.0]),
        base_scale=np.array([0.15, 0.15, 0.15]),
    )
    
    system = FieldSystem([elem1, elem2])
    
    # Let them overlap and see interference
    for _ in range(60):
        buf = system.step(dt=1/60)
    
    img = render_splats_to_image(buf)
    out_path = Path(__file__).resolve().parent / "demo_output" / "field_physics" / "interference.png"
    Image.fromarray(img).save(out_path)
    
    stats = system.stats()
    print(f"   {stats['n_elements']} elements, densities: {[e.density for e in system.elements]}")
    print(f"   -> saved to {out_path}")
    return buf


if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    out_dir = Path(__file__).resolve().parent / "demo_output" / "field_physics"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("Field Physics Demo — electron/black-hole coupling")
    print("=" * 60)
    
    demo_orbital_ring()
    demo_density_clump()
    demo_binary_system()
    demo_interference()
    
    print("\n" + "=" * 60)
    print("All demos complete. Images saved to demo_output/field_physics/")
    print("=" * 60)
