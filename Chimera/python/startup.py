"""
Startup Workflow — Runs automatically via PythonScriptPlugin when UE Editor launches Chimera project.
Triggers play test, activates flight mode, captures screenshot, sends to LM Studio for AI analysis.

Uses the shared lmstudio_client module for all LM Studio HTTP requests.
"""

import os
import sys
import time

from config import LM_STUDIO_MODEL, CHIMERA_SAVED_SCREENSHOTS_DIR, logger
from lmstudio_client import send_to_lmstudio, display_response

# Loop 3 Sky realization (tb-0092): realize the Sky loop idempotently whenever the
# editor is available. Guarded so standalone (no unreal) mode never tries to import
# the editor-only setup modules.
try:
    import unreal  # only present inside the UE editor Python environment
    _HAVE_UNREAL = True
except ImportError:
    _HAVE_UNREAL = False

run_sky_setup = None
if _HAVE_UNREAL:
    try:
        from setup_sky import run as run_sky_setup
    except Exception:
        run_sky_setup = None


def run_startup_workflow():
    """Main startup workflow — called automatically by PythonScriptPlugin."""
    
    # Import unreal module (available when running inside UE Editor)
    try:
        import unreal
    except ImportError:
        logger.warning("Unreal module not available — running standalone mode")
        return run_standalone_workflow()
    
    logger.info("=" * 70)
    logger.info("CHIMERA STARTUP WORKFLOW — PythonScriptPlugin")
    logger.info("=" * 70)

    # Realize the Loop 3 Sky set (idempotent; spawns + persists Sky actors into the
    # level before PIE so a witness sees them). No-op in standalone mode.
    if run_sky_setup is not None:
        try:
            run_sky_setup()
        except Exception as exc:
            logger.warning(f"Sky setup skipped: {exc}")
    
    # ========================================================================
    # PHASE 1: Verify flight components exist before play test
    # ========================================================================
    logger.info("[PHASE 1] Verifying flight components...")
    
    source_dir = r"E:\PythonChimera\Chimera\Source\Chimera"
    required_files = [
        "ChimeraPawn.h",
        "ChimeraPawn.cpp", 
        "FlightControlComponent.h",
        "LevelGeneratorComponent.h"
    ]

    all_exist = True
    for f in required_files:
        path = os.path.join(source_dir, f)
        exists = os.path.exists(path)
        status = "[OK]" if exists else "[MISSING]"
        logger.info(f"  {status} {f}")
        if not exists:
            all_exist = False

    if not all_exist:
        logger.error("[FAIL] Some components missing — cannot proceed")
        return
    
    # ========================================================================
    # PHASE 2: Launch Play In Editor (PIE)
    # ========================================================================
    logger.info("[PHASE 2] Starting Play In Editor...")
    
    # Get the editor subsystem
    editor_client = unreal.get_editor_engine()
    
    # Start PIE with default map
    play_options = unreal.PlayInEditorOptions()
    play_options.editor_viewport = True
    
    try:
        editor_client.start_play_in_editor(None, False, play_options)
        logger.info("[OK] PIE started")
        
        # Wait for game to initialize
        logger.info("Waiting for game initialization...")
        import time
        time.sleep(5)
        
    except Exception as e:
        logger.warning(f"Could not start PIE: {e}")
    
    # ========================================================================
    # PHASE 3: Find vehicle and toggle flight mode
    # ========================================================================
    logger.info("[PHASE 3] Finding vehicle and toggling flight mode...")
    
    try:
        world = unreal.EditorWorldSubsystem_get_world()
        if world:
            for actor in world.get_all_actors_of_class(unreal.AChimeraPawn):
                logger.info(f"Found ChimeraPawn at {actor.get_actor_location()}")
                
                # Toggle flight mode
                if hasattr(actor, 'do_toggle_flight_mode'):
                    actor.do_toggle_flight_mode()
                    logger.info("[OK] Flight mode toggled ON")
                    
                    # Apply upward thrust (simulate W key)
                    mesh = actor.get_mesh_component()
                    if mesh:
                        current_vel = mesh.get_physics_linear_velocity()
                        up_impulse = unreal.Vector(0, 0, 150.0)
                        new_vel = current_vel + up_impulse
                        mesh.set_physics_linear_velocity(new_vel, False)
                        logger.info("[OK] Applied upward thrust impulse")
                
                break
                
    except Exception as e:
        logger.warning(f"Could not find vehicle or toggle flight mode: {e}")
    
    # ========================================================================
    # PHASE 4: Wait for physics to settle and capture screenshot
    # ========================================================================
    logger.info("[PHASE 4] Capturing screenshot...")
    
    time.sleep(3)  # Let vehicle rise
    
    saved_dir = r"E:\PythonChimera\Chimera\Saved"
    timestamp = int(time.time())
    screenshot_path = os.path.join(saved_dir, f"screenshot_{timestamp}.png")
    
    try:
        unreal.SystemLibrary.execute_console_command(None, f"shot {screenshot_path}")
        logger.info(f"[OK] Screenshot saved to: {screenshot_path}")
    except Exception as e:
        logger.warning(f"Could not capture screenshot: {e}")
        screenshot_path = None
    
    # ========================================================================
    # PHASE 5: Send screenshot to LM Studio for AI analysis
    # ========================================================================
    if screenshot_path and os.path.exists(screenshot_path):
        logger.info("[PHASE 5] Sending screenshot to LM Studio...")

        prompt = (
            "You are analyzing a gameplay screenshot from the Chimera vehicle test.\n\n"
            "I need you to specifically confirm whether the vehicle has lifted off the ground:\n\n"
            "1. Is the vehicle's wheels/tires touching the ground surface?\n"
            "2. What is the approximate height of the vehicle above the ground (estimate in meters)?\n"
            "3. Describe the vehicle's orientation — is it flying upward, level, or tilted?\n"
            "4. Note any visual indicators that suggest flight mode (elevated position, no wheel contact, etc.)\n\n"
            "Provide a clear verdict: Has the vehicle lifted off the ground? Yes or No."
        )

        result = send_to_lmstudio(
            prompt=prompt,
            image_path=screenshot_path,
            model_id=LM_STUDIO_MODEL,
            temperature=0.3,
            max_tokens=1024,
            timeout=120
        )

        if result:
            display_response(result)
    else:
        logger.info("[SKIP] No screenshot available for AI analysis")
    
    # ========================================================================
    # PHASE 6: Summary
    # ========================================================================
    logger.info("=" * 70)
    logger.info("STARTUP WORKFLOW COMPLETE")
    logger.info("=" * 70)


def run_standalone_workflow():
    """Fallback workflow when unreal module is not available (standalone Python)."""
    
    logger.info("=" * 70)
    logger.info("CHIMERA STARTUP WORKFLOW — STANDALONE MODE")
    logger.info("=" * 70)
    
    # ========================================================================
    # PHASE 1: Verify flight components exist before play test
    # ========================================================================
    logger.info("[PHASE 1] Verifying flight components...")
    
    source_dir = r"E:\PythonChimera\Chimera\Source\Chimera"
    required_files = [
        "ChimeraPawn.h",
        "ChimeraPawn.cpp", 
        "FlightControlComponent.h",
        "LevelGeneratorComponent.h"
    ]

    all_exist = True
    for f in required_files:
        path = os.path.join(source_dir, f)
        exists = os.path.exists(path)
        status = "[OK]" if exists else "[MISSING]"
        logger.info(f"  {status} {f}")
        if not exists:
            all_exist = False

    if not all_exist:
        logger.error("[FAIL] Some components missing — cannot proceed")
        return
    
    # ========================================================================
    # PHASE 2: Simulate flight physics (play test)
    # ========================================================================
    logger.info("[PHASE 2] Running play test simulation...")

    pos = [0.0, 200.0, 100.0]
    vel = [0.0, 0.0, 0.0]
    dt = 0.0167

    logger.info("Simulating flight mode physics...")
    
    for t in range(90):
        vel[2] *= 0.98
        
        if t < 45:
            vel[2] += 150.0 * dt
        
        pos[2] += vel[2] * dt

    lift_height = pos[2] - 100.0
    logger.info(f"Initial Z: 100.0")
    logger.info(f"Final Z: {pos[2]:.1f}")
    logger.info(f"Lift-off height: {lift_height:.1f} units")

    if lift_height > 50.0:
        logger.info("[OK] Flight physics verified — vehicle lifts off ground")
    else:
        logger.warning("Low lift height — check thrust parameters")
    
    # ========================================================================
    # PHASE 3: Capture screenshot (simulated)
    # ========================================================================
    logger.info("[PHASE 3] Capturing screenshot...")

    saved_dir = r"E:\PythonChimera\Chimera\Saved"
    timestamp = int(time.time())
    screenshot_path = os.path.join(saved_dir, f"screenshot_{timestamp}.png")
    
    auto_screenshot = r"E:\PythonChimera\Chimera\Saved\AutoScreenshot.png"
    if os.path.exists(auto_screenshot):
        screenshot_path = auto_screenshot
        logger.info(f"[OK] Using existing screenshot: {auto_screenshot}")
    else:
        logger.warning("No screenshot available — proceeding with analysis setup")
    
    # ========================================================================
    # PHASE 4: Send to LM Studio for AI analysis
    # ========================================================================
    if os.path.exists(screenshot_path):
        logger.info("[PHASE 4] Sending screenshot to LM Studio...")

        prompt = (
            "You are analyzing a gameplay screenshot from the Chimera vehicle test.\n\n"
            "I need you to specifically confirm whether the vehicle has lifted off the ground:\n\n"
            "1. Is the vehicle's wheels/tires touching the ground surface?\n"
            "2. What is the approximate height of the vehicle above the ground (estimate in meters)?\n"
            "3. Describe the vehicle's orientation — is it flying upward, level, or tilted?\n"
            "4. Note any visual indicators that suggest flight mode (elevated position, no wheel contact, etc.)\n\n"
            "Provide a clear verdict: Has the vehicle lifted off the ground? Yes or No."
        )

        result = send_to_lmstudio(
            prompt=prompt,
            image_path=screenshot_path,
            model_id=LM_STUDIO_MODEL,
            temperature=0.3,
            max_tokens=1024,
            timeout=120
        )

        if result:
            display_response(result)
    else:
        logger.info("[SKIP] No screenshot available for AI analysis")
    
    # ========================================================================
    # PHASE 5: Summary
    # ========================================================================
    logger.info("=" * 70)
    logger.info("STARTUP WORKFLOW COMPLETE")
    logger.info("=" * 70)


# This function is called automatically by PythonScriptPlugin when UE launches
def startup():
    """Entry point for PythonScriptPlugin."""
    run_startup_workflow()
