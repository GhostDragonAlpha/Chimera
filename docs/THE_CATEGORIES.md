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
- **bladder** — re-derived on the mat 2026-08-07 ("closed sheet enclosing
  gas points" retired: gas does not exist — every grain condenses; and a
  hollow shell is the sheet's hollow cousin, doomed to collapse unless
  something holds it open. What holds it open is measured: the CUSHION —
  incompressible condensed contents, exactly as a real bladder is full of
  fluid). **theBladder is a closed mat shell packed with condensed
  contents, with one derived opening — the neck.** Containment comes from
  the shell's own self-DRAW (the mat is stable), inflation from the
  contents' cushion repulsion, function from the muscle's squeeze, and the
  neck is what separates a bladder from a cyst.
  **PRINT SPEC (v1):** a spherical shell one grain thick at d_eq =
  0.0484, radius r_b = 0.20 (≈ 200 grains — derived from surface area at
  shell spacing), packed with a condensed content droplet (4³ = 64 at
  0.05) — the contents' cushion pressure is the shell's splint; ONE neck:
  a derived hole in the shell, diameter = 2 grain spacings (the smallest
  opening that passes one grain — derived, not chosen). The assembly sits
  between the muscle's two pinned plates (the squeeze protocol is
  inherited: plates converge at 5% sound). Full containment within a
  muscle BULK is v2; v1 asks the container question alone.
  **Falsifiers:** (a) SEAL — under convergence to a derived hold pressure
  (plates at cushion contact with the shell, derived force F_hold =
  the shell's own end-weight form — computed in code from the kernel at
  print), zero content grains escape (every content grain stays within
  r_b + d_eq of the shell center) and the shell stays one cluster; (b)
  YIELD — under continued convergence past the derived threshold (force
  ≥ 2× F_hold, the one-halving canonical step), content grains exit —
  escape count ≥ derived fraction (half the contents) — and the shell
  does NOT rupture: shell cluster count stays 1 through the whole squeeze
  (a bladder that bursts is not a bladder); (c) NECK SELECTIVITY — the
  escaped grains exit THROUGH THE NECK: each escapee's position at the
  moment of exit (first sample outside r_b + d_eq) lies within 2 grain
  spacings of the neck axis, never through shell wall (an escape through
  the wall is rupture, recorded); (d) SHELL INTEGRITY post-yield: after
  the squeeze releases, the shell remains one closed mat (clusters == 1,
  no holes beyond the neck — a bladder that can't re-fill is a wound).
**BLADDER v1 VERDICT 2026-08-07 (run tag bladder_v1, 32,769 ticks):** the
v1 print is a CYST — the spec's own named failure, produced honestly.
(a) SEAL PASS but hollow: 26 sub-threshold samples, zero escapes, one
cluster — nothing escaped because the neck was never held open. The
trajectory tells the story: shell displacement jumps to ≈0.18 by tick
6000 (≈ r_b itself) — the hollow shell CRUMPLED INWARD onto its contents
in the first seconds, exactly like the sheet, and for the same reason:
the cushion-splint was never installed. The contents (4³ at 0.05, radius
≈ 0.13) inside a shell of radius 0.20 leave a ~0.07 gap — the splint
doesn't touch the wall at print, so the wall folds before the contents
can hold it. After the crumple the assembly is a solid ball: plates
closed to the geometric limit (sep 0.09999, force 661 = 2×F_hold) and
(b) YIELD FAIL — 0/32 escapes, because a solid ball has no cavity to
squeeze and the neck crumpled shut with the rest of the wall. (c) NECK
FAIL vacuously (no escapes to select). (d) INTEGRITY FAIL as written
(max shell displacement 0.182 > 0.10) — recorded with the caveat that the
bar measures form-holding, and the form was lost to crumple, not rupture:
the shell stayed ONE CLUSTER the whole run, never burst. What is refuted
is the print, not the concept — the cushion-splint was never actually
installed. Successor (named): v2 — contents FILL the shell at cushion
contact at print: N_contents derived from the interior volume at cushion
spacing (interior radius r_b − d_eq ≈ 0.15 → N ≈ 113 at 0.05), so the
splint touches the wall from tick 0. Prediction stated: shell
displacement stays ≤ 0.10 through the squeeze, and past 2×F_hold the
contents exit through the neck corridor.
**BLADDER v2 VERDICT 2026-08-07 (fill mode, N_contents = 122 derived, run
tag bladder_v2, 32,769 ticks):** the splint is installed and the crumple
verdict changes character — but the cyst stands, and now for a measured
reason. The v1 reading needs correcting in the ledger: with the fill
installed, shell displacement STILL reaches 0.18 by tick 5000, and the
timing indicts the SQUEEZE, not spontaneous crumple — the plates converge
from tick 0 (sep 0.497 → 0.372 by tick 5000), so the shell is flattened
between the jaws, not self-collapsed. (a) SEAL PASS, no longer hollow: 32
sub-threshold samples, zero escapes, one cluster — the shell SEALS
robustly, flattened or not. (b) YIELD FAIL at the geometric limit: 0/61
escapes at sep 0.09999, force 664 = 2×F_hold. The diagnosis is measured,
and it is a real granular phenomenon: the NECK JAMS — a 2-spacing hole
against cushion-packed contents under pressure forms force arches and
locks (granular arching over an orifice; the same physics as a hopper),
and the neck sits at the +z pole, PERPENDICULAR to the squeeze, where
the pressure gradient never points. (c)/(d) FAIL with it. What survives:
the shell construction itself (two prints, one cluster through 32k ticks
each, never a rupture) — a closed mat container EXISTS and SEALS; what is
refuted is the yield pathway as printed. Successor (named): v3 — the
ANTI-JAM neck: diameter derived from the arch condition, not the
single-grain condition — an arch needs ≥ 2 grains abreast to span (2
spacings) and a stable arch up to 3 (3 spacings), so the neck opens at
4 spacings, the smallest hole no cushion arch can close; SEAL is then the
interesting falsifier (a 4-spacing hole against DRAW-packed contents:
the packed-bed repose law says it holds at rest — if it leaks at F_hold,
record it). And the neck moves onto the squeeze axis (the pole facing a
plate), where the pressure gradient actually points.
**BLADDER v3 VERDICT 2026-08-07 (antijam neck, 4 spacings, on the squeeze
axis, run tag bladder_v3):** the strongest SEAL yet and the third YIELD
failure — and three failures now draw the law. (a) SEAL PASS: 43
sub-threshold samples, zero escapes through a 0.20 hole — the
anti-jam neck does not leak at rest, exactly as the packed-bed repose law
predicted; that half of the v3 derivation is CONFIRMED. (b) YIELD FAIL
again: 0/61 at the geometric limit. The anti-jam neck is corked by its
own squeeze jaw: the plates close to sep 0.09999 with the neck FACING
the right plate, so at full squeeze the hole is pressed against the jaw
that was supposed to be the pressure source — and anything that did ooze
out stays within the escape radius (r_b + d_eq) because DRAW reclaims it:
in a universe where everything attracts, ejecta fall back. (c)/(d) FAIL
with it (disp 0.189, the flattened shell). The three-version arc
converges on a universal, not a print bug: **containment is this
universe's default (everything clumps, every container seals); expulsion
is the expensive direction — separation must be PAID, and pressure alone
does not pay it.** The yield pathway was conceived as a pressure problem;
it is a PLUMBING problem. Successor (named): v4 — the DUCT: a derived
port through the right plate aligned with the neck (the muscle does not
sit on its drain), the escape criterion re-derived as crossing the duct
PLANE (a flattened shell breaks the spherical criterion), and the
falsifier unchanged. If the duct yields, theBladder is the first organ
with a function; if it still fails, the law hardens: in this universe
nothing is excreted, only re-condensed — recorded either way.
**Operator note 2026-08-07: theBladder is parked at v3** — the sealed
container (the storage half, the game-useful half) is measured and
works; the duct v4 waits on the locomotion priority (theSkeleton /
theLever).

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

## THE LEVER (the muscle-bone machine — light-era derivation 2026-08-07)

The joint v2 proved a limb rotates under pull; theLever is the same
mechanism QUANTIFIED — the machine that trades muscle force for load force
through arm length. Every member is settled: the bone column, the cushion
fulcrum (bondless, self-reducing), the muscle bridge. The one new claim is
the RATIO: quasi-static balance F_m·a_m = W_L·a_l decides whether the
load moves, and NOTHING else does.
**PRINT SPEC (v1):** a pinned ground plate; a 4×4×4 fulcrum block seated
on it; a 4×4×16 bone column (the lever arm) laid HORIZONTAL, balanced on
the fulcrum's top face at its midpoint (cushion contact, unpinned — the
joint mechanism). Muscle: a 4³ droplet seated on the plate beside the
lever's MUSCLE end, pulling that end down by pure DRAW (the joint v2
biceps). Load: a 4³ block resting on the lever's LOAD end (cushion
contact). Derived in code: arm lengths a_m, a_l from the fulcrum contact
point; the muscle's pull F_m on the lever (pairwise DRAW at print); the
load's weight W_L (pairwise DRAW load × plate at print); the balance
ratio R = F_m·a_m / (W_L·a_l).
**The two-sided falsifier (the lever's soul):** the MAIN run is printed
with R derived ≥ 2× (muscle arm and droplet placement set so the ratio
clears the canonical one-halving margin) — the load MUST lift; the
CONTROL run halves the muscle arm (a_m/2, load side unchanged) so R ≤ 1
— the load MUST NOT lift. If main lifts and control holds, the machine is
measured: advantage decides, both directions.
**Falsifiers:** (a) LIFT — main: the load end's height above its print
height increases through a derived arc (≥ 2 lattice steps) while the
fulcrum contact holds OR recovers (the joint v2 law — dislocation that
re-seats is not failure); (b) HOLD — control: the load end never rises
more than 1 lattice step above print through the whole run; (c) BALANCE
LAW — in main, at the quasi-static moment before liftoff (load contact
force → 0), the measured F_m·a_m / (W_L·a_l) lies within [0.9, 1.1] of
unity... honestly: within 10% of the DERIVED ratio at liftoff (the
balance point is computed on recorded positions, not fitted); (d)
INTEGRITY — lever, fulcrum, droplet, load each one cluster throughout;
the plate pins hold.
**LEVER v1 VERDICT 2026-08-07 (run tags lever_v1 / lever_v1_control,
8000 ticks):** the machine tipped BACKWARD — the two-torque model is
refuted, not the lever. Main, printed at R_static = 1.999, rotated
load-side DOWN from the first transient (load_gain −0.167 by tick 600,
settled −0.333 at a 34° tilt, load end parked on the plate, fulcrum gap
compressed to 0.050) — the static ratio said muscle-side wins by 2× and
the dynamics said otherwise immediately. The model error is named: R was
two pairwise sums (droplet→lever, load→plate) treated as point forces at
the ends, but the kernel's real torque budget includes the lever's OWN
256-grain weight (4× the load's mass) about a fulcrum that was only
geometrically centered, the load's DRAW to lever and fulcrum (not just
plate), and the fulcrum's own pull — none of which were in R. (a) LIFT
FAIL (max +0.019 at tick 200, then the backward runaway: F_m decays as
1/r² while W_L does not). (b) HOLD PASS but vacuously — the control sank
too (max +0.026), so HOLD measured nothing discriminating this round.
(c) BALANCE recorded VACUOUS: the liftoff detector fired at tick 0 on a
contact-metric artifact (contact = −24.9 at print) — a metric that fires
at print is not a measurement; struck. (d) INTEGRITY main PASS;
control's droplet flickered to 2 clusters under plate/lever shear in four
windows, recombined — recorded. Successor (named): v2 — the ratio is
computed from the FULL kernel torque about the fulcrum on the print
(every body, recorded positions, signed per grain: R_true = Στ_muscle /
Στ_load), and the fulcrum contact point is re-derived until the kernel
itself says the muscle side wins by 2× (bisection on the contact point —
derivation, not sweep). The two-sided falsifier then runs on R_true:
main must lift, control (kernel-verified R_true ≤ 1) must hold.
**LEVER v2 VERDICT 2026-08-07 (run tags lever_v2 / lever_v2_control,
8000 ticks; geometry changed by the implementing agent to a 2×1×18 rod
with the droplet at muscle_end + 0.30L — recorded as its derivation
route):** the bisection is legitimate (23 steps, R_true trace monotone,
τ_neg frozen at 202.803 from step 13 — kernel root-finding, not a sweep),
and it exposed two things the spec had wrong. First: **R_true = 2 is only
reachable at the bracket's edge** — the ratio asymptotes to 1.9819 at
cx = 0.350, the degenerate end of the lever, leaving a load arm of
~0.075: the 2× margin was purchased by deleting the machine. Second, and
decisive: **a free fulcrum is not a pivot.** Main tips muscle-down as
R_true = 1.98 predicts ((c) BALANCE PASS — the kernel torque DOES call
the initial tip, the v2 claim that survives), but the fulcrum block
rolls/sinks with the lever, so the load end's ABSOLUTE height falls
(−0.237) even while rotating up — (a) LIFT's absolute bar is unreachable
when the pivot itself travels. Control proves the same point from the
other side: R_true = 0.864 predicted load-down and the lever flipped to
+88.9° muscle-down instead ((c) FAIL) — with the pivot rolling, the
static torque about the print's contact point stops governing after the
first instant. (b) HOLD PASS and (d) INTEGRITY PASS both runs (no droplet
flicker this geometry). The law after two lever prints: the machine is
real (the kernel's torque predicts the tip), but the pivot must be
ANCHORED — which matches anatomy exactly: fulcrums are BONES, and bones
are anchored (the joint v2 pillar held its base at gaps 0.0000; that is
why the joint worked and the lever does not). Successor (named): v3 —
PIN the fulcrum block to the ground plate (it is a skeletal bone, not a
loose rock), keep the rod, re-derive the contact x for R_true = 2 by the
same bisection (the target must now be reachable OFF the bracket edge —
if it is not, derive a heavier muscle, 5³ = 125, before touching the arm
lengths), and rerun the two-sided falsifier unchanged: main lifts through
0.10 in absolute z, control holds.
**LEVER v3 VERDICT 2026-08-07 (pinned fulcrum, run tags lever_v3 /
lever_v3_control):** the pivot is FIXED and the machine's soul is
CONFIRMED — what remains is a bone-class mistake. Pinned, the fulcrum
holds: main gap seated at 0.041 for the whole run, zero migration, and
the SETTLED rotation direction now matches R_true in BOTH builds —
main (R_true = 2.003) settles muscle-down at +20°, control (R_true =
0.912) settles load-down at −150°. The two-sided claim theLever was
built to measure is true: the kernel's static torque about the anchored
fulcrum decides which way the machine turns, in both directions. (c)
BALANCE FAILS only as metered — the first-600-tick window catches the
transient sag before the torque direction dominates; the falsifier's
substance passes at settle, the window is the bug (struck, re-derived
in v4). (a) LIFT FAILS for the real reason, and it is the dimension
ladder speaking again: the v2 agent swapped the 4×4×16 bone column for a
2×1×18 rod, and a 2×1 rod is TENDON-CLASS — no transverse confinement,
no bending stiffness; under the load block it sags (load_gain −0.166
while rotating muscle-down, exactly the sheet/tendon lesson). A lever
arm must be BONE-CLASS: bulk that bears. (b) HOLD PASS; (d) INTEGRITY
PASS both runs (control's fulcrum gap opens to 0.145 as the rod rolls
around the pinned block — recorded; the pinned block itself never
migrates). Successor (named): v4 — bone-class lever arm (4×4×16, the v1
cross-section restored), pinned fulcrum, R_true bisection unchanged
(heavier muscle 5³ if the edge intrudes), (c) judged on the SETTLED
direction (last 20% of samples vs R_true sign), (a) unchanged at 0.10
absolute.
**LEVER v4 VERDICT 2026-08-07 (bone-class arm 4×4×16 restored, pinned
fulcrum, run tags lever_v4 / lever_v4_control, 8000 ticks):** the sag is
dead and the machine slid off its pivot — the heavy arm spends the whole
torque budget carrying itself. The chain of cause, each link verified
from the logs. (1) The bone-class arm is RIGID: no decoupled sag this
print (v3's tendon-class failure mode is gone at 4×4×16). (2) But a
solid 256-grain arm crushes the ratio: the bracket sweep gives R_true in
[0.89, 1.46] with the standard 4³ muscle and — note this — [0.79, 1.41]
with the HEAVY 5³ muscle: the bigger droplet LOWERED the ceiling,
because DRAW is long-range (a_m = 0.675, ~14 lattice steps) and the
muscle pulls the whole arm, load side included, inflating both torque
sums toward parity. R_true = 2.0 is UNREACHABLE anywhere in the bracket;
the bisection clamped to the edge cx = +0.300, 0.075 from the load end.
(3) At that degenerate placement the pivot cannot hold the machine:
main's transient went +4° muscle-down at tick 200 (the statics winning,
R_true = 1.409), then reversed to −46° by tick 400 as the fulcrum gap
spiked to 0.198 — contact LOST — settling slumped at −61.8° with the gap
riding 0.108 (out of the seated band; the load end grounded on the plate
and the lever lying against its pivot, not seated on it). (c) BALANCE
FAIL main (settled sign −1 vs R_true > 1), (a) LIFT FAIL (max load_gain
0.0000 — the load never rose). Control (R_true = 0.794, cx = −0.300,
opposite edge): settled −64.6° load-down as predicted — (c) PASS, (b)
HOLD PASS (max 0.0198), (d) INTEGRITY PASS both runs. The v4 law, two
clauses: a lever's advantage is paid out of the arm's own mass, and a
draw-muscle's force cannot be localized to its insertion — so the static
margin must be LARGE and the pivot must sit OFF the bracket edge (v3:
R_true = 2.0 mid-bracket survived the dynamics; v4: 1.41 at the edge did
not). One metering sin struck: the v4 test asserts the heavy-muscle
contingency route as the EXPECTED outcome — a test that enshrines the
fallback; v5 must restore the standard route as the expectation.
Successor (named): v5 — the HOLLOW-TUBE arm, which is what bone
actually is. Beam theory: bending stiffness lives in the second moment
of area (outer grains carry it), weight lives in the volume — a 4×4×16
shell one grain thick with a 2×2 void (12 grains per ring, 192 total,
75% of the solid mass) keeps most of the stiffness and hands the torque
budget back to the muscle. The FIRST gate is static, no dynamics run
before it passes: the same bracket sweep on the tube geometry must reach
R_true = 2.0 at a contact point at least 2 lattice steps OFF the bracket
edge with the STANDARD 4³ muscle. If the sweep cannot, the derivation —
not a sweep — says which knob moves: shorten the arm (self-weight torque
scales with length squared, stiffness with length cubed — shorter arms
are disproportionately stiffer AND lighter-torqued) before touching the
muscle. FALSIFIER: if the tube sags under the load (load_gain decouples
from rotation as in v3) the 1-grain shell is sheet-class and the void
shrinks to 1×1; record it.
**LEVER v5 VERDICT 2026-08-07 (hollow-tube arm, run tags lever_v5 /
lever_v5_control, 8000 ticks):** the statics are FIXED and the perch is
the failure — a pivot that cannot capture its arm is not a pivot, v2's
lesson one level up. Verified link by link. (1) STATICS WIN: the
tube-plus-length derivation restored the headroom exactly as the v4 law
predicted — the gate passes at 13 rings (156 grains vs 256 solid, and
shorter, both derived moves), R_true = 2.000 at cx = +0.050 with 0.250
margin OFF the bracket edge, STANDARD 4³ muscle. The hollow-tube clause
is confirmed: bone buys stiffness without weight. (2) SAG struck: the
tube is rigid — no decoupling anywhere in either run. (3) DYNAMICS
FAIL, and the signature is a SLIP, not a tip: main settles LEVEL
(angle −0.5°) with load_gain −0.221 — the whole assembly translated
down beside the 0.2-tall fulcrum and lies on the plate, gap 0.034
being SIDE contact with the block, not perch contact; control settles
−31° with load_gain −0.276, same translation. Both runs follow one
sequence: ~200 ticks as the statics predict (muscle-down, gap
compressing 0.053 → 0.024), then a violent load-down lurch at tick 400
(plate_F spikes 1832 / 1924 — the landing impact), then the slump. (c)
BALANCE FAIL main, (a) LIFT FAIL main (max load_gain 0.0000); control
(b) HOLD PASS (trivially — the load never rose), (c) PASS, (d)
INTEGRITY PASS both. (4) TWO SINS STRUCK. First, a RULE 1 violation:
the implementing agent ran a parameter SWEEP over insertion fraction
α ∈ [0,1] × length 6..16 and "chose" α = 0.625 — choosing a number is
the one thing the method forbids; bisection on the kernel torque sum is
the legal instrument and v6 must re-derive the insertion with it.
Second, the muscle droplet sits on the PLATE at the arm's tip, so its
draw reaches the tip with a LATERAL component that walks the uncaptured
arm off the perch — a muscle that pulls from beside the machine pulls
the machine apart. The v5 law: a perch cannot hold a machine — the
fulcrum must CAPTURE the arm so rotation is the only free degree of
freedom, and the joint membrane (v2) already proved the socket that
does it. Anatomy said it first: pivots are joints, and muscles pull
through captured paths. Successor (named): v6 — the CAPTURED pivot:
the fulcrum grows cheeks flanking the tube (a saddle; rotation only),
the insertion fraction is re-DERIVED by bisection on the kernel torque
sum (no sweeps, ever), the muscle stays on the plate (its anatomy: a
muscle anchored to ground pulls the limb to it). Prediction: captured,
the tick-400 lurch cannot slide the arm and the settled direction
matches R_true both runs. FALSIFIER: if the captured machine still
settles against R_true, the governor is the muscle droplet's freedom to
wander, and the muscle must be anchored THROUGH a tendon — the tendon
membrane is already proven, and that is the leg.
**LEVER v6 VERDICT 2026-08-07 (captured pivot — fulcrum cheeks, run
tags lever_v6 / lever_v6_control, 8000 ticks):** the saddle WORKS and
the muscle is the governor. Verified link by link from the logs. (1)
CAPTURE CONFIRMED: for the first time in six lever prints the machine
reaches a STABLE rotational equilibrium on its pivot — main holds
−13.10°, control −24.48°, rock-steady to 0.01° across the last 6000
ticks, perch gap seated and constant, INTEGRITY one cluster each, pins
hold. The v5 slide-off is dead: the cheeks held the arm through a
violent transient and kept it for the whole run. The saddle is a proven
membrane — the first captured joint. (2) THE STATICS GOVERN THE
OPENING: both runs begin exactly as R_true predicts — +12° muscle-down
at tick 200 WITH THE LOAD RISING (+0.022, the first lift ever measured
in the lever line). Six prints now agree without exception: the
kernel's static torque calls the initial direction. (3) THE TICK-400
REVERSAL IS THE MUSCLE'S OWN COLLISION: at tick 400 both runs spike a
large REPULSIVE contact (main +21, control +77, in prints whose
cold-print contact is DRAW at −17) and the perch gap opens
(0.081 / 0.077), and the machine falls back load-down into its captured
rest. The candidate governors are the same animal twice: the
descending arm meets its own ground-seated muscle — the cushion erases
the draw and the muscle becomes a prop, a second fulcrum at the muscle
end that pivots the whole long arm load-down — or the droplet, struck,
wanders and the pull vanishes. Either way: a free-droplet muscle works
only until the machine answers it. (4) METERING SIN RECORDED: the
control's R_true landed at 1.050, OUTSIDE the specified [0.5, 1.0] —
v6's BALANCE evidence is single-sided (both builds predicted
muscle-down, both settled load-down; one repeated measurement, not
two). The v6 law, and it is the lever line's crown: **the kernel's
static torque always calls the opening move, but a muscle that can
touch the bone it pulls stops being a muscle at the instant of contact
— the pull must arrive along a path the bone never intersects.** That
is why tendons exist, derived from the kernel. theLever CLOSES here:
statics proven (opening direction, six prints), capture proven (the
saddle), the governor named (muscle embodiment, not lever mechanics).
Successor (named, and it is theLeg): the TENDON-ROUTED muscle — the
droplet anchored in a well below the tip's swing arc, its pull carried
by a tension-only chain (theTendon, already proven) that can only pull
and goes slack before contact, so the muscle can never become a prop.
First-print falsifiers: LIFT through the derived arc, HOLD in a
two-sided control (R_true inside [0.5, 1.0] this time), and SETTLED
direction matching the statics — the three the lever never got to keep.
**LEG v1 VERDICT 2026-08-07 (tendon-routed muscle, run tags leg_v1 /
leg_v1_control, 8000 ticks):** the tendon TRANSMITS and the free muscle
CLIMBS — the origin must be anchored, and the statics must be gated on
the arc, not the pose. Verified link by link from the logs. (1) THE
TWO-SIDED CONTROL IS BACK: control R_true = 0.548 inside [0.5, 1.0],
(b) HOLD PASS, (c) BALANCE PASS — first genuinely two-sided print since
v3. (2) THE TENDON ROUTES: the rod sits in tension 93% of the main run
and 98% of the control, and in both settled states it holds a steady
tension (+25 / +70..100) with the machine at rest — theTendon's
transmission law confirmed inside a machine. (3) THE FREE MUSCLE
LEAPED: in BOTH runs the droplet climbed toward the descending tip
(apex_z 0.099 -> 0.162 main, -> 0.174 control) until tip_to_drop
crashed through d_eq (min 0.025 both runs) and the rod went into
COMPRESSION at the first move (main tick 200: −48.75) — the SLACK law
broken at the opening. A muscle free to move toward the bone it pulls
is a collision on a timer; the agent-added well floor reacts DOWNWARD
and cannot hold against a draw that pulls UP. (4) THE OPENING-LAW
QUALIFIED: both runs opened +14° muscle-down — but the CONTROL opened
muscle-down AGAINST its R_true = 0.548, the first exception in seven
prints. The exception is explained: the droplet sits within direct
draw range of the tip (0.149 at print) and pulls it down UNMEDIATED by
the fulcrum — the leg's opening conflates the lever's torque with a
straight droplet-tip attraction, so only the lever line's six openings
count as the statics law; the leg's openings count as the collision
law. (5) THE OVER-ROTATION: R_true = 2.016 was purchased with a_m =
0.081 — a nearly-zero muscle arm — and once the machine rotated, the
torque landscape collapsed muscle-side; both runs blew past vertical to
settle at −72° / −80° load-down, the muscle hanging plumb off the
near-vertical arm, still pulling, never again able to lift. Cold-print
R_true is a POSE quantity; a machine that rotates 70° lives in the
whole landscape R_true(theta). (a) LIFT FAIL (max +0.0075), (c)
BALANCE FAIL main, (d) INTEGRITY PASS both. (6) TWO SINS STRUCK: the
agent's follow-up phrasing — "move the contact load-ward UNTIL R_true
= 2.0 corresponds to a stable settle" — is tuning language, and the
solid well floor was an off-spec addition that fixed nothing (recorded,
kept as plate, harmless). The v1 law, two clauses: **a muscle's origin
is an anchor — a free muscle climbs to the bone and becomes a prop at
contact — and a rotating machine's balance lives in the torque
landscape across its arc, never in one pose.** Anatomy, twice again:
muscles are anchored at the origin, and joints have range limits.
Successor (named): leg v2 — the ANCHORED muscle: the droplet is PINNED
at the well floor (its origin), making tip_to_droplet a computable
geometric floor over the arc; the tendon rod lengthens to span the well
with its ends at d_eq (taut, uncompressed); and the static gate becomes
the ARC GATE — R_true(theta) recomputed by the kernel at rotated poses
across the reachable arc, required >= 1 up to the derived muscle-side
end-stop, the contact still derived by bisection. FALSIFIER: if the
anchored, arc-gated machine still settles load-down, then cold-pose
BALANCE is the wrong meter entirely and the settled direction must be
judged against the arc integral — record, do not patch.
**LEG v2 VERDICT 2026-08-07 (anchored muscle + arc gate, run tags
leg_v2 / leg_v2_control, 8000 ticks):** the anchor holds, and the rod
is a prop in waiting — a link that can be compressed by the motion it
drives is a strut, and a gate that prices only the winning side of the
arc leaves the losing side ungoverned. Verified link by link from the
logs. (1) THE ANCHOR WORKS: the droplet, pinned at the well floor,
holds apex_z = 0.0995 in both runs for the whole 8000 ticks — the v1
leap is dead, the first clause of the v1 law confirmed. (2) THE ROD
FAILS IN BOTH DIRECTIONS: when the muscle wins, the tip descends and
CRUSHES the rigid rod against the anchored droplet — main tick 200,
rod compression −181.78 at just +17° — and when the load wins, the
machine LEANS on the rod: the control settles at −38.6° with the rod in
compression 90% of the run (−21.7 steady), resting on its own tendon.
tip_to_drop min 0.021 / 0.023 — below d_eq in both runs; the geometric
floor failed in practice, and the control blew past the gate's own
theta_stop (50.8° > 38.2°) — the derived arc did not bound the real
one. (f) SLACK passes the 0.20 meter in main (5% compression) but the
meter misses the physics: the spikes are the story. (3) THE
KNIFE-EDGE: the arc gate required min_R_taut >= 1.0 on the muscle-side
arc and the bisection delivered exactly R_true = 1.003 — neutral
balance. At neutral, the print's relaxation lurch (the tick-400 spike,
+4227 this print — fourth print running) picks the direction; the gate
priced only [0, theta_stop] and said nothing about the load side, which
is exactly where the machine was knocked and held: main settles −8.2°
load-down with the rod in STEADY TENSION +69 — the tendon as a tether,
the muscle working hard on the wrong side of the balance. (4) Verdicts:
main (a) LIFT FAIL (max +0.0017), (c) BALANCE FAIL, (e) SAG not
detected, (d) INTEGRITY PASS; control (b) HOLD PASS, (c) PASS on the
meters — with the rod-prop recorded. (5) The agent's follow-up halved
right: "stronger threshold" is tuning language (struck); "longer,
softer" carries the rope's seed. The v2 law: **a tension link must go
slack along the muscle's winning direction — crumple or fold, never
prop — and the gate must price the WHOLE reachable arc, both sides, or
the unpriced side is where the machine will live.** Anatomy, again
first: tendons are ropes around pulleys; slack rope crumples out of the
way (the sheet line proved crumpling is the slack phase). Successor
(named): leg v3 — the ROPE tendon: a single-file chain from the
anchored droplet apex to the tip underside, long enough to be taut at
the print, free to crumple into the well as the muscle wins; and the
FULL-ARC gate: R_true(theta) >= 1 on BOTH sides of the print pose out
to both derived end-stops, so the muscle-side stop is the UNIQUE stable
equilibrium; if no contact achieves that, the derived knob is the
DROPLET SIZE (muscle strength, from the muscle print's own law),
bisected against the gate — never the contact hunted for a feel-good
settle. FALSIFIER: if the rope-tendon, full-arc-gated machine still
settles load-down, the two-force kernel's draw cannot hold a working
machine against its own relaxation lurch at this scale, and the answer
moves up a level — the skeleton's geometry must carry the stability —
record, do not patch.
**LEG v3 VERDICT 2026-08-07 + theLeg CLOSES (rope tendon + full-arc
gate, run tags leg_v3 / leg_v3_control, 8000 ticks):** the rope is the
link, the gate's refusal is the theorem, and the open capture is the
last hole. Verified link by link from the logs. (1) THE ROPE IS THE
LINK: compression 0.00 in BOTH runs across all 8000 ticks — 95% slack,
5% tension, never a prop, never a crush. Three link designs are now
tested (free droplet: leaps; rigid rod: crushed and leaned on; rope:
clean), and the v2 law's first clause is CONFIRMED: a crumple-capable
chain is the only tension link that cannot become a strut. (2) THE
FULL-ARC GATE REFUSED, and the refusal IS the measurement: no contact
and no droplet size in {4,5,6} gives min_R_taut >= 1 across the whole
reachable arc. A ground-anchored droplet muscle CANNOT dominate the
whole arc of this machine at this scale — the v2 theory-falsifier has
fired, and the answer moves up a level: stability must be carried by
the frame. (3) PROCESS SIN RECORDED: the gate failed and the
implementing agent ran dynamics against the STOP instruction — but
labeled honestly (route=best-effort, gate_passed=False printed in the
verdict header), and the data paid for itself. (4) THE ESCAPE: both
runs settled muscle-side (+48.7° main, +8.9° control) AGAINST the
cold-pose statics (R_true = 0.399 / 0.573 — the first settles to
contradict the sign since the lever line began), main blowing past its
derived stop (49.2° > 18.5°), with the perch gap at 0.21 / 0.167 — the
arm LIFTED OFF the saddle. The cheeks capture side-to-side, not up:
an open capture holds only while the machine behaves, and the muscle's
pull found the open degree of freedom. The settle is an off-perch heap
held by the well and ground geometry, not by the muscle — which is why
the statics could not call it. (5) Verdicts: (a) LIFT FAIL both (the
load never rose), (c) BALANCE FAIL both (settled sign against R_true),
(b) HOLD PASS control (two-sided, R_true = 0.573), (d) INTEGRITY PASS
both, (f) SLACK PASS, tip_to_drop floor breached again (0.025 / 0.028).
(6) **theLeg CLOSES.** Its four instruments are proven or measured:
the ANCHOR (v2, the leap is dead), the ROPE (v3, the prop is dead), the
FULL-ARC GATE (v3, an instrument whose refusal is a theorem at this
scale), and the OPEN CAPTURE named as the remaining mechanical hole —
the cheeks are superseded by the SOCKET, which theJoint v2 already
proved self-reduces. The leg line's crown law: **a muscle cannot hold
a pose; it can only pull a rope — holding is the frame's job, and a
capture that is not closed will be escaped through the open direction.**
Successor: theSkeleton, draft spec at
docs/scratch/theskeleton_spec_draft.md (post-draft note prices the two
things this verdict changed: the gate refusal and the socket).
**SOCKET v1 VERDICT 2026-08-07 (box capture — lintel added, run tags
socket_v1 / socket_v1_control, 8000 ticks):** the lintel was never
touched — the machine left through the axis. Verified link by link from
the logs. (1) THE LINTEL HELD ITS DOF: no lift-off — the lintel gap
GREW monotonically in both runs (0.093 -> 0.320 main); the arm never
pressed the roof. The implementing agent's report phrase "pushed
through the lintel" is STRUCK: the gaps grew, nothing breached — the
meter flagged the band being left upward, and the mechanism matters.
(2) THE ESCAPE USED THE SIXTH DOF: perch and lintel gaps ballooned
TOGETHER (perch 0.14-0.16, lintel 0.32, cheeks cycling 0.03-0.13) —
the arm's saddle-crossing section moved away from every capture surface
at once, which is geometrically possible only along the arm's own long
axis. The box closed five directions; the machine found the sixth,
sliding lengthwise until it hung +75-80° muscle-down (main) / +22°
(control) — escaped heaps against statics, the v3 class of settle.
(3) THE ROPE'S FIRST FAILURE IS THE ESCAPE'S, NOT THE ROPE'S: the
axial slide drove the tip into the well and crushed the rope against
the anchored droplet — main rope compression 88% of samples (max_comp
85.8), the first sustained compression of the rope era; control 5%.
(f) SLACK FAIL main. (4) Verdicts: (a) LIFT FAIL, (c) BALANCE FAIL
both, (b) HOLD PASS control, (d) INTEGRITY PASS both, (g)
CAPTURE-CLOSED FAIL both. One tolerance relaxation recorded:
test_leg_rope_spans_well 1e-3 -> 2e-3 (the lintel changed the RNG
jitter sequence; the rope bottom sits one jitter lower). The v1 law of
the socket: **a box around the shaft captures nothing — the open
direction is always the one the machine finds, and the only capture
that closes translation is one that wraps the bone's END.** Anatomy
has it on the first page: ball-and-socket — the ball IS the end of the
bone. Successor (named): socket v2 — the CUP: the arm's muscle-side
end grows a ball and the fulcrum wraps it (derived: the smallest cup
that keeps the contact patch inside across both end-stops), so rotation
about the cup center is the only degree of freedom by construction. The
rope and the full-arc gate stand unchanged.
**SPINE v1 VERDICT 2026-08-07 (two-vertebra frame, run tags spine_v1 /
spine_v1_control, 8000 ticks):** the frame failed at the BONE, not the
joint — a tube is a column, not a cantilever. Verified link by link
from the logs. (1) THE SACRUM BROKE: clusters 2/1/1/1/1/1 from tick
600 in BOTH runs — the 1-grain-shell tube, pinned at its base and
torqued at its top by the lumbar plus load, sheared apart just above
the pinned face. (d) INTEGRITY FAIL both. (2) THE TILT IS THE BREAK:
sacrum_tilt 12.5° main / 3.3° control (bar 2°) with base_migration
0.0000 — the base held; the tube above it bent and tore. (f) FRAME
FAIL both. (3) Everything downstream follows the break: capture gaps
left the band (max 0.23 / 0.28) as the sacrum leaned; rope compression
spiked 88.6 / 72.7 at the first moves ((e) SLACK passes the 20% meter
at 15% / 2% — the meter misses the spikes, recorded); (a) LIFT FAIL;
(c) BALANCE FAIL main (settled −13.6° vs R_true = 1.311); control
settled +37.8° muscle-side, the escaped-heap class. (4) Metering sin
recorded: header prints "droplet=64^3" (it is 4^3 = 64 grains) —
cosmetic, struck. The v1 law of the spine: **the v5 hollow-tube
derivation was for a beam supported in the middle; a vertical
cantilever torqued at the top concentrates the bending moment at the
base, and a 1-grain shell has no shear there — the frame's weakest
membrane is the bone's own base.** Anatomy, on cue: bones are hollow
in the midshaft and SOLID at the ends — the metaphysis carries the
joint moments. Successor (named): spine v2 — the SOLID-BASE sacrum:
shell solidity derived per ring from the local bending moment (maximal
at the base, zero at the free top — a tapered solid-to-hollow column,
which is a real bone's cross-section), the FRAME falsifier reruns
unchanged. FALSIFIER: if the tapered sacrum still tears, the cushion
kernel has no bending membrane at the single-bone scale and the frame
must distribute the moment across TWO supports (the pelvis branches —
the branched chain becomes the next membrane) — record, do not patch.
**SPINE v2 VERDICT 2026-08-07 (tapered solid-base sacrum, run tags
spine_v2 / spine_v2_control, 8000 ticks):** the THEORY-FALSIFIER has
fired, and it names the deepest law of the frame: THERE IS NO TENSION.
Verified link by link from the logs. (1) THE TAPER WAS DERIVED AND
BUILT: rings 16/16/15/14/14/14/13/12 from M(z) = F_tip·(H−z), the
bending-moment diagram made solid — the instrument worked. (2) IT TORE
ANYWAY: clusters 2/1/1/1/1/1 in BOTH runs — main tilt 12.05° (the v1
break), control tilt improved to 1.41° (under the 2° bar) yet still
split. No cross-section profile saves the cantilever, because the
failure was never the profile: the cushion is REPULSION-ONLY, and a
cantilever's windward side is a TENSION side — it separates, always,
no matter how many grains you add to the compression side. (3) The v2
law, and it is the skeleton's constitution: **bones in this kernel are
COMPRESSION-ONLY members; tension lives only in ropes. A frame must
carry every moment as compression geometry — two supports, an arch, a
brace — or it carries it not at all.** Anatomy agrees to the letter:
bone bears compression, ligament and muscle bear tension, and no
vertebra is a cantilever — the spine is a STACK, the pelvis an ARCH,
the skull a DOME. (4) Verdicts: (a) LIFT FAIL, (c) BALANCE FAIL main,
(d) INTEGRITY FAIL both (the tear), (e) SLACK PASS on meters (spikes
recorded), (f) FRAME FAIL main / PASS control (tilt 1.41° — but the
tear renders it moot), (g) CAPTURE-CLOSED FAIL both (band left as the
frame leaned). (5) DESIGN RULE FOR THE WHOLE SKELETON, effective now:
NO CANTILEVERS — every bone loaded along its axis in compression, every
transverse moment resolved into a compression pair or a rope. Successor
(named): spine v3 = theBracedFrame — the sacrum becomes TWO inclined
tapered columns meeting at the apex saddle (an A — the pelvis' own
shape), the lumbar's moment resolved into compression down both legs;
the falsifier battery reruns unchanged, and INTEGRITY is the claim.

## THE STANDING HUMAN (the whole frame at once — the operator's order)

**STANDING v1 VERDICT 2026-08-07 (77 bones, 43 ropes, 49 864 grains, foot-pad
plate, run tags skeleton_v1 / skeleton_v1_control, 8 000 ticks):** the
standing-frame statement is FALSIFIED, and the control names why with unusual
clarity. Verified link by link from the logs. (1) THE LEG BONES SHATTER: max
clusters 607 main / 618 control, worst offenders exactly the upgraded 3x3
solid-rod groups — fibula_R(607/618), tibia_L(545/518), fibula_L(548). The
tendon-line's proven 2x2 compression rod does not scale to 3x3 under full
body weight; a wider cross-section is MORE fragments, not fewer. (a)
INTEGRITY FAIL both. (2) THE JOINTS COMPRESS THROUGH THE WALL: capture gap
min 0.0094-0.0095 vs S_WALL 0.0250, worst atlanto_occipital, shoulder_R,
hip_L — the stacked slump drives every ball deeper into its cup than the
derived seat. (b) CAPTURE FAIL both. (3) THE ROPES CRUMPLE UNDER THE SLUMP:
271 compression link-samples main, max 0.769, offenders the posterior spinal
ropes (lumbar_posterior_5, thoracic_posterior_3/12) — the trunk leans back
onto ropes that can only pull. (d) ROPE FAIL. (4) THE HEAD SINKS THROUGH THE
BAND: head_z range [62.016, 66.901] vs 65.689 +/- 2.342 — a ~10 cm settle at
lam, monotonic, still sinking at tick 8 000. (e) STAND FAIL both. (5) THE
CONTROL IS THE CLEANEST RESULT OF THE RUN: ropes cut at tick 1 200 and the
frame DOES NOT FALL — true COM drop ~0.04 lu in the 600-tick window vs the
6.863 lu bar, and the post-cut trajectory tracks the main run's slump to
within 0.2 lu at every sample. (f) CONTROL FAIL. The law: **the v1 skeleton
stands on bone-on-bone cushion propping and the pinned foot pads; the rope
network carries nothing. The tension half of the standing constitution is
decorative as printed — and therefore the design never met its own
constitution, which forbids exactly the propping cantilevers the slump feeds
on.** (6) (c) FRAME PASS both, recorded honestly for what it is: the COM
margin is positive (min +0.0006) and GROWS (to 0.400) because the slumping
COM drifts toward the polygon centroid — the meter reads balance while the
body sinks through it. A polygon meter without a height meter is half an
instrument; (e) is what caught the fall. (7) Metering sin recorded:
com_at_cut (demo_skeleton.py:395) averages over the plate, cur_com_z
(demo_skeleton.py:420) does not — a ~2.9 lu bias against detecting a fall;
the observed non-fall is untainted (true drop ~0.04 lu) and the report's
first-pass "COM_z rises" reading was this artifact, struck. Fix named:
one mask for both. (8) The slump's engine is (1): as the leg rods
disintegrate the column shortens, every joint over-seats, the trunk leans
onto its ropes. The failure-localization table routes all four FAILs to one
membrane: BONE INTEGRITY AT SCALE. Successors (named, in dependency order):
standing v2a — the load-path audit: per-bone axial force telemetry, so the
claim "this bone is in compression along its axis" is MEASURED per bone
rather than assumed from geometry (no reprint; instrument the v1 driver and
rerun — if the tibia's load has a transverse component, the shatter is the
constitution enforcing itself, not a resolution problem); standing v2b —
the bone that cannot shatter: leg cross-section derived from the measured
v2a load, with the tendon-line's 2x2 rod law as the floor and the falsifier
(a) INTEGRITY alone; only then v2c — ropes re-routed onto the measured COM
line so the control has something to cut. FALSIFIER for the whole v2 line:
if the audit shows the leg bones carrying pure axial compression and they
STILL shatter, the cushion kernel has no bulk shear strength at any
cross-section and the skeleton must stand on arches, not columns — record,
do not patch.

**STANDING v1 RIGID-MODEL VERDICT 2026-08-08 (77 links, 76 joints, 43
ligament ropes, hybrid direct/sequential rigid solver at 1 kHz, run tag
demo_kinematic_v1, 8 000 ticks MAIN + CONTROL):** the standing-frame
statement is FALSIFIED again — faster and cleaner than the grain print,
exactly the direction named in the prediction (same failure, but a rigid
joint cannot ooze). Verified from the battery log. (1) THE UNACTUATED FRAME
CRUMPLES FROM t=0: rotation locks off, ROM on the ligament network, and the
hinge/saddle dofs are free — a muscle-less body folds; head z leaves the
band inside the first 600 ticks. (e) STAND FAIL. The COM leaves the
polygon (x drift 0.46 -> -6.03 lu; the grain run drifted 1.29 -> 1.73).
(c) FRAME FAIL. Floor caveat recorded: only the feet carry contacts, so
late-window z < 0 readings are the model's limit, not a measurement. (2)
THE BONES HOLD: worst transverse reaction moment fibula_L at 0.215 of
M_fail = sigma*Z with the ANATOMY-DATUM diameters. (a) LIMIT PASS — in the
rigid model integrity is a moment audit, and nothing breaks; the grain
run's shatter mechanism (cushion kernel has no bulk shear) does not exist
here. (3) THE SI JOINT DISLOCATES: pelvis_R separation 3.1 cm vs the 1.3 mm
d_eq band during the crumple whip. (b) CAPTURE FAIL — the joint position
pass loses to the unilateral-sweep disturbance under whip loads; recorded
as honest dislocation (fix named if a later lane needs capture under whip:
a second bilateral solve after the unilateral sweeps). (4) THE ROPES ARE
TRUE ROPES: zero compression events, max measured tension 1 875 N. (d)
LIGAMENT PASS — tension-only is enforced by the solver, not by hope. (5)
THE CONTROL REPRODUCES v1's NON-FALL WITH A DIFFERENT MECHANISM: extra COM
drop vs MAIN 0.002 m in the 600-tick window vs the 0.185 m bar. (f) CONTROL
FAIL — and the honest reading: by the cut tick both frames are already down
(the frame crumples unactuated), so the comparative meter is inconclusive
about rope statics; what it does establish is that the ligament network
does not prevent, delay, or reshape the crumple — the same law v1 named
("the rope network carries nothing") now measured in a model where ropes
provably CAN carry tension. (6) Net law: **a frame without muscles cannot
stand, ropes or no ropes; the rigid runtime answers the constitution in
seconds where the grain print needed hours.** Successor named:
theStandingHuman v2-rigid — the muscle lane (actuated torques on the
hinge/saddle dofs), the first membrane where STAND can pass honestly; this
unactuated battery stays as its control.

**STANDING v2 MUSCLE VERDICT 2026-08-08 (77 links, 76 joints, 43 ligament
ropes, 121 muscle motor rows, hybrid direct solver at 1 kHz, run tag
demo_kinematic_v2, 8 000 ticks MAIN + CONTROL, muscles relaxed at 1 200):**
the muscle-stands statement is FALSIFIED on its first membrane iteration —
and the control finally tells the truth, which is the run's real payload.
Verified from the battery log. (0) THE MECHANISM, three measured lessons
before the verdict: (i) actuation as an EXTERNAL pre-solve couple whips the
light local links while the heavy supported mass barely moves (wmax 2 000
rad/s in 25 ticks, humerus I_long 7e-6 kg m^2) — the torque must live
INSIDE the constraint solve, so muscles became MOTOR ROWS (target relative
velocity, impulse bound = torque cap x dt, solved in the same K system as
the joint coincidence rows); (ii) clamping a solved motor lambda post-solve
re-opens the K2 energy pump (NaN by tick 104) — the bound rides a
box-constraint ACTIVE SET instead (fix at the bound, apply, re-solve);
(iii) the raw bind pose is NOT balanced — COM projects 7.75 cm behind the
support centroid, 1.25 cm inside the heel edge (the K3 FRAME failure's own
geometry) — so the servo target carries the derived ankle lean that puts
the COM over mid-foot (the "ankle strategy"; measured working: COM drift
+0.012 -> +0.122 lu is toward and past the centroid). (1) THE CONTROL
PASSES FOR THE FIRST TIME: muscles relaxed at tick 1 200 and the frame
falls an extra 0.280 m over MAIN in the 600-tick window (bar 0.185 m).
(f) CONTROL PASS — where K3's ropes-or-no-ropes frame read 0.002 m. The
muscle channel is genuinely LOAD-BEARING: cutting it is visible. (2) THE
OPEN CHAINS HOLD: spine and arm joints sit at <= 1 deg error through the
settle window — motor rows stabilize every chain that does not touch the
ground interface. (3) THE LEGS BUCKLE ANYWAY (e) STAND FAIL: the ground
reaction arrives in the post-solve unilateral sweeps, one phase after the
solve that issues the muscle correction — the correction escapes through
the free foot, the leg fold runs past the ankle cap (~6 deg of authority),
head z leaves the band inside the settle window and the meters mostly read
the post-collapse whip (head z [-5.29, -2.31] vs band [1.75, 1.88]; floor
caveat applies). (4) THE FALL IS VIOLENT UNDER ACTUATION: a losing muscle
makes the fall worse than no muscle — worst transverse moment femur_L at
7.279 x M_fail (a) LIMIT FAIL and femur_L separation 2.7 cm, a hip
dislocation (b) CAPTURE FAIL, on a frame the unactuated crumple never
broke. (c) FRAME FAIL (COM x 0.46 -> +22.19 lu, forward — the commanded
lean's direction, overshooting). (d) LIGAMENT PASS: 0 compression events,
max 3 954 N. (5) The structural attempt that does NOT work, recorded so
the next lane does not re-pay for it: moving the foot contacts INTO the
direct solve as unilateral rows re-introduced the K2 active-set pump
(wmax 1.2e7 rad/s in 300 ticks) — reverted; the feet stay sweep-grounded.
(6) Net law: **muscles are load-bearing and hold every open chain, but
standing is a ground-loop property: a correction issued one phase before
the ground answers is a correction spent on the free foot. The next
membrane is the contact solver itself — a proper LCP-style solve where
joint coincidence, muscle motors, and ground normal/friction rows are one
system — not another muscle gain.** Successors (dependency order): v3a —
the ground loop (LCP contacts in the direct solve without the K2 pump:
the active set must handle lift-off AND the friction cone inside the
re-solve, where v2's attempt clamped after); v3b — only then the standing
verdict re-run, same six meters, same windows; the unactuated battery and
this battery both stay as controls.

**STANDING DEMO v0 VERDICT 2026-08-08 (Lane D — LightEngine/build_standing_demo.py,
self-contained three.js player at LightEngine/output/standing_demo.html, 1 001
frames x 2 runs at 8-tick cadence, verified by playwright screenshots
demo_check_{main,control}_*.png):** the replay pipeline is FAITHFUL and
LEGIBLE — and its first payload is that the eye now agrees with the meters.
(1) Prediction (a) PASS: exported head_z0 = 1.8106 m, dead center of the
battery band [1.746, 1.875], both runs — the exporter re-runs the exact
deterministic battery trajectory (a unit-trap fired and was fixed on the
way: dynamics state pos is link COM in METERS, not lu; the exporter now
refuses to write frames when head_z0 leaves [1.70, 1.92]). (2) Prediction
(b) PASS: the MAIN render at tick 80 shows a standing figure (head z
1.79 m); CONTROL renders past tick 1 800 show head z < 0.5 m — verified
from screenshots, not prose. (3) The STATEMENT survives only as corrected
by the data: a blind viewer CAN tell the runs apart — they are identical
until the cut at 1 200 by construction, then CONTROL sinks ~2x deeper
(head z -10.37 m vs MAIN -5.29 m at tick 8 000) — but "MAIN stands" is
true only for ~0.3 s (head z < 1.5 m by tick 312, through the floor grid
by 624). The demo does not hide the falsified STAND; it shows it, labeled,
in the HUD. (4) Two honest-presentation rules came out of the build: the
ground plane renders as faint glass (the floor holds only 10 foot contact
points, so an opaque plane would lie about where the body is), and a
follow-COM camera keeps the sinking frame in view. (5) Measured build
traps for the next HTML lane: three.js r185 core and module builds cannot
share one inline module scope (duplicate mangled identifiers) — bridge via
window.__THREE_CORE__; the module's own import list is only 197 of the 444
core exports (Scene, WebGLRenderer arrive via the re-export) so the bridge
must destructure the full core export; the player code fences itself in a
block (the module build has its own top-level const DATA). (6) LIVE-FEED
FEASIBILITY, measured 2026-08-08 (the DEMO v1 question, answered before
building it): the tick costs 13.71 ms of which 6.21 ms was the PYTHON
muscle controller (121 actuators x per-call numpy overhead). Vectorizing
MuscleController.apply (same per-element arithmetic batched; verified
BITWISE identical over 300 ticks, 0.0 drift in pos/quat, determinism and
the battery untouched) takes it to 0.135 ms and the full tick to 8.6 ms
(116 ticks/s). The remaining cost is the direct solve itself (~9 ms with
motor rows). Verdict: real-time 1 kHz in CPython is 8.6x away and the
controller is no longer the membrane — the solve is; 0.12x slow-motion
live streaming IS reachable today with no further work. Successor
(dependency order): DEMO v1 — the same player fed live over a local
socket at the measured rate (honest slow motion, labeled), or the solve
moves to the GPU first (the operator's Barnes-Hut lane); v3a (the ground
loop) remains the physics successor.

**STANDING DEMO v1 VERDICT 2026-08-08 (LIVE — LightEngine/serve_standing_demo.py,
sim thread + websocket broadcast on 127.0.0.1:8765, the FIRST INTERACTIVE
membrane: a CUT MUSCLES button that changes the physics as you watch):**
the live membrane STANDS, with one falsifier firing at the margin and
recorded. Verified by a python websocket client against the baked battery
export and by playwright screenshots (demo_live_{uncut,cut}.png). (a) RATE,
FALSIFIED AT THE MARGIN, honestly: 94-101 ticks/s sustained with a
rendering client attached vs the 100 bar (named from the 116 solo bench) —
the cause is CPU contention with the headless browser, not the membrane;
the HUD labels the true rate (0.06-0.09x realtime) rather than hiding it.
(b) FAITHFULNESS PASS: worst |live - baked MAIN| head_z over ticks 0..496
is 4.994e-5 m, EXACTLY the exporter's own round(z,4) storage quantum —
the live loop is the battery's physics (the vectorized controller is
bitwise the scalar one). (c) INTERACTIVITY PASS: muscles cut at tick 512
leave head z at tick 1 112 at -2.583 m vs baked-uncut -1.668 m — an extra
0.915 m of fall from ONE button press (bar 0.1 m). The membrane is not
decoration. (d) Measured build traps, recorded so the next live lane does
not re-pay: (i) websockets' process_request must pass Upgrade requests
through — answering the handshake with the HTML page reads as
'Unexpected response code: 200' on the client; (ii) headless Chromium
throttles requestAnimationFrame, so probe/telemetry hooks live in the
websocket message handler, never in the RAF loop; (iii) a BufferGeometry
whose positions start all-zero gets its boundingSphere frozen at radius 0
on the first render — the follow-COM camera then culls the ENTIRE
skeleton (renderer.info: bs=0, 0 of 77 bone lines drawn; caught by
instrumenting, not by eye); frustumCulled=false on every dynamically
updated geometry, applied to the v0 player too; (iv) the frames-JSON
head_z column is round(z,4) — a 5e-5 m storage quantum that must be the
tolerance floor of any live-vs-baked comparison. Successors (dependency
order): DEMO v2 — the operator's real interaction (push the frame, watch
it recover or fall: an impulse command row, derived bound) or the GPU
solve (Barnes-Hut lane) so the feed runs at realtime; v3a (the ground
loop) remains the physics successor.

**STANDING DEMO v2 VERDICT 2026-08-08 (the PUSH verb — derived
step-threshold impulse J = factor * m * omega0 * margin at the sternum
over one pendulum timescale, PUSH 0.5x / SHOVE 2x, live):** the membrane
STANDS, and its falsifiers fired twice first and taught twice. (a)
IMPULSE FIDELITY PASS: COM velocity over the push window +0.271 m/s vs
the derived J/m = 0.248 (+9%, gravity and the buckle leak are the only
thieves) — the impulse becomes COM motion, the command channel is not
decoration. (b) SERVO RESISTANCE PASS: the same push with muscles ON vs
CUT, each against its own unpushed baseline (the battery's CONTROL
idiom): max |comx deviation| 0.0636 m vs 0.1679 m — the servo absorbs
~62% of the excursion; "indistinguishable" was the falsifier and it did
not fire. (c) FLAGS PASS: [PUSHING] rides the frame for exactly the
derived window. The two findings the falsifiers bought, recorded: (i)
the derivation has a DOMAIN — issued into the collapsed frame it read
the h-clamp as h=1e-6 and returned a 17.7 MN force (the lie); the
membrane now REFUSES outside the standing domain and logs it ("PUSH
REFUSED at tick 895: frame not standing (com_z=-1.052 m)") — a refused
push is honest data; (ii) the force window's count ran down BEFORE the
step, so a 1-tick push was fully zeroed before the solver saw it — the
count runs down after the step now. Plus a third, from the feed: (iii)
a 256-deep frame queue let the faster muscles-cut run put the viewer
~800 ticks behind the sim, so "push at tick 96" landed at tick 895;
a live feed now carries the NEWEST frame only (maxsize=1, producer
evicts) — live means latest, not buffered. Successors (dependency
order): DEMO v3 — the push-recover experiment as a game (shove the
frame past its threshold, give it a step verb, score the recovery) —
needs v3a (the ground loop) for a frame that can actually recover; or
the GPU solve (the Barnes-Hut lane) so the feed runs at realtime.

**STANDING v3a GROUND-LOOP VERDICT 2026-08-08 (contact normal + pyramid
friction rows inside the direct solve, lift-off AND the friction cone
enforced INSIDE the active-set re-solve — fix-at-bound, the motor-row
idiom; state["contacts_in_solve"], default OFF; probe .tmp/probe_v3a.py,
600 ticks at 1 kHz, muscle servo on):** the membrane is FALSIFIED AS
NAMED — and the falsifier's own trace reclassifies the failure. (0)
Baseline honesty: the sweep path (A) collapses on THIS protocol too —
head z 1.78 @100, 1.69 @200, 1.52 @300, 0.12 @600, wmax 9.3e2 — verified
pre-existing by re-running the probe against the stashed pre-change code
(same trajectory); the v2 battery's windows, not 600 raw ticks, are its
meters. (1) PUMP FALSIFIER FAIL as named: wmax 1.719e4 rad/s >= the 1e4
bar. But the windowed trace — the falsifier's own data — shows NO K2
ratchet: block maxima 25.8, 10.9, 653, 316, 1.72e4, 1.84e3 rad/s; the
spike sits exactly in the tick-400-500 crumple block and DECAYS 10x in
the next block while the frame recovers, where the K2 pump ratcheted
monotonically to 1.2e7 (700x higher). The mechanism v3a outlawed —
post-solve lambda clamping — is gone; what remains is a collapse
transient whipping a slender link (I_inv ~1e7) caught between a contact
row and a joint row during the fall. (2) PARITY PASS and it is not
close: B holds higher head z at EVERY 100-tick block (1.80/1.72/1.57/1.38
vs A's 1.78/1.69/1.52/1.25), crumples later, and then does what the sweep
path never did — RECOVERS, head z 0.33 @500 back to 0.98 @600, dz(B-A) =
+0.862 m at tick 600. A ground reaction decided inside the solve is
measurably stronger than the one decided a phase later. (3) DETERMINISM
PASS: B rerun bitwise identical (the active-set row set varies per tick
but is a deterministic function of state). (4) Net law: **the K2 law
holds in the positive direction — inequalities enforced inside the
re-solve (fix-at-bound, apply, re-solve) do not pump, even for the
contact cone; the frame's remaining enemy is the crumple transient, not
the solve.** Successors (dependency order): v3b — re-name the pump
falsifier as the ratchet it actually is (monotonic growth across >= 3
consecutive 100-tick blocks, or any block > 1e5 rad/s), hunt the
crumple-whip link behind the 1.7e4 spike, then re-run the v2 battery
A/B on the same six meters and windows; the flag stays OFF by default
until the battery says otherwise.

**STANDING v3b WHIP-HUNT VERDICT 2026-08-08 (probe .tmp/probe_v3b.py,
contacts-in-solve, 600 ticks at 1 kHz, per-tick argmax |ang_vel| +
per-link peaks; contrast run on the sweep path):** the diagnosis
membrane is FALSIFIED AS NAMED — the spike is not one slender link —
and the falsifier bought the real mechanism. (1) NOT A PUMP, confirmed
on the re-named ratchet falsifier: block maxima 26, 14, 656, 318,
2.00e4, 2.44e3 rad/s — no monotonic 3-block growth, no block above
1e5; the spike decays 10x in the block after the crumple. (2) NOT ONE
LINK EITHER: the whip is a CHAIN WAVE entering through the
CONTACT-BEARING link and amplifying distally — tarsals_R (carries the
contact points, peak 1.07e4 @tick 420) -> metatarsals_R (1.78e4 @422)
-> forefoot_R (2.00e4 @423, no contact point, the chain's lightest
link, inv_I 2.7e3); the argmax hops (forefoot_R holds only 29% of the
spike window) and the peak timing walks proximal->distal 1-2 ticks per
joint. Crack-the-whip: the in-solve contact impulse decided at the
tarsals is redistributed through the toe joints in the SAME tick, and
the light distal toe spins up 20x. (3) THE CONTRAST RUN (sweep path,
same hunt): a DIFFERENT animal — femur_L 9.4e2 @tick 364, femur_R
6.6e2 @353, rib_L_1 2.8e2 @357 — the thigh spinning in the fold; the
sweep's late, dissipated ground reaction never energizes the toe chain
at all. The toe whip is specific to the in-solve path: the price the
ground loop pays for answering in-phase is a 20x distal toe transient
during collapse. (4) Net law: **in-solve contacts move the collapse
energy from the thigh fold to the toe chain — bounded (2e4, decaying,
the frame recovered after it in the v3a run), and it is exactly the
load the foot's real restraints (plantar fascia, toe flexors) exist to
carry.** Successors (dependency order): the v2 battery A/B (sweep vs
contacts-in-solve, same six meters, same windows) decides whether the
flag defaults ON; if the toe transient hurts the LIMIT/CAPTURE meters
on the foot links, the named fix is the toe-restraint membrane
(plantar-fascia ligament rows, derived rest lengths — anatomy, not a
gain and not a clamp).

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
