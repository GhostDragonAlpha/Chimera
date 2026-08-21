# THE SECTIONING METHOD — the tailor step: chalk, intersection, stick figure

> Declared by the operator and approved on screen, 2026-08-21: *"Yes this is the
> correct technique. It has to be applied the same way photogrammetry is applied."*
> This file owns HOW a real object gets divided into named, hierarchical, jointed
> sections. It is the manual method under [`THE_METHOD.md`](THE_METHOD.md); the
> sections it produces feed the genome extraction in
> [`THE_AUTHORED_PIPELINE.md`](THE_AUTHORED_PIPELINE.md) (Trainable COAT).
> The donor is a REAL multi-view 3DGS scan (CO3D bear 34 — 202 real photos,
> measured cameras, 14-float anisotropic splats, verified by measurement:
> anisotropy median 6.9, quats non-identity). Not AI-generated. Ever.

## The principle

Sectioning is done **by eye, with chalk, from many angles** — the way photogrammetry
works, applied to labeling instead of capture. No auto-segmentation algorithm decides
where an ear ends. The labeler (the AI, acting as the tailor) looks at renders of the
real object and draws polygons on what it sees. Only the projection is computed.

Two instruments, drawn on the same views, improving together on every pass:

1. **CHALK (regions).** A polygon in pixel coordinates on a view. Every splat
   projecting inside takes the label. The same part circled from several views is
   **intersected** — the view cylinders carve the 3D region, and contamination
   (static clouds, floaters) dies because it cannot be circled from a second angle.
   This is SfM's triangulation-consistency test, used as a sectioning tool.
2. **THE STICK FIGURE (skeleton).** Joints marked as single pixels in 2+ views are
   **triangulated** (least-squares ray intersection) into 3D joint positions; bones
   connect parent→child. The figure must sit INSIDE the body — verified numerically
   (distance to the core/membrane shells) and by overlay on every view. Placement
   error is a number (reprojection RMS in px), so each pass measurably improves.

**Hierarchy is recorded as both levels are drawn**: head contains
eyes/ears/nose/snout; torso carries the limbs; arm contains paw; leg contains foot.
The region tree and the joint tree are two views of the same anatomy — the CAD body's
standardized shape hangs from this tree.

## The loop (recursive by design)

1. `sheet` — render the donor as true anisotropic ellipse splats into one contact
   sheet (front/right/back/left/top/bottom). Never chalk on placeholder renders.
2. The labeler LOOKS and writes polygons/joint marks (JSON, pixel coords per tile).
3. `sheet --ops/--skel` — overlay the chalk and the skeleton BEFORE applying.
   Chalk before ink: bad lines are caught here, by looking.
4. `apply` — intersect multi-view ops, denoise off-membrane splats, splats become
   authoritative, both CAD membranes (inner core + outer membrane, from
   `tools/shell_fit.py`) inherit labels by nearest splat.
5. `skel` — triangulate joints, report reprojection RMS + containment.
6. Present the sheet to the human. Fix what they mark wrong. Repeat.

Every pass re-aligns regions AND skeleton. The marks files
(`tools/specs/*_chalk*.json`, `*_skeleton.json`) are append-only training records —
when enough passes exist, an algorithm can learn the marking itself. Until then the
labeler marks manually, per the declaration.

## Rules learned on bear 34 (measured, not lore)

- **Two+ views per region where the feature is visible in two+ views.** Head, ears,
  arms, feet: intersected. Deeply 3D-ambiguous placements (the flopped left ear's
  side profile) may run single-view with `surface_only` + a `thick` slab — an empty
  intersection is the signal your second view was aimed at the wrong feature.
- **`replace` ops redraw a region** (old members outside the new chalk are released
  and refill from nearest labeled neighbors). Ellipsoid base labels
  (`tools/label_regions.py`, spec `tools/specs/bear34_regions.json`) seed the body;
  chalk ops refine it.
- **Denoise before labeling**: bear 34 carried 17,850 splats >4cm off the membrane
  (static contamination from capture) — dropped, never labeled.
- **First-pass triangulation RMS was 1.5–20 px** across 16 joints; the high-error
  joints are exactly where marks disagree across views — the loop's fix list.
- Stable NAME-keyed colors; spec edits must never reshuffle the palette.

## Tools

`tools/lasso_label.py` — subcommands `render` (single views), `sheet` (contact sheet,
chalk + skeleton overlay), `skel` (triangulate + containment report), `apply`
(ops → labels JSON + viz splats). Specs live in `tools/specs/`. Inspection renders go
through `tools/http_shots.js` (the real viewer) for final judging; the tool's own
renderer exists so chalk pixels and projection math share one camera.

## Gate

The human sees the chalk sheet, the skeleton overlay, and the labeled result. Their
authorization opens genome extraction. First authorized state (bear 34): 16 regions,
16 joints, all six views clean.
