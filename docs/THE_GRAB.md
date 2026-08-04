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

**Dial runs D=0.25 / D=0.30 — VERDICTS: prediction failed at BOTH
points; falsifier 1 fires; and the flatness of the curve names the
real wall.** The patch reached the physics (headers: 21.68 kg /
153 N, 37.46 kg / 265 N; the turn-title's hardcoded 59.49 kg is
cosmetic, train_carry.py:193, noted for the record). Neither run
produced a survivor: D=0.25 best held 3.04 s with a 79%-load
candidate falling at 1.94 s (jmax 1.85, the honest attempt); D=0.30
best held 3.60 s with 78%-load at 2.08 s. v6's prediction is dead at
both points, falsifier 1 fires, and the three-point curve says WHERE
it points:

| dial D | mass | % of lifting body | best held | best load | survivors |
|---|---|---|---|---|---|
| 0.25 m | 21.68 kg | 26.4% | 3.04 s | 79% (fell 1.94 s) | 0 / 48×32 |
| 0.30 m | 37.46 kg | 45.7% | 3.60 s | 78% (fell 2.08 s) | 0 / 48×32 |
| 0.35 m | 59.49 kg | 72.5% | 3.02 s | 32% (fell 3.02 s) | 0 / 48×32 |

**Survival is FLAT across a 2.7× mass range** (3.04 / 3.60 / 3.02 s),
and load-routing does not track mass either (79% at 26%, 78% at 46%,
32% at 72%). If strength were binding, 26% would survive dramatically
longer than 72%. It does not. The d=0.25 pictures show the body
routing the FULL 733 N (body + stone) through its feet for ~0.9 s
and then losing the rebalanced posture — the binding constraint is
not the stone's weight but the body's response to ANY sustained
off-axis torso load arriving at t=1.0. Falsifier 1's second clause,
not its first: the wall is the catch, not the mass.

## AMENDMENT — v7: THE DECISIVE POINT (stated before the run)

**STATEMENT.** A flat survival curve over 26–72% of body mass cannot
be a strength curve. Two candidates remain for the wall: (i) the snap
EVENT — the weld's engagement itself, or the policy's complete lack
of training for any sudden CoM shift, regardless of magnitude; (ii)
the carry foundation — the 870-dim sagittal theta every run here
warm-started from, tuned in the 72.5% world. One more dial point
separates "small load still kills" from "the event kills": D = 0.15 m
is 4.68 kg = 33.1 N = **5.7%** of the lifting body — a load the
trained stand should shrug off if load is the question at all.

**PREDICTION.** At 5.7%, survivors appear with load ≥ 80% and
stone-floor ≤ 20% inside 48×32 — the flat curve bends at the low
end, the wall is load after all, and the dial's feasible band opens
below ~10%.

**FALSIFIERS.** 1. No survivor at 5.7% either — the curve is flat to
the floor, load is exonerated across 5.7–72.5%, and the wall is the
SNAP EVENT or the FOUNDATION, named with numbers. The dial question is
then REPLACED: no stone size saves the carry; the catch must be
trained against the frontal stand (rung 9's 9.08 s foundation), and
M8a's finding to THE HUMAN changes from "how big a stone" to "the
body must learn to catch before the dial matters". 2. Survivors
appear but the load path is fake (weld-hang reprised at small mass) —
the exploit audit reopens at this mass, named here.

**D=0.15 run — VERDICT: falsifier 1 FIRES. The curve is flat to the
floor; load is exonerated.** At 5.7% of the lifting body (4.68 kg,
33 N): zero survivors across 48×32, best held 2.68 s — SHORTER than
at 72.5%, the direction the warm-start incumbent (tuned in the heavy
world) predicts and the opposite of what a strength limit predicts.
The full four-point curve:

| dial D | mass | % of lifting body | best held | survivors |
|---|---|---|---|---|
| 0.15 m | 4.68 kg | 5.7% | 2.68 s | 0 / 48×32 |
| 0.25 m | 21.68 kg | 26.4% | 3.04 s | 0 / 48×32 |
| 0.30 m | 37.46 kg | 45.7% | 3.60 s | 0 / 48×32 |
| 0.35 m | 59.49 kg | 72.5% | 3.02 s | 0 / 48×32 |

Plus one new exploit signature at small mass: stone-floor contact
forces to **1682%** of the stone's weight — the weld dragging the
light stone across the floor (the grind, exploit class six, priced by
the same v3 term). **The M8 finding to THE HUMAN is REPLACED.** The
question is not how big a stone the body can hold; no stone size gets
held. The question is why a body that stands 9.08 s cannot absorb ANY
sudden off-axis torso load — and that is physics, not a dial: the
catch is a skill the policy was never trained with, and every run so
far searched a sagittal-only policy class (870 numbers, no roll
channel) inherited from before rung 9.

## AMENDMENT — v8: THE FRONTAL CATCH (stated before the run)

**STATEMENT.** Rung 9 proved the roll channel is trainable only when
the search shapes the policy around it (warm 9.08 s, cold pending).
The carry has been failing on exactly that missing channel: every
collapse — at every mass — is the body losing the rebalanced posture
~1–2 s after the snap, and the rebalanced posture is a frontal-plane
problem (the weld sits at (0.45, 0.15, −0.15) in the torso frame —
0.15 m off the sagittal midline). A carry search in the 4-block
policy class (a0/kh/kp/kr, 1160 numbers, warm from the frontal stand
itself) will find catches the 870-class search provably cannot
contain.

**PREDICTION.** Against the slice's own stone (59.49 kg, the dial
unmoved — the mass is exonerated, so the test runs on the real
target): a survivor emerges inside 48×32 with load ≥ 80%,
stone-floor ≤ 20%, pelvis ≥ 80% through f6's window — the first true
carry.

**FALSIFIERS.** 1. No survivor in the 4-block class either — the
frontal channel was not the carry's wall; the remaining candidate is
the snap EVENT as a policy-shock no feedforward formula absorbs
(named with numbers, and the membrane turns to training the catch as
its own port, the way standing got its own). 2. A survivor with a
fake load path (grind/hang reprised) — the exploit audit reopens.
3. The carry holds but under the pelvis bar — the posture trade,
published as-is, bar unmoved. TRAINER AND JUDGE CHANGE TOGETHER (the
run-4/5 lesson): train_carry searches 4*nu with roll feedback in the
law; f6's obs gains roll; the parser already prices a 4-block theta
transparently (1f24f74). A 3-block checkpoint still runs unchanged
(kr = 0) — but v8 REFUSES an 870 init: mixing foundations is the
theta-pair lesson, and the warm start is the frontal stand alone.

**Run 10 — VERDICT: falsifier 1 fires, and the mechanism is measured
to the millisecond.** No survivor in the 4-block class either — best
held 2.64 s, nobody past the window. But the frontal channel was not
nothing: the UNTUNED frontal stand routes **107%** of body+stone
through its feet at turn 0 (the sagittal class never showed a full
load path untrained), the launch arcs are gone from every picture,
and the pelvis holds its 0.85–1.0 m band calmly for ~2 s before a
slow buckle (jmax ~2.0, vs the sagittal 3.2–4.2). The collapse is
not a topple and not a balance loss. The saturation probe (.tmp,
one rollout of the saved best) names the killer:

| t | pelvis | saturated (u ≥ 1.0) |
|---|---|---|
| 1.00 (the snap) | 0.889 m | 0.0% |
| **1.02 (first control step after)** | **0.752 m** | **35.9%** |
| 1.10–1.70 | 0.67–0.85 m, wobbling | 31–36% sustained |
| 1.80 | 0.733 m, buckling | 47.9% |

**14 cm in one 20 ms control interval.** The 421 N arrives
instantaneously; muscle activation dynamics cannot answer inside one
interval; the reactive law (no anticipation, demand 0.225 at the
event, no ramp) begins its catch from a crouch it never chose, and
from there a third of the muscle set sits at its ceiling until the
buckle. The catch does not fail in the HOLD — it fails in the
event's first 20 ms. And that implicates the snap itself: no human
experiences an instantaneous load. A real pick-up ramps weight onto
the body over ~0.5–1.0 s as the lift progresses — M8b's territory.
The satisfied snap removed the solver artifact but kept an
idealization: weight arrival in zero time.

## AMENDMENT — v9: THE RAMPED ARRIVAL (stated before the run)

**STATEMENT.** The snap is the membrane's idealization of the
pick-up, and v8's measurement shows the idealization, not the load,
is what kills: the event must model weight ARRIVAL, not weight
TELEPORTATION. v9: at T_SNAP the weld engages satisfied exactly as
v4 wrote it, and the stone's mass then arrives linearly over 0.5 s
(25 control intervals) — a boundary-condition refinement at the
event, the same discipline as the snap, explicitly not a trajectory
and not a scripted pose. The reactive law can track a 2.38
kg-per-control-interval arrival; it provably cannot track 59.49 kg
in one. (The interval share was first written 0.84 kg — an
arithmetic slip, corrected here BEFORE the run: 59.49 kg / 25
intervals = 2.38 kg.)

**PREDICTION.** With the ramped arrival, the 4-block search produces
a survivor inside 48×32 with load ≥ 80%, stone-floor ≤ 20%, pelvis
≥ 80% — the sustained 72.5% hold that v8's calm 2 s already suggests
is in the body.

**FALSIFIERS.** 1. No survivor with the ramp either — then the
buckle is sustained strength at 72.5% after all, the saturation
sustained at ~31% is the honest measure of a body at its limit, and
THE HUMAN's dial returns with full numbers (the catch skill being
trainable no longer helps: the HOLD is what fails). 2. Survivors
only appear if the ramp exceeds 1.0 s — the event model is doing
the lifting, not the body; the idealization boundary is named here.
3. A survivor with a fake load path — the exploit audit reopens.
Trainer and judge change together; the probe re-runs against the
saved best to report the arrival's first-interval sink.

**Stone landmark audit (same day, between runs).** THE_RECORDED_SESSION_2.md
quotes the slice saying *"65.1 kg of basalt (Quaglio 2020)"* — a different
mass AND a different rock than this membrane's 59.49 kg quartzite. Traced:
`5f31629` (16:45, rung 4) unified the stone to quartzite end-to-end
(_RHO_BASALT 2900 → _RHO_QUARTZITE 2650, same `_STONE_D`, one home in
touchables.py); the recorded session's log carries the PRE-unification
text, i.e. the session ran against a stale working tree — the same
evidence-vs-code drift that session's recorder fix addresses, one level
up. Verified live: `touchables` and `grab_port.derive_grab_port()` now
derive 59.49 kg from the same two constants and MATCH to 1e-9. One
landmark, current. No action owed; recorded so the session doc's stone
lines are read as stale-state artifacts, not as a second stone.

**v9 addendum — the instrument's sign inversion (caught mid-run 11, fixed
before the run was believed).** Run 11's first launch was killed at turn
~8: turn 7's PNG showed the best carry behavior this membrane has produced
(pelvis MIN 87%, full 4.0 s survival, calm) while the score column read
NEGATIVE and climbing (−0.00040 → −0.00026). Measured cause: the trainer
priced each step with `stand_reward`'s scalar, which is
`r_h·r_s·r_j − 3.0·fell − 0.01·effort`. Under load the signed effort term
makes every survivor's mean reward slightly negative, and v5's
multiplicative score `(tot/n)·((k+1)/steps)` then ranks instant death
(score ≈ 0) ABOVE any survivor — the same exploit family as run 5's
born-carry, this time authored by the instrument itself. It had not bitten
yet (no instant-death candidates in the pool; the search was still
improving), but an instrument whose ordering inverts under load is not an
instrument. Fix, before relaunch: the trainer prices ONLY the three
gaussians (each in [0,1]); the effort coefficient is a chosen constant
(out by v5's own rule) and the fell term is already priced by the
survival fraction. Smoke (1×4, warm from the frontal stand): score ≥ 0,
full-window hold at 101%. Run 11 relaunched on the fixed score; all turn
numbers from the killed launch are discarded, none cited as evidence.

**RUN 11 VERDICT (v9, THE RAMPED ARRIVAL, 48×32 warm from the frontal
stand): F6 FAIL — falsifier 3 fired (gravity is cheated in the carry
path), and the ramp itself is the hole.** The membrane asked whether the
body could catch a weight that ARRIVES over 0.5 s instead of teleporting
in 20 ms. The measured answer: the arrival as implemented never reaches
the body at all.

Measured, in order:

- **f6 on the saved best: plantar 679.2 → 0.0 N at the weld** (delta
  −679 N against the +421 N bar). QACC instability at t = 1.307, the
  pelvis trace spikes through the floor (visible in f6's own plot), and
  by the phase-2 window (t ≥ 1.6) the solver has settled into a
  non-physical SUSPENSION: pelvis ~0.99 m, plantar 0, stone-floor 0 —
  nothing touches the ground, and nothing falls. Phase 3 fails the same
  way (0.0 → 0.0 N on release).
- **The trainer's own evaluate on the same theta** (`.tmp/run11_probe.py`):
  no explosion — but the same suspension: plantar 0.0 N AND stone-floor
  0.0 N for the entire 3.0 s post-snap, pelvis floating at 0.93–1.00 m.
  A static body with zero contact force anywhere is not a carry; it is
  the solver holding a degenerate constraint. The trainer/judge
  divergence (dip-and-suspend in evaluate, spike-through-floor in f6)
  is a matter of degree inside the same degenerate regime.
- **The mechanism, stated as the measured shape it is:** the ramp scales
  the stone's mass AND INERTIA from ~0.12 kg while the weld is already
  engaged. A near-massless body welded to an 82 kg torso is a
  numerically degenerate constraint; the solver can hold the welded
  system suspended (or blow it up) instead of transmitting weight. The
  weight-arrival idea was aimed at the 20 ms killer; it routed the
  arrival through ~0 inertia and found the solver's hole instead.
- **The exploit instruments worked; the search did not.** The trainer's
  load column read 0% for all 48 turns — every candidate priced ~0
  (saved best: 0.000712), the weld-hang correctly priced at nothing. But
  with the joints gaussian crushing every candidate's r to ~1e-4 under
  load, the score had no gradient and CEM's elites were noise. The dark
  reward, third appearance (Claude's stand-reward, the walk's, now the
  carry's).
- **Instrument repairs landed with this verdict:** f6's phase-2 window
  now refuses a non-finite or non-positive carry trace (the old `min()`
  skipped NaN silently — it printed 0.9915 m while its own plot showed
  the body at −10 m); the trainer's evaluate treats a non-finite pelvis
  as a fall and breaks before the NaN can poison the score.

The v9 falsifiers read: (3) fired — the fake load path survivor exists
and is the run's saved best. (1) fires in form but not in meaning: there
was no survivor with the ramp, but what failed is the EVENT MODEL, not
the body's sustained strength — the dial question does not return to THE
HUMAN on this evidence.

**v10 — THE HANDOFF (stated 2026-08-04, before the build).**

**STATEMENT.** v9's prediction was right and its mechanism was wrong. The
arrival must be spread over ~0.5 s (v8 measured the 20 ms killer), but
spreading it through mass+inertia routes through ~0 inertia and lands in
the solver's degenerate constraint (run 11: the suspension, plantar 0/0,
nothing falling). The event the membrane always meant is a HANDOFF: the
stone at FULL mass and FULL inertia at every instant, with the giver's
hands supporting (1 − frac)·W of its weight, tapered to zero over the
arrival window. The body feels frac·W growing at 2.38 kg per control
interval — v9's number, kept — and the solver never sees a degenerate
body. The support is a boundary force at the event (`xfrc_applied`), the
same discipline as the snap's one write; no trajectory, no pose script,
and no chosen constants beyond the membrane's already-stated 0.5 s.

**PREDICTION (not yet measured).** The frontal STAND policy — NO retrain
— catches and holds the tapered stone: f6 phase 1, the plantar delta
lands within 20% of 421 N measured after arrival completes; phase 2,
pelvis ≥ 80% of target through the carry window (under the repaired
clean-window guard); phase 3, the drop returns to the unloaded band and
the stone rests at its radius.

**FALSIFIERS (named before the run).**

1. **The suspension or the explosion reappears at full inertia** —
   plantar 0 with the pelvis up, or QACC instability — the degeneracy
   was never the inertia; the weld event itself is broken and the next
   membrane goes after the weld.
2. **The load path is real and the body still buckles** (the delta
   lands, then the sink and the buckle, as v8) — the catch genuinely
   exceeds the reactive law at 72.5% of body weight, and the pick-up
   becomes M8b's motion to build, with these numbers as its brief.
3. **A pass with a fake load path** (delta right but stone-floor
   nonzero, or any suspension) — the exploit audit reopens.

**v10's question, named before anything is built:** the arrival must not
pass through ~0 inertia. The physical event is a load TRANSFER: the
stone at full mass, gripped while it rests on the floor, the floor
contact sharing the load and unloading as the body rises — the contact
mediates the arrival, nothing teleports, nothing goes massless. That is
v8's event, and its killer was the first control interval, which is a
POLICY problem (no anticipation of a load the body can feel building
through its own hands), not an event problem. Whether the answer is a
braced-anticipation phase in the formula (the body pre-tensions before
the weld, the way a person does) or a soft-constraint engagement is a
derivation, not a pick. And the dark score needs its own membrane: under
load the joints gaussian zeroes the signal for every candidate, so the
search cannot rank a true carry against a suspension even though the
load factor prices them correctly — the reward's form, third time, is
the wall.

---

**RUN 12 — v10 VERDICT (2026-08-04): F6 FAIL, falsifier 2 fires. The weld
event was broken twice underneath every prior run; fixing it is this run's
payload. The no-retrain prediction is refuted — the catch becomes M8b's
brief, with numbers.**

The v10 build (support taper, full inertia) was tested as stated: the
frontal stand policy, no retrain, against f6. Falsifier 1 fired on the
first run — and the post-mortem found the weld event broken in **two
independent ways that had been there since v4**, invisible at ~0 inertia:

1. **The carry pose was written in the wrong frame.** `CARRY_RELPOS`
   (0.45, 0.15, −0.15) read the torso frame as X-forward. Measured with
   the body standing (pelvis 0.951): torso local X points DOWN
   ([−0.26, −0.11, −0.96]), Y points LEFT, Z points FORWARD. The stated
   pose materialized the 59.49 kg stone **0.115 m inside femur_l**
   (solver's own contact pass). The expulsion was the f6 launch: pelvis
   0.95 → 1.55 m, stone z to 1.75, two 4 kN plantar spikes. A real-contact
   clearance sweep over the 1.0–2.0 s sway envelope found
   **(0.10, 0.00, 0.40)** — 0.10 m down, centred, 0.40 m forward — never
   touches any body geom. That is the carry pose now, same intent, the
   frame the torso actually has.
2. **The weld's relpose was INVERTED, and had never once been satisfied.**
   MuJoCo's weld relpose is the pose of body2 in body1's frame; the XML
   had `body1=stone body2=torso relpose=CARRY_RELPOS` — stone-in-torso
   where torso-in-stone was required. Measured after the snap:
   torso-in-stone = (−0.0997, 0.0009, −0.4002) against a stored target of
   (+0.1, 0, +0.4) — a **0.82 m constant violation**, twice the carry
   offset, at every carry in every run since v4. The snap's docstring
   claimed the weld "engages SATISFIED"; it never did. With v9's ~0-mass
   stone the phantom yank had nothing to move; at full inertia it threw
   the system. Fixed by swapping to `body1=torso body2=stone`, which makes
   the constraint read exactly what the snap writes.

With both repaired, the event probe is clean: no launch, pelvis 0.951 →
0.966 m through the whole 0.5 s taper, the load arriving at 2.38 kg per
control interval as stated. (One grazing stone/femur_r contact, −2 mm,
appears only under full load — the stone resting against the thigh, which
is how a person carries a heavy rock. Physical, kept.)

Then the stated test ran: stand_theta, no retrain, f6. **FAIL — and the
failure is physics, not artifact.** The plantar delta lands: 642.7 → 1100 N
peak (+457 N ≈ the stone's 421 N weight). The body **catches** the load and
holds it for ~1.0 s (pelvis 0.99 m to t≈2.0), then pitches slowly forward
and buckles by t≈2.8. Phase bars read: (1) +181 N in the window vs +421 N
required — FAIL; (2) pelvis MIN 0.186 m — FAIL; (3) drop FAIL with the
body already down. **Falsifier 2 fires, cleanly, as written:** the load
path is real and the body buckles — the catch exceeds the reactive law at
73% of body weight held 0.40 m in front. The no-retrain prediction is
refuted.

**What run 12 settles.** (a) The weld event is now physically true for the
first time — every carry number before this run was measured against a
0.82 m phantom, which reframes but does not invalidate the exploit classes
runs 1–10 priced (they priced trainer/judge asymmetries, not the weld).
(b) F3's unloaded stand is untouched — no ligament, no policy, no landmark
moved; only the stone's event changed. (c) The catch is now a TRAINING
problem exactly as the membrane routed: a 421 N load at a 0.40 m lever
(~170 N·m pitch moment at the torso) must be met by a policy that can
anticipate it. The frozen frontal stand holds it one second and falls —
that number is M8b's brief. (d) The dark score is now the binding
instrument debt: the retrain cannot rank candidates until the joints
gaussian stops zeroing the reward under load (run 11, third appearance).
The dark-score membrane is stated next, before any retrain runs.

---

**v11 — THE DARK SCORE (stated 2026-08-04, before the reprice; the third
appearance of the pattern, and the first time it is measured to the joint).**

**STATEMENT.** The carry score is dark in the FIXED world — measured: 100%
of the incumbent's post-arrival samples score r < 1e-3, incumbent total
0.0008 — and the mechanism is not the weld (run 11's guess, now dead) and
not a model-range artifact (Claude's mtp, which tallies only 3 of 30
samples). It is the **joints gaussian's center**. The term
`exp(-((jf - 0.8) / 0.1)^2)` was derived for the UNLOADED stand, when the
stops had no tissue: "keep 20% off the stop" was the only protection the
body had. The stops are now ligament-engagement edges (the trunk/foot/hip
membranes), and the body under a 421 N carry load does what a loaded body
does — it settles ONTO the tissue: `knee_angle_l` sits at jf 1.014–1.028,
sustained, for the whole carry (measured, worst-joint tally 21/30 samples).
At that point on the gaussian's tail, a 1.3% difference in where the loaded
knee settles against its ligament — variation the policy does not control —
swings the multiplied reward 3x, while the excursion the term exists to
punish (a fling to jf 1.3+) prices ~0 identically for every candidate.
Signal-to-noise is inverted: the term prices uncontrollable variation
loudly and its own purpose silently. **The fix moves the center to the
stop itself — one-sided: 1.0 for jf <= 1.0, then the same 0.1 width
beyond.** 1.0 is not a chosen number; it is the physical landmark the
ligaments were derived from. 0.8 was the chosen one, and its reason
(no tissue) no longer exists. At-the-stop is now the tissue's job, and
the tissue prices it physically; the reward must price only what the
tissue cannot — excursions PAST the stop.

**PREDICTION.** With the one-sided term, the incumbent's fixed-world trace
scores at least two orders of magnitude above its current 0.0008 (the
height/support/load factors carry real signal — measured span 1e-18 to
1e-3 in the SAME trace — and the joints factor stops multiplying it by
noise), and a candidate that collapses at the snap scores strictly below
one that catches and holds, by a margin CEM can rank (not tail noise).

**FALSIFIERS (named before the build).**

1. **The reprice does not restore ranking** — the incumbent's score stays
   ~1e-3 or the collapse candidate ranks at/above the holder — the
   darkness was not the center, and the term's whole form is re-derived
   (per-joint ligament torque as the price), not patched again.
2. **The fling exploit reopens** — any elite in the retrain holds a joint
   past jf 1.2 on a tissue-less stop at no visible score cost — the
   one-sided form is wrong and the two-sided gaussian returns, centered
   at the stop.

**v11 VERDICT (interim, 2026-08-04 — the reprice, measured before the retrain).**

The prediction holds in its ranking clause and is refuted in its magnitude
clause — recorded as written:

- **Ranking: RESTORED.** The incumbent (catches, holds ~1 s, buckles) scores
  0.0219 against a collapse-at-the-snap control's 0.00055 — a 40x
  separation, rankable by CEM. Falsifier 1 does not fire.
- **Magnitude: 27x, not the predicted 100x.** The reprice exposed a SECOND
  crusher the joints term was hiding: the support gaussian prices the
  combined body+stone CoM over the feet, and a 421 N stone welded 0.40 m
  forward moves the system CoM ~0.2 m ahead of the base — support ~1e-4
  even at pelvis 0.969 m. That is not darkness; it is the lean-back
  gradient, real signal with a physical direction (a candidate that leans
  back prices higher). The score is no longer dark — it is low because the
  incumbent genuinely does not lean back. The membrane's two-crusher
  reading: joints was noise priced as signal (fixed); support is signal
  that looks like darkness only because the frozen policy has no answer
  for it yet (the retrain's job).
- **Falsifier 2 (fling reopen) is the retrain's to test** — any elite
  holding a tissue-less stop past jf 1.2 at no cost reopens the two-sided
  form. The run-13 retrain (48x32, warm from stand_theta, secs 4.0) is in
  flight on the repriced score; its elites' jmax column is the check.

---

**RUN 13 — v11 VERDICT (2026-08-04): F6 FAIL on phases 1 and 3, and the
first PASS on the one that matters: THE BODY STANDS THROUGH THE CARRY.
The dark score was the wall, and the wall is down. The release is the
next membrane — the trainer's episode ends at the drop and it shows.**

The retrain (48x32, warm from stand_theta, repriced score, fixed handoff
event) turned the 0.022 incumbent into a **0.656** best, PROVEN on 33 of
48 turns (pelvis >= 80%, full 4.00 s, load >= 80% through the feet,
stone-floor <= 20%). The saved best's own picture: pelvis flat at
0.91-0.92 through the whole carry, plantar ~1000 N sustained, and the CoM
trace does exactly what the v11 verdict said the gradient pointed at —
it starts +0.13 m forward and **pulls back to the ankle** as the weight
arrives. The lean-back was learned, not assumed. Dark-score falsifier 2
does not fire: the saved best's carry-window fling audit reads
knee_angle_l peak 1.017, knee_angle_r 1.009, mtp_angle_l 1.008, **zero
samples past jf 1.2** — every stop approached is the tissue-bearing set,
at tissue-engagement depth. The one-sided joints term priced exactly what
it was meant to price.

Then f6 judged the saved best:

1. **THE LOAD IS FELT — FAIL (+302.6 of +421 N).** The delta is 72% of
   the weight against an 80% bar. Two candidate causes, both named, not
   yet separated: (a) windowed-mean noise — the pre-grab baseline read
   654.9 N against a static body weight of 580.6 N (+74 N of bob in the
   mean), while the carry window reads 44 N under statics, so up to
   ~118 N of the shortfall could be the instrument's windows, not the
   load path; (b) a real shortfall. v12 must separate them — the cheap
   decisive version is the quasi-static check: a motionless hold must
   read exactly wb+wl or the windows are lying.
2. **THE BODY STANDS — PASS (pelvis MIN 0.9073 m through the carry).**
   The run-12 buckle is trained away. This is the milestone's sentence:
   the body picks up 73% of its own weight and stands with it.
3. **DROPPING IS FELT — FAIL, and the cause is measured, not guessed.**
   The carry holds ~0.94 m to t=3.9; the weld releases at t=4.0; the
   plantar sum decays to ZERO by t=4.7 and the pelvis follows to the
   floor by t=5.3. The trainer's episode is 4.0 s with the weld engaged
   the entire time — **no candidate ever lived a release**. The lean-back
   is baked into the policy's open-loop terms (there is no load channel
   in the observations — z, pitch, roll only), so when 421 N vanishes in
   one timestep the compensation has nothing to react with. It is v8's
   20 ms killer run in reverse: the arrival was tapered for exactly this
   reason; the release was not. The fix is the episode, not a tweak:
   train the full cycle — weld OFF at T_DROP inside every candidate's
   life, with the load factor's expectation dropping to wb on the same
   step (the trainer's `expect` currently charges for the stone forever
   once snapped — a second instrument debt, minor but real).

**What run 13 settles.** The dark score was the last instrument wall
between the fixed event and a trained carry; it fell. The pick-up, the
catch, and the hold are PROVEN physics. What remains for the port is the
release — v12, THE SET-DOWN — plus the phase-1 instrument separation.
M8's sentence "pick up the stone, feel its weight through the body's own
load path" is true on camera for the first time; the port closes when
the body can also put it down.

---

**v12 — THE SET-DOWN (stated 2026-08-04, before the build).**

**STATEMENT.** Run 13 measured the release killing the carry: the
trainer's 4.0 s episode ends exactly at the drop with the weld engaged
throughout, so no candidate ever lived a release, and the policy's
lean-back — baked into open-loop terms, with no load channel in the
observations (z, pitch, roll only) — is pure liability when 421 N
vanishes in one timestep. It is v8's 20 ms killer run in reverse, and it
has v8's answer: the physical event is a SET-DOWN, the handoff in
reverse. At T_DROP the giver's hands take the weight back — the support
ramps 0 to full over the same derived 0.5 s, the body's load vanishing
at 2.38 kg per control interval, the arrival's number kept — and ONLY
THEN does the weld release, with zero residual, the stone free-falling
from the carry pose to rest. The episode becomes the full cycle: stand,
pick up, carry, set down, stand — f6's own 6.0 s horizon, the weld
releasing at T_DROP + RAMP_S inside every candidate's life. Three
instrument debts close with the same build: the load factor's
expectation must track what the body actually carries through the
set-down (`wb + body_frac * wl`, not "the stone forever once snapped");
the stone-floor anti-exploit check must scope to the welded window (a
landed stone is not a load-path cheat — after the release it is
SUPPOSED to be on the floor); and f6's phase-3 window must start after
the handoff completes (T_DROP + RAMP_S + 0.1), same event, trainer and
judge changing together — the run-4/5 lesson.

**PREDICTION.** Warm-started from run 13's carry best, the full-cycle
retrain passes f6 phase 3 — plantar returns to baseline ±20% after the
handoff, the body still standing at t = 6.0 — WITHOUT giving back phase
2 (pelvis >= 80% through the carry). One policy class spans both states
because the re-balance is the catch's feedback run backward through the
same taper.

**FALSIFIERS (named before the run).**

1. **The full-cycle retrain still falls after the release** — the
   z/pitch/roll policy class cannot represent both loaded and unloaded
   posture, and the observation needs a load channel (the weld's own
   constraint force, which the body physically has through its hands).
   Named, not built, unless this fires.
2. **The stone does not rest at 0.175 ± 0.05 after the handoff** (it
   hovers, or the release throws it) — the event model is wrong, not
   the policy.
3. **Phase 2 regresses below 0.80 in the full-cycle run** — the cycle
   traded the carry away; one policy class does not span both states.

**The phase-1 question, carried from run 13 and answered in run 14's
verdict, not by a build:** the +302.6/+421 N shortfall splits into
windowed-mean noise vs a real deficit by the quasi-static check — a
motionless hold must read exactly wb + wl, or f6's windows are lying.
Measured on run 14's own trace; no code changes for it.

---

**RUN 14 — v12 VERDICT (2026-08-04): FALSIFIER 1 FIRES. 48 full-cycle turns
never beat the warm start (0.558 plateau): the release is not learnable from
z/pitch/roll alone, and the membrane's named consequence is taken — the
policy needs the load channel the body physically has. Phase 1 is measured
to be INSTRUMENT, not load path.**

The full-cycle retrain (48x32, warm from run 13's best, 6.0 s episode, the
set-down at 4.0–4.5 s inside every candidate's life) saved its own turn-0
incumbent: the population mean climbed 0.054 → 0.230 toward it and no
elite ever passed it. The incumbent's own trace names the mechanism
precisely: the carry holds pelvis 0.90–0.95 m with plantar ~1000 N through
t = 4.3 — then, the handoff completing at 4.5, the body is on the floor by
5.3 s. The set-down taper gives it 0.5 s of graceful unload and it still
cannot use it: the lean-back is baked into open-loop terms, the
observations carry no load channel, and the compensation has nothing to
follow as the load leaves. This is falsifier 1 as written — the deficit is
OBSERVABILITY, and the answer is the channel the body physically has: the
Golgi tendon organs report muscle tension, and the load through the hands
is the most direct signal in the carry. v13 — THE TENDON ORGAN — is stated
next: u = a0 + kh(tgt−z) + kp·pitch + kr·roll + kw·F, F the weld's measured
constraint force normalized by the stone's own weight (a derived scale, not
a chosen one), so the compensation scales WITH the felt load — present
under load, gone when the load leaves, reactive instead of baked.

**The phase-1 question, answered by measurement (no build, as the membrane
said).** Quasi-static split on the saved best — windows where the pelvis
moves < 1 cm in 0.1 s, where statics admits no noise:

| window | motionless plantar | statics | gap |
|---|---:|---:|---:|
| pre-grab (0.3–0.9 s) | 619.3 N | wb = 580.5 N | +38.8 N |
| carry (1.6–3.9 s) | 970.4 N | wb+wl = 1001.5 N | −31.1 N |

The quasi-static delta is **+351.1 N = 83.4% of the weight — INSIDE the
±20% bar.** The windowed +302.6 N that failed phase 1 was the instrument:
the baseline window reads +38.8 N high, the carry window −31.1 N low, and
the two windows' compositions differ. The feet carry the stone; f6's
phase-1 metric needs the motionless-window delta, and that repair lands
with the v13 build (the bar itself does not move).

**What run 14 settles.** The event cycle is now physically complete
(pick-up, arrival, carry, set-down, release-to-rest — the stone lands at
0.175 m exactly) and the instruments are honest about it (expect tracks
body_frac, the sfc audit is scoped to the welded window, phase 1's noise
is measured and named). What remains is exactly one thing: the policy
cannot feel the load. Falsifiers 2 (stone rest) and 3 (carry regression)
did not fire — the stone rests at its radius and the carry held through
every turn. The plateau is the lesson Claude's walk lane taught from the
other side: a term added after training is a liability; the channel must
be trained WITH the policy. v13 trains it.

---

**v13 — THE TENDON ORGAN (stated 2026-08-04, before the build; run 14's
falsifier 1 fired, and this is the consequence the membrane named).**

**STATEMENT.** Run 14 measured that the release is unlearnable from
z/pitch/roll alone: the lean-back is baked into open-loop terms because
the policy cannot feel the load it compensates for. The body CAN — the
Golgi tendon organs report muscle tension, and the load through the
hands is the most direct signal in the entire carry. The policy class
gains exactly that channel and no more: u = a0 + kh(tgt−z) + kp·pitch +
kr·roll + **kw·F**, where F is the weld's MEASURED constraint force —
the solver's own equality rows (efc_force at the weld's efc rows),
catch transients included — normalized by the stone's weight (a derived
scale, not a chosen one). Explicitly NOT the harness's body_frac: the
harness's knowledge is not the body's sense. The kw block is nu new
numbers, zero-initialized on the run-13 best — the pad is stated, and a
zero kw reproduces the incumbent's behavior exactly (the theta-pair
lesson was about SILENT padding; this one is the membrane's own
protocol and behavior-preserving). The compensation becomes reactive:
present under load, gone when the load leaves. Trainer and judge change
together: f6 passes the same F through the parser's obs; the parser's
stand formula takes the kw block as OPTIONAL (4-block thetas behave
exactly as before — the walk lane and F3 are untouched). f6's phase-1
metric gains the quasi-static delta alongside the windowed one (run 14
measured the windowed one understates by window composition; the bar,
±20%, does not move) and judges on the quasi-static.

**PREDICTION.** Warm-started from the run-13 best, the 5-block retrain
(48x32, 6.0 s full cycle) passes f6 phase 3 — the body still standing at
t = 6.0, plantar back at baseline ±20% — WITHOUT giving back phase 2,
because kw has a signal to follow down the set-down taper and the search
starts one gradient step from a proven carry.

**FALSIFIERS (named before the run).**

1. **The 5-block retrain still falls after the release** — the deficit
   is not observability but AUTHORITY: the muscles cannot re-balance
   within the set-down's 0.5 s, and that number must then be RE-DERIVED
   against the body's measured force-bandwidth, not re-chosen.
2. **The channel feeds an exploit** — an elite that keeps F near zero
   while "carrying" (driving the weld's measured force down instead of
   bearing the load) — the load-factor audit on the elites catches it,
   and the channel's form is re-derived.
3. **Phase 2 regresses below 0.80** — the fifth block traded the carry
   away; one policy class does not span the cycle even with the sense.

---

**RUN 15 — v13 VERDICT (2026-08-04): FALSIFIER 1 FIRES A SECOND TIME, and
the follow-up measurements relocate the deficit for the third time. It is
not the event (the taper works — the body is fine half a second AFTER the
handoff), not the policy's baked lean (the F3-proven stand falls from the
same state), not an impact (the stone never touches the body). The
post-release STATE is outside every proven policy's recovery basin. The
set-down is a TRANSITION, and both policies are static postural laws.**

The 5-block retrain (48x32, kw zero-padded onto the run-13 best, full
cycle) saved the incumbent again: 0.558, never beaten, best-per-turn
0.532. The channel was explored (sd 0.3/dim on kw) and did not move the
plateau. Then three cheap measurements cut deeper than another retrain:

1. **THE SWAP TEST.** At the release instant, control handed to the
   F3-passing stand theta — the body's own proven unloaded policy, the
   parser's own grammar answer (GRAB overlay releases, STAND resumes).
   **It falls too:** pelvis 0.920 at the release, 0.899 at t = 5.0, then
   a smooth 0.6 s sink to 0.156. If the deficit were the carry policy's
   baked lean, the stand policy would have caught it. It did not.
2. **THE STONE IS INNOCENT.** Tracked through the release: it falls
   cleanly 0.2 m in front, lands at t ≈ 5.0, rests at 0.17 m, and its
   only body contact in the whole window is the known femur graze DURING
   the carry. No impact, no trip, no foot strike.
3. **THE TIMING ACQUITS THE TAPER.** The collapse begins ~0.5 s after
   the handoff completes, from a clean state (pelvis 0.899, plantar
   533 N). The set-down transient itself is survived — the body even
   rises 0.920 → 0.937 under the stand policy for 0.3 s before the sink.
   The 0.5 s handoff is not too fast. Authority within the transient is
   not the wall.

**What run 15 settles.** The deficit is the STATE, not the event and not
a policy: the carry's equilibrium (lean-back, knees on tissue, pelvis
~0.90, the configuration 421 N at 0.40 m requires) lies outside the
recovery basin of the unloaded stand, and the carry policy's own
unloaded basin was never trained (its 1.5 s of post-release per episode
are spent falling, so the gradient there is noise). Physically: at the
release the body must move its CoM from the carried equilibrium back to
the unloaded one — a MOTION, the same species as the walk's weight
shift, and Claude's lane has measured for weeks that static postural
laws do not do transitions. Run 12's falsifier-2 routing said it: the
pick-up is M8b's motion to build. The set-down is the second half of the
same sentence.

**v14 — THE RETURN — is named, and its protocol is measurement-first:**
collect the post-release states (snapshots at release + 0.3/0.5/0.7 s
from the full-cycle runs — the states exist, recorded), and train the
recovery FROM them — a recovery curriculum over real states, warm from
the stand theta, judged by F3 from those states. The alternative (price
distance-to-stand-pose at the release instant inside the carry score)
adds a chosen term; the curriculum adds none. If even the recovery
curriculum cannot find a policy covering both basins, then the two
basins are disjoint in this muscle set and the membrane after that asks
whether the carry equilibrium itself must change (a closer carry pose,
measured collision-free — CARRY_RELPOS has a second, nearer solution).

---

## v14 — THE RETURN (recovery curriculum over real post-release states)

**STATEMENT.** The post-release fall is not a policy deficit and not an
event deficit — it is a TRAINING-DATA deficit: every proven policy is a
static postural law, and no training run has ever presented the
post-release state as a START. End-to-end cycle training cannot fix
this because its candidates reach the post-release state already
committed to their own approach trajectory (and usually already
falling), so the gradient at the state itself is noise. Training the
recovery FROM the real post-release states — resetting each candidate
to a recorded snapshot and asking it to stand from there — is the
missing data, and a policy recovered that way holds F3's bar from
those states.

**PREDICTION.** A 4-block theta warm-started from the F3-passing stand
theta, trained against snapshots drawn from the full-cycle runs at
release + {0.0, 0.3, 0.5, 0.7} s (12+ distinct states: qpos, qvel,
ctrl, eq_active, xfrc_applied), holds F3's bar (pelvis ≥ 80% of
0.9201 m, joints within stops) for ≥ 3.0 s from EVERY snapshot in the
training set — and, the audit that makes it real rather than a reset
exploit, completes the FULL CYCLE end-to-end under f6_grab with phase
3 PASS when the recovery takes control at the release.

**FALSIFIER 1 — the basins are disjoint.** If the curriculum plateaus
below the bar on states its own candidates were reset into (a falsifier
that cannot blame reachability), then no policy in this muscle set
covers both the carry equilibrium and the unloaded stand from the
post-release state. The question v14's own verdict named fires: the
CARRY EQUILIBRIUM is the membrane — a nearer collision-free
CARRY_RELPOS (the run-12 clearance probe found candidates) moves the
post-release state toward the stand basin instead of asking the policy
to span the gap.

**FALSIFIER 2 — the reset is the exploit.** If the curriculum-trained
policy passes from snapshots but the full-cycle run (carry policy until
release, recovery after) still falls, the recovery only works from
states it has memorized and the prediction's second clause dies. The
verdict is then: the recovery is real but the HANDOFF is the membrane —
the carry policy must arrive at the release in a state inside the
recovery's basin, and the carry score needs its end-of-episode state
priced against the recovery's entry set. That prices a state, not a
term.

**What is NOT in this membrane.** No new formula terms (the stand
grammar suffices — the swap test showed even IT nearly holds: 0.937 at
+0.3 s), no new channels, no changed bars. The build is: a snapshot
collector (states already exist in the recorded runs), a
`--from-states` training mode (random snapshot per candidate, warm
from stand theta), and the two-stage full-cycle audit (carry theta →
release → recovery theta). Zero chosen terms.

---

**RUN 16 — v14 FIRST VERDICT (2026-08-04): the 10-state curriculum plateaus,
and the measurement underneath it is exact.** The snapshot restore is
bit-faithful (replay of state 0 under its own generating policy matches the
recorded collapse to the millimeter at every 0.1 s -- the states are the
real trajectory, not a corrupted copy). The control numbers the debt
precisely: the F3-proven stand falls from ALL TEN standing states
(0/10; even from the release instant itself -- pelvis 0.920, nearly
motionless -- it holds ~1.0 s, rises to 0.937, then sinks through the
bar). 48x32 CEM warm from the stand theta never beat the incumbent
(0.088): per-state scores [0.116, 0.006, 0.000] on the fixed trio show
the deep states (falling at 1.3 m/s past 0.7 m) are unrecoverable by
physics, not policy, and their zero scores compress the landscape.

**The addendum the picture named.** The real cycle is DETERMINISTIC --
the recovery only ever faces the ONE state the carry policy produces at
the release, plus its immediate neighborhood. A specialist trained on
state 0 alone is not a reset exploit; it is the operating point, and
the two-stage full-cycle audit (carry theta to the release, return
theta after) is its judge. `--only` built into train_return.py; runs
17 (state 0) and 18 (states 0,1,2) in flight. If even the state-0
specialist plateaus below the bar, falsifier 1 fires on the shallowest
possible state and the CARRY EQUILIBRIUM becomes the membrane -- a
nearer collision-free CARRY_RELPOS moves the post-release state toward
the stand basin instead of asking the policy to span the gap.

---

**RUNS 17+18 — v14 SECOND VERDICT (2026-08-04): FALSIFIER 1 FIRES on the
shallowest possible state, and its named fallback is REFUTED by
measurement. The pose cannot move; the policy class must.**

- **The specialists plateau.** State-0 alone: 48 turns converged
  (best == mean from turn ~25) at held 1.16 s of the 3.0 s bar, pelvis
  MIN 48% -- trained on the ONE state the deterministic cycle produces,
  warm from the F3-proven stand, and still falling. States {0,1,2}:
  converged at 0.94 s. The 10-state run's plateau was not the deep
  states poisoning the signal: the deficit survives at the operating
  point itself. (Instrument note: both runs drew return_turn_*.png to
  one directory; run 18 overwrote run 17's pictures mid-flight --
  namespace by --out next time. The numbers are untouched.)
- **The fall, forensically.** From state 0 under the stand theta: the
  CoM starts 4.5 cm behind the foot centre and drifts to -31.6 cm in
  1.0 s -- far outside any base of support (half-length 13.6 cm) --
  while roll runs 0 -> -50 deg. The carried equilibrium's lean-back,
  unopposed once the 421 N leaves, sits the body down backward with a
  lateral runaway on top. Both planes move; neither is static-recoverable
  from that configuration.
- **The named fallback is measured dead.** Falsifier 1 said ask whether
  a NEARER collision-free CARRY_RELPOS exists. The run-12 clearance
  method, swept in the current frame: 0.35/0.30/0.25/0.20 m forward all
  penetrate the pelvis (worst -0.19 m at 0.20); lower penetrates the
  femurs; torso-centre-height at 0.30 still penetrates 3.3 cm. The
  0.40 m carry is the ONLY collision-free sagittal pose at this stone's
  size. Physics priced the stone; the pose is already at its wall.

**What runs 16-18 settle.** The deficit is neither reachability (the
curriculum reset INTO the states), nor the operating point (the
specialist had exactly it), nor movable by the pose. What remains is
the formula's own shape: u = a0 + kh*(tgt-z) + kp*pitch + kr*roll is a
STATIC law -- position feedback only, zero rate terms -- and the
post-release state is DYNAMICALLY unstable (backward drift 0.3 m/s at
handoff, roll accelerating). Claude's lane settled the same sentence
for walking: static postural laws do not do transitions. The set-down
is a transition.

**v15 -- THE SPINDLE -- is named.** The rate sense the formula lacks is
not a hack: the muscle spindle (Ia afferent, stretch-rate feedback) is
the most replicated sensorimotor circuit in physiology, and it is the
same legitimacy class as v13's Golgi tendon organ (the load channel
that was DERIVED, not tuned). The formula gains the rates of exactly
the quantities it already senses -- z-dot, pitch-rate, roll-rate --
nothing else. RULE 0 below.

## v15 -- THE SPINDLE (rate feedback on the stand grammar's own channels)

**STATEMENT.** The post-release state is recoverable by the stand
grammar plus rate feedback -- u = a0 + kh*(tgt-z) + kp*pitch + kr*roll
+ kv*zdot + kpv*pitch_rate + krv*roll_rate, the rates of the SAME three
sensed quantities -- where the position-only law provably falls (runs
16-18). Standing balance in the literature is a rate-dependent reflex
(spindle Ia feedback, ~40-50 ms loop), not a static map; the formula
without its rates is half the reflex.

**PREDICTION.** A 7-block theta (the four position blocks + three rate
blocks, zero-padded onto the stand theta so the incumbent's behavior is
preserved exactly), trained from state 0, holds F3's bar (pelvis >= 80%
of 0.9201 m) for 3.0 s from state 0, AND passes the two-stage
full-cycle audit (carry theta to the release, return theta after;
stone rests 0.175 +/- 0.05 m).

**FALSIFIER 1 -- authority, not sensing.** If the rate-augmented search
also plateaus below the bar from state 0, then no policy of ANY sensing
class in this muscle set recovers that configuration: the carried lean
at this stone mass is physically unrecoverable after release, and the
milestone's own stone (59.49 kg -- the ledger's derived object) becomes
the question. That would be a finding about the WORLD, not the policy.

**FALSIFIER 2 -- the static stand trades away.** If the rate terms pass
from state 0 but F3 from the keyframe regresses (rate gains
destabilize quiet standing), then recovery and standing are DIFFERENT
policies and the parser's overlay grammar (the GRAB precedent: a verb
layered on STAND) gets a RETURN overlay for the post-release window --
the grammar's own answer, not a monolith.

**What is NOT in this membrane.** No new SENSED quantities (the three
rates are the time-derivatives of z, pitch, roll -- the formula's own
channels), no changed bars, no re-derivation of the pose (measured at
its wall above), no score changes. Zero chosen terms.

---

**RUNS 19+20 — v15 VERDICT (2026-08-04): the SPINDLE channels are INERT
(1.20 s / 1.02 s vs 1.16 s / 1.24 s position-only -- the rates of z,
pitch, roll add nothing), and the capture measurement relocates the
deficit a FOURTH time, to the exact quantity the policy cannot see.**

Before accepting v15's falsifier-1 letter ("authority, not sensing"),
the authority question was quantified with the published criterion
(Hof 2008: XCoM = x + v/w0, w0 = sqrt(g/l); CoM velocity kinematic via
mj_comVel, stone excluded): **at the release instant the extrapolated
CoM is INSIDE the actual base of support -- XCoM-x -0.180 m against a
0.283 m half-extent, 10 cm of margin.** Capturable without a step. The
state is recoverable by the physics; five converged searches (runs
16-20, two policy classes) cannot recover it. So it is not authority.

What the policy lacks is not rate but POSITION OF THE CoM ITSELF. The
formula senses (z, pitch, roll) -- pelvis height and orientation. The
reward prices (dx, dy) -- CoM over the foot centre. At state 0 the
height is AT target and rising (0.920 -> 0.938) while the CoM drifts
backward past the margin: the policy literally sees nothing wrong until
the drift is 0.3 m/s, and pitch encodes the lean only through a
configuration-dependent mapping (3.6 deg at state 0 -- a crouch with
flexed knees reads near-zero pitch while its CoM sits 4.5 cm back).
Third time in this membrane chain: the missing channel is exactly the
quantity the reward prices and the formula lacks (v13 the load, v16 the
sway). Observability is the recurring deficit species.

## v16 -- THE GRAVICEPTOR (the CoM-over-support channel)

**STATEMENT.** The stand grammar's sensed set is incomplete: it lacks
(dx, dy) = body-CoM minus foot-centre -- the quantities stand_reward's
support gaussian prices, the ankle-strategy literature's own variable
(Horak & Nashner 1986), and a real biological sense (graviceptive /
vestibulospinal sway estimate). Adding kx*dx + ky*dy -- two blocks, no
rates (v15 measured them inert), the body-only CoM (the stone is the
giver's after the release; subtree_com including it prices a landmark
the body no longer carries -- rule 19, the reward's dx/dy switch to
body-only under the same flag) -- makes the capturable state-0
recoverable.

**PREDICTION.** A 6-block theta (a0|kh|kp|kr|kx|ky, zero-padded from
the stand theta), trained from state 0, holds F3's bar for 3.0 s from
state 0 and passes the two-stage full-cycle audit.

**FALSIFIER 1 -- THEN it is authority, quantified.** If the sway
channel also plateaus below the bar from a state the capture criterion
proves capturable, the deficit is the muscle set's realizable wrench,
and the next measurement is the required ankle/hip moment from the
LIPM against what spanning() measures the muscles can produce.

**FALSIFIER 2 -- the sense games the reward.** If training passes from
state 0 but the two-stage audit fails, the policy learned the reset,
not the return; the handoff becomes the membrane.

---

**RUNS 21+22 — v16 VERDICT (2026-08-04): FALSIFIER 1 FIRES A THIRD TIME.
The GRAVICEPTOR channel was explored (kx/ky std 0.30 over 48 turns) and
converged to ~zero mean; the wall stands at 1.20 s -- invariant across
FOUR membranes and seven campaigns (position 1.16 s, rates 1.20 s, sway
1.20 s, neighborhood 1.24 s). The score curve is the picture of a clean
optimization finding its class ceiling: smooth climb, saturate, flat.**

The chain of relocations is now complete: not the event (the taper is
acquitted -- the collapse starts 0.5 s AFTER the handoff), not the load
sense (v13 inert), not the rate sense (v15 inert), not the sway sense
(v16 inert), not the pose (measured at its collision wall), and NOT the
physics (the release instant is capturable -- XCoM 10 cm inside the
BoS). A static, decoupled, scalar-channel law simply does not realize
the capture the physics permits -- and the capture literature's own
answer for a drift the in-place strategy cannot arrest is THE STEP,
which is the walk lane's wall exactly (Claude's ninth hypothesis:
transitions must be TRAINED, never appended).

**But the fourth relocation names a design defect, not a policy one.**
v12's set-down releases the stone AT CARRY HEIGHT -- the giver snatches
59.49 kg out of mid-air at 0.40 m forward, and the body must recover
from the full lean-back with nothing to push against. Nobody sets down
a stone that way. The physical set-down is a LOWERING: the body squats
WITH the load (the weld rides the torso; the stone descends with it),
the giver takes the weight AT THE BOTTOM, and the release state is a
SQUAT -- which is inside the stand policy's PROVEN basin, because F3's
own keyframe is a seated pose the policy stands up from at every reset.
v12 optimized the event for instrument cleanliness (the arrival's 0.5 s
number reversed) and priced the body a mid-air snatch no human
attempts. The wall at 1.2 s is the price of that design.

## v17 -- THE LOWERING (set the stone down; do not snatch it)

**STATEMENT.** The set-down's unrecoverable post-release state is an
artifact of releasing at carry height. If the descent is part of the
event -- the welded stone descends with the torso along a derived path
to its rest height (0.175 m), the giver's taper runs AT THE BOTTOM, and
the weld releases there -- then the post-release state is a deep squat
with quiet CoM, inside the F3-proven stand basin (the keyframe is
seated; standing up from it is the policy's most-practiced motion),
and THE RETURN IS THE STAND ITSELF -- no new channels, no new policy,
the parser's own grammar (GRAB overlay releases, STAND resumes).

**PREDICTION.** With the descent added to the event (a derived
constant-velocity lowering of the weld target from CARRY_RELPOS to rest
over the same 0.5 s the arrival used, the taper coincident with the
descent's end), the PROVEN carry theta rides the descent, and the
F3-PROVEN STAND theta -- untrained, zero new numbers -- holds the bar
for 3.0 s after the bottom release. Zero training. If the stand must
be re-taught to stand up from a squat it was literally seeded in, the
basin claim was wrong and that is measurable at turn 0.

**FALSIFIER 1 -- the loaded descent itself destabilizes.** If the carry
theta cannot ride the descent (the squat under 421 N breaks the carry
before the bottom), then the descent joins the pick-up as M8b's second
motion to TRAIN (a descent curriculum over the descent path's states --
v14's own method, now with a target basin that exists).

**FALSIFIER 2 -- the squat is NOT in the basin.** If the stand theta
falls from the bottom-release state, the seated keyframe was not the
basin evidence it read as; measure the state against the keyframe
(joint by joint) and the difference names the real gap.

**What is NOT in this membrane.** No new formula blocks, no new
channels, no retraining by default (the PREDICTION is zero-shot), no
changed bars. The descent path's endpoint is the stone's measured rest
height; its duration is the arrival's own 0.5 s. Zero chosen numbers.

---

**RUN 22 + THE ZERO-SHOT (2026-08-04): v16 closes (neighborhood sway
0/3, best 1.32 s -- the 1.2 s wall invariant across all four
observability membranes), and v17's zero-shot prediction is REFUTED
with its mechanism named, which redesigns the event.**

The zero-shot probe ran the full cycle: the carry theta rides a target
ramp (tgt - 0.628 m, the derived descent depth: stone z 0.803 at carry,
rest 0.175), the taper concurrent, weld release at the ramp's end, the
F3-proven stand theta after. What the table showed:

1. **The target-verb does not actuate a descent.** Over the 0.5 s LOWER
   window the pelvis moved 0.003 m. The carry theta's kh block is
   mixed-sign per muscle (mean -0.025, std 1.27) -- trained to HOLD at
   one operating point, not to track a moving target; lowering the
   target ACTIVATES the negative-kh muscles and the two signs cancel.
   The verb exists in the grammar, but this policy's gains make it a
   no-op. The descent must be TRAINED -- v17's falsifier 1 route is the
   build.
2. **Release-on-timer is wrong physics.** The weld released at the
   ramp's end with the stone still at 0.81 m -- it free-fell 0.63 m to
   the floor, the mid-air snatch again, delayed. The real event is
   CONTACT-TRIGGERED: the body squats the full 421 N down (a loaded
   squat -- the descent is trained under load), the stone LANDS, the
   giver's taper runs on floor contact over the arrival's own 0.5 s,
   the weld releases at the taper's end. The release state is then a
   deep squat, unloaded, quiet -- the basin F3's seated keyframe proves.

**v17's build, settled by the zero-shot's two lessons:** LOWER phase in
the full-cycle trainer -- tgt_now ramps 0.9201 -> (tgt - depth) over
LOWER_S = 0.5 s with body_frac = 1.0 THROUGHOUT (the loaded squat; the
giver does not help until the floor does); the height gaussian tracks
tgt_now (stand_reward with the target swapped -- the target is the
verb, the reward prices the verb); on stone-floor CONTACT (measured,
not timed) the taper runs and the weld releases; tgt ramps home; the
return needs no training IF falsifier 2 stays quiet. The campaign is
run 23.
