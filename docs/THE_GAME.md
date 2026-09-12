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
