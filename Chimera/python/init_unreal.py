"""
Chimera Project Initialization — Automatically executed by PythonScriptPlugin on UE Editor launch.

Dual-mode startup: tries MCP-native automated testing first, falls back to legacy scripts if unavailable.
Captures screenshots during gameplay, sends them to LM Studio for AI analysis, and stops PIE automatically.
"""

import os
import sys

# Add project Python directory to path
project_python = os.path.dirname(os.path.abspath(__file__))
if project_python not in sys.path:
    sys.path.insert(0, project_python)


def run_chimera_startup():
    """Main initialization — tries MCP workflow first, falls back to legacy scripts."""
    
    # Mode 1: MCP-native automated testing (preferred)
    try:
        from mcp_automation_client import run_mcp_automated_test
        
        print("\n[INIT] Attempting MCP-based automated test...")
        run_mcp_automated_test()
        
        print("\n[MCP] Workflow completed successfully.")
        return  # Exit early — MCP succeeded
    
    except (ImportError, Exception) as e:
        print(f"\n[WARN] MCP workflow unavailable ({e})")
        print("[INFO] Falling back to legacy startup scripts...")

    # Mode 2: Legacy synchronous startup (fallback)
    try:
        import unreal
        
        from procedural_game_generator import run_startup_workflow, generate_all
        from play_test import FlightPlayTest, run_playtest
        from runtime_screenshot_playtest import RuntimeScreenshotPlayTest, run_runtime_screenshot_playtest
        
        print("\n[LEGACY] Running complete startup workflow...")
        
        # Phase 1: Generate C++ files and sync project state
        print("\n[PHASE 1] Generating C++ components and syncing project state...")
        generate_all()
        
        # Phase 2: Run runtime screenshot play test with automatic PIE stop
        print("\n[PHASE 2] Starting automated in-editor play test...")
        run_runtime_screenshot_playtest()
        
        print("\n" + "=" * 70)
        print("CHIMERA INITIALIZATION COMPLETE — Legacy workflow finished")
        print("=" * 70)
        
    except ImportError as e:
        print(f"\n[WARN] Could not import legacy modules: {e}")
        print("[INFO] Exiting gracefully.")
    except Exception as e:
        print(f"\n[ERROR] Legacy startup failed: {e}")
        print("[INFO] Exiting gracefully — existing scripts unaffected")


# Execute automatically on module load
run_chimera_startup()
