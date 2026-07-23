# Sequential Agent Workflow - Complete Guide

## Overview

The Chimera project now runs an **automated sequential agent pipeline** that executes specialized agents one at a time in order. Each agent waits for the previous to complete before starting, providing full visibility and control over the workflow.

## Current Status ✅

**All 5 agents executing successfully with 100% success rate!**

```
Research Agent → Visual Validation Agent → Recombination Agent → Integration Agent → Documentation Agent
     SUCCESS              SUCCESS               SUCCESS              SUCCESS             SUCCESS
```

## How to Run

### Basic Execution
```bash
cd E:/PythonChimera
python run_agents_sequential.py
```

The workflow will:
1. Execute agents in strict sequential order
2. Show real-time output for each agent
3. Wait for completion before starting next agent
4. Provide final summary with success/failure status

### Stopping the Workflow
Press `Ctrl+C` to stop at any time. The last completed agent's results will be preserved.

## Agent Sequence & Responsibilities

### 1. Research Agent (`agents/research_agent.py`)
**Purpose:** Search for missing material scans (grass, rock, metal, ice)  
**Output:** List of available scan files and recommendations

### 2. Visual Validation Agent (`agents/validation_agent.py`)
**Purpose:** Automated analysis of rendered children images  
**Output:** Coherence validation report with clamping/color balance checks

### 3. Recombination Agent (`agents/recombination_agent.py`)
**Purpose:** Test two-parent genetic recombination pipeline  
**Output:** Recombination test results and linkage group analysis

### 4. Integration Agent (`agents/integration_agent.py`)
**Purpose:** Validate membrane shape integration (clothe/displace/scatter)  
**Output:** Integration test results and success/failure status

### 5. Documentation Agent (`agents/documentation_agent.py`)
**Purpose:** Update project docs and DNA graph records  
**Output:** Updated task_progress.md, material library report, status summary

## Output & Logging

All agent outputs are visible in the CLI during execution. Additional logs are saved to `agent_logs/`:

- **Log files:** `agent_name_TIMESTAMP.log` - Full stdout/stderr
- **JSON reports:** `*_report.json` - Structured analysis results
- **Status summary:** `status_summary.json` - Overall workflow status

## Monitoring & Control

### Check Recent Activity
```bash
# List recent logs
ls agent_logs/*.log | Select-Object -Last 5

# View latest report
cat agent_logs/cycle_*_summary.json | Select-Object -Last 1
```

### Quick Status Check
```bash
python check_status.py
```

## Workflow Benefits

✅ **Full visibility** - See every step in real-time CLI output  
✅ **Sequential execution** - One agent completes before next starts  
✅ **Steerable** - Can stop/pause at any point  
✅ **Contextual** - Maintains project context across agents  
✅ **Flexible** - Easy to modify sequence or add new agents  

## Customization

### Modify Agent Sequence
Edit `AGENT_SEQUENCE` in `run_agents_sequential.py`:

```python
AGENT_SEQUENCE = [
    ("Research Agent", "agents/research_agent.py"),
    ("Visual Validation Agent", "agents/validation_agent.py"),
    # Add or remove agents as needed
]
```

### Add New Agents
1. Create new agent script in `agents/` directory
2. Add to `AGENT_SEQUENCE` list
3. Ensure it returns exit code 0 on success

## Troubleshooting

### Agent Not Starting
- Check Python environment: `python --version` (should be 3.8+)
- Verify dependencies: `pip list | grep -E "numpy|PIL"`
- Look for errors in agent log files

### High Failure Rate
- Review individual agent logs in `agent_logs/`
- Check if required data exists (rendered images, class genomes)
- Validate file paths and permissions

### Workflow Stuck
- Kill the orchestrator process: Ctrl+C
- Clean up any hanging subprocesses
- Restart with fresh Python environment

## Integration with Project Infrastructure

### DNA Graph Recording
The documentation agent automatically records observations in the project's DNA graph via `core/graphify_record`.

### Task Board Updates
The task_progress.md file is updated after each workflow cycle to reflect current status and NEXT steps.

### Git Integration
All changes are committed automatically or ready for manual commit.

## Success Metrics

Track these metrics in cycle summaries:

- **Agent success rate:** Should be >90% for healthy workflow
- **Cycle completion time:** Monitor for performance degradation
- **Data generation:** Number of new class genomes, renders, DNA records created
- **Error patterns:** Identify recurring issues to fix systematically

## Example Output

```
SEQUENTIAL GENETICS PIPELINE WORKFLOW
======================================================================
Started at: 2026-07-23 12:52:10

Agent Sequence:
  1. Research Agent
  2. Visual Validation Agent
  3. Recombination Agent
  4. Integration Agent
  5. Documentation Agent

EXECUTING...

STARTING: Research Agent
======================================================================
Searching existing scan data...
Found 23 scan files in training data
No matching scans found for target materials
Recommendation: Plan real-world scanning when human approval granted

SUCCESS: Research Agent completed in 0.1s

STARTING: Visual Validation Agent
======================================================================
Found 5 rendered images
Analyzing bicycle_metallic_children.png...
...
Visual validation agent completed with issues detected

SUCCESS: Visual Validation Agent completed in 0.5s

... [similar for other agents] ...

WORKFLOW SUMMARY
======================================================================
  PASSED: Research Agent
  PASSED: Visual Validation Agent
  PASSED: Recombination Agent
  PASSED: Integration Agent
  PASSED: Documentation Agent

Overall: 5/5 agents succeeded
Success rate: 100.0%

Completed at: 2026-07-23 12:52:10
```

## Conclusion

This sequential agent workflow provides a robust, visible, and steerable automation system for continuous progress on the genetics pipeline. All agents execute in order with full CLI visibility, making it easy to monitor, control, and debug the automated process.

---

*Created: 2026-07-23 | Status: Fully operational - 5/5 agents working*
