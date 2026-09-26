# F04 Report — ground and trunk contact geometry verification

Author: M-F04. Date: 2026-09-24. Checkout `E:/ChimeraWork/monkey-play-20260924`,
branch `monkey-play-20260924`. Item F04, verbatim: "No unacceptable tunnelling,
ghost support, interpenetration or visual/collision disagreement in frozen cases.
Only claimed collision capabilities must be demonstrated." Contracts C08 (contact/
collision), C14 (terrain), C15 (trunk surface). Depends on F02 + F03 (both
integrated and validated at load: `terrain_query.load` re-proves the bundle,
`trunk_recipe.validate_declaration` re-proves the trunk declaration against the
LIVE F01 file — no `f02_*`/`f03_*` refusals).

## What was done

1. **Read the three artifacts** (F01 clearing declaration, F02 terrain bundle +
   query + report §5 follow-ups, F03 trunk declaration + HANDOFFS "To F04") and
   the engine's contact machinery (`gait_controller.hpp` 94/36/52/635-645/716/
   1727/1961/2005-2010, `earth_environment.hpp` 67/110/118, `graph_earth.hpp`
   26-30/82/100, `main.cpp` 736/751/764).
2. **Froze the case matrix BEFORE implementation** (`PREREGISTRATION.md`): 12
   cases + 2 harness-sensitivity controls, every bound derived from pinned numbers
   (r_sole 0.004 m `gait_scene.py:28`; kTouch 1e-5 `gait_controller.hpp:36`;
   dt <= 1/300 s `gait_controller.hpp:1961`; v_max 1.01 m/s
   `derived_numbers.json timing_paper.simulated_before`; trunk TOL 2e-4 m
   `trunk_declaration`; F02's frozen 1e-9/1e-12 tolerances; F01's 0.05 slope law).
   Two-layer separation declared up front: **L1** = the declared geometric contact
   model (terrain triangulation query + analytic trunk cylinder vs the walker's
   sole points under the engine's own gap law), verifiable now; **L2** = the
   engine-integration status, recorded as the gap statement below (frozen-core
   law: record, never edit C++).
3. **Implemented the suite** (`verify_contact.py`, stdlib-only, CPU, headless):
   exact capped-cylinder SDF; exact point-triangle distance (Ericson 5.1.5) for
   render-mesh queries; the engine gap law `gap = point_y + r - h` verbatim
   (`gait_controller.hpp:635-643`, `gait_scene.py:178`); seeded sweeps
   (seed 20260924); receipts `run.json`/`run.txt`.
4. **Ran it** (deterministic: two fresh-process runs byte-identical, 10,442-byte
   run.json, sha256 `efded804…b70e6a`, `receipts/determinism.txt`). 13/13 verdicts
   green (11 PASS + 2 PASS-AS-DECLARED), both controls fire. Exit code 0.
5. **Wrote the L2 gap statement + handoffs** (`HANDOFFS.md`, G01/G04 consumers).

## Measured numbers (per case; full detail in `receipts/run.json`)

| Case | Verdict | Numbers vs frozen bound |
|---|---|---|
| TUN-01 through-face terrain (7 sweeps: worst-slope centroid, 5 mound crests, 45-deg terrain-following onto (19.5,5.5), trunk-site cell) | PASS | 7/7 caught at the declared tick (dt=1/300, v=1.01 m/s); worst penetration 1.0000e-3 m <= 3.3667e-3 m per-tick bound (vertical), <= 1.6812e-4 m (terrain-following; worst ratio 0.297) |
| TUN-02 ridge-skip CONTROL | PASS (control fires) | flyover at law-rest height, 4.329635 m samples, half-step phase: min sampled gap 3.0702e-2 m > kTouch -> MISSED, while the true path grazes gap=0 (non-vacuity of the harness) |
| TUN-03 head-on trunk | PASS | caught at s_tick=3.3667e-3 m spacing, pen 1.0000e-4 m <= 3.3667e-3; CONTROL at 0.164 m spacing (> 0.082 m catch chord 2R+2r_s): min sdf 0.043 m > r_s -> MISSED |
| TUN-04 crease/edge sweeps | PASS | 500/500 seeded edge drops caught (worst pen 1.0000e-3 <= 3.3667e-3); worst twisted cell (36,28) diagonal-split 7.023e-3 m; edge continuity: worst |dh| 8.1888e-7 m at eps, ratio 0.0868 <= 0.2 (derived 4x0.05), linear-identity residual 1.887e-16 <= 1e-9 |
| GHO-01 outside extent | PASS | 12/12 probes (strict >, each edge +1e-9/+1e-6/+0.5): classify "outside" AND height/gradient/normal all refuse `f02_outside_extent` |
| GHO-02 floating support | PASS | 5 probes (spawn + 4 mound-pair midpoints): law-rest gap exactly 0 (<= 1e-15); floating +1e-4 gap = 1.0e-4 > kTouch (no support claimed); geometric-tangent reading = 8e-3 (see misses) |
| GHO-03 trunk volume/void | PASS-AS-DECLARED | axis probes: analytic sdf = -0.037 (inside the solid) while mesh-only distance = 0.036822 (the declared analytic-vs-render split); mid-facet shell: mesh-tangent sphere pen 1.78165e-4 m and analytic-tangent ghost gap 1.78307e-4 m, both <= TOL 2e-4 |
| INT-01 sphere vs trunk solid | PASS | 320 lateral + 66 cap + 32 rim tangency: worst \|sdf - r_s\| = 7.043e-16 <= 1e-9; 4,096 seeded non-contact: zero penetration, min margin 2.3028e-4 m; 256 interior: max sdf -0.02332 (all inside, expected) |
| INT-02 vertical-law slope submergence | PASS | 3,200 triangles: worst r(1-n_y) = 3.6114e-6 m at slope 0.042522 <= derived legal bound 4.9906e-6 m (18.1% of the 2e-4 TOL) |
| INT-03 trunk base vs terrain | PASS | 65 cap-disk + 81 footprint-grid samples: worst \|terrain height\| = 0.0 exactly; gradient (0,0): coplanar joint, zero gap, zero penetration |
| VIS-01 terrain render vs collision (trunk ring + boundary) | PASS | 2,500 ring + 400 boundary samples: worst height disagreement 6.939e-18 <= 1e-9; worst normal component disagreement 0.0 <= 1e-12; classify inside at the closed edge; ring is exactly flat (0.0), analytic-vs-collision on the ring 0.0 (declared global discretization 6.46e-3 m unchanged, F02's) |
| VIS-02 trunk render vs analytic | PASS | chord error recomputed from the stored vertex table 1.78307e-4 m == declared (diff 3.9e-11), = sagitta + 1.42e-7 <= 2e-7, <= TOL 2e-4; 128/128 triangles outward; worst vertex off-surface 3.67e-7 <= 1e-6 |
| VIS-03 posts render-only | PASS-AS-DECLARED | declared post 30 (20,0,0) of 80: collision query serves ground ONLY; sole-sphere center 1.7321e-2 m from post mesh; law-rest sole point 1.7776e-2 m; body-envelope sphere (r=0.25) overlap depth 0.2327 m — measured, declared render-only, NO capability claimed |

## Prereg misses and adjudications (recorded, not tuned away)

1. **GHO-02 (falsifier F-b: NOT FIRED; prediction missed).** The prereg's
   "sphere tangent at h + r_s must report gap == 0" presumed geometric tangency.
   Measured: gap = 8e-3 = 2*r_sole. Diagnosis: the engine's own law is
   `gap = point_y + r - surface` (`gait_controller.hpp:635-643`, `gait_scene.py:178`
   — and the walker's seat validation `gait_scene.py:400` confirms rest at
   `point = plane - r`): the law's zero-gap rest is `point_y = h - r_sole`.
   Adjudication: NOT a ghost — the divergence is one-sided (the law claims contact
   LATER than naive geometry, never earlier), so falsifier F-b ("support claimed
   where no surface exists") does not fire; the law-rest bound (gap == 0 <= 1e-15)
   holds at all 5 probes. Handed to G01 as the convention note.
2. **TUN-04 continuity (falsifier F-d as literally frozen: FIRED once, then
   adjudicated).** The frozen absolute 1e-9 bound on |dh| across an edge ignored
   that the value difference across a crease scales LINEARLY with the probe eps
   (each side is exactly linear): measured worst |dh| = 8.1888e-7 m at eps up to
   1e-5 — value continuity HOLDS (ratio 0.0868 <= derived 4x0.05 = 0.2; signed
   linear-identity residual 1.887e-16). The frozen bound was mis-derived, the
   corrected bound is derived from F01's slope law, and the miss is recorded here.
3. **TUN-04 pen bound application (implementation correction).** The prereg's
   1.6812e-4 m terrain-following per-tick bound was initially applied to VERTICAL
   drops; a vertical drop's derived per-tick travel is s_tick = 3.3667e-3 m
   (TUN-01's bound). Each case now carries its own derived per-tick bound,
   matching F-a's wording ("its derived per-tick bound"). No measurement changed.
4. **INT-02 bound arithmetic slip in the prereg.** Hand arithmetic wrote
   4.9938e-6; the exact evaluation of the same formula is 4.990644e-6 (implemented
   in code). Direction and verdict unaffected (measured 3.6114e-6 = 72.4% of the
   bound).
5. **Case-parameter corrections forced by declared laws (not bound changes).**
   TUN-02's flyover moved from mound 1 to mound 5 (the only crest with room for
   the full step span inside the extent rule — `f02_outside_extent` refused the
   original probes), and its sample phase is half-step offset (a control modeling
   a MISSED crossing cannot place a sample exactly on the crest; the first run's
   symmetric phase landed gap = 0.0 and "caught"). TUN-04's continuity seeds are
   restricted to interior edges (eps probes on both sides must stay on-patch).

## Falsifier verdicts (frozen set F-a..F-d)

- **F-a tunnelling: NOT OBSERVED.** Every swept case at the declared tick/speed is
  caught with penetration within its derived per-tick bound; both harness controls
  (TUN-02 ridge-skip, TUN-03b chord-jump) FIRE, proving the detector can miss.
- **F-b ghost support: NOT OBSERVED.** No surface past the strict-> extent
  (12/12 refusals); no support claim outside the touch band (floating probes
  1e-4 above rest report gap 1e-4 > kTouch); the trunk void is closed by the
  declared analytic contract (mesh-only reading would ghost by 0.037 m on-axis —
  the declaration names the analytic solid as the collision representation, and
  the <= TOL shell split is the declared representation error).
- **F-c interpenetration: NOT OBSERVED.** Trunk tangency exact to 7.0e-16; zero
  non-contact penetration (min margin 2.3e-4); slope submergence 3.6114e-6 <=
  4.9906e-6; base joint exactly coplanar (0.0).
- **F-d visual/collision disagreement: NOT OBSERVED beyond declared tolerances.**
  Terrain render-vs-collision 6.9e-18 m / 0.0 (F02's frozen family, re-verified
  at the trunk neighborhood and boundary); trunk chord error = declared
  1.78307e-4 <= 2e-4; posts measured render-only with the envelope overlap
  (0.2327 m) recorded under an explicit NO-CLAIM (the item's own observation
  clause: only claimed capabilities must be demonstrated — post collision is not
  claimed anywhere in F01/F02/F03 or the engine route survey).

## The L2 engine-service gap statement (for G04; full version in HANDOFFS.md)

The frozen engine supports exactly ONE contact topology today: contact-point
spheres vs ONE ground plane. Citations: `gait_controller.hpp:94` (single
`plane_model_y_` for all points), `:635-643` (vertical gap law), `:645`
(contact rows carry only the plane's y-normal), `:716` (discrete-cone Coulomb
solve), `:1727` (kTouch + speed engagement gate), `:1961` (dt <= 1/300, 4
substeps), `:2005-2010` (ONE `contact_plane_height_m`; friction in [0,1];
1..8 contact points), `earth_environment.hpp:67,110,118` (sphere-vs-plane;
strict-> out_of_patch), `graph_earth.hpp:26-30,82,100` + `main.cpp:736,751,764`
(meshes are render-only; no collision query route exists in the HTTP contract).

Consequently NONE of F04's cases can be exercised in-vivo today: terrain-heightfield
contact does not exist (the walker's plane is ONE height — even the TERRAIN is
beyond the current walker contact model); trunk contact does not exist (no
rigid-prop machinery at all); multi-surface support (ground+trunk, non-(0,1,0)
normals) has no solver rows to live in; there is no continuous-collision detection
(the kTouch tick band vs the plane is all). Per the frozen-core law this is
RECORDED, not patched: G04's prerequisite is a separately-gated, preregistered
engine task (per-point surface service implementing F03's analytic contract + F02's
terrain query, multi-normal rows into the existing friction solve, a collision
query route, and the measured bark friction) — no C++ was touched in F04.

## Integrity paste (git status --porcelain -uall at completion)

```
 M tools/monkey_campaign/agents/U02_camera/receipts/latency_run.json
?? tools/monkey_campaign/agents/F04_contact/HANDOFFS.md
?? tools/monkey_campaign/agents/F04_contact/PREREGISTRATION.md
?? tools/monkey_campaign/agents/F04_contact/brief.md
?? tools/monkey_campaign/agents/F04_contact/receipts/determinism.txt
?? tools/monkey_campaign/agents/F04_contact/receipts/run.json
?? tools/monkey_campaign/agents/F04_contact/receipts/run.txt
?? tools/monkey_campaign/agents/F04_contact/report.md
?? tools/monkey_campaign/agents/F04_contact/verify_contact.py
?? tools/monkey_campaign/agents/R4_intent_review/PREREGISTERED_CHECKS.md
?? tools/monkey_campaign/agents/R4_intent_review/brief.md
?? tools/monkey_campaign/agents/TIE2/brief.md
```

M-F04's footprint is EXACTLY `tools/monkey_campaign/agents/F04_contact/` (8 files:
brief.md, PREREGISTRATION.md, verify_contact.py, HANDOFFS.md, report.md, and
receipts/ x3). The one modified file (`U02_camera/receipts/latency_run.json`) and
the R4_intent_review / TIE2 paths belong to parallel sessions — untouched by
M-F04. No existing file was modified; no engine C++ edits; no GPU; no servers
launched; no writes outside the agent dir. Not committed (coordinator commits
agent files, per campaign pattern).

## Honest boundaries

- **L1 only.** Everything above verifies the DECLARED geometric model in Python.
  Not a single case ran inside the engine (see the L2 gap statement). The verdict
  "no unacceptable tunnelling/ghost support/interpenetration/disagreement" holds
  for the declared model and its frozen cases; in-vivo demonstration is G04/W10
  territory and is recorded as owed.
- **Friction untouched.** The suite is geometry-only; the 0.6 placeholder remains
  unevidenced with G04 named as the acquisition prerequisite.
- **The gap-law convention surprise** (miss 1) is the run's real discovery: the
  engine's rest configuration puts sole contact points r_sole BELOW the surface.
  Any future render-vs-physics comparison (W10) and any support-envelope math
  (G01) must use the law's convention deliberately.
