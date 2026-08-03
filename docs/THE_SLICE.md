# THE SLICE — the smallest thing that is the game

<!-- CHIMERA-LAW -->
> **RULE 0 — EVERY MEMBRANE IS A THEORY. STATE IT BEFORE YOU BUILD IT.** Three parts, all three
> required: a **STATEMENT** someone could disagree with · a **PREDICTION** you have not measured
> yet · a **FALSIFIER** named *before* the run. **A description survives any result; a theory can
> lose.** No falsifier, no build.
>
> **RULE 1 — DERIVE IT BEFORE YOU TRAIN IT.** A parameter sweep is an admission the derivation was
> not done. Before any run, any sweep, any "let's try N variants": trace the variables and show the
> equations close. If you are choosing a number, you broke the chain and substituted taste for a
> law. Ask what QUESTION each variant answers — if the answer is "which number is best", STOP.
>
> **RULE 0 IS ENFORCED AT S-1 VALIDATE** — every port tested alone, and `port_test()` REFUSES to
> register a test that names no falsifier. The model it feeds: `docs/THE_COMPILER.md` — ports →
> primitives → programs → parser → runtime → calibration.
>
> **[docs/THE_LAW.md](THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 26 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

> Drafted 2026-08-03, operator-approved direction: **finish the ladder; THE_LIVING_MATTER runs in
> parallel.** Status: THEORY, UNRUN. The product is a membrane too, so it gets a statement it can
> lose.

---

## THE THEORY

**STATEMENT.** The smallest thing that is the game — the slice — is this: *a player stands,
walks, and touches three classes of passive matter on aBlueWorld, through twelve buttons,
rendered by the splat engine, with every number on screen tracing to a parent membrane or a
measurement.* Everything beyond that — vehicles, buildings, NPCs, shifting biomes — is
ADDITION on this proven base, which is the one operation the architecture is good at.

**PREDICTION (not yet measured).** A blind vision read of a recorded slice session — the
dyad's own instrument, pointed at the product — names it "a person walking on a living
world" at alignment ≥ the engine's threshold. No slice session has ever existed, so no such
reading has ever been taken.

**FALSIFIERS (named before the run).** Any one kills the slice *as stated*:

- **F1.** Any number on screen that cannot be walked to a parent `numbers.json` or a cited
  measurement (`python -m core.why --feature slice --loop` reaches neither PHYSICS nor THE
  HUMAN). A typed constant in the product is the product failing, not a bug.
- **F2.** The blind read does not converge — the render is wrong, and no amount of parser
  polish fixes physics (redo the physics, never the tolerance).
- **F3.** The body cannot stand up on the world's own gravity through the parser with
  zero pose-scripted frames. If a single frame is kinematically placed, the slice is a
  cutscene wearing a game's clothes.

---

## WHERE THE LADDER STANDS (2026-08-03, SECOND READING — from the ledgers, not from memory)

| layer | status | the gap |
|---|---|---|
| PORTS | **12/12 validated** (`tools/port_tests.py` + `port_tests_more.py`) | — |
| PRIMITIVES (mechanism) | **7/7** (`tools/primitive_tests.py`) | — |
| PRIMITIVES (action) | **9/11** (`tools/action_tests.py`, 1 REFUSED as absent structure) | PUSH, PULL fail HONESTLY — foot geometry sets the slip bound, not friction; the falsifiers fire as designed |
| PROGRAMS | STEP/PLANT/REACH/GRIP/BRACE/STAND/WALK designed (`docs/CONTROLLER_MAP.md`) | not composed |
| PARSER | ~12 buttons, two bindings, one formula layer — designed | not built |
| RUNTIME | `w` from `tools/world.py`, no fallback | not built |
| CALIBRATION | DERIVED / INGESTED / TRAINED, `training_gate.py` enforces Froude | gate exists, layer not assembled |
| THE WORLD ANSWERS | THE_LIVING_MATTER Phase 1 ✅ (energy trace, exact, under test) + parallel area update ✅ (read-live/commit-on-accept; H falls and plateaus, parity restored) | Phase 2: the control run — research tissue surface tensions, derive the 5×5 J |

**The first reading's three red mechanism primitives are GREEN, and each was an instrument
fault with a different name** (the full evidence lives in `tools/primitive_tests.py` at each
test and in the note above `p_stiffness`; the ledger table is at `docs/THE_PIECES.md` §16):

- **STIFFNESS** conflated muscle STRENGTH with feedback DIRECTION — the loop drove its
  strongest group, which at the knee accelerates the same way gravity pulls. The feedback is
  now strictly directional, and the bench is the ankle: measured, the knee's strong muscles and
  its gravity load point the same way (+2277 vs +1164 rad/s²), so the knee cannot answer this
  question at all. 2.07° closed vs 16.44° open.
- **WEIGHT_TRANSFER** stood its statue on a mid-gait keyframe (one foot 2.3 cm up), overwrote
  the root orientation to "lean" it, and let it keep momentum — it tipped, bounced, or went
  integrator-unstable. Now: symmetric default pose, 4 mm seating penetration, COMPOSED lean
  quaternion, all velocity zeroed every step. Totals 537–613 N of 581; share moves 79 pts.
- **UPRIGHT**'s matched-mean ablation was structurally blind — a proportional loop at
  equilibrium settles where gain×|lean| equals its own mean drive, so the control was the same
  system (proven six ways, ratio 1.00). Its drive direction was also inverted. The ablation is
  now the signal DESTROYED: the same loop reading the gravity vector inverted. RMS lean 10.37°
  true vs 14.05° inverted, the inverted loop spending MORE drive to hold worse.

The lesson the three share is now written where the next reader will hit it: when a falsifier
fires, doubt the INSTRUMENT first — but doubt it by measuring, and keep the falsifier's intent,
not its first construction.

---

## THE SEQUENCE

**Phase A — green the mechanism layer.** ✅ DONE (2026-08-03): 12/12 · 7/7 · 9/11 on the full
battery, plus 1 REFUSED (GRIP — no arm in the model). The four action failures resolved as:
STEP and BALANCE were instrument faults and are now PASS (contact-force ground truth, solver
pivot + exact cosh fit); CROUCH was a posing fault and is now PASS (a crouch is a POSE —
closed-form squat 22.5/45/22.5°, braced AT the pose, 8.7% between the two routes); PUSH and
PULL are HONEST FAILURES — their falsifiers fire on real physics, not harness: from the
symmetric stance the body slides at 137.9 N push / 88.1 N pull against one 348.3 N cone
bound, and the ankle-height control (480.1/157.7 N, 67.1% apart, one direction ABOVE μN)
proves the bound is set by toe/heel capsule geometry and the tipping moment, never by the
cone alone. Full evidence in `tools/action_tests.py` at `_slip`, `a_push`, `a_pull`.

**Phase B — LIVING_MATTER.** ✅ Phase 1 DONE (2026-08-03): the energy-trace instrument in
`Chimera/core/matter_gpu.py` (per-pass Hamiltonian, one readback, persistent
`open_lattice/step/close`), exact to 0.0000% against the CPU Hamiltonian and under test
(`Chimera/tests/test_matter_gpu_energy.py`). Its falsifier fired on first use (parallel
area update overshoots) and the prerequisite membrane is RESOLVED the same day: the
marginal is a plain read of the live count, committed only on acceptance — H falls
8.87M → 6.51M and plateaus, parity sorts (differential 17.2/18.1/24.1, uniform not),
areas hold at the CPU's own offset. Two predictions missed and are recorded, not
reconciled: σ_a is 100–152 cells vs the 2.58 serial scale (cohort-correlated wander —
the deterministic z-slab route remains named if the operator wants the last 50×), and
the 1% monotonicity bar was underived — the trace's own thermal scale is 1.51% and the
check now derives its bar from the trace. **Phase 2 DONE (2026-08-03):** the 5×5 J is
DERIVED from measured tissue surface tensions (Foty 1996: limb bud 20.1 / pigmented
epithelium 12.6 / heart 8.5 / neural retina 1.6 mN/m; Girifalco-Good interfacial
default; α via the cortical-floor anchor, `Chimera/core/matter_derive.py`) — F1 PASS
(derived J sorts the scramble 15.0/17.1/23.3, uniform does not), F2 PASS (literature
ordering = burial order, analytic), **F3 FIRED** (τ_sort ratio 0.07, direction
opposite to the prediction — the cortical-floor scale reproduces rung-1's structure,
not its kinetics; rung-1's hand-fit implicitly assumed active fluctuations ~35× the
passive floor — published per Rule 17). Next: Phase 2b — the liquidity anchor
(kT_eff ~ γ·ℓ²), stated when built.

**Phase C — PROGRAMS.** Build order is the controller map's, because the story picks the
buttons: BALANCE (STAND as a state, not a pose) → STEP/PLANT/SHIFT/RECOVER (MOVE) → LAUNCH/
ABSORB (JUMP) → REACH/GRIP/BRACE (GRAB). Each program is a process and its stop condition,
never a final position; each composes only validated primitives; each gets a port_test-style
registration with a falsifier.

**Phase D — PARSER.** The binding table from `docs/CONTROLLER_MAP.md`: ~12 buttons, keyboard
+ mouse primary, one input-agnostic formula layer. Built last of the ladder because it
cannot be wrong in an interesting way.

**Phase E — RUNTIME + the world answers.** `w` from `tools/world.py`; the ground under the
feet from aBlueWorld's membranes; three passive object classes (the living-matter control
set: one grown lattice, one rigid, one granular) placed by the story. The slice session is
recorded, the blind read is taken, F1–F3 are judged.

## EXPLICITLY NOT IN THE SLICE

Vehicles, buildings, NPCs, combat, economy, biomes evolving, the whole universe. The seed
does not need to be finished for the game to be real; the path the player touches needs to
be proven. Addition afterward is legal, free, and the architecture's home turf.

## THE OPERATOR'S RULINGS REMAINING

1. **The kinetic freedom** from THE_LIVING_MATTER (derive temp from physical fluctuation
   energy and publish the disagreement, vs train it against a named objective) — needed at
   Phase 2 of that track, not before.
2. **The term names** for the world objects when Phase E lands (thePlant? theRock? theSoil?
   — the engine's rule: the operator names them).
