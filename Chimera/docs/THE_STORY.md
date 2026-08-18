# THE STORY — the teddy bear, the seed (the outermost membrane)

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
> **[docs/THE_LAW.md](../../docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 26 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

> **SECURED 2026-08-17** — the story is now the **teddy bear**: a third-person game character trained like a
> robot, run on cellular-automaton rules. This is not a game-narrative (the old solar-system timeline is
> archived below); it is the **membrane decomposition** of one controllable creature. The decomposition
> names the MEMBRANES and how they interact — *what the bear looks like is trained, not written* (TRELLIS:
> image → 3D → voxel base representation), *how it moves is rule, not keyframe* (cellular automaton: a
> muscle is a column that shortens; motion is cells added and removed), and *how it decides is a learned
> policy, not a script* (retinal senses → Q-learning → a chosen step). Read the construction method before
> touching any term: [`ChimeraEngine/docs/HOW_TO_MAKE_A_THING.md`](../../ChimeraEngine/docs/HOW_TO_MAKE_A_THING.md).
> **Change the story here, re-run `python ChimeraEngine/gen_decl.py`, and the whole game re-derives.**

---

## The one idea

**A creature is grown, not sculpted.** The teddy bear is not a model dragged into the world; it is a
lattice of cells grown from one number — the genome — given a base shape by TRELLIS, moved by
cellular-automaton rules, and judged by an eye. The engine has exactly two poles:

- **The Barnes-Hut tree** talks across distance — every additive point-source field (gravity, light,
  heat, acoustics) is one tree traversal.
- **The cellular automaton** decides what to BE — structure is a cell set grown by rules, and motion
  is cells added and removed (a muscle is a column that shortens; a joint is voxels removed around an
  axis of incidence).

**A splat IS a cell.** Rendering is Gaussian splats bound to sim cells. If you are drawing circles,
you have left the engine.

## The membranes (the terms)

The decomposition below is the membranes, in construction order. Each is a theory: it is proven when
its falsifier is measured — a NUMBER at the PHYSICS terminal, a JUDGMENT at THE HUMAN terminal. The
appearance of the bear is NOT a term — it is trained (TRELLIS) and only ever *verified* by the eye.

### theSeed — the genome

In the beginning is a number. One genome — a table of key=value DATA — plus the TRELLIS base
representation, grows the whole lattice, deterministically: the same genome grows the same cells,
bit-identical, forever. The genome is data; the core is the reader. You never touch C++ to change the
creature. Its only law is `theDeterminism`: same seed → same cells.

### theShape — the voxel lattice body

The body is a cell set (occupancy + rig chains) carried as DATA. TRELLIS gives the base
representation; the CA owns it from that moment on. Before it can move it must STAND — its center of
mass must project inside the paw support hull with **margin ≥ 1 cell** (one lattice step of
discretization slack). A doll that tips is not a body; it is a bad statue, and the physics that
animates it is faithfully animating a bad statue. `theBalance` is the gate that separates the two.

### theMuscle — the column that shortens

A muscle is a column that shortens. On the CA lattice, movement is cells added and removed — the
lattice itself shortens and lengthens. This is the ONLY way the bear moves. There is no keyframe, no
pose blend, no rig drive: a step is *lift* (remove paw cells) → *swing* (re-place them) → *plant* →
*shift* (advance the body and repay the planted paws).

### theRig — the chains the muscle rides on

The rig is the set of chains (hip → paw) that the muscle shortens along. It is DERIVED from the
shape, never the reverse. A chain that does not reach the ground is not a leg; the gait stalls with
zero errors and zero motion.

### theGait — the beat machine

The walk is a cyclic beat machine: LIFT, SWING, PLANT, SHIFT. It is verified **one joint at a time,
against the eye**: does the left knee bend like a knee? does the paw plant where it should? does the
hip lift without the torso falling? Every movement is proven by asking the judge model *that specific
question* against a rendered frame. `theStand` (rest equilibrium: paws planted, zero drift, no
airwalk) must hold before `theWalk` exists. **The stride is trained only after every movement is
verified** — never train movement on an unverified body.

### theScan — sense: the retinal senses

The bear reads its world the way a sim-trained robot reads a gym: a **retina** — a small set of
discretized sensor readings (ground underfoot, goal bearing, what is in reach) — sampled from the
lattice every tick. A sense is an integer, never a float story: the bear knows "ground ahead at
distance 3", not "the ground is 2.94 cells away". Senses are the ONLY input to the decision layer.

### theChoose — plan: the learned policy

Given the scan and a goal, the bear picks a step. The choice is a learned policy — **Q-learning over
rest / wave / walk** — trained in the environment, not scripted. The learner's ledger (Q-values,
visits, sense counts) is the proof: a bear that stalls (Case B) is a documented deficiency, never a
patched one. Sense → plan → act is the whole loop; the plan is the middle term.

### theControl — third-person control

The operator steers the bear (third-person), or hands over to its own policy. Direction is a COMMAND,
not a genome fact — reversing the beat machine is a sign flip, not a redesign (walk west must be the
bit-exact mirror of walk east). Control and autonomy are the same verbs; only who holds the dial
changes.

### theWorld — the training environment (the gym)

The bear stands in an environment, not a void: terrain, contact, gravity, and a goal placed in it.
This is the sim — the gym a robot is trained in before it ever ships. The world is the seed's world
(a 1D profile extruded along z today; the 2D terrain field is the known next membrane). The ground
holds the bear by contact, and the bear answers its world.

### theAppearance — the splat surface

The bear is rendered as Gaussian splats bound to its cells — anisotropic, EWA-projected, a continuous
surface with no through-holes, legible at canonical framing. The outer skin must transform smoothly
with the lattice; to make that verifiable, **SPL markers** (splat/surface-point markers) ride the
lattice so a movement can be checked at the point level — a knee marker must bend where the knee
bends, or the skin is lying.

### theMeaning — the human's terminal

The last question is not a number: **is it recognizably a teddy bear?** The physics score (P) says the
body obeys the laws; the visual score (V) says a skeptic names it without being told. They are two
terminals — PHYSICS and THE HUMAN — and they must agree. The eye is the vision model (Ollama's
qwen3.8), asked one specific question per movement, BLIND to the numbers.

---

## The decomposition (the membranes, compiled by gen_decl.py)

```chimera-terms
theStory [H] the teddy bear -- a third-person character, trained like a robot, run by CA rules
  theSeed [P] the genome + TRELLIS base: one number grows the whole lattice, deterministically
    theDeterminism [P] same genome -> same cells, bit-identical -- the seed's only law
  theShape [P] the voxel lattice body -- TRELLIS gives the base representation; the CA owns it after
    theBalance [P] center of mass inside the paw support hull (margin >= 1 cell) -- the standing gate
  theMuscle [P] a column that shortens -- movement is cells added/removed on the lattice
  theRig [P] the chains the muscle rides on, derived from the shape (never the reverse)
  theGait [P] the beat machine (LIFT/SWING/PLANT/SHIFT) -- each joint verified before the walk
    theStand [P] rest equilibrium: paws planted, zero drift, no airwalk
    theWalk [P] the stride -- trained only after every movement is verified
  theScan [P] sense: the retinal senses read the field around the bear (ground, goal bearing, reach)
  theChoose [P] plan: Q-learning over rest/wave/walk picks the steps toward a goal (sense -> plan -> act)
  theControl [P] third-person control -- the operator steers the bear, or hands over to its own policy
  theWorld [P] the training environment (the gym): terrain, contact, gravity, and the goal placed in it
  theAppearance [P] the splat surface -- SPL markers so the outer skin transforms smoothly with the lattice
  theMeaning [H] is it recognizably a teddy bear -- the eye judges each movement (right knee? right bend?)
```

---

## The control protocol (the operator's keys)

The bear answers commands, not a keyboard-heavy sim. Bindings live in the genome's command loop
(`ca_core.cpp`), reached through the relay and the native viewer:

| Command | Does |
|---|---|
| `WAVE` (1) | greet — lift one paw, the least-motion movement |
| `WALK` (2, toggle) | the beat machine, east (`walkw` = west) |
| `REST` (3) | plant all paws, zero drift |
| `AUTO` (4) | the learner runs |
| `DROP` (5) | the drop law falsifier (contact tick vs prediction) |
| `NAV` (6) | navigate toward a goal |
| `ROM` (9) | range-of-motion survey — every joint swept, for the eye to judge |

Direction is a command, not a genome fact: `walk` / `walkw`, and (next) heading as z-axis turning —
the honest open problem is that rotating a live lattice leaks cells; the CA-native answer is likely
"grow the turn" (differential paw-plant columns), not rotating the cell set.

---

## Feature status & the Holding Bay (the archive protocol)

Every term in the decomposition is a FEATURE: **in play** (in `chimera-terms`, compiles into the game)
or **held** (moved to `chimera-archive`, inert by construction). To archive, CUT the block and PASTE
it here with a `# HELD <date>: <reason>` line; to restore, move it back.

```chimera-archive
# HELD 2026-08-17: the solar-system timeline (theSeed..theMeaning of the old game) -- the studio
# pivoted to the teddy bear. These 58 terms are kept whole so their proofs and bindings are
# recyclable, but they are OUT of play: gen_decl.py parses only the block above.
theSeed [P] the number + the laws that unfold the world
  theDeterminism [P] same seed -> same world, bit-identical
  theLaws [P] the trained physics the seed runs under
  theTruth [P] every fact reaches physics; the world cannot lie
theSolarSystem [P] the setting you fly
  theStar [P] the yellow hearth
  thePlanets [P] the worlds in orbit
    aPlanet [P] the world you fall toward
      theTerrain [P] the whole-sphere surface
      theAtmosphere [P] air, sky, weather
      theOcean [P] the water
      theBiomes [P] climate + life bands
      theGround [P] the surface underfoot (matter under boots)
      theInterior [P] layers, ore, caves
        theMining [P] planetary excavation -- the dig verb on a world (bore, ore, claim, beacon)
      theGarden [P] the lush living place (lushEden)
        theEcosystem [P] life cascading from physics
        theTree [P] the Tree of Knowledge
          theTreeForm [P] grown from one genome
          theFruit [H] knowledge of good and evil
        thePlanting [P] the tree grows into the surface (the seam)
        theFarming [P] cultivation -- grow food from energy + soil (the grow verb, tended)
          thePlanetaryFarm [P] farms on a world's surface
          theLunarFarm [P] farms on airless / low-g worlds (domes, regolith hydroponics)
          theOrbitalFarm [P] hydroponic farms in orbit / deep space
  theSpace [P] the medium you fly (the dark, gravity, scale)
  theDensityClock [P] time leans with mass and speed
theShip [P] the player's vessel; the cold start
  theFlight [P] translation, pitch / yaw / roll, VTOL, wings, landing gear
  theShipPower [P] power buses + capacitor routing (attack / drive / barrier)
  theShipCombat [P] targeting grid, batteries, heavy ordnance, countermeasures
  theShields [P] the barrier grid + directional bias
  theWarpDrive [P] fold travel; VCM / WTM configuration
  theShipView [P] pilot / external-drone perspective, camera presets
  theSalvage [P] the industrial array -- space mining + graviton handling
theDescent [P] traversing the scales (the membrane onion; LOD of meaning)
  theStanding [P] you stand on real ground, witnessed by contact
  theBlackHole [P] the density clock's ceiling; the hole you can't see into
theVerbs [P] how you act -- verb over nouns
  theThrust [P] energy -> motion (the density clock)
  theDig [P] into the ground (grain physics)
  theBalance [P] center-of-mass vs center-of-thrust
  theGrow [P] life from energy (logistic)
  theScan [P] read composition (spectral)
  theNavigate [P] orbital mechanics, reach a target
  theShoot [P] aim + discharge weapons (infantry and ship)
  theMelee [P] close-quarters strike
  theEVA [P] suit traversal in vacuum / low-g (jetpack, mag-boots)
theLoop [P] world + player + input -> verbs -> state -> tick
  thePlayer [P] the character; presence before action (the Dot)
  theInput [P] keystrokes -> verb dials
  theState [P] what ticks
  thePersistence [P] same seed, same world, forever (save / return)
theMeaning [H] deciding what things mean; the gift, your terminal
  theParadise [H] does Eden read as paradise
  theChoice [H] good and evil; the human decides
  theWorthPlaying [H] is it a game worth playing
  theExperience [H] the felt whole; understood, not won
```
