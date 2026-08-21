# SESSION LOG 2026-08-21 — the sectioning method is declared and locked

## What happened, in order

1. Resumed mid-iteration on bear-34 region labels (post-compaction). Judged round-4
   shots; labels anatomically clean. Added eye regions from MEASURED dark-splat
   clusters (two clusters at y=0.109, symmetric about the measured head center
   x=-0.047) — not eyeballed.
2. `tools/label_regions.py` committed (e903f83): ellipsoid base spec, labels traced on
   the outer membrane, stable NAME-keyed colors (spec edits never reshuffle palette).
3. Operator rulings, in force:
   - Donor = pajama bear (CO3D 34) — YES. Torso genome will be printed flannel, head/
     paws/feet are fur; two material classes from one donor, technique must handle both.
   - Sectioning must be part of the CAD process — it is: labels live on splats
     (authoritative), both CAD membranes inherit by nearest splat.
   - *"Take the original object, not the circle-sphere object"* — the first chalk
     renderer drew circular dots (the "orbs" the operator correctly rejected); v2
     renders true projected-covariance ellipses.
   - The technique must run photogrammetry-style: circle each part from MANY angles,
     intersect the views; contamination that can't be circled twice dies (SfM logic).
   - Add the stick figure: a skeleton drawn INSIDE the bear, adjusted per view the
     same way as the chalk — recursive co-improvement; the marks files accumulate as
     the training record for a future auto-marker.
4. Format dispute settled BY MEASUREMENT: co3d_34.splat = 84,589 splats x 32 bytes,
   decodes to 14 floats (pos3 rgb3 alpha1 scale3 quat4), anisotropy median 6.9 /
   p90 28.8, quats non-identity (|w| median 0.519). NOT 7-variable. The real loss vs
   the training PLY is dropped spherical harmonics (flat RGB) — noted, not blocking.
5. Built `tools/lasso_label.py` (the tailor's chalk): subcommands render/sheet/skel/
   apply. Ops: set / replace (redraw releases old members, refill nearest) / sub;
   surface_only front-layer picking per pixel; multi-view INTERSECTION; --denoise
   off-membrane drop; hierarchy recorded in the labels JSON.
6. Whole-body chalk pass (`tools/specs/bear34_chalk2.json`): 16 regions incl. paw_L,
   foot_L, foot_R. First intersections caught two of my own aiming errors (ear_L
   front∧left = empty; paw_L = 20 splats) — the method rejecting bad second views,
   working as designed. Fixed to single-view slabs for those; final counts sane
   (snout 1657 > nose 342; eyes 151/191; feet ~1800 each; torso 12,113).
7. Skeleton (`tools/specs/bear34_skeleton.json`): 16 joints, pixel-marked across
   front/right/left, least-squares triangulated. First-pass reprojection RMS
   1.5–20 px; all joints measured inside the body (0–28 mm from core surface).
   Overlay verified on all six sheet tiles — the figure sits inside the bear.
8. Committed b8f04b7. Presented chalk + skeleton + labeled result on one page.
   **Operator: "Yes that's more like it. We now have our methodology locked in
   place."** — documented in `docs/THE_SECTIONING_METHOD.md`; pointer added to
   THE_AUTHORED_PIPELINE.md (Trainable COAT extracts PER REGION, post-sectioning).

## State

- Donor: `models/co3d/co3d_34.splat` + `bear34_shells.npz` + `bear34_labels.json`
  (16 regions, hierarchy, splat/membrane/core labels) + `bear34_skeleton_solved.json`.
- Restart incident mid-session: no work lost (all committed); viewer server + browser
  tasks were relaunched.

## Next

- Per-label margin genome extraction (patches relative to the inner core).
- Spray: rebuild bear 34 from its own genomes onto its own core (reconstruction
  test — must pass before any novel body).
