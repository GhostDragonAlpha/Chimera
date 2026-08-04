# THE STEP — MOVE as STEP + PLANT + STAND (the walk's second theory)

> DRAFT membrane, stated 2026-08-04. Opened by the walk port's falsifier 3
> FIRING (`tools/walk_port.py` LEDGER, third entry): STAND + one rhythm, six
> numbers, plateaued at 34% travel with upright never in the same body,
> across 3,000+ rollouts and three plant/reward configurations. The milestone
> always said what walking is composed of: **STEP + PLANT + STAND**. This is
> that composition, stated so it can lose.

---

## WHAT THE ATOMS ALREADY PROVE (`tools/action_tests.py`)

- **STANCE is a conservation law**: `sum(plantar) = (1−s)·W` across three
  harness settings, slope −W. The feet carry exactly what nothing else
  carries. Load transfer has a judge before it has a controller.
- **SWING is a compound pendulum**: the unloaded leg's period is `2π√(I/mgd)`
  from the model's own inertia tensors, measured to within the membrane's
  15% bar. A step's TIMING is a property of the body; nobody selects it.
- **BALANCE is an inverted pendulum**: divergence at `ω0 = √(g/H)`, the
  0.4066 s time-to-fall every control-rate argument rests on. STAND is the
  cage; the walk may not leave the cage.

## THE LANDSCAPE THE FIRST THEORY LEFT

`WalkOscillator` (entrainment, the `swing_allowed` interlock, evidence
preserved in commit `7a819fe`) was never judgeable — the parser's MOVE drove
the clock while the trainer drove the sensors. That defect class is now
named and closed (train what you judge, `7376a54`), and its resolution makes
this membrane's mechanism CHEAP: the parser's `obs` is a free-form dict by
design (`tools/parser.py:143`), so foot contact enters the parse with no
grammar change at all — the "parser obs amendment" the walk ledger priced
is the harness feeding two more keys, not a new parser.

---

## RULE 0 — THE THEORY

**STATEMENT.** A walk is a per-leg two-state machine composed INSIDE the
stand formula, and its transitions are EVENTS THE BODY CAN OBSERVE, never
clock ticks:

- **STANCE** — the leg carries. STAND cages the inverted pendulum over it
  (the frozen stand theta, untouched — composition, not retraining).
- **SWING** — the leg unloads and swings as the compound pendulum SWING
  validated: effort at the hip/knee/ankle through the muscles, never a
  commanded angle (the operator's control law: command the process and its
  stop condition). The swing's duration is the pendulum's own; the effort
  profile's cadence is DERIVED (theHuman's stride, closure-checked against
  the pendulum T the way `walk_port` closure-checks speed).
- **PLANT** — the touch sensor's rising edge IS stance onset, the one event
  in the gait cycle the body can observe without being told (the
  `plantar_pressure` port validated those sensors read 0.000000 lifted).
- **THE INTERLOCK, DERIVED**: duty factor 0.6027 > 0.5 means both feet are
  never airborne in a walk — a leg may not enter swing while the
  contralateral foot is unloaded. This is `swing_allowed`, promoted from
  the deferred oscillator into the composition's law.

No sinusoid is injected. The limit cycle is PLANT → unload → SWING → PLANT
through the sensors; periodicity is an OUTPUT the judge measures, not an
input the program plays back. The only trained numbers are the swing
efforts (the OSC_JOINTS pattern: hip/knee/ankle amplitudes and intra-limb
offsets — six or fewer; cadence, antiphase, and the interlock are derived).

**PREDICTION.** `tools/f4_walk.py` — its bars do not move — reports: travel
within 75–125% of the derived 0.9924 m/s, footfall periodicity ≥ 0.60,
upright ≥ 80% of the stand target through the whole run, and the oscillator
ablation (swing efforts zeroed) below 20%. **And the new fifth judge, the
SENSOR ablation: with contact obs zeroed the machine cannot transition and
travel collapses** — the mechanism is the sensors, or the composition is
lying about what drives it.

**FALSIFIERS.** Named before the build, three independent triggers:

1. **It becomes a hop or a run.** Measured duty factor < 0.5 — both feet
   airborne — at any point the judge samples: the interlock is decorative
   and the machine walks by leaving the ground.
2. **The sensor ablation still walks.** Travel survives with contact obs
   zeroed: the transitions are a clock in disguise and this is the
   falsifier-3 program wearing a state machine's clothes.
3. **The atoms do not compose.** No trained setting clears the bar the
   first theory fired on (50% of derived speed AND upright in one body) —
   then walking needs structure below the atom level, published per Rule
   17, not patched with a joint-angle target.

---

## NEXT

1. `f4_walk.run_one` feeds `cr`/`cl` from the model's own touch sensors into
   obs (the harness already imports `foot_contact`'s pattern from
   `train_walk`); the sensor ablation joins the judge as judge five.
2. `move_formula_fn` v2: the per-leg state machine inside the stand
   formula, reusing `muscle_groups` and the `swing_gate` slot `walk_formula`
   already carries. The trainer drives THE SAME machine (train what you
   judge — the lesson this project paid for twice in one day).
3. Train the swing efforts; judge. Record here, either way.

---

## BUILD RECORD (2026-08-04, built as stated — new files, the first theory untouched)

- `tools/step_port.py` — `StepMachine` (transitions are sensor events only:
  swing enters on the contralateral foot's PLANT edge, stance on the own
  foot's; the interlock is the door's shape, not a check), `step_formula`
  (stand frozen + 6 swing efforts), `move_formula_fn` (the machine lives in
  the parser formula's closure — obs gains `cr`/`cl`, no grammar change).
  The swing window is DERIVED: (1 − 0.6027) × 1.1730 = **0.4660 s**.
- `tools/train_step.py` — CEM over the 6 efforts, driving THE SAME machine
  and formula the judge drives. Trains 8 s, judged 6 s.
- `tools/f5_step.py` — f4's four bars unmoved + judge five (sensor ablation)
  + judge six (duty ≥ 0.50 each foot, falsifier 1's shape). Zero-theta
  sanity: the body simply STANDS (pelvis 85%, travel −0%, both ablations
  trivially collapsed) — the machine does not destabilize the stand.

**CLOSURE FINDING, measured at build time** (`python tools/step_port.py`):
the duty-derived swing window is 0.4660 s; the leg's passive pendulum
half-period, computed from the model's own inertia tensors (`a_swing`'s
prediction half), is **0.8963 s — 92% longer**. The finding: a human swing
is not ballistic. The leg is driven through its swing at roughly twice its
passive rate by muscle effort — which is exactly what the six trained
efforts are FOR. If swing were pendular, the efforts would be noise on a
motion the body already owned. The window stays duty-derived (the sensors
own the cadence; the window only splits the effort profile into
early/late); the pendulum number is the cross-check, and the cross-check
says: swing is work, not falling.

## VERDICT (2026-08-04): v1 FAILS — falsifier 3's shape, and the mechanism is MEASURED

Session: 24×32 CEM, 792 rollouts. Score plateaued identically for the last
16 turns (variance collapsed to the 1e-3 floor — converged, not stalled).
`f5_step.py` on the session-best theta: travel −4%, periodicity 0.18,
upright 47% (fall at 3.52 s) — FAIL on 1/2/3. **Judges 4, 5, 6 PASS**: the
efforts do work, the sensors are the mechanism (zeroed obs → the body
stands; falsifier 2 does NOT fire), no hopping.

Two candidates, one verdict:

- **Best-score theta** (−4.115): marches in place — the machine visibly
  STEPS (footfall alternates at ~0.2 s, duty 0.66/0.75), sensors drive real
  transitions, pelvis holds 3.2 s. Travel −4%. The score priced survival
  over motion and selected standing.
- **Best-travel candidate** (turn 7, 52%): accelerates forward and falls at
  2.4 s. The travel curve is *accelerating into the fall* — the signature
  of toppling, not walking.

No trained setting held 50% of derived speed AND upright in one body.
**The mechanism, measured not inferred: v1 gives the stance leg the stand
formula ALONE, so the composition has no propulsion source. Without
push-off, forward motion can only come from falling forward** — and the two
candidates are the two ways that plays out: topple (travel exists, upright
dies) or march in place (upright survives, no travel). This is not "the
atoms don't compose" in the deep sense — it is the composition missing the
stance leg's content, which v1 omitted by design ("no push-off term in v1:
if no travel results, that is a measured finding"). Travel resulted. The
finding is published here per Rule 17.

---

## AMENDMENT — v2: THE PUSH-OFF (stated before the build)

**STATEMENT.** Propulsion is not toppling. In human gait the body's forward
work comes from the STANCE leg — terminal-stance ankle plantarflexion
during single support — not from the swing, and not from falling. v2 adds
exactly that, in the machine's own vocabulary: while the contralateral leg
is in LATE swing (its phase ≥ half the derived window — the machine's own
single-support second half, no clock, no new state), the stance leg's
measured plantarflexors (`muscle_groups`' ext for `ankle_angle`) are driven
reciprocally. ONE new trained number (the push-off amplitude; seven total).
Someone can disagree: push-off could be hip-first, or early-stance — the
published record (Perry 1992, gait analysis: ~80% of propulsive work at the
ankle in terminal stance) says ankle, late; the falsifiers below decide.

**PREDICTION.** The same trainer, the same judge, bars unmoved: travel
≥ 50% of derived speed AND upright (pelvis ≥ 80% of target, no fall) in one
body — the bar v1 could not clear — because propulsion now has a source
that is not toppling.

**FALSIFIERS.** 1. The search converges the push-off amplitude to ~0 and
nothing changes — the mechanism is not ankle push-off; published. 2. Travel
rises but upright still dies past ~2.5 s — the deficit is catch-up, not
propulsion; the swing-timing question reopens with data. 3. Carried from
v1: sensor ablation must still collapse travel, or the machine became a
clock in disguise.

## VERDICT, v2 RUN 1 (2026-08-04): mechanism RECRUITED, gradient LIVE, budget extended

24×32 CEM. `f5_step.py` on the session-best (score −3.815, turn 17): travel
10%, periodicity 0.43, upright 48% (held 4.60 s) — FAIL on 1/2/3; judges
4/5/6 PASS again. Read against this amendment's three falsifiers:

1. **Push-off rejected?** NO — P_push converged to **0.2121**, recruited at
   the same magnitude as the swing efforts (B_hip 0.2289, A_ankle 0.2497).
   Falsifier 1 does not fire: the search wants the mechanism.
2. **Travel rises, upright dies?** NEITHER CLEANLY — the shape changed
   instead: survival jumped (held 2.4 s → **4.1–4.6 s every turn**, pelvis
   0.9–1.0 m through it) while travel stayed 10–29%. The body now MARCHES —
   real alternating support, duty 0.88/0.61 — where v1 could only topple or
   freeze. The push-off bought balance, not yet speed.
3. **Sensor ablation clean?** YES — zeroed obs collapses travel (−0%). The
   machine is still the sensors.

**The decisive observation: the population mean was STILL CLIMBING at turn
24** (−4.48 → −4.05, monotonic in the last decile) where v1 had plateaued
identically for 16 turns. v1's theory was exhausted; v2's is not — its
budget is. A converged search answers the question; a climbing one has not
finished answering. The prediction (≥ 50% AND upright) stands UNMOVED, and
the run continues: warm start from the session-best, 48 turns.

Verdict: _pending the continuation._
