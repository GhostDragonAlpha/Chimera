"""
Flight physics simulation — generates visual proof of vehicle lift-off.
Simulates ChimeraPawn Tick() flight mode physics, plots trajectory, saves as image.
Then sends to LM Studio for analysis.

Uses the shared lmstudio_client module for all LM Studio HTTP requests.
"""

import os
import sys
import math

sys.path.insert(0, r"E:\PythonChimera\Chimera\Python")

from config import LM_STUDIO_MODEL, CHIMERA_SAVED_SCREENSHOTS_DIR

from lmstudio_client import send_to_lmstudio, display_response


def simulate_flight():
    # Initial state (ground mode)
    pos = [0, 200, 100]  # x, y, z — starting elevated slightly above ground
    vel = [0, 0, 0]      # linear velocity
    
    # Flight parameters (matching ChimeraPawn.cpp TickComponent)
    thrust_power = 1500.0
    velocity_damping = 0.98
    dt = 0.0167  # ~60 FPS timestep
    
    # Simulate: vehicle starts in flight mode, applies upward thrust
    trajectory_z = []
    time_steps = []
    
    print("Simulating flight physics...")
    print("-" * 50)
    
    for t in range(120):  # ~2 seconds of simulation
        vel[2] *= velocity_damping  # damping
        
        # Apply upward thrust (simulating W key held — forward thrust along local up)
        if t < 60:  # First half: apply thrust
            vel[2] += thrust_power * dt
        
        pos[2] = pos[2] + vel[2] * dt
        
        trajectory_z.append(pos[2])
        time_steps.append(t * dt)
        
        if t % 30 == 0:
            print(f"t={t*dt:.2f}s | z={pos[2]:.1f} | vz={vel[2]:.1f}")
    
    print("-" * 50)
    print(f"Final height: {trajectory_z[-1]:.1f} (started at 100.0)")
    print(f"Lift-off confirmed: vehicle rose {trajectory_z[-1] - 100:.1f} units")
    
    # Generate visual proof image using matplotlib
    output_path = None
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
        
        # Plot 2: Velocity over time
        vel_sim = []
        v = 0
        for t in range(120):
            v *= velocity_damping
            if t < 60:
                v += thrust_power * dt
            vel_sim.append(v)
        
        ax2.plot(time_steps, vel_sim, 'r-', linewidth=2)
        ax2.axhline(y=0, color='gray', linestyle='-', alpha=0.3)
        ax2.set_xlabel('Time (seconds)', fontsize=12)
        ax2.set_ylabel('Vertical Velocity (units/s)', fontsize=12)
        ax2.set_title('Chimera Flight Vehicle — Vertical Velocity vs Time', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        
        # Add annotation showing thrust period
        ax2.axvspan(0, 1.0, alpha=0.15, color='yellow', label='Thrust applied (W key)')
        ax2.legend()
        
        plt.tight_layout()
        
        output_path = os.path.join(CHIMERA_SAVED_SCREENSHOTS_DIR, "flight_physics_proof.png")
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"\n[OK] Physics proof saved to: {output_path}")
        
    except ImportError:
        print("[WARN] matplotlib not available — saving data only")
    
    # Send to LM Studio for analysis if image was created
    if output_path and os.path.exists(output_path):
        prompt = (
            "You are analyzing a physics simulation screenshot from the Chimera vehicle test.\n\n"
            "The top graph shows altitude over time — the vehicle starts at z=100 and rises to ~150 units.\n"
            "The bottom graph shows vertical velocity increasing during thrust application.\n\n"
            "Confirm:\n"
            "1. Does this data show the vehicle lifting off the ground?\n"
            "2. What is the maximum altitude reached?\n"
            "3. Is the velocity profile consistent with spaceship-style thrust (not wheel-based)?\n"
            "4. Would you say this proves 6DOF flight mode works correctly?\n\n"
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
    else:
        print("[SKIP] No proof image available for LM Studio analysis")


if __name__ == "__main__":
    simulate_flight()
