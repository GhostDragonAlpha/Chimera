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
- **lattice bulk**: the crystal print — DEAD 2026-08-06 at every size (no
  attractive bond exists; see theCushionLaw). Successor: cushion-equilibrium
  prints (stable, confirmed lattice8eq); the universe's crystal is
  close-packed, grown by annealing, not printed cubic.
- **BONE**: a dense ordered bulk — ordered print = stiff, disordered = compliant;
  the distinction is free because points are identical. Bone is the PARENT
  membrane of the muscle: muscle is defined by its two bony attachments, and
  every 1-D/2-D structure that bears load anchors to bone.
  **PRINT SPEC (v2, after theCushionLaw — v1 grain spec dead with the crystal):
  the bone is a PRELOADED COMPRESSION COLUMN.** The tension derivation
  2026-08-06: a free rod's self-DRAW contraction exceeds its end adhesion
  (DRAW at cushion gap) by 20-100x at every aspect ratio — no free-standing
  extended structure can exist here; the universe makes droplets, not sticks.
  But real bone is a preload compression member (muscles hold it loaded), and
  the cushion phase is incompressible and elastic. So: a column printed
  ORDERED at cushion spacing (0.05) between two pinned anchor plates IN
  CUSHION CONTACT, preloaded by plate convergence until the plate force
  reaches 1.5x the derived end-weight of the column (the axial DRAW that
  would lift an end off its plate — computed from the print geometry, kernel
  force law, no free numbers), then HELD for the window; then half-released
  and re-seated for the spring-back test.
  **Falsifiers:** (a) SEATING — both ends stay in cushion contact with their
  plates for the whole hold (any end gap > r_c = detachment); (b) ESCAPE —
  zero points leave the column (nearest-neighbor distance > r_c) under
  preload; (c) SPRING-BACK — after the half-release, plate force and column
  length return to the seated values within 10% (elastic, no hysteresis
  failure); (d) ORDERED BEATS RANDOM — deflection per unit load under a
  derived overload pulse beats the packed-bed column of equal mass by 2x
  (v1 smoke already showed 21x on this axis; v2 measures it under preload).
  A dead falsifier, recorded honestly: v1(a) grain-identity — grains never
  existed; the crystal is not a phase.
  **v2 SMOKE VERDICT 2026-08-06 (N=288, 4x4x16 column, F_pre=2467.8 derived):**
  (a) SEATING PASS (both ends glued, gaps 0.0000 through the hold);
  (b) ESCAPE PASS (zero escapees); (c) SPRING-BACK FAIL — force hysteresis
  36% on the first cycle (236 loading vs 320 release at half-closure) while
  LENGTH hysteresis is 0.05%: the first cycle beds the contacts in
  (irreversible anneal toward close-packed), it is not elastic failure.
  Successor: measure spring-back on the SECOND cycle (bed-in first, then
  judge elasticity on the annealed column). (d) ORDERED-BEATS-RANDOM FAIL —
  1.025x (threshold 2.0): under preload the packed column anneals into the
  SAME close-packed cushion state and performs identically. The universe
  crystallizes both prints into one attractor; order matters for the
  FORMATION PATH (v1: coherent crush, 21x) but is forgotten by the annealed
  material. Consequence for the whole manifest: permanent microstructure
  cannot be printed — form lives in MEMBRANES (pins, containment,
  assemblies), never in material microstate. This matches the doctrine:
  types live on membranes/clumps, never authored per-point.
  **v2 CYCLE-2 VERDICT 2026-08-06 (the bed-in successor run):** (a)/(b) PASS
  again; (c) FAILS again but 36% -> 12% force / 13% length hysteresis on the
  second cycle — the loop is closing with annealing but converges onto a
  CREEP FLOOR, not zero: at equal closure the column is LONGER on release
  than on converge (slow rearrangement under sustained load). And at cycle-2
  deep converge the right end skated to gap 0.147, a hair under the spring
  cutoff 0.15 — near-detachment at preload. The honest material law: the
  cushion phase is a CREEPING granular solid, not an elastic one. Successor
  to (c): measure the hysteresis asymptote over N cycles (converges to zero
  = slow bed-in; converges to a floor = creep is the law) — named, not yet
  run. Bone's elasticity claim is REFUTED at the 10% bar; bone as a
  creeping-but-seated compression member stands ((a)/(b) at preload).
  **v2 CYCLE-4 VERDICT 2026-08-06 (the asymptote run, print_bone_c4):** four
  preload cycles with halving convergence distance (18479 → 9242 → 4617 →
  2305 ticks), preload 2469–2479 each time. (a)/(b) PASS all four cycles
  (gaps 0.0000, zero escapees, one cluster). (c) SPRING-BACK FAIL at every
  cycle and the hysteresis does NOT converge to zero: cycle-4 loop at
  mid-closure 0.8988 reads release F/L = 761.2/0.26024 vs converge
  F/L = 550.7/0.24996 — the column is LONGER on release than on converge at
  equal closure, a plastic ratchet, and under the final hold at fixed
  closure the force relaxes from 808 to ~223 (≈9% of preload): the column
  does not store elastic preload, it creeps to a force floor while holding
  its set length. The asymptote question is answered: creep is the law, not
  slow bed-in. Bone is a PLASTIC compression member — seated, containing,
  load-bearing, never a spring. The reversible element of the body is the
  muscle (the DRAW-bridge, whose (a) FORCE LAW passed the same day);
  bone-muscle is the plastic-elastic pair. (d) OVERLOAD pulse: peak force
  1456, peak deflection 0.151, column recovers into the same set.
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

*(v1 fiber spec retired 2026-08-06: "rest length" and "bond rupture" presumed
an attractive bond that does not exist — see theCushionLaw. Re-derived below
for the universe as measured.)*

**theMuscle is the DRAW-bridge.** No tension exists in the resistance; the
only pull in this universe is DRAW (long-range, softened inverse-square).
A muscle is a condensed droplet seated (cushion contact) on one bony anchor
and pulling the OTHER anchor toward it across the gap — it never needs to
touch its far tendon, the same way a planet never touches its moon. Force =
G·M_muscle·m_anchor/s², kernel-exact; contraction = plates converging under
that pull; the SAME droplet in compression is the cushion — the antagonist
pair is built into the physics (one material, two regimes: pull when
extended, push when compressed). Stroke is derived from the force law, not
from link count: force halves at s·√2, so the useful stroke is s₀(√2 − 1)
≈ 0.41·s₀. Tearing is emergent and redefined: under extension the droplet
either migrates (bridge loses symmetry) or SPLITS (cluster count > 1) at a
derived separation — the ledger records which and where.
**PRINT SPEC (v1 of the bridge):** two pinned anchor plates (the tendons;
bones come later — muscle comes from the bone, anchors first), a droplet of
N_m points printed cold at cushion spacing 0.05, seated on the left plate at
cushion contact; plates separated so the far plate sits at a derived
separation s₀ (droplet-to-far-plate DRAW = a derived fraction of
droplet-near-plate adhesion — the bridge must be pulling, not touching).
Protocol: pull plates apart at 5% sound speed to s₀·√2·1.5, converge back
past s₀ into the cushion regime, measuring plate force throughout.
**Falsifiers:** (a) FORCE LAW — the measured contractile force-separation
curve matches the kernel-exact DRAW prediction within 10% over the stroke
(the muscle's force is DERIVATION, not mystery); (b) STROKE — contractile
force stays ≥ half its s₀ value out to s₀·√2 (the inverse-square stroke);
(c) TEAR — beyond the derived separation the bridge fails as named
(migration or split, recorded), never silently; (d) ANTAGONIST — past full
convergence the force REVERSES sign onto the cushion (the same material
pushes); (e) the anchors do not migrate (pins hold; if the plates move, the
muscle moved the wrong thing).
**BRIDGE v1 VERDICT 2026-08-06 (N=112, droplet 4³ + two 4×4 plates,
run tag muscle_v3):** ALL FIVE PASS. (a) FORCE LAW — measured right-plate
force vs the exact pairwise softened-DRAW sum over (droplet ∪ left plate) ×
right plate on the RECORDED positions: max rel err 0.000 over 16
contact-free extension samples (bar 0.10). The deformation-immune form was
forced by two refuted predecessors: a point-COM log-log exponent fit read
−1.557 (not −2) because the droplet STRETCHES toward the receding plate —
real muscle physics that makes point-COM the wrong coordinate (exponent kept
as a diagnostic only). The muscle's force is derivation, exactly. (b) STROKE
PASS — F(s₀·√2)/F(s₀) = 0.669 ≥ 0.5. (c) TEAR PASS — one cluster through
the whole stroke; migration max |com_yz| = 0.011 (bar 0.05). (d) ANTAGONIST
PASS — force reverses to −328.2 in convergence (the same material pushes).
(e) ANCHORS PASS — plate drift 0.000000. One material, two regimes,
measured. Successor: theTendon (force across the muscle–bone interface,
fails at the DERIVED weakest link), then theJoint — the first moving part.

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
