# Gate & Grader Integrity Audit

**Auditor:** haiku-16 (read-only investigation)  
**Date:** 2026-07-12  
**Scope:** `core/gates.py` (mandatory hard gates) and `core/result_grader.py` (rubric grading)  
**Critical Question:** Can a gate PASS or a grade be A/B when evidence is MISSING/EMPTY/NONE/FAKE?

> **⚠️ ORCHESTRATOR VERDICT (2026-07-12): of the 4 "confirmed", 1 is real, 1 false, 2 not-bugs.**
> - **gate_gpa line 114 (missing `gpa` field → pass): REAL & FIXED** — now falls through to grade-history instead of silently trusting a malformed cumulative node.
> - **gate_gpa line 143 (`else 4.0`): FALSE POSITIVE** — unreachable. `all_grades` is pre-filtered to `grade in grade_map` (line 128) and `len(unique) >= 3` guarantees `scores` non-empty, so the `4.0` fallback is dead code.
> - **gate_envelope line 366 (exception → True): INTENTIONAL** — documented fail-open ("absence of a sensor is not evidence"; Malcolm's philosophy) and it prints the reason. Not a bug.
> - **gate_playtest line 324 (missing `failed` → 0): BENIGN** — "no failures to block on" is reasonable lenience; fail-closed would spuriously block skipped-playtest runs.
> `result_grader.py` correctly fails-loud (missing evidence → 0 → F). Gates are essentially sound.

---

## Executive Summary

**CONFIRMED BUGS: 4**  
**SAFE (fail-loud on missing): Yes** — `result_grader.py` correctly fails on missing evidence.

---

## CONFIRMED BUGS (Pass-on-Missing)

### 1. gate_gpa_not_critically_falling() — Missing GPA value passes as 1.0+

**File:Line** `core/gates.py:114–123`

**Code:**
```python
if overall:
    latest = sorted(overall, key=lambda n: n.get("timestamp", ""), reverse=True)[0]
    gpa = latest.get("gpa")  # line 114: default None
    if gpa is not None and gpa < 1.0:  # line 115: short-circuit if gpa is None
        raise GateViolation(...)
    return True  # line 123: passes if gpa is None
```

**Pass-on-Missing Input:**
- Cumulative GPA node exists in graph but lacks "gpa" field

**Trace:**
1. `latest.get("gpa")` → returns None (missing key)
2. Condition `gpa is not None and gpa < 1.0` → False (first part fails)
3. No exception raised
4. Line 123 returns True (GATE PASSES)

**Impact:** The project's cumulative GPA is unknown, yet gate passes as if GPA ≥ 1.0.

---

### 2. gate_gpa_not_critically_falling() — Invalid grade values default to perfect 4.0

**File:Line** `core/gates.py:142–153`

**Code:**
```python
recent = unique[:10]
scores = [grade_map[g["grade"]] for g in recent if g.get("grade") in grade_map]
avg = sum(scores) / len(scores) if scores else 4.0  # line 143: sentinel 4.0 (A+)

if avg < 1.0:
    raise GateViolation(...)
return True
```

**Pass-on-Missing Input:**
- ProfessorGrade nodes exist but all have `grade="Z"` (invalid) or `grade=None`

**Trace:**
1. Line 128 filters: `and n.get("grade") in grade_map` excludes invalid grades
2. `recent` has entries, but all `g.get("grade")` are not in {"A","B","C","D","F"}
3. Comprehension filters all out: `scores = []` (empty list)
4. Line 143 sentinel: `sum([]) / len([]) if [] else 4.0` → `avg = 4.0` (perfect score)
5. Condition `avg < 1.0` → False (4.0 is not < 1.0)
6. No exception raised
7. Line 153 returns True (GATE PASSES WITH A+ SCORE)

**Impact:** All grades corrupted or missing → gate registers project as A+ academically, no blocker.

**Severity:** Critical — this allows "fixing GPA by deleting all grade records" or silently passing corrupted data.

---

### 3. gate_envelope() — Exception in envelope check passes gate

**File:Line** `core/gates.py:362–371`

**Code:**
```python
def gate_envelope() -> bool:
    try:
        from core.malcolm import check_hard
        breaches = check_hard()
    except Exception as e:
        print(f"  [GATE] envelope unavailable ({e}) — passing open")
        return True  # line 367: passes on ANY exception
    for b in breaches:
        print(...)
    return not breaches
```

**Pass-on-Missing Input:**
- `core.malcolm` module not found, or `check_hard()` raises any exception

**Trace:**
1. `from core.malcolm import check_hard` → ModuleNotFoundError or AttributeError
2. Except clause catches Exception (line 365)
3. Line 367 returns True (GATE PASSES)

**Impact:** The container (hardware/systemic wall enforcement) is unavailable, yet the gate passes. The docstring says "absence of a sensor is not evidence" (correct philosophy), but the code silently suppresses sensor FAILURE (wrong).

**Severity:** High — a system that should block on measured wall breach silently passes when unmeasured.

---

### 4. gate_playtest_no_failures() — Missing test failure count defaults to 0

**File:Line** `core/gates.py:320–332`

**Code:**
```python
def gate_playtest_no_failures(playtest_report) -> bool:
    if playtest_report is None:
        return True  # line 323: null report passes
    failed = playtest_report.summary.get("failed", 0)  # line 324: missing key → 0
    if failed > 0:
        raise GateViolation(...)
    return True
```

**Pass-on-Missing Input:**
- `playtest_report.summary` dict exists but lacks "failed" key (e.g., test harness crashed mid-summary)

**Trace:**
1. `playtest_report.summary.get("failed", 0)` → returns 0 (missing key)
2. Condition `failed > 0` → False (0 is not > 0)
3. No exception raised
4. Line 332 returns True (GATE PASSES)

**Impact:** Playtest summary corrupted or incomplete (missing failure tally) → gate misses failures.

**Severity:** Medium — assumes test framework reliably records failures; a crash that prevents summary completion bypasses the gate.

---

## SAFE PATTERNS (Fail-Loud on Missing)

✅ **result_grader.py** — ALL scoring functions correctly penalize missing evidence:

- `_score_correctness()` line 56: `if total == 0 or criteria_total == 0: return 0.0, note` ← F grade on no tests
- `_score_stability()` line 71: `if t.get("crash_free") is True:` ← only True adds points; None/False/missing adds 0
- `_score_stability()` line 77: `if fps is not None:` ← unmeasured fps scores 0
- `_score_checklist()` line 100: `if c.get(item) is True:` ← only True earns points; missing = 0
- `_score_fidelity()` line 111: `except (TypeError, ValueError): return 0.0` ← non-numeric fidelity = 0 points

**Verdict:** Missing telemetry, checklist, or fidelity data → score = 0 → F grade. Correct fail-loud behavior.

---

## No Issues Found

✅ **gate_no_junk_nodes()** — Empty graph correctly has no junk (line 82–93)  
✅ **gate_provenance_complete()** — Empty graph correctly has no missing provenance (line 162)  
✅ **gate_node_count_bounded()** — Empty graph within ceiling (line 184)  
✅ **gate_build_succeeded()** — Missing "success" key fails with default None → falsy → raises (line 273)  
✅ **gate_auto_fixer_attempted()** — Missing auto_fixer_ran fails (line 288)  
✅ **gate_lm_studio_online()** — Failed request raises, not passes (line 232)  

---

## Remediation

### Priority 1 (Blockers)

**gate_gpa_not_critically_falling() lines 114 & 143:**
- Line 114: Change `if gpa is not None and gpa < 1.0:` to `if gpa is None or gpa < 1.0:` (fail if missing)
  - Or: explicitly `if gpa is None: raise GateViolation("cumulative GPA missing")`
- Line 143: Change sentinel from `4.0` to explicit fail
  - Option A: `if not scores: raise GateViolation("no valid grades recorded")`
  - Option B: Change to `avg = 0.0` (safe fail-low), then `if avg < 1.0: raise`

**gate_envelope() line 366:**
- Change `except Exception as e: print(...); return True` to:
  ```python
  except Exception as e:
      raise GateViolation(
          "gate_envelope",
          f"Container unavailable: {e} — cannot verify hardware/systemic walls",
          "blocker"
      )
  ```

### Priority 2 (High)

**gate_playtest_no_failures() line 324:**
- Validate `playtest_report.summary` exists and is complete before `.get("failed", 0)`
- Or: check both `playtest_report` and `playtest_report.summary` are non-None

---

## Audit Trace Evidence

All findings traced by:
1. Reading complete function implementations
2. Identifying default/missing-evidence code paths
3. Tracing through condition evaluation
4. Confirming gate returns True (pass) rather than raising GateViolation

**Code review method:** Static trace. No execution or test framework used (per audit scope: read-only).

---

## Calibration Notes

Per audit guidance ("a default/missing value is only a BUG if downstream comparison PASSES on it"):

- **gates.py bugs 1–4:** All confirmed; all comparisons PASS on missing/invalid evidence.
- **result_grader.py:** All comparisons explicitly check for presence (`is True`, `is not None`, `is False`); missing evidence always scores zero. No bugs found.

