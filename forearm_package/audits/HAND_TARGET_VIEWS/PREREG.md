# PREREG — HAND_TARGET_VIEWS (M-handtgt) — FROZEN BEFORE ANY RENDER

**Date frozen:** 2026-09-24 · **Fulfills:** `audits/HAND_EVIDENCE_REQUEST/HAND_EVIDENCE_REQUEST.md` §R1
**Camera numbers:** the §R1.4 defaults, executed AS-IS (the request states they are "executable as-is"; they are arithmetic on O2's recorded vectors). Every constant below also appears as a named constant in `scripts/render_hand_views.py`; the script ASSERTS the derived vectors against the §R1.4 recorded values before rendering.

## 1. IDENTITY PINS (re-asserted before rendering — F-R1b)

| pin | value | verified |
|---|---|---|
| `monkey_birth.bin` | sha256 `550a5b3ec927ea13614ad250963b23e2948e76a238ac110da9889f339aabfa3c` (661,076 B) | YES (this audit, pre-render) |
| `monkey_joints.bin` | sha256 `74b3ab044b7adaed4a0f9349a81f5d3c87441084b2ec8981f4e0afaba50c1662` (296,589 B) | YES |
| loader copy | `work/mesh_target_htv.py` ≡ `baseline_snapshot/code/mesh_target.py`, sha256 `268f139a9e90e561f4a5f8ab02553f0d87f51633f635139e6cec6f5c9cfa19a0` | YES (byte-identical) |
| `mesh_unit_to_m` | 0.065 (authored) | from loader |
| frame | anterior = +z, up = +y, right = −x (O1 §frame) | cited |

No mesh repair/resampling of any kind: the rendered surface derives from the pinned file verbatim (the sidecar's repair field records "none").

## 2. FROZEN CAMERA PAIR (right hand; the deliverable)

Derived in-script from the pinned joint pack (values asserted to the §R1.4 recorded 6-decimal values):

- `wrist_R = (−0.144995, 0.261482, −0.005956)` m, `elbow_R = (−0.1155, 0.3191, −0.0061)` m (loader, asserted)
- `a = unit(wrist_R − elbow_R)`, asserted ≈ `(−0.455844, −0.890058, 0.001857)`
- `T_R` = C3's fixed rule "rejection of global +x on the plane orthogonal to a", asserted ≈ `(0.890060, −0.455843, 0.000951)`
- `n_t = unit(a × T_R)`, asserted ≈ `(0.000000, 0.002086, 1.000000)` (the palm-normal CANDIDATE axis — its anatomical sign is exactly what the human answer creates; nothing here assumes it)
- `look_at = wrist_R + 0.083·a`, asserted ≈ `(−0.182830, 0.187607, −0.005802)`
- **View 1 (+n_t-side view):** `eye₁ = look_at + 0.30·n_t`, view direction `f₁ = −n_t`, **letter A** = the broad face toward this camera (the +n_t-side face)
- **View 2 (−n_t-side view):** `eye₂ = look_at − 0.30·n_t`, view direction `f₂ = +n_t`, **letter B** = the broad face toward this camera (the −n_t-side face)
- `up = a` (both views) · camera right = `unit(up × unit(eye − look_at))` (both views; this makes view 2 the horizontal mirror of view 1 — declared, not accidental)

## 3. FROZEN PROJECTION / CROP (region definition = the camera; falsifier b tests it)

- Orthographic projection, half-width **0.040 m** (the §R1.4 default), image **2048×2048 px**.
- Rasterizer: **custom z-buffer triangle rasterizer over the pinned mesh triangles** (the "compute the projection yourself" option of the task brief), numpy-only, CPU. Supersample factor 2 (render 4096², 2×2 box downsample — declared, deterministic). Depth slab |depth along f| ≤ 0.65 m about the eye (generous; the object is at 0.30 m).
- Triangle pre-filter (rendering cost only, never a region edit): triangles with any vertex inside the frame box expanded by **5 mm**. Every mesh triangle competes for pixels; the frame is the only crop.
- **Crop check (falsifier b, executed as assertions):** all band verts (axial station t = (v−wrist_R)·a ∈ [55, 111.4] mm within the B1 r < 42 mm cap) must project inside the frozen frame; the projected stations 55 and 111.4 mm must lie ≥ 3 mm inside the frame edges; the measured on-image span of the 47.1 mm broad face must be **≥ 600 px** (R1.5 visibility bar).

## 4. FROZEN SHADING (declared, symmetric across the opposed pair)

- Light direction TO LIGHT, in camera frame `(right, up, forward)`: `unit(0.25, 0.30, −1.0)` — a declared headlight offset, identical relative geometry in BOTH views, so neither face is favored.
- Intensity `= 0.25 + 0.75·max(0, n̂_visible · L̂)` (two-sided visible normal), albedo 0.62 (neutral gray, no hue bias), background 0.94.
- Per view, a **depth-relief inset** (420×420 px, bottom-right): the z-buffer of the visible surface rendered grayscale (lighter = closer to camera) — makes flat-vs-bulged legible without suggesting an answer; drawn from the same declared camera.

## 5. FROZEN ANNOTATION PLAN (all machine-drawn from the declared constants; nothing hand-placed)

Each PNG carries:
1. **Title strip** (top, fixed rows): view name + face letter; camera declaration: eye, look_at, view direction, up, projection ("orthographic half-width 0.040 m"), light, mesh sha256 prefix, script + invocation.
2. **Scale bar** (bottom-left): 10.00 mm = 256 px exactly (2048 px / 0.080 m), drawn with end ticks and label.
3. **Axis triad** (top-right): world +x/+y/+z projected onto the view (2D arrows), labeled — so the reader sees the birth frame.
4. **Axial ruler** (the projected axis line, u=0 by construction): ticks at **0 / 48 / 55 / 80 / 111 mm** (§R1.3-B stations). Frozen declaration: the 0 mm tick (wrist_R) projects 83.0 mm below frame center — **outside** the frozen 40 mm half-width — so it is drawn as a frame-edge arrow annotation reading "wrist_R (0 mm) — 83 mm below frame"; ticks 48/55/80/111 are in-frame (frame covers t ∈ [43, 123] mm). Ticks 55 and 111 bound the distal band; the band is additionally labeled "distal band 55–111.4 mm".
5. **Face letters**: view 1 draws a large **A** with a leader line to the projected band center ("face A — toward camera"); view 2 draws **B** likewise. The letters label FACES (A ≡ +n_t-side face, B ≡ −n_t-side face), never an anatomical claim.
6. **Guidance line** (bottom strip, verbatim from O2's recorded diagnostics via §R1.3-B): "One broad face is the flatter/slightly cupped one; the other carries the outward lens bulge — state which lettered face is the PALM (volar)."
7. **wrist_R origin marker**: the frame-edge arrow of item 4 plus a cross marker at the projected wrist position when in-frame (it is not, under the frozen camera — the arrow carries the world coordinates).

## 6. FROZEN OUTPUT PATHS

- `figures/hand_target_R_view1_plusnt.png` (+ `.json` sidecar) — right hand, +n_t-side view, face A
- `figures/hand_target_R_view2_minusnt.png` (+ `.json` sidecar) — right hand, −n_t-side view, face B
- `figures/hand_target_L_mirror_check.png` (+ `.json` sidecar) — LEFT hand, same construction mirrored (axes: `a_L`, `T_L` by the same fixed +x-rejection rule, `n_tL = unit(a_L × T_L)`), both opposed views stacked 2048×4096; letters A/B by the same convention; CONSISTENCY CHECK ONLY (not a deliverable view)
- Sidecars carry the §R1.3-C fields (eye, look_at, up, view_direction, projection, image_size_px, mesh/joints/loader sha256, mesh_unit_to_m, renderer/channel, exact invocation, repair="none") + measured face-span px + letter mapping. Sidecars contain no timestamps (byte-reproducible).

## 7. FROZEN REPRODUCIBILITY PROTOCOL

The script runs twice unmodified; all six files must hash identical run-to-run (no timestamps anywhere). Declared renderer nondeterminism: none expected (pure numpy arithmetic + Agg PNG); if any hash differs, the divergence is recorded and the pixel arrays compared — that is falsifier (a).

## 8. FALSIFIERS (from the task brief; named before the run)

- **(a)** the render not reproducible from the script constants → the deliverable FAILS, recorded.
- **(b)** the crop missing the distal band (any §3 assertion fails) → the deliverable FAILS, recorded.
- **(c)** any GPU usage — none permitted; Agg before pyplot import; no OpenGL/Vulkan/WebGL/context imports anywhere in the script (grep-checked in the receipt).
- Plus §R1.6 as written: **F-R1a** (if the human cannot distinguish the faces at the ≥600 px bar, the visibility assumption is REFUTED — recorded, not retried with a re-framed camera); **F-R1b** (hash mismatch / undeclared modification → rejected); **F-R1c** (if the views reveal non-hand anatomy → escalate §R3 before any palm sign is consumed). The render only supplies the VIEW; R1.3-D places the verdict with the human terminal (an LLM answer is another claim, never the verdict).

## 9. STOP RULE

The opposed pair rendered + reproducibility proven (hashes) + the human-question card prepared → STOP and report. No palm sign is authored here; no curvature/assembly/scale/production quantity is computed (§R1 scope).
