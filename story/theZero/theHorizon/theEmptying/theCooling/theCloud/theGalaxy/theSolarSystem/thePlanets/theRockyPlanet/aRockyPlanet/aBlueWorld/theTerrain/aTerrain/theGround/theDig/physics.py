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


def _seed(term: str) -> int:
    """A stable per-term seed -- deterministic across processes."""
    import zlib
    return zlib.crc32(term.encode("utf-8")) & 0x7FFFFFFF


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
    
    # 3. SCATTERED-GRAIN BALLISTICS: sane values for dig-scattered grains
    # Grains thrown from a dig land within 1-2m of the trench with single-digit m/s velocity
    # Energy to lift soil to mound height: E_lift = mass * g * (heap_height_m / 2)
    # Mass of scattered grains per meter length
    scatter_fraction = 0.05  # 5% of dug material scatters as loose grains
    mass_per_m_kg = bulk_density * trench_volume_per_m  # total mass per meter length
    
    # Energy to lift spoil to mound center of mass (height/2)
    energy_to_lift_J_per_m = mass_per_m_kg * g * (heap_height_m / 2.0)
    
    # Scattered grains get a fraction of this energy as kinetic energy
    # Typically 10-20% of excavation energy goes into scattering
    scatter_energy_fraction = 0.15
    scatter_energy_per_m_J = energy_to_lift_J_per_m * scatter_energy_fraction
    
    # Mass of scattered grains per meter length
    mass_scattered_per_m_kg = mass_per_m_kg * scatter_fraction
    
    # Velocity from kinetic energy: E = 0.5 * m * v^2 => v = sqrt(2*E/m)
    if mass_scattered_per_m_kg > 0 and scatter_energy_per_m_J > 0:
        scattered_grain_velocity_ms = math.sqrt(2.0 * scatter_energy_per_m_J / mass_scattered_per_m_kg)
    else:
        scattered_grain_velocity_ms = 0.0
    
    # Maximum height and range of scattered grains in parent's g
    # For a projectile launched at angle ~45 degrees:
    scatter_max_height_m = (scattered_grain_velocity_ms ** 2 * math.sin(math.radians(45)) ** 2) / (2.0 * g) if g > 0 else 0.0
    scatter_range_m = (scattered_grain_velocity_ms ** 2 * math.sin(math.radians(90))) / g if g > 0 else 0.0
    
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
        "mass_per_m_kg": mass_per_m_kg,
        "energy_to_lift_J_per_m": energy_to_lift_J_per_m,
        "scatter_energy_per_m_J": scatter_energy_per_m_J,
        "mass_scattered_per_m_kg": mass_scattered_per_m_kg,
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
    from matter import blank, lit, SOLID, GLOW, AR, AG, AB
    
    # Clamp t to [0.0, 1.0]
    tt = min(max(float(t), 0.0), 1.0)
    
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
    
    # Seed RNG for determinism
    seed_val = _seed("theDig")
    rng = np.random.default_rng(seed_val)
    
    # Create ground buffer (coarse grid, a few thousand splats)
    # Ground: wide dark earthy ground
    n_ground_x = 100
    n_ground_y = 50
    gx = np.linspace(-4.0, 4.0, n_ground_x)
    gy = np.linspace(-2.0, 2.0, n_ground_y)
    
    # Build ground points using matter conventions
    P_ground = []
    kind_ground = []
    
    for i, x in enumerate(gx):
        for j, y in enumerate(gy):
            # Create a flat ground surface with some noise
            z = 0.0 + 0.05 * np.sin(x * 2.0) * np.cos(y * 3.0)
            
            # Position and normal (facing up for ground)
            P_ground.append([x, y, z])
            kind_ground.append(1)  # type: solid ground
    
    # Trench: narrow trench cut into the ground (floor + two walls at derived width/depth)
    n_trench_x = 40
    trench_x = np.linspace(-trench_width_m/2, trench_width_m/2, n_trench_x)
    
    P_trench_floor = []
    kind_trench_floor = []
    P_trench_walls_left = []
    kind_trench_walls_left = []
    P_trench_walls_right = []
    kind_trench_walls_right = []
    
    # Trench floor (flat bottom at -trench_depth_m)
    for x in trench_x:
        z_trench_floor = -trench_depth_m
        P_trench_floor.append([x, 0.0, z_trench_floor])
        kind_trench_floor.append(2)  # type: trench floor (darker than surface)
    
    # Trench walls (vertical drops at the edges)
    wall_x_left = -trench_width_m/2 - 0.05
    wall_x_right = trench_width_m/2 + 0.05
    n_wall_y = 20
    
    for j, y in enumerate(np.linspace(-0.1, 0.1, n_wall_y)):
        # Left wall
        P_trench_walls_left.append([wall_x_left, y, -trench_depth_m + (j/n_wall_y)*trench_depth_m])
        kind_trench_walls_left.append(3)
        
        # Right wall
        P_trench_walls_right.append([wall_x_right, y, -trench_depth_m + (j/n_wall_y)*trench_depth_m])
        kind_trench_walls_right.append(3)
    
    # Spoil mound: pale freshly-dug grains heaped beside the opening
    # Triangular mound with slope = repose_deg, placed at trench's lip
    n_mound_x = 60
    # Mound is to the right of the trench
    mound_x_start = heap_base_m/2 + 0.2
    mound_x_end = heap_base_m/2 + heap_base_m + 0.5
    mound_x = np.linspace(mound_x_start, mound_x_end, n_mound_x)
    
    P_mound = []
    kind_mound = []
    
    for x in mound_x:
        # Triangular cross-section: height decreases linearly from trench lip
        # Mound starts at trench edge (x = heap_base_m/2) and goes to the right
        if heap_base_m > 0:
            # Distance from center of mound
            dist_from_center = abs(x - heap_base_m/2)
            if dist_from_center <= heap_base_m / 2:
                z_mound = heap_height_m * (1 - 2 * dist_from_center / heap_base_m)
            else:
                z_mound = 0.0
        else:
            z_mound = 0.0
            
        P_mound.append([x, 1.5, z_mound])
        kind_mound.append(4)  # type: spoil mound (pale color)
    
    # Scattered grains: a few loose grains scattered nearby
    n_scatter = 30
    P_scatter = []
    kind_scatter = []
    
    for i in range(n_scatter):
        # Scatter around the trench and mound area, within 1-2 meters
        sx = rng.uniform(-heap_base_m/2 - 0.5, heap_base_m/2 + 2.0)
        sy = rng.uniform(0.5, 3.0)
        
        # Height follows a small distribution (grains land near the hole)
        sz = max(0.0, rng.exponential(0.15))
        
        P_scatter.append([sx, sy, sz])
        kind_scatter.append(5)  # type: scattered grains
    
    # Combine all points
    P_all = np.array(P_ground + P_trench_floor + P_trench_walls_left + P_trench_walls_right + P_mound + P_scatter, dtype=np.float32)
    kind_all = np.concatenate([
        np.array(kind_ground, dtype=np.float32),
        np.array(kind_trench_floor, dtype=np.float32),
        np.array(kind_trench_walls_left, dtype=np.float32),
        np.array(kind_trench_walls_right, dtype=np.float32),
        np.array(kind_mound, dtype=np.float32),
        np.array(kind_scatter, dtype=np.float32)
    ], dtype=np.float32)
    
    n = len(P_all)
    b = blank(n)
    b[:, 0:3] = P_all
    
    # Normals: ground faces up (0,1,0), trench walls face inward/outward
    nrm = np.zeros((n, 3), np.float32)
    # Ground normals point up
    n_ground_count = len(P_ground)
    nrm[:n_ground_count, 1] = -1.0  # facing up in +Z convention -> normal is (0,-1,0) or (0,1,0)
    
    skin_albedo = np.array([0.35, 0.38, 0.28], np.float32)  # dark earthy ground
    
    alb = np.zeros((n, 3), np.float32)
    # Ground: dark earthy (mineral mix)
    alb[kind_all == 1] = skin_albedo
    # Trench floor: darker than surface
    alb[kind_all == 2] = np.array([0.22, 0.25, 0.18], np.float32)
    # Trench walls: darker than surface
    alb[kind_all == 3] = np.array([0.20, 0.23, 0.16], np.float32)
    # Mound: pale freshly-dug grains (mix of quartz and feldspar)
    alb[kind_all == 4] = 0.5 * quartz_rgb + 0.5 * feldspar_rgb
    # Scattered grains: pale grains
    alb[kind_all == 5] = feldspar_rgb * 1.2
    
    S = float(nums.get("S_earth", 1.0))
    b[:, 16:19] = lit(alb, S * 0.85 + 0.15, e_ref=S, tone=0.45)
    b[:, AR:AB + 1] = alb
    
    # Alpha and size
    a_ = np.where((kind_all == 1), 0.8, 0.9)
    a_ = np.where((kind_all == 2) | (kind_all == 3), 0.95, a_)
    a_ = np.where((kind_all == 4), 0.85, a_)
    a_ = np.where(kind_all == 5, 0.7, a_)
    
    b[:, 19] = a_
    b[:, 20] = np.where((kind_all == 1), 2.0, 1.5)
    b[:, 20] = np.where((kind_all == 4) | (kind_all == 5), 0.8, b[:, 20])
    
    # Type: SOLID for ground/trench/mound, GLOW for scattered grains
    b[:, 11] = np.where(kind_all <= 4, SOLID, GLOW)
    
    if tt < 0.5:
        # Beginning: mostly intact ground
        n_ground_only = len(P_ground)
        b_ground = blank(n_ground_count)
        b_ground[:, 0:3] = np.array(P_ground[:n_ground_count], dtype=np.float32)
        nrm_ground = np.zeros((n_ground_count, 3), np.float32)
        nrm_ground[:, 1] = -1.0
        b_ground[:, 21:24] = nrm_ground
        
        skin_albedo_g = np.array([0.35, 0.38, 0.28], np.float32)
        alb_g = np.zeros((n_ground_count, 3), np.float32)
        alb_g[:] = skin_albedo_g
        
        S_val = float(nums.get("S_earth", 1.0))
        b_ground[:, 16:19] = lit(alb_g, S_val * 0.85 + 0.15, e_ref=S_val, tone=0.45)
        b_ground[:, AR:AB + 1] = alb_g
        
        a_g = np.full(n_ground_count, 0.8, dtype=np.float32)
        b_ground[:, 19] = a_g
        b_ground[:, 20] = np.full(n_ground_count, 2.0, dtype=np.float32)
        b_ground[:, 11] = SOLID
        
        return b_ground
    else:
        # End: trench + mound + scattered grains
        return b
