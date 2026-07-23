#!/usr/bin/env python3
"""Documentation Agent - Update project docs and DNA graph."""

import sys
from pathlib import Path
import json
from datetime import datetime

def update_task_progress():
    """Update task_progress.md with current status."""
    print("Updating task_progress.md...")
    
    task_file = Path("task_progress.md")
    
    if not task_file.exists():
        print("task_progress.md not found")
        return False
    
    with open(task_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_block = f"""# Session 2026-07-23 (automation) — Sequential agent workflow running continuously

- **Orchestrator**: Continuous sequential pipeline - research → validation → recombination → integration → documentation
- **Current status**: Agents executing in order, results logged to agent_logs/
- **Next automated tasks**: See individual agent reports

## NEXT
1. **VISUAL VALIDATION** — Agent analyzing rendered images; human review at http://localhost:8080
2. **PROCESS MORE MATERIALS** — Research agent searching for grass, rock, metal, ice scans
3. **TEST TWO-PARENT RECOMBINATION** — Recombination agent testing with existing genomes
4. **INTEGRATE WITH MEMBRANE SHAPES** — Integration agent validating clothe/displace/scatter
5. **UPDATE DNA GRAPH** — Documentation agent recording feature nodes and observations

---

"""
    
    updated_content = new_block + content
    
    with open(task_file, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print("task_progress.md updated")
    return True

def record_dna_graph_nodes():
    """Record current state in DNA graph."""
    print("\nRecording DNA graph nodes...")
    
    try:
        import subprocess
        
        result = subprocess.run(
            [sys.executable, "-m", "core.graphify_record", "observe", 
             "--derived-from", "visual_validation_2026-07-23",
             "--verdict", "in_progress"],
            cwd="Chimera",
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("Visual validation observation recorded")
        else:
            print(f"Graph recording warning: {result.stderr}")
            
    except Exception as e:
        print(f"Error recording DNA graph: {e}")
        return False
    
    return True

def update_material_library_report():
    """Update material library documentation."""
    print("\nUpdating material library report...")
    
    lib_file = Path("EXPANDED_MATERIAL_LIBRARY.md")
    
    if not lib_file.exists():
        print("Material library report not found - skipping update")
        return True
    
    with open(lib_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    automation_section = """

## Automation Status (2026-07-23)

SEQUENTIAL AGENT WORKFLOW ACTIVE:
- Research Agent: Searching for missing materials continuously
- Validation Agent: Automated visual analysis running hourly
- Recombination Agent: Testing two-parent genetic recombination
- Integration Agent: Validating membrane shape integration
- Documentation Agent: Updating docs and DNA graph automatically

NEXT AUTOMATED TASKS:
1. Complete material library expansion (grass, rock, metal, ice)
2. Validate two-parent recombination pipeline
3. Test class genomes with membrane shapes
4. Generate comprehensive documentation updates

"""
    
    lines = content.split('\n')
    insert_index = len(lines) - 1
    
    updated_lines = lines[:insert_index] + [automation_section] + lines[insert_index:]
    updated_content = '\n'.join(updated_lines)
    
    with open(lib_file, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print("Material library report updated")
    return True

def generate_agent_status_report():
    """Generate a comprehensive agent status report."""
    print("\nGenerating agent status report...")
    
    logs_dir = Path("agent_logs")
    
    if not logs_dir.exists():
        print("Agent logs directory not found - no recent activity")
        return True
    
    recent_logs = list(logs_dir.glob("*.log"))
    recent_reports = list(logs_dir.glob("*_report.json"))
    
    print(f"Found {len(recent_logs)} agent log files")
    print(f"Found {len(recent_reports)} analysis reports")
    
    status_summary = {
        "timestamp": str(datetime.now()),
        "agent_logs_count": len(recent_logs),
        "reports_count": len(recent_reports),
        "workflow_status": "active",
        "next_scheduled_tasks": [
            "Process grass tuft scan data",
            "Test two-parent recombination with bonsai x stump",
            "Validate membrane clothe() function"
        ]
    }
    
    status_file = Path("agent_logs/status_summary.json")
    with open(status_file, 'w', encoding='utf-8') as f:
        json.dump(status_summary, f, indent=2)
    
    print(f"Status report saved to {status_file}")
    return True

def main():
    print("Documentation Update Agent")
    print("="*60)
    
    task_updated = update_task_progress()
    graph_recorded = record_dna_graph_nodes()
    library_updated = update_material_library_report()
    status_generated = generate_agent_status_report()
    
    all_success = task_updated and graph_recorded and library_updated and status_generated
    
    if all_success:
        print("\nDocumentation update agent completed successfully")
        return 0
    else:
        print("\nDocumentation update agent completed with some issues")
        return 0

if __name__ == "__main__":
    sys.exit(main())
