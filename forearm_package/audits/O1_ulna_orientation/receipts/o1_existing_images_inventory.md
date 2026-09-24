# O1 — EXISTING-IMAGE INVENTORY (brief method (c), second lane) — NEGATIVE RESULT, preserved

Question: does an EXISTING image of the target body settle the forearm's volar/dorsal?
Admissibility rule (brief, verbatim): an image counts only if the forearm's volar/dorsal is
VISUALLY DECIDABLE and the VIEW ORIENTATION is knowable.

Inventory (read directly; no new renders were needed or made for this lane):

| image | what it shows | view orientation knowable? | volar/dorsal decidable? | counts? |
|---|---|---|---|---|
| `baseline_snapshot/runs/figure_actual_fit.png` | matplotlib projections (front x-y, side z-y) of the target mesh point cloud + joints | YES (labeled panels; side panel shows muzzle at +z, tail at -z) | NO — forearms are thin silhouettes behind the legs; no surface shading | no (but USED as facing corroboration: anterior = +z) |
| `baseline_snapshot/runs/figure_forearm_candidates.png` | b/c scatter of fitted sites in fit-frame coordinates | axes are fit-frame, anatomically unlabeled | NO (this IS the unlabeled-roll problem) | no |
| `baseline_snapshot/runs/figure_transverse_candidate.png` | same family | same | NO | no |
| `Saved/dyad/jnt2_elbow_flex.png` | engine render, whole monkey, small | YES (posterior view: no face visible, tail visible) | NO — forearm ~40 px wide, edge-on | no |
| `Saved/dyad/2026-09-03_loaded_review/viewport_loaded.png`, `orbit_00..05.png` | engine renders, lower body/hands | partially | NO — elbows cropped/too small | no |
| `Saved/dyad/2026-09-03_loaded_review/glass_after_fix*.png` | viewport/glass UI debugging | n/a | NO | no |

Verdict: **no existing image settles the forearm volar/dorsal** under the brief's own
admissibility rule. The olecranon geometric measurement
(`receipts/o1_target_sections_directed.json`) is therefore the deciding target evidence,
with `figure_actual_fit.png`'s side panel retained as independent corroboration of the
FACING fact (anterior = +z) that the olecranon test's sector definition rests on.
Note: using already-existing images is gaming-safe; no new GPU render was queued or made.
