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
- **bladder**: closed sheet enclosing gas points; pressure from wall collisions.
  Falsifier: holds derived pressure-volume relation; ruptures past derived
  pressure (tearing already in the bond law).

## 3-D — BULKS (flesh, organs, soil, rock)

- **packed bed**: random points at ~bond density under their own draw — soil,
  sand, granular ground. Falsifier: holds a derived angle of repose against a
  printed tilt (the matter era's repose lesson, relearned emergently).
- **lattice bulk**: the crystal print (RUNNING). Falsifier: bond retention > 50%.
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
between two anchor plates. Contraction = shortened fiber rest length; force =
derived aggregate; stroke = L x (r_c - r_bond) per link. Tearing, failed
movement, and limits are EMERGENT (bond rupture, force balance). Falsifier:
bundle delivers derived force to anchors, survives contraction, and a pulled
fiber tears at r_c rather than stretching forever.

## ORDER OF PROOF (derived from dependency depth)

lattice (running) -> packed bed (needs nothing) -> fiber/rope (needs lattice
anchors) -> sheet (needs fiber) -> tendon/socket (needs bulk+chain) -> muscle
(needs all) -> bladder -> LIFE (a boundary that maintains itself — needs all).
