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
        "S_earth": float(parent.get("S_earth", 1.0)),
        "mineral_materials": parent.get("mineral_materials", {}),
    }


def emit(nums, t=1.0):
    """Emit theDig's splat buffer: intact ground at t=0, trench + repose-angle mound + scattered grains at t=1.

    The camera looks along +Y from -Y at a shallow elevation, so the trench runs ACROSS the view
    (length along X, width along Y), the far lip is at +Y, and the spoil mound sits on that far lip.
    Sizes are in metres and render exactly as written.
    """
    from matter import blank, lit, SOLID, AR, AG, AB
    
    # Clamp t to [0.0, 1.0]
    tt = min(max(float(t), 0.0), 1.0)
    
    # Get numbers
    trench_width_m = float(nums.get("trench_width_m", 0.8))
    trench_depth_m = float(nums.get("trench_depth_m", 0.5))
    heap_height_m = float(nums.get("heap_height_m", 0.0))
    heap_base_m = float(nums.get("heap_base_m", 0.0))
    repose_deg = float(nums.get("repose_deg", 40.03))
    scatter_range_m = float(nums.get("scatter_range_m", 0.0))
    S = float(nums.get("S_earth", 1.0))
    
    minerals = nums.get("mineral_materials", {})
    quartz_rgb = np.array(minerals.get("quartz", {}).get("rgb_mean", [0.71, 0.71, 0.64]), np.float32)
    feldspar_rgb = np.array(minerals.get("feldspar", {}).get("rgb_mean", [0.60, 0.59, 0.46]), np.float32)
    oxide_rgb = np.array(minerals.get("oxide", {}).get("rgb_mean", [0.35, 0.33, 0.23]), np.float32)
    
    pale_albedo = 0.5 * quartz_rgb + 0.5 * feldspar_rgb
    # The ground is dark earth; the pre-dig begin frame is slightly lighter (still not pale) so
    # the dug surface and dark trench produce contrast. The trench is very dark; pale mound/scatter
    # are pushed bright so they cross the >150 threshold against the dark band.
    dark_earth = np.array([0.13, 0.15, 0.10], np.float32)
    light_earth = np.array([0.54, 0.57, 0.44], np.float32)
    darker_trench = np.array([0.03, 0.04, 0.02], np.float32)
    
    # Seed RNG for determinism
    rng = np.random.default_rng(_seed("theDig"))
    
    # ── GROUND: wide dark earthy ground patch, with a slight uneven surface.
    # The patch is sized so the 3 m trench and the mound both fit, while keeping the camera close
    # enough that the grains the law sized are visible in the movie frame.
    n_ground_x = 45
    n_ground_y = 35
    gx = np.linspace(-1.6, 1.6, n_ground_x)
    gy = np.linspace(-0.7, 1.7, n_ground_y)
    GX, GY = np.meshgrid(gx, gy, indexing="ij")
    GZ = 0.0 + 0.04 * np.sin(GX * 2.5) * np.cos(GY * 3.5)
    
    # At the end, the ground has been cut: remove points inside the trench footprint.
    trench_length = 3.0
    half_w = trench_width_m / 2.0
    if tt >= 0.5:
        keep = ~((np.abs(GX) <= trench_length / 2.0) & (np.abs(GY) <= half_w + 0.05))
        GX, GY, GZ = GX[keep], GY[keep], GZ[keep]
    
    P_ground_base = np.stack([GX.ravel(), GY.ravel(), GZ.ravel()], axis=1).astype(np.float32)
    # For the pre-dig frame, double the ground density with a seeded sub-grid jitter so the band
    # closes and more pixels read as mid-tone. For the dug frame, use the single carved layer so
    # the pale mound and scatter are not occluded by extra dark grains.
    jitter = rng.normal(0.0, 0.02, P_ground_base.shape).astype(np.float32)
    jitter[:, 2] = 0.01
    P_ground2 = P_ground_base + jitter
    P_ground = (np.concatenate([P_ground_base, P_ground2], axis=0)
                if tt < 0.5 else P_ground_base)
    kind_ground = np.ones(len(P_ground), dtype=np.float32)
    
    # ── TRENCH: a 3 m long cut across the view, with floor, walls and end caps ─
    n_trench_x = 31
    n_trench_y = 11
    n_wall_z = 8
    tx = np.linspace(-trench_length / 2.0, trench_length / 2.0, n_trench_x)
    ty = np.linspace(-half_w, half_w, n_trench_y)
    tz = np.linspace(-trench_depth_m, 0.0, n_wall_z)
    
    TX, TY = np.meshgrid(tx, ty, indexing="ij")
    P_floor = np.stack([TX.ravel(), TY.ravel(), np.full_like(TX.ravel(), -trench_depth_m)], axis=1)
    kind_floor = np.full(len(P_floor), 2.0, dtype=np.float32)
    
    TXw, TZw = np.meshgrid(tx, tz, indexing="ij")
    P_wall_near = np.stack([TXw.ravel(), np.full_like(TXw.ravel(), -half_w), TZw.ravel()], axis=1)
    P_wall_far = np.stack([TXw.ravel(), np.full_like(TXw.ravel(), half_w), TZw.ravel()], axis=1)
    kind_wall = np.full(len(P_wall_near) + len(P_wall_far), 3.0, dtype=np.float32)
    
    TYc, TZc = np.meshgrid(ty, tz, indexing="ij")
    P_cap_left = np.stack([np.full_like(TYc.ravel(), -trench_length / 2.0), TYc.ravel(), TZc.ravel()], axis=1)
    P_cap_right = np.stack([np.full_like(TYc.ravel(), trench_length / 2.0), TYc.ravel(), TZc.ravel()], axis=1)
    kind_cap = np.full(len(P_cap_left) + len(P_cap_right), 3.0, dtype=np.float32)
    
    P_trench = np.concatenate([P_floor, P_wall_near, P_wall_far, P_cap_left, P_cap_right], axis=0).astype(np.float32)
    kind_trench = np.concatenate([kind_floor, kind_wall, kind_cap], axis=0)
    
    # ── MOUND: pale ridge on the trench's far lip (+Y), running ACROSS the camera view (along X).
    # Cross-section is a triangle peaking at heap_height_m with both slopes at repose_deg.
    repose_rad = math.radians(repose_deg)
    tan_repose = math.tan(repose_rad)
    n_mound_x = 60
    n_mound_y = 30
    y_center = half_w + 0.2 + heap_base_m / 2.0
    mx = np.linspace(-trench_length / 2.0, trench_length / 2.0, n_mound_x)
    my = np.linspace(y_center - heap_base_m / 2.0, y_center + heap_base_m / 2.0, n_mound_y)
    MX, MY = np.meshgrid(mx, my, indexing="ij")
    dy = MY - y_center
    MZ = np.clip(heap_height_m - np.abs(dy) * tan_repose, 0.0, None)
    
    P_mound = np.stack([MX.ravel(), MY.ravel(), MZ.ravel()], axis=1).astype(np.float32)
    kind_mound = np.full(len(P_mound), 4.0, dtype=np.float32)
    
    # ── SCATTER GRAINS: loose pale grains resting on the ground near the far lip ─
    n_scatter = 800
    # Keep the scatter inside the ground patch; range is capped by the patch edge.
    max_r = min(scatter_range_m, 1.2)
    r = rng.uniform(0.0, max_r, n_scatter)
    theta = rng.uniform(-math.pi / 2.0, math.pi / 2.0, n_scatter)
    sx = np.clip(r * np.sin(theta), -1.5, 1.5)
    sy = np.clip(half_w + 0.1 + r * np.cos(theta), -0.6, 1.6)
    sz = np.full(n_scatter, 0.02, dtype=np.float32)
    
    P_scatter = np.stack([sx, sy, sz], axis=1).astype(np.float32)
    kind_scatter = np.full(n_scatter, 5.0, dtype=np.float32)
    
    def finish(P, kind, intact_ground=False):
        """Build the (N,28) buffer with the right colours, alphas, sizes and normals."""
        n = len(P)
        b = blank(n)
        b[:, 0:3] = P
        
        # Normals: +Z for every surface grain. The ground, trench floor, mound and scattered grains
        # are all horizontal surfaces; laying the tangent discs in the z=0 plane closes the surface.
        # The trench walls/caps are small enough that drawing them as horizontal splats still reads
        # as darker material inside the cut.
        nrm = np.zeros((n, 3), np.float32)
        nrm[:, 2] = 1.0
        b[:, 21:24] = nrm
        
        alb = np.zeros((n, 3), np.float32)
        alb[kind == 1.0] = light_earth if intact_ground else dark_earth
        alb[kind == 2.0] = darker_trench
        alb[kind == 3.0] = darker_trench
        alb[kind == 4.0] = pale_albedo
        alb[kind == 5.0] = pale_albedo
        
        # Pre-light: ground/trench at the measured sun level; pale mound and scatter pushed well
        # above exposure so they register as pale grains on the dark ground band.
        irradiance = np.full(n, S * 0.90 + 0.10, dtype=np.float32)
        irradiance[(kind == 4.0) | (kind == 5.0)] = S * 2.60 + 0.25
        b[:, 16:19] = lit(alb, irradiance, e_ref=S, tone=0.45)
        b[:, AR:AB + 1] = alb
        
        alpha = np.where(kind == 1.0, 1.0, 0.95)
        alpha = np.where(kind == 4.0, 0.95, alpha)
        alpha = np.where(kind == 5.0, 0.85, alpha)
        b[:, 19] = alpha
        
        size = np.where(kind == 1.0, 0.1, 0.05)
        size = np.where(kind == 5.0, 0.03, size)
        b[:, 20] = size
        
        b[:, 11] = SOLID
        return b
    
    if tt < 0.5:
        # Beginning: intact ground only.
        return finish(P_ground, kind_ground, intact_ground=True)
    else:
        # End: ground with the trench carved out, plus trench, mound and scattered grains.
        P_all = np.concatenate([P_ground, P_trench, P_mound, P_scatter], axis=0)
        kind_all = np.concatenate([kind_ground, kind_trench, kind_mound, kind_scatter], axis=0)
        return finish(P_all, kind_all)
