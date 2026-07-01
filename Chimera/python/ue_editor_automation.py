"""
UE Editor Automation — Launches game, tests flight mode, captures screenshots.
Integrates with LM Studio for AI-powered analysis of gameplay footage.

Uses the shared lmstudio_client module for all LM Studio HTTP requests.
Uses only Python standard library + centralized config paths.
"""

import os
import sys
import subprocess
import time

from config import LM_STUDIO_MODEL

from lmstudio_client import send_to_lmstudio, display_response


def launch_game():
    """Launch the Chimera game in editor mode."""
    
    from config import UE_EDITOR_EXE, CHIMERA_UPROJECT_FILE
    
    print("=" * 60)
    print("UE EDITOR AUTOMATION")
    print("=" * 60)
    
    print(f"\n[STEP 1] Launching Unreal Editor...")
    print(f"Editor: {UE_EDITOR_EXE}")
    print(f"Project: {CHIMERA_UPROJECT_FILE}")
    
    # Launch editor (non-blocking)
    cmd = [UE_EDITOR_EXE, CHIMERA_UPROJECT_FILE]
    proc = subprocess.Popen(cmd)
    print(f"[OK] Editor launched (PID: {proc.pid})")
    
    return proc


def capture_screenshot(path):
    """Capture viewport screenshot using UE console command."""
    try:
        # This would use unreal module in-editor
        # For now, we'll simulate the process
        print(f"\n[STEP 2] Capturing screenshot to {path}...")
        
        # In a real scenario, this would execute:
        # unreal.SystemLibrary.execute_console_command(None, f"shot {path}")
        
        print("[OK] Screenshot captured (simulated)")
        return True
        
    except Exception as e:
        print(f"[FAIL] Screenshot capture failed: {e}")
        return False


def analyze_screenshot(screenshot_path):
    """Send screenshot to LM Studio for AI analysis.
    
    Uses shared lmstudio_client.send_to_lmstudio() to eliminate duplicate HTTP code.
    """
    if not os.path.exists(screenshot_path):
        print("[WARN] No screenshot file found")
        return None

    prompt = (
        "Analyze this gameplay screenshot from the Chimera vehicle test.\n\n"
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
    
    return result


def run_automation():
    """Run complete UE editor automation workflow."""
    
    saved_dir = r"E:\PythonChimera\Chimera\Saved"
    screenshot_path = os.path.join(saved_dir, "automated_screenshot.png")
    
    # Launch game (simulated for now)
    proc = launch_game()
    
    # Capture screenshot
    capture_success = capture_screenshot(screenshot_path)
    
    if capture_success:
        # Analyze with AI
        result = analyze_screenshot(screenshot_path)
        
        if result:
            print("\n[OK] Automation complete — AI analysis received")
        else:
            print("\n[WARN] Could not get AI analysis")
    else:
        print("\n[FAIL] Screenshot capture failed")
    
    return proc


if __name__ == "__main__":
    run_automation()
