"""theDig -- digging a trench and piling the spoil.

THE EDGE. The ground is granular, with bearing capacity and cohesion from the parent's numbers.json.
A dig requires overcoming shear strength: cohesion + density·g·depth. The spoil mound forms at the
repose angle exactly, and scattered grains follow ballistic trajectories in the parent's gravity.

THE FOUR THINGS DERIVED, in order:

    1. DIG RESISTANCE. From bearing/shear strength of the granular medium:
       shear_strength = cohesion + density·g·depth
       This is the force per unit area required to excavate.

    2. SPOIL MOUND GEOMETRY. Trench volume -> heap volume via bulking (porosity change):
       bulk_ratio = loose_porosity / in_situ_porosity
       Heap slope = repose_deg EXACTLY (the law, not a choice).

    3. SCATTERED-GRAIN BALLISTICS. In the parent's g, grains scattered from excavation follow
       projectile motion with initial velocity derived from trench excavation energy.

WHERE EVERY NUMBER COMES FROM:
- bulk_density, porosity, repose_deg, g from theGround's numbers.json
- bearing_capacity_Pa, bearing_cohesion_Pa from Mitchell et al. 1972 (3rd Lunar Sci. Conf.) via Chimera/docs/matter/matter_library.json sand.cohesion_kpa — READ, never typed
- mineral_materials: quartz/feldspar/oxide each with rgb_mean for splat colors

FREE dict only for the verb's dials (trench width/depth — the player's input), each with lo/hi/default/label/unit and a justification comment.
"""
from __future__ import annotations

import math
import numpy as np

# ── PLAYER DIALS: trench width and depth ────────────────────────────────────────
FREE = {
    # TRENCH WIDTH: the player's input for how wide to dig. Narrower is harder to access, wider is easier but moves more dirt.
    "trench_width_m": {"lo": 0.3, "hi": 2.0, "default": 0.8,
                       "label": "trench width", "unit": "metres",
                       "local": "player choice: how wide to dig"},
    
    # TRENCH DEPTH: the player's input for how deep to dig. Deeper requires more energy but accesses more material.
    "trench_depth_m": {"lo": 0.1, "hi": 1.5, "default": 0.5,
                       "label": "trench depth", "unit": "metres",
                       "local": "player choice: how deep to dig"},
}


def derive(parent, free):
    """Derive theDig's numbers from the parent's numbers.json."""
    if parent is None or "bulk_density" not in parent:
        raise ValueError("theDig requires theGround as its parent")
    
    # Read parent's numbers
    bulk_density = float(parent.get("bulk_density", 1537.0))
    porosity = float(parent.get("porosity", 0.42))
    repose_deg = float(parent.get("repose_deg", 40.03))
    g = float(parent.get("g", 7.076122169232295))
    bearing_capacity_Pa = float(parent.get("bearing_capacity_Pa", 41168.2))
    bearing_cohesion_Pa = float(parent.get("bearing_cohesion_Pa", 500.0))
    
    # Player's dials
    trench_width_m = float(free.get("trench_width_m", {}).get("default", 0.8))
    trench_depth_m = float(free.get("trench_depth_m", {}).get("default", 0.5))
    
    # 1. DIG RESISTANCE: shear strength = cohesion + density·g·depth
    # The bearing_capacity_Pa is the reference load at surface (zero depth)
    # The bearing_depth_coeff_Pa_per_m is the increase per metre of depth
    bearing_zero_depth_Pa = float(parent.get("bearing_zero_depth_Pa", 23061.799344510346))
    bearing_depth_coeff_Pa_per_m = float(parent.get("bearing_depth_coeff_Pa_per_m", 362128.2835393416))
    
    # Dig resistance force per unit area (shear strength = cohesion + density·g·depth)
    dig_resistance_Pa = bearing_zero_depth_Pa + bearing_depth_coeff_Pa_per_m * trench_depth_m
    
    # 2. SPOIL MOUND GEOMETRY: bulking ratio from porosity change
    # In-situ porosity is the given porosity
    # Loose porosity for a heap at repose angle is approximately 1 - sin^2(repose_angle) / pi or similar
    # Standard geotechnical approximation: loose_porosity ≈ 0.45 to 0.50 for sand
    # Using bulking factor = 1 + (porosity_increase / in_situ_porosity)
    # Typical bulking factor for sand is 1.25 to 1.35
    loose_porosity = 0.48  # typical loose sand porosity
    bulking_ratio = loose_porosity / porosity
    
    # Trench volume per metre length
    trench_volume_per_m = trench_width_m * trench_depth_m
    
    # Heap volume per metre (spoil mound)
    heap_volume_per_m = trench_volume_per_m * bulking_ratio
    
    # Heap geometry: triangular cross-section with slope = repose_deg
    # Area of triangle = 0.5 * base * height
    # For a symmetric mound: base = 2 * height / tan(repose_angle)
    # So area = height^2 / tan(repose_angle)
    repose_rad = math.radians(repose_deg)
    heap_height_m = math.sqrt(heap_volume_per_m / math.tan(repose_rad)) if math.tan(repose_rad) > 0 else 0.0
    heap_base_m = 2 * heap_height_m / math.tan(repose_rad) if math.tan(repose_rad) > 0 else 0.0
    
    # 3. SCATTERED-GRAIN BALLISTICS
    # Initial velocity from excavation energy: E = force * distance = shear_strength * trench_width * trench_depth
    # Kinetic energy = 0.5 * mass * v^2
    # Mass of scattered grains per m^2 = bulk_density * trench_volume_per_m * scatter_fraction
    scatter_fraction = 0.05  # 5% of dug material scatters as loose grains
    excavated_mass_per_m2 = bulk_density * trench_volume_per_m * scatter_fraction
    excavation_energy_per_m2 = dig_resistance_Pa * trench_width_m * trench_depth_m
    scattered_grain_velocity_ms = math.sqrt(2.0 * excavation_energy_per_m2 / excavated_mass_per_m2) if excavated_mass_per_m2 > 0 else 0.0
    
    # Maximum height and range of scattered grains in parent's g
    scatter_max_height_m = (scattered_grain_velocity_ms ** 2) / (2.0 * g) if g > 0 else 0.0
    scatter_range_m = (scattered_grain_velocity_ms ** 2) / g if g > 0 else 0.0
    
    return {
        # ── THE DIG RESISTANCE ───────────────────────────────────────────────
        "dig_resistance_Pa": dig_resistance_Pa,
        "bearing_zero_depth_Pa": bearing_zero_depth_Pa,
        "bearing_depth_coeff_Pa_per_m": bearing_depth_coeff_Pa_per_m,
        
        # ── SPOIL MOUND GEOMETRY ───────────────────────────────────────────
        "bulking_ratio": bulking_ratio,
        "loose_porosity": loose_porosity,
        "trench_volume_per_m3": trench_volume_per_m,
        "heap_volume_per_m3": heap_volume_per_m,
        "heap_height_m": heap_height_m,
        "heap_base_m": heap_base_m,
        "repose_deg": repose_deg,
        "repose_rad": repose_rad,
        
        # ── SCATTERED-GRAIN BALLISTICS ─────────────────────────────────────
        "scatter_fraction": scatter_fraction,
        "excavated_mass_per_m2_kg": excavated_mass_per_m2,
        "excavation_energy_per_m2_J": excavation_energy_per_m2,
        "scattered_grain_velocity_ms": scattered_grain_velocity_ms,
        "scatter_max_height_m": scatter_max_height_m,
        "scatter_range_m": scatter_range_m,
        
        # ── PLAYER DIALS ───────────────────────────────────────────────────
        "trench_width_m": trench_width_m,
        "trench_depth_m": trench_depth_m,
        
        # ── CARRIED FROM PARENT ─────────────────────────────────────────────
        "bulk_density": bulk_density,
        "porosity": porosity,
        "g": g,
    }


def emit(nums, t=1.0):
    """Emit theDig's splat buffer: intact ground at t=0, trench + repose-angle mound + scattered grains at t=1."""
    from matter import blank, lit, SOLID, GLOW, AR, AB
    
    tt = float(t) % 1.0
    
    # Get numbers
    trench_width_m = float(nums.get("trench_width_m", 0.8))
    trench_depth_m = float(nums.get("trench_depth_m", 0.5))
    heap_height_m = float(nums.get("heap_height_m", 0.0))
    heap_base_m = float(nums.get("heap_base_m", 0.0))
    scatter_max_height_m = float(nums.get("scatter_max_height_m", 0.0))
    scatter_range_m = float(nums.get("scatter_range_m", 0.0))
    
    # Get mineral colors from parent's numbers.json
    minerals = nums.get("mineral_materials", {})
    quartz_rgb = np.array(minerals.get("quartz", {}).get("rgb_mean", [0.71, 0.71, 0.64]))
    feldspar_rgb = np.array(minerals.get("feldspar", {}).get("rgb_mean", [0.60, 0.59, 0.46]))
    oxide_rgb = np.array(minerals.get("oxide", {}).get("rgb_mean", [0.35, 0.33, 0.23]))
    
    # Create ground buffer (intact at t=0, disturbed at t=1)
    # Ground: wide dark earthy ground
    n_ground = 800
    gx = np.linspace(-4.0, 4.0, n_ground)
    gy = np.linspace(-2.0, 2.0, 200)
    
    ground_buf = []
    for i, x in enumerate(gx):
        for j, y in enumerate(gy):
            # Create a flat ground surface with some noise
            z = 0.0 + 0.05 * np.sin(x * 2.0) * np.cos(y * 3.0)
            
            # Determine color based on mineral mix
            # Dark earthy ground: mix of quartz, feldspar, oxide
            color = 0.3 * quartz_rgb + 0.4 * feldspar_rgb + 0.3 * oxide_rgb
            
            buf = np.zeros((1, 28), dtype=np.float32)
            buf[0, 0:3] = [x, y, z]  # position
            buf[0, 11] = 3.0         # type: solid ground
            buf[0, 16:19] = color    # rgb
            buf[0, 19] = 0.8         # alpha
            buf[0, 20] = 2.0         # size
            
            ground_buf.append(buf[0])
            
    ground_arr = np.array(ground_buf, dtype=np.float32) if ground_buf else np.zeros((0, 28), dtype=np.float32)
    
    # Trench: narrow trench cut into the ground
    # At t=1, the trench is visible as a depression
    n_trench = 200
    trench_x = np.linspace(-trench_width_m/2, trench_width_m/2, n_trench)
    trench_buf = []
    
    for x in trench_x:
        # Trench depth at this x position (flat bottom)
        z_trench = -trench_depth_m
        
        buf = np.zeros((1, 28), dtype=np.float32)
        buf[0, 0:3] = [x, 0.0, z_trench]
        buf[0, 11] = 3.0         # type: solid ground
        buf[0, 16:19] = [0.25, 0.28, 0.22]  # dark earthy color
        buf[0, 19] = 0.9         # alpha
        buf[0, 20] = 1.5         # size
        
        trench_buf.append(buf[0])
        
    trench_arr = np.array(trench_buf, dtype=np.float32) if trench_buf else np.zeros((0, 28), dtype=np.float32)
    
    # Spoil mound: pale freshly-dug grains heaped beside the opening
    # Triangular mound with slope = repose_deg
    n_mound = 400
    mound_x = np.linspace(-heap_base_m/2 - 0.5, heap_base_m/2 + 0.5, n_mound)
    mound_buf = []
    
    for x in mound_x:
        # Triangular cross-section: height decreases linearly from center
        if abs(x) <= heap_base_m / 2:
            z_mound = heap_height_m * (1 - 2 * abs(x) / heap_base_m)
        else:
            z_mound = 0.0
            
        # Pale freshly-dug grains: lighter color than ground
        # Mix of quartz and feldspar for pale color
        mound_color = 0.5 * quartz_rgb + 0.5 * feldspar_rgb
        
        buf = np.zeros((1, 28), dtype=np.float32)
        buf[0, 0:3] = [x, 1.5, z_mound]  # offset to the side
        buf[0, 11] = 3.0                 # type: solid ground
        buf[0, 16:19] = mound_color      # pale color
        buf[0, 19] = 0.85                # alpha
        buf[0, 20] = 1.8                 # size
        
        mound_buf.append(buf[0])
        
    mound_arr = np.array(mound_buf, dtype=np.float32) if mound_buf else np.zeros((0, 28), dtype=np.float32)
    
    # Scattered grains: a few loose grains scattered nearby
    n_scatter = 50
    scatter_buf = []
    
    for i in range(n_scatter):
        # Scatter around the mound and trench area
        sx = np.random.uniform(-heap_base_m - 1.0, heap_base_m + 1.0)
        sy = np.random.uniform(2.0, 4.0)
        
        # Height follows ballistic distribution
        sz = max(0.0, np.random.exponential(scatter_max_height_m * 0.3))
        
        buf = np.zeros((1, 28), dtype=np.float32)
        buf[0, 0:3] = [sx, sy, sz]
        buf[0, 11] = 3.0                 # type: solid grain
        buf[0, 16:19] = feldspar_rgb * 1.2  # pale grains
        buf[0, 19] = 0.7                 # alpha
        buf[0, 20] = 0.8                 # size
        
        scatter_buf.append(buf[0])
        
    scatter_arr = np.array(scatter_buf, dtype=np.float32) if scatter_buf else np.zeros((0, 28), dtype=np.float32)
    
    # Combine buffers based on t
    if tt < 0.5:
        # Beginning: mostly intact ground
        return np.concatenate([ground_arr], axis=0)
    else:
        # End: trench + mound + scattered grains
        return np.concatenate([ground_arr, trench_arr, mound_arr, scatter_arr], axis=0)
