# Sequential Agent Chain - Orchestrator Setup

## Overview
This document describes the sequential agent chain for continuous genetics pipeline progress. The main orchestrator agent runs in the foreground and spawns sub-agents sequentially, waiting for each to complete before starting the next.

## Agent Sequence (Chain Order)

1. **Research Agent** → Search for missing material scans
2. **Validation Agent** → Analyze rendered children images  
3. **Recombination Agent** → Test two-parent genetic recombination
4. **Integration Agent** → Validate membrane shape integration
5. **Documentation Agent** → Update docs and DNA graph

## How It Works

### Main Orchestrator Agent
- Runs in foreground (visible CLI output)
- Spawns sub-agents sequentially using chain mode
- Waits for each agent to complete before next spawn
- Can be steered/paused/stopped at any time
- Maintains context across all agents

### Sub-Agent Execution Flow
```
Orchestrator → Research Agent (complete) → Validation Agent (complete) → 
Recombination Agent (complete) → Integration Agent (complete) → 
Documentation Agent (complete) → Loop back to start
```

## Configuration

### Chain Definition
```python
Agent(
    subagent_type="general-purpose",
    prompt="Run sequential genetics pipeline workflow...",
    chain=[
        {agent: "research_agent", task: "Research missing materials..."},
        {agent: "validation_agent", task: "Validate rendered images..."},
        {agent: "recombination_agent", task: "Test recombination..."},
        {agent: "integration_agent", task: "Test membrane integration..."},
        {agent: "documentation_agent", task: "Update documentation..."}
    ],
    async: false,  # Runs synchronously, visible in CLI
    model: "anthropic/claude-sonnet-4"  # Or your preferred model
)
```

## Steering Commands

While the chain is running, you can use:

### `steer_subagent` - Redirect mid-run
```python
steer_subagent(
    agent_id="orchestrator_agent_id",
    message="Skip validation step and move to recombination"
)
```

### `get_subagent_result` - Check status
```python
get_subagent_result(agent_id="orchestrator_agent_id")
```

### Stop/Resume
- Press Ctrl+C to stop current agent
- Use `resume` command to continue from where it stopped

## Output Visibility

All agent outputs are visible in the conversation:
- Each sub-agent's work is shown as it executes
- Results and findings appear immediately
- Errors and issues are reported in real-time
- Final summary provided by orchestrator

## Benefits of This Approach

✅ **Full visibility** - See every step in CLI  
✅ **Steerable** - Redirect workflow mid-execution  
✅ **Sequential** - One agent completes before next starts  
✅ **Contextual** - Maintains project context across agents  
✅ **Flexible** - Easy to modify chain order or add steps  

## Usage

### Start the Sequential Chain
```python
Agent(
    subagent_type="general-purpose",
    prompt="Execute sequential genetics pipeline workflow...",
    chain=[...],  # See above
    async: false
)
```

### Monitor Progress
Watch the conversation for real-time updates from each agent.

### Steer Mid-Execution
Use `steer_subagent` to redirect or modify the workflow.

---

*This setup provides maximum control and visibility for your automated genetics pipeline.*
