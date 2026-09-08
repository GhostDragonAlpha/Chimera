# GLM-DYAD-01 — the dyad's membrane window review (2026-09-08)

Executed per `docs/THE_DYAD_PROTOCOL.md` and `ChimeraEngine/senses.py`:
one image per `senses.watch_one` call (the one-image wall), structured
NON-LEADING questions (the r7 contamination lesson), no timeouts, full
recording of served model, prompts, context, image hashes, raw responses
and finish reasons. `PYTHONIOENCODING=utf-8` throughout. The protocol's
`Saved/dyad/dyad_log.jsonl` also carries every call (written by senses
itself). Review tool: `tools/run_dyad_membrane_review.py`.

**Served model (read back from responses, not assumed):**
`qwen3.8-27b-nvfp4-mtp` (LM Studio resident, auto-follow; `can_see` probe
passed before use). No pin file was set. **Human (Alan) acceptance: NOT
CLAIMED — reserved to the operator. GPU-dynamics claim: NONE.**

## Context supplied to the dyad (every call)

The GLM-DYAD-01 physical-context briefing, verbatim: six triangles joined
around one centre vertex; six outer vertices fixed in a flat hexagonal rim;
the centre can move only perpendicular to the rim plane; U = gamma × total
triangle area; forces are the negative gradient; positive gamma seeks less
area so the raised centre approaches the rim plane; gamma=0 produces no
force so the initial bump remains; area-minimization only — no certified
elasticity, bending stiffness, water pressure, gravity or contact dynamics;
optimization iterations are not physical time; at identical geometry
doubling gamma doubles calculated energy and force, which alone does not
require a visible shape change. Plus the limit: numerical evidence, not
screenshots, establishes energy and force correctness; the prediction is
context, not permission to report a feature that is not visible.

Plus actual run facts from the recorded evidence: geometry (7 vertices, 6
triangles, rim radius 1.0 m, centre height 0.125 m initial / ~0 final, rim
edges 1.0 m), the exact camera values from the sidecars, render mode,
neutral color, capture mechanism, upload↔blob byte-verification.

## Round 1 — the three original captures (phi 0.3, fill only)

Evidence: `docs/evidence/membrane_window_demo/dyad_20260908T171550.069059Z/`.

| image | sha256 (first 16) | dyad verdict |
|---|---|---|
| window_gamma1_final | e3e6a49f1cacc900 | expected geometry NOT VISIBLE — empty dark field + red band; "capture/render fault" |
| window_gamma0_unchanged | 742b936ba0e78781 | consistent-with-bump only marginally; faint dark wedge; cannot resolve sign |
| window_gamma2_doubling | e3e6a49f1cacc900 | NOT VISIBLE — identical byte-hash to gamma1 (noted by the reviewer itself as expected given identical geometry) |

**Measurement before fixing (protocol step 4) — pixel arithmetic confirmed
the dyad's observations:**

- gamma1 and gamma2 PNGs are **byte-identical** (same sha256) — consistent
  with the proven bit-identical geometry and a deterministic renderer, not a
  capture fault.
- Background = RGB 32; gamma0's wedge = RGB 25: the mesh IS rendered but
  nearly black — its face normals sit ~90° from the engine's top light.
- Root cause found in source: **B2 is Z-UP, the engine world is Y-UP**
  (engine floor = XZ plane, height = Y). Uploaded unmapped, the membrane
  stood vertically with the bump pointing along the view axis.

**Concrete correction (Rule-0: statement/prediction/falsifier — falsifier =
the round-1 observations persisting in round-2 captures):** an explicit
axis-convention mapping at the upload boundary,
`(x, y, z)_b2 -> (x, z, -y)_engine` (rigid rotation; a presentation
transform of the ACCEPTED geometry — NOT a second simulation and not a
visual approximation; the f64 state of record is unchanged and both hashes
are recorded), camera elevation raised for legibility (phi 0.3 → 0.7,
recorded in sidecars), and fill+wire render mode (slotmode 2) as the dyad
itself requested. Fixed-camera law per run is untouched (all captures of a
run share one camera).

## Round 2 — recaptured states (axis-mapped, phi 0.7, fill+wire)

Evidence: `dyad_r2_20260908T172614.525525Z/`. Upload↔blob corroboration
MATCH for both captures.

| image | sha256 (first 12) | dyad verdict |
|---|---|---|
| dyad2_gamma0_bump | 2d0428545306 | **consistent** with the untouched low cone (hexagon + offset darker band = tilt-shading of the raised centre); bump-vs-flat NOT certifiable from this view alone — spokes not legible |
| dyad2_gamma1_flat | 14cf14591794 | **consistent**: flat plate, all spokes converging at a single IN-PLANE centre, no shading gradient; dyad cross-check: 2.598 J = area of a flat regular hexagon (3√3/2 ≈ 2.598) — "consistent with what is seen" |

The dyad's requested additional evidence: a near-top-down view where a
raised centre separates cleanly; brighter/contrasting edges.

## Round 3 — dyad-requested near-top-down diagnostic pair

Evidence: `dyad_r3_20260908T173301.037919Z/`; captures
`20260908T173201.273793Z/dyad2top_gamma0_bump_topdown.png` and
`20260908T173204.430256Z/dyad2top_gamma1_flat_topdown.png` (diagnostic
camera phi 1.45 rad, radius 3.5 — explicitly labelled in their sidecars;
upload↔blob corroboration MATCH ×2 via
`tools/dyad_topdown_capture.py`).

| image | sha256 (first 12) | dyad verdict |
|---|---|---|
| gamma0 top-down | 61ee64bd91f6 | **consistent, unconfirming**: uniform hexagon; the 0.125 m cone is indistinguishable from flat at ~83° elevation with flat top-lighting; wireframe not resolvable |
| gamma1 top-down | c7d839114a8c | **consistent**: flat hexagon, X of diagonal spokes converging at one centre point; flagged horizontal banding + a black lens across the middle — plausibly the coplanar mesh vs engine floor (depth-buffer ambiguity / z-fighting) |

## DYAD verdict (aggregated)

1. **Is the membrane visible and suitably framed?** After the round-1
   correction: YES — a well-framed hexagonal membrane with the centre fan
   legible in the fill+wire mode (rounds 2–3). In round 1 it was NOT (the
   axis-convention defect), which the dyad correctly called a render/capture
   fault and measurement confirmed.
2. **Is the centre-height difference resolvable?** The FLAT state is
   positively readable (spokes at an in-plane centre, uniform fill, energy
   = flat-hexagon area cross-checked by the reviewer). The 0.125 m BUMP is
   *visible as content* (round 2's offset darker band) but its SIGN and
   magnitude are not certifiable from any single view — the dyad says so
   explicitly and correctly: the height is 1/8 of the radius, foreshortened
   by every oblique view and collapsed entirely by the top-down view.
3. **Are the rendered results consistent with the stated geometry?** YES —
   every round-2/3 capture judged **consistent** with its declared state,
   with the reviewers' own uncertainty stated; no image contradicts the
   declared states or the numerical record.
4. **Rendered-vs-geometry discrepancies and their explanation:** the
   round-1 invisibility = axis-convention defect (fixed, falsified by the
   round-2/3 improvement); the round-3 banding/black-lens = coplanar
   mesh-vs-floor depth ambiguity — a NEW, concrete, unresolved rendering
   defect, recorded for the render lane (not a geometry fault; it does not
   affect any numerical verdict).

## Verdict classes (separate, as the law requires)

- **CPU/numerical:** PASS (prior evidence unchanged: F1–F7, all checks).
- **Upload:** payload/hash recorded; association CONDITIONAL with
  position-byte corroboration MATCH on every capture.
- **Window:** EXECUTED; visible and legible after the axis-mapping
  correction.
- **DYAD (this review):** CONSISTENT — the rendered results are consistent
  with the declared accepted states at every checked capture after
  correction; the membrane is visible and suitably framed; the flat state's
  centre offset is affirmatively absent from the images; the 0.125 m bump's
  sign/magnitude is NOT visually certifiable (stated by the dyad, with
  uncertainty, as required).
- **Human (Alan):** NOT CLAIMED — reserved.
- **GPU-driven dynamics:** NO CLAIM — this remains a CPU-reference
  visualization milestone.

## Open items recorded for the render lane

1. Coplanar mesh/floor depth ambiguity (banding + black lens in top-down
   views of the flat state) — z-fighting candidate; needs the render lane's
   own membrane.
2. Wireframe legibility: edges render thin/near-fill-coloured; the dyad
   requested contrasting/thicker edges (would also make the bump's spoke
   convergence readable).
3. A height-marker overlay or exaggerated-height pass would let the eye
   certify bump magnitude — a presentation feature, NOT a second geometry.
