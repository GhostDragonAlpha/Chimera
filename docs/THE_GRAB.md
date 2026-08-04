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

---

## BUILD RECORD (2026-08-04) — and the arithmetic, corrected BEFORE the run

The stone is the slice's own: D = 0.35 m (marked THE HUMAN design dial),
quartzite 2650 kg/m³ (Schoen 2011). Measured through
`tools/grab_port.py`: **59.49 kg = 421.0 N in this world's g = 63% of the
94.5 kg body** — the prediction above said "5–10% more mass," and it was a
guess. Corrected here before any verdict; the falsifiers do not move.

Built: `tools/grab_port.py` (derive / stone_xml / spawn_stone /
grab_formula_fn — weld `stone_carry` to the `torso` body, born inactive,
relpose stated at (0.45, 0.15, −0.15) — waist, ahead-right, where the
slice's kinematic carry puts it), `tools/f6_grab.py` (three phases: load
felt / body stands / dropping felt). GRAB leaves the parser's Refusal
list as an OVERLAY formula: held + inside the derived reach (0.772 m,
ANSUR) → the weld engages. The formula owns the grab; the harness owns
the release (the parser never calls formulas for unheld verbs).

**Run 1** (harness bug, fixed): GRAB held from t=0 → the formula engaged
at the FIRST parse, snapping 421 N onto a body still settling from the
spawn. The "fall before GRAB" was the early weld. Held from T_GRAB=1.0 s
now; the pre-phase is a true baseline.

**Run 2** (the measurement): unloaded baseline plantar sum 733.7 N
(sane: 669 N static + dynamics). Weld at 1.0 s → the body is down
INSTANTLY: pelvis 4% of target, plantar sum 0.0 N through the carry. The
load is real — it destroyed the posture, which is the strongest possible
"felt"; the delta metric reads −733 N only because the feet left the
load path entirely. **This is falsifier 2's shape at the CURRENT
setting**, and the membrane's own prescription applies: the retrain is
the answer and is run. The CoM arithmetic says it is not a formality:
the stone at 0.45 m ahead puts the combined CoM ~0.23 m ahead of the
body origin — at the edge of the support zone. A carry REQUIRES a
lean-back the unloaded theta never learned. NEXT: `train_carry.py` — the
stand formula's 870 numbers re-searched with the weld ACTIVE from the
spawn (warm start from stand_theta; the loaded stand is a separate
artifact, carry_theta.npy). f6's phase 2 then judges the carry policy;
phase 1 and 3's bars do not move.
