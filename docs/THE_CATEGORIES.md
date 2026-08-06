# THE CATEGORIES — the constraint manifest (skeleton)

*2026-08-06. The giant list. Every concept in the game is a CONSTRAINT TYPE — a
declared connection topology read by the two frozen forces (draw + resistance +
contact radiation). No entry may change the forces. No entry ships without its
falsifier fired and recorded in the ledger. Organized by constraint dimension:
0-D anchors, 1-D chains, 2-D sheets, 3-D bulks, and the cross-structure joints
that connect them. Status: SKELETON — entries graduate to full membranes (own
RULE 0 doc section) as the print proofs earn them.*

## THE SAFETY CONTRACT (why a giant list is safe)

1. The two forces never change. Constraints are connections, not laws.
2. Every entry has a falsifier named BEFORE its run (RULE 0 per membrane).
3. Every entry trains in an isolated ensemble world — no leakage (verified
   bitwise in `tests/test_ensemble.py`).
4. The ledger records every verdict; only PASS entries enter the game.
5. Every constraint parameter is DERIVED from the force constants
   (rest length from r_bond, rupture from r_c, stiffness from K_BOND) — never tuned.

## 0-D — ANCHORS & POINT JOINTS

- **anchor**: a point fixed to the world frame (or to a heavier clump) that
  other structures attach to. Falsifier: holds position under derived max load.
- **hinge**: two structures sharing one point, free to rotate, translation locked.
  Falsifier: transmits force, allows rotation, fails (ruptures) past derived load.

## 1-D — CHAINS (fibers, ropes, limbs, vessels)

- **fiber**: serial chain i..i+1 at r_bond; rupture past r_c is built in.
  Falsifier (the muscle question): transmits derived aggregate force AND survives
  its own contraction without crumpling (the fascicle test — does packing hold
  chains straight, or is angular stiffness needed from the modifier M?).
- **rope**: fiber optimized for tension only, no compression. Emerges free: the
  bond spring is already asymmetric about r_bond. Falsifier: buckles under
  compression, holds under tension.
- **branched chain**: a chain with degree-3 nodes (trees, vessels, nerves).
  Falsifier: branch angles persist; load distributes as derived.
- **hinged limb**: two chains sharing a hinge with an angle limit (joint stop).
  Angle limits are a CONNECTION property (link i+1 constrained to an arc about
  the hinge), not a new force. Falsifier: moves through range, stops at the stop.

## 2-D — SHEETS (skin, membranes, cloth, shells)

- **sheet**: triangular/hex lattice at r_bond, one point thick. Falsifier: holds
  area and edge under derived pressure; drapes (no bending stiffness = cloth) or
  resists (packed multi-layer = shell) as printed.
- **SKIN**: a sheet printed CONFORMAL to a muscle/composite bulk and anchored to
  it at derived spacing — skin comes from the muscle: the muscle is its parent
  membrane, the layer beneath that it must move with. Falsifier: stays conformal
  through the muscle's full contraction cycle — does not slide off (anchor
  retention), does not tear (strain distributes as derived across the sheet),
  and its edge stays closed (a bag with a hole is not skin).
- **bladder**: closed sheet enclosing gas points, CONTAINED WITHIN the muscle
  bulk (like the brain within bone) — the muscle is its parent by enclosure,
  and the muscle's contraction is its function: squeeze is what moves contents.
  Falsifier: holds its contents under the muscle's derived squeeze pressure
  without rupture, and yields its contents when the squeeze exceeds a derived
  threshold (a bladder that can't empty is a cyst).

## 3-D — BULKS (flesh, organs, soil, rock)

- **packed bed**: random points at ~bond density under their own draw — soil,
  sand, granular ground. Falsifier: holds a derived angle of repose against a
  printed tilt (the matter era's repose lesson, relearned emergently).
- **lattice bulk**: the crystal print (RUNNING). Falsifier: bond retention > 50%.
- **BONE**: a dense lattice bulk — ordered packing = stiff, disordered = compliant;
  the distinction is free because points are identical. Bone is the PARENT
  membrane of the muscle: muscle is defined by its two bony attachments, and
  every 1-D/2-D structure that bears load anchors to bone.
  **PRINT SPEC (v1, after theMaxChunk):** an ASSEMBLY of sub-critical grains —
  each grain a lattice chunk of side 6-8 (216-512 points, below M_crit=640) —
  grains bonded face-to-face at r_bond in a rod. Never one merged mass: the
  grains are the atoms, the rod is the bone (real bone: mineral crystallites
  in a matrix — the universe agrees). Load is applied by two ANCHOR plates
  (pinned 0-D points, the anchor membrane) driven together at a derived speed.
  **Falsifiers:** (a) no grain merges into another — grain count stable through
  the window (the assembly must not collapse into one core); (b) under derived
  compression the rod deflects and springs back with NO bond ruptures below the
  derived load, and ruptures AT the derived load (not before); (c) deflection
  per unit load is less than a packed-bed rod of equal mass by a derived factor
  (ordered beats random).
- **BRAIN**: a soft bulk CONTAINED WITHIN bone (the skull) — the second relation
  this manifest tracks: not anchors-to but contains-within. Bone is the brain's
  parent by enclosure: it takes the load so the brain doesn't have to.
  Falsifier: a bone shell surrounding a compliant bulk absorbs a derived impact
  — shell bonds may rupture, but the contained bulk's structure persists (its
  bond retention stays above threshold) where an UNSHELLED bulk of the same
  stuff fails. LIFE is contained in the brain — the deepest nesting.
- **composite bulk**: fibers embedded in packed bed = flesh, muscle-in-sheath.
  Falsifier: the composite holds forms neither component holds alone (this is
  where the muscle print lives).

## CROSS-STRUCTURE — ATTACHMENTS (tendons, sockets, roots)

- **tendon**: a chain connecting a 1-D structure to a 3-D bulk (muscle to bone).
  Falsifier: force transmits across the interface; the interface fails at the
  DERIVED weakest link (chain, bond, or bulk — the ledger records which).
- **socket**: a 0-D anchor embedded in a bulk, holding a hinge. Falsifier:
  pullout strength matches derivation from bulk packing.

## THE MUSCLE (flagship composite — the operator's spec)

Bundle of fibers (arbitrary L, O(L) per fiber to compute) packed in a sheath,
strung between two BONES via tendons — muscle comes from the bone; there is no
muscle without a bony anchor at each end. Contraction = shortened fiber rest
length; force = derived aggregate; stroke = L x (r_c - r_bond) per link. Tearing,
failed movement, and limits are EMERGENT (bond rupture, force balance). Falsifier:
bundle delivers derived force to the bones, survives contraction, and a pulled
fiber tears at r_c rather than stretching forever — and the BONES do not migrate
(the anchor holds; if the bones move, the muscle moved the wrong thing).

## ORDER OF PROOF (derived from dependency depth)

lattice (running) -> BONE (a lattice that bears load) -> BRAIN (a bulk contained
in bone) -> packed bed (needs nothing) -> fiber/rope (needs bone anchors) ->
sheet (needs fiber) -> tendon/socket (needs bone+chain) -> muscle (needs all)
-> SKIN (a sheet conformal to muscle) + bladder (contained in muscle) ->
LIFE (contained in the brain — a boundary that maintains itself; needs all).

The anatomy is the dependency graph, and it tracks TWO relations:
anchors-to (muscle to bone, skin to muscle) and contains-within (bone holds
the brain, muscle holds the bladder, the brain holds life). Each layer's
parent is the layer it anchors to or the layer it lives inside.
