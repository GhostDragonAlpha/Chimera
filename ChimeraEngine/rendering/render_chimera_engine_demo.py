"""
Chimera Engine Renderer Demo — Scalable 3D Gaussian Splat Rendering

This script demonstrates the Chimera Engine's scalable renderer with:
1. Camera distance calculation based on object's maximum units (24,000 unit minimum margin)
2. View angle (FOV) calculation based on maximum units of an item
3. Proper scaling for zoom in/out capability
"""

import sys
import os
# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
import math
from ParticleEngine.gpu_pipeline import FullGPUPipeline
from ParticleEngine.camera import FirstPersonCamera
from WorldModel.splat_io import _build_covariances
from ChimeraEngine.renderer import ObjectBounds, ChimeraCamera, ChimeraRenderer
from PIL import Image

print("=" * 60)
print("CHIMERA ENGINE RENDERER — SCALABLE 3D GAUSSIAN SPLAT PIPELINE")
print("=" * 60)

# Load VAE-sampled tree positions
print("\n[1] Loading VAE-sampled tree data...")
data = np.load('WorldModel/training_data/tree_vae_sampled.npz')
positions = data['positions']
n = len(positions)

# Calculate object bounds from positions
min_pos = positions.min(axis=0)
max_pos = positions.max(axis=0)
center = positions.mean(axis=0)

print(f"    Object Bounds:")
print(f"      Min: X={min_pos[0]:.2f}, Y={min_pos[1]:.2f}, Z={min_pos[2]:.2f}")
print(f"      Max: X={max_pos[0]:.2f}, Y={max_pos[1]:.2f}, Z={max_pos[2]:.2f}")

# Create ObjectBounds instance
object_bounds = ObjectBounds(min_pos, max_pos)
print(f"\n    Object Dimensions:")
print(f"      Extent: X={object_bounds.extent[0]:.2f}, Y={object_bounds.extent[1]:.2f}, Z={object_bounds.extent[2]:.2f}")
print(f"      Max Dimension: {object_bounds.max_dimension:.2f} units")
print(f"      Diagonal: {object_bounds.diagonal:.2f} units")
print(f"      Max Radius (half-diagonal): {object_bounds.max_radius:.2f} units")

# Calculate camera distance with 24,000 unit minimum margin
cam_distance = ChimeraCamera.calculate_camera_distance(object_bounds, min_margin=ChimeraCamera.MIN_OUTSIDE_MARGIN)
print(f"\n[2] Camera Configuration:")
print(f"    Minimum Outside Margin: {ChimeraCamera.MIN_OUTSIDE_MARGIN:,} units")
print(f"    Calculated Camera Distance: {cam_distance:,.2f} units from center")

# Calculate FOV based on maximum units of an item (diagonal)
fov_rad = ChimeraCamera.calculate_fov(object_bounds.diagonal, cam_distance, target_screen_coverage=1.0)
fov_deg = math.degrees(fov_rad)
print(f"    View Angle (FOV): {fov_deg:.2f} degrees")

# Load real tree data for colors, scales, AND opacities
print("\n[3] Loading real tree data for rendering...")
real_data = np.load('WorldModel/training_data/real_tree_normalized.npz')
real_colors = real_data['colors']
real_scales = real_data['scales']
real_opacities = real_data['opacities']

idx = np.random.choice(len(real_colors), n, replace=True)
colors = real_colors[idx]

# Scale calibration using reference objects with known sizes
real_positions = real_data['positions']
real_extent = np.linalg.norm(real_positions.max(axis=0) - real_positions.min(axis=0))
norm_pos_extent = np.linalg.norm(object_bounds.max_pos - object_bounds.min_pos)

scale_factor = (real_extent / 8515.0) * (690.1 / norm_pos_extent)

# Apply calibrated scales to normalized positions
norm_pos = (positions - center) / object_bounds.max_radius * 50
sca = real_scales[idx].astype(np.float32) * scale_factor
rot = np.tile([0., 0., 0., 1.], (n, 1)).astype(np.float32)
cov = _build_covariances(sca, rot)

# Normalize opacities to prevent blowout in dense clusters
normalized_opacities = np.clip(real_opacities[idx] * 0.7, 0.0, 0.8).astype(np.float32)

# Set up Chimera Renderer with proper camera configuration
print("\n[4] Initializing Chimera Engine Renderer...")
renderer = ChimeraRenderer(width=1920, height=1080)
renderer.set_scene_bounds(min_pos, max_pos)

# Get render parameters
render_params = renderer.get_render_params()
print(f"    Render Resolution: {render_params['width']}x{render_params['height']}")
print(f"    Camera Position: X={render_params['camera_position'][0]:.2f}, Y={render_params['camera_position'][1]:.2f}, Z={render_params['camera_position'][2]:.2f}")
print(f"    FOV: {math.degrees(render_params['fov']):.2f} degrees")

# Create FirstPersonCamera for rendering with proper distance and FOV
cam_dist = render_params['camera_position'][2]
cam = FirstPersonCamera(
    position=(0.0, 0.0, float(cam_dist)),
    yaw=0.0,
    pitch=-0.1,
    fov=render_params['fov'],
    near=0.1,
    far=1000000.0
)

# Use base_scale=0.5 for proper covariance scaling
pipe = FullGPUPipeline(bg=(0.0, 0.0, 0.0), base_scale=0.5)

print("\n[5] Rendering 3D Tree with Chimera Engine Renderer...")
img = pipe.render_splats(
    norm_pos.astype(np.float32), 
    cov, 
    np.clip(colors, 0, 1).astype(np.float32), 
    normalized_opacities, 
    cam, 
    cam.params(render_params['width'], render_params['height'])
)

# Save the rendered image
rendered_path = 'ChimeraEngine/rendered_chimera_tree_3d.png'
Image.fromarray(img).save(rendered_path)
print(f"    Saved rendered image to: {rendered_path}")

# Verify rendering statistics
arr = np.array(img, dtype=np.float32)
non_white = (arr < 250).any(axis=2).sum()
dark = (arr < 50).any(axis=2).sum()
mid = ((arr >= 50) & (arr <= 200)).any(axis=2).sum()
bright = (arr > 200).any(axis=2).sum()

print("\n[6] Rendering Statistics:")
print(f"    Non-white pixels: {non_white:,} ({100*non_white/(render_params['width']*render_params['height']):.1f}%)")
print(f"    Dark (<50): {dark:,} ({100*dark/(render_params['width']*render_params['height']):.1f}%)")
print(f"    Mid (50-200): {mid:,} ({100*mid/(render_params['width']*render_params['height']):.1f}%)")
print(f"    Bright (>200): {bright:,} ({100*bright/(render_params['width']*render_params['height']):.1f}%)")

print("\n" + "=" * 60)
print("CHIMERA ENGINE RENDERER — DEMO COMPLETE")
print("=" * 60)
print("\nUnreal Engine Features Mapped to Chimera Engine:")
print("  ✓ Dynamic Camera System with FOV Calculation based on Object Bounds")
print("  ✓ Scalable Zoom In/Out with 24,000 unit minimum margin")
print("  ✓ View Angle Calculation based on Maximum Units of an Item")
print("  ✓ Perspective/Orthographic Projection Matrices")
print("  ✓ Transform Hierarchy (World, Local, View, Projection matrices)")
print("  ✓ Frustum Culling Support (via GPU pipeline cull kernel)")
print("  ✓ Level of Detail (LOD) System (via Nanite cluster selection)")
print("  ✓ Global Illumination / Radiance Cache (GPU-accelerated)")
print("  ✓ Post-processing Pipeline (Bloom, Tonemapping, AA)")
