# THE BEAR PIPELINE — splat source, generation, verification, rigging

> **2026-08-20: superseded as the generation path.** The authored pipeline —
> CAD body → gravity-settled coat → spray-painted appearance → regions — is now the
> governing architecture: [`THE_AUTHORED_PIPELINE.md`](THE_AUTHORED_PIPELINE.md).
> This file still owns the splat FORMAT (§1), the verification GATES (§3), and the
> captured-source history. Single-image generation (§2) is rejected as a source.

Settled decisions and the repeatable workflow for producing a riggable teddy bear.
Written 2026-08-18 after an agent burned a session re-discovering each of these. If you
are about to re-investigate a step, it is answered here. The renderer itself lives in
[`THE_RENDERER_DECISION.md`](THE_RENDERER_DECISION.md).

## 1. Splat format — settled

The C++ Vulkan renderer (`ChimeraEngine/engine/`) consumes **14-float 3DGS splats**:

```
x,y,z, r,g,b, a, sx,sy,sz, qw,qx,qy,qz   = 14 floats per splat
pos(3)  color(3)  alpha(1)  scale(3)  rotation-quaternion(4)
```

- **Source of truth: TripoSplat `.splat`** (32 bytes/splat: `f32 xyz`, `f32 scale`,
  `u8 rgba`, `u8 rot`). This is the only generator that emits the full 14-float layout
  (anisotropic scale + quaternion per splat).
- **TRELLIS is REJECTED.** It emits **7-float splats** — `x,y,z,r,g,b,size` — which carry
  no per-splat scale or rotation. That is not the 3DGS layout the renderer shades, and it
  cannot represent oriented ellipsoids. Do not re-open this.
- The 7-float story membranes (`story/*/physics.py` `emit()`) are a **separate legacy
  path**, not the teddy. The teddy is 3DGS (TripoSplat), not that path.

## 2. Generation workflow — image → `.splat`

1. **Reference image** — local SDXL Turbo at `models/imagegen/`:
   `sd-cli.exe -m sdxl_turbo_fp16.safetensors -p "<prompt>" -n "<neg>" -H 768 -W 768
   --steps 4 --cfg-scale 1.0 --guidance 3.5 --sampling-method euler_a -s <seed>`.
   The T-pose prompt is: *"product photo of a classic brown teddy bear, standing on hind
   legs, arms raised out wide in a T pose, soft even ambient studio lighting, no shadows,
   plain light grey background, centered, full body visible"* (neg: *"shadow, dramatic
   lighting, sitting, arms down, dark, watermark, text"*). SDXL Turbo is stochastic — the
   same prompt gives waving/asymmetric poses for most seeds, so **generate several seeds
   and pick the clean T-pose with the eye** (seeds 100 and 200 worked; 42 gave a wave).
2. **3D Gaussian splats** — TripoSplat (`models/triposplat/`, a vendored model — its
   checkpoints and data are gitignored, the wrapper is a few lines run from inside
   `models/triposplat/`):

   ```python
   from triposplat import TripoSplatPipeline
   pipe = TripoSplatPipeline(
       ckpt_path="ckpts/diffusion_models/triposplat_fp16.safetensors",
       decoder_path="ckpts/vae/triposplat_vae_decoder_fp16.safetensors",
       dinov3_path="ckpts/clip_vision/dino_v3_vit_h.safetensors",
       flux2_vae_encoder_path="ckpts/vae/flux2-vae.safetensors",
       rmbg_path="ckpts/background_removal/birefnet.safetensors", device="cuda")
   gaussian, _ = pipe.run("<image>.png", num_gaussians=262144, show_progress=True)
   gaussian.save_splat("<out>.splat"); gaussian.save_ply("<out>.ply")
   ```

   **Single-image.** This is the source of the §3 failure.
3. **Static verification — MANDATORY, gates rigging.** Before any skeleton is marked, the
   eye checks the bear for defects. See §3. A bear that fails is regenerated, never rigged.

## 3. Static verification — the gate the pipeline must pass

**Division of labor (non-negotiable):** the vision model (`senses.py`, qwen3.8) is the
EYE — it looks and reports defects. It does **not** analyze physics. Analyzing *why* a
defect exists (and confirming it in the data) is the **code agent's job**.

The gate: render the bear from N angles and ask the eye, defect-focused. A bear passes
only if every limb reads as **one** limb (right count), the pose is what was asked, and
**front and back agree** (same fur, same shape).

**The current T-pose bear FAILED (2026-08-18):**
- **Four arms, not two.** On each side the arm-region splats smear across a wide depth band
  (left z ∈ [−0.10, +0.22], right z ∈ [−0.13, +0.06]) — a front copy + a hallucinated back
  copy merged. Confirmed in the splat data, not just by the eye.
- **Front/back mismatch.** Front arm color ≈ (0.47,0.34,0.21) vs back (0.30,0.22,0.15);
  the back is ~40–50% darker — an invented surface, not the same fur.
- **Root cause:** TripoSplat is single-image. It has no depth and no back-view, so any
  limb whose z is ambiguous gets duplicated, and the unseen back is hallucinated in a
  different color. This is an **information problem**, not a sampling/prompting problem —
  more seeds cannot fix it.

**Open decision (regenerate before proceeding):** multi-view reconstruction (feed
front+side+back together) vs a fresh sample vs a real 3DGS asset. Single-image is out.

## 4. Rigging workflow — `ChimeraEngine/native/skeleton.py`

Repeatable tool, four stages, each writes a JSON artifact and can be re-run alone:

```
python ChimeraEngine/native/skeleton.py analyze      <splat> --dir <workdir>
python ChimeraEngine/native/skeleton.py mark         <splat> --dir <workdir>
python ChimeraEngine/native/skeleton.py triangulate  <workdir>/marks.json --dir <workdir>
python ChimeraEngine/native/skeleton.py assign       <splat> --skeleton <workdir>/skeleton.json --dir <workdir>
```

1. **analyze** — render N views (8 azimuths + 2 elevated), vision-DESCRIBE each →
   `analysis.json`. This is §3's gate: read the descriptions and the eye's defect report
   BEFORE marking.
2. **mark** — same views, vision-MARK the 13 joints as normalized 2D coords → `marks.json`.
   Joints: head_center, neck, shoulder L/R, elbow L/R, hand L/R, hip_center, knee L/R,
   foot L/R.
3. **triangulate** — un-project each 2D mark with the engine's exact orbit-camera model
   (radius/theta/phi, 45° FOV, Vulkan Y-down) → least-squares ray intersection → 3D joints
   → `skeleton.json`. Back views get a left/right swap (the eye's image-left/right flips).
4. **assign** — point-to-segment distance to each bone, nearest bone per splat →
   `assignment.json` (per-bone counts).

The camera model in `skeleton.py` matches the C++ engine exactly, so a mark the eye places
is a ray in the same frame the renderer uses — no reprojection drift.

## 5. THE SERIES — ordered steps, each gated

Do them IN ORDER. Do not proceed past a FAILED gate. A step is not "done" until its
gate passes; "looks okay" is not a pass.

1. **SOURCE a valid bear** — 2 NORMAL arms (not two fused into one per side), front and back
   identical in texture AND color.
   - GATE: the eye reports exactly 2 arms, and front texture == back texture.
   - STATUS (2026-08-18): **FAILED** — arms melded (2 fused per side), back texture mismatched.
2. **EXTRACT materials** — vision marks the materials; extract average color AND the texture
   genome (`log_size`, `aniso`, `opacity` distributions) from the front splats.
   - GATE: the codebook separates into distinct materials (not one grey).
   - STATUS: **DONE** — 6 materials, color genome + texture genome extracted (§3, §5).
3. **REAPPLY** — recolor every splat to its material average (done), then resample the back's
   splat scale/density to the front's texture distribution (relocate splats within the shape).
   - GATE: front and back agree in color AND in log_size/opacity distribution.
   - STATUS: color done; texture relocation **NOT done**.
4. **RIG** — mark joints → triangulate → assign bones (`skeleton.py`).
   - GATE: static verification passes (2 normal arms, coherent limb assignment).
5. **DRIVE** — the CA/force dynamics (gravity field + muscle/contact forces); pose emerges.

## 6. State (2026-08-18)

- Sitting teddy `teddy.splat` renders correctly; its rig attempt failed (limbs too tangled
  — that is why we moved to a T-pose).
- T-pose teddy `teddy_tpose.splat` renders but **failed static verification** (4 arms,
  front/back mismatch). Do not rig it.
- **T-pose teddy `tpose2_640.splat` PASSED static verification** (eye: exactly 2 arms,
  front/back fur agrees; data: single-layer arms, back ~8–11% darker not 40–50%). This is
  the bear to rig (§4).
- Engine fix (same day): `engine.cpp` alpha accumulation `dstAlphaBlendFactor`
  ZERO → ONE_MINUS_SRC_ALPHA — the old state let each splat's alpha *replace* the
  destination's, and low-alpha skirts composited to white on readback. Also
  `cpp_bridge.render_splat_movie()` (orbit movie of a `.splat`, no CPU pre-sort — the
  GPU bitonic sort is authoritative) and `_post_membrane_bin` now checks the response
  body (`"ok":true`), not just HTTP 200 — the engine answers 200 + `{"ok":false}` on a
  payload-size mismatch, which silently kept the previous buffer on screen.
- Next: rig `tpose2_640.splat` (§4), then DRIVE.

Agent: Kilo (chimera-code)
