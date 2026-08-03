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
passive floor — published per Rule 17). **Phase 2b DONE (2026-08-03): F1/F2/F3 ALL
PASS** — the liquidity anchor (kT_eff = σ̄·ℓ², σ̄ = 7.66 mN/m the geometric mean of
the four Foty tensions) closes the theory with ZERO fitted numbers: derived J sorts
(12.8/21.2/26.8, uniform does not), τ_sort ratio 0.60 inside [0.5, 2], and rung-1's
hand-fit turns out to have sat at 1.5× the derived anchor all along. Open debts
recorded: interfacial pairs are Girifalco-Good defaults, λ underived (own membrane),
type mapping tested on ordering only. **Phase 4 first control DONE (2026-08-03):**
sand/rock/medium sorts with rock burial under the derived world J (γ_sand = c·d =
36 mN/m from library cohesion×grain, γ_rock = K_IC²/2E = 36.9 J/m² from measured
basalt toughness), PASS across 3 runs with the uniform control's orientation random
(rock/tie/sand) — the machine does not manufacture the ordering. **Phase 3 DONE
(2026-08-03): fracture is in the shaker** (`_rupture_pass` in `Chimera/core/matter_gpu.py`,
 Griffith from K_IC, zero fitted numbers) — three clauses, each earned by a fired
falsifier: fracture needs a measured K_IC (sand never fractures), rupture needs
void-connectivity (cracks advance from surfaces), plucking is erosion not fracture
(13 sand deaths, 0.16%, mechanism named). Stable: burial persists, ruptures decay
7,293 → 5, zero bulk violations. Measured en route: λ/temp is load-bearing for
life-and-death — λ's derivation is now the sharpest open debt. **Phase 5 DONE
(2026-08-03): the λ membrane ran — mapping DEAD as predicted.** Derived per-tissue
λ (395 soft / 2,375 bone, from measured bulk moduli) freezes the lattice: no sort,
counts frozen ±0.3%, H rises as λD² dominates — the per-type area term is mass
conservation, NOT bulk elasticity. Published: rung-1's 0.9 = K_eff 5.3 MPa (the
shaker is foam-like, measured); tissue-real incompressibility needs deficit-paired
swaps (named, unbuilt). The kernel now takes per-tissue λ arrays; default scalar
path unchanged, both instrument tests pass. **Phase 4 full families DONE
(2026-08-03): FIRED — the interesting way.** All five world materials derived into
one 6×6 J (metal 6,094 ≫ rock 36.92 > ice 0.735 > sand 0.036 > basin 0.0056 J/m² —
every number measured or Griffith-derived, σ_geo = 2.016 J/m², no new freedom).
Metal did not freeze as the pre-run quench caveat predicted — it EVAPORATED: a
single-grain dispersion of a γ/σ_geo ≈ 3,000 material is below any critical
nucleus, so annihilation (ΔH ≈ −326,000/site) beats aggregation. The survivors
ordered perfectly (rock 14.5 < ice 15.7 < sand 30.2; uniform control random),
sand/basin inversion recorded as the pre-named Girifalco-Good precision limit.
Instrument paid en route: `metrics_3d` now takes `types` (metal's id 4 collided
with TENDON). **Phase 4 nucleation DONE (2026-08-03): FIRED — question closed.**
Seeded metal (two r=12 compact seeds, 14,246 cells) evaporated exactly as the
dispersion did — and the post-mortem derivation is the law: the machine runs
18-connectivity (the membrane wrongly derived 6), so a flat face erodes iff
13×(J_ab−J_aa) < 5×(J_ab−J_bb) — always true for extreme-γ metal. Survival
belongs to the λ jail, not the face: a type lives iff its erosion drive <
2λ×population. Metal's drive (37,676) exceeds any jail its population can raise
(25,642) at any seed size this lattice holds — metal has no stable finite phase
in the shaker; rock's 4% bleed is the same condition, solvent. Three runs, one
equation, zero fitted numbers. Named routes for metal: per-type λ ≥ 1.4, or a
frozen_type skeleton (structure not tissue) — both new membranes, operator's
call. Next: tissue K_IC, or the operator's pick.

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

**Phase E, rung 1 — the loop BOOTS AND PLAYS (measured 2026-08-03, smoke run):**
`python ChimeraEngine/gallery.py 8791` → `http://127.0.0.1:8791/live` — the playable loop
is already real and every seam answered: /stand returned the membrane readout (g 7.08,
walk 0.99, run 1.8 m/s — Froude), /walk?fwd=1 for 6 s moved the body y 0.0 → 6.0 m (the
derived walk speed, exact), the MJPEG stream carries live frames, and the third-person
frame shows theHuman's own suited figure standing on the carved terrain under the
Rayleigh sky (`ChimeraEngine/output/slice_smoke_third.jpg`). Keyboard WASD + mouse-look
bind in the page (browser keydown/keyup → /walk). One trap measured en route: the render
thread idles with zero clients, so HTTP-driven walks only integrate while a client holds
/stream — the browser never hits this, a curl script always does. **The gap to the slice
as stated: nothing to TOUCH yet — the three passive classes and GRAB (E) are unbuilt;
the recorded session and blind read (F1–F3) have never been taken.**

**Phase E, rung 2 — TOUCH (membrane stated 2026-08-03, before the build).**

**STATEMENT.** Three passive classes suffice to make the world tangible: a RIGID
stone (contact impulse + Coulomb friction), a GROWN tuft (damped spring — the
passive-tissue port, grass-sized), a GRANULAR pile (kicked grains, repose-limited
settle). Each is driven by the player's commanded velocity at contact — the process
principle: the object decides where it ends up, the touch only hands it energy.
Every number traces to theGround's numbers.json (stone size from the fractal
distribution, friction from the repose angle, pile repose from regolith) or a cited
measurement (rock density; stem stiffness). Placement near spawn is level design —
THE HUMAN's placeholder, the operator's to move.

**PREDICTION.** Walking into each class produces its own signature, measurable in a
headless test: (1) the stone's post-contact speed scales with m_body/m_stone and it
stops within the μ-derived braking distance; (2) the tuft deflects away from the
player and recovers to rest in < 2 s, never diverging; (3) the pile keeps a
permanent footprint and every kicked grain settles (max grain speed < 1 cm/s at
3 s after contact). GRAB (E) picks the stone up inside arm's reach and drops it at
the feet — carried mass is reported by the HUD.

**FALSIFIER.** Any class violating its own equation (stone brakes long or never
stops; tuft oscillates unbounded or never returns; a grain still moving after
settle time), OR any constant in the objects' code tracing to neither a
numbers.json nor a named citation (F1 applied to the new file: a provenance table
in its header, each row PHYSICS or THE HUMAN).

*VERDICT (2026-08-03: headless `python tools/touch_tests.py` — 19/19 PASS, then the
live loop over HTTP).* **PASS — the world answers, and every number has a home.**

- **Stone (rigid):** impulse measured 1.4516 × v_cmd = m_body/m_stone exactly
  (65.1 kg of basalt, Quaglio 2020); stops after 0.140 m against the μ-derived
  0.151 m (μ = tan 40.03° = 0.84, theGround's repose); same law from another side
  at another speed; player never blocked.
- **Tuft (grown):** bends 52.1° away from the player (alignment 1.000), recovers
  to < 2° within 2 s, never diverges. Stiffness derived from a measured grass:
  Kosmalla et al. 2025 (Earth Surface Dynamics 13, 791) — marram grass E
  1050–1910 MPa, geometric mean 1416 MPa, blade Ø 1.6 mm, cantilever scaling →
  k 45.3 s⁻² (ω_n 6.73 rad/s).
- **Pile (granular):** a walk-through kicks 395 of 400 grains (cone height =
  base × tan(40.03°), derived); the footprint is permanent; all grains settled
  (< 1 cm/s) at 3 s.
- **GRAB (E):** reach = 0.44 × stature (ANSUR) = 0.772 m; pick-up → carried at the
  body's derived CoM height → walked 5.5 m → dropped 0.30 m from the feet; the HUD
  names the carried mass. Verified live over HTTP: walk to it, "E: pick up the
  stone (65.1 kg)" → carried → walked → "E: put down the stone" → dropped, the
  affordance flipping on the real server.
- **F1:** the provenance table is in `ChimeraEngine/touchables.py`'s header —
  every constant PHYSICS (numbers.json or citation) or THE HUMAN (design rows:
  spawn spots, blade count, kick factors), no hidden literals.
- `python tools/walk_demo.py` still PASS (no regression).

**Phase E, rung 3 — THE RECORDED SESSION AND THE BLIND READ (2026-08-03).**

A scripted play session was recorded over the live server (9 frames + drive log,
`ChimeraEngine/output/slice_session_20260803/`): stand → walk (0.99 m/s exact) →
to the stone → through the pile (footprint 1.08 m, HUD-proven) → jump → first
person. The blind read — a fresh vision agent given the frames with zero context,
the dyad's advisory instrument — captioned the set: *"a primitive white mannequin
stands, and possibly walks and carries things, in a nearly empty dark 3D landscape
of green hills and blue sky — with the actions mostly implied by faint pale
patches on the ground rather than anything clearly depicted."*

**F1 — PASS.** Everything on the HUD traces: g/walk/run from theHuman, sun/season/
daylight from the planet's own laws, the touch line's mass/μ/grain/repose numbers
from theGround + citations, and `touchables.py`'s provenance table has no hidden
literal. (`python -m core.why` walk remains to be run as the formal check.)

**F2 — FIRED, and the causes are measured, not argued:**
1. **The instrument was STILLS; the charter's instrument is a MOVIE.** Gait is
   temporal — no still can show "walking". The session recorder captured JPEGs;
   the dyad's own protocol (render → movie → blind read) was not used.
2. **The carry never happened in this recording.** The scripted drive overshot
   the stone (HTTP steering without position feedback), so beats 4–6 show a body
   near a stone, not carrying it. The blind read honestly reported nothing
   carried. Recorder fault, recorded.
3. **Legibility is the real physics gap the read measured:** the scene is dim
   (tone 0.45 at sun_alt 52.5° reads as twilight), the 0.35 m stone and the
   0.84 m pile are faint patches at 3.2 m camera distance, the tuft was never in
   frame. Objects sized for touching are not sized for SEEING. Per F2's own rule
   the fix is the presentation physics — exposure, object scale, and reading
   video — never the tolerance.

**F3 — JUDGED 2026-08-04: PASS by the slice's letter; one named debt carried forward.**
Harness: `python tools/f3_stand.py` (exit 0 PASS; verdict picture
`ChimeraEngine/output/ports/f3_stand.png`). The musculoskeletal body (290 muscles,
`myobody.xml`) stands on this world's gravity (g = 7.076, read by `tools/world.py` from
theHuman — never assumed) **through a parser** (`BUTTONS = {"stand": formula}` — a button
toggles the derived formula `a0 + kh·(tgt−z) + kp·pitch`; the full Phase D grammar comes
later, and the path button → formula → muscles is what F3 tests) with **zero pose-scripted
frames**: after a one-time projection of the keyframe into the body's own declared joint
ranges at reset, nothing writes `d.qpos` — every frame is `mj_step` under muscle control
and gravity. Measured over the run: Phase 1 (STAND held 5.0 s) pelvis MIN **93.0%** of the
derived 0.9201 m target (bar 90%), CoM excursion **0.84×** the base-of-support box (bar
1.00); Phase 2 (STAND released) the body slumps below 50% of target in **0.9 s** — the
button is load-bearing, not a replayed checkpoint. The stand policy itself was re-derived
this session: CEM warm-started twice (`--init`, added to `tools/train_stand.py`), 24
turns × pop 48 at the full 5 s horizon.

**The named debt (the port's full contract, honestly failed):** `stand_port.py`'s printed
PROVEN line adds "joints off their limits", and the policy arches the lumbar past its
declared stop — worst joint **1.56×** range transient, **1.14–1.34× sustained at
L4_L5_FE** (≈ 3–5° past a soft stop), with knees/subtalar grazing at 1.01–1.03×. The cause
is named, not theorised: `tools/world.py`'s passive-tissue derivation covers hip/knee/
ankle and *refuses* the trunk — "left alone 13 (out of range, no ligament)" — because
theHuman publishes no lumbar motion envelope to derive a slack band from. **Next rung,
fixed by this firing:** the TRUNK PASSIVE-TISSUE port (lumbar ligaments), which needs
published lumbar passive moment-angle data; a chosen stiffness would be rule 1. This was
F3's predecessor paragraph ("exists as a separate artifact… not driven through the slice
parser") resolved: the artifact now stands through the parser.

**Next rung, fixed by this firing:** re-record with position-closed-loop drive,
capture VIDEO for the blind read, fix exposure and object legibility, then read
again. The bar does not move.

**Phase E, rung 4 — THE RE-READ (2026-08-03).** The three rung-3 causes, fixed and
measured:

1. **Exposure was presentation, not physics** (S_earth = 1.005 — the planet is
   Earth-bright; the frame was the lens). `_EXPOSURE = 2.0` in `walker.py` — the
   camera's two-stop compensation, the ONE human dial, same legal status as
   `lit()`'s tone; ground, body, skin-wrap and touchables all sit in the same
   photograph.
2. **The real F2 cause, measured en route:** the ground's lattice-closing
   0.95 m splats form a picket fence ~0.47 m tall — a chest-height camera cannot
   see ANY ground object past ~1 m over it (probe: stone, pile, tuft all
   invisible from chest height, all visible from above). Rung-3's "faint
   patches" were occlusion, not size. The recorder looks down (+0.55 pitch).
3. **Legibility:** the stone is now honest quartzite end-to-end — the
   quartz-look/basalt-mass mismatch was an F1 lie and is fixed (albedo from
   theGround's quartz, ρ 2,650 kg/m³ Schön 2011, 59.5 kg; probe and tests tell
   the same rock). Pile clods 6 cm; tuft brightened (it had zero contrast at
   palette parity).
4. **The recorder is closed-loop** (`tools/slice_record.py`): a goto() servo on
   the walker's own readout, pick-up closed on the OUTCOME (stone.carried), 121
   frames + per-beat contact sheets. The carry is on tape this time.

The blind read of the contact sheets (fresh vision agent, zero context):
*"A white humanoid character walks continuously across a flat green terrain —
legs alternating in a continuous walk cycle — while pale matter appears at its
hands and feet: something carried near the right hand, a mound approached and
passed, a splash at the feet that fades behind it."* Against rung-3's "mannequin
stands, possibly walks, in an empty dark landscape": **walking is now read
unambiguously, and the three touches read as interactions** (carry, mound,
footprint). What is NOT read yet: the carried matter does not read as a STONE
(it reads as a speckled cluster), and "living world" is not named — the terrain
is still a flat green plane with ambiguous dark streaks.

**F2 status: converging, not converged — the final call is THE HUMAN's** (the
dyad's rule: the operator is the authoritative ear; the agent read is the
advisory second opinion). The named remaining gap is fidelity of matter, not
physics: the stone needs a denser sphere to read as rock; the world needs the
vegetation its albedo already claims. Both are addition, not redesign.

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
