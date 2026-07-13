# Phantom Pain Verdict: sleepwalker PIE Guard

## Pain Statement (id: phase_33cc2d55125bc551:P1)
"sleepwalker may still attempt PIE if runtime_report is not checked properly."

**Context**: `core/sleepwalker.py` is the AI playtester that executes beat scripts in Play-In-Editor (PIE). Before attempting to start PIE, it should CHECK a `runtime_report` (editor/PIE availability) and BAIL if conditions aren't met. This pain worries the guard is missing or weak, allowing sleepwalker to attempt PIE without proper validation.

---

## ⚠️ ORCHESTRATOR CORRECTION (2026-07-12) — supersedes the CONFIRMED verdict below → **REFUTED**

The verdict below is a **FALSE POSITIVE**. It was written from a wrong premise (that "proceed when `isPIE` is absent/falsy" is a defect) without checking the `isPIE` contract or the upstream guard. On investigation:

1. **The contract: absent `isPIE` == `False` == "no live PIE" everywhere.** `core/research_auth.py:152,311` read it as `result_data.get("isPIE", False)`. So the guard at line 628 (`if rt.get("isPIE"):`) is a **PIE-COLLISION guard by design** — skip only when a live PIE definitely exists; otherwise proceed. Treating missing `isPIE` as "safe to start" is correct, not a bug.
2. **Editor readiness IS guarded — upstream.** Lines 602–626 wrap `_runtime()` in try/except: if the editor is unreachable, `_runtime()` throws → `ensure_editor()` self-heals or the run skips ("editor unreachable"). The isPIE check is not responsible for reachability.
3. **The proposed fix would REGRESS sleepwalker.** "Bail unless `isPIE` is explicitly `False`" would make the playtester skip **every normal idle run** where the report omits `isPIE` — breaking the nightly rhythm the pain claims to protect.

**Net: the guard is correct; no code change made.** The one genuine sliver (a *reachable* editor whose `runtime_report` returns malformed non-error data) is marginal and not what the verdict described.

**Calibration lesson:** this verdict used the fewest tool calls of the fleet (5) and never inspected the `isPIE` contract or the upstream try/except. Low-investigation "CONFIRMED"s are the least trustworthy — always verify a confirmed finding against the actual data contract before acting.

---

## Verdict: CONFIRMED

**The guard exists but is INSUFFICIENT for proper runtime_report validation.**

---

## Evidence

### 1. Guard Location and Implementation
**File**: `core/sleepwalker.py`  
**Lines**: 627–646

```python
# PIE-collision guard (prerequisite for nightly rhythm): check isPIE=false first.
if rt.get("isPIE"):
    record_pathway(
        "sleepwalker",
        "pie_collision_guard",
        "blocked",
        {"reason": "live session exists (isPIE=true)"},
    )
    # skip and note it
    chronicle = self.w.finalize()
    return {...}  # early exit
self._call("control_editor", {"action": "play"})  # LINE 647
```

The guard ONLY checks: `if rt.get("isPIE"):` — if isPIE is truthy (true).

### 2. What the Guard Does NOT Check
The guard is a **single boolean check** that only verifies PIE is not already running. It does NOT:

1. **Verify isPIE field presence**: If `runtime_report` returns a dict without an `isPIE` field, `rt.get("isPIE")` returns `None` (falsy), and the guard silently passes without proper validation.
2. **Validate runtime_report completeness**: No check that the runtime_report is valid, complete, or recent.
3. **Verify editor readiness for PIE**: The guard only checks if PIE is already active (`isPIE=true`). It does NOT check that the editor is actually READY to start PIE (e.g., no other blocking conditions, editor fully responsive).
4. **Handle missing or invalid runtime_report**: If `runtime_report` fails silently or returns incomplete data after `ensure_editor()` succeeds (line 626), sleepwalker proceeds blindly.

### 3. Execution Flow to PIE Start
**File**: `core/sleepwalker.py`, `run()` method, lines 598–647

```python
def run(self, keep_pie: bool = False) -> dict:
    # LINE 603: Get runtime_report
    try:
        rt = self._runtime()
    except Exception:
        from core.unblock import ensure_editor
        ok, note = ensure_editor()
        if not ok:
            # ... return early with error
            return {...}
        rt = self._runtime()  # LINE 626: Try again after heal

    # LINE 628: Single guard check
    if rt.get("isPIE"):
        # ... skip and return early
        return {...}

    # LINE 647: START PIE (no additional validation)
    self._call("control_editor", {"action": "play"})
    
    try:
        time.sleep(settle)
        for beat in self.spec.get("beats", []):
            # ... execute beats
            rt = self._runtime()  # Only AFTER PIE starts do we check again
```

**Critical path**: The ONLY validation before line 647 (`play`) is the single isPIE check at line 628. If that check passes (isPIE is falsy or missing), sleepwalker barrels straight into PIE without:
- Verifying isPIE==False explicitly
- Checking other runtime_report fields
- Validating editor responsiveness

### 4. Missing Explicit Readiness Check
Compare with witness.py (lines 94–98), which properly extracts and uses runtime_report:
```python
r = c.call("inspect", {"action": "runtime_report"})
res = r.get("result", {}).get("structuredContent", {}).get("result", {}) or {}
w.mark("runtime", {"isPIE": res.get("isPIE"), ...})
```

Sleepwalker's `_runtime()` (line 169–170) returns the extracted result dict, but sleepwalker NEVER validates:
- That result dict is non-empty
- That required fields (isPIE, pawn, worldName, etc.) are present
- That values are in expected ranges

---

## Root Cause
The comment at line 627 says "check isPIE=false first," implying intent to verify isPIE is explicitly FALSE before proceeding. But the actual code only checks `if rt.get("isPIE"):` — a one-way gate that skips only if isPIE is TRUE. This allows sleepwalker to proceed if:
- isPIE field is missing entirely from runtime_report
- isPIE is None or any falsy value (not just False)
- runtime_report is incomplete or stale but technically returns without error

---

## Impact
Sleepwalker CAN attempt PIE (call `play` at line 647) even when:
1. Editor is not fully ready or responsive
2. runtime_report is incomplete or invalid
3. Prior recovery (`ensure_editor()`) was incomplete

Beats then fail at execution time (lines 656+), wasting PIE sessions and producing false evidence.

---

## DISPOSITION
`phase_33cc2d55125bc551:P1:refuted` (orchestrator-corrected; see banner at top)

The guard is a correct PIE-COLLISION check given the contract that absent `isPIE` == not-in-PIE; editor reachability is guarded upstream (try/except + ensure_editor). The originally-proposed hardening would regress the nightly rhythm. No code change made.
