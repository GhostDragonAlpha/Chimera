# THE HUMAN FEATURE MENU — everything that can go into this human, researched

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
> **[docs/THE_LAW.md](../docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 26 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

> Built 2026-07-31 for the operator's selection. Scope: THE HUMAN ONLY, with adaptive systems at
> the core. Each item: what it is · how the industry does it (cited) · what we ALREADY have ·
> what it costs. Pick any set; the ones marked [READY] can start immediately.

## A. LOCOMOTION ADAPTIVITY — the moving body

| # | feature | how the best do it | we have | cost |
|---|---|---|---|---|
| A1 | **Velocity-facing body** — the figure turns to face where it *moves*, easing back to camera when still | CoD/Star Citizen default ("free run") | the uncommitted `body_yaw` edit (ready, 20 lines) | [READY] trivial |
| A2 | **Aim-mode strafing** — torso locked to camera, legs do *true* directional gaits (cross-step left/right, backpedal) | CoD aiming stance; For Honor's full-body catalog | state machine already names SIDESTEP_L/R, WALK_B | needs A3 |
| A3 | **Directional gait cycles** — backpedal, cross-step, all 360° directions, from real mocap | Motion matching catalogs carry full 360° sets | CMU MoCap mirror (directional sets fetchable); the trained-policy pipeline (5 rounds deep) | mocap fetch + training |
| A4 | **Turn-in-place** — planted turns with foot shuffle when steering without moving | Ubisoft: "turn-on-spot has foot-shuffling" (gameanim.com) | controller TURN_L/R states | small |
| A5 | **Motion matching** — replace the pose cache with a search over mocap: predicted trajectory vs clip cost (Fréchet) + pose continuity cost, blended | Ubisoft For Honor (2016): "the church of full body animation"; Last of Us 2; "the goal is to be PREDICTABLE, not responsive" | mocap BVH library + GPU | the real animation brain; medium-large |
| A6 | **Slope-adaptive gait** — step height follows slope, torso leans uphill, foot plants conform to the carved ground | Death Stranding's whole game; For Honor's procedural layer: foot IK + torso rotation on slopes | aTerrain's carved height field + gradients already sampled per tick | medium |
| A7 | **Speed-continuous gait** — walk→jog→run as ONE continuum, no state flip | Motion matching's trajectory constraint (speed is a search axis) | analog deflection = speed already | comes with A5 |
| A8 | **Jump/crouch/land animations** — real crouch-launch-tuck-land over the derived ballistics | standard | jump physics proven (apex 0.349 m) | small |
| A9 | **Fatigue & injury adaptation** — tired gait after exertion, limp after falls | RDR2 actor status; Star Citizen's actor-state system | — | needs C1/C3 |

## B. THE BODY'S OWN PHYSICS — the adaptive machine

| # | feature | how the best do it | we have | cost |
|---|---|---|---|---|
| B1 | **Foot IK + ground conform** — soles land ON the carved terrain, never through it | For Honor's procedural foot IK | height_at() per foot position | [READY] small-medium |
| B2 | **Stumble & recover** — shove/slip response on repose-limited slopes | Euphoria-style; RDR2 | theBalance membrane EXISTS in the story tree; repose gates live | medium |
| B3 | **Ragdoll on big falls** | NaturalMotion Euphoria (GTA) | myobody MuJoCo physics is already a full-body sim | medium |
| B4 | **Terrain-reactive movement** — mud/snow/ice friction changes footing | Death Stranding | theGround's friction angle + soil data; biome bands | small-medium |
| B5 | **Load effects** — carrying mass changes posture and gait | Death Stranding (the whole mechanic) | theLoad membrane EXISTS; jump/speed derivations take mass | small |

## C. PHYSIOLOGY — the living body (membranes already grown here)

| # | feature | what it wires | we have | cost |
|---|---|---|---|---|
| C1 | **Breath** — O2 drain on exertion, recovery curves, altitude thinness | theBreath membrane EXISTS (P_loop, consumables) | [READY] small |
| C2 | **Thermal** — sweat/shiver, insulation, wind chill on skin | theSweep membrane EXISTS (T_loop, insulation loops) | [READY] small |
| C3 | **Exertion model** — heart rate, stamina pool driving A9 | simple adaptive model on theBreath's numbers | small |
| C4 | **Suit pressure/oxygen for EVA** — the suit's consumables, warnings | theVerbs/theEVA in the engine hierarchy; suit masses + breathable_unaided=False already derived | medium |

## D. SENSES & PERCEPTION

| # | feature | how the best do it | we have | cost |
|---|---|---|---|---|
| D1 | **Gaze leads body** — eyes/head turn first, torso follows past a threshold | every AAA (gaze-then-step) | look yaw exists | small |
| D2 | **First-person body** — look down and see your own torso/legs/hands | CoD/Star Citizen standard | body_buffer exists (just render in first person too) | [READY] small |
| D3 | **Helmet visor** — condensation, glare, visor up/down | Star Citizen helmet system | visor albedo already derived as its own material | small-medium |
| D4 | **The eye as a membrane** — fovea/periphery, real field-of-view limits | theEye membrane EXISTS in the story tree | medium |

## E. INTERACTION — the hands

| # | feature | how the best do it | we have | cost |
|---|---|---|---|---|
| E1 | **GRAB** — one process, every object: close until you can't, the object parameterises the result | CONTROLLER_MAP.md's own law (pin or bowling ball) | theGrip + theHand membranes EXIST | medium |
| E2 | **Tools** — dig, scanner (theDig, theScan in the engine hierarchy) | Star Citizen multi-tool | theVerbs hierarchy | medium-large |
| E3 | **Vault & climb** — ledge detection + knee drive over it | Assassin's Creed / Star Citizen vault | theAnkle rocker membrane EXISTS; terrain height query | medium |

## F. MATERIAL REALISM — the operator's direct criticism, answered

| # | feature | what it uses | we have | cost |
|---|---|---|---|---|
| F1 | **MEASURED SKIN** — melanin/hemoglobin absorption + subsurface scattering, not flat albedo; and suit/visor materials from the SPLAT-DNA MATERIAL TRAINING SYSTEM (Construction/ pipeline: genome-trained material appearance) | OMLC Jacques optics (ARCHIVED); `Construction/SPLAT_DNA_WORKFLOW.md` + material_appearance trainable | [READY] medium |
| F2 | **Real body geometry** — ANSUR II measured distributions driving proportions (already wired into theHuman), or the SMPL learned skin (operator's license click) | ansur_anchors.json LIVE; SMPL gated | medium / one click |
| F3 | **Muscle-driven visible body** — the 290-muscle myobody (VERIFIED through our splat renderer) as the visible figure, driven by the mocap-trained policies, replacing the pose-cache placeholder | myobody + verify_myo_splat + training rounds 1-6 | the payoff of the current training |
| F4 | **Hands & face detail** | theHand membrane EXISTS; ANSUR hand measures downloaded | medium |

## G. THE TRAINING PIPELINE — how the adaptive human is MADE

| # | feature | why | we have | cost |
|---|---|---|---|---|
| G1 | **Mocap library expansion** — directional sets, slope sets, carry sets, fatigue sets from CMU/other mirrors | A3/A5/A6/A9 need the reference footage | one mirror already cloned (subject 35) | hours |
| G2 | **Direction-conditioned policy** — one brain, all 360° directions (direction as policy input) | round 5's spec worked; extend the observation with the command direction | rounds of GPU (overnight) |
| G3 | **Terrain-adaptive training** — train on aTerrain's carved ground, not flat floor | A6/B4 become real instead of scripted | the walker physics already integrates the carved field | rounds of GPU |
| G4 | **Motion-matching runtime** (A5's engine) — the database, the costs, the blend | Ubisoft's published architecture (cited above) | medium-large, mostly CPU |

---

## The operator's answer needed

Which letters/numbers do we do, and in what order? My honest suggested sequence:
**A1 → F1 → B1 → A3+G2 → A5+G1 → C1+C3 → B2 → the rest by feel.** A1 and B1 are
[READY]; F1 answers your material-system criticism with the pipeline we already own.
