# PREREG AMENDMENT 1 — HAND_TARGET_VIEWS — dated 2026-09-24, BEFORE the official renders

Amendments to `PREREG.md`, motivated ONLY by (i) a code bug found on the debug run and
(ii) render-free arithmetic on the pinned mesh (`scripts/geometry_probe.py`; receipt
`receipts/geometry_probe.txt` / `.json`). No image had been inspected for palm/dorsum
content when this amendment was frozen; F-R1a (which forbids re-framing a camera after a
FAILED HUMAN IDENTIFICATION) is untouched — no identification has been attempted.

## A1. What the probe measured (render-free, pinned mesh only)

Per-station exact sections of the distal band (triangle-plane intersections, O2's
construction), right hand, stations 60–110 mm:

| t [mm] | extent along T_R [mm] | extent along n_t [mm] | PCA major [mm] | PCA minor [mm] | major dir · n_t |
|---:|---:|---:|---:|---:|---:|
| 60 | 15.70 | 49.95 | 49.91 | 15.55 | +0.9990 |
| 70 | 13.92 | 48.08 | 48.07 | 13.87 | +0.9985 |
| 80 | 13.10 | 47.23 | 47.24 | 12.69 | +0.9980 |
| 90 | 12.64 | 46.79 | 46.82 | 11.82 | +0.9980 |
| 100 | 11.60 | 46.11 | 46.14 | 10.70 | −0.9989 |
| 110 | 5.68 | 23.05 | 23.06 | 4.97 | −0.9992 |

Far-end (80–111.4 mm, r<42 mm) PCA: **b1 = 47.1 mm** (matches B1's recorded 47.1) with
**b1 direction · n_t = −0.9989** — the 47.1 mm major extent lies ALONG n_t (≈ world z).

**Consequence (measured):** each band section is a lens ~46–50 mm wide along n_t and
~6–16 mm thick along T_R. The two BROAD faces (the ±T faces O2's curvature test measured)
are normal to **T_R**, not to n_t. The R1.4 default camera (±n_t, n_t labelled "broad-face
normal candidate") therefore views the lens nearly EDGE-ON: the whole band's projected
screen-right span under that camera is 22.15 mm = **567.0 px < the R1.5-3 visibility bar
(600 px on the 47.1 mm broad face)** — the 47.1 mm face is spread along the frozen view
DIRECTION, where it cannot span the frame. This is arithmetic on recorded receipts
(B1 extents + O2 vectors), not a re-interpretation of any failed proxy.

## A2. Amendment 1 — camera deliverables (deviation declared per R1.4's own clause:
"any deviation is acceptable if fully declared in the sidecar")

1. **PRIMARY pair (letters A/B, the human question):** cameras opposed along the MEASURED
   broad-face normal ±T̂_R (T_R unchanged: the fixed +x-rejection rule, asserted to O2's
   recorded value). View 1: `eye = look_at + 0.30·T̂_R`, view direction −T̂_R, face A toward
   camera (the +T_R-side face). View 2: `eye = look_at − 0.30·T̂_R`, view direction +T̂_R,
   face B toward camera (the −T_R-side face). `up = a`, ortho half-width 0.040 m,
   2048×2048 — all other §2/§3/§4/§5 constants unchanged. This photographs each broad face
   FACE-ON, which is §R1.3-A's stated design intent ("both broad faces are photographed").
2. **RECORD pair (no question letters):** the literal R1.4 ±n_t cameras, rendered and kept
   byte-reproducibly as the frozen-prereg execution record, titled "literal R1.4 camera
   (record only)". Its band span (567.0 px) is recorded against the bar and FAILS it —
   recorded, not tuned away.
3. **Visibility assertion (falsifier-adjacent, executed):** for the PRIMARY pair, the
   far-end (80–111.4 mm) projected span must be ≥ 600 px (expected ≈ 47.1 mm × 25.6 px/mm
   ≈ 1206 px). For the RECORD pair the number is recorded only.
4. **Crop-check bug fix:** the debug run's band-v assertion used (p−wrist)·y_cam, omitting
   the eye offset −0.083 (that fired a false F-R1b). Fixed to project about the eye. Not a
   camera change.
5. **Left-hand mirror check:** same construction on the left hand (a_L, T_L by the same
   fixed rule, n_tL asserted). The fixed +x-rejection rule is NOT mirror-equivariant
   (+T_L = −M·T_R, O2's recorded anti-mirror), so check-figure letters are assigned by the
   MIRROR RELATION and declared: A_L := the face mirroring R's face A (outward normal
   M·T_R = −T_L, i.e. the −T_L-side view), B_L := the +T_L-side face. If the reader names
   the same letter on both sides, mirror consistency holds. Mesh x-mirror exactness was
   measured (90.87 % of verts / 88.11 % of triangles exactly mirrored) — the check is
   VISUAL, not exact; a rendered-pixel mirror difference is recorded as an informational
   receipt.
6. **Visibility-metric refinement:** the ≥600 px bar is evaluated on the far-end face
   population (80–111.4 mm, r<42 mm — the population on which B1 recorded 47.1 mm), not on
   the whole band, because the 55–80 mm population includes the ownership-anomaly skin
   flare (tail_base/spine_lower, B1 receipt) that reaches 39.9 mm from the axis under the
   face-on camera. Whole-band spans are recorded alongside.

## A2.7 (debug-render finding, frozen before the official renders) — BAND DEPTH SLAB

The face-on debug render showed the +T_R view occluded by NEAR BODY GEOMETRY: the eye
position for view 1 (+T_R side) lies toward the monkey's torso/leg, and in-column skin at
depths far in front of the band enters the frame. Measured depth of in-column vertices
(|u|,|v| ≤ 45 mm) along the view direction, per view (pinned mesh, CPU):

| view | in-column verts | depth percentiles 0/5/25/50/75/100 % [mm] | band verts' depth [mm] |
|---|---:|---|---|
| +T_R (v1) | 1625 | −25.2 / −7.3 / 73.8 / 300.0 / 306.5 / 320.2 | [296.7, 318.9] |
| −T_R (v2) | 1625 | 279.8 / 284.4 / 293.5 / 300.0 / 526.2* / 625.2 | [281.1, 303.3] |
| +n_t (record v1) | 1027 | 239.9 / 244.7 / 284.9 / 303.2 / 320.1 / 332.6 | [260.1, 332.6] |

*far-side body. **Frozen rule:** the render is of the BAND REGION (task brief: "rasterize
the band's silhouette + shading by the declared camera"): geometry whose depth along f
lies outside **[0.24, 0.36] m** from the eye is excluded (declared depth crop; contains
the band with ≥7 mm margin in every view, excludes the body cluster ≤ ~150 mm and the
far-side body ≥ ~520 mm). The projection remains orthographic; extrinsics unchanged;
the slab is recorded in every sidecar.

Everything else in PREREG.md stands: identity pins, ortho 0.040 m / 2048², SS 2, light,
annotations, sidecar fields, reproducibility protocol, falsifiers (a)/(b)/(c) + F-R1a/b/c,
stop rule.
