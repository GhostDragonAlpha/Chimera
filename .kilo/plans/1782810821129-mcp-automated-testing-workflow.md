# MCP-Based Automated Testing Workflow — Final Plan

## Goal

Replace the broken init_unreal.py synchronous startup approach with an MCP-native automated testing workflow that runs after PIE starts, using the McpAutomationBridge plugin native HTTP transport on port 3000. The workflow captures screenshots during gameplay, sends them to LM Studio for AI analysis, and stops PIE automatically. Dual-mode initialization ensures fallback to legacy scripts if MCP is unavailable.

## Design Decisions (Resolved)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Workflow trigger | Automatic on editor startup with retry/backoff + standalone runner | Current approach runs before PIE exists; need post-PIE hook that retries until ready |
| Init mode priority | MCP first, legacy fallback | New workflow is preferred; old scripts preserved as fallback |
| Flight vehicle MCP tools | Use existing control_editor + system_control via console commands | Custom C++ tool definitions require plugin recompilation; console commands sufficient for now |
| Authentication | No auth initially (loopback-only binding) | Local dev security adequate; enable capability token later if LAN access needed |
| Screenshot capture | full_editor_window mode with polling fallback | game_viewport is async and unreliable; full_editor_window returns base64 synchronously |
| LM Studio health check | Check /v1/models before sending screenshots, retry once | Prevents wasted requests when LM Studio restarts or model fails to load |
| Error handling | Graceful degradation: skip AI analysis if LM Studio down, log error and exit if MCP unavailable after 30s | No crashes; existing scripts remain untouched |

## Completed Implementation

### Phase 1: MCP Automation Workflow (All Tasks Complete)

**Task 1: Create mcp_automation_client.py** — Chimera/Python/mcp_automation_client.py (new, ~350 lines)
- MCPTestClient class manages MCP session lifecycle with initialize_session(), call_tool(), _request() methods
- Exponential backoff retry logic (max 10 retries, starting at 100ms, doubling each attempt)
- run_automated_test() orchestrates full workflow: PIE start -> ground screenshots (x2) -> flight mode toggle -> thrust -> flight screenshots (x3) -> AI analysis -> PIE stop
- _analyze_screenshots() and _analyze_single_screenshot() handle LM Studio integration with health checks

**Task 2: Modify init_unreal.py** — Chimera/Python/init_unreal.py (modified, 65 lines)
- Dual-mode startup: tries MCP workflow first, falls back to legacy scripts on failure
- Mode 1: MCP-native automated testing via mcp_automation_client.run_mcp_automated_test()
- Mode 2: Legacy synchronous startup with procedural_game_generator, play_test, runtime_screenshot_playtest

**Task 3: Create run_mcp_test.py** — Chimera/Python/run_mcp_test.py (new, ~60 lines)
- Standalone test runner for manual triggering from UE Python Console or terminal
- Provides run_standalone_test() function that calls mcp_automation_client.run_mcp_automated_test()

**Task 4: Update .mcp.json** — Chimera/.mcp.json (modified, 9 lines)
- Added instructions field describing MCP tools for automated testing (control_editor, system_control, manage_level, inspect)

### Phase 2: Dual-Mode Init and Validation Testing (All Tasks Complete)

**Task 1: Update init_unreal.py — Dual-Mode Startup** — COMPLETED in Phase 1 above
- Replaced MCP-only approach with dual-mode initialization that tries MCP first, falls back to legacy scripts on failure

**Task 2: Create Validation Test Suite** — Chimera/Python/validation_test_suite.py (new, 130 lines)
- Comprehensive validation script that imports and tests all 6 modules independently
- Tests mcp_automation_client, procedural_game_generator, play_test, runtime_screenshot_playtest, screenshot_lmstudio_workflow, unreal_api_operations
- Each test attempts import, verifies expected classes/functions exist, reports PASS/FAIL with error message
- Usage from UE Python Console: from validation_test_suite import run_validation; run_validation()

**Task 3: Add Standalone Usage Examples** — COMPLETED
- play_test.py: Added __main__ block that detects UE Editor mode vs standalone simulation mode and runs full playtest
- runtime_screenshot_playtest.py: Added __main__ block requiring unreal module, exits with error if run standalone


## Affected Boundaries

| Boundary | Impact | Migration Path |
|----------|--------|----------------|
| init_unreal.py | Dual-mode (MCP -> legacy fallback) | No breaking changes; existing scripts untouched |
| mcp_automation_client.py | New dependency for all MCP workflows | Standalone runner independent of editor startup |
| run_mcp_test.py | New standalone test runner | Independent of editor startup |
| validation_test_suite.py | New dependency for backward compatibility testing | Standalone runner independent of editor startup |
| .mcp.json | Added instructions for AI clients | No breaking changes to existing config structure |
| play_test.py, runtime_screenshot_playtest.py | Added __main__ blocks for direct execution | No functional changes to existing behavior |

## Data Flow

UE Editor Startup (PythonScriptPlugin)
    -> init_unreal.py loads
        -> Tries MCP workflow: mcp_automation_client.run_mcp_automated_test()
            -> MCPTestClient.initialize_session() -> HTTP POST /mcp (JSON-RPC)
                -> control_editor action=play -> PIE starts
                    -> Wait 5s for world load
                        -> control_editor action=screenshot (full_editor_window, returnBase64=True) x2
                            -> system_control console_command=bFlightModeEnabled=True
                                -> system_control console_command=thrust input
                                    -> Wait 3s for physics simulation
                                        -> control_editor action=screenshot x3
                                            -> HTTP POST to LM Studio /v1/chat/completions (base64 images)
                                                -> control_editor action=stop -> PIE stops

Standalone Validation (terminal)
    -> python validation_test_suite.py
        -> Validates imports for all modules
            -> Reports pass/fail summary

Fallback Path (if MCP unavailable)
    -> procedural_game_generator.generate_all()
    -> runtime_screenshot_playtest.run_runtime_screenshot_playtest()


## Validation Steps

### Step 1 - Module Import Suite (UE Editor)

Open UE Python Console and run:
from validation_test_suite import run_validation; run_validation()

Expected output: All 6 modules report PASS, summary shows Total: 6/6 modules validated successfully

| # | Module | Expected Classes/Functions |
|---|--------|---------------------------|
| 1.1 | mcp_automation_client | MCPTestClient, run_mcp_automated_test |
| 1.2 | procedural_game_generator | GameConfiguration, generate_all, sync_cpp_project_state |
| 1.3 | play_test | FlightPlayTest, run_playtest |
| 1.4 | runtime_screenshot_playtest | RuntimeScreenshotPlayTest, run_runtime_screenshot_playtest |
| 1.5 | screenshot_lmstudio_workflow | LMSStudioClient, run_screenshot_analysis_workflow, display_lmstudio_response |
| 1.6 | unreal_api_operations | generate_levels_and_actors, create_procedural_level |

### Step 2 - Dual-Mode Startup (Open Chimera.uproject)

Check Output Log for startup message:

If MCP server is running on port 3000:
[INIT] Attempting MCP-based automated test...
[MCP] Workflow completed successfully.

If MCP server is NOT running (fallback):
[WARN] MCP workflow unavailable (...)
[INFO] Falling back to legacy startup scripts...
[LEGACY] Running complete startup workflow...
CHIMERA INITIALIZATION COMPLETE - Legacy workflow finished

| # | Check | Expected Result |
|---|------|-----------------|
| 2.1 | Output Log shows dual-mode message | MCP success OR legacy fallback |
| 2.2 | No crash on startup | Editor remains responsive |
| 2.3 | Existing scripts still work independently | Can call from UE Python Console without errors |


### Step 3 - Standalone Execution (Terminal)

From PowerShell terminal:
python E:\PythonChimera\Chimera\Python\play_test.py

Expected output: [WARN] unreal module not available, simulation mode, no crash.

| # | Check | Expected Result |
|---|------|-----------------|
| 3.1 | play_test.py standalone execution | Simulation mode, no crash |
| 3.2 | runtime_screenshot_playtest.py standalone | Error message + exit code 1 (requires UE Editor) |

### Step 4 - MCP Workflow Integration (Optional, requires MCP server)

If McpAutomationBridge plugin is active on port 3000:
from run_mcp_test import run_standalone_test; run_standalone_test()

Expected flow: MCP session -> PIE start -> ground screenshots -> flight mode -> thrust -> flight screenshots -> AI analysis -> PIE stop.

| # | Check | Expected Result |
|---|------|-----------------|
| 4.1 | MCP connection established | Session initialized message in Output Log |
| 4.2 | Screenshots saved to Screenshots/ directory | ground_*.png and flight_*.png files present |
| 4.3 | AI analysis output in Output Log | Lift-off confirmation or similar from LM Studio |
## Failure Modes

| Scenario | Behavior | Recovery |
|----------|----------|----------|
| MCP server not ready on startup | Retry 10 times with exponential backoff (30s max) | Log error, exit gracefully; user can run standalone runner manually |
| LM Studio not available | Skip AI analysis, still capture screenshots to disk | Screenshots saved locally for later analysis |
| PIE fails to start | control_editor returns error, workflow stops | Log error, no crash; existing scripts unaffected |
| Screenshot capture timeout | _request() times out after 30s per call | Retry once, then skip that screenshot |
| MCP server unavailable on startup (fallback) | Falls back to legacy scripts automatically | No user intervention needed; logs warning |
| Legacy script ImportError | Prints error, exits gracefully | User can run individual scripts manually from UE Python Console |
| Validation test import failure | Reports FAIL with specific module name | Check sys.path configuration in validation_test_suite.py line 59-61 |

## Rollout / Migration Path

1. **Current state** - MCP workflow replaces old synchronous startup; legacy scripts preserved as fallback via dual-mode init_unreal.py
2. **Validation phase** - Run validation suite to confirm all modules import correctly (Step 1)
3. **Production use** - Dual-mode init handles both scenarios automatically on UE Editor launch (Step 2)
4. **Future enhancements** (out of scope) - Custom MCP tools, capability token auth, SSE notifications

## Open Questions (Out of Scope)

- Custom MCP tool definitions for flight vehicle actions - can be added later if console commands prove insufficient
- Capability token authentication - enable when LAN access is needed beyond loopback
- SSE progress notifications for long-running tools - implement when workflow timing becomes critical
