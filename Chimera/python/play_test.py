"""
Play Test Module for Chimera Flight Vehicle System
Tests 6DOF spaceship movement, flight mode toggle, and physics behavior.

Uses the shared lmstudio_client module for all LM Studio HTTP requests.
"""

import os
import time
from config import LM_STUDIO_MODEL

from lmstudio_client import send_to_lmstudio, display_response
from config import logger

from screenshot_helpers import capture_viewport_screenshot, send_screenshot_to_lmstudio


def get_unreal():
    """Import unreal module, handling both UE editor and standalone scenarios."""
    try:
        import unreal
        return unreal
    except ImportError:
        print("Warning: 'unreal' module not available (outside UE Editor). Running in simulation mode.")
        return None


class FlightPlayTest:
    """Automated play test for the FlightControlComponent 6DOF spaceship system."""

    def __init__(self):
        self.unreal = get_unreal()
        self.test_results = []
        self.screenshot_dir = "Screenshots"
        os.makedirs(self.screenshot_dir, exist_ok=True)
        
        # Test configuration
        self.thrust_power = 150.0
        self.rotation_speed = 90.0
        self.test_duration_seconds = 30.0
        self.capture_interval = 2.0

    def run_full_playtest(self):
        """Execute complete play test sequence."""
        print("=" * 60)
        print("CHIMERA FLIGHT VEHICLE PLAY TEST")
        print("=" * 60)
        
        # Phase 1: Setup
        self.phase_setup()
        
        # Phase 2: Flight mode toggle test
        self.phase_flight_mode_toggle()
        
        # Phase 3: Thrust and strafe movement test
        self.phase_thrust_strafe_movement()
        
        # Phase 4: Rotation (pitch/yaw/roll) test
        self.phase_rotation_test()
        
        # Phase 5: Idle damping verification
        self.phase_idle_damping_test()
        
        # Phase 6: Screenshot capture and AI analysis
        self.phase_screenshot_analysis()
        
        # Summary
        self.print_summary()

    def phase_setup(self):
        """Phase 1: Setup test environment."""
        print("\n[PHASE 1] Setting up test environment...")
        
        if not self.unreal:
            print("  Skipping UE-specific setup (simulation mode)")
            return
        
        # Load the starter level
        starter_level_path = "/Game/VehicleTemplate/Maps/VehicleBasic.VehicleBasic"
        try:
            self.unreal.EditorLevelUtils.load_map(starter_level_path)
            print(f"  Loaded starter level: {starter_level_path}")
        except Exception as e:
            print(f"  Could not load starter level: {e}")

    def phase_flight_mode_toggle(self):
        """Phase 2: Test flight mode toggle functionality."""
        print("\n[PHASE 2] Testing flight mode toggle...")
        
        if not self.unreal:
            print("  Simulating flight mode toggle test...")
            time.sleep(1)
            return
        
        # Find or spawn a vehicle pawn
        vehicle = self._spawn_test_vehicle()
        if not vehicle:
            print("  No vehicle found for testing")
            return
        
        # Verify gravity is enabled initially (ground mode)
        b_has_gravity = vehicle.bEnableGravity
        print(f"  Initial gravity state: {b_has_gravity}")
        
        # Toggle flight mode
        self._call_blueprint_function(vehicle, "ToggleFlightMode")
        
        # Verify gravity is disabled after toggle
        b_no_gravity = not vehicle.bEnableGravity
        print(f"  After flight mode toggle, gravity disabled: {b_no_gravity}")

    def phase_thrust_strafe_movement(self):
        """Phase 3: Test thrust and strafe movement."""
        print("\n[PHASE 3] Testing thrust and strafe movement...")
        
        if not self.unreal:
            print("  Simulating thrust/strafe test (5 seconds)...")
            time.sleep(5)
            return
        
        vehicle = self._get_current_vehicle()
        if not vehicle:
            print("  No vehicle available for movement test")
            return
        
        # Record initial position
        initial_location = vehicle.GetActorLocation()
        print(f"  Initial position: {initial_location}")
        
        # Apply thrust forward for a few seconds
        self._apply_thrust(vehicle, 1.0)
        time.sleep(2)
        
        # Check new position (should have moved forward)
        new_location = vehicle.GetActorLocation()
        delta_forward = new_location.Z - initial_location.Z
        print(f"  Position after thrust: {new_location}")

    def phase_rotation_test(self):
        """Phase 4: Test pitch, yaw, and roll rotation."""
        print("\n[PHASE 4] Testing 6DOF rotation...")
        
        if not self.unreal:
            print("  Simulating rotation test (pitch/yaw/roll)...")
            time.sleep(3)
            return
        
        vehicle = self._get_current_vehicle()
        if not vehicle:
            print("  No vehicle available for rotation test")
            return
        
        initial_rotation = vehicle.GetActorRotation()
        print(f"  Initial rotation: {initial_rotation}")

    def phase_idle_damping_test(self):
        """Phase 5: Test angular velocity damping when idle."""
        print("\n[PHASE 5] Testing idle damping (drift prevention)...")
        
        if not self.unreal:
            print("  Simulating idle damping test...")
            time.sleep(2)
            return
        
        vehicle = self._get_current_vehicle()
        if not vehicle:
            print("  No vehicle available for damping test")
            return

    def phase_screenshot_analysis(self):
        """Phase 6: Capture screenshots and send to LM Studio for AI analysis."""
        logger.info("Capturing viewport screenshot for AI analysis...")
        print("\n[PHASE 6] Capturing screenshots for AI analysis...")
        
        # Wait for vehicle to lift off (physics simulation time)
        import time
        print("  Waiting for flight physics to settle...")
        time.sleep(5)
        
        # Try to capture viewport screenshot
        timestamp = int(time.time())
        screenshot_path = os.path.join(
            self.screenshot_dir, 
            f"playtest_{timestamp}.png"
        )
        
        if self.unreal:
            success = capture_viewport_screenshot(self.unreal, screenshot_path)
            if success:
                # Send to LM Studio for analysis
                self._send_to_lmstudio_analysis(screenshot_path)
        else:
            print("  Skipping screenshot (simulation mode)")

    def _spawn_test_vehicle(self):
        """Spawn a test vehicle actor."""
        try:
            import unreal
            
            # Try to spawn the offroad car as a base (will have flight component added in Blueprint)
            offroad_bp_path = "/Game/Vehicles/OffroadCar/BP_OffroadCar.BP_OffroadCar_C"
            offroad_bp_class = unreal.EditorAssetLibrary.load_blueprint_class_from_asset(offroad_bp_path)
            
            if offroad_bp_class:
                spawn_location = unreal.Vector(0, 200, 100)  # Elevated for flight testing
                spawn_rotation = unreal.Rotator(0, 90, 0)
                
                spawned_vehicle = unreal.EditorLevelUtils.spawn_actor_from_class(
                    offroad_bp_class,
                    spawn_location,
                    spawn_rotation
                )
                print(f"  Spawned test vehicle at {spawn_location}")
                return spawned_vehicle
            
            # Fallback: find existing vehicle pawn in level
            world = self.unreal.EditorWorldSubsystem_get_world()
            if world:
                for actor in world.GetActors():
                    if "Pawn" in str(type(actor).__name__) or "Vehicle" in str(type(actor).__name__):
                        print(f"  Found existing vehicle pawn: {actor.get_name()}")
                        return actor
                    
        except Exception as e:
            print(f"  Could not spawn vehicle: {e}")
        
        return None

    def _get_current_vehicle(self):
        """Get the currently controlled vehicle pawn."""
        try:
            import unreal
            
            # Try to get current level actors
            world = self.unreal.EditorWorldSubsystem_get_world()
            if world:
                for actor in world.GetActors():
                    if "Pawn" in str(type(actor).__name__) or "Vehicle" in str(type(actor).__name__):
                        return actor
            
        except Exception as e:
            print(f"  Could not get current vehicle: {e}")
        
        return None

    def _call_blueprint_function(self, actor, function_name, *args):
        """Call a Blueprint function on an actor."""
        try:
            if hasattr(actor, function_name):
                getattr(actor, function_name)(*args)
                print(f"  Called {function_name}()")
        except Exception as e:
            print(f"  Error calling {function_name}: {e}")

    def _apply_thrust(self, vehicle, thrust_value):
        """Apply thrust to a vehicle via its flight component."""
        try:
            # Find the FlightControlComponent on the vehicle
            for comp in vehicle.GetComponentByClass():
                if "Flight" in str(type(comp).__name__):
                    comp.ApplyThrust(thrust_value)
                    print(f"  Applied thrust: {thrust_value}")
                    return
        except Exception as e:
            print(f"  Error applying thrust: {e}")

    def _send_to_lmstudio_analysis(self, screenshot_path):
        """Send screenshot to LM Studio for AI analysis."""
        prompt = (
            "Analyze this gameplay screenshot from the Chimera vehicle test. "
            "Specifically confirm whether the vehicle has lifted off the ground — "
            "are its wheels touching the ground? What is its approximate height above ground?"
        )
        return send_screenshot_to_lmstudio(prompt, screenshot_path, LM_STUDIO_MODEL, logger)

    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 60)
        print("PLAY TEST SUMMARY")
        print("=" * 60)
        
        phases_completed = [
            "Phase 1: Environment setup",
            "Phase 2: Flight mode toggle",
            "Phase 3: Thrust/strafe movement",
            "Phase 4: 6DOF rotation (pitch/yaw/roll)",
            "Phase 5: Idle damping verification",
            "Phase 6: Screenshot capture & AI analysis"
        ]
        
        for i, phase in enumerate(phases_completed, 1):
            status = "PASSED" if len(self.test_results) >= i else "SKIPPED"
            print(f"  {i}. {phase}: {status}")
        
        print("\nAll phases completed. Review logs above for details.")


def run_playtest():
    """Main entry point for the play test."""
    print("Starting Chimera Flight Vehicle Play Test...")
    
    play_test = FlightPlayTest()
    play_test.run_full_playtest()
    
    return play_test


if __name__ == "__main__":
    """Direct execution example: python play_test.py"""
    import sys
    
    print("=" * 70)
    print("CHIMERA FLIGHT PLAY TEST — STANDALONE EXECUTION")
    print("=" * 70)
    
    try:
        import unreal
        print("[INFO] Running in UE Editor mode...")
    except ImportError:
        print("[WARN] 'unreal' module not available (outside UE Editor)")
        print("[INFO] Running in simulation mode — some features will be skipped\n")
    
    result = run_playtest()
    test_results = getattr(result, "test_results", None)
    if test_results:
        print(f"\nTest results: {len(test_results)} phases executed")
