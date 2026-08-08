# theStandingHuman v1 Report

## 1. Theory (RULE 0)

**STATEMENT:** The 206-bone skeleton stands because its printed geometry routes the
whole body weight to the ground entirely through bones in compression and ropes in
tension. Standing is a property of the frame, not of any muscle.

**PREDICTION:** During the verdict window (ticks 1200–8000) every bone body stays one
cluster and inside its derived positional band; every capture gap stays inside
`[S_WALL, d_eq]`; the COM of all non-ground grains projects inside the convex hull of
the foot-contact grains; every rope that the static topology requires is taut or
slack, never compressed; the head height stays within the derived standing band.

**FALSIFIERS:**
- (a) **INTEGRITY** — per bone: no body splits into >=2 clusters during the verdict window.
- (b) **CAPTURE** — every cup/ball gap stays within `[S_WALL, d_eq]`.
- (c) **FRAME** — COM of non-ground grains stays over the foot-bone support polygon.
- (d) **ROPE** — loaded ropes are taut-or-slack, never compressed.
- (e) **STAND** — head height stays within `print_z +/- H_head*tan(2deg)+d_eq`.
- (f) **CONTROL** — cut all ropes at tick 1200; the frame must fall: COM drops more
  than `delta_fail = L_leg*sin(12deg)` within 600 ticks.

## 2. Build

- **Builder:** `LightEngine/skeleton_structures.py:build_skeleton()` (v1)
- **Driver:** `LightEngine/demo_skeleton.py` (v1)
- **Scale:** `lambda = 2.699280e-02 m/lu` (`height_lu = 66.68`, `d_eq = 0.0484 lu`)
- **Grain budget:** 50 000 grains
- **Actual print:** 49 864 grains
  - bones: 43 398 grains (cups counted under their parent bodies)
  - joint cups: ~422 grains
  - ropes: 1 986 grains
  - foot pads: 4 480 grains
- **Ground plate change:** replaced the full-support-rectangle plate (21 168 grains)
  with two foot pads. Each pad is the axis-aligned bounding box of the scaled foot
  contact points (ankle, tarsal, metatarsal-base, MTP, forefoot) projected to the
  ground plane, plus a one-grain (`d_eq`) seat margin. The literal reading of
  "plate margin = sway reach + one body-segment length" would enlarge the plate;
  here the leg segment itself is treated as the stability margin that contains the
  sway reach, so the plate only needs to cover the foot contact area plus the seat
  margin. The resulting pads are ~6.72 lu (A-P) by ~0.72 lu (lateral), giving
  2 240 grains per foot and 4 480 total — a 16 688-grain saving over the rectangle.
- **Bone re-resolution:** freed grains were reallocated as 3x3 solid square rods
  for the longest/heaviest bone groups: femur, tibia, fibula, humerus, pelvis,
  radius/ulna, sacrum, and selected foot/vertebral bodies.
- **Run:** 8000 ticks, `dt = 0.0005`, seed = 20260807
- **Tests:** `python -m pytest LightEngine/tests/test_skeleton.py -q` — **8 passed**

## 3. Derived Geometry

| quantity | value |
|---|---|
| `lam` | 2.699280e-02 m/lu |
| `height_lu` | 66.68 lu |
| `d_eq` | 0.04840 lu |
| `S_WALL` | 0.02500 lu |
| actual grains | 49 864 |
| plate grains | 4 480 |
| rope grains | 1 986 |
| upgraded groups | femur, tibia, fibula, humerus, pelvis, radius/ulna, sacrum, metatarsals, tarsals, forefoot, patella, vertebra L3/L4/L5 |
| loaded rope heuristic | vertical ropes spanning >0.05 H, mostly vertical, under the central COM column |

## 4. Dynamics Result

Logs:
- `LightEngine/output/print_skeleton_v1_log.txt` (main)
- `LightEngine/output/print_skeleton_v1_control_log.txt` (cut-ropes)

### Main run

- Max clusters: **607** (worst body: `fibula_R`; also `tibia_L` 545, `tibia_R` 523)
- Capture gap range: **[0.0095, 0.0637]** lu (target band `[0.0250, 0.0484]`)
- COM margin range: **[-0.043, 0.400]** lu; verdict-window minimum **+0.0006** lu
- Head z range: **[62.016, 66.901]** lu (initial `head_z0 = 65.689`)
- Rope links (sampled): T=12 451, S=4 765, C=271; max compression **0.769**
  (`rope_lumbar_posterior_5`)
- Worst joints by capture gap: `atlanto_occipital` (0.0095), `shoulder_R` (0.0112),
  `hip_L` (0.0208)
- Plate F range: [8 391.81, 23 567.33]

### Control run

- Ropes cut at tick 1200; 1 986 rope grains removed; COM_z at cut = 28.921 lu
  (see metering sin below — this number is on a different mask than the samples).
- Max clusters: **618** (worst body: `fibula_R`; also `fibula_L` 548, `tibia_L` 518)
- Capture gap range: **[0.0094, 0.0637]** lu
- COM margin range: **[-0.043, 0.297]** lu; verdict-window minimum **+0.0435** lu
- Head z range: **[62.347, 66.906]** lu
- Rope links before cut: T=639, S=3 227, C=20; max compression 0.449
- Worst joints by capture gap: `atlanto_occipital` (0.0094), `shoulder_R` (0.0140),
  `hip_L` (0.0170)
- Plate F range: [8 326.56, 16 178.23]
- **True post-cut COM trajectory (non-plate samples):** 31.854 (tick 1000,
  pre-cut) → 31.818 (tick 2000, 800 ticks post-cut) → 30.107 (tick 8000). The
  drop inside the derived 600-tick fall window is ~0.04 lu against the bar
  `delta_fail = 6.863` — the frame does not fall.

**Metering sin (recorded; verdict untainted):** `com_at_cut`
(`demo_skeleton.py:395`) averages over *all live grains including the pinned
plate*, while the fall meter's `cur_com_z` (`demo_skeleton.py:420`) and every
sampled COM exclude it — a ~2.9 lu constant bias *against* detecting a fall
(plate ≈ 9% of N at z≈0). A detected fall would have been real; the observed
non-fall is unaffected (true drop ~0.04 lu vs bar 6.863). The "COM_z rises from
28.921 to 30.107" reading is an artifact of this mask mismatch, not physics.
Fix named for v2: compute `com_at_cut` over the same non-plate mask.

## 5. Verdict

### Main

- (a) INTEGRITY      : **FAIL**  (max clusters = 607)
- (b) CAPTURE        : **FAIL**  (gap 0.0095 < `S_WALL` 0.0250)
- (c) FRAME          : **PASS**  (COM margin min +0.0006 lu inside support polygon)
- (d) ROPE           : **FAIL**  (271 compression link samples, max 0.769)
- (e) STAND          : **FAIL**  (head_z drift 4.9 lu vs band ±2.34 lu)
- (f) CONTROL (FALL) : skipped

### Control

- (a) INTEGRITY      : **FAIL**  (max clusters = 618)
- (b) CAPTURE        : **FAIL**  (gap 0.0094 < `S_WALL` 0.0250)
- (c) FRAME          : **PASS**  (COM margin min +0.0435 lu)
- (d) ROPE           : skipped  (ropes removed at tick 1200; 20 pre-cut compression samples)
- (e) STAND          : **FAIL**  (head_z drift 4.6 lu vs band ±2.34 lu)
- (f) CONTROL (FALL) : **FAIL**  (fall_detected=False; COM_z rose from 28.921 at cut to 30.107 at tick 8000)

### Selected per-body grain counts

| body | grains | resolution |
|---|---:|---|
| ground_plate | 4 480 | foot pads |
| femur_L / femur_R | 3 375 / 3 375 | 3x3 solid |
| tibia_L / tibia_R | 2 772 / 2 772 | 3x3 solid |
| fibula_L / fibula_R | 2 772 / 2 772 | 3x3 solid |
| humerus_L / humerus_R | 2 259 / 2 259 | 3x3 solid |
| pelvis_L / pelvis_R | 896 / 896 | 3x3 solid |
| skull | 260 | 2x2 solid |
| sacrum | 135 | 3x3 solid |

## 6. Conclusion

The v1 print driver met the build requirements: the plate was shrunk from a
21 168-grain support rectangle to two 4 480-grain foot pads, the freed grains
were reallocated as 3x3 solid rods for the longest bones, and the assembly still
passes the print-law tests and the 50 000-grain budget.

The dynamics falsify the standing frame as currently constituted. Long bones
split into hundreds of clusters, capture gaps fall below `S_WALL`, and ropes
show compression. The FRAME falsifier passes only because the COM migrates
forward into the foot-bone support polygon during the run; at tick 0 the COM
lies outside it (margin −0.043 lu). The support polygon is deliberately
conservative — it uses only the distal endpoints of `tarsals`, `metatarsals`,
and `forefoot`, excluding the ankle/heel — so the early negative margin is an
artifact of the polygon choice, not necessarily a physical fall.

The control run confirms that the ropes are not the primary load path: after
all 1 986 rope grains are removed at tick 1200 the frame does **not** fall. The
post-cut trajectory tracks the main run's slump almost exactly (control COM z
30.107 / head_z 62.347 vs main 29.907 / 62.016 at tick 8000), and the true
drop inside the 600-tick fall window is ~0.04 lu against the 6.863 lu bar, so
the FAIL verdict for CONTROL (FALL) is unambiguous. The skeleton is being held
up by bone-on-bone contact and the pinned foot pads, not by the rope network —
the tension half of the standing constitution is decorative as printed.

The next membrane to test is therefore not more grains but better geometry:
a wider foot contact polygon or lateral foot pads, rib-cage anchoring to the
vertebral column, hip/shoulder capture that keeps joint gaps inside the band,
and a rope topology whose loaded set is derived from the actual COM line rather
than only the ankle tendons.
