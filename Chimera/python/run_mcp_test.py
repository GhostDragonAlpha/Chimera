"""
Standalone MCP Test Runner — Manual triggering of automated testing workflow.

Can be called from UE Python Console:
    from run_mcp_test import run_standalone_test; run_standalone_test()

Or executed directly from terminal:
    python run_mcp_test.py
"""

import os
import sys


def run_standalone_test():
    """Run the MCP automated test workflow standalone.

    Imports and executes the full automation pipeline from mcp_automation_client.
    Can be called independently of UE Editor startup.
    """
    # Add project Python directory to path if needed
    script_dir = os.path.dirname(os.path.abspath(__file__))
    python_dir = os.path.join(script_dir, "Python")

    if os.path.isdir(python_dir) and python_dir not in sys.path:
        sys.path.insert(0, python_dir)

    try:
        from mcp_automation_client import run_mcp_automated_test

        print("\n" + "=" * 60)
        print("STANDALONE MCP TEST RUNNER")
        print("=" * 60)
        print(f"\n[CONFIG] MCP URL: http://localhost:3000/mcp")
        print("[INFO] Ensure McpAutomationBridge plugin is active on port 3000")

        run_mcp_automated_test()

    except ImportError as e:
        print(f"[ERROR] Failed to import mcp_automation_client: {e}")
        print("[INFO] Verify the file exists in Chimera/Python directory")
    except Exception as e:
        print(f"[ERROR] Standalone test failed: {e}")


if __name__ == "__main__":
    run_standalone_test()
