"""
Runtime Screenshot Play Test Module — In-Editor Automated Testing
Captures screenshots during gameplay, sends to LM Studio for AI analysis, then stops PIE automatically.

Uses the shared lmstudio_client module for all LM Studio HTTP requests.
Uses UE TimerManager for non-blocking delays instead of time.sleep().
"""

import os
import sys
from config import LM_STUDIO_MODEL

from lmstudio_client import send_to_lmstudio, display_response
from screenshot_helpers import capture_viewport_screenshot, send_screenshot_to_lmstudio


class RuntimeScreenshotPlayTest:
    """Automated in-editor screenshot capture and AI analysis with automatic stop."""
    
    def __init__(self):
        self.unreal = None
        try:
            import unreal
            self.unreal = unreal
        except ImportError:
            print("[ERROR] Must run inside UE Editor — 'unreal' module not available")
            return
        
        self.screenshot_dir = "Screenshots"
        os.makedirs(self.screenshot_dir, exist_ok=True)
        
        # State machine
        self.phase = 0
        self.captured_screenshots = []
        self.analysis_results = []
        self.timer_handle = None
        
        # Configuration
        self.max_ground_captures = 2
        self.max_flight_captures = 3
        self.wait_frames_before_flight = 60  # ~1 second at 60 FPS
    
    def run(self):
        """Start the automated play test — captures screenshots, analyzes, stops PIE."""
        print("=" * 70)
        print("RUNTIME SCREENSHOT PLAY TEST — IN-EDITOR AUTOMATED")
        print("=" * 70)
        
        # Phase 1: Capture ground-level screenshots immediately
        self.phase = 1
        print("\n[PHASE 1] Capturing ground-level screenshots...")
        self._capture_ground_screenshots()
    
    def _capture_ground_screenshots(self):
        """Capture initial ground-level screenshots."""
        for i in range(self.max_ground_captures):
            filepath = os.path.join(self.screenshot_dir, f"ground_{i}.png")
            success = self._capture_screenshot(filepath)
            if success:
                self.captured_screenshots.append({"type": "ground", "path": filepath})
                print(f"  Captured ground screenshot {i+1}/{self.max_ground_captures}")
        
        # Wait for vehicle to lift off, then capture flight screenshots
        print("\n[PHASE 2] Waiting for flight physics simulation...")
        self._start_flight_wait_timer()
    
    def _capture_screenshot(self, filepath):
        """Capture viewport screenshot using UE console command."""
        return capture_viewport_screenshot(self.unreal, filepath)
    
    def _start_flight_wait_timer(self):
        """Use UE TimerManager to wait for flight physics without blocking."""
        world = self.unreal.EditorWorldSubsystem_get_world()
        if not world:
            print("[ERROR] No world available")
            self._stop_playtest()
            return
        
        # Schedule next phase after ~1 second (60 frames)
        timer_manager = world.GetTimerManager()
        
        def on_flight_wait_complete():
            self.phase = 2
            print("\n[PHASE 3] Capturing mid-flight screenshots...")
            self._capture_flight_screenshots()
        
        # Use a simple delay approach — schedule via TimerManager
        timer_manager.SetTimer("ScreenshotPlayTest_FlightWait", on_flight_wait_complete, 1.0)
    
    def _capture_flight_screenshots(self):
        """Capture mid-flight screenshots."""
        for i in range(self.max_flight_captures):
            filepath = os.path.join(self.screenshot_dir, f"flight_{i}.png")
            success = self._capture_screenshot(filepath)
            if success:
                self.captured_screenshots.append({"type": "flight", "path": filepath})
                print(f"  Captured flight screenshot {i+1}/{self.max_flight_captures}")
        
        # Send to LM Studio for analysis
        print("\n[PHASE 4] Sending screenshots to LM Studio...")
        self._send_to_lmstudio()
    
    def _send_to_lmstudio(self):
        """Send all captured screenshots to LM Studio for AI analysis."""
        if not self.captured_screenshots:
            print("[ERROR] No screenshots captured")
            self._stop_playtest()
            return
        
        # Analyze ground screenshots
        ground_shots = [s for s in self.captured_screenshots if s["type"] == "ground"]
        flight_shots = [s for s in self.captured_screenshots if s["type"] == "flight"]
        
        print(f"  Ground screenshots: {len(ground_shots)}")
        print(f"  Flight screenshots: {len(flight_shots)}")
        
        # Analyze first ground screenshot
        if ground_shots:
            self._analyze_screenshot(ground_shots[0]["path"], "ground")
        
        # Analyze first flight screenshot
        if flight_shots:
            self._analyze_screenshot(flight_shots[0]["path"], "flight")
        
        # Stop playtest after analysis (give LM Studio time to respond)
        world = self.unreal.EditorWorldSubsystem_get_world()
        timer_manager = world.GetTimerManager() if world else None
        
        def on_stop_playtest():
            print("\n[PHASE 5] Stopping Play In Editor...")
            self._stop_pie()
        
        if timer_manager:
            timer_manager.SetTimer("ScreenshotPlayTest_StopPIE", on_stop_playtest, 10.0)
    
    def _analyze_screenshot(self, filepath, analysis_type="flight"):
        """Send screenshot to LM Studio for AI analysis."""
        if analysis_type == "ground":
            prompt = (
                "Analyze this gameplay screenshot from the Chimera vehicle test. "
                "Confirm whether the vehicle is on the ground — are its wheels touching the surface?"
            )
        else:
            prompt = (
                "Analyze this gameplay screenshot from the Chimera vehicle test. "
                "Specifically confirm whether the vehicle has lifted off the ground — "
                "are its wheels touching? What is its approximate height above ground?"
            )
        
        result = send_screenshot_to_lmstudio(prompt, filepath, LM_STUDIO_MODEL, None, "  ")
        if result:
            self.analysis_results.append({"type": analysis_type, "result": result})
    
    def _stop_pie(self):
        """Stop Play In Editor automatically."""
        try:
            self.unreal.EditorLevelUtils.stop_play_in_editor(0)
            print("[OK] PIE stopped successfully")
        except Exception as e:
            print(f"[WARN] Could not stop PIE: {e}")
        
        # Print summary
        self._print_summary()
    
    def _print_summary(self):
        """Print play test results."""
        print("\n" + "=" * 70)
        print("RUNTIME SCREENSHOT PLAY TEST SUMMARY")
        print("=" * 70)
        
        ground_count = len([s for s in self.captured_screenshots if s["type"] == "ground"])
        flight_count = len([s for s in self.captured_screenshots if s["type"] == "flight"])
        
        print(f"\n  Screenshots captured: {len(self.captured_screenshots)}")
        print(f"    Ground-level: {ground_count}")
        print(f"    Mid-flight: {flight_count}")
        
        print(f"\n  AI analyses completed: {len(self.analysis_results)}")
        
        # Check for lift-off confirmation from analysis results
        lifted_off = False
        for analysis in self.analysis_results:
            result = analysis["result"]
            if result and isinstance(result, dict):
                content = result.get("content", "")
                reasoning_content = result.get("reasoning_content", "")
                
                text = (content + " " + reasoning_content).lower()
                if any(keyword in text for keyword in ["lifted off", "in the air", "above ground", "wheels not touching"]):
                    lifted_off = True
        
        print(f"\n  [RESULT] Vehicle lift-off confirmed: {lifted_off}")
        
        print("\n" + "=" * 70)


def run_runtime_screenshot_playtest():
    """Main entry point for in-editor automated play test."""
    print("Starting Runtime Screenshot Play Test...")
    
    play_test = RuntimeScreenshotPlayTest()
    play_test.run()
    
    return play_test


if __name__ == "__main__":
    """Direct execution example: python runtime_screenshot_playtest.py
    
    Note: This module requires UE Editor ('unreal' module available).
    Running standalone will print error and exit.
    """
    try:
        import unreal
        run_runtime_screenshot_playtest()
    except ImportError:
        print("[ERROR] Must run inside UE Editor — 'unreal' module not available")
        sys.exit(1)
