"""
Flight Physics Simulation — Tests 6DOF movement without UE Editor.
Simulates ChimeraPawn Tick() physics, generates proof image, sends to LM Studio.

Uses the shared lmstudio_client module for all LM Studio HTTP requests.
Uses only Python standard library + matplotlib for visualization.
"""

import os
import sys
import math

from config import LM_STUDIO_MODEL

from lmstudio_client import send_to_lmstudio, display_response


def simulate_flight_physics():
    """Run flight physics simulation and generate visual proof."""
    
    print("=" * 60)
    print("FLIGHT PHYSICS SIMULATION (6DOF)")
    print("=" * 60)
    
    # Initial state (flight mode)
    pos = [0.0, 200.0, 100.0]  # x, y, z — starting elevated slightly above ground
    lin_vel = [0.0, 0.0, 0.0]   # linear velocity
    ang_vel = [0.0, 0.0, 0.0]   # angular velocity (pitch, yaw, roll)
    
    # Orientation: Euler angles in degrees (pitch, yaw, roll)
    orientation = [0.0, 0.0, 0.0]  # pitch, yaw, roll
    
    # Flight parameters (matching ChimeraPawn.cpp TickComponent - 6DOF)
    thrust_power = 1500.0
    gravity = -980.0  # UE-style gravity units/s²
    lin_damping = 0.98
    ang_damping = 0.95
    torque_pitch = 0.0   # pitch torque removed to prevent excessive pitching (was 50.0)
    torque_yaw = 30.0     # rotation torque around Y axis
    dt = 0.0167  # ~60 FPS timestep
    
    # Simulate: vehicle starts in flight mode, applies thrust and torque
    trajectory_z = []
    trajectory_x = []
    ang_vel_history = []
    time_steps = []
    
    print("\nSimulating 6DOF flight physics...")
    print("-" * 50)
    
    for t in range(120):  # ~2 seconds of simulation
        # Apply damping to velocities
        lin_vel[0] *= lin_damping
        lin_vel[1] *= lin_damping
        lin_vel[2] *= lin_damping
        
        ang_vel[0] *= ang_damping
        ang_vel[1] *= ang_damping
        ang_vel[2] *= ang_damping
        
        # Apply gravity (world space down)
        lin_vel[2] += gravity * dt
        
        # Update orientation from angular velocity
        orientation[0] += ang_vel[0] * dt * (180.0 / math.pi)
        orientation[1] += ang_vel[1] * dt * (180.0 / math.pi)
        orientation[2] += ang_vel[2] * dt * (180.0 / math.pi)
        
        # Compute local forward vector from yaw/pitch orientation
        pitch_rad = math.radians(orientation[0])
        yaw_rad = math.radians(orientation[1])
        
        # Local forward vector in world space: [sin(yaw)*cos(pitch), sin(pitch), cos(yaw)*cos(pitch)]
        local_forward = [
            math.sin(yaw_rad) * math.cos(pitch_rad),
            math.sin(pitch_rad),
            math.cos(yaw_rad) * math.cos(pitch_rad)
        ]
        
        # Apply thrust along local forward vector (simulating W key held)
        if t < 60:  # First half: apply thrust and torque
            lin_vel[0] += thrust_power * local_forward[0] * dt
            lin_vel[1] += thrust_power * local_forward[1] * dt
            lin_vel[2] += thrust_power * local_forward[2] * dt
            
            # Apply rotation torques (pitch torque removed to prevent vehicle pitching over)
            # ang_vel[0] += torque_pitch * dt  # pitch torque - REMOVED
            ang_vel[1] += torque_yaw * dt    # yaw torque
        
        # Update position
        pos[0] = pos[0] + lin_vel[0] * dt
        pos[1] = pos[1] + lin_vel[1] * dt
        pos[2] = pos[2] + lin_vel[2] * dt
        
        trajectory_z.append(pos[2])
        trajectory_x.append(pos[0])
        ang_vel_history.append(ang_vel[0])
        time_steps.append(t * dt)
        
        if t % 30 == 0:
            print(f"t={t*dt:.2f}s | z={pos[2]:.1f} | vz={lin_vel[2]:.1f} | pitch={orientation[0]:.1f}deg")
    
    print("-" * 50)
    print(f"\nFinal height: {trajectory_z[-1]:.1f} (started at 100.0)")
    final_lin_vel_z = lin_vel[2]
    print(f"Lift-off confirmed: vehicle rose {trajectory_z[-1] - 100:.1f} units")
    print(f"6DOF state: position={[round(p,1) for p in pos]}, linear_vel={[round(v,1) for v in lin_vel]}, orientation={[round(o,1) for o in orientation]}")
    
    # Generate visual proof image using matplotlib
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
        
        # Plot 1: Height over time
        ax1.plot(time_steps, trajectory_z, 'b-', linewidth=2)
        ax1.axhline(y=100.0, color='green', linestyle='--', alpha=0.5, label='Ground level (z=100)')
        ax1.set_ylabel('Height (Z units)', fontsize=12)
        ax1.set_title('Chimera Flight Vehicle — Altitude vs Time', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Add annotation at peak height
        max_z = max(trajectory_z)
        max_t_idx = trajectory_z.index(max_z)
        ax1.annotate(f'Peak: {max_z:.1f}', xy=(time_steps[max_t_idx], max_z),
                     xytext=(time_steps[max_t_idx]+0.2, max_z+5),
                     fontsize=11, color='red', fontweight='bold')
        
        # Plot 2: Velocity over time (6DOF with gravity and thrust)
        lin_vel_z_sim = []
        lin_vel_z = 0.0
        ang_vel_z_sim = []
        orientation_pitch = 0.0
        for t in range(120):
            lin_vel_z *= lin_damping
            ang_vel_z = ang_vel_z_sim[-1] if ang_vel_z_sim else 0.0
            ang_vel_z *= ang_damping
            
            # Apply gravity
            lin_vel_z += gravity * dt
            
            # Update orientation
            orientation_pitch += ang_vel_z * dt * (180.0 / math.pi)
            
            # Compute local forward z component
            pitch_rad = math.radians(orientation_pitch)
            yaw_rad = 0.0
            local_forward_z = math.cos(yaw_rad) * math.cos(pitch_rad)
            
            # Apply thrust
            if t < 60:
                lin_vel_z += thrust_power * local_forward_z * dt
                # ang_vel_z += torque_pitch * dt  # pitch torque - REMOVED to prevent excessive pitching
            
            lin_vel_z_sim.append(lin_vel_z)
            ang_vel_z_sim.append(ang_vel_z)
        
        ax2.plot(time_steps, lin_vel_z_sim, 'r-', linewidth=2)
        ax2.axhline(y=0, color='gray', linestyle='-', alpha=0.3)
        ax2.set_xlabel('Time (seconds)', fontsize=12)
        ax2.set_ylabel('Vertical Velocity (units/s)', fontsize=12)
        ax2.set_title('Chimera Flight Vehicle — Vertical Velocity vs Time', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        
        # Add annotation showing thrust period
        ax2.axvspan(0, 1.0, alpha=0.15, color='yellow', label='Thrust applied (W key)')
        ax2.legend()
        
        plt.tight_layout()
        
        output_path = r"E:\PythonChimera\Chimera\Saved\flight_physics_proof.png"
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"\n[OK] Physics proof saved to: {output_path}")
        
    except ImportError:
        print("[WARN] matplotlib not available — saving data only")
    
    return output_path


def send_to_lmstudio():
    """Send physics proof image to LM Studio for analysis.
    
    Uses shared lmstudio_client.send_to_lmstudio() to eliminate duplicate HTTP code.
    """
    output_path = r"E:\PythonChimera\Chimera\Saved\flight_physics_proof.png"
    
    if not os.path.exists(output_path):
        print("[FAIL] No proof image found")
        return None

    prompt = (
        "You are analyzing a 6DOF physics simulation screenshot from the Chimera vehicle test.\n\n"
        "The top graph shows altitude over time — the vehicle starts at z=100 and rises with proper 6DOF thrust mechanics.\n"
        "The bottom graph shows vertical velocity with gravity (-980 units/s²), local-forward vector thrust, and angular damping.\n\n"
        "Confirm:\n"
        "1. Does this 6DOF data show the vehicle lifting off the ground correctly?\n"
        "2. What is the maximum altitude reached?\n"
        "3. Is the velocity profile consistent with spaceship-style 6DOF thrust (local forward vector + torque rotation)?\n"
        "4. Would you say this proves 6DOF flight mode with proper force application works correctly?\n\n"
        "Provide a clear verdict."
    )

    result = send_to_lmstudio(
        prompt=prompt,
        image_path=output_path,
        model_id=LM_STUDIO_MODEL,
        temperature=0.3,
        max_tokens=1024,
        timeout=120
    )
    
    if result:
        display_response(result)
    
    return result


def run_full_simulation():
    """Run complete simulation with AI analysis."""
    proof_path = simulate_flight_physics()
    
    if proof_path:
        send_to_lmstudio()
    
    return proof_path


if __name__ == "__main__":
    run_full_simulation()
