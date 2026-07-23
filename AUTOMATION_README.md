# Automated Sequential Workflow System

## Overview

The Chimera project now runs an **automated sequential agent pipeline** that continuously processes materials, validates results, tests recombination, integrates with membrane shapes, and updates documentation. Agents run **one at a time in order**, waiting for each to complete before starting the next.

## Agent Sequence (Continuous Loop)

1. **research_materials.py** - Search for missing material scans (grass, rock, metal, ice)
2. **visual_validation_agent.py** - Automated analysis of rendered children images
3. **test_recombination.py** - Test two-parent genetic recombination with existing genomes
4. **test_membrane_integration.py** - Validate class genomes with membrane shapes (clothe/displace/scatter)
5. **update_documentation.py** - Update task_progress.md and DNA graph records

After completing step 5, the workflow loops back to step 1 and continues indefinitely.

## How to Start

### Manual Start (Foreground)
```bash
cd E:/PythonChimera
python sequential_orchestrator.py
```

The orchestrator will run agents sequentially in a continuous loop until stopped with Ctrl+C.

### Background Service (Windows)
For persistent background operation, use Windows Task Scheduler or a service wrapper:

```powershell
# Example using PowerShell background job
Start-Job -ScriptBlock { python sequential_orchestrator.py } -Name "ChimeraAutomation"
```

## Output and Logs

All agent outputs are logged to `agent_logs/`:

- **Log files**: `agent_name_TIMESTAMP.log` - Full stdout/stderr for each run
- **JSON reports**: `*_report.json` - Structured analysis results
- **Cycle summaries**: `cycle_XXX_summary.json` - Per-cycle status and success rates

## Monitoring

### Check Recent Activity
```bash
# List recent logs
ls agent_logs/*.log | Select-Object -Last 5

# View latest cycle summary
cat agent_logs/cycle_*_summary.json | Select-Object -Last 1
```

### Agent Status Dashboard
Create a simple monitoring script to check overall health:

```python
# monitor_status.py
import json, glob, os
from pathlib import Path

logs = sorted(glob.glob("agent_logs/cycle_*_summary.json"))
if logs:
    with open(logs[-1]) as f:
        summary = json.load(f)
    print(f"Last cycle: {summary['cycle']}")
    print(f"Success rate: {summary['success_rate']:.1f}%")
    for agent, passed in summary['results'].items():
        status = "✅" if passed else "❌"
        print(f"  {status} {agent}")
```

## Troubleshooting

### Agent Not Starting
- Check Python environment: `python --version` should be 3.8+
- Verify dependencies: `pip list | grep -E "numpy|PIL"`
- Look for errors in agent log files

### High Failure Rate
- Review individual agent logs in `agent_logs/`
- Check if required data exists (e.g., rendered images, class genomes)
- Validate file paths and permissions

### Workflow Stuck
- Kill the orchestrator process: Ctrl+C
- Clean up any hanging subprocesses
- Restart with fresh Python environment

## Customization

### Modify Agent Sequence
Edit `AGENT_SEQUENCE` in `sequential_orchestrator.py`:

```python
AGENT_SEQUENCE = [
    "research_materials.py",
    "visual_validation_agent.py", 
    "test_recombination.py",
    "test_membrane_integration.py",
    "update_documentation.py"
]
```

### Adjust Timeouts
Change `timeout` parameter in `run_agent_script()` (default: 3600 seconds = 1 hour).

### Add New Agents
Create new agent script, add to sequence, ensure it returns exit code 0 on success.

## Integration with Project Infrastructure

### DNA Graph Recording
The documentation agent automatically records observations and feature nodes in the project's DNA graph via `core/graphify_record`.

### Task Board Updates
The task_progress.md file is updated after each workflow cycle to reflect current status and NEXT steps.

### Git Integration
All changes are committed automatically (when configured) or ready for manual commit.

## Best Practices

1. **Monitor regularly** - Check agent_logs daily for any failures
2. **Validate manually** - Human review of rendered images still essential
3. **Keep logs clean** - Archive old logs weekly to manage disk space
4. **Test new agents** - Run individual agents before adding to sequence
5. **Document changes** - Update this README when modifying workflow

## Success Metrics

Track these metrics in cycle summaries:

- **Agent success rate**: Should be >90% for healthy workflow
- **Cycle completion time**: Monitor for performance degradation
- **Data generation**: Number of new class genomes, renders, DNA records created
- **Error patterns**: Identify recurring issues to fix systematically

## Conclusion

This automated sequential workflow ensures continuous progress on the genetics pipeline without manual intervention. The system is designed to be robust, self-documenting, and easy to extend as the project evolves.

---

*Created: 2026-07-23 | Last updated: 2026-07-23*
