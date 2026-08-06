# THE HIERARCHY — every term, one tree (light era)

*2026-08-06. The master index: the hierarchy of every concept the game — and the
method — will ever judge. Replaces the matter-era story tree (48 membranes, archived
at tag `matter-era-end`). Every term has: a PARENT (the term it anchors to or is
contained within), a constraint DIMENSION (0-D point / 1-D chain / 2-D sheet /
3-D bulk / FORCE / COMPOSITE), and a falsifier stub. Full membranes graduate into
`docs/THE_CATEGORIES.md` or their own RULE 0 sections as proofs earn them.*

## THE EXCLUSION RULE (non-dangerous by construction, not by promise)

No term enters this tree whose function is harm: no weapons, no injury-optimized
structures, no force-law modifications, nothing whose falsifier would require
breaking another membrane on purpose. The tree builds, contains, connects, and
maintains — that is the whole vocabulary. A term that can only be tested by
damaging something is not a term; it is the absence of one.

## LEVEL 0 — THE SEED (proven chain: runs 1-4)

- **theElectron** — the identical point. FORCE. Parent: none.
- **theDraw** — blind long-range gravity. FORCE. Parent: theElectron.
- **theResistance** — wall + bond, short-range. FORCE. Parent: theElectron.
- **theRadiation** — contact dissipation as light. FORCE. Parent: theResistance.
- **theBalance** — clumps settle (bulk PASS at N=4096, two seeds). Parent: all above.
- **theCollapseLimit** — above 4x density the draw wins (run 4c). Parent: theBalance.

## LEVEL 1 — CELESTIAL (the biggest balances)

- **theClump** — a settled bound cluster. 3-D. Parent: theBalance. PROVEN (runs 3-4).
- **theCore** — a clump dense enough to hold orbiters. 3-D. Parent: theClump. PROVEN
  (core_shell print: bound 1.000, accretes).
- **theOrbit** — a point bound to a core at derived speed. 0-D. Parent: theCore.
- **theShell** — orbiting cloud around a core. 3-D. Parent: theOrbit. FAILED at
  f_core=0.5 (relaxation) — successor: shell mass << core mass.
- **theDisk** — differentially rotating sheet of orbiters. 2-D. Parent: theOrbit.
  (RUNNING — fragments into orbiting clumps: planet-formation as failure mode.)
- **thePlanetSystem** — core + persistent shell at mass hierarchy. COMPOSITE.
  Parent: theShell's successor.
- **theGalaxy** — disk of cores. COMPOSITE. Parent: theDisk.

## LEVEL 2 — GEOLOGICAL (the ground things)

- **theCrystal** — lattice bulk, ordered bonds. 3-D. Parent: theBalance. DEAD
  2026-08-06 at every tested size (8..4096): no attractive bond exists, so no
  static crystal can (see theCushionLaw). Its successor is not a smaller
  chunk but a different print: cushion-phase matter printed AT equilibrium.
  The term survives as the ORDERED INITIAL CONDITION — the bone smoke showed
  an ordered start self-crushes coherently into an elastic slug that bears
  load 21x better (deflection/load) than a random start ("the memory of
  order"), while the random start stays mud. Order matters as PRINT
  GEOMETRY, not as a phase.
- **theMaxChunk** — SUPERSEDED 2026-08-06 by theCushionLaw, after the full
  crush series (8, 27, 64, 216, 512, 4096 — every bond-spaced lattice chunk
  collapses). The M_crit chain (640 naive, ~45 hydrostatic) asked the wrong
  question because it assumed an attractive bond existed to be overwhelmed.
  Read the kernel's actual law (kernel.py:150-154): the "bond spring"
  f = K_BOND(r-r_bond)/(r_bond*r) exists ONLY on [r_wall, r_bond] and is
  REPULSIVE there; beyond r_bond there is NO resistance force at all; below
  r_wall the wall. THE RESISTANCE IS REPULSION-ONLY — a cushion. All
  cohesion in this universe is DRAW. R_BOND never was an attraction
  distance; it is the outer edge of the cushion. (The kernel comment
  "attractive when stretched" is a lie the code never told — the branch is
  unreachable for r > r_bond.)
- **theCushionLaw** — the one condensed phase. Every free condensed body is
  a self-gravitating droplet resting on the spring+wall cushion: DRAW pulls
  in, the cushion pushes out, equilibrium spacing sits AT/BELOW the wall
  edge (~0.048 for a 2^3 cube, ~0.028 at N=512 — deeper with mass,
  hydrostatically). Rock-stable once settled (512 held radius 0.140 for
  270k ticks, CV=0). The crush from a bond-spaced start is free-fall onto
  the cushion — there is nothing at r_bond to catch it, because no
  attraction ever lived there. CONSEQUENCES: (1) there is no static crystal
  at any size — theCushionLaw is the only solid; (2) the printer's first
  law: PRINT AT EQUILIBRIUM, or the 4th dimension finds it violently and
  radiates the difference; (3) extended shapes (rods, sheets) are NOT
  equilibria — they survive only HELD (pinned anchors pushing, containment,
  rotation) or as blobs; tension does not exist beyond the cushion, so a
  rod must be held OPEN, never hung. PREDICTION (named before the run): a
  2^3 cube printed at its derived cushion equilibrium d_eq = 0.0484 (corner
  force root, kernel-exact) HOLDS — radius stable ~0.042, E_rad ~ 0, no
  crush — while the same cube at r_bond crushes (already observed).
  FALSIFIER: if the equilibrium print ALSO collapses or wanders, the
  kernel-exact force reading is wrong and the integrator itself is next
  under the light. CONFIRMED 2026-08-06 (lattice8eq): no collapse, radius
  steady at 0.055 (the +31% over the cold root is the builder's thermal
  sigma — print cold next), radiation 4.6x under the bond-spaced start; a
  20k-tick CPU replica shows the cube ANNEALS into a close-packed
  wall-spaced cluster (17 contacts at 0.0499) — the printed shape is not
  the equilibrium shape, and the equilibrium shape of this universe is the
  close-packed droplet. The crystal this universe grows is close-packed,
  not cubic. 3-D. Parent: theBalance.
- **theBone** — load-bearing dense lattice. 3-D. Parent: theCrystal.
- **theSoil** — packed bed, disordered bonds. 3-D. Parent: theBalance.
- **theSlope** — packed bed at a tilt; repose angle emergent. 3-D. Parent: theSoil.
- **theRock** — dense packed bed, high bound fraction. 3-D. Parent: theSoil.
- **theTerrain** — slabs/slopes at game scale. COMPOSITE. Parent: theSlope.
- **theCavern** — a stable void contained within a bulk. 3-D. Parent: theRock.
  (Contains-within enters geology too: the cave is the rock's brain.)

## LEVEL 3 — FLUID (the flowing things)

- **theGas** — hot unbound points. 3-D. Parent: theElectron. (Run 2 is its portrait.)
- **theLiquid** — cool bound points below the collapse limit, no lattice. 3-D.
  Parent: theBalance.
- **theDroplet** — a liquid ball holding its edge. 3-D. Parent: theLiquid.
- **theBubble** — gas contained within liquid/sheet. 3-D. Parent: theDroplet.
- **theCurrent** — liquid in bulk motion through terrain. COMPOSITE. Parent: theLiquid
  + theTerrain.

## LEVEL 4 — FIBROUS (the 1-D things — the operator's chain)

- **theFiber** — serial chain, rupture past r_c built in. 1-D. Parent: theCrystal.
- **theRope** — tension-only fiber. 1-D. Parent: theFiber.
- **theBranch** — degree-3 chain nodes (trees, vessels, rivers of the body). 1-D.
  Parent: theFiber.
- **theHinge** — two chains, one shared point, rotation free. 0-D. Parent: theFiber.
- **theTendon** — chain joining muscle to bone. 1-D. Parent: theFiber + theBone.

## LEVEL 5 — SHEETED (the 2-D things)

- **theSheet** — bonded lattice one point thick. 2-D. Parent: theFiber.
- **theSkin** — sheet conformal to muscle. 2-D. Parent: theMuscle.
- **theShellHard** — multi-layer sheet that resists (bark, skull-plates). 2-D.
  Parent: theSheet + theBone.

## LEVEL 6 — COMPOSITES (the anatomy — anchored & contained)

- **theMuscle** — fiber bundle between bones, O(L) per fiber. COMPOSITE.
  Parent: theBone + theTendon. Falsifier incl.: the bones do not migrate.
- **theBladder** — closed sheet contained within muscle; squeeze is its function.
  2-D/3-D. Parent: theMuscle (contained-within).
- **theBrain** — soft bulk contained within bone. 3-D. Parent: theBone
  (contained-within). Falsifier: shelled bulk survives impact that kills unshelled.
- **theOrgan** — any composite contained within skin. COMPOSITE. Parent: theSkin.
- **theSkeleton** — the bone tree of a body. COMPOSITE. Parent: theBone.

## LEVEL 7 — MECHANICAL (the made things — non-dangerous subset only)

- **theLever** — a rigid bulk rotating on a 0-D fulcrum. COMPOSITE. Parent: theBone
  + theHinge.
- **theWheel** — a disk rotating on an axle hinge. COMPOSITE. Parent: theDisk
  (reused at body scale!) + theHinge.
- **theFrame** — rigid bone-tree that bears a load (hut, bridge). COMPOSITE.
  Parent: theSkeleton.
- **theContainer** — a skin/bladder for things, not fluids. 3-D. Parent: theSkin.

## LEVEL 8 — LIFE (the boundary that maintains itself)

- **theBoundary** — a closed skin whose inside differs from its outside. 2-D.
  Parent: theSkin.
- **theMetabolism** — a boundary that exchanges points/energy and persists.
  COMPOSITE. Parent: theBoundary + theRadiation.
- **theSignal** — a branched chain that transmits a state change faster than the
  medium diffuses it (the nerve question). 1-D. Parent: theBranch.
- **theLife** — boundary + metabolism + signal, contained in a brain, contained
  in bone. COMPOSITE. Parent: theBrain (contained-within). The final membrane.

## RULES OF THE TREE

1. Two relations only: **anchors-to** and **contains-within**. Every parent link
   is one or the other, labeled.
2. A term enters the queue only with its falsifier written (RULE 0).
3. A term's proof uses only terms already proven below it.
4. The forces never change. Types emerge or are printed; they are never authored
   onto points.
5. The exclusion rule above is enforced at authorship — a harmful term is not
   failed, it is never written.

## SUB-HIERARCHIES (the imported breadth — 2026-08-06)

This file is the MASTER SPINE: the physics-first terms that get membranes, prints,
and falsifiers. Beneath it hang the imported sub-hierarchies — 35,835 physical-world
terms from WordNet (`LightEngine/hierarchy_import/wordnet_terms.json`, built by
`LightEngine/hierarchy_import.py`, exclusions applied: 1,252 ancestry-dropped,
567 backstop-dropped, both audited). The graft points — which imported subtrees hang
under which spine term — live in `LightEngine/hierarchy_import/graft_map.json`.

Promotion rule: a sub-hierarchy term is CANDIDATE VOCABULARY. It joins this spine
only through membrane authorship (parent named, constraint dimension assigned,
falsifier written). The spine decides what is REAL; the sub-hierarchies decide what
is NAMEABLE. This doc points at the import; it does not duplicate it.
