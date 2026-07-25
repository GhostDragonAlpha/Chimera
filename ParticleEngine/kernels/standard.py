"""
Standard physics kernels: gravity, wind, collision, friction, accumulation.

Every kernel receives (data, active_mask, control_vars, dt) and modifies
`data` in-place — fully vectorized against all active particles.
"""

import numpy as np
from ParticleEngine.core import COL, C_VEL, C_ACC, C_POS, C_PROPS, PARTICLE_TYPES


# ── Gravity ─────────────────────────────────────────────────────

def gravity_kernel(data, active, cvars, dt):
    """
    Apply gravity to all active particles.
    Reads `gravity` from control_vars, defaults to Earth gravity.
    """
    gx, gy, gz = cvars.get("gravity", (0.0, 0.0, -981.0))  # cm/s² default
    data[active, COL["ax"]] += gx
    data[active, COL["ay"]] += gy
    data[active, COL["az"]] += gz


# ── Wind / External Force ───────────────────────────────────────

def wind_kernel(data, active, cvars, dt):
    """
    Apply a wind force field to all active particles.
    Reads `wind_vector` (3-tuple) and `wind_strength` from control_vars.
    Wind affects particles proportionally to their size (drag model).
    """
    wx, wy, wz = cvars.get("wind_vector", (0.0, 0.0, 0.0))
    strength = cvars.get("wind_strength", 1.0)
    # Drag: smaller particles = more affected
    size = data[active, COL["size"]]
    drag = np.clip(1.0 / (size + 0.01), 0.1, 10.0)
    data[active, COL["ax"]] += wx * strength * drag
    data[active, COL["ay"]] += wy * strength * drag
    data[active, COL["az"]] += wz * strength * drag


# ── Boundary / Ground Collision ─────────────────────────────────

def ground_collision_kernel(data, active, cvars, dt):
    """
    Bounce particles off the ground plane (z=0) with restitution.
    Reads `ground_level`, `restitution`, and `friction` from control_vars.
    """
    ground_z = cvars.get("ground_level", 0.0)
    restitution = cvars.get("restitution", 0.3)
    friction = cvars.get("friction", 0.5)

    pos_z = data[:, COL["pz"]]
    vel_z = data[:, COL["vz"]]
    below = active & (pos_z < ground_z)

    if not below.any():
        return

    # Snap to ground
    data[below, COL["pz"]] = ground_z

    # Bounce with restitution
    data[below, COL["vz"]] = -vel_z[below] * restitution

    # Apply friction to horizontal velocity
    data[below, COL["vx"]] *= (1.0 - friction)
    data[below, COL["vy"]] *= (1.0 - friction)


# ── Box Boundary Collision ──────────────────────────────────────

def box_boundary_kernel(data, active, cvars, dt):
    """
    Contain particles within a box defined by control_vars.
    Reads `boundary_min` and `boundary_max` (3-tuples).
    """
    bmin = np.array(cvars.get("boundary_min", (-10000, -10000, -1000)), dtype=np.float32)
    bmax = np.array(cvars.get("boundary_max", (10000, 10000, 10000)), dtype=np.float32)
    restitution = cvars.get("boundary_restitution", 0.3)

    pos = data[:, 0:3]
    vel = data[:, 3:6]

    for axis in range(3):
        below = active & (pos[:, axis] < bmin[axis])
        above = active & (pos[:, axis] > bmax[axis])

        if below.any():
            pos[below, axis] = bmin[axis]
            vel[below, axis] = abs(vel[below, axis]) * restitution

        if above.any():
            pos[above, axis] = bmax[axis]
            vel[above, axis] = -abs(vel[above, axis]) * restitution


# ── Surface Accumulation (dust / sand settling) ─────────────────

def accumulation_kernel(data, active, cvars, dt):
    """
    Dust/sand particles accumulate on downward-facing surfaces.
    When a particle of type=dust or sand is nearly stationary near
    the ground, increment its prop0 (accumulation factor).
    Reads `accumulation_threshold` and `accumulation_rate` from control_vars.
    """
    threshold = cvars.get("accumulation_threshold", 5.0)    # max speed for "settled"
    rate = cvars.get("accumulation_rate", 0.05)              # per second

    types = data[:, COL["type"]]
    dust_code = PARTICLE_TYPES.get("dust", 0)
    sand_code = PARTICLE_TYPES.get("sand", 1)

    is_particulate = active & ((types == dust_code) | (types == sand_code))
    if not is_particulate.any():
        return

    speed = np.linalg.norm(data[is_particulate, C_VEL], axis=1)
    settled = speed < threshold

    if settled.any():
        settled_idx = np.where(is_particulate)[0][settled]
        data[settled_idx, COL["prop0"]] += rate * dt
        data[settled_idx, COL["alpha"]] = np.clip(
            data[settled_idx, COL["alpha"]] - 0.1 * dt, 0.0, 1.0
        )


# ── Temperature / Kinetic Energy ────────────────────────────────

def temperature_kernel(data, active, cvars, dt):
    """
    Track particle kinetic energy in prop1 (temperature proxy).
    Reads `ambient_temperature` from control_vars — particles
    drift toward ambient temperature over time.
    """
    ambient = cvars.get("ambient_temperature", 20.0)
    cooling_rate = cvars.get("cooling_rate", 0.5)

    if not active.any():
        return

    # Kinetic energy → temperature
    ke = 0.5 * data[active, COL["mass"]] * np.linalg.norm(
        data[active, C_VEL], axis=1
    ) ** 2
    # Bleed toward ambient
    current_temp = data[active, COL["prop1"]]
    data[active, COL["prop1"]] += (ambient - current_temp) * cooling_rate * dt
    # Add kinetic contribution
    data[active, COL["prop1"]] += ke * 0.01


# ── Color Over Lifetime ─────────────────────────────────────────

def color_lifetime_kernel(data, active, cvars, dt):
    """
    Fade particle alpha based on remaining life.
    Particles with life < 1.0 fade proportionally.
    """
    life = data[:, COL["life"]]
    # Only process mortal particles nearing death
    fading = active & (life > 0) & (life < 1.0)
    if fading.any():
        data[fading, COL["alpha"]] = np.clip(life[fading], 0.0, 1.0)
