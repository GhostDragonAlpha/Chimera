#!/usr/bin/env python3
"""Agent orchestrator for continuous workflow automation."""

import subprocess
import sys
from pathlib import Path
import json
import time
from datetime import datetime

# Agent configuration
AGENT_CONFIG = {
    "research": {
        "name": "Material Research Agent",
        "task": "Research and locate scan data for missing materials (grass, rock, pure metal, ice)",
        "script": "research_materials.py",
        "interval_minutes": 30,
        "max_runs": 10
    },
    "processing": {
        "name": "Genetics Processing Agent", 
        "task": "Process materials through genetics pipeline (scan → genome → children → render)",
        "script": "process_materials_pipeline.py",
        "interval_minutes": 60,
        "max_runs": 20
    },
    "validation": {
        "name": "Visual Validation Agent",
        "task": "Automated visual validation of rendered children images",
        "script": "visual_validation_agent.py",
        "interval_minutes": 15,
        "max_runs": 50
    },
    "recombination": {
        "name": "Recombination Testing Agent",
        "task": "Test two-parent recombination pipeline with existing class genomes",
        "script": "test_recombination.py",
        "interval_minutes": 120,
        "max_runs": 5
    },
    "integration": {
        "name": "Membrane Integration Agent",
        "task": "Integrate class genomes with membrane shapes (clothe function)",
        "script": "test_membrane_integration.py",
        "interval_minutes": 180,
        "max_runs": 3
    },
    "documentation": {
        "name": "Documentation Agent",
        "task": "Update project documentation and DNA graph records",
        "script": "update_documentation.py",
        "interval_minutes": 60,
        "max_runs": 100
    }
}

class AgentOrchestrator:
    def __init__(self):
        self.project_root = Path(__file__).resolve().parents[1]
        self.logs_dir = self.project_root / "agent_logs"
        self.logs_dir.mkdir(exist_ok=True)
        self.running_agents = {}
        
    def run_agent(self, agent_name, config):
        """Run a single agent task."""
        print(f"\n{'='*60}")
        print(f"Starting {config['name']} ({agent_name})")
        print(f"{'='*60}")
        
        start_time = time.time()
        log_file = self.logs_dir / f"{agent_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        try:
            # Run the agent script
            script_path = self.project_root / config["script"]
            if not script_path.exists():
                print(f"ERROR: Script {script_path} not found")
                return False
                
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout per agent
            )
            
            elapsed = time.time() - start_time
            
            # Log output
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"Agent: {config['name']}\n")
                f.write(f"Start Time: {datetime.now().isoformat()}\n")
                f.write(f"Elapsed: {elapsed:.2f} seconds\n")
                f.write(f"Return Code: {result.returncode}\n")
                f.write("\n--- STDOUT ---\n")
                f.write(result.stdout)
                f.write("\n--- STDERR ---\n")
                f.write(result.stderr)
            
            if result.returncode == 0:
                print(f"✅ {config['name']} completed successfully in {elapsed:.2f}s")
                return True
            else:
                print(f"❌ {config['name']} failed with exit code {result.returncode}")
                return False
                
        except subprocess.TimeoutExpired:
            elapsed = time.time() - start_time
            print(f"⏰ {config['name']} timed out after 1 hour")
            return False
            
        except Exception as e:
            print(f"❌ {config['name']} encountered error: {e}")
            return False
    
    def run_all_agents(self, agent_names=None):
        """Run all agents or specified subset sequentially."""
        if agent_names is None:
            agent_names = list(AGENT_CONFIG.keys())
            
        results = {}
        for agent_name in agent_names:
            config = AGENT_CONFIG[agent_name]
            success = self.run_agent(agent_name, config)
            results[agent_name] = success
            
        return results
    
    def run_continuous_loop(self):
        """Run agents continuously based on schedule."""
        print("🔄 Starting continuous agent orchestration loop")
        print(f"Project root: {self.project_root}")
        print(f"Logs directory: {self.logs_dir}")
        
        # Track last run times and counts
        last_runs = {name: 0 for name in AGENT_CONFIG}
        run_counts = {name: 0 for name in AGENT_CONFIG}
        
        while True:
            current_time = time.time()
            
            print(f"\n{'='*60}")
            print(f"Orchestrator tick at {datetime.now().isoformat()}")
            print(f"{'='*60}")
            
            # Check which agents should run
            for agent_name, config in AGENT_CONFIG.items():
                if last_runs[agent_name] == 0 or (current_time - last_runs[agent_name]) >= (config["interval_minutes"] * 60):
                    if run_counts[agent_name] < config["max_runs"]:
                        print(f"\n🚀 Triggering {config['name']}...")
                        success = self.run_agent(agent_name, config)
                        
                        if success:
                            last_runs[agent_name] = time.time()
                            run_counts[agent_name] += 1
                            print(f"✅ {config['name']} scheduled for next run in {config['interval_minutes']} minutes")
                    else:
                        print(f"⚠️ {config['name']} has reached max runs ({config['max_runs']})")
            
            # Sleep before next check (every 5 minutes)
            time.sleep(300)  # 5 minutes

def main():
    orchestrator = AgentOrchestrator()
    
    print("🎯 Agent Orchestrator initialized")
    print(f"Available agents: {', '.join(AGENT_CONFIG.keys())}")
    print("\nPress Ctrl+C to stop the continuous loop, or enter 'run-all' to execute all agents once.")
    
    try:
        while True:
            # Simple command interface for manual triggering
            if not orchestrator.running_agents:  # Not in continuous mode yet
                cmd = input("\nCommand (run-all / start-continuous / stop): ").strip().lower()
                
                if cmd == "run-all":
                    print("\n🔄 Running all agents sequentially...")
                    results = orchestrator.run_all_agents()
                    print(f"\n{'='*60}")
                    print("AGENT EXECUTION SUMMARY")
                    print(f"{'='*60}")
                    for name, success in results.items():
                        status = "✅ SUCCESS" if success else "❌ FAILED"
                        print(f"{name}: {status}")
                        
                elif cmd == "start-continuous":
                    print("\n🔄 Starting continuous orchestration loop...")
                    orchestrator.run_continuous_loop()
                    
                elif cmd == "stop":
                    print("🛑 Stopping orchestrator")
                    break
                    
            else:
                # In continuous mode, just wait
                time.sleep(60)
                
    except KeyboardInterrupt:
        print("\n\n🛑 Orchestrator stopped by user")
    except Exception as e:
        print(f"\n❌ Orchestrator error: {e}")

if __name__ == "__main__":
    main()
