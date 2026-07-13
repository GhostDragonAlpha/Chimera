# Audit Report: Regression Curator Feature Mapping Bug

**Auditor**: haiku-13 (Regression Curator Audit)
**Date**: 2026-07-12
**Status**: BUG CONFIRMED + ONE-LINE FIX IDENTIFIED

## Bug Summary

The `RegressionCurator.mine()` function in `core/regression.py` maps **all 31 rejection observations** to `feature: "unknown"` instead of their actual feature names. The function is reading the wrong node dictionary key.

## Root Cause

**Line 62 of `core/regression.py` reads the wrong key:**

```python
"feature": node.get("feature", "unknown"),
```

The code looks for `node.get("feature")`, but actual rejection nodes in the DNA graph store the feature name under the key `"feature_name"` instead.

## Evidence: Actual Node Structure

Queried all rejection observations from DNA graph (verdict in "rejected", "chaos", "crash"):
- **Total rejection nodes found**: 31 (matches expected count)
- **Key distribution**:
  - `"feature"` (what the code reads): 0 nodes have it
  - `"feature_name"` (what the nodes actually use): 31 nodes have it
  - Other keys: 0

### Sample Node (observation_f629252c5bdbcd07)

```json
{
  "id": "observation_f629252c5bdbcd07",
  "type": "Observation",
  "timestamp": "2026-07-07T00:07:52.427196",
  "feature_name": "Verb_Step",
  "verdict": "rejected",
  "notes": "I have no ability to move my character",
  "observer": "human-via-attribution",
  "derived_from": "playtest_2211898b230aa5eb",
  "quote": "I have no ability to move my character",
  "error_signature": "human_rejection",
  "template_file": "observation/Verb_Step",
  "error_category": "human_rejection"
}
```

**Key finding**: The feature is stored as `"feature_name": "Verb_Step"`, NOT `"feature": ...`.

## Type Filter Verification

The `if node.get("type") != "Observation": continue` filter on line 55 is **CORRECT**:
- All 31 rejection nodes have `"type": "Observation"`
- The verdict filter (line 59) correctly catches `"rejected"`, `"chaos"`, and `"crash"`

The type/verdict filters are working as designed; only the key name is wrong.

## Exact One-Line Fix

**File**: `core/regression.py`  
**Line**: 62

**OLD**:
```python
"feature": node.get("feature", "unknown"),
```

**NEW**:
```python
"feature": node.get("feature_name", "unknown"),
```

## Impact Assessment

After this fix:
- `curator.mine()` will correctly populate the `"feature"` field in returned records with actual feature names (e.g., "Verb_Step", "Verb_Look", "Verb_Bend")
- All 31 rejection observations will map to their correct features instead of "unknown"
- The `propose()` method will generate beat names with real feature names

## Edge Cases & Robustness

- **Empty graph**: `.get("feature_name", "unknown")` safely defaults to "unknown" if the key is missing
- **Malformed nodes**: The default fallback ensures no KeyError exceptions
- **Backward compatibility**: No other code reads `"feature"` from rejection records; this is an internal mapping bug

## Verification Method

To verify the fix works after applying it:

```bash
cd E:\PythonChimera\Chimera
python -m core.regression mine
```

Expected output (sample):
```
Found 31 rejection observations:
  1. observation_f629252c5bdbcd07   Verb_Step                                [rejected]
  2. observation_4f5df1d23ee81c4b   Verb_Look                                [rejected]
  3. observation_44efdff7a36a3d5c   Verb_Bend                                [rejected]
  ...
```

(Instead of all showing "unknown")

---

**Conclusion**: The bug is a simple typo in the dictionary key name. The fix is a one-character change from `"feature"` to `"feature_name"`.
