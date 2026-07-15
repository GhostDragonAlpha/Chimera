# Perpetual Orchestrator Mode (chimera-perpetual)

## Purpose
Spawn duty-cycle subagents indefinitely, chaining workflow cycles without terminal completion. Each cycle executes the full CYCLE_PROMPT.md duty agent, records results, and re-spawns the next. The orchestrator itself never completes — it only stops on explicit stop-file or fatal error.

## Execution

1. **Pre-check**: `python -m core.preflight` → abort if GPA < 1.0 (gate_gpa_not_critically_falling).
1.5 **Horizon check (terminal/idle state)**: `python -m core.horizon` → exit code 10 = IDLE
   (board complete, nothing ripens, observation queue empty). On IDLE: run
   `python -m core.horizon --summarize` (writes docs/SESSION_SUMMARY.md), log
   `IDLE-COMPLETE`, and exit cleanly — same graceful path as the stop-file. Never
   spawn duty cycles against an idle horizon.
2. **Spawn duty subagent**: `Agent { subagent_type: "mode-code", prompt: CYCLE_PROMPT_FULL }`
   - Inject the current NEXT item from task_progress.md, or rehearsal's choice if NEXT empty
   - Set timeout 90min (a full duty cycle is ~45min; 90min leaves margin)
3. **Await result**: collect output, error state, build artifacts
4. **Record**: `python -m core.graphify_record cycle --loop N --result <grade> --timestamp <utc>`
5. **Check stop-file**: if `E:\PythonChimera\.STOP_PERPETUAL` exists, delete it and exit (graceful shutdown)
6. **Loop**: increment cycle counter, jump to step 1

## Stop-file contract
- Create `E:\PythonChimera\.STOP_PERPETUAL` (any content) to signal the orchestrator to finish the current cycle and exit cleanly
- The orchestrator checks this between cycles, never mid-cycle
- On exit: final summary printed, no unfinished work left in task_progress.md

## Constraints (locked, no override)
- No `attempt_completion` in the orchestrator loop (prevents terminal closure)
- Each subagent is independent; the orchestrator does NOT edit their output (protected NEXT items)
- If a subagent crashes (timeout, fatal gate), record the failure, pause 5min, then retry (up to 3 retries per cycle)
- The orchestrator's job is **spawning and recording**, not decision-making (decisions stay in rehearsal + the human's veto table)

## Failure recovery
- Subagent timeout after 90min → record as `cycle_failed: timeout` + retry loop (max 3)
- Subagent gate failure (GPA < 1.0) → orchestrator stops, prints alert to stdout, awaits manual intervention or .STOP_PERPETUAL
- MCP/editor down → unblock before retry
- After 3 retries: record failure, pause 10min, try once more, then stop if still broken

## Integration with existing workflow
- The perpetual orchestrator is a **wrapper** around the existing duty cycle (CYCLE_PROMPT.md)
- It does NOT change duty-cycle logic, gates, or laws
- Rehearsal, gardener, sleepwalker, dream_loop continue to run nightly via schtasks (01:00, 02:15)
- The orchestrator's job: keep cycles firing back-to-back during business hours (example: 08:00–18:00)

## Example invocation (manual)
```
# Start perpetual orchestration in foreground
Agent(subagent_type: "mode-orchestrate", prompt: "Run chimera-perpetual mode — spawn duty cycles indefinitely until E:\\PythonChimera\\.STOP_PERPETUAL exists or a fatal gate blocks. Record each cycle, respect subagent output as law, never call attempt_completion.")
```

Or (background task in VS Code):
Create a VS Code task that calls the orchestrator and leaves it running, with output captured to a log file.

## State tracking
Each cycle writes a line to `E:\PythonChimera\Chimera\Saved\Logs\orchestrator.log`:
```
2026-07-08 08:15Z cycle_001 status=started duty_agent_spawned
2026-07-08 08:57Z cycle_001 status=complete grade=B next_item="Demo_Phase2_DemoTerminal" retry_count=0
2026-07-08 09:00Z cycle_002 status=started duty_agent_spawned
...
```

This log is the **single source of truth** for what the perpetual orchestrator did; it is read-only and append-only (never edited by the duty agent).
