#!/usr/bin/env python3
"""Sequential continuous workflow orchestrator - runs agents one at a time in order."""

import sys
from pathlib import Path
import subprocess
import time
from datetime import datetime

# Agent sequence - runs in this exact order, continuously looping
AGENT_SEQUENCE = [
    "research_materials.py",      # Research missing materials
    "visual_validation_agent.py", # Validate rendered images  
    "test_recombination.py",      # Test two-parent recombination
    "test_membrane_integration.py", # Test membrane integration
    "update_documentation.py"     # Update docs and DNA graph
]

def log_message(message):
    """Log message with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def run_agent_script(script_name, timeout=3600):
    """Run a single agent script sequentially."""
    log_message(f"🚀 Starting {script_name}...")
    
    try:
        result = subprocess.run(
            [sys.executable, str(Path(__file__).parent / script_name)],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        if result.returncode == 0:
            log_message(f"✅ {script_name} completed successfully")
            return True
        else:
            log_message(f"❌ {script_name} failed with exit code {result.returncode}")
            # Print last few lines of output for debugging
            print(result.stdout[-1000:])
            print(result.stderr[-1000:])
            return False
            
    except subprocess.TimeoutExpired:
        log_message(f"⏰ {script_name} timed out after {timeout}s")
        return False
        
    except Exception as e:
        log_message(f"❌ Error running {script_name}: {e}")
        return False

def run_continuous_sequential_workflow():
    """Run agents sequentially in continuous loop."""
    print("🎯 Sequential Continuous Workflow Orchestrator")
    print("="*60)
    
    # Create agent_logs directory
    logs_dir = Path("agent_logs")
    logs_dir.mkdir(exist_ok=True)
    
    log_message(f"Logs directory: {logs_dir}")
    log_message(f"Agent sequence: {len(AGENT_SEQUENCE)} agents in order")
    
    print("\n📋 Agent Sequence (runs continuously):")
    for i, script in enumerate(AGENT_SEQUENCE, 1):
        print(f"  {i}. {script}")
    
    print("\n🔄 Starting sequential workflow loop...")
    print("="*60)
    
    # Track results across all runs
    all_results = {}
    total_runs = 0
    
    try:
        while True:
            log_message(f"\n{'='*60}")
            log_message(f"Starting new workflow cycle (run #{total_runs + 1})")
            log_message(f"{'='*60}")
            
            cycle_results = {}
            
            for script in AGENT_SEQUENCE:
                success = run_agent_script(script, timeout=1800)  # 30 minute timeout each
                cycle_results[script] = success
            
            total_runs += 1
            
            # Print cycle summary
            log_message(f"\n{'='*60}")
            log_message(f"CYCLE #{total_runs} SUMMARY")
            log_message(f"{'='*60}")
            
            passed = sum(1 for v in cycle_results.values() if v)
            total = len(cycle_results)
            
            for script, success in cycle_results.items():
                status = "✅ PASSED" if success else "❌ FAILED"
                log_message(f"  {script}: {status}")
            
            log_message(f"\nCycle Success Rate: {passed}/{total} agents succeeded ({(passed/total)*100:.1f}%)")
            
            # Save cycle summary
            cycle_summary = {
                "cycle": total_runs,
                "timestamp": str(datetime.now()),
                "agents_run": AGENT_SEQUENCE,
                "results": cycle_results,
                "success_rate": (passed/total)*100 if total > 0 else 0
            }
            
            summary_file = logs_dir / f"cycle_{total_runs:03d}_summary.json"
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(cycle_summary, f, indent=2)
            
            log_message(f"\n📄 Cycle summary saved to {summary_file}")
            
            # Wait before next cycle (optional - can remove for continuous fast loop)
            # Uncomment the next line if you want a delay between cycles
            # time.sleep(60)  # 1 minute pause between cycles
            
    except KeyboardInterrupt:
        log_message("\n\n🛑 Workflow stopped by user")
        
        # Print final summary
        print("\n" + "="*60)
        print("FINAL WORKFLOW SUMMARY")
        print("="*60)
        
        total_passed = sum(1 for results in all_results.values() if results.get('passed', False))
        total_agents = len(all_results) * len(AGENT_SEQUENCE)
        
        print(f"Total cycles: {total_runs}")
        print(f"Total agents executed: {total_agents}")
        print(f"Overall success rate: {(total_passed/total_agents)*100:.1f}%")
        
    except Exception as e:
        log_message(f"\n❌ Fatal error in workflow: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(run_continuous_sequential_workflow())
