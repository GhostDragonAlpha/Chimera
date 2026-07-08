# Manual Steps for Playtest Verification

## Overview

The pipeline compiles and links all automation tests successfully, but headless test execution requires a running UE Editor instance. This is documented in [`playtest_runner.py`](../../core/playtest_runner.py:290).

## Why Tests Are Skipped

When the pipeline runs, `PlaytestRunner._execute_ue_automation()` tries multiple strategies:
1. `UnrealEditor-Cmd.exe -nullrhi` (headless)
2. `UnrealEditor.exe -nullrhi` (editor with null renderer)
3. Various render backends

If none produce valid automation output, tests are marked **SKIPPED** — they compiled and linked fine, but the UE automation framework needs an interactive editor session to execute.

## Manual Execution Steps

### Option 1: Via UE Editor UI (Recommended)

1. Launch `Chimera.uproject` in Unreal Editor
2. Navigate to the **Test Automation** window:
   - Menu: `Window > Test Automation`
3. In the Test Automation panel, select **ChimeraTests** from the dropdown
4. Click **Run All** or select individual tests

### Option 2: Via Command Line (After Editor Launch)

1. Open UE Editor with the project loaded
2. Press `~` to open the Console
3. Type and execute:
   ```
   Automation RunTests ChimeraTests
   ```
4. Results will appear in the Output log

### Option 3: Via UnrealEditor-Cmd.exe (Interactive)

```powershell
& "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe" ^
  "E:\PythonChimera\Chimera\Chimera.uproject" ^
  -ExecCmds="Automation RunTests ChimeraTests; Quit" ^
  -log
```

## Expected Output

When tests execute successfully, you should see in the output log:
```
LogAutomation: Test 'TestName' Passed
LogAutomation: Test 'AnotherTest' Failed
```

Or UE5 format:
```
Test Completed. Result={Passed} Name={TestName}
```

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| "Could not be successfully initialized after it was loaded" | Plugin or module mismatch | Rebuild the project in-editor |
| No automation output | Tests not compiled | Run `Automation RunTests` after build |
| Editor crashes on test execution | Test code bug | Check Output log for crash dump |

## Automation Integration

To automate this in CI/CD:
1. Use a headless build machine with UE installed
2. Add the editor path to `UE_ROOT` environment variable
3. The pipeline will detect it and attempt headless execution automatically

See [`playtest_runner.py`](../../core/playtest_runner.py:53) for detection logic.
