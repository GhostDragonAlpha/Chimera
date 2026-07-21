"""
Reflection and deflection physics kernel — calculates proper angle of
reflection when particles hit surfaces with arbitrary normals.

Extends the standard kernel set with:
  - Normal-aware reflection (not just horizontal ground)
  - Angle of incidence = angle of reflection
  - Surface normal estimation from neighbor particles or from explicit geometry
  - Gaussian angle formulation (specular-like spread based on impact angle)

The reflection formula:
  v_out = v_in - 2(v_in · n) * n
  with restitution (energy loss) and spread (random perturbation).
"""

import numpy as np
from ParticleEngine.core import COL, C_VEL, C_POS, C_PROPS


def reflect_kernel(data, active, cvars, dt):
    """
    Generic reflection kernel — particles bounce off surfaces based on
    control variables specifying surface geometry.

    Reads from control_vars:
      ground_level:       float  — Z-coordinate of a horizontal ground plane
      restitution:        float  — bounce energy retention (0=stick, 1=perfect)
      reflection_spread:  float  — random angular spread after reflection
      surface_normals:    optional — explicit surface normals

    For each particle that passes through or touches a surface, computes
    the proper reflection vector and applies it.
    """
    ground_z = cvars.get("ground_level", 0.0)
    restitution = cvars.get("restitution", 0.3)
    spread = cvars.get("reflection_spread", 0.05)  # radians of random perturb

    pos_z = data[:, COL["pz"]]
    vel_z = data[:, COL["vz"]]

    # Find particles below ground
    below = active & (pos_z < ground_z)

    if not below.any():
        return

    # Ground surface normal = (0, 0, 1) (pointing up)
    n = np.array([0.0, 0.0, 1.0], dtype=np.float32)

    # For each particle below ground:
    vel = data[below, C_VEL]  # (M, 3)

    # Compute reflection: v_out = v_in - 2*(v_in·n)*n
    v_dot_n = np.dot(vel, n)  # (M,) — should be negative (falling)
    v_reflected = vel - 2.0 * v_dot_n[:, np.newaxis] * n  # (M, 3)

    # Apply restitution (energy loss)
    v_reflected *= restitution

    # Apply random spread (simulates surface roughness / Gaussian scattering)
    if spread > 0:
        # Random perturbation in the hemisphere above the surface
        rand_theta = np.random.uniform(0, 2 * np.pi, len(vel))
        rand_phi = np.random.uniform(0, spread, len(vel))
        perturb = np.stack([
            np.sin(rand_phi) * np.cos(rand_theta),
            np.sin(rand_phi) * np.sin(rand_theta),
            np.cos(rand_phi),
        ], axis=1)
        v_reflected += perturb * np.linalg.norm(v_reflected, axis=1, keepdims=True) * 0.5

    # Apply new velocity
    data[below, C_VEL] = v_reflected

    # Snap to surface
    data[below, COL["pz"]] = ground_z

    # Record impact in prop3 (impact counter / energy accumulator)
    impact_energy = 0.5 * np.sum(vel * vel, axis=1) * data[below, COL["mass"]]
    data[below, COL["prop3"]] += impact_energy


def angled_surface_reflect_kernel(data, active, cvars, dt):
    """
    Reflection off non-horizontal surfaces defined by a heightfield.

    Reads from control_vars:
      surface_z:    2D array or callable that returns Z for any (x,y) world position
      surface_nx:   normal X-component field
      surface_ny:   normal Y-component field
      surface_nz:   normal Z-component field

    This kernel assumes the surface is defined as z = f(x,y) with normals
    pre-computed per cell. For dynamic surfaces, the normals can be estimated
    from neighbor particle positions.

    For now, demonstrates the concept with a sloped surface: z = 0.1 * x (ramp).
    """
    # Default: ramp surface z = slope * x
    slope = cvars.get("ramp_slope", 0.0)  # 0 = flat ground
    ground_z = cvars.get("ground_level", 0.0)
    restitution = cvars.get("restitution", 0.3)

    if slope == 0.0:
        return  # flat ground — use reflect_kernel instead

    px = data[active, COL["px"]]
    py = data[active, COL["py"]]
    pz = data[active, COL["pz"]]

    # Surface height at each particle's (x, y)
    surface_z = ground_z + slope * px
    below = pz < surface_z

    if not below.any():
        return

    # Ramp normal: surface z - slope*x = 0, gradient = (-slope, 0, 1)
    # Normalized: n = (-slope, 0, 1) / sqrt(slope² + 1)
    normal_mag = np.sqrt(slope * slope + 1.0)
    nx = -slope / normal_mag
    ny = 0.0
    nz = 1.0 / normal_mag
    n = np.array([nx, ny, nz], dtype=np.float32)

    below_idx = np.where(below)[0]
    vel = data[below_idx, C_VEL]

    # Reflection: v_out = v_in - 2*(v_in·n)*n
    v_dot_n = vel[:, 0] * n[0] + vel[:, 1] * n[1] + vel[:, 2] * n[2]
    v_refl = vel - 2.0 * v_dot_n[:, np.newaxis] * n

    # Only reflect if velocity is INTO the surface (v_dot_n < 0)
    incoming = v_dot_n < 0
    if incoming.any():
        inc_idx = below_idx[incoming]
        data[inc_idx, C_VEL] = v_refl[incoming] * restitution

    # Snap to surface
    data[below_idx, COL["pz"]] = surface_z[below]

    # Record impact
    data[below_idx, COL["prop3"]] += np.abs(v_dot_n) * data[below_idx, COL["mass"]]


def gaussian_scatter_kernel(data, active, cvars, dt):
    """
    After a collision, scatter the reflected velocity with a Gaussian
    angular distribution based on the impact roughness parameter.

    The spread angle σ is read from control_vars as 'surface_roughness'.
    The reflected velocity is perturbed by a random 3D rotation with
    standard deviation σ around the perfect reflection direction.

    This creates the "Gaussian angle" formulation — the reflected
    particles form a Gaussian lobe around the specular direction,
    which is exactly what a microfacet BRDF would model.
    """
    roughness = cvars.get("surface_roughness", 0.1)  # radians σ

    if roughness <= 0:
        return

    # Find particles that recently impacted (prop3 > 0 = impact recorded)
    impacted = active & (data[:, COL["prop3"]] > 0)

    if not impacted.any():
        return

    n_impacted = impacted.sum()
    vel = data[impacted, C_VEL]
    speed = np.linalg.norm(vel, axis=1, keepdims=True)

    # Normalize velocity to get reflection direction
    vel_dir = vel / (speed + 1e-12)

    # Generate Gaussian angular perturbation
    # Random axis perpendicular to velocity
    # Random angle from Gaussian distribution with σ = roughness
    theta = np.random.normal(0, roughness, n_impacted)  # azimuthal
    phi = np.random.uniform(0, 2 * np.pi, n_impacted)    # around reflection axis

    # Rodrigues' rotation formula: rotate vel_dir by angle θ around random axis
    # Pick a perpendicular axis
    perp = np.zeros_like(vel_dir)
    # Cross product with an arbitrary vector to get perpendicular
    arb = np.array([0.0, 0.0, 1.0], dtype=np.float32)
    for i in range(len(vel_dir)):
        if abs(np.dot(vel_dir[i], arb)) > 0.99:
            arb = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        axis = np.cross(vel_dir[i], arb)
        axis /= np.linalg.norm(axis) + 1e-12
        # Second perpendicular
        axis2 = np.cross(vel_dir[i], axis)
        # Rotate
        v_rot = (
            vel_dir[i] * np.cos(theta[i])
            + axis * np.sin(theta[i]) * np.cos(phi[i])
            + axis2 * np.sin(theta[i]) * np.sin(phi[i])
        )
        data[np.where(impacted)[0][i], C_VEL] = v_rot * speed[i, 0]

    # Clear impact markers
    data[impacted, COL["prop3"]] = 0
