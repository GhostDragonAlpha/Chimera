# AMENDMENT A4 — MAT2-U07 (correction r1: the mechanical pixel-content
# gate; review-refuted render, frozen BEFORE the re-sealed run)

## What the independent review refuted

Review sgt-pr312-69772e91 (head `69772e9143d582cdd0d2d56c990c0a5b0e697509`,
PR #312): VERDICT CHANGES-REQUIRED on the pixel gate. Every STRUCTURE gate
passed (manifest fields complete, pinned validator `structurally_valid`,
byte-identical side-view repeats) while ALL 32 committed FFV1 frames were
blank — the clean view, the obstructed view, the close-target view and the
side view are each a single uniform background colour, and the declared
diagnostic layers exist only as manifest strings. Root cause: the
candidate's `camera_views.py` `U07_VIEWS` omitted the pinned renderer's
follow flag, so the camera stayed at the absolute spawn pose ~75 degrees
off-axis while the walked body was near x=8.4 m; every body triangle
projected outside the frustum.

## The view law is NOT changed (reviewer-confirmed reading)

The frozen preregistration ALREADY declares the follow semantics this
correction implements:

- the camera arms section names C-V1 "the declared follow view";
- the frozen probes/views section places the occluder "in the body-anchored
  camera frame" and declares the C-V1 look ray as EYE OFFSET
  `[1.2,1.6,3.2]` -> TARGET OFFSET `[0,0.5,0]`.

`camera_views.py` `U07_VIEWS` now carries `"follow": True` on all four
views (the pinned `MAT2-W10/visualization.py` `render_frame` view-spec
contract). No frozen number changed: the offsets, per-view FOVs and
near/far planes are the prereg's own values, byte-for-byte. The manifest
camera records additionally declare W10's `position_frame` law
("body-anchored offsets; the anchor per frame is recorded in the row's
anchor_ticks"), resolving the reviewer-noted self-contradiction between
offset records and the unfollowed render.

## A4-1: the mechanical pixel-content gate (the new acceptance machinery)

The capture stage now DECODES EVERY declared frame of the committed FFV1
video (per-frame decoded-sha equality against the piped bytes — the
3-probe law is upgraded to all frames) and a new task-owned module
`pixel_gate.py` asserts, per frame, against declared per-class law:

- (a) NON-UNIFORM content: at least two unique colours in every frame;
- (b) BODY PRESENCE: the pinned renderer's exact body palette (thorax
  `(120,80,60)`, left leg `(200,60,50)`, right leg `(60,90,200)`) present
  at declared per-class minimum pixel counts. Floors were declared from
  skeleton geometry, corrected ONCE from the r1 dev-run census (refusal D9
  in DEV_RUN_REFUSALS.md) and re-frozen BEFORE the evidence run: clean and
  diagnostic C_V1 frames 200 px (dev census 385-418 px), close-target 200
  px (census ~6300 px), side views 100 px (census 137-144 px). The
  obstructed view declares body_min_px 0 WITH REASON: the frozen occluder
  box provably stands between camera and body (the P9 numerics put the
  target inside the box's projected footprint) and the dev census shows it
  FULLY conceals the body (fill 17678 px, body 0 px) — requiring body
  pixels there would demand concealing the declared obstruction; the
  required content on obstructed frames is the occluder fill (floor 100
  px, census ~17.7k), with the body count recorded informationally;
- (c) DECLARED LAYERS WHERE DECLARED: on every diagnostic frame the overlay
  furniture (tick digits, stride bar region, corner chip), the
  camera-target/frustum marker and the body-associated label marker must be
  present at declared minimums; on the obstructed view the declared
  occluder fill must be present.

Gate verdict GREEN is REQUIRED for the run to pass; `make_report.py`
refuses to emit a report otherwise. PLANTED-DEFECT SELFTEST: a
deliberately blank frame FAILS the gate (uniformity + body-absence
refusals), the historical overlay-only defect (furniture but no body in a
clean frame) FAILS body presence, content-bearing frames of each declared
class PASS, and occluder absence FAILS the occluder law. The selftest runs
in the named-check suite AND at capture time; both records are receipted.

## A4-2: the declared diagnostic layers are DRAWN (task-owned, deterministic)

The profile declares diagnostic layers ["input/state/tick display",
"camera target and frustum diagnostics", "selected creature labels"]. The
pinned renderer draws only the tick/stride-bar/chip furniture, so this
card's own code now draws, on the RENDERER'S RETURNED BUFFER (pinned bytes
unmodified; records-only law P10 unaffected):

- the projected camera-target crosshair + four viewport frustum corner
  brackets (colour `(255,0,255)`) — the "camera target and frustum
  diagnostics" layer;
- the body-ASSOCIATED creature label: a crosshair marker at the projected
  com anchor (colour `(0,220,220)`) plus the creature digit "1" in the
  pinned chip colour (the glyph table is digits-only; the label now rides
  the body projection instead of a fixed corner chip);
- the declared occluder box, projected and hull-filled (colour
  `(60,60,70)`) on the obstructed view in BOTH modes — occlusion declared,
  never concealed.

All marker colours are distinct from every pinned palette entry. Drawing
is a pure function of the declared geometry and the returned camera, so
the side-view byte-identity pair law is preserved. Projected marker
positions are recorded per frame in `frames_meta.json`.

## A4-3: recorded observation (no frozen prose is edited)

The frozen prereg's P9 text says the profile carries 15
`camera_required_fields`; the registry's `controls` profile carries 16 and
the receipts assert the registry list (complete). The stale count stays in
the hash-pinned prose; this amendment records it. The sealed receipts now
embed `amendment_a4_sha256` beside the earlier amendment hashes and refuse
any mismatch.

## Unchanged

P1 (as amended by A1) through P12 stand; the measurement pipeline, arms,
pins and limits laws are untouched by this correction. The full battery is
RE-EXECUTED and re-sealed at package base `69772e9143d582cdd0d2d56c990c0a
5b0e697509`; measurement artifacts reproduce byte-identically (the prior
review's own fourth execution already demonstrated this determinism).
