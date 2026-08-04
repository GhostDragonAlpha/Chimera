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

**Run 6 — VERDICT: v2's falsifier 1 CONFIRMED, and the loophole is now
measured to the Newton.** Seven full-window survivors, load column
0–5% — the term did not move the strategy. Probed steady state on the
saved survivor (t=3.98 s): pelvis 0.552 (above the 0.46 fall line),
stone z = 0.175 (floor), weld constraint force |F| = 580 N, **plantar
sum 0.0 N — the feet carry NOTHING**. The body is not resting the
stone on the floor; it is HANGING from the floor-anchored stone by the
weld, feet in the air. The loophole stack is now fully mapped: run 5's
floor-rest let the floor bear the STONE; run 6's weld-hang lets the
anchored stone bear the BODY. Same root — the stone on the floor is an
anchor and the weld to it is a lifeline. And the same score-form
defect the other agent named on M3 the same day: reward×load_factor
prices the hang at ~0, and 0 beats any real-carry attempt that risks
the additive −3 fall penalty.

## AMENDMENT — v3: COMPLETE THE CONSERVATION LAW (stated before the run)

**STATEMENT.** A carry has exactly two load paths and the world has no
third: everything through the feet (v2's term), and NOTHING through
the stone-floor interface. v2 priced the first; the hang routes the
second. v3 adds the second conservation term: post-snap,
reward ×= clip(1 − F_stonefloor / W_stone, 0, 1) — the stone's weight
scale, derived, no chosen constant. With both terms, floor-rest prices
0, the weld-hang prices 0 (term 1), and ONLY a true carry — stone
floating, feet bearing body+stone — prices ≈ 1. There is no fourth
state: the world contains floor, stone, body, and nothing else.

**PREDICTION.** Survivors now show plantar ≈ body+stone AND stone-floor
contact ≈ 0 through the carry — f6's phases 1 and 3 pass, phase 2
judged on its own bar.

**FALSIFIERS.** 1. A survivor emerges with both terms priced that is
STILL not a carry — a fourth load path exists and it will be named in
this doc. 2. No survivor at all across 48×32 with the complete law —
the standing catch-and-carry of 73% of model mass on a 0.45 m lever is
beyond this body, falsifier 2 fires with full numbers, and the finding
goes to THE HUMAN's dial. 3. Survivors carry but under the 80% pelvis
bar — the posture/strength trade measured and published as-is.

**Run 7 — VERDICT: the complete law priced, and the exploits reprice to
~0 AND STILL DOMINATE. The score form is the wall.** Eight survivors,
all load 0–5% AND stone-floor 160–204% — both conservation terms zero,
reward ≈ 0, score ≈ 0 — and 0 beats every real attempt behind the
additive −3 fall penalty. Fallers' scores are IDENTICAL to run 6's
(turn 0: −3.260 both runs) because with both factors at 0 the score is
pure penalty: the search has NO gradient toward the true-carry region,
which sits behind the fall wall. But v3's falsifier 2 ("no survivor →
the body is too weak") does NOT fire, because a confound stands in
front of it, and it is measured: **the snap itself**. Every candidate,
including the proven stand theta, goes AIRBORNE at t=1.0 — the f6
trace shows a 22 kN plantar spike (52× the stone's weight) and a
pelvis arc to 1.4 m. No human lift produces 52×. That impulse is not
physics; it is MuJoCo's constraint solver correcting a 0.6 m weld
violation in a handful of timesteps — an artifact of engaging the
weld with the stone on the floor, far from its relpose. And the catch
of that artifact is not this membrane's question: M8a is THE CARRIED
LOAD (can the body hold it); the pick-up MOTION is M8b's arm. Run 5's
amendment conflated them by "matching the judge's event" — the judge's
event was the artifact.

## AMENDMENT — v4: THE SATISFIED SNAP (stated before the run)

**STATEMENT.** The pick-up event the membrane states ("the pick-up
snap is the event; the LOAD after it is the physics") is an instant
ATTACHMENT, not an instant TELEPORT-CORRECTION. A real attachment
engages where the thing is held. v4: at T_GRAB the stone's freejoint
qpos is written ONCE to the weld-satisfied pose — the pick-up, a
boundary condition at the event, the same discipline as spawn_stone at
the reset, explicitly NOT a trajectory and NOT a pose-scripted frame —
and the weld engages SATISFIED. Zero violation, zero artifact impulse;
the 421 N that arrives is the stone's weight, which is the physics
under test. TRAINER AND JUDGE MOVE TOGETHER (the run-4/5 lesson: they
must judge the same event). The bars do not move: phase 1 delta within
20% of weight_N, phase 2 pelvis ≥ 80%, phase 3 ballistic drop.

**PREDICTION.** With the artifact removed, the search's gradient
reaches the true-carry region: a survivor emerges with load ≈ 100%,
stone-floor ≈ 0, pelvis ≥ 80% — or it does not, and nothing now
stands between that result and the body.

**FALSIFIERS.** 1. No survivor across 48×32 with the satisfied snap
and the complete law — v3's falsifier 2 fires CLEAN: the standing
carry of 73% of model mass at a 0.45 m lever is beyond this body, and
the finding (the stone's D, THE HUMAN's dial) goes to the operator
with full numbers. 2. A survivor that still is not a carry — a fourth
path, named here. 3. The carry holds but under the pelvis bar —
published as the posture/strength trade, bar unmoved.

**Run 8 — VERDICT: the artifact is gone, the gradient is LIVE, and the
penalty cliff is measured ranking carriers BELOW hangers.** The
satisfied snap did exactly what it was written to do: from turn 2 on,
nearly every candidate survives the full 4.00 s — no 22 kN spike, no
airborne phase, no pelvis arc. The mean climbs monotonically −3.85 →
−3.05 across 47 turns, the first LIVE gradient since the membrane
opened. The best candidate's pelvis MIN rises 56% → 72–74% and
holding. Load readings 0–67% (typically 20–45%); stone-floor 0–200%
(typically 50–100% — the stone is still floor-supported). No true
carry yet. **But the run measured the score defect a third time, and
this time in its sharpest form:** turns 4/5 produced candidates
carrying 65–67% of the stone's weight that fell at 3.7–3.8 s and
scored −3.11 — ranked BELOW zero-load survivors at 0.000. The search
was shown the real thing and was built to prefer nothing. Same wall
as run 7, named on the walk by Claude's score-form ablation
(subtractive picks standers at 4% speed, multiplicative picks
travelers at 62%), and the fix is the same shape with no constants to
choose.

## AMENDMENT — v5: THE MULTIPLICATIVE SCORE (stated before the run)

**STATEMENT.** The additive penalty structure is the third appearance
of the same defect: `mean_r − 3·fell − 2·(1−frac)` mixes a reward
whose whole range is ~0.5 with penalties of 3 and 2, so the fall
cliff dominates absolutely and a 0-by-loophole outranks every real
attempt. If the score is `mean_r × frac` — both factors dimensionless
in [0,1], multiplied, the same form `stand_reward` already uses —
there is no scale to get wrong, no constant chosen, and a fall prices
itself through the fraction it survived. Precedent: the walk's
multiplicative ablation made travelers outrank standers; here it must
make carriers outrank hangers.

**PREDICTION.** A 65%-load candidate that falls at 3.7 s (mean_r > 0,
frac ≈ 0.9) now scores above any zero-load survivor (mean_r = 0 →
score 0), so the gradient points INTO the load-bearing region for the
first time: load readings climb past 80% with stone-floor under 20%
in the survivors.

**FALSIFIERS.** 1. The ranking does not invert — hangers still beat
carriers — and the score's form was not the wall; named here. 2. No
survivor at all across 48×32 with the multiplicative score — v3's
falsifier 2 finally fires CLEAN: the standing carry of 73% of model
mass at a 0.45 m lever is beyond this body, and the finding (the
stone's D = 0.35 m, THE HUMAN's dial) goes to the operator with full
numbers. 3. A carry that holds under the pelvis bar — the
posture/strength trade, published as-is, bar unmoved.

**Run 8 — PICTURE ADDENDUM (the same day, before run 9 overwrote the
turns).** The log-based verdict above overstated one line, and the
pictures correct it. "Pelvis MIN of best rising 56% → 72–74% and
holding" read as a deepening crouch. The turn-41 and turn-47 PNGs say
otherwise: the final bests are **launch-and-crash arcs** — the pelvis
leaves 0.92 m at the snap, peaks near **3.0–3.1 m** (absurd for a
standing lift; at g = 7.08 m/s² an Earth-sized muscle set can throw
body + stone airborne), then crashes, and the quoted MIN is the
*crash bottom* (0.684 m at turn 41, 0.550 m at turn 47), not a held
posture. The best-score panel oscillates 0 ↔ −3.2 turn by turn:
hangers and launchers tie at ≈ 0 under the additive score, and the
search bounced between them. The "live gradient" was the mix
shifting, not a carry forming. The instrument lesson is the one this
project keeps paying for: **a scalar MIN over a whole rollout cannot
distinguish a crouch from a crash** — one quantity, one landmark. v5's
multiplicative form prices these correctly without a new constant:
launchers sit far from the pelvis target most of the rollout, so
mean_r ≈ 0 and they join the hangers at the bottom of the ranking,
below any candidate whose plantar path actually carries the stone.

**Run 9 — VERDICT: the ranking inverted, the search found the real
thing once, and NOBODY survives the window. Falsifier 2 FIRES
CLEAN.** The multiplicative score did what it was written to do:
hangers and launchers both price to exactly 0.000, and the single
turn whose candidate put the load path through its feet — turn 20,
plantar spikes to ~1200 N post-snap, load 32%, stone-floor 28%, held
3.02 s — took the session's best at 0.001 and was saved. The form is
honest now; a candidate can only score by actually carrying. And
across all 48×32 candidates, warm-started from run 8's best, **not
one survives the 4.00 s window**: held-times cluster 2.0–2.9 s, which
is 1.0–1.9 s after the 421 N arrives. jmax sits 3.2–4.2 throughout —
the collapse is through the joints' stops. f6 against the saved best:
plantar 619.8 → 0.0 N at the weld (the body is on the ground, not
filtering the load), pelvis MIN 21% — FAIL on all three phases, bars
unmoved. **Cleanliness of the falsifier:** the one standing confound
is the unloaded stand's 7.0 s ceiling (the foot-ligament regression,
Claude's rung 9 in flight). It does not reach: the carry horizon is
4.0 s, the unloaded body is solid through it (~100% pelvis to 5 s),
and every fall lands 1.0–1.9 s after the snap — the load is the
killer, attributable, no proxy in the way. **The finding, for THE
HUMAN's dial:** the stone is D = 0.35 m quartzite, 59.49 kg = 421 N
at g 7.08 — **63% of the 94.5 kg theHuman publishes, 73% of the 82.0
kg the model masses** (the mass discrepancy stays on record,
unreconciled). The catch pose puts it on a 0.45 m lever → ~206 N·m
at the hip, the edge of published human maximal voluntary hip
extension, asked of a body whose postural policy was never trained
for it. The dial, all three settings legal: **(a)** shrink the stone
— D ≈ 0.25 m is ~21.6 kg, 23–26% of body mass, a load a trained
stand can plausibly hold; **(b)** keep the stone and let M8b's arm be
the story of a lift that fails — the body straining and going down is
a true read of the ledger; **(c)** leave the stone and revisit after
the stand ceiling rises (rung 9's frontal retrain). The choice is
taste about what the world should ask of the body — THE HUMAN's
terminal, named as such. M8a's instrument half is complete either
way: five exploit classes (born-carry, crouch, floor-rest, weld-hang,
launch-and-crash) each found, priced, and closed; the load path, the
stone-floor interface, the snap, and the score form all honest. What
remains open on the rung is M8b — the pick-up MOTION, the arm — and
it starts from whatever the dial says.

## AMENDMENT — v6: PRICE THE DIAL (stated before the runs)

**First, a correction this amendment pays for.** Every load fraction
this membrane has published was priced against theHuman's SUITED
94.504 kg — the same two-landmarks defect stand_port already fixed
once (rule 19). The lifting body is myobody.xml's 82.041 kg; the suit
and consumables lift nothing. grab_port now prices against the
simulated mass (ledger mass kept as CHK), and the record corrects:
the D = 0.35 m stone is **72.5% of the body that lifts**, not 63%.
f6's header prints the corrected basis from here.

**STATEMENT.** THE HUMAN's dial is priced by measurement, not chosen
blind. The run-9 falsifier fixed one point on the dial's curve: 72.5%
of body mass at a 0.45 m lever is beyond this body. Two more points
bound the feasible band: D = 0.25 m (21.68 kg = 153.4 N = **26.4%**
of the lifting body — a load a trained stand can plausibly hold) and
D = 0.30 m (37.46 kg = 265.0 N = **45.7%** — the boundary region).
The measurements run in parallel against train_carry's own machinery,
outputs isolated, the dial's home (touchables.py) untouched: the runs
price the settings; they do not choose one.

**PREDICTION.** D = 0.25 produces a survivor with load ≥ 80%,
stone-floor ≤ 20%, pelvis ≥ 80% inside 48×32 warm from the run-9
best — the body's true-carry region opens at 26%. D = 0.30 produces
real load with survivors under the pelvis bar, or no survivor — the
limit sits between 46% and 72%.

**FALSIFIERS.** 1. D = 0.25 also yields no survivor — the limit is
below 26%, and either the dial's (a) setting shrinks further or the
stand ceiling itself is the wall (rung 9's question, named with
numbers). 2. D = 0.30 yields a full true carry — the limit is above
46%, closer to the run-9 point than this prediction says; the band
narrows to 46–72%. 3. BOTH carry — then run 9's verdict was about
the search at 72.5%, not the body, and the correction is published.
