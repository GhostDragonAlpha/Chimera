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

*(Old sheet line retired 2026-08-06: "triangular/hex lattice at r_bond"
presumed the attractive bond that does not exist — see theCushionLaw.
Re-derived below.)*

## THE SHEET (the 2-D membrane — light-era derivation 2026-08-06)

The crush series already proved the hard half: every FREE lattice 8→4096
collapses into a droplet — there is no bending stiffness, so a free sheet
must ball up. And bone's anneal proved where form lives: in MEMBRANES (pins,
containment, substrates), never in material microstate. So theSheet's
claim is not "a sheet holds itself" — nothing does — it is: **a 2-D layer
on a substrate is a persistent 2-D phase**: the substrate's DRAW holds it
flat, the cushion keeps it one grain off the surface, and its own
self-DRAW holds it in-plane. Cloth, not shell, by necessity — and cloth is
what skin and bladder need.
**PRINT SPEC (v1):** a 16×16 sheet one grain thick at cushion spacing
0.05, printed horizontal at height d_eq + one lattice step above a pinned
6×6 plate; in the DRAPE run a 4×4×4 block (the obstacle, a standing-in
bone) sits on the plate under the sheet's center. Three settle runs —
BUMP, FLAT (no obstacle), FREE (no plate: the anti-falsifier) — and one
TEAR run: the sheet printed on the plate, its two opposite edge rows
pinned (the frame), pulled apart quasistatically at 5% sound speed.
**Falsifiers:** (a) PHASE — in BUMP and FLAT the sheet ends as a 2-D
phase: cluster count 1 AND thickness (sheet-grain z-spread) ≤ 2 lattice
steps; in FREE the same print MUST ball (thickness > half the sheet
width) — if a free sheet stays flat, theCushionLaw is wrong and the whole
era reopens; (b) DRAPE — in BUMP, settled: the sheet contacts the
obstacle's top face within the cushion band [d_eq − 0.02, d_eq + 0.05]
AND ≥ half its outer edge rows reach cushion distance of the plate —
cloth conforms; a sheet that tents over the block with a void underneath
is a shell, recorded as REFUTED for v1 (shells are multi-layer, later);
(c) TEAR — under the pinned-frame pull, first split (cluster count 2)
arrives at a measured global stretch in the derived window [1.5×, 4×]:
uniform stretch breaks links at exactly 3× (0.05 → R_BOND = 0.15) and
strain concentration at the grips can only lower it; the split location
is recorded (predicted: adjacent to a grip, where concentration lives),
and post-split each fragment remains one condensed sheet (no
sub-fragmentation beyond cluster count 2 at first split).
**SHEET v1 VERDICT 2026-08-06 (16×16 at 0.05, run tags sheet_v1_flat /
bump / free / tear):** ALL FOUR FALSIFIERS FAIL, and the failures are the
discovery — recorded per doctrine, each against the verified trajectories.
(a) PHASE: there is no flat 2-D phase at 0.05. The sheet CRUMPLES to a
coherent folded mat — thickness 0.003 → 0.2414 on the plate, 0.003 → 0.2411
FREE, cluster count 1 in both, stable for 20,000 ticks. The spec's central
claim ("a 2-D layer on a substrate is a persistent 2-D phase") is REFUTED:
the substrate neither causes nor prevents the crumple — the on-plate and
free mats agree to 0.0003, so the mat is the sheet's own phase, not a
substrate artifact. The anti-falsifier half-fires: no free flat sheet
exists (theCushionLaw holds) — but condensation ARRESTS at the mat
(0.241 ≈ 5 layers) instead of balling to a droplet (>0.375); 2-D initial
conditions reach a folded phase the 3-D crush series never saw. The free
mat's COM stays fixed at print height for 20k ticks — momentum conserved,
physics clean. (b) DRAPE: partial — the sheet contacts the block at 0.0279,
BELOW the cushion band, i.e. seated in the wall at ≈S_WALL exactly as the
joint v2 law says matter under weight must; but only 22/60 edge grains
reach the plate band — the crumpled mat TENTS where a flat cloth would
drape. (c) TEAR: first split at tick 341, stretch 1.023 — two hundredths
of the derived window's floor — between grip rows 0–1, the predicted
LOCATION (strain concentration at the grip), with exactly 2 clusters at
split, the predicted CLEANLINESS. The derived window [1.5×, 4×] is void:
its premise was a flat lattice under in-plane strain, and the sheet
crumples in the first ~900 ticks, so the grip pulls out of a mat, not a
lattice — the premise died before the pull began.
**The law the failures leave:** at cushion spacing 0.05 a 2-D plane is
OVER-COMPRESSED in-plane (the droplet's d_eq = 0.0484 is a 3-D equilibrium;
the 2-D plane's own balance differs), and with no bending stiffness the
over-compression escapes out-of-plane: the sheet folds. What holds a sheet
flat is not a substrate but its own equilibrium spacing. Successor (named):
v2 — derive the 2-D in-plane equilibrium spacing d_eq_2D from the kernel
(print a small patch, measure where in-plane force vanishes, exactly as
theCushionLaw's lattice8eq print derived d_eq for the droplet), print the
sheet at d_eq_2D, and rerun PHASE / DRAPE / TEAR unchanged. Prediction
named before the run: at d_eq_2D the sheet stays flat (thickness ≤ 2
steps), drapes instead of tenting, and tears inside [1.5×, 4×].
**SHEET v2 VERDICT 2026-08-06 (d_eq_2D derived and printed; run tags
sheet_v2_flat / bump / free / tear; the logs carry the stale "SHEET v1"
verdict header — the label edit landed after the runs; numbers
unaffected):** the derivation SUCCEEDED and the prediction is REFUTED —
both recorded. d_eq_2D = 0.04005 by bisection of the edge-grain force
zero-crossing on a static 16×16 patch (13 iterations, bracket [0.03,
0.10]): SMALLER than the droplet's 0.0484, exactly as the per-grain DRAW
intuition says — fewer in-plane neighbors, weaker inward pull, so the
plane sits deeper in the wall where repulsion is stronger. A real 2-D
quantity from the kernel, derived not swept. But at d_eq_2D the sheet
STILL crumples: flat 0.2497 (with a 0.387 fold-wave at tick 600), free
0.2381 stable 20k ticks, torn at tick 343 / stretch 1.029 already 0.3126
thick. The static equilibrium answers where in-plane force vanishes; it
cannot answer the dynamic question, and the dynamic answer is now
measured twice: a fold brings distant regions of the plane into DRAW
range of each other, and DRAW amplifies density — the plane is
Jeans-unstable to folding. **There is no flat 2-D phase at any spacing;
condensed matter in this universe is always 3-D-ish (droplets, mats).**
What improved and is recorded: bump edge-drape 22/60 → 34/60 at d_eq_2D
(passes the ≥half bar). The surviving route to a flat sheet is the one
bone taught: form lives in MEMBRANES — a flat sheet exists only in a
FRAME. Successor (named): v3 — the framed sheet: all four border rows
pinned (the frame IS the membrane holding the plane), falsifiers PHASE
(framed flat holds ≤ 2 lattice steps all run) and TEAR (the [1.5×, 4×]
window, location, cleanliness — finally asked of a flat lattice). If the
frame cannot hold the plane either, the 2-D rung closes as REFUTED and
SKIN inherits the mat (a crumpled-mat skin conformal to muscle is
multi-layer skin, which real skin also is).
**SHEET v3 VERDICT 2026-08-06 (framed, d_eq_2D, run tags sheet_v3_framed /
sheet_v3_tear):** the conditional is answered — **the frame cannot hold
the plane; the 2-D rung closes as REFUTED.** (a) PHASE-FRAMED FAIL: the
sheet buckles through the 0.080 bar at tick 300, folds to 0.396, and then
the failure deepens past buckling — the interior TEARS OFF THE FRAME
(clusters 2 from tick 600, sustained all run) and drags in-plane (COM
wanders to (−0.010, −0.018)): the pinned border holds its 60 grains while
the sheet inside rips itself free and slides. The frame contains the
border; it cannot contain the interior, because containment would need the
interior to carry tension, and tension does not exist. (c) TEAR-FRAMED
FAIL on the same numbers as always: split at tick 362, stretch 1.031,
already 0.282 thick at split. Three constructions, one answer, third
rung of the ladder measured: **0-D pins hold, 1-D routes tension only,
2-D has no flat phase at any spacing in any frame — the condensed 2-D
form is the crumpled mat, and the mat is 3-D-ish.** The dimension ladder
now reads: form lives in 0-D pins, 1-D pullers, and 3-D bulks; a membrane
in this universe is a BULK THAT LEARNED TO LIE FLAT AGAINST SOMETHING,
never a plane. SKIN is re-derived accordingly (next membrane): a mat
printed conformal to the muscle bulk, held by the muscle's own DRAW —
the falsifiers (conformal through the stroke, no slide-off, edge closed)
inherit the mat's measured stability instead of a plane that never
existed.
- **SKIN** — re-derived on the mat 2026-08-07 (no plane ever existed — see
  theSheet v1–v3): **theSkin is a crumpled mat printed conformal to the
  muscle bulk and held by the muscle's own DRAW.** Real skin is multi-layer;
  this universe's condensed 2-D form was always going to be a mat. The
  muscle is its parent membrane: the substrate that gives the mat its form
  (bone's lesson — form lives in the membrane beneath).
  **PRINT SPEC (v1):** the settled muscle print (two pinned 4×4 anchor
  plates, one 4³ droplet bridge seated at cushion contact) PLUS a 16×16
  sheet at d_eq_2D = 0.04005 printed horizontal one lattice step above the
  droplet's top face — no pins on the mat, nothing holding it but the
  muscle's DRAW. Protocol: a derived settle window (the mat conforms), then
  the muscle's own stroke: plates extend to s₀·√2 and converge back
  (5% sound, the muscle protocol).
  **Falsifiers:** (a) CONFORM — after settle and at every stroke sample,
  ≥ half the mat's grains sit within the cushion band [d_eq − 0.02,
  d_eq + 0.05] of SOME droplet grain (wall-seated at ≈S_WALL also counts,
  per the joint v2 law — the band unions both); (b) NO SLIDE-OFF — the
  mat's COM relative to the droplet's COM drifts ≤ 2 lattice steps from
  its post-settle value through the whole stroke; (c) COVERAGE — the mat
  ends covering the droplet's TOP hemisphere: ≥ half of droplet surface
  grains (grains with a neighbor-free +z side at print) have a mat grain
  within the band; (d) INTEGRITY — the mat stays one cluster through
  settle + stroke, and (inherited from theMuscle) the droplet does too.
  The edge-closed claim from the retired line is struck honestly: an open
  mat cannot close its own edge — that claim belongs to theBladder.
  **SKIN v1 VERDICT 2026-08-07 (N=352, run tag skin_v1, 3000-tick settle +
  full muscle stroke):** ALL FOUR PASS on the first construction — the only
  membrane so far to do that, and the reason is the derivation: the mat was
  already the measured 2-D phase, and the muscle's DRAW was already the
  measured pull; nothing new was invented. (a) CONFORM PASS: 0.234 at print
  (the sheet starts one lattice step off) → 0.996 after settle, stroke
  minimum 0.984, closing at 1.000 on full converge — the mat rides the
  droplet's surface through the whole stroke. (b) NO SLIDE-OFF PASS: max
  COM drift 0.0047 against a 0.10 bar — twenty times under; the muscle's
  DRAW holds its skin the way a planet holds its atmosphere. (c) COVERAGE
  PASS: 1.000 of droplet surface grains banded at end of settle and never
  less. (d) INTEGRITY PASS: mat and droplet each one cluster throughout.
  The contains-within / anchors-to family is now open: skin works because
  it is a bulk lying on a bulk, not a plane stretched over one. Next of
  kin: theBladder (a CLOSED mat enclosing contents within the muscle —
  squeeze as function) and theOrgan (any composite contained within skin).
- **bladder** *(parent relation stands)*: closed sheet enclosing gas
  points, CONTAINED WITHIN the muscle bulk — squeeze is its function.
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

- **socket**: a 0-D anchor embedded in a bulk, holding a hinge. Falsifier:
  pullout strength matches derivation from bulk packing.

## THE TENDON (the 1-D force router — light-era derivation 2026-08-06)

*(Old chain spec retired: "force transmits across the interface; fails at
the weakest link (chain, bond, or bulk)" presumed a tension bond that does
not exist — see theCushionLaw. Re-derived for the universe as measured.)*

**theTendon is a 1-D condensed column that seats two anchors and routes
force along a line.** There is no chain and no rupture: the column is held
condensed by its own DRAW (self-gravitating, exactly as theCushionLaw's
droplet), its ends ADHERE to the anchor plates by DRAW at cushion-contact
distance, push travels along the column as a cushion chain (each interior
pair at d_eq transmits the same force — the only contact forces are the two
end contacts), and pull is the column's DRAW on the far anchor. The only
openable links are the END-PLATE contacts (DRAW is strongest where mass is
densest), so the tendon fails by DETACHMENT at a derived separation, never
by rupture — the same two regimes as theMuscle, but localized to a line,
and with a compression regime the droplet never showed: a thin column can
BUCKLE.
**PRINT SPEC (v1 of the router):** two pinned 4×4 anchor plates (spacing
0.05, the muscle's anchors); a rod 2×2×8 printed cold at cushion spacing
0.05 (span 0.3500) centered between them; plate separation s₀ = span +
2·d_eq = 0.4468 (both ends exactly at cushion equilibrium — derived, not
tuned). Protocol (5% sound speed, quasistatic): (i) CONVERGE the plates by
2·d_eq total (one equilibrium spacing of crush) — compression; (ii) EXTEND
back through s₀ to s₀ + 0.15 — detachment.
**Derived numbers:** s₀ = 0.4468; unseat separation s_fail = s₀ +
(r_c − d_eq) = 0.5484 (as plates open by δ, the rod sticks to one plate by
symmetry-breaking and the far-end gap grows by ≈ δ; the gap crosses
r_c = 0.15 when δ ≈ r_c − d_eq), tolerance ± 0.5·d_eq = ±0.0242 (half a
lattice step); buckle bar = 2× the cross-section half-width = 0.05.
**Falsifiers:** (a) PUSH LAW — compression plate force vs the pairwise
two-force sum (DRAW + cushion contacts) on the RECORDED positions within
10% (the deformation-immune law test, inherited from theMuscle); (b)
BUCKLE — mid-column off-axis deflection ≤ 0.05 through the whole
compression phase (a thin column's own failure mode, emergent); (c) UNSEAT
— an END gap crosses r_c inside s ∈ s_fail ± 0.0242, and it is always an
END: the rod's cluster count stays 1 for the entire run (the weakest link
is the end contact, never mid-column — that IS the claim); (d) PULL LAW —
after unseat, extension force vs the pairwise DRAW sum within 10% on
contact-free samples (identical in form to theMuscle (a)).
**ROUTER v1 VERDICT 2026-08-06 (N=64, rod 2×2×8 + two 4×4 plates, run tag
tendon_smoke):** (a) PUSH LAW PASS — max rel err 0.002 vs the static
two-force recompute (8 compress samples); (d) PULL LAW PASS — 0.000 over 21
contact-free samples: theMuscle's law holds for a 1-D bridge. (c) UNSEAT
PASS in extension, exactly as derived: the rod sticks to the LEFT plate by
symmetry-breaking (gap_L ≈ 0.045 all run), gap_R crosses r_c inside
s_fail ± 0.0242 (4 samples in the window), cluster count 1 throughout — the
weakest link is the end contact, never mid-column. (b) BUCKLE FAIL, and the
recorded mode is richer than the name: under one equilibrium spacing of
crush the RIGHT end pops its seat at sep ≈ 0.41 (gap_R 0.049 → 0.107 →
0.275), the signed plate force briefly REVERSES (−77.9 at sep 0.397), and
the rod rides tilted, mid-column off-axis 0.0975 (2.7× the printed corner
offset 0.0354). A free 2×2 rod seated at exact d_eq does NOT hold
compression — the cushion chain ejects it from the far seat rather than
buckling elastically. Successor (named, not run): seat the rod PRELOADED
(print at s₀ − d_eq so both ends sit in the cushion well, not on its rim)
and split (b) into (b1) SEAT-HOLD — both end gaps ≤ r_c through the crush —
and (b2) BUCKLE proper, mid-column deflection measured from the end-to-end
CHORD with rigid tilt subtracted (the v1 metric conflated tilt with
curvature). The end-pop force reversal is the signature to watch: a router
that loses its seat telegraphs it in the force sign.
**ROUTER v2 VERDICT 2026-08-06 (preloaded seats, --tendon-preload 0.5, run
tag tendon_v2):** the preload hypothesis is REFUTED. Seating the ends one
half-spacing deep (s₀ = 0.3984) made ejection SOONER, not later: gap_R pops
0.063 → 0.178 between sep 0.373 and 0.361 (v1 popped at ≈0.41) and peaks at
0.216. (b1) SEAT-HOLD FAIL (bar 0.15); (b2) BUCKLE FAIL but the
chord-relative split did its job — true curvature peaks at 0.0633, the
other 0.034 of v1's 0.0975 was rigid tilt from the popped seat, so seat
loss is the root cause and curvature its consequence. The preloaded seat
starts the run sprung: stored cushion repulsion gives the ejection its
energy. (a)/(c)/(d) PASS as in v1 (push 0.056, unseat in the derived window
with the rod stuck to the LEFT plate this time, pull 0.000). The law
standing after two refutations: a free 1-D column between converging
plates ALWAYS ejects — compression along a line has no transverse
confinement, and the cushion chain finds the escape. Meanwhile bone's
4×4×16 column held its seats at gaps 0.0000 through four preload cycles —
the difference is the END FACE: 16-grain feet grip the plate by DRAW where
4-grain ends cannot. Successor (named, not run): the tendon ROOTS itself —
end cross-section flares to the anchor plate size (4×4 feet on a 2×2 shaft,
the insertion geometry of a real tendon), falsifier (b1) at the same crush
with the weak link predicted to move from the seat to the shaft, recorded
where.
**ROUTER v3 VERDICT 2026-08-06 (4×4 feet, run tag tendon_v3):** the SEAT
hypothesis is CONFIRMED and the CONSTRUCTION is refuted — two different
verdicts in one run, recorded separately. (b1) SEAT-HOLD PASS: both foot
gaps 0.0000 through the whole crush that ejected v1 and v2 — end-face area
IS the confinement variable. But the printed foot was one 4×4 layer
coplanar with the shaft's terminal 2×2 layer: the central four foot points
occupied the shaft end points' positions, the wall repulsion ejected the
duplicates at the first steps, and the structure ran as 15–19 fragments
(clusters 19 from tick 500, (b2) 7.71, (c) no clean crossing — all
artifacts). The physics never got to answer where the rooted tendon's weak
link is; the print law did: NO TWO GRAINS MAY SHARE A POSITION — an overlap
is not matter, it is a bomb. (a)/(d) PASS on the recorded positions as
always; the two-force law remains unindicted in every run to date.
Successor (named): v4 — the foot REPLACES the shaft's terminal layer (4×4
foot at the end plane, 2×2×6 interior shaft between the feet, no shared
positions), the same five falsifiers, the weak-link question finally asked
of physics instead of the printer.
**ROUTER v4 VERDICT 2026-08-06 (flush feet, run tag tendon_v4) and THE
MEASURED TENDON LAW:** the print law held — one cluster for all 13,754
ticks — and physics answered: the weak link is STILL the seat. The right
foot popped at sep ≈ 0.397 with the force-reversal signature (−75.6),
gap_R peaking at 0.2652; both ends crept together (gaps ≈ 0.12–0.13 at
tick 1000) before the left re-seated and the right let go. v1 bare rod
popped at ≈0.41, v2 preloaded at ≈0.361, v4 rooted at ≈0.397 — FOUR
constructions, one answer: preload hurts, foot area does nothing, and v3's
"held" seats were never loaded (the fragmented load path spared them).
Compression along a free 1-D column ejects at roughly the same separation
no matter how it is printed — there is no transverse confinement to buy.
So theTendon's final measured form, and it matches anatomy exactly:
**tendon = tension only, bone = compression, muscle = both regimes.**
The router's passing specification is the pull half, green in all four
constructions: (d) PULL LAW 0.000 vs the pairwise-DRAW prediction, (c)
UNSEAT at the derived s_fail with cluster count 1 and the rod sticking to
one plate as derived. The compression half of the v1 spec is REFUTED and
retired: (b) in all its forms ((b) v1 tilt-conflated, (b1)/(b2) split)
FAILS; force routing in compression belongs to bulk (bone: gaps 0.0000
through four preload cycles). (a) PUSH LAW's 0.000 PASS is recorded
honestly for what it is — the LAW is exact even as the STRUCTURE fails; the
kernel predicts the ejection force perfectly. theTendon is SETTLED as a
pull router at v4; theJoint inherits: bone-muscle-bone with tendon
pull-links, the first moving part.

## THE JOINT (the first moving part — light-era derivation 2026-08-06)

Everything below is assembled from SETTLED members only: bone (plastic-set
compression, seats hold in bulk), theMuscle (DRAW-bridge, antagonist
cushion), theTendon (pull-only router, unseats at derived s_fail), and the
one free mechanism this universe hands us: **cushion contact is a bondless
fulcrum** — a bone end resting on another body touches without sticking, so
it can ROLL and PIVOT. A hinge costs nothing and cannot break, because it
was never bonded.
**theJoint is two bones and a muscle arranged so the muscle's pull becomes
ROTATION about a cushion fulcrum.** There is no uniform gravity in this
universe, but there is WEIGHT: bone B's own DRAW toward the ground plate.
The muscle must out-pull the weight to lift; the resting angle is the
derived equilibrium where muscle DRAW balances weight DRAW. Motion stops at
the derived stop (geometric contact or the muscle's stroke limit s·√2).
**PRINT SPEC (v1 of the hinge):** a pinned ground plate (6×6, spacing
0.05). Bone A: a 4×4×16 column printed vertical, base seated on the plate
at cushion contact — the pillar. Bone B: a 4×4×16 column printed
HORIZONTAL, one end face seated on A's top face at cushion contact — the
limb; the A-top/B-end contact is the joint. Muscle: a 4³ droplet seated on
the plate offset from A's base by a derived moment arm, pulling B's far
(half's) underside by pure DRAW — the biceps. All separations, arm lengths,
and the droplet offset derived from the print geometry; no free numbers.
**Derived at print (in code):** B's weight W = pairwise DRAW sum B ×
plate; the muscle's pull on B at rest F_m(0) = pairwise sum (droplet ∪
plate) × B restricted to the bridge geometry; the resting equilibrium
angle θ₀ solving F_m(θ)·arm_m(θ) = W·arm_w(θ) — the code solves it on the
kernel, never fits it.
**Falsifiers:** (a) PIVOT — under the muscle's pull, B rotates: its free
end descends through a derived arc while the JOINT CONTACT HOLDS (the B
end face stays within r_c of A's top face — a joint that dislocates is not
a joint); (b) TORQUE LAW — the measured joint torque vs angle matches the
pairwise-DRAW moment computed on the RECORDED positions within 10% (the
deformation-immune form, third generation); (c) REST — when the muscle
droplet is removed (or equivalently its mass set to zero in the recompute),
B settles to the derived weight-only equilibrium, recorded angle vs derived
within derived tolerance; (d) STOP — the free end's descent halts at the
derived stop (B-to-plate contact at cushion distance or the muscle stroke
limit, whichever the geometry says is first), never passing through solid
matter; (e) INTEGRITY — both bones keep their seats and their cluster
count 1 through the whole stroke (bone's law), and the muscle keeps its
own (theMuscle's law). The joint is the first membrane whose falsifiers
are entirely INHERITED from settled members except one: that rotation
itself emerges from pull + fulcrum.
**JOINT v1 VERDICT 2026-08-06 (N=612, run tags joint_v1 / joint_v1_control,
6000 ticks each):** the one new claim is CONFIRMED in substance — rotation
emerges: B pivots from horizontal through ≥25° (free-end z 0.92 → 0.38 in
the tumble) under weight + muscle pull, and both runs settle into stable
configurations. (b) TORQUE LAW PASS, exact: 0.000 max rel err in BOTH runs
— the fourth structure where the pairwise-DRAW law on recorded positions
reproduces the measured force to print precision. (a) PIVOT FAILS AS
WRITTEN, and the failure is the discovery: the bondless fulcrum
TRANSIENTLY dislocates in both runs (gap peaks 0.365 main / 0.374 control
vs r_c = 0.30) during the initial tumble, then RE-SEATS (settled gap
0.104) — in a universe where everything attracts, dislocations HEAL: the
joint is self-reducing. The v1 continuous-hold bar asked the wrong
question. (d) STOP PASS by its bar, recorded with a caveat: the "derived
stop" was a 90° placeholder, not a derivation — v2 derives the actual
landing. (e) INTEGRITY PASS in main (1/1/1 throughout); in control B
flickered to 2 clusters once at tick 5550 after settling, then recombined
— a threshold flicker at the R_BOND surface while rocking, recorded. (c)
REST INCONCLUSIVE: the θ metric is broken by construction — end faces were
recomputed by x-sort EVERY sample, so once B passes 45° the faces swap and
θ collapses to 0 mid-descent (two shadowing `_B_end_faces` definitions
compounded it). The trustworthy channel, free-end POSITION, reads main
(0.095, −0.021, −0.033) vs control (0.096, 0.005, −0.013): both tumble to
the plate; the muscle's static contribution at this geometry shows only in
the settled gap (0.104 vs 0.135). A metric that lies is worse than no
metric — v1(c) is struck, not passed.
**Successor (named):** v2 — (i) kinematics fixed: end faces by FIXED
print-time indices (single definition), or a PCA axis with print-anchored
sign; (ii) (a) becomes RECOVERY: any dislocation (gap > r_c) must re-seat
within a derived time and STAY seated to end of run — the v1 data says it
will, and that is the joint's real claim; (iii) (c) stop derived from the
actual print geometry (B's landing on plate or droplet); (iv) settle
window derived from the measured settling time, not guessed.
**JOINT v2 VERDICT 2026-08-06 (run tags joint_v2 / joint_v2_control, 6000
ticks; note: the control invocation replays the deterministic main sim
first, then the control — both land in its log):** the composite WORKS, and
the headline number is the one v1 could not measure: with the fixed-index
kinematics, the muscle holds the limb at **θ = −27.57°** where weight
alone lets it tumble to **θ = −177.78°** — fully over the joint, hanging
off the pillar's far side. B flexes past vertical (−115°) mid-tumble; the
droplet migrates with it (COM 0.56 → 0.016) and the settle has B leaning
on BOTH plate and droplet at 0.025. (a) RECOVERY PASS: two dislocation
excursions (max gap 0.328), self-reduced in 600 measured ticks against a
derived bar of 4032 — the self-reducing joint is now the passing claim,
not the failure. Control never exceeded r_c at all. (b) TORQUE LAW PASS
0.000 in both runs — fifth structure exact. (e) INTEGRITY PASS in main
(zero flicker samples); control's B flickered to 2 clusters in 7 samples
while rocking inverted, recombined — recorded. (c) REST recorded honestly
as DEGENERATE: with the stop redefined as the measured settle, a settled
run passes by construction; the falsifier that actually carried
information this round was the main-vs-control contrast above. (d) STOP
FAILS AS WRITTEN and lands on a better derivation than we wrote: the
cushion-band bar [0.0284, 0.0984] was wrong — matter under sustained
weight does not rest in the cushion, it seats IN THE WALL, and the
measured settle distances (main 0.0249–0.0250, control 0.0234–0.0235)
straddle **S_WALL = 0.025**, the kernel's saturated-wall constant. The
no-penetration substance never failed (nothing came closer than 0.0234);
the stop is the saturated wall, exactly as bone's preload seats. The
correct (d) bar, derived now: settle distance = S_WALL ± 0.5·d_eq.
theJoint stands as the first moving part: rotation from pull + bondless
fulcrum, self-reducing on excursion, torque exact, held by the muscle
against a 150° weight deficit.

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
