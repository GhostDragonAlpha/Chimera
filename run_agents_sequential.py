#!/usr/bin/env python3
"""Run sequential agent chain with full CLI visibility."""

import subprocess
import sys
from pathlib import Path
from datetime import datetime

# Agent sequence - runs in this exact order, continuously looping
AGENT_SEQUENCE = [
    ("Research Agent", "agents/research_agent.py"),
    ("Visual Validation Agent", "agents/validation_agent.py"),
    ("Recombination Agent", "agents/recombination_agent.py"),
    ("Integration Agent", "agents/integration_agent.py"),
    ("Documentation Agent", "agents/documentation_agent.py")
]

def run_agent(name, script):
    """Run a single agent and show output."""
    print(f"\n{'='*70}")
    print(f"STARTING: {name}")
    print(f"{'='*70}")
    
    start_time = datetime.now()
    
    try:
        result = subprocess.run(
            [sys.executable, str(Path(__file__).parent / script)],
            cwd=Path(__file__).parent,
            capture_output=False,  # Show real-time output
            text=True,
            timeout=1800  # 30 minutes
        )
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        if result.returncode == 0:
            print(f"\nSUCCESS: {name} completed in {elapsed:.1f}s")
            return True
        else:
            print(f"\nFAILED: {name} with exit code {result.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"\nTIMEOUT: {name} after {elapsed:.1f}s")
        return False
        
    except Exception as e:
        print(f"\nERROR running {name}: {e}")
        return False

def main():
    print("SEQUENTIAL GENETICS PIPELINE WORKFLOW")
    print("="*70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nAgent Sequence:")
    for i, (name, script) in enumerate(AGENT_SEQUENCE, 1):
        print(f"  {i}. {name}")
    
    print("\n" + "="*70)
    print("EXECUTING...\n")
    
    results = {}
    
    for name, script in AGENT_SEQUENCE:
        success = run_agent(name, script)
        results[name] = success
    
    # Final summary
    print("\n" + "="*70)
    print("WORKFLOW SUMMARY")
    print("="*70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, success in results.items():
        status = "PASSED" if success else "FAILED"
        print(f"  {status}: {name}")
    
    print(f"\nOverall: {passed}/{total} agents succeeded")
    print(f"Success rate: {(passed/total)*100:.1f}%")
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check for recent logs
    log_files = list(Path("agent_logs").glob("*.log"))
    if log_files:
        print(f"\nAgent logs available in agent_logs/ ({len(log_files)} files)")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
