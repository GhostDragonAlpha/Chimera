#!/usr/bin/env python3
"""Main automation startup script - launches continuous agent workflow."""

import sys
from pathlib import Path
import subprocess
import time
from datetime import datetime

def log_message(message):
    """Log message with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def run_agent_script(script_name, timeout=3600):
    """Run a single agent script."""
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

def main():
    print("🎯 Chimera Automation System Starting")
    print("="*60)
    
    # Create agent_logs directory
    logs_dir = Path("agent_logs")
    logs_dir.mkdir(exist_ok=True)
    
    log_message(f"Logs directory: {logs_dir}")
    
    # Agent scripts to run in sequence
    agent_scripts = [
        "research_materials.py",      # Research missing materials
        "visual_validation_agent.py", # Validate rendered images
        "test_recombination.py",      # Test two-parent recombination
        "test_membrane_integration.py", # Test membrane integration
        "update_documentation.py"     # Update docs and DNA graph
    ]
    
    print("\n📋 Agent Scripts to Execute:")
    for i, script in enumerate(agent_scripts, 1):
        print(f"  {i}. {script}")
    
    print("\n🔄 Starting automated workflow...")
    print("="*60)
    
    # Track results
    results = {}
    
    for script in agent_scripts:
        success = run_agent_script(script, timeout=1800)  # 30 minute timeout each
        results[script] = success
    
    # Print summary
    print("\n" + "="*60)
    print("AUTOMATED WORKFLOW SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for script, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {script}: {status}")
    
    print(f"\nOverall: {passed}/{total} agents succeeded")
    print(f"Success rate: {(passed/total)*100:.1f}%")
    
    # Save workflow summary
    summary = {
        "timestamp": str(datetime.now()),
        "agents_run": agent_scripts,
        "results": results,
        "success_rate": (passed/total)*100 if total > 0 else 0
    }
    
    summary_file = logs_dir / "workflow_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n📄 Workflow summary saved to {summary_file}")
    
    # Return success if all agents passed
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
