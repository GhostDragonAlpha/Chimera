# R5 — PREREGISTERED CHECKLIST (frozen before any run)

Reviewer: R5, non-author of F01–F08. Laws: READ-ONLY outside
agents/R5_forest_review/; CPU-only headless; preregister first.

## A. Cross-artifact identity
- A1 Recompile all four declarations from the recipes in fresh subprocesses;
  byte-compare vs committed files. Expected self-pins / file sha256:
  clearing aa2607df…/18dd2ff6…; terrain 8c7d60c8…/446ed3fb…;
  trunk b7089e78…/94ff906e…; routes 7c3ad6e8…/28dff2b3….
  FALSIFIER: any byte drift or self-pin mismatch.
- A2 Mutual pins: trunk.site.provenance.declaration_sha256 == clearing body pin;
  route inputs pin all three upstream file_sha256 + self pins; loader receipt
  re-states them. FALSIFIER: any pin naming a digest the tree does not reproduce.
- A3 Trunk site one number everywhere: F01 trunk_sites[0].site_m ==
  F03 site.base_centre_m == F07 routes.trunk_axis_m == F07 B2.site_m ==
  F08 initial_state.trunk_site.base_centre_m == (11.976783, 0.0, 2.471766).
- A4 Spawn one number everywhere: F01 == F03 approach_and_bounds ==
  F07 routes.spawn_m == F08 initial_state == (0,0,0).
- A5 Route graph vs F04 blocking causes: B2 r_block = 0.037+0.250 = 0.287;
  recompute the 801x801 @0.05 m blocked-cell count (expect 107, all B2);
  N1 slope never fires (expect 0 slope-refused cells); the predicate has no
  post term (N2 structural). FALSIFIER: any blocked cell whose cause is not B1/B2.
- A6 F08 initial_state_sha256 == c3286e14… reproduced from scratch.

## B. Integrated scenario (my own, headless, loader-driven)
- B1 load_forest() from repo root; receipt artifacts byte-checks green.
- B2 F02 surface at trunk site and spawn: height 0.0, gradient (0,0),
  normal (0,1,0), classify inside.
- B3 F04-style trunk SDF: on-axis analytic sdf = -0.037; tangency worst
  |sdf - r_sole| at declared law ~0; base-cap disk over footprint flush on the
  terrain (recompute worst |terrain h| over the disk).
- B4 F07 corridor: R0 sample walk from spawn; clearance profile; blocked-sample
  count 0 up to the declared stop; BFS corridor min clearance 0.538 at (11.3,2.0)
  re-derived coarsely.
- B5 Negative/edge coordinates: height/gradient/normal at the four closed
  corners; refusals at +-1e-9 past each edge; on-node clamped max edge.
- B6 Site slope truth: gradient_at at the site == analytic gradient; distances
  from the site to all five mound centres exceed their radii.

## C. Citation spot-checks (3 per item, 24 total)
F01: bytes 13,112 + aa2607df/18dd2ff6; worst grid slope 0.034606; posts 80,
gap 1.0, off-edge 0.0; clearance 11.729184690233646.
F02: bytes 877,752 + 8c7d60c8/446ed3fb; mesh 13,920v/13,920i/4,640tri
(3,200+1,440); worst triangle slope 0.042522 at (17,7); mesh-analytic 6.46 mm
at (19.5,5.5).
F03: bytes 16,634 + b7089e78/94ff906e; H 1.158 = (0.419+0.482)+(0.125+0.132),
R 0.037 = 0.074/2; rep error 1.78307e-4 vs sagitta 1.78165e-4; energies
113.992539 / 25.298862 J.
F04: run.json 10,442 B sha efded804…, 13/13; INT-01 worst 7.043e-16; INT-03
flush 0.0; VIS-03 overlap 0.2327.
F07: bytes 8,495 + 7c3ad6e8/28dff2b3; 641,494 free / 107 blocked all B2;
corridor 0.538 @ (11.3,2.0), R0 min clearance 0.502; analytic slope 0.037956.
F08: 66/66 GREEN, initial_state c3286e14…; worst_triangle_slope
0.042522289331596436 via the loaded surface; forest_loader sha 53d7fdde…,
verify_loading sha fc4d34ab….

## D. Falsifier mining (notes; each either measured or bounded)
- D1 R0 endpoint semantics: route_declaration says R0 "ends at the contact ring:
  dist_to_axis = r_block" but carries to_m = trunk axis and length_m = 12.229185
  (the full axis distance). MEASURE: dist_to_axis at t = length_m along R0;
  read route_recipe/verify_routes for the frozen semantics. FALSIFIER: the
  committed declaration's numbers and its own note cannot both be true.
- D2 Negative-coordinate behavior of terrain_query (float negation, -0.0,
  clamped max edge, refusals).
- D3 Trunk flushness at the site's local gradient (analytic y=0 vs F02 surface
  vs render mesh triangles under the footprint).
- D4 Posts straddle the physical edge (render-only, NO-CLAIM): a walker pushed
  against the extent visually overlaps posts; recorded, not a defect, but W10
  must not read post contact as physical.
- D5 Mound 2 (19.265584, 6.057064) R 4.329635 crosses the east edge (reaches
  x=23.6): its analytic continuation is unrendered/unquerable past |x|>20 —
  does any declaration claim otherwise?
- D6 F-row "done when" float against reality, esp. F02 (render vs collision
  surfaces agree — but no native heightfield contact exists in the engine),
  F04 (L1-only), F08 (teardown adapter is new data-layer machinery, cited to
  SessionFlow's shape).
- D7 Loader initial_state route_graph fields equal F07's declaration verbatim.
- D8 Re-run author suites from scratch where they write NOTHING outside their
  own already-owned dirs or my dir; byte-compare fresh run.json against the
  committed receipts (F04, F08). If a verifier would overwrite sibling files,
  run it only in observation mode / skip with note.

## E. W10-readiness verdict
W10 row: "Player can walk, turn and stop in the scene on a supported surface;
numerical and visual receipts match." Judge the forest front's contribution and
name the remaining gap precisely (expected: engine-side heightfield/prop contact
service + trained walking policy — outside this front).

FROZEN. Executed below; results in receipts/ and report.md.
