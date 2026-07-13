# Audit: Module-Level Import-Time Side Effects

**Date:** 2026-07-12  
**Scope:** `core/*.py` (114 files scanned)  
**Method:** AST inspection + manual verification of top-level (module scope) code execution

---

## Summary

**HIGH PRIORITY FINDINGS:** 1  
**Files with module-level side effects:** 1

### Risk Classification

| Finding | Type | Severity | File:Line |
|---------|------|----------|-----------|
| JSON file I/O + stdout at import time | Crash + State mutation | **HIGH** | `core/_preflight_check.py:10-11, 13-58` |

---

## Detailed Findings

### HIGH: `core/_preflight_check.py` — Module-Level File I/O + Execution

**Location:** `core/_preflight_check.py` lines 5-58

**Issue:** The entire module is executed at import time (no guarding under functions or `if __name__ == "__main__":`).

**Statements executing at import:**

| Line | Statement | Effect |
|------|-----------|--------|
| 5 | `sys.path.insert(0, r'E:\PythonChimera\Chimera\core')` | Modifies sys.path (state mutation) |
| 10 | `kg = json.loads(kg_path.read_text(encoding='utf-8'))` | **FILE I/O:** Reads `docs/chimera_knowledge_graph.json` |
| 11 | `dna = json.loads(dna_path.read_text(encoding='utf-8'))` | **FILE I/O:** Reads `docs/chimera_dna_graph.json` |
| 13-58 | `print(...)` + data processing (loops, filtering) | Prints to stdout; processes kg/dna at module scope |

**Consequences of importing this module:**

1. **Crash on missing files:** If `docs/chimera_knowledge_graph.json` or `docs/chimera_dna_graph.json` do not exist, import fails with `FileNotFoundError`
2. **Crash on unreadable files:** If files exist but are unreadable (permissions, encoding), import fails with `OSError` or `UnicodeDecodeError`
3. **Unwanted stdout:** Importing the module (e.g., to check for a function) will print diagnostic output to stdout
4. **State mutation:** `sys.path` is modified for any process that imports this module
5. **Slow import:** JSON parsing at import time adds latency to any import chain
6. **Requires runtime state:** Cannot be imported until after Unreal has run and generated logs (if that's what populates the JSON files)

**Current usage:** No other core/ modules import this file (confirmed via grep). However, it is a **landmine** if ever imported as part of a larger test suite or automated system.

**Fix required:** Move all executable code under `if __name__ == "__main__":` block.

---

## Verification Results

**Other files checked for similar patterns:**
- `core/fix_stalled.py` — ✅ CLEAN (was a previous offender; now guarded under `if __name__ == "__main__":`)
- `core/interpreter.py`, `core/validator.py`, `core/dsl_workflow_orchestrator.py` — ✅ CLEAN (file I/O inside `__init__` methods, not module scope)
- `core/telemetry_probe.py`, `core/witness.py`, `core/circadian.py` — ✅ CLEAN (path definitions only; I/O inside functions)
- `core/metronome.py`, `core/perpetual_orchestrator.py`, `core/ralph_loop_harness.py` — ✅ CLEAN (path definitions only)

**Search patterns applied:**
- Module-level `open()`, `json.load()`, `json.dump()`
- Module-level `read_text()`, `write_text()`
- Module-level `subprocess.*`, `requests.*`, `urllib.*`
- Module-level `.stat()`, `.glob()` calls
- Module-level file access to `Saved/Logs` or other runtime paths

---

## Recommendations

1. **URGENT:** Rewrite `core/_preflight_check.py` to guard all executable code:
   ```python
   if __name__ == "__main__":
       # ... move all lines 5-58 here
   ```

2. **Add import safety test:** Verify that importing any `core/*.py` module does not trigger file I/O or stdout, e.g.:
   ```bash
   python3 -c "import sys; import io; sys.stdout = io.StringIO(); from core import some_module"
   ```

3. **Document the pattern:** Add guidance to CLAUDE.md or SUCCESSOR_RUNBOOK.md prohibiting module-level side effects.

---

## Additional Findings: Test Files

**MED: Test files with module-level file I/O** (less critical — intentional test setup)

The following test files perform file I/O at module scope to set up test environments BEFORE importing the modules under test:

| File | Lines | Pattern | Notes |
|------|-------|---------|-------|
| `test_faculty.py` | 14-46 | Creates temp dir; writes test curriculum + constitution | Intentional; env-redirect before import |
| `test_curriculum.py` | 14-25 | Sets environment variables; defines temp paths | Same pattern; no actual file I/O until functions called |
| Others (glob: `test_*.py`) | ? | Similar setup patterns | Test files use module-level env setup as convention |

**Risk:** Low (these are standalone test scripts meant to be run directly, not imported by production code). However, if any test file is imported by another module, it will trigger setup side effects.

**Note:** This is a recognized pattern in the codebase — the docstrings of these files explicitly state "Standalone assert-script" and "Run: python ...". The pattern is intentional but nonstandard.

---

## Conclusion

**Severity breakdown:**
- **HIGH (blocks import):** 1 file: `core/_preflight_check.py` (lines 10-11, 13-58)
- **MED (test-only, intentional):** ~5 test files with module-level setup (acceptable for tests)

The `_preflight_check.py` issue is the only genuine production-code problem and is isolated and easy to fix.

No other core/ production modules exhibit unguarded import-time side effects.
