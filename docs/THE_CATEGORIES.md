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

**STANDING v3c BATTERY A/B VERDICT 2026-08-08 (the v2 battery, same six
meters, same windows, sweep (A) vs contacts-in-solve (B);
CONTACTS_IN_SOLVE env flag added to demo_kinematic_v2 and
serve_standing_demo for exactly this A/B; MAIN + CONTROL, 8 000 ticks
each):** the membrane is FALSIFIED as named and the flag stays OFF. A
reproduces the recorded v2 battery exactly (LIMIT femur_L 7.279, CAPTURE
0.0269 m, FRAME +22.19 lu, LIGAMENT PASS 0 events / 3 954 N, STAND head
z [-5.294, -2.308], CONTROL PASS +0.280 m) — the control side is
bit-consistent with history. B holds better through the early window
(the 600-tick probe's +0.862 m was real) and then DIVERGES on the long
protocol: vmax 2e156 m/s by tick 8 000 with numpy overflow warnings,
LIMIT / CAPTURE / FRAME reading 1e170-class debris numbers, and — the
falsifier named before the run — (d) LIGAMENT FAILS (7 compression
events), a meter A passed. ((f) CONTROL reads PASS at 3.979 m but is
vacuous: both frames are exploded debris by the cut window.) (1) The
600-tick probe and the 8 000-tick battery are BOTH true: the in-solve
ground loop delays the crumple, then a slow energy leak the short
window cannot see goes supercritical on the LYING frame, where many
contact rows are active at once and the fix-at-bound friction, the
active-set entries/exits, and the post-solve ligament sweep interact
tick after tick. (2) Net law: **a solver membrane is not done when it
wins the short window — the K2 ghost did not die, it moved to a longer
timescale: the leak is not the post-solve clamp (that stayed removed)
but somewhere in the bound-revision / active-set / ligament-sweep
interaction, and only a per-tick energy-drift meter over a long
lying-frame run will name it.** Successors (dependency order): v3d —
the energy audit: run the lying frame with contacts-in-solve, log total
kinetic energy and per-row-kind impulse work each tick, and find the
row kind whose mean work is positive (prime suspect: friction
fix-at-bound with a bound computed from a lambda_n the re-solve later
revises; second: the ligament sweep fighting the in-solve contacts);
only then another battery A/B. The flag stays OFF everywhere (battery,
demo server, exporter) until a full battery passes with it ON.

**STANDING v3d ENERGY-AUDIT VERDICT 2026-08-08 (probe .tmp/probe_v3d.py,
four 8 000-tick configs, per-tick total kinetic energy, bar 1e8 J; the
contact_friction=0 instrumentation toggle added to step_core_direct for
exactly this audit, default unchanged):** the statement HOLDS — the
long-timescale leak lives in the friction fix-at-bound machinery, and
the meter names the address by elimination. (1) sweep (reference):
BOUNDED, max KE 1.3e3 J, post-crumble steady state ~30 J. (2) full
cone: EXPLODED at tick 7 713 — and the trace is the payload: KE climbs
to 1.3e5 J by tick 2 000 and SIMMERS there for 6 000 ticks (1.29e5 ->
1.6e5, a slow positive-work pump holding the lying frame hot at 4 000x
the sweep's steady state) before going supercritical (2.5e228 J). Not
a spike: a simmer. (3) friction rows skipped: BOUNDED, max KE 3.0e3 J,
a sweep-like profile — the normal-row active set alone is clean. (4)
ligaments neutralized (rest length 1e9): EXPLODED EARLIER, tick 1 436 —
ligaments are not a component of the leak at all; without them the
frame crumples faster and the friction pump goes critical sooner. (5)
Net law: **the in-solve friction cone as built — bound computed from
the current attempt's lambda_n, fixed, applied, row removed, lambda_n
then revised by the re-solve — does positive mean work on the jiggling
lying frame; the normals-in-solve active set is stable; the K2 ghost's
address is the intra-tick bound revision.** Successors (dependency
order): v3e — the derived fix candidates, in order: (i) normals-in-solve
+ friction back in the post-solve sweep (dissipative there by
construction; the hybrid keeps the in-phase ground loop that won the
short window); (ii) cone bound from the PREVIOUS TICK's lambda_n (a
warm-start box constraint, no intra-tick revision); then the battery
A/B again — the flag stays OFF until a full battery passes ON.

**STANDING v3e HYBRID VERDICT 2026-08-08 (normals in-solve + friction
swept, cone bound MU x the solve's own normal impulse; probe
.tmp/probe_v3e.py + the v2 battery CONTACTS_IN_SOLVE=1
CONTACT_FRICTION=2, MAIN + CONTROL, 8 000 ticks):** the membrane is
FALSIFIED AS NAMED on its early-gain falsifier — and it is still the
first in-solve ground loop that survives the full protocol; the
falsifier bought the exact price list. (1) ENERGY PASS: 8 000 ticks
BOUNDED, max KE 4.3e3 J, post-crumble steady state 32.0 J = the sweep's
~30 J — the simmer pump is dead. (2) EARLY-GAIN FAIL as named: head z
@600 = 0.368 m < the 0.5 bar (full cone: 0.980; sweep: 0.118) —
in-solve friction WAS buying early grip, and swept friction recovers
only a third of it. (3) THE BATTERY ARBITRATES (same six meters, same
windows, vs the sweep's recorded numbers): (a) LIMIT femur_L 7.439 vs
7.279 (~same), (b) CAPTURE femur_L 0.0265 m vs 0.0269 m (~same), (c)
FRAME drift 7.45 lu vs 22.19 lu (3x BETTER), (d) LIGAMENT PASS 0
compression events (force 6 502 N vs 3 954 N), (e) STAND head z
[-2.533, -1.284] vs [-5.294, -2.308] (2x SHALLOWER crumple), (f)
CONTROL PASS +0.842 m vs +0.280 m (3x stronger muscle visibility).  No
meter the sweep passed regressed; every failing meter's numbers
improved or held; vmax 28.2 m/s is the sweep's post-crumble whip
class, not the full cone's 1e156 debris.  The sweep path verified
bit-identical after the kernel changes (head z @600 0.1178, wmax
934.7, both exact). (4) Net law: **the full cone's early-window
advantage was bought with a 6 000-tick simmer that explodes — not a
foundation; the hybrid trades two thirds of the early grip for
long-protocol stability and is strictly battery-equivalent-or-better,
so the hybrid becomes the DEMO's ground loop (server + exporter;
CONTACTS_IN_SOLVE=0 opts out) while the step() library default stays
sweep until the wider suite says otherwise.** Successors (dependency
order): the warm-start cone bound (previous tick's lambda_n) if the
early grip matters for STAND; the toe-restraint membrane (plantar
fascia, v3b) still stands; DEMO v3 (the push-recover game) now has a
ground loop that can actually recover.

**STANDING v3f DEMO VERDICT 2026-08-08 (hybrid artifacts rebuilt,
server v10 live on 127.0.0.1:8765; probes .tmp/probe_live.js,
playwright screenshots):** (1) LIVE == BAKED PASS: the live server's
head_z matches the baked replay to |d| = 3.94e-5 m, one round(z,4)
quantum — the hybrid solver in the server and the exporter are the
same machine. (2) CUT EFFECT PASS: [MUSCLES CUT] buys an extra 0.4287
m of head drop at the probed tick — the muscle channel is visibly
load-bearing in the live demo. (3) RATE FAIL, marginal: 69.2 t/s vs
the 100 t/s bar — CPU contention on a shared box, physics fine;
recorded, not patched (a rate bar is a hardware claim, not a law).
(4) SCREENSHOTS VERIFIED BY EYE: demo_live_uncut.png (tick 504,
figure mid-crumple, head_z 0.90) and demo_live_cut.png (tick 888,
[MUSCLES CUT] flag up, deeper fall) are faithful renders of the
state. (5) Net: the demo a player opens IS the hybrid ground loop
that passed the v3e battery — standing_demo.html +
standing_demo_frames.json rebuilt on it (MAIN + CONTROL 1001 frames
each, head_z0 = 1.8106 guard passed). Successor: DEMO v3 — the
push-recover game (shove the frame with the derived PUSH/SHOVE
impulse already in serve_standing_demo.py, give it a step verb, score
the recovery) — it now has a ground loop that can recover.

**DEMO v3 PUSH-RECOVERY VERDICT 2026-08-08 (probe .tmp/probe_demo_v3.py,
hybrid ground loop, muscles ON, push at tick 100):** the membrane is
FALSIFIED AS NAMED on both recovery and dose — and the falsifier found
the real hole, which is not in the push channel. (1) The push channel
is honest: 0.5x push = 58.7 N for 332 ticks (J = 19.5 N s), 2.0x shove
= 234.7 N (J = 77.9 N s), both derived from the live support geometry;
REFUSAL PASS (the guard refuses at tick 3000, frame flat at head_z =
-1.877 m). (2) RECOVERY FAIL as named: gap vs the unpushed run peaks
0.2521 m and is still growing at push_end + 4W. BUT the baseline
itself is falling: unpushed head_z 1.796 @100 -> 0.923 @500 ->
-0.545 @1000. Recovery was defined against a trajectory that collapses
on its own inside one recovery window (4W = 1 328 ticks) — past
tick ~1 000 the gap measures chaotic divergence of two collapsing
runs, not push lethality. The pendulum domain the recovery verb is
defined in does not exist long enough to test recovery in it. (3) DOSE
FAIL as named: shove peak gap 0.1404 m < push peak 0.2521 m — an
inverted dose response, same confound: once both runs are falling,
gap-vs-base is noise, not dose. (4) Net law: **the push-recovery game
cannot be scored until the frame HOLDS the standing domain on its own;
the falsifier redirects from the push channel (honest) to the standing
controller (absent — muscles ON slows the crumple but does not stop
it).** Successors (dependency order): a standing-balance membrane
(servo that keeps COM inside the support polygon indefinitely — the
recovery verb's arena); then DEMO v3 re-probed, unchanged, against a
baseline that stands.

**BALANCE FORENSICS VERDICT 2026-08-08 (probe
.tmp/probe_balance_forensics.py, hybrid ground loop, muscles ON,
candidates: reference lie / saturation / slip):** the membrane STANDS —
exactly one signature present, and it is SLIP. (1) REFERENCE LIE absent:
the COM- centroid offset SHRINKS 0.0645 -> 0.0119 m through the fall
window — the servo's balanced reference works; the body converges on
its target. (2) SATURATION absent: no sustained clamping before the
fall — the physiology is strong enough. (3) SLIP PRESENT: loaded
contact points migrate 80 mm by tick 200, 271 mm by tick 300, against
the solver's own 1.31 mm slop — the feet slide out from under a frame
that is balancing correctly; head falls 0.18 m by tick 267. (4) Net
law: **the collapse is not a balance failure, it is a GRIP failure —
the v3e hybrid's swept friction under-grips exactly where the v3e
battery said it would (early-gain FAIL: 'swept friction recovers only
a third of the early grip'), and standing is where that bill comes
due.** Successors (dependency order): friction v4 — the warm-start
cone bound (previous tick's lambda_n as the box constraint, no
intra-tick revision — the derived fix already named in the v3d/v3e
successors), probed FIRST by this forensics probe (slip signature must
go absent, head_z fall tick must move past 1 000), THEN the v2 battery
(the simmer pump must stay dead), then DEMO v3 re-probed unchanged.

**FRICTION v4 PRE-PROBE VERDICT 2026-08-08 (probe
.tmp/probe_friction_v4_pre.py, hybrid, ticks 100-300):** the cone-
limited membrane is FALSIFIED — and the falsifier found the real
address. (1) Of 1 338 loaded contact-ticks with residual slip,
only 154 are cone-limited; 1 184 are UNDER bound with the budget
unspent; ZERO contact-ticks are fully arrested. The slip is not a
small MU. (2) The dominant under-bound mode: bound = 0.0000 while the
point carries 0.1-0.6 m/s tangential — the solve's normal impulse is
ZERO at most loaded points (the samples show 2 of 8 foot points
carrying the whole normal load: the rigid-indeterminate contact solve
legally concentrates the load, and with it ALL the friction budget).
The few loaded pivots arrest (residual 2.4 mm/s, ~10% of budget
spent); the unloaded points are carried through big arcs as the foot
rocks and yaws about those pivots under the servo's ankle torques —
that is where the 271 mm of 'drift' is traced. (3) Instrumentation
note (honest): the probe's 50 mm 'loaded' bar counts hovering points
the solver never rows; the zero-bound class mixes hovering (no row —
physically correct) with in-row zero-impulse (the degeneracy). (4) Net
law: **the grip failure is the rigid contact solve's load concentration:
normal impulse — and therefore MU x normal — pools onto a few pivot
points while the rest of the foot offers zero resistance; Coulomb for a
rigid foot depends on the LINK's total normal load, not on which
indeterminate point the solver happened to charge.** Successors
(dependency order): (a) a pivot-rotation probe that separates hovering
from in-row-zero and measures drift-about-loaded-pivots per foot link;
(b) v4: pool the cone bound per LINK (each point's bound = MU x the
link's total normal impulse this tick — derived from rigid-contact
mechanics, no number chosen), then the forensics probe (slip must go
absent) and the v2 battery (the simmer pump must stay dead).

**PIVOT PROBE VERDICT 2026-08-08 (probe .tmp/probe_pivot.py, hybrid,
ticks 100-300):** FALSIFIED on two of three legs — and the falsification
kills BOTH the load-concentration theory and the forensics' slip
reading. (1) (a) PASS: loaded pivots HOLD — median drift 5.36 mm vs
the 13.1 mm bar (max 73 mm). The points the solver charges do not
slide. (2) (c) FAIL decisively: the zero-bound class is 1 605 HOVER
vs 37 in-row — the anatomical sole is NOT flat (heel/ball/toes load,
arch points hover; 2-3 load zones per foot is reality, not a solver
degeneracy). The '2 of 8 points charged' reading was anatomy, not
concentration. (3) (b) FAIL: in-row unloaded points are nearly
nonexistent (n=37). There is no pool of touching-but-uncharged points
for a pooled bound to empower — v4-as-pooling would change ~2% of
contact-ticks. (4) The fatal re-read: the forensics' 271 mm 'drift'
was measured across ALL sole points including anatomically airborne
ones swinging through arcs — contaminated. Pivots hold in xy, the COM
converges on the polygon centroid (forensics (1)), no saturation —
and the head still sinks 0.18 m in 167 ticks. A body sinking STRAIGHT
DOWN over held feet is not a skate and not a slip: it is either a
posture fold (joints flexing away from the servo reference without
clamping) or a trapdoor (the contact plane itself creeps -z). (5) Net
law: **the ground loop may be innocent; the fall's next candidate
address is vertical, not tangential — pivot z-creep vs joint fold,
one probe decides.** Successors (dependency order): the sink probe
(per-tick pivot z + per-joint max |theta_err|, ticks 100-267); only
then a membrane touching the solve.

**SINK PROBE VERDICT 2026-08-08 (probe .tmp/probe_sink.py, hybrid,
ticks 100-267):** FOLD PRESENT, TRAPDOOR absent — and the fold has ONE
address. (1) TRAPDOOR absent: loaded pivots creep 4.69 mm (3% of the
head drop) — the ground loop is INNOCENT of the standing collapse.
(2) FOLD present: max actuated-joint error grows 0.641 -> 2.988 rad
(4.7x), monotonic from tick 100, at ONE joint the whole way:
**tarsals_R on tibia_R — the right ankle**. The body does not slip,
skate, or sink: it slowly hinges over the right ankle, and the servo
never stops it — while (forensics) no sustained clamping shows in the
row stats. (3) The open question the fold raises: the error measured
is the TOTAL angle; the servo can only actuate the joint's FREE axes.
Either the ankle's free-axis error grows UNCLAMPED (the servo is not
spending budget it has — a servo-law bug) or the growth lives on a
LOCKED axis (a joint-constraint leak — the solve lets a constrained
dof drift, and no muscle can fix that). (4) Net law: **the standing
collapse is a single-ankle hinge; the next probe reads the error
decomposed onto the actuator axes with the row's impulse vs its
bound — servo starvation vs constraint leak, one run decides.**
Successors (dependency order): the ankle autopsy probe; then the
membrane for whichever system is guilty — nothing else is touched.

**ANKLE AUTOPSY VERDICT 2026-08-08 (probe .tmp/probe_ankle_autopsy.py,
hybrid, ticks 100-267):** LEAK PRESENT, starvation and physiology-weak
both absent — the guilty system is the constraint solve, not the
muscle. (1) tarsals_R is a HINGE: one free dof, axis ~(0,1,0)
(plantarflexion), torque cap 75 N m. (2) The servo holds the axis it
owns: free-axis error 0.143 -> 0.176 rad (1.2x) through the whole
'collapse'. (3) The fold lives on the LOCKED axes: residual 2.983 rad
at the fall tick, 17x the free error, growing ~0.011 rad/tick
monotonic from tick 100 — the two constrained rotational dofs of the
right ankle drift 171 degrees while every other system watches. (4)
Net law: **the standing collapse is a joint-constraint leak at ONE
hinge: the solve enforces the ankle's free axis (the muscle's row is
in the same K system and holds) but lets the two locked axes bleed
at a steady rate — no servo, friction law, or ground loop could ever
have fixed that, and every previous probe in this chain was measuring
its shadow.** Successors (dependency order): read the kernel's joint
rows for hinge locked axes (K solve + position_pass — where is the
locked-axis error's correction row?); the leak-rate membrane
(0.011 rad/tick = ?); the derived fix; then the FULL probe chain
re-run unchanged: sink (fold absent) -> forensics -> DEMO v3.

**BONE-CLOSURE A/B VERDICT 2026-08-08 (probe .tmp/probe_bone_closure.py,
locks ON, hybrid):** FALSIFIED as a fix SHAPE — the flag kills the leak
but wounds the frame worse. (1) (a) LEAK DEAD PASS: tarsals_R locked
residual SHRINKS 0.304 -> 0.149 rad — the lock rows do close the
corkscrew, so the leak's address was right. (2) (b) NO FOLD FAIL,
decisive: head_z @267 = 1.047 m — the frame falls FASTER with locks
on than with the leak open (1.615 m), and it is already losing height
by tick 100 (1.629 vs 1.796 locks-off): the lock machinery hurts the
frame from the first second, before any collapse debris exists. (3)
(c) NON-VACUOUS PASS: muscles-cut CONTROL still falls (head_z 1.933
below zero at 1499) — the v2 constitution's fear is confirmed
unfounded on this leg: locks never do the muscles' job. (4) (d) NO
PUMP FAIL as named: max |w| 13 817 rad/s, KE 16.8 kJ over the 8000 —
measured across the early collapse the number is debris-class, not
standing-class, but with (b) already red the distinction is moot. (5)
Net law: **the constitution was half right — locks as implemented are
toxic, but NOT because they make STAND vacuous: something in the lock
machinery (the bilateral equality rows in the direct K solve fighting
the motor rows? the BETA=0.2 position-pass lock stabilization pumping
the chain it corrects? both?) breaks the standing frame faster than
the leak does.** Successors (dependency order): locks-on forensics —
where does the locks-ON frame fall first (same joint autopsy,
locks ON), and a position-pass A/B (lock rows in the velocity solve
ONLY vs position-pass ONLY vs both) — the toxic component, one run
each; then the fix membrane for the component, not the flag.

**LOCK COMPONENT + MODE-2 PROTOCOL VERDICTS 2026-08-08 (probes
.tmp/probe_lock_components.py, .tmp/probe_mode2_full.py; kernel split:
lock mode 0=off, 1=both legacy, 2=velocity rows only, 3=position
stabilization only):** the component A/B membrane STOOD and named the
poison; the full-protocol membrane then FALSIFIED mode 2 as a fix —
and the two together hand us the classic derived shape. (1) Component
A/B (400 ticks): mode 2 SAFE and eerily level (head 1.810 -> 1.810 ->
1.811, resid 0.013 rad, max |w| 20.6); mode 3 TOXIC (head 0.975 @399,
|w| 1 855) — the BETA=0.2 position-pass stabilization is the K2 pump's
living address: it rotates quats without touching velocities, an
energy-inconsistent correction, exactly the note the code already
carried. (2) Mode 2 full protocol (8 000 ticks): FALSIFIED on three
legs — STAND fails (head @1000 = 1.399, @4000 = -0.682), the LEAK
RE-OPENS (locked resid 0.011 -> 0.632 @1000 -> 2.784 @7999), whip
2 915 rad/s in the debris; NON-VACUOUS passes. Velocity-level equality
rows hold locked-axis VELOCITY at zero but integrate no position
correction: the leak converts from a pump to a slow drift. (3) Net
law: **locked-axis closure needs velocity rows that carry their own
position error as a Baumgarte bias (row target = -BETA/dt x the
locked-axis error, inside the SAME K solve that carries motors and
contacts — positions and velocities corrected together, no separate
quat pass): velocity-only drifts, position-only pumps, the bias form
is the derived middle; BETA is the file's existing stabilization
factor, no constant is chosen.** Successors (dependency order): the
bias-row membrane (mode 4) in the direct solve + the sweep; the full
protocol re-run unchanged; then the v2 battery ROTATION_LOCKS=4; then
the demo default flips and the v2 constitution comment is corrected
(locks were never vacuous — CONTROL still falls on every run of this
saga).

**MODE-4 BAUMGARTE VERDICT 2026-08-08 (probe .tmp/probe_mode4_full.py,
bias rows in both cores):** FALSIFIED on three legs — and the anomaly
inside the failure re-aims the hunt from the correction LAW to the
solve's ENFORCEMENT FIDELITY. (1) (a) STAND FAIL, worse than mode 2:
head_z @1000 = 0.713 m (mode 2: 1.399). (2) (d) LEAK STAYS DEAD FAIL —
but the number is the tell: locked residual @1000 = 0.6507 rad vs mode
2's 0.6323, statistically the SAME drift. A working bias would move
that number in EITHER direction; the ankle behaves as if the bias is
not there, while the rest of the frame falls FASTER. (3) (b) NO PUMP
FAIL (|w| 3 537 in debris); (c) NON-VACUOUS PASS (fourth time: locks
never hold the frame for the muscles). (4) Integrity: the default
paths verified bit-identical across the mode-4 kernel edits via a
stash A/B (head_z@600 0.1111 pre == post, wmax 934.7 exact; the
0.1178 on record was the battery harness, not this probe's). (5) Net
law: **the drift was never a missing correction law — mode 2's
velocity rows already demand w_rel.L = 0 exactly, yet 0.63 rad of
error accumulates by tick 1 000: the solve UNDER-ENFORCES the lock
rows (min-norm regularizer + over-constrained tree + attempt cap),
and the Baumgarte bias just gave the same under-enforcing solve a
larger, more violent target to miss. The address is enforcement
fidelity, not BETA.** Successors (dependency order): the enforcement
probe — per-tick post-solve |w_rel.L| at tarsals_R in mode 2: ~0
means enforced-and-integrating (bias-law territory), significant
means never-enforced (solve-fidelity territory: regularizer eps,
attempt cap, or row redundancy); then the membrane for whichever is
measured.

**OPERATOR DATUM 2026-08-08 (THE HUMAN terminal, standing biomechanics —
recorded verbatim because it reframes the balance membrane's target):**
"Standing is simply shifting the weight back and forth between the two
legs until there's a balance. It doesn't matter the position of the
legs — it's like the body is taking a step forward and a step backward
but the legs don't move, it's just a weight shift. Weight shift is how
you start moving: you tilt your pelvis in the direction of movement.
For standing you rock back and forth until you find a stabilizing
position to lock your muscles."  Consequences for the membrane stack:
(1) the balance servo's reference is NOT a static pose — it is a
bounded COM oscillation INSIDE the support polygon (sway), with the
lock-rows and muscle rows holding the sway's envelope, not a point;
(2) the pelvis is the LEAD segment for any translation intent — the
step verb's seed is a pelvis tilt, not a foot command;
(3) "lock the muscles once stabilized" names the terminal state: sway
decaying into a clamped equilibrium — which is exactly what a working
lock/solve stack should permit.  The probes in this saga measured
against a static-pose bar; the datum stands as the reference the
balance membrane's next design must derive from.

**OPERATOR DATUM 2, 2026-08-08 (THE HUMAN terminal, locomotion control —
recorded verbatim):** "If you want to move fast you have to increase
the angle. If you accelerate fast you have to increase that angle of
torso inclination. If you do it too much you'll fall over — but if you
want to go fast quickly you have to kind of fall over to that one
point where the pressure of your legs counteracts the equilibrium
momentarily and overrides, so that when you get up to full velocity
you're actually forward still, but not as much — just enough to
counter wind resistance. In a way running is just about the maximum
velocity that we can move in any direction, and then we base
everything off of that. That's how our brain works."  Consequences
for the membrane stack: (1) the locomotion controller's ONE input
knob is the lean (torso/pelvis inclination): acceleration demand ->
lean angle, derived from the inverted-pendulum balance of gravity
moment vs ground-reaction moment — the same omega0 geometry the push
verb already uses; (2) "too much and you fall" IS the falsifiable
boundary: the lean has a derived maximum (the step threshold — beyond
the polygon edge a step MUST fire or the frame falls); (3) steady-
state lean != 0: cruise lean balances drag, so the gait membrane's
equilibrium is speed-dependent, not upright; (4) THE HUMAN defines
the locomotion envelope as RUNNING = maximum velocity in any
direction, with every other gait derived as a fraction of it — the
reference for the walk/run membranes is a top-down scale, not a
bottom-up walk that gets faster.

**OPERATOR DATUM 3, 2026-08-08 (THE HUMAN terminal, the two pivot
strategies — recorded verbatim):** "That inclining pivot happens at
two locations: one is the hip and the other is the ankle. You'll find
that you'll need the two to work together — the hip for fast
movements and the ankles for slow adjustments — and it's where most
of the standing algorithm is calculated."  Consequences for the
membrane stack: (1) the balance controller is a TWO-CHANNEL system
with a derived frequency split, not one pose servo: the ankle channel
owns the slow, small-amplitude corrections (the sway envelope of
datum 1), the hip channel owns the fast, large-amplitude corrections
(acceleration leans of datum 2, push recovery); (2) the split itself
is derivable, not chosen: each channel's bandwidth is bounded by its
own segment dynamics — the ankle strategy moves the whole-body
pendulum about the support (slow, omega0 of the full COM height),
the hip strategy moves the upper body about the hip (fast, the
shorter pendulum of trunk-above-hip) — the same "the body responds
at the rate the body falls" law the muscle servo already uses, now
with two pendulums; (3) the probe chain's numbers already show why
both are needed: the ankle fold was a SLOW leak (ankle channel's
domain), while the shove recovery needs a FAST catch (hip channel's
domain).

**OPERATOR DATUM 4, 2026-08-08 (THE HUMAN terminal, why the sway exists —
recorded verbatim):** "It's more like a range enforcement. That's why
you see a human kind of swaying a little bit slowly as you watch them
stand, or why they shift their position — it's because muscles get
tired and you're balancing the whole load throughout the system. It's
about energy efficiency for all things."  Consequences for the
membrane stack: (1) the balance target is a RANGE (a deadband), not a
point: the COM has an allowed band inside the support polygon and the
muscles act at the band's EDGES, not against every millimeter of
error — a point-servo spends energy fighting the very micro-motion
the body uses to rest; (2) the sway is LOAD ROTATION: sustained
isometric contraction fatigues a muscle group, so the controller
periodically hands the load to a different group (shift the weight,
rest the last one) — the sway's existence, and its slow rate, follow
from the fatigue rate, not from any geometry; (3) the controller's
objective is therefore ENERGY EFFICIENCY (minimize sustained
activation) subject to the band, not pose error — the first
controller objective in this stack with a physiology datum as its
source; (4) this gives the muscle model its missing term: an
activation-cost integral per group, and the hand-off rule derives
from it (hand the load over when the carrying group's cost integral
exceeds the relief cost of the shift) — no chosen threshold, the
crossing point of two measured costs.

**OPERATOR DATUM 5, 2026-08-08 (THE HUMAN terminal, the chain ABOVE
the hip — recorded verbatim):** "Besides the ankle and the hip there
is the neck, which LEADS the hip, and then the spine in between,
which is more of a curve than a joint."  Consequences for the
membrane stack: (1) the balance chain is FOUR tiers, not two: ankle
(slow, datum 3) -> spine (a distributed curve, not a pivot) -> hip
(fast) -> neck (the lead). The neck leading matches the head's role
as the balance organ's platform: the head stabilizes first and the
trunk follows it (vestibular lead), so the hip channel's reference
comes from the neck, not from the pelvis; (2) the SPINE is not a
pivot to servo at one joint: it distributes the lean over its
vertebrae as a CURVE — the stack already has the 2-D sheet/1-D chain
machinery for distributed members, so the spine's balance role maps
to a curvature target shared across the lumbar/thoracic actuators
rather than a single-joint offset; (3) for the demo lane this lands
AFTER the ankle channel stands: the v-order is ankle (in flight) ->
hip fast channel (push recovery, datum 3) -> neck lead + spine curve
(the full four-tier chain) — the standing demo does not gate on the
upper tiers, but the walking/gait membranes do, and the four-tier
chain is now on record as the architecture.

**ENFORCEMENT + GHOST VERDICTS 2026-08-08 (probes
.tmp/probe_enforcement.py, .tmp/probe_ghost.py; mode 2, ticks
100-1000, tarsals_R):** the ankle drift's accounting CLOSES — two
measured parents, no fourth mechanism. (1) UNDER-ENFORCEMENT
CONFIRMED: the post-solve relative spin on the locked axes averages
0.41 rad/s (max 21.8) — the velocity rows ask for 0 and the solve
delivers 0.41; its signed integral covers about half the drift. (The
enforcement probe's leg (b) FALSIFIED as named — ratio 0.47 vs the
0.5 bar — and that falsifier bought the question the ghost probe
answered.) (2) GHOST CONFIRMED: 2.20 rad/s mean of orientation change
at the ankle that exists NOWHERE in the velocity record —
position-level quat rotations (the joint-coincidence BETA projections
rotate quats, never touching ang_vel). The full accounting
rv_total = w*dt + ghost closes at 0.94 of the measured +0.617 rad
growth (bar 0.5-2x). (3) Net law: **the ankle fold has exactly two
parents and both are solver machinery: the direct solve under-
enforces the lock rows (velocity channel), and the position pass
rotates the bones outside the velocity record (the same energy-
inconsistent class already proven to be the K2 pump in the lock
lane). No muscle law, friction law, or balance strategy could have
stood this frame.** Successors (dependency order): the ghost-source
probe — which position-pass projection injects at the ankle (joint
coincidence is the only always-on suspect; ligaments engage on
stretch): instrument by quat delta per position-pass block, one run;
then the fix membrane for the two parents together; then the
two-channel balance controller (operator datums 1-4).

**GHOST-SOURCE VERDICT 2026-08-08 (probe .tmp/probe_ghost_source.py +
kernel instrumentation: ghost_coinc/ghost_lig/ghost_lock per-link
position-level rotation accumulators; mode 2, ticks 100-1000):** the
'coincidence >= 80%' membrane is FALSIFIED as named — the ghost at the
ankle has TWO co-equal parents in a tug-of-war, and the instrumentation
is proven faithful. (1) (b) PASS, the anchor: the instrumented net
ghost at the ankle sums to 1.0139 rad vs the ghost probe's independent
1.0157 rad — ratio 1.00. The accumulators tell the truth. (2) (a)
FAIL as named: gross relative churn splits coincidence 53.1% /
ligaments 46.9% (lock block 0.000 as expected in mode 2). (3) The net
split is the smoking gun: coincidence net 6.93 rad, ligament net 6.15
rad, TOTAL net 1.01 rad — the two blocks rotate the ankle in nearly
OPPOSITE directions ~7 rad each over 900 ticks, 86% cancelling, and
the 1.0 rad residue is exactly the ghost that folds the ankle. The
position pass is not a stabilizer at this joint; it is two projectors
fighting through the bone, outside the velocity record, and the muscle
servo spends its budget correcting yesterday's ghost. (4) Net law:
**the ankle fold's second parent is the coincidence<->ligament
tug-of-war at position level: joint-coincidence corrections rotate
links (ghost channel 1), ligament stretch corrections rotate links
back (ghost channel 2) — and the ligaments already have a velocity-
level sweep (5b), so their position projection is a SECOND, ghosting
application of the same constraint.** Successors (dependency order):
the ghost-free projection membrane — (i) coincidence corrected by
TRANSLATION ONLY (two meeting points need no link rotation; kills
channel 1 by construction); (ii) the ligament position projection
retired to its velocity sweep (kills channel 2 by construction) —
A/B against the full protocol, 'measured stable on every rig' on
record as the falsifier bar; then the two-channel balance controller
(operator datums 1-4) on clean hardware.

**GHOST-FREE A/B VERDICT 2026-08-08 (probe .tmp/probe_ghostfree.py,
pos_pass_mode=1 + lock mode 2, hybrid, 8 000 MAIN / 1 500 CONTROL):**
FALSIFIED on three legs — and the three PASSES are the biggest wins of
the saga while the three FAILURES name the next two membranes. (1)
(a) GHOST DEAD PASS: ankle net ghost 0.0000 rad (legacy 1.0139) — the
tug-of-war is abolished by construction and the instrumentation
proves it. (2) (b) FOLD HALVED PASS, 49x better than the bar:
locked-resid growth +0.0131 rad vs legacy +0.617 (bar was 50%) —
with the ghost gone the fold is 98% dead; parent 1's lock-row under-
enforcement turns out to have been mostly the ghost's shadow (the
servo was fighting phantom corrections). (3) (c) STAND FAIL, but the
horizon TRIPLED first: head_z 1.810 -> 1.811 @1000 (level), then
-0.782 @4000 — the frame stands three times longer than anything
ever measured, then something NEW kills it between ticks 1000 and
4000. (4) (d) NO PUMP FAIL (|w| 2 091, debris-class post-fall); (f)
RIG STABILITY PASS (coincidence held to 1.32 mm vs the 13.1 mm bar —
translation-only holds joints as well as the legacy rotations did).
(5) (e) NON-VACUOUS FAIL — the constitution's fear arrives in its
true form: the muscles-cut CONTROL only sags to 1.312 m by tick 1499
(legacy: -0.5): with clean hardware the PASSIVE structure (lock rows
with unlimited rigid authority + sweep ligaments) holds the frame for
hundreds of ticks with no muscles at all — the frame is too rigid
passively, and a real relaxed body falls immediately. (6) Net law:
**the ghost was the fold; with it dead, standing lasts 1 000+ ticks
on muscle law alone, and the saga's remaining two questions are now
named precisely: (i) what kills the frame between 1000 and 4000 (a
new failure mode, forensicate with the same probe chain); (ii) the
passive-stiffness membrane — real bone geometry has PLAY and limited
passive stiffness (the d_eq band), the current lock rows are
infinitely rigid, and the (e) failure is that rigidity's price.**
Successors (dependency order): the 1000-4000 fall forensics (sink/
fold/which-joint, unchanged probes); then passive play; then the
two-channel balance controller (operator datums 1-4).

**FALL-FORENSICS VERDICT 2026-08-08 (probe .tmp/probe_fall_forensics.py,
pos_pass_mode=1 + lock mode 2, hybrid, ticks 100-4000):** FOLD, and the
folding joint is the TOE. The killer's address, measured: (a) FOLD
PRESENT — max actuated-joint error grows 0.1065 -> 0.7996 rad (7.5x)
and LEADS the fall (half-error at tick 1138, quarter head-drop at
1321); the worst joint is metatarsals on tarsals (the ball-of-foot
flexion axis) on BOTH feet, alternating R/L as the roll advances. (b)
TRAPDOOR absent — loaded pivots hold z to 0.1 mm (they even rise).
(d) CREEP absent — joint-center coincidence holds 1.31 -> 1.40 mm
against the 13.1 mm bar; the retired ligament position projection was
NOT load-bearing on the long horizon. (c) DRIFT absent as named (the
fold fired first) but the COM tells the mechanism: it creeps forward
+x monotonically from tick 100 (0.0119 -> 0.2765 m by the fall) in
lockstep with the toe error. The fall, narrated: **a slow forward
roll over the forefoot — the toes dorsiflex under the ground reaction,
the support point and the COM advance together, the heel unloads
(pivot_z goes NaN at ticks 1020/1135/1480: moments with NO loaded
contact at all), and past ~0.26 m of COM travel the frame tips.** The
hardware is clean (pivots, coincidence, locks all hold); what is
missing is the operator's datum-1/datum-3 channel: a real stander
arrests exactly this roll by shifting weight BACK through the ankle
(slow channel) long before the toe reaches 0.8 rad. The static-pose
servo holds every joint at bind and has no sway — it watches the COM
leave and corrects nothing. This verdict RE-ORDERS the successors:
the toe fold is not a hardware bug to patch but the named absence of
the balance controller — so the two-channel balance controller (hip
fast / ankle slow, weight-shift sway, deadband + fatigue rotation)
moves UP to first, and passive play (NON-VACUOUS) follows, since both
touch the lock/muscle rows and the controller's authority depends on
what passivity holds.

**BALANCE-PROBE v1 FALSIFIED 2026-08-08 (probe .tmp/probe_balance.py,
ankle-channel capture-point loop, ghost-free config, 8 000 ticks):**
all four legs FAIL — and the failure is the most instructive of the
saga because the data isolates the wrong piece. Head_z: 1.810 @100,
1.812 @1000 (level), then the SAME fall as uncontrolled (1.729 @1416;
forensics had the uncontrolled fall at 1490) and then WORSE: the loop
flails the fallen frame, COM to -3.75 m, max err 3.09 rad (29x), |w|
1 664, KE 2 262 J — debris class. The isolation: the COM trace with
the loop matches the UNCONTROLLED trace tick-for-tick through the
creep (+0.0433 @758 vs +0.0468 @790 uncontrolled) — the loop did
NOTHING during the entire roll, because the named deadband was the
whole support polygon and the capture point only exits the polygon
AFTER the toe has folded 0.5+ rad and the heel has unloaded; the
correction then fires as a full-amplitude bang (off = centroid -
x_ic) at a frame already past recovery, and with no authority clamp
it keeps banging on the debris. **The falsified element is precisely
"polygon = deadband": datum 4's range is NOT the polygon edge (the
edge is where balance is already LOST) — the sway band is a narrow
band around the support centroid, corrected continuously and small,
and the correction must clamp to what the ankle authority can
actually produce.** What the probe did NOT falsify: the measurement
(capture point), the venue (ankle channel), the rate (servo omega_n)
— none of them ever got to act. Successor (one membrane, named):
balance v2 = narrow derived deadband about the centroid (candidate:
the system's own derived small length d_eq_m, the measured joint
play) + proportional correction + authority clamp (the loop lets go
beyond what the ankles can recapture — no flailing).

**PASSIVE-RIGIDITY FORENSICS 1, FALSIFIED 2026-08-08 (probe
.tmp/probe_passive_forensics.py, ghost-free CONTROL, muscles cut
@1200):** the lock rows are NOT the excess rigidity. (b) PASS — the
sag is carried 100% by FREE axes (tarsals 2.57 rad, metatarsals 2.55,
femur 1.61, L5 1.24 @1499); (c) PASS — the sag is slower than the
pendulum (head 1.312 > 0.5 m bar); but (a) FAIL — locked axes are
not frozen (only 86.7% of joints under 0.05 rad locked error @1499,
ankles at 0.21). The frame IS folding through its free axes like a
closing knife — 2.5 rad at the ankle — yet the head is still at
1.31 m, so something ELSE holds it up. The lock-row play-band
membrane is hereby DEAD (it would have made standing worse, not
CONTROL better — exactly what forensics are for). Successor probe
named: ligaments (stiff from rest, k = F_max/d_eq_m, no play band)
vs axial spin vs new furniture contacts.

**PASSIVE-RIGIDITY FORENSICS 2, VERDICT 2026-08-08 (probe
.tmp/probe_passive_forensics2.py, ghost-free CONTROL @1499):** THE
LIGAMENTS ARE THE RIGIDITY. (a) PASS — 25 of 43 sweep ligaments taut,
carrying 1 313 N = 1.67x body weight with every muscle cut: the
frame's passive tissues alone can hold it standing, which no relaxed
body does. (b) PASS — the ankle fold is 100% single-axis pitch (a
real fold, not axial spin; the slow head drop is not a measurement
artifact). (d) PASS — only the two tarsals touch the ground (87 N
each): no furniture, the frame is not resting on new contacts. (c)
FAIL as named, and the failure sharpens the membrane: mean taut
extension is 4.2 mm = 3.2x the d_eq_m design bound (1.31 mm) — the
spring law k = F_max/d_eq_m engages FROM REST with zero play and the
velocity-level solve then lets extensions overshoot the intended
elongation 3x. The anatomical ligament is the opposite shape: SLACK
through the joint's play band, stiff only at its end. **Passive-play
membrane (aimed): ligament rest length gains the measured play —
force = k*(ext - d_eq_m) beyond the band, zero inside it — so a
muscles-cut body folds freely through the play and the elastic wall
only appears at the anatomical limit, where gravity torque and
momentum already exceed the catch.** Uncertainty named before the
A/B: at the folded pose (ext 4.2 mm) force still engages beyond the
band — whether the frame then falls depends on whether the catch
holds at large fold angle; that is exactly what the probe measures.
Open question deferred from (c): whether the 3.2x extension overshoot
is its own membrane (solve softness) — not gated by the play band.

**BALANCE-PROBE v2 FALSIFIED 2026-08-08 (probe .tmp/probe_balance2.py,
d_eq deadband 1.31 mm + proportional + clamp 95.6 mm + anatomical
polygon, ghost-free, 8 000 ticks):** (e) CLAMP HOLDS PASS (|off| never
exceeded the derived 95.6 mm) — and the other four legs FAIL with a
signature that names the culprit: the COM creeps forward FASTER than
uncontrolled (+0.0592 @758 vs +0.0468) with the correction saturated,
the fall lands at the same tick (~1416), then debris (|w| 11 405).
The loop pushes the frame FORWARD. The v2 lean channel inherited
v1's row set: every actuator whose child carries a contact — ankle
(tarsals) AND TOE (metatarsals). Commanding a backward COM shift
through the TOE rows commands a backward tip about the ball of the
foot (the toe joint's pivot), whose ground reaction presses the frame
forward — positive feedback, matching the trace. Datum 3 assigns the
slow channel to the ANKLE only. v2's other pieces are unfalsified:
the d_eq deadband fired early and proportionally as designed, the
anatomical polygon did not chase the fall, the clamp bounded the
flail. Successor named: v3 = v2 with the lean channel restricted to
the ankle rows (one change, per the one-membrane rule).

**BALANCE-PROBE v3 FALSIFIED 2026-08-08 (probe .tmp/probe_balance3.py,
ankle-only lean channel): BIT-IDENTICAL to v2 — every number matches
to all printed digits (head_z, COM, max_err, KE, |w| 11 405, |off|
95.6). The identity itself is the verdict: the toe rows contributed
NOTHING to v2's channel (their lever projection is ~zero at this
geometry), so the "toe rows push the frame forward" theory is
falsified and the forward push — if it exists — comes through the
ANKLE rows themselves, or the channel is inert and v2/v3's divergence
from the uncontrolled trace was set during the settle (max_err @100
differs: 0.162 vs 0.106 uncontrolled — the correction was already
acting before tick 100). Open either way: whether the ankle lean
channel moves the COM WITH the commanded off, AGAINST it (the static
bind-pose derivation inverts in closed loop), or NOT AT ALL
(authority never reaches the COM). Successor named: a sign-forensics
probe — twin runs from one initial state, A with the loop, B with off
forced to zero, divergence vs commanded off measured per tick.

**BALANCE SIGN FORENSICS 2026-08-08 (probe .tmp/probe_balance_sign.py,
twin runs A=loop / B=no-channel, one initial state, 600 ticks):**
WORKS — the channel moves the COM as commanded (D(599) +8.3 mm with
cumulative off +29.0, sign match, (c) PRESENT; INVERTED and INERT
absent). The channel is exonerated; the trace convicts the TARGET:
off_x is +67 mm FROM TICK 0 — the loop commands a FORWARD lean from
the very start, because the anatomical contact-point mean (the
polygon "centroid") sits ~7 cm ahead of the bind pose's achievable
balance (COM +0.0125 at settle). The uncontrolled frame stands level
1 000 ticks precisely BECAUSE the static servo never converges to
that forward reference; v2/v3 closed the loop on it and dragged the
frame into the fall it was meant to prevent. This is the operator's
datum 1 in numbers: muscles lock onto the STABILIZING POSITION THEY
FIND — a measured, achieved equilibrium — not onto a geometric
centroid. (It also re-reads the intrinsic creep: B creeps forward
+16 mm/600 ticks with no loop at all — consistent with the servo
slowly tracking its own too-forward static reference; v4 measures
whether the creep dies when the target stops pulling.) Successor
named: balance v4 = v3 with the target = the ACHIEVED SETTLE
POSITION (mean COM over ticks 50-100, the system's own measured
equilibrium — nothing chosen), deadband d_eq, ankle channel, clamp.
Kernel note: ligament play-band flag (state["lig_play_band"],
rest+d_eq, default off) landed with pytest 201/201.

**BALANCE-PROBE v4 FALSIFIED 2026-08-08 (probe .tmp/probe_balance4.py,
settle-position target (+0.0119,-0.0001) measured ticks 50-100,
ankle channel, d_eq band, clamp):** (e) CLAMP PASS; the other four
FAIL — but the early trace is the diagnostic: +0.0432 @758 matches
the UNCONTROLLED creep (+0.0468), so the target fix removed v2/v3's
forward drag, and still the frame falls at the same tick (~1416)
with the channel saturated at 95.6 mm. Per v4's own named falsifier,
the creep's parent is the STATIC BALANCED REFERENCE itself: the
muscle servo keeps dragging the COM toward its derived forward lean
(~7 cm ahead of the achievable equilibrium) and the balance loop
fights its own servo at limited authority. Datum 1, second reading:
it is the SERVO, not just the loop, that must lock onto the
stabilizing position found. Successor named: v5 = v4 + at tick 100
rebase the static ankle target_offset to the MEASURED settle
theta_err, so the servo holds the achieved position and the creep
dies at the source.

**PASSIVE-PLAY A/B 2026-08-08 (probe .tmp/probe_play_band.py, ligament
play band rest+d_eq_m, ghost-free):** (b) STANDING UNAFFECTED PASS —
MAIN with the band matches without it to <= 34 mm at every
checkpoint (the band is slack in a held pose; the flag is safe to
ship). (a) NON-VACUOUS FAIL, and the forensics-2 uncertainty
resolves: CONTROL with the band still sags to 1.328 m (off: 1.312),
taut tension ROSE to 1 444 N (22 taut) — ligaments stretched ~3x
past the band still hold 1.8x body weight, because the velocity rows
apply UNLIMITED tension impulse (near-rigid in tension). The same
disease as the lock rows, one row over. Successor named: the
ligament force LIMIT — clamp the row's impulse to the
physiological F_max * dt (F_max is already in the ligament table;
stiffness = F_max/d_eq_m derives from it), so an overstretched
ligament YIELDS and the relaxed body crumples past the catch.

**BALANCE-PROBE v5 FALSIFIED 2026-08-08 (probe .tmp/probe_balance5.py,
static reference rebased to the measured settle theta_err — ankle
t_off -0.0900 rad vs the derived -0.0675):** (e) CLAMP PASS; all
others FAIL, and the verdict closes a whole branch: across FIVE
controller variants (no loop / polygon deadband / anatomical polygon
/ settle-COM target / settle-rebased servo) the creep proceeds
IDENTICALLY (+0.043 @758, fall ~1416) — no reference or target or
loop above the ankle touches it. The creep's parent is below the
controller layer entirely, at the roll's pivot: the TOE joint's own
servo/authority (the forefoot group is the weakest actuator in the
table: 6.0 kg PCSA, 0.020 m moment arm — and the forensics' first
mover was metatarsals, leading the head by 180 ticks). Successor
named: toe-authority forensics — are the metatarsals motor rows
saturated (|impulse| at lmax) through the creep while the ankle rows
are not? If yes: the roll is a physiological authority question
(is the forefoot spec right?), not a control question. If no: the
toe servo has authority and doesn't correct — then the toe's
reference/measurement is the address.

**OPERATOR DATUM 6, 2026-08-08 (THE HUMAN terminal, the posture
OBJECTIVE — recorded verbatim):** "Head height is a reward: the human
needs to be as tall as possible to see — the elevation it acquires,
the more [it reads of the] environment."  Consequences for the
membrane stack: (1) the standing controller's objective is not
"hold the pose" but MAXIMIZE HEAD HEIGHT subject to the balance band
(datums 1/4) and the energy budget (datum 4) — posture is a
sensing strategy: elevation buys environmental read, so a stander
extends, it does not merely not-fall; (2) this explains the neck's
lead in datum 5: the neck stabilizes the sensor platform (the head)
at its maximum elevation first, and the chain below organizes to
afford it; (3) for the probe suite: head_z is not just the fall
detector — it is the REWARD SIGNAL, and a standing controller that
stands at 1.75 m when 1.81 is available is failing the objective
even if every balance bar passes; the demo's standing leg should
report achieved head height against the skeleton's maximum, not only
against the no-fall bar.

**TOE-AUTHORITY FORENSICS, FALSIFIED 2026-08-08 (probe
.tmp/probe_toe_authority.py, ghost-free, ticks 100-1200):** nobody is
saturated. Toe rows at >= 95% lmax for 1% of creep ticks, ankle rows
0% — (a) FAIL, (b) PASS, (c) FAIL as measured (forefoot reaction
moment reads 0.0: the contact spec attaches ALL contacts to tarsals,
none ahead of the MTP joint — a spec gap named, not patched). The
servo HAS authority and doesn't use it. The actuator table (measured,
no sim): toe rows m_sub 3.53 kg vs ankle 74.11 kg — the toe muscle's
gain derivation supports ONLY THE TOE BONES (kp 0.091 vs the ankle's
1 598.7, omega_n 1.45-1.66 alive but tiny-gained, tau_lim 2.25 N m vs
75). In standing, the toe muscle's real load is the BODY's roll
moment over the MTP, not the toes' weight — the gain law's subtree
logic misassigns the load path at exactly the joint the forensics
named first mover. Successor: a single-row time-series probe
(theta_err, target, lambda, achieved w_rel, error, ticks 100-1300)
to name WHERE the chain breaks — command (target small), impulse
(lambda small vs needed), or tracking (w_rel achieved yet error
grows — geometry).

**TOE-CHAIN TIME SERIES 2026-08-08 (probe .tmp/probe_toe_chain.py,
row 102 metatarsals_R, ticks 100-1300):** IMPULSE — the chain breaks
at delivery. The command is ALIVE and correct (target -0.153 ->
-0.649 rad/s, tracking the growing error exactly as the servo law
prescribes); the tracking bar is not the issue; but the solved
lambda sits at ~30% of lmax through the creep while the achieved
w_rel goes the WRONG WAY (+0.41 vs target -0.31 @800; |w_rel -
target| mean 1.20 rad/s). The direct solve satisfies its equality
rows exactly, so the overwrite lands AFTER the solve: the post-solve
LIGAMENT SWEEP rewrites the foot's velocities with unlimited impulse
(1 313 N of taut tension vs the toe muscle's 2.25 N m — 30:1). The
toe servo never lost; it was overruled after the verdict. This
convicts the same row as the NON-VACUOUS failure — the unlimited
ligament tension — from the opposite direction: it makes the held
stand too WEAK at the toe (muscles overruled) and the cut body too
STRONG (frame held without muscles). The ligament force-limit
membrane (clamp the row to f_max * dt, f_max = g * heavier subtree,
already derived in the table) is hereby the named fix for BOTH.

**FORCE-LIMIT FULL PROTOCOL, FALSIFIED 2026-08-08 (probe
.tmp/probe_force_limit.py, lig_force_limit + lig_play_band,
ghost-free):** only (d) RIG STABILITY passes (coinc 1.33 mm). MAIN
still falls at ~1416 (head 1.737 @1416, -0.735 @4000), toe error
still leads (0.64 @1416, 0.81 @2000), CONTROL still sags (1.330 —
identical to play band alone). The clamp barely binds, and the
record must say why: f_max = g x heavier subtree was the STATIC LOAD
CRITERION of the stiffness derivation, not a yield ceiling — clamped
there, 25 ligaments still apply ~20 N s per tick, sustained, against
the toe's 0.002 N s. The ligament-tension venue is hereby CLOSED by
exhaustion: play band, force limit, both — the fall does not move.
Five controller variants and two ligament membranes all fail at the
SAME tick: the standing fall is not an overruling, not a target, not
a reference, not an authority. What has never been measured: the
TORQUE BUDGET at the MTP joint itself — who applies the dorsiflexion
moment that grows the toe error from tick 100 (ligaments pre-taut at
bind? joint coincidence reaction? the contact spec's tarsals-only
attachment putting the forefoot's ground reaction where anatomy
doesn't?). Successor named: toe torque-budget forensics — per-tick,
per-source moment about the MTP axis: ligament, joint reaction,
servo, gravity, contact. Also on record: the demo battery's verdict
window (t >= 1200 over 8 000 ticks, demo_kinematic_v2.py) equals the
saga's bar — no shortcut exists; the stand must hold 8 000.

**MTP TORQUE-BUDGET, RESIDUAL WITH A BOOKKEEPING CAVEAT 2026-08-08
(probe .tmp/probe_toe_budget.py, ticks 100-800):** the toe's one
ligament is SLACK (0.0000 N m — ligaments exonerated AT THE TOE),
servo +0.67 vs gravity -0.44 (the servo outmuscles gravity), and the
"joint" term (-1.36) failed its 3x bar — but on accounting, not
physics: joint_impulses_ang is recorded about the body COM, not the
joint center, so that term mixes frames and is struck from the
record. What survives: the servo wins its local budget and the toe
STILL dorsiflexes against command (w_rel +0.4 vs target -0.3,
toe-chain probe) — the overwrite is post-solve, and with ligaments
slack at the toe the only post-solve writer left at the foot is the
v3e HYBRID FRICTION SWEEP: every contact point attaches to tarsals,
and the swept friction impulses act at those points with real levers
about the ankle and MTP — a per-tick forward rotation the solve
never sees and no servo can answer. Fits the saga's fingerprint:
identical fall tick in every configuration (the contacts never
changed), nobody ever saturated. Successor named: contact-moment
budget — normal vs friction reaction moment about the ankle and MTP
joint centers (impulse at world point x lever; no impulse-frame
ambiguity), vs the servo moments, over the clean creep window.

**CONTACT-MOMENT BUDGET, BALANCED 2026-08-08 (probe
.tmp/probe_contact_moment.py, ticks 100-800, tarsals_R):** the ground
loop is CLEAN — friction moment 0.2x the servo trim, normal 1.4x,
both under the 2x bar; and all three traces grow together in the
same direction, the signature of moments DOWNSTREAM of the creep
(COM advances, gravity moment grows, ground reaction shifts, servo
trims harder) rather than its cause. The v3e hybrid is exonerated.
One post-solve writer at the foot remains unmeasured: the LIGAMENT
SWEEP's moment about the ANKLE (the toe ligament was slack, but the
taut population clusters at the ankle/midfoot — 25 taut, 1 313 N,
applied post-solve every tick the same way the toe-chain probe
caught). Successor named: ankle ligament-moment budget.

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
