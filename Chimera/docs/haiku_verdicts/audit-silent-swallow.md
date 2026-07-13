# Silent Error-Swallowing Audit

**Date**: 2026-07-12  
**Agent**: haiku-9  
**Scope**: core/ directory, patterns of silent failure paths  
**Precedent**: heuristic_distiller.py (fixed) where `if not src.exists(): continue` silently skipped entire CLAUDE.md constitution

---

## HIGH RISK

### 1. MCPPathways file disappearance: empty pathway discovery

**File**: `core/ralph_loop_harness.py:1182-1184`

```python
def _parse(self) -> None:
    if not self.pathways_path.exists():
        logger.warning(f"MCP Pathways file not found: {self.pathways_path}")
        return
```

**What fails silently**: If `docs/MCP_PATHWAYS.md` is missing or moved, the constructor silently returns with an empty `self._pathways` dict. Subsequent calls to `find(feature_type)` return `[]` (no pathways discovered). The Ralph Loop continues as if no MCP integrations exist, silently degrading to default/fallback behavior.

**Evidence**: Line 1256 instantiates `MCPPathways()` in `__init__`, line 1567 calls `find()` expecting pathways. If file doesn't exist, `find()` always returns `[]`, agents proceed without known working MCP tool sequences.

**Impact**: Features bypass proven MCP pathways, reverting to generic/slower alternatives. A missing config file produces no alert but silently changes system behavior.

---

### 2. KeyError on missing fallback key in FEATURE_TO_SCHOOL

**File**: `core/ralph_loop_harness.py:1461`

```python
schools = FEATURE_TO_SCHOOL.get(feature_type, FEATURE_TO_SCHOOL["Model"])
```

**What fails silently (or not—raises KeyError)**: The nested bracket lookup `FEATURE_TO_SCHOOL["Model"]` will raise `KeyError` if `"Model"` key is ever removed or corrupted in the dict. Unlike the safer pattern at line 925 (`FEATURE_TO_SCHOOL.get(feature_type, FEATURE_TO_SCHOOL.get("Model", []))`), this risks an unhandled exception.

**Safer pattern exists**: Line 925 in the same file uses `FEATURE_TO_SCHOOL.get("Model", [])` as final fallback, guaranteeing no KeyError.

**Impact**: Inconsistency in fallback safety; dictionary mutation or initialization bug could crash feature research mid-cycle without recoverable error context.

---

### 3. Build.cs silently skipped if not found

**File**: `core/build_orchestrator.py:585-587`

```python
if not build_cs_path.exists():
    print(f"Warning: {build_cs_path} not found, skipping Build.cs update")
    return
```

**What fails silently**: If `Chimera/Source/Chimera/Chimera.Build.cs` doesn't exist, the entire method returns without updating module dependencies. Build.cs is a critical project manifest; its absence means the project is in an inconsistent state. This warning-then-return pattern masks a real misconfiguration.

**Evidence**: The method is called from the build pipeline to inject missing module dependencies. If the file doesn't exist, those dependencies are never recorded, but the pipeline continues as if success occurred.

---

## MEDIUM RISK

### 4. Ralph Loop MCP reader thread: bare except with pass

**File**: `core/ralph_loop_harness.py:613, 619, 803`

```python
# Line 613:
except: pass

# Line 619:
except: pass

# Line 803:
except: pass
```

**What fails silently**: MCP response parsing in a background thread swallows ALL exceptions. If the MCP stream is malformed, truncated, or the stdio bridge is broken, the error is silently ignored and the thread exits. The calling code waits forever for a response that will never arrive.

**Impact**: MCP communication failures produce no diagnostic; the system hangs indefinitely.

---

### 5. JSON load with silent None return

**File**: `core/agent_tunnel.py:180-181`

```python
try:
    return json.loads(p.read_text(encoding="utf-8"))
except Exception:
    return None
```

**What fails silently**: Any JSON parsing or file I/O error returns `None` without logging. Malformed session state, file corruption, or permission errors are invisible to the caller.

**Evidence**: Used at line 179-180 to load session state; callers must check for None and handle gracefully, but there's no breadcrumb about WHY the state is None (corruption? missing? permission?).

---

## LOW RISK

### 6. Decomposer template loading with fallback

**File**: `core/decomposer.py:141-145`

```python
if TEMPLATES_PATH.exists():
    try:
        return json.loads(TEMPLATES_PATH.read_text(encoding="utf-8"))
    except Exception:
        pass
```

**Status**: LOW RISK (fallback exists). If the file doesn't exist or is corrupted, the method falls through to FOUNDING_TEMPLATES and writes them out. Silent, but safe.

---

## SUMMARY

| File | Line | Pattern | Severity | Hidden Failure |
|------|------|---------|----------|---|
| ralph_loop_harness.py | 1182–1184 | `if not exists(): return` | **HIGH** | MCP pathways silently empty |
| ralph_loop_harness.py | 1461 | Unsafe dict fallback `["Model"]` | **HIGH** | KeyError if dict corrupted |
| build_orchestrator.py | 585–587 | `if not exists(): return` | **HIGH** | Build.cs deps never recorded |
| ralph_loop_harness.py | 613, 619, 803 | `except: pass` in thread | **MEDIUM** | MCP stream errors invisible, hangs |
| agent_tunnel.py | 180–181 | `except Exception: return None` | **MEDIUM** | State corruption undiagnosed |

**Recommendation**: 
- File-missing patterns (MCPPathways, Build.cs) should **raise** or at least log ERROR + record to graph for investigation.
- Bare `except: pass` in I/O code (MCP reader, JSON parse) should be specific and logged.
- Use consistent safe fallback patterns (nested `.get(key, fallback)` not bracket lookup).
