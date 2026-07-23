# Chimera — Deployment Guide


> **Current conventions (2026-07-06):** Pre-Flight is one command: `python -m core.preflight`; Post-Flight: `python -m core.postflight --phase "..." --result "<UBT verbatim>"`. Never hand-write mutation dicts — use the typed helpers (`record_feature`/`record_pathway`/`record_loop`/`record_phase`/`record_grade`/`record_build`) or `python -m core.graphify_record`; mis-keyed writes are rejected with `rejected_*` and every node is auto-stamped `recorded_by`+`run_id`. Generator-owned C++ (Flight, Ship, GameMode, PCG, Missions, Docking, QuantumTravel, Factions, Economy, Save, Combat suite, PirateAI) is regenerated every pipeline run — fix templates in `core/game_code_generator.py`, never the C++. Build failures auto-grade F; non-pass visual verification grades C; stale trees under `Source/` fail the build.

Complete operational reference for building, testing, deploying, and maintaining the Chimera UE 5.8 vehicle simulation project with MCP automation bridge.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Development Setup](#2-development-setup)
3. [Build Process](#3-build-process)
4. [Testing](#4-testing)
5. [Deployment](#5-deployment)
6. [Troubleshooting](#6-troubleshooting)
7. [Monitoring](#7-monitoring)
8. [Backup & Recovery](#8-backup--recovery)

---

## 1. Prerequisites

### Hardware Requirements

| Component | Minimum | Recommended | High-End |
|-----------|---------|-------------|----------|
| RAM | 8 GB | 16 GB | 32 GB |
| Storage | 50 GB free | 100 GB free (SSD) | 200 GB free (NVMe) |
| GPU | DX12 compatible | Dedicated GPU | High-end dedicated GPU |

### Software Stack

| Component | Version | Notes |
|-----------|---------|-------|
| **Unreal Engine** | 5.8 | Installed at `C:\Program Files\Epic Games\UE_5.8` |
| **Visual Studio** | 2022 (17.x) | C++ workload required, MSVC compiler |
| **Python** | 3.10+ | For automation scripts and MCP testing |
| **LM Studio** | Latest | Running on `http://localhost:1234` for AI analysis |

### Verify Installation

```powershell
# Check Python version
python --version

# Check Visual Studio installation
Get-ChildItem -Path "C:\Program Files\Microsoft Visual Studio" -Directory -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.Name -match "2022|2019" } | Select-Object -First 1 Name

# Check Unreal Engine installation
Get-ChildItem -Path "C:\Program Files\Epic Games" -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -match "^UE-" } | Select-Object -First 1 Name

# Verify LM Studio is running
curl http://localhost:1234/api/v1/models
```

### Check Available Models in LM Studio

```bash
python check_models.py
```

Expected output format:
```
qwen3.6-35b-a3b-mtp@iq2_m | loaded=True | vision=False
```

---

## 2. Development Setup

### Step 1 — Clone / Locate the Project

The project resides at `E:\PythonChimera`. Ensure all files are present:

```powershell
Test-Path "E:\PythonChimera\Chimera\Chimera.uproject"
Test-Path "E:\PythonChimera\Chimera\Source\Chimera"
Test-Path "E:\PythonChimera\Chimera\Plugins\McpAutomationBridge"
```

### Step 2 — Open the Project in UE Editor

```powershell
# From E:\PythonChimera
start Chimera\Chimera.uproject
```

The project will auto-compile. If compilation fails:

```powershell
cd Chimera
run_build.bat build
```

### Step 3 — Verify Build Completes Successfully

```powershell
cd Chimera
run_build.bat validate
run_build.bat status
```

Expected `status` output:
```
Last build log: 20260630_170000-build.json
Status:   Success
Time:     2026-06-30T17:00:00
Duration: 45.23s
Errors:   0
```

### Step 4 — Configure Python Environment

Ensure the Python path includes the project scripts directory:

```powershell
# Add to your PYTHONPATH (system or user environment variable)
setx PYTHONPATH "E:\PythonChimera\Chimera\Python"

# Or set per-session
$env:PYTHONPATH = "E:\PythonChimera\Chimera\Python"
```

### Step 5 — Verify MCP Server Configuration

Check `Chimera\Config\DefaultGame.ini`:

```ini
[McpAutomationBridgeSettings]
bEnableNativeMCP=True
NativeMCPPort=3000
bLoadAllToolsOnStart=True
EndpointUrl=http://localhost:1234
```

Verify the MCP server is accessible at `http://localhost:3000/mcp`.

### Step 6 — Verify LM Studio Connectivity

```bash
cd Chimera\Python
python -c "from config import is_endpoint_reachable; print(is_endpoint_reachable('http://localhost:1234'))"
```

Expected output: `True`

---

## 3. Build Process

### Quick Build Commands

All commands are run from `E:\PythonChimera\Chimera`:

| Command | Description |
|---------|-------------|
| `run_build.bat build` | Full rebuild (default) |
| `run_build.bat incremental` | Incremental build (detects changes) |
| `run_build.bat plugins` | Compile only the plugins |
| `run_build.bat validate` | Run post-build validation only |
| `run_build.bat clean` | Clean Intermediate, Saved, Binaries directories |
| `run_build.bat status` | Show last build status and time |

### Full Rebuild

```powershell
cd E:\PythonChimera\Chimera
run_build.bat build
```

This performs:
1. Prerequisites check (UE engine, Visual Studio, disk space)
2. Module compilation via UnrealBuildTool
3. Plugin compilation (`McpAutomationBridge`, `PythonScriptPlugin`)
4. Post-build validation (DLL existence, compile error scan)
5. JSON build summary saved to `E:\PythonChimera\build_logs\`

### Incremental Build

```powershell
cd E:\PythonChimera\Chimera
run_build.bat incremental
```

The pipeline checks for modified `.cpp`, `.h`, and `.cs` files since the last build timestamp. If no changes are detected, the build is skipped with:

```
No source files modified since last build. Skipping incremental build.
```

### Plugin-Only Compilation

```powershell
cd E:\PythonChimera\Chimera
run_build.bat plugins
```

Compiles `McpAutomationBridge` and `PythonScriptPlugin` in dependency order (PythonScriptPlugin first, then McpAutomationBridge).

### Custom Build Targets

Pass arguments through to the PowerShell pipeline:

```powershell
# Custom target/platform/config
cd E:\PythonChimera\Chimera
run_build.bat build -Target ChimeraEditor -Platform Win64 -Config Development

# Shipping (release) configuration
run_build.bat build -Config Shipping

# DebugGame configuration
run_build.bat build -Config DebugGame

# Test configuration
run_build.bat build -Config Test
```

### Clean Build

When encountering stale artifacts or corrupted intermediates:

```powershell
cd E:\PythonChimera\Chimera
run_build.bat clean
run_build.bat build
```

This removes:
- `Intermediate/` — compiler intermediates
- `Saved/` — UE saved data
- `Binaries/` — compiled DLLs
- `DerivedDataCache/` — DDC cache (forces fresh shader compilation)

### Build Output and Logs

Build summaries are written as JSON to `E:\PythonChimera\build_logs\`:

```
E:\PythonChimera\build_logs\
├── 20260630_170000-build.json      # Full build summary
├── 20260630_170045-plugins.json    # Plugin-only build summary
└── 20260630_170100-validation.json # Validation-only summary
```

Each JSON file contains: `Status`, `Timestamp`, `TotalDuration`, `ModulesBuilt`, `PluginsCompiled`, `SuccessCount`, `FailureCount`, `ErrorCount`.

### Build Configuration

Edit `Chimera\BuildScripts\BuildConfig.json` to modify defaults:

| Field | Default | Description |
|-------|---------|-------------|
| `DefaultTarget` | `"ChimeraEditor"` | Main build target |
| `PlatformSettings.DefaultPlatform` | `"Win64"` | Target platform |
| `ConfigurationSettings.DefaultConfiguration` | `"Development"` | Build configuration |

---

## 4. Testing

### MCP Integration Tests

#### Run All Test Categories

```powershell
cd E:\PythonChimera\Chimera\Python
python mcp_integration_test_runner.py
```

This connects to the MCP server at `http://localhost:3000/mcp` and runs all three test categories:
- **inspection** — Actor inspection, properties, components
- **actor_control** — Spawn, transform, component attach/detach
- **level_management** — List levels, streaming dry run, metadata

#### Run Specific Test Categories

```powershell
# Only inspection tests
python mcp_integration_test_runner.py inspection

# Only actor control tests
python mcp_integration_test_runner.py actor_control

# Only level management tests
python mcp_integration_test_runner.py level_management

# Multiple categories
python mcp_integration_test_runner.py inspection actor_control
```

#### Custom MCP Server URL and Report Path

```powershell
python mcp_integration_test_runner.py ^
    --mcp-url "http://localhost:3000/mcp" ^
    --max-concurrent 5 ^
    --report-path "E:\PythonChimera\test_results.json"
```

#### Batch Test Runner

Use the batch script for automated full-suite execution:

```powershell
cd E:\PythonChimera
run_all_tests.bat
```

This runs all categories and saves results to `E:\PythonChimera\test_results.json`.

### Standalone MCP Test

Run from UE Python Console or terminal:

```python
# From UE Python Console
from run_mcp_test import run_standalone_test; run_standalone_test()
```

Or from terminal:

```powershell
cd E:\PythonChimera\Chimera\Python
python run_mcp_test.py
```

### Flight Physics Simulation

```powershell
cd E:\PythonChimera\Chimera\Python
python -c "from flight_simulation import simulate_flight; result = simulate_flight(); print(result)"
```

Or use the standalone entry point:

```powershell
cd E:\PythonChimera\Chimera
python run_flight_physics.py
```

### Screenshot Analysis

Quick single-screenshot lift-off verification:

```powershell
cd E:\PythonChimera\Chimera
python analyze_screenshot.py
```

Full screenshot analysis workflow (PIE → screenshots → LM Studio AI analysis):

```powershell
cd E:\PythonChimera\Chimera
python run_screenshot_analysis.py
```

### Earth-Scale Landscape Verification

```powershell
cd E:\PythonChimera\Chimera\Python
python -c "from tes_earth_scale_analysis import run_earth_scale_verification; print(run_earth_scale_verification())"
```

Verifies:
1. Seamless edge wrapping at landscape boundaries
2. Flat-to-sphere morph formula (`app_radius = actual_radius / distance`)
3. No pop, stutter, or visual tearing during transitions

### Multi-Agent Coordination Tests

```powershell
cd E:\PythonChimera\Chimera\Python

# Default race track scenario (6 agents)
python run_multi_agent.py

# Custom task with parallel execution
python run_multi_agent.py --task "build a desert outpost"

# Sequential mode for debugging
python run_multi_agent.py --sequential

# Override agent count
python run_multi_agent.py --agents 6

# Async fire-and-forget mode
python run_multi_agent.py --async
```

### Test Report Location

All test results are saved to:

```
E:\PythonChimera\test_results.json
```

The JSON report contains: `report_version`, `generated_at`, `mcp_server_url`, `session_initialized`, `execution_time_seconds`, `summary` (total/passed/failed/skipped/pass_rate_percent), and per-category results.

---

## 5. Deployment

### Staging Environment Setup

1. **Build in Test Configuration:**
   ```powershell
   cd E:\PythonChimera\Chimera
   run_build.bat build -Config Test
   ```

2. **Run Full Test Suite:**
   ```powershell
   cd E:\PythonChimera
   run_all_tests.bat
   ```

3. **Verify Build Artifacts:**
   ```powershell
   # Check expected DLLs exist
   Get-ChildItem -Path "E:\PythonChimera\Chimera\Binaries\Win64" -Recurse -Include "*.dll" | Select-Object Name, Length
   
   # Validate build
   run_build.bat validate
   ```

### Production Environment Setup

1. **Build in Shipping Configuration:**
   ```powershell
   cd E:\PythonChimera\Chimera
   run_build.bat clean
   run_build.bat build -Config Shipping
   ```

2. **Verify Shipping Build:**
   ```powershell
   # Check shipping executable exists
   Test-Path "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealGame-Win64-Shipping.exe"
   
   # Validate DLLs
   run_build.bat validate
   ```

3. **Package for Distribution:**
   ```powershell
   # Use UnrealPak to create a pak file
   & "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealPak.exe" ^
       "E:\PythonChimera\Chimera\Saved\Paks\chimera.pak" ^
       "E:\PythonChimera\Chimera\Content\*" -add
   ```

### Deployment Checklist

- [ ] Build completed with zero errors (`run_build.bat status` shows `Errors: 0`)
- [ ] All expected DLLs present in `Binaries\Win64\`
- [ ] MCP server accessible at `http://localhost:3000/mcp`
- [ ] LM Studio running on port 1234
- [ ] Test suite passed (`run_all_tests.bat`)
- [ ] Build logs reviewed for warnings
- [ ] Configuration files verified (`DefaultGame.ini`, `.mcp.json`)

---

## 6. Troubleshooting

### Plugin Not Loading in Editor

**Symptom:** McpAutomationBridge shows as disabled or fails to load in UE Editor.

**Steps:**
```powershell
# 1. Verify plugin .uplugin file exists
Test-Path "E:\PythonChimera\Chimera\Plugins\McpAutomationBridge\McpAutomationBridge.uplugin"

# 2. Recompile plugins only
cd E:\PythonChimera\Chimera
run_build.bat clean
run_build.bat plugins

# 3. Check plugin compilation output in build logs
Get-ChildItem "E:\PythonChimera\build_logs\*plugins.json" | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Get-Content
```

### MCP Connection Failed

**Symptom:** Python scripts report `Failed to initialize MCP session`.

**Steps:**
```powershell
# 1. Verify server is listening on port 3000
netstat -an | FindStr ":3000"

# 2. Test HTTP endpoint directly
curl http://localhost:3000/mcp

# 3. Check DefaultGame.ini configuration
Get-Content "E:\PythonChimera\Chimera\Config\DefaultGame.ini"

# 4. Verify MCP server is enabled (bEnableNativeMCP=True)
```

**If port 3000 is blocked:** Edit `Config\DefaultGame.ini`:
```ini
[McpAutomationBridgeSettings]
NativeMCPPort=3001
```

### LM Studio API Errors

**Symptom:** `[ERROR] Chimera: LM Studio API error: 400` in logs.

**Steps:**
```powershell
# 1. Check if LM Studio is running
curl http://localhost:1234/api/v1/models

# 2. List available models
python check_models.py

# 3. Verify model name matches config
Get-Content "E:\PythonChimera\Chimera\Python\config.py" | Select-String "LM_STUDIO_MODEL"
```

**Common LM Studio issues:**
- Model not loaded: Open the model in LM Studio before running tests
- Vision model required for screenshots: Use a vision-capable model
- Rate limiting: Check `rate_limit_validation.py` output

### Build Fails with Compile Errors

**Symptom:** `run_build.bat build` exits with errors.

**Steps:**
```powershell
# 1. Check the latest build log
Get-ChildItem "E:\PythonChimera\build_logs\*build.json" | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Get-Content

# 2. Clean and rebuild
cd E:\PythonChimera\Chimera
run_build.bat clean
run_build.bat build

# 3. Check for C++ compile errors in log files
Select-String -Path "E:\PythonChimera\build_logs\*.log" -Pattern "error\s+C\d+|fatal\s+error|LNK110[0-9]" | Select-Object -First 20
```

**Common C++ issues:**
- Missing include paths: Verify `Source\Chimera.Build.cs` has correct module dependencies
- Linker errors (LNK): Check for unresolved external symbols in `.cpp` files
- Header conflicts: Ensure all `.h` files have proper include guards (`#pragma once`)

### UE Editor Crashes on Startup

**Steps:**
```powershell
# 1. Clear DerivedDataCache
cd E:\PythonChimera\Chimera
run_build.bat clean

# 2. Verify .uproject file integrity
Get-Content "E:\PythonChimera\Chimera\Chimera.uproject" | Select-String -Pattern "ProjectVersion|EngineAssociation"

# 3. Open with command-line flags for verbose logging
& "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe" ^
    "E:\PythonChimera\Chimera\Chimera.uproject" -log
```

### Python Import Errors

**Symptom:** `ModuleNotFoundError` when running automation scripts.

**Steps:**
```powershell
# 1. Verify PYTHONPATH is set
echo $env:PYTHONPATH

# 2. Add to session if missing
$env:PYTHONPATH = "E:\PythonChimera\Chimera\Python"

# 3. Test import directly
cd E:\PythonChimera\Chimera\Python
python -c "import config; print(config.CHIMERA_PROJECT_ROOT)"
```

---

## 7. Monitoring

### Server Status Checks

#### MCP Server (Port 3000)

```powershell
# Check if port is listening
netstat -an | FindStr ":3000"

# Send a test request to verify responsiveness
curl http://localhost:3000/mcp -Method POST -ContentType "application/json" ^
    -Body '{"jsonrpc":"2.0","method":"initialize","params":[],"id":1}'

# Check LM Studio model availability
python check_models.py
```

#### Build Status

```powershell
cd E:\PythonChimera\Chimera
run_build.bat status
```

### Log Locations

| Log Type | Path | Rotation |
|----------|------|----------|
| Application logs | `E:\PythonChimera\Chimera\Saved\Logs\chimera.log` | 10 MB, 5 backups |
| Build logs (JSON) | `E:\PythonChimera\build_logs\*.json` | 30-day retention |
| Build logs (text) | `E:\PythonChimera\build_logs\build_*.log` | Per-build |

### Viewing Logs

```powershell
# View application log (last 50 lines)
Get-Content "E:\PythonChimera\Chimera\Saved\Logs\chimera.log" -Tail 50

# Search for errors in application log
Select-String -Path "E:\PythonChimera\Chimera\Saved\Logs\chimera.log" -Pattern "ERROR|CRITICAL" | Select-Object -Last 20

# View latest build summary
Get-ChildItem "E:\PythonChimera\build_logs\*build.json" | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Get-Content

# Search for compile errors in all build logs
Select-String -Path "E:\PythonChimera\build_logs\*.log" -Pattern "error\s+C\d+|fatal\s+error"
```

### Diagnosing Problems via Logs

**Common log patterns to search:**

```powershell
# LM Studio connection failures
Select-String -Path "E:\PythonChimera\Chimera\Saved\Logs\chimera.log" -Pattern "LM Studio API error|endpoint not reachable"

# MCP session errors
Select-String -Path "E:\PythonChimera\Chimera\Saved\Logs\chimera.log" -Pattern "Failed to initialize|MCP.*error|session.*failed"

# Compile errors in build logs
Select-String -Path "E:\PythonChimera\build_logs\*.log" -Pattern "LNK110[0-9]|fatal error C|error C\d+"

# Plugin compilation failures
Get-ChildItem "E:\PythonChimera\build_logs\*plugins.json" | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Get-Content | ConvertFrom-Json | Select-Object -ExpandProperty PluginResults
```

### Performance Monitoring

Check UE performance metrics through the ChimeraPerformanceMonitor module:

```python
# From UE Python Console or Python script
from config import GameConfiguration
print(GameConfiguration.ue_game())  # Path to game executable
```

---

## 8. Backup & Recovery

### Save Game Backup Procedures

#### Manual Backup

```powershell
# Locate save games
Get-ChildItem "E:\PythonChimera\Chimera\Saved" -Recurse -Include "*.sav", "*.save" | Select-Object FullName, Length

# Create timestamped backup archive
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backup_dir = "E:\PythonChimera\backups\$timestamp"
New-Item -ItemType Directory -Path $backup_dir -Force

# Backup save data and config
Copy-Item "E:\PythonChimera\Chimera\Saved\*" -Destination "$backup_dir\Saved\" -Recurse -Force
Copy-Item "E:\PythonChimera\Chimera\Config\*.ini" -Destination "$backup_dir\Config\" -Force

# Verify backup integrity
Test-Path "$backup_dir\Saved"
Test-Path "$backup_dir\Config\DefaultGame.ini"
```

#### Automated Backup Script

Create a scheduled task or batch script:

```powershell
# backup_chimera.ps1
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$project_root = "E:\PythonChimera\Chimera"
$backup_base = "E:\PythonChimera\backups"
$backup_path = "$backup_base\$timestamp"

New-Item -ItemType Directory -Path $backup_path -Force | Out-Null

# Backup Saved directory (save games, logs)
Copy-Item "$project_root\Saved" -Destination "$backup_path\Saved" -Recurse -Force

# Backup Config directory
Copy-Item "$project_root\Config" -Destination "$backup_path\Config" -Recurse -Force

Write-Host "Backup complete: $backup_path"
```

### Configuration Restoration

#### Restore from Backup

```powershell
$restore_source = "E:\PythonChimera\backups\20260630_170000\Config"
$project_config = "E:\PythonChimera\Chimera\Config"

# Restore DefaultGame.ini
Copy-Item "$restore_source\DefaultGame.ini" -Destination "$project_config\DefaultGame.ini" -Force

# Restore DefaultEngine.ini
Copy-Item "$restore_source\DefaultEngine.ini" -Destination "$project_config\DefaultEngine.ini" -Force

# Verify restored configuration
Get-Content "$project_config\DefaultGame.ini"
```

#### Config Backup Directory

Configuration backups are stored in `Chimera\Config\Backup\`. To create a backup of current configs:

```powershell
$backup_dir = "E:\PythonChimera\Chimera\Config\Backup"
New-Item -ItemType Directory -Path $backup_dir -Force | Out-Null
Copy-Item "E:\PythonChimera\Chimera\Config\*.ini" -Destination "$backup_dir\" -Force
```

### Full Project Backup

For complete project snapshots including source code:

```powershell
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$full_backup = "E:\PythonChimera\backups\$timestamp"

# Use robocopy for reliable large-file backup
robocopy "E:\PythonChimera\Chimera" "$full_backup\Chimera" ^
    /MIR /COPY:DAT /R:3 /W:5 /XD Intermediate Binaries DerivedDataCache Saved\Paks __pycache__

Write-Host "Full project backup complete: $full_backup"
```

### Recovery After Corruption

If the project becomes corrupted after a bad build or config change:

```powershell
# Step 1: Clean all build artifacts
cd E:\PythonChimera\Chimera
run_build.bat clean

# Step 2: Restore configs from backup (if modified)
Copy-Item "E:\PythonChimera\Chimera\Config\Backup\DefaultGame.ini" ^
    -Destination "E:\PythonChimera\Chimera\Config\DefaultGame.ini" -Force

# Step 3: Rebuild from scratch
run_build.bat build

# Step 4: Verify
run_build.bat validate
run_build.bat status
```

---

## Quick Reference

### Key Ports

| Service | Port | URL |
|---------|------|-----|
| MCP Server | 3000 | `http://localhost:3000/mcp` |
| LM Studio API | 1234 | `http://localhost:1234` |

### Key Paths

| Item | Path |
|------|------|
| Project root | `E:\PythonChimera` |
| UE project | `E:\PythonChimera\Chimera` |
| C++ source | `E:\PythonChimera\Chimera\Source\Chimera` |
| Python scripts | `E:\PythonChimera\Chimera\Python` |
| MCP plugin | `E:\PythonChimera\Chimera\Plugins\McpAutomationBridge` |
| Config files | `E:\PythonChimera\Chimera\Config` |
| Build logs | `E:\PythonChimera\build_logs` |
| Application logs | `E:\PythonChimera\Chimera\Saved\Logs\chimera.log` |
| Test results | `E:\PythonChimera\test_results.json` |

### Essential Commands Cheat Sheet

```powershell
# Build
cd E:\PythonChimera\Chimera && run_build.bat build
cd E:\PythonChimera\Chimera && run_build.bat incremental
cd E:\PythonChimera\Chimera && run_build.bat plugins
cd E:\PythonChimera\Chimera && run_build.bat clean

# Test
cd E:\PythonChimera && run_all_tests.bat
cd E:\PythonChimera\Chimera\Python && python mcp_integration_test_runner.py inspection actor_control level_management

# Monitor
run_build.bat status
Get-Content "E:\PythonChimera\Chimera\Saved\Logs\chimera.log" -Tail 30
netstat -an | FindStr ":3000"
```
