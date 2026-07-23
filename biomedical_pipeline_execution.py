#!/usr/bin/env python3
"""
Biomedical Research Methodology Integration Pipeline
Execute sequential agent pipeline with parallel phases for concurrent experiments.
"""

import subprocess
import sys
import os
from datetime import datetime
import json

class BiomedicalPipeline:
    def __init__(self):
        self.project_dir = r"E:\PythonChimera"
        self.agents_dir = os.path.join(self.project_dir, "agents")
        self.results = {}
        self.start_time = None

    def run_agent(self, agent_name, script_path, phase_num):
        """Run a single agent as subprocess."""
        print(f"\n{'='*80}")
        print(f"PHASE {phase_num}: {agent_name}")
        print('='*80)

        start = datetime.now()
        try:
            # Run the agent script
            cmd = [sys.executable, os.path.join(self.agents_dir, script_path)]
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.project_dir,
                universal_newlines=True
            )

            # Stream output
            for line in process.stdout:
                print(line.strip())

            process.wait()
            end = datetime.now()
            duration = (end - start).total_seconds()

            if process.returncode == 0:
                self.results[agent_name] = {
                    "status": "completed",
                    "duration_seconds": duration,
                    "timestamp": end.isoformat(),
                    "phase": phase_num
                }
                print(f"\n[SUCCESS] PHASE {phase_num} COMPLETE: {agent_name}")
            else:
                self.results[agent_name] = {
                    "status": "failed",
                    "returncode": process.returncode,
                    "timestamp": end.isoformat(),
                    "phase": phase_num
                }
                print(f"\n[FAILED] PHASE {phase_num} FAILED: {agent_name}")

            return process.returncode == 0

        except Exception as e:
            end = datetime.now()
            self.results[agent_name] = {
                "status": "error",
                "error": str(e),
                "timestamp": end.isoformat(),
                "phase": phase_num
            }
            print(f"\n[ERROR] PHASE {phase_num} ERROR: {agent_name}")
            print(f"   Error: {e}")
            return False

    def run_parallel_agents(self, agents):
        """Run multiple agents in parallel."""
        import threading

        threads = []
        results_lock = threading.Lock()

        def thread_target(agent_name, script_path, phase_num):
            success = self.run_agent(agent_name, script_path, phase_num)
            with results_lock:
                self.results[agent_name]["success"] = success

        for agent_info in agents:
            agent_name = agent_info["name"]
            script_path = agent_info["script"]
            phase_num = agent_info["phase"]

            thread = threading.Thread(
                target=thread_target,
                args=(agent_name, script_path, phase_num)
            )
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

    def generate_report(self):
        """Generate comprehensive pipeline report."""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()

        print("\n" + "="*80)
        print("BIOMEDICAL RESEARCH PIPELINE EXECUTION REPORT")
        print("="*80)
        print(f"Execution Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')} - {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total Duration: {total_duration:.2f} seconds")

        # Summary statistics
        completed = sum(1 for r in self.results.values() if r.get("status") == "completed")
        failed = sum(1 for r in self.results.values() if r.get("status") == "failed")
        errors = sum(1 for r in self.results.values() if r.get("status") == "error")

        print(f"\nEXECUTION SUMMARY:")
        print(f"  Total Phases: {len(self.results)}")
        print(f"  Completed: {completed}")
        print(f"  Failed: {failed}")
        print(f"  Errors: {errors}")
        print(f"  Success Rate: {completed/len(self.results)*100:.1f}%")

        # Detailed results per phase
        print("\nPHASE RESULTS:")
        for agent_name, result in self.results.items():
            status = result.get("status", "unknown").upper()
            duration = result.get("duration_seconds", 0)
            timestamp = result.get("timestamp", "")

            print(f"\n  {agent_name}:")
            print(f"    Status: {status}")
            print(f"    Duration: {duration:.2f}s")
            print(f"    Timestamp: {timestamp}")

        # Save report to JSON
        report = {
            "pipeline": "biomedical_research_integration",
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "total_duration_seconds": total_duration,
            "summary": {
                "total_phases": len(self.results),
                "completed": completed,
                "failed": failed,
                "errors": errors,
                "success_rate_percent": completed/len(self.results)*100 if self.results else 0
            },
            "phases": self.results
        }

        report_path = os.path.join(self.project_dir, "biomedical_pipeline_report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)

        print(f"\n[Pipeline report saved to: {report_path}]")
        return completed == len(self.results)  # All phases completed successfully

    def run_pipeline(self):
        """Execute the complete biomedical research pipeline."""
        self.start_time = datetime.now()

        print("="*80)
        print("BIOMEDICAL RESEARCH METHODOLOGY INTEGRATION PIPELINE")
        print("="*80)
        print(f"Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nEXECUTION PROTOCOL:")
        print("  Phase 1: Research Materials (Biological Sampling)")
        print("  Phases 2-4: Parallel Experiments (Validation, Recombination, Integration)")
        print("  Phase 5: Documentation Update (Knowledge Base)")

        # Phase 1: Single agent - Research Materials
        print("\n" + "-"*80)
        print("PHASE 1: RESEARCH MATERIALS (Biological Sampling)")
        print("-"*80)
        phase1_success = self.run_agent(
            "Research Agent",
            "research_agent.py",
            1
        )

        if not phase1_success:
            print("\n⚠️ Phase 1 failed. Continuing with remaining phases...")

        # Phases 2-4: Parallel agents - Concurrent experiments
        parallel_agents = [
            {"name": "Validation Agent", "script": "validation_agent.py", "phase": 2},
            {"name": "Recombination Agent", "script": "recombination_agent.py", "phase": 3},
            {"name": "Integration Agent", "script": "integration_agent.py", "phase": 4}
        ]

        print("\n" + "-"*80)
        print("PHASES 2-4: PARALLEL EXPERIMENTS (Concurrent Testing)")
        print("-"*80)
        self.run_parallel_agents(parallel_agents)

        # Phase 5: Documentation Update - Knowledge Base
        print("\n" + "-"*80)
        print("PHASE 5: DOCUMENTATION UPDATE (Knowledge Base)")
        print("-"*80)
        phase5_success = self.run_agent(
            "Documentation Agent",
            "documentation_agent.py",
            5
        )

        # Generate final report
        success = self.generate_report()

        if success:
            print("\n✅ BIOMEDICAL RESEARCH PIPELINE EXECUTION COMPLETE")
        else:
            print("\n⚠️ PIPELINE EXECUTION COMPLETED WITH ISSUES")

        return success

if __name__ == "__main__":
    pipeline = BiomedicalPipeline()
    pipeline.run_pipeline()
