# Sequential Agent Chain - Orchestrator Setup

<!-- CHIMERA-LAW -->
> **RULE 0 — EVERY MEMBRANE IS A THEORY. STATE IT BEFORE YOU BUILD IT.** Three parts, all three
> required: a **STATEMENT** someone could disagree with · a **PREDICTION** you have not measured
> yet · a **FALSIFIER** named *before* the run. **A description survives any result; a theory can
> lose.** No falsifier, no build.
>
> **RULE 1 — DERIVE IT BEFORE YOU TRAIN IT.** A parameter sweep is an admission the derivation was
> not done. Before any run, any sweep, any "let's try N variants": trace the variables and show the
> equations close. If you are choosing a number, you broke the chain and substituted taste for a
> law. Ask what QUESTION each variant answers — if the answer is "which number is best", STOP.
>
> **RULE 0 IS ENFORCED AT S-1 VALIDATE** — every port tested alone, and `port_test()` REFUSES to
> register a test that names no falsifier. The model it feeds: `docs/THE_COMPILER.md` — ports →
> primitives → programs → parser → runtime → calibration.
>
> **[docs/THE_LAW.md](docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 26 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

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
