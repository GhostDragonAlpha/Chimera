# THE GAME — the product constitution of Chimera

Status: operator-ratified 2026-09-12. This file is the destination every
lane serves. It changes only by operator direction, recorded in amendments
(append-only). The physics spine (docs/THE_LAW.md lineage) is the engine
room; THIS file is the ship we are building with it.

## The vision (operator, verbatim intent)

A membrane-based reality simulator with **Minecraft's accessibility and
scope, Star Citizen's feature depth, Space Engineers' material detail** —
spanning **cosmic level down to molecular structure level**. Every
material's outer membrane — the triangle surface of the render+physics
combo system — carries real physical properties. People play it online
with their friends, and because the physics cannot lie, they LEARN from it
by seeing it.

**The one-sentence pitch:** a creature that cannot lie about its own body,
in a world built the same way.

## The universal primitive: membranes all the way down

One membrane encompasses the thigh bone; one encompasses the shin bone; a
third encompasses the joint that connects them. Compose membranes and you
compose the world — bone, joint, water, cloth, terrain, planet. This is
not a new architecture: the engine's rig, water plane, and strain overlays
already ARE membranes. The game is this pattern scaled from bone to world.

## The operating doctrine (each law earned in the field)

1. **One feature at a time.** Serialized, never parallel feature lanes.
   The inventory advances one line at a time; everything else queues.
2. **A feature is a visually provable concept.** It does not exist until a
   blind dyad judge can SEE it — pictures, on the operator's desktop
   (CHIMERA_PROOF), or it did not happen.
3. **Pass = frozen.** When a feature passes the human and the dyad, it is
   DONE — untouched until a later polish pass. No gold-plating, no
   revisiting.
4. **Proofs wait for visuals.** Mathematical verification of a mechanism
   comes only after the visual/simulation evidence says the mechanism is
   worth keeping. Do not invest formal proof in what the eye may reject.
5. **The kitchen rule.** The C++ engine is a frozen service consumed over
   its HTTP contract; all product work is Python. When a feature needs a
   capability the contract lacks, the lead may add exactly one engine
   route as a NAMED, recorded exception (precedent: root-translation,
   2026-09-12). Appliances one at a time, each announced, never hidden.
6. **All invisible elements shall be seen when put in motion** — and
   rendered invisible again once proven (user-toggleable; in the teaching
   game, making the invisible visible IS the lesson).
7. **The dyad owns the parts; the human owns the hands.** The dyad
   verifies every knee, membrane, and material. The operator tests input,
   controls, and feel — the moment there is something to control.
8. **Division of evidence:** operator observations are reports of the
   present; databases are claims about the past. When they conflict,
   check the operator's window first. Liveness is proven by file writes,
   never by status flags.

## Chimera language (the operator communication protocol)

Named by the operator, 2026-09-12. Rules: simple relatable metaphors for
structure (bold the metaphors); **percentile chances** for every forecast
and fork (the operator extrapolates all data points simultaneously as a
pattern recognizer); direct policy questions with the lead's
recommendation attached; one-word veto or blessing; silence = the
recommendation stands. Metaphors in use: the **kitchen** (engine) and its
**appliances** (routes); the **muppet that tells the truth** (visual life
over numeric honesty — both, but looks-first); **taxi vs bus** (spend
rate); **parts vs hands** (dyad vs human testing).

## The feature inventory (the build order)

TIER 0 — THE BODY [FROZEN, PROVEN]
1. Creature renders, 28-joint rig · 2. Truthful HUD (readouts track
motion) · 3. Multi-joint choreography · 4. Whole-body camera fit ·
5. HTTP viewer (live view, byte-identical snapshots, movies, fit preset)

TIER 1 — LOCOMOTION [CURRENT]
6. Walks and travels (root-translation exception + travels lane) ·
7. Feet plant, no slide · 8. Arms counter-swing + torso bob (composed and
RENDERED — the commanded-vs-rendered gap is a known open defect)

TIER 2 — FLUIDS: 9. Water as a body (pool, not stain) · 10. Downhill
flow · 11. Buoyancy (first teaching moment)

TIER 3 — MATERIALS (the membrane heart): 12. Squash/spring · 13. Cloth
bend · 14. Fracture (the Minecraft verb) · 15. Freeze (frost plane
exists) · 16. Melt · 17. Burn

TIER 4 — HANDS: 18. Grab · 19. Carry · 20. Throw · 21. Place/build
(Space Engineers verb)

TIER 5 — WORLD: 22. Terrain chunks · 23. Variable gravity (the cosmic
end) · 24. Wind · 25. Day/night + light

TIER 6 — MOLECULAR END: 26. Heat spreads visibly · 27. Vibration/sound ·
28. State changes (ice→water→steam)

TIER 7 — FRIENDS: 29. Multiplayer — the engine is already a server; the
HTTP contract IS the client-server architecture.

TIER 8 — CONTROLS (the operator's test bench): 30. Keyboard→motion ·
31. Mouse→camera · 32. Click→interact · 33. Gamepad — all Python-side
through the viewer, arriving as parts freeze.

Cadence (measured 2026-09-12): ~1 visible feature per day at one-at-a-time
bus mode, dyad first-pass rate 7-of-8 (PRs #97-#109); full inventory ≈ 4-5 weeks.

## The commitment

Operator, 2026-09-12: "I am not going to stop until I'm dead or it's
created. My autistic mind will not let this one go ever."
The fleet's answer: one membrane at a time, every one visible, every one
true.

## Amendments (append-only)

### Amendment 1 (2026-09-12) — the aligned operating system

Recorded from the operator's direct instruction; canonical text:
[THE_ALIGNMENT.md](THE_ALIGNMENT.md). Laws sharpened this session:
(a) the dyad receives ONLY the scenario and the goal — never what to look
for; its unprompted generalized report is the decision instrument, and
feedback translates into feedback until the bones of truth stand exposed;
(b) the human is the override — pass = dyad approves AND the operator
agrees; operator observations arrive on the same channel at higher priority
and supersede all; (c) rendering-engine (C++) changes are made in STRICT
SERIES, never in parallel — the standing work is Python correctness over the
frozen engine; (d) the multi-agent fleet is retired and its liveness
reporting may not return — the only truth is a dyad report describing an
image actually rendered by the engine; (e) the near plan (tempo → footstep
equation → unfold joints → train the in-between → material inventory) lives
in THE_ALIGNMENT.md §5; (f) the project is programmable matter: the outside
membrane programmed with the mathematical characteristics of the material it
simulates, all math figured out on the triangles.

— Agent: glm53-lead-02


### Amendment 2 (2026-09-20) — the operator's three laws, constitution-grade

Recorded from the operator's direct instruction, banked verbatim in
tools/creature_graph/validation/reality_gate_20260920/receipt.json (lane
agent/reality-fantasy-gate-20260920). The World, Movement, and Aliveness laws
(docs/THE_SHIP_GOAL.md) govern the SHIP; these three govern the BODY — every
creature, every anatomy dataset, every render of one. The vision already says
every membrane is a triangle surface; this amendment makes the doctrine
BINDING and falsifiable instead of descriptive. Same shape as every law in
the house: a statement someone could disagree with, a named falsifier, an
enforcement point that measures.

#### THE BIOLOGICAL LAW (operator directive, 2026-09-20: "no life-stage mixing
#### — a baby macaque is the way it is for biological reasons (clinging to
#### mother); life differs by stage; rules for mixing data follow BIOLOGICAL
#### rules as well as physics")

One creature, one life stage. Allometric coherence per stage: segment
proportions must match the stage's OWN scaling laws. A baby macaque's
proportions are adaptive, not defective — clinging to the mother, a large
head ratio, a flexed posture; that is biology, not noise to be corrected
toward the adult. Stage labels are ADMISSION-REQUIRED for anatomy data: an
adult dataset must be adult-CONFIRMED from collection records, like sha256 —
the label is provenance, never presumption — and unlabeled is unadmitted.
A stage-true baby creature is VALID: baby and adult coexist; neither mixes.

THE FALSIFIER THAT KEEPS IT HONEST: a stage-mixed body cannot hide, and a
stage-true one is not falsely flagged. The adjudication of record: the chimera
bundle (an adult forelimb grafted onto the infant skeleton) classified FANTASY
— stage-mixed, adult-unconfirmed, humerus:femur +259.0%, forearm:tibia
+249.7% — while the within-forelimb ratios stayed stage-true and were NOT
flagged, exactly as predicted (the negative control that proves the check
measures the law, not the creature).

ENFORCEMENT: the reality gate's stage_consistency + allometric_coherence
checks — tools/creature_graph/reality_gate.py (branch
agent/reality-fantasy-gate-20260920). Allometry expectations are DERIVED from
pinned measured files, never duplicated: adult = the walker's Table-1
(Oku/Ogihara 2021, the model the physics already uses); infant = the two real
infant CT specimens' banked bone identification with leave-one-out exclusions
(a replication test, not circularity); tolerance = the house 15% band.

#### THE TWO-CATEGORY LAW (operator directive, 2026-09-20: "two categories —
#### REALITY (follows the laws) and FANTASY (chimeras, developer-driven
#### explicit construction, never accidental data mixing). REALITY FIRST:
#### reality is the reference; everything else is fantasy BY DEFAULT (measured
#### deviation)")

There are exactly two categories of creature. REALITY follows the laws — it
is the default and the reference, the thing physics vouches for. FANTASY is
chimera-making: developer-driven EXPLICIT construction with an acknowledged
violation manifest; it is never accidental data mixing. Violations are never
silent. If the user wants a half-adult half-baby macaque with machine guns,
that is the user's right — but the user must UNDERSTAND it violates the laws
of nature. Reality is not the opposite of fantasy; it is the measuring stick
fantasy is measured against.

THE FALSIFIER THAT KEEPS IT HONEST: a silent violation, or a misclassification.
Four adjudications were preregistered BEFORE the run and all four HIT: the
infant CT specimen (USNM 497136-3) → REALITY, 0 violations (the first reality
creature); the H2 per-bone mount → FANTASY (stage-mixed + 7 per-bone scale
incoherences vs the trunk-anchored 3.2315, +17.4% to +173.0%, cross-species
fuscata/mulatta distance 2); the walker → REALITY with the physics bars
passing on measured closures (per-drive work-sum closure 0.0%, GRF impulse
closure −0.004%); the chimera → FANTASY. An unacknowledged fantasy is
itself a violation (fantasy-unacknowledged): the manifest must be
acknowledged, never assumed.

ENFORCEMENT: the gate CLASSIFIES, not just refuses — the output is
{category: reality|fantasy, violations: [...]}, every violation itemized with
its measured numbers (tools/creature_graph/reality_gate.py::adjudicate).
Fantasy construction requires acknowledging the manifest — the operator's
bio.fantasy_acknowledge command, whose measured form today is the bundle's
fantasy_manifest_acknowledged field plus the itemized fantasy-unacknowledged
violation it prevents (branch agent/reality-fantasy-gate-20260920).

#### THE TRIANGLE DOCTRINE (operator directive, 2026-09-20: mesh-with-triangles
#### is the data currency; anatomy layers are membrane outlines — bones,
#### muscles, skin — defined by triangles in the matter construction system;
#### never splatified for rendering)

Mesh-with-triangles is the data currency. Every anatomical layer is a membrane
outline defined by triangles in the matter construction system — bones
(compartments) now, muscles next, skin eventually — and the same triangles
carry the physics and the render. Creature data is NEVER splatified for
rendering: a splat cloud is the canonical violation, measured and named (the
monkey rendered as a splat cloud was the divergence that cost a lane and
produced the workflow checklist).

THE FALSIFIER THAT KEEPS IT HONEST: the render path cannot lie about what it
composed. The conformance gate drives the REAL compose + render path against a
recorder and inspects the wire: the scene must post mesh geometry through
/mesh_bin and must NEVER post the skeleton as a splat buffer (/membrane_bin).
Pixel truth makes the presentation measurable without eyeballs or a vision
model: a splat cloud is GRAINY (intersplat texture) and leaves silhouette
holes (coverage < 1); a shaded mesh tends to the smooth-shading floor and
fills its own silhouette (coverage ~ 1).

ENFORCEMENT: the Defect A conformance gate
(tools/science_funnel/tests/test_ct_skeleton_triangle.py) + the deterministic
pixel checks (tools/science_funnel/pixel_truth.py: grain, coverage,
object_seen, guide_seen, clip_scan), receipt triangle_monkey_20260920 (branch
agent/triangle-monkey-grid-20260920; the splat-divergence origin recorded in
docs/THE_CHECKLIST.md, branch agent/workflow-checklist-20260920).

— Agent: GLM 5.3
