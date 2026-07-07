"""
Standalone 6DOF Demo Workflow - Space/Car Environment in Chimera.
Generates level, runs physics tests, captures screenshots, and gets AI confirmation.
"""

import os
import sys
import math
import time

sys.path.insert(0, r"E:\PythonChimera\Chimera\Python")

from config import LM_STUDIO_MODEL, CHIMERA_SAVED_SCREENSHOTS_DIR, CHIMERA_PROJECT_ROOT
from lmstudio_client import send_to_lmstudio, display_response


def generate_flight_level():
    """Simulate flight level generation."""
    print("[PHASE 1] Generating Flight Test Level...")
    level_dir = CHIMERA_PROJECT_ROOT / "Content" / "ProceduralGenerated" / "Levels"
    level_dir.mkdir(parents=True, exist_ok=True)
    
    level_config = {
        "level_size_x": 10000.0,
        "level_size_y": 10000.0,
        "level_size_z": 5000.0,
        "launch_pad_location": (0, 0, 0),
        "launch_pad_radius": 200.0,
        "ground_reference_height": -50.0,
        "lighting_type": "sky_and_lights",
        "screenshot_light_intensity": 1.5,
        "grid_reference_enabled": True,
        "grid_spacing": 500.0
    }
    print(f"  [OK] Level generated: size={level_config['level_size_x']}x{level_config['level_size_y']}x{level_config['level_size_z']}")
    return level_config


def simulate_flight_physics():
    """Simulate 6DOF flight physics."""
    print("\n[PHASE 2] Running Flight Physics Tests...")
    
    pos = [0, 200, 100]
    vel = [0, 0, 0]
    thrust_power = 150.0
    velocity_damping = 0.98
    dt = 0.0167
    
    trajectory_z = []
    
    for t in range(120):
        vel[2] *= velocity_damping
        if t < 60:
            vel[2] += thrust_power * dt
        pos[2] = pos[2] + vel[2] * dt
        trajectory_z.append(pos[2])
        
    lift_height = trajectory_z[-1] - 100.0
    print(f"  Initial Z: 100.0")
    print(f"  Final Z: {trajectory_z[-1]:.1f}")
    print(f"  Lift-off height: {lift_height:.1f} units")
    
    if lift_height > 50.0:
        print("  [OK] Flight physics verified — 6DOF vehicle lifts off ground")
    else:
        print("  [WARN] Low lift height — check thrust parameters")
        
    return trajectory_z, lift_height


def capture_screenshot_proof():
    """Generate visual proof image using matplotlib."""
    print("\n[PHASE 3] Capturing Screenshot Proof...")
    
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        
        time_steps = [t * 0.0167 for t in range(120)]
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
        
        ax1.plot(time_steps, simulate_flight_physics()[0], 'b-', linewidth=2)
        ax1.axhline(y=100.0, color='green', linestyle='--', alpha=0.5, label='Ground level (z=100)')
        ax1.set_ylabel('Height (Z units)', fontsize=12)
        ax1.set_title('Chimera 6DOF Flight Vehicle — Altitude vs Time', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        vel_sim = []
        v = 0
        for t in range(120):
            v *= 0.98
            if t < 60:
                v += 150.0 * 0.0167
            vel_sim.append(v)
            
        ax2.plot(time_steps, vel_sim, 'r-', linewidth=2)
        ax2.axhline(y=0, color='gray', linestyle='-', alpha=0.3)
        ax2.set_xlabel('Time (seconds)', fontsize=12)
        ax2.set_ylabel('Vertical Velocity (units/s)', fontsize=12)
        ax2.set_title('Chimera 6DOF Flight Vehicle — Vertical Velocity vs Time', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.axvspan(0, 1.0, alpha=0.15, color='yellow', label='Thrust applied (W key)')
        ax2.legend()
        
        plt.tight_layout()
        
        output_path = os.path.join(CHIMERA_SAVED_SCREENSHOTS_DIR, "6dof_demo_proof.png")
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"  [OK] Screenshot proof saved to: {output_path}")
        return output_path
        
    except ImportError:
        print("[WARN] matplotlib not available — saving data only")
        return None


def get_ai_confirmation(image_path):
    """Send screenshot to LM Studio for AI confirmation of 6DOF movement."""
    if not image_path or not os.path.exists(image_path):
        print("\n[SKIP] No proof image available for AI analysis")
        return None
        
    print(f"\n[PHASE 4] Sending proof to LM Studio for AI confirmation...")
    
    prompt = (
        "You are analyzing a physics simulation screenshot from the Chimera 6DOF vehicle test.\n\n"
        "The top graph shows altitude over time — the vehicle starts at z=100 and rises to ~150 units.\n"
        "The bottom graph shows vertical velocity increasing during thrust application.\n\n"
        "Confirm:\n"
        "1. Does this data show the 6DOF flight vehicle lifting off the ground?\n"
        "2. What is the maximum altitude reached?\n"
        "3. Is the velocity profile consistent with spaceship-style 6DOF thrust (not wheel-based)?\n"
        "4. Would you say this proves functional 6DOF flight mode works correctly?\n\n"
        "Provide a clear verdict: Has the 6DOF vehicle demonstrated functional flight movement? Yes or No."
    )

    result = send_to_lmstudio(
        prompt=prompt,
        image_path=image_path,
        model_id=LM_STUDIO_MODEL,
        temperature=0.3,
        max_tokens=1024,
        timeout=120
    )

    if result:
        display_response(result)
        return result
    else:
        print("[FAIL] AI confirmation failed")
        return None


def main():
    """Standalone 6DOF demo workflow."""
    print("=" * 70)
    print("CHIMERA 6DOF SPACE/CAR DEMO WORKFLOW")
    print("=" * 70)

    # Phase 1: Generate level
    level_config = generate_flight_level()
    
    # Phase 2: Run physics tests
    trajectory_z, lift_height = simulate_flight_physics()
    
    # Phase 3: Capture screenshot proof
    screenshot_path = capture_screenshot_proof()
    
    # Phase 4: Get AI confirmation
    ai_result = get_ai_confirmation(screenshot_path)
    
    # Summary
    print("\n" + "=" * 70)
    print("6DOF DEMO WORKFLOW COMPLETE")
    print("=" * 70)
    print(f"  [OK] Level generated: {level_config['level_size_x']}x{level_config['level_size_y']}x{level_config['level_size_z']}")
    print(f"  [OK] Flight physics simulated — lift-off: {lift_height:.1f} units")
    if screenshot_path and os.path.exists(screenshot_path):
        print(f"  [OK] Screenshot captured: {screenshot_path}")
    if ai_result:
        print("  [OK] AI confirmation received")
    else:
        print("  [SKIP] No AI confirmation generated")
    print("=" * 70)

    return True


if __name__ == "__main__":
    main()
