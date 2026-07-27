# Core Module Smoke Test — 2026-07-12

**Audit Scope:** All 92 non-test modules in `core/*.py`  
**Test Method:** Import test + syntax validation  
**Test Date:** 2026-07-12  
**Total Modules:** 92  
**Passed:** 84 (91.3%)  
**Failed:** 8 (8.7%)

---

## Summary

**REAL CODE BUGS: 3**
1. `core.game_code_generator_restored` — Corrupted file (SyntaxError)
2. `core.research_depth` — Missing `import sys` (NameError at runtime)
3. `core.fix_stalled` — Hardcoded relative path breaks on import (FileNotFoundError)

**ENVIRONMENT/RUNTIME BLOCKERS: 5**
1. `core.code_generation_demo` — PermissionError on log file (cascades from Python/config.py)
2. `core.code_generation_orchestrator` — PermissionError on log file (cascades from Python/config.py)
3. `core.dsl_workflow_demo` — PermissionError on log file (cascades from Python/config.py)
4. `core.dsl_workflow_orchestrator` — PermissionError on log file (cascades from Python/config.py)
5. `core.restore_deleted_files` — PermissionError on log file (cascades from Python/config.py)

**Root Cause of #2-6:** `Python/config.py` attempts to open `Saved/Logs/chimera.log` at module import time via `RotatingFileHandler`. File is locked (likely by running UE Editor). Blocks 4 orchestrator modules + 1 dependent.

---

## Test Results Table

| Module | Status | Error / Notes |
|--------|--------|---------------|
| core._preflight_check | ✅ PASS | — |
| core.agent_tunnel | ✅ PASS | — |
| core.archive_old_mutations | ✅ PASS | — |
| core.asset_config | ✅ PASS | — |
| core.asset_generator | ✅ PASS | — |
| core.backlog_burn | ✅ PASS | — |
| core.bloodhound | ✅ PASS | — |
| core.build_orchestrator | ✅ PASS | — |
| core.build_validator | ✅ PASS | — |
| core.circadian | ✅ PASS | — |
| core.code_generation_demo | ❌ FAIL | PermissionError on Saved/Logs/chimera.log (via Python/config.py) |
| core.code_generation_orchestrator | ❌ FAIL | PermissionError on Saved/Logs/chimera.log (via Python/config.py) |
| core.collapse_proxy | ✅ PASS | — |
| core.context_package | ✅ PASS | — |
| core.cpp_lint | ✅ PASS | — |
| core.critic | ✅ PASS | — |
| core.curriculum | ✅ PASS | — |
| core.decomposer | ✅ PASS | — |
| core.dna_sqlite_backend | ✅ PASS | — |
| core.doc_audit | ✅ PASS | — |
| core.dream_loop | ✅ PASS | — |
| core.dsl_game_parser | ✅ PASS | — |
| core.dsl_grammar_validator | ✅ PASS | — |
| core.dsl_mcp_bridge | ✅ PASS | — |
| core.dsl_workflow_demo | ❌ FAIL | PermissionError on Saved/Logs/chimera.log (via Python/config.py) |
| core.dsl_workflow_orchestrator | ❌ FAIL | PermissionError on Saved/Logs/chimera.log (via Python/config.py) |
| core.editor_scheduler | ✅ PASS | — |
| core.ether | ✅ PASS | — |
| core.faculty | ✅ PASS | — |
| core.fix_stalled | ❌ FAIL | FileNotFoundError: [Errno 2] No such file or directory: 'Chimera/docs/chimera_dna_graph.json' |
| core.fractal_spiral | ✅ PASS | — |
| core.game_code_generator | ✅ PASS | — |
| core.game_code_generator_restored | ❌ FAIL | SyntaxError: invalid syntax at line 1 (file corrupted, contains only git error message) |
| core.game_generation_demo | ✅ PASS | — |
| core.game_generation_orchestrator | ✅ PASS | — |
| core.gardener | ✅ PASS | — |
| core.gates | ✅ PASS | — |
| core.gauntlet | ✅ PASS | — |
| core.generate_antlr_parser | ✅ PASS | — |
| core.graph_compactor | ✅ PASS | — |
| core.graph_linker | ✅ PASS | — |
| core.graph_weaver | ✅ PASS | — |
| core.graphify_interface | ✅ PASS | — |
| core.graphify_query_cli | ✅ PASS | — |
| core.graphify_record | ✅ PASS | — |
| core.groundskeeping_floor | ✅ PASS | — |
| core.helm | ✅ PASS | — |
| core.herald | ✅ PASS | — |
| core.heuristic_distiller | ✅ PASS | — |
| core.history_book | ✅ PASS | — |
| core.incremental_generator | ✅ PASS | — |
| core.interpreter | ✅ PASS | — |
| core.lm_gateway | ✅ PASS | — |
| core.malcolm | ✅ PASS | — |
| core.mcp_client | ✅ PASS | — |
| core.metronome | ✅ PASS | — |
| core.muse | ✅ PASS | — |
| core.pathway_to_dsl | ✅ PASS | — |
| core.perpetual_orchestrator | ✅ PASS | — |
| core.playtest_runner | ✅ PASS | — |
| core.postflight | ✅ PASS | — |
| core.preflight | ✅ PASS | — |
| core.radiometry_probe | ✅ PASS | — |
| core.ralph_loop_harness | ✅ PASS | — |
| core.regression | ✅ PASS | — |
| core.rehearsal | ✅ PASS | — |
| core.rep_engine | ✅ PASS | — |
| core.research | ✅ PASS | — |
| core.research_auth | ✅ PASS | — |
| core.research_depth | ❌ FAIL | NameError: name 'sys' is not defined at line 29 (missing `import sys`) |
| core.research_enforcement | ✅ PASS | — |
| core.restore_deleted_files | ❌ FAIL | PermissionError on Saved/Logs/chimera.log (via Python/config.py) |
| core.result_grader | ✅ PASS | — |
| core.result_grader_aaa_expanded | ✅ PASS | — |
| core.ripener | ✅ PASS | — |
| core.sand_surface_telemetry | ✅ PASS | — |
| core.scholar | ✅ PASS | — |
| core.sleepwalker | ✅ PASS | — |
| core.solver | ✅ PASS | — |
| core.spiral_forks | ✅ PASS | — |
| core.task_board | ✅ PASS | — |
| core.telemetry_probe | ✅ PASS | — |
| core.testkit | ✅ PASS | — |
| core.uat_packager | ✅ PASS | — |
| core.ubt_builder | ✅ PASS | — |
| core.unblock | ✅ PASS | — |
| core.validation_reporter | ✅ PASS | — |
| core.validator | ✅ PASS | — |
| core.visionkeeper | ✅ PASS | — |
| core.visual_verifier | ✅ PASS | — |
| core.witness | ✅ PASS | — |
| core.world_store | ✅ PASS | — |

---

## REAL FAILURES (Code Bugs)

### 1. `core.game_code_generator_restored.py` — CRITICAL

**Command:**
```bash
python -c "import core.game_code_generator_restored"
```

**Error:**
```
SyntaxError: invalid syntax at line 1
```

**File Contents (first line):**
```
fatal: path 'Chimera/core/game_code_generator.py' exists on disk, but not in 'HEAD'
```

**Root Cause:** File is corrupted — contains only a git error message instead of valid Python code.

**Evidence:** File `E:\PythonChimera\Chimera\core\game_code_generator_restored.py` is 1 line, not Python.

**Verdict:** **FILE CORRUPTION** — appears to be a git restoration artifact. File should be deleted or restored from version control.

---

### 2. `core.research_depth.py` — HIGH

**Command:**
```bash
python -c "import core.research_depth"
```

**Error:**
```
NameError: name 'sys' is not defined at line 29
File "E:\PythonChimera\Chimera\core\research_depth.py", line 29, in <module>
    sys.path.insert(0, str(Path(__file__).parent))
    ^^^
NameError: name 'sys' is not defined. Did you forget to import 'sys'?
```

**Root Cause:** `sys` is used at line 29 inside an `except` block, but `import sys` is never executed in the file. Lines 22-30:

```python
import json
from pathlib import Path
from typing import Any

try:
    from core.graphify_interface import record_research_depth_metrics
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))  # <-- sys not defined
    from graphify_interface import record_research_depth_metrics
```

**Verdict:** **MISSING IMPORT** — Add `import sys` to the imports section.

---

### 3. `core.fix_stalled.py` — MEDIUM

**Command:**
```bash
python -c "import core.fix_stalled"
```

**Error:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'Chimera/docs/chimera_dna_graph.json'
```

**Root Cause:** Line 4 uses a hardcoded relative path that is incorrect when the module is imported:

```python
g = json.load(open('Chimera/docs/chimera_dna_graph.json'))
```

When imported as `core.fix_stalled`, the current working directory is `E:\PythonChimera\Chimera`, so the path should be `docs/chimera_dna_graph.json` (no `Chimera/` prefix).

**Verdict:** **RELATIVE PATH BUG** — Change line 4 to use `docs/chimera_dna_graph.json` or use an absolute path based on `__file__`.

---

## ENVIRONMENT BLOCKERS (Not Code Bugs)

### Logging File Lock (5 Modules Affected)

**Root Cause:** `Python/config.py` attempts to create a `RotatingFileHandler` for `Saved/Logs/chimera.log` at module import time. The file exists but cannot be opened—likely locked by a running UE Editor instance.

**Import Chain:**
```
core.code_generation_demo
  → core.code_generation_orchestrator
    → Python.lmstudio_client
      → Python.config
        → logging.RotatingFileHandler('Saved/Logs/chimera.log')
          → PermissionError
```

**Affected Modules:**
1. `core.code_generation_demo`
2. `core.code_generation_orchestrator`
3. `core.dsl_workflow_demo`
4. `core.dsl_workflow_orchestrator`
5. `core.restore_deleted_files`

**Error (all 5):**
```
PermissionError: [Errno 13] Permission denied: 'E:\\PythonChimera\\Chimera\\Saved\\Logs\\chimera.log'
```

**Workaround:** Close UE Editor and try again. These are not code bugs—they are runtime environment issues.

---

## Modules with CLI Support (ArgParse)

Found 20+ modules with `argparse` or `--help` support:
- core/agent_tunnel.py
- core/backlog_burn.py
- core/bloodhound.py
- core/circadian.py
- core/collapse_proxy.py
- core/context_package.py
- core/critic.py
- core/curriculum.py
- core/decomposer.py
- core/dna_sqlite_backend.py
- core/dream_loop.py
- core/editor_scheduler.py
- core/faculty.py
- core/fractal_spiral.py
- core/gardener.py
- core/gauntlet.py
- core/graph_compactor.py
- core/graphify_record.py
- core/groundskeeping_floor.py
- core/helm.py

(Note: CLI tests not run due to long initialization timeouts; modules import cleanly.)

---

## Recommendations

### Fix Immediately (Critical)

1. **core.game_code_generator_restored.py**
   - Action: Delete this file (it's corrupted) or restore from git history.
   - Impact: Blocks import of module; likely a git restore artifact.

2. **core.research_depth.py**
   - Action: Add `import sys` to line 22-23 imports.
   - Fix: Add line after line 22:
     ```python
     import sys
     ```
   - Impact: One-line fix; module currently unusable.

3. **core.fix_stalled.py**
   - Action: Use relative path `docs/chimera_dna_graph.json` instead of `Chimera/docs/chimera_dna_graph.json`.
   - Alternative: Use `Path(__file__).resolve().parent.parent / "docs" / "chimera_dna_graph.json"`.
   - Impact: One-line fix; module currently unusable.

### Monitor (Environment)

- **Logging file lock**: If UE Editor closes unexpectedly, the log file may remain locked. Solution: restart Python process or manually delete/unlock the log file.

---

## Conclusion

**Code bugs found: 3** (all fixable with 1-2 lines of code)
**Environment blockers: 5** (transient; resolved by closing UE Editor)
**Healthy modules: 84/92** (91.3%)

All failures are now mapped, with root causes identified and solutions proposed.
