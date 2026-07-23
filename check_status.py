#!/usr/bin/env python3
"""Quick status check for automated sequential workflow."""

import json
from pathlib import Path
from datetime import datetime

def get_latest_cycle():
    """Get the most recent cycle summary."""
    logs_dir = Path("agent_logs")
    if not logs_dir.exists():
        return None
    
    summaries = list(logs_dir.glob("cycle_*_summary.json"))
    if not summaries:
        return None
    
    latest = max(summaries, key=lambda p: p.stat().st_mtime)
    
    with open(latest, 'r') as f:
        return json.load(f)

def main():
    print("🔍 Chimera Automation Status")
    print("="*60)
    
    summary = get_latest_cycle()
    
    if not summary:
        print("❌ No cycle summaries found - workflow may not have started yet")
        print("\nStart the workflow with:")
        print("  python sequential_orchestrator.py")
        return
    
    # Print basic stats
    print(f"Last Cycle: #{summary['cycle']}")
    print(f"Timestamp: {summary['timestamp']}")
    print(f"Success Rate: {summary['success_rate']:.1f}%")
    
    print("\n📊 Agent Results:")
    for agent, passed in summary['results'].items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {status}: {agent}")
    
    # Check for recent logs
    log_files = list(Path("agent_logs").glob("*.log"))
    if log_files:
        print(f"\n📁 Recent agent logs: {len(log_files)} files")
    
    # Print next steps based on results
    all_passed = all(summary['results'].values())
    
    if all_passed:
        print("\n✅ All agents succeeded - workflow running smoothly!")
    else:
        failed_agents = [a for a, passed in summary['results'].items() if not passed]
        print(f"\n⚠️ {len(failed_agents)} agent(s) failed:")
        for agent in failed_agents:
            print(f"  - {agent}")
        print("\nCheck agent_logs/ for error details.")

if __name__ == "__main__":
    main()
