# THE AUTHORED PIPELINE — CAD body → gravity-settled paint → spray-painted appearance → regions

> **This pipeline runs under [`THE_METHOD.md`](THE_METHOD.md)** (declared 2026-08-20):
> every stage has a slot in the Chimera viewer, every stage passes only on the human's
> authorization, and every transition is an MCP tool call. Read that first.

**This is the game-asset workflow, not the bear workflow.** The teddy is the demo object;
every step here applies to any authored part or imported model. Written 2026-08-20; the
session narrative and measured numbers are in
[`SESSION_LOG_2026-08-20.md`](SESSION_LOG_2026-08-20.md). The renderer this feeds is the
C++ Vulkan engine ([`THE_RENDERER_DECISION.md`](THE_RENDERER_DECISION.md)); the splat
format is 14-float 3DGS ([`THE_BEAR_PIPELINE.md`](THE_BEAR_PIPELINE.md) §1).

## Why this exists

Single-image 3D generation cannot pass the SOURCE gate by construction (the back is
hallucinated). AI-video photogrammetry can, but it is soft, spendy, and drift-prone —
measured: simultaneity of views is worth +4.1 dB, and even the best run needs artifact
surgery after training. The authored pipeline inverts the relationship: **we no longer
ask a generator to invent geometry.** Geometry is authored (exact, symmetric, jointed,
mass-known). Generative/captured data only supplies *appearance*, painted onto geometry
that is already right.

## The four stages

### 1. BODY — the CAD substrate

`tools/teddy_catalog.py` (parts library) + `tools/teddy_body.py` (math).

- A body is a **parts list of analytic primitives** (ellipsoid / capsule / sphere).
  13 slots for the teddy, each with multiple style variants; `assemble(style_map)`
  builds an instance.
- Every part carries **joint metadata** (parent, pivot, axis) — limbs are segmented
  (upper_arm + forearm, thigh + shin), which is what makes posing well-defined.
- Every part has **analytic mass** (volume × density, closed form) and the union is an
  **SDF** (smin-blended) with exact normals via the gradient.
- **Any imported model joins here**: convert mesh → SDF once, and everything below
  applies unchanged. Import gives you a statue; joints make it a puppet.

### 2. SETTLE — paint rains on under gravity

`tools/teddy_skin.py::settle_coat()`. The operator's model: **every part is a
gravitational body.** Paint does not get *placed*; it *falls and lands*.

- Each part's paint starts as an **orb** — a spherical cloud around the part.
- Attraction: n-body, force ∝ part **mass** / r² toward the part centroid. Nearby parts
  win captures; at joints two attractors share the crease, which closes joint gaps.
- Collision: the union SDF stops particles at the surface (project out, kill the inward
  velocity, keep the tangential slide).
- Repulsion: short-range mutual repulsion spreads the coat evenly.
- Derivations, not knobs: particle budget ∝ part **surface area** (coverage scales r²;
  mass scales r³ — mass sets force, area sets budget); spacing s = √(A_total/N);
  repulsion radius and disc radius follow from s.
- The settle is damped (quasi-static): particles spiral in and land, not orbit.
- Output identity: every splat leaves with **(part_id, uv)** — capsule uv = (axial t,
  angle around limb), ellipsoid uv = (azimuth, elevation). Saved as a `.meta.npz`
  sidecar next to the `.splat`.

### 3. PAINT — appearance is spray-painted on welded geometry

`tools/train_spray.py` (gsplat, .venv-gs).

- After settling, **positions are welded**. Only color/alpha/scale train. (Measured
  lesson: letting offsets train inside a clamp cost 21.4 → 15.6 dB. Weld, don't clamp.)
- The source is anything image-like: SV3D frames (28.0 dB held-out on the authored body),
  real photos with cameras (CO3D lane: `tools/co3d_to_views.py` — conversion validated at
  99.5% mask hit by projecting the real pointcloud), or flat/pattern materials.
- Loss is masked: foreground L1+SSIM on the object, |pred| on the background.
- Body fit to a real target: `tools/fit_body_to_cloud.py` (cluster labels by projecting
  centroids onto a photo; centroid-anchored primitive fit; children FOLLOW parents).

### 4. REGIONS — draw on the surface, repaint just there

A region is a **named predicate over (part_id, uv)** — the pencil drawing on the CAD.

- Example: `bow_tie = (part_id == torso) & (u in neck band) & (v in front window)`.
- A region gets its own **material channel**: extract those splats, freeze the rest,
  repaint only the region (photo, flat color, pattern).
- v1: analytic regions (numbers on the parametric surface — precise, scriptable).
  v2 (planned): mouse-drawn strokes in the viewer, ray-cast onto the SDF → uv paint.
- This is the membrane granularity the engine wants: body → parts → regions → materials,
  every level addressable without touching the rest.

## The trainable layers (declared 2026-08-21)

Both authored layers are LEARNED from real scans, not hand-tuned. Under
[`THE_SPACE.md`](THE_SPACE.md) everything trains in the canonical metric frame.

### Trainable COAT — the patch genome library

Materials are extracted from REAL photogrammetry 3DGS scans (CO3D teddies first —
real fur, real adaptive-density statistics; `splat_genome.py` proved the size/aniso
fingerprint exists ONLY in ADC-trained clouds). **Before extraction, the donor is
sectioned by [`THE_SECTIONING_METHOD.md`](THE_SECTIONING_METHOD.md)** (declared
2026-08-21): chalk-drawn hierarchical regions + a triangulated stick figure, both
eye-verified on the real object — genomes are extracted PER REGION, relative to the
inner core. The unit of extraction is the
**patch**: a ~2cm surface disc carrying its full splat population (count, sizes,
anisotropies, orientations, colors, relief heights) plus a **context key**
(part-relative position, tone, curvature, **nap direction** — fur lies along a grain;
the orientation field is extracted with the patch or sprayed fur reads as noise).

Spraying is **conditional transplant**: target locations on the CAD body retrieve
patches whose context matches, transplant with jitter, blend seams. Variation is
guaranteed because every patch is a real observed instance — the system learns the
DISTRIBUTION, never the average (averaging collapses to the blur we keep rejecting).
Multiple scans of the same material class teach cross-instance variation (what "plush
torso" is as a class vs one bear's belly). A small conditional sampler trained on the
library then generates NOVEL combinations/series (v2).

### Trainable BODY — the parametric shape space

Every real scan gets its CAD body fitted to it (`tools/fit_body_to_cloud.py`); each
fit is one point in the class's shape space (teddy: limb lengths, torso profile,
head/body ratio, ear placement). PCA (then a small neural net) over those fits gives a
samplable body model — the SMAL precedent (a learned animal body trained on toy scans,
a teddy bear among them) proves the shape. A sampled body is born posable: the rig
hangs off the parametric parts. Scan in → fit → shape space grows; sample out → new
legal body → pose → spray.

The full machine: **sample a body → pose it → spray fresh material combinations →
all in canonical metric space.** Nothing hallucinated flat; every layer measured.

## Verification contract

Every stage shows its output before the next begins: the raw settled coat is inspected at
6 angles (geometry only, no paint) before training; the painted bear is inspected before
posing. The eye (qwen3.8 via `senses.py`) reports; the operator is the terminal judge.
Numbers over prose: held-out PSNR for paint, mask-hit rate for camera fits, per-part
landed counts for the settle.
