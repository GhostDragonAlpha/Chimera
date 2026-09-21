# PREREGISTRATION — the constraint-ledger pilot (lane agent/constraint-ledger-20260921)

Date: 2026-09-21. Agent: GLM 5.3. Base: master `6ea2702c23c191ff1d3f14bc895ba668f4586dac`
(verified by `git ls-remote` before clone). Branch: `agent/constraint-ledger-20260921`.
This file is written BEFORE any code of the lane. The pre-registered block below is never
edited; amendments append (amendment-1 is appended below, the Astra consultation, received
before the first line of lane code was written — it amends the DESIGN, not the falsifiers'
substance; P2's criterion it sharpens, per its item (6)).

## RULE 0 — STATEMENT

THE THEORY (scoped, falsifiable): development state is an append-only system of CONSTRAINT
RECORDS; an edit adds a record; records compose by conjunction (order-free — this is what
makes parallelism free); conflicts are COMPUTED (records touching disjoint quantity-sets
compose trivially; overlaps produce a named interaction term), never discovered as text
collisions. End state piloted toward: the walk controller's laws as records + a compiler
that turns the record set into executable behavior identical to today's hand-written C++
(`ChimeraEngine/engine/gait_controller.hpp`).

A description survives any result; a theory can lose.

## PREDICTIONS (made before the runs)

- **P1** (the math core): an interference calculator over typed records — independent(X,Y)
  iff W_X ∩ (R_Y ∪ W_Y) = ∅ AND W_Y ∩ (R_X ∪ W_X) = ∅ (asymmetric form, amendment-1; shared
  reads are harmless) — matches hand-derived ground truth on a pre-built suite of ≥10 record
  pairs, including read-write overlap, write-write, shared-read-only (predicted NON-interfering),
  transitive aliasing through a shared quantity, and a parameterized-record expansion overlap.
- **P2** (the compiler proof): the two pilot laws expressed as records — the wave-22 TOUCH BAND
  (`leg_contact`, kTouch=1e-5, genuine departure > kTouch+kReleaseBand=1.1e-5, receipt_wave22.json)
  and the hind-step stand-first hold's arming/release predicate (the touching-class read
  `live_slot: phi>=TOE_OFF ∧ touching`, the floor-anchor capture `hind_step_plant_y_`,
  the release quantum, the wave-31 band-entry completion; receipts wave28b/wave31) — compiled
  and replayed over a lossless recorded trace reproduce the shipped C++ decisions EXACTLY:
  every tick's touch class == shipped `touching_left/right`, every band exit == shipped
  `clear_tick`, every hold arming == shipped `held` — one divergent tick fires the falsifier.
  Amendment-1 sharpens: bit-exact means OUTPUT AND NEXT-STATE BITS on lossless replay
  (float quantities carried as IEEE-754 bit patterns, thresholds probed at nextafter neighbors).
- **P3** (the parallel demonstration): two processes appending record families to ONE shared
  store directory concurrently, then one canonical merge, yield a store byte-identical to the
  sequentially-merged store (order-independence), with zero false conflicts flagged between
  the disjoint families, and the merge preserving declared store invariants
  (invariant-confluence, amendment-1 item 5) — notably one-defining-writer per quantity-version.

## FALSIFIERS (named before the run)

- **P1 falsifier**: any calculator verdict disagreeing with the hand-derived ground truth on
  the sealed suite (>=10 cases) fires. The suite is written and its ground truth fixed BEFORE
  the calculator runs it.
- **P2 falsifier**: one divergent tick (touch class, band exit, hold arming, or next-state
  bits) fires. A harness misalignment (trace convention error) is diagnosed, fixed, and
  REPORTED as such — the falsifier tests the compiled records, and the tick convention is
  part of the registered compiler contract below; a law-relevant divergence is not tuned away.
- **P3 falsifier**: merged ≠ sequential byte-for-byte, or a false cross-family conflict, or a
  violated store invariant after merge — any of the three fires.

## THE PILOT LAWS AND A NAMED DEVIATION

The operator's brief names the second law "the wave-33 STAND-FIRST HOLD". MEASURED FACT:
wave-33 is BANKED, not shipped — `receipt_wave32.json` names the wave-33 bank ("the next law
must bound the CARRIER's standing era by the SWING leg's DESCENT") and no wave-33 record exists
in master. The pilot therefore compiles the SHIPPED law the bank builds on, whose arming
predicate matches the brief's description exactly: the hind-step stand-first hold
(`ChimeraEngine/engine/gait_controller.hpp` lines ~2069-2100):
- arming at a step fire: `live_slot = phi_[hl] >= TOE_OFF && touching_prev_[hl]` — THE
  TOUCHING-CLASS READ — then `hind_step_held_[hl]=true` and the FLOOR-ANCHOR CAPTURE
  `hind_step_plant_y_[hl] = (heel_y + mp_y)/2` at the liftoff spot;
- release (the genuine-departure test): pair-min pads gap > kTouch+kReleaseBand → held=false,
  clear_tick=tick;
- completion (the wave-31 band entry): mode==1 ∧ t+1>=tair ∧ pair-min <= kTouch → replant
  completes, held=false.
Law 1 = the wave-22 touch band (`leg_contact` hysteresis, lines 564-576). The two COMPOSE:
the hold's arming reads the touch record's same-tick write; both read the gap quantities —
the interference calculator must name exactly this interaction term.

## REGISTERED BASELINE / TRACE CONVENTION (the compiler contract P2 tests against)

- Substrate: `ChimeraEngine/engine/gait_controller.hpp` @ `6ea2702c...`, READ-ONLY (never edited).
- Scene: regenerated by `python tools/science_funnel/gait_scene.py --output .tmp/gait-walker`
  (a DIRECTORY; scene.json sha256 recorded at run time in the lane receipt).
- Trace: a NEW harness `tools/constraint_ledger/trace_harness.cpp` includes the UNCHANGED
  header, runs the same walk (config `{"capture_enabled":true,"reset":true}`, horizon
  10*CYCLE_TICKS, stop at refusal) and dumps per-tick census row i = status after step i
  (0-based): the 4 hind pad gaps + their IEEE bits, phases, the shipped decisions
  (touching_left/right, held, clear_tick, fire counts, mode, t, alt_due, fire_class, plant_y),
  the hind pads' world x/y. Tick convention: decisions recorded at row i are functions of the
  quantity series through row i-1 (the tick-start evaluation is the end-of-step-i-1 state)
  plus same-tick ordered dependencies (touch law at tick start; hold at the decision phase —
  the dependency the record set itself declares). The compiled replay is seeded ONLY from
  declared initial state (touching=false,false; held=false; clear_tick=-1; anchor bits 0) and
  NEVER resets its memory from the reference mid-run.
- Lossless: float quantities carry both shortest-round-trip decimal and uint64 bit patterns;
  the replay asserts decimal↔bits agreement before comparing anything.
- External inputs of the fragment (declared): gaps, phases, fire events (from the shipped
  scheduler's counter), mode, t, alt_due, pad world positions. The scheduler itself is NOT a
  pilot record — named successor work (full-controller migration, L0/L9 of the Astra program).
- Boundary fixtures (amendment-1 item 6): each threshold probed at the value and its
  nextafter neighbors in BOTH directions: kTouch=1e-5, kTouch+kReleaseBand=1.1e-5; plus the
  initialization/reset cases and both Boolean state combinations of the hysteresis latch.

## GATES (the lane's own, run before the report)

creature_graph suite 69 OK with BOTH PYTHONPATH roots; matter_kernel test_definition 9/9;
training_gate PASS; P1/P2/P3 suites green. No existing engine/validation file is modified;
new code lives under `tools/constraint_ledger/`.

## AMENDMENT-1 (the Astra consultation, received before the first line of lane code)

Citation: operator-forwarded consultant corrections (Astra round 2), 2026-09-21, spec
`chimera-pilot-registration-specification.md` (read-only, outside the repo). Applied to the
P1 schema and P2 representation BEFORE finalization:

1. RECORD KINDS: every record carries `kind` ∈ {invariant, definition, contribution,
   alternative, measurement, proof}. Requirements/invariants conjoin
   (Models(R∪{c}) = Models(R)∩Models(c)); definitions compose as STAGED updates (never
   simultaneous equations over one output); alternatives stay in the store and are selected
   by an explicit snapshot manifest.
2. QUANTITIES: declarations carry entity, coordinate frame, unit, numeric type, tick/substep,
   state version; reads/writes are DERIVED from the typed expression and CHECKED against the
   declarations.
3. INTERFERENCE: the asymmetric test above; overlap = POTENTIAL conflict, discharged by a
   witness search (∃s: Obs(F_X(F_Y(s))) ≠ Obs(F_Y(F_X(s)))) — fixture-based here (no SMT in
   the pilot toolchain; SMT is successor L4); transitive propagation registers physics edges
   (law → force → body state → contact guard → load-share sensor → later law) alongside
   controller-expression edges; unknown externals reach everything conservatively.
4. EXECUTABLE FRAGMENT RULES: acyclic within a tick over same-tick edges; explicit delayed
   state (`prev:`); ONE defining writer per quantity-version; reject ambiguous writers,
   instantaneous cycles, unspecified initial state, underdetermined outputs.
5. P3 acceptance = INVARIANT-CONFLUENCE (independently-valid extensions merge preserving
   declared invariants; satisfiability is not preserved by union), not Knaster-Tarski.
6. P2 bit-exactness as stated above (output AND next-state bits; nextafter fixtures).

The ten-lane program (L0-L9, F-BASELINE-BYTES … F-CLOSED-LOOP-BYTES) is the successor
structure; this pilot proves its L1/L2/L3/L5/L9 core on real substrate.
