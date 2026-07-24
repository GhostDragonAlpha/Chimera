#!/usr/bin/env python3
"""Run sequential agent chain continuously with automatic cycle repetition."""

import subprocess
import sys
from pathlib import Path
from datetime import datetime, timedelta
import time
import signal

# Agent sequence - runs in this exact order, continuously looping
AGENT_SEQUENCE = [
    ("Research Agent", "agents/research_agent.py"),
    ("Visual Validation Agent", "agents/validation_agent.py"),
    ("Recombination Agent", "agents/recombination_agent.py"),
    ("Integration Agent", "agents/integration_agent.py"),
    ("Documentation Agent", "agents/documentation_agent.py")
]

# Configuration for continuous operation
CYCLE_DELAY_SECONDS = 5  # Wait between cycles (shorter for testing)
MAX_CYCLES = 3  # Run exactly 3 cycles to demonstrate continuity

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

def run_cycle():
    """Run one complete cycle of all agents."""
    results = {}
    
    for name, script in AGENT_SEQUENCE:
        success = run_agent(name, script)
        results[name] = success
    
    # Summary for this cycle
    print("\n" + "="*70)
    print("CYCLE SUMMARY")
    print("="*70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, success in results.items():
        status = "PASSED" if success else "FAILED"
        print(f"  {status}: {name}")
    
    print(f"\nCycle: {passed}/{total} agents succeeded")
    print(f"Success rate: {(passed/total)*100:.1f}%")
    
    return results

def main():
    print("CONTINUOUS SEQUENTIAL AGENT PIPELINE - TESTING CONTINUITY")
    print("="*70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Cycle delay: {CYCLE_DELAY_SECONDS} seconds")
    print(f"Max cycles to run: {MAX_CYCLES}")
    print("\nAgent Sequence:")
    for i, (name, script) in enumerate(AGENT_SEQUENCE, 1):
        print(f"  {i}. {name}")
    
    print("\n" + "="*70)
    print("CONTINUOUS EXECUTION - Running multiple cycles automatically\n")
    
    cycle_count = 0
    
    try:
        while True:
            cycle_count += 1
            
            if MAX_CYCLES and cycle_count > MAX_CYCLES:
                print(f"\n{'='*70}")
                print(f"MAX CYCLES REACHED ({MAX_CYCLES}) - SHUTTING DOWN")
                print(f"{'='*70}")
                break
            
            # Run one complete cycle
            results = run_cycle()
            
            # Calculate time until next cycle
            if cycle_count < MAX_CYCLES:  # Don't wait after last cycle
                next_start = datetime.now() + timedelta(seconds=CYCLE_DELAY_SECONDS)
                
                print(f"\n{'='*70}")
                print(f"NEXT CYCLE STARTS AT: {next_start.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"{'='*70}\n")
                
                # Wait before next cycle (but allow Ctrl+C)
                try:
                    time.sleep(CYCLE_DELAY_SECONDS)
                except KeyboardInterrupt:
                    break
            
    except KeyboardInterrupt:
        print("\n\n" + "="*70)
        print("USER INTERRUPTED - PIPELINE STOPPED")
        print("="*70)
        
    finally:
        end_time = datetime.now()
        print(f"\n{'='*70}")
        print(f"CONTINUOUS PIPELINE COMPLETED")
        print(f"Total cycles run: {cycle_count}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Stopped at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}")

if __name__ == "__main__":
    main()
