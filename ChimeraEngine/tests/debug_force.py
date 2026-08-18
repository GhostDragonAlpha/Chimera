"""Debug script to understand GPU vs CPU force divergence."""
import sys
sys.path.insert(0, '.')
import numpy as np
from numba import cuda
from ChimeraEngine.core.field_physics_gpu import GPUFieldSystem, GPUSimulationConfig, _compute_forces_tiled_kernel
from ChimeraEngine.core.field_physics import FieldSystem, FieldElement
import math

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

# Sync GPU state to match CPU exactly
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

# Check device upload
d_pos_host = gpu_sys.d_pos.copy_to_host()
print("Device upload match:", np.allclose(d_pos_host, cpu_positions))

# Compute forces on both
cpu_forces = cpu_sys._compute_forces()  # float64
block = max(32, 64)
grid = int(math.ceil(n / block))
_compute_forces_tiled_kernel[grid, block](gpu_sys.d_pos, gpu_sys.d_mass, gpu_sys.d_charge, gpu_sys.d_forces, n)
cuda.synchronize()
gpu_forces = gpu_sys.d_forces.copy_to_host()

print("\nForce comparison:")
diff = np.linalg.norm(cpu_forces - gpu_forces, axis=1)
max_idx = int(np.argmax(diff))
print(f"Max force diff: {np.max(diff):.6f} at particle {max_idx}")
print(f"CPU force[{max_idx}]: {cpu_forces[max_idx]}")
print(f"GPU force[{max_idx}]: {gpu_forces[max_idx]}")
print(f"CPU pos[{max_idx}]: {cpu_positions[max_idx]}")
print(f"GPU pos[{max_idx}]: {d_pos_host[max_idx]}")

# Check distances between all pairs to find near-collisions
min_dist = float('inf')
min_pair = None
for i in range(n):
    for j in range(i+1, n):
        d = np.linalg.norm(cpu_positions[i] - cpu_positions[j])
        if d < min_dist:
            min_dist = d
            min_pair = (i, j)
print(f"\nClosest pair: {min_pair} at distance {min_dist:.6f}")

# Now run full step
cpu_sys.step(dt=1/120)
gpu_sys.step(dt=1/120)

cpu_pos = np.array([e.position for e in cpu_sys.elements])
gpu_pos = gpu_sys.buffer[:, 0:3]
diff_after = np.linalg.norm(cpu_pos - gpu_pos, axis=1)
max_idx_after = int(np.argmax(diff_after))
print(f"\nAfter step - max diff: {np.max(diff_after):.4f} at particle {max_idx_after}")
print(f"CPU pos[{max_idx_after}]: {cpu_pos[max_idx_after]}")
print(f"GPU pos[{max_idx_after}]: {gpu_pos[max_idx_after]}")
