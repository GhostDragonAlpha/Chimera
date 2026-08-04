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

**Run 3 — `train_carry.py` run 1 (24×32, warm from the retrained stand
theta, weld ON from the spawn, horizon 3.0 s = f6's window): NO CARRY
FOUND, and the instrument question answered by probe BEFORE any theory
moved.** Every turn fell at 1.1–1.9 s, pelvis MIN 46–50%, best score
−3.737 (turn 16). Flat to the eye — but not dead: the mean climbed
−4.554 → −4.253 and the best held-time crept 1.82 → 1.92 s. A live,
weak gradient. Two measurements taken before reading anything into it:

- **The landmark was already right.** Suspicion: the reward grades
  `subtree_com[0]`, which might exclude the welded stone (separate
  freejoint tree) — the same wrong-landmark species the other agent
  caught in f3 the same week. PROBED, not theorised: `subtree_com[0]`
  equals the hand-computed body+stone CoM to the fourth decimal
  ((−0.0313, 0.1776) both ways). The compass was correct all along.
  Also surfaced: the model's bodies sum to 82.0 kg, not theHuman's
  94.5 — the load fraction against the MODEL's mass is 59.49/82.0 =
  73%, heavier than the doc's headline. Recorded, not reconciled.
- **Born outside the polygon.** At the seated spawn with the weld on,
  the combined CoM sits 0.178 m ahead in y against a fore box half of
  0.1355 — 4.2 cm OUTSIDE the base of support at t=0. Statics: the
  hold needs the body's own CoM ~10.5 cm BEHIND the foot centre, and
  the hip-extensor moment is ~206 N·m (stone 189 + torso ~17) — at the
  edge of the published human maximum (strongman-class, not
  impossible). f6 with carry_theta confirmed all three phases red —
  the body is down before the weld even engages.

Falsifier 2 (cannot stand with the load at ANY trained setting) is NOT
fired: 24 narrow warm-start turns with a weak but live gradient is not
"any trained setting" — the same discipline the walk got (v2 run 1
climbing → continuation granted). Backed up to
`carry_theta.run1.bak.npy`; a 48-turn continuation from the session
best runs now. If the continuation plateaus with no candidate holding
3.0 s, falsifier 2 fires with its numbers and the finding to publish
is the stone itself: 73% of model mass at a 0.45 m lever is a dial
(THE HUMAN's D = 0.35 m) sitting past the edge of the published human
hip moment — and only THE HUMAN moves that dial.

**Run 4 — the 48-turn continuation VERDICT: the search found the CROUCH,
and the crouch exposed the trainer's own mismatch.** Steady climb all
48 turns (best −3.737 → −3.06 band, mean −4.56 → −3.66, held 1.92 →
2.94 s), and six turns (23/24/32/40/43/47) produced FULL-WINDOW
survivors (score ≈ −0.004, held 3.00 s) — at 50–57% pelvis. The
pictures show the atlas-stone strategy: drop, stabilize the combined
CoM inside the polygon in a deep crouch, hold. The mean was STILL
CLIMBING at turn 47. But f6 knocked the crouch theta flat in ONE FRAME
(pelvis 16%, plantar sum 0 from the weld): the trainer welded from the
spawn with the stone born AT the carry pose, while f6's stone starts
on the FLOOR and the weld engages at t=1.0. The snap's impulse is the
membrane's own stated event ("the pick-up snap is the event; the LOAD
after it is the physics"), and the born-carry policy never felt it.
**The trainer was training a different event than the judge judges —
the same proxy-for-target species train_stand's docstring records.**

**Run 5 — trainer amended to match the judged event EXACTLY** (stated
before the run): stone spawned on the floor, weld INACTIVE, snap at
t=1.0 s, horizon 4.0 s (1.0 pre + f6's 3.0 window). Nothing else moved
— same 870 numbers, same reward, same bar. Warm start from the crouch
theta (backed up to `carry_theta.crouch.bak.npy`): it knows the hold;
the catch is the new lesson. Smoke test: the crouch theta survives the
snap + 0.5 s at 80% pelvis MIN — the catch is not instantly fatal,
which means the gradient into it exists. 48×32 running.

**Run 5 — VERDICT: the search found the LOOPHOLE, not the carry. The
crouch-hold is a floor-rest, measured by f6's own phase 1.** Nine
full-window survivors (score ≈ −0.003, pelvis 51–59%), and f6 on the
saved one reads: plantar sum BELOW baseline through the carry, stone z
= 0.175 m (its radius) from t≈2.3 s on. **The "carried" stone is
sitting on the floor.** The weld is active and the constraint force is
~0: crouch deep enough and the carry pose IS the floor, the floor bears
the 421 N, and the hold is free. Falsifier 1's exact shape — "the weld
is decorative and the load is fake" — produced by the optimizer, not by
a broken weld. Nothing in `stand_reward` prices the load path, so the
search routed around the load: the exploit is the product, again. (Also
measured, same f6: a 22 kN snap spike and an airborne arc — the snap
impulse is priced nowhere either. And a launch mistake, published per
rule 17: run 5 warm-started from STAND theta, not the crouch — a
missing `--init` — which cost nothing, the crouch was a dead end, but
the record says what ran.)

## AMENDMENT — v2: PRICE THE LOAD PATH (stated before the run)

**STATEMENT.** A carry is a conservation law, not a pose: welded or
not, body + stone are borne by the feet, and the plantar sum is the
ledger that cannot be faked — the stone resting on the floor shows up
there instantly. Training without that term grades the pose and invites
the floor-rest. The fix is to price falsifier 1's OWN quantity in the
search: post-snap, reward ×= clip(plantar_sum / (W_body + W), 0, 1),
W_body = (total model mass − stone) × g — derived from the model, no
chosen constant, the multiplicative form `stand_reward` already uses
(and the form the other agent's M3 score work just vindicated). Going
airborne prices as zero (sum = 0 in flight); floor-resting prices as
~0.3–0.7; only a true carry prices ≈ 1.

**PREDICTION.** With the load path priced, survivors stop floor-resting:
the plantar sum through the carry reads ≈ baseline + 421 N, and f6's
phase 1 passes (delta within 20% of weight_N) — phases 2 and 3's bars
unmoved.

**FALSIFIERS.** 1. Survivors still floor-rest — the loophole is
elsewhere, published. 2. NO survivor emerges at all with the term
priced — the standing catch-and-carry is beyond this body's strength at
any of 48×32 settings, falsifier 2's numbers arrive, and the finding
becomes the stone (73% of model mass, THE HUMAN's dial). 3. The sum
rises but phases 2/3 collapse — the posture and the load trade against
each other, published as the measurement.
