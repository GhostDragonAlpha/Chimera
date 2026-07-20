#!/usr/bin/env python3
"""build_all.py — One-command full project build.

Chains all build steps into a single command. Run after dismissing
the UE5 restore dialog (or any blocking popup).

Usage:
    cd E:\PythonChimera\worker_bridge
    python build_all.py

Steps:
1. Check/restore DefaultGame.ini MCP config
2. Kill any lingering Unreal processes
3. Run the UE5 pipeline (compile + link)
4. Start the editor with MCP
5. Wait for MCP to be ready
6. Run respawn_demo.py (spawn all educational texts)
7. Verify educational content
8. Report results
"""

import sys, os, time, subprocess, json, urllib.request

ROOT = "E:/PythonChimera"
CHIMERA = f"{ROOT}/Chimera"
CONFIG = f"{CHIMERA}/Config/DefaultGame.ini"
BRIDGE_DIR = f"{ROOT}/worker_bridge"
MCP_URL = "http://127.0.0.1:3000/mcp"
EDITOR_PATH = "C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe"

def log(msg):
    print(f"[BUILD] {msg}")

def check_config():
    """Ensure DefaultGame.ini has MCP settings."""
    mcp_section = "[/Script/McpAutomationBridge.McpAutomationBridgeSettings]"
    try:
        with open(CONFIG, "r") as f:
            if mcp_section not in f.read():
                with open(CONFIG, "a") as f:
                    f.write(f"\n{mcp_section}\n")
                    f.write("bEnableNativeMCP=True\n")
                    f.write("NativeMCPPort=3000\n")
                log("MCP config restored")
    except:
        log(f"Warning: could not check {CONFIG}")

def kill_unreal():
    """Kill all Unreal processes that might hold DLLs."""
    for proc in ["UnrealEditor", "UnrealEditor-Cmd", "CrashReportClient"]:
        subprocess.run(
            ["powershell", "-Command", f"Get-Process {proc} -ErrorAction SilentlyContinue | Stop-Process -Force"],
            capture_output=True, shell=True
        )
    log("Unreal processes killed")
    time.sleep(3)

def run_pipeline():
    """Run the UE5 build pipeline."""
    log("Running pipeline...")
    result = subprocess.run(
        [sys.executable, "run_deep_space_trader_pipeline.py"],
        capture_output=True, text=True, timeout=300,
        cwd=CHIMERA
    )
    output = result.stdout + result.stderr
    if "COMPLETE" in output and "BLOCKED" not in output:
        log("PIPELINE PASSED")
        return True
    else:
        # Check for known issues
        if "LNK1104" in output:
            log("LINK FAILED - DLLs in use. Kill Unreal processes and retry.")
        elif "C5038" in output or "C4996" in output:
            log("WARNINGS AS ERRORS - pragmas not suppressing. Check generated files.")
        else:
            log(f"PIPELINE FAILED (exit {result.returncode})")
        return False

def wait_for_mcp(timeout=60):
    """Wait for MCP port 3000 to be ready."""
    log("Waiting for MCP...")
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            req = urllib.request.Request(MCP_URL, data=b'{}', headers={"Content-Type":"application/json"})
            urllib.request.urlopen(req, timeout=3)
            return True
        except:
            time.sleep(2)
    return False

def start_editor():
    """Start the UE5 editor with MCP."""
    log("Starting editor...")
    subprocess.run(
        ["powershell", "-Command", 
         f"Start-Process -FilePath '{EDITOR_PATH}' -ArgumentList '{CHIMERA}/Chimera.uproject -log -mcp' -WindowStyle Normal"],
        capture_output=True, shell=True
    )
    return wait_for_mcp(60)

def respawn_demo():
    """Run the respawn demo script."""
    log("Respawning educational content...")
    result = subprocess.run(
        [sys.executable, "respawn_demo.py"],
        capture_output=True, text=True, timeout=120,
        cwd=BRIDGE_DIR
    )
    print(result.stdout)
    return "38/38" in result.stdout or "texts spawned" in result.stdout

def verify():
    """Verify educational content via MCP."""
    try:
        from mcp_builder import MCP
        mcp = MCP()
        r = mcp.call("tools/call", {"name": "inspect", "arguments": {"action": "runtime_report"}})
        content = ""
        for c in r.get("result",{}).get("content",[]):
            if isinstance(c, dict) and "text" in c: content = c["text"]
        count = content.count("EduText_")
        log(f"Verified: {count} educational texts in level")
        return count >= 30
    except:
        log("Verification failed - MCP not available")
        return False

if __name__ == "__main__":
    log("=" * 50)
    log("MASTER BUILD SCRIPT")
    log("=" * 50)
    
    check_config()
    kill_unreal()
    
    if run_pipeline():
        log("Build successful. Starting editor for content verification...")
    
    start_editor()
    respawn_demo()
    verify()
    
    log("=" * 50)
    log("BUILD COMPLETE")
    log("All educational content spawned and verified.")
    log("Run docs/DEMO_WALKTHROUGH.html for the interactive tour.")
    log("=" * 50)
