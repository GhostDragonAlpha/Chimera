# GLM-DEMO-CONTRAST-01 — edges contrast works; height distinction still INCONCLUSIVE; experiment stopped (2026-09-08)

Task: continue from `ae5c5d6ed0a20c88c75ea29fb9055203de1e3c0e` on
`astra/gait-capture`, isolated checkout. Numerical law, fixtures,
tolerances, physical geometry, presentation lift and energy law untouched.

## Preregistration (before implementation)

- **STATEMENT:** Contrasting edges make the actual centre/rim geometry more
  distinguishable without changing accepted simulation state.
- **PREDICTION:** DYAD can locate the centre and rim and distinguish the
  raised and relaxed configurations in a suitable fixed oblique view.
- **FALSIFIER:** Geometry changes, ordinary rendering regresses, or the
  height distinction remains unresolved (→ **INCONCLUSIVE**).

## Implementation — smallest opt-in patch

- `ChimeraEngine/engine/shaders/render_tri_edge.frag` (NEW): constant light
  edge color `(0.90, 0.90, 0.95)` — derived from the measured fill band
  (147–167 8-bit) and the family neutral's +0.05 blue tint, strictly above
  the whole fill band; no new lighting, no invented taste.
- `engine.hpp`: `tri_edge_pipeline_` + `tri_edge_frag_mod_` +
  `tri_edge_contrast_` members.
- `engine.cpp`: the env var `CHIMERA_TRI_EDGE_CONTRAST` is latched at init;
  the module load is optional-instrument law (a stale/missing spv costs the
  feature, not the engine); the LINE-mode twin is created ONLY when latched
  on, sharing all state with the wire twin except the fragment; the wire
  draw substitutes it when present. **When the env var is absent, no new
  pipeline exists and no code path changes.**
- Ordinary engine path unchanged when disabled — proven, not assumed:

## Regression — ordinary rendering preserved (byte-identical)

Patched exe (`f3714eb9…`), env UNSET, same flat state, exact round-3
camera, lifts 0.0/+0.5: PNG sha256 **`c7d83911…`** and **`83f4b364…`** —
byte-identical to the pre-patch captures. (A corroboration FAIL during
this run was tooling — the blob path pointed at build1's snapshot; fixed
with the `CHIMERA_MESH_BLOB` override and re-run green. Recorded in
`launch_20260908T203000Z/regression_record.json`.)

## Physics invariance — verified

Checks F1–F8 on the contrast-pair γ=1 evidence
(`20260908T203626.782212Z`): **ALL PASS** (energy bit-identity,Armijo,
rails, pins, upload boundary, F8 geometry-of-record gates). State IDs
differ from earlier runs only because they are commit-scoped (HEAD moved
`931ce1e5` → `ae5c5d6e`); energies and geometry hashes are bit-identical.

## Captures (gate ON, PID 25480, exe `f3714eb9…`)

Raised (γ=0, 0 steps): `20260908T203620.679992Z/raised_contrast_oblique.png`
Relaxed (γ=1, 126 steps): `20260908T203626.782212Z/relaxed_contrast_oblique.png`
Identical +0.5 m presentation lift, identical oblique camera (r=3.0,
φ=0.55), fill+wire render; blob corroboration MATCH both.

Measured effect: bright-edge pixels 408 (raised) / 376 (relaxed) where the
pre-patch renders had 0; fill statistics unchanged (mean 157.6, spread 0.0).

## DYAD round 6 — honest split verdict

Served model `qwen3.8-27b-nvfp4-mtp`, protocol followed, full recording
(`dyad_r6_20260908T203756.192289Z/dyad_review.json`):

- **The patch achieved its aim:** the dyad now LOCATES the centre ("the
  spoke junction") and the rim, and reads the mesh as floating clear of
  the floor — previously impossible.
- **The height distinction remains NOT RESOLVABLE:** "the six spokes are
  straight line segments in 3D whether or not the centre is raised, so
  their projection looks identical flat vs raised", and perspective alone
  confounds any junction offset. Flat state: consistent. Raised state:
  cannot determine.

**Verdict under the preregistration: the height distinction is
INCONCLUSIVE.** The falsifier fired on "height distinction remains
unresolved"; per the task's stop rule, **this visual experiment stops
here** — no further presentation loop.

## The geometric fact now established (for the operator)

Two independent, mutually-confirming proofs that THIS rendering approach
cannot resolve the B2 bump height:

1. **Zero shading response** (GLM-DYAD-02, measured): the engine's lighting
   produces identical fill statistics for raised and flat states at every
   tested camera.
2. **Projection invariance** (this task, dyad-stated and geometrically
   sound): straight spokes project identically raised or flat at these
   elevations, and perspective confounds the junction offset.

Resolving the height visually requires a different evidence class —
side/elevation orthographic view, a rim-plane reference overlay, or a
height/normal color ramp — all general-renderer or demo-tool work beyond
"smallest opt-in rendering change". Left to the operator.

## Scope boundaries respected

No physical geometry change, no height exaggeration, no energy-law change,
no simulated forces; the identical recorded rigid presentation lift was
retained for both compared states; ordinary rendering preserved when the
gate is unset (byte-identical regression); builds in scratch dirs only;
only my own instances controlled; no master push, no force-push, no
protected-path writes, no tolerance change. Human acceptance and
GPU-driven integration remain unclaimed.

## Verdict classes (separate)

- Numerical CPU: **PASS** (F1–F8, both pair runs)
- Upload: CONDITIONAL with position-byte corroboration MATCH
- Window: EXECUTED (isolated instance, gate OFF regression + gate ON pair)
- **DYAD: centre/rim LOCATABLE (patch works); height distinction
  INCONCLUSIVE — experiment stopped per stop rule**
- Human (Alan): NOT CLAIMED — the new pair is presented for review
- GPU-driven dynamics: NO CLAIM

## For Alan — the contrast pair for human review

- Raised: `docs/evidence/membrane_window_demo/20260908T203620.679992Z/raised_contrast_oblique.png`
- Relaxed: `docs/evidence/membrane_window_demo/20260908T203626.782212Z/relaxed_contrast_oblique.png`
