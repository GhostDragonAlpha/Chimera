# THE GRAB — the carried load, and the absent arm

> DRAFT membrane, stated 2026-08-04. Milestone M8: "grasping of passive objects
> with real contact: pick up the stone, feel its weight_N through the body's
> own load path. That's the first moment the player touches the ledger."

---

## THE MEASURED PREMISE, BEFORE ANY THEORY

`tools/action_tests.py::a_grip` REFUSES, and its refusal is the landscape:
myobody has **no arm** — a search across every joint for
finger/thumb/wrist/hand/elbow/shoulder finds zero. The parser's GRAB is a
named Refusal ("its atoms are M8 (REACH+GRIP+BRACE)"), and the slice's E-grab
(`tools/touch_tests.py:180`) is a kinematic attach on the Walker mover: a
`carried` flag, the stone following at waist height, the HUD reporting mass.
No contact, no load path, no body.

So M8 is two membranes, not one, and the milestone's sentence splits cleanly:

- **M8a — THE CARRIED LOAD** (this doc): "feel its weight_N through the
  body's own load path." Needs no arm. The stone's mass joins the body as a
  carried load and the STANCE conservation law prices it.
- **M8b — THE ARM** (named, not stated): "grasping with real contact." Needs
  the armed body (`external/myo_sim/body/myoupperbody.xml` exists as a
  separate model). Attaching it changes the body's mass distribution, its CoM,
  its DOF count — and invalidates every frozen theta trained on the armless
  body (the stand port's 870 numbers, and M3's walk composed over them).
  M8b is milestone-scale and must come AFTER the walk closes on the armless
  body, or it takes the walk down with it.

---

## RULE 0 — M8a: THE CARRIED LOAD

**STATEMENT.** Carrying is not a flag. When a body holds a stone, the stone's
weight travels the same path every other load travels: muscles and passive
tissue to the feet, feet to the ground. `action_tests.py`'s STANCE is a
conservation law — `sum(plantar) = (1−s)·W` — and a carried stone is just W
grown by `weight_N`. A weld (MuJoCo `weld` equality, or a site-attached mass)
between stone and torso makes the load REAL: the body's own balance policy
must hold the extra mass or fall, and the feet must report it. Someone can
disagree: the weld point could be the pelvis, the chest, the hands-that-
aren't-there — the derivation takes the torso frame the stand policy already
balances about, and the choice is stated, not hidden.

**PREDICTION.** With the stone welded to the standing body (the parser's
GRAB verb driving the weld — E inside the stone's derived reach, exactly the
slice's current button), `tools/f3_stand.py`'s own harness, extended with the
plantar sum it already measures, reports:

1. **The load is felt.** `sum(plantar)` with the stone carried exceeds the
   unloaded sum by the stone's `weight_N` ± the sensors' own noise floor
   (the `plantar_pressure` port published that floor).
2. **The body still stands.** F3's stand bar with the load aboard: pelvis
   ≥ 80% of target through phase 1. If the stand needs a retrain to hold
   5–10% more mass, the retrain is the answer and is run — same precedent as
   the trunk and foot membranes, no new rule.
3. **Dropping is felt too.** Release (second E) removes exactly `weight_N`
   from the plantar sum, and the stone falls ballistically (`a_throw`'s
   gravity, already PROVEN) to rest at the feet.

**FALSIFIERS.** Named before the build:

1. The plantar sum moves by less than 90% of `weight_N` with the stone
   aboard — the weld is decorative and the load is fake. The membrane dies.
2. The body cannot stand with the load at ANY trained setting — the stand
   port's composition does not extend to carried mass, and the deficit is
   structural (published per Rule 17, not patched).
3. The released stone does not fall to rest — gravity is being cheated
   somewhere in the carry path.

---

## NEXT

1. Read `ChimeraEngine/touchables.py`'s Stone (weight_N derivation, reach)
   and the parser's GRAB Refusal registration; design the weld as a parser
   Formula so GRAB stops being a Refusal.
2. Build in a world where the stand retrain has closed (the off-sagittal
   tissue question owns the world hash until f3's verdict lands).
3. Judge through the extended f3 harness; record here.
