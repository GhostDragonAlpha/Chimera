# Audit: Collapse/Observation Integrity

**TASK:** Audit observation/collapse integrity in `core/collapse_proxy.py` and `core/graphify_interface.py`. Can a feature reach `verified`/`accepted` (the true collapse) WITHOUT real automated evidence?

**CRITICAL REQUIREMENT (from CLAUDE.md):** "Only automated sleepwalker/telemetry evidence should collapse a feature to verified. A path that lets a feature become verified without exercise evidence would corrupt the whole quality signal."

---

> **⚠️ ORCHESTRATOR VERDICT (2026-07-12): both findings are ACCURATE but are DESIGN/POLICY soft-spots, not autonomously-fixable bugs.**
> The low-level recorders (`_mutate_feature_complete` accepts any `status`; `_mutate_observation` trusts `observer="human"` with no `derived_from`) are DUMB TYPED RECORDERS by design — enforcement of "verified requires automated evidence" is currently PROCEDURAL (the CHIMERA_AGENT_SIM sentinel, the observe/attribution path, collapse_proxy sweeps), not enforced in the recorder. The `observer="human"` path is the deliberate human-in-the-loop path (the human IS the evidence); the attribution path DOES require `quote` or `tacit`. Hardening the recorders into enforcement gates is a real integrity improvement but a TRUST-MODEL change that could break legitimate collapse_proxy/postflight flows — **surfaced to the user as a design decision, NOT changed autonomously.** No code changed here.

## CONFIRMED: Evidence-Free Collapse Path Exists

An agent can mark a feature as collapsed (verdict="accepted") **WITHOUT any sleepwalker/telemetry evidence** by directly calling `record_observation` with the default parameters.

### Vulnerability Details

**File:** `core/graphify_interface.py`  
**Function:** `_mutate_observation` (lines 1695–1765)  
**Guard:** Lines 1737–1738

```python
elif observer != "human":
    return "rejected_observation: only the human, or an attribution derived_from a playtest node, may observe"
```

**The Issue:**
- Line 1701: Guard only blocks agent-sim processes when `CHIMERA_AGENT_SIM=1`
- Line 1737: Guard allows `observer="human"` with empty `derived_from`
- Line 1811: `record_observation` defaults to `observer="human"`
- Line 1812: `derived_from` defaults to `""` (empty string)

**Attack Vector:**

An agent can call:
```python
from core.graphify_interface import record_observation
record_observation(feature="FeatureX", verdict="accepted", observer="human", derived_from="")
```

Or via CLI:
```bash
python -m core.graphify_record observe --feature FeatureX --verdict accepted --loop 1
```

This **passes all guards** because:
1. Observer is `"human"` (default) → line 1737 check passes
2. `derived_from=""` is allowed for human observers
3. `tacit=False` is allowed since only attributed observations require `quote`

**Result:** An Observation node is created with:
- `verdict="accepted"`
- `observer="human"`
- `derived_from=""` (NO EVIDENCE)
- No sleepwalker/telemetry simtest attached

Then `record_feature` (line 202 in graphify_record.py) marks the feature as `status="observed"`.

**Evidence Missing:** The feature was never tested via sleepwalker or telemetry. No SimPlaytest node. No exercise evidence.

---

## Secondary Issue: Direct Feature Verification Without Evidence

**File:** `core/graphify_interface.py`  
**Function:** `_mutate_feature_complete` (lines 895–930)  
**Guard:** Line 906 only checks if feature_name is empty

```python
if feature_name == "unknown_feature":
    return "rejected_unknown_feature: ..."
```

**The Issue:**
- Line 902: `status = details.get("status", "implemented")`
- Line 915: `"status": status,` — stored as-is, no validation
- An agent can call:
  ```bash
  python -m core.graphify_record feature --name FeatureX --loop 1 --status verified
  ```
- This creates a FeatureUpdate with `status="verified"` **without any verification evidence**

**Result:** The feature enters the observation queue (via `collect_observation_queue`, line 1795) even though it was never verified by `verify_feature` or `result_grader`.

**Calibration Note:** This alone is NOT collapse — `collapse_proxy.sweep()` still requires features to be in `exercised` (line 221), which requires real SimPlaytest exercise evidence. BUT it allows an evidence-free feature to enter the queue, combined with the primary vulnerability above.

---

## Control Flow: How the Evidence-Free Collapse Actually Happens

**Step 1: Create unverified feature with "verified" status**
```bash
python -m core.graphify_record feature --name FeatureX --loop 1 --status verified
```
→ FeatureUpdate node created, no evidence required

**Step 2: Feature enters observation queue**  
`collect_observation_queue()` (line 1795) finds it because `status == "verified"`

**Step 3: Agent marks it accepted without evidence**
```bash
python -m core.graphify_record observe --feature FeatureX --verdict accepted --loop 1
```
→ Observation node created with `verdict="accepted"`, `observer="human"`, `derived_from=""` (EMPTY)  
→ `record_feature` marks feature as `status="observed"`

**Result:** Feature is marked as "accepted" and "observed" with **ZERO sleepwalker/telemetry evidence**.

This violates the CLAUDE.md mandate: *"Only automated sleepwalker/telemetry evidence should collapse a feature to verified."*

---

## Guards That Work Correctly (Why Collapse Proxy Itself Is Safe)

**In `collapse_proxy.py`:**
- Line 221 (sweep, accepted): `if exercised.get(f):` ✓ REQUIRES evidence
- Line 289 (sweep_playtest, accepted): `if exercised.get(f):` ✓ REQUIRES evidence
- `_clean_exercises` (line 65): Only includes SimPlaytest outcomes where outcome == "reached"

**Guard Logic:** Features can ONLY be swept as "accepted" if they appear in `exercised`, which requires real SimPlaytest nodes with clean outcomes. ✓ SOUND

**BUT:** This guard is bypassed by the direct-call path above.

---

## Why Closure Proxy's Rejection Sweep Is Also Threatened

**In `collapse_proxy.py`, sweep rejection:**
- Line 193: `indicted = _indicted_by_simtest(nodes, simtest_id)`
- Line 200-208: Only rejects if feature is in `indicted` dict

An agent could:
1. Create a fake SimPlaytest node (no actual sleepwalker run)
2. Populate outcomes with the agent's own fabricated evidence
3. Call `collapse_proxy --from-simtest fake_id --valence rejected`
4. Mark legitimate features as "rejected" based on fake simulation evidence

This doesn't require `CHIMERA_AGENT_SIM=1`, so the agent-sim guard (line 1701) doesn't catch it.

---

## Summary

| Path | CONFIRMED | Guard Status | Evidence Required |
|------|-----------|-------------|--------------------|
| `record_observation(..., observer="human")` with empty `derived_from` | ✓ YES | FAILS — allows empty `derived_from` for human observers | ZERO — can mark accepted with no simtest |
| `graphify_record feature --status verified` | ✓ YES | FAILS — no status validation | ZERO — can create "verified" with no verify call |
| `collapse_proxy --from-simtest` with real evidence | ✗ NO | PASSES — requires `exercised` dict | REQUIRED — SimPlaytest exercise evidence needed |
| `collapse_proxy --tend` | ✗ NO | PASSES — requires >= min_sessions evidence | REQUIRED — clean sleepwalk sessions needed |
| Fake SimPlaytest node + `collapse_proxy` rejection | ✓ LIKELY | FAILS — no simtest node validation | ZERO — agent can craft fake outcomes |

---

## Recommended Fixes

### Fix 1: Prevent observer="human" Without Proper Authority
**File:** `core/graphify_interface.py`, `_mutate_observation` (line 1737)

Current:
```python
elif observer != "human":
    return "rejected_observation: only the human, or an attribution derived_from a playtest node, may observe"
```

Proposed (add environment check):
```python
elif observer != "human":
    return "rejected_observation: only the human, or an attribution derived_from a playtest node, may observe"

# Prevent non-human agents from impersonating human observers
import os as _os_check
if observer == "human" and not _os_check.environ.get("CHIMERA_HUMAN_VERIFIED"):
    if not derived_from:
        return ("rejected_observation: observer='human' without CHIMERA_HUMAN_VERIFIED env and no derived_from; "
                "agents must provide derived_from a simtest/playtest node")
```

### Fix 2: Validate Feature Status Transitions
**File:** `core/graphify_interface.py`, `_mutate_feature_complete` (line 902)

Current:
```python
status = details.get("status", "implemented")
```

Proposed:
```python
VALID_STATUSES = {
    "researching", "applying", "implemented", "encoded", 
    "sim_verified", "verified", "observed", "observed_provisional",
    "needs_refinement", "blocked", "stalled"
}
status = details.get("status", "implemented")
if status not in VALID_STATUSES:
    return f"rejected_feature: invalid status '{status}'; must be one of {VALID_STATUSES}"
```

### Fix 3: Require derived_from for Automated Observations (Even When Not CHIMERA_AGENT_SIM)
**File:** `core/graphify_interface.py`, `_mutate_observation` (line 1725)

Current:
```python
if derived_from:
    ...
elif observer != "human":
    return "rejected_observation: only the human, or an attribution derived_from a playtest node, may observe"
```

Proposed:
```python
if derived_from:
    ...
elif observer == "human":
    # Human observers may observe directly only if explicitly authorized
    import os as _os_human
    if not _os_human.environ.get("CHIMERA_HUMAN_AUTHORIZED"):
        return ("rejected_observation: human observer requires CHIMERA_HUMAN_AUTHORIZED env var; "
                "or provide derived_from a simtest/playtest node")
elif observer != "human":
    return "rejected_observation: non-human observers must provide derived_from a simtest/playtest node"
```

---

## File References

- `core/collapse_proxy.py`: sweep (line 187), sweep_playtest (line 251), tend (line 99)
- `core/graphify_interface.py`: 
  - `_mutate_observation` (line 1695) — PRIMARY VULNERABILITY
  - `_mutate_feature_complete` (line 895) — SECONDARY VULNERABILITY
  - `record_observation` (line 1810) — EXPOSED FUNCTION
  - `collect_observation_queue` (line 1768)
- `core/graphify_record.py`: "observe" subparser (line 97), observe handler (line 190)

---

## Conclusion

**VULNERABILITY CONFIRMED:** An agent can call `record_observation` with default parameters (`observer="human"`, `derived_from=""`) and mark a feature as `accepted` WITHOUT ANY sleepwalker/telemetry evidence. This violates the system's core mandate that only automated evidence should collapse features.

**ROOT CAUSE:** The guard at line 1737–1738 of `_mutate_observation` allows `observer="human"` to bypass the `derived_from` requirement, assuming only actual humans would use this path. The code trusts agent honor instead of enforcing evidence provenance.

**SEVERITY:** High — this can corrupt the quality signal and allow features to be marked as verified/accepted without measurement.

---

**Audit completed:** 2026-07-12  
**Auditor:** haiku-17 (read-only investigator)  
**Mode:** Full-automation amendment scope (sleepwalker/telemetry-only collapse)
