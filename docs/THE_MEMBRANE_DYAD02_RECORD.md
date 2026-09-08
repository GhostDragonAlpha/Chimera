# GLM-DYAD-02 — floor ambiguity resolved; bump-height visual comparison INCONCLUSIVE (2026-09-08)

Task: continue from `931ce1e596fffbc08212bf07b13e4f294c35bd7a`, on
`astra/gait-capture`, isolated checkout. Numerical law, fixtures and
tolerances untouched.

## Preregistration (written before the controlled test)

- **STATEMENT:** Removing floor overlap (rigid +0.5 m presentation lift
  along engine y, identical across compared captures) improves surface
  legibility without changing the accepted physical geometry.
- **PREDICTION:** With the lift, rim and centre are distinguishable and a
  raised-vs-flat comparison becomes resolvable in captures made with
  identical presentation, camera and render settings.
- **FALSIFIER:** The ambiguity persists, the physical geometry changes, or
  centre height remains visually unresolved (an unresolved height is
  **INCONCLUSIVE** for that visual comparison).

## Part 1 — the reported floor/mesh ambiguity: hypothesis → supported

The round-3 dyad flagged "horizontal banding + a black lens" on the flat
gamma-1 top-down capture. Treated as a hypothesis, then tested by control:

- **Controlled comparison** (`dyad02_control_20260908T191152.065006Z/`):
  same uploaded state (gamma=1 accepted terminal state, recomputed by the
  same procedure), same camera (the exact round-3 camera: r=3.5, θ=0,
  φ=1.45), same render mode; **only the lift differs** (0.0 vs +0.5 m).
- The lift=0.0 capture is **byte-identical** to the round-3 artifact capture
  (`c7d83911…`, matches the sidecar in `20260908T173204.430256Z/`) — the
  artifact reproduces exactly.
- The lifted capture shows **zero** sub-background pixels (<32 luminance)
  where the coplanar one shows 61,138; row-band std drops 21.32 → 11.83.
- A first control attempt on the *bumped* state at φ=1.10 showed no
  artifact in either presentation — correct outcome, wrong state (only the
  bump's rim is coplanar). Preserved as `control_record.json` in the same
  directory; the corrected control is `flat_control_record.json`.

**Verdict: hypothesis SUPPORTED.** The artifact belongs to the coplanar
presentation, not to the physical state. It is a depth conflict between the
flat membrane and the engine's floor/shadow plane (both rasterize y=0,
`engine.cpp` ~1497).

## Part 2 — the presentation lift (no physics touched)

No floor-visibility control exists in the engine's HTTP surface, so the
documented route was the **rigid presentation translation**: uploads now
carry an optional vertical lift (default 0.5 m, engine y; recorded per run
and per sidecar). The accepted f64 geometry of record, energies, forces and
state IDs are untouched; `F8` gates enforce this (upload-state geometry =
fixture; each capture's geometry = its run's accepted state). No bump
exaggeration, no contact physics, no general-renderer repair.

## Part 3 — raised vs relaxed pair, identical presentation/camera

- Raised (γ=0, 0 steps): `20260908T191901.379767Z/` (φ=1.10 pair) and
  `20260908T192702.077867Z/` (oblique φ=0.55 pair)
- Relaxed (γ=1, 126 steps, energy 2.6245730615178493 → 2.5980761647224426 J):
  `20260908T191858.213817Z/` and `20260908T192708.250952Z/`
- Every capture: fixed/diagnostic camera recorded in its sidecar, blob
  corroboration MATCH at capture time. Checks F1–F8: **ALL PASS**
  (γ=1 evidence `20260908T191858.213817Z`).

## Parts 4–5 — DYAD rounds 4 and 5, and the honest verdict

Protocol executed (one image per call, no timeouts, non-leading questions,
full recording; served model read back as `qwen3.8-27b-nvfp4-mtp`):

- **Round 4** (φ=1.10 pair): relaxed = **CONSISTENT**; raised =
  **cannot determine** — no legible bump cue at that elevation.
- **Round 5** (oblique φ=0.55 pair, the dyad's own requested
  discriminator): relaxed = **CONSISTENT** (flat, nothing to see);
  raised = **cannot determine** — the interior carries no cue: no visible
  wireframe spokes, no shading gradient.

**Verdict under the preregistration: the raised-vs-flat centre-height
comparison is INCONCLUSIVE.** The falsifier fired on "centre height remains
visually unresolved"; per the task, this is recorded as INCONCLUSIVE, not
PASS, and per Rule 0 the expectation "a raised centre must be legible" is
*retired* for the current presentation stack.

## Remaining cause (measured + source-verified, not speculation)

1. **Zero shading response (measured):** raised vs relaxed fill statistics
   are identical at every tested camera (mean 157.1, p5–p95 spread 0.0,
   std ≈ 4.2): the engine's default lighting produces no brightness
   gradient across the bump's cone faces.
2. **Interior contrast is zero by construction (source-verified):** the
   wireframe pass is the fill pipeline with polygon mode LINE, drawing
   **the same vertex color as the fill** (`engine.cpp` ~1439: "identical in
   every state except polygon mode"). 1px same-color interior lines cannot
   be seen against the fill — the dyad's uniform "featureless hexagon"
   report is what the renderer currently produces.

Making the centre height legible (contrasting edge color, centre marker, or
shading response) is a **general-renderer improvement** — explicitly out of
scope here. Recorded for the operator as the concrete next lever.

## Evidence paths

- Controlled comparison: `docs/evidence/membrane_window_demo/dyad02_control_20260908T191152.065006Z/`
- Raised/relaxed pairs: `20260908T191901.379767Z/`, `20260908T191858.213817Z/`,
  `20260908T192702.077867Z/`, `20260908T192708.250952Z/`
- DYAD rounds: `dyad_r4_20260908T192355.462899Z/`, `dyad_r5_20260908T192906.085166Z/`
- Launch record (PID 66400, exe hash, CWD, endpoint; stopped after use):
  `launch_20260908T183000Z/`

## Verdict classes (separate)

- Numerical CPU: **PASS** (F1–F8, all checks green)
- Upload: payload/hash recorded; association **CONDITIONAL** with position-byte
  blob corroboration MATCH on every capture
- Window: **EXECUTED** (isolated instance; operator's engine untouched)
- **DYAD: artifact RESOLVED (controlled evidence); centre-height visual
  comparison INCONCLUSIVE** (cause identified and recorded)
- Human (Alan): **NOT CLAIMED** — the pair is presented below for review
- GPU-driven dynamics: **NO CLAIM** (CPU-reference visualization)

## For Alan — the image pair for human review

The same view (oblique φ=0.55), identical presentation, differing only in
accepted state:

- Raised (γ=0, bump 0.125 m): `docs/evidence/membrane_window_demo/20260908T192702.077867Z/raised_gamma0_oblique.png`
- Relaxed (γ=1, flat): `docs/evidence/membrane_window_demo/20260908T192708.250952Z/relaxed_gamma1_oblique.png`

(Also available: the φ=1.10 pair in `20260908T191901.379767Z/` /
`20260908T191858.213817Z/`. DYAD judged the flat state consistent in every
round but could not resolve the bump visually — see the cause analysis
above.)
