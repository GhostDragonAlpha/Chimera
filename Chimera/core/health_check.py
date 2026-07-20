"""Pre-action health check. Run before ANY operation that touches UE5 or MCP.

Catches the mistakes that keep happening:
1. Editor not running or crashed
2. MCP bridge not responding  
3. Recent crash reports unacknowledged
4. Build failures from sed corruption (t prefix)

Usage: python -m core.health_check
Exit 0 = all clear. Exit 1 = fix needed.
"""

import os, sys, subprocess, time
from pathlib import Path
from datetime import datetime, timezone

CRASH_DIR = Path("C:/Program Files/Epic Games/UE_5.8/Engine/Saved/Crashes")
LOG_DIR = Path("E:/PythonChimera/Chimera/Saved/Logs")
PROCEDURAL = Path("E:/PythonChimera/Chimera/Source/Chimera/ProceduralGenerated")

def check_editor_process() -> bool:
    """Is UnrealEditor.exe running?"""
    try:
        result = subprocess.run(
            ['powershell', '-NoProfile', '-Command',
             'Get-Process UnrealEditor -ErrorAction SilentlyContinue | Select-Object -First 1 Id'],
            capture_output=True, text=True, timeout=10)
        return "Id" in result.stdout
    except:
        return False

def check_mcp_bridge() -> bool:
    """Can we connect to the MCP bridge and get a response?"""
    try:
        from core.telemetry_probe import MCPStdioClient
        c = MCPStdioClient()
        r = c.call('inspect', {'action': 'get_scene_stats'})
        return r.get('result',{}).get('structuredContent',{}).get('success', False)
    except:
        return False

def check_recent_crashes() -> list:
    """Any crash reports from the last hour?"""
    recent = []
    if not CRASH_DIR.exists():
        return recent
    now = datetime.now(timezone.utc)
    for crash in CRASH_DIR.iterdir():
        if crash.is_dir():
            mtime = datetime.fromtimestamp(crash.stat().st_mtime, tz=timezone.utc)
            age_min = (now - mtime).total_seconds() / 60
            if age_min < 60:
                recent.append((crash.name, age_min))
    return recent

def check_sed_corruption() -> list:
    """Files with 't' prefix from broken sed commands?"""
    corrupted = []
    for ext in ['.cpp', '.h', '.py']:
        for f in PROCEDURAL.rglob(f'*{ext}'):
            try:
                text = f.read_text(encoding='utf-8', errors='replace')
                for i, line in enumerate(text.splitlines(), 1):
                    if line.startswith('t\t') or line.startswith('tUE_LOG') or line.startswith('tInputComponent') or line.startswith('tvoid') or line.startswith('tFActorSpawnParameters'):
                        corrupted.append(f"{f.name}:{i}: {line[:60]}")
            except:
                pass
    return corrupted[:10]

def check_build_log() -> str:
    """Last build result from the log."""
    log = LOG_DIR / "Chimera.log"
    if not log.exists():
        return "no log"
    text = log.read_text(encoding='utf-8', errors='replace')
    if "Fatal error:" in text:
        for line in text.splitlines():
            if "Fatal error:" in line:
                return line.strip()[-200:]
    return "no fatal errors in log"


def main():
    issues = []
    
    # 1. Editor process
    if not check_editor_process():
        issues.append("EDITOR: Not running. Run: chimera_unblock(ensure='editor')")
    else:
        print("OK Editor process running")
    
    # 2. MCP bridge
    if check_mcp_bridge():
        print("OK MCP bridge responding")
    else:
        issues.append("MCP: Bridge not responding. Editor may be loading or crashed.")
    
    # 3. Recent crashes
    crashes = check_recent_crashes()
    if crashes:
        for name, age in crashes:
            issues.append(f"CRASH: {name} ({age:.0f}m ago)")
    else:
        print("OK No recent crashes")
    
    # 4. Sed corruption
    corrupted = check_sed_corruption()
    if corrupted:
        for c in corrupted:
            issues.append(f"SED BUG: {c}")
    
    # 5. Build log
    log_issue = check_build_log()
    if "Fatal error" in log_issue:
        issues.append(f"BUILD: {log_issue}")
    else:
        print(f"OK Build log: {log_issue[:80]}")
    
    if issues:
        print(f"\nFAIL {len(issues)} ISSUE(S):")
        for i in issues:
            print(f"  - {i}")
        return 1
    
    print("\nOK ALL CLEAR")
    return 0

if __name__ == "__main__":
    sys.exit(main())
