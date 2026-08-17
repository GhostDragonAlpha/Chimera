# Task 10 — Methodology Gate Compliance Audit (read-only)

## Scope

Verify that `training_gate.py` actually enforces S4 (DERIVE), and
that `methodology_gate.py` correctly scores all 42 membranes.

## S4 context

From CLAUDE.md (line 114-115) and THE_WORKFLOW.md (line 394):

    S0 FRAME · S1 QUESTION · S2 SATURATE · S3 CLASSIFY · S4 DERIVE
    · S5 TRAIN · S6 EMIT · S7 DYAD · S8 RECOMPOSE

S4 (DERIVE) = "the equations close, from the PARENT only."
S5 (TRAIN) is the actual machine-learning training step.

The methodology_gate.py docstring (line 33-36) states:

    "WHAT IT DOES NOT CHECK: whether the physics is right. A membrane
    can pass every column and still be an Earth gait at 0.72 g."

## Finding 1: training_gate.py ENFORCES S4 correctly

### Verification method

Ran the gate with both Earth-derived (invalid) and derived (valid) targets.

**FAIL case (Earth-derived targets):**
```
python tools/training_gate.py --target-speed 1.285 --stride-s 1.127
```
Result: REFUSED
> TARGET SPEED 1.2850 m/s is 1.29x the speed this body derives for itself
> (0.9924). If it came from an Earth dataset, Froude says it becomes
> 1.0915 m/s here.

**PASS case (derived targets):**
```
python tools/training_gate.py --target-speed 0.9924 --stride-s 1.173
```
Result: PASS
> PASS -- every target is Froude-consistent with the world this body
> stands in.

### What the gate checks (3 S4 conditions)

1. **Froude consistency of target speed**: v^2/(g*L) must match the
   world's gravity. If speed came from Earth, it is scaled by
   sqrt(g_here / g_earth) before comparison. (training_gate.py:86-94)

2. **Stride time matches the body's own derivation**: stride_s must
   equal 2 * step_time_s from theHuman/numbers.json within 6% TOL.
   (training_gate.py:113-127)

3. **No hard-coded Earth speeds in trainers**: --trainer flag scans
   physics.py for "X.XXXX m/s" literals and checks the worst one.
   (training_gate.py:149-157)

### Conclusion for Task 10a

**PASS.** training_gate.py enforces S4. It refuses training targets
not derived from this world's physics. The gate correctly:
- Scales Earth speeds via Froude number
- Compares stride times against the membrane's own derivation
- Scans trainers for hard-coded constants
- Returns exit code 1 on refusal, 0 on pass

## Finding 2: methodology_gate.py — 2 FAILs in "units" column

### Verification method

Ran `python tools/methodology_gate.py` (all 42 membranes, tree order).

### Results

    form        42/42
    derives     42/42
    emits       42/42
    free        42/42
    units       40/42   (2 FAIL)
    dups        42/42
    typed       42/42
    predicts    42/42

### The 2 failures

| Membrane | Blind key | Physics location | Nature of value |
|----------|-----------|-------------------|-----------------|
| theGround | reference_load_vs_threshold | story/marbleMaze/physics.py:389 | `press / q0` — dimensionless ratio |
| theHuman | footprint_deeper_on_earth_by | story/marbleMaze/physics.py:1193 | `print_earth / print_depth` — dimensionless ratio |

### Root cause

The `unit_of_key` function (story/folding.py:285) assigns units by:
1. Explicit override in units.json
2. Suffix pattern match (e.g., `_m`, `_s`, `_rad`, `_Nm`)
3. Per-membrane declaration in units.json
4. Global declaration in units.json

Both failing keys have no unit suffix and no declaration in units.json.
They are dimensionless ratios (pressure/threshold and depth/depth),
which correctly have no physical unit — but the gate has no way to
recognize dimensionless quantities yet.

### Are these real defects?

**No.** These are design limitations of the units checker, not physics
defects. Both values are pure ratios (numerator unit = denominator
unit), so assigning them any physical unit would be wrong. The fix
is to either:

1. Add `"dimensionless"` entries for these keys in units.json, OR
2. Add `_dimless` suffixes to the key names (which folding.py would
   need to recognize), OR
3. Make the units checker accept keys that are clearly ratios by
   pattern (e.g., names containing `_vs_`, `_deeper_`, `_shallower_`).

### Conclusion for Task 10b

**methodology_gate.py works correctly.** It correctly flags two
membranes whose numbers lack unit declarations. The 2 flags are
false positives (dimensionless ratios, not unit errors), and the
gate itself is functioning as designed. The score is honest: 40/42
numbers have readable units, 2 do not.
