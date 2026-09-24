# O2 receipts — exact commands and key outputs

Environment: Windows / Git Bash; every python run used `PYTHONDONTWRITEBYTECODE=1`;
every figure from `import matplotlib; matplotlib.use("Agg")` BEFORE pyplot import
(CPU-only software renderer; NO GPU/OpenGL/Vulkan/WebGL contexts of any kind —
the gaming-safety rule was met without needing the GPU broker and without new renders
of the mesh; the only images read are pre-existing repo files).

## 0. Resumption hygiene (the transient-failure leftovers)

```
$ diff forearm_package/baseline_snapshot/code/mesh_target.py \
       forearm_package/audits/O2_hand_orientation/work/mesh_target_o2.py && echo IDENTICAL
IDENTICAL
$ sha256sum work/mesh_target_o2.py baseline_snapshot/code/mesh_target.py
268f139a9e90e561f4a5f8ab02553f0d87f51633f635139e6cec6f5c9cfa19a0  (both files)
```
The dead attempt's `brief.md` was read and found to BE the frozen preregistration
(verbatim, thresholds and stop rule intact) — followed as-is, no edits.
`work/mesh_target_o2.py` was byte-consistent with the baseline module and was REUSED.

## 1. Source sign (method a)

```
$ cd audits/O2_hand_orientation && PYTHONDONTWRITEBYTECODE=1 python scripts/o2_source_sign.py
wrote receipts/o2_source_sign.json
--- hand_right ---
  27-geom plane normal n (undirected): [-0.132643, -0.111185, -0.984908]
  plane centroid (local m): [0.004962, -0.067505, 0.001351]
  geom residual rms/max: 10.66 / 28.61 mm
    ECRL-P4   -12.33   [z -6.71 | tilt -5.62]   palm13 -7.39   raw z +8.16
    ECRB-P4   -14.43   [z -9.33 | tilt -5.10]   palm13 -11.23  raw z +10.82
    ECU-P6     -0.86   [z +0.30 | tilt -1.16]   palm13 +0.02   raw z +1.05
    FCR-P3     -1.99   [z +3.15 | tilt -5.14]   palm13 +2.22   raw z -1.85
    FCU-P4     +5.40   [z +6.44 | tilt -1.04]   palm13 +6.71   raw z -5.19
  FROZEN clean-split criterion: False
    violations if palm := +n side: {flexor:FCR-P3: -1.99, extensor:ECRB-P4: -14.43,
                                    extensor:ECRL-P4: -12.33, extensor:ECU-P6: -0.86}
    violations if palm := -n side: {flexor:FCU-P4: 5.4}
  jackknife: 1/27 refits clean
    ECRL-P4 [-13.20, +12.14]  ECRB-P4 [-14.95, +14.28]  ECU-P6 [-5.29, +1.07]
    FCR-P3 [-2.63, +1.82]     FCU-P4 [-6.43, +7.14]   (mm, leave-one-geom-out ranges)
--- hand_left ---  (offsets bit-identical, raw local z exactly negated; same verdict)
origin crosscheck hand_r: [-0.0731, 0.532647, 0.202699]   (== C3 receipt / A4)
```

C3-construction reproduction check (`receipts/c3_crosscheck.log`):

```
C3  per-site offsets (m): [-0.012326947, -0.014432797, -0.000862169, -0.001989213, 0.005403188]
O2  per-site offsets (m): [-0.012326947, -0.014432797, -0.000862169, -0.001989213, 0.005403188]
max |O2 - C3| = 0.000e+00 ; |cos(n27_O2, n27_C3)| = 1.000000000000
ASSERTIONS PASSED: O2 source plane == C3 frozen construct
```

## 2. Target sign (method b)

```
$ PYTHONDONTWRITEBYTECODE=1 python scripts/o2_target_curvature.py
input hashes match MANIFEST (birth 550a5b3e..., pack 74b3ab04...)
--- side R ---
  +T basis e1 = [0.8901, -0.4558, 0.001]  (fixed rule: rejection of +x on the plane orthogonal to a)
  paddle PCA vs a: 6.4 deg (776 verts)
  frozen window 55.6..111.3 mm, 72 stations
  midline_sagitta    sag  -3.392 mm @t= 83.0 (quadfit  -3.288 mm)
  faceplus_sagitta   sag  +2.117 mm @t= 106.0 (quadfit  -0.950 mm)
  faceminus_sagitta  sag  -5.109 mm @t= 94.0 (quadfit  -4.512 mm)
  D1 (frozen sagitta difference) = +7.226 mm (quadfit +3.561 mm)  threshold |D1| > 1.0 mm
  D2 (mid-line signed sagitta)   = -3.392 mm (quadfit -3.288 mm)
  trimmed-window diagnostic: D1 = -0.31 mm          (window [55.65, 103.3], rim excluded)
--- side L --- (exact ANTI-mirror: +T_L = (0.8901, +0.4558, -0.001); mid +3.392;
  face +5.109@94 / -2.117@106; D1 +7.226; trimmed -0.31 — measurement-validity check)
```

Key profile facts (receipt `o2_target_curvature.json`): thickness 17.5 mm @40-52 mm,
16.46 @56 (window start), ~13.1 @76-84, 10.56 @104, then rim collapse to 2.92 @111;
mid-window thickness exceeds its endpoint chord by ~3.4 mm (12.94 actual vs 9.57 chord
@84) — a thickness LENS, not a uniform bend. Uniform-bend arithmetic at the measured
mid-line bow (3.3 mm over a ~28 mm half-window) predicts a face-sagitta difference of
only ~0.33 mm; measured 3.56 (quadfit) to 7.23 (max-dev) — 10-20x, i.e. thickness
redistribution + rim, not resting-flexion bending.

## 3. Existing-image inventory (secondary lane)

Read-only reads + matplotlib-Agg crop figures (`work/zoom_hands.py`, `work/zoom_hands2.py`):

```
$ md5sum Saved/vision_trial/{A_front_rest,B_leftside_rest,C_threeq_rest,D_front_elbowL50}.png
bff97689...  d8272e80...  289f3e0c...  5f499eb2...   (four DISTINCT renders, 2560x1440)
```
Subjects confirmed: Saved/mesh_view + docs/evidence shape_dyad = TEDDY renders (judgments.jsonl);
Saved/vision_trial = the MONKEY (the target character). Crop figures written to
figures/inventory_zoom_*.png. Verdict: INSUFFICIENT (report §4.3).

## 4. External compartment citations (class=EXTERNAL; fetched live 2026-09-24)

- FCR  — en.wikipedia.org/wiki/Flexor_carpi_radialis_muscle : "superficial layer of the
  anterior compartment"; inserts "on the anterior aspect of the base of the metacarpal
  of the index finger" (+ slip to 3rd MC, trapezium).
- FCU  — en.wikipedia.org/wiki/Flexor_carpi_ulnaris_muscle : anterior compartment,
  superficial group; "inserts onto the pisiform, hook of the hamate (via the pisohamate
  ligament) and the anterior surface of the base of the fifth metacarpal".
- ECRL — en.wikipedia.org/wiki/Extensor_carpi_radialis_longus_muscle : posterior
  compartment "mobile wad"; "inserted into the dorsal surface of the base of the
  metacarpal of the index finger (second metacarpal)".
- ECRB — en.wikipedia.org/wiki/Extensor_carpi_radialis_brevis_muscle : posterior
  compartment; "inserts into the dorsal/posterior surface of the base of the metacarpal
  of the long finger (third metacarpal)".
- ECU  — en.wikipedia.org/wiki/Extensor_carpi_ulnaris_muscle : "Being an extensor muscle,
  extensor carpi ulnaris is located on the posterior side of the forearm"; "insert at the
  base of the 5th metacarpal" (ulnar side).

## 5. Figures (all Agg; view directions stated in each title)

- figures/o2_source_plane_views.png — (A) view along +n27, (B) view along -n27,
  (C) signed offsets vs the fitted plane (FROZEN result banner), (D) raw local z
  diagnostic (clean 3/2). Compartments colored (flexors red triangles, extensors blue circles).
- figures/o2_target_paddle_profiles.png — R/L face + mid-line profiles with chords,
  frozen window shaded; thickness profiles showing the lens + rim.
- figures/inventory_zoom_*.png — hand crops of the four existing renders.

## 6. Integrity

```
$ git status --porcelain -- forearm_package/baseline_snapshot      -> (empty, 0 lines)
$ git rev-parse --short HEAD                                        -> 5db981cb
input sha256: birth 550a5b3ec927ea13... (661,076 B)  pack 74b3ab044b7adaed... (296,589 B)  == MANIFEST
no __pycache__/ .pyc under audits/O2_hand_orientation/ (PYTHONDONTWRITEBYTECODE=1)
all writes confined to audits/O2_hand_orientation/{brief.md(existed), report.md, scripts/, receipts/, work/, figures/}
no git writes; no writes into baseline_snapshot/; no scale, assembly-correspondence, or
production-mapping quantity computed anywhere.
```
