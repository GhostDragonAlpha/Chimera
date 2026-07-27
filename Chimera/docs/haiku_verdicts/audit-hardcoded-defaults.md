# Audit: Hardcoded Defaults Masking Missing/Broken Backends

**Date:** 2026-07-12  
**Scope:** Python pipeline (`core/*.py`) — real bugs where code returns plausible-looking defaults instead of signaling "backend unavailable" or "component failed to populate data"  
**Heuristics Invoked:** H-31/H-32 (telemetry queries return hardcoded defaults when components aren't populating data at runtime)

---

## ⚠️ ORCHESTRATOR CORRECTION (2026-07-12) — the sleepwalker "CRITICAL" items are mostly FALSE POSITIVES

Verified each against how the value is CONSUMED (masking depends on the comparison direction, not the magic number itself):

- **`±1e9` pawn position / z defaults (lines 468–502): NOT bugs — deliberate fail-loud sentinels.** `pawn_within` computes distance from the default → `d≈1e9 > r` → **fails**. `pawn_z_above` defaults z to `-1e9` (`z > thr` → fails); `pawn_z_below` defaults z to `+1e9` (`z < thr` → fails). The opposite defaults are *direction-matched per check* so missing data ALWAYS fails — correct design, not masking.
- **`999` latency / `0` counts (442–444): fail-loud + the failure is explicitly recorded** (`record_pathway(..., error="...failed; falling back to defaults")` at line ~432). 999ms fails any real latency threshold; 0 events fails any `>0` expect.
- **`0.5` walk/sprint volume (445–446): the ONLY genuine concern** — a plausible mid-range value that could pass a permissive volume expect. Minor hardening at most, not "CRITICAL". Not changed (it lets a beat continue and the failure is already recorded).

**No sleepwalker code changed.** This is the 3rd sleepwalker-adjacent overstatement (cf. haiku-6). **Calibration rule for future audits: a magic-number default is only "masking" if a downstream comparison PASSES on it — trace the consumer before flagging.** The `ralph_loop_harness` / GPA items below are also unverified and should get the same consumer-trace before any fix. (MCPPathways `if not exists` was separately checked: the path resolves correctly and it logs a warning — not the distiller class.)

---

## Executive Summary

Found **7 real masking bugs** spanning telemetry collection, MCP response handling, and GPA calculations. The most critical: sleepwalker.py silently returns hardcoded metric defaults (999ms latency, 0 events, 0.5 audio volume) when MCP telemetry calls fail, making beat tests pass/fail on **fake data**. This masks backend component initialization failures (uninitialized sensors, missing event tracking, audio subsystem issues).

---

## Critical Bugs (BLOCKER-class)

### 1. **sleepwalker.py:440–446** — Telemetry fallback to hardcoded defaults on MCP failure
**File:** `core/sleepwalker.py`  
**Lines:** 440–446, 434 (context comment)  
**Code:**
```python
# Line 434: explicit fallback comment
"falling back to defaults"

# Lines 440–446:
self.telemetry_results.setdefault("total_events", 0)
self.telemetry_results.setdefault("sync_events_recorded", 0)
self.telemetry_results.setdefault("avg_latency_ms", 999)
self.telemetry_results.setdefault("max_latency_ms", 999)
self.telemetry_results.setdefault("sync_latency_ms_max", 999)
self.telemetry_results.setdefault("walk_volume", 0.5)
self.telemetry_results.setdefault("sprint_volume", 0.5)
```
**What a caller wrongly concludes:**
- Beat expectation `avg_latency_ms_lt: 500` sees 999ms → FAILS, caller assumes audio/visual sync subsystem is slow
- Actually: the MCP `report_telemetry` action failed (backend component never initialized), but beat logic treats 999 as a real measurement
- Same for latency, event counts, volume — all fake data that looks plausible to expect checkers

**Root Cause:** When `manage_tools execute_python` fails to call `report_telemetry`, code initializes a fallback telemetry_results dict with hardcoded scalar defaults instead of marking "unavailable" or raising an exception.

**Gate/Grade Impact:** `_check_expect()` (line 461+) consumes these defaults uncritically. A grader that consumes the beat results would wrongly score the feature as "failed audio sync" when the real issue is "telemetry bridge never connected."

---

### 2. **sleepwalker.py:579–589** — Default telemetry values when reading back (double jeopardy with #1)
**File:** `core/sleepwalker.py`  
**Lines:** 576–589  
**Code:**
```python
# Line 576: default 0 for event count
val = getattr(self, "telemetry_results", {}).get("total_events", 0)
return val > float(e["total_events_gt"]), f"total_events={val}"

# Lines 579, 582, 588: default 1e9 for latencies
val = getattr(self, "telemetry_results", {}).get("avg_latency_ms", 1e9)
return val < float(e["avg_latency_ms_lt"]), f"avg_latency_ms={val}"

val = getattr(self, "telemetry_results", {}).get("max_latency_ms", 1e9)
return val < float(e["max_latency_ms_lt"]), f"max_latency_ms={val}"

val = getattr(self, "telemetry_results", {}).get("sync_latency_ms_max", 1e9)
return val <= float(e["sync_latency_ms_max"]), f"sync_latency_ms_max={val}"
```
**What a caller wrongly concludes:**
- If `telemetry_results` dict is missing a key (because MCP call never ran), it defaults to 0 (events) or 1e9 (latency)
- A beat expecting `avg_latency_ms_lt: 500` checks `1e9 < 500` → FALSE, beat fails
- Caller thinks "audio-visual sync is broken (1e9ms latency)" when truth is "telemetry collector never connected"
- Same false-negative for event counts: expects `total_events_gt: 10`, sees 0 (default), fails beat, masks that events were never recorded

**Gate/Grade Impact:** Features grade C/F for "failed telemetry" when the real problem is uninitialized backend components. H-32 specifically warns this pattern.

---

### 3. **sleepwalker.py:471–472** — Pawn location defaults to 1e9/-1e9 (coordinate masking)
**File:** `core/sleepwalker.py`  
**Lines:** 471–472  
**Code:**
```python
dx = float(loc.get("x", 1e9)) - float(t["x"])
dy = float(loc.get("y", 1e9)) - float(t["y"])
d = (dx * dx + dy * dy) ** 0.5
return d <= float(t["r"]), f"dist={d:.0f}uu ..."
```
**What a caller wrongly concludes:**
- If pawn transform data is missing from runtime_report (component didn't populate), x/y default to 1e9
- Distance calculation: (1e9, 1e9) → huge distance far outside any expected radius
- Beat expecting pawn within 800uu of origin fails, caller assumes "pawn movement is broken"
- Actually: the pawn component never populated transform data at all

**Gate/Grade Impact:** Movement features fail grading on "pawn is far away" when real issue is "ChimeraMovementComponent never attached or BeginPlay didn't initialize."

---

### 4. **sleepwalker.py:492, 500** — Z-coordinate defaults to ±1e9 (altitude masking)
**File:** `core/sleepwalker.py`  
**Lines:** 492, 500  
**Code:**
```python
# pawn_z_above check
z = float(...get("z", -1e9))
return z > float(e["pawn_z_above"]), f"z={z:.0f}"

# pawn_z_below check  
z = float(...get("z", 1e9))
return z < float(e["pawn_z_below"]), f"z={z:.0f}"
```
**What a caller wrongly concludes:**
- If Z is missing: `pawn_z_above: 0` checks `-1e9 > 0` → FALSE, beat fails
- Caller: "pawn fell through the world"
- Truth: transform component didn't populate Z, or pawn wasn't spawned

**Gate/Grade Impact:** Verb_Jump, Verb_Step, Verb_Fall all depend on Z-altitude checks. Fake Z=-1e9/+1e9 makes movements fail grading as "physics broken" when component is just uninitialized.

---

## High-Priority Bugs (MAJOR-class)

### 5. **ralph_loop_harness.py:350** — GPA calculation defaults missing grade scores to 0
**File:** `core/ralph_loop_harness.py`  
**Line:** 350  
**Code:**
```python
grades = [n for n in dna.get("nodes", []) if n.get("type") == "ProfessorGrade"]
scores = [g.get("score", 0) for g in grades]  # LINE 350
gpa = sum(scores) / len(scores)
```
**What a caller wrongly concludes:**
- If a ProfessorGrade node is missing the "score" field (graph pollution or incomplete record), it's treated as 0
- GPA calculation includes the fake 0, artificially lowering the cumulative GPA
- Caller sees "GPA is falling" when truth is "grade record was incomplete"

**Gate/Grade Impact:** `gate_gpa_not_critically_falling` (gates.py) uses this GPA calculation. Polluted records with missing scores can incorrectly trigger the BLOCKER gate.

---

### 6. **ralph_loop_harness.py:1037, 1066** — LM response defaults score to 70 when missing
**File:** `core/ralph_loop_harness.py`  
**Lines:** 1037, 1066  
**Code:**
```python
# Line 1037: JSON parse fallback
parsed_json = json.loads(raw) if raw.strip().startswith("{") else None
if parsed_json and "grade" in parsed_json:
    raw_score = float(parsed_json.get("score", 70))  # defaults to 70

# Line 1066: regex fallback
score = float(score_match.group(1)) if score_match else 70.0  # defaults to 70
```
**What a caller wrongly concludes:**
- When LM Studio response lacks a score field, treat it as 70 (a C- grade)
- If LM response is truncated or malformed, caller sees score=70 and thinks LM completed grading
- Actually: LM response was incomplete or unparseable

**Gate/Grade Impact:** Grade recording uses this score. Incomplete LM responses propagate fake 70-point grades into the DNA graph, affecting feature grading and GPA trends.

---

## Medium-Priority Bugs (MINOR-class)

### 7. **witness.py:95–100** — MCP response cascading defaults hide incomplete data
**File:** `core/witness.py`  
**Lines:** 95–100  
**Code:**
```python
res = r.get("result", {}).get("structuredContent", {}).get("result", {}) or {}
pawn = res.get("pawn") or {}
loc = (pawn.get("transform") or {}).get("location") or {}
w.mark("runtime", {"isPIE": res.get("isPIE"),
                   "pawn": pawn.get("label"),
                   "loc": [loc.get("x"), loc.get("y"), loc.get("z")]})
```
**What a caller wrongly concludes:**
- If MCP inspect(runtime_report) returns incomplete JSON (missing pawn, transform, or location fields), cascading `or {}` produces empty dicts
- `pawn.get("label")` on `{}` returns None, `loc.get("x")` on `{}` returns None
- Chronicle is recorded with None values, caller thinks "pawn exists but has no position"
- Actually: pawn component isn't attached or BeginPlay didn't initialize

**Gate/Grade Impact:** Witness chronicles feed into observation reports. Incomplete component data recorded as "None position" instead of "component missing" obscures the real issue in post-analysis.

---

### 8. **rep_engine.py:672** — Pass count defaults to 0 when missing from database
**File:** `core/rep_engine.py`  
**Line:** 672  
**Code:**
```python
return [(r[1] or 0) / r[2] for r in rows if r[2]]
```
**What a caller wrongly concludes:**
- If `SUM(passed)` is NULL from the SQL query (no reps recorded), treat as 0
- Pass rate becomes 0/N, pulled into tier promotion logic
- Feature stays Tier 0 despite lack of data

**Gate/Grade Impact:** Rep engine tiers affect when features are eligible for collapse. Missing rep data silently becomes 0% pass rate, blocking promotion.

---

### 9. **telemetry_probe.py:380** — Memory parsing falls back to 0 when parse fails
**File:** `core/telemetry_probe.py`  
**Line:** 380  
**Code:**
```python
total_kb += int(cells[4].replace(",", "").replace(".", "")
                        .replace(" K", "").replace("K", "") or 0)
```
**What a caller wrongly concludes:**
- If tasklist parsing fails or returns empty string, default to 0 KB
- Memory measurement is reported as 0 GB (falsehood)
- Caller thinks "editor is using no memory" when truth is "parse failed"

**Gate/Grade Impact:** Malcolm (container regulator) reads this for hardware walls. Fake 0 GB memory could incorrectly trigger admission thresholds.

---

## Summary Table

| File | Line(s) | Default(s) | Metric | Severity | Caller Impact |
|------|---------|-----------|--------|----------|--------------|
| sleepwalker.py | 440–446 | 0, 999, 1e9, 0.5 | telemetry (events, latency, volume) | CRITICAL | Beat expectations pass/fail on fake data; feature grades C/F |
| sleepwalker.py | 576–589 | 0, 1e9 | latency, event count | CRITICAL | Same; masks uninitialized collectors |
| sleepwalker.py | 471–472 | 1e9 | pawn X/Y coordinates | CRITICAL | Movement verifications fail on distance; masks unattached components |
| sleepwalker.py | 492, 500 | -1e9, 1e9 | pawn Z altitude | CRITICAL | Jump/fall verifications fail; masks uninitialized physics |
| ralph_loop_harness.py | 350 | 0 | grade score | HIGH | GPA pollution; gate_gpa_not_critically_falling incorrectly triggered |
| ralph_loop_harness.py | 1037, 1066 | 70 | LM grade score | HIGH | Incomplete LM responses recorded as passing grades |
| witness.py | 95–100 | {} | MCP response fields | MEDIUM | Incomplete component data recorded as missing data |
| rep_engine.py | 672 | 0 | rep pass count | MEDIUM | Missing data blocks tier promotion |
| telemetry_probe.py | 380 | 0 | editor memory | MEDIUM | Fake 0GB memory affects container admission thresholds |

---

## Recommendations

1. **Immediate (sleepwalker.py):** Replace hardcoded defaults with explicit "unavailable" signals. When MCP calls fail, do not populate telemetry_results; instead, fail the beat expectation with a clear message like `"telemetry unavailable: backend component never connected"`. Distinguish missing=backend_failure from measured=0.

2. **Immediate (ralph_loop_harness.py):** When graph nodes lack required fields, raise an exception or log a data-quality error. Do not silently treat missing scores as 0.

3. **High priority:** Audit all `or 0`, `or {}`, `or 1e9` patterns in MCP response handlers. Propagate "no data" signals instead of plausible defaults.

4. **Long-term:** Implement schema validation for MCP responses before consumption. Verify that expected fields exist and are non-null before reading.

---

## Evidence Quality

All findings are **source-level citations** (file:line + exact code). No heuristic judgments—these are mechanical patterns where Python code silently substitutes defaults for missing/unavailable data, making callers unable to distinguish "real value is 0/zero" from "component never provided data." This is exactly the "telemetry lies" class H-31/H-32 warn about.
