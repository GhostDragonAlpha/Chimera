"""
Project Build Runner — Compiles Chimera C++ project via UE Editor.
Uses centralized config paths from config.py.
"""

import os
import sys
import subprocess
import time


def build_project():
    """Build the Chimera C++ project using UnrealEditor-Cmd with Compile commandlet."""
    
    # Import centralized config
    sys.path.insert(0, r"E:\PythonChimera\Chimera\Python")
    from config import (
        UE_EDITOR_CMD_EXE,
        CHIMERA_UPROJECT_FILE,
        UBT_DOTNET_AUTOMATIONTOOL,
        SHADER_COMPILE_WORKER_EXE,
        CHIMERA_SOURCE_DIR,
        CHIMERA_PROJECT_ROOT,
    )

    print("=" * 60)
    print("CHIMERA PROJECT BUILD")
    print("=" * 60)
    
    # Verify files exist
    if not os.path.exists(CHIMERA_UPROJECT_FILE):
        print(f"[FAIL] uproject file not found: {CHIMERA_UPROJECT_FILE}")
        return False
    
    print(f"Project file: {CHIMERA_UPROJECT_FILE}")
    
    # Method 1: Launch UE Editor with Compile commandlet (non-blocking)
    print("\n[STEP 1] Launching UnrealEditor-Cmd with Compile commandlet...")
    
    cmd = [UE_EDITOR_CMD_EXE, CHIMERA_UPROJECT_FILE, "-run=Compile"]
    print(f"Command: {' '.join(cmd)}\n")
    
    try:
        # Start the editor process (it will compile and then exit)
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,  # Line buffered
            encoding='utf-8',
            errors='replace'
        )
        
        print("[INFO] Build process started. Waiting for completion...\n")
        
        # Read output in real-time and look for success/failure indicators
        build_success = False
        has_error = False
        
        while True:
            line = proc.stdout.readline()
            if not line:
                break
            
            print(line, end='')
            
            # Check for compilation results
            if "Result: Success" in line or "Build succeeded" in line:
                build_success = True
            if "Error:" in line or "Failed" in line or "Result: Failed" in line:
                has_error = True
        
        proc.wait()
        
        print("\n" + "=" * 60)
        if build_success and not has_error:
            print("BUILD RESULT: SUCCESS")
            print("=" * 60)
            return True
        elif has_error:
            print("BUILD RESULT: FAILED — check logs above for errors")
            print("=" * 60)
            return False
        else:
            print(f"Build process exited with code: {proc.returncode}")
            print("Check UE Editor logs for build status.")
            return proc.returncode == 0
            
    except FileNotFoundError as e:
        print(f"[FAIL] UE Editor not found at: {UE_EDITOR_CMD_EXE}")
        print(f"Error: {e}")
        return False
    
    except Exception as e:
        print(f"[FAIL] Unexpected error: {e}")
        return False


def verify_compiled_files():
    """Check if FlightControlComponent and ChimeraPawn compiled successfully."""
    import sys
    sys.path.insert(0, r"E:\PythonChimera\Chimera\Python")
    from config import CHIMERA_SOURCE_DIR
    
    print("\n" + "=" * 60)
    print("VERIFICATION — Checking compiled C++ files...")
    print("=" * 60)
    
    expected_files = [
        "FlightControlComponent.h",
        "FlightControlComponent.cpp",
        "ChimeraPawn.h",
        "ChimeraPawn.cpp",
    ]
    
    all_found = True
    for filename in expected_files:
        filepath = os.path.join(CHIMERA_SOURCE_DIR, filename)
        exists = os.path.exists(filepath)
        status = "[OK]" if exists else "[MISSING]"
        print(f"  {status} {filename}")
        if not exists:
            all_found = False
    
    print("=" * 60)
    
    # Check Intermediate/Build for compiled binaries
    build_dir = os.path.join(CHIMERA_PROJECT_ROOT, "Intermediate", "Build")
    print("\n[STEP] Checking Intermediate/Build directory...")
    
    if os.path.exists(build_dir):
        print(f"  Build dir exists: {build_dir}")
        
        # Look for FlightControlComponent in build output
        for root, dirs, files in os.walk(build_dir):
            for f in files:
                if "FlightControlComponent" in f or "ChimeraPawn" in f:
                    print(f"  Found in build: {os.path.join(root, f)}")
    else:
        print("  Build directory not yet created (editor may still be building)")


if __name__ == "__main__":
    # Run the build
    success = build_project()
    
    if success:
        verify_compiled_files()
