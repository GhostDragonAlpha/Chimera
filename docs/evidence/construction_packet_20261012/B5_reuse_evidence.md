# B5 — part/connector reuse and the broader shape grammar

GAME_PLAN_ACTION_RPG.md §13, B5 gate row: *"reuse function and broaden
shape"* — evidence column: *"Reuse the cradle/frame parts in a bridge or
hoist; extend cutting/meshing to concavity, holes and branch junctions
when qualified"*; acceptance: *"One part/connector works in multiple
contexts; torus/concave/triple-junction cases pass; no hand-authored
genre-specific replacement physics."* Two halves, both measured: a
partition half (`b5_shapes.py` + `test_b5_shapes.py`, 6/6) that compiles
the torus/concave/triple-junction/oblique-partition cases through the
**unchanged** `tools/material_volume.py`, and a runtime half
(`test_b5_bridge.py`, 4/4, run 6× consecutively green) that reuses the
B2/B3/B4 generators, the B4 weld connector and the B4 cradle block
verbatim as a suspended-span bridge on the resident engine (port 8793).

## What was built

**Partition half** (`tools/construction_packet/b5_shapes.py`). Every
shape is a tetrahedral partition in the compiler's own idiom: axis-
aligned boxes are Kuhn/Freudenthal-triangulated (6 tets per box, bit-
ordered corners, grid-adjacent boxes sharing the face diagonal so unions
are conforming), and the oblique chamber uses the same bit-order on
skewed hexes. Nothing extends the compiler — the module docstring states
it and the commit touches no compiler line. Three instruments make the
gate checkable:

- `boundary_genus(boundary_faces)`: χ = V−E+F over the **compiled**
  boundary faces, genus = (2−χ)/2 — the hole is counted from what the
  compiler accepted, not from the author's intent.
- `inside_solid(vertices, boundary_faces, point)`: fixed +x ray parity
  (Moeller–Trumbore) over the compiled boundary — "the hole remains a
  hole" and "the notch is not filled" become point queries.
- refusal controls: functions that must return a named `CompileError`
  (raising `AssertionError` if accepted) — "reject unsupported geometry
  instead of filling it silently" is a test, not a promise.

**Runtime half** (`tools/construction_packet/test_b5_bridge.py`). Two
granite piers and a timber deck, every part emitted by the same
`b2_scene_gen.box_document` + rung derivation that built the B2 wedges,
B3 stack and B4 block; joined by the same weld document the B4 cradle
clamp used; loaded by a part byte-identical (mass, inertia, µ) to the
B4 cradle block. The deck is a **suspended span**: its soffit sits 60 mm
above the pier tops and its corners overhang by 60 mm, so every
deck↔pier vertex pair stays outside the 50 mm part-part contact radius —
the only load path deck→piers is the connector. `b5_bridge_frame.png`
shows it: piers red/green, deck blue, load yellow, each hue verified at
its projected pixel.

## Measured — partition half (compiler unchanged)

| shape | cells | volume m³ | mass kg | boundary χ / genus | interfaces |
|---|---|---|---|---|---|
| ring frame (torus case) | 48 | 0.020 (rel 1e-12) | 54.000 | **0 / 1** | 0 |
| concave L | 18 | 0.032 | 52.800 | 2 / 0 | 1 pair, 0.040 m² |
| triple junction | 24 | 0.048 = envelope | 166.200 | 2 / 0 | **3 pairs, 6 faces, 0.140 m²** |
| oblique chamber | 12 | 0.091683208333 | 284.70191 | 2 / 0 | **1 pair, 2 faces, 0.253064704 m²** |

- **Gallery #4 (hole):** the ring frame compiles complete with boundary
  χ = 0 → genus 1; the hole centre (0, 0, 0.03) is OUTSIDE the solid
  while tube points (0, −0.25, 0.03) and (−0.25, 0.07, 0.03) are inside
  and above-centre (0, 0, 0.30) is outside — the hole remains a hole.
  Refusal controls: the pinched ring (edge-contact wall) is refused
  `non_manifold_boundary`, a flat-wall shell `degenerate_tetrahedron`,
  an inverted tet `inverted_tetrahedron` — unsupported geometry is
  rejected, never silently filled. The concave L's notch point
  (0.4, 0.11, 0.3) is outside while both legs' interiors are inside, and
  the compiled volume (0.032) is strictly below the bounding box.
- **Gallery #5 (branch junction):** three regions meet along the edge
  (0.3, 0, 0.2)–(0.3, 0.2, 0.2); the compiler reports exactly the three
  region pairs and six interface faces, every interface triangle carries
  a junction vertex, the volume equals the envelope exactly (no
  duplicated wall, no gap), and ownership is complete (no ambiguous
  region).
- **Gallery #3 (oblique partition):** the lopsided quadrilateral
  footprint (0,0)-(0.62,0.02)-(0.55,0.47)-(0.04,0.43) is cut by the
  plane through I0–I2; the interface area matches the analytic
  parallelogram to 1e-12, the interface normal (−0.1476, −0.0984,
  0.9841) lies in the plane's own normal to >0.9999 while |n_z| = 0.984
  < 0.999 proves the cut is oblique; the separator is ONE interface pair
  (counted once); each region compiled solo is a closed genus-0 solid;
  region volumes and masses sum to the whole (inventory preserved).

## Measured — runtime half (engine unchanged)

**Statics — the connector is the whole load path.** At rest the deck
hangs with zero contact pairs (`contacts_pp_active = 0`): weld forces
5.474 N each, 2 × 5.474 = 10.948 N = deck weight exactly; each pier's
ground reaction 54.740 N = own weight 49.266 + weld pull 5.474;
`total_reaction_n` = `total_weight_n` to 5e-5.

**Eccentric load — the connector law composes with the contact law.**
The 0.848 N load (the B4 block's exact mass/inertia/µ) sits at x = 0.17,
α = 0.32 between the weld centres. The published B2 contact law applies
each pair's torque about the VERTEX OWNER's COM (`pp_pair_`:
`Ts -= (P − o.c) × f`), so a footprint symmetric about its own COM
exerts zero couple however off-centre it sits — the load enters the deck
through its COM and both welds must share it exactly. Measured pier
deltas 0.4235 / 0.4247 N vs LOAD_W/2 = 0.424 N (0.3%), weld total
DECK_W + LOAD_W, and the deck COM sinks 0.300 mm vs the series-
compliance law 0.298 mm (weld stretch 0.212 + pier rung sink 0.086).
The same F = k·stretch the B4 cradle verified, now in series with the
rungs.

**Sever — removing exactly one connector.** `weld_remove` while paused:
the weld list goes 2 → 1; 0.10 s after release (pre-impact window) the
deck is still suspended (y > 0.30) swinging on the surviving weld at
0.58–0.64 m/s with the load riding it (0.42–0.48 m/s — the deck surface
accelerates at ~4.7 m/s² < g, so contact holds), and the surviving
connector is still engaged. After the collapse: scene not diverged, one
weld left, the load on the ground plane carrying exactly its own weight
(0.848 N), ground still carrying the whole scene.

**Frame.** `b5_bridge_frame.png` (1920×1009): projected-pixel hue probes
name pier_a red (1075, 377), pier_b green (810, 413), deck blue
(960, 344), load yellow (1014, 272); telemetry at capture: welds
5.8978 N each = (DECK_W+LOAD_W)/2, reactions 55.1636 each,
total_reaction = total_weight = 110.3272 N, energy drift −0.026 J.

## Engineering findings (authored-scene physics, not engine changes)

1. **Anchor sets must be moment-symmetric.** The first anchor layout
   z = (−0.02, −0.02, +0.02) has mean z ≠ 0, so each weld applied a net
   r × F couple even at equilibrium stretch: the deck tipped 2° in
   0.25 s and the swing dragged the 49 N piers over at t ≈ 1.5 s.
   Z- and x-symmetric anchors (−0.02, +0.02, 0 about the pier centre)
   made the suspended bridge an exact equilibrium (speed 0.0000,
   quaternion identity, drift +0.009 J).
2. **The 50 mm contact radius is a design constraint for clearances.**
   A 20 mm soffit gap measured spurious near-boundary contact pairs that
   walked the bridge apart; 60 mm on every deck↔pier pair keeps the
   connector the only path.
3. **What the sever test does NOT assert.** The wedged end state of a
   0.62 m deck collapsing against 0.06 m piers is bistable (measured
   pier_b reactions 42.8–103 N depending on where the deck lands), and
   the sever launches a spring-mass engagement transient (ω ≈ 42 rad/s)
   that makes weld force phase-sensitive for ~0.3 s. The quantitative
   "removes exactly its contribution" claim is therefore the STATIC one
   (pier_b carried the weld pull: rb0 − W = 5.474 = weld force) plus
   connector bookkeeping; the collapse is asserted only to be
   survivable and to end with the load on the ground.

## Test battery

`tools/construction_packet/test_b5_shapes.py` — 6 tests: ring genus/volume/
mass + containment probes, three refusal controls, concave L, triple
junction, oblique chamber (area vs analytic, obliqueness, solo-region
closure, additive inventory), inventory JSON contract.
`tools/construction_packet/test_b5_bridge.py` — 4 tests, 6 consecutive
clean runs: statics + connector law, sever redistribution, part/
connector reuse identity (field sets and byte-equal mass/inertia/µ vs
the B4 block and B3 layer documents), frame pixel naming.

## Gate honesty

- "One part/connector works in multiple contexts" is evidenced by
  identity (the load part's mass/inertia/µ equal the B4 block's to the
  printed digit; every bridge part is `box_document` output with the B3
  layer field set) plus function in a new load topology (suspended span
  where B4 was a clamp across a gap).
- "Torus/concave/triple-junction cases pass" means they compile through
  the unchanged compiler AND the genus/hole/junction claims are read
  back from compiled output (χ over boundary faces, ray parity,
  interface tables), not from author metadata.
- "No hand-authored genre-specific replacement physics": this commit
  changes no engine file and no compiler line; the bridge is authored
  entirely from the existing generators and the existing connector
  document.
