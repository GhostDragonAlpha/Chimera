# PREREGISTRATION AMENDMENT 3 — the render's pixel classes measured and re-derived (banked BEFORE the re-capture)

The FIRST capture ran and is on disk (renders/*.png, render_record.json); its outcome stands
in the record: F10 fired on four clauses. MEASURED CAUSES, each with its derived repair; no
capture is retouched, no capture is deleted.

1. P-R1 MASK (fired: coverage 0.9965/0.9953 >> 0.40 class top). The banked mask
   ("pixels differing from the corner-sampled background") is refuted by the measured frame:
   the engine scene paints a sky gradient AND a studio floor/grid over ~96% of the frame, so
   nearly every pixel differs from the black corner. MEASURED FRAME CLASSES (both stills):
   sky (R < 40) ~20-21%; neutral floor/grid (|R-B| < 20, R < 110) ~75-77% at mean RGB
   (54.9, 54.0, 48.5) — R-B ~ +6; bone-tint pixels (R-B >= 25, R >= 45): corpse 1.86%,
   standing 3.30%, mean RGB (139-179, 126-161, 100-125). THE DERIVED MASK: object pixel :=
   (R - B >= 25) AND (R >= 45) — the compose's own bone tint (0.82, 0.75, 0.60) under shading,
   separated from both measured neutral classes with margins (floor R-B ~ 6 vs bone >= 25;
   sky R ~ 2 vs bone R >= 45). Coverage classes unchanged: [1%, 40%] of frame.
2. CAMERA (not a falsifier; a framing defect against the rule's own intent "the operator
   sees the skeleton"). The proven rule fits the bbox HEIGHT; the standing body is long and
   low (pads' plane level), so the skull filled the frame. DERIVED REPAIR: radius = 1.35 *
   (max(bbox_height, bbox_x_extent, bbox_z_extent) / 2) / tan(fov_y/2) — the SAME rule for
   both stills (the corpse still keeps its frame: its height dominates).
3. P-R4 (fired: implementation error, variance compared against spread). The battery's own
   verified per-pad signed distances (battery.json pad_plane.signed_dist_mm) are the record;
   the render's scene spread (max-min along the placed plane normal) is compared against
   (max-min of the battery's signed distances) * scale_scene_per_mm / 1000.0, tolerance
   1e-6 m, unchanged.
4. SETTLE HARDENING (P-R3 corpse revisit failed once): the first upload of a fresh engine
   needs a deeper quiesce (the visual lane's own measured GPU-sort settle behavior). The
   capture now requires THREE consecutive byte-equal fresh captures; the revisit check is a
   further capture after that.

Everything else stands verbatim (path, registration, placement derivation, P-R2 >= 1000 px,
coverage class band, falsifier F10). Banked before the re-capture.

Trailer: Agent: GLM 5.3
