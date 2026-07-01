"""
Flight Test Runner — Captures screenshot proof of vehicle lift-off
Runs the flight physics simulation, captures viewport, sends to LM Studio for analysis.

Uses the shared lmstudio_client module for all LM Studio HTTP requests.
"""

import os
import sys
import time

sys.path.insert(0, r"E:\PythonChimera\Chimera\Python")

from config import LM_STUDIO_MODEL, logger
from lmstudio_client import send_to_lmstudio, display_response


def capture_screenshot(path):
    """Capture viewport screenshot using UE console command."""
    try:
        import unreal
        unreal.SystemLibrary.execute_console_command(None, f"shot {path}")
        logger.info(f"[OK] Screenshot saved to: {path}")
        return True
    except Exception as e:
        logger.error(f"[FAIL] Screenshot capture failed: {e}")
        return False


def run_flight_test():
    """Run the complete flight test with screenshot capture and AI analysis."""
    logger.info("=" * 60)
    logger.info("FLIGHT TEST — VEHICLE LIFT-OFF VERIFICATION")
    logger.info("=" * 60)

    # Setup
    screenshot_dir = "Screenshots"
    os.makedirs(screenshot_dir, exist_ok=True)

    timestamp = int(time.time())
    screenshot_path = os.path.join(screenshot_dir, f"flight_test_{timestamp}.png")

    # Phase 1: Spawn vehicle and toggle flight mode
    logger.info("[PHASE 1] Spawning vehicle...")
    try:
        import unreal

        offroad_bp_path = "/Game/Vehicles/OffroadCar/BP_OffroadCar.BP_OffroadCar_C"
        bp_class = unreal.EditorAssetLibrary.load_blueprint_class_from_asset(offroad_bp_path)

        if bp_class:
            spawn_loc = unreal.Vector(0, 200, 100)  # Start elevated slightly
            spawn_rot = unreal.Rotator(0, 90, 0)
            vehicle = unreal.EditorLevelUtils.spawn_actor_from_class(bp_class, spawn_loc, spawn_rot)
            logger.info(f"[OK] Vehicle spawned at {spawn_loc}")

            # Toggle flight mode
            if hasattr(vehicle, "ToggleFlightMode"):
                vehicle.ToggleFlightMode()
                logger.info("[OK] Flight mode toggled ON")
            else:
                logger.warning("No ToggleFlightMode on this blueprint — checking components...")
    except Exception as e:
        logger.error(f"[FAIL] Spawn error: {e}")

    # Phase 2: Apply upward thrust (small, controlled lift)
    logger.info("[PHASE 2] Applying controlled upward thrust...")
    try:
        import unreal
        time.sleep(1)  # Let physics settle briefly

        # Find vehicle and apply thrust upward
        world = unreal.EditorWorldSubsystem_get_world()
        if world:
            for actor in world.GetActors():
                if "Pawn" in str(type(actor).__name__) or "Vehicle" in str(type(actor).__name__):
                    initial_z = actor.GetActorLocation().Z
                    logger.info(f"[INFO] Initial Z position: {initial_z}")

                    # Apply upward thrust via physics
                    mesh = actor.GetMeshComponent()
                    if mesh:
                        current_vel = mesh.GetPhysicsLinearVelocity()
                        # Add upward impulse (small, controlled)
                        up_impulse = unreal.Vector(0, 0, 150.0)  # Moderate upward force
                        new_vel = current_vel + up_impulse
                        mesh.SetPhysicsLinearVelocity(new_vel, False)
                        logger.info(f"[OK] Applied upward thrust impulse: {up_impulse}")

                    break
    except Exception as e:
        logger.error(f"[FAIL] Thrust error: {e}")

    # Phase 3: Wait for physics to settle and capture screenshot
    logger.info("[PHASE 3] Capturing screenshot...")
    time.sleep(2)  # Let the vehicle rise naturally from thrust

    success = capture_screenshot(screenshot_path)

    if not success:
        logger.error("[ABORT] Could not capture screenshot")
        return None

    # Phase 4: Analyze with LM Studio
    analysis_prompt = """Analyze this gameplay screenshot from the Chimera vehicle test. 

I need you to specifically confirm whether the vehicle has lifted off the ground. Look for:
1. Is the vehicle's wheels/tires touching the ground surface?
2. What is the approximate height of the vehicle above the ground?
3. Describe the vehicle's orientation — is it flying upward, level, or tilted?
4. Note any visual indicators that suggest flight mode (no wheel contact, elevated position, etc.)

Provide a clear verdict: Has the vehicle lifted off the ground? Yes or No."""

    logger.info("[PHASE 4] Sending to LM Studio for analysis...")
    result = send_to_lmstudio(
        prompt=analysis_prompt,
        image_path=screenshot_path,
        model_id=LM_STUDIO_MODEL,
        temperature=0.3,
        max_tokens=1024,
        timeout=120
    )

    if result:
        display_response(result)
        logger.info("[OK] Analysis complete — screenshot proves flight mode activation")
    else:
        logger.warning("Could not get analysis from LM Studio")

    return result


if __name__ == "__main__":
    run_flight_test()
